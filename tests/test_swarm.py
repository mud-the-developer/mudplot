"""Circle clearance at actual draw-time transforms, not fixed jitter."""

from __future__ import annotations

import json
import warnings

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from mudplot._categorical import MAX_SWARM_POINTS
from mudplot._swarm import SwarmCollection, pack_circles


def _collection(ax) -> SwarmCollection:
    return next(c for c in ax.collections if isinstance(c, SwarmCollection))


def _assert_clearance(ax, *, crowded=False):
    collection = _collection(ax)
    points = ax.transData.transform(collection.get_offsets())
    diameter = (
        (np.sqrt(collection.get_sizes()[0]) + np.asarray(collection.get_linewidth())[0])
        * ax.figure.dpi
        / 72
    )
    distances = np.sqrt(((points[:, None, :] - points[None, :, :]) ** 2).sum(axis=2))
    pairs = distances[np.triu_indices(len(points), 1)]
    if not crowded:
        assert collection.crowded_count == 0
        assert np.all(pairs >= diameter - 1e-6), (pairs.min(), diameter)
    assert np.isfinite(points).all()
    return collection


def test_interval_packer_preserves_order_and_circle_clearance():
    rng = np.random.default_rng(42)
    cases = [np.zeros(35), np.arange(35), np.ones(1)]
    cases += [rng.uniform(-10, 10, size=n) for n in range(1, 36)]
    cases += [np.round(rng.uniform(-2, 2, size=35), 1) for _ in range(30)]
    for values in cases:
        offsets, crowded = pack_circles(values, 2, 100)
        assert crowded == 0 and abs(offsets).max() <= 100
        np.testing.assert_array_equal(offsets, pack_circles(values, 2, 100)[0])
        for i in range(len(values)):
            for j in range(i):
                assert (
                    np.hypot(offsets[i] - offsets[j], values[i] - values[j]) >= 2 - 1e-7
                )


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("dpi", [72, 160, 300])
@pytest.mark.parametrize("log", [False, True])
def test_swarm_has_actual_pixel_clearance_for_orientation_dpi_and_log_values(
    orient, dpi, log
):
    values = [1, 1, 1.001, 1.001, 1.01, 1.01, 2, 2, 2.001, 2.001]
    data = {"cat": ["A"] * len(values), "value": values}
    p = (
        mp.plot(data)
        .swarmplot("cat", "value", orient=orient, marker_size=7, line_width=1.5)
        .size(4, 3)
    )
    from mudplot import actions as A

    p.dispatch(A.SetDpi(dpi))
    if log:
        p = p.xscale("log") if orient == "h" else p.yscale("log")
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    collection = _assert_clearance(ax)
    np.testing.assert_array_equal(
        np.asarray(collection.get_offsets())[:, 0 if orient == "h" else 1], values
    )
    assert np.ptp(np.asarray(collection.get_offsets())[:, int(orient == "h")]) > 0


