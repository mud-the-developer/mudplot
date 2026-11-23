"""Numeric semantic guides use the mark domain without replacing observations."""

from decimal import Decimal, localcontext

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.colors import to_rgba


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def semantic_config(**changes):
    return {"hue": "temperature", "hue_kind": "numeric", **changes}


@pytest.mark.parametrize("kind", ["scatter", "lineplot"])
@pytest.mark.parametrize(
    "bounds",
    [
        [-10.0, 10.0],
        [-1e308, 1e308],
        [-1e-323, 1e-323],
        [1e308, float(np.nextafter(1e308, np.inf))],
    ],
)
def test_numeric_bar_matches_independent_fractions_and_raw_signed_domain(kind, bounds):
    low, high = bounds
    data = {
        "x": [0, 1, 2, 0, 1, 2],
        "y": [1, 2, 3, 4, 5, 6],
        "temperature": [low, low, low, high, high, high],
    }
    p = mp.plot(data)
    if kind == "scatter":
        p.scatter("x", "y", semantics=semantic_config(hue_norm=bounds), colorbar=True)
    else:
        p.lineplot(
            "x",
            "y",
            errorbar=None,
            semantics=semantic_config(hue_norm=bounds),
            colorbar=True,
        )
    p.xlim(-1, 3).ylim(0, 7)
    fig = p.render()
    ax, guide = fig.axes
    assert guide.get_ylabel() == "temperature"
    middle = max(low, min(high, low * 0.5 + high * 0.5))
    raw_ticks = list(dict.fromkeys([low, middle, high]))
    with localcontext() as context:
        context.prec = 80
        expected_ticks = [
            float((Decimal(value) - Decimal(low)) / (Decimal(high) - Decimal(low)))
            for value in raw_ticks
        ]
    np.testing.assert_allclose(guide.get_yticks(), expected_ticks)
    assert [t.get_text() for t in guide.get_yticklabels()] == [
        str(value) for value in raw_ticks
    ]
    endpoint_colors = guide.collections[-1].to_rgba([0.0, 1.0])
    np.testing.assert_array_equal(ax.get_xlim(), [-1, 3])
    np.testing.assert_array_equal(ax.get_ylim(), [0, 7])
    if kind == "scatter":
        offsets = np.asarray(ax.collections[0].get_offsets())
        np.testing.assert_array_equal(offsets, np.column_stack([data["x"], data["y"]]))
        colors = ax.collections[0].get_facecolors()
        np.testing.assert_array_equal(colors[0], colors[2])
        np.testing.assert_array_equal(colors[3], colors[5])
        assert not np.array_equal(colors[0], colors[3])
        np.testing.assert_allclose(colors[[0, 3]], endpoint_colors)
    else:
        lines = [line for line in ax.lines if len(line.get_xdata())]
        assert len(lines) == 2
        np.testing.assert_array_equal(lines[0].get_ydata(), [1, 2, 3])
        np.testing.assert_array_equal(lines[1].get_ydata(), [4, 5, 6])
        np.testing.assert_allclose(
            [to_rgba(line.get_color()) for line in lines], endpoint_colors
        )
    assert not any(
        label.startswith("hue:") for label in ax.get_legend_handles_labels()[1]
    )
    assert p.spec.data.columns == data
    assert mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log)


@pytest.mark.parametrize("constant", [-4.0, 0.0, 5e-324, 1e308])
def test_constant_numeric_hue_is_one_solid_midpoint_swatch_with_exact_tick(constant):
    p = mp.plot({"x": [1, 2], "y": [3, 4], "temperature": [constant, constant]})
    p.scatter(
        "x", "y", semantics=semantic_config(), colorbar=True, clabel="Temperature"
    )
    ax, guide = p.render().axes
    assert guide.get_ylabel() == "Temperature"
    assert [text.get_text() for text in guide.get_yticklabels()] == [str(constant)]
    colors = ax.collections[0].get_facecolors()
    np.testing.assert_array_equal(colors[0], colors[1])
    np.testing.assert_allclose(guide.collections[-1].to_rgba(0.5), colors[0])


