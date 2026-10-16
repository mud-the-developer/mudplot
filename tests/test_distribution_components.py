"""Bounded, independent box/letter-value artist styles and pure JSON contracts."""

from __future__ import annotations

import json
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgba
from mudplot.spec import ComponentStyleSpec as Style
from mudplot.spec import DistributionComponentsSpec as Components
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _data():
    return {"c": [10] * 6, "v": [1, 2, 3, 4, 5, 30]}


def _components(kind):
    result = {
        "body": {
            "color": "#217a8a",
            "edge_color": "#aa1122",
            "line_width": 1.2,
            "line_style": ":",
            "alpha": 1,
            "hatch": "",
        },
        "median": {
            "color": "#ff8800",
            "line_width": 2,
            "line_style": "--",
            "alpha": 0.8,
        },
        "flier": {
            "color": "#332211",
            "edge_color": "#1122aa",
            "face_color": "#ffffcc",
            "marker": "D",
            "marker_size": 5,
            "marker_edge_width": 1.3,
            "alpha": 0.5,
        },
    }
    if kind == "box":
        result.update(
            whisker={"color": "#bb2211", "line_width": 0.4, "line_style": "-."},
            cap={"color": "#2244bb", "line_width": 1.7, "line_style": "--"},
            mean={
                "color": "#008800",
                "edge_color": "#880088",
                "face_color": "#ffffff",
                "marker": "s",
                "marker_size": 4,
                "marker_edge_width": 0.9,
                "alpha": 0.7,
            },
        )
    return result


