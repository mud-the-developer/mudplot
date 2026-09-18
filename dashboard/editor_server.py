"""A dependency-light local interactive editor server.

It uses stdlib ``http.server`` + ``mudplot[render]`` and one vendored,
dependency-free htmx file (``dashboard/static/htmx.min.js``, 0BSD licensed).
There is exactly one piece of session state (``EditorSession``), and it holds
nothing the engine doesn't already model — every edit is a dispatched
``Action``, same as the fluent API.

English by default (per project convention).
"""

from __future__ import annotations

import copy
import functools
import io
import ipaddress
import socket
import threading
from dataclasses import fields as dataclass_fields
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import mudplot as mp
from mudplot import actions as A
from mudplot.capabilities import LAYER_TYPES
from mudplot.io import _loads_json
from mudplot.spec import FigureSpec, LayerSpec
from mudplot.store import Store
from mudplot.validate import assert_valid

from .editor_view import _DRAG_JS, render_app_body, render_docs_page, render_page
from .markdown_lite import markdown_to_html
from .samples import sample_columns

__all__ = ["EditorSession", "make_server", "serve"]

_HTMX_JS = (Path(__file__).parent / "static" / "htmx.min.js").read_bytes()
_MAX_BODY_BYTES = 16 * 1024 * 1024
_CSP = (
    "default-src 'self'; img-src 'self'; script-src 'self'; "
    "style-src 'unsafe-inline'; object-src 'none'; form-action 'self'; "
    "base-uri 'none'; frame-ancestors 'none'"
)


