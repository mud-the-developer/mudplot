"""Cluster orders, geometry and display metadata remain tied to source indices."""

from __future__ import annotations

import builtins
import copy
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from mudplot._cluster import MAX_CLUSTER_DIMENSION, linkage_issues
from mudplot._cluster_render import cluster_summary

MATRIX = [[1, 2, 8], [2.5, 1, 7], [9, 8, 2], [8, 9.5, 1]]


def build(cluster=None, heatmap=None, values=None, **style):
    return (
        mp.plot()
        .matrix("m", MATRIX if values is None else values)
        .clustermap("m", cluster=cluster, heatmap=heatmap, **style)
        .size(7, 6)
    )


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_source_orders_match_scipy_and_mask_labels_colours_follow_the_same_indices():
    from scipy.cluster.hierarchy import leaves_list, linkage

    config = mp.ClusterSpec(
        row_colors=["red", "red", "blue", "blue"],
        col_colors=["green", "gray", "orange"],
    )
    mask = [[False, True, False], [False] * 3, [False] * 3, [False] * 3]
    display = mp.HeatmapSpec(
        annot=True, mask=mask, xlabels=["A", "B", "C"], ylabels=["N1", "N2", "S1", "S2"]
    )
    xlabels, ylabels = display.xlabels, display.ylabels
    row_colors, col_colors = config.row_colors, config.col_colors
    assert xlabels is not None and ylabels is not None
    assert row_colors is not None and col_colors is not None
    p = build(config, display)
    assert mp.validate(p.spec) == []
    result = cluster_summary(MATRIX, config)
    np.testing.assert_array_equal(
        result.rows, leaves_list(linkage(MATRIX, method="average"))
    )
    np.testing.assert_array_equal(
        result.cols, leaves_list(linkage(np.asarray(MATRIX).T, method="average"))
    )
    figure = p.render()
    ax = figure.axes[0]
    assert len(figure.axes) == 6
    actual = ax.images[0].get_array()
    assert actual is not None
    np.testing.assert_allclose(
        np.ma.getdata(actual), np.asarray(MATRIX)[np.ix_(result.rows, result.cols)]
    )
    np.testing.assert_array_equal(
        np.ma.getmaskarray(actual), np.asarray(mask)[np.ix_(result.rows, result.cols)]
    )
    assert [text.get_text() for text in ax.get_xticklabels()] == [
        xlabels[i] for i in result.cols
    ]
    assert [text.get_text() for text in ax.get_yticklabels()] == [
        ylabels[i] for i in result.rows
    ]
    assert len(ax.texts) == 11
    np.testing.assert_allclose(
        np.asarray(figure.axes[1].images[0].get_array()),
        [[to_rgba(col_colors[i]) for i in result.cols]],
    )
    np.testing.assert_allclose(
        np.asarray(figure.axes[2].images[0].get_array()),
        [[to_rgba(row_colors[i])] for i in result.rows],
    )
    assert p.spec.data.matrices["m"] == MATRIX and config.row_colors == [
        "red",
        "red",
        "blue",
        "blue",
    ]
    figure.canvas.draw()
    body = ax.get_position()
    col_tree, row_tree = figure.axes[3], figure.axes[4]
    np.testing.assert_allclose(
        [col_tree.get_position().x0, col_tree.get_position().x1], [body.x0, body.x1]
    )
    np.testing.assert_allclose(
        [row_tree.get_position().y0, row_tree.get_position().y1], [body.y0, body.y1]
    )
    assert isinstance(row_tree.collections[0], LineCollection)
    assert row_tree.get_ylim() == (40, 0) and col_tree.get_xlim() == (0, 30)


