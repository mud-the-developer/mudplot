"""N12 consumer geometry/labels/domains; independent scalar and datetime oracles."""

from __future__ import annotations

import math
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


def plot_xy(x=(0, 1, 2), y=(1, 2, 1)):
    return mp.plot({"x": list(x), "y": list(y)}).line("x", "y", marker="o")


def test_multiple_offset_and_minor_subdivision_positions_are_axis_coordinates():
    p = plot_xy().xlim(0, 2)
    p.ticks("x", {"locator": {"kind": "multiple", "step": 0.5, "offset": 0.25}})
    p.ticks("x", {"locator": {"kind": "auto_minor", "subdivisions": 4}}, which="minor")
    fig = p.render()
    try:
        axis = fig.axes[0]
        np.testing.assert_allclose(
            axis.get_xticks(), [-0.25, 0.25, 0.75, 1.25, 1.75, 2.25]
        )
        minor = axis.get_xticks(minor=True)
        assert 0.125 in minor and 0.375 in minor and 0.25 not in minor
    finally:
        plt.close(fig)


def test_locator_requested_interval_and_failed_huge_request_leave_active_view_usable():
    p = plot_xy().xlim(0, 2).ticks("x", {"locator": {"kind": "multiple", "step": 1}})
    fig = p.render()
    try:
        axis = fig.axes[0]
        locator = axis.xaxis.get_major_locator()
        np.testing.assert_array_equal(locator.tick_values(10, 12), [9, 10, 11, 12, 13])
        with pytest.raises(ValueError, match="512"):
            locator.tick_values(0, 1e100)
        fig.canvas.draw()
        np.testing.assert_array_equal(axis.get_xticks(), [-1, 0, 1, 2, 3])
        np.testing.assert_array_equal(axis.get_xlim(), [0, 2])
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "values", [[True, 2], [2**54, 2**54 + 1], [1, 1], [2, 1], [1, float("inf")]]
)
def test_fixed_coordinates_reject_bool_order_and_float_collapse(values):
    with pytest.raises((ValueError, TypeError)):
        plot_xy().ticks(
            "x", mp.TickSpec(locator=mp.LocatorSpec(kind="fixed", values=values))
        )


@pytest.mark.parametrize("kind", ["line", "stripplot", "swarmplot"])
def test_ordinal_auto_keeps_visible_category_names_and_rejects_numeric_relabeling(kind):
    p = mp.plot({"c": ["A", "B", "C"], "v": [1, 2, 1]})
    if kind == "stripplot":
        p.stripplot("c", "v", strip={"jitter_policy": "none"})
    else:
        getattr(p, kind)("c", "v")
    p.ticks("x", {"locator": {"kind": "auto"}})
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        np.testing.assert_array_equal(axis.get_xticks(), [0, 1, 2])
        assert [text.get_text() for text in axis.get_xticklabels()] == ["A", "B", "C"]
    finally:
        plt.close(fig)
    p.ticks("x", {"locator": {"kind": "multiple", "step": 0.5}})
    with pytest.raises(ValueError, match="ordinal"):
        p.render()


def test_percent_and_engineering_labels_keep_declared_numeric_units():
    p = plot_xy((0, 1500, 3000), (0, 0.5, 1)).xlim(0, 3000).ylim(0, 1)
    p.ticks(
        "x",
        {
            "locator": {"kind": "linear", "count": 3},
            "formatter": {"kind": "engineering", "unit": "V", "precision": 1},
        },
    )
    p.ticks(
        "y",
        {
            "locator": {"kind": "linear", "count": 5},
            "formatter": {"kind": "percent", "xmax": 1, "decimals": 1},
        },
    )
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        assert [text.get_text() for text in axis.get_xticklabels()] == [
            "0.0 V",
            "1.5 kV",
            "3.0 kV",
        ]
        assert [text.get_text() for text in axis.get_yticklabels()] == [
            "0.0%",
            "25.0%",
            "50.0%",
            "75.0%",
            "100.0%",
        ]
    finally:
        plt.close(fig)