def test_shared_line_scatter_pool_preserves_geometry_units_and_one_bar_per_panel():
    data = {
        "x": [0, 1, 2, 0, 1, 2],
        "y": [1, 2, 3, 4, 5, 6],
        "temperature": [-10, -10, -10, 10, 10, 10],
        "mass": [0, 0, 0, 10, 10, 10],
    }
    config = semantic_config(scale_id="pool", size="mass", sizes=[2, 8])
    p = mp.plot(data)
    p.scatter(
        "x", "y", semantics=config, colorbar=True, edge_color="black", line_width=0.75
    )
    p.lineplot("x", "y", errorbar=None, semantics=config, colorbar=True)
    fig = p.render()
    assert len(fig.axes) == 2
    ax = fig.axes[0]
    collection = ax.collections[0]
    np.testing.assert_array_equal(collection.get_sizes(), [4, 4, 4, 64, 64, 64])
    np.testing.assert_allclose(collection.get_edgecolors()[0], to_rgba("black"))
    np.testing.assert_array_equal(collection.get_linewidths(), [0.75])
    lines = [line for line in ax.lines if len(line.get_xdata())]
    assert [line.get_linewidth() for line in lines] == [2, 8]
    np.testing.assert_allclose(
        collection.get_facecolors()[0], to_rgba(lines[0].get_color())
    )
    np.testing.assert_allclose(
        collection.get_facecolors()[-1], to_rgba(lines[-1].get_color())
    )
    labels = ax.get_legend_handles_labels()[1]
    assert any(label.startswith("size:") for label in labels)
    assert any(label.startswith("size (line width, pt):") for label in labels)


@pytest.mark.parametrize("semantic", [False, True])
@pytest.mark.parametrize("width", [0, 0.25, 2])
def test_outlines_apply_explicit_points_without_changing_marker_diameters(
    semantic, width
):
    p = mp.plot({"x": [1, 2], "y": [3, 4], "temperature": [-1, 1]})
    p.scatter(
        "x",
        "y",
        semantics=semantic_config() if semantic else None,
        marker_size=7,
        edge_color="#123456",
        line_width=width,
        alpha=0.6,
    )
    collection = p.render().axes[0].collections[0]
    np.testing.assert_array_equal(
        np.broadcast_to(collection.get_sizes(), (2,)), [49, 49]
    )
    np.testing.assert_array_equal(collection.get_linewidths(), [width])
    np.testing.assert_allclose(collection.get_edgecolors()[0], to_rgba("#123456", 0.6))
    np.testing.assert_array_equal(collection.get_offsets(), [[1, 3], [2, 4]])


def test_requested_colourbar_survives_hidden_semantic_legend_and_empty_facet():
    p = mp.plot({"x": [1, 2], "y": [3, 4], "temperature": [-1, 1], "facet": ["a", "b"]})
    p.scatter("x", "y", semantics=semantic_config(legend=False), colorbar=True)
    p.facet(col="facet", col_order=["a", "b", "empty"])
    fig = p.render()
    assert len(fig.axes) == 5  # Three data panels, two observed pooled-domain bars.
    empty = [ax for ax in fig.axes if not ax.collections]
    assert len(empty) == 1
    assert not empty[0].get_legend_handles_labels()[1]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"semantics": {"hue": "temperature"}, "colorbar": True},
        {"semantics": semantic_config(), "clabel": "Temperature"},
        {"semantics": semantic_config(), "colorbar": 1},
        {"semantics": semantic_config(), "line_width": -1},
        {"semantics": semantic_config(), "line_width": True},
        {"semantics": semantic_config(), "edge_color": "not a colour"},
    ],
)
def test_invalid_guide_or_outline_requests_reject_before_artists(kwargs):
    p = mp.plot({"x": [1], "y": [2], "temperature": [-3]}).scatter("x", "y", **kwargs)
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


