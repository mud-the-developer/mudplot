"""Images complement independent semantic assertions; neither replaces the other."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from PIL import Image


def draw(tmp_path, name, groups, color="#246a91"):
    plot = (
        mp.plot({"x": [1.0, 2.0], "y": [1.0, 2.0], "g": groups})
        .size(4, 3)
        .scatter("x", "y", group="g", color=color, marker="o", marker_size=14)
        .xlim(0, 3)
        .ylim(0, 3)
        .legend(show=False)
        .encoding(redundant_encoding=False)
    )
    plot.dispatch(mp.actions.SetDpi(120))
    target = tmp_path / f"{name}.png"
    figure = plot.save(target)
    try:
        ax = figure.axes[0]
        offsets = [
            np.asarray(item.get_offsets(), dtype=float).tolist()
            for item in ax.collections
        ]
        assert ax.get_xlim() == (0.0, 3.0) and ax.get_ylim() == (0.0, 3.0)
        assert tuple(figure.get_size_inches()) == (4.0, 3.0)
        with Image.open(target) as image:
            pixels = np.array(image.convert("RGB"))
        assert pixels.shape == (360, 480, 3)
        return pixels, offsets
    finally:
        plt.close(figure)


def test_same_environment_repetition_and_numeric_oracle_are_exact(tmp_path):
    before = plt.get_fignums()
    a, offsets = draw(tmp_path, "baseline", [1, "1"])
    b, repeated = draw(tmp_path, "repeat", [1, "1"])
    assert offsets == repeated == [[[1.0, 1.0]], [[2.0, 2.0]]]
    np.testing.assert_array_equal(a, b)
    assert plt.get_fignums() == before


def test_pixel_identical_control_can_still_have_wrong_group_semantics(tmp_path):
    good, groups = draw(tmp_path, "good", [1, "1"])
    bad, collapsed = draw(tmp_path, "collapsed", [1, 1])
    np.testing.assert_array_equal(good, bad)
    assert groups == [[[1.0, 1.0]], [[2.0, 2.0]]]
    assert collapsed == [[[1.0, 1.0], [2.0, 2.0]]] and collapsed != groups


def test_appearance_control_changes_image_without_changing_numeric_meaning(tmp_path):
    a, groups = draw(tmp_path, "baseline", [1, "1"])
    b, changed = draw(tmp_path, "red", [1, "1"], "#b84242")
    assert groups == changed == [[[1.0, 1.0]], [[2.0, 2.0]]]
    assert np.any(a != b)
