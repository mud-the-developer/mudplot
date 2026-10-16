"""Pure hierarchical-heatmap contracts; SciPy is an optional effect only."""

from __future__ import annotations

from dataclasses import replace

from ._components import _color
from ._ecdf import finite_number
from ._heatmap import heatmap_issues
from .spec import ClusterSpec, HeatmapSpec

CLUSTER_METHODS = (
    "single",
    "complete",
    "average",
    "weighted",
    "centroid",
    "median",
    "ward",
)
CLUSTER_METRICS = ("euclidean", "cityblock", "cosine", "correlation")
MAX_CLUSTER_DIMENSION = 512


def linkage_issues(linkage, size):
    if linkage is None:
        return []
    if not isinstance(linkage, (list, tuple)) or len(linkage) != size - 1:
        return ["linkage must have n-1 rows of [left,right,distance,count]"]
    available = dict.fromkeys(range(size), 1)
    for index, row in enumerate(linkage):
        if (
            not isinstance(row, (list, tuple))
            or len(row) != 4
            or any(not finite_number(value) for value in row)
        ):
            return ["linkage rows require four finite numeric values"]
        a, b, distance, count = row
        if (
            a != int(a)
            or b != int(b)
            or a == b
            or a not in available
            or b not in available
        ):
            return [
                "linkage nodes must reference distinct unconsumed previous clusters"
            ]
        expected = available.pop(a) + available.pop(b)
        if distance < 0 or count != expected:
            return [
                "linkage distances must be nonnegative and counts match merged leaves"
            ]
        available[size + index] = expected
    return []


def cluster_issues(matrix, layer, panel, spec):
    config = ClusterSpec() if layer.cluster is None else layer.cluster
    display = HeatmapSpec() if layer.heatmap is None else layer.heatmap
    issues = heatmap_issues(matrix, replace(layer, heatmap=display), panel)
    if not isinstance(config, ClusterSpec):
        return [*issues, "cluster must be ClusterSpec or None"]
    if config.method not in CLUSTER_METHODS:
        issues.append("unsupported clustering linkage method")
    if config.metric not in CLUSTER_METRICS:
        issues.append("unsupported clustering distance metric")
    if config.method in ("ward", "centroid", "median") and config.metric != "euclidean":
        issues.append("ward/centroid/median require Euclidean distance")
    for name in ("row_cluster", "col_cluster", "optimal_ordering"):
        if type(getattr(config, name)) is not bool:
            issues.append(f"cluster {name} must be boolean")
    for name in ("z_score", "standard_scale"):
        if getattr(config, name) not in (None, "row", "col"):
            issues.append(f"cluster {name} must be row/col/None")
    if config.z_score is not None and config.standard_scale is not None:
        issues.append("z_score and standard_scale are mutually exclusive")
    if (
        isinstance(display, HeatmapSpec)
        and display.norm == "log"
        and (config.z_score is not None or config.standard_scale is not None)
    ):
        issues.append("log display cannot combine with cluster standardization")
    if (
        not finite_number(config.dendrogram_ratio)
        or not 0.05 <= config.dendrogram_ratio <= 0.5
    ):
        issues.append("dendrogram_ratio must be finite in [0.05,0.5]")
    if not finite_number(config.tree_width) or not 0 <= config.tree_width <= 10:
        issues.append("cluster tree_width must be finite in [0,10] points")
    if not _color(config.tree_color):
        issues.append("cluster tree_color must be a supported colour")
    if (
        len(panel.layers) != 1
        or panel.y2 is not None
        or panel.projection != "2d"
        or panel.filters
        or panel.dropna
    ):
        issues.append("clustermap requires its own primary unfiltered Cartesian panel")
    if (
        spec.share_x != "none"
        or spec.share_y != "none"
        or panel.x.share_id is not None
        or panel.y.share_id is not None
        or panel.x.limits is not None
        or panel.y.limits is not None
    ):
        issues.append("clustered cell axes do not support sharing or cropped limits")
    if (
        not isinstance(matrix, (list, tuple))
        or not matrix
        or any(not isinstance(row, (list, tuple)) or not row for row in matrix)
        or len({len(row) for row in matrix}) != 1
    ):
        return issues
    rows, cols = len(matrix), len(matrix[0])
    if max(rows, cols) > MAX_CLUSTER_DIMENSION:
        issues.append(f"clustermap dimensions are capped at {MAX_CLUSTER_DIMENSION}")
    for name, size in (("row", rows), ("col", cols)):
        linkage = getattr(config, name + "_linkage")
        if linkage is not None and not getattr(config, name + "_cluster"):
            issues.append(f"{name}_linkage requires {name}_cluster=True")
        issues.extend(f"{name}: {problem}" for problem in linkage_issues(linkage, size))
        colors = getattr(config, name + "_colors")
        if colors is not None and (
            not isinstance(colors, (list, tuple))
            or len(colors) != size
            or any(not _color(value) for value in colors)
        ):
            issues.append(f"{name}_colors requires one supported colour per item")
    transform = config.z_score or config.standard_scale
    if transform in ("row", "col"):
        vectors = matrix if transform == "row" else zip(*matrix, strict=True)
        if any(all(value == vector[0] for value in vector) for vector in vectors):
            issues.append("constant axes cannot be standardized")
    return issues