@pytest.mark.parametrize("orient", ["v", "h"])
def test_each_draw_repacks_after_resize_limits_scale_and_dpi_without_drift(orient):
    values = [1] * 6 + [1.01] * 4
    p = (
        mp.plot({"x": ["A"] * len(values), "y": values})
        .swarmplot("x", "y", orient=orient)
        .size(5, 4)
    )
    fig = p.render()
    ax = fig.axes[0]
    for size, dpi, log in (
        ([4, 4], 72, False),
        ([5, 3], 250, True),
        ([4, 4], 72, False),
    ):
        fig.set_size_inches(size[0], size[1])
        fig.set_dpi(dpi)
        scale = ax.set_xscale if orient == "h" else ax.set_yscale
        limits = ax.set_xlim if orient == "h" else ax.set_ylim
        scale("log" if log else "linear")
        limits(0.7, 2)
        fig.canvas.draw()
        collection = _assert_clearance(ax)
        first = np.asarray(collection.get_offsets()).copy()
        fig.canvas.draw()
        np.testing.assert_allclose(
            np.asarray(collection.get_offsets()), first, atol=1e-12
        )
        np.testing.assert_array_equal(
            np.asarray(collection.get_offsets())[:, 0 if orient == "h" else 1], values
        )


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("dodge", [None, 0, 0.5])
def test_hue_order_empty_slots_and_non_dodged_hues_pack_jointly(orient, dodge):
    data = {"cat": ["B", "A"] * 6, "y": [1] * 12, "g": ["u"] * 6 + ["v"] * 6}
    p = (
        mp.plot(data)
        .swarmplot(
            "cat",
            "y",
            group="g",
            orient=orient,
            order=["A", "empty", "B"],
            hue_order=["v", "absent", "u"],
            dodge=dodge,
            marker_size=4,
            gap=0.1,
        )
        .size(6, 5)
    )
    ax = p.render().axes[0]
    collection = _assert_clearance(ax)
    assert len(np.asarray(collection.get_offsets())) == 12
    labels = ax.get_yticklabels() if orient == "h" else ax.get_xticklabels()
    assert [t.get_text() for t in labels] == ["A", "empty", "B"]
    assert ax.get_legend_handles_labels()[1] == ["v", "u"]
    rgba = np.asarray(collection.get_facecolor())
    np.testing.assert_allclose(rgba[0], rgba[5])
    assert not np.array_equal(rgba[0], rgba[6])
    assert all(len(np.asarray(line.get_xdata())) == 0 for line in ax.lines)
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_final_multiplot_layout_and_outside_legend_still_have_clearance():
    data = {"x": ["A"] * 6, "y": [1] * 6, "g": ["a"] * 3 + ["b"] * 3}
    p = mp.plot(data).layout(1, 2).size(7, 3)
    for panel in range(2):
        p.swarmplot("x", "y", group="g", marker_size=5, panel=panel)
        p.legend(location="outside right", title="A long group legend", panel=panel)
    for ax in p.render().axes:
        _assert_clearance(ax)


def test_missing_and_unselected_rows_are_not_invented_or_packed():
    data = {
        "x": ["A", "A", "A", "B", None, "A"],
        "y": [1, 1, None, 10, 5, 1],
        "g": ["u", "u", "u", "v", "u", None],
    }
    p = mp.plot(data).swarmplot(
        "x", "y", group="g", order=["A", "empty"], hue_order=["u"]
    )
    collection = _assert_clearance(p.render().axes[0])
    np.testing.assert_array_equal(np.asarray(collection.get_offsets())[:, 1], [1, 1])


def test_overcrowding_retains_all_rows_and_warns_once():
    data = {"x": ["A"] * 100, "y": [1] * 100}
    p = (
        mp.plot(data)
        .swarmplot("x", "y", width=0.1, marker_size=12, warn_thresh=0)
        .size(3, 2)
    )
    with pytest.warns(UserWarning, match="retained at gutters") as captured:
        fig = p.render()
    assert len(captured) == 1
    collection = _assert_clearance(fig.axes[0], crowded=True)
    assert collection.crowded_count > 0
    assert len(np.asarray(collection.get_offsets())) == 100
    np.testing.assert_array_equal(np.asarray(collection.get_offsets())[:, 1], data["y"])
    with warnings.catch_warnings(record=True) as repeated:
        warnings.simplefilter("always")
        fig.canvas.draw()
    assert not any("swarmplot" in str(w.message) for w in repeated)


def test_even_single_marker_too_wide_for_a_slot_is_reported():
    p = mp.plot({"x": ["A"], "y": [1]}).swarmplot("x", "y", width=0.001, warn_thresh=0)
    with pytest.warns(UserWarning, match="1/1 observations"):
        ax = p.render().axes[0]
    assert _collection(ax).crowded_count == 1


