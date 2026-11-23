"""F02 bivariate and canonical literal-coordinate references."""

from datetime import date
from fractions import Fraction

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest

from test_temporal_distributions import _assert_geometry, _geometry

DATES = [
    "2026-01-01",
    "2026-01-02",
    "2026-01-03",
    "2026-01-06",
    "2026-01-08",
    "2026-01-11",
]
DAYS = [20454, 20455, 20456, 20459, 20461, 20464]


@pytest.mark.parametrize("kind", ["hist2d", "kde2d"])
def test_date_bivariate_coordinates_match_day_reference(kind):
    source = {"t": DATES, "v": [1, 3, 2, 7, 4, 6]}
    options = (
        {"bins": 4, "colorbar": False}
        if kind == "hist2d"
        else {"gridsize": 25, "cut": 0}
    )
    plot = getattr(mp.plot(source), kind)("t", "v", **options).date_axis(
        "x", timezone="UTC"
    )
    reference = getattr(mp.plot({**source, "t": DAYS}), kind)("t", "v", **options)
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        for a, b in zip(f.axes[0].collections, r.axes[0].collections, strict=True):
            if a.get_array() is not None:
                np.testing.assert_allclose(a.get_array(), b.get_array())
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_strip_date_positions_remain_elapsed_time_without_jitter_inference():
    source = {"t": DATES, "v": [1, 3, 2, 7, 4, 6]}
    plot = mp.plot(source).stripplot("t", "v", jitter=0).date_axis("x", timezone="UTC")
    figure = plot.render()
    try:
        np.testing.assert_allclose(
            np.asarray(figure.axes[0].collections[0].get_offsets())[:, 0], DAYS
        )
        assert plot.spec.data.columns == source
    finally:
        plt.close(figure)


def test_literal_reference_event_and_annotation_use_declared_calendar_day_units():
    event = mp.temporal_coordinates(["2026-01-02"], timezone="UTC")[0]
    assert event == 20455
    plot = (
        mp.plot({"t": DATES, "v": [1, 3, 2, 7, 4, 6]})
        .scatter("t", "v")
        .date_axis("x", timezone="UTC")
        .vline(event)
        .text("event", at=[event, 4])
    )
    before = plot.to_json()
    figure = plot.render()
    try:
        assert list(np.asarray(figure.axes[0].lines[0].get_xdata())) == [20455, 20455]
        assert figure.axes[0].texts[0].get_position() == (20455, 4)
        assert plot.to_json() == before
    finally:
        plt.close(figure)


