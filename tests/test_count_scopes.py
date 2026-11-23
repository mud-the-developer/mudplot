"""C06 contracts chosen by the owner: panel-local scopes and raw log sums."""

import copy
import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.container import BarContainer
from mudplot._estimate import summarize


def _data():
    return {"x": [1, 1, 10, 10], "g": ["u", "v", "u", "v"], "w": [2, 3, 4, 1]}


def _summary(plot):
    assert mp.validate(plot.spec) == []
    return summarize(plot.spec.data.columns, plot.spec.panels[0].layers[0])


@pytest.mark.parametrize("scope", [None, "all", "category", "group"])
@pytest.mark.parametrize("mode", ["probability", "proportion", "percent"])
@pytest.mark.parametrize("weighted", [False, True])
def test_each_scope_matches_independent_selected_mass_reference(scope, mode, weighted):
    data = _data()
    original = copy.deepcopy(data)
    plot = mp.plot(data).countplot(
        "x",
        group="g",
        weights="w" if weighted else None,
        stat=mode,
        normalize_scope=scope,
    )
    estimates = _summary(plot).estimates
    masses = data["w"] if weighted else [1] * 4
    factor = 100 if mode == "percent" else 1
    for estimate in estimates:
        cell = [
            i
            for i in range(4)
            if data["x"][i] == estimate.category and data["g"][i] == estimate.group
        ]
        selected = [
            i
            for i in range(4)
            if (scope != "category" or data["x"][i] == estimate.category)
            and (scope != "group" or data["g"][i] == estimate.group)
        ]
        expected = (
            math.fsum(masses[i] for i in cell)
            / math.fsum(masses[i] for i in selected)
            * factor
        )
        assert estimate.value == pytest.approx(expected)
    assert data == original and plot.spec.data.columns == original


@pytest.mark.parametrize("scope", ["all", "category", "group"])
def test_scope_filters_missing_zero_and_excluded_levels_before_denominator(scope):
    data = {
        "x": [1, 1, 10, 10, 100, None],
        "g": ["u", "v", "u", "v", "u", "u"],
        "w": [2, None, 4, 0, 1000, 1000],
    }
    plot = mp.plot(data).countplot(
        "x",
        group="g",
        weights="w",
        stat="percent",
        normalize_scope=scope,
        order=[10, 1],
        hue_order=["empty", "u", "v"],
    )
    result = _summary(plot)
    assert [(e.category, e.group) for e in result.estimates] == [(10, "u"), (1, "u")]
    expected = [100, 100] if scope == "category" else [200 / 3, 100 / 3]
    assert [e.value for e in result.estimates] == pytest.approx(expected)


@pytest.mark.parametrize("scope", ["category", "group"])
def test_overflow_normalization_is_partition_local_not_global(scope):
    data = {
        "x": [1, 1, 10, 10],
        "g": ["u", "v", "u", "v"],
        "w": [1e308, 1e308, 5e-324, 5e-324],
    }
    if scope == "group":
        data["g"] = ["u", "u", "v", "v"]
    result = _summary(
        mp.plot(data).countplot(
            "x", group="g", weights="w", stat="probability", normalize_scope=scope
        )
    )
    assert [e.value for e in result.estimates] == (
        [0.5] * 4 if scope == "category" else [1, 1]
    )


@pytest.mark.parametrize("scope", ["all", "category"])
@pytest.mark.parametrize("mode", ["probability", "proportion", "percent"])
@pytest.mark.parametrize("large_count", [1, 2])
@pytest.mark.parametrize("small", [[5e-16], [1e-16] * 10])
def test_representable_tiny_normalized_mass_is_never_scaled_to_zero(
    scope, mode, large_count, small
):
    weights = [1e308] * large_count + small
    data = {
        "x": [1] * len(weights),
        "g": ["big"] * large_count + ["small"] * len(small),
        "w": weights,
    }
    result = _summary(
        mp.plot(data).countplot(
            "x", group="g", weights="w", stat=mode, normalize_scope=scope
        )
    )
    expected = float(
        sum(map(Fraction, small), Fraction())
        / sum(map(Fraction, weights), Fraction())
        * (100 if mode == "percent" else 1)
    )
    value = next(e.value for e in result.estimates if e.group == "small")
    assert expected > 0 and value > 0
    assert value == expected