def _is_loopback_address(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_loopback_host(host: str) -> bool:
    try:
        parsed = urlparse(f"//{host}")
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    return (
        hostname is not None
        and parsed.username is None
        and parsed.path == ""
        and parsed.query == ""
        and parsed.fragment == ""
        and _is_loopback_address(hostname)
    )


class EditorSession:
    """One editor's worth of state: a Store plus the last render, if any.

    A thin imperative-shell wrapper -- all real state lives in the Store's
    FigureSpec; this caches the most recent render (PNG bytes + a bit of
    layout info the client needs to place draggable handles) so ``/fig.png``
    doesn't have to re-render on every request, and provides a lock since
    ThreadingHTTPServer handles each request on its own thread.
    """

    def __init__(self) -> None:
        self.store = Store()
        self.error: str | None = None
        self.lock = threading.Lock()
        self.png: bytes = b""
        self.layout: dict = {}
        # Which panel the side controls edit and the drag handles belong to.
        # UI state, not figure state, so it lives here rather than in the
        # spec (the spec must stay exactly what a script would produce).
        self.active_panel = 0
        self.refresh()

    def select_panel(self, index: int) -> None:
        spec = self.store.state
        n = len(spec.panels)
        if not 0 <= index < max(n, 1):
            raise IndexError(f"no panel {index} (figure has {n})")
        try:
            png, layout = self._render_preview(spec, index)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            return
        self.active_panel = index
        self.png, self.layout, self.error = png, layout, None

    def _clamp_panel(self) -> int:
        """Keep the selection valid when the layout shrinks under it."""
        n = len(self.store.state.panels)
        if self.active_panel >= n:
            self.active_panel = max(n - 1, 0)
        return self.active_panel

    def action_log(self) -> list[dict]:
        return [A.action_to_dict(a) for a in self.store.history]

    def _commit_store(self, candidate: Store, active_panel: int) -> None:
        spec = candidate.state
        assert_valid(spec)
        active_panel = min(active_panel, max(len(spec.panels) - 1, 0))
        png, layout = self._render_preview(spec, active_panel)
        self.store = candidate
        self.active_panel = active_panel
        self.png, self.layout, self.error = png, layout, None

    def dispatch_safe(self, action) -> None:
        candidate = copy.deepcopy(self.store)
        try:
            candidate._dispatch(action)
            self._commit_store(candidate, self.active_panel)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def undo(self) -> None:
        candidate = copy.deepcopy(self.store)
        try:
            candidate.undo()
            self._commit_store(candidate, self.active_panel)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def redo(self) -> None:
        candidate = copy.deepcopy(self.store)
        try:
            candidate.redo()
            self._commit_store(candidate, self.active_panel)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def reset(self) -> None:
        try:
            self._commit_store(Store(), 0)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def load_spec(self, text: str) -> None:
        """Open a saved .mplot.json atomically after validation and rendering."""
        try:
            self._commit_store(Store(mp.from_json(text)), 0)
        except Exception as e:
            raise ValueError(f"invalid figure spec: {e}") from e

    def _render_preview(
        self, spec: FigureSpec, active_panel: int
    ) -> tuple[bytes, dict]:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mudplot._render import _preview_dpi, _save_figure, render

        assert_valid(spec)
        preview_spec = replace(spec, dpi=_preview_dpi(spec))
        fig = render(preview_spec)
        try:
            layout = self._extract_layout(spec, fig, active_panel)
            buf = io.BytesIO()
            _save_figure(fig, preview_spec, buf, "png")
            return buf.getvalue(), layout
        finally:
            plt.close(fig)

    def refresh(self) -> None:
        """Re-render the current figure, using a placeholder on failure."""
        import matplotlib.pyplot as plt

        spec = self.store.state
        try:
            self.png, self.layout = self._render_preview(spec, self.active_panel)
            self.error = None
            return
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            self.layout = {}

        fig = self._error_figure(self.error)
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150)
            self.png = buf.getvalue()
        finally:
            plt.close(fig)

    def export(self, fmt: str) -> bytes:
        """Render the current spec to a vector format at its exact configured
        size -- the whole point of the engine, so the editor must not only
        hand out the screen-resolution PNG preview.
        """
        if fmt not in ("pdf", "svg"):
            raise ValueError(f"unsupported export format {fmt!r}")
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mudplot._render import _save_figure, render

        spec = self.store.state
        assert_valid(spec)
        fig = render(spec, fmt=fmt)
        try:
            buf = io.BytesIO()
            _save_figure(fig, spec, buf, fmt)
        finally:
            plt.close(fig)
        return buf.getvalue()

    def _extract_layout(self, spec, fig, index: int) -> dict:
        if not spec.panels or not fig.axes:
            return {}
        index = min(index, len(spec.panels) - 1)
        # Not fig.axes[index]: twin (y2) and colorbar axes land in that list
        # too, so it stops matching panel order after the first one.
        ax = next(
            (a for a in fig.axes if getattr(a, "_mudplot_panel", None) == index), None
        )
        if ax is None:
            return {}
        panel = spec.panels[index]
        if panel.projection == "3d":
            return {"is_3d": True, "panel": index}
        bbox = ax.get_position()
        text_layers = [
            {"index": i, "type": layer.type, "at": list(layer.at)}
            for i, layer in enumerate(panel.layers)
            if layer.type in ("text", "annotate") and layer.at
        ]
        return {
            "is_3d": False,
            "panel": index,
            "panel_bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
            "xlim": list(ax.get_xlim()),
            "ylim": list(ax.get_ylim()),
            "xscale": ax.get_xscale(),
            "yscale": ax.get_yscale(),
            "text_layers": text_layers,
        }

    @staticmethod
    def _error_figure(message: str):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 2.2))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            f"render error:\n{message}",
            ha="center",
            va="center",
            wrap=True,
            fontsize=9,
            color="#8a2c22",
        )
        return fig


# -- form field -> Action translation --------------------------------------
@functools.lru_cache(maxsize=1)
def _docs_page() -> str:
    """The engine reference as a full HTML page (cached: static per process,
    like the rest of ``mudplot.capabilities()``-derived content).
    """
    return render_docs_page(markdown_to_html(mp.reference_markdown()))


def _float_field(fields: dict, name: str) -> float:
    try:
        return float(fields[name])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"{name} must be a number") from e


