"""Tests for the dashboard's interactive editor.

Split into pure view-layer unit tests (no server) and integration tests that
spin up a real (ephemeral-port) HTTP server via ``make_server()``.
"""

import http.client
import json
import socket
import struct
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode, urlparse

import matplotlib
import pytest

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dashboard.editor_server import EditorSession, _build_action, make_server
from dashboard.editor_view import render_app_body, render_docs_page, render_page
from dashboard.samples import SAMPLES, sample_columns
from mudplot import actions as A
from mudplot.capabilities import LAYER_TYPES
from mudplot.spec import FigureSpec, LayerSpec, LegendSpec
from mudplot.store import Store

# --------------------------------------------------------------------------
# pure view-layer tests
# --------------------------------------------------------------------------


def test_label_controls_preserve_position_and_allow_clearing():
    store = Store()
    store.dispatch(A.SetTitlePosition([0.2, 0.8]))
    for kind, fields in (
        ("set_title", {"text": 'Title <&"'}),
        ("set_axis_label", {"axis": "x", "text": "Time (s)"}),
        ("set_axis_label", {"axis": "y", "text": "Amplitude"}),
    ):
        store.dispatch(_build_action(kind, fields, store.state))
    panel = store.state.panels[0]
    assert panel.title_position == [0.2, 0.8]
    assert panel.x.label == "Time (s)"
    assert panel.y.label == "Amplitude"
    page = render_page(store.state, [])
    assert "Title &lt;&amp;&quot;" in page
    # labels must stay bound to their control (screen readers, and the
    # browser tests' get_by_label locators, both depend on it)
    assert "<label>X-axis label<input" in page
    store.dispatch(_build_action("set_title", {}, store.state))
    assert store.state.panels[0].title == ""


def test_vector_export_uses_configured_size_and_rejects_bad_format():
    session = EditorSession()
    session.dispatch_safe(A.SetData({"x": [1, 2, 3], "y": [1, 4, 9]}))
    session.dispatch_safe(
        A.AddLayer(
            LayerSpec(
                type="line",
                x="x",
                y="y",
                label="paper",
                href="https://example.org/paper",
            )
        )
    )
    session.dispatch_safe(A.SetSize(4.0, 3.0))
    assert session.error is None
    assert session.export("pdf").startswith(b"%PDF")
    svg_bytes = session.export("svg")
    assert svg_bytes == session.export("svg")
    svg = svg_bytes.decode()
    assert "<svg" in svg
    assert "https://example.org/paper" in svg
    # exact configured physical size, not a cropped/expanded one
    assert 'width="288pt"' in svg and 'height="216pt"' in svg
    with pytest.raises(ValueError):
        session.export("jpeg")

    session.dispatch_safe(A.SetSize(100, 50))
    session.dispatch_safe(A.SetDpi(2400))
    assert struct.unpack(">II", session.png[16:24]) == (2000, 1000)
    assert session.store.state.dpi == 2400


def test_collapsible_sections_are_keyed_for_state_restore():
    # The swap handler restores <details> by data-key, so every collapsible
    # section must carry one (summary text alone is unstable: the history
    # label embeds a live action count).
    body = render_app_body(FigureSpec(), [])
    assert body.count("<details") == body.count("data-key=")
    page = render_page(FigureSpec(), [])
    for key in ("samples", "advanced", "history"):
        assert f'data-key="{key}"' in page


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
        "Action history",
    ):
        assert text in html


def test_any_layer_form_is_driven_by_every_registered_layer_type():
    page = render_page(FigureSpec(), [])
    assert 'name="layer_json"' in page
    for layer_type in LAYER_TYPES:
        assert f'<option value="{layer_type}">' in page


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
    spec.data.columns = {'<img src=x onerror="alert(2)">': [1]}
    html = render_page(spec, [])
    assert "<script>alert(1)</script>" not in html
    assert '<img src=x onerror="alert(2)">' not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
    assert '"allowScriptTags":false' in html


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
    assert 'class="drag-handle legend"' not in html


