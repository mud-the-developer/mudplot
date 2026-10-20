"""Named size domains pool original Swarm rows without pooling observations/colours."""

import copy

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._semantics import shared_scale_domains
from mudplot._swarm import SwarmCollection

from test_swarm_sizes import _pixel_clearance


def _collections(ax):
    return [c for c in ax.collections if isinstance(c, SwarmCollection)]


def _guides(ax):
    return [
        line
        for line in ax.lines
        if isinstance(label := line.get_label(), str) and label.startswith("size:")
    ]


def _numeric(*, same_panel=False, legends=(True, True)):
    data = {
        "cat": ["A"] * 3,
        "left": [1, None, 1],
        "right": [None, 2, 2],
        "mass": [0, 5, 10],
        "g": ["u", "v", "u"],
    }
    p = mp.plot(data)
    if not same_panel:
        p.layout(1, 2).size(8, 4)
    for index, value in enumerate(("left", "right")):
        p.swarmplot(
            "cat",
            value,
            group="g",
            dodge=0,
            panel=0 if same_panel else index,
            semantics={"size": "mass", "scale_id": "study", "legend": legends[index]},
            references={
                "u": mp.ReferenceSpec(href="https://example.test/u"),
                "v": mp.ReferenceSpec(href="https://example.test/v"),
            },
        )
    return p


def test_numeric_pool_uses_deduplicated_original_rows_and_local_observations():
    p = _numeric()
    before = copy.deepcopy(p.spec)
    assert mp.validate(p.spec) == []
    domain = shared_scale_domains(p.spec)["study"]
    assert domain["rows"] == [0, 1, 2] and domain["colors"] == 0
    fig = p.render()
    try:
        first, second = fig.axes
        np.testing.assert_allclose(_collections(first)[0].get_sizes(), [9, 81])
        np.testing.assert_allclose(_collections(second)[0].get_sizes(), [36, 81])
        assert _collections(first)[0].get_urls() == ["https://example.test/u"] * 2
        assert _collections(second)[0].get_urls() == [
            "https://example.test/v",
            "https://example.test/u",
        ]
        for ax in (first, second):
            _pixel_clearance(ax)
            assert (
                np.asarray(_collections(ax)[0].get_offsets(), dtype=float).shape[0] == 2
            )
            assert [g.get_label() for g in _guides(ax)] == [
                "size: mass=0.0",
                "size: mass=5.0",
                "size: mass=10.0",
            ]
            np.testing.assert_allclose(
                [g.get_markersize() for g in _guides(ax)], [3, 6, 9]
            )
            assert all(
                np.asarray(g.get_xdata()).size == 0 and g.get_url() is None
                for g in _guides(ax)
            )
        assert (
            "v" not in first.get_legend_handles_labels()[1]
            and "v" in second.get_legend_handles_labels()[1]
        )
        assert (
            p.spec == before
            and mp.from_json(p.to_json()) == p.spec
            and mp.apply(p.action_log) == p.spec
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "legends,expected", [((True, True), 3), ((False, True), 3), ((False, False), 0)]
)
def test_same_panel_reuses_size_guide_once_without_merging_collections(
    legends, expected
):
    p = _numeric(same_panel=True, legends=legends)
    fig = p.render()
    try:
        ax = fig.axes[0]
        assert len(_collections(ax)) == 2 and len(_guides(ax)) == expected
        np.testing.assert_allclose(_collections(ax)[0].get_sizes(), [9, 81])
        np.testing.assert_allclose(_collections(ax)[1].get_sizes(), [36, 81])
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "order,first_area,second_area,guide_labels,guide_diameters",
    [
        (None, [9, 81], [36, 81, 9], ["large", "small", "medium"], [3, 6, 9]),
        (
            ["small", "reserved", "medium", "large"],
            [81, 49],
            [9, 49, 81],
            ["small", "medium", "large"],
            [3, 7, 9],
        ),
    ],
)
def test_pooled_categorical_order_is_source_order_not_layer_registration_order(
    order, first_area, second_area, guide_labels, guide_diameters
):
    data = {
        "cat": ["A"] * 4,
        "left": [1, None, 1, None],
        "right": [None, 2, 2, 2],
        "grade": ["large", "small", "medium", "large"],
    }
    p = mp.plot(data).layout(1, 2).size(8, 4)
    for panel, value in ((1, "right"), (0, "left")):
        p.swarmplot(
            "cat",
            value,
            panel=panel,
            semantics={
                "size": "grade",
                "size_kind": "categorical",
                "size_order": order,
                "scale_id": "study",
            },
        )
    assert shared_scale_domains(p.spec)["study"]["rows"] == [0, 1, 2, 3]
    fig = p.render()
    try:
        np.testing.assert_allclose(_collections(fig.axes[0])[0].get_sizes(), first_area)
        np.testing.assert_allclose(
            _collections(fig.axes[1])[0].get_sizes(), second_area
        )
        for ax in fig.axes:
            assert [g.get_label() for g in _guides(ax)] == [
                f"size: grade={x}" for x in guide_labels
            ]
            np.testing.assert_allclose(
                [g.get_markersize() for g in _guides(ax)], guide_diameters
            )
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "other", [{"sizes": [4, 10]}, {"size_norm": [0, 20]}, {"size_kind": "categorical"}]
)
def test_incompatible_named_settings_fail_without_overwriting_output(tmp_path, other):
    p = mp.plot({"cat": ["A"] * 3, "value": [1, 1, 1], "mass": [0, 5, 10]})
    p.swarmplot("cat", "value", semantics={"size": "mass", "scale_id": "same"})
    p.swarmplot("cat", "value", semantics={"size": "mass", "scale_id": "same", **other})
    out = tmp_path / "old.png"
    out.write_bytes(b"previous")
    with pytest.raises(ValueError, match="identical"):
        p.save(out)
    assert out.read_bytes() == b"previous"


