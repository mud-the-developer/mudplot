"""A minimal local interactive editor server.

Deliberately dependency-light (stdlib ``http.server`` + ``mudplot[render]``,
no web framework): this is a *prototype* per the dashboard roadmap, meant to
exercise the engine's Store/actions/reducer through a real UI before a
Rust/htmx editor replaces it. There is exactly one piece of session state
(``EditorSession``) and it holds nothing the engine doesn't already model —
every edit is a dispatched ``Action``, same as the fluent API.

English by default (per project convention).
"""

from __future__ import annotations

import functools
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import mudplot as mp
from mudplot import actions as A
from mudplot.spec import LayerSpec
from mudplot.store import Store
from mudplot.validate import assert_valid

from .editor_view import render_docs_page, render_page
from .markdown_lite import markdown_to_html
from .samples import sample_columns

__all__ = ["EditorSession", "make_server", "serve"]


class EditorSession:
    """One editor's worth of state: a Store plus the last error, if any.

    A thin imperative-shell wrapper -- all real state lives in the Store's
    FigureSpec; this just remembers the most recent error message for
    display, and provides a lock since ThreadingHTTPServer handles each
    request on its own thread.
    """

    def __init__(self) -> None:
        self.store = Store()
        self.error: str | None = None
        self.lock = threading.Lock()

    def action_log(self) -> list[dict]:
        return [A.action_to_dict(a) for a in self.store.history]

    def dispatch_safe(self, action) -> None:
        try:
            self.store.dispatch(action)
            self.error = None
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"

    def render_png(self) -> bytes:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mudplot._render import render

        spec = self.store.state
        try:
            assert_valid(spec)
            fig = render(spec)
            self.error = None
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            fig = self._error_figure(self.error)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=spec.dpi if spec.panels else 150)
        plt.close(fig)
        return buf.getvalue()

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
        group = fields.get("group") or None
        return A.AddLayer(
            LayerSpec(
                type=fields["layer_type"], x=fields["x"], y=fields["y"], group=group
            )
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

    def _redirect_home(self) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        session = self.session
        if path == "/":
            with session.lock:
                page = render_page(
                    session.store.state, session.action_log(), error=session.error
                )
            self._send_html(page)
        elif path == "/docs":
            self._send_html(_docs_page())
        elif path == "/fig.png":
            with session.lock:
                png = session.render_png()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(png)
        elif path == "/spec.json":
            with session.lock:
                text = json.dumps(session.store.state.to_dict(), indent=2)
            data = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
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
            self._redirect_home()
        elif path == "/action/raw":
            fields = _parse_form(body)
            with session.lock:
                try:
                    data = json.loads(fields.get("json", "{}"))
                    action = A.action_from_dict(data)
                    session.dispatch_safe(action)
                except Exception as e:
                    session.error = f"{type(e).__name__}: {e}"
            self._redirect_home()
        elif path == "/undo":
            with session.lock:
                session.store.undo()
                session.error = None
            self._redirect_home()
        elif path == "/redo":
            with session.lock:
                session.store.redo()
                session.error = None
            self._redirect_home()
        elif path == "/reset":
            with session.lock:
                session.store = Store()
                session.error = None
            self._redirect_home()
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
