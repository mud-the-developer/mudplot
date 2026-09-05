"""Tests for the dashboard's interactive editor (prototype).

Split into pure view-layer unit tests (no server) and integration tests that
spin up a real (ephemeral-port) HTTP server via ``make_server()``.
"""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import matplotlib
import pytest

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dashboard.editor_server import EditorSession, _build_action, make_server
from dashboard.editor_view import render_docs_page, render_page
from dashboard.samples import SAMPLES, sample_columns
from mudplot import actions as A
from mudplot.spec import FigureSpec, LegendSpec
from mudplot.store import Store

# --------------------------------------------------------------------------
# pure view-layer tests
# --------------------------------------------------------------------------


def test_render_page_contains_core_sections():
    html = render_page(FigureSpec(), [])
    for text in (
        "mudplot editor",
        "Sample data",
        "Theme &amp; journal",
        "Palette",
        "Add layer",
        "History",
        "Advanced",
        "Export",
        "Preview",
        "Action log",
    ):
        assert text in html


def test_render_page_shows_error_banner():
    html = render_page(FigureSpec(), [], error="something went wrong")
    assert 'class="error"' in html
    assert "something went wrong" in html


def test_render_page_no_error_banner_when_none():
    html = render_page(FigureSpec(), [])
    assert 'class="error"' not in html


def test_render_page_escapes_untrusted_text():
    spec = FigureSpec()
    spec.suptitle = "<script>alert(1)</script>"
    html = render_page(spec, [])
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_page_lists_available_columns():
    spec = FigureSpec()
    spec.data.columns = {"foo": [1, 2], "bar": [3, 4]}
    html = render_page(spec, [])
    assert "foo" in html
    assert "bar" in html


def test_render_page_shows_action_log_entries():
    log = [{"type": "SetTitle", "text": "hi"}]
    html = render_page(FigureSpec(), log)
    assert "SetTitle" in html


def test_render_page_lists_current_layers_with_remove_buttons():
    from mudplot.spec import LayerSpec

    spec = FigureSpec()
    spec.data.columns = {"x": [1, 2], "y": [3, 4]}
    spec.panels[0].layers = [LayerSpec(type="line", x="x", y="y")]
    html = render_page(spec, [])
    assert "Current layers" in html
    assert "layer-row" in html
    assert "remove_layer" in html


def test_render_page_shows_no_layers_hint_when_empty():
    html = render_page(FigureSpec(), [])
    assert "(no layers yet)" in html


def test_render_page_has_editor_tab_active_and_links_docs():
    html = render_page(FigureSpec(), [])
    assert 'class="navtab active" href="/"' in html
    assert 'href="/docs"' in html


def test_render_docs_page_has_docs_tab_active_and_links_editor():
    html = render_docs_page("<h2>hello</h2>")
    assert 'class="navtab active" href="/docs"' in html
    assert 'href="/">Editor' in html
    assert "<h2>hello</h2>" in html


def test_render_page_no_legend_handle_without_explicit_position():
    spec = FigureSpec()
    spec.data.columns = {"x": [1, 2], "y": [3, 4]}
    html = render_page(spec, [])
    assert 'id="legend-handle"' not in html


def test_render_page_shows_legend_handle_at_explicit_position():
    spec = FigureSpec()
    spec.panels[0].legend = LegendSpec(bbox_to_anchor=[0.25, 0.75])
    html = render_page(spec, [])
    assert 'id="legend-handle"' in html
    assert 'data-x="0.25"' in html
    assert 'data-y="0.75"' in html
    assert "left:25%" in html
    assert "top:25%" in html  # CSS top is flipped: (1 - 0.75) * 100


def test_samples_are_valid_columns():
    for name in SAMPLES:
        cols = sample_columns(name)
        lengths = {len(v) for v in cols.values()}
        assert len(lengths) == 1  # row-aligned


def test_sample_columns_unknown_raises():
    with pytest.raises(ValueError, match="unknown sample"):
        sample_columns("does-not-exist")


def test_build_action_set_legend_position_preserves_other_legend_fields():
    spec = FigureSpec()
    spec.panels[0].legend = LegendSpec(
        title="series", location="upper left", frame=True
    )
    action = _build_action(
        "set_legend_position", {"x": "0.3", "y": "0.4", "panel": "0"}, spec
    )
    assert action == A.SetLegend(
        show=True,
        title="series",
        location="upper left",
        frame=True,
        panel=0,
        bbox_to_anchor=[0.3, 0.4],
    )


def test_build_action_reset_legend_position_clears_bbox_only():
    spec = FigureSpec()
    spec.panels[0].legend = LegendSpec(
        title="series", bbox_to_anchor=[0.3, 0.4], location="upper left"
    )
    action = _build_action("reset_legend_position", {"panel": "0"}, spec)
    assert action.bbox_to_anchor is None
    assert action.title == "series"
    assert action.location == "upper left"


# --------------------------------------------------------------------------
# EditorSession (no HTTP)
# --------------------------------------------------------------------------


def test_session_dispatch_safe_records_error_without_raising():
    session = EditorSession()
    session.dispatch_safe(A.SetTheme("not-a-real-theme"))
    assert session.error is not None
    assert "not-a-real-theme" in session.error