@pytest.mark.parametrize("scope", [True, [], "", "figure", "hue", "unknown"])
def test_unknown_or_unapproved_scope_names_are_not_silent_aliases(scope):
    plot = mp.plot(_data()).countplot(
        "x", group="g", weights="w", stat="percent", normalize_scope=scope
    )
    assert any("unknown count normalization scope" in i for i in mp.validate(plot.spec))


def test_scope_requires_meaningful_count_normalization_and_group():
    plot = mp.plot(_data()).countplot(
        "x", weights="w", stat="percent", normalize_scope="group"
    )
    assert any("requires group" in i for i in mp.validate(plot.spec))
    plot = mp.plot(_data()).countplot("x", group="g", normalize_scope="category")
    assert any("requires normalized counts" in i for i in mp.validate(plot.spec))
    plot = mp.plot(_data()).barplot("x", "w", errorbar=None)
    panel = plot.spec.panels[0]
    layer = panel.layers[0]
    assert layer.stat is not None
    bad = replace(layer, stat=replace(layer.stat, normalize_scope="all"))
    assert any(
        "only supported for countplot" in i
        for i in mp.validate(replace(plot.spec, panels=[replace(panel, layers=[bad])]))
    )


@pytest.mark.parametrize("scope", ["all", "category", "group"])
def test_scopes_roundtrip_actions_and_read_legacy_without_scope(scope):
    plot = mp.plot(_data()).countplot(
        "x", group="g", weights="w", stat="percent", normalize_scope=scope
    )
    assert mp.apply(plot.action_log) == plot.spec
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
    original = mp.plot(_data()).countplot("x", group="g", weights="w")
    legacy = json.loads(original.to_json())
    assert "normalize_scope" not in legacy["panels"][0]["layers"][0]["stat"]
    restored = mp.Plot.from_json(json.dumps(legacy))
    assert restored.spec == original.spec and mp.validate(restored.spec) == []
    config = restored.spec.panels[0].layers[0].stat
    assert config is not None and config.normalize_scope is None


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("scope", ["all", "category", "group"])
def test_log_stacks_preserve_raw_cumulative_tops_and_segment_labels(
    orient, native, scope
):
    plot = mp.plot(_data()).countplot(
        "x",
        group="g",
        weights="w",
        stat="percent",
        normalize_scope=scope,
        stack=True,
        baseline=0.1,
        native_scale=native,
        orient=orient,
        value_labels=True,
        label_format=".1f",
    )
    (plot.yscale if orient == "v" else plot.xscale)("log")
    if native:
        (plot.xscale if orient == "v" else plot.yscale)("log")
    original = plot.to_json()
    expected = _summary(plot).estimates
    figure = plot.render()
    try:
        ax = figure.axes[0]
        bars = [
            patch
            for container in ax.containers
            if isinstance(container, BarContainer)
            for patch in container
        ]
        totals = {}
        for patch, estimate in zip(bars, expected, strict=True):
            previous = totals.get(estimate.category, 0)
            top = previous + estimate.value
            bottom = patch.get_y() if orient == "v" else patch.get_x()
            height = patch.get_height() if orient == "v" else patch.get_width()
            assert bottom == pytest.approx(previous if previous else 0.1)
            assert bottom + height == pytest.approx(top)
            totals[estimate.category] = top
        assert [t.get_text() for t in ax.texts] == [f"{e.value:.1f}" for e in expected]
        for text, patch in zip(ax.texts, bars, strict=True):
            position = text.get_position()[1 if orient == "v" else 0]
            bottom = patch.get_y() if orient == "v" else patch.get_x()
            height = patch.get_height() if orient == "v" else patch.get_width()
            assert bottom < position < bottom + height
        assert plot.to_json() == original
    finally:
        plt.close(figure)


