"""F02 vertical raw-series slice; other temporal families remain required work."""

import copy
import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot import actions as A
from mudplot._temporal_render import _CalendarLocator
from mudplot.spec import AxisSpec

DATES = ["2026-01-01", "2026-01-02", "2026-01-11"]


def _plot(kind="scatter"):
    return getattr(mp.plot({"t": DATES, "v": [2, 3, 4]}), kind)("t", "v")


@pytest.mark.parametrize("kind", ["scatter", "line"])
def test_explicit_temporal_axis_draws_elapsed_days_without_changing_data(kind):
    plot = _plot(kind).date_axis("x", timezone="UTC").labels(x="Date", y="Value")
    original = plot.to_json()
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        ax = figure.axes[0]
        x = (
            np.asarray(ax.collections[0].get_offsets())[:, 0]
            if kind == "scatter"
            else np.asarray(ax.lines[0].get_xdata())
        )
        assert list(x) == [20454, 20455, 20464]
        assert list(x[1:] - x[:-1]) == [1, 9]
        assert any("2026-01" in t.get_text() for t in ax.get_xticklabels())
        assert plot.to_json() == original and plot.spec.data.columns["t"] == DATES
    finally:
        plt.close(figure)


def test_old_strings_stay_categorical_and_new_unset_axis_field_is_omitted():
    plot = _plot()
    original = plot.to_json()
    assert "temporal" not in json.loads(original)["panels"][0]["x"]
    assert "temporal" not in AxisSpec().to_dict()
    figure = plot.render()
    try:
        assert list(np.asarray(figure.axes[0].collections[0].get_offsets())[:, 0]) == [
            0,
            1,
            2,
        ]
        assert [t.get_text() for t in figure.axes[0].get_xticklabels()] == DATES
        assert plot.to_json() == original
    finally:
        plt.close(figure)


@pytest.mark.parametrize("axis", ["y", "y2"])
def test_temporal_response_axis_routing(axis):
    plot = mp.plot({"x": [1, 2, 3], "t": DATES})
    if axis == "y2":
        plot.secondary_yaxis("Event date")
    plot.scatter("x", "t", axis=axis).date_axis(axis, timezone="UTC")
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        ax = figure.axes[-1]
        assert list(np.asarray(ax.collections[0].get_offsets())[:, 1]) == [
            20454,
            20455,
            20464,
        ]
        assert any("2026-01" in t.get_text() for t in ax.get_yticklabels())
    finally:
        plt.close(figure)


@pytest.mark.parametrize("semantic", ["group", "hue"])
def test_coordinate_and_semantic_role_can_share_a_source_column(semantic):
    options: dict[str, Any] = (
        {"group": "t"} if semantic == "group" else {"semantics": {"hue": "t"}}
    )
    plot = (
        mp.plot({"t": DATES, "v": [2, 3, 4]})
        .scatter("t", "v", **options)
        .date_axis("x", timezone="UTC")
    )
    source = copy.deepcopy(plot.spec.data.columns)
    reference = (
        mp.plot({**source, "numeric": [0, 1, 2]})
        .scatter("numeric", "v", **options)
        .render()
    )
    try:
        reference_legend = reference.axes[0].get_legend()
        assert reference_legend is not None
        expected_labels = [t.get_text() for t in reference_legend.get_texts()]
        expected_colors = [
            np.asarray(c.get_facecolor()).tolist()
            for c in reference.axes[0].collections
        ]
    finally:
        plt.close(reference)
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        positions = [
            p[0]
            for c in figure.axes[0].collections
            for p in np.asarray(c.get_offsets())
        ]
        assert sorted(positions) == [20454, 20455, 20464]
        legend = figure.axes[0].get_legend()
        assert (
            legend is not None
            and [t.get_text() for t in legend.get_texts()] == expected_labels
        )
        assert [
            np.asarray(c.get_facecolor()).tolist() for c in figure.axes[0].collections
        ] == expected_colors
        assert plot.spec.data.columns == source
        assert "__mudplot_temporal" not in plot.to_json()
    finally:
        plt.close(figure)


