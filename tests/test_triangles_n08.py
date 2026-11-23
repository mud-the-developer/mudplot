"""Native explicit triangulation geometry; no positive-effect substitutes."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.path import Path


def test_equal_counts_explicit_role_and_mask_keep_authored_order():
    source = {"x": [0, 6, 0, 1, 2], "y": [0, 0, 6, 1, 2], "s": [0, 3, 6, 9, 12]}
    faces = [[0, 1, 3], [1, 2, 4], [2, 3, 4], [3, 1, 4], [2, 0, 3]]
    mask = [False, True, False, False, False]
    p = mp.plot(source).layout(1, 2).size(7, 3)
    p.tripcolor(
        "x", "y", c="s", triangulation=mp.TriangulationSpec(faces, mask, "vertex")
    )
    p.tripcolor(
        "x",
        "y",
        triangulation=mp.TriangulationSpec(faces, mask, "face", source["s"]),
        panel=1,
    )
    reopened = mp.Plot.from_json(p.to_json())
    fig = reopened.render()
    try:
        a, b = (ax.collections[0] for ax in fig.axes)
        np.testing.assert_array_equal(a.get_array(), [4, 9, 8, 5])
        np.testing.assert_array_equal(b.get_array(), [0, 6, 9, 12])
        for artist in (a, b):
            assert len(artist.get_paths()) == 4
            quad = artist.get_paths()[0]
            np.testing.assert_array_equal(
                quad.vertices, [[0, 0], [6, 0], [1, 1], [0, 0]]
            )
            assert quad.codes[-1] == Path.CLOSEPOLY
        assert reopened.to_json() == p.to_json()
        assert reopened.spec.data.columns == source
    finally:
        plt.close(fig)


def test_masked_native_edges_contour_bands_and_shared_3d_surface():
    source = {
        "x": [0, 2, 2, 0],
        "y": [0, 0, 2, 2],
        "q": [0, 2, 2, 0],
        "height": [0, 3, 6, 20],
    }
    faces = [[2, 1, 0], [0, 2, 3]]  # first is clockwise; stored form must survive
    plain = mp.TriangulationSpec(faces, [False, True])
    field = mp.TriangulationSpec(faces, [False, True], "vertex")
    p = mp.plot(source).layout(2, 2).size(8, 6)
    p.triplot("x", "y", triangulation=plain)
    p.tricontour("x", "y", "q", triangulation=field, levels=[1, 3], panel=1)
    p.tricontourf("x", "y", "q", triangulation=field, levels=[0, 1, 2], panel=2)
    p.projection3d(panel=3).trisurf("x", "y", "height", triangulation=plain, panel=3)
    fig = p.render()
    try:
        wire, marker = fig.axes[0].lines
        xy = wire.get_xydata().reshape(-1, 3, 2)
        edges = {frozenset(map(tuple, seg[:2])) for seg in xy}
        assert edges == {
            frozenset(((0, 0), (2, 0))),
            frozenset(((2, 0), (2, 2))),
            frozenset(((2, 2), (0, 0))),
        }
        assert not len(marker.get_xdata())
        (line,) = fig.axes[1].collections
        assert line.levels.tolist() == [1, 3]
        actual, empty = line.get_paths()
        assert sorted(map(tuple, actual.vertices)) == [(1, 0), (1, 1)] and not len(
            empty.vertices
        )
        np.testing.assert_array_equal(actual.codes, [Path.MOVETO, Path.LINETO])
        (fill,) = fig.axes[2].collections
        assert fill.levels.tolist() == [0, 1, 2]
        assert len(fill.get_paths()) == 2 and all(
            path.codes is not None for path in fill.get_paths()
        )
        fig.canvas.draw()
        assert fig.axes[3].name == "3d"
        (surf,) = fig.axes[3].collections
        assert len(surf.get_paths()) == 1 and surf.get_array().tolist() == [3]
        assert p.spec.panels[0].layers[0].triangulation.triangles == faces
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "x,y,faces,mask,message",
    [
        ([0, 1, 0], [0, 0, 1], [[0, True, 2]], None, "not bool"),
        ([0, 1, 0], [0, 0, 1], [[0, 1, 3]], None, "zero-based"),
        ([0, 1, 2], [0, 0, 0], [[0, 1, 2]], None, "signed area"),
        ([0, 1e-200, 0], [0, 0, 1e-200], [[0, 1, 2]], None, "signed area"),
        ([0, 1, 0], [0, 0, 1], [[0, 1, 2], [2, 1, 0]], None, "duplicate triangle"),
        ([0, 1, 0], [0, 0, 1], [[0, 1, 2]], [True], "visible face"),
        (
            [0, 4, 0, 1, 2, 1],
            [0, 0, 4, 1, 1, 2],
            [[0, 1, 2], [3, 4, 5]],
            None,
            "overlap",
        ),
        (
            [0, 4, 0, 2, 3, 1],
            [0, 0, 4, 0, -2, -2],
            [[0, 1, 2], [3, 4, 5]],
            None,
            "nonconforming",
        ),
        (
            [0, 4, 2, 0, 4, 2],
            [0, 0, 4, 3, 3, -1],
            [[0, 1, 2], [3, 4, 5]],
            None,
            "cross",
        ),
        (
            [0, 4, 0, 4, 2],
            [0, 0, 4, 3, -2],
            [[0, 1, 2], [0, 1, 3], [1, 0, 4]],
            None,
            "incidences",
        ),
    ],
)
def test_invalid_topology_and_original_row_replacement_preserve_prior_output(
    tmp_path, x, y, faces, mask, message
):
    p = mp.plot({"x": x, "y": y}).triplot(
        "x", "y", triangulation=mp.TriangulationSpec(faces, mask)
    )
    path = tmp_path / "prior.svg"
    path.write_bytes(b"prior")
    with pytest.raises(ValueError, match=message):
        p.save(str(path))
    assert path.read_bytes() == b"prior"


def test_sweep_counts_y_disjoint_candidate_visits_before_intersection_work():
    x, y, faces = [], [], []
    for i in range(320):
        n = len(x)
        x.extend([0, 1, 0])
        y.extend([3 * i, 3 * i, 3 * i + 1])
        faces.append([n, n + 1, n + 2])
    p = mp.plot({"x": x, "y": y}).triplot(
        "x", "y", triangulation=mp.TriangulationSpec(faces)
    )
    assert any("50000 active-box pair visits" in issue for issue in mp.validate(p.spec))
