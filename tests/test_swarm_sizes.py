"""Pairwise display-space clearance after normal native artist size edits."""

import copy
import warnings

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._swarm import SwarmCollection, pack_circles


def _collection(ax) -> SwarmCollection:
    return next(c for c in ax.collections if isinstance(c, SwarmCollection))


def _pixel_clearance(ax):
    c = _collection(ax)
    offsets = np.asarray(c.get_offsets(), dtype=float)
    points = ax.transData.transform(offsets)
    n = len(points)
    areas = np.resize(np.asarray(c.get_sizes(), dtype=float), n)
    widths = np.resize(np.asarray(c.get_linewidth(), dtype=float), n)
    diameters = (np.sqrt(areas) + widths) * ax.figure.dpi / 72
    distance = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    required = (diameters[:, None] + diameters[None, :]) / 2
    pairs = np.triu_indices(n, 1)
    assert c.crowded_count == 0
    assert np.all(distance[pairs] >= required[pairs] - 1e-6)
    axis = c._category_axis
    for indices, lower, upper in c._cells:
        edges = np.repeat(c._base_offsets[indices[:1]], 2, axis=0)
        edges[:, axis] = [lower, upper]
        left, right = np.sort(ax.transData.transform(edges)[:, axis])
        assert np.all(points[indices, axis] - diameters[indices] / 2 >= left - 1e-6)
        assert np.all(points[indices, axis] + diameters[indices] / 2 <= right + 1e-6)
    return c


@pytest.mark.parametrize(
    "values,bound,expected,crowded",
    [
        ([0] * 5, 20, [0.0, -2.0000002, 2.0000002, -4.0000004, 4.0000004], 0),
        (
            [0, 0, 1, 1, 3, 0],
            20,
            [0.0, -2.0000002, -3.7320512385089817, 3.7320512385089817, 0.0, 2.0000002],
            0,
        ),
        ([0] * 5, 1, [0.0, 1.0, -1.0, 1.0, 1.0], 4),
    ],
)
def test_uniform_legacy_offsets_are_unchanged(values, bound, expected, crowded):
    actual, count = pack_circles(values, 2, bound)
    np.testing.assert_array_equal(actual, expected)
    assert count == crowded
    vector, vector_count = pack_circles(
        values, np.full(len(values), 2.0), np.full(len(values), float(bound))
    )
    np.testing.assert_array_equal(vector, expected)
    assert vector_count == crowded


def test_variable_packer_uses_pair_sums_not_the_largest_radius_for_every_mark():
    diameter = np.array([20.0, 2.0, 2.0])
    values = np.zeros(3)
    offsets, count = pack_circles(values, diameter, np.full(3, 100.0))
    assert count == 0
    np.testing.assert_allclose(np.abs(offsets[1:]), 11 * (1 + 1e-7))
    assert offsets[1] * offsets[2] < 0
    # A later large radius must still see earlier marks that a small one did not.
    offsets, count = pack_circles([0.0, 1.0, 2.0], np.array([0.2, 0.2, 5.0]), 100.0)
    assert count == 0
    for i in range(3):
        for j in range(i):
            assert (
                np.hypot(offsets[i] - offsets[j], i - j)
                >= (np.array([0.2, 0.2, 5.0])[i] + np.array([0.2, 0.2, 5.0])[j]) / 2
                - 1e-7
            )


def test_random_variable_packing_is_deterministic_and_respects_each_gutter():
    rng = np.random.default_rng(31)
    for n in range(1, 25):
        values = np.round(rng.uniform(-5, 5, n), 1)
        diameters = rng.uniform(0.2, 4, n)
        bounds = rng.uniform(45, 60, n)
        offsets, count = pack_circles(values, diameters, bounds)
        assert count == 0 and np.all(np.abs(offsets) <= bounds)
        np.testing.assert_array_equal(
            offsets, pack_circles(values, diameters, bounds)[0]
        )
        for i in range(n):
            for j in range(i):
                assert (
                    np.hypot(offsets[i] - offsets[j], values[i] - values[j])
                    >= (diameters[i] + diameters[j]) / 2 - 1e-7
                )


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("dpi", [72, 200])
@pytest.mark.parametrize("log", [False, True])
def test_native_sizes_and_linewidths_repack_joint_hues_at_actual_transforms(
    orient, dpi, log
):
    values = [1.0, 1.0, 1.001, 1.001, 1.01, 1.01]
    p = (
        mp.plot({"cat": ["A"] * 6, "value": values, "hue": ["u", "v"] * 3})
        .swarmplot("cat", "value", group="hue", orient=orient, dodge=0, marker_size=4)
        .size(6, 4)
    )
    before = copy.deepcopy(p.spec)
    p.dispatch(mp.actions.SetDpi(dpi))
    if log:
        if orient == "h":
            p.xscale("log")
        else:
            p.yscale("log")
    expected = copy.deepcopy(p.spec)
    fig = p.render()
    try:
        ax = fig.axes[0]
        c = _collection(ax)
        base = np.asarray(c.get_offsets(), dtype=float)[
            :, 0 if orient == "h" else 1
        ].copy()
        c.set_sizes([9, 100, 36, 196, 49, 16])
        c.set_linewidth([0, 0.5, 1.5, 0.25, 0, 2])
        for size, next_dpi in (((6, 4), dpi), ((7, 5), dpi * 1.5), ((6, 4), dpi)):
            fig.set_size_inches(*size)
            fig.set_dpi(next_dpi)
            fig.canvas.draw()
            _pixel_clearance(ax)
            np.testing.assert_array_equal(
                np.asarray(c.get_offsets(), dtype=float)[:, 0 if orient == "h" else 1],
                base,
            )
            first = np.asarray(c.get_offsets(), dtype=float).copy()
            fig.canvas.draw()
            np.testing.assert_allclose(
                np.asarray(c.get_offsets(), dtype=float), first, atol=1e-12
            )
        assert p.spec == expected and before.data == p.spec.data
        assert len(ax.collections) == 1
    finally:
        plt.close(fig)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_variable_radii_keep_native_log_category_gutters_after_inversion(orient):
    p = (
        mp.plot({"cat": [1, 1, 10, 10], "value": [1.0] * 4})
        .swarmplot("cat", "value", orient=orient, native_scale=True, marker_size=3)
        .size(7, 4)
    )
    if orient == "v":
        p.xscale("log")
    else:
        p.yscale("log")
    fig = p.render()
    try:
        ax = fig.axes[0]
        c = _collection(ax)
        c.set_sizes([4, 100, 36, 196])
        c.set_linewidth([0.5, 1])
        fig.canvas.draw()
        _pixel_clearance(ax)
        if orient == "v":
            ax.invert_xaxis()
        else:
            ax.invert_yaxis()
        fig.canvas.draw()
        _pixel_clearance(ax)
    finally:
        plt.close(fig)