def test_max_n_integer_pruning_and_safe_fixed_decimal_output():
    p = plot_xy((0, 5, 10)).xlim(0, 10)
    p.ticks(
        "x",
        {
            "locator": {"kind": "max_n", "nbins": 5, "integer": True, "prune": "lower"},
            "formatter": {
                "kind": "number",
                "notation": "fixed",
                "precision": 2,
                "suffix": " s",
            },
        },
    )
    fig = p.render()
    try:
        fig.canvas.draw()
        np.testing.assert_array_equal(fig.axes[0].get_xticks(), [2, 4, 6, 8, 10])
        assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == [
            "2.00 s",
            "4.00 s",
            "6.00 s",
            "8.00 s",
            "10.00 s",
        ]
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "formatter",
    [
        {"kind": "number", "precision": 1_000_000},
        {"kind": "number", "notation": "general", "precision": 0},
        {"kind": "number", "template": "{x.__class__}"},
    ],
)
def test_unbounded_or_attribute_formatting_is_not_a_tick_language(formatter):
    with pytest.raises((ValueError, TypeError)):
        plot_xy().ticks("x", {"formatter": formatter})


def test_shared_none_inherits_tick_geometry_and_conflicting_explicit_requests_reject():
    p = plot_xy().line("x", "y", panel=1).layout(1, 2)
    p.dispatch(mp.actions.SetShare(x="all"))
    p.ticks("x", {"locator": {"kind": "multiple", "step": 0.5, "offset": 0.25}})
    fig = p.render()
    try:
        left, right = fig.axes
        assert left.get_shared_x_axes().joined(left, right)
        for axis in (left, right):
            np.testing.assert_allclose(
                axis.get_xticks(), [-0.25, 0.25, 0.75, 1.25, 1.75, 2.25]
            )
    finally:
        plt.close(fig)
    p.ticks("x", {"locator": {"kind": "multiple", "step": 1}}, panel=1)
    with pytest.raises(ValueError, match="conflicting explicit"):
        p.render()


def test_figure_tick_bound_counts_every_inherited_physical_axis():
    p = mp.plot({"x": [0, 1], "y": [0, 1]}).layout(3, 11)
    for panel in range(33):
        p.line("x", "y", panel=panel)
    p.dispatch(mp.actions.SetShare(x="all"))
    p.ticks("x", {"locator": {"kind": "fixed", "values": list(range(512))}})
    with pytest.raises(ValueError, match="16384"):
        p.render()


@pytest.mark.parametrize(
    "kind,options",
    [
        ("symlog", {"base": 2, "linthresh": 1, "linscale": 2}),
        ("asinh", {"linear_width": 2, "base": 10}),
    ],
)
def test_signed_native_scale_geometry_matches_closed_transform(kind, options):
    x = [-100, -1, 0, 1, 100]
    p = plot_xy(x, range(5)).axis_scale("x", kind, options=options).xlim(-100, 100)
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        actual = (
            axis.lines[0].get_transform().transform(axis.lines[0].get_xydata())[:, 0]
        )
        actual = (actual - axis.bbox.x0) / axis.bbox.width
        if kind == "asinh":
            transformed = [2 * math.asinh(value / 2) for value in x]
        else:
            transformed = [
                value * 4
                if abs(value) <= 1
                else math.copysign(4 + math.log2(abs(value)), value)
                for value in x
            ]
        expected = [
            (v - transformed[0]) / (transformed[-1] - transformed[0])
            for v in transformed
        ]
        np.testing.assert_allclose(actual, expected, atol=1e-12)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("axis_name", ["x", "y", "y2"])