def test_kde2d_hue_selection_precedes_date_parsing_without_losing_rows():
    source = {
        "t": [*DATES, "bad"],
        "v": [1, 3, 2, 7, 4, 6, 8],
        "h": ["keep"] * 6 + ["omit"],
        "w": [1] * 7,
    }
    plot = (
        mp.plot(source)
        .kde2d("t", "v", weights="w", group="h", hue_order=["keep"], gridsize=25, cut=0)
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    plt.close(plot.render())
    assert plot.spec.data.columns == source


def test_kde2d_selection_preserves_unselected_invalid_date_and_source_rows():
    source = {"t": [*DATES, "bad"], "v": [1, 3, 2, 7, 4, 6, 8], "w": [1] * 6 + [0]}
    plot = (
        mp.plot(source)
        .kde2d("t", "v", weights="w", gridsize=25, cut=0)
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    plt.close(plot.render())
    assert plot.spec.data.columns == source


def test_horizontal_y2_histogram_uses_each_clock_and_canonical_day_cell_area():
    source = {
        "u": [0, 0.5, 1, 2],
        "v": [0, 2, 3, 4],
        "w": [1, 2, 3, 4],
        "value": [-1, 1, 0.5, 2],
        "id": ["a", "b", "c", "d"],
    }
    plot = (
        mp.plot(source)
        .line("v", "value")
        .secondary_yaxis("Millisecond observations")
        .date_axis("x", unit="day", origin="2000-01-01", timezone="UTC")
        .date_axis("y2", unit="ms", origin="2026-01-01", timezone="UTC")
        .hist2d(
            "u",
            "v",
            orient="h",
            axis="y2",
            weights="w",
            stat="density",
            bins=mp.BivariateBinsSpec(
                x=[
                    "2026-01-01T00:00:00",
                    "2026-01-01T00:00:00.001",
                    "2026-01-01T00:00:00.002",
                ],
                y=["2000-01-01", "2000-01-02", "2000-01-04", "2000-01-05"],
            ),
            colorbar=True,
        )
    )
    before = plot.to_json()
    figure = mp.Plot.from_json(before).render()
    reference, native = plt.subplots()
    try:
        x_origin = (date(2000, 1, 1) - date(1970, 1, 1)).days
        y_origin = (date(2026, 1, 1) - date(1970, 1, 1)).days
        native.plot(np.array(source["v"]) + x_origin, source["value"])
        np.testing.assert_array_equal(
            figure.axes[0].dataLim.get_points(), native.dataLim.get_points()
        )
        np.testing.assert_allclose(figure.axes[0].get_ylim(), native.get_ylim())
        mesh = figure.axes[1].collections[0]
        coordinates = np.asarray(mesh.get_coordinates())
        np.testing.assert_array_equal(
            coordinates[0, :, 0], np.array([0, 1, 3, 4]) + x_origin
        )
        np.testing.assert_array_equal(
            coordinates[:, 0, 1], np.array([0, 1, 2]) / 86_400_000 + y_origin
        )
        # Cells are one millisecond by 1/2/1 days, never one millisecond
        # interpreted as one day or one density value interpreted as a date.
        masses = [[1, 2, 0], [0, 0, 7]]
        expected = [
            [
                float(Fraction(86_400_000 * mass, 10 * width))
                for mass, width in zip(row, [1, 2, 1], strict=True)
            ]
            for row in masses
        ]
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array()).reshape(2, 3), expected
        )
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(figure)
        plt.close(reference)


def test_horizontal_y2_joint_or_field_keeps_original_clock_knots_and_row_mass():
    source = {
        "u": [0, 0.5, 1, 2],
        "v": [0, 2, 3, 4],
        "w": [1, 2, 3, 4],
        "id": ["a", "b", "c", "d"],
    }
    plot = (
        mp.plot(source)
        .secondary_yaxis("Millisecond observations")
        .date_axis("x", unit="day", origin="2000-01-01", timezone="UTC")
        .date_axis("y2", unit="ms", origin="2026-01-01", timezone="UTC")
        .ecdf2d(
            "u",
            "v",
            orient="h",
            axis="y2",
            weights="w",
            stat="percent",
            complementary=True,
            bounds=[
                ["2026-01-01T00:00:00", "2026-01-01T00:00:00.002"],
                ["2000-01-01", "2000-01-05"],
            ],
            query_x=["2026-01-01T00:00:00.000500"],
            query_y=["2000-01-02", "2000-01-04"],
            colorbar=True,
        )
    )
    before = plot.to_json()
    figure = mp.Plot.from_json(before).render()
    try:
        x_origin = (date(2000, 1, 1) - date(1970, 1, 1)).days
        y_origin = (date(2026, 1, 1) - date(1970, 1, 1)).days
        mesh = figure.axes[1].collections[0]
        coordinates = np.asarray(mesh.get_coordinates())
        logical_x, logical_y = [0, 0.5, 1, 2], [0, 1, 2, 3, 4]
        np.testing.assert_array_equal(
            coordinates[0, :, 0], np.array(logical_y) + x_origin
        )
        np.testing.assert_array_equal(
            coordinates[:, 0, 1], np.array(logical_x) / 86_400_000 + y_origin
        )
        expected = [
            [
                10
                * sum(
                    weight
                    for u, v, weight in zip(
                        source["u"], source["v"], source["w"], strict=True
                    )
                    if u > qx or v > qy
                )
                for qy in logical_y[:-1]
            ]
            for qx in logical_x[:-1]
        ]
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array()).reshape(3, 4), expected
        )
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(figure)
