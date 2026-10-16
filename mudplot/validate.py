"""Pure spec validation: catch mistakes early with clear, agent-friendly errors.

Returns a list of human-readable issue strings instead of raising, so callers
(agents, dashboards, tests) can decide whether to warn or abort. ``render()``
uses this to fail fast with a helpful message instead of a raw ``KeyError``.
"""

from __future__ import annotations

import math
from dataclasses import fields
from itertools import pairwise
from numbers import Real
from urllib.parse import urlsplit

from ._categorical import (
    CATEGORY_TYPES,
    DISTRIBUTION_TYPES,
    MAX_SWARM_POINTS,
    MAX_VIOLIN_POINTS,
    distribution_columns,
    distribution_rows,
    native_category_geometry,
)
from ._cluster import cluster_issues
from ._components import _color, component_issues
from ._ecdf import ECDF_STATS, ecdf_config, ecdf_groups, ecdf_rows, finite_mass
from ._facet import (
    RAW_HUE_TYPES,
    ordered_group_columns,
    panel_columns,
    panel_filter_issues,
)
from ._heatmap import heatmap_issues
from ._histogram import (
    HISTOGRAM_ELEMENTS,
    HISTOGRAM_MULTIPLES,
    HISTOGRAM_STATS,
    MAX_HISTOGRAM_BINS,
    NORMALIZED_STATS,
    histogram_rows,
)
from ._kde import kde_rows
from ._kde import option_issues as kde_option_issues
from ._kde2d import MAX_KDE2D_ROWS, kde2d_config, kde2d_rows
from ._kde2d import option_issues as kde2d_option_issues
from ._letter_value import option_issues as letter_value_option_issues
from ._regression import MAX_REGRESSION_ROWS
from ._regression import group_issues as regression_group_issues
from ._regression import option_issues as regression_option_issues
from ._semantics import category_key, shared_scale_issues
from ._semantics import data_issues as semantic_data_issues
from ._stat import (
    COUNT_STATS,
    ESTIMATORS,
    INTERVAL_METHODS,
    LABEL_FORMATS,
    MAX_BOOTSTRAPS,
    STAT_LAYER_TYPES,
    is_missing,
    stat_config,
    usable_rows,
)
from ._violin_options import MAX_INNER_OBSERVATIONS
from ._violin_options import option_issues as violin_option_issues
from .capabilities import LAYER_TYPES, PALETTE_PRESETS, PROJECTIONS
from .spec import (
    ECDFSpec,
    FigureSpec,
    HistogramSpec,
    KDE2DSpec,
    KDESpec,
    LayerSpec,
    StatSpec,
)

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
    "barplot",
    "pointplot",
    "countplot",
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
    "y_lower",
    "y_upper",
    "group",
    "weights",
    "c",
    "u",
    "v",
    "z",
)
_VALID_SPINE_CHARS = set("LRTB")
_POINT_TYPES = {"text", "annotate"}  # layers whose ``at``/``to`` is [x, y]
_MATRIX_LAYER_TYPES = {
    "heatmap",
    "clustermap",
    "contour",
    "contourf",
    "surface",
    "wireframe",
}
_CMAP_LAYER_TYPES = {
    "heatmap",
    "clustermap",
    "contour",
    "contourf",
    "surface",
    "hist2d",
    "hexbin",
}
_BIVARIATE_DENSITY_TYPES = {"hist2d", "hexbin"}
_POLAR_TYPES = {"line", "scatter", "bar"}
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
    if val is None:
        return
    try:
        valid = len(val) == 2 and all(_finite(value) for value in val)
    except TypeError:
        valid = False
    if not valid:
        issues.append(f"{where}: {field_name!r} must be [x, y] finite numbers")