def _int_field(fields: dict, name: str, default=None) -> int:
    try:
        value = fields[name] if default is None else fields.get(name, default)
        return int(value)
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"{name} must be an integer") from e


def _limits_fields(fields: dict) -> list[float] | None:
    lo, hi = fields.get("lo"), fields.get("hi")
    if lo in (None, "") and hi in (None, ""):
        return None
    if lo in (None, "") or hi in (None, ""):
        raise ValueError("both lower and upper limits are required")
    return [_float_field(fields, "lo"), _float_field(fields, "hi")]


def _layer_from_json(fields: dict) -> LayerSpec:
    layer_type = fields.get("layer_type", "")
    if layer_type not in LAYER_TYPES:
        raise ValueError(
            f"unknown layer type {layer_type!r}; valid: {sorted(LAYER_TYPES)}"
        )
    try:
        values = _loads_json(fields.get("layer_json", "{}"))
    except (TypeError, ValueError, RecursionError) as e:
        raise ValueError(f"layer fields must be valid JSON: {e}") from e
    if not isinstance(values, dict):
        raise ValueError("layer fields must be a JSON object")

    allowed = {f.name for f in dataclass_fields(LayerSpec)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"unknown LayerSpec field(s): {sorted(unknown)}")
    missing = [
        name
        for name in LAYER_TYPES[layer_type]["required"]
        if name not in values or values[name] is None or values[name] == ""
    ]
    if missing:
        raise ValueError(f"{layer_type} requires field(s): {', '.join(missing)}")
    layer = LayerSpec.from_dict({**values, "type": layer_type})
    if not isinstance(layer, LayerSpec):  # defensive: generic SpecBase return
        raise TypeError("layer fields did not produce a LayerSpec")
    return layer


