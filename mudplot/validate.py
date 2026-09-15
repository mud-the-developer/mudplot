"""Pure spec validation: catch mistakes early with clear, agent-friendly errors.

Returns a list of human-readable issue strings instead of raising, so callers
(agents, dashboards, tests) can decide whether to warn or abort. ``render()``
uses this to fail fast with a helpful message instead of a raw ``KeyError``.
"""

from __future__ import annotations

import math
from itertools import pairwise
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
_DRAWSTYLES = {"default", "steps", "steps-pre", "steps-mid", "steps-post"}
# layer types whose renderer actually honours ``layer.axis`` (routes to the
# secondary y-axis); hist/box/heatmap always draw on the primary axes only.
_AXIS_ROUTABLE_TYPES = {
    "line",
    "regplot",
    "scatter",
    "stripplot",
    "stackplot",
    "hist2d",
    "hexbin",
    "quiver",
    "bar",
    "errorbar",
    "band",
    "hline",
    "vline",
    "text",
    "annotate",
}
_COLUMN_FIELDS = (
    "x",
    "y",
    "y2",
    "yerr",
    "xerr",
    "group",
    "c",
    "u",
    "v",
    "z",
)
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
_CMAP_LAYER_TYPES = {
    "heatmap",
    "contour",
    "contourf",
    "surface",
    "hist2d",
    "hexbin",
}
_BIVARIATE_DENSITY_TYPES = {"hist2d", "hexbin"}
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
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _stable_group_indices(values) -> list[tuple[object, list[int]]]:
    # ponytail: equality grouping is O(n²) for all-unique keys; index hashable
    # keys if validation of very large grouped layers becomes a bottleneck.
    groups: list[tuple[object, list[int]]] = []
    for index, key in enumerate(values):
        for existing, indices in groups:
            if key == existing:
                indices.append(index)
                break
        else:
            groups.append((key, [index]))
    return groups


def _check_regression_data(cols, layer, where: str, issues: list[str]) -> None:
    """Check each fitted group before NumPy reaches its linear-algebra path."""
    x_values = cols[layer.x]
    y_values = cols[layer.y]
    if len(x_values) != len(y_values):
        return  # _check_data_integrity reports the shared-table mismatch
    if layer.group is None:
        groups = [(None, list(range(len(x_values))))]
    else:
        group_values = cols[layer.group]
        if len(group_values) != len(x_values):
            return
        groups = _stable_group_indices(group_values)

    if not groups:
        issues.append(f"{where}: regression requires observations")
        return

    for key, indices in groups:
        suffix = f" group {key!r}" if layer.group is not None else ""
        pairs = [(x_values[i], y_values[i]) for i in indices]
        if any(not _finite(value) for pair in pairs for value in pair):
            issues.append(f"{where}{suffix}: regression values must be finite numbers")
            continue
        distinct_x: list[object] = []
        for x, _y in pairs:
            if not any(x == seen for seen in distinct_x):
                distinct_x.append(x)
        parameters = layer.degree + 1
        minimum = parameters + (layer.confidence is not None)
        if len(pairs) < minimum:
            issues.append(
                f"{where}{suffix}: degree {layer.degree} regression requires at "
                f"least {minimum} observations"
            )
        if len(distinct_x) < parameters:
            issues.append(
                f"{where}{suffix}: degree {layer.degree} regression requires at "
                f"least {parameters} distinct x values"
            )


def _check_stackplot_data(cols, layer, where: str, issues: list[str]) -> None:
    """Require every stack to provide finite y values on the same x sequence."""
    x_values = cols[layer.x]
    y_values = cols[layer.y]
    group_values = cols[layer.group]
    if len(x_values) != len(y_values) or len(group_values) != len(x_values):
        return  # _check_data_integrity reports the shared-table mismatch
    groups = _stable_group_indices(group_values)
    if not groups:
        issues.append(f"{where}: stackplot requires observations")
        return

    reference_x = [x_values[i] for i in groups[0][1]]
    for key, indices in groups:
        if any(not _finite(y_values[i]) for i in indices):
            issues.append(f"{where} group {key!r}: stack values must be finite numbers")
        if [x_values[i] for i in indices] != reference_x:
            issues.append(
                f"{where} group {key!r}: every stack must use the same x sequence"
            )


