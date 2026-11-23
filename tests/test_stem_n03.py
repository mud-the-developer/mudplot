"""N03 geometry against native Axes.stem on supplied displayed coordinates."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.collections import LineCollection, PathCollection


def test_fixed_grouped_horizontal_date_twin():
    source = {
        "where": [
            "1970-01-05T01:00:00+01:00",
            "1970-01-02T00:00:00Z",
            "1970-01-05T00:00:00Z",
            "not a date",
            "not a date",
        ],
        "hours": [86400, 0, 43200, -5, -9],
        "group": [True, 1, True, "skip", True],
        "style": ["open", "filled", "filled", "open", "excluded"],
        "panel": ["Observed"] * 5,
        "size": [1, 2, 3, 4, 9],
    }
    p = (
        mp.plot(source)
        .secondary_yaxis("Location time")
        .stem(
            "where",
            "hours",
            axis="y2",
            orient="h",
            baseline=1.75,
            group="group",
            hue_order=[1, "Reserved", True],
            marker_size=5,
            semantics=mp.SemanticSpec(
                size="size",
                sizes=[1, 3],
                style="style",
                style_order=["open", "filled"],
                markers=["o", "s"],
                dashes=["-", "--"],
                scale_id="stem-shared",
            ),
        )
        .date_axis("y2")
        .date_axis("x", unit="s", origin="1970-01-03T00:00:00Z")
        .facet(col="panel", col_order=["Empty", "Observed"], live=True)
        .size(8, 4)
    )
    original = p.to_json()
    p = mp.Plot.from_json(original)
    fig = p.render()
    ref, ax = plt.subplots()
    try:
        observed = next(
            axis
            for axis in fig.axes
            if any(isinstance(c, LineCollection) for c in axis.collections)
        )
        assert observed.get_ylabel() == "Location time"
        assert all(
            not axis.collections and not axis.lines
            for axis in fig.axes
            if axis is not observed
        )
        expect = ax.stem([4, 1, 4], [3, 2, 2.5], orientation="horizontal", bottom=1.75)
        (native,) = [c for c in observed.collections if isinstance(c, LineCollection)]
        np.testing.assert_array_equal(
            native.get_segments(), expect.stemlines.get_segments()
        )
        np.testing.assert_array_equal(native.get_linewidths(), [1, 2, 3])
        np.testing.assert_array_equal(native.get_colors()[0], native.get_colors()[2])
        assert not np.array_equal(native.get_colors()[0], native.get_colors()[1])
        heads = [c for c in observed.collections if isinstance(c, PathCollection)]
        assert len(heads) == 2 and all(c.get_sizes().tolist() == [25] for c in heads)
        assert native.get_linestyles()[0][1] is None and native.get_linestyles()[1][1]
        (baseline,) = [line for line in observed.lines if len(line.get_xdata())]
        np.testing.assert_array_equal(
            baseline.get_xydata(), expect.baseline.get_xydata()
        )
        assert not any(
            "Reserved" in text for text in observed.get_legend_handles_labels()[1]
        )
        assert p.spec.data.columns == source and p.to_json() == original
    finally:
        plt.close(fig)
        plt.close(ref)


def test_horizontal_mapped_nonlinear_raw_bounds():
    source = {
        "place": [20, 40],
        "head": [4, 8],
        "amount": [1, 3],
        "old_x": [3, 9],
        "old_y": [10, 100],
    }
    p = (
        mp.plot(source)
        .secondary_yaxis("Location", scale="symlog")
        .axis_scale("x", "asinh")
        .line("old_x", "old_y", axis="y2")
        .stem(
            "place",
            "head",
            axis="y2",
            orient="h",
            baseline=5,
            semantics=mp.SemanticSpec(size="amount", sizes=[0, 2]),
        )
    )
    fig = p.render()
    try:
        ax = fig.axes[1]
        np.testing.assert_array_equal(ax.dataLim.get_points(), [[3, 10], [9, 100]])
        np.testing.assert_array_equal(ax.dataLim.minpos, [3, 10])
        assert ax.get_xlim()[0] > 0.5 and ax.get_ylim()[0] > 0.5
        (stroke,) = [c for c in ax.collections if isinstance(c, LineCollection)]
        np.testing.assert_array_equal(
            stroke.get_segments(), [[[5, 20], [4, 20]], [[5, 40], [8, 40]]]
        )
    finally:
        plt.close(fig)


def test_valid_logit_and_grouped_hue_guides():
    p = (
        mp.plot({"x": [0.2, 0.3], "y": [0.4, 0.9], "grade": [2, 7], "sz": [1, 2]})
        .stem(
            "x",
            "y",
            orient="h",
            baseline=0.1,
            colorbar=True,
            semantics=mp.SemanticSpec(
                hue="grade",
                hue_kind="numeric",
                hue_norm=[0, 10],
                size="sz",
                sizes=[1, 3],
                scale_id="quality",
            ),
        )
        .axis_scale("x", "logit")
        .axis_scale("y", "logit")
        .shared_guides([mp.SharedGuideSpec(scale_id="quality")])
        .size(6, 4)
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        np.testing.assert_array_equal(ax.dataLim.get_points(), [[0.1, 0.2], [0.9, 0.3]])
        (stroke,) = [c for c in ax.collections if isinstance(c, LineCollection)]
        (heads,) = [c for c in ax.collections if isinstance(c, PathCollection)]
        np.testing.assert_array_equal(stroke.get_colors(), heads.get_facecolors())
        (cax,) = [
            guide
            for guide in fig._mudplot_shared_guide_artists
            if getattr(guide, "get_xlabel", lambda: "")() == "grade"
        ]
        assert [float(label.get_text()) for label in cax.get_xticklabels()] == [
            0,
            5,
            10,
        ]
        assert cax._colorbar.mappable.get_clim() == (0, 1)
        assert any(
            "stem stroke, pt" in t.get_text()
            for legend in fig.legends
            for t in legend.get_texts()
        )
    finally:
        plt.close(fig)


def _reject(p, message):
    try:
        p.render()
    except ValueError as error:
        assert message in str(error), str(error)
    else:
        raise AssertionError(f"Render did not reject: {message}")


def test_invalid_horizontal_domains_and_owner_conflicts():
    def p(head, bottom):
        return (
            mp.plot({"loc": [2], "value": [head]})
            .secondary_yaxis("Location", scale="log")
            .stem("loc", "value", orient="h", axis="y2", baseline=bottom)
            .xscale("log")
        )

    _reject(p(2, 0), "log stem heads and baseline must be positive")
    _reject(p(-2, 1), "log stem heads and baseline must be positive")
    base = {"x": [1, 2], "y": [2, 3], "kind": ["A", "B"], "s": [1, 2]}
    _reject(
        mp.plot(base).stem("x", "y", group="kind", semantics={"hue": "kind"}),
        "cannot combine with legacy group",
    )
    _reject(
        mp.plot(base).stem("x", "y", line_width=1, semantics={"size": "s"}),
        "cannot override mapped size",
    )
    _reject(
        mp.plot(base).stem("x", "y", axis="y2", semantics={"size": "s"}),
        "stem y2 target must be configured",
    )


def test_unowned_stem_guide_scope_rejects_action_atomically():
    base = {"x": [1, 2], "y": [2, 3], "s": [1, 2]}
    owner = mp.plot(base).stem("x", "y", semantics={"size": "s", "scale_id": "valid"})
    original = owner.to_json()
    try:
        owner.shared_guides([mp.SharedGuideSpec(scale_id="no-owner")])
    except ValueError as error:
        assert "no persisted owner" in str(error)
    else:
        raise AssertionError("SetSharedGuides accepted a scope with no persisted owner")
    assert owner.to_json() == original


if __name__ == "__main__":
    test_fixed_grouped_horizontal_date_twin()
    test_horizontal_mapped_nonlinear_raw_bounds()
    test_valid_logit_and_grouped_hue_guides()
    test_invalid_horizontal_domains_and_owner_conflicts()
    test_unowned_stem_guide_scope_rejects_action_atomically()
    print("5 N03 behavior checks passed")
