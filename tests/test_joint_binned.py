"""Opt-in binned joint centers share exact paired rows without new defaults."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.patches import Rectangle


def data():
    return {
        "x": [0.2, 0.4, None, 0.8, 0.9],
        "y": [0.3, None, 0.6, 0.8, 0.7],
        "unused": [None] * 5,
    }


def plot(kind, **style):
    p = mp.plot(data())
    if kind == "hist2d":
        p.hist2d("x", "y", bins=[0, 0.5, 1], colorbar=False, **style)
    else:
        p.hexbin("x", "y", gridsize=5, mincnt=1, colorbar=False, **style)
    return p


@pytest.mark.parametrize("kind", ["hist2d", "hexbin"])
@pytest.mark.parametrize("marginal", ["hist", "kde"])
def test_binned_joint_preserves_pairs_and_independent_density_axes(kind, marginal):
    p = plot(kind)
    original = copy.deepcopy(p.spec.data)
    options = (
        {"marginal_kind": "kde", "kde": {"gridsize": 32, "cut": 0}}
        if marginal == "kde"
        else {"bins": 2, "marginal_stat": "count"}
    )
    p.joint(**options).size(6, 5)
    assert p.spec.data == original
    assert [panel.dropna for panel in p.spec.panels] == [["x", "y"]] * 3
    assert p.spec.panels[0].layers[0].type == kind
    assert mp.from_json(p.to_json()) == p.spec
    figure = p.render()
    try:
        main, right, bottom = figure.axes
        assert main.get_shared_y_axes().joined(main, right)
        assert main.get_shared_x_axes().joined(main, bottom)
        assert not main.get_shared_y_axes().joined(main, bottom)
        values = np.asarray(main.collections[0].get_array())
        assert values.sum() == 3
        if kind == "hist2d":
            np.testing.assert_array_equal(values.reshape(2, 2), [[1, 0], [0, 2]])
        if marginal == "hist":
            widths, heights = [], []
            for bar in right.patches:
                assert isinstance(bar, Rectangle)
                widths.append(bar.get_width())
            for bar in bottom.patches:
                assert isinstance(bar, Rectangle)
                heights.append(bar.get_height())
            np.testing.assert_array_equal(widths, [1, 2])
            np.testing.assert_array_equal(heights, [1, 2])
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["hist2d", "hexbin"])
def test_binned_joint_recomputes_pairs_after_setdata(kind):
    p = plot(kind).joint(bins=2, marginal_stat="count")
    updated = {"x": [0.2, 0.8, None], "y": [0.2, 0.8, 0.5]}
    p.dispatch(mp.actions.SetData(updated))
    figure = p.render()
    try:
        assert np.asarray(figure.axes[0].collections[0].get_array()).sum() == 2
        assert p.spec.data.columns == updated
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["hist2d", "hexbin"])
@pytest.mark.parametrize(
    "style", [{"group": "g"}, {"hue_order": ["A"]}, {"weights": "w"}]
)
def test_binned_joint_rejects_unimplemented_mapping_without_state_change(kind, style):
    p = plot(kind, **style)
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError, match="ungrouped, unweighted"):
        p.joint()
    assert p.to_json() == before and p.action_log == history


@pytest.mark.parametrize("kind", ["hist2d", "hexbin"])
def test_binned_joint_does_not_silently_disable_colorbar(kind):
    p = mp.plot(data())
    getattr(p, kind)("x", "y")
    before = p.to_json()
    with pytest.raises(ValueError):
        p.joint()
    assert p.to_json() == before


@pytest.mark.parametrize("kind", ["hist2d", "hexbin"])
def test_binned_dropna_does_not_enable_general_panel_filters(kind):
    spec = plot(kind).joint().spec
    spec.panels[0].filters = {"x": 0.2}
    assert any("does not support panel filters" in issue for issue in mp.validate(spec))


def test_binned_joint_capability_is_explicit():
    assert mp.capabilities()["joint_grid"]["main"] == [
        "scatter",
        "regplot",
        "hist2d",
        "hexbin",
    ]