def test_constant_logit_probabilities_are_visible_and_complement_symmetric(axis_name):
    fractions = {}
    for probability in (0.01, 0.5, 0.99):
        if axis_name == "x":
            p = plot_xy([probability] * 2, [1, 2])
        else:
            p = mp.plot({"x": [1, 2], "p": [probability] * 2})
            if axis_name == "y2":
                p.secondary_yaxis("Probability")
            p.line("x", "p", axis=axis_name, marker="o")
        p.axis_scale(axis_name, "logit")
        fig = p.render()
        try:
            fig.canvas.draw()
            axis = fig.axes[0 if axis_name != "y2" else 1]
            limits = axis.get_xlim() if axis_name == "x" else axis.get_ylim()
            assert 0 < limits[0] < probability < limits[1] < 1
            pixels = axis.lines[0].get_transform().transform(axis.lines[0].get_xydata())
            assert np.all((pixels[:, 0] > axis.bbox.x0) & (pixels[:, 0] < axis.bbox.x1))
            assert np.all((pixels[:, 1] > axis.bbox.y0) & (pixels[:, 1] < axis.bbox.y1))
            coordinate = pixels[0, 0 if axis_name == "x" else 1]
            origin = axis.bbox.x0 if axis_name == "x" else axis.bbox.y0
            size = axis.bbox.width if axis_name == "x" else axis.bbox.height
            fractions[probability] = (coordinate - origin) / size
        finally:
            plt.close(fig)
    assert fractions[0.01] + fractions[0.99] == pytest.approx(1)
    assert fractions[0.5] == pytest.approx(0.5)


def test_explicit_logit_view_is_not_replaced_by_constant_data_padding():
    p = plot_xy([0.99, 0.99], [1, 2]).axis_scale("x", "logit").xlim(0.98, 0.999)
    fig = p.render()
    try:
        np.testing.assert_array_equal(fig.axes[0].get_xlim(), [0.98, 0.999])
    finally:
        plt.close(fig)


@pytest.mark.parametrize("scale", ["symlog", "asinh", "logit"])
@pytest.mark.parametrize("kind", ["bar", "errorbar", "stem", "broken_barh"])
def test_nonlinear_collection_limits_use_raw_endpoints_and_retain_prior_artists(
    scale, kind
):
    x = [0.3, 0.7] if scale == "logit" else [-3, 3]
    prior_x = [0.45, 0.55] if scale == "logit" else [-0.5, 0.5]
    p = mp.plot(
        {
            "x": x,
            "y": [1, 2],
            "error": [0.1, 0.1],
            "duration": [0.1, 0.1],
            "prior_x": prior_x,
            "prior_y": [-0.5, 3],
        }
    )
    p.line("prior_x", "prior_y")
    if kind == "bar":
        p.bar("x", "y", bar_width=0.1, yerr="error")
        expected_x = [x[0] - 0.05, x[1] + 0.05]
    elif kind == "errorbar":
        p.errorbar("x", "y", yerr="error", xerr="error")
        expected_x = [x[0] - 0.1, x[1] + 0.1]
    elif kind == "stem":
        p.stem("x", "y")
        expected_x = [x[0], x[1]]
    else:
        p.broken_barh("x", "duration", bottom=0.5, height=0.1)
        expected_x = [x[0], x[1] + 0.1]
    p.axis_scale("x", scale)
    source = p.to_json()
    fig = p.render()
    try:
        axis = fig.axes[0]
        np.testing.assert_allclose(
            axis.dataLim.get_points(),
            [[expected_x[0], -0.5], [expected_x[1], 3]],
            atol=1e-12,
        )
        prior = axis.lines[0].get_xydata()
        np.testing.assert_array_equal(prior, np.c_[prior_x, [-0.5, 3]])
        corners = np.array([[expected_x[0], -0.5], [expected_x[1], 3]])
        pixels = axis.transData.transform(corners)
        assert all(axis.bbox.contains(*point) for point in pixels)
        assert axis.dataLim.minpos[0] <= min(value for value in prior_x if value > 0)
        assert p.to_json() == source
    finally:
        plt.close(fig)


def test_nonlinear_errorbar_twin_limits_do_not_replace_primary_or_prior_twin_data():
    p = (
        mp.plot(
            {
                "x": [1, 2],
                "primary": [100, 200],
                "prior": [-0.5, 3],
                "value": [0.1, 0.9],
                "error": [0.01, 0.01],
            }
        )
        .line("x", "primary")
        .secondary_yaxis("Second length")
        .line("x", "prior", axis="y2")
        .errorbar("x", "value", yerr="error", axis="y2")
        .axis_scale("y2", "asinh", options={"linear_width": 2})
    )
    fig = p.render()
    try:
        np.testing.assert_allclose(fig.axes[0].dataLim.intervaly, [100, 200])
        np.testing.assert_allclose(fig.axes[1].dataLim.intervaly, [-0.5, 3])
        np.testing.assert_allclose(fig.axes[0].lines[0].get_ydata(), [100, 200])
    finally:
        plt.close(fig)


