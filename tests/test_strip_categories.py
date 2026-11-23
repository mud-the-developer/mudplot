"""Consumer-visible category strips, slot geometry and legacy preservation."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("orient", ["v", "h"])
def test_reserved_nested_slots_keep_measurements_and_explicit_order(orient):
    data = {
        "c": ["a", "b", "a", "b", "a"],
        "v": [1, 2, 3, 4, None],
        "g": ["u", "u", "w", "w", "u"],
    }
    p = mp.plot(data).stripplot(
        "c",
        "v",
        group="g",
        orient=orient,
        order=["b", "empty", "a"],
        hue_order=["u", "reserved", "w"],
        dodge=0.9,
        strip={"jitter_policy": "none", "seed": 41},
    )
    ax = p.render().axes[0]
    dim = int(orient == "h")
    first, last = [np.asarray(c.get_offsets()) for c in ax.collections]
    np.testing.assert_allclose(first[:, dim], [1.7, -0.3])
    np.testing.assert_allclose(last[:, dim], [2.3, 0.3])
    np.testing.assert_array_equal(first[:, 1 - dim], [1, 2])
    np.testing.assert_array_equal(last[:, 1 - dim], [3, 4])
    ticks = ax.get_yticklabels() if orient == "h" else ax.get_xticklabels()
    assert [t.get_text() for t in ticks] == ["b", "empty", "a"]
    assert ax.get_legend_handles_labels()[1] == ["u", "w"]
    assert p.spec.data.columns == data
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


@pytest.mark.parametrize("scale", ["linear", "log"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_native_jitter_uses_minimum_axis_spacing_and_all_reserved_slots(scale, orient):
    data = {"c": [10, 10, 40, 40], "v": [1, 2, 3, 4], "g": ["u"] * 4}
    p = mp.plot(data).stripplot(
        "c",
        "v",
        group="g",
        native_scale=True,
        order=[40, 100, 10],
        hue_order=["u", "empty"],
        dodge=0.8,
        orient=orient,
        jitter=0.2,
        strip=mp.StripSpec(seed=81),
    )
    (p.yscale if orient == "h" else p.xscale)(scale)
    ax = p.render().axes[0]
    dim = int(orient == "h")
    offsets = np.asarray(ax.collections[0].get_offsets())
    centers = np.asarray(data["c"], dtype=float)
    if scale == "log":
        centers = np.log10(centers)
        spacing = np.log10(100) - np.log10(40)
        actual = np.log10(offsets[:, dim])
    else:
        spacing, actual = 30, offsets[:, dim]
    expected = centers - 0.8 * spacing / 4
    half_slot = 0.2 * 0.8 * spacing / 2
    expected += np.random.default_rng(81).uniform(-half_slot, half_slot, 4)
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-14)
    np.testing.assert_array_equal(offsets[:, 1 - dim], data["v"])


def test_legacy_default_numeric_coordinates_match_independent_raw_jitter():
    data = {"c": [10, 10, 40], "v": [1, 2, 3]}
    p = mp.plot(data).stripplot("c", "v")
    actual = np.asarray(p.render().axes[0].collections[0].get_offsets())
    np.testing.assert_array_equal(
        actual[:, 0],
        np.asarray(data["c"]) + np.random.default_rng(0).uniform(-0.15, 0.15, 3),
    )
    np.testing.assert_array_equal(actual[:, 1], data["v"])


def test_jitter_is_local_reproducible_and_keeps_observation_order():
    p = mp.plot({"c": ["a"] * 20, "v": list(range(20))}).stripplot(
        "c", "v", strip={"seed": 73}, jitter=0.5
    )
    state = np.random.get_state()
    first = np.asarray(p.render().axes[0].collections[0].get_offsets())
    second = np.asarray(p.render().axes[0].collections[0].get_offsets())
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(first[:, 1], range(20))
    assert np.all(np.abs(first[:, 0]) <= 0.5)
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


@pytest.mark.parametrize(
    "config",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**32},
        {"seed": 0.2},
        {"jitter_policy": "normal"},
    ],
)
def test_invalid_named_policy_rejects(config):
    with pytest.raises((ValueError, TypeError)):
        mp.plot({"c": ["a"], "v": [1]}).stripplot("c", "v", strip=config).render()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dodge": -1},
        {"dodge": 1.1},
        {"jitter": True},
        {"orient": "bad"},
        {"native_scale": True},
    ],
)
def test_invalid_category_options_reject(kwargs):
    with pytest.raises(ValueError):
        mp.plot({"c": ["a"], "v": [1]}).stripplot("c", "v", strip={}, **kwargs).render()


def test_strip_policy_is_not_silently_accepted_on_other_marks():
    p = mp.plot({"c": [1], "v": [2]}).line("c", "v")
    spec = p.spec
    spec.panels[0].layers[0].strip = mp.StripSpec()
    assert any("strip is not supported" in issue for issue in mp.validate(spec))


def test_temporal_category_spacing_raw_timestamps_and_horizontal_orientation():
    dates = ["2024-01-01T00:00:00Z", "2024-01-11T00:00:00Z"]
    p = (
        mp.plot({"c": dates, "v": [4, 8]})
        .stripplot("c", "v", orient="h", strip={"jitter_policy": "none"})
        .date_axis("y")
    )
    assert mp.validate(p.spec) == []
    offsets = np.asarray(p.render().axes[0].collections[0].get_offsets())
    np.testing.assert_array_equal(offsets[:, 0], [4, 8])
    np.testing.assert_allclose(np.diff(offsets[:, 1]), [10])
    assert p.spec.data.columns["c"] == dates
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_facets_reserve_category_hue_domains_and_empty_frames():
    p = mp.plot({"c": ["a", "b"], "v": [1, 2], "g": ["u", "w"], "f": ["x", "y"]})
    p.stripplot("c", "v", group="g", strip={"jitter_policy": "none"}, dodge=0.8).facet(
        col="f", col_order=["x", "y", "z"]
    )
    fig = p.render()
    assert [len(ax.collections) for ax in fig.axes] == [1, 1, 0]
    for ax in fig.axes:
        assert [tick.get_text() for tick in ax.get_xticklabels()] == ["a", "b"]
        np.testing.assert_array_equal(ax.get_xticks(), [0, 1])
    np.testing.assert_allclose(fig.axes[0].collections[0].get_offsets(), [[-0.2, 1]])
    np.testing.assert_allclose(fig.axes[1].collections[0].get_offsets(), [[1.2, 2]])
    assert fig.axes[0].get_legend_handles_labels()[1] == ["u"]
    assert fig.axes[1].get_legend_handles_labels()[1] == ["w"]
    assert p.spec.data.columns["v"] == [1, 2]


def test_native_log_value_y2_and_missing_selection():
    p = mp.plot({"c": [10, 40, None], "v": [1, 10, -1]}).stripplot(
        "c", "v", native_scale=True, strip={"jitter_policy": "none"}, axis="y2"
    )
    p.secondary_yaxis(scale="log")
    assert mp.validate(p.spec) == []
    fig = p.render()
    assert len(fig.axes[0].collections) == 0
    np.testing.assert_array_equal(
        fig.axes[1].collections[0].get_offsets(), [[10, 1], [40, 10]]
    )


def test_legacy_positional_model_alpha_still_controls_visible_scatter():
    from mudplot.spec import LayerSpec

    layer = LayerSpec(
        "scatter",
        "x",
        "y",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "default",
        None,
        None,
        None,
        0.25,
    )
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).dispatch(mp.actions.AddLayer(layer))
    collection = p.render().axes[0].collections[0]
    assert collection.get_alpha() == 0.25
    np.testing.assert_array_equal(collection.get_offsets(), [[1, 3], [2, 4]])
