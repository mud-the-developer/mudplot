"""Native category geometry and explicit data/axis-space summary contracts."""

from __future__ import annotations

import json
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection
from mudplot._categorical import native_category_geometry
from mudplot._letter_value import letter_value_summary
from mudplot._swarm import SwarmCollection

KINDS = ("box", "violin", "boxenplot", "swarmplot")
SUMMARIES = KINDS[:-1]


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _vertices(ax, kind):
    return (
        [np.asarray(p.get_path().vertices) for p in ax.patches]
        if kind == "box"
        else [np.asarray(c.get_paths()[0].vertices) for c in ax.collections[:1]]
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("scale", ["linear", "log"])
def test_native_centers_width_spacing_and_reserved_nonmonotonic_order(
    kind, orient, scale
):
    data = {"c": [10] * 4 + [40] * 4, "v": [1, 2, 4, 8] * 2}
    p = (
        getattr(mp.plot(data), kind)(
            "c",
            "v",
            native_scale=True,
            order=[40, 100, 10],
            width=0.6,
            gap=0.2,
            orient=orient,
            marker_size=1,
        )
        if kind != "violin"
        else (
            mp.plot(data).violin(
                "c",
                "v",
                native_scale=True,
                order=[40, 100, 10],
                width=0.6,
                gap=0.2,
                orient=orient,
            )
        )
    )
    (p.yscale if orient == "h" else p.xscale)(scale)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    catdim = int(orient == "h")
    if kind == "swarmplot":
        offsets = np.asarray(ax.collections[0].get_offsets())
        # Distinct value coordinates need no collision displacement.
        np.testing.assert_allclose(offsets[:, catdim], [10] * 4 + [40] * 4, rtol=1e-14)
        np.testing.assert_array_equal(offsets[:, 1 - catdim], data["v"])
    else:
        verts = _vertices(ax, kind)[0]
        coords = np.log10(verts[:, catdim]) if scale == "log" else verts[:, catdim]
        center = np.log10(40) if scale == "log" else 40
        spacing = np.log10(100 / 40) if scale == "log" else 30
        np.testing.assert_allclose((coords.max() + coords.min()) / 2, center)
        np.testing.assert_allclose(coords.max() - coords.min(), 0.6 * 0.8 * spacing)
    limits = ax.get_ylim() if orient == "h" else ax.get_xlim()
    assert min(limits) < 10 and max(limits) > 100
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


@pytest.mark.parametrize("kind", SUMMARIES)
@pytest.mark.parametrize("mode", ["data", "axis"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_log_summary_median_and_quantiles_use_explicit_stat_coordinates(
    kind, mode, orient
):
    p = getattr(mp.plot({"c": [10, 10], "v": [1, 9]}), kind)(
        "c", "v", native_scale=True, orient=orient, stat_scale=mode
    )
    (p.xscale if orient == "h" else p.yscale)("log")
    ax = p.render().axes[0]
    expected = 5 if mode == "data" else 3
    vd = int(orient != "h")
    if kind == "box":
        median = ax.lines[4]
        values = median.get_xdata() if orient == "h" else median.get_ydata()
        np.testing.assert_allclose(np.asarray(values), [expected] * 2)
        verts = _vertices(ax, kind)[0]
        q = [3, 7] if mode == "data" else [9**0.25, 9**0.75]
        np.testing.assert_allclose([verts[:, vd].min(), verts[:, vd].max()], q)
    elif kind == "boxenplot":
        line = ax.lines[0]
        values = line.get_xdata() if orient == "h" else line.get_ydata()
        np.testing.assert_allclose(np.asarray(values), [expected] * 2)
    else:
        collection = ax.collections[-1]
        assert isinstance(collection, LineCollection)
        median = np.asarray(collection.get_segments()[0])
        np.testing.assert_allclose(median[:, vd], [expected] * 2)
    lo, hi = ax.get_xlim() if orient == "h" else ax.get_ylim()
    assert lo > 0 and hi >= 9


def test_axis_space_violin_matches_independent_native_log_kde_grid():
    values = [1, 2, 4, 8, 16, 32, 64]
    p = (
        mp.plot({"c": [10] * 7, "v": values})
        .violin(
            "c",
            "v",
            native_scale=True,
            stat_scale="axis",
            points=37,
            showmeans=True,
            showextrema=True,
        )
        .yscale("log")
    )
    ax = p.render().axes[0]
    _, reference = plt.subplots()
    parts = reference.violinplot(
        [np.log10(values)],
        positions=[10],
        widths=0.8,
        points=37,
        showmeans=True,
        showmedians=True,
    )
    parts = cast(dict[str, Any], parts)
    expected = np.asarray(parts["bodies"][0].get_paths()[0].vertices).copy()
    expected[:, 1] = 10 ** expected[:, 1]
    np.testing.assert_allclose(
        np.asarray(ax.collections[0].get_paths()[0].vertices), expected
    )
    for collection in ax.collections[1:]:
        assert isinstance(collection, LineCollection)
        assert all((np.asarray(s)[:, 1] > 0).all() for s in collection.get_segments())


def test_axis_space_letter_area_widths_and_observed_tails_remain_raw():
    values = [1, 2, 4, 8, 16, 32, 64, 128]
    p = (
        mp.plot({"c": [10] * 8, "v": values})
        .boxenplot(
            "c",
            "v",
            native_scale=True,
            stat_scale="axis",
            k_depth=3,
            width_method="area",
        )
        .yscale("log")
    )
    ax = p.render().axes[0]
    summary = letter_value_summary(np.log10(values), k_depth=3, width_method="area")
    for i, path in enumerate(ax.collections[0].get_paths()):
        v = np.asarray(path.vertices)
        np.testing.assert_allclose(
            [v[:, 1].min(), v[:, 1].max()], 10 ** np.asarray(summary.values[i : i + 2])
        )
        np.testing.assert_allclose(
            v[:, 0].max() - v[:, 0].min(), 0.8 * summary.widths[i]
        )
    np.testing.assert_allclose(np.asarray(ax.lines[-1].get_ydata()), [1, 128])


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_legacy_single_column_default_log_statistics_and_category_coordinates_stay(
    kind,
):
    p = getattr(mp.plot({"v": [1, 9]}), kind)("v").yscale("log")
    ax = p.render().axes[0]
    verts = _vertices(ax, kind)[0]
    assert (verts[:, 0].max() + verts[:, 0].min()) / 2 == 1
    if kind == "box":
        np.testing.assert_allclose(np.asarray(ax.lines[4].get_ydata()), [5, 5])
    p = getattr(mp.plot({"v": [1, 2, 3, 4]}), kind)("v").xscale("log")
    assert mp.validate(p.spec) == [] and p.render().axes[0].get_xscale() == "log"


@pytest.mark.parametrize("kind", SUMMARIES)
def test_native_single_column_group_and_joint_hue_widths(kind):
    p = getattr(mp.plot({"v": [1, 2, 3, 4], "c": [10, 10, 40, 40]}), kind)(
        "v", group="c", native_scale=True, width=0.5
    )
    assert mp.validate(p.spec) == []
    verts = _vertices(p.render().axes[0], kind)[0]
    np.testing.assert_allclose(verts[:, 0].max() - verts[:, 0].min(), 15)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_native_log_swarm_clearance_raw_values_bounds_and_repeated_draws(orient):
    p = mp.plot({"c": [10] * 12 + [100] * 12, "v": [1] * 12 + [2] * 12}).swarmplot(
        "c", "v", native_scale=True, orient=orient, marker_size=2, warn_thresh=0
    )
    (p.yscale if orient == "h" else p.xscale)("log")
    fig = p.render()
    ax = fig.axes[0]
    collection = ax.collections[0]
    assert isinstance(collection, SwarmCollection)
    catdim = int(orient == "h")
    for dpi in (90, 180):
        fig.set_dpi(dpi)
        fig.set_size_inches(7, 3)
        fig.canvas.draw()
        offsets = np.asarray(collection.get_offsets())
        np.testing.assert_array_equal(offsets[:, 1 - catdim], [1] * 12 + [2] * 12)
        for ids, lo, hi in collection._cells:
            assert ((offsets[ids, catdim] >= lo) & (offsets[ids, catdim] <= hi)).all()
            display = ax.transData.transform(offsets[ids])
            distances = np.linalg.norm(
                display[:, None, :] - display[None, :, :], axis=2
            )
            diameter = (2 + 0.5) * dpi / 72
            assert np.min(distances + np.eye(len(ids)) * 1e6) >= diameter * (1 - 1e-7)
        before = offsets.copy()
        fig.canvas.draw()
        np.testing.assert_array_equal(collection.get_offsets(), before)
    (ax.invert_yaxis if orient == "h" else ax.invert_xaxis)()
    fig.canvas.draw()
    assert collection.crowded_count == 0


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "options",
    [
        {"native_scale": "yes"},
        {"native_scale": True, "order": [10, "other"]},
        {"native_scale": True, "width": 2},
        {"native_scale": True, "dodge": 2},
    ],
)
def test_native_bad_flags_levels_spans_fail_before_matplotlib(kind, options):
    p = getattr(mp.plot({"c": [10, 10], "v": [1, 2]}), kind)("c", "v", **options)
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("kind", KINDS)
def test_log_checks_selected_values_and_reserved_category_levels(kind):
    p = getattr(mp.plot({"c": [10, 10, 40], "v": [1, 2, 0]}), kind)(
        "c", "v", native_scale=True, order=[10]
    ).yscale("log")
    assert mp.validate(p.spec) == []
    p = getattr(mp.plot({"c": [10, 10], "v": [1, 2]}), kind)(
        "c", "v", native_scale=True, order=[10, 0]
    ).xscale("log")
    assert any("positive" in i for i in mp.validate(p.spec))
    p = getattr(mp.plot({"c": [10, 10], "v": [0, 2]}), kind)("c", "v").yscale("log")
    assert any("positive" in i for i in mp.validate(p.spec))


def test_spacing_rejects_collapsed_float_log_or_overflow_coordinates():
    for levels, scale in [
        ([2**60, 2**60 + 1], "linear"),
        ([1e100, np.nextafter(1e100, np.inf)], "log"),
        ([-1e308, 1e308], "linear"),
    ]:
        with pytest.raises(ValueError):
            native_category_geometry(levels, scale)
    assert native_category_geometry([10], "log") == ([1], 1)


def test_mixed_native_ordinal_shared_scales_and_ignored_flags_fail():
    p = mp.plot({"c": [10, 10], "v": [1, 2]}).box("c", "v", native_scale=True)
    p.swarmplot("c", "v")
    assert any("mixes native and ordinal" in i for i in mp.validate(p.spec))
    q = mp.plot({"c": [10, 10], "v": [1, 2]}).layout(1, 2).share(x="all")
    q.box("c", "v", native_scale=True, panel=0).box(
        "c", "v", native_scale=True, panel=1
    )
    q.xscale("log", panel=0)
    assert any("conflicting scale" in i for i in mp.validate(q.spec))
    p = mp.plot({"c": [10, 10], "v": [1, 2]}).swarmplot("c", "v", stat_scale="axis")
    assert any("stat_scale is not supported" in i for i in mp.validate(p.spec))
    p = mp.plot({"c": [10, 10], "v": [1, 2]}).barplot("c", "v", native_scale=True)
    assert mp.validate(p.spec) == []  # statistical native coordinates are supported
    p = mp.plot({"c": [10, 10], "v": [1, 2]}).scatter("c", "v", native_scale=True)
    assert any("native_scale is not supported" in i for i in mp.validate(p.spec))


def test_native_schema_editor_actions_and_repeatable_exports(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    session = EditorSession()
    session.dispatch_safe(A.SetData({"c": [10] * 4 + [100] * 4, "v": [1, 2, 4, 8] * 2}))
    session.dispatch_safe(A.SetScale("x", "log"))
    session.dispatch_safe(A.SetScale("y", "log"))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "boxenplot",
            "layer_json": json.dumps(
                {"x": "c", "y": "v", "native_scale": True, "stat_scale": "axis"}
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    jsonschema.Draft202012Validator(mp.json_schema()).validate(
        session.store.state.to_dict()
    )
    p = mp.Plot.from_json(mp.to_json(session.store.state))
    assert mp.apply([A.action_to_dict(a) for a in session.store.history]) == p.spec
    before = np.random.get_state()
    for fmt in ("png", "pdf", "svg"):
        one, two = tmp_path / f"one.{fmt}", tmp_path / f"two.{fmt}"
        plt.close(p.save(str(one)))
        plt.close(p.save(str(two)))
        assert one.read_bytes() == two.read_bytes()
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