@pytest.mark.parametrize("kind", ["scatter", "lineplot"])
def test_swarm_named_size_domain_does_not_silently_mix_other_families(kind):
    p = mp.plot(
        {"cat": ["A"] * 3, "x": [1, 2, 3], "value": [1, 2, 3], "mass": [0, 5, 10]}
    )
    p.swarmplot("cat", "value", semantics={"size": "mass", "scale_id": "same"})
    if kind == "scatter":
        p.scatter("x", "value", semantics={"size": "mass", "scale_id": "same"})
    else:
        p.lineplot("x", "value", semantics={"size": "mass", "scale_id": "same"})
    with pytest.raises(ValueError, match="mix"):
        p.render()


def test_legacy_group_colours_and_urls_stay_local_with_shared_sizes():
    p = _numeric()
    local = copy.deepcopy(p.spec)
    for panel in local.panels:
        config = panel.layers[0].semantics
        assert isinstance(config, mp.SemanticSpec)
        config.scale_id = None
    shared_fig = p.render()
    local_fig = mp.render(local)
    try:
        for shared_ax, local_ax in zip(shared_fig.axes, local_fig.axes, strict=True):
            np.testing.assert_allclose(
                colors.to_rgba_array(_collections(shared_ax)[0].get_facecolor()),
                colors.to_rgba_array(_collections(local_ax)[0].get_facecolor()),
            )
            assert (
                _collections(shared_ax)[0].get_urls()
                == _collections(local_ax)[0].get_urls()
            )
    finally:
        plt.close(shared_fig)
        plt.close(local_fig)


