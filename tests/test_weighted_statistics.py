"""Weighted/cluster bootstrap contracts compared with independent formulas."""

import json
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from mudplot._estimate import summarize
from mudplot._stat import usable_rows


def _point(p):
    return summarize(p.spec.data.columns, p.spec.panels[0].layers[0]).estimates[0]


def _weighted_plot(**kwargs):
    return mp.plot({"x": ["A"] * 4, "y": [1, 2, 8, 100], "w": [1, 3, 2, 0]}).barplot(
        "x", "y", weights="w", **kwargs
    )


def test_weighted_mean_drops_zero_weight_rows_without_mutating_data():
    p = _weighted_plot(errorbar=None)
    assert mp.validate(p.spec) == []
    point = _point(p)
    assert point.value == pytest.approx(23 / 6)
    assert point.n == 3 and point.lower is None
    assert p.spec.data.columns["w"] == [1, 3, 2, 0]
    assert usable_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [0, 1, 2]


def test_weighted_ci_resamples_value_weight_pairs_not_weighted_sampling_probabilities():
    p = _weighted_plot(n_boot=107, seed=42, errorbar=("ci", 80))
    rng = np.random.default_rng(42)
    values, weights = np.array([1, 2, 8]), np.array([1, 3, 2])
    indices = rng.integers(0, 3, size=(107, 3))
    expected = np.quantile(
        np.sum(values[indices] * weights[indices], axis=1)
        / np.sum(weights[indices], axis=1),
        [0.1, 0.9],
    )
    point = _point(p)
    assert point.lower is not None and point.upper is not None
    np.testing.assert_allclose([point.lower, point.upper], expected)
    assert _point(p) == point


def test_weighted_bootstrap_chunks_do_not_change_results(monkeypatch):
    from mudplot import _estimate

    p = _weighted_plot(n_boot=107, seed=42)
    first = _point(p)
    monkeypatch.setattr(_estimate, "_BOOTSTRAP_CHUNK_ELEMENTS", 9)
    assert _point(p) == first


def test_weighted_mean_scaling_avoids_overflow_in_products_or_weight_sum():
    p = mp.plot({"x": ["A", "A"], "y": [1e308, 1e308], "w": [1e308, 1e308]}).barplot(
        "x", "y", weights="w", errorbar=None
    )
    assert _point(p).value == 1e308


@pytest.mark.parametrize("weighted", [False, True])
def test_hierarchical_ci_matches_independent_unit_then_row_resampling(weighted):
    data = {
        "x": ["A"] * 5,
        "y": [1, 2, 8, 9, 10],
        "unit": ["u1"] * 2 + ["u2"] * 3,
        "w": [1, 3, 2, 1, 2],
    }
    p = mp.plot(data).pointplot(
        "x",
        "y",
        units="unit",
        weights="w" if weighted else None,
        n_boot=101,
        seed=42,
        errorbar=("ci", 80),
    )
    assert mp.validate(p.spec) == []
    rng = np.random.default_rng(42)
    clusters = [[0, 1], [2, 3, 4]]
    results = []
    for _ in range(101):
        chosen = rng.integers(0, 2, 2)
        rows = []
        for j in chosen:
            cluster = clusters[j]
            rows.extend(cluster[k] for k in rng.integers(0, len(cluster), len(cluster)))
        values = [data["y"][i] for i in rows]
        weights = [data["w"][i] for i in rows] if weighted else None
        results.append(np.average(values, weights=weights))
    point = _point(p)
    expected_center = np.average(data["y"], weights=data["w"] if weighted else None)
    assert point.value == pytest.approx(expected_center)
    assert point.n == 5 and point.n_units == 2
    assert point.lower is not None and point.upper is not None
    np.testing.assert_allclose(
        [point.lower, point.upper], np.quantile(results, [0.1, 0.9])
    )


def test_one_unit_does_not_invent_between_unit_uncertainty():
    p = mp.plot({"x": ["A"] * 3, "y": [1, 2, 3], "u": ["same"] * 3}).barplot(
        "x", "y", units="u"
    )
    point = _point(p)
    assert point.n == 3 and point.n_units == 1
    assert point.lower is None and point.upper is None
    with pytest.warns(UserWarning, match="independent resampling units"):
        p.render()


def test_missing_weights_and_units_are_listwise_dropped():
    p = mp.plot(
        {
            "x": ["A"] * 4,
            "y": [1, 2, 3, 100],
            "w": [1, 1, None, 1],
            "u": ["a", "b", "c", None],
        }
    ).barplot("x", "y", weights="w", units="u")
    assert _point(p).value == 1.5 and _point(p).n == 2


@pytest.mark.parametrize(
    "weights,message",
    [
        ([0, 0], "no usable observations"),
        ([-1, 1], "nonnegative"),
        ([True, 1], "nonnegative"),
        (["1", 2], "nonnegative"),
    ],
)
def test_bad_weights_are_rejected(weights, message):
    p = mp.plot({"x": ["A", "A"], "y": [1, 2], "w": weights}).barplot(
        "x", "y", weights="w"
    )
    assert any(message in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "options,message",
    [
        ({"weights": "unknown"}, "existing column"),
        ({"weights": ""}, "existing column"),
        ({"weights": "w", "estimator": "median"}, "weights support mean"),
        ({"weights": "w", "errorbar": "se"}, "weights support mean"),
        ({"units": "u", "errorbar": None}, "units require bootstrap"),
        ({"units": "missing"}, "existing column"),
    ],
)
def test_unsupported_or_ignored_weight_unit_settings_are_explicit(options, message):
    p = mp.plot({"x": ["A", "A"], "y": [1, 2], "w": [1, 2], "u": ["a", "b"]})
    p.barplot("x", "y", **options)
    assert any(message in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "stat,scale",
    [("count", 5), ("probability", 1), ("proportion", 1), ("percent", 100)],
)
def test_count_normalization_uses_all_usable_rows_across_hues(stat, scale):
    p = mp.plot(
        {"x": ["A", "A", "A", "B", "B", None], "g": ["u", "v", "u", "v", "v", "u"]}
    ).countplot("x", group="g", stat=stat)
    assert mp.validate(p.spec) == []
    summary = summarize(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert sum(point.value for point in summary.estimates) == pytest.approx(scale)
    assert [point.value for point in summary.estimates] == pytest.approx(
        [2 / 5 * scale, 1 / 5 * scale, 2 / 5 * scale]
    )
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_weighted_units_and_normalization_paths_still_have_dependency_free_builders():
    code = """
import sys
import mudplot as mp
raw = {"x": ["A"] * 4, "y": [1,2,3,4], "w": [1,2,3,4], "u": ["a","a","b","b"]}
p = (mp.plot(raw).barplot("x", "y", weights="w", units="u")
     .countplot("x", stat="percent"))
assert mp.validate(p.spec) == []
assert mp.Plot.from_json(p.to_json()).spec == p.spec
assert "numpy" not in sys.modules
assert "matplotlib" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_weighted_settings_survive_actions_schema_and_editor_json():
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    data = {
        "x": ["A"] * 4,
        "y": [1, 2, 3, 4],
        "w": [1, 2, 3, 4],
        "u": ["a", "a", "b", "b"],
    }
    session = EditorSession()
    session.dispatch_safe(A.SetData(data))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "barplot",
            "layer_json": json.dumps(
                {
                    "x": "x",
                    "y": "y",
                    "stat": {"weights": "w", "units": "u", "seed": 42},
                }
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    replay = mp.apply([A.action_to_dict(a) for a in session.store.history])
    assert replay.panels[0].layers[0].stat is not None