def test_render_page_shows_legend_handle_at_explicit_position():
    spec = FigureSpec()
    spec.panels[0].legend = LegendSpec(bbox_to_anchor=[0.25, 0.75])
    html = render_page(spec, [])
    assert 'class="drag-handle legend"' in html
    assert 'data-imgx="0.25"' in html
    assert 'data-imgy="0.75"' in html
    assert "left:25%" in html
    assert "top:25%" in html  # CSS top is flipped: (1 - 0.75) * 100


def test_render_page_legend_handle_needs_no_layout_info():
    # unlike title/text-layer handles, the legend is figure-fraction and
    # doesn't depend on the panel-0 axes bbox being known.
    spec = FigureSpec()
    spec.panels[0].legend = LegendSpec(bbox_to_anchor=[0.1, 0.1])
    html = render_page(spec, [], layout={})
    assert 'class="drag-handle legend"' in html


def test_render_page_title_handle_needs_panel_bbox_from_layout():
    from mudplot.spec import PanelSpec

    spec = FigureSpec()
    spec.panels[0] = PanelSpec(title="Hi", title_position=[0.5, 0.9])
    assert 'class="drag-handle title"' not in render_page(spec, [], layout={})
    html = render_page(
        spec, [], layout={"panel_bbox": [0.1, 0.1, 0.9, 0.9], "is_3d": False}
    )
    assert 'class="drag-handle title"' in html
    # axes-fraction 0.5 -> figure-fraction 0.1 + 0.5*(0.9-0.1) = 0.5
    assert 'data-imgx="0.5"' in html


def test_render_page_no_title_handle_without_title_text():
    from mudplot.spec import PanelSpec

    spec = FigureSpec()
    spec.panels[0] = PanelSpec(title="", title_position=[0.5, 0.9])
    html = render_page(
        spec, [], layout={"panel_bbox": [0.1, 0.1, 0.9, 0.9], "is_3d": False}
    )
    assert 'class="drag-handle title"' not in html


def test_render_page_layer_at_handle_uses_data_coordinate_mapping():
    from mudplot.spec import LayerSpec as LS
    from mudplot.spec import PanelSpec

    spec = FigureSpec()
    spec.data.columns = {"x": [0, 1], "y": [0, 1]}
    spec.panels[0] = PanelSpec(layers=[LS(type="text", text="n", at=[5.0, 0.0])])
    layout = {
        "is_3d": False,
        "panel_bbox": [0.0, 0.0, 1.0, 1.0],
        "xlim": [0.0, 10.0],
        "ylim": [-1.0, 1.0],
        "xscale": "linear",
        "yscale": "linear",
        "text_layers": [{"index": 0, "type": "text", "at": [5.0, 0.0]}],
    }
    html = render_page(spec, [], layout)
    assert 'class="drag-handle layer-at"' in html
    assert 'data-imgx="0.5"' in html  # (5-0)/(10-0)
    assert 'data-imgy="0.5"' in html  # (0-(-1))/(1-(-1))
    assert 'data-field2="layer_index=0"' in html


def test_render_page_no_handles_for_3d_layout():
    from mudplot.spec import LegendSpec as LG
    from mudplot.spec import PanelSpec

    spec = FigureSpec()
    spec.panels[0] = PanelSpec(
        title="Hi", title_position=[0.5, 0.9], legend=LG(bbox_to_anchor=[0.1, 0.1])
    )
    html = render_page(spec, [], layout={"is_3d": True})
    # legend still draggable (figure-fraction, independent of the axes)...
    assert 'class="drag-handle legend"' in html
    # ...but title needs the (unavailable, for 3-D) axes bbox
    assert 'class="drag-handle title"' not in html


def test_samples_are_valid_columns():
    for name in SAMPLES:
        cols = sample_columns(name)
        lengths = {len(v) for v in cols.values()}
        assert len(lengths) == 1  # row-aligned


def test_sample_columns_unknown_raises():
    with pytest.raises(ValueError, match="unknown sample"):
        sample_columns("does-not-exist")


def test_projection_control_targets_the_selected_panel():
    spec = FigureSpec()
    action = _build_action("set_projection", {"projection": "3d", "panel": "0"}, spec)
    assert action == A.SetProjection("3d", panel=0)
    page = render_page(spec, [])
    assert 'name="projection"' in page
    assert '<option value="polar">polar</option>' in page