@pytest.mark.parametrize(
    "options,message",
    [
        ({"orient": "horizontal"}, "orient"),
        ({"width": 0}, "width"),
        ({"width": 1.1}, "width"),
        ({"width": True}, "width"),
        ({"dodge": True}, "dodge"),
        ({"dodge": 0.9}, "dodge"),
        ({"gap": 1}, "gap"),
        ({"warn_thresh": True}, "warn_thresh"),
        ({"warn_thresh": -0.1}, "warn_thresh"),
        ({"marker": "s"}, "circular"),
        ({"marker_size": 0}, "positive"),
        ({"marker_size": 1001}, "<=1000"),
        ({"line_width": -1}, "line_width"),
        ({"line_width": True}, "line_width"),
        ({"order": []}, "nonempty"),
        ({"hue_order": ["u"]}, "hue_order"),
        ({"jitter": 0.1}, "not supported"),
        ({"c": "y"}, "not supported"),
        ({"stat": mp.StatSpec()}, "not supported"),
        ({"bw_method": "scott"}, "not supported"),
        ({"axis": "y2"}, "axis is not supported"),
    ],
)
def test_bad_or_ignored_options_fail_before_packing(options, message):
    p = mp.plot({"x": ["A", "A"], "y": [1, 2]}).swarmplot("x", "y", **options)
    assert any(message in issue for issue in mp.validate(p.spec)), mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "values,message",
    [
        ([1, True], "finite numbers"),
        ([1, "2"], "finite numbers"),
        ([1, float("inf")], "finite numbers"),
        ([None, float("nan")], "no usable"),
    ],
)
def test_invalid_observations_fail_explicitly(values, message):
    p = mp.plot({"x": ["A", "A"], "y": values}).swarmplot("x", "y")
    assert any(message in issue for issue in mp.validate(p.spec))


def test_log_value_positivity_ordinal_category_and_resource_bounds():
    p = mp.plot({"x": ["A", "A"], "y": [0, 1]}).swarmplot("x", "y").yscale("log")
    assert any("must be positive" in i for i in mp.validate(p.spec))
    p = mp.plot({"x": ["A"], "y": [1]}).swarmplot("x", "y").xscale("log")
    assert any("requires native_scale" in i for i in mp.validate(p.spec))
    p = mp.plot(
        {"x": ["A"] * (MAX_SWARM_POINTS + 1), "y": [1] * (MAX_SWARM_POINTS + 1)}
    ).swarmplot("x", "y")
    assert any("at most 2000" in i for i in mp.validate(p.spec))


def test_shared_order_and_box_overlay_align_and_conflicts_fail():
    data = {"x": ["B", "A"] * 4, "y": [1, 2, 1, 2, 1, 2, 1, 2]}
    p = (
        mp.plot(data)
        .box("x", "y", order=["A", "B"], width=0.6)
        .swarmplot("x", "y", order=["A", "B"])
    )
    _assert_clearance(p.render().axes[0])
    bad = (
        mp.plot(data)
        .box("x", "y", order=["A", "B"])
        .swarmplot("x", "y", order=["B", "A"])
    )
    with pytest.raises(ValueError, match="conflicting category order"):
        bad.render()


def test_schema_actions_editor_png_and_deterministic_export_without_rng(tmp_path):
    import jsonschema
    import matplotlib.pyplot as plt
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    data = {"x": ["A"] * 6, "y": [1, 1, 1, 2, 2, 2]}
    p = mp.plot(data).swarmplot("x", "y", orient="h", label="Observations")
    jsonschema.Draft202012Validator(mp.json_schema()).validate(p.spec.to_dict())
    before = np.random.get_state()
    for fmt in ("png", "svg", "pdf"):
        a, b = tmp_path / f"a.{fmt}", tmp_path / f"b.{fmt}"
        plt.close(p.save(str(a)))
        plt.close(p.save(str(b)))
        assert a.read_bytes() == b.read_bytes()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    session = EditorSession()
    session.dispatch_safe(A.SetData(data))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "swarmplot",
            "layer_json": json.dumps({"x": "x", "y": "y", "orient": "h"}),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert (
        mp.apply([A.action_to_dict(a) for a in session.store.history])
        == session.store.state
    )
