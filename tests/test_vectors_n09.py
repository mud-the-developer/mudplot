"""N09 geometry against directly authored native Matplotlib controls."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.colors import to_rgba


def test_data_quiver_mask_typed_groups_and_twin_positions():
    data = {
        "x": [0, 1, 4, 6],
        "y": [1, 3, 2, 2],
        "u": [1, 99, -2, 0],
        "v": [0.5, 99, 1, 0],
        "mask": [False, True, False, False],
        "g": [True, True, 1, 1],
    }
    plot = (
        mp.plot(data)
        .secondary_yaxis("Native twin")
        .size(6, 4)
        .quiver(
            "x",
            "y",
            "u",
            "v",
            vector={"mode": "data", "mask_column": "mask", "pivot": "middle"},
            group="g",
            hue_order=[True, "Reserved", 1],
            width=0.03,
            axis="y2",
        )
    )
    opened = mp.Plot.from_json(plot.to_json())
    fig = opened.render()
    ref = plt.figure(figsize=fig.get_size_inches(), dpi=fig.dpi)
    try:
        a, b = fig.axes
        (q,) = b.collections
        assert not a.collections
        assert b.get_ylabel() == "Native twin"
        assert b.get_legend_handles_labels()[1] == ["True", "1"]
        np.testing.assert_array_equal(q.get_offsets(), [[0, 1], [4, 2]])
        np.testing.assert_array_equal(q.U, [1, -2])
        np.testing.assert_array_equal(q.V, [0.5, 1])
        assert q.angles == "xy" and q.scale_units == "xy" and q.scale == 1
        twin = ref.add_axes(b.get_position().bounds)
        twin.set_xlim(b.get_xlim())
        twin.set_ylim(b.get_ylim())
        expected = twin.quiver(
            [0, 4],
            [1, 2],
            [1, -2],
            [0.5, 1],
            angles="xy",
            scale_units="xy",
            scale=1,
            units="width",
            width=0.03,
            minlength=0,
            pivot="middle",
        )
        ref.canvas.draw()
        fig.canvas.draw()
        colours = q.get_facecolors()
        assert len(colours) == 2 and not np.array_equal(colours[0], colours[1])
        np.testing.assert_allclose(
            colours, [to_rgba(line.get_color()) for line in b.lines]
        )
        for actual, want in zip(q.get_paths(), expected.get_paths(), strict=True):
            np.testing.assert_allclose(actual.vertices, want.vertices, atol=1e-9)
        assert opened.spec.data.columns == data and opened.to_json() == plot.to_json()
    finally:
        plt.close(fig)
        plt.close(ref)


def test_barbs_with_nonuniform_rows_and_named_component_units():
    raw = {
        "x": [1, 3, 8, 7],
        "y": [9, 4, 1, 2],
        "u": [2, 4, 10, 0],
        "v": [0, 0, 0, 0],
        "mask": [False, True, False, False],
    }
    p = mp.plot(raw).barbs(
        "x",
        "y",
        "u",
        "v",
        vector={
            "mask_column": "mask",
            "length": 9,
            "pivot": "middle",
            "half": 2,
            "full": 4,
            "flag": 10,
            "rounding": False,
        },
    )
    fig = p.render()
    ref, ax = plt.subplots()
    try:
        (actual,) = fig.axes[0].collections
        expected = ax.barbs(
            [1, 8, 7],
            [9, 1, 2],
            [2, 10, 0],
            [0, 0, 0],
            length=9,
            pivot="middle",
            barb_increments={"half": 2, "full": 4, "flag": 10},
            rounding=False,
        )
        np.testing.assert_array_equal(actual.get_offsets(), [[1, 9], [8, 1], [7, 2]])
        assert [len(path.vertices) for path in actual.get_paths()] == [
            len(path.vertices) for path in expected.get_paths()
        ]
        for have, want in zip(actual.get_paths(), expected.get_paths(), strict=True):
            np.testing.assert_array_equal(have.vertices, want.vertices)
        assert p.spec.data.columns == raw
    finally:
        plt.close(fig)
        plt.close(ref)


def test_native_horizontal_masked_flow_and_explicit_data_seed():
    x = [0, 1, 2, 3, 4]
    y = [0, 1, 2, 3]
    u = [[1] * 5 for _ in y]
    v = [[0] * 5 for _ in y]
    u[3][4] = None
    v[3][4] = None
    mask = [[False] * 5 for _ in y]
    mask[0][0] = True
    cfg = mp.VectorSpec(
        x_coords=x,
        y_coords=y,
        u_matrix="u",
        v_matrix="v",
        mask=mask,
        start_points=[[1, 1]],
        density=0.5,
        minlength=0.03,
        maxlength=2,
        integration_direction="forward",
        arrowsize=1.2,
    )
    p = mp.plot().matrix("u", u).matrix("v", v).streamplot(vector=cfg, alpha=0.7)
    reopened = mp.Plot.from_json(p.to_json())
    fig = reopened.render()
    ref, ax = plt.subplots()
    try:
        hidden = np.array(mask)
        hidden[3, 4] = True
        expected = ax.streamplot(
            x,
            y,
            np.ma.array(np.asarray(u, dtype=float), mask=hidden),
            np.ma.array(np.asarray(v, dtype=float), mask=hidden),
            start_points=[[1, 1]],
            density=0.5,
            minlength=0.03,
            maxlength=2,
            integration_direction="forward",
            arrowsize=1.2,
        )
        (rendered,) = fig.axes[0].collections
        np.testing.assert_allclose(
            np.vstack(rendered.get_segments()), np.vstack(expected.lines.get_segments())
        )
        assert len(fig.axes[0].patches) == len(ax.patches) >= 1
        assert all(patch.get_alpha() == 0.7 for patch in fig.axes[0].patches)
        xy = np.vstack(rendered.get_segments())
        assert (xy[:, 1] == 1).all()
        assert xy[:, 0].max() > 1
        assert reopened.spec.data.matrices["u"] == u and not reopened.spec.data.columns
    finally:
        plt.close(fig)
        plt.close(ref)


def test_native_3d_raw_and_normalized_shaft_length():
    data = {
        "x": [1, 2, 7],
        "y": [1, 4, 2],
        "z": [0, 2, 2],
        "u": [3, 0, 0],
        "v": [4, 1, 0],
        "w": [0, 0, 0],
    }
    p = mp.plot(data).layout(1, 2).size(8, 4)
    p.projection3d().quiver3d("x", "y", "z", "u", "v", "w", vector={"length": 0.5})
    p.projection3d(panel=1).quiver3d(
        "x", "y", "z", "u", "v", "w", vector={"length": 2, "normalize": True}, panel=1
    )
    fig = p.render()
    try:
        for idx, want in enumerate(([2.5, 0.5], [2, 2])):
            axis = fig.axes[idx]
            (actual,) = axis.collections
            seg = np.array(actual._segments3d)
            assert axis.name == "3d" and len(seg) == 6
            np.testing.assert_allclose(
                np.linalg.norm(seg[:2, 0] - seg[:2, 1], axis=1), want
            )
            np.testing.assert_allclose(seg[:2, 1], [[1, 1, 0], [2, 4, 2]])
    finally:
        plt.close(fig)


def test_legacy_null_remains_old_and_invalid_vectors_preserve_output(tmp_path):
    raw = {
        "x": [1, 2],
        "y": [1, 2],
        "u": [1, 2],
        "v": [0, 1],
        "g": ["A", "B"],
        "mask": [1, False],
    }
    old = mp.plot(raw).quiver("x", "y", "u", "v")
    assert "vector" not in old.spec.panels[0].layers[0].to_dict()
    out = tmp_path / "original.svg"
    out.write_text("prior")
    cases = [
        (
            mp.plot(raw).quiver("x", "y", "u", "v", vector={}, group="g").xscale("log"),
            "linear numeric",
        ),
        (
            mp.plot(raw).barbs("x", "y", "u", "v", vector={}, group="g").date_axis("x"),
            "linear numeric",
        ),
        (
            mp.plot(raw).quiver("x", "y", "u", "v", vector={"mask_column": "mask"}),
            "aligned booleans",
        ),
        (
            mp.plot(raw).quiver("x", "y", "u", "v", vector={"length": 1}),
            "not supported",
        ),
        (
            mp.plot()
            .matrix("u", [[1, 1], [1, 1]])
            .matrix("v", [[0, 0], [0, 0]])
            .streamplot(
                vector={
                    "x_coords": [0, 1, 3],
                    "y_coords": [0, 1],
                    "u_matrix": "u",
                    "v_matrix": "v",
                }
            ),
            "uniformly increasing",
        ),
        (
            mp.plot()
            .matrix("u", [[1, None], [1, 1]])
            .matrix("v", [[0, 0], [0, 0]])
            .streamplot(
                vector={
                    "x_coords": [0, 1],
                    "y_coords": [0, 1],
                    "u_matrix": "u",
                    "v_matrix": "v",
                }
            ),
            "paired null",
        ),
        (mp.plot(raw).streamplot(vector={}, group="g"), "do not accept row grouping"),
        (
            mp.plot(raw).barbs("x", "y", "u", "v", vector={"half": 1e-6}),
            "64 half-increments",
        ),
    ]
    for p, message in cases:
        with pytest.raises(ValueError, match=message):
            p.save(str(out))
        assert out.read_text() == "prior"