def _finite(value) -> bool:
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _check_uncertainty(cols, layer, where: str, issues: list[str]) -> None:
    """Validate supplied errors without inferring their statistical meaning."""
    for field_name in ("yerr", "xerr"):
        name = getattr(layer, field_name)
        if (
            isinstance(name, str)
            and name in cols
            and any(not _finite(v) or v < 0 for v in cols[name])
        ):
            issues.append(
                f"{where}: {field_name} values must be finite, nonnegative "
                "error magnitudes"
            )

    has_lower = layer.y_lower is not None
    has_upper = layer.y_upper is not None
    if has_lower != has_upper:
        issues.append(f"{where}: y_lower and y_upper must be supplied together")
    if (has_lower or has_upper) and layer.yerr is not None:
        issues.append(f"{where}: use yerr OR y_lower/y_upper, not both")
    names = (layer.y, layer.y_lower, layer.y_upper)
    if (
        has_lower
        and has_upper
        and all(isinstance(name, str) and name in cols for name in names)
    ):
        values = [cols[name] for name in names]
        if len({len(column) for column in values}) == 1:
            for center, lower, upper in zip(*values, strict=True):
                if not all(_finite(v) for v in (center, lower, upper)):
                    issues.append(
                        f"{where}: y/y_lower/y_upper values must be finite numbers"
                    )
                    break
                if not lower <= center <= upper:
                    issues.append(
                        f"{where}: interval must satisfy y_lower <= y <= y_upper"
                    )
                    break
                if not all(_finite(v) for v in (center - lower, upper - center)):
                    issues.append(f"{where}: interval error magnitudes must be finite")
                    break

    for field_name in ("capsize", "capthick", "error_line_width", "line_width"):
        value = getattr(layer, field_name)
        if value is not None and (not _finite(value) or value < 0):
            issues.append(f"{where}: {field_name} must be finite and nonnegative")
    if layer.type in {"bar", "barplot", "countplot"}:
        width = layer.bar_width
        if width is not None and (not _finite(width) or width <= 0):
            issues.append(f"{where}: bar_width must be positive and finite")
    for field_name in ("error_color", "edge_color"):
        value = getattr(layer, field_name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            issues.append(f"{where}: {field_name} must be a non-empty color string")


def _check_category_order(levels, name, where, issues) -> None:
    if levels is None:
        return
    if not isinstance(levels, (list, tuple)) or not levels:
        issues.append(f"{where}: {name} must be a nonempty array of category levels")
        return
    seen, labels = set(), set()
    for value in levels:
        if not isinstance(value, (str, bool)) and not _finite(value):
            issues.append(f"{where}: {name} levels must be strings or finite scalars")
            return
        if value in seen or str(value) in labels:
            issues.append(
                f"{where}: {name} levels must be unique without label collisions"
            )
            return
        seen.add(value)
        labels.add(str(value))


def _check_histogram_layer(cols, layer, panel, where, issues) -> None:
    config = layer.histogram
    if config is None:
        if any(
            getattr(layer, name) != getattr(LayerSpec(), name)
            for name in (
                "hue_order",
                "orient",
                "edge_color",
                "line_width",
            )
        ):
            issues.append(f"{where}: histogram options require HistogramSpec")
        return  # Legacy density/group/alpha/bin behavior is intentionally unchanged.
    if not isinstance(config, HistogramSpec):
        issues.append(f"{where}: histogram must be HistogramSpec or None")
        return
    if config.stat not in HISTOGRAM_STATS:
        issues.append(f"{where}: invalid histogram stat; expected {HISTOGRAM_STATS}")
    if config.multiple not in HISTOGRAM_MULTIPLES:
        issues.append(
            f"{where}: invalid histogram multiple; expected {HISTOGRAM_MULTIPLES}"
        )
    if config.multiple in ("stack", "dodge") and layer.group is None:
        issues.append(f"{where}: histogram multiple={config.multiple!r} requires group")
    if config.element not in HISTOGRAM_ELEMENTS:
        issues.append(
            f"{where}: invalid histogram element; expected {HISTOGRAM_ELEMENTS}"
        )
    if config.element == "step" and config.multiple == "dodge":
        issues.append(f"{where}: histogram step supports layer/stack, not dodge")
    for name in ("common_norm", "cumulative"):
        if type(getattr(config, name)) is not bool:
            issues.append(f"{where}: histogram {name} must be boolean")
    if config.stat not in NORMALIZED_STATS and config.common_norm is False:
        issues.append(f"{where}: common_norm=False only applies to normalized stats")
    if config.stat == "frequency" and config.cumulative:
        issues.append(f"{where}: cumulative frequency is unsupported; use count")
    if type(layer.density) is not bool:
        issues.append(f"{where}: histogram density alias must be boolean")
    elif layer.density and config.stat != "density":
        issues.append(f"{where}: density=True conflicts with histogram stat")
    if config.weights is not None:
        if not isinstance(config.weights, str) or not config.weights:
            issues.append(f"{where}: histogram weights must be a nonempty column name")
        else:
            _check_column(cols, config.weights, where, issues)
    bins = layer.bins
    valid_bins = type(bins) is int and 1 <= bins <= MAX_HISTOGRAM_BINS
    if isinstance(bins, (list, tuple)):
        valid_bins = (
            2 <= len(bins) <= MAX_HISTOGRAM_BINS + 1
            and all(_finite(edge) for edge in bins)
            and all(a < b for a, b in pairwise(bins))
        )
    if not valid_bins:
        issues.append(
            f"{where}: histogram bins require 1..{MAX_HISTOGRAM_BINS} integer "
            "or finite increasing edges"
        )
    if layer.orient not in ("v", "h"):
        issues.append(f"{where}: histogram orient must be v or h")
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.hue_order is not None and layer.group is None:
        issues.append(f"{where}: histogram hue_order requires group")
    allowed = set(LAYER_TYPES["hist"]["optional"]) | {
        "type",
        "x",
        "citation",
        "href",
        "references",
    }
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in allowed and getattr(layer, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"{where}: {field.name} is not supported for typed hist")
    if layer.line_width is not None and (
        not _finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append(f"{where}: histogram line_width must be in [0,1000]")
    for name in ("color", "edge_color"):
        if getattr(layer, name) is not None and not _color(getattr(layer, name)):
            issues.append(f"{where}: histogram {name} must be bounded name or hex")
    value_axis, mass_axis = (
        (panel.x, panel.y) if layer.orient == "v" else (panel.y, panel.x)
    )
    if mass_axis.scale != "linear":
        issues.append(f"{where}: histogram height axis must be linear (zero bins)")
    if (
        value_axis.scale == "log"
        and isinstance(bins, (list, tuple))
        and valid_bins
        and bins[0] <= 0
    ):
        issues.append(f"{where}: log histogram bin edges must be positive")
    rows = histogram_rows(cols, layer)
    if any(not _finite(cols[layer.x][i]) for i in rows):
        issues.append(
            f"{where}: histogram observations must be finite numeric, not bool"
        )
    elif value_axis.scale == "log" and any(cols[layer.x][i] <= 0 for i in rows):
        issues.append(f"{where}: log histogram observations must be positive")
    if config.weights is not None and any(
        not _finite(cols[config.weights][i]) or cols[config.weights][i] < 0
        for i in rows
    ):
        issues.append(
            f"{where}: histogram weights must be finite nonnegative, not bool"
        )
    if layer.group is not None and rows:
        groups = [cols[layer.group][i] for i in rows]
        if any(not isinstance(g, (str, bool)) and not _finite(g) for g in groups):
            issues.append(
                f"{where}: histogram groups must be strings or finite scalars"
            )
        else:
            _check_category_order(
                list(dict.fromkeys(groups)), "histogram groups", where, issues
            )


def _check_kde_layer(cols, layer, panel, where, issues) -> None:
    config = layer.kde
    if config is None:
        if any(
            getattr(layer, name) != getattr(LayerSpec(), name)
            for name in ("hue_order", "orient", "edge_color")
        ):
            issues.append(f"{where}: KDE options require KDESpec")
        return  # Preserve documented legacy curves/style/default bandwidth.
    if not isinstance(config, KDESpec):
        issues.append(f"{where}: kde must be KDESpec or None")
        return
    issues.extend(f"{where}: KDE {issue}" for issue in kde_option_issues(config))
    if config.weights is not None:
        if not isinstance(config.weights, str) or not config.weights:
            issues.append(f"{where}: KDE weights must be a nonempty column name")
        else:
            _check_column(cols, config.weights, where, issues)
    if layer.orient not in ("v", "h"):
        issues.append(f"{where}: KDE orient must be v or h")
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.hue_order is not None and layer.group is None:
        issues.append(f"{where}: KDE hue_order requires group")
    allowed = set(LAYER_TYPES["kde"]["optional"]) | {
        "type",
        "x",
        "citation",
        "href",
        "references",
    }
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in allowed and getattr(layer, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"{where}: {field.name} is not supported for typed KDE")
    if layer.edge_color is not None and not config.fill:
        issues.append(f"{where}: KDE edge_color requires fill=True")
    for name in ("color", "edge_color"):
        if getattr(layer, name) is not None and not _color(getattr(layer, name)):
            issues.append(f"{where}: KDE {name} must be bounded name or hex")
    if layer.line_width is not None and (
        not _finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append(f"{where}: KDE line_width must be in [0,1000]")
    if layer.line_style is not None and layer.line_style not in ("-", "--", ":", "-."):
        issues.append(f"{where}: KDE line_style must be -, --, : or -.")
    value_axis, density_axis = (
        (panel.x, panel.y) if layer.orient == "v" else (panel.y, panel.x)
    )
    if density_axis.scale != "linear":
        issues.append(f"{where}: KDE density/CDF axis must be linear")
    if (
        value_axis.scale == "log"
        and config.clip is not None
        and (
            isinstance(config.clip, (list, tuple))
            and len(config.clip) == 2
            and any(v is not None and _finite(v) and v <= 0 for v in config.clip)
        )
    ):
        issues.append(f"{where}: KDE log clip bounds must be positive")
    rows = kde_rows(cols, layer)
    if any(not _finite(cols[layer.x][i]) for i in rows):
        issues.append(f"{where}: KDE observations must be finite numeric, not bool")
    elif value_axis.scale == "log" and any(cols[layer.x][i] <= 0 for i in rows):
        issues.append(f"{where}: KDE log observations must be positive")
    if config.weights is not None and any(
        not _finite(cols[config.weights][i]) or cols[config.weights][i] < 0
        for i in rows
    ):
        issues.append(f"{where}: KDE weights must be finite nonnegative, not bool")
    if layer.group is not None and rows:
        groups = [cols[layer.group][i] for i in rows]
        if any(not isinstance(g, (str, bool)) and not _finite(g) for g in groups):
            issues.append(f"{where}: KDE groups must be strings or finite scalars")
        else:
            _check_category_order(
                list(dict.fromkeys(groups)), "KDE groups", where, issues
            )


def _check_kde2d_layer(cols, layer, panel, where, issues) -> None:
    config = kde2d_config(layer)
    if not isinstance(config, KDE2DSpec):
        issues.append(f"{where}: kde2d must be KDE2DSpec or None")
        return
    issues.extend(f"{where}: KDE2D {issue}" for issue in kde2d_option_issues(config))
    if config.weights is not None:
        if not isinstance(config.weights, str) or not config.weights:
            issues.append(f"{where}: KDE2D weights must be a nonempty column name")
        else:
            _check_column(cols, config.weights, where, issues)
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.hue_order is not None and layer.group is None:
        issues.append(f"{where}: KDE2D hue_order requires group")
    allowed = set(
        LAYER_TYPES["kde2d"]["required"] + LAYER_TYPES["kde2d"]["optional"]
    ) | {
        "type",
        "citation",
        "href",
        "references",
    }
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in allowed and getattr(layer, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"{where}: {field.name} is not supported for KDE2D")
    if layer.edge_color is not None and not config.fill:
        issues.append(f"{where}: KDE2D edge_color requires fill=True")
    for name in ("color", "edge_color"):
        if getattr(layer, name) is not None and not _color(getattr(layer, name)):
            issues.append(f"{where}: KDE2D {name} must be bounded name or hex")
    if layer.line_width is not None and (
        not _finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append(f"{where}: KDE2D line_width must be in [0,1000]")
    if layer.line_style is not None and layer.line_style not in ("-", "--", ":", "-."):
        issues.append(f"{where}: KDE2D line_style must be -, --, : or -.")
    rows = kde2d_rows(cols, layer)
    if len(rows) > MAX_KDE2D_ROWS:
        issues.append(f"{where}: KDE2D at most {MAX_KDE2D_ROWS} usable rows supported")
    for axis, name in ((panel.x, layer.x), (panel.y, layer.y)):
        if any(not _finite(cols[name][i]) for i in rows):
            issues.append(
                f"{where}: KDE2D observations must be finite numeric, not bool"
            )
        elif axis.scale == "log" and any(cols[name][i] <= 0 for i in rows):
            issues.append(f"{where}: KDE2D log observations must be positive")
    if (
        config.clip is not None
        and isinstance(config.clip, (list, tuple))
        and len(config.clip) == 2
    ):
        for axis, bound in zip((panel.x, panel.y), config.clip, strict=True):
            if (
                axis.scale == "log"
                and isinstance(bound, (list, tuple))
                and len(bound) == 2
                and any(v is not None and _finite(v) and v <= 0 for v in bound)
            ):
                issues.append(f"{where}: KDE2D log clip bounds must be positive")
    if config.weights is not None and any(
        not _finite(cols[config.weights][i]) or cols[config.weights][i] < 0
        for i in rows
    ):
        issues.append(f"{where}: KDE2D weights must be finite nonnegative, not bool")
    if layer.group is not None and rows:
        groups = [cols[layer.group][i] for i in rows]
        if any(not isinstance(g, (str, bool)) and not _finite(g) for g in groups):
            issues.append(f"{where}: KDE2D groups must be strings or finite scalars")
        else:
            _check_category_order(
                list(dict.fromkeys(groups)), "KDE2D groups", where, issues
            )


def _check_ecdf_layer(cols, layer, panel, where, issues) -> None:
    if layer.ecdf is not None and not isinstance(layer.ecdf, ECDFSpec):
        issues.append(f"{where}: ecdf must be an ECDFSpec or None")
        return
    config = ecdf_config(layer)
    if config.stat not in ECDF_STATS:
        issues.append(f"{where}: ECDF stat must be proportion, percent or count")
    if type(config.complementary) is not bool:
        issues.append(f"{where}: ECDF complementary must be boolean")
    if config.weights is not None:
        if not isinstance(config.weights, str) or not config.weights:
            issues.append(f"{where}: ECDF weights must be a nonempty column name")
        else:
            _check_column(cols, config.weights, where, issues)
    if layer.orient not in ("v", "h"):
        issues.append(f"{where}: ECDF orient must be v or h")
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.hue_order is not None and layer.group is None:
        issues.append(f"{where}: ECDF hue_order requires group")
    allowed = set(LAYER_TYPES["ecdf"]["optional"]) | {
        "type",
        "x",
        "citation",
        "href",
        "references",
    }
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in allowed and getattr(layer, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"{where}: {field.name} is not supported for ecdf")
    if layer.line_width is not None and (
        not _finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append(f"{where}: ECDF line_width must be finite in [0,1000]")
    if layer.line_style is not None and layer.line_style not in ("-", "--", ":", "-."):
        issues.append(f"{where}: ECDF line_style must be -, --, : or -.")
    if layer.color is not None and not _color(layer.color):
        issues.append(f"{where}: ECDF color must be a bounded name or hex color")
    value_axis, mass_axis = (
        (panel.x, panel.y) if layer.orient == "v" else (panel.y, panel.x)
    )
    if mass_axis.scale != "linear":
        issues.append(f"{where}: ECDF cumulative mass axis must be linear (includes 0)")
    rows = ecdf_rows(cols, layer)
    valid = True
    for i in rows:
        value = cols[layer.x][i]
        if not _finite(value):
            issues.append(
                f"{where}: ECDF observations must be finite numbers, not bool"
            )
            valid = False
            break
        if value_axis.scale == "log" and value <= 0:
            issues.append(f"{where}: log ECDF observations must be positive")
            valid = False
            break
    if (
        config.weights is not None
        and rows
        and any(
            not _finite(cols[config.weights][i]) or cols[config.weights][i] < 0
            for i in rows
        )
    ):
        issues.append(f"{where}: ECDF weights must be finite nonnegative, not bool")
        valid = False
    if layer.group is not None and rows:
        groups = [cols[layer.group][i] for i in rows]
        if any(not isinstance(key, (str, bool)) and not _finite(key) for key in groups):
            issues.append(f"{where}: ECDF groups must be strings or finite scalars")
            valid = False
        else:
            _check_category_order(
                list(dict.fromkeys(groups)), "ECDF groups", where, issues
            )
    if valid and config.stat == "count" and config.weights is not None and rows:
        for group in ecdf_groups(cols, layer, rows):
            try:
                finite_mass(
                    cols[config.weights][i]
                    for i in rows
                    if layer.group is None or cols[layer.group][i] == group
                )
            except ValueError as exc:
                issues.append(f"{where}: {exc}")
                break


def _check_distribution_layer(cols, layer, where: str, issues: list[str]) -> None:
    category, value, hue = distribution_columns(layer)
    if layer.orient not in ("v", "h"):
        issues.append(f"{where}: orient must be 'v' or 'h'")
    for name in ("width", "dodge", "gap", "line_width", "marker_size"):
        number = getattr(layer, name)
        if number is None:
            continue
        valid = _finite(number)
        if valid:
            valid = (
                (0 <= number < 1)
                if name == "gap"
                else (number > 0 if name == "width" else number >= 0)
            )
        if not valid:
            issues.append(f"{where}: invalid {name}; use a finite valid span/size")
    for name in ("notch", "showmeans", "showfliers", "showmedians", "showextrema"):
        if getattr(layer, name) is not None and type(getattr(layer, name)) is not bool:
            issues.append(f"{where}: {name} must be boolean or None")
    if layer.whis is not None:
        whis = layer.whis
        valid = _finite(whis) and whis >= 0
        if isinstance(whis, (list, tuple)):
            valid = (
                len(whis) == 2
                and all(_finite(v) for v in whis)
                and 0 <= whis[0] < whis[1] <= 100
            )
        if not valid:
            issues.append(
                f"{where}: whis must be a nonnegative IQR multiplier "
                "or an increasing percentile pair in [0, 100]"
            )
    if layer.bw_method is not None and not (
        (isinstance(layer.bw_method, str) and layer.bw_method in ("scott", "silverman"))
        or (
            isinstance(layer.bw_method, (int, float))
            and _finite(layer.bw_method)
            and layer.bw_method > 0
        )
    ):
        issues.append(
            f"{where}: bw_method must be scott, silverman or a positive factor"
        )
    if layer.points is not None and (
        type(layer.points) is not int or not 2 <= layer.points <= MAX_VIOLIN_POINTS
    ):
        issues.append(f"{where}: points must be an integer in 2..{MAX_VIOLIN_POINTS}")
    _check_category_order(layer.order, "order", where, issues)
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.order is not None and category is None:
        issues.append(f"{where}: order requires a category column or legacy group")
    if layer.hue_order is not None and hue is None:
        issues.append(f"{where}: hue_order requires both y and group")
    if not layer.y and layer.dodge is not None:
        issues.append(f"{where}: dodge requires category/value columns")
    supported = set(
        LAYER_TYPES[layer.type]["required"] + LAYER_TYPES[layer.type]["optional"]
    )
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in supported | {
            "type",
            "citation",
            "href",
            "references",
        } and getattr(layer, field.name) != getattr(defaults, field.name):
            issues.append(f"{where}: {field.name} is not supported for {layer.type}")
    valid_columns = True
    for name in (category, hue):
        if name is None:
            continue
        if not isinstance(name, str) or name not in cols:
            valid_columns = False
            continue
        seen = {}
        values = (
            [cols[name][i] for i in distribution_rows(cols, layer)]
            if layer.type == "violin" and layer.weights is not None
            else cols[name]
        )
        for v in values:
            if is_missing(v):
                continue
            if not isinstance(v, (str, bool)) and not _finite(v):
                issues.append(f"{where}: categories must be strings or finite scalars")
                valid_columns = False
                break
            key = str(v)
            if key in seen and seen[key] != v:
                issues.append(
                    f"{where}: category labels collide after string conversion"
                )
                valid_columns = False
                break
            seen[key] = v
    if not isinstance(value, str) or value not in cols:
        valid_columns = False
    elif any(
        not is_missing(v) and not _finite(v)
        for v in (
            [cols[value][i] for i in distribution_rows(cols, layer)]
            if layer.type == "violin" and layer.weights is not None
            else cols[value]
        )
    ):
        issues.append(f"{where}: observations must be finite numbers or missing")
        valid_columns = False
    if valid_columns and not distribution_rows(cols, layer):
        issues.append(f"{where}: no usable observations after dropping missing rows")


def _check_violin_layer(cols, layer, panel, where, issues):
    issues.extend(f"{where}: {issue}" for issue in violin_option_issues(layer))
    rows = distribution_rows(cols, layer)
    if layer.weights is not None:
        if (
            isinstance(layer.weights, str)
            and layer.weights in cols
            and any(
                not _finite(cols[layer.weights][i]) or cols[layer.weights][i] < 0
                for i in rows
            )
        ):
            issues.append(
                f"{where}: violin weights must be finite nonnegative, not bool"
            )
        if len(rows) > MAX_INNER_OBSERVATIONS:
            issues.append(
                f"{where}: weighted violin supports at most {MAX_INNER_OBSERVATIONS} "
                "usable observations; no replication/sampling"
            )
    if (
        isinstance(layer.inner, str)
        and layer.inner in ("point", "stick")
        and (len(rows) > MAX_INNER_OBSERVATIONS)
    ):
        issues.append(
            f"{where}: point/stick inner supports at most {MAX_INNER_OBSERVATIONS} "
            "usable observations; no silent sampling"
        )
    if type(layer.split) is bool and layer.split:
        _category, _value, hue = distribution_columns(layer)
        if not layer.y or not isinstance(hue, str) or hue not in cols:
            issues.append(f"{where}: split requires category/value columns and hue")
        elif layer.hue_order is None:
            values = [cols[hue][i] for i in rows]
            if all(isinstance(v, (str, bool)) or _finite(v) for v in values) and (
                len(dict.fromkeys(values)) != 2
            ):
                issues.append(
                    f"{where}: split requires exactly two selected hue levels"
                )
        elif isinstance(layer.hue_order, (list, tuple)) and len(layer.hue_order) != 2:
            issues.append(f"{where}: split requires exactly two selected hue levels")
    value_axis = panel.x if layer.orient == "h" else panel.y
    if (
        value_axis.scale == "log"
        and isinstance(layer.clip, (list, tuple))
        and any(_finite(v) and v <= 0 for v in layer.clip if v is not None)
    ):
        issues.append(f"{where}: log-value clip bounds must be positive raw values")


def _check_distribution_scales(cols, layer, panel, where, issues):
    category, value, _hue = distribution_columns(layer)
    cat_axis = panel.y if layer.orient == "h" else panel.x
    val_axis = panel.x if layer.orient == "h" else panel.y
    if type(layer.native_scale) is not bool:
        issues.append(f"{where}: native_scale must be boolean")
    if layer.stat_scale not in ("data", "axis"):
        issues.append(f"{where}: stat_scale must be 'data' or 'axis'")
    # Preserve legacy one-column box/violin log axes at one-based positions.
    if (
        cat_axis.scale == "log"
        and not layer.native_scale
        and (layer.y or layer.type in {"swarmplot", "boxenplot"})
    ):
        issues.append(f"{where}: log category axis requires native_scale=True")
    rows = distribution_rows(cols, layer)
    if (
        val_axis.scale == "log"
        and isinstance(value, str)
        and value in cols
        and any(_finite(cols[value][i]) and cols[value][i] <= 0 for i in rows)
    ):
        issues.append(f"{where}: log-value observations must be positive")
    if type(layer.native_scale) is bool and layer.native_scale:
        if not isinstance(category, str) or category not in cols:
            issues.append(f"{where}: native_scale requires a category column")
            return
        values = [cols[category][i] for i in rows]
        if any(not _finite(v) for v in values):
            issues.append(f"{where}: native_scale requires numeric finite levels")
            return
        if layer.order is not None and not isinstance(layer.order, (list, tuple)):
            return
        levels = layer.order if layer.order is not None else list(dict.fromkeys(values))
        try:
            native_category_geometry(levels, cat_axis.scale)
        except ValueError as exc:
            issues.append(f"{where}: {exc}")
        width = 0.8 if layer.width is None else layer.width
        if not _finite(width) or not 0 < width <= 1:
            issues.append(f"{where}: native width must be in (0,1]")
        if layer.dodge is not None and (
            not _finite(layer.dodge)
            or not _finite(width)
            or not 0 <= layer.dodge <= width
        ):
            issues.append(f"{where}: native dodge must be in [0,width]")


def _check_shared_category_scales(spec, colsn, issues):
    """Shared axes cannot silently mix incompatible coordinate declarations."""
    if type(colsn) is not int or colsn < 1:
        return  # Malformed layouts are already reported by validate().
    for axis_name in ("x", "y"):
        share = getattr(spec, f"share_{axis_name}")
        groups = {}
        for pi, panel in enumerate(spec.panels):
            if panel.projection != "2d":
                continue
            key = (
                "all"
                if share == "all"
                else pi // colsn
                if share == "row"
                else pi % colsn
                if share == "col"
                else pi
            )
            name = getattr(panel, axis_name).share_id
            if name is not None and share != "none":
                issues.append(
                    f"named shared {axis_name} axes cannot mix figure sharing modes"
                )
            key = ("named", name) if isinstance(name, str) and name else ("mode", key)
            groups.setdefault(key, []).append(panel)
        for key, panels in groups.items():
            if key[0] == "named":
                bounds = [getattr(p, axis_name).limits for p in panels]
                valid = [
                    tuple(v)
                    for v in bounds
                    if isinstance(v, (list, tuple))
                    and len(v) == 2
                    and all(_finite(item) for item in v)
                ]
                if len(set(valid)) > 1:
                    issues.append(
                        f"named shared {axis_name} axes have conflicting limits"
                    )
            if len({getattr(p, axis_name).scale for p in panels}) > 1:
                issues.append(
                    f"shared {axis_name} axes have conflicting scale declarations"
                )
            modes = set()
            for panel in panels:
                for layer in panel.layers:
                    if layer.type == "scatter" and layer.semantics is not None:
                        modes.add("native")
                    if layer.type in CATEGORY_TYPES | STAT_LAYER_TYPES and (
                        axis_name == ("y" if layer.orient == "h" else "x")
                    ):
                        modes.add(
                            "native"
                            if layer.type == "lineplot"
                            or (type(layer.native_scale) is bool and layer.native_scale)
                            else "ordinal"
                        )
            if len(modes) > 1:
                issues.append(
                    f"shared {axis_name} category axis mixes native and ordinal modes"
                )
            if "ordinal" in modes and any(
                layer.type == "hist" and layer.histogram is not None
                for panel in panels
                for layer in panel.layers
            ):
                issues.append(
                    f"typed histogram numeric {axis_name} axis cannot mix "
                    "ordinal categories"
                )
            if "ordinal" in modes and any(
                layer.type == "kde" and layer.kde is not None
                for panel in panels
                for layer in panel.layers
            ):
                issues.append(
                    f"typed KDE numeric {axis_name} axis cannot mix ordinal categories"
                )
            if "ordinal" in modes and any(
                layer.type == "kde2d" for panel in panels for layer in panel.layers
            ):
                issues.append(
                    f"KDE2D numeric {axis_name} axis cannot mix ordinal categories"
                )
            if "native" in modes:
                for panel in panels:
                    columns = spec.data.columns
                    if not panel_filter_issues(columns, panel):
                        columns = panel_columns(columns, panel)
                    for layer in panel.layers:
                        if layer.type not in {
                            "line",
                            "scatter",
                            "stripplot",
                            "bar",
                            "band",
                            "errorbar",
                        }:
                            continue
                        if layer.type == "scatter" and layer.semantics is not None:
                            # Its own contract validates selected numeric rows.
                            continue
                        try:
                            layer_columns = ordered_group_columns(columns, layer)
                        except ValueError:
                            layer_columns = columns
                        name = getattr(layer, axis_name)
                        if (axis_name != "y" or layer.axis == "y") and (
                            isinstance(name, str)
                            and name in layer_columns
                            and any(isinstance(v, str) for v in layer_columns[name])
                        ):
                            issues.append(
                                f"native {axis_name} category axis cannot "
                                "mix string series"
                            )


def _check_statistical_scales(cols, layer, panel, where, issues):
    """Pure positivity/native geometry contracts; derived bounds checked by effect."""
    cat_axis = panel.y if layer.orient == "h" else panel.x
    val_axis = (
        panel.x if layer.orient == "h" else panel.y2 if layer.axis == "y2" else panel.y
    )
    value_scale = "linear" if val_axis is None else val_axis.scale
    native = layer.type == "lineplot" or layer.native_scale
    if type(layer.native_scale) is not bool:
        issues.append(f"{where}: native_scale must be boolean")
    if layer.stat_scale not in ("data", "axis"):
        issues.append(f"{where}: stat_scale must be 'data' or 'axis'")
    if layer.axis == "y2" and (
        native
        or layer.stat_scale == "axis"
        or cat_axis.scale == "log"
        or value_scale == "log"
    ):
        issues.append(
            f"{where}: statistical native/log subset supports primary axes only"
        )
    if cat_axis.scale == "log" and not native:
        issues.append(f"{where}: log category axis requires native_scale=True")
    if layer.baseline is not None:
        if not _finite(layer.baseline):
            issues.append(f"{where}: baseline must be a finite raw-value number")
        if layer.stack:
            issues.append(
                f"{where}: explicit baseline is not supported for stacked counts"
            )
    if value_scale == "log" and layer.type in {"barplot", "countplot"}:
        if layer.baseline is None or not _finite(layer.baseline) or layer.baseline <= 0:
            issues.append(
                f"{where}: log statistical bars require a positive explicit baseline"
            )
        if layer.stack:
            issues.append(f"{where}: stacked counts require a linear value axis")
    if layer.stat is not None and not isinstance(layer.stat, StatSpec):
        return
    config = stat_config(layer)
    if (
        value_scale == "log"
        and layer.stat_scale == "axis"
        and (
            not isinstance(config.estimator, str)
            or config.estimator not in {"mean", "median", "min", "max"}
        )
    ):
        issues.append(
            f"{where}: axis log estimation supports mean/median/min/max, not sum/count"
        )
    rows = usable_rows(cols, layer)
    if (
        value_scale == "log"
        and config.estimator != "count"
        and (
            isinstance(layer.y, str)
            and layer.y in cols
            and any(_finite(cols[layer.y][i]) and cols[layer.y][i] <= 0 for i in rows)
        )
    ):
        issues.append(f"{where}: log-value observations must be positive")
    if type(native) is bool and native:
        if layer.order is not None and not isinstance(layer.order, (list, tuple)):
            return
        values = [cols[layer.x][i] for i in rows]
        if any(not _finite(v) for v in values):
            issues.append(
                f"{where}: native_scale requires numeric finite category levels"
            )
            return
        categories = (
            layer.order if layer.order is not None else list(dict.fromkeys(values))
        )
        try:
            native_category_geometry(categories, cat_axis.scale)
        except ValueError as exc:
            issues.append(f"{where}: {exc}")
        if layer.type in {"barplot", "countplot"}:
            width = 0.8 if layer.bar_width is None else layer.bar_width
            if not _finite(width) or not 0 < width <= 1:
                issues.append(f"{where}: native bar_width must be in (0,1]")
        elif layer.dodge is not None and (
            not _finite(layer.dodge) or not 0 <= layer.dodge <= 1
        ):
            issues.append(f"{where}: native point dodge must be in [0,1]")


def _check_lineplot_layer(cols, layer, where, issues):
    if layer.semantics is None and layer.cmap_kind != "sequential":
        issues.append(f"{where}: cmap_kind requires numeric semantic hue")
    if type(layer.sort) is not bool:
        issues.append(f"{where}: lineplot sort must be boolean")
    if layer.error_style not in (None, "band", "bars"):
        issues.append(f"{where}: error_style must be band, bars or None")
    if layer.error_alpha is not None and (
        not _finite(layer.error_alpha) or not 0 <= layer.error_alpha <= 1
    ):
        issues.append(f"{where}: error_alpha must be finite in [0,1]")
    style = "band" if layer.error_style is None else layer.error_style
    if style == "band" and any(
        getattr(layer, name) is not None
        for name in ("error_line_width", "capsize", "capthick")
    ):
        issues.append(f"{where}: error_line_width/capsize/capthick require bars")
    if style == "bars" and layer.error_alpha is not None:
        issues.append(f"{where}: error_alpha requires band")
    if (
        (layer.stat is None or isinstance(layer.stat, StatSpec))
        and stat_config(layer).errorbar is None
        and any(
            getattr(layer, name) is not None
            for name in (
                "error_style",
                "error_alpha",
                "error_color",
                "error_line_width",
                "capsize",
                "capthick",
            )
        )
    ):
        issues.append(f"{where}: explicit interval styling requires errorbar")
    if layer.line_width is not None and (
        not _finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append(f"{where}: line_width must be finite in [0,1000]")


def _check_statistical_layer(cols, layer, where: str, issues: list[str]) -> None:
    if layer.stat is not None and not isinstance(layer.stat, StatSpec):
        issues.append(f"{where}: stat must be a StatSpec or None")
        return
    config = stat_config(layer)
    if not isinstance(config.estimator, str) or config.estimator not in ESTIMATORS:
        issues.append(
            f"{where}: unknown estimator {config.estimator!r}; use {ESTIMATORS}"
        )
    if config.errorbar is not None and (
        not isinstance(config.errorbar, str) or config.errorbar not in INTERVAL_METHODS
    ):
        issues.append(f"{where}: unknown errorbar method {config.errorbar!r}")
    if layer.type == "countplot" and (
        config.estimator != "count" or config.errorbar is not None
    ):
        issues.append(
            f"{where}: countplot requires estimator='count' and errorbar=None"
        )
    if config.errorbar == "se" and config.estimator != "mean":
        issues.append(f"{where}: SE is sample-mean SEM; use estimator='mean' or CI")
    if config.estimator == "count" and config.errorbar is not None:
        issues.append(f"{where}: count estimator requires errorbar=None")
    if config.weights is not None and (
        config.estimator != "mean" or config.errorbar not in (None, "ci")
    ):
        issues.append(f"{where}: weights support mean with no interval or bootstrap CI")
    if config.units is not None and config.errorbar != "ci":
        issues.append(f"{where}: units require bootstrap CI")
    if not isinstance(config.normalize, str) or config.normalize not in COUNT_STATS:
        issues.append(f"{where}: unknown count normalization {config.normalize!r}")
    elif layer.type != "countplot" and config.normalize != "count":
        issues.append(f"{where}: count normalization is only supported for countplot")
    for field_name in ("weights", "units"):
        name = getattr(config, field_name)
        if name is None:
            continue
        if not isinstance(name, str) or not name or name not in cols:
            issues.append(f"{where}: stat.{field_name} must name an existing column")
            continue
        values = [v for v in cols[name] if not is_missing(v)]
        if field_name == "weights":
            if any(not _finite(v) or v < 0 for v in values):
                issues.append(f"{where}: weights must be finite nonnegative numbers")
        elif any(not isinstance(v, (str, bool)) and not _finite(v) for v in values):
            issues.append(f"{where}: units must be strings or finite scalars")
    if config.level is not None:
        if not _finite(config.level) or config.level <= 0:
            issues.append(f"{where}: stat.level must be positive and finite")
        elif config.errorbar in ("pi", "ci") and config.level > 100:
            issues.append(f"{where}: PI/CI stat.level must be at most 100 percent")
        if config.errorbar is None:
            issues.append(f"{where}: stat.level requires an errorbar method")
    if (
        isinstance(config.n_boot, bool)
        or not isinstance(config.n_boot, int)
        or not 1 <= config.n_boot <= MAX_BOOTSTRAPS
    ):
        issues.append(f"{where}: stat.n_boot must be an integer in 1..{MAX_BOOTSTRAPS}")
    if (
        isinstance(config.seed, bool)
        or not isinstance(config.seed, int)
        or config.seed < 0
    ):
        issues.append(f"{where}: stat.seed must be a nonnegative integer")
    if layer.dodge is not None and (not _finite(layer.dodge) or layer.dodge < 0):
        issues.append(f"{where}: dodge must be finite and nonnegative")
    if layer.marker_size is not None and (
        not _finite(layer.marker_size) or layer.marker_size < 0
    ):
        issues.append(f"{where}: marker_size must be finite and nonnegative")
    if layer.orient not in ("v", "h"):
        issues.append(f"{where}: orient must be 'v' or 'h'")
    if layer.orient == "h" and layer.axis == "y2":
        issues.append(f"{where}: horizontal statistical plots do not route to y2")
    if layer.gap is not None and (not _finite(layer.gap) or not 0 <= layer.gap < 1):
        issues.append(f"{where}: gap must be finite in [0, 1)")
    for name in ("stack", "value_labels"):
        if type(getattr(layer, name)) is not bool:
            issues.append(f"{where}: {name} must be boolean")
    if (
        not isinstance(layer.label_format, str)
        or layer.label_format not in LABEL_FORMATS
    ):
        issues.append(f"{where}: label_format must be one of {LABEL_FORMATS}")
    _check_category_order(layer.order, "order", where, issues)
    _check_category_order(layer.hue_order, "hue_order", where, issues)
    if layer.hue_order is not None and layer.group is None:
        issues.append(f"{where}: hue_order requires group")

    # New statistical layers must not silently ignore unrelated primitive
    # settings. Legacy layer validation/serialization behavior is unchanged.
    supported = set(
        LAYER_TYPES[layer.type]["required"] + LAYER_TYPES[layer.type]["optional"]
    )
    defaults = LayerSpec()
    for field in fields(LayerSpec):
        if field.name not in supported | {"type", "citation", "href", "references"}:
            value = getattr(layer, field.name)
            if value is not None and value != getattr(defaults, field.name):
                issues.append(
                    f"{where}: {field.name} is not supported for {layer.type}"
                )

    selected = usable_rows(cols, layer) if layer.semantics is not None else None
    for name in (layer.x, layer.group):
        if not isinstance(name, str) or name not in cols:
            continue
        seen = {}
        values = cols[name] if selected is None else [cols[name][i] for i in selected]
        for value in values:
            if is_missing(value):
                continue
            if not isinstance(value, (str, bool)) and not _finite(value):
                issues.append(f"{where}: categories must be strings or finite scalars")
                break
            label = str(value)
            if label in seen and seen[label] != value:
                issues.append(
                    f"{where}: category labels collide after string conversion"
                )
                break
            seen[label] = value
    if (
        layer.type != "countplot"
        and isinstance(layer.y, str)
        and layer.y in cols
        and any(
            not is_missing(v) and not _finite(v)
            for v in (
                cols[layer.y]
                if selected is None
                else [cols[layer.y][i] for i in selected]
            )
        )
    ):
        issues.append(f"{where}: observations must be finite numbers or missing")
    required = [layer.x] + ([layer.y] if layer.type != "countplot" else [])
    if all(
        isinstance(name, str) and name in cols for name in required
    ) and not usable_rows(cols, layer):
        issues.append(f"{where}: no usable observations after dropping missing rows")


def _stable_group_indices(values) -> list[tuple[object, list[int]]]:
    groups: list[tuple[object, list[int]]] = []
    positions: dict[object, int] = {}
    try:
        for index, key in enumerate(values):
            _ = hash(key)  # route lists/dicts to fallback before comparison
            if key != key:  # e.g. NaN: dict identity differs from explicit equality
                raise TypeError
            if key in positions:
                groups[positions[key]][1].append(index)
            else:
                positions[key] = len(groups)
                groups.append((key, [index]))
        return groups
    except TypeError:
        # ponytail: unusual unhashable/non-reflexive programmatic keys retain
        # the old O(n²) equality fallback; JSON scalar group keys stay linear.
        groups = []
        for index, key in enumerate(values):
            for existing, indices in groups:
                if key == existing:
                    indices.append(index)
                    break
            else:
                groups.append((key, [index]))
        return groups


def _check_regression_data(
    cols, layer, where: str, issues: list[str], *, allow_empty: bool = False, panel=None
) -> None:
    """Check each fitted group before NumPy reaches its linear-algebra path."""
    x_values = cols[layer.x]
    y_values = cols[layer.y]
    if len(x_values) != len(y_values):
        return  # _check_data_integrity reports the shared-table mismatch
    if allow_empty and len(x_values) == 0:
        return
    config = layer.regression
    if config is not None:
        if regression_option_issues(config, layer.degree, layer.confidence):
            return
        if len(x_values) > MAX_REGRESSION_ROWS:
            issues.append(
                f"{where}: typed regression supports at most {MAX_REGRESSION_ROWS} rows"
            )
            return
    if layer.group is None:
        groups = [(None, list(range(len(x_values))))]
    else:
        group_values = cols[layer.group]
        if len(group_values) != len(x_values):
            return
        if layer.hue_order is None:
            groups = _stable_group_indices(group_values)
        else:
            groups = []
            for level in layer.hue_order:
                indices = [
                    i
                    for i, value in enumerate(group_values)
                    if category_key(value) == category_key(level)
                ]
                if indices:
                    groups.append((level, indices))

    if not groups:
        issues.append(f"{where}: regression requires observations")
        return

    for key, indices in groups:
        suffix = f" group {key!r}" if layer.group is not None else ""
        pairs = [(x_values[i], y_values[i]) for i in indices]
        if any(not _finite(value) for pair in pairs for value in pair):
            issues.append(f"{where}{suffix}: regression values must be finite numbers")
            continue
        try:
            distinct_x = len({x for x, _y in pairs})
        except TypeError:
            unique_x: list[object] = []
            for x, _y in pairs:
                if not any(x == seen for seen in unique_x):
                    unique_x.append(x)
            distinct_x = len(unique_x)
        if config is not None:
            issues.extend(
                f"{where}{suffix}: {problem}"
                for problem in regression_group_issues(config, pairs, distinct_x)
            )
            if panel is not None:
                response_axis = panel.y2 if layer.axis == "y2" else panel.y
                if panel.x.scale == "log" and any(x <= 0 for x, _y in pairs):
                    issues.append(
                        f"{where}{suffix}: log x axes require positive coordinates"
                    )
                if (
                    response_axis is not None
                    and response_axis.scale == "log"
                    and any(y <= 0 for _x, y in pairs)
                ):
                    issues.append(
                        f"{where}{suffix}: log y axes require positive coordinates"
                    )
        parameters = layer.degree + 1
        minimum = parameters + (layer.confidence is not None)
        if len(pairs) < minimum:
            issues.append(
                f"{where}{suffix}: degree {layer.degree} regression requires at "
                f"least {minimum} observations"
            )
        if distinct_x < parameters:
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
# punctuation ("_", "&", "#", "%", "?", "~") is fine there too. Braces,
# backslashes, controls, whitespace, relative links, and active/non-web URI
# schemes are unsafe for standalone SVG/PDF output.
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
) -> bool:
    if value is None:
        return False
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{where}: {field_name} must be a non-empty string")
        return False
    bad = sorted(unsafe & set(value))
    if bad:
        issues.append(f"{where}: {field_name} may not contain {''.join(bad)!r} ({why})")
        return False
    return True


def _check_href(href: str | None, where: str, issues: list[str]) -> None:
    valid = _check_ref_field(
        "href",
        href,
        _HREF_UNSAFE,
        "it is substituted into a LaTeX \\href{...} argument verbatim",
        where,
        issues,
    )
    if not valid or not isinstance(href, str):
        return
    if any(char.isspace() for char in href):
        issues.append(f"{where}: href may not contain whitespace")
        return
    try:
        parsed = urlsplit(href)
        hostname = parsed.hostname
        _ = parsed.port  # force validation of a declared port
    except ValueError:
        issues.append(f"{where}: href must be an absolute http, https, or mailto URI")
        return
    scheme = parsed.scheme.lower()
    valid_web = scheme in {"http", "https"} and bool(hostname)
    valid_mail = scheme == "mailto" and not parsed.netloc and bool(parsed.path)
    if not (valid_web or valid_mail):
        issues.append(f"{where}: href must be an absolute http, https, or mailto URI")


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
    _check_href(href, where, issues)


def _check_axis(axis, where: str, issues: list[str]) -> None:
    if axis is None:
        return
    if axis.share_id is not None and (
        not isinstance(axis.share_id, str)
        or not axis.share_id.strip()
        or len(axis.share_id) > 64
        or any(ord(char) < 32 for char in axis.share_id)
    ):
        issues.append(f"{where}: share_id must be a nonempty name up to 64 characters")
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
    source_columns = cols

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
        filter_problems = panel_filter_issues(source_columns, panel)
        issues.extend(f"{where_axis}: {problem}" for problem in filter_problems)
        cols = (
            source_columns if filter_problems else panel_columns(source_columns, panel)
        )
        panel_data = cols
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
            axis = getattr(panel, name)
            _check_axis(axis, f"{where_axis} {name}", issues)
            if (
                axis is not None
                and axis.share_id is not None
                and (name not in ("x", "y") or panel.projection != "2d")
            ):
                issues.append(
                    f"{where_axis}: named sharing supports primary Cartesian x/y only"
                )
        if panel.projection != "2d" and panel.y2 is not None:
            issues.append(f"{where_axis}: secondary y-axis requires projection='2d'")
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
        if panel.projection not in PROJECTIONS:
            issues.append(
                f"{where_axis}: invalid projection {panel.projection!r}; "
                f"valid: {sorted(PROJECTIONS)}"
            )
        if panel.z is not None and panel.projection != "3d":
            issues.append(
                f"{where_axis}: z-axis is configured but projection is "
                f'{panel.projection!r} (z only applies to "3d" panels)'
            )

        for li, layer in enumerate(panel.layers):
            cols = panel_data
            order_valid = True
            where = f"panel {pi} layer {li} ({layer.type})"
            if layer.type in RAW_HUE_TYPES and layer.hue_order is not None:
                try:
                    cols = ordered_group_columns(cols, layer)
                except ValueError as error:
                    issues.append(f"{where}: {error}")
                    order_valid = False
            if layer.type not in LAYER_TYPES:
                issues.append(
                    f"{where}: unknown layer type; valid: {sorted(LAYER_TYPES)}"
                )
                continue
            required = LAYER_TYPES[layer.type]["required"]
            for field_name in required:
                val = getattr(layer, field_name, None)
                if val is None or (isinstance(val, str) and val == ""):
                    issues.append(f"{where}: missing required field {field_name!r}")
            if (
                layer.type in {"hline", "vline"}
                and layer.value is not None
                and not _finite(layer.value)
            ):
                issues.append(f"{where}: value must be a finite number")

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
            elif panel.projection == "polar" and layer.type not in _POLAR_TYPES:
                issues.append(
                    f"{where}: {layer.type!r} is not supported on a polar panel; "
                    f"supported: {sorted(_POLAR_TYPES)}"
                )
            # Capabilities are the contract for which LayerSpec column-name
            # fields each layer actually interprets. Reject ignored fields and
            # malformed optional names before they become renderer KeyErrors.
            supported_fields = set(required) | set(LAYER_TYPES[layer.type]["optional"])
            layer_defaults = LayerSpec()
            for style_field in (
                "bar_width",
                "baseline",
                "edge_color",
                "error_color",
                "error_line_width",
                "capthick",
                "stat",
                "semantics",
                "sort",
                "error_style",
                "error_alpha",
                "ecdf",
                "histogram",
                "heatmap",
                "cluster",
                "regression",
                "kde",
                "kde2d",
                "dodge",
                "orient",
                "native_scale",
                "stat_scale",
                "order",
                "hue_order",
                "gap",
                "stack",
                "value_labels",
                "label_format",
                "width",
                "warn_thresh",
                "k_depth",
                "width_method",
                "outlier_prop",
                "trust_alpha",
                "whis",
                "components",
                "notch",
                "showmeans",
                "showfliers",
                "showmedians",
                "showextrema",
                "bw_method",
                "points",
                "inner",
                "split",
                "density_norm",
                "common_norm",
                "bw_adjust",
                "cut",
                "clip",
            ):
                if (
                    getattr(layer, style_field) != getattr(layer_defaults, style_field)
                    and style_field not in supported_fields
                ):
                    issues.append(
                        f"{where}: {style_field} is not supported for {layer.type}"
                    )
            for col_field in _COLUMN_FIELDS:
                val = getattr(layer, col_field, None)
                empty = val is None or (isinstance(val, str) and val == "")
                if col_field not in supported_fields:
                    if not empty:
                        issues.append(
                            f"{where}: {col_field} is not supported for {layer.type}"
                        )
                elif empty:
                    if (
                        col_field not in required
                        and val == ""
                        and not (col_field == "y" and layer.type in DISTRIBUTION_TYPES)
                    ):
                        issues.append(
                            f"{where}: {col_field} must be a non-empty column "
                            "name or None"
                        )
                elif not isinstance(val, str):
                    issues.append(
                        f"{where}: {col_field} must be a non-empty column name"
                    )
                else:
                    _check_column(cols, val, where, issues)

            if (
                layer.type in _MATRIX_LAYER_TYPES
                and layer.matrix not in spec.data.matrices
            ):
                issues.append(
                    f"{where}: matrix {layer.matrix!r} not found in data "
                    f"(available: {sorted(spec.data.matrices)})"
                )

            if layer.type == "clustermap":
                issues.extend(
                    f"{where}: {problem}"
                    for problem in cluster_issues(
                        spec.data.matrices.get(layer.matrix)
                        if layer.matrix is not None
                        else None,
                        layer,
                        panel,
                        spec,
                    )
                )
            if layer.type == "heatmap":
                issues.extend(
                    f"{where}: {problem}"
                    for problem in heatmap_issues(
                        spec.data.matrices.get(layer.matrix)
                        if layer.matrix is not None
                        else None,
                        layer,
                        panel,
                    )
                )
            if layer.type in ("scatter", "lineplot") and layer.semantics is not None:
                issues.extend(
                    f"{where}: {issue}"
                    for issue in semantic_data_issues(cols, layer, panel)
                )

            if layer.type in {"bar", "errorbar"} | STAT_LAYER_TYPES:
                _check_uncertainty(cols, layer, where, issues)
            if layer.type in STAT_LAYER_TYPES:
                _check_statistical_layer(cols, layer, where, issues)
                _check_statistical_scales(cols, layer, panel, where, issues)
                if layer.type == "lineplot":
                    _check_lineplot_layer(cols, layer, where, issues)

            if layer.type == "hist":
                _check_histogram_layer(cols, layer, panel, where, issues)

            if layer.type == "kde":
                _check_kde_layer(cols, layer, panel, where, issues)

            if layer.type == "kde2d":
                _check_kde2d_layer(cols, layer, panel, where, issues)

            if layer.type == "ecdf":
                _check_ecdf_layer(cols, layer, panel, where, issues)

            if layer.type == "swarmplot":
                _check_distribution_layer(cols, layer, where, issues)
                width = 0.8 if layer.width is None else layer.width
                if not _finite(width) or not 0 < width <= 1:
                    issues.append(f"{where}: swarm width must be in (0, 1]")
                if layer.dodge is not None and (
                    not _finite(layer.dodge)
                    or not _finite(width)
                    or not 0 <= layer.dodge <= width
                ):
                    issues.append(f"{where}: swarm dodge must be in [0, width]")
                if layer.warn_thresh is not None and (
                    not _finite(layer.warn_thresh) or not 0 <= layer.warn_thresh <= 1
                ):
                    issues.append(f"{where}: warn_thresh must be a fraction in [0, 1]")
                if layer.marker not in (None, "o"):
                    issues.append(
                        f"{where}: swarm currently supports circular marker='o' only"
                    )
                for name in ("marker_size", "line_width"):
                    number = getattr(layer, name)
                    if number is not None and (
                        not _finite(number)
                        or not 0 <= number <= 1000
                        or (name == "marker_size" and number == 0)
                    ):
                        issues.append(
                            f"{where}: {name} must be a finite size <=1000 "
                            "(marker_size must be positive)"
                        )
                _check_distribution_scales(cols, layer, panel, where, issues)
                rows = distribution_rows(cols, layer)
                if len(rows) > MAX_SWARM_POINTS:
                    issues.append(
                        f"{where}: swarm supports at most {MAX_SWARM_POINTS} "
                        "usable observations per layer"
                    )

            if layer.type in DISTRIBUTION_TYPES:
                _check_distribution_layer(cols, layer, where, issues)
                _check_distribution_scales(cols, layer, panel, where, issues)
                if layer.type in {"box", "boxenplot"}:
                    issues.extend(
                        f"{where}: {issue}" for issue in component_issues(layer)
                    )
                if layer.type == "violin":
                    _check_violin_layer(cols, layer, panel, where, issues)
                if layer.type == "boxenplot":
                    issues.extend(
                        f"{where}: {issue}"
                        for issue in letter_value_option_issues(
                            layer.k_depth,
                            layer.width_method,
                            layer.outlier_prop,
                            layer.trust_alpha,
                        )
                    )
                    if layer.marker not in (
                        None,
                        "o",
                        "d",
                        "D",
                        "s",
                        "^",
                        "v",
                        "+",
                        "x",
                        ".",
                        "*",
                    ):
                        issues.append(f"{where}: unsupported boxenplot flier marker")
                    width = 0.8 if layer.width is None else layer.width
                    if not _finite(width) or not 0 < width <= 1:
                        issues.append(f"{where}: boxenplot width must be in (0, 1]")
                    if layer.dodge is not None and (
                        not _finite(layer.dodge)
                        or not _finite(width)
                        or not 0 <= layer.dodge <= width
                    ):
                        issues.append(f"{where}: boxenplot dodge must be in [0, width]")
                    for name in ("marker_size", "line_width"):
                        number = getattr(layer, name)
                        if number is not None and (
                            not _finite(number) or not 0 <= number <= 1000
                        ):
                            issues.append(f"{where}: {name} must be in [0,1000]")

            if layer.type == "quiver":
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
                issues.extend(
                    f"{where}: {problem}"
                    for problem in regression_option_issues(
                        layer.regression, layer.degree, layer.confidence
                    )
                )
                config = layer.regression
                value_axis = panel.y2 if layer.axis == "y2" else panel.y
                if (
                    config is not None
                    and getattr(config, "residual", False)
                    and (value_axis is not None and value_axis.scale != "linear")
                ):
                    issues.append(f"{where}: residual response axes must be linear")
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
                    and order_valid
                ):
                    _check_regression_data(
                        cols,
                        layer,
                        where,
                        issues,
                        panel=panel,
                        allow_empty=bool(
                            panel.filters or panel.dropna or layer.hue_order is not None
                        ),
                    )

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

    _check_shared_category_scales(spec, colsn, issues)
    issues.extend(shared_scale_issues(spec))
    return issues


def assert_valid(spec: FigureSpec) -> None:
    """Raise ``ValueError`` with all issues joined, if any."""
    issues = validate(spec)
    if issues:
        bullet = "\n  - ".join(issues)
        raise ValueError(f"invalid FigureSpec:\n  - {bullet}")
