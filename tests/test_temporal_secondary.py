"""Secondary-y routing for univariate distributions and explicit temporal semantics.

Vertical distributions put mass/density on y2. Horizontal KDE/ECDF instead
put observations on the actual y2 clock and mass/density on shared primary x.
"""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._quality import assess

from test_temporal_distributions import DATES, DAYS, _assert_geometry, _geometry

UNIVARIATE = {"ecdf": {}, "hist": {"bins": 3, "stat": "density"}, "kde": {"cut": 0}}


def _drawn(ax):
    """Drawn geometry, excluding empty legend proxies owned by semantic guides."""
    geometry = _geometry(ax)
    collections = [c for c in ax.collections if np.asarray(c.get_offsets()).size]
    geometry["lines"] = [line for line in geometry["lines"] if len(line[0])]
    geometry["paths"] = [p.vertices for c in collections for p in c.get_paths()]
    geometry["offsets"] = [np.asarray(c.get_offsets()) for c in collections]
    return geometry


def _assert_secondary_matches(plot, reference):
    assert mp.validate(plot.spec) == []
    before = plot.to_json()
    source = copy.deepcopy(plot.spec.data.columns)
    figure, expected_figure = plot.render(), reference.render()
    try:
        primary, secondary = figure.axes
        expected = expected_figure.axes[0]
        assert not any(len(values) for values in _drawn(primary).values())
        _assert_geometry(_drawn(secondary), _drawn(expected))
        np.testing.assert_allclose(secondary.get_xlim(), expected.get_xlim())
        np.testing.assert_allclose(secondary.get_ylim(), expected.get_ylim())
    finally:
        plt.close(figure)
        plt.close(expected_figure)
    assert plot.spec.data.columns == source and plot.to_json() == before
    assert mp.Plot.from_json(before).spec == plot.spec
    assert mp.apply(plot.action_log) == plot.spec


@pytest.mark.parametrize("kind", sorted(UNIVARIATE))
@pytest.mark.parametrize("temporal", [False, True], ids=["numeric", "iso"])
def test_vertical_univariate_y2_matches_primary_day_reference(kind, temporal):
    source = {"t": DATES if temporal else DAYS, "w": [1, 2, 3, 4, 2, 1]}
    options = {"weights": "w", **UNIVARIATE[kind]}
    plot = getattr(mp.plot(source).secondary_yaxis("Mass"), kind)(
        "t", axis="y2", **options
    )
    if temporal:
        plot.date_axis("x", timezone="UTC")
    reference = getattr(mp.plot({**source, "t": DAYS}), kind)("t", **options)
    _assert_secondary_matches(plot, reference)


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_legacy_y2_distribution_keeps_its_declared_log_mass_axis(kind):
    source = {"x": [1.0, 2.0, 2.5, 4.0, 5.0, 7.0]}
    plot = getattr(mp.plot(source).secondary_yaxis("Mass", scale="log"), kind)(
        "x", axis="y2"
    )
    layer = plot.spec.panels[0].layers[0]
    assert getattr(layer, "histogram" if kind == "hist" else "kde") is None
    reference = getattr(mp.plot(source), kind)("x").yscale("log")
    _assert_secondary_matches(plot, reference)


@pytest.mark.parametrize("kind", sorted(UNIVARIATE))
def test_typed_y2_mass_axis_keeps_the_primary_linear_contract(kind):
    source = {"x": [1.0, 2.0, 4.0]}
    plot = getattr(mp.plot(source).secondary_yaxis("Mass", scale="log"), kind)(
        "x", axis="y2", **UNIVARIATE[kind]
    )
    primary = getattr(mp.plot(source), kind)("x", **UNIVARIATE[kind]).yscale("log")
    issues = mp.validate(plot.spec)
    assert issues and issues == mp.validate(primary.spec)


def test_horizontal_histogram_y2_rejection_preserves_source_and_history():
    plot = (
        mp.plot({"x": [1.0, 2.0, 4.0]})
        .secondary_yaxis("Value")
        .hist("x", axis="y2", orient="h", bins=3, stat="density")
    )
    before, history = plot.to_json(), plot.action_log
    figures = plt.get_fignums()
    assert mp.validate(plot.spec)
    with pytest.raises(ValueError):
        plot.render()
    assert plot.to_json() == before and plot.action_log == history
    assert plt.get_fignums() == figures