@pytest.mark.parametrize(
    "transform,axis",
    [
        ("z_score", "row"),
        ("z_score", "col"),
        ("standard_scale", "row"),
        ("standard_scale", "col"),
    ],
)
def test_standardization_matches_displayed_values_without_source_mutation(
    transform, axis
):
    config = mp.ClusterSpec(row_cluster=False, col_cluster=False, **{transform: axis})
    result = cluster_summary(MATRIX, config)
    raw = np.asarray(MATRIX)
    dimension = 1 if axis == "row" else 0
    if transform == "z_score":
        expected = (raw - raw.mean(axis=dimension, keepdims=True)) / raw.std(
            axis=dimension, ddof=1, keepdims=True
        )
    else:
        expected = (raw - raw.min(axis=dimension, keepdims=True)) / np.ptp(
            raw, axis=dimension, keepdims=True
        )
    np.testing.assert_allclose(result.matrix, expected, atol=1e-12)
    p = build(config, {"annot": True, "fmt": ".1f"})
    assert mp.validate(p.spec) == [] and len(p.render().axes) == 2
    assert p.spec.data.matrices["m"] == MATRIX


def test_provided_linkages_are_used_without_recomputed_orders():
    rows: list[list[float]] = [[0, 1, 1, 2], [2, 3, 1.5, 2], [4, 5, 5, 4]]
    cols: list[list[float]] = [[0, 2, 2, 2], [1, 3, 4, 3]]
    p = build({"row_linkage": rows, "col_linkage": cols})
    assert mp.validate(p.spec) == []
    result = cluster_summary(MATRIX, mp.ClusterSpec(row_linkage=rows, col_linkage=cols))
    assert result.rows == (0, 1, 2, 3) and result.cols == (1, 0, 2)
    assert vars(p.render().axes[0])["_mudplot_cluster_order"] == {
        "rows": result.rows,
        "cols": result.cols,
    }


@pytest.mark.parametrize(
    "options",
    [
        {"method": "bad"},
        {"metric": "bad"},
        {"method": "ward", "metric": "cityblock"},
        {"row_cluster": 1},
        {"col_cluster": "no"},
        {"optimal_ordering": 1},
        {"z_score": "bad"},
        {"standard_scale": "bad"},
        {"z_score": "row", "standard_scale": "col"},
        {"dendrogram_ratio": True},
        {"dendrogram_ratio": 0},
        {"dendrogram_ratio": 0.7},
        {"tree_width": -1},
        {"tree_color": "not a colour"},
        {"row_colors": ["red"]},
        {"col_colors": ["red", "bad", "blue"]},
        {"row_cluster": False, "row_linkage": []},
    ],
)
def test_invalid_cluster_options_report_errors_without_mutation(options):
    spec = build().spec
    spec.panels[0].layers[0].cluster = mp.ClusterSpec(**options)
    before = copy.deepcopy(spec)
    assert mp.validate(spec) and spec == before


@pytest.mark.parametrize(
    "nodes",
    [
        [],
        [[0, 0, 1, 2]],
        [[0, 2, 1, 2]],
        [[0, 1, -1, 2]],
        [[0, 1, 1, 3]],
        [[0.5, 1, 1, 2]],
        [[0, 1, float("inf"), 2]],
    ],
)
def test_invalid_linkage_boundaries_are_rejected_purely(nodes):
    assert linkage_issues(nodes, 2)


def test_constant_standardization_log_transforms_and_layout_conflicts_are_rejected():
    assert mp.validate(build({"z_score": "row"}, values=[[1, 1], [2, 2]]).spec)
    assert mp.validate(build({"z_score": "row"}, {"norm": "log"}).spec)
    assert mp.validate(build().share(x="all").spec)
    assert mp.validate(build().share_axis("x", "pool").spec)
    assert mp.validate(build().xlim(0, 1).spec)
    assert mp.validate(build().hline(0).spec)
    assert mp.validate(build().secondary_yaxis().spec)
    assert mp.validate(build(values=[[1] * (MAX_CLUSTER_DIMENSION + 1)]).spec)
    wrong = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y", cluster=mp.ClusterSpec())
    assert any(
        "cluster is not supported" in problem for problem in mp.validate(wrong.spec)
    )


