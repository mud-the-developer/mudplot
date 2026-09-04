import mudplot as mp
import pytest
from mudplot import actions as A


def test_capabilities_shape():
    caps = mp.capabilities()
    for key in (
        "layers",
        "themes",
        "journals",
        "palettes",
        "tex_presets",
        "actions",
        "spec_version",
    ):
        assert key in caps
    assert "line" in caps["layers"]
    assert "x" in caps["layers"]["line"]["required"]
    assert "AddLayer" in caps["actions"]


def test_action_roundtrip_simple():
    a = A.action_from_dict({"type": "SetSize", "width": 4, "height": 3})
    assert isinstance(a, A.SetSize)
    assert A.action_to_dict(a) == {"type": "SetSize", "width": 4, "height": 3}


def test_action_roundtrip_nested_layer():
    d = {"type": "AddLayer", "layer": {"type": "line", "x": "a", "y": "b"}, "panel": 0}
    a = A.action_from_dict(d)
    assert isinstance(a, A.AddLayer)
    assert a.layer.x == "a"
    back = A.action_to_dict(a)
    assert back["type"] == "AddLayer"
    assert back["layer"]["x"] == "a"


def test_action_unknown_type_raises():
    with pytest.raises(ValueError, match="unknown action type"):
        A.action_from_dict({"type": "Nope"})


def test_action_unknown_field_raises():
    with pytest.raises(ValueError, match="unknown field"):
        A.action_from_dict({"type": "SetSize", "width": 1, "height": 1, "z": 9})


def test_apply_builds_spec_from_json():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1, 2], "y": [3, 4]}},
            {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
            {"type": "SetAxisLabel", "axis": "x", "text": "X"},
            {"type": "SetTheme", "name": "paper"},
        ]
    )
    assert spec.data.columns == {"x": [1, 2], "y": [3, 4]}
    assert spec.panels[0].layers[0].type == "line"
    assert spec.panels[0].x.label == "X"


def test_apply_is_pure():
    base = mp.FigureSpec()
    snap = base.to_dict()
    mp.apply([{"type": "SetSize", "width": 9, "height": 9}], spec=base)
    assert base.to_dict() == snap  # untouched


def test_json_schema_structure():
    sch = mp.json_schema()
    assert sch["title"] == "FigureSpec"
    assert "panels" in sch["properties"]
    assert "LayerSpec" in sch["$defs"]
    # LayerSpec.type default is present
    assert sch["$defs"]["LayerSpec"]["properties"]["type"]["default"] == "line"


def test_action_log_and_replay():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").theme("boxed")
    log = p.action_log
    assert log[0]["type"] == "SetData"
    # replay the log into a fresh spec -> identical
    replayed = mp.apply(log)
    assert replayed.to_dict() == p.spec.to_dict()


def test_store_undo():
    from mudplot.store import Store

    store = Store()
    store.dispatch(A.SetSize(4, 3))
    store.dispatch(A.SetTitle("hi"))
    assert store.state.panels[0].title == "hi"
    store.undo()
    assert store.state.panels[0].title == ""
    assert store.state.size == [4, 3]
    assert len(store.history) == 1
