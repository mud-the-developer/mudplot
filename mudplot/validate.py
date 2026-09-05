"""Pure spec validation: catch mistakes early with clear, agent-friendly errors.

Returns a list of human-readable issue strings instead of raising, so callers
(agents, dashboards, tests) can decide whether to warn or abort. ``render()``
uses this to fail fast with a helpful message instead of a raw ``KeyError``.
"""

from __future__ import annotations

import math
from numbers import Real

from .capabilities import LAYER_TYPES, PALETTE_PRESETS
from .spec import FigureSpec

__all__ = ["assert_valid", "validate"]

_AXIS_SCALES = {"linear", "log"}
_LEGEND_LOCS = {
    "best",
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
    "outside right",
    "outside top",
    "outside bottom",
}
_SHARE_MODES = {"none", "all", "row", "col"}
_CMAP_KINDS = {"sequential", "diverging"}
_LAYER_AXES = {"y", "y2"}
# layer types whose renderer actually honours ``layer.axis`` (routes to the
# secondary y-axis); hist/box/heatmap always draw on the primary axes only.
_AXIS_ROUTABLE_TYPES = {
    "line",
    "scatter",
    "bar",
    "errorbar",
    "band",
    "hline",
    "vline",
    "text",
    "annotate",
}
_COLUMN_FIELDS = ("x", "y", "y2", "yerr", "xerr", "group", "c", "z")
_NO_COLUMN_TYPES = {
    "hline",
    "vline",
    "text",
    "annotate",
    "heatmap",
    "contour",
    "contourf",
    "surface",
    "wireframe",
}
_VALID_SPINE_CHARS = set("LRTB")
_POINT_TYPES = {"text", "annotate"}  # layers whose ``at``/``to`` is [x, y]
_MATRIX_LAYER_TYPES = {"heatmap", "contour", "contourf", "surface", "wireframe"}
_CMAP_LAYER_TYPES = {"heatmap", "contour", "contourf", "surface"}
_PROJECTIONS = {"2d", "3d"}
# layer types that only make sense on a projection="3d" panel
_3D_ONLY_TYPES = {"scatter3d", "line3d", "surface", "wireframe"}


def _check_column(cols: dict, name: str | None, where: str, issues: list[str]):
    if name is None:
        return
    if name not in cols:
        issues.append(
            f"{where}: column {name!r} not found in data (available: {sorted(cols)})"
        )


def _check_data_integrity(spec: FigureSpec, issues: list[str]) -> None:
    """All columns (and each matrix's rows) must be row-aligned in length.

    A mudplot figure treats ``data.columns`` as one implicit table; silently
    mismatched lengths would otherwise surface as confusing numpy broadcast
    errors (or, worse, silently misaligned data) deep inside rendering.
    """
    cols = spec.data.columns
    if cols:
        lengths = {name: len(vals) for name, vals in cols.items()}
        distinct = set(lengths.values())
        if len(distinct) > 1:
            issues.append(f"data.columns have mismatched lengths: {lengths}")

    for name, matrix in spec.data.matrices.items():
        row_lengths = {len(row) for row in matrix}
        if len(row_lengths) > 1:
            issues.append(
                f"data.matrices[{name!r}] has jagged rows (lengths: "
                f"{sorted(row_lengths)})"
            )


def _check_point(layer, field_name: str, where: str, issues: list[str]) -> None:
    val = getattr(layer, field_name, None)
    if val is not None and len(val) != 2:
        issues.append(f"{where}: {field_name!r} must be [x, y] (length 2), got {val!r}")


def _finite(value) -> bool:
    return (
        isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)
    )


def _check_axis(axis, where: str, issues: list[str]) -> None:
    if axis is None:
        return
    if axis.scale not in _AXIS_SCALES:
        issues.append(f"{where}: invalid scale {axis.scale!r}")
    if axis.limits is not None:
        limits = axis.limits
        if (
            not isinstance(limits, (list, tuple))
            or len(limits) != 2
            or not all(_finite(v) for v in limits)
            or limits[0] == limits[1]
        ):
            issues.append(f"{where}: limits must contain two distinct finite numbers")
        elif axis.scale == "log" and any(v <= 0 for v in limits):
            issues.append(f"{where}: log limits must be positive")


