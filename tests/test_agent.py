import mudplot as mp
import pytest
from mudplot import actions as A


def test_v1_public_surface_and_matplotlib_ownership(tmp_path):
    # Additions are compatible; removing an established name needs a major release.
    exports = {
        "AVAILABLE_JOURNALS",
        "AVAILABLE_THEMES",
        "JOURNAL_PROFILES",
        "JOURNAL_SIZES",
        "PREAMBLE",
        "TEX_PRESETS",
        "FigureSpec",
        "JournalProfile",
        "LintIssue",
        "LintReport",
        "Plot",
        "Reference",
        "ReferenceCatalog",
        "ReferenceSpec",
        "Store",
        "TexContext",
        "action_from_dict",
        "action_to_dict",
        "actions",
        "apply",
        "assert_valid",
        "capabilities",
        "color",
        "color_palette",
        "figsize_for",
        "from_json",
        "get_journal_profile",
        "json_schema",
        "lint_figure",
        "load_spec",
        "plot",
        "reduce",
        "reduce_all",
        "reference_markdown",
        "render",
        "resolve_reference_href",
        "save",
        "save_spec",
        "tex_preview",
        "to_json",
        "validate",
    }
    builders = {
        "spec",
        "store",
        "dispatch",
        "apply",
        "action_log",
        "line",
        "regplot",
        "scatter",
        "stripplot",
        "stackplot",
        "hist2d",
        "hexbin",
        "quiver",
        "heatmap",
        "matrix",
        "contour",
        "contourf",
        "bar",
        "errorbar",
        "band",
        "hline",
        "vline",
        "text",
        "annotate",
        "hist",
        "box",
        "violin",
        "kde",
        "rug",
        "pie",
        "scatter3d",
        "line3d",
        "surface",
        "wireframe",
        "projection3d",
        "projection_polar",
        "zlabel",
        "remove_layer",
        "set_layer_at",
        "layout",
        "suptitle",
        "panel_label",
        "auto_label",
        "labels",
        "title_reference",
        "title_position",
        "reference_style",
        "xscale",
        "yscale",
        "xlim",
        "ylim",
        "legend",
        "theme",
        "journal",
        "palette",
        "font",
        "axes_style",
        "grid_style",
        "ticks_style",
        "encoding",
        "share",
        "secondary_yaxis",
        "size",
        "tex_size",
        "render",
        "save",
        "preview",
        "lint",
        "to_json",
        "from_json",
    }
    assert exports <= set(mp.__all__)
    assert all(hasattr(mp, name) for name in exports)
    assert all(hasattr(mp.Plot, name) for name in builders)
    assert mp.Reference is mp.ReferenceSpec

    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    plot = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").size(4, 3)
    before = plot.to_json()
    for figure in (plot.render(), plot.save(str(tmp_path / "figure.svg"))):
        try:
            assert isinstance(figure, Figure)
            assert plt.fignum_exists(figure.number)
            assert tuple(figure.get_size_inches()) == (4, 3)
            assert plot.to_json() == before
        finally:
            plt.close(figure)


def test_capabilities_shape():
    caps = mp.capabilities()
    for key in (
        "layers",
        "projections",
        "themes",
        "journals",
        "palettes",
        "tex_presets",
        "actions",
        "spec_version",
    ):
        assert key in caps
    assert caps["projections"] == ["2d", "polar", "3d"]
    assert "line" in caps["layers"]
    assert "x" in caps["layers"]["line"]["required"]
    assert "AddLayer" in caps["actions"]


def test_action_roundtrip_simple():
    a = A.action_from_dict({"type": "SetSize", "width": 4, "height": 3})
    assert isinstance(a, A.SetSize)
    assert A.action_to_dict(a) == {"type": "SetSize", "width": 4, "height": 3}


def test_action_roundtrip_supports_clearing_axis_limits_and_secondary_axis():
    limits = A.action_from_dict(
        {"type": "SetLimits", "axis": "x", "lo": None, "hi": None, "panel": 0}
    )
    secondary = A.action_from_dict(
        {
            "type": "SetSecondaryAxis",
            "label": None,
            "scale": "linear",
            "limits": None,
            "panel": 0,
        }
    )
    assert limits == A.SetLimits("x", None, None)
    assert secondary == A.SetSecondaryAxis(None)
    assert A.action_to_dict(limits)["lo"] is None
    assert A.action_to_dict(secondary)["label"] is None


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


@pytest.mark.parametrize(
    "payload",
    [
        [],
        [["type", "SetTitle"], ["text", "not an object"]],
        {"type": []},
        {"action": "SetTitle", "text": "undocumented alias"},
        {"type": [], "action": "SetTitle", "text": "must not fall back"},
        {1: "not a JSON key", "type": "SetTitle", "text": "bad"},
        {"type": "AddLayer", "layer": []},
        {"type": "SetTitle", "text": []},
        {"type": "SetSize", "width": "wide", "height": 3},
        {"type": "SetAutoLabel", "enabled": 1},
        {"type": "SetLayout", "rows": True, "cols": 2},
        {"type": "SetLayerAt", "layer_index": 0, "at": "center"},
    ],
)
def test_action_fields_are_type_checked_before_reducer_dispatch(payload):
    with pytest.raises(TypeError):
        A.action_from_dict(payload)


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