def test_session_dispatch_safe_clears_error_on_success():
    session = EditorSession()
    session.dispatch_safe(A.SetTheme("not-a-real-theme"))
    assert session.error is not None
    session.dispatch_safe(A.SetSuptitle("ok"))
    assert session.error is None


def test_session_render_png_returns_bytes_for_empty_figure():
    session = EditorSession()
    png = session.render_png()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_session_render_png_shows_placeholder_on_invalid_spec():
    session = EditorSession()
    session.store = Store(FigureSpec(panels=[]))  # invalid: no panels
    png = session.render_png()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert session.error is not None


# --------------------------------------------------------------------------
# integration tests: a real (ephemeral) HTTP server
# --------------------------------------------------------------------------


@pytest.fixture
def running_server():
    server = make_server(port=0)  # OS-assigned ephemeral port
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def _post(url: str, fields: dict) -> int:
    data = urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        return r.status


def test_get_home_page(running_server):
    with urllib.request.urlopen(running_server + "/") as r:
        assert r.status == 200
        assert b"mudplot editor" in r.read()


def test_get_unknown_path_is_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(running_server + "/nope")
    assert exc.value.code == 404


def test_load_sample_then_add_layer_then_render(running_server):
    assert (
        _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
        == 200
    )
    assert (
        _post(
            running_server + "/action",
            {
                "type": "add_layer",
                "layer_type": "line",
                "x": "x",
                "y": "y",
                "group": "series",
            },
        )
        == 200
    )
    with urllib.request.urlopen(running_server + "/fig.png") as r:
        assert r.status == 200
        assert r.headers.get("Content-Type") == "image/png"
        png = r.read()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_spec_json_reflects_dispatched_actions(running_server):
    _post(running_server + "/action", {"type": "set_suptitle", "text": "hello"})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["suptitle"] == "hello"


def test_set_theme_and_palette(running_server):
    assert (
        _post(running_server + "/action", {"type": "set_theme", "name": "boxed"}) == 200
    )
    assert (
        _post(
            running_server + "/action",
            {
                "type": "set_palette",
                "kind": "sequential",
                "hue_start": "10",
                "chroma": "40",
                "lightness": "50",
            },
        )
        == 200
    )
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["theme"]["name"] == "boxed"
    assert spec["theme"]["palette"]["kind"] == "sequential"


def test_undo_redo_via_http(running_server):
    _post(running_server + "/action", {"type": "set_suptitle", "text": "v1"})
    _post(running_server + "/action", {"type": "set_suptitle", "text": "v2"})
    _post(running_server + "/undo", {})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        assert json.loads(r.read())["suptitle"] == "v1"
    _post(running_server + "/redo", {})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        assert json.loads(r.read())["suptitle"] == "v2"


def test_add_then_remove_layer_via_http(running_server):
    _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
    _post(
        running_server + "/action",
        {"type": "add_layer", "layer_type": "line", "x": "x", "y": "y", "group": ""},
    )
    _post(
        running_server + "/action",
        {"type": "add_layer", "layer_type": "scatter", "x": "x", "y": "y", "group": ""},
    )
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert [ly["type"] for ly in spec["panels"][0]["layers"]] == ["line", "scatter"]

    _post(running_server + "/action", {"type": "remove_layer", "layer_index": "0"})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert [ly["type"] for ly in spec["panels"][0]["layers"]] == ["scatter"]


def test_remove_layer_out_of_range_shows_error_not_crash(running_server):
    status = _post(
        running_server + "/action", {"type": "remove_layer", "layer_index": "9"}
    )
    assert status == 200
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()


def test_reset_clears_state(running_server):
    _post(running_server + "/action", {"type": "set_suptitle", "text": "temp"})
    _post(running_server + "/reset", {})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        assert json.loads(r.read())["suptitle"] == ""


def test_raw_json_action(running_server):
    payload = json.dumps({"type": "SetTitle", "text": "raw-title"})
    _post(running_server + "/action/raw", {"json": payload})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["title"] == "raw-title"


def test_docs_route_serves_engine_reference(running_server):
    with urllib.request.urlopen(running_server + "/docs") as r:
        assert r.status == 200
        body = r.read().decode()
    assert "mudplot" in body
    assert "Layers" in body  # from mp.reference_markdown()
    assert 'class="navtab active" href="/docs"' in body


def test_legend_drag_then_reset_via_http(running_server):
    _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
    _post(
        running_server + "/action",
        {
            "type": "add_layer",
            "layer_type": "line",
            "x": "x",
            "y": "y",
            "group": "series",
        },
    )
    _post(
        running_server + "/action",
        {"type": "set_legend_position", "x": "0.2", "y": "0.9", "panel": "0"},
    )
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["legend"]["bbox_to_anchor"] == [0.2, 0.9]
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'id="legend-handle"' in r.read()

    _post(running_server + "/action", {"type": "reset_legend_position", "panel": "0"})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["legend"]["bbox_to_anchor"] is None
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'id="legend-handle"' not in r.read()


def test_invalid_action_does_not_crash_server(running_server):
    # missing required fields for add_layer
    status = _post(running_server + "/action", {"type": "add_layer"})
    assert status == 200  # redirect handled, error recorded not raised
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()


def test_malformed_raw_json_does_not_crash_server(running_server):
    status = _post(running_server + "/action/raw", {"json": "not json"})
    assert status == 200
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()