@pytest.mark.parametrize("target", ["y", "y2"])
def test_logit_event_lane_uses_actual_half_length_and_rejects_invalid_endpoints(target):
    p = mp.plot({"event": [1, 2]})
    if target == "y2":
        p.secondary_yaxis("Events")
    p.eventplot("event", offset=0.5, length=0.8, axis=target).axis_scale(
        target, "logit"
    )
    source = p.to_json()
    fig = p.render()
    try:
        axis = fig.axes[-1]
        segments = axis.collections[0].get_segments()
        np.testing.assert_allclose(
            segments, [[[1, 0.9], [1, 0.1]], [[2, 0.9], [2, 0.1]]]
        )
        np.testing.assert_allclose(axis.dataLim.intervaly, [0.1, 0.9])
        assert all(
            axis.bbox.contains(*point)
            for point in axis.transData.transform(np.concatenate(segments))
        )
        assert p.to_json() == source
    finally:
        plt.close(fig)
    invalid = mp.plot({"event": [1, 2]}).eventplot("event", offset=0.5, length=1.2)
    invalid.axis_scale("y", "logit")
    with pytest.raises(ValueError, match="logit geometry"):
        invalid.render()


def test_declared_logit_stairs_retains_exact_raw_steps_and_visible_vertices():
    p = (
        mp.plot({"height": [0.2, 0.8]})
        .stairs("height", [0.1, 0.4, 0.9], baseline=0.3)
        .axis_scale("x", "logit")
        .axis_scale("y", "logit")
    )
    fig = p.render()
    try:
        axis = fig.axes[0]
        vertices = axis.patches[0].get_path().vertices
        np.testing.assert_allclose(
            vertices,
            [[0.1, 0.3], [0.1, 0.2], [0.4, 0.2], [0.4, 0.8], [0.9, 0.8], [0.9, 0.3]],
        )
        assert all(
            axis.bbox.contains(*point) for point in axis.transData.transform(vertices)
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("missing", [None, float("nan")])
@pytest.mark.parametrize("kind", ["line", "errorbar"])
def test_logit_missing_pair_preserves_native_gap_and_only_visible_points(kind, missing):
    from matplotlib.path import Path

    p = mp.plot({"x": [0, missing, 2], "y": [0.1, 3, 0.9], "error": [0.01, 100, 0.01]})
    getattr(p, kind)(
        "x", "y", marker="o", **({"yerr": "error"} if kind == "errorbar" else {})
    )
    p.axis_scale("y", "logit")
    source = p.to_json()
    fig = p.render()
    try:
        axis = fig.axes[0]
        path = axis.lines[0].get_path()
        segments = list(path.iter_segments(remove_nans=True, simplify=False))
        assert [code for _, code in segments] == [Path.MOVETO, Path.MOVETO]
        np.testing.assert_array_equal(
            [point for point, _ in segments], [[0, 0.1], [2, 0.9]]
        )
        np.testing.assert_array_equal(axis.lines[0].get_ydata(), [0.1, 3, 0.9])
        lo, hi = axis.get_ylim()
        assert 0 < lo < 0.1 < 0.9 < hi < 1
        assert p.to_json() == source
    finally:
        plt.close(fig)


def test_logit_band_uses_all_three_coordinate_gaps_without_joining_polygons():
    p = (
        mp.plot(
            {
                "x": [0, 1, 2, 3, 4],
                "low": [0.1, 0.2, 3, 0.6, 0.7],
                "high": [0.2, 0.3, None, 0.8, 0.9],
            }
        )
        .band("x", "low", "high")
        .axis_scale("y", "logit")
    )
    source = p.to_json()
    fig = p.render()
    try:
        paths = fig.axes[0].collections[0].get_paths()
        assert len(paths) == 2
        np.testing.assert_allclose(
            [[path.vertices[:, 0].min(), path.vertices[:, 0].max()] for path in paths],
            [[0, 1], [3, 4]],
        )
        assert all(
            np.all((path.vertices[:, 1] > 0) & (path.vertices[:, 1] < 1))
            for path in paths
        )
        assert p.to_json() == source
    finally:
        plt.close(fig)


def test_missing_pair_domain_view_does_not_hide_unparseable_native_column():
    p = mp.plot({"x": [0, None, 2], "y": [0.1, "not numeric", 0.9]}).line("x", "y")
    p.axis_scale("y", "logit")
    with pytest.raises(ValueError):
        p.render()


def test_logit_uses_actual_dodged_rectangle_edges_not_raw_center_or_full_span():
    for center, valid in ((0.3, False), (0.39, True)):
        p = (
            mp.plot({"x": [center, center], "y": [1, 2], "g": ["a", "b"]})
            .bar("x", "y", group="g", bar_width=0.8)
            .axis_scale("x", "logit")
        )
        if not valid:
            with pytest.raises(ValueError, match=r"logit.*(geometry|interval|inside)"):
                p.render()
            continue
        fig = p.render()
        try:
            fig.canvas.draw()
            np.testing.assert_allclose(
                [(p.get_x(), p.get_x() + p.get_width()) for p in fig.axes[0].patches],
                [[0.006, 0.374], [0.406, 0.774]],
            )
        finally:
            plt.close(fig)


@pytest.mark.parametrize("scale", ["log", "symlog", "asinh"])
def test_auto_major_base_powers_remain_independent_of_minor_geometric_subs(scale):
    x = [1, 2, 4, 8, 16] if scale == "log" else [-16, -8, -4, -2, -1, 0, 1, 2, 4, 8, 16]
    options = {"base": 2, "subs": [math.sqrt(2)]}
    options.update(
        {"linthresh": 1}
        if scale == "symlog"
        else {"linear_width": 1}
        if scale == "asinh"
        else {}
    )
    p = (
        plot_xy(x, range(len(x)))
        .axis_scale("x", scale, options=options)
        .xlim(min(x), max(x))
    )
    p.ticks(
        "x",
        {
            "locator": {"kind": "auto"},
            "formatter": {"kind": "number", "notation": "general", "precision": 3},
        },
    )
    p.ticks("x", {"locator": {"kind": "auto"}}, which="minor")
    fig = p.render()
    try:
        axis = fig.axes[0]
        major = axis.get_xticks()
        nonzero = np.abs(major[major != 0])
        np.testing.assert_allclose(
            np.log2(nonzero), np.rint(np.log2(nonzero)), atol=1e-14
        )
        minor = np.abs(axis.get_xticks(minor=True))
        assert len(minor) > 0
        np.testing.assert_allclose(np.log2(minor) % 1, 0.5, atol=1e-14)
        labels = dict(
            zip(
                major, (text.get_text() for text in axis.get_xticklabels()), strict=True
            )
        )
        assert [labels[value] for value in (1, 2, 4)] == ["1", "2", "4"]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", ["box", "barplot", "swarmplot"])
def test_explicit_log_base_keeps_applicable_native_category_geometry(kind):
    p = mp.plot({"c": [2, 2, 8, 8, 32, 32], "v": [1, 2, 2, 3, 3, 4]})
    getattr(p, kind)("c", "v", native_scale=True)
    p.xscale("log", options={"base": 2, "subs": [1.5]})
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        pixels = axis.transData.transform(np.c_[[2, 8, 32], [0, 0, 0]])[:, 0]
        assert pixels[1] - pixels[0] == pytest.approx(pixels[2] - pixels[1])
        if kind == "swarmplot":
            offsets = axis.collections[0].get_offsets()
            assert set(offsets[:, 1]) == {1, 2, 3, 4}
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "transform,limits,derived,original,unit",
    [
        (
            {"kind": "celsius_fahrenheit"},
            [-40, 100],
            [-40, 32, 212],
            [-40, 0, 100],
            "°F",
        ),
        (
            {"kind": "celsius_fahrenheit", "reverse": True},
            [32, 212],
            [0, 50, 100],
            [32, 122, 212],
            "°C",
        ),
        (
            {"kind": "radians_degrees"},
            [0, math.pi],
            [0, 90, 180],
            [0, math.pi / 2, math.pi],
            "degree",
        ),
        ({"kind": "seconds_milliseconds"}, [0, 2], [0, 1000, 2000], [0, 1, 2], "ms"),
        ({"kind": "hertz_period"}, [1, 10], [0.1, 0.2, 0.5, 1], [10, 5, 2, 1], "s"),
        (
            {
                "kind": "reciprocal",
                "factor": 1000,
                "source_unit": "u",
                "target_unit": "v",
            },
            [1, 10],
            [100, 200, 500, 1000],
            [10, 5, 2, 1],
            "v",
        ),
        (
            {
                "kind": "affine",
                "factor": -2,
                "offset": 10,
                "source_unit": "u",
                "target_unit": "v",
            },
            [1, 4],
            [2, 4, 6, 8],
            [4, 3, 2, 1],
            "v",
        ),
    ],
)
def test_secondary_tick_geometry_matches_analytic_inverse_and_declared_units(
    transform, limits, derived, original, unit
):
    # A zero raw observation outside a positive reciprocal view remains valid.
    x = (
        [0, *original]
        if transform["kind"] in ("hertz_period", "reciprocal")
        else original
    )
    p = (
        plot_xy(x, range(len(x)))
        .xlim(*limits)
        .secondary_xaxis(
            transform, major_ticks={"locator": {"kind": "fixed", "values": derived}}
        )
    )
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        secondary = axis.child_axes[0]
        actual = secondary.transData.transform(np.c_[derived, np.zeros(len(derived))])[
            :, 0
        ]
        expected = axis.transData.transform(np.c_[original, np.zeros(len(original))])[
            :, 0
        ]
        np.testing.assert_allclose(actual, expected, atol=1e-7)
        assert secondary.get_xlabel() == unit
    finally:
        plt.close(fig)


