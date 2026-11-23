"""Actual renderer changes and authenticated native HDR path inputs."""

from fractions import Fraction
from math import nextafter
from xml.etree import ElementTree

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._hdr_render import HDRCollection, _affine_radius
from mudplot._kernel_math import KernelPrecisionError
from mudplot.io import _atomic_destination


@pytest.mark.parametrize(
    "a,b,v,dpi",
    [
        (1024.007, -781.25, 1.2150642514499919, 72.0),
        (-0.12501, 0.015, -0.4, 301.0),
        (2.0**-1022, 0.0, 2.0**-40, 72.0),
    ],
)
def test_native_affine_radius_encloses_realized_separate_rounds(a, b, v, dpi):
    radius = _affine_radius(a, b, abs(v), dpi)
    # Independently recover pre-affine coordinates of observed rounded output
    # with either end of the serializer's exact rational error allocation.
    pixel = Fraction(float(float(a * v) + b))
    for sign in (-1, 1):
        rebuilt = (pixel + sign * Fraction(dpi) / 2_000_000 - Fraction(b)) / Fraction(a)
        assert abs(rebuilt - Fraction(v)) <= radius


def test_hdr_native_redraw_changing_backends_view_and_paths(tmp_path):
    source = {"x": [24.8, 25.0, 32.0, 34.0], "y": [24.6, 30.0, 25.0, 33.0]}
    plot = (
        mp.plot(source)
        .xscale("log")
        .yscale("log")
        .kde2d(
            "x",
            "y",
            levels=[0.55],
            gridsize=12,
            hdr=mp.HDRSpec(scope="full", tolerance=0.04),
            fill=True,
            line_width=0,
            colorbar=False,
        )
    )

    before = plot.to_json()
    figure = plot.render()
    try:
        ax = figure.axes[0]
        artist = next(
            item for item in ax.collections if isinstance(item, HDRCollection)
        )
        initial = artist._mudplot_hdr["actual_logical_view"]
        budget = figure._mudplot_field_budget
        proof_vertices = budget.report()["by_kind"]["native_hdr_preimage_vertices"]
        figure.set_dpi(160)
        ax.invert_xaxis()
        figure.canvas.draw()
        assert artist._mudplot_hdr["actual_logical_view"] == initial
        for ext, magic in [("png", b"\x89PNG"), ("svg", b"<?xml"), ("pdf", b"%PDF-")]:
            path = tmp_path / f"hdr.{ext}"
            figure.savefig(path)
            assert path.read_bytes().startswith(magic)
            if ext == "svg":
                group = next(
                    node
                    for node in ElementTree.parse(path).iter()
                    if node.get("id") == artist.get_gid()
                )
                assert sum(1 for child in group if child.tag.endswith("path")) == len(
                    artist.get_paths()
                )
            assert artist._mudplot_hdr["levels"][0]["total_conditional_error"] <= 0.04
        assert (
            budget.report()["by_kind"]["native_hdr_preimage_vertices"] == proof_vertices
        )

        # A supported view can fall outside the optional first proof envelope.
        figure.set_size_inches(figure.get_figwidth() * 0.80, figure.get_figheight())
        figure.canvas.draw()
        after_resize = budget.report()["by_kind"]["native_hdr_preimage_vertices"]
        assert after_resize > proof_vertices
        assert artist._mudplot_hdr["actual_logical_view"] == initial

        path = next(path for path in artist.get_paths() if len(path.vertices) > 5)
        vertices, codes = np.asarray(path.vertices), np.asarray(path.codes)
        old_value = float(vertices[1, 0])
        vertices[1, 0] = nextafter(old_value, float("inf"))
        figure.canvas.draw()
        assert budget.report()["by_kind"]["native_hdr_preimage_vertices"] > after_resize
        saved_code = codes[1]
        codes[1] = 1  # Opens a new subpath, despite matching vertex bytes.
        with pytest.raises(KernelPrecisionError, match="path codes"):
            figure.canvas.draw()
        codes[1] = saved_code
        after_mutation = budget.report()["by_kind"]["native_hdr_preimage_vertices"]
        ax.set_xscale("log", base=2)
        figure.canvas.draw()
        assert (
            budget.report()["by_kind"]["native_hdr_preimage_vertices"] > after_mutation
        )
        assert artist._mudplot_hdr["levels"][0]["total_conditional_error"] <= 0.04

        # The real output transaction preserves its original destination
        # when the native renderer encounters an unprovable authored view.
        output = tmp_path / "hdr.png"
        old_output = output.read_bytes()
        ax.set_xlim(1e-200, 1e200)
        with (
            pytest.raises(KernelPrecisionError, match="native HDR"),
            _atomic_destination(output) as stage,
        ):
            figure.savefig(stage, format="png")
        assert output.read_bytes() == old_output
        assert plot.to_json() == before
    finally:
        plt.close(figure)