@pytest.mark.parametrize("kind", ["ecdf", "kde"])
@pytest.mark.parametrize("temporal", [False, True], ids=["numeric", "iso"])
def test_horizontal_observations_use_actual_y2_and_preserve_primary_value_frame(
    kind, temporal
):
    import math
    from fractions import Fraction

    observed = list(DAYS if temporal else [1.0, 2.0, 4.0])
    weights = [index + 1 for index in range(len(observed))]
    source = {
        "observation": list(DATES) if temporal else observed,
        "w": weights,
        "reference_x": np.linspace(0, 1, len(observed)).tolist(),
        "reference_y": list(range(3, len(observed) + 3)),
    }
    plot = (
        mp.plot(source)
        .line("reference_x", "reference_y")
        .secondary_yaxis("Observations")
    )
    if kind == "ecdf":
        plot.ecdf("observation", weights="w", orient="h", axis="y2")
    else:
        plot.kde(
            "observation",
            orient="h",
            axis="y2",
            kde=mp.KDESpec(weights="w", bw_method=0.6, cut=0, gridsize=17),
        )
    if temporal:
        plot.date_axis("y2", timezone="UTC")
    before = plot.to_json()
    reference_figure, reference = plt.subplots()
    reference.plot(source["reference_x"], source["reference_y"])
    figure = plot.render()
    try:
        primary, secondary = figure.axes
        np.testing.assert_array_equal(
            primary.dataLim.get_points()[:, 1], reference.dataLim.get_points()[:, 1]
        )
        np.testing.assert_allclose(primary.get_ylim(), reference.get_ylim())
        line = next(artist for artist in secondary.lines if len(artist.get_xdata()))
        if kind == "ecdf":
            masses = {}
            for value, weight in zip(observed, weights, strict=True):
                key = Fraction(value)
                masses[key] = masses.get(key, 0) + weight
            total, prefix = sum(weights), 0
            vertices = line.get_path().vertices
            for value, mass in sorted(masses.items()):
                for endpoint in (prefix, prefix + mass):
                    expected = [float(Fraction(endpoint, total)), float(value)]
                    assert any(np.array_equal(point, expected) for point in vertices)
                prefix += mass
        else:
            total = sum(weights)
            mean = (
                sum(
                    Fraction(value) * weight
                    for value, weight in zip(observed, weights, strict=True)
                )
                / total
            )
            variance = sum(
                weight * (Fraction(value) - mean) ** 2
                for value, weight in zip(observed, weights, strict=True)
            ) / (total - Fraction(sum(weight**2 for weight in weights), total))
            bandwidth = math.sqrt(float(variance)) * 0.6
            expected = [
                sum(
                    weight * math.exp(-0.5 * ((query - value) / bandwidth) ** 2)
                    for value, weight in zip(observed, weights, strict=True)
                )
                / (total * bandwidth * math.sqrt(2 * math.pi))
                for query in line.get_ydata()
            ]
            np.testing.assert_allclose(line.get_xdata(), expected, rtol=3e-13, atol=0)
        assert plot.to_json() == before and plot.spec.data.columns == source
        assert mp.Plot.from_json(before).spec == plot.spec
        assert mp.apply(plot.action_log) == plot.spec
    finally:
        plt.close(figure)
        plt.close(reference_figure)


@pytest.mark.parametrize("kind", sorted(UNIVARIATE))
def test_secondary_mass_probability_density_axis_cannot_be_calendar_time(kind):
    plot = getattr(mp.plot({"x": [1, 2, 3]}).secondary_yaxis("Mass"), kind)(
        "x", axis="y2"
    )
    plot.date_axis("y2", timezone="UTC")
    assert any(
        "mass/probability/density axes cannot be temporal" in issue
        for issue in mp.validate(plot.spec)
    )


@pytest.mark.parametrize("kind", ["scatter", "lineplot"])
@pytest.mark.parametrize("clock", ["x", "y2"])
def test_semantic_y2_marks_use_the_declared_clock(kind, clock):
    temporal_x = clock == "x"
    source = {
        "x": DATES if temporal_x else [1, 1, 2, 2, 3, 3],
        "y": [1.0, 3.0, 2.0, 5.0, 4.0, 6.0] if temporal_x else DATES,
        "g": ["u", "v"] * 3,
    }
    numeric = {**source, ("x" if temporal_x else "y"): DAYS}
    options = (
        {"hue": "g", "errorbar": None}
        if kind == "lineplot"
        else {"semantics": {"hue": "g"}}
    )
    plot = getattr(mp.plot(source).secondary_yaxis("Second"), kind)(
        "x", "y", axis="y2", **options
    ).date_axis(clock, timezone="UTC")
    reference = getattr(mp.plot(numeric), kind)("x", "y", **options)
    _assert_secondary_matches(plot, reference)