def test_panel_selection_precedes_temporal_parsing():
    source = {
        "t": [*DATES, "not a time"],
        "v": [1, 2, 3, 4],
        "f": ["yes", "yes", "yes", "no"],
    }
    plot = (
        mp.plot(source)
        .scatter("t", "v")
        .facet(col="f", col_order=["yes"])
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert list(np.asarray(figure.axes[0].collections[0].get_offsets())[:, 0]) == [
            20454,
            20455,
            20464,
        ]
        assert plot.spec.data.columns == source
    finally:
        plt.close(figure)


def test_faceting_still_requires_a_valid_completed_template():
    plot = (
        mp.plot({"t": [*DATES, "bad"], "v": [1, 2, 3, 4], "f": ["yes"] * 3 + ["no"]})
        .scatter("t", "v")
        .date_axis("x", timezone="UTC")
    )
    before = plot.to_json()
    with pytest.raises(ValueError, match="unsupported ISO"):
        plot.facet(col="f", col_order=["yes"])
    assert plot.to_json() == before


def test_facets_with_different_date_domains_share_physical_time_not_categories():
    plot = (
        mp.plot(
            {
                "t": ["2026-01-01", "2026-01-02", "2026-01-10", "2026-01-11"],
                "v": [1, 2, 3, 4],
                "f": ["a", "a", "b", "b"],
            }
        )
        .scatter("t", "v")
        .date_axis("x", timezone="UTC")
        .facet(col="f")
    )
    figure = plot.render()
    try:
        assert [
            list(np.asarray(ax.collections[0].get_offsets())[:, 0])
            for ax in figure.axes
        ] == [
            [20454, 20455],
            [20463, 20464],
        ]
        assert figure.axes[0].get_xlim() == figure.axes[1].get_xlim()
    finally:
        plt.close(figure)


def test_numeric_unit_and_origin_are_used_in_actual_geometry():
    plot = (
        mp.plot({"t": [0, 86400000, 864000000], "v": [1, 2, 3]})
        .line("t", "v")
        .date_axis("x", unit="ms", origin="2026-01-01T00:00:00Z")
    )
    figure = plot.render()
    try:
        assert list(np.asarray(figure.axes[0].lines[0].get_xdata())) == [
            20454,
            20455,
            20464,
        ]
    finally:
        plt.close(figure)


@pytest.mark.parametrize("zone_name", ["UTC", "+05:30", "-04:00"])
def test_calendar_ticks_follow_declared_local_midnights(zone_name):
    source = {"t": [value + "T00:00:00Z" for value in DATES], "v": [2, 3, 4]}
    plot = mp.plot(source).scatter("t", "v").date_axis("x", timezone=zone_name)
    figure = plot.render()
    try:
        ax = figure.axes[0]
        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, _CalendarLocator)
        epoch = datetime(1970, 1, 1, tzinfo=UTC)
        low, high = ax.get_xlim()
        bounds = [
            (epoch + timedelta(days=float(value))).astimezone(locator.inner.tz)
            for value in (low, high)
        ]
        native = mdates.AutoDateLocator(tz=locator.inner.tz)
        expected = np.asarray(cast(Any, native).tick_values(*bounds)) - float(
            mdates.date2num(epoch)
        )
        np.testing.assert_allclose(ax.get_xticks(), expected, rtol=0, atol=1e-10)
        np.testing.assert_array_equal(
            np.asarray(ax.collections[0].get_offsets())[:, 0], [20454, 20455, 20464]
        )
    finally:
        plt.close(figure)


def test_timezone_changes_tick_display_without_changing_instants():
    data = {
        "t": ["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "2026-01-11T00:00:00Z"],
        "v": [1, 2, 3],
    }
    plot = mp.plot(data).scatter("t", "v").date_axis("x", timezone="+05:30")
    figure = plot.render()
    try:
        ax = figure.axes[0]
        assert list(np.asarray(ax.collections[0].get_offsets())[:, 0]) == [
            20454,
            20455,
            20464,
        ]
        assert ax.xaxis.get_major_formatter()(20454).startswith("2026-01-01")
        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, _CalendarLocator)
        offset = locator.inner.tz.utcoffset(None)
        assert offset is not None and offset.total_seconds() == 19800
    finally:
        plt.close(figure)


def test_temporal_actions_json_and_clear_preserve_old_workflows():
    plot = _plot().date_axis("x", timezone="UTC")
    assert mp.apply(plot.action_log) == plot.spec
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
    action = A.action_to_dict(A.SetTemporalAxis("x", mp.TemporalSpec(timezone="UTC")))
    assert A.action_from_dict(action) == A.SetTemporalAxis(
        "x", mp.TemporalSpec(timezone="UTC")
    )
    plot.dispatch(A.SetTemporalAxis("x", None))
    assert plot.to_json() == _plot().to_json()
    with pytest.raises(ValueError, match="requires x, y or y2"):
        plot.dispatch(A.SetTemporalAxis("z", mp.TemporalSpec()))
    with pytest.raises(ValueError, match="enabled axis"):
        plot.dispatch(A.SetTemporalAxis("y2", mp.TemporalSpec()))


def test_non_coordinate_pie_axis_cannot_be_declared_temporal():
    plot = (
        mp.plot({"t": DATES, "v": [1, 2, 3]})
        .pie("t", "v")
        .date_axis("x", timezone="UTC")
    )
    assert any("not connected" in i for i in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="not connected"):
        plot.render()


