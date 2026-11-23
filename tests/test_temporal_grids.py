"""F02/G02/G03 ISO grid integration retains original variables and clock metadata."""

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

from test_temporal_distributions import _assert_geometry, _geometry

DATES = ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-11"]
DAYS = [20454, 20455, 20457, 20464]


@pytest.mark.parametrize("kind", ["hist", "kde", "ecdf"])
@pytest.mark.parametrize("axis", ["x", "y"])
def test_iso_joint_marginals_match_canonical_day_reference(kind, axis):
    source = {"t": DATES, "v": [1, 3, 2, 4]}
    numeric = {**source, "t": DAYS}
    x, y = ("t", "v") if axis == "x" else ("v", "t")
    options = {
        "bins": 3 if kind == "hist" else 20,
        "marginal_kind": kind,
        "marginal_stat": "probability" if kind == "ecdf" else "density",
    }
    plot = (
        mp.plot(source).scatter(x, y).date_axis(axis, timezone="UTC").joint(**options)
    )
    reference = mp.plot(numeric).scatter(x, y).joint(**options)
    assert mp.validate(plot.spec) == []
    assert (
        plot.spec.panels[0].x.temporal is not None
        if axis == "x"
        else plot.spec.panels[0].y.temporal is not None
    )
    before = plot.to_json()
    f, r = plot.render(), reference.render()
    try:
        for actual, expected in zip(f.axes, r.axes, strict=True):
            _assert_geometry(_geometry(actual), _geometry(expected))
        assert plot.spec.data.columns == source and plot.to_json() == before
        assert mp.Plot.from_json(before).spec == plot.spec
        assert mp.apply(plot.action_log) == plot.spec
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize("kind", ["hist", "kde", "ecdf"])
def test_iso_pair_variables_use_explicit_per_variable_clocks(kind):
    source = {"t": DATES, "v": [1, 3, 2, 4]}
    options = {
        "bins": 3 if kind == "hist" else 20,
        "diag_kind": kind,
        "diag_stat": "probability" if kind == "ecdf" else "density",
    }
    plot = mp.plot(source).pair(
        ["t", "v"], temporal={"t": {"timezone": "UTC"}}, **options
    )
    reference = mp.plot({**source, "t": DAYS}).pair(["t", "v"], **options)
    assert mp.validate(plot.spec) == []
    assert (
        plot.spec.panels[0].x.temporal is not None
        and plot.spec.panels[0].y.temporal is None
    )
    assert plot.spec.panels[1].y.temporal is not None
    assert plot.spec.panels[2].x.temporal is not None
    before = plot.to_json()
    assert mp.apply(plot.action_log) == plot.spec
    assert mp.Plot.from_json(before).spec == plot.spec
    f, r = plot.render(), reference.render()
    try:
        for actual, expected in zip(f.axes, r.axes, strict=True):
            _assert_geometry(_geometry(actual), _geometry(expected))
        assert plot.spec.data.columns == source and plot.to_json() == before
    finally:
        plt.close(f)
        plt.close(r)


@pytest.mark.parametrize(
    "temporal",
    [
        {"missing": {"timezone": "UTC"}},
        {"t": {"unit": "s"}},
        {"t": {"timezone": "Europe/Paris"}},
        {"t": {"callback": "unsafe"}},
        {"t": 1},
    ],
)
def test_pair_temporal_declarations_are_explicit_strict_and_transactional(temporal):
    plot = mp.plot({"t": DATES, "v": [1, 2, 3, 4]})
    before = plot.to_json()
    with pytest.raises((ValueError, TypeError)):
        plot.pair(["t", "v"], temporal=temporal)
    assert plot.to_json() == before


def test_naive_pair_clock_requires_timezone_without_guessing():
    with pytest.raises(ValueError, match="explicit timezone"):
        mp.plot({"t": DATES, "v": [1, 2, 3, 4]}).pair(["t", "v"], temporal={"t": {}})


def test_group_selection_precedes_pair_date_parsing_and_keeps_source_rows():
    source = {"t": [*DATES, "bad"], "v": [1, 2, 3, 4, 5], "g": ["keep"] * 4 + ["omit"]}
    plot = mp.plot(source).pair(
        ["t", "v"],
        group="g",
        hue_order=["keep"],
        temporal={"t": mp.TemporalSpec(timezone="UTC")},
        bins=3,
    )
    assert mp.validate(plot.spec) == [] and plot.spec.data.columns == source
    assert mp.apply(plot.action_log) == plot.spec
    figure = plot.render()
    plt.close(figure)
    assert plot.spec.data.columns == source


def test_two_temporal_pair_variables_preserve_pairwise_missing_rows_and_metadata():
    source = {
        "t": [*DATES, None],
        "u": ["2027-01-01", None, "2027-01-04", "2027-01-11", "2027-01-12"],
    }
    plot = mp.plot(source).pair(
        ["t", "u"],
        temporal={"t": {"timezone": "UTC"}, "u": {"timezone": "+02:00"}},
        bins=3,
    )
    assert mp.validate(plot.spec) == []
    for index, panel in enumerate(plot.spec.panels):
        assert panel.x.temporal is not None
        assert (panel.y.temporal is None) == (index in (0, 3))
    assert mp.apply(plot.action_log) == plot.spec
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
    figure = plot.render()
    plt.close(figure)
    assert plot.spec.data.columns == source


def test_pair_action_keeps_legacy_positional_arguments_and_default_json_shape():
    action = mp.actions.SetPairGrid(["a", "b"], "g")
    assert action.group == "g" and action.temporal is None
    encoded = mp.action_to_dict(action)
    assert "temporal" not in encoded
    assert mp.action_from_dict(encoded) == action


def test_undeclared_iso_pair_does_not_guess_clock_or_change_legacy_defaults():
    with pytest.raises(ValueError, match="numeric"):
        mp.plot({"t": DATES, "v": [1, 2, 3, 4]}).pair(["t", "v"])
