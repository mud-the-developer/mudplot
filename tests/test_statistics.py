"""Numeric contract tests for the shared estimation effect (no image guesses)."""

import json
import subprocess
import sys

import mudplot as mp
import numpy as np
import pytest
from mudplot._estimate import summarize
from mudplot._stat import make_stat
from mudplot.spec import LayerSpec, StatSpec


def _summary(
    values, estimator="mean", errorbar=None, *, level=None, n_boot=1000, seed=0
):
    layer = LayerSpec(
        type="barplot",
        x="category",
        y="value",
        stat=StatSpec(
            estimator=estimator,
            errorbar=errorbar,
            level=level,
            n_boot=n_boot,
            seed=seed,
        ),
    )
    return summarize({"category": ["A"] * len(values), "value": values}, layer)


@pytest.mark.parametrize(
    "estimator,expected",
    [
        ("mean", 3.5),
        ("median", 2.5),
        ("sum", 14),
        ("min", 1),
        ("max", 8),
        ("count", 4),
    ],
)
def test_named_estimators_match_reference_values(estimator, expected):
    result = _summary([1, 2, 3, 8], estimator).estimates[0]
    assert result.value == pytest.approx(expected)
    assert result.n == 4
    assert result.lower is None and result.upper is None


@pytest.mark.parametrize("method", ["sd", "se"])
@pytest.mark.parametrize("level", [None, 2.0])
def test_sd_and_sem_use_sample_ddof_and_distinct_units(method, level):
    values = [1, 2, 3, 4]
    result = _summary(values, errorbar=method, level=level).estimates[0]
    width = np.std(values, ddof=1)
    if method == "se":
        width /= np.sqrt(len(values))
    width *= 1 if level is None else level
    assert result.value == 2.5
    assert result.lower == pytest.approx(2.5 - width)
    assert result.upper == pytest.approx(2.5 + width)


def test_percentile_interval_can_honestly_exclude_the_estimate():
    result = _summary(
        [1, 2, 3, 100], estimator="min", errorbar="pi", level=50
    ).estimates[0]
    assert result.value == 1
    assert result.lower is not None
    assert result.lower == pytest.approx(1.75)
    assert result.upper == pytest.approx(27.25)
    assert result.lower > result.value


@pytest.mark.parametrize("estimator", ["mean", "median", "sum", "min", "max", "count"])
def test_bootstrap_ci_matches_independent_seeded_reference(estimator):
    values = np.array([1, 2, 3, 8.0])
    rng = np.random.default_rng(42)
    resampled = values[rng.integers(0, len(values), size=(101, len(values)))]
    if estimator == "count":
        estimates = np.full(101, len(values))
    else:
        estimates = getattr(np, estimator)(resampled, axis=1)
    expected = np.quantile(estimates, [0.1, 0.9])
    result = _summary(list(values), estimator, "ci", level=80, n_boot=101, seed=42)
    point = result.estimates[0]
    assert point.lower is not None and point.upper is not None
    np.testing.assert_allclose([point.lower, point.upper], expected, rtol=1e-12)
    assert result == _summary(
        list(values), estimator, "ci", level=80, n_boot=101, seed=42
    )


def test_bootstrap_chunking_does_not_change_rng_or_estimated_quantiles(monkeypatch):
    from mudplot import _estimate

    values = [1, 2, 4, 7, 10]
    first = _summary(values, errorbar="ci", n_boot=107, seed=2026)
    monkeypatch.setattr(_estimate, "_BOOTSTRAP_CHUNK_ELEMENTS", 15)
    second = _summary(values, errorbar="ci", n_boot=107, seed=2026)
    assert second == first


def test_local_bootstrap_rng_does_not_modify_numpy_global_rng_state():
    before = np.random.get_state()
    _summary([1, 2, 3, 4], errorbar="ci", seed=123)
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize("method", [None, "sd", "se", "pi", "ci"])
def test_singleton_keeps_estimate_but_does_not_invent_an_interval(method):
    point = _summary([3], errorbar=method).estimates[0]
    assert point.value == 3 and point.n == 1
    assert point.lower is None and point.upper is None


