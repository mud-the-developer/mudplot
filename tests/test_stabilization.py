"""Regression checks for data fidelity, editing isolation and exact-size export."""

import struct
from typing import Any, cast

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot import actions as A
from mudplot import io
from mudplot.__main__ import main
from mudplot.spec import FigureSpec


def test_categories_share_positions_across_layers_and_twins():
    p = mp.plot({"a": ["A", "B"], "b": ["B", "C"], "y": [10, 20]})
    p.line("a", "y").line("b", "y").secondary_yaxis().line("b", "y", axis="y2")
    ax, twin = p.render().axes
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), [0, 1])
    np.testing.assert_array_equal(ax.lines[1].get_xdata(), [1, 2])
    np.testing.assert_array_equal(twin.lines[0].get_xdata(), [1, 2])
    assert [t.get_text() for t in ax.get_xticklabels()] == ["A", "B", "C"]


@pytest.mark.parametrize("mode", ["all", "row", "col"])
def test_categories_share_positions_across_panels(mode):
    p = mp.plot({"a": ["A", "B"], "b": ["B", "C"], "y": [10, 20]})
    p.layout(*((2, 1) if mode == "col" else (1, 2))).share(x=mode)
    p.line("a", "y").line("b", "y", panel=1)
    ax, other = p.render().axes
    np.testing.assert_array_equal(other.lines[0].get_xdata(), [1, 2])
    for a in (ax, other):
        assert [t.get_text() for t in a.get_xticklabels()] == ["A", "B", "C"]


@pytest.mark.parametrize("three_d", [False, True])
def test_grouped_scatter_uses_one_norm_and_colorbar(three_d):
    data = {
        "x": [1, 2, 3, 4],
        "y": [2, 3, 4, 5],
        "z": [1, 2, 3, 4],
        "g": ["a", "a", "b", "b"],
        "c": [0, 1, 100, 101],
    }
    p = mp.plot(data)
    if three_d:
        p.projection3d().scatter3d("x", "y", "z", group="g", c="c", colorbar=True)
    else:
        p.scatter("x", "y", group="g", c="c", colorbar=True)
    fig = p.render()
    assert len(fig.axes) == 2
    a, b = fig.axes[0].collections
    assert a.norm is b.norm
    assert a.get_clim() == (0, 101)
    assert b.get_clim() == (0, 101)


def test_3d_panel_labels_axes_and_legend():
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4], "z": [5, 6]})
        .projection3d()
        .line3d("x", "y", "z", label="data")
        .auto_label()
        .xlim(1, 20)
        .ylim(3, 40)
        .xscale("log")
        .yscale("log")
        .zlabel("Z", scale="log", limits=[5, 60])
        .legend(location="lower left")
    )
    ax = cast(Any, p.render().axes[0])
    assert [t.get_text() for t in ax.texts] == ["a)"]
    assert ax.get_xlim() == (1, 20)
    assert ax.get_ylim() == (3, 40)
    assert ax.get_zlim() == (5, 60)
    assert (ax.get_xscale(), ax.get_yscale(), ax.get_zscale()) == ("log",) * 3
    assert cast(Any, ax.get_legend())._loc == 3


def test_mixed_projection_preserves_2d_axis_sharing():
    p = mp.plot({"x": [1, 2], "y": [3, 4], "z": [5, 6]}).layout(1, 3)
    p.line("x", "y").line("x", "y", panel=1)
    p.projection3d(panel=2).line3d("x", "y", "z", panel=2).share(x="all")
    ax, other, three_d = p.render().axes
    assert ax.get_shared_x_axes().joined(ax, other)
    assert not ax.get_shared_x_axes().joined(ax, three_d)


def test_independent_layers_and_pie_get_enough_colors():
    p = mp.plot({"x": [1, 2], "y": [3, 4]})
    for i in range(5):
        p.line("x", "y", label=str(i))
    assert len({line.get_color() for line in p.render().axes[0].lines}) == 5
    pie = mp.plot({"label": list("abcde"), "v": [1, 2, 3, 4, 5]}).pie("label", "v")
    assert len({w.get_facecolor() for w in pie.render().axes[0].patches}) == 5


def test_store_isolates_actions_history_snapshots_and_listeners():
    store = mp.Store()
    initial = store.state
    initial.suptitle = "corrupted"
    data = {"x": [1]}
    store.dispatch(A.SetData(data))
    data["x"][0] = 999
    first_action = store.history[0]
    assert isinstance(first_action, A.SetData)
    first_action.columns["x"][0] = 998
    store.state.data.columns["x"][0] = 997
    store.dispatch(A.SetTitle("hello"))
    assert store.undo().data.columns == {"x": [1]}
    assert store.redo().data.columns == {"x": [1]}
    assert store.state.suptitle == ""

    def corrupt(state, action):
        state.data.columns["x"][0] = 996
        if isinstance(action, A.SetData):
            action.columns["x"][0] = 995

    store.subscribe(corrupt)
    result = store.dispatch(A.SetData({"x": [2]}))
    result.data.columns["x"][0] = 994
    assert store.state.data.columns == {"x": [2]}
    last_action = store.history[-1]
    assert isinstance(last_action, A.SetData)
    assert last_action.columns == {"x": [2]}
    store.undo()
    store.redo()
    assert store.state.data.columns == {"x": [2]}


