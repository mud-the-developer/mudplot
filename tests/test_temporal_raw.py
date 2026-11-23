"""Required raw date paths compare against explicit canonical-day geometry."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest

from test_temporal_distributions import _assert_geometry, _geometry

DATES = ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-11"]
DAYS = [20454, 20455, 20457, 20464]


def _build(kind, data):
    plot = mp.plot(data)
    if kind == "band":
        return plot.band("t", "low", "high")
    if kind == "errorbar":
        return plot.errorbar("t", "v", y_lower="low", y_upper="high")
    if kind == "hexbin":
        return plot.hexbin("t", "v", gridsize=5, colorbar=False)
    return plot.bar("t", "v", y_lower="low", y_upper="high")


@pytest.mark.parametrize("kind", ["bar", "errorbar", "band", "hexbin"])
def test_raw_date_predictors_preserve_reference_geometry_and_source(kind):
    source = {"t": DATES, "v": [2, 4, 3, 5], "low": [1, 3, 2, 4], "high": [3, 5, 4, 6]}
    plot = _build(kind, source).date_axis("x", timezone="UTC")
    reference = _build(kind, {**source, "t": DAYS})
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        for a, b in zip(f.axes[0].collections, r.axes[0].collections, strict=True):
            actual_array, expected_array = a.get_array(), b.get_array()
            if actual_array is not None:
                assert expected_array is not None
                np.testing.assert_allclose(actual_array, expected_array)
        assert plot.spec.data.columns == source and plot.to_json() == before
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("absolute", [False, True])
def test_missing_coordinate_and_uncertainty_share_the_same_observation_mask(
    axis, absolute
):
    source = {
        "t": ["2026-01-01", None],
        "v": [1, 2],
        "e": [0.5, -2],
        "low": ["2025-12-31", "bad"],
        "high": ["2026-01-02", "bad"],
    }
    if absolute:
        plot = (
            mp.plot(source)
            .errorbar("v", "t", y_lower="low", y_upper="high")
            .date_axis("y", timezone="UTC")
        )
        reference = mp.plot(
            {"x": [1], "y": [20454], "low": [20453], "high": [20455]}
        ).errorbar("x", "y", y_lower="low", y_upper="high")
    elif axis == "x":
        plot = (
            mp.plot(source).errorbar("t", "v", xerr="e").date_axis("x", timezone="UTC")
        )
        reference = mp.plot({"x": [20454], "y": [1], "e": [0.5]}).errorbar(
            "x", "y", xerr="e"
        )
    else:
        plot = (
            mp.plot(source).errorbar("v", "t", yerr="e").date_axis("y", timezone="UTC")
        )
        reference = mp.plot({"x": [1], "y": [20454], "e": [0.5]}).errorbar(
            "x", "y", yerr="e"
        )
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("error", [None, -1, "bad"])
def test_malformed_uncertainty_on_a_usable_temporal_observation_still_rejects(error):
    plot = (
        mp.plot({"t": ["2026-01-01"], "v": [1], "e": [error]})
        .errorbar("t", "v", xerr="e")
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec)
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("axis", ["x", "y"])
def test_numeric_timestamp_uncertainty_is_a_duration_in_declared_input_units(axis):
    source = {"t": [0, 86400], "v": [1, 2], "error": [3600, 7200]}
    numeric = {"t": [20454, 20455], "v": [1, 2], "error": [1 / 24, 1 / 12]}
    if axis == "x":
        plot = mp.plot(source).errorbar("t", "v", xerr="error")
        reference = mp.plot(numeric).errorbar("t", "v", xerr="error")
    else:
        plot = mp.plot(source).errorbar("v", "t", yerr="error")
        reference = mp.plot(numeric).errorbar("v", "t", yerr="error")
    plot.date_axis(axis, unit="s", origin="2026-01-01T00:00:00Z")
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source and plot.to_json() == before
    finally:
        plt.close(f)
        plt.close(r)


def test_iso_timestamp_error_magnitudes_use_explicit_calendar_day_geometry():
    source = {"t": DATES, "v": [1, 2, 3, 4], "e": [0.5] * 4}
    plot = mp.plot(source).errorbar("t", "v", xerr="e").date_axis("x", timezone="UTC")
    reference = mp.plot({**source, "t": DAYS}).errorbar("t", "v", xerr="e")
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("error", [-3600, 0.0000001])
def test_temporal_uncertainty_invalid_sign_or_precision_rejects(error):
    plot = (
        mp.plot({"t": [0, 86400], "v": [1, 2], "e": [error, error]})
        .errorbar("t", "v", xerr="e")
        .date_axis("x", unit="s", origin="2026-01-01T00:00:00Z")
    )
    assert mp.validate(plot.spec)
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("kind", ["stackplot", "rug"])
def test_stacked_and_rug_date_predictors_match_declared_day_geometry(kind):
    source = {"t": DATES * 2, "v": [1, 2, 3, 4, 2, 3, 4, 5], "g": ["a"] * 4 + ["b"] * 4}
    if kind == "stackplot":
        plot = (
            mp.plot(source)
            .stackplot("t", "v", group="g")
            .date_axis("x", timezone="UTC")
        )
        reference = mp.plot({**source, "t": DAYS * 2}).stackplot("t", "v", group="g")
    else:
        plot = mp.plot(source).rug("t", group="g").date_axis("x", timezone="UTC")
        reference = mp.plot({**source, "t": DAYS * 2}).rug("t", group="g")
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_stacked_sums_cannot_become_calendar_outputs():
    source = {"t": DATES * 2, "v": [1, 2, 3, 4] * 2, "g": ["a"] * 4 + ["b"] * 4}
    plot = mp.plot(source).stackplot("t", "v", group="g")
    plot.date_axis("y", timezone="UTC")
    assert any("cannot be temporal" in issue for issue in mp.validate(plot.spec))


@pytest.mark.parametrize("kind", ["band", "errorbar"])
def test_date_response_absolute_endpoints_use_the_same_clock(kind):
    source = {
        "x": [1, 2],
        "y": ["2026-01-02", "2026-01-04"],
        "low": ["2026-01-01", "2026-01-03"],
        "high": ["2026-01-03", "2026-01-05"],
    }
    numeric = {
        "x": [1, 2],
        "y": [20455, 20457],
        "low": [20454, 20456],
        "high": [20456, 20458],
    }
    if kind == "band":
        plot = mp.plot(source).band("x", "low", "high").date_axis("y", timezone="UTC")
        reference = mp.plot(numeric).band("x", "low", "high")
    else:
        plot = (
            mp.plot(source)
            .errorbar("x", "y", y_lower="low", y_upper="high")
            .date_axis("y", timezone="UTC")
        )
        reference = mp.plot(numeric).errorbar("x", "y", y_lower="low", y_upper="high")
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)