@pytest.mark.parametrize("method", ["sd", "se", "pi", "ci"])
def test_constant_repeated_values_have_valid_zero_width_intervals(method):
    point = _summary([3, 3, 3], errorbar=method).estimates[0]
    assert point.lower == point.upper == point.value == 3


def test_grouping_drops_missing_observations_and_preserves_first_seen_order():
    columns = {
        "x": ["B", "A", "B", "A", None, "C", "D"],
        "y": [2, 1, 4, 3, 10, None, 10],
        "g": ["z", "a", "z", "a", "z", "z", None],
    }
    layer = LayerSpec(
        type="barplot", x="x", y="y", group="g", stat=StatSpec(errorbar=None)
    )
    result = summarize(columns, layer)
    assert result.categories == ["B", "A"]
    assert result.groups == ["z", "a"]
    assert [(p.category, p.group, p.value, p.n) for p in result.estimates] == [
        ("B", "z", 3, 2),
        ("A", "a", 2, 2),
    ]


def test_countplot_counts_usable_categories_and_hues_without_a_value_column():
    columns = {
        "x": ["B", "A", "B", None, "A", "C"],
        "g": ["z", "a", "z", "z", None, "z"],
    }
    result = summarize(columns, LayerSpec(type="countplot", x="x", group="g"))
    assert result.categories == ["B", "A", "C"]
    assert result.groups == ["z", "a"]
    assert [(p.category, p.group, p.value) for p in result.estimates] == [
        ("B", "z", 2),
        ("C", "z", 1),
        ("A", "a", 1),
    ]
    assert all(p.lower is None and p.upper is None for p in result.estimates)


def test_sparse_high_cardinality_groups_do_not_materialize_a_cartesian_product():
    n = 1000
    columns = {"x": list(range(n)), "g": [f"g{i}" for i in range(n)]}
    result = summarize(columns, LayerSpec(type="countplot", x="x", group="g"))
    assert len(result.estimates) == n
    assert all(p.value == 1 for p in result.estimates)


def test_scaled_mean_and_median_do_not_overflow_for_large_finite_values():
    for estimator in ("mean", "median"):
        point = _summary([1e308, 1e308], estimator).estimates[0]
        assert point.value == 1e308
    with pytest.raises(ValueError, match="finite plotting range"):
        _summary([1e308, 1e308], estimator="sum")


@pytest.mark.parametrize(
    "errorbar,method,level",
    [
        (None, None, None),
        ("sd", "sd", None),
        (("ci", 90), "ci", 90),
    ],
)
def test_interval_choice_is_a_named_serializable_configuration(errorbar, method, level):
    config = make_stat("median", errorbar, 101, 42)
    assert mp.StatSpec is StatSpec
    assert config.errorbar == method and config.level == level
    assert StatSpec.from_dict(json.loads(json.dumps(config.to_dict()))) == config
    layer = LayerSpec(type="pointplot", x="x", y="y", stat=config, dodge=0.3)
    assert LayerSpec.from_dict(layer.to_dict()) == layer


@pytest.mark.parametrize("value", [True, 1, (), ("ci",), ("ci", 95, "extra")])
def test_malformed_interval_choice_is_not_silently_interpreted(value):
    with pytest.raises(ValueError, match="errorbar"):
        make_stat("mean", value, 100, 0)


def test_statistical_configuration_and_serialization_remain_dependency_free():
    code = """
import sys
import mudplot as mp
from mudplot._stat import make_stat
from mudplot.spec import LayerSpec
config = make_stat("mean", ("ci", 95), 1000, 0)
layer = LayerSpec(type="barplot", x="x", y="y", stat=config)
assert LayerSpec.from_dict(layer.to_dict()) == layer
assert isinstance(config, mp.StatSpec)
p = (mp.plot({"x": ["A"] * 4, "y": [1, 2, 3, 4]})
       .barplot("x", "y", errorbar=("ci", 95))
       .pointplot("x", "y", errorbar=None)
       .countplot("x"))
assert mp.validate(p.spec) == []
assert mp.Plot.from_json(p.to_json()).spec == p.spec
assert "numpy" not in sys.modules
assert "matplotlib" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