def test_axis_controls_build_scale_limits_secondary_and_z_actions():
    spec = FigureSpec()
    assert _build_action(
        "set_scale", {"axis": "x", "scale": "log", "panel": "0"}, spec
    ) == A.SetScale("x", "log", panel=0)
    assert _build_action(
        "set_limits", {"axis": "y", "lo": "-1", "hi": "2", "panel": "0"}, spec
    ) == A.SetLimits("y", -1.0, 2.0, panel=0)
    assert _build_action(
        "set_limits", {"axis": "y", "lo": "", "hi": "", "panel": "0"}, spec
    ) == A.SetLimits("y", None, None, panel=0)
    assert _build_action(
        "set_secondary_axis",
        {"label": "Y2", "scale": "log", "lo": "1", "hi": "10"},
        spec,
    ) == A.SetSecondaryAxis("Y2", "log", [1.0, 10.0], panel=0)
    assert _build_action("clear_secondary_axis", {}, spec) == A.SetSecondaryAxis(
        None, panel=0
    )
    assert _build_action(
        "set_z_axis",
        {"label": "Z", "scale": "linear", "lo": "", "hi": ""},
        spec,
    ) == A.SetZAxis("Z", "linear", None, panel=0)


def test_axis_controls_render_for_2d_and_z_controls_render_only_for_3d():
    spec = FigureSpec()
    page_2d = render_page(spec, [])
    assert "Axis scales &amp; limits" in page_2d
    assert 'value="set_secondary_axis"' in page_2d
    assert 'value="set_z_axis"' not in page_2d
    spec.panels[0].projection = "3d"
    page_3d = render_page(spec, [])
    assert 'value="set_z_axis"' in page_3d
    assert 'value="set_secondary_axis"' not in page_3d
    spec.panels[0].projection = "polar"
    page_polar = render_page(spec, [])
    assert 'value="set_z_axis"' not in page_polar
    assert 'value="set_secondary_axis"' not in page_polar


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
    assert isinstance(action, A.SetLegend)
    assert action.bbox_to_anchor is None
    assert action.title == "series"
    assert action.location == "upper left"


# --------------------------------------------------------------------------
# EditorSession (no HTTP)
# --------------------------------------------------------------------------


_REQUIRED_LAYER_VALUE = {
    "x": "x",
    "y": "y",
    "y2": "y2",
    "z": "z",
    "u": "u",
    "v": "v",
    "group": "group",
    "value": 0.0,
    "text": "note",
    "at": [0.0, 0.0],
    "matrix": "matrix",
}


@pytest.mark.parametrize("layer_type", sorted(LAYER_TYPES))
def test_build_action_accepts_every_registered_layer_type_as_json(layer_type):
    values = {
        name: _REQUIRED_LAYER_VALUE[name]
        for name in LAYER_TYPES[layer_type]["required"]
    }
    action = _build_action(
        "add_layer_json",
        {"layer_type": layer_type, "layer_json": json.dumps(values)},
        FigureSpec(),
    )
    assert isinstance(action, A.AddLayer)
    assert action.layer.type == layer_type
    for name, value in values.items():
        assert getattr(action.layer, name) == value


def test_build_action_rejects_unknown_json_layer_field():
    with pytest.raises(ValueError, match="unknown LayerSpec field"):
        _build_action(
            "add_layer_json",
            {
                "layer_type": "line",
                "layer_json": json.dumps({"x": "x", "y": "y", "typo": 1}),
            },
            FigureSpec(),
        )


def test_build_action_reports_invalid_numeric_field():
    with pytest.raises(ValueError, match="width must be a number"):
        _build_action("set_size", {"width": "wide", "height": "2"}, FigureSpec())


