"""Dependency-free contracts for opt-in matrix display controls."""

from __future__ import annotations

from ._components import _color
from ._ecdf import finite_number
from ._stat import LABEL_FORMATS
from .spec import HeatmapSpec

MAX_HEATMAP_ANNOTATIONS = 4096


def heatmap_issues(matrix, layer, panel):
    config = layer.heatmap
    if config is None:
        return (
            ["heatmap cell borders require HeatmapSpec"]
            if layer.line_width is not None or layer.edge_color is not None
            else []
        )
    if not isinstance(config, HeatmapSpec):
        return ["heatmap must be HeatmapSpec or None"]
    issues = []
    if config.norm not in ("linear", "log"):
        issues.append("heatmap norm must be linear or log")
    for name in ("vmin", "vmax", "center"):
        value = getattr(config, name)
        if value is not None and not finite_number(value):
            issues.append(f"heatmap {name} must be finite numeric or None")
    if (
        config.vmin is not None
        and config.vmax is not None
        and finite_number(config.vmin)
        and finite_number(config.vmax)
        and config.vmin >= config.vmax
    ):
        issues.append("heatmap vmin must be smaller than vmax")
    for name in ("robust", "annot", "square"):
        if type(getattr(config, name)) is not bool:
            issues.append(f"heatmap {name} must be boolean")
    if config.fmt not in LABEL_FORMATS:
        issues.append("heatmap fmt must use the bounded numeric-format whitelist")
    if config.center is not None:
        if config.norm != "linear" or layer.cmap_kind != "diverging":
            issues.append("heatmap center requires linear norm and diverging palette")
        if finite_number(config.center):
            if (
                config.vmin is not None
                and finite_number(config.vmin)
                and config.vmin >= config.center
            ):
                issues.append("heatmap center must be greater than vmin")
            if (
                config.vmax is not None
                and finite_number(config.vmax)
                and config.vmax <= config.center
            ):
                issues.append("heatmap center must be smaller than vmax")
    if panel.x.scale != "linear" or panel.y.scale != "linear":
        issues.append(
            "typed heatmap cell axes must be linear; norm controls colour scale"
        )
    if layer.line_width is not None and (
        not finite_number(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append("heatmap line_width must be finite in [0,1000] points")
    if layer.edge_color is not None and not _color(layer.edge_color):
        issues.append("heatmap edge_color must be a supported colour")

    if (
        not isinstance(matrix, (list, tuple))
        or not matrix
        or any(not isinstance(row, (list, tuple)) or not row for row in matrix)
        or len({len(row) for row in matrix}) != 1
    ):
        return [*issues, "typed heatmap requires a nonempty rectangular matrix"]
    rows, cols = len(matrix), len(matrix[0])
    if any(not finite_number(value) for row in matrix for value in row):
        issues.append("typed heatmap matrix must contain finite numeric values")
    mask = config.mask
    if mask is not None and (
        not isinstance(mask, (list, tuple))
        or len(mask) != rows
        or any(
            not isinstance(row, (list, tuple))
            or len(row) != cols
            or any(type(value) is not bool for value in row)
            for row in mask
        )
    ):
        return [*issues, "heatmap mask must be a same-shaped boolean matrix"]
    visible = [
        value
        for i, row in enumerate(matrix)
        for j, value in enumerate(row)
        if mask is None or not mask[i][j]
    ]
    if not visible:
        issues.append("heatmap needs at least one unmasked value")
    if config.annot and len(visible) > MAX_HEATMAP_ANNOTATIONS:
        issues.append(f"heatmap annot supports at most {MAX_HEATMAP_ANNOTATIONS} cells")
    if config.norm == "log":
        if any(finite_number(v) and v <= 0 for v in visible):
            issues.append("log heatmap requires positive unmasked values")
        if any(
            v is not None and finite_number(v) and v <= 0
            for v in (config.vmin, config.vmax)
        ):
            issues.append("log heatmap bounds must be positive")
    for name, expected in (("xlabels", cols), ("ylabels", rows)):
        labels = getattr(config, name)
        if labels is not None and (
            not isinstance(labels, (list, tuple))
            or len(labels) != expected
            or any(not isinstance(value, str) or len(value) > 512 for value in labels)
        ):
            issues.append(
                f"heatmap {name} needs {expected} strings of at most 512 characters"
            )
    return issues