# Reference metadata is substituted verbatim into a .pgf export, which the
# user's LaTeX then compiles -- so these are a trust boundary, not just a
# formatting concern: an unbalanced brace or a stray backslash would inject
# arbitrary markup into their document (and break the build at best).
#
# citation and href get different rules because they land in different
# places: a citation is only ever used as a \figcite{KEY} *argument*, which
# LaTeX uses purely for lookup (never typeset), so ordinary BibTeX-key
# characters like "_"/":"/"-" are fine -- only characters that could break
# out of that argument (braces/backslash/macro-prefix chars) are unsafe.
# href becomes a \href{URL}{...} argument, which hyperref itself reads with
# special "URL-safe" catcodes (the same trick \url uses), so ordinary URL
# punctuation ("_", "&", "#", "%", "?", "~") is fine there too -- only
# braces/backslash (which would break hyperref's own argument scanning) and
# control characters are unsafe.
_CONTROL_CHARS = {chr(i) for i in range(32)} | {"\x7f"}
_CITATION_UNSAFE = set("{}\\%$#&~^") | _CONTROL_CHARS
_HREF_UNSAFE = set("{}\\") | _CONTROL_CHARS


def _check_ref_field(
    field_name: str,
    value: str | None,
    unsafe: set,
    why: str,
    where: str,
    issues: list[str],
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{where}: {field_name} must be a non-empty string")
        return
    bad = sorted(unsafe & set(value))
    if bad:
        issues.append(f"{where}: {field_name} may not contain {''.join(bad)!r} ({why})")


def _check_reference(
    citation: str | None, href: str | None, where: str, issues: list[str]
) -> None:
    _check_ref_field(
        "citation",
        citation,
        _CITATION_UNSAFE,
        "it is used as a BibTeX/\\figcite key argument",
        where,
        issues,
    )
    _check_ref_field(
        "href",
        href,
        _HREF_UNSAFE,
        "it is substituted into a LaTeX \\href{...} argument verbatim",
        where,
        issues,
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
    from .spec import SPEC_VERSION

    issues: list[str] = []
    cols = spec.data.columns

    if spec.version != SPEC_VERSION:
        issues.append(
            f"unknown spec version {spec.version!r}; this mudplot understands "
            f"{SPEC_VERSION!r} (a spec built via FigureSpec.from_dict()/from_json() "
            "would have been migrated or rejected already -- this one was "
            "constructed directly with a mismatched version)"
        )

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

    if spec.reference_measure_text is not None:
        if not spec.reference_measure_text.strip():
            issues.append("reference_measure_text must be a non-empty string")
        else:
            # Stripped back out (with its exact spelling) at PGF-substitution
            # time via a plain-text match against the saved .pgf -- which
            # only works if matplotlib's pgf backend wrote it back out
            # unescaped. Reuse the citation charset (same escaping risk).
            bad = sorted(_CITATION_UNSAFE & set(spec.reference_measure_text))
            if bad:
                issues.append(
                    f"reference_measure_text may not contain {''.join(bad)!r} "
                    "(matplotlib's PGF backend would escape it, breaking the "
                    "plain-text match used to strip it back out)"
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
        _check_reference(
            panel.title_citation, panel.title_href, f"{where_axis} title", issues
        )
        for li, layer in enumerate(panel.layers):
            _check_reference(
                layer.citation, layer.href, f"{where_axis} layer {li}", issues
            )
            if layer.references:
                for key, ref in layer.references.items():
                    _check_reference(
                        ref.citation,
                        ref.href,
                        f"{where_axis} layer {li} reference[{key!r}]",
                        issues,
                    )
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
        tp = panel.title_position
        if tp is not None and (len(tp) != 2 or not all(_finite(v) for v in tp)):
            issues.append(
                f"{where_axis}: title_position must be [x, y] finite numbers, "
                f"got {tp!r}"
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

            if layer.type == "quiver":
                if layer.group is not None:
                    issues.append(f"{where}: group is not supported for quiver")
                u_name, v_name = layer.u, layer.v
                if (
                    layer.x in cols
                    and layer.y in cols
                    and isinstance(u_name, str)
                    and u_name in cols
                    and isinstance(v_name, str)
                    and v_name in cols
                ):
                    values = [
                        *cols[layer.x],
                        *cols[layer.y],
                        *cols[u_name],
                        *cols[v_name],
                    ]
                    if layer.c is not None and layer.c in cols:
                        values.extend(cols[layer.c])
                    if not values:
                        issues.append(f"{where}: quiver requires observations")
                    elif any(not _finite(value) for value in values):
                        issues.append(
                            f"{where}: x/y/u/v/c values must be finite numbers"
                        )
                for name, value in (
                    ("quiver_scale", layer.quiver_scale),
                    ("quiver_width", layer.quiver_width),
                ):
                    if value is not None and (not _finite(value) or value <= 0):
                        issues.append(f"{where}: {name} must be positive or None")
                if layer.colorbar and layer.c is None:
                    issues.append(f"{where}: colorbar requires a c column")

            if layer.type in _BIVARIATE_DENSITY_TYPES:
                if layer.group is not None:
                    issues.append(
                        f"{where}: group is not supported for bivariate density layers"
                    )
                if layer.x in cols and layer.y in cols:
                    values = [*cols[layer.x], *cols[layer.y]]
                    if not values:
                        issues.append(f"{where}: density plot requires observations")
                    elif any(not _finite(value) for value in values):
                        issues.append(f"{where}: x/y values must be finite numbers")
                if layer.type == "hist2d":
                    if type(layer.density) is not bool:
                        issues.append(f"{where}: density must be true or false")
                    bins = layer.bins
                    valid_bins = type(bins) is int and bins > 0
                    if isinstance(bins, list):
                        if len(bins) == 2:
                            valid_bins = all(
                                type(value) is int and value > 0 for value in bins
                            )
                        else:
                            valid_bins = (
                                len(bins) >= 3
                                and all(_finite(value) for value in bins)
                                and all(a < b for a, b in pairwise(bins))
                            )
                    if not valid_bins:
                        issues.append(
                            f"{where}: bins must be a positive integer, a positive "
                            "[x, y] integer pair, or increasing finite edges"
                        )
                else:
                    if type(layer.gridsize) is not int or layer.gridsize <= 0:
                        issues.append(f"{where}: gridsize must be a positive integer")
                    if layer.mincnt is not None and (
                        type(layer.mincnt) is not int or layer.mincnt < 0
                    ):
                        issues.append(
                            f"{where}: mincnt must be a nonnegative integer or None"
                        )

            if (
                layer.type == "stackplot"
                and layer.x in cols
                and layer.y in cols
                and isinstance(layer.group, str)
                and layer.group in cols
            ):
                _check_stackplot_data(cols, layer, where, issues)

            if layer.type == "stripplot":
                jitter = 0.15 if layer.jitter is None else layer.jitter
                if not _finite(jitter) or not (0 <= jitter <= 0.5):
                    issues.append(f"{where}: jitter must be between 0 and 0.5")
            elif layer.jitter is not None:
                issues.append(f"{where}: jitter only applies to stripplot layers")

            if layer.type == "regplot":
                if type(layer.degree) is not int or not (1 <= layer.degree <= 10):
                    issues.append(f"{where}: degree must be an integer from 1 to 10")
                if layer.confidence is not None and (
                    not _finite(layer.confidence) or not (0 < layer.confidence < 100)
                ):
                    issues.append(
                        f"{where}: confidence must be between 0 and 100, or None"
                    )
                if (
                    layer.x in cols
                    and layer.y in cols
                    and (layer.group is None or layer.group in cols)
                    and type(layer.degree) is int
                    and 1 <= layer.degree <= 10
                ):
                    _check_regression_data(cols, layer, where, issues)

            if layer.drawstyle not in _DRAWSTYLES:
                issues.append(
                    f"{where}: invalid drawstyle {layer.drawstyle!r}; "
                    f"valid: {sorted(_DRAWSTYLES)}"
                )
            elif layer.type != "line" and layer.drawstyle != "default":
                issues.append(f"{where}: drawstyle only applies to line layers")

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
                layer.type in {"scatter", "scatter3d", "quiver"} and layer.c is not None
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