@pytest.mark.parametrize("baseline", [2, 3])
def test_baseline_must_be_below_each_first_positive_mass_and_preserves_output(
    tmp_path, baseline
):
    plot = (
        mp.plot(_data())
        .countplot("x", group="g", weights="w", stack=True, baseline=baseline)
        .yscale("log")
    )
    assert mp.validate(plot.spec) == []
    target = tmp_path / "previous.svg"
    target.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises(
        ValueError, match="baseline must be below each first positive mass"
    ):
        plot.save(target)
    assert target.read_bytes() == b"previous" and plt.get_fignums() == before


@pytest.mark.parametrize("scale", ["linear", "log"])
def test_cumulative_weight_overflow_is_explicit(scale):
    plot = (
        mp.plot({"x": [1, 1], "g": ["u", "v"], "w": [1e308, 1e308]})
        .countplot(
            "x",
            group="g",
            weights="w",
            stack=True,
            baseline=1 if scale == "log" else None,
        )
        .yscale(scale)
    )
    with pytest.raises(ValueError, match="endpoint exceeds finite plotting range"):
        plot.render()


def test_positive_log_segments_that_collapse_are_not_replaced_by_fake_geometry():
    plot = (
        mp.plot({"x": [1, 1], "g": ["u", "v"], "w": [1e16, 1]})
        .countplot("x", group="g", weights="w", stack=True, baseline=0.1)
        .yscale("log")
    )
    with pytest.raises(ValueError, match="coordinates collapse"):
        plot.render()


@pytest.mark.parametrize("scope", ["all", "category", "group"])
def test_scopes_remain_panel_local_in_facets_with_empty_reserved_cells(scope):
    data = {
        "x": [1, 1, 10, 10] * 2,
        "g": ["u", "v", "u", "v"] * 2,
        "w": [2, 3, 4, 1, 8, 2, 1, 9],
        "f": ["L"] * 4 + ["R"] * 4,
    }
    plot = mp.plot(data).countplot(
        "x", group="g", weights="w", stat="percent", normalize_scope=scope
    )
    plot.facet(col="f", col_order=["empty", "L", "R"]).size(10, 3)
    figure = plot.render()
    try:
        assert not figure.axes[0].containers
        for ax, facet in zip(figure.axes[1:], ["L", "R"], strict=True):
            bars = [p for c in ax.containers if isinstance(c, BarContainer) for p in c]
            expected = []
            for group in ["u", "v"]:
                for category in [1, 10]:
                    cell = [
                        i
                        for i in range(8)
                        if data["f"][i] == facet
                        and data["g"][i] == group
                        and data["x"][i] == category
                    ]
                    pool = [
                        i
                        for i in range(8)
                        if data["f"][i] == facet
                        and (scope != "group" or data["g"][i] == group)
                        and (scope != "category" or data["x"][i] == category)
                    ]
                    expected.append(
                        math.fsum(data["w"][i] for i in cell)
                        / math.fsum(data["w"][i] for i in pool)
                        * 100
                    )
            assert [p.get_height() for p in bars] == pytest.approx(expected)
        assert plot.spec.data.columns == data
    finally:
        plt.close(figure)


def test_named_scope_is_available_in_dependency_free_core(tmp_path):
    code = (
        "import sys,mudplot as m; "
        "p=m.plot({'x':[1],'g':['u'],'w':[2]}).countplot("
        "'x',group='g',weights='w',stat='percent',normalize_scope='group'); "
        "assert m.validate(p.spec)==[]; assert m.apply(p.action_log)==p.spec; "
        "assert 'numpy' not in sys.modules"
    )
    subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        check=True,
    )


def test_log_stacks_skip_empty_hue_slots_and_keep_raw_tops_without_baseline_offset():
    plot = (
        mp.plot({"x": [1, 1], "g": ["u", "v"], "w": [2, 3]})
        .countplot(
            "x",
            group="g",
            hue_order=["empty", "u", "v"],
            weights="w",
            stack=True,
            baseline=1,
        )
        .yscale("log")
    )
    figure = plot.render()
    try:
        bars = [
            p
            for c in figure.axes[0].containers
            if isinstance(c, BarContainer)
            for p in c
        ]
        assert [(p.get_y(), p.get_height()) for p in bars] == [(1, 1), (2, 3)]
        assert bars[-1].get_y() + bars[-1].get_height() == 5
    finally:
        plt.close(figure)
