"""Pure hierarchical-heatmap contracts; SciPy is an optional effect only."""

from __future__ import annotations

from dataclasses import replace

from ._components import _color
from ._ecdf import finite_number
from ._heatmap import heatmap_issues
from ._semantics import MAX_LEVELS
from .spec import (
    ClusterCutSpec,
    ClusterSpec,
    ClusterTrackLevelSpec,
    ClusterTrackSpec,
    CondensedDistanceSpec,
    HeatmapSpec,
)

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
EUCLIDEAN_METHODS = ("ward", "centroid", "median")
ADVANCED_FIELDS = (
    "missing",
    "row_distances",
    "col_distances",
    "row_cut",
    "col_cut",
    "row_tracks",
    "col_tracks",
    "row_dendrogram_ratio",
    "col_dendrogram_ratio",
    "track_legend_side",
)


def advanced_cluster(config):
    return isinstance(config, ClusterSpec) and any(
        getattr(config, name) is not None for name in ADVANCED_FIELDS
    )


def _text(value, limit=512):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _track_issues(tracks, size):
    if tracks is None:
        return []
    if not isinstance(tracks, (tuple, list)):
        return ["tracks must be an ordered array"]
    ids = set()
    for track in tracks:
        if not isinstance(track, ClusterTrackSpec):
            return ["tracks require ClusterTrackSpec entries"]
        if not _text(track.id, 64) or track.id in ids or not _text(track.title):
            return ["track needs a unique nonblank id <=64 and title <=512"]
        ids.add(track.id)
        if track.ratio is not None and (
            not finite_number(track.ratio) or not 0 < track.ratio <= 0.5
        ):
            return ["track ratio must be finite in (0,0.5]"]
        if track.legend is not None and type(track.legend) is not bool:
            return ["track legend must be boolean"]
        if (
            not isinstance(track.levels, (tuple, list))
            or not 1 <= len(track.levels) <= MAX_LEVELS
        ):
            return [f"track levels require 1..{MAX_LEVELS} entries"]
        keys, labels, colors = set(), set(), set()
        for level in track.levels:
            if (
                not isinstance(level, ClusterTrackLevelSpec)
                or not (_text(level.key) and _text(level.label) and _color(level.color))
                or level.color == "none"
            ):
                return [
                    "track level needs a bounded key, label and "
                    "visible supported colour"
                ]
            if level.key in keys or level.label in labels or level.color in colors:
                return ["track levels must have distinct keys, labels and colours"]
            keys.add(level.key)
            labels.add(level.label)
            colors.add(level.color)
        if (
            not isinstance(track.values, (tuple, list))
            or len(track.values) != size
            or any(not isinstance(key, str) or key not in keys for key in track.values)
        ):
            return ["track values must map every original position to a declared level"]
    return []


def _axis_issues(config, name, size):
    issues = []
    enabled = getattr(config, name + "_cluster")
    links = getattr(config, name + "_linkage")
    distances = getattr(config, name + "_distances")
    if distances is not None:
        count = size * (size - 1) // 2
        if not enabled or size < 2:
            issues.append("distances require an enabled multi-item tree")
        elif not isinstance(distances, CondensedDistanceSpec) or not (
            _text(distances.label)
            and isinstance(distances.values, (tuple, list))
            and len(distances.values) == count
            and all(finite_number(v) and v >= 0 for v in distances.values)
        ):
            issues.append(
                f"distances need a label and {count} finite "
                "nonnegative condensed values"
            )
        if links is not None:
            if not config.optimal_ordering:
                issues.append(
                    "distances with supplied linkage require optimal_ordering"
                )
        elif config.method in EUCLIDEAN_METHODS:
            issues.append(
                "ward/centroid/median cannot build from external dissimilarities"
            )
    cut = getattr(config, name + "_cut")
    if cut is not None:
        if not enabled or size < 2:
            issues.append("cut requires an enabled multi-item tree")
        elif (
            not isinstance(cut, ClusterCutSpec)
            or not finite_number(cut.height)
            or cut.height < 0
        ):
            issues.append("cut height must be finite and nonnegative")
        elif cut.anchor is not None and (
            type(cut.anchor) is not int or not 0 <= cut.anchor < size
        ):
            issues.append("cut anchor must be an original item index")
    ratio = getattr(config, name + "_dendrogram_ratio")
    if ratio is not None and (not finite_number(ratio) or not 0.05 <= ratio <= 0.5):
        issues.append("dendrogram ratio must be finite in [0.05,0.5]")
    issues.extend(_track_issues(getattr(config, name + "_tracks"), size))
    return [f"{name}: {issue}" for issue in issues]


def common_features(matrix, name):
    """Observed original feature indices shared by all items of one axis."""
    features = zip(*matrix, strict=True) if name == "row" else matrix
    return tuple(j for j, values in enumerate(features) if None not in values)


def named_fit(config, name, size):
    return (
        size > 1
        and getattr(config, name + "_cluster")
        and getattr(config, name + "_distances") is None
        and (getattr(config, name + "_linkage") is None or config.optimal_ordering)
    )


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
    if not isinstance(config, ClusterSpec):
        return [
            *heatmap_issues(matrix, replace(layer, heatmap=display), panel),
            "cluster must be ClusterSpec or None",
        ]
    nullable = config.missing == "complete_features"
    issues = heatmap_issues(
        matrix, replace(layer, heatmap=display), panel, nullable=nullable
    )
    if config.missing not in (None, "complete_features"):
        issues.append("cluster missing must be complete_features or omitted")
    if config.track_legend_side not in (None, "right", "bottom"):
        issues.append("track_legend_side must be right or bottom")
    if config.method not in CLUSTER_METHODS:
        issues.append("unsupported clustering linkage method")
    if config.metric not in CLUSTER_METRICS:
        issues.append("unsupported clustering distance metric")
    if config.method in EUCLIDEAN_METHODS and config.metric != "euclidean":
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
        issues.extend(_axis_issues(config, name, size))
        if (
            nullable
            and named_fit(config, name, size)
            and not common_features(matrix, name)
        ):
            issues.append(f"{name}: cluster metric has no common observed features")
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
        for vector in vectors:
            observed = (value for value in vector if not nullable or value is not None)
            first = next(observed, None)
            if all(value == first for value in observed):
                issues.append(
                    "constant or insufficient axes cannot be standardized"
                    if nullable
                    else "constant axes cannot be standardized"
                )
                break
    return issues
