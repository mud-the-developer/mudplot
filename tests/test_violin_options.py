"""Independent KDE/normalization math and real extended violin geometry."""

from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection
from mudplot._violin import density_cell, prepare_violin
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _data():
    return {
        "c": [10] * 10 + [40] * 10,
        "v": [1, 2, 3, 4, 8] * 4,
        "h": ["A"] * 5 + ["B"] * 5 + ["A"] * 5 + ["B"] * 5,
    }


def _bodies(ax):
    return [c for c in ax.collections if isinstance(c, PolyCollection)]


@pytest.mark.parametrize("method", [None, "scott", "silverman", 0.45])
@pytest.mark.parametrize("adjust", [0.5, 1, 2])
@pytest.mark.parametrize("cut", [0, 2])
def test_gaussian_grid_bandwidth_density_matches_independent_equation(
    method, adjust, cut
):
    values = np.array([-2, -0.4, 1, 3, 4])
    factor = (
        (len(values) * 0.75) ** -0.2
        if method == "silverman"
        else (len(values) ** -0.2 if method in (None, "scott") else method)
    )
    bandwidth = np.std(values, ddof=1) * factor * adjust
    cell = density_cell(values, bw_method=method, bw_adjust=adjust, points=37, cut=cut)
    expected = np.linspace(
        values.min() - cut * bandwidth, values.max() + cut * bandwidth, 37
    )
    difference = (expected[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * difference**2).mean(axis=1) / (
        bandwidth * np.sqrt(2 * np.pi)
    )
    np.testing.assert_allclose(cell.support, expected, atol=2e-15)
    np.testing.assert_allclose(cell.bandwidth, bandwidth)
    np.testing.assert_allclose(cell.density, density, rtol=1e-13)
    np.testing.assert_allclose(cell.profile, density / density.max(), rtol=1e-13)


def test_clip_controls_support_not_fit_count_or_observations():
    data = [-2, -0.4, 1, 3, 4]
    cell = density_cell(data, cut=2, clip=[0, 2], points=41)
    reference = density_cell(data, cut=0, clip=[0, 2], points=41)
    np.testing.assert_array_equal(cell.observations, data)
    np.testing.assert_allclose(cell.support, [i / 20 for i in range(41)])
    np.testing.assert_allclose(cell.density, reference.density)
    assert len(cell.observations) == 5
    with pytest.raises(ValueError, match="support"):
        density_cell(data, clip=[10, 11])
    with pytest.raises(ValueError, match="constant"):
        density_cell([1], clip=[2, 3])


@pytest.mark.parametrize("mode", ["width", "area", "count"])
@pytest.mark.parametrize("common", [False, True])
def test_normalization_scope_uses_selected_cells_not_empty_slots(mode, common):
    cells = {
        "A": {10: [1, 2, 4, 8], 40: [1, 2, 4, 8] * 2},
        "B": {10: [1, 4, 8, 16], 40: [1, 4, 8, 16] * 4},
        "empty": {},
    }
    layer = LayerSpec(type="violin", density_norm=mode, common_norm=common)
    result = prepare_violin(cells, layer)
    for (group, cat), cell in result.items():
        reference = [v for (g, _c), v in result.items() if common or g == group]
        if mode == "width":
            expected = cell.density / cell.density.max()
        elif mode == "area":
            expected = cell.density / max(v.density.max() for v in reference)
        else:
            expected = (
                cell.density
                / cell.density.max()
                * len(cells[group][cat])
                / max(len(v.observations) for v in reference)
            )
        np.testing.assert_allclose(cell.profile, expected)
        assert (cell.profile >= 0).all() and cell.profile.max() <= 1
    assert len(result) == 4


@pytest.mark.parametrize("inner", [None, "legacy", "box", "quart", "point", "stick"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("split", [False, True])
def test_inner_split_real_geometry_keeps_positions_values_palette_and_legend(
    inner, orient, split
):
    p = mp.plot(_data()).violin(
        "c",
        "v",
        group="h",
        inner=inner,
        split=split,
        orient=orient,
        order=[10, "empty", 40],
        hue_order=["B", "A"],
        gap=0.2,
        bw_adjust=1,
        edge_color="#334155",
        line_width=0.7,
        line_style=":",
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    bodies = _bodies(ax)
    catdim = int(orient == "h")
    assert len(bodies) == 4
    assert ax.get_legend_handles_labels()[1] == ["B", "A"]
    np.testing.assert_allclose(
        np.asarray(bodies[0].get_facecolor()), np.asarray(bodies[1].get_facecolor())
    )
    assert bodies[0].get_hatch() == bodies[1].get_hatch() != bodies[2].get_hatch()
    for i, body in enumerate(bodies):
        vertices = np.asarray(body.get_paths()[0].vertices)
        c = i % 2 * 2
        position = vertices[:, catdim]
        if split:
            np.testing.assert_allclose(position.max() if i < 2 else position.min(), c)
            np.testing.assert_allclose(
                position.min() if i < 2 else position.max(),
                c + (-0.32 if i < 2 else 0.32),
            )
        else:
            np.testing.assert_allclose(
                (position.min() + position.max()) / 2, c + (-0.2 if i < 2 else 0.2)
            )
        assert np.isfinite(vertices).all()
    extra = [c for c in ax.collections if isinstance(c, LineCollection)]
    expected = {None: 0, "legacy": 4, "box": 8, "quart": 4, "point": 0, "stick": 4}[
        inner
    ]
    assert len(extra) == expected
    if inner == "point":
        assert len(ax.lines) == 4
        for line in ax.lines:
            values = np.asarray(line.get_xdata() if orient == "h" else line.get_ydata())
            np.testing.assert_array_equal(values, [1, 2, 3, 4, 8])
    if inner == "stick":
        assert sum(len(c.get_segments()) for c in extra) == 20
    if inner == "quart":
        for collection in extra:
            values = np.asarray(collection.get_segments())[:, :, 1 - catdim]
            np.testing.assert_allclose(values, [[2, 2], [3, 3], [4, 4]])
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("inner", [None, "box", "quart", "point", "stick"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_log_native_split_all_artists_inverse_map_including_observed_points(
    inner, orient
):
    p = mp.plot(_data()).violin(
        "c",
        "v",
        group="h",
        inner=inner,
        split=True,
        orient=orient,
        native_scale=True,
        stat_scale="axis",
        cut=2,
        clip=(0.5, 16),
    )
    p.xscale("log").yscale("log")
    ax = p.render().axes[0]
    cd = int(orient == "h")
    vd = 1 - cd
    spacing = math.log10(4)
    for i, body in enumerate(_bodies(ax)):
        vertices = np.asarray(body.get_paths()[0].vertices)
        coord = np.log10(vertices[:, cd])
        center = math.log10(10 if i % 2 == 0 else 40)
        np.testing.assert_allclose(coord.max() if i < 2 else coord.min(), center)
        np.testing.assert_allclose(
            coord.min() if i < 2 else coord.max(),
            center + (-0.4 if i < 2 else 0.4) * spacing,
        )
        assert vertices[:, vd].min() >= 0.5 * (1 - 1e-14)
        assert vertices[:, vd].max() <= 16 * (1 + 1e-14)
    for collection in ax.collections:
        if isinstance(collection, LineCollection):
            assert all((np.asarray(s) > 0).all() for s in collection.get_segments())
    if inner == "point":
        for line in ax.lines:
            np.testing.assert_allclose(
                np.asarray(line.get_xydata())[:, vd], [1, 2, 3, 4, 8]
            )
    assert ax.get_xscale() == ax.get_yscale() == "log"
    assert (np.asarray(ax.dataLim.minpos) > 0).all()


@pytest.mark.parametrize("inner", ["box", "quart", "point", "stick"])
def test_default_data_vs_explicit_axis_summary_coordinates_on_log(inner):
    for mode, median in [("data", 5), ("axis", 3)]:
        p = (
            mp.plot({"c": [10, 10], "v": [1, 9]})
            .violin("c", "v", inner=inner, stat_scale=mode)
            .yscale("log")
        )
        ax = p.render().axes[0]
        if inner == "box":
            np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata()), [median])
        elif inner == "quart":
            c = ax.collections[1]
            assert isinstance(c, LineCollection)
            np.testing.assert_allclose(
                np.asarray(c.get_segments()[1])[:, 1], [median] * 2
            )
        elif inner == "point":
            np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata()), [1, 9])
        else:
            c = ax.collections[1]
            assert isinstance(c, LineCollection)
            np.testing.assert_allclose(
                np.asarray(c.get_segments())[:, :, 1], [[1, 1], [9, 9]]
            )


@pytest.mark.parametrize("mode", ["width", "area", "count"])
def test_singular_constant_and_missing_cells_are_finite_not_fabricated_kdes(mode):
    p = mp.plot({"c": [10, 10, 40, 80], "v": [3, 3, 4, None]}).violin(
        "c", "v", density_norm=mode, inner="box", order=[10, 40, 80, "empty"]
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert len(_bodies(ax)) == 2
    for body in _bodies(ax):
        assert np.isfinite(body.get_paths()[0].vertices).all()
    assert len(ax.lines) == 2
    assert density_cell([1, 1]).singular and density_cell([1]).bandwidth == 0


def test_empty_reserved_split_side_has_no_fake_body_or_legend():
    p = mp.plot({"c": [10, 10], "v": [1, 2], "h": ["A", "A"]}).violin(
        "c", "v", group="h", hue_order=["missing", "A"], split=True, inner=None
    )
    ax = p.render().axes[0]
    assert len(_bodies(ax)) == 1 and ax.get_legend_handles_labels()[1] == ["A"]
    assert np.asarray(_bodies(ax)[0].get_paths()[0].vertices)[:, 0].min() == 0


@pytest.mark.parametrize(
    "options,match",
    [
        ({"inner": "invalid"}, "inner"),
        ({"inner": True}, "inner"),
        ({"inner": "quart", "showmedians": False}, "require inner"),
        ({"inner": None, "showmeans": True}, "require inner"),
        ({"split": "yes"}, "boolean"),
        ({"split": 1}, "boolean"),
        ({"split": True, "dodge": 0.2}, "dodge"),
        ({"density_norm": "density"}, "density_norm"),
        ({"common_norm": 1}, "boolean"),
        ({"common_norm": True}, "requires density_norm"),
        ({"bw_adjust": 0}, "bw_adjust"),
        ({"bw_adjust": True}, "bw_adjust"),
        ({"bw_adjust": float("inf")}, "bw_adjust"),
        ({"bw_adjust": 1001}, "bw_adjust"),
        ({"bw_adjust": lambda x: x}, "bw_adjust"),
        ({"cut": -1}, "cut"),
        ({"cut": 11}, "cut"),
        ({"cut": True}, "cut"),
        ({"clip": [2, 1]}, "clip"),
        ({"clip": [1]}, "clip"),
        ({"clip": [False, 2]}, "clip"),
        ({"clip": [1, float("inf")]}, "clip"),
        ({"inner": "stick", "marker_size": 3}, "marker/marker_size"),
        ({"inner": "point", "marker": "INVALID"}, "marker"),
        ({"inner": "point", "marker_size": 0}, "marker_size"),
        ({"line_width": 1001}, "line_width"),
    ],
)
def test_invalid_ignored_and_unsafe_settings_fail_before_matplotlib(options, match):
    p = mp.plot(_data()).violin("c", "v", group="h", **options)
    assert any(match in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match=match):
        p.render()


@pytest.mark.parametrize(
    "builder", ["box", "boxenplot", "swarmplot", "barplot", "scatter"]
)
@pytest.mark.parametrize(
    "options",
    [
        {"inner": None},
        {"split": True},
        {"density_norm": "area"},
        {"common_norm": True},
        {"cut": 2},
        {"clip": [1, 8]},
        {"bw_adjust": 0.5},
    ],
)
def test_violin_controls_are_rejected_on_other_layers(builder, options):
    p = getattr(mp.plot(_data()), builder)("c", "v", **options)
    assert any("not supported" in i for i in mp.validate(p.spec))


def test_split_requires_two_hues_without_legacy_group_reinterpretation():
    for data, options in [
        ({"c": [10], "v": [1], "h": ["A"]}, {}),
        (_data(), {"hue_order": ["A", "B", "third"]}),
    ]:
        p = mp.plot(data).violin("c", "v", group="h", split=True, **options)
        assert any("two selected hue" in i for i in mp.validate(p.spec))
    p = mp.plot(_data()).violin("v", group="h", split=True)
    assert any("category/value" in i for i in mp.validate(p.spec))
    p = mp.plot(_data()).violin("c", "v", split=True)
    assert any("hue" in i for i in mp.validate(p.spec))


def test_clip_inner_observations_log_positivity_and_row_bounds_are_explicit():
    p = (
        mp.plot({"c": [10] * 3, "v": [0.5, 4, 100]})
        .violin("c", "v", inner="point", clip=[1, 8], stat_scale="axis")
        .yscale("log")
    )
    ax = p.render().axes[0]
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata()), [0.5, 4, 100])
    vertices = np.asarray(_bodies(ax)[0].get_paths()[0].vertices)
    np.testing.assert_allclose([vertices[:, 1].min(), vertices[:, 1].max()], [1, 8])
    p = mp.plot(_data()).violin("c", "v", clip=[0, 8]).yscale("log")
    assert any("positive raw" in i for i in mp.validate(p.spec))
    p = mp.plot({"v": [1, 2, 3, 4]}).violin("v", cut=2).yscale("log")
    with pytest.raises(ValueError, match="geometry"):
        p.render()
    p = mp.plot({"c": [10] * 10001, "v": [1] * 10001}).violin("c", "v", inner="stick")
    assert any("10000" in i for i in mp.validate(p.spec))


def test_legacy_explicit_summary_flags_and_old_defaults_remain_supported():
    p = mp.plot({"c": [10] * 4, "v": [1, 2, 3, 8]}).violin(
        "c", "v", cut=1, showmedians=False, showmeans=True, showextrema=True
    )
    ax = p.render().axes[0]
    lines = [c for c in ax.collections if isinstance(c, LineCollection)]
    assert len(lines) == 3
    np.testing.assert_allclose(np.asarray(lines[0].get_segments()[0])[:, 1], [3.5, 3.5])
    layer = LayerSpec.from_dict({"type": "violin", "x": "v"})
    assert isinstance(layer, LayerSpec)
    assert layer.inner == "legacy" and layer.density_norm == "width"
    assert not layer.common_norm and not layer.split and layer.cut is None


def test_editor_schema_actions_and_reproducible_exports_do_not_use_global_rng(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    session.dispatch_safe(A.SetScale("x", "log"))
    session.dispatch_safe(A.SetScale("y", "log"))
    fields = {
        "x": "c",
        "y": "v",
        "group": "h",
        "inner": "quart",
        "split": True,
        "density_norm": "count",
        "common_norm": True,
        "bw_adjust": 0.7,
        "points": 61,
        "cut": 2,
        "clip": [0.5, 16],
        "native_scale": True,
        "stat_scale": "axis",
    }
    before = np.random.get_state()
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {"layer_type": "violin", "layer_json": json.dumps(fields)},
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
