"""Check physical N10 geometry on both supported native 3D representations."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def _vertices(collection):
    if hasattr(collection, "_faces"):
        return np.asarray(collection._faces).reshape(-1, 3)
    return collection._vec[:3].T


def _limits(points):
    return np.asarray([np.min(points, axis=0), np.max(points, axis=0)])


def test_nonuniform_grid_uses_every_native_surface_face_and_wire():
    x = [(i / 10) ** 2 for i in range(52)]
    y = [1, 4, 11]
    values = [[j + i % 3 for i in range(len(x))] for j in range(3)]
    p = mp.plot().layout(1, 2).size(8, 4).matrix("height", values)
    cfg = mp.SpatialSpec(x_coords=x, y_coords=y)
    p.projection3d().surface("height", spatial=cfg, colorbar=False)
    p.projection3d(panel=1).wireframe("height", spatial=cfg, panel=1)
    fig = mp.Plot.from_json(p.to_json()).render()
    ref = plt.figure()
    ax = ref.add_subplot(projection="3d")
    try:
        xs, ys = np.meshgrid(x, y)
        native = ax.plot_surface(xs, ys, np.asarray(values), rstride=1, cstride=1)
        actual = fig.axes[0].collections[0]
        np.testing.assert_allclose(_vertices(actual), _vertices(native))
        assert len(actual.get_array()) == 102
        lines = fig.axes[1].collections[0]._segments3d
        assert len(lines) == len(x) + len(y)
        np.testing.assert_allclose(
            lines[1], np.column_stack((x, [4] * len(x), values[1]))
        )
        np.testing.assert_allclose(
            lines[-1], np.column_stack(([x[-1]] * 3, y, [0, 1, 2]))
        )
    finally:
        plt.close(fig)
        plt.close(ref)


def test_mixed_signed_bars_extent_and_fixed_limits_with_previous_artist():
    raw = {
        "x": [1, 4],
        "y": [2, 6],
        "base": [-2, 10],
        "dx": [2, 1],
        "dy": [1, 2],
        "dz": [3, -4],
        "prior": [-5, -5],
    }
    p = (
        mp.plot(raw)
        .projection3d()
        .bar3d("x", "y", "base", spatial={"dx": "dx", "dy": "dy", "dz": "dz"})
    )
    fig = p.render()
    try:
        (ax,) = fig.axes
        native = _vertices(ax.collections[0])
        np.testing.assert_array_equal(
            _limits(native[native[:, 0] <= 3]), [[1, 2, -2], [3, 3, 1]]
        )
        np.testing.assert_array_equal(
            _limits(native[native[:, 0] >= 4]), [[4, 6, 6], [5, 8, 10]]
        )
        assert (ax.zz_dataLim.xmin, ax.zz_dataLim.xmax) == (-2, 10)
        assert ax.get_zlim()[0] <= -2 and ax.get_zlim()[1] >= 10
    finally:
        plt.close(fig)
    p = (
        mp.plot(raw)
        .projection3d()
        .line3d("x", "y", "prior")
        .bar3d("x", "y", "base", spatial={"dx": "dx", "dy": "dy", "dz": "dz"})
        .zlabel("Height", limits=[-6, 12])
    )
    fig = p.render()
    try:
        (ax,) = fig.axes
        assert (ax.zz_dataLim.xmin, ax.zz_dataLim.xmax) == (-5, 10)
        assert ax.get_zlim() == (-6, 12) and len(ax.lines) == 1
        assert p.spec.data.columns == raw
    finally:
        plt.close(fig)


def test_lateral_contours_match_native_scalar_ranges_and_projected_paths():
    x, y = [1, 3, 8], [10, 14, 20]
    z = [[100 + a + 2 * b for a in x] for b in y]
    xs, ys = np.meshgrid(x, y)
    p = mp.plot().layout(1, 3).size(11, 3.8).matrix("grid", z)
    p.projection3d().contour3d(
        "grid",
        levels=[2, 6],
        spatial={"x_coords": x, "y_coords": y, "direction": "x", "offset": 12},
    )
    p.projection3d(panel=1).contourf3d(
        "grid",
        levels=[11, 15, 19],
        spatial={"x_coords": x, "y_coords": y, "direction": "y", "offset": 7},
        panel=1,
    )
    p.projection3d(panel=2).contour3d(
        "grid", levels=[135, 145], spatial={"x_coords": x, "y_coords": y}, panel=2
    )
    fig = p.render()
    ref = plt.figure()
    ax = ref.add_subplot(projection="3d")
    try:
        controls = (
            ax.contour(xs, ys, z, levels=[2, 6], zdir="x", offset=12),
            ax.contourf(xs, ys, z, levels=[11, 15, 19], zdir="y", offset=7),
            ax.contour(xs, ys, z, levels=[135, 145]),
        )
        for idx, control in enumerate(controls):
            axis = fig.axes[idx]
            actual = axis.collections[0]
            np.testing.assert_array_equal(actual.levels, control.levels)
            for (ap, ac), (ep, ec) in zip(
                actual._3dverts_codes, control._3dverts_codes, strict=True
            ):
                np.testing.assert_allclose(ap, ep)
                np.testing.assert_array_equal(ac, ec)
                assert len(ap)
                if idx < 2:
                    assert (ap[:, idx] == [12, 7][idx]).all()
        assert fig.axes[0].xy_dataLim.xmin == fig.axes[0].xy_dataLim.xmax == 12
        assert fig.axes[0].get_xlim()[0] <= 12 <= fig.axes[0].get_xlim()[1]
        assert fig.axes[1].xy_dataLim.ymin == fig.axes[1].xy_dataLim.ymax == 7
        assert fig.axes[1].get_ylim()[0] <= 7 <= fig.axes[1].get_ylim()[1]
    finally:
        plt.close(fig)
        plt.close(ref)


def test_voxel_edges_and_native_camera_with_triangles_and_vectors():
    raw = {
        "x": [1, 3, 1],
        "y": [2, 2, 5],
        "z": [7, 8, 10],
        "u": [0, 1, 0],
        "v": [1, 0, 1],
        "w": [0, 0, 1],
    }
    p = mp.plot(raw).layout(1, 2).size(8, 4)
    occupancy = [
        [[False, True, False], [True, False, False]],
        [[False, False, False], [False, False, True]],
    ]
    x, y, z = [1, 2, 5, 9], [2, 4, 8], [7, 9, 15]
    p.projection3d().voxels(
        spatial={"occupancy": occupancy, "x_coords": x, "y_coords": y, "z_coords": z},
        color="#23757b",
    )
    p.projection3d(panel=1).trisurf(
        "x", "y", "z", triangulation={"triangles": [[0, 1, 2]]}, panel=1
    )
    p.quiver3d("x", "y", "z", "u", "v", "w", vector={"length": 0.5}, panel=1)
    p.xlim(0, 6, panel=1).ylim(0, 6, panel=1).zlabel("Height", limits=[6, 12], panel=1)
    p.camera3d(
        {
            "elevation": 18,
            "azimuth": -51,
            "roll": 12,
            "vertical_axis": "y",
            "projection": "ortho",
            "box_aspect": [2, 1, 0.7],
            "zoom": 0.9,
        },
        panel=1,
    )
    reopened = mp.Plot.from_json(p.to_json())
    fig = reopened.render()
    rf = plt.figure()
    ctr = rf.add_subplot(projection="3d")
    try:
        left, right = fig.axes
        expected = [
            [[2, 2, 7], [5, 4, 9]],
            [[1, 4, 7], [2, 8, 9]],
            [[5, 4, 9], [9, 8, 15]],
        ]
        got = [
            _limits(_vertices(collection)).tolist() for collection in left.collections
        ]
        assert sorted(got) == sorted(expected)
        assert len(right.collections) == 2
        np.testing.assert_array_equal(
            np.unique(_vertices(right.collections[0]), axis=0),
            [[1, 2, 7], [1, 5, 10], [3, 2, 8]],
        )
        arrows = np.array(right.collections[1]._segments3d[:3])
        np.testing.assert_allclose(
            arrows[:, 0] - arrows[:, 1],
            0.5 * np.column_stack((raw["u"], raw["v"], raw["w"])),
        )
        ctr.set_xlim(0, 6)
        ctr.set_ylim(0, 6)
        ctr.set_zlim(6, 12)
        ctr.view_init(18, -51, 12, "y")
        ctr.set_proj_type("ortho")
        ctr.set_box_aspect([2, 1, 0.7], zoom=0.9)
        np.testing.assert_allclose(right.get_proj(), ctr.get_proj())
        assert right.get_xlim() == (0, 6) and right.get_zlim() == (6, 12)
        assert reopened.spec.panels[0].layers[0].spatial.occupancy == occupancy
        assert reopened.to_json() == p.to_json()
    finally:
        plt.close(fig)
        plt.close(rf)


def test_native_lateral_filled_bands_without_offset_stay_at_midpoints():
    x, y = [1, 4, 8], [2, 5, 9]
    z = [[10 + a + b for a in x] for b in y]
    p = (
        mp.plot()
        .projection3d()
        .matrix("surface", z)
        .contourf3d(
            "surface",
            levels=[2, 4, 8],
            spatial={"x_coords": x, "y_coords": y, "direction": "x"},
        )
    )
    fig = p.render()
    ref = plt.figure()
    ax = ref.add_subplot(projection="3d")
    try:
        xs, ys = np.meshgrid(x, y)
        control = ax.contourf(xs, ys, z, levels=[2, 4, 8], zdir="x")
        (actual,) = fig.axes[0].collections
        for midpoint, (have, codes), (want, native_codes) in zip(
            [3, 6], actual._3dverts_codes, control._3dverts_codes, strict=True
        ):
            assert len(have) and (have[:, 0] == midpoint).all()
            np.testing.assert_allclose(have, want)
            np.testing.assert_array_equal(codes, native_codes)
    finally:
        plt.close(fig)
        plt.close(ref)