@pytest.mark.parametrize("low", [1e-6, 0.1])
def test_temperature_offset_rounding_does_not_reject_representable_unit_view(low):
    p = (
        plot_xy([low, 100], [1, 2])
        .xlim(low, 100)
        .secondary_xaxis({"kind": "celsius_fahrenheit"})
    )
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        child = axis.child_axes[0]
        expected = axis.transData.transform([[low, 1], [100, 1]])[:, 0]
        actual = child.transData.transform([[low * 1.8 + 32, 0], [212, 0]])[:, 0]
        np.testing.assert_allclose(actual, expected, atol=1e-7)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("operation", ["draw", "tightbbox"])
def test_later_native_secondary_zoom_rechecks_real_view_precision_and_domain(operation):
    for transform, initial, invalid, message in [
        (
            {
                "kind": "affine",
                "factor": 1,
                "offset": 1e20,
                "source_unit": "u",
                "target_unit": "v",
            },
            [1e20, 2e20],
            [1, 2],
            "precision",
        ),
        ({"kind": "hertz_period"}, [1, 10], [-1, 1], "positive"),
    ]:
        p = plot_xy(initial, [1, 2]).xlim(*initial).secondary_xaxis(transform)
        fig = p.render()
        try:
            axis = fig.axes[0]
            axis.set_xlim(*invalid)
            with pytest.raises(ValueError, match=message):
                fig.canvas.draw() if operation == "draw" else fig.get_tightbbox(
                    fig.canvas.get_renderer()
                )
        finally:
            plt.close(fig)