def test_session_rejects_invalid_or_unrenderable_changes_atomically(monkeypatch):
    session = EditorSession()
    session.dispatch_safe(A.SetSuptitle("keep"))
    before = session.store.state.to_dict()
    before_history = session.store.history
    before_png = session.png

    session.dispatch_safe(A.AddLayer(LayerSpec(type="line", x="missing", y="y")))
    assert session.error is not None
    assert session.store.state.to_dict() == before
    assert session.store.history == before_history

    def fail_render(*_args):
        raise RuntimeError("render failed")

    monkeypatch.setattr(session, "_render_preview", fail_render)
    session.dispatch_safe(A.SetSuptitle("must not commit"))
    assert "render failed" in (session.error or "")
    assert session.store.state.to_dict() == before
    assert session.store.history == before_history
    assert session.png == before_png

    with pytest.raises(ValueError, match="render failed"):
        session.load_spec(json.dumps(FigureSpec(suptitle="must not import").to_dict()))
    for operation in (session.undo, session.redo, session.reset):
        operation()
        assert session.store.state.to_dict() == before
        assert session.store.history == before_history
        assert session.png == before_png


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


def test_session_png_cached_after_construction():
    session = EditorSession()
    assert session.png[:8] == b"\x89PNG\r\n\x1a\n"


def test_session_refresh_shows_placeholder_on_invalid_spec():
    session = EditorSession()
    session.store = Store(FigureSpec(panels=[]))  # invalid: no panels
    session.refresh()
    assert session.png[:8] == b"\x89PNG\r\n\x1a\n"
    assert session.error is not None
    assert session.layout == {}


def test_session_layout_reflects_panel_bbox_and_limits_after_dispatch():
    session = EditorSession()
    session.dispatch_safe(A.SetData({"x": [1, 2, 3], "y": [1, 4, 9]}))
    session.dispatch_safe(
        A.AddLayer(LayerSpec(type="line", x="x", y="y")),
    )
    assert session.error is None
    assert session.layout["is_3d"] is False
    assert len(session.layout["panel_bbox"]) == 4
    assert session.layout["xlim"][0] < 1 and session.layout["xlim"][1] > 3
    assert session.layout["text_layers"] == []


def test_session_layout_lists_text_and_annotate_layers():
    session = EditorSession()
    session.dispatch_safe(A.SetData({"x": [1, 2], "y": [1, 2]}))
    session.dispatch_safe(A.AddLayer(LayerSpec(type="line", x="x", y="y")))
    session.dispatch_safe(A.AddLayer(LayerSpec(type="text", text="n", at=[1.5, 1.5])))
    assert session.layout["text_layers"] == [
        {"index": 1, "type": "text", "at": [1.5, 1.5]}
    ]


def test_session_layout_empty_for_3d_panel():
    from mudplot.spec import PanelSpec

    session = EditorSession()
    session.store = Store(FigureSpec(panels=[PanelSpec(projection="3d")]))
    session.dispatch_safe(A.SetData({"x": [1], "y": [1], "z": [1]}))
    session.dispatch_safe(A.AddLayer(LayerSpec(type="line3d", x="x", y="y", z="z")))
    assert session.layout == {"is_3d": True, "panel": 0}


# --------------------------------------------------------------------------
# integration tests: a real (ephemeral) HTTP server
# --------------------------------------------------------------------------


def test_server_rejects_non_loopback_bind_before_creating_a_session():
    with pytest.raises(ValueError, match="loopback"):
        make_server("0.0.0.0", 0)


def test_server_supports_ipv6_loopback():
    if not socket.has_ipv6:
        pytest.skip("Python has no IPv6 support")
    server = make_server("::1", 0)
    try:
        assert server.address_family == socket.AF_INET6
    finally:
        server.server_close()


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
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Cache-Control"] == "no-store"
        assert r.headers["Cross-Origin-Resource-Policy"] == "same-origin"
        csp = r.headers["Content-Security-Policy"]
        assert "object-src 'none'" in csp
        assert "script-src 'self';" in csp
        assert "script-src 'self' 'unsafe-inline'" not in csp
        assert b"mudplot editor" in r.read()