def test_unmapped_lineplot_does_not_silently_ignore_colourbar_request():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).lineplot(
        "x", "y", errorbar=None, colorbar=True
    )
    assert any("semantic numeric hue" in issue for issue in mp.validate(p.spec))


def test_later_scope_request_replaces_earlier_hue_calibration_not_other_guides():
    data = {
        "x": [0, 1],
        "y": [1, 2],
        "temperature": [-1, 1],
        "mass": [1, 2],
        "shape": ["A", "B"],
    }
    config = semantic_config(scale_id="pool", size="mass", style="shape")
    p = mp.plot(data).scatter(
        "x", "y", semantics=config, label="observations", colorbar=False
    )
    p.lineplot(
        "x",
        "y",
        semantics=config,
        label="estimates",
        errorbar=None,
        colorbar=True,
    )
    before = p.spec
    fig = p.render()
    assert len(fig.axes) == 2
    labels = fig.axes[0].get_legend_handles_labels()[1]
    assert "observations" in labels and "estimates" in labels
    assert not any(label.startswith("hue:") for label in labels)
    assert any(label.startswith("size:") for label in labels)
    assert any(label.startswith("size (line width, pt):") for label in labels)
    assert any(label.startswith("style:") for label in labels)
    np.testing.assert_array_equal(
        np.concatenate([artist.get_offsets() for artist in fig.axes[0].collections]),
        [[0, 1], [1, 2]],
    )
    assert p.spec == before


def test_primary_secondary_shared_scope_has_one_logical_panel_colourbar():
    data = {
        "date": ["2026-01-01", "2026-01-11"],
        "y": [1, 2],
        "temperature": [-1, 1],
        "mass": [1, 2],
    }
    config = semantic_config(scale_id="pool", size="mass")
    p = mp.plot(data).scatter(
        "date", "y", semantics=config, colorbar=True, label="primary"
    )
    p.scatter(
        "date",
        "y",
        semantics=config,
        colorbar=True,
        axis="y2",
        label="secondary",
    ).date_axis("x", timezone="UTC").secondary_yaxis()
    before = p.spec
    fig = p.render()
    assert len(fig.axes) == 3
    primary, secondary = fig.axes[:2]
    fig.canvas.draw()
    np.testing.assert_allclose(
        primary.get_position().bounds,
        secondary.get_position().bounds,
        rtol=0,
        atol=1e-14,
    )
    points = np.asarray(primary.collections[0].get_offsets())
    np.testing.assert_allclose(
        primary.transData.transform(points)[:, 0],
        secondary.transData.transform(points)[:, 0],
        rtol=0,
        atol=1e-9,
    )
    np.testing.assert_array_equal(
        primary.collections[0].get_offsets(), secondary.collections[0].get_offsets()
    )
    np.testing.assert_array_equal(primary.collections[0].get_offsets()[:, 1], [1, 2])
    np.testing.assert_allclose(
        np.diff(primary.collections[0].get_offsets()[:, 0]), [10]
    )
    labels = primary.get_legend_handles_labels()[1]
    labels += secondary.get_legend_handles_labels()[1]
    assert "primary" in labels and "secondary" in labels
    assert not any(label.startswith("hue:") for label in labels)
    assert any(label.startswith("size:") for label in labels)
    assert p.spec == before


def test_incompatible_requested_shared_colourbar_labels_reject():
    data = {"x": [0, 1], "y": [1, 2], "temperature": [-1, 1]}
    config = semantic_config(scale_id="pool")
    p = mp.plot(data).scatter(
        "x", "y", semantics=config, colorbar=True, clabel="Temperature"
    )
    p.scatter("x", "y", semantics=config, colorbar=True, clabel="Other units")
    assert any("identical labels" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="identical labels"):
        p.render()