def test_single_axis_and_zero_distance_trees_need_no_invented_distance():
    p = build(values=[[5, 5, 5]])
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert vars(ax)["_mudplot_cluster_order"]["rows"] == (0,)
    assert len(ax.figure.axes) == 3


def test_undefined_metric_fails_without_replacing_existing_output(tmp_path):
    p = build({"metric": "correlation"}, values=[[1, 1, 1], [2, 2, 2]])
    path = tmp_path / "keep.png"
    path.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="undefined"):
        p.save(str(path))
    assert path.read_bytes() == b"previous output" and not plt.get_fignums()


def test_missing_scipy_is_explicit_but_disabled_clustering_needs_no_extra(
    tmp_path, monkeypatch
):
    original = builtins.__import__

    def without_scipy(name, *args, **kwargs):
        if name.startswith("scipy"):
            raise ImportError("simulated unavailable effect")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_scipy)
    path = tmp_path / "keep.svg"
    path.write_bytes(b"previous output")
    with pytest.raises(ImportError, match=r"mudplot\[cluster\]"):
        build().save(str(path))
    assert path.read_bytes() == b"previous output" and not plt.get_fignums()
    assert len(build({"row_cluster": False, "col_cluster": False}).render().axes) == 2


def test_new_matrix_values_recompute_orders_without_stale_derived_columns():
    p = build()
    first = vars(p.render().axes[0])["_mudplot_cluster_order"]
    p.matrix("m", MATRIX[::-1])
    second = vars(p.render().axes[0])["_mudplot_cluster_order"]
    assert second["rows"] != first["rows"]
    assert p.spec.data.matrices["m"] == MATRIX[::-1]
    assert len(p.spec.data.matrices) == 1


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_cluster_exports_actions_schema_and_global_rng(tmp_path, extension):
    state = np.random.get_state()
    p = build({"optimal_ordering": True}, {"annot": True})
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    first, second = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(first)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(second)))
    assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_core_schema_editor_and_old_cluster_defaults():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = build(heatmap={"annot": True})
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.store.state == p.spec and b"<svg" in session.export("svg")
    raw = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").spec.to_dict()
    del raw["panels"][0]["layers"][0]["cluster"]
    assert mp.FigureSpec.from_dict(raw).panels[0].layers[0].cluster is None


@pytest.mark.parametrize(
    "method,metric",
    [
        ("single", "cityblock"),
        ("complete", "euclidean"),
        ("average", "cosine"),
        ("average", "correlation"),
        ("ward", "euclidean"),
    ],
)
def test_computed_orders_match_independent_linkages_across_supported_metrics(
    method, metric
):
    from scipy.cluster.hierarchy import leaves_list, linkage

    result = cluster_summary(MATRIX, mp.ClusterSpec(method=method, metric=metric))
    np.testing.assert_array_equal(
        result.rows, leaves_list(linkage(MATRIX, method=method, metric=metric))
    )


def test_optimal_ordering_also_applies_to_provided_linkages():
    from scipy.cluster.hierarchy import leaves_list, linkage, optimal_leaf_ordering
    from scipy.spatial.distance import pdist

    source = linkage(MATRIX, method="average")
    config = mp.ClusterSpec(row_linkage=source.tolist(), optimal_ordering=True)
    result = cluster_summary(MATRIX, config)
    expected = leaves_list(optimal_leaf_ordering(source, pdist(MATRIX)))
    np.testing.assert_array_equal(result.rows, expected)


def test_clustering_core_does_not_import_optional_packages():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot().matrix('m',[[1,2],[3,4]]).clustermap('m'); "
        "assert m.validate(p.spec)==[] and m.apply(p.action_log)==p.spec; "
        "assert m.Plot.from_json(p.to_json()).spec==p.spec; "
        "assert 'numpy' not in sys.modules and 'scipy' not in sys.modules "
        "and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)