def test_non_loopback_or_malformed_host_is_rejected(running_server):
    for host in (
        "attacker.example",
        "127.0.0.1:invalid-port",
        "user@127.0.0.1",
        "127.0.0.1/path",
        "127.0.0.1?query",
    ):
        request = urllib.request.Request(
            running_server + "/spec.json", headers={"Host": host}
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 403


def test_cross_origin_mutation_is_rejected_without_changing_state(running_server):
    data = urlencode({"type": "set_suptitle", "text": "CSRF"}).encode()
    request = urllib.request.Request(
        running_server + "/action",
        data=data,
        headers={"Origin": "https://attacker.example"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(request)
    assert exc.value.code == 403
    with urllib.request.urlopen(running_server + "/spec.json") as response:
        assert json.load(response)["suptitle"] == ""


def test_get_unknown_path_is_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(running_server + "/nope")
    assert exc.value.code == 404


def test_form_field_count_is_bounded(running_server):
    data = urlencode({str(index): "x" for index in range(1_001)}).encode()
    request = urllib.request.Request(running_server + "/action", data=data)
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(request)
    assert exc.value.code == 400


@pytest.mark.parametrize("length", ["invalid", str(16 * 1024 * 1024 + 1)])
def test_invalid_or_oversized_content_length_returns_400(running_server, length):
    parsed = urlparse(running_server)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port)
    try:
        connection.putrequest("POST", "/action")
        connection.putheader("Content-Length", length)
        connection.endheaders()
        assert connection.getresponse().status == 400
    finally:
        connection.close()


def test_add_any_layer_form_dispatches_valid_layer(running_server):
    assert (
        _post(
            running_server + "/action",
            {
                "type": "add_layer_json",
                "layer_type": "hline",
                "layer_json": json.dumps({"value": 0.5, "label": "Threshold"}),
            },
        )
        == 200
    )
    with urllib.request.urlopen(running_server + "/spec.json") as response:
        layer = json.loads(response.read())["panels"][0]["layers"][0]
    assert layer["type"] == "hline"
    assert layer["value"] == 0.5


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


def test_vector_export_routes_serve_downloadable_files(running_server):
    _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
    _post(
        running_server + "/action",
        {"type": "add_layer", "layer_type": "line", "x": "x", "y": "y", "group": ""},
    )
    for path, ctype, magic in (
        ("/fig.pdf", "application/pdf", b"%PDF"),
        ("/fig.svg", "image/svg+xml", b"<?xml"),
    ):
        with urllib.request.urlopen(running_server + path) as r:
            assert r.status == 200
            assert r.headers["Content-Type"] == ctype
            assert r.read().startswith(magic)


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
        assert b'class="drag-handle legend"' in r.read()

    _post(running_server + "/action", {"type": "reset_legend_position", "panel": "0"})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["legend"]["bbox_to_anchor"] is None
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="drag-handle legend"' not in r.read()


def test_invalid_action_does_not_crash_server(running_server):
    # missing required fields for add_layer
    status = _post(running_server + "/action", {"type": "add_layer"})
    assert status == 200  # redirect handled, error recorded not raised
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        '{"type":"SetSize","width":NaN,"height":2}',
        '{"type":"SetSize","width":1e400,"height":2}',
        r'{"type":"SetTitle","text":"\ud800","panel":0}',
    ],
)
def test_malformed_raw_json_does_not_crash_server(running_server, payload):
    status = _post(running_server + "/action/raw", {"json": payload})
    assert status == 200
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()


# --------------------------------------------------------------------------
# htmx: fragment responses (no redirect) + title/text-layer drag handles
# --------------------------------------------------------------------------


def _hx_post(url: str, fields: dict) -> bytes:
    data = urlencode(fields).encode()
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"HX-Request": "true"}
    )
    with urllib.request.urlopen(req) as r:
        assert r.status == 200
        body = r.read()
    assert body.startswith(b'<aside class="inspector"')
    assert b'id="app-body"' not in body  # innerHTML must not nest the target
    return body


def test_htmx_request_gets_fragment_not_redirect(running_server):
    body = _hx_post(running_server + "/action", {"type": "set_suptitle", "text": "hi"})
    assert b"<!doctype html>" not in body
    assert b"hi" in body


