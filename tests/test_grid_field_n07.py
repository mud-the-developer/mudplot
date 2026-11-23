"""Focused native artist, saved input and force-independent resource checks."""

from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


def test_native_masked_mesh_geometry_and_raw_scalar_colourbar():
    raw = [[1, 999, 3], [4, 5, None]]
    grid = mp.GridFieldSpec(
        x=[0, 1, 4, 8],
        y=[-2, 1, 5],
        position="edges",
        shading="flat",
        mask=[[False, True, False], [False, False, False]],
    )
    pictures = (
        mp.plot().matrix("values", raw).pcolor("values", grid=grid),
        mp.plot()
        .matrix("values", raw)
        .pcolormesh(
            "values",
            grid=grid,
            colorbar=True,
            clabel="Signal (mV)",
        ),
    )
    for p, count in zip(pictures, (4, 6), strict=True):
        saved = p.to_json()
        reopened = mp.Plot.from_json(saved)
        fig = reopened.render()
        try:
            (artist,) = fig.axes[0].collections
            assert len(artist.get_paths()) == count
            if count == 6:
                fig.canvas.draw()
                np.testing.assert_array_equal(
                    artist.get_facecolors()[:, 3], [1, 0, 1, 1, 1, 0]
                )
                coords = artist.get_coordinates()
                np.testing.assert_array_equal(coords[0, :, 0], [0, 1, 4, 8])
                assert (
                    artist.get_clim() == (1, 5)
                    and fig.axes[1].get_ylabel() == "Signal (mV)"
                )
            assert reopened.to_json() == saved and not reopened.spec.data.columns
            assert reopened.spec.data.matrices["values"] == raw
        finally:
            plt.close(fig)


def test_direct_pixels_preserve_opacity_without_scalar_colourbar():
    p = mp.plot().imshow(
        grid=mp.GridFieldSpec(
            pixels=[[[1, 0, 0, 0.5], [0, 1, 0, 1]]],
            mask=[[False, True]],
            extent=[1, 4, 2, 5],
        ),
        alpha=0.5,
    )
    fig = p.render()
    try:
        assert len(fig.axes) == 1
        (image,) = fig.axes[0].images
        np.testing.assert_array_equal(image.get_array()[0, :, 3], [0.25, 0])
        np.testing.assert_array_equal(image.get_extent(), [1, 4, 2, 5])
        assert p.spec.panels[0].layers[0].grid.pixels[0][0][3] == 0.5
    finally:
        plt.close(fig)


def test_native_contour_labels_and_filled_boundaries():
    p = (
        mp.plot()
        .matrix("value", [[0, 2, 6]] * 3)
        .contour(
            "value",
            levels=[1, 4],
            colorbar=False,
            grid=mp.GridFieldSpec(
                x=[0, 2, 7],
                y=[0, 4, 9],
                position="centers",
                label_levels=[4],
                label_format=".1f",
                label_inline=False,
            ),
        )
    )
    fig = p.render()
    try:
        (cs,) = fig.axes[0].collections
        assert [label.get_text() for label in fig.axes[0].texts] == ["4.0"]
        for x, path in zip((1, 4.5), cs.get_paths(), strict=True):
            np.testing.assert_allclose(path.vertices[:, 0], x)
    finally:
        plt.close(fig)


def test_constant_native_colourbar_and_empty_declared_contours():
    p = (
        mp.plot()
        .matrix("z", [[7]])
        .pcolormesh(
            "z",
            grid=mp.GridFieldSpec(x=[0, 1], y=[0, 1], position="edges", shading="flat"),
            colorbar=True,
            clabel="Constant signal (mV)",
        )
    )
    fig = p.render()
    try:
        (mesh,) = fig.axes[0].collections
        assert mesh.get_clim() == (6.65, 7.35)
        np.testing.assert_array_equal(mesh.get_array().ravel(), [7])
        assert fig.axes[1].get_ylabel() == "Constant signal (mV)"
        assert p.spec.data.matrices["z"] == [[7]]
    finally:
        plt.close(fig)

    q = (
        mp.plot()
        .matrix("z", [[7, 7], [7, 7]])
        .contour(
            "z",
            grid=mp.GridFieldSpec(
                x=[0, 1], y=[0, 1], position="centers", label_levels=[8]
            ),
            levels=[8, 9],
            colorbar=False,
        )
    )
    fig = q.render()
    try:
        (contours,) = fig.axes[0].collections
        np.testing.assert_array_equal(contours.levels, [8, 9])
        assert not any(len(path.vertices) for path in contours.get_paths())
        assert not fig.axes[0].texts
    finally:
        plt.close(fig)


def test_grid_opt_in_caps_and_failed_save_preserve_output(tmp_path: Path):
    out = tmp_path / "prior.svg"
    out.write_text("prior")
    wide = mp.plot().matrix("z", [[0] * 10001]).imshow("z", grid=mp.GridFieldSpec())
    with pytest.raises(ValueError, match="10000 cells"):
        wide.save(str(out))
    assert out.read_text() == "prior"
    p = mp.plot().matrix("z", [[0, 1]] * 100)
    grid = mp.GridFieldSpec(
        x=[0, 1],
        y=list(range(100)),
        position="centers",
        label_levels=list(range(1, 22)),
    )
    p.contour("z", grid=grid, levels=list(range(1, 22)))
    assert any("4096 prospective labels" in issue for issue in mp.validate(p.spec))
    # A layer fits; repeatedly retaining it exceeds the aggregate reservation.
    q = mp.plot().matrix("z", [[0, 1] * 50] * 100)
    typed = mp.GridFieldSpec(x=list(range(100)), y=list(range(100)), position="centers")
    levels = [i / 10 for i in range(1, 7)]
    q.contour("z", grid=typed, levels=levels, colorbar=False)
    assert not mp.validate(q.spec)
    for _ in range(4):
        q.contour("z", grid=typed, levels=levels, colorbar=False)
    assert any(
        "reservation" in issue or "prospective path vertices" in issue
        for issue in mp.validate(q.spec)
    )