@pytest.mark.parametrize("kind", ["box", "boxenplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("log", [False, True])
def test_named_styles_override_only_properties_not_statistics_geometry_or_native_logs(
    kind, orient, log
):
    options = {
        "orient": orient,
        "native_scale": True,
        "stat_scale": "axis",
        "edge_color": "#555555",
        "line_width": 0.8,
        "alpha": 0.4,
    }
    if kind == "box":
        options["showmeans"] = True
    figures = []
    for components in (None, _components(kind)):
        p = getattr(mp.plot(_data()), kind)("c", "v", **options, components=components)
        if log:
            p.xscale("log").yscale("log")
        assert mp.validate(p.spec) == []
        assert (
            mp.Plot.from_json(p.to_json()).spec == p.spec
            and mp.apply(p.action_log) == p.spec
        )
        figures.append(p.render())
    before, after = [f.axes[0] for f in figures]
    for a, b in zip(before.lines, after.lines, strict=True):
        np.testing.assert_array_equal(
            np.asarray(a.get_xydata()), np.asarray(b.get_xydata())
        )
    if kind == "box":
        np.testing.assert_array_equal(
            before.patches[0].get_path().vertices, after.patches[0].get_path().vertices
        )
        body = after.patches[0]
        median, flier = after.lines[4], after.lines[6]
        for line in after.lines[:2]:
            assert line.get_color() == "#bb2211" and line.get_linewidth() == 0.4
        for line in after.lines[2:4]:
            assert line.get_color() == "#2244bb" and line.get_linewidth() == 1.7
        mean = after.lines[5]
        assert (
            mean.get_marker() == "s"
            and mean.get_markersize() == 4
            and mean.get_alpha() == 0.7
        )
        assert (
            mean.get_markerfacecolor() == "#ffffff"
            and mean.get_markeredgewidth() == 0.9
        )
    else:
        body = after.collections[0]
        assert isinstance(body, PolyCollection)
        for a, b in zip(
            before.collections[0].get_paths(), body.get_paths(), strict=True
        ):
            np.testing.assert_array_equal(
                np.asarray(a.vertices), np.asarray(b.vertices)
            )
        median, flier = after.lines
        # An explicit base color preserves lighter tail tiers (depth>=1).
        faces = np.asarray(body.get_facecolor())
        depth = (len(faces) + 1) // 2
        np.testing.assert_allclose(faces[depth - 1], to_rgba("#217a8a"))
    assert body.get_alpha() == 1 and body.get_hatch() == ""
    np.testing.assert_allclose(
        np.asarray(body.get_edgecolor()).reshape(-1, 4), [to_rgba("#aa1122")]
    )
    assert median.get_color() == "#ff8800" and median.get_linewidth() == 2
    assert median.get_alpha() == 0.8
    assert flier.get_marker() == "D" and flier.get_markersize() == 5
    assert (
        flier.get_markerfacecolor() == "#ffffcc"
        and flier.get_markeredgecolor() == "#1122aa"
    )
    assert flier.get_markeredgewidth() == 1.3 and flier.get_alpha() == 0.5
    assert (after.get_xscale() == "log") == log and (after.get_yscale() == "log") == log


@pytest.mark.parametrize("kind", ["box", "boxenplot"])
def test_none_and_empty_components_preserve_old_native_defaults_and_one_based_positions(
    kind,
):
    axes = [
        getattr(mp.plot(_data()), kind)("v", components=c).render().axes[0]
        for c in (None, {}, Components())
    ]
    for other in axes[1:]:
        for a, b in zip(axes[0].lines, other.lines, strict=True):
            assert (
                a.get_color() == b.get_color()
                and a.get_linewidth() == b.get_linewidth()
            )
            np.testing.assert_array_equal(a.get_xydata(), b.get_xydata())
    if kind == "box":
        vertices = np.asarray(axes[0].patches[0].get_path().vertices)
    else:
        vertices = np.asarray(axes[0].collections[0].get_paths()[0].vertices)
    assert (vertices[:, 0].min() + vertices[:, 0].max()) / 2 == 1
    legacy = LayerSpec.from_dict({"type": kind, "x": "v"})
    assert isinstance(legacy, LayerSpec) and legacy.components is None


def test_hue_hatches_empty_slots_and_letter_tints_survive_partial_component_overrides():
    data = {"c": [10] * 8, "v": [1, 2, 4, 8] * 2, "h": ["A"] * 4 + ["B"] * 4}
    p = mp.plot(data).boxenplot(
        "c",
        "v",
        group="h",
        k_depth=3,
        hue_order=["B", "empty", "A"],
        components={"median": {"color": "#000000"}},
    )
    ax = p.render().axes[0]
    bodies = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(bodies) == 2 and ax.get_legend_handles_labels()[1] == ["B", "A"]
    assert bodies[0].get_hatch() != bodies[1].get_hatch()
    for body in bodies:
        colors = np.asarray(body.get_facecolor())
        assert len({tuple(c) for c in colors}) > 1


@pytest.mark.parametrize("kind", ["box", "boxenplot"])
def test_transparent_body_and_exact_alpha_zero_do_not_mutate_medians_or_fliers(kind):
    ax = (
        getattr(mp.plot(_data()), kind)(
            "c", "v", components={"body": {"color": "none", "alpha": 0}}
        )
        .render()
        .axes[0]
    )
    body = ax.patches[0] if kind == "box" else ax.collections[0]
    assert body.get_alpha() == 0
    faces = np.asarray(body.get_facecolor())
    assert faces.size == 0 or (faces[..., 3] == 0).all()
    assert len(ax.lines) > 0


def test_explicit_cap_and_body_style_enable_their_artist_under_ambient_hidden_rc():
    with matplotlib.rc_context({"boxplot.showcaps": False, "boxplot.showbox": False}):
        p = mp.plot(_data()).box(
            "c", "v", components={"cap": {"color": "red"}, "body": {}}
        )
        ax = p.render().axes[0]
        assert len(ax.patches) == 1
        assert [line.get_color() for line in ax.lines[2:4]] == ["red", "red"]


@pytest.mark.parametrize("role", ["whisker", "cap", "mean"])
def test_nonexistent_letter_components_are_rejected_even_when_empty(role):
    p = mp.plot(_data()).boxenplot("c", "v", components={role: {}})
    assert any("not supported" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "role,field,value",
    [
        ("body", "marker", "o"),
        ("body", "face_color", "red"),
        ("whisker", "edge_color", "red"),
        ("median", "marker_size", 2),
        ("flier", "hatch", "/"),
        ("body", "color", "INVALID"),
        ("body", "color", "#xx2233"),
        ("body", "alpha", 2),
        ("body", "alpha", True),
        ("median", "line_width", -1),
        ("median", "line_width", float("inf")),
        ("median", "line_width", True),
        ("median", "line_style", "INVALID"),
        ("body", "hatch", "Q"),
        ("body", "hatch", "/" * 33),
        ("flier", "marker", "INVALID"),
        ("flier", "marker_size", 0),
        ("flier", "marker_edge_width", 1001),
    ],
)
def test_role_specific_bounded_settings_fail_before_matplotlib(role, field, value):
    # Typed objects retain invalid values so pure validate can report each cause.
    style = Style(**{field: value})
    p = mp.plot(_data()).box("c", "v", components=Components(**{role: style}))
    assert any(f"components.{role}.{field}" in i for i in mp.validate(p.spec))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "options",
    [
        {"components": {"mean": {}}, "showmeans": None},
        {"components": {"flier": {}}, "showfliers": False},
    ],
)
def test_styling_disabled_box_artists_is_not_silently_ignored(options):
    p = mp.plot(_data()).box("c", "v", **options)
    assert any("requires" in i for i in mp.validate(p.spec))


def test_boxen_hidden_median_and_bad_direct_object_types_fail():
    p = mp.plot(_data()).boxenplot(
        "c", "v", showmedians=False, components={"median": {}}
    )
    assert any("visible medians" in i for i in mp.validate(p.spec))
    layer = LayerSpec(type="box", x="v", components=cast(Any, {}))
    spec = mp.plot(_data()).spec
    spec.panels[0].layers.append(layer)
    assert any("DistributionComponentsSpec" in i for i in mp.validate(spec))
    p = mp.plot(_data()).box("c", "v", components=Components(body=cast(Any, {})))
    assert any("ComponentStyleSpec" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "payload",
    [
        {"unknown": {}},
        {"body": {"unknown": 1}},
        {"body": {"line_width": True}},
        {"median": 3},
    ],
)
def test_unknown_keys_and_wrong_json_shapes_rejected_without_dropping_settings(payload):
    with pytest.raises((ValueError, TypeError)):
        mp.plot(_data()).box("c", "v", components=payload)
    with pytest.raises((ValueError, TypeError)):
        LayerSpec.from_dict({"type": "box", "x": "v", "components": payload})


@pytest.mark.parametrize("kind", ["violin", "swarmplot", "barplot", "scatter"])
def test_other_types_reject_component_field(kind):
    p = getattr(mp.plot(_data()), kind)("c", "v", components=Components())
    assert any("components is not supported" in i for i in mp.validate(p.spec))


def test_json_schema_rejects_unknown_component_fields():
    import jsonschema

    schema = mp.json_schema()
    for name in ("ComponentStyleSpec", "DistributionComponentsSpec"):
        assert schema["$defs"][name]["additionalProperties"] is False
    spec = (
        mp.plot(_data())
        .box("c", "v", components={"body": {"color": "red"}})
        .spec.to_dict()
    )
    jsonschema.Draft202012Validator(schema).validate(spec)
    spec["panels"][0]["layers"][0]["components"]["body"]["unknown"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(spec)


def test_editor_actions_json_and_repeatable_exports_keep_global_rng(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    fields = {
        "x": "c",
        "y": "v",
        "components": _components("box"),
        "showmeans": True,
        "native_scale": True,
        "stat_scale": "axis",
    }
    before = np.random.get_state()
    session.dispatch_safe(A.SetScale("x", "log"))
    session.dispatch_safe(A.SetScale("y", "log"))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {"layer_type": "box", "layer_json": json.dumps(fields)},
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    jsonschema.Draft202012Validator(mp.json_schema()).validate(
        session.store.state.to_dict()
    )
    p = mp.Plot.from_json(mp.to_json(session.store.state))
    assert mp.apply([A.action_to_dict(a) for a in session.store.history]) == p.spec
    for fmt in ("png", "pdf", "svg"):
        one, two = tmp_path / f"one.{fmt}", tmp_path / f"two.{fmt}"
        plt.close(p.save(str(one)))
        plt.close(p.save(str(two)))
        assert one.read_bytes() == two.read_bytes()
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