def _build_action(action_type: str, fields: dict, spec: FigureSpec) -> A.Action:
    if action_type == "load_sample":
        return A.SetData(sample_columns(fields["name"]))
    if action_type == "set_theme":
        return A.SetTheme(fields["name"])
    if action_type == "set_journal":
        name = fields.get("name", "none")
        return A.SetJournal(None if name == "none" else name)
    if action_type == "set_palette":
        return A.SetPalette(
            kind=fields.get("kind"),
            params={
                "hue_start": _float_field(fields, "hue_start"),
                "chroma": _float_field(fields, "chroma"),
                "lightness": _float_field(fields, "lightness"),
            },
        )
    if action_type == "add_layer_json":
        return A.AddLayer(
            _layer_from_json(fields), panel=_int_field(fields, "panel", 0)
        )
    if action_type == "add_layer":
        layer_type = fields["layer_type"]
        panel = _int_field(fields, "panel", 0)
        if layer_type in ("text", "annotate"):
            at = [_float_field(fields, "x"), _float_field(fields, "y")]
            return A.AddLayer(
                LayerSpec(
                    type=layer_type,
                    text=fields.get("text", ""),
                    at=at,
                    citation=fields.get("citation") or None,
                    href=fields.get("href") or None,
                ),
                panel=panel,
            )
        group = fields.get("group") or None
        return A.AddLayer(
            LayerSpec(
                type=layer_type,
                x=fields["x"],
                y=fields["y"],
                group=group,
                label=fields.get("label") or None,
                citation=fields.get("citation") or None,
                href=fields.get("href") or None,
            ),
            panel=panel,
        )
    if action_type == "remove_layer":
        return A.RemoveLayer(
            _int_field(fields, "layer_index"),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "set_layout":
        return A.SetLayout(_int_field(fields, "rows"), _int_field(fields, "cols"))
    if action_type == "set_projection":
        return A.SetProjection(
            fields.get("projection", "2d"),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "set_suptitle":
        return A.SetSuptitle(fields.get("text", ""))
    if action_type == "set_title":
        return A.SetTitle(
            fields.get("text", ""),
            panel=_int_field(fields, "panel", 0),
            citation=fields.get("citation") or None,
            href=fields.get("href") or None,
        )
    if action_type == "set_axis_label":
        return A.SetAxisLabel(
            fields["axis"],
            fields.get("text", ""),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "set_scale":
        return A.SetScale(
            fields["axis"],
            fields.get("scale", "linear"),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "set_limits":
        limits = _limits_fields(fields)
        lo, hi = limits if limits is not None else (None, None)
        return A.SetLimits(fields["axis"], lo, hi, panel=_int_field(fields, "panel", 0))
    if action_type == "set_secondary_axis":
        return A.SetSecondaryAxis(
            label=fields.get("label", ""),
            scale=fields.get("scale", "linear"),
            limits=_limits_fields(fields),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "clear_secondary_axis":
        return A.SetSecondaryAxis(label=None, panel=_int_field(fields, "panel", 0))
    if action_type == "set_z_axis":
        return A.SetZAxis(
            label=fields.get("label", ""),
            scale=fields.get("scale", "linear"),
            limits=_limits_fields(fields),
            panel=_int_field(fields, "panel", 0),
        )
    if action_type == "set_size":
        return A.SetSize(_float_field(fields, "width"), _float_field(fields, "height"))
    if action_type in ("set_legend_position", "reset_legend_position"):
        panel = _int_field(fields, "panel", 0)
        cur = spec.panels[panel].legend
        bbox = (
            None
            if action_type == "reset_legend_position"
            else [_float_field(fields, "x"), _float_field(fields, "y")]
        )
        return A.SetLegend(
            show=cur.show,
            title=cur.title,
            location=cur.location,
            frame=cur.frame,
            panel=panel,
            bbox_to_anchor=bbox,
        )
    if action_type in ("set_title_position", "reset_title_position"):
        panel = _int_field(fields, "panel", 0)
        position = (
            None
            if action_type == "reset_title_position"
            else [_float_field(fields, "x"), _float_field(fields, "y")]
        )
        return A.SetTitlePosition(position, panel=panel)
    if action_type == "set_layer_at":
        return A.SetLayerAt(
            _int_field(fields, "layer_index"),
            [_float_field(fields, "x"), _float_field(fields, "y")],
            panel=_int_field(fields, "panel", 0),
        )
    raise ValueError(f"unknown editor action type {action_type!r}")


def _parse_form(body: bytes) -> dict:
    parsed = parse_qs(body.decode("utf-8"), max_num_fields=1_000)
    return {k: v[0] for k, v in parsed.items()}


class _Handler(BaseHTTPRequestHandler):
    session: EditorSession  # set by make_server()

    def log_message(self, format: str, *args) -> None:  # quieter test/dev output
        pass

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", _CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _reject_untrusted_request(self, *, mutation: bool = False) -> bool:
        host = self.headers.get("Host", "")
        if not _is_loopback_host(host):
            self.send_error(403, "non-loopback Host is not allowed")
            return True
        if mutation:
            origin = self.headers.get("Origin")
            if self.headers.get("Sec-Fetch-Site") == "cross-site" or (
                origin is not None and origin != f"http://{host}"
            ):
                self.send_error(403, "cross-origin mutations are not allowed")
                return True
        return False

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect_home(self) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def _read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError) as e:
            raise ValueError("Content-Length must be an integer") from e
        if length < 0:
            raise ValueError("Content-Length must not be negative")
        if length > _MAX_BODY_BYTES:
            raise ValueError("request body exceeds the 16 MiB limit")
        return self.rfile.read(length) if length else b""

    def _respond_after_action(self, session: EditorSession) -> None:
        """htmx requests get the updated fragment back in-place (no full
        navigation); anything else (a plain form post, curl, urllib) falls
        back to the classic redirect-then-GET / round trip.
        """
        if self.headers.get("HX-Request") == "true":
            fragment = render_app_body(
                session.store.state,
                session.action_log(),
                session.layout,
                error=session.error,
                active_panel=session._clamp_panel(),
            )
            self._send_html(fragment)
        else:
            self._redirect_home()

    def do_GET(self) -> None:
        if self._reject_untrusted_request():
            return
        path = urlparse(self.path).path
        session = self.session
        if path == "/":
            with session.lock:
                page = render_page(
                    session.store.state,
                    session.action_log(),
                    session.layout,
                    error=session.error,
                    active_panel=session._clamp_panel(),
                )
            self._send_html(page)
        elif path == "/docs":
            self._send_html(_docs_page())
        elif path == "/static/htmx.min.js":
            self._send_bytes(_HTMX_JS, "application/javascript")
        elif path == "/static/editor.js":
            self._send_bytes(_DRAG_JS.encode("utf-8"), "application/javascript")
        elif path == "/fig.png":
            with session.lock:
                png = session.png
            self._send_bytes(png, "image/png")
        elif path in ("/fig.pdf", "/fig.svg"):
            fmt = path.rsplit(".", 1)[1]
            with session.lock:
                try:
                    data = session.export(fmt)
                except Exception as e:
                    self.send_error(400, f"{type(e).__name__}: {e}")
                    return
            ctype = "application/pdf" if fmt == "pdf" else "image/svg+xml"
            self._send_bytes(data, ctype)
        elif path == "/spec.json":
            with session.lock:
                text = mp.to_json(session.store.state)
            self._send_bytes(text.encode("utf-8"), "application/json")
        else:
            self.send_error(404, "not found")

    def do_POST(self) -> None:
        if self._reject_untrusted_request(mutation=True):
            return
        path = urlparse(self.path).path
        session = self.session
        try:
            fields = _parse_form(self._read_body())
        except (UnicodeDecodeError, ValueError) as e:
            self.send_error(400, str(e))
            return
        if path == "/action":
            action_type = fields.pop("type", "")
            with session.lock:
                try:
                    # Panel-scoped actions default to the selected panel, so
                    # every control doesn't have to carry it explicitly.
                    fields.setdefault("panel", str(session.active_panel))
                    action = _build_action(action_type, fields, session.store.state)
                    session.dispatch_safe(action)
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
                self._respond_after_action(session)
        elif path == "/action/raw":
            with session.lock:
                try:
                    data = _loads_json(fields.get("json", "{}"))
                    action = A.action_from_dict(data)
                    session.dispatch_safe(action)
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
                self._respond_after_action(session)
        elif path == "/undo":
            with session.lock:
                session.undo()
                self._respond_after_action(session)
        elif path == "/redo":
            with session.lock:
                session.redo()
                self._respond_after_action(session)
        elif path == "/open":
            with session.lock:
                try:
                    session.load_spec(fields.get("json", ""))
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
                self._respond_after_action(session)
        elif path == "/select-panel":
            with session.lock:
                try:
                    session.select_panel(_int_field(fields, "panel", 0))
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
                self._respond_after_action(session)
        elif path == "/reset":
            with session.lock:
                session.reset()
                self._respond_after_action(session)
        else:
            self.send_error(404, "not found")


class _IPv6ThreadingHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def make_server(
    host: str = "127.0.0.1", port: int = 8765, session: EditorSession | None = None
) -> ThreadingHTTPServer:
    """Build (but don't start) an editor HTTP server."""
    if not _is_loopback_address(host):
        raise ValueError("dashboard editor only accepts a loopback bind address")
    bound_session = session or EditorSession()
    handler_cls = type("_BoundHandler", (_Handler,), {"session": bound_session})
    server_type = _IPv6ThreadingHTTPServer if ":" in host else ThreadingHTTPServer
    return server_type((host, port), handler_cls)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the editor and block until interrupted (Ctrl+C)."""
    server = make_server(host, port)
    display_host = f"[{host}]" if ":" in host else host
    url = f"http://{display_host}:{port}/"
    print(f"mudplot editor running at {url} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