def test_zero_size_and_zero_stroke_still_preserve_rows():
    fig = (
        mp.plot({"cat": ["A"] * 2, "value": [1.0] * 2})
        .swarmplot("cat", "value")
        .render()
    )
    try:
        c = _collection(fig.axes[0])
        c.set_sizes([0, 1])
        c.set_linewidth(0)
        fig.canvas.draw()
        _pixel_clearance(fig.axes[0])
        assert len(np.asarray(c.get_offsets())) == 2
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "widths", [[], [0.1, 0.2, 0.3], [-1, 0.5], [float("nan"), 0.5], [float("inf"), 0.5]]
)
def test_invalid_native_linewidth_arrays_reject_without_repacking(widths):
    fig = (
        mp.plot({"cat": ["A"] * 2, "value": [1.0] * 2})
        .swarmplot("cat", "value")
        .render()
    )
    try:
        c = _collection(fig.axes[0])
        before = np.asarray(c.get_offsets()).copy()
        with pytest.raises(ValueError):
            c.set_linewidth(widths)
            fig.canvas.draw()
        np.testing.assert_array_equal(c.get_offsets(), before)
    finally:
        plt.close(fig)


def test_native_edit_does_not_claim_style_semantics():
    p = mp.plot({"cat": ["A", "A"], "value": [1, 1], "size": [2, 3]}).swarmplot(
        "cat",
        "value",
        semantics={"size": "size", "scale_id": "shared", "style": "size"},
    )
    with pytest.raises(ValueError, match="not supported"):
        p.render()


def test_native_short_size_arrays_cycle_and_do_not_invent_rows():
    fig = (
        mp.plot({"cat": ["A"] * 6, "value": [1.0] * 6})
        .swarmplot("cat", "value", marker_size=4)
        .size(7, 4)
        .render()
    )
    try:
        ax = fig.axes[0]
        c = _collection(ax)
        c.set_sizes([16, 400])
        c.set_linewidth([0.5, 1.5, 0])
        random_before = np.random.get_state()
        fig.canvas.draw()
        random_after = np.random.get_state()
        assert random_before[0] == random_after[0]
        np.testing.assert_array_equal(random_before[1], random_after[1])
        assert random_before[2:] == random_after[2:]
        _pixel_clearance(ax)
        assert len(np.asarray(c.get_offsets())) == 6
        np.testing.assert_array_equal(c.get_sizes(), [16, 400])
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "size,area,expected", [((2, 8), 40000, 1), ((4, 3), 1000000, 2)]
)
def test_oversized_and_colliding_rows_are_counted_once_and_retained(
    size, area, expected
):
    p = (
        mp.plot({"cat": ["A"] * 3, "value": [0.0, 100.0, 200.0]})
        .swarmplot("cat", "value", marker_size=2, warn_thresh=0)
        .size(*size)
    )
    fig = p.render()
    try:
        c = _collection(fig.axes[0])
        c.set_sizes([1, area, 1])
        with pytest.warns(UserWarning, match=f"{expected}/3 observations") as caught:
            fig.canvas.draw()
        assert len(caught) == 1 and c.crowded_count == expected
        np.testing.assert_array_equal(np.asarray(c.get_offsets())[:, 1], [0, 100, 200])
        with warnings.catch_warnings(record=True) as repeated:
            warnings.simplefilter("always")
            fig.canvas.draw()
        assert not any("swarmplot" in str(w.message) for w in repeated)
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "areas", [[], [1, 2, 3], [float("nan"), 1], [float("inf"), 1], [1e308, 1]]
)
def test_invalid_native_size_arrays_reject_before_offset_mutation(areas):
    fig = (
        mp.plot({"cat": ["A"] * 2, "value": [1.0, 1.0]})
        .swarmplot("cat", "value")
        .render()
    )
    try:
        c = _collection(fig.axes[0])
        before = np.asarray(c.get_offsets()).copy()
        c.set_sizes(areas)
        with pytest.raises(ValueError):
            fig.canvas.draw()
        np.testing.assert_array_equal(c.get_offsets(), before)
    finally:
        plt.close(fig)