def test_log_temporal_axes_are_rejected():
    plot = _plot().date_axis("x", timezone="UTC").xscale("log")
    assert any(
        "temporal axes require a linear scale" in i for i in mp.validate(plot.spec)
    )


@pytest.mark.parametrize("other", [None, "+01:00"])
def test_shared_axes_reject_mixed_date_or_display_zone_contracts(other):
    plot = (
        mp.plot({"t": DATES, "v": [1, 2, 3], "f": ["a", "b", "b"]})
        .scatter("t", "v")
        .date_axis("x", timezone="UTC")
        .facet(col="f")
    )
    plot.dispatch(
        A.SetTemporalAxis(
            "x", None if other is None else mp.TemporalSpec(timezone=other), panel=1
        )
    )
    assert any("conflicting temporal" in i for i in mp.validate(plot.spec))


def test_shared_hue_facets_keep_original_ids_and_raw_date_values():
    from mudplot._semantics import shared_scale_domains

    data = {
        "t": ["2026-01-01", "2026-01-02", "2026-01-10", "2026-01-11"],
        "v": [1, 2, 3, 4],
        "f": ["a", "a", "b", "b"],
    }
    plot = (
        mp.plot(data)
        .scatter("t", "v", semantics={"hue": "t"})
        .date_axis("x", timezone="UTC")
        .facet(col="f")
    )
    domains = shared_scale_domains(plot.spec)
    assert len(domains) == 1
    domain = next(iter(domains.values()))
    assert domain["rows"] == [0, 1, 2, 3] and domain["columns"] == data
    figure = plot.render()
    try:
        assert [
            np.asarray(ax.collections[0].get_offsets())[:, 0].tolist()
            for ax in figure.axes
        ] == [[20454, 20455], [20463, 20464]]
    finally:
        plt.close(figure)


def test_non_cartesian_date_axes_are_rejected():
    plot = _plot().date_axis("x", timezone="UTC")
    bad = replace(plot.spec, panels=[replace(plot.spec.panels[0], projection="polar")])
    assert any("temporal axes require Cartesian" in i for i in mp.validate(bad))


def test_date_render_failure_preserves_previous_output_and_figures(tmp_path):
    plot = (
        mp.plot({"t": ["invalid"], "v": [1]})
        .scatter("t", "v")
        .date_axis("x", timezone="UTC")
    )
    target = tmp_path / "previous.svg"
    target.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises(ValueError, match="unsupported ISO"):
        plot.save(target)
    assert target.read_bytes() == b"previous" and plt.get_fignums() == before


@pytest.mark.parametrize("role", ["hue", "size", "style"])
def test_semantic_selection_precedes_date_parsing_for_every_role(role):
    config: dict[str, Any] = {role: "h", f"{role}_order": ["keep"]}
    if role == "size":
        config["size_kind"] = "categorical"
    source = {"t": ["2026-01-01", "bad"], "v": [1, 2], "h": ["keep", "omit"]}
    plot = (
        mp.plot(source)
        .scatter("t", "v", semantics=config)
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert np.asarray(figure.axes[0].collections[0].get_offsets()).tolist() == [
            [20454, 1]
        ]
        assert plot.spec.data.columns == source
    finally:
        plt.close(figure)


def test_typed_raw_group_selection_agrees_in_validation_and_rendering():
    source = {"t": ["bad", "2026-01-01"], "v": [1, 2], "h": [True, 1]}
    plot = (
        mp.plot(source)
        .scatter("t", "v", group="h", hue_order=[1])
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert np.asarray(figure.axes[0].collections[0].get_offsets()).tolist() == [
            [20454, 2]
        ]
        assert plot.spec.data.columns == source
    finally:
        plt.close(figure)


def test_missing_raw_group_reference_reports_issues_instead_of_keyerror():
    plot = (
        mp.plot({"t": ["2026-01-01"], "v": [1]})
        .scatter("t", "v", group="absent", hue_order=["keep"])
        .date_axis("x", timezone="UTC")
    )
    issues = mp.validate(plot.spec)
    assert any("existing group column" in issue for issue in issues)
    with pytest.raises(ValueError, match="existing group column"):
        plot.render()


def test_nondefault_matplotlib_epoch_does_not_change_geometry_or_labels(tmp_path):
    code = """
import matplotlib as m
m.rcParams['date.epoch']='2000-01-01T00:00:00'
import matplotlib.dates as d
import matplotlib.pyplot as plt
import mudplot as mp
before=d.get_epoch()
p=mp.plot({'t':['2026-01-01','2026-01-11'],'v':[1,2]}).scatter('t','v').date_axis('x',timezone='UTC')
f=p.render()
assert list(f.axes[0].collections[0].get_offsets()[:,0])==[20454,20464]
assert any('2026-01' in t.get_text() for t in f.axes[0].get_xticklabels())
assert d.get_epoch()==before
plt.close(f)
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        check=True,
    )