def test_derived_right_axis_is_not_independent_y2():
    p = plot_xy().secondary_yaxis("Independent")
    with pytest.raises(ValueError, match="independent y2"):
        p.secondary_axis("y", {"kind": "celsius_fahrenheit"})


_CLOCK = r"""
import sys
from matplotlib import dates
dates.set_epoch(sys.argv[1])
import matplotlib.pyplot as plt
import mudplot as m
raw=['2100-01-01T00:00:00.000020Z','2100-01-01T00:00:00.000021Z']
values=m.temporal_coordinates(raw,timezone='UTC')
bounds=m.temporal_coordinates(['2100-01-01T00:00:00.000000Z','2100-01-01T00:00:00.000100Z'],timezone='UTC')
for route in ('auto','date','concise_date'):
 p=m.plot({'t':raw,'v':[1,2]}).line('t','v').date_axis('x',timezone='+05:30').xlim(*bounds)
 f={'kind':route}
 if route=='date':f['pattern']='subsecond'
 p.ticks('x',{'locator':{'kind':'fixed','values':values},'formatter':f})
 figure=p.render();figure.canvas.draw();axis=figure.axes[0]
 labels=[t.get_text() for t in axis.get_xticklabels()]
 assert '.000020' in labels[0] and '.000021' in labels[1],(route,labels)
 if route in ('auto','date'):
  assert all('2100-01-01' in label and '05:30:00' in label for label in labels)
 else:
  context=axis.xaxis.get_offset_text().get_text()
  assert '2100' in context and '05:30' in context,context
 assert dates.get_epoch()==sys.argv[1]
 plt.close(figure)
print('PASS canonical20/21us all3routes; declared clock, unchanged epoch')
"""


