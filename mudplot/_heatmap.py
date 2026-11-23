"""Dependency-free contracts for opt-in matrix display controls."""

from __future__ import annotations

from itertools import pairwise

from ._axis_options import MAX_TICKS_PER_LEVEL
from ._components import _color
from ._ecdf import finite_number
from ._stat import LABEL_FORMATS
from .spec import ColorbarOptionsSpec, HeatmapSpec

MAX_HEATMAP_ANNOTATIONS = 4096
HEATMAP_NORMS = ("linear", "log", "symlog", "power", "boundary")
COLORBAR_LOCATIONS = ("left", "right", "top", "bottom")


def linear_constant_bounds(value):
    """The existing five-percent display pad (half a unit at zero)."""
    padding = abs(value) * 0.05 or 0.5
    return value - padding, value + padding


def advanced_heatmap(config):
    return isinstance(config, HeatmapSpec) and (
        config.norm not in ("linear", "log") or config.colorbar_options is not None
    )


def _increasing(values, minimum):
    return (
        isinstance(values, (list, tuple))
        and minimum <= len(values) <= MAX_TICKS_PER_LEVEL
        and all(finite_number(v) for v in values)
        and all(a < b for a, b in pairwise(values))
    )


def _colour_options_issues(config):
    issues = []
    for name, family in (("linthresh", "symlog"), ("gamma", "power")):
        value = getattr(config, name)
        if config.norm == family:
            if not finite_number(value) or value <= 0:
                issues.append(f"heatmap {family} needs finite positive {name}")
        elif value is not None:
            issues.append(f"heatmap {name} requires {family} norm")
    if config.norm == "boundary":
        if not _increasing(config.boundaries, 2):
            issues.append(
                f"heatmap boundaries need 2..{MAX_TICKS_PER_LEVEL} "
                "increasing finite edges"
            )
        if config.robust or any(
            v is not None for v in (config.vmin, config.vmax, config.center)
        ):
            issues.append("boundary norm excludes robust, vmin, vmax and center")
    elif config.boundaries is not None:
        issues.append("heatmap boundaries require boundary norm")
    bar = config.colorbar_options
    return issues + colorbar_options_issues(
        bar,
        norm=config.norm,
        boundaries=config.boundaries,
        vmin=config.vmin,
        vmax=config.vmax,
    )


def colorbar_options_issues(bar, *, norm, boundaries, vmin, vmax, scalar=False):
    issues = []
    if bar is None:
        return issues
    if not isinstance(bar, ColorbarOptionsSpec):
        return ["colourbar options must be ColorbarOptionsSpec"]
    if bar.extend is not None and (
        not scalar or bar.extend not in ("neither", "min", "max", "both")
    ):
        issues.append("colourbar extend requires scalar_display and a named extension")
    if bar.location is not None and bar.location not in COLORBAR_LOCATIONS:
        issues.append("colourbar location must be left/right/top/bottom")
    if bar.tick_format is not None and bar.tick_format not in LABEL_FORMATS:
        issues.append(
            "colourbar tick_format must use the bounded numeric-format whitelist"
        )
    if bar.fraction is not None and (
        not finite_number(bar.fraction) or not 0 < bar.fraction <= 0.5
    ):
        issues.append("colourbar fraction must be finite in (0,0.5]")
    if bar.pad is not None and (not finite_number(bar.pad) or not 0 <= bar.pad <= 0.5):
        issues.append("colourbar pad must be finite in [0,0.5]")
    if bar.ticks is not None:
        if not _increasing(bar.ticks, 1):
            issues.append(
                f"colourbar ticks need 1..{MAX_TICKS_PER_LEVEL} "
                "increasing finite values"
            )
        elif norm == "boundary" and _increasing(boundaries, 2):
            edges = set(boundaries)
            if any(tick not in edges for tick in bar.ticks):
                issues.append("boundary colourbar ticks must be declared edges")
        elif (
            (finite_number(vmin) and bar.ticks[0] < vmin)
            or (finite_number(vmax) and bar.ticks[-1] > vmax)
            or (norm == "log" and bar.ticks[0] <= 0)
        ):
            issues.append("colourbar ticks must be in the display-value domain")
    return issues


def heatmap_issues(matrix, layer, panel, *, nullable=False):
    config = layer.heatmap
    if config is None:
        return (
            ["heatmap cell borders require HeatmapSpec"]
            if layer.line_width is not None or layer.edge_color is not None
            else []
        )
    if not isinstance(config, HeatmapSpec):
        return ["heatmap must be HeatmapSpec or None"]
    issues = _colour_options_issues(config)
    if config.norm not in HEATMAP_NORMS:
        issues.append(f"heatmap norm must be one of {HEATMAP_NORMS}")
    for name in ("vmin", "vmax", "center"):
        value = getattr(config, name)
        if value is not None and not finite_number(value):
            issues.append(f"heatmap {name} must be finite numeric or None")
    for name in ("xrotation", "yrotation"):
        value = getattr(config, name)
        if value is not None and (not finite_number(value) or not -360 <= value <= 360):
            issues.append(f"heatmap {name} must be finite in [-360,360] degrees")
    if config.annot_data is not None and config.annot is not True:
        issues.append("heatmap annot_data requires annot=True")
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
    annotations = config.annot_data
    if annotations is not None and (
        not isinstance(annotations, list)
        or len(annotations) != rows
        or any(
            not isinstance(row, list)
            or len(row) != cols
            or any(not isinstance(value, str) or len(value) > 512 for value in row)
            for row in annotations
        )
    ):
        issues.append(
            "heatmap annot_data must be a same-shaped matrix of strings "
            "of at most 512 characters"
        )
    if any(
        not finite_number(value) and not (nullable and value is None)
        for row in matrix
        for value in row
    ):
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
    visible = 0
    invalid_log = False
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if (nullable and value is None) or (mask is not None and mask[i][j]):
                continue
            visible += 1
            if config.norm == "log" and finite_number(value) and value <= 0:
                invalid_log = True
    if not visible and layer.scalar_display is None:
        issues.append("heatmap needs at least one unmasked value")
    if config.annot and visible > MAX_HEATMAP_ANNOTATIONS:
        issues.append(f"heatmap annot supports at most {MAX_HEATMAP_ANNOTATIONS} cells")
    if config.norm == "log":
        if invalid_log:
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
