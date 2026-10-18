"""DATA-04/09: raw grouping uses Python equality, not NumPy string coercion."""

import copy

import matplotlib

matplotlib.use("Agg")
import mudplot as mp
import numpy as np
import pytest
from mudplot._render import _series_masks
from mudplot.spec import LayerSpec


@pytest.mark.parametrize(
    "groups,expected",
    [
        (["1", 1], [[0], [1]]),
        (["1", 1, None], [[0], [1], [2]]),
        (["A", 1, 1.0, True], [[0], [1, 2, 3]]),
        (["", None, "1", 1, True], [[0], [1], [2], [3, 4]]),
    ],
)
def test_default_raw_group_identity_does_not_depend_on_array_string_inference(
    groups, expected
):
    columns = {
        "x": list(range(len(groups))),
        "y": list(range(len(groups))),
        "g": groups,
    }
    before = copy.deepcopy(columns)
    layer = LayerSpec(type="scatter", x="x", y="y", group="g")
    actual = [
        np.flatnonzero(mask).tolist() for _label, mask in _series_masks(columns, layer)
    ]
    assert actual == expected
    assert columns == before
    assert (
        mp.from_json(
            mp.plot(columns).scatter("x", "y", group="g").to_json()
        ).data.columns
        == before
    )


@pytest.mark.parametrize("kind", ["line", "scatter"])
def test_raw_mixed_string_and_number_groups_keep_their_original_observations(kind):
    data = {"x": [2, 1, 2, 0], "y": [20, 10, 30, 0], "g": ["1", "1", 1, 1]}
    plot = getattr(mp.plot(data), kind)("x", "y", group="g")
    axes = plot.render().axes[0]
    if kind == "line":
        assert len(axes.lines) == 2
        np.testing.assert_array_equal(axes.lines[0].get_xdata(), [2, 1])
        np.testing.assert_array_equal(axes.lines[1].get_xdata(), [2, 0])
    else:
        assert len(axes.collections) == 2
        np.testing.assert_array_equal(
            axes.collections[0].get_offsets(), [[2, 20], [1, 10]]
        )
        np.testing.assert_array_equal(
            axes.collections[1].get_offsets(), [[2, 30], [0, 0]]
        )
    # Display labels use str(key), so callers should normalize ambiguous labels.
    assert axes.get_legend_handles_labels()[1] == ["1", "1"]
    assert plot.spec.data.columns == data