@pytest.mark.parametrize(
    "epoch", ["1900-01-01T00:00:00", "1970-01-01T00:00:00", "2000-01-01T00:00:00"]
)
def test_all_clock_formatter_routes_preserve_f02_accepted_precision_and_context(epoch):
    result = subprocess.run(
        [sys.executable, "-c", _CLOCK, epoch],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_calendar_auto_uses_new_provider_and_declared_local_midnights():
    zone = timezone(timedelta(hours=5, minutes=30))
    instants = [datetime(2026, 1, day, tzinfo=zone) for day in (1, 2, 3)]
    origin = datetime(1970, 1, 1, tzinfo=UTC)
    expected = [(value - origin).total_seconds() / 86400 for value in instants]
    p = (
        mp.plot({"t": [v.isoformat() for v in instants], "y": [1, 2, 1]})
        .line("t", "y")
        .date_axis("x", timezone="+05:30")
        .xlim(expected[0], expected[-1])
    )
    p.ticks("x", {"locator": {"kind": "calendar", "unit": "day", "interval": 1}})
    fig = p.render()
    try:
        fig.canvas.draw()
        np.testing.assert_allclose(fig.axes[0].get_xticks(), expected)
        assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ]
    finally:
        plt.close(fig)


def test_temporal_unix_secondary_is_canonical_day_not_input_milliseconds():
    days = [
        (
            datetime(2026, 1, d, tzinfo=UTC) - datetime(1970, 1, 1, tzinfo=UTC)
        ).total_seconds()
        / 86400
        for d in (1, 2, 3)
    ]
    seconds = [datetime(2026, 1, d, tzinfo=UTC).timestamp() for d in (1, 2, 3)]
    p = (
        mp.plot({"t": [0, 86400000, 172800000], "y": [1, 2, 1]})
        .line("t", "y")
        .date_axis("x", unit="ms", origin="2026-01-01T00:00:00Z", timezone="UTC")
        .xlim(days[0], days[-1])
    )
    p.secondary_xaxis(
        {"kind": "unix_seconds"},
        major_ticks={
            "locator": {"kind": "linear", "count": 3},
            "formatter": {"kind": "number", "notation": "fixed", "precision": 0},
        },
    )
    fig = p.render()
    try:
        fig.canvas.draw()
        axis = fig.axes[0]
        child = axis.child_axes[0]
        assert [t.get_text() for t in child.get_xticklabels()] == [
            str(int(v)) for v in seconds
        ]
        actual = child.transData.transform(np.c_[seconds, [0, 0, 0]])[:, 0]
        expected = axis.transData.transform(np.c_[days, [0, 0, 0]])[:, 0]
        np.testing.assert_allclose(actual, expected, atol=1e-6)
        assert child.get_xlabel() == "Unix seconds (UTC)"
    finally:
        plt.close(fig)