def test_htmx_undo_redo_reset_return_fragments(running_server):
    _hx_post(running_server + "/action", {"type": "set_suptitle", "text": "v1"})
    body = _hx_post(running_server + "/undo", {})
    assert b"<!doctype html>" not in body
    _hx_post(running_server + "/redo", {})
    body = _hx_post(running_server + "/reset", {})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        assert json.loads(r.read())["suptitle"] == ""


def test_static_editor_scripts_are_served(running_server):
    for path in ("/static/htmx.min.js", "/static/editor.js"):
        with urllib.request.urlopen(running_server + path) as r:
            assert r.status == 200
            assert r.headers.get("Content-Type") == "application/javascript"
            script = r.read()
            assert len(script) > 1000
            if path.endswith("htmx.min.js"):
                assert b'version:"1.9.12"' in script


def test_title_position_drag_handle_appears_and_moves_title_via_http(running_server):
    _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
    _post(
        running_server + "/action",
        {"type": "add_layer", "layer_type": "line", "x": "x", "y": "y", "group": ""},
    )
    payload = json.dumps({"type": "SetTitle", "text": "Hello", "panel": 0})
    _post(running_server + "/action/raw", {"json": payload})
    body = _hx_post(
        running_server + "/action",
        {"type": "set_title_position", "x": "0.5", "y": "0.9", "panel": "0"},
    ).decode()
    assert 'class="drag-handle title"' in body
    assert 'data-bbox="[' in body

    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["title_position"] == [0.5, 0.9]

    _post(running_server + "/action", {"type": "reset_title_position", "panel": "0"})
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="drag-handle title"' not in r.read()


def test_annotation_layer_gets_a_draggable_handle_with_data_coords(running_server):
    _post(running_server + "/action", {"type": "load_sample", "name": "sine"})
    _post(
        running_server + "/action",
        {"type": "add_layer", "layer_type": "line", "x": "x", "y": "y", "group": ""},
    )
    body = _hx_post(
        running_server + "/action",
        {
            "type": "add_layer",
            "layer_type": "text",
            "text": "note",
            "x": "3",
            "y": "0.5",
        },
    ).decode()
    assert 'class="drag-handle layer-at"' in body
    assert 'data-xlim="[' in body
    assert 'data-field2="layer_index=1"' in body

    _hx_post(
        running_server + "/action",
        {
            "type": "set_layer_at",
            "panel": "0",
            "layer_index": "1",
            "x": "5",
            "y": "0.2",
        },
    )
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        spec = json.loads(r.read())
    assert spec["panels"][0]["layers"][1]["at"] == [5.0, 0.2]


def test_set_layer_at_out_of_range_shows_error_not_crash(running_server):
    status = _post(
        running_server + "/action",
        {
            "type": "set_layer_at",
            "panel": "0",
            "layer_index": "9",
            "x": "1",
            "y": "1",
        },
    )
    assert status == 200
    with urllib.request.urlopen(running_server + "/") as r:
        assert b'class="error"' in r.read()


def test_open_spec_replaces_the_figure(running_server):
    spec = FigureSpec()
    spec.data.columns = {"a": [1, 2, 3], "b": [3, 2, 1]}
    spec.panels[0].layers.append(LayerSpec(type="line", x="a", y="b"))
    spec.suptitle = "opened"
    _post(running_server + "/open", {"json": json.dumps(spec.to_dict())})
    with urllib.request.urlopen(running_server + "/spec.json") as r:
        loaded = json.loads(r.read())
    assert loaded["suptitle"] == "opened"
    assert loaded["panels"][0]["layers"][0]["x"] == "a"


def test_open_invalid_spec_reports_error_and_keeps_current_figure(running_server):
    _post(running_server + "/action", {"type": "set_suptitle", "text": "keep me"})
    for payload in (
        "not json at all",
        '{"dpi":NaN}',
        json.dumps({"panels": [{"layers": [{}]}]}),
    ):
        _post(running_server + "/open", {"json": payload})
        with urllib.request.urlopen(running_server + "/") as r:
            page = r.read().decode()
        assert 'class="error"' in page
        with urllib.request.urlopen(running_server + "/spec.json") as r:
            assert json.loads(r.read())["suptitle"] == "keep me"
