"""Small native artist oracles for N05 event and N06 interval lanes."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection


def test_grouped_semantic_events_keep_duplicate_row_traits_and_fixed_cells():
    source = {
        "date": [
            "1970-01-04T00:00:00Z",
            "1970-01-02T00:00:00Z",
            "1970-01-04T00:00:00Z",
            "not a date",
            "not a date",
        ],
        "group": [True, 1, True, "Outside", True],
        "cell": ["Observed"] * 5,
        "quality": [2, 7, 9, 5, 200],
        "stroke": [1, 3, 5, 9, 1000],
        "style": ["solid", "dashed", "dashed", "solid", "excluded"],
    }
    p = (
        mp.plot(source)
        .secondary_yaxis("Lane date")
        .date_axis("y2")
        .eventplot(
            "date",
            axis="y2",
            offset=5,
            length=2,
            group="group",
            hue_order=[True, "Reserved", 1],
            lane_step=4,
            colorbar=True,
            semantics=mp.SemanticSpec(
                hue="quality",
                hue_kind="numeric",
                hue_norm=[0, 10],
                size="stroke",
                sizes=[1, 5],
                style="style",
                style_order=["solid", "dashed"],
                dashes=["-", "--"],
                scale_id="event-quality",
            ),
        )
        .date_axis("x")
        .labels(x="Event date (UTC)")
        .facet(col="cell", col_order=["Empty", "Observed"], live=True)
        .shared_guides([mp.SharedGuideSpec(scale_id="event-quality")])
        .size(9, 4)
    )
    raw = p.to_json()
    p = mp.Plot.from_json(raw)
    fig = p.render()
    ref, ax = plt.subplots()
    try:
        (twin,) = [axis for axis in fig.axes if axis.collections]
        (tick,) = twin.collections
        assert twin.get_ylabel() == "Lane date" and isinstance(tick, LineCollection)
        assert all(
            not axis.lines and not axis.collections
            for axis in fig.axes
            if axis is not twin
        )
        expected = [
            ax.eventplot([x], lineoffsets=y, linelengths=2)[0].get_segments()[0]
            for x, y in [(3, 5), (1, 13), (3, 5)]
        ]
        np.testing.assert_array_equal(tick.get_segments(), expected)
        np.testing.assert_array_equal(tick.get_linewidths(), [1, 3, 5])
        np.testing.assert_array_equal(twin.dataLim.get_points(), [[1, 4], [3, 14]])
        assert tick.get_linestyles()[0][1] is None and all(
            tick.get_linestyles()[i][1] for i in [1, 2]
        )
        (cax,) = [
            axis
            for axis in fig._mudplot_shared_guide_artists
            if getattr(axis, "get_xlabel", lambda: "")() == "quality"
        ]
        assert [float(t.get_text()) for t in cax.get_xticklabels()] == [0, 5, 10]
        np.testing.assert_allclose(
            tick.get_colors(), cax._colorbar.mappable.cmap([0.2, 0.7, 0.9])
        )
        assert any(
            "event tick stroke, pt" in t.get_text()
            for legend in fig.legends
            for t in legend.get_texts()
        )
        assert p.spec.data.columns == source and p.to_json() == raw
    finally:
        plt.close(fig)
        plt.close(ref)
    p.apply([{"type": "SetData", "columns": {**source, "cell": ["New"] * 5}}])
    assert [panel.filters for panel in p.spec.panels] == [
        {"cell": "Empty"},
        {"cell": "Observed"},
    ]
    fig = p.render()
    try:
        assert not fig.legends and not any(ax.collections for ax in fig.axes)
    finally:
        plt.close(fig)


def test_grouped_intervals_keep_elapsed_duration_and_overlap_painter_order():
    source = {
        "start": [86400, 0, 86400, "excluded"],
        "duration": [43200, 172800, 43200, -1],
        "lane": [True, 1, True, "outside"],
        "cell": ["Observed"] * 4,
    }
    p = (
        mp.plot(source)
        .secondary_yaxis("Lane day")
        .date_axis("y2")
        .broken_barh(
            "start",
            "duration",
            axis="y2",
            bottom=1,
            height=3,
            group="lane",
            hue_order=[True, "Reserved", 1],
            lane_step=1,
            alpha=0.6,
        )
        .date_axis("x", unit="s", origin="1970-01-03T00:00:00Z")
        .facet(col="cell", col_order=["Empty", "Observed"], live=True)
        .size(8, 3.5)
    )
    raw = p.to_json()
    q = mp.Plot.from_json(raw)
    fig = q.render()
    ref, ax = plt.subplots()
    try:
        (twin,) = [axis for axis in fig.axes if axis.collections]
        (band,) = twin.collections
        assert isinstance(band, PolyCollection)
        assert twin.get_ylabel() == "Lane day"
        assert len(band.get_paths()) == 3
        for path, start, duration, bottom in zip(
            band.get_paths(), (3, 2, 3), (0.5, 2, 0.5), (1, 3, 1), strict=True
        ):
            native = ax.broken_barh([(start, duration)], (bottom, 3)).get_paths()[0]
            np.testing.assert_array_equal(path.vertices, native.vertices)
        rgba = band.get_facecolors()
        np.testing.assert_array_equal(rgba[0], rgba[2])
        assert not np.array_equal(rgba[0], rgba[1])
        assert twin.get_legend_handles_labels()[1] == ["True", "1"]
        np.testing.assert_array_equal(twin.dataLim.get_points(), [[2, 1], [4, 6]])
        assert all(
            not axis.collections and not axis.patches
            for axis in fig.axes
            if axis is not twin
        )
        assert q.spec.data.columns == source and q.to_json() == raw
    finally:
        plt.close(fig)
        plt.close(ref)


def test_logs_keep_true_extents_and_prior_artists_on_actual_twins():
    for kind in ("eventplot", "broken_barh"):
        source = {
            "x": [6, 9],
            "d": [2, 3],
            "u": [4, 20],
            "v": [11, 25],
            "g": ["B", "A"],
        }
        p = (
            mp.plot(source)
            .secondary_yaxis("Twin lane", scale="log")
            .xscale("log")
            .line("u", "v", axis="y2")
        )
        if kind == "eventplot":
            p.eventplot("x", offset=3, length=4, axis="y2", group="g", lane_step=2)
        else:
            p.broken_barh(
                "x", "d", bottom=1, height=4, axis="y2", group="g", lane_step=2
            )
        fig = p.render()
        try:
            primary, twin = fig.axes
            assert not primary.collections and len(twin.collections) == 1
            np.testing.assert_array_equal(twin.lines[0].get_ydata(), [11, 25])
            np.testing.assert_array_equal(twin.dataLim.get_points(), [[4, 1], [20, 25]])
            np.testing.assert_array_equal(twin.dataLim.minpos, [4, 1])
            assert twin.get_xscale() == twin.get_yscale() == "log"
        finally:
            plt.close(fig)


def test_qualified_logit_geometry_has_no_fake_zero_and_group_overlay():
    fig = (
        mp.plot({"x": [0.2, 0.5], "g": [True, 1]})
        .eventplot(
            "x", offset=0.5, length=0.4, group="g", line_width=0, line_style="--"
        )
        .axis_scale("x", "logit")
        .axis_scale("y", "logit")
        .render()
    )
    try:
        ax = fig.axes[0]
        (mark,) = ax.collections
        np.testing.assert_allclose(ax.dataLim.get_points(), [[0.2, 0.3], [0.5, 0.7]])
        np.testing.assert_allclose(
            mark.get_segments(), [[[0.2, 0.7], [0.2, 0.3]], [[0.5, 0.7], [0.5, 0.3]]]
        )
        assert all(width == 0 for width in mark.get_linewidths())
    finally:
        plt.close(fig)


def test_invalid_lane_coordinates_rollback_existing_export(tmp_path):
    base = {"x": [2, 3], "d": [1, 1], "group": ["A", "B"], "value": [0, 1]}
    target = tmp_path / "prior.svg"
    target.write_text("existing")
    for plot, message in (
        (mp.plot(base).eventplot("x", lane_step=1), "requires a real group"),
        (
            mp.plot(base).eventplot("x", group="group", lane_step=True),
            "finite positive step",
        ),
        (
            mp.plot(base).eventplot("x", offset=1, length=2).yscale("log"),
            "lane endpoints must be positive",
        ),
        (
            mp.plot(base)
            .eventplot("x", offset=0.5, length=1, group="group")
            .axis_scale("y", "logit"),
            "strictly inside",
        ),
        (
            mp.plot(base).eventplot("x", semantics={"size": "value"}, line_width=2),
            "cannot override mapped size",
        ),
        (
            mp.plot(base).eventplot("value").xscale("log"),
            "positions/starts must be positive",
        ),
        (
            mp.plot(base).broken_barh("value", "d", bottom=1).xscale("log"),
            "positions/starts must be positive",
        ),
        (
            mp.plot(base).broken_barh(
                "x", "d", height=10, bottom=1e16, group="group", lane_step=0.125
            ),
            "collapses adjacent",
        ),
        (
            mp.plot(base).broken_barh("x", "d", bottom=0).yscale("log"),
            "lane endpoints must be positive",
        ),
        (
            mp.plot({"x": [1e16], "d": [0.125]})
            .broken_barh("x", "d", bottom=1)
            .xscale("log"),
            "interval endpoints collapse",
        ),
    ):
        with pytest.raises(ValueError, match=message):
            plot.save(str(target))
        assert target.read_text() == "existing"