def test_different_named_ids_keep_independent_size_domains():
    p = _numeric()
    spec = p.spec
    config = spec.panels[1].layers[0].semantics
    assert isinstance(config, mp.SemanticSpec)
    config.scale_id = "other"
    fig = mp.render(spec)
    try:
        assert set(shared_scale_domains(spec)) == {"study", "other"}
        np.testing.assert_allclose(_collections(fig.axes[0])[0].get_sizes(), [9, 81])
        np.testing.assert_allclose(_collections(fig.axes[1])[0].get_sizes(), [9, 81])
    finally:
        plt.close(fig)


def test_shared_cohort_respects_layer_category_hue_and_missing_size_selection():
    p = mp.plot(
        {
            "cat": ["A", "A", "B", "C", "B"],
            "value": [1] * 5,
            "mass": [0, 10, 100, 1000, None],
            "g": ["u", "v", "u", "u", "u"],
        }
    )
    p.swarmplot(
        "cat",
        "value",
        order=["A"],
        group="g",
        hue_order=["u"],
        semantics={"size": "mass", "scale_id": "same"},
    )
    p.swarmplot(
        "cat",
        "value",
        order=["A", "B"],
        group="g",
        hue_order=["u"],
        semantics={"size": "mass", "scale_id": "same"},
    )
    assert shared_scale_domains(p.spec)["same"]["rows"] == [0, 2]
    fig = p.render()
    try:
        c0, c1 = _collections(fig.axes[0])
        np.testing.assert_allclose(c0.get_sizes(), [9])
        np.testing.assert_allclose(c1.get_sizes(), [9, 81])
        assert [g.get_label() for g in _guides(fig.axes[0])] == [
            "size: mass=0.0",
            "size: mass=50.0",
            "size: mass=100.0",
        ]
    finally:
        plt.close(fig)


def test_duplicate_member_rows_are_not_counted_twice_toward_pool_budget():
    data = {"cat": ["A"] * 2000, "value": [1] * 2000, "mass": list(range(2000))}
    p = mp.plot(data)
    for _ in range(6):
        p.swarmplot("cat", "value", semantics={"size": "mass", "scale_id": "same"})
    assert (
        mp.validate(p.spec) == []
        and len(shared_scale_domains(p.spec)["same"]["rows"]) == 2000
    )


def test_distinct_pool_rows_and_pooled_levels_have_independent_limits():
    p = mp.plot(
        {
            "cat": [str(i // 2000) for i in range(12000)],
            "value": [1] * 12000,
            "mass": list(range(12000)),
        }
    )
    for i in range(6):
        p.swarmplot(
            "cat",
            "value",
            order=[str(i)],
            semantics={"size": "mass", "scale_id": "same"},
        )
    assert any("10000" in issue for issue in mp.validate(p.spec))
    p = mp.plot(
        {
            "cat": ["L"] * 32 + ["R"] * 33,
            "value": [1] * 65,
            "grade": [str(i) for i in range(65)],
        }
    )
    for value in ("L", "R"):
        p.swarmplot(
            "cat",
            "value",
            order=[value],
            semantics={"size": "grade", "size_kind": "categorical", "scale_id": "same"},
        )
    assert any("pooled levels" in issue for issue in mp.validate(p.spec))


def test_pooled_positive_area_underflow_is_rejected_by_pure_validation():
    p = mp.plot(
        {
            "cat": ["A"] * 3,
            "left": [1, None, None],
            "mid": [None, 1, None],
            "right": [None, None, 1],
            "mass": [0, 1e-100, 1e-200],
        }
    )
    for value in ("left", "mid", "right"):
        p.swarmplot(
            "cat",
            value,
            semantics={"size": "mass", "sizes": [0, 1e-160], "scale_id": "same"},
        )
    assert any("representable" in issue for issue in mp.validate(p.spec))


def test_shared_size_does_not_allow_invalid_facet_or_dropna_columns():
    p = _numeric()
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="missing")
    assert p.spec == before and p.action_log == history
    spec = p.spec
    spec.panels[0].dropna = ["missing"]
    assert any("does not exist" in issue for issue in mp.validate(spec))
