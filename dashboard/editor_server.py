"""A minimal local interactive editor server.

Deliberately dependency-light (stdlib ``http.server`` + ``mudplot[render]``,
plus a single vendored, dependency-free JS file for htmx partial-page
updates -- see ``dashboard/static/htmx.min.js``, 0BSD licensed): this is a
*prototype* per the dashboard roadmap, meant to exercise the engine's
Store/actions/reducer through a real UI before a Rust/htmx editor replaces
it. There is exactly one piece of session state (``EditorSession``) and it
holds nothing the engine doesn't already model — every edit is a
dispatched ``Action``, same as the fluent API.

English by default (per project convention).
"""

from __future__ import annotations

import functools
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import mudplot as mp
from mudplot import actions as A
from mudplot.spec import LayerSpec
from mudplot.store import Store
from mudplot.validate import assert_valid

from .editor_view import render_app_body, render_docs_page, render_page
from .markdown_lite import markdown_to_html
from .samples import sample_columns

__all__ = ["EditorSession", "make_server", "serve"]

_HTMX_JS = (Path(__file__).parent / "static" / "htmx.min.js").read_bytes()


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
        self.refresh()

    def action_log(self) -> list[dict]:
        return [A.action_to_dict(a) for a in self.store.history]

    def dispatch_safe(self, action) -> None:
        try:
            self.store.dispatch(action)
        except Exception as e:
            # Dispatch itself failed (e.g. bad action fields) -- the store's
            # state is untouched, so there's nothing new to render; refresh()
            # would just re-render the same (still valid) spec and silently
            # clear this error again.
            self.error = f"{type(e).__name__}: {e}"
            return
        self.refresh()

    def undo(self) -> None:
        self.store.undo()
        self.error = None
        self.refresh()

    def redo(self) -> None:
        self.store.redo()
        self.error = None
        self.refresh()

    def reset(self) -> None:
        self.store = Store()
        self.error = None
        self.refresh()

    def refresh(self) -> None:
        """Re-render the figure and cache both the PNG and the layout info
        (panel-0 axes bbox/limits/scale, draggable text-layer positions)
        the client uses to place handles -- one render pass serves both
        ``/fig.png`` and the fragment HTML, instead of re-rendering twice
        (once per request) with the risk of them disagreeing.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mudplot._render import render

        spec = self.store.state
        try:
            assert_valid(spec)
            fig = render(spec)
            self.error = None
            self.layout = self._extract_layout(spec, fig)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            fig = self._error_figure(self.error)
            self.layout = {}
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=spec.dpi if spec.panels else 150)
        plt.close(fig)
        self.png = buf.getvalue()

    @staticmethod
    def _extract_layout(spec, fig) -> dict:
        if not spec.panels or not fig.axes:
            return {}
        panel = spec.panels[0]
        ax = fig.axes[0]
        if panel.projection == "3d":
            return {"is_3d": True}
        bbox = ax.get_position()
        text_layers = [
            {"index": i, "type": layer.type, "at": list(layer.at)}
            for i, layer in enumerate(panel.layers)
            if layer.type in ("text", "annotate") and layer.at
        ]
        return {
            "is_3d": False,
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


def _build_action(action_type: str, fields: dict, spec=None):
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
                "hue_start": float(fields["hue_start"]),
                "chroma": float(fields["chroma"]),
                "lightness": float(fields["lightness"]),
            },
        )
    if action_type == "add_layer":
        layer_type = fields["layer_type"]
        if layer_type in ("text", "annotate"):
            at = [float(fields["x"]), float(fields["y"])]
            return A.AddLayer(
                LayerSpec(type=layer_type, text=fields.get("text", ""), at=at)
            )
        group = fields.get("group") or None
        return A.AddLayer(
            LayerSpec(type=layer_type, x=fields["x"], y=fields["y"], group=group)
        )
    if action_type == "remove_layer":
        return A.RemoveLayer(int(fields["layer_index"]))
    if action_type == "set_suptitle":
        return A.SetSuptitle(fields.get("text", ""))
    if action_type == "set_size":
        return A.SetSize(float(fields["width"]), float(fields["height"]))
    if action_type in ("set_legend_position", "reset_legend_position"):
        panel = int(fields.get("panel", 0))
        cur = spec.panels[panel].legend
        bbox = (
            None
            if action_type == "reset_legend_position"
            else [float(fields["x"]), float(fields["y"])]
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
        panel = int(fields.get("panel", 0))
        position = (
            None
            if action_type == "reset_title_position"
            else [float(fields["x"]), float(fields["y"])]
        )
        return A.SetTitlePosition(position, panel=panel)
    if action_type == "set_layer_at":
        return A.SetLayerAt(
            int(fields["layer_index"]),
            [float(fields["x"]), float(fields["y"])],
            panel=int(fields.get("panel", 0)),
        )
    raise ValueError(f"unknown editor action type {action_type!r}")


def _parse_form(body: bytes) -> dict:
    parsed = parse_qs(body.decode("utf-8"))
    return {k: v[0] for k, v in parsed.items()}


class _Handler(BaseHTTPRequestHandler):
    session: EditorSession  # set by make_server()

    def log_message(self, fmt, *args) -> None:  # quieter test/dev output
        pass

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str, *, no_store=False) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if no_store:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _redirect_home(self) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
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
            )
            self._send_html(fragment)
        else:
            self._redirect_home()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        session = self.session
        if path == "/":
            with session.lock:
                page = render_page(
                    session.store.state,
                    session.action_log(),
                    session.layout,
                    error=session.error,
                )
            self._send_html(page)
        elif path == "/docs":
            self._send_html(_docs_page())
        elif path == "/static/htmx.min.js":
            self._send_bytes(_HTMX_JS, "application/javascript")
        elif path == "/fig.png":
            with session.lock:
                png = session.png
            self._send_bytes(png, "image/png", no_store=True)
        elif path == "/spec.json":
            with session.lock:
                text = json.dumps(session.store.state.to_dict(), indent=2)
            self._send_bytes(text.encode("utf-8"), "application/json")
        else:
            self.send_error(404, "not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        session = self.session
        body = self._read_body()
        if path == "/action":
            fields = _parse_form(body)
            action_type = fields.pop("type", "")
            with session.lock:
                try:
                    action = _build_action(action_type, fields, session.store.state)
                    session.dispatch_safe(action)
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
                self._respond_after_action(session)
        elif path == "/action/raw":
            fields = _parse_form(body)
            with session.lock:
                try:
                    data = json.loads(fields.get("json", "{}"))
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
        elif path == "/reset":
            with session.lock:
                session.reset()
                self._respond_after_action(session)
        else:
            self.send_error(404, "not found")


def make_server(
    host: str = "127.0.0.1", port: int = 8765, session: EditorSession | None = None
) -> ThreadingHTTPServer:
    """Build (but don't start) an editor HTTP server."""
    bound_session = session or EditorSession()
    handler_cls = type("_BoundHandler", (_Handler,), {"session": bound_session})
    server = ThreadingHTTPServer((host, port), handler_cls)
    return server


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the editor and block until interrupted (Ctrl+C)."""
    server = make_server(host, port)
    url = f"http://{host}:{port}/"
    print(f"mudplot editor running at {url} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
