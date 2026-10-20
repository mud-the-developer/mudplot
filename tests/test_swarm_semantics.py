"""Size-only semantic swarm: one selected cohort, numeric scale and honest guides."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._categorical import distribution_rows
from mudplot._swarm import SwarmCollection

from test_swarm_sizes import _pixel_clearance


def _swarm(ax) -> SwarmCollection:
    return next(c for c in ax.collections if isinstance(c, SwarmCollection))


def test_size_cohort_source_areas_guides_and_joint_hue_packing_agree():
    data = {
        "cat": ["A", "A", "A", "B", "B", "C"],
        "value": [1] * 6,
        "mass": [0, 5, 10, None, 2, "unselected"],
        "g": ["u", "v", "u", "u", "v", "u"],
    }
    p = (
        mp.plot(data)
        .swarmplot(
            "cat",
            "value",
            group="g",
            dodge=0,
            order=["A", "B", "empty"],
            hue_order=["v", "u", "absent"],
            semantics={"size": "mass"},
        )
        .size(7, 4)
    )
    before = copy.deepcopy(p.spec)
    assert mp.validate(p.spec) == []
    assert distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [
        0,
        1,
        2,
        4,
    ]
    assert mp.from_json(p.to_json()) == p.spec and mp.apply(p.action_log) == p.spec
    fig = p.render()
    try:
        ax = fig.axes[0]
        c = _swarm(ax)
        _pixel_clearance(ax)
        np.testing.assert_allclose(c.get_sizes(), [9, 36, 81, 4.2**2])
        np.testing.assert_array_equal(np.asarray(c.get_offsets())[:, 1], [1] * 4)
        guides = [
            line
            for line in ax.lines
            if isinstance(label := line.get_label(), str)
            and label.startswith("size: mass=")
        ]
        assert [line.get_label() for line in guides] == [
            "size: mass=0.0",
            "size: mass=5.0",
            "size: mass=10.0",
        ]
        np.testing.assert_allclose(
            [line.get_markersize() for line in guides], [3, 6, 9]
        )
        assert len(ax.collections) == 1 and all(
            np.asarray(line.get_xdata()).size == 0 for line in ax.lines
        )
        labels = ax.get_legend_handles_labels()[1]
        assert "absent" not in labels and "u" in labels and "v" in labels
        assert p.spec == before
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "values,norm,areas",
    [
        ([5, 5], None, [36, 36]),
        ([-1, 5, 11], [0, 10], [9, 36, 81]),
        (
            [
                1e300,
                np.nextafter(1e300, float("inf")),
                np.nextafter(np.nextafter(1e300, float("inf")), float("inf")),
            ],
            None,
            [9, 36, 81],
        ),
        ([-1e308, 0, 1e308], None, [9, 36, 81]),
    ],
)
def test_numeric_mapping_uses_stable_layer_domain_not_per_category(values, norm, areas):
    p = mp.plot(
        {
            "cat": [str(i) for i in range(len(values))],
            "value": [1] * len(values),
            "mass": values,
        }
    ).swarmplot("cat", "value", semantics={"size": "mass", "size_norm": norm})
    fig = p.render()
    try:
        np.testing.assert_allclose(_swarm(fig.axes[0]).get_sizes(), areas)
        if values == [5, 5]:
            guides = [
                line
                for line in fig.axes[0].lines
                if isinstance(label := line.get_label(), str)
                and label.startswith("size:")
            ]
            assert len(guides) == 1 and guides[0].get_markersize() == 6
    finally:
        plt.close(fig)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("dpi", [72, 200])
def test_public_sizes_pack_at_actual_dpi_orientation_log_values_and_redraw(orient, dpi):
    p = (
        mp.plot({"cat": ["A"] * 4, "value": [1, 1, 1.01, 1.01], "mass": [0, 10, 5, 8]})
        .swarmplot(
            "cat", "value", orient=orient, semantics={"size": "mass"}, line_width=1.5
        )
        .size(6, 4)
    )
    p.dispatch(mp.actions.SetDpi(dpi))
    if orient == "v":
        p.yscale("log")
    else:
        p.xscale("log")
    fig = p.render()
    try:
        for size in ((6, 4), (7, 5)):
            fig.set_size_inches(*size)
            fig.canvas.draw()
            _pixel_clearance(fig.axes[0])
        c = _swarm(fig.axes[0])
        np.testing.assert_array_equal(
            np.asarray(c.get_offsets())[:, 0 if orient == "h" else 1],
            [1, 1, 1.01, 1.01],
        )
    finally:
        plt.close(fig)


def test_unselected_invalid_size_does_not_relax_strict_json_numbers():
    p = mp.plot(
        {"cat": ["A", "B"], "value": [1, 1], "mass": [0, float("inf")]}
    ).swarmplot("cat", "value", order=["A"], semantics={"size": "mass"})
    assert mp.validate(p.spec) == []
    fig = p.render()
    try:
        np.testing.assert_array_equal(_swarm(fig.axes[0]).get_sizes(), [36])
    finally:
        plt.close(fig)
    with pytest.raises(ValueError, match="finite"):
        p.to_json()


def test_legend_false_keeps_size_mapping_but_omits_size_only_proxies():
    p = mp.plot({"cat": ["A", "A"], "value": [1, 1], "mass": [0, 10]}).swarmplot(
        "cat", "value", semantics={"size": "mass", "legend": False}
    )
    fig = p.render()
    try:
        np.testing.assert_array_equal(_swarm(fig.axes[0]).get_sizes(), [9, 81])
        assert not any(
            isinstance(label := line.get_label(), str) and label.startswith("size:")
            for line in fig.axes[0].lines
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "value", [True, float("inf"), float("-inf"), "large", None, float("nan")]
)
def test_invalid_or_all_missing_selected_sizes_fail_before_artists(value):
    p = mp.plot({"cat": ["A"], "value": [1], "mass": [value]}).swarmplot(
        "cat", "value", semantics={"size": "mass"}
    )
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "option",
    [
        {"hue": "g"},
        {"style": "g"},
        {"scale_id": ""},
        {"size_kind": "categorical", "size_norm": [0, 1]},
        {"dashes": ["--"]},
        {"hue_kind": "numeric"},
    ],
)
def test_size_only_contract_does_not_ignore_other_semantic_options(option):
    p = mp.plot({"cat": ["A"], "value": [1], "mass": [2], "g": ["u"]}).swarmplot(
        "cat", "value", semantics={"size": "mass", **option}
    )
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("mass", [0, 1])
def test_scalar_override_and_nonrepresentable_areas_preserve_existing_output(
    tmp_path, mass
):
    data = {"cat": ["A"], "value": [1], "mass": [mass]}
    p = mp.plot(data).swarmplot(
        "cat", "value", semantics={"size": "mass"}, marker_size=4
    )
    with pytest.raises(ValueError):
        p.render()
    p = mp.plot(data).swarmplot(
        "cat",
        "value",
        semantics={"size": "mass", "sizes": [0, 1e-200], "size_norm": [0, 1]},
    )
    path = tmp_path / "old.png"
    path.write_bytes(b"previous")
    with pytest.raises(ValueError):
        p.save(path)
    assert path.read_bytes() == b"previous"


def test_facet_and_panel_dropna_are_explicitly_rejected_without_plot_mutation():
    p = mp.plot(
        {"cat": ["A", "A"], "value": [1, 2], "mass": [0, 10], "g": ["u", "v"]}
    ).swarmplot("cat", "value", semantics={"size": "mass"})
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
    spec = p.spec
    spec.panels[0].dropna = ["mass"]
    assert any("not supported" in issue for issue in mp.validate(spec))


def test_selected_group_links_stay_on_observations_not_numeric_guides():
    p = mp.plot(
        {
            "cat": ["A"] * 3,
            "value": [1] * 3,
            "mass": [0, None, 10],
            "g": ["u", "u", "v"],
        }
    ).swarmplot(
        "cat",
        "value",
        group="g",
        dodge=0,
        semantics={"size": "mass"},
        references={
            "u": mp.ReferenceSpec(href="https://example.test/u"),
            "v": mp.ReferenceSpec(href="https://example.test/v"),
        },
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        assert _swarm(ax).get_urls() == [
            "https://example.test/u",
            "https://example.test/v",
        ]
        guides = [
            line
            for line in ax.lines
            if isinstance(label := line.get_label(), str) and label.startswith("size:")
        ]
        assert guides and all(line.get_url() is None for line in guides)
        assert all(np.asarray(line.get_xdata()).size == 0 for line in guides)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("config", [{"size": "mass", "unknown": 1}, "bad", [1, 2]])
def test_bad_semantic_config_fails_before_builder_mutation(config):
    p = mp.plot({"cat": ["A"], "value": [1], "mass": [2]})
    before, history = p.spec, p.action_log
    with pytest.raises((ValueError, TypeError)):
        p.swarmplot("cat", "value", semantics=config)
    assert p.spec == before and p.action_log == history


def test_usable_size_rows_define_the_swarm_budget_without_changing_source():
    source = {"cat": ["A"] * 2001, "value": [1] * 2001, "mass": [1] * 2000 + [None]}
    p = mp.plot(source).swarmplot("cat", "value", semantics={"size": "mass"})
    assert (
        mp.validate(p.spec) == []
        and len(distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]))
        == 2000
    )
    source["mass"][-1] = 1
    p.dispatch(mp.actions.SetData(source))
    assert any("2000" in issue for issue in mp.validate(p.spec))