def validate(spec: FigureSpec) -> list[str]:
    """Return a list of problems found in ``spec`` (empty = valid)."""
    issues: list[str] = []
    cols = spec.data.columns

    if (
        not isinstance(spec.size, (list, tuple))
        or len(spec.size) != 2
        or not all(_finite(v) and v > 0 for v in spec.size)
    ):
        issues.append("size must contain two positive finite numbers")
    if not _finite(spec.dpi) or spec.dpi <= 0:
        issues.append("dpi must be a positive finite number")
    if spec.theme.redundant_encoding and (
        not spec.theme.markers or not spec.theme.line_styles or not spec.theme.hatches
    ):
        issues.append(
            "redundant encoding requires non-empty markers, line_styles and hatches"
        )
    if (
        spec.theme.palette.preset is not None
        and spec.theme.palette.preset not in PALETTE_PRESETS
    ):
        issues.append(
            f"unknown palette preset {spec.theme.palette.preset!r}; "
            f"choose from {sorted(PALETTE_PRESETS)}"
        )

    if not spec.panels:
        issues.append("figure has no panels (spec.panels is empty)")

    if spec.share_x not in _SHARE_MODES:
        issues.append(
            f"invalid share_x {spec.share_x!r}; valid: {sorted(_SHARE_MODES)}"
        )
    if spec.share_y not in _SHARE_MODES:
        issues.append(
            f"invalid share_y {spec.share_y!r}; valid: {sorted(_SHARE_MODES)}"
        )

    bad_spine_chars = set(spec.theme.axes.spines) - _VALID_SPINE_CHARS
    if bad_spine_chars:
        issues.append(
            f"theme.axes.spines {spec.theme.axes.spines!r} has invalid "
            f"character(s) {sorted(bad_spine_chars)}; valid: L, R, T, B"
        )

    _check_data_integrity(spec, issues)

    n_panels = len(spec.panels)
    rows, colsn = 1, n_panels
    if spec.layout is not None:
        if (
            not isinstance(spec.layout, (list, tuple))
            or len(spec.layout) != 2
            or any(type(v) is not int or v <= 0 for v in spec.layout)
        ):
            issues.append("layout must contain two positive integers")
        else:
            rows, colsn = spec.layout
            if rows * colsn < n_panels:
                issues.append(
                    f"layout {rows}x{colsn} has {rows * colsn} slots but there are "
                    f"{n_panels} panels"
                )
    for name, expected in (("width_ratios", colsn), ("height_ratios", rows)):
        ratios = getattr(spec, name)
        if ratios is not None and (
            not isinstance(ratios, (list, tuple))
            or len(ratios) != expected
            or not all(_finite(v) and v > 0 for v in ratios)
        ):
            issues.append(f"{name} must contain {expected} positive finite entries")

    for pi, panel in enumerate(spec.panels):
        where_axis = f"panel {pi}"
        for name in ("x", "y", "y2", "z"):
            _check_axis(getattr(panel, name), f"{where_axis} {name}", issues)
        if panel.projection == "3d" and panel.y2 is not None:
            issues.append(f"{where_axis}: secondary y-axis is not supported in 3-D")
        if panel.legend.location not in _LEGEND_LOCS:
            issues.append(
                f"{where_axis}: unknown legend location {panel.legend.location!r}"
            )
        bta = panel.legend.bbox_to_anchor
        if bta is not None and (len(bta) != 2 or not all(_finite(v) for v in bta)):
            issues.append(
                f"{where_axis}: legend bbox_to_anchor must be [x, y] finite numbers, "
                f"got {bta!r}"
            )
        if panel.projection not in _PROJECTIONS:
            issues.append(
                f"{where_axis}: invalid projection {panel.projection!r}; "
                f"valid: {sorted(_PROJECTIONS)}"
            )
        if panel.z is not None and panel.projection != "3d":
            issues.append(
                f"{where_axis}: z-axis is configured but projection is "
                f'{panel.projection!r} (z only applies to "3d" panels)'
            )

        for li, layer in enumerate(panel.layers):
            where = f"panel {pi} layer {li} ({layer.type})"
            if layer.type not in LAYER_TYPES:
                issues.append(
                    f"{where}: unknown layer type; valid: {sorted(LAYER_TYPES)}"
                )
                continue
            required = LAYER_TYPES[layer.type]["required"]
            for field_name in required:
                val = getattr(layer, field_name, None)
                if val in (None, ""):
                    issues.append(f"{where}: missing required field {field_name!r}")

            if layer.type in _3D_ONLY_TYPES and panel.projection != "3d":
                issues.append(
                    f"{where}: {layer.type!r} requires panel.projection == "
                    f'"3d" (this panel is {panel.projection!r})'
                )
            elif panel.projection == "3d" and layer.type not in _3D_ONLY_TYPES:
                issues.append(
                    f"{where}: {layer.type!r} is not a 3-D layer type; a "
                    f'"3d" panel only supports {sorted(_3D_ONLY_TYPES)}'
                )
            # x/y/y2/yerr/xerr/group/c hold column *names* for series-like
            # layers; a few layer types don't reference columns at all
            if layer.type not in _NO_COLUMN_TYPES:
                for col_field in _COLUMN_FIELDS:
                    val = getattr(layer, col_field, None)
                    if val:
                        _check_column(cols, val, where, issues)

            if (
                layer.type in _MATRIX_LAYER_TYPES
                and layer.matrix not in spec.data.matrices
            ):
                issues.append(
                    f"{where}: matrix {layer.matrix!r} not found in data "
                    f"(available: {sorted(spec.data.matrices)})"
                )

            if layer.axis not in _LAYER_AXES:
                issues.append(f"{where}: invalid axis {layer.axis!r}")
            elif layer.axis == "y2":
                if layer.type not in _AXIS_ROUTABLE_TYPES:
                    issues.append(
                        f"{where}: axis='y2' is not supported for {layer.type!r} "
                        f"layers (only {sorted(_AXIS_ROUTABLE_TYPES)} route to "
                        "the secondary axis)"
                    )
                elif panel.y2 is None:
                    issues.append(
                        f"{where}: routes to y2 but panel {pi} has no secondary "
                        "axis (use .secondary_yaxis(...))"
                    )

            uses_cmap = layer.type in _CMAP_LAYER_TYPES or (
                layer.type in {"scatter", "scatter3d"} and layer.c is not None
            )
            if uses_cmap and layer.cmap_kind not in _CMAP_KINDS:
                issues.append(f"{where}: invalid cmap_kind {layer.cmap_kind!r}")

            if layer.type in _POINT_TYPES:
                _check_point(layer, "at", where, issues)
                _check_point(layer, "to", where, issues)

            if not _finite(layer.alpha) or not (0.0 <= layer.alpha <= 1.0):
                issues.append(f"{where}: alpha {layer.alpha!r} must be in [0, 1]")

    return issues


def assert_valid(spec: FigureSpec) -> None:
    """Raise ``ValueError`` with all issues joined, if any."""
    issues = validate(spec)
    if issues:
        bullet = "\n  - ".join(issues)
        raise ValueError(f"invalid FigureSpec:\n  - {bullet}")