def test_reducer_result_does_not_alias_action_payload():
    columns = {"x": [1.0]}
    state = mp.reduce(FigureSpec(), A.SetData(columns))
    columns["x"][0] = 9
    assert state.data.columns == {"x": [1.0]}

    markers = ["o", "s"]
    state = mp.reduce(state, A.SetEncoding({"markers": markers}))
    markers[0] = "x"
    assert state.theme.markers == ["o", "s"]

    limits = [1.0, 10.0]
    state = mp.reduce(state, A.SetSecondaryAxis(limits=limits))
    limits[0] = 9
    assert state.panels[0].y2 is not None
    assert state.panels[0].y2.limits == [1, 10]

    z_limits = [-1.0, 1.0]
    state = mp.reduce(state, A.SetZAxis(limits=z_limits))
    z_limits[0] = 0
    assert state.panels[0].z is not None
    assert state.panels[0].z.limits == [-1, 1]


def test_exact_size_export_ignores_ambient_tight_crop(tmp_path):
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").size(4, 3)
    p.dispatch(A.SetDpi(100))
    path = tmp_path / "figure.png"
    with plt.rc_context({"savefig.bbox": "tight"}):
        p.save(path)
    with path.open("rb") as f:
        f.read(16)
        assert struct.unpack(">II", f.read(8)) == (400, 300)
    p.save(path, tight=True)
    with path.open("rb") as f:
        f.read(16)
        assert struct.unpack(">II", f.read(8)) != (400, 300)
    svg = tmp_path / "figure.svg"
    plt.close(mp.save(p.spec, svg))
    assert 'width="288pt" height="216pt"' in svg.read_text()
    pdf = tmp_path / "figure.pdf"
    plt.close(mp.save(p.spec, pdf))
    assert b"/MediaBox [ 0 0 288 216 ]" in pdf.read_bytes()

    extensionless = tmp_path / "extensionless"
    with plt.rc_context({"savefig.format": "svg"}):
        plt.close(mp.save(p.spec, extensionless))
    assert not extensionless.exists()
    assert extensionless.with_suffix(".svg").exists()


def test_svg_export_stays_standalone_despite_ambient_config(tmp_path):
    path = tmp_path / "heat.svg"
    plot = mp.plot({}).matrix("m", [[1, 2], [3, 4]]).heatmap("m")
    with plt.rc_context({"svg.image_inline": False}):
        plt.close(mp.save(plot.spec, path))

    assert "data:image/png;base64" in path.read_text(encoding="utf-8")
    assert sorted(tmp_path.iterdir()) == [path]


def test_save_preserves_existing_output_on_atomic_replace_failure(
    tmp_path, monkeypatch
):
    path = tmp_path / "figure.png"
    path.write_bytes(b"keep")
    open_figures = set(plt.get_fignums())

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        mp.save(mp.plot({"x": [1], "y": [2]}).line("x", "y").spec, path)

    assert path.read_bytes() == b"keep"
    assert sorted(tmp_path.iterdir()) == [path]
    assert set(plt.get_fignums()) == open_figures


def test_cli_preview_caps_pixels_without_changing_spec(tmp_path, capsys):
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").size(100, 50)
    p.dispatch(A.SetDpi(2400))
    spec_path, png = tmp_path / "figure.json", tmp_path / "preview.png"
    mp.save_spec(p.spec, spec_path)

    assert main(["render", str(spec_path), str(png), "--preview"]) == 0
    with png.open("rb") as handle:
        handle.read(16)
        assert struct.unpack(">II", handle.read(8)) == (2000, 1000)
    assert mp.load_spec(spec_path).dpi == 2400

    assert main(["render", str(spec_path), str(tmp_path / "bad.pdf"), "--preview"]) == 1
    assert "--preview requires a .png output path" in capsys.readouterr().err


