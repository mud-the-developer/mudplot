"""STATE-03/EDIT-01/HIST-03: compare supported operations, not different UI scopes."""

from __future__ import annotations

import copy
import json
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import matplotlib

matplotlib.use("Agg")
import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession, _build_action, make_server
from mudplot import actions as A
from mudplot.__main__ import main

CASE = json.loads(
    (Path(__file__).parent / "fixtures/review_state_paths.json").read_text(
        encoding="utf-8"
    )
)


def _python_form(step):
    if "python_form" in step:
        return copy.deepcopy(step["python_form"])
    action = step["action"]
    layer = dict(action["layer"])
    kind = layer.pop("type")
    return {
        "type": "add_layer_json",
        "layer_type": kind,
        "layer_json": json.dumps(layer),
        "panel": str(action["panel"]),
    }


def test_fluent_functional_and_store_paths_preserve_the_same_complete_state(tmp_path):
    initial = mp.FigureSpec.from_dict(CASE["initial"])
    actions = [step["action"] for step in CASE["steps"]]
    expected = mp.apply(actions, initial)
    plot = (
        mp.Plot.from_json(mp.to_json(initial))
        .theme("boxed")
        .size(8.0, 3.0)
        .layout(1, 2)
    )
    plot.labels(title="Cross-path series", x="Time").yscale("log").xlim(0.5, 2.5)
    plot.line(
        "x",
        "y",
        group="g",
        line_width=1.4,
        references={
            "A": mp.Reference(citation="method_2026"),
            "B": mp.Reference(href="https://example.invalid/source"),
        },
    )
    plot.heatmap(
        "m",
        colorbar=False,
        heatmap={
            "annot": True,
            "fmt": ".1f",
            "xlabels": ["u", "v"],
            "ylabels": ["r", "s"],
        },
        panel=1,
    ).labels(title="Matrix", panel=1)
    store = mp.Store(initial)
    store.dispatch_all([A.action_from_dict(action) for action in actions])
    assert plot.spec == store.state == expected
    assert mp.validate(expected) == []
    assert expected.data == initial.data
    for name, state in (
        ("fluent", plot.spec),
        ("functional", expected),
        ("store", store.state),
    ):
        path = tmp_path / f"{name}.json"
        mp.save_spec(state, path)
        assert mp.load_spec(path) == expected


def test_cli_matches_each_expected_intermediate_state(tmp_path):
    state = mp.FigureSpec.from_dict(CASE["initial"])
    path, action_path = tmp_path / "cli.json", tmp_path / "action.json"
    mp.save_spec(state, path)
    for step in CASE["steps"]:
        action_path.write_text(json.dumps(step["action"]), encoding="utf-8")
        assert main(["apply", str(path), str(action_path), "-o", str(path)]) == 0
        state = mp.apply([step["action"]], state)
        assert mp.load_spec(path) == state


@pytest.mark.parametrize("route", ["action", "form"])
def test_python_session_matches_action_and_visual_form_paths(route, tmp_path):
    session = EditorSession()
    state = mp.FigureSpec.from_dict(CASE["initial"])
    session.load_spec(mp.to_json(state))
    for step in CASE["steps"]:
        if route == "form":
            fields = _python_form(step)
            action = _build_action(fields.pop("type"), fields, session.store.state)
        else:
            action = A.action_from_dict(step["action"])
        session.dispatch_safe(action)
        assert session.error is None
        state = mp.apply([step["action"]], state)
        assert session.store.state == state
    path = tmp_path / f"session-{route}.json"
    mp.save_spec(session.store.state, path)
    assert mp.load_spec(path) == state


@pytest.fixture(scope="module")
def editor_http():
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("route", ["action", "form"])
def test_python_http_state_matches_each_supported_action_or_form(route, editor_http):
    def post(path, fields):
        request = urllib.request.Request(
            editor_http + path,
            urlencode(fields).encode(),
            headers={"HX-Request": "true"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            assert b'class="error"' not in response.read()

    state = mp.FigureSpec.from_dict(CASE["initial"])
    post("/open", {"json": mp.to_json(state)})
    for step in CASE["steps"]:
        if route == "form":
            post("/action", _python_form(step))
        else:
            post("/action/raw", {"json": json.dumps(step["action"])})
        state = mp.apply([step["action"]], state)
        with urllib.request.urlopen(editor_http + "/spec.json", timeout=30) as response:
            assert mp.FigureSpec.from_dict(json.load(response)) == state


@pytest.mark.parametrize(
    "failure", ["invalid_action", "damaged_json", "render_action", "render_import"]
)
def test_python_failures_preserve_spec_history_preview_and_future(failure):
    session = EditorSession()
    valid = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    session.load_spec(valid.to_json())
    session.dispatch_safe(A.SetTitle("A"))
    session.dispatch_safe(A.SetTitle("B"))
    future, future_png = session.store.state, session.png
    session.undo()
    before, history, preview = session.store.state, session.store.history, session.png
    invalid = (
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y", color="not-a-color").spec
    )
    assert mp.validate(invalid) == []  # Exercise the effect failure, not validation.
    if failure == "invalid_action":
        session.dispatch_safe(A.SetSize(-1, 3))
    elif failure == "damaged_json":
        with pytest.raises(ValueError):
            session.load_spec("{damaged JSON")
    elif failure == "render_action":
        session.dispatch_safe(A.AddLayer(copy.deepcopy(invalid.panels[0].layers[0])))
    else:
        with pytest.raises(ValueError):
            session.load_spec(mp.to_json(invalid))
    assert session.store.state == before and session.store.history == history
    assert session.png == preview
    session.redo()
    assert session.store.state == future and session.png == future_png
    session.dispatch_safe(A.SetTitle("recovered"))
    assert session.error is None