def test_primary_and_y2_semantic_layers_share_one_declared_hue_domain():
    source = {
        "x": [1, 2, 3, 1, 2, 3],
        "t": DATES,
        "v": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "g": ["u", "v"] * 3,
    }
    semantics = {"hue": "g", "scale_id": "shared"}
    plot = (
        mp.plot(source)
        .secondary_yaxis("Date")
        .scatter("x", "v", semantics=semantics)
        .scatter("x", "t", axis="y2", semantics=semantics)
        .date_axis("y2", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        primary, secondary = figure.axes
        drawn = [
            [c for c in ax.collections if np.asarray(c.get_offsets()).size]
            for ax in (primary, secondary)
        ]
        assert [len(collections) for collections in drawn] == [1, 1]
        offsets = np.asarray(drawn[1][0].get_offsets(), dtype=float)
        np.testing.assert_allclose(offsets[:, 1], DAYS)
        np.testing.assert_allclose(
            np.asarray(drawn[0][0].get_facecolor(), dtype=float),
            np.asarray(drawn[1][0].get_facecolor(), dtype=float),
        )
        legend = secondary.get_legend()
        assert primary.get_legend() is None
        assert legend is not None
    finally:
        plt.close(figure)
    assert plot.spec.data.columns == source


def test_invalid_semantic_y2_clock_role_contracts_reject_atomically():
    source = {"x": [1, 2], "t": DATES[:2], "v": [3.0, 4.0], "g": ["a", "b"]}

    def base():
        return mp.plot(source).secondary_yaxis("Second")

    cases = [
        base().scatter("x", "t", axis="y2", semantics={"hue": "g"}),
        base().scatter("x", "v", axis="y2", semantics={"hue": "g"}),
        # Horizontal t is the X response; this y2 clock instead sees numeric x.
        base()
        .lineplot("x", "t", axis="y2", hue="g", errorbar=None, orient="h")
        .date_axis("y2", timezone="UTC"),
    ]
    for plot in cases:
        before, history = plot.to_json(), plot.action_log
        figures = plt.get_fignums()
        assert mp.validate(plot.spec)
        with pytest.raises(ValueError):
            plot.render()
        assert plot.to_json() == before and plot.action_log == history
        assert plot.spec.data.columns == source
        assert plt.get_fignums() == figures


RAW_DATE_X = {
    "band": lambda p, axis: p.band("t", "lo", "v", axis=axis),
    "bar": lambda p, axis: p.bar("t", "v", axis=axis),
    "errorbar": lambda p, axis: p.errorbar("t", "v", yerr="e", axis=axis),
    "hexbin": lambda p, axis: p.hexbin("t", "v", axis=axis, colorbar=False),
    "hist2d": lambda p, axis: p.hist2d("t", "v", bins=3, axis=axis, colorbar=False),
    "line": lambda p, axis: p.line("t", "v", axis=axis),
    "regplot": lambda p, axis: p.regplot("t", "v", axis=axis),
    "scatter": lambda p, axis: p.scatter("t", "v", axis=axis),
    "stem": lambda p, axis: p.stem("t", "v", axis=axis),
    "stripplot": lambda p, axis: p.stripplot("t", "v", axis=axis),
}


@pytest.mark.parametrize("kind", sorted(RAW_DATE_X))
def test_raw_y2_marks_share_the_primary_date_x_clock(kind):
    source = {
        "t": DATES,
        "v": [1.0, 3.0, 2.0, 5.0, 4.0, 6.0],
        "e": [0.1] * 6,
        "lo": [0.5, 2.0, 1.0, 4.0, 3.0, 5.0],
    }
    build = RAW_DATE_X[kind]
    plot = build(mp.plot(source).secondary_yaxis("Second"), "y2").date_axis(
        "x", timezone="UTC"
    )
    reference = build(mp.plot({**source, "t": DAYS}), "y")
    _assert_secondary_matches(plot, reference)


@pytest.mark.parametrize("kind", ["line", "scatter", "stripplot"])
def test_raw_y2_date_responses_use_the_secondary_clock(kind):
    source = {"x": [1, 2, 3, 4, 5, 6], "t": DATES}
    plot = getattr(mp.plot(source).secondary_yaxis("Date"), kind)(
        "x", "t", axis="y2"
    ).date_axis("y2", timezone="UTC")
    reference = getattr(mp.plot({**source, "t": DAYS}), kind)("x", "t")
    _assert_secondary_matches(plot, reference)


@pytest.mark.parametrize("axis", ["y", "y2"])
def test_declared_log_response_scale_applies_before_typed_regression_checks(axis):
    # Secondary scales must be active while drawing, exactly like primary scales.
    source = {"x": [1.0, 2, 3, 4, 5], "y": [5.0, 3, 1, 0.5, 0.2], "w": [1.0] * 5}
    plot = mp.plot(source)
    if axis == "y2":
        plot.secondary_yaxis("Response", scale="log")
    else:
        plot.yscale("log")
    plot.regplot("x", "y", axis=axis, weights="w")
    with pytest.raises(ValueError, match="positive on log y"):
        plot.render()
    plt.close("all")


def test_secondary_temporal_step_dodge_matches_numeric_day_reference():
    source = {"t": DATES, "g": ["A", "B"] * 3, "w": [1, 2, 3, 4, 2, 1]}
    reference = {**source, "t": DAYS}

    def build(data, axis):
        return mp.plot(data).hist(
            "t",
            bins=3,
            group="g",
            weights="w",
            element="step",
            multiple="dodge",
            stat="density",
            axis=axis,
        )

    plot = build(source, "y2").secondary_yaxis("Density").date_axis("x", timezone="UTC")
    _assert_secondary_matches(plot, build(reference, "y"))


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_secondary_distributions_do_not_change_primary_ordinal_y(kind):
    source = {"c": ["a", "b", "a"], "v": [1.0, 2.0, 3.0]}
    plot = (
        mp.plot(source)
        .secondary_yaxis("Density")
        .barplot("c", "v", orient="h", errorbar=None)
    )
    getattr(plot, kind)("v", axis="y2", **UNIVARIATE[kind])
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert [label.get_text() for label in figure.axes[0].get_yticklabels()] == [
            "a",
            "b",
        ]
        assert figure.axes[1].get_ylim()[1] > 0
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["hist", "kde"])
def test_secondary_distribution_still_rejects_shared_ordinal_x(kind):
    plot = (
        mp.plot({"c": ["a", "b", "a"], "v": [1.0, 2.0, 3.0]})
        .secondary_yaxis("Density")
        .barplot("c", "v", errorbar=None)
    )
    getattr(plot, kind)("v", axis="y2", **UNIVARIATE[kind])
    assert any(
        "numeric x axis cannot mix ordinal categories" in issue
        for issue in mp.validate(plot.spec)
    )


def test_temporal_secondary_scatter_does_not_change_primary_ordinal_y():
    plot = (
        mp.plot({"c": ["a", "b", "a"], "v": [1.0, 2.0, 3.0], "t": DATES[:3]})
        .secondary_yaxis("Observed date")
        .barplot("c", "v", orient="h", errorbar=None)
        .scatter("v", "t", semantics={"hue": "c"}, axis="y2")
        .date_axis("y2", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert [label.get_text() for label in figure.axes[0].get_yticklabels()] == [
            "a",
            "b",
        ]
        observed = sorted(
            point[1]
            for collection in figure.axes[1].collections
            for point in np.asarray(collection.get_offsets())
        )
        assert observed == DAYS[:3]
    finally:
        plt.close(figure)


@pytest.mark.parametrize("axis", ["y", "y2"])
@pytest.mark.parametrize(
    ("kind", "code"), [("scatter", "overcrowded-data"), ("hist", "hatch-noise")]
)
def test_temporal_primary_and_secondary_artists_share_quality_diagnostics(
    axis, kind, code
):
    source = {"t": [DATES[0]] * 60, "v": [1.0] * 60, "g": ["a"] * 60}
    plot = mp.plot(source).secondary_yaxis("Mass").date_axis("x", timezone="UTC")
    if kind == "scatter":
        plot.scatter("t", "v", semantics={"hue": "g"}, axis=axis)
    else:
        plot.hist("t", bins=6, stat="count", group="g", axis=axis)
    before = plot.to_json()
    figure = plot.render()
    try:
        if kind == "hist":
            patches = figure.axes[0 if axis == "y" else 1].patches
            assert len(patches) >= 6
            for patch in patches:
                patch.set_hatch("///")
        issues = [issue for issue in assess(figure, plot.spec) if issue.code == code]
        assert len(issues) == 1 and issues[0].panel == 0
    finally:
        plt.close(figure)
    assert plot.to_json() == before