def test_png_pdf_and_svg_exports_are_byte_reproducible(tmp_path):
    p = mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]}).line("x", "y")
    for fmt in ("pdf", "svg", "png"):
        first, second = tmp_path / f"first.{fmt}", tmp_path / f"second.{fmt}"
        plt.close(p.save(first))
        plt.close(p.save(second))
        first_bytes = first.read_bytes()
        assert first_bytes == second.read_bytes(), fmt
        if fmt == "pdf":
            assert b"/CreationDate" not in first_bytes
            assert b"/ModDate" not in first_bytes

    reordered = mp.plot({"y": [1, 4, 9], "x": [1, 2, 3]}).line("x", "y")
    assert p.spec == reordered.spec
    first, second = tmp_path / "ordered.svg", tmp_path / "reordered.svg"
    plt.close(p.save(first))
    plt.close(reordered.save(second))
    assert first.read_bytes() == second.read_bytes()


def test_context_free_tex_preview_keeps_vector_artists(monkeypatch):
    original_figure = plt.figure

    def quantized_figure(*args, **kwargs):
        fig = original_figure(*args, **kwargs)
        fig.set_size_inches((3.0, 2.0), forward=False)
        return fig

    monkeypatch.setattr(plt, "figure", quantized_figure)
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y")
    fig = p.preview(tex="ieee", show_context=False)
    assert len(fig.axes[0].lines) == 1
    assert not fig.axes[0].images
    np.testing.assert_allclose(
        fig.get_size_inches(), mp.figsize_for(mp.TEX_PRESETS["ieee"])
    )


def test_tex_context_displays_image_at_true_physical_width(monkeypatch):
    original_subplots = plt.subplots

    def quantized_subplots(*args, **kwargs):
        fig, ax = original_subplots(*args, **kwargs)
        fig.set_size_inches((4.0, 4.0), forward=False)
        return fig, ax

    monkeypatch.setattr(plt, "subplots", quantized_subplots)
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y")
    fig = p.preview(tex="ieee", fraction=0.5)
    fig.canvas.draw()
    ax = fig.axes[0]
    left, right, bottom, _ = ax.images[0].get_extent()
    start, end = ax.transData.transform([(left, bottom), (right, bottom)])
    width_inches = (end[0] - start[0]) / fig.dpi
    assert width_inches == pytest.approx(mp.figsize_for(mp.TEX_PRESETS["ieee"])[0] / 2)


def test_render_and_save_failures_close_their_figures(tmp_path, capsys):
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y", color="not-a-color")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before

    huge = 10**1000
    huge_y = mp.plot({"x": [1], "y": [huge]}).line("x", "y")
    for plot in (
        mp.plot({"x": [huge], "y": [1]}).line("x", "y"),
        huge_y,
        mp.plot({}).matrix("m", [[huge]]).heatmap("m"),
    ):
        with pytest.raises(ValueError, match="outside the floating-point range"):
            plot.render()
        assert plt.get_fignums() == before

    huge_style = mp.plot({"x": [1], "y": [2]}).line("x", "y", line_width=huge)
    for index, plot in enumerate((huge_y, huge_style)):
        spec_path = tmp_path / f"huge-{index}.json"
        output = tmp_path / f"figure-{index}.png"
        mp.save_spec(plot.spec, spec_path)
        output.write_bytes(b"keep")
        assert main(["render", str(spec_path), str(output)]) == 1
        error = capsys.readouterr().err
        assert error.startswith("error:")
        assert "Traceback" not in error
        assert output.read_bytes() == b"keep"
        assert plt.get_fignums() == before

    p = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    with pytest.raises(ValueError):
        p.save(tmp_path / "figure.unsupported")
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("size", [0, 2]),
        ("size", [float("nan"), 2]),
        ("dpi", -1),
        ("layout", [-1, -1]),
        ("layout", [2]),
        ("layout", [1.5, 2]),
        ("width_ratios", [0]),
        ("height_ratios", [1, 2]),
    ],
)
def test_invalid_geometry_is_rejected(field, value):
    spec = FigureSpec()
    setattr(spec, field, value)
    assert any(field in issue for issue in mp.validate(spec))
    with pytest.raises(ValueError, match="invalid FigureSpec"):
        mp.render(spec)


@pytest.mark.parametrize("axis", ["x", "y", "y2", "z"])
def test_every_axis_validates_scale_and_limits(axis):
    from mudplot.spec import AxisSpec

    spec = FigureSpec()
    setattr(spec.panels[0], axis, AxisSpec(scale="unknown"))
    assert any("invalid scale" in issue for issue in mp.validate(spec))
    setattr(spec.panels[0], axis, AxisSpec(scale="log", limits=[-1, 10]))
    assert any("log limits" in issue for issue in mp.validate(spec))


@pytest.mark.parametrize("index", [-1, 0.5, True])
def test_invalid_panel_index_is_rejected_without_changing_store(index):
    store = mp.Store()
    before = store.state.to_dict()
    with pytest.raises(ValueError, match="panel index"):
        store.dispatch(A.SetTitle("wrong panel", panel=index))
    assert store.state.to_dict() == before
    assert store.history == []
