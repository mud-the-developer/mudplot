"""Native stem/event/interval/step temporal paths retain supplied geometry."""

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

from test_temporal_distributions import _assert_geometry, _geometry

DATES = ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-11"]
DAYS = [20454, 20455, 20457, 20464]


@pytest.mark.parametrize("kind", ["stem", "eventplot", "broken_barh"])
def test_native_date_coordinates_match_explicit_day_reference(kind):
    source = {"t": DATES, "v": [2, 4, 3, 5], "duration": [0.5, 1, 0.25, 2]}
    numeric = {**source, "t": DAYS}

    def build(data):
        plot = mp.plot(data)
        if kind == "stem":
            return plot.stem("t", "v", baseline=0.5)
        if kind == "eventplot":
            return plot.eventplot("t", offset=2, length=0.5)
        return plot.broken_barh("t", "duration", bottom=1, height=0.5)

    plot = build(source).date_axis("x", timezone="UTC")
    reference = build(numeric)
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_numeric_interval_durations_use_input_units_without_origin_shift():
    source = {"start": [0, 86400], "duration": [3600, 7200]}
    plot = (
        mp.plot(source)
        .broken_barh("start", "duration", bottom=1, height=0.5)
        .date_axis("x", unit="s", origin="2026-01-01T00:00:00Z")
    )
    reference = mp.plot(
        {"start": [20454, 20455], "duration": [1 / 24, 1 / 12]}
    ).broken_barh("start", "duration", bottom=1, height=0.5)
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_supplied_stair_heights_and_iso_edges_are_not_reestimated():
    source = {"height": [2, 4, 3]}
    plot = (
        mp.plot(source)
        .stairs(
            "height",
            ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-11"],
            baseline=1,
        )
        .date_axis("x", timezone="UTC")
    )
    reference = mp.plot(source).stairs("height", DAYS, baseline=1)
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.to_json() == before and plot.spec.data.columns == source
        assert plot.spec.panels[0].layers[0].bins == DATES
    finally:
        plt.close(f)
        plt.close(r)


def test_extreme_interval_duration_reports_issue_and_preserves_source():
    source = {"t": ["2026-01-01"], "duration": [10**500]}
    plot = mp.plot(source).broken_barh("t", "duration").date_axis("x", timezone="UTC")
    before = plot.to_json()
    assert any("temporal duration row 0" in issue for issue in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="temporal duration row 0"):
        plot.render()
    assert plot.to_json() == before


def test_missing_interval_duration_column_is_a_validation_issue():
    plot = (
        mp.plot({"t": DATES}).broken_barh("t", "missing").date_axis("x", timezone="UTC")
    )
    before = plot.to_json()
    issues = mp.validate(plot.spec)
    assert any("duration" in issue or "column" in issue for issue in issues)
    with pytest.raises(ValueError):
        plot.render()
    assert plot.to_json() == before


def test_date_valued_stair_heights_map_to_value_axis_not_bin_axis():
    source = {"height": DATES[:3]}
    plot = mp.plot(source).stairs("height", [0, 1, 2, 3]).date_axis("y", timezone="UTC")
    reference = mp.plot({"height": DAYS[:3]}).stairs("height", [0, 1, 2, 3])
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)
