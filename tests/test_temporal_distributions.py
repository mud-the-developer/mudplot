"""F02 distribution/regression equivalence in declared canonical day units."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest

DATES = [
    "2026-01-01",
    "2026-01-02",
    "2026-01-03",
    "2026-01-06",
    "2026-01-08",
    "2026-01-11",
]
DAYS = [20454, 20455, 20456, 20459, 20461, 20464]


def _geometry(ax):
    return {
        "lines": [
            (
                np.asarray(line.get_xdata(), dtype=float),
                np.asarray(line.get_ydata(), dtype=float),
            )
            for line in ax.lines
        ],
        "patches": [
            p.get_patch_transform().transform(p.get_path().vertices) for p in ax.patches
        ],
        "paths": [path.vertices for c in ax.collections for path in c.get_paths()],
        "offsets": [np.asarray(c.get_offsets()) for c in ax.collections],
    }


def _assert_geometry(actual, expected):
    assert actual.keys() == expected.keys()
    for key in actual:
        assert len(actual[key]) == len(expected[key]), key
        for a, b in zip(actual[key], expected[key], strict=True):
            np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-9, err_msg=key)


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_default_legacy_distribution_keeps_temporal_observations_and_defaults(kind):
    source = {"t": DATES}
    plot = getattr(mp.plot(source), kind)("t").date_axis("x", timezone="UTC")
    assert (
        getattr(plot.spec.panels[0].layers[0], "histogram" if kind == "hist" else "kde")
        is None
    )
    reference = getattr(mp.plot({"t": DAYS}), kind)("t")
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
        assert f.axes[0].patches or f.axes[0].lines
    finally:
        plt.close(f)
        plt.close(r)
    bad = getattr(mp.plot({"t": [*DATES, "bad"]}), kind)("t").date_axis(
        "x", timezone="UTC"
    )
    assert any("unsupported ISO" in i for i in mp.validate(bad.spec))


@pytest.mark.parametrize("kind", ["hist", "kde", "ecdf"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_temporal_univariate_matches_day_coordinate_reference(kind, orient):
    options = (
        {"bins": [20453, 20457, 20465], "stat": "density"}
        if kind == "hist"
        else {"cut": 0}
        if kind == "kde"
        else {}
    )
    source = {"t": DATES, "w": [1, 2, 3, 4, 2, 1]}
    plot = getattr(mp.plot(source), kind)(
        "t", weights="w", orient=orient, **options
    ).date_axis("x" if orient == "v" else "y", timezone="UTC")
    reference = getattr(mp.plot({**source, "t": DAYS}), kind)(
        "t", weights="w", orient=orient, **options
    )
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source and plot.to_json() == before
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("kind", ["box", "violin", "boxenplot", "swarmplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_date_distribution_categories_have_native_elapsed_spacing(kind, orient):
    source = {
        "t": [DATES[0]] * 5 + [DATES[-1]] * 5,
        "v": [1, 2, 3, 4, 5, 2, 4, 6, 8, 10],
    }
    numeric = {**source, "t": [DAYS[0]] * 5 + [DAYS[-1]] * 5}
    plot = getattr(mp.plot(source), kind)("t", "v", orient=orient).date_axis(
        "x" if orient == "v" else "y", timezone="UTC"
    )
    reference = getattr(mp.plot(numeric), kind)(
        "t", "v", orient=orient, native_scale=True
    )
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("kind", ["box", "violin", "boxenplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_one_column_date_distributions_use_value_axis_not_category_axis(kind, orient):
    source = {"t": DATES}
    plot = getattr(mp.plot(source), kind)("t", orient=orient).date_axis(
        "y" if orient == "v" else "x", timezone="UTC"
    )
    reference = getattr(mp.plot({"t": DAYS}), kind)("t", orient=orient)
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("kind", ["hist", "kde", "violin"])
def test_explicit_iso_edges_and_clips_are_converted_without_rewriting_source(kind):
    source = {"t": DATES}
    if kind == "hist":
        options = {
            "bins": ["2026-01-01", "2026-01-06", "2026-01-12"],
            "stat": "density",
        }
        numeric_options = {"bins": [20454, 20459, 20465], "stat": "density"}
        axis = "x"
    else:
        options = {"clip": ["2026-01-01", "2026-01-12"], "cut": 0}
        numeric_options = {"clip": [20454, 20465], "cut": 0}
        axis = "y" if kind == "violin" else "x"
    plot = getattr(mp.plot(source), kind)("t", **options).date_axis(
        axis, timezone="UTC"
    )
    reference = getattr(mp.plot({"t": DAYS}), kind)("t", **numeric_options)
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_mixed_iso_and_numeric_bounds_are_rejected_instead_of_guessing_units():
    plot = (
        mp.plot({"t": DATES})
        .hist("t", bins=["2026-01-01", 20465])
        .date_axis("x", timezone="UTC")
    )
    assert any(
        "all ISO strings or all day coordinates" in i for i in mp.validate(plot.spec)
    )


@pytest.mark.parametrize("mode", ["residual", "logistic"])
def test_non_calendar_regression_outputs_cannot_use_a_calendar_response_axis(mode):
    plot = mp.plot({"x": [1, 2, 3, 4], "t": ["1970-01-01", "1970-01-02"] * 2})
    if mode == "residual":
        plot.residplot("x", "t")
    else:
        plot.regplot("x", "t", regression={"model": "logistic"})
    plot.date_axis("y", timezone="UTC")
    assert any("calendar regression response" in i for i in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="calendar regression response"):
        plot.render()


def test_date_predictor_residuals_remain_numeric_durations():
    plot = (
        mp.plot({"t": DATES, "v": [1, 2, 4, 5, 9, 11]})
        .residplot("t", "v")
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert plot.spec.panels[0].y.temporal is None
        np.testing.assert_allclose(
            np.asarray(figure.axes[0].collections[0].get_offsets())[:, 0], DAYS
        )
    finally:
        plt.close(figure)


def test_regression_date_predictor_matches_declared_day_reference():
    source = {"t": DATES, "v": [1, 2, 3, 6, 8, 11]}
    plot = mp.plot(source).regplot("t", "v").date_axis("x", timezone="UTC")
    reference = mp.plot({**source, "t": DAYS}).regplot("t", "v")
    assert mp.validate(plot.spec) == []
    f, r = plot.render(), reference.render()
    try:
        _assert_geometry(_geometry(f.axes[0]), _geometry(r.axes[0]))
        assert plot.spec.data.columns == source
    finally:
        plt.close(f)
        plt.close(r)


def test_weighted_date_regression_excludes_zero_weight_rows_before_parsing():
    source = {"t": [*DATES, "bad"], "v": [1, 2, 3, 6, 8, 11, 20], "w": [1] * 6 + [0]}
    plot = mp.plot(source).regplot("t", "v", weights="w").date_axis("x", timezone="UTC")
    assert mp.validate(plot.spec) == []
    plt.close(plot.render())
    assert plot.spec.data.columns == source


@pytest.mark.parametrize("kind", ["hist", "kde", "ecdf"])
def test_temporal_distribution_selection_precedes_parsing(kind):
    source = {"t": [*DATES, "bad"], "w": [1] * len(DATES) + [0]}
    plot = getattr(mp.plot(source), kind)("t", weights="w").date_axis(
        "x", timezone="UTC"
    )
    before = copy.deepcopy(plot.spec.data.columns)
    assert mp.validate(plot.spec) == []
    plt.close(plot.render())
    assert plot.spec.data.columns == before


@pytest.mark.parametrize("kind", ["hist", "kde", "ecdf"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_calendar_axis_cannot_replace_mass_probability_or_density(kind, orient):
    plot = getattr(mp.plot({"t": DAYS}), kind)("t", orient=orient).date_axis(
        "y" if orient == "v" else "x", timezone="UTC"
    )
    assert any("temporal" in i and "mass" in i for i in mp.validate(plot.spec))
