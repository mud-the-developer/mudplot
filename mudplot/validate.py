"""Pure spec validation: catch mistakes early with clear, agent-friendly errors.

Returns a list of human-readable issue strings instead of raising, so callers
(agents, dashboards, tests) can decide whether to warn or abort. ``render()``
uses this to fail fast with a helpful message instead of a raw ``KeyError``.
"""

from __future__ import annotations

from .capabilities import LAYER_TYPES
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
_COLUMN_FIELDS = ("x", "y", "y2", "yerr", "xerr", "group", "c")
_NO_COLUMN_TYPES = {"hline", "vline", "text", "annotate", "heatmap"}
_VALID_SPINE_CHARS = set("LRTB")
_POINT_TYPES = {"text", "annotate"}  # layers whose ``at``/``to`` is [x, y]


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


def validate(spec: FigureSpec) -> list[str]:
    """Return a list of problems found in ``spec`` (empty = valid)."""
    issues: list[str] = []
    cols = spec.data.columns

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
    if spec.layout:
        rows, colsn = spec.layout
        if rows * colsn < n_panels:
            issues.append(
                f"layout {rows}x{colsn} has {rows * colsn} slots but there are "
                f"{n_panels} panels"
            )
        if spec.width_ratios and len(spec.width_ratios) != colsn:
            issues.append(
                f"width_ratios has {len(spec.width_ratios)} entries, expected {colsn}"
            )
        if spec.height_ratios and len(spec.height_ratios) != rows:
            issues.append(
                f"height_ratios has {len(spec.height_ratios)} entries, expected {rows}"
            )

    for pi, panel in enumerate(spec.panels):
        where_axis = f"panel {pi}"
        if panel.x.scale not in _AXIS_SCALES:
            issues.append(f"{where_axis}: invalid x scale {panel.x.scale!r}")
        if panel.y.scale not in _AXIS_SCALES:
            issues.append(f"{where_axis}: invalid y scale {panel.y.scale!r}")
        if panel.legend.location not in _LEGEND_LOCS:
            issues.append(
                f"{where_axis}: unknown legend location {panel.legend.location!r}"
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
            # x/y/y2/yerr/xerr/group/c hold column *names* for series-like
            # layers; a few layer types don't reference columns at all
            if layer.type not in _NO_COLUMN_TYPES:
                for col_field in _COLUMN_FIELDS:
                    val = getattr(layer, col_field, None)
                    if val:
                        _check_column(cols, val, where, issues)

            if layer.type == "heatmap" and layer.matrix not in spec.data.matrices:
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

            uses_cmap = layer.type == "heatmap" or (
                layer.type == "scatter" and layer.c is not None
            )
            if uses_cmap and layer.cmap_kind not in _CMAP_KINDS:
                issues.append(f"{where}: invalid cmap_kind {layer.cmap_kind!r}")

            if layer.type in _POINT_TYPES:
                _check_point(layer, "at", where, issues)
                _check_point(layer, "to", where, issues)

            if not (0.0 <= layer.alpha <= 1.0):
                issues.append(f"{where}: alpha {layer.alpha!r} must be in [0, 1]")

    return issues


def assert_valid(spec: FigureSpec) -> None:
    """Raise ``ValueError`` with all issues joined, if any."""
    issues = validate(spec)
    if issues:
        bullet = "\n  - ".join(issues)
        raise ValueError(f"invalid FigureSpec:\n  - {bullet}")
