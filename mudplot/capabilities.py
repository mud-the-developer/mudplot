"""Machine-readable description of what the engine can do.

Designed for AI agents: a single ``capabilities()`` call returns everything an
agent needs to plan a figure — layer types and their fields, available themes /
journals / TeX presets / palette kinds, and the full action vocabulary. Pure
and dependency-free.
"""

from __future__ import annotations

from dataclasses import MISSING, fields

from . import actions as _actions
from ._categorical import MAX_SWARM_POINTS
from ._ecdf import ECDF_STATS
from ._facet import FACET_LAYER_TYPES, MAX_FACET_PANELS
from ._histogram import (
    HISTOGRAM_ELEMENTS,
    HISTOGRAM_MULTIPLES,
    HISTOGRAM_STATS,
    MAX_BIVARIATE_BINS,
    MAX_HISTOGRAM_BINS,
)
from ._kde import MAX_KDE_POINTS
from ._kde2d import MAX_KDE2D_LEVELS, MAX_KDE2D_POINTS, MAX_KDE2D_ROWS
from ._letter_value import DEPTH_METHODS, MAX_LETTER_DEPTH, WIDTH_METHODS
from ._semantics import MARKERS, MAX_CURVES, MAX_LEVELS, MAX_ROWS
from ._stat import (
    COUNT_STATS,
    ESTIMATORS,
    INTERVAL_LEVELS,
    INTERVAL_METHODS,
    MAX_BOOTSTRAPS,
)
from ._violin_options import MAX_INNER_OBSERVATIONS
from .spec import (
    MAX_FIGURE_LAYERS,
    MAX_FIGURE_PANELS,
    MAX_RENDER_PIXELS,
    ECDFSpec,
    HistogramSpec,
    KDE2DSpec,
    KDESpec,
    SemanticSpec,
    StatSpec,
)
from .theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES

__all__ = [
    "BACKEND_CAPABILITIES",
    "LAYER_TYPES",
    "PALETTE_KINDS",
    "PALETTE_PRESETS",
    "PROJECTIONS",
    "capabilities",
]

# Per-layer field guidance (what an agent should provide for each layer type).
PROJECTIONS = ("2d", "polar", "3d")

LAYER_TYPES: dict[str, dict[str, list[str]]] = {
    "line": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "line_width",
            "line_style",
            "drawstyle",
            "marker",
            "marker_size",
            "alpha",
            "axis",
        ],
    },
    "stem": {
        "required": ["x", "y"],
        "optional": [
            "baseline",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "alpha",
            "axis",
        ],
    },
    "stairs": {
        "required": ["x", "bins"],
        "optional": [
            "baseline",
            "label",
            "color",
            "line_width",
            "line_style",
            "alpha",
            "axis",
        ],
    },
    "eventplot": {
        "required": ["x"],
        "optional": [
            "baseline",
            "width",
            "label",
            "color",
            "line_width",
            "line_style",
            "alpha",
            "axis",
        ],
    },
    "broken_barh": {
        "required": ["x", "y"],
        "optional": [
            "baseline",
            "width",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
            "alpha",
            "axis",
        ],
    },
    "regplot": {
        "required": ["x", "y"],
        "optional": [
            "regression",
            "weights",
            "degree",
            "confidence",
            "group",
            "hue_order",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "alpha",
            "axis",
        ],
    },
    "scatter": {
        "required": ["x", "y"],
        "optional": [
            "semantics",
            "group",
            "hue_order",
            "label",
            "color",
            "marker",
            "marker_size",
            "alpha",
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
            "axis",
        ],
    },
    "stripplot": {
        "required": ["x", "y"],
        "optional": [
            "jitter",
            "group",
            "hue_order",
            "label",
            "color",
            "marker",
            "marker_size",
            "alpha",
            "axis",
        ],
    },
    "swarmplot": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "semantics",
            "orient",
            "order",
            "hue_order",
            "width",
            "dodge",
            "gap",
            "native_scale",
            "warn_thresh",
            "label",
            "color",
            "edge_color",
            "line_width",
            "marker",
            "marker_size",
            "alpha",
        ],
    },
    "stackplot": {
        "required": ["x", "y", "group"],
        "optional": ["color", "line_width", "line_style", "alpha", "axis"],
    },
    "quiver": {
        "required": ["x", "y", "u", "v"],
        "optional": [
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
            "label",
            "color",
            "line_width",
            "quiver_scale",
            "quiver_width",
            "alpha",
            "axis",
        ],
    },
    "bar": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "bar_width",
            "edge_color",
            "line_width",
            "yerr",
            "y_lower",
            "y_upper",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
            "alpha",
            "axis",
        ],
    },
    "barplot": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "stat",
            "native_scale",
            "stat_scale",
            "baseline",
            "orient",
            "order",
            "hue_order",
            "gap",
            "value_labels",
            "label_format",
            "label",
            "color",
            "bar_width",
            "edge_color",
            "line_width",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
            "alpha",
            "axis",
        ],
    },
    "pointplot": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "stat",
            "native_scale",
            "stat_scale",
            "orient",
            "order",
            "hue_order",
            "dodge",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
            "alpha",
            "axis",
        ],
    },
    "lineplot": {
        "required": ["x", "y"],
        "optional": [
            "semantics",
            "cmap_kind",
            "group",
            "stat",
            "orient",
            "stat_scale",
            "hue_order",
            "sort",
            "error_style",
            "error_alpha",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
            "alpha",
        ],
    },
    "countplot": {
        "required": ["x"],
        "optional": [
            "group",
            "stat",
            "native_scale",
            "baseline",
            "orient",
            "order",
            "hue_order",
            "gap",
            "stack",
            "value_labels",
            "label_format",
            "label",
            "color",
            "bar_width",
            "edge_color",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "errorbar": {
        "required": ["x", "y"],
        "optional": [
            "yerr",
            "xerr",
            "y_lower",
            "y_upper",
            "group",
            "hue_order",
            "label",
            "color",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
            "marker",
            "marker_size",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "band": {
        "required": ["x", "y", "y2"],
        "optional": ["group", "hue_order", "label", "color", "alpha", "axis"],
    },
    "hline": {
        "required": ["value"],
        "optional": [
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "vline": {
        "required": ["value"],
        "optional": [
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "text": {
        "required": ["text", "at"],
        "optional": ["color", "alpha", "axis"],
    },
    "annotate": {
        "required": ["text", "at"],
        "optional": ["to", "color", "alpha", "axis"],
    },
    "hist": {
        "required": ["x"],
        "optional": [
            "bins",
            "density",
            "histogram",
            "group",
            "hue_order",
            "orient",
            "label",
            "color",
            "edge_color",
            "line_width",
            "alpha",
        ],
    },
    "boxenplot": {
        "required": ["x"],
        "optional": [
            "y",
            "group",
            "orient",
            "order",
            "hue_order",
            "width",
            "dodge",
            "gap",
            "native_scale",
            "stat_scale",
            "k_depth",
            "components",
            "width_method",
            "outlier_prop",
            "trust_alpha",
            "showfliers",
            "showmedians",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "alpha",
        ],
    },
    "box": {
        "required": ["x"],
        "optional": [
            "y",
            "group",
            "orient",
            "order",
            "hue_order",
            "width",
            "dodge",
            "gap",
            "native_scale",
            "stat_scale",
            "whis",
            "components",
            "notch",
            "showmeans",
            "showfliers",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
            "marker",
            "marker_size",
            "alpha",
        ],
    },
    "hist2d": {
        "required": ["x", "y"],
        "optional": [
            "bins",
            "density",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "axis",
        ],
    },
    "hexbin": {
        "required": ["x", "y"],
        "optional": [
            "gridsize",
            "mincnt",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "axis",
        ],
    },
    "heatmap": {
        "required": ["matrix"],
        "optional": [
            "heatmap",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "line_width",
            "edge_color",
        ],
    },
    "clustermap": {
        "required": ["matrix"],
        "optional": [
            "cluster",
            "heatmap",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "line_width",
            "edge_color",
        ],
    },
    "contour": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels"],
    },
    "contourf": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels"],
    },
    "violin": {
        "required": ["x"],
        "optional": [
            "y",
            "group",
            "orient",
            "order",
            "hue_order",
            "width",
            "dodge",
            "gap",
            "native_scale",
            "stat_scale",
            "bw_method",
            "points",
            "weights",
            "inner",
            "split",
            "density_norm",
            "common_norm",
            "bw_adjust",
            "cut",
            "clip",
            "marker",
            "marker_size",
            "showmeans",
            "showmedians",
            "showextrema",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
            "alpha",
        ],
    },
    "ecdf": {
        "required": ["x"],
        "optional": [
            "ecdf",
            "group",
            "hue_order",
            "orient",
            "label",
            "color",
            "line_width",
            "line_style",
            "alpha",
        ],
    },
    "kde": {
        "required": ["x"],
        "optional": [
            "kde",
            "group",
            "hue_order",
            "orient",
            "label",
            "color",
            "alpha",
            "line_width",
            "line_style",
            "edge_color",
        ],
    },
    "kde2d": {
        "required": ["x", "y"],
        "optional": [
            "kde2d",
            "group",
            "hue_order",
            "label",
            "color",
            "alpha",
            "line_width",
            "line_style",
            "edge_color",
        ],
    },
    "rug": {
        "required": ["x"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "alpha",
            "line_width",
            "line_style",
        ],
    },
    "pie": {
        "required": ["x", "y"],
        "optional": ["color", "alpha"],
    },
    "scatter3d": {
        "required": ["x", "y", "z"],
        "optional": [
            "group",
            "label",
            "color",
            "marker",
            "marker_size",
            "alpha",
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
        ],
    },
    "line3d": {
        "required": ["x", "y", "z"],
        "optional": [
            "group",
            "label",
            "color",
            "line_width",
            "line_style",
            "marker",
            "alpha",
        ],
    },
    "surface": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "wireframe": {
        "required": ["matrix"],
        "optional": ["color", "alpha"],
    },
}

PALETTE_KINDS = ["qualitative", "sequential", "diverging"]

# Named, pre-verified qualitative presets (see mudplot.color.palette for the
# generator that consumes these). Kept here, not in mudplot.color.palette,
# so this plain data stays reachable without importing numpy -- capabilities()
# is part of the dependency-free declarative core (see tests/test_no_deps.py).
PALETTE_PRESETS: dict[str, dict] = {
    # General-purpose default: verified CVD-safe + true-greyscale-safe for
    # n=3..6 categories (see tests/test_palette_presets.py).
    "paper": {
        "params": {
            "lightness": 60.0,
            "chroma": 58.0,
            "hue_start": 270.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 6,
        "description": "Balanced default; safe for up to 6 categories.",
    },
    # Higher chroma for slides/posters; also verified for n=3..6.
    "vivid": {
        "params": {
            "lightness": 68.0,
            "chroma": 52.0,
            "hue_start": 315.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 6,
        "description": "More saturated; safe for up to 6 categories.",
    },
    # Lower-chroma, lighter set for large-area fills (bar/heatmap
    # backgrounds) where full saturation is visually too heavy; only
    # verified safe up to n=5 -- combine with .encoding(hatches=[...]) or
    # more categories.
    "soft": {
        "params": {
            "lightness": 68.0,
            "chroma": 36.0,
            "hue_start": 280.0,
            "lightness_jitter": 18.0,
        },
        "max_verified_n": 5,
        "description": "Muted/pastel; safe for up to 5 categories.",
    },
}


def _default_of(f):
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:  # type: ignore[misc]
        return f.default_factory()
    return None


def _action_fields(cls) -> list[dict]:
    return [
        {
            "name": f.name,
            "type": _type_name(f.type),
            "required": f.default is MISSING and f.default_factory is MISSING,
            "default": _default_of(f),
        }
        for f in fields(cls)
    ]


def _type_name(tp) -> str:
    name = getattr(tp, "__name__", str(tp))
    # avoid a bare "|" in union type names (e.g. "str | None") leaking into
    # markdown/pipe-table renderings downstream; "or" reads fine either way.
    return name.replace(" | ", " or ")


def action_vocabulary() -> dict[str, list[dict]]:
    """All dispatchable actions and their fields (name/type/default)."""
    return {
        name: _action_fields(cls)
        for name, cls in sorted(_actions.ACTION_REGISTRY.items())
    }


# What each output format actually preserves. Reference metadata
# (citation/href) is backend-dependent -- raster formats can only show
# plain text, SVG can make an entry a clickable link, and PGF emits real
# \figcite{...}/\href{...}{...} macros the *document* resolves at TeX-compile
# time. Exposed so an agent/editor can warn e.g. "citations are only kept in
# PGF export" instead of that being implicit renderer behaviour.
BACKEND_CAPABILITIES = {
    "png": {
        "vector": False,
        "citations": False,
        "hyperlinks": False,
        "requires_tex": False,
    },
    "pdf": {
        "vector": True,
        "citations": False,
        "hyperlinks": False,
        "requires_tex": False,
    },
    "svg": {
        "vector": True,
        "citations": False,
        "hyperlinks": True,
        "requires_tex": False,
    },
    "pgf": {
        "vector": True,
        "citations": True,
        "hyperlinks": True,
        "requires_tex": True,
    },
}


def _journal_profiles() -> dict:
    """Consolidated publication constraint profiles for known journals
    (see ``mudplot.theme.JOURNAL_PROFILES``) -- column/text geometry,
    base/tick/min font sizes, default figure size, recommended DPI, and
    grayscale/CVD policies.
    """
    from .theme import JOURNAL_PROFILES

    return {name: prof.to_dict() for name, prof in JOURNAL_PROFILES.items()}


def capabilities() -> dict:
    """Return a machine-readable summary of the engine's capabilities."""
    from ._cluster import CLUSTER_METHODS, CLUSTER_METRICS, MAX_CLUSTER_DIMENSION
    from ._heatmap import MAX_HEATMAP_ANNOTATIONS
    from ._pair import MAX_PAIR_VARIABLES
    from ._regression import MAX_LOWESS_ROWS, MAX_REGRESSION_ROWS, REGRESSION_MODELS
    from .spec import ClusterSpec, HeatmapSpec, RegressionSpec
    from .tex import TEX_PRESETS

    return {
        "spec_version": _spec_version(),
        "layers": LAYER_TYPES,
        "projections": list(PROJECTIONS),
        "themes": list(AVAILABLE_THEMES),
        "facets": {
            "action": "SetFacets",
            "fields": _action_fields(_actions.SetFacets),
            "panel_selector": "filters: exact JSON scalar matches on up to two columns",
            "max_panels": MAX_FACET_PANELS,
            "supported_layers": sorted(FACET_LAYER_TYPES),
            "template": "one completed unfiltered primary Cartesian2D panel",
            "ordering": "first-seen/explicit levels; row-major; col-only wrap",
            "statistics": "row selection before cell-local estimation/normalization",
            "semantics": "pooled original selected row IDs; named shared domains",
            "layout": "explicit cells; later edits panel-scoped; size unchanged",
            "data_updates": "selectors/orders persist; rebuild to add new levels",
            "raw_groups": "hue_order selects/reserves; raw rows/gaps/values kept",
            "limits": "no matrices/3D/polar/y2/c colourbars; "
            "hist needs typed config and common explicit edges; kde needs KDESpec",
        },
        "joint_grid": {
            "action": "SetJointGrid",
            "fields": _action_fields(_actions.SetJointGrid),
            "main": ["scatter", "regplot", "hist2d", "hexbin"],
            "marginals": "hist count/density/probability/percent, KDE density, "
            "or ECDF count/probability/percent",
            "layout": "main top-left, y right, x below; no fourth axes",
            "selection": "dynamic complete x/y/group cases; source table intact",
            "sharing": "x by column, y by row; density axes remain independent",
            "limits": "one raw primary Cartesian2D template; "
            "no semantics/c/y2/weights; binned centers require "
            "no group/hue_order/colourbar",
        },
        "pair_grid": {
            "action": "SetPairGrid",
            "fields": _action_fields(_actions.SetPairGrid),
            "max_variables": MAX_PAIR_VARIABLES,
            "cells": "raw scatter off diagonal; typed hist/KDE/ECDF diagonal",
            "selection": "pairwise complete rows; diagonal variable-only rows",
            "sharing": "named x columns/y off-diagonal rows; density y independent",
            "limits": "2..8 numeric vars; categorical group; no corner/weights; "
            "ECDF needs non-density stat and unused default bins",
        },
        "named_axis_sharing": {
            "field": "AxisSpec.share_id",
            "action": "SetAxisShare",
            "axes": ["x", "y"],
            "limits": "primary Cartesian; figure mode none; same scales/limits",
        },
        "heatmap": {
            "fields": _action_fields(HeatmapSpec),
            "defaults": HeatmapSpec().to_dict(),
            "norms": ["linear", "log"],
            "center": "linear diverging TwoSlope; inferred bounds symmetric",
            "robust": "unmasked finite-value 2nd/98th percentiles",
            "mask": "same-shaped booleans; hidden values excluded from norm/text",
            "annotations": "raw values/bounded formats; alpha-aware text contrast",
            "max_annotations": MAX_HEATMAP_ANNOTATIONS,
            "borders": "typed layer line_width/edge_color in points",
            "legacy": "heatmap=None retains old imshow display",
            "limits": "finite rectangular matrix; no custom text/cluster/date axes",
        },
        "clustermap": {
            "fields": _action_fields(ClusterSpec),
            "defaults": ClusterSpec().to_dict(),
            "methods": list(CLUSTER_METHODS),
            "metrics": list(CLUSTER_METRICS),
            "max_dimension": MAX_CLUSTER_DIMENSION,
            "optional": "mudplot[cluster], scipy>=1.10 for clustering effects",
            "orders": "fit or supplied linkage; labels/mask/colours follow leaves",
            "standardization": "row/col sample z-score or min-max, mutually exclusive",
            "mask": "display only; does not remove fit or standardization values",
            "layout": "own Cartesian panel; no axis sharing/cropped limits/overlays",
            "data": "source matrix unchanged; fit-time transformation/order only",
            "limits": "one colour strip/axis; no missing data/continuous strip legend",
        },
        "stem": {
            "orientation": "vertical numeric positions and heads; rows unchanged",
            "baseline": "raw scalar, default zero; positive on log response axes",
            "max_rows": MAX_ROWS,
            "limits": "primary/y2 Cartesian only; no group/semantics/facet/weights",
        },
        "stairs": {
            "values": "x names the supplied height column; bins stores N+1 edges",
            "geometry": "vertical outline, scalar baseline default zero; no rebinning",
            "max_rows": MAX_ROWS,
            "limits": "linear primary/y2 only; no fill/open/group/facet/weights",
        },
        "eventplot": {
            "positions": "one numeric train, source and duplicate events retained",
            "geometry": "vertical marks; baseline offset, width length in raw units",
            "max_rows": MAX_ROWS,
            "limits": "linear primary/y2; no group/facet/weights/log/date mappings",
        },
        "broken_barh": {
            "intervals": "x=start, y=positive duration; rows/overlaps retained",
            "band": "baseline=bottom, width=positive raw height; defaults 0/1",
            "max_rows": MAX_ROWS,
            "limits": "linear primary/y2 single band; no date/group/facet mappings",
        },
        "regression": {
            "fields": _action_fields(RegressionSpec),
            "defaults": RegressionSpec().to_dict(),
            "models": list(REGRESSION_MODELS),
            "residual": "residplot alias; observed y minus in-sample fitted response",
            "optional": "mudplot[regression], statsmodels>=0.14.1",
            "confidence": "normal-approx poly/logx only; no bootstrap",
            "grouping": "fit after panel/hue selection; source rows retained",
            "max_rows": MAX_REGRESSION_ROWS,
            "max_lowess_rows": MAX_LOWESS_ROWS,
            "failures": "nonfinite/singular/separated/unconverged fits raise",
            "legacy": "regression=None retains old polynomial effects",
            "weights": "LayerSpec.weights; relative poly/logx point fits/raw "
            "residuals; zero rows excluded; scaling must remain representable",
            "limits": "no weighted CI/robust/logistic/LOWESS; "
            "no bootstrap/deviance residuals/residual smooth trend",
        },
        "statistics": {
            "estimators": list(ESTIMATORS),
            "interval_methods": list(INTERVAL_METHODS),
            "interval_constraints": {
                "se": "sample-mean SEM only",
                "count": "no intervals",
            },
            "default_levels": dict(INTERVAL_LEVELS),
            "max_bootstraps": MAX_BOOTSTRAPS,
            "fields": _action_fields(StatSpec),
            "layer_defaults": {
                "barplot": StatSpec().to_dict(),
                "pointplot": StatSpec().to_dict(),
                "lineplot": StatSpec().to_dict(),
                "countplot": StatSpec(estimator="count", errorbar=None).to_dict(),
            },
            "axes": "Cartesian 2-D primary native/log; legacy linear ordinal y2 only",
            "unknown_stat_options": "rejected, never silently ignored",
            "category_scale": "ordinal default; explicit numeric native/log",
            "stat_scale": "raw default; axis log mean/median/min/max + inverse",
            "log_intervals": "SD/SEM/PI/CI in declared space; no endpoint clipping",
            "axis_log_estimators": ["mean", "median", "min", "max"],
            "baseline": "bar/count raw endpoint base; log needs explicit positive base",
            "bar_endpoint": "estimate, not baseline+estimate; labels show estimate",
            "log_stack": "no log values; native/log categories + linear stacks",
            "native_sizes": "bar_width in (0,1], point dodge [0,1] times min spacing",
            "orientations": ["v", "h"],
            "category_argument": "x remains categorical, y remains the value even in h",
            "empty_levels": "reserve slots, never invent estimates or legend entries",
            "stack": "countplot only; additive counts/proportions/percentages",
            "missing_rows": "drop missing required rows; countplot needs no y",
            "singleton_intervals": "omitted with a render warning",
            "weights": True,
            "weighted_methods": "mean with None or paired-row percentile bootstrap CI",
            "zero_weights": "excluded from estimation and resampling",
            "repeated_measures": True,
            "unit_resampling": "resample units, then rows within each selected unit",
            "unit_point_estimate": "observation-weighted, not an equal-unit mean",
            "count_statistics": list(COUNT_STATS),
            "count_denominator": "all usable selected rows across categories and hues",
            "callable_estimators": False,
        },
        "scatter_semantics": {
            "fields": _action_fields(SemanticSpec),
            "defaults": SemanticSpec().to_dict(),
            "roles": "independent hue/size/style, not inferred redundant grouping",
            "scale_id": "named figure pool, identical settings except legend",
            "shared_rows": "unique member rows in original table order",
            "shared_guides": "pooled scope guides, once per panel; dataset labels kept",
            "shared_palette": "one reserved colour block per name, legacy cannot shift",
            "sharing_limits": "pool <=10000 rows/64levels/enough distinct markers",
            "hue": "categorical LCH slots or explicit numeric linear mapping",
            "size": "numeric/categorical diameters in points; native area=diameter**2",
            "style": "categorical unique filled markers; no cycling/repeating",
            "orders": "selected/reserved levels; missing rows drop listwise",
            "norms": "selected global bounds or explicit mapping-only clipped bounds",
            "constant": "numeric auto-constant maps midpoint, one numeric guide",
            "legend": "observed categories / numeric mapping guides, no plotted data",
            "max_levels": MAX_LEVELS,
            "max_rows": MAX_ROWS,
            "markers": list(MARKERS),
            "limits": "primary2D numeric x/y; no group/c, colorbar, date/y2, outline",
            "legacy": "semantics=None leaves existing group/c/marker calls unchanged",
        },
        "lineplot": {
            "coordinates": "numeric predictor x; horizontal swaps display only",
            "default": "mean/seeded pointwise CI band; raw line primitive unchanged",
            "interval_scope": "per-x cells, not simultaneous or whole-curve bootstrap",
            "sort": "ascending default; False per-hue first observed x order",
            "bands": "monotonic x; split at missing bounds, no fake singleton CI",
            "weights_units": "shared mean/paired CI and within-x unit bootstrap",
            "axes": "primary2D; raw/log predictors; explicit data/axis response fit",
            "semantics": "independent raw hue/size/style tuples define curves",
            "size": "sizes interpolate main stroke widths in points, not marker area",
            "style": "unique filled markers; optional distinct named dashes",
            "shared": "figure scale_id pools row domains; per-geometry guide blocks",
            "numeric_curves": "clipping changes appearance, never merges raw curves",
            "limits": "no categorical/date x, y2, dodge, callable/whole-curve CI",
            "max_semantic_curves": MAX_CURVES,
        },
        "render_budget": {"max_canvas_pixels": MAX_RENDER_PIXELS},
        "figure_structure": {
            "max_panels": MAX_FIGURE_PANELS,
            "max_layout_cells": MAX_FIGURE_PANELS,
            "max_layers": MAX_FIGURE_LAYERS,
        },
        "bivariate_density": {
            "max_bins_per_axis": MAX_BIVARIATE_BINS,
            "max_hexbin_gridsize": MAX_BIVARIATE_BINS,
        },
        "histogram": {
            "fields": _action_fields(HistogramSpec),
            "defaults": HistogramSpec().to_dict(),
            "statistics": list(HISTOGRAM_STATS),
            "multiple": list(HISTOGRAM_MULTIPLES),
            "elements": list(HISTOGRAM_ELEMENTS),
            "max_bins": MAX_HISTOGRAM_BINS,
            "legacy": "histogram=None preserves old density/group/bin/alpha effects",
            "bins": "pooled shared equal-width integer bins or explicit raw edges",
            "membership": "[left,right), final edge closed; outside mass excluded",
            "weights": "finite nonnegative paired rows; missing/zero weights dropped",
            "normalization": "in-bin mass: common_norm=True pooled, False per-curve",
            "width": "density/frequency divide raw data bin widths, not log widths",
            "cumulative": "count/mass sums; density integrates mass; no frequency",
            "axes": "primary2D v/h; positive raw observation log, linear heights",
            "style": "bars/hatches or unfilled steps/dashes; exact alpha/edge/width",
            "step": "native stairs; layer/stack only; edge_color overrides stroke",
            "geometry": "grouped stack/dodge keep heights; dodge splits raw bin width "
            "including reserved empty hues",
            "precision": "scaled mass/prefixes; nonfinite/collapsed geometry fails",
            "limits": "no fill/poly/step dodge/discrete/auto estimator/2D/KDE/y2",
        },
        "kde": {
            "fields": _action_fields(KDESpec),
            "defaults": KDESpec().to_dict(),
            "max_points": MAX_KDE_POINTS,
            "legacy": "kde=None keeps 1.06*sample-SD*n**(-1/5)/200-point fit",
            "weights": "nonnegative relative row mass, not sample replication",
            "bandwidth": "unbiased weighted SD times factor*bw_adjust; effective n",
            "methods": ["scott", "silverman", "positive covariance factor"],
            "rows": "paired missing/zero weights/hue deselection excluded",
            "normalization": "all usable selected mass, including singular hues",
            "clip": "evaluation only; never trims fit rows or renormalizes tails",
            "common_grid": "pooled weighted support, per-curve bandwidths retained",
            "cumulative": "analytic full Gaussian CDF from -infinity, not ECDF",
            "singular": "skip without fake bandwidth; warn_singular controls warning",
            "axes": "primary2D v/h; positive raw/log observations + support",
            "density_units": "raw data even on logs; linear density/CDF axis only",
            "style": "line or fill; exact alpha/width; hue dash/hatch slots",
            "limits": "no bivariate/stack/multiple/date/y2/kernel/callable/log fit",
            "precision": "scaled sums/covariance, bounded chunks; invalid derived fail",
        },
        "kde2d": {
            "fields": _action_fields(KDE2DSpec),
            "defaults": KDE2DSpec().to_dict(),
            "max_points_per_axis": MAX_KDE2D_POINTS,
            "max_usable_rows": MAX_KDE2D_ROWS,
            "max_levels": MAX_KDE2D_LEVELS,
            "weights": "relative paired x/y row mass, not sample replication",
            "covariance": "unbiased weighted full covariance, effective n",
            "bandwidth": "d=2 Scott=Silverman=n_eff**(-1/6); numeric factor",
            "normalization": "all usable selected mass incl skipped singular hues",
            "support": "cut/clip evaluation only; pooled grid, conditional fits",
            "levels": "increasing enclosed HDR fractions conditional on grid mass",
            "quadrature": "raw-coordinate trapezoidal nodes; ties all included",
            "level_precision": "approximate grid HDR, not CI/full-space coverage",
            "singular": "skip rank deficient, no jitter/regularization or fake fit",
            "axes": "Cartesian2D raw x/y; positive observations + support on logs",
            "style": "native contours/fill, exact alpha/outline, hue dash/hatch",
            "limits": "no cumulative/orient/date/y2/colorbar/kernel/log fit/kwargs",
            "precision": "scaled covariance/product, bounded point-row matrices",
        },
        "ecdf": {
            "fields": _action_fields(ECDFSpec),
            "defaults": ECDFSpec().to_dict(),
            "statistics": list(ECDF_STATS),
            "definition": "right-continuous mass of X<=t; complement is X>t",
            "weights": "finite nonnegative; count sums weights, not number of rows",
            "normalization": "within each selected curve, not across hues",
            "rows": "drop required missing and zero-weight rows before positivity",
            "ties": "aggregate equal values into one full jump",
            "empty": "no curve/legend; explicit hue order reserves color/style",
            "support": "finite numeric; full jump at min; no tail extension",
            "axes": "primary Cartesian2D; v/h; positive observation log, linear mass",
            "precision": "scaled proportion sums; strict tails summed from the right",
            "unknown": "reject ignored options; no fit/intervals/censoring/2-D ECDF",
        },
        "distribution_components": {
            "box": ["body", "whisker", "cap", "median", "mean", "flier"],
            "boxenplot": ["body", "median", "flier"],
            "defaults": "None inherits existing layer/native/hue/tier defaults",
            "precedence": "component overrides layer shorthand; body color keeps tiers",
            "colors": "hex RGB/RGBA, basic names, C0..C9 or none",
            "stroke": "named styles; finite sizes in [0,1000]",
            "alpha": "fraction [0,1], exact override including 0/1",
            "hatch": "body only; <=32 native symbols; empty disables redundant hatch",
            "mean": "requires showmeans=True; style does not infer visibility",
            "hidden": "reject styles for explicitly hidden median/fliers",
            "unknown": "reject unknown component/property keys; no arbitrary kwargs",
        },
        "violin": {
            "inner": ["legacy", "box", "quart", "point", "stick", None],
            "default_inner": "legacy",
            "density_norm": ["width", "area", "count"],
            "default_density_norm": "width",
            "common_norm": "area/count: across hues; False compares within hue",
            "area": "common KDE density scale, not exact truncated polygon area",
            "count": "peak-normalized profile times row count or weight mass / max",
            "weights": "relative paired rows; unbiased covariance/effective n",
            "weighted_inner": "inverse weighted ECDF quartiles; weighted mean",
            "weighted_rows": "missing/zero rows dropped; no replication or sampling",
            "weighted_limit": MAX_INNER_OBSERVATIONS,
            "split": "two selected/reserved hues; shared center; no positive dodge",
            "bw_adjust": "finite multiplier in (0,1000], default 1",
            "cut": "finite in [0,10] bandwidths, default 0",
            "clip": "increasing finite/None raw-value bounds; KDE support only",
            "inner_rows": "point/stick <=10000 usable rows; no silent sampling",
            "singular": "finite degenerate body, never invent a KDE or sample",
            "log": "stat_scale controls fitted coordinates; clip stays raw units",
            "unknown_options": "callable KDE and arbitrary inner_kws rejected",
        },
        "categorical_scales": {
            "layers": [
                "box",
                "violin",
                "boxenplot",
                "swarmplot",
                "barplot",
                "pointplot",
                "countplot",
            ],
            "native_scale_default": False,
            "native_levels": "finite numeric scalars, not bool/strings/dates",
            "native_order": "select/reserve numeric positions, not physical reorder",
            "spacing": "minimum selected/reserved spacing in axis coordinates",
            "singleton_spacing": 1,
            "native_log_category": "positive levels; geometry in log10 coordinates",
            "log_value": "positive usable selected observations only",
            "stat_scale_default": "data",
            "stat_scale_axis": "opt-in log10 summaries/KDE, inverse-map all artists",
            "stat_scale_layers": ["box", "violin", "boxenplot", "barplot", "pointplot"],
            "legacy": "ordinal and one-column one-based coordinates unchanged",
            "shared_axes": "reject native/ordinal mixtures or conflicting scales",
        },
        "letter_values": {
            "depth_methods": list(DEPTH_METHODS),
            "max_depth": MAX_LETTER_DEPTH,
            "depth_default": "tukey",
            "named_depths": "bounded to 1..32; explicit integers in 1..32",
            "width_methods": list(WIDTH_METHODS),
            "width_default": "exponential",
            "quantiles": "linear interpolation of usable raw observations per cell",
            "area_widths": "probability mass / band height, normalized within cell",
            "zero_height_area": "zero width; all-constant cells use exponential",
            "outlier_prop": "(0,1), proportion rule only; default 0.007",
            "trust_alpha": "[1e-12,1), trustworthy rule only; default 0.05",
            "tail_points": "raw rows strictly outside outer letter values, not IQR",
            "full_depth": "outer endpoints are min/max, no tail points",
            "width": "total category span in (0,1]; default 0.8",
            "dodge": "total hue span <=width; None auto, 0 overlays hues",
            "flier_markers": ["o", "d", "D", "s", "^", "v", "+", "x", ".", "*"],
            "flier_defaults": "hollow diamond, 3pt; median/tails shown",
            "stroke_sizes": "line_width/marker_size finite in [0,1000] points",
            "axes": "Cartesian 2-D; ordinal or native numeric/log categories",
            "stat_scale": "data default; axis opts into log10 quantiles/area heights",
            "missing_rows": "listwise drop; empty slots have no invented summaries",
            "intervals": "distribution quantiles, not confidence intervals",
            "unknown_options": "reject rather than ignore",
        },
        "swarm": {
            "max_observations": MAX_SWARM_POINTS,
            "packing": "stable display-space greedy circles; repack every draw",
            "markers": ["o"],
            "marker_size": "positive points <=1000; default 6, reject with mapped size",
            "size_semantics": "numeric or categorical size; selected layer guides",
            "size_order": "categorical row selection, reserved ranks, observed guides",
            "size_cohort": "drop missing size with category/value/hue; source retained",
            "size_scale_id": "Swarm-only named original-row pool; sizes not colours",
            "size_pool": "deduplicated original rows <=10000; categorical levels <=64",
            "size_scope": "no facet/dropna/mixed-family pool, semantic hue/style/date",
            "line_width": "points in [0,1000]; default 0.5",
            "category_scale": "ordinal or native numeric/log; x remains category in h",
            "value_scales": ["linear", "positive log"],
            "width": "total category span in (0,1]; default 0.8",
            "dodge": "total hue span <=width; None auto, 0 jointly packs hues",
            "overcrowding": "keep all rows at gutters; greedy packing is not optimal",
            "warn_thresh": "fraction in [0,1]; default 0.05; warn once per collection",
            "unknown_options": "reject rather than ignore",
        },
        "journals": list(AVAILABLE_JOURNALS),
        "palettes": PALETTE_KINDS,
        "palette_presets": PALETTE_PRESETS,
        "backends": BACKEND_CAPABILITIES,
        "tex_presets": {
            name: {
                "columnwidth_pt": ctx.columnwidth_pt,
                "textwidth_pt": ctx.textwidth_pt,
                "fontsize_pt": ctx.fontsize_pt,
                "columns": ctx.columns,
            }
            for name, ctx in TEX_PRESETS.items()
        },
        "journal_profiles": _journal_profiles(),
        "actions": action_vocabulary(),
    }


def _spec_version() -> str:
    from .spec import SPEC_VERSION

    return SPEC_VERSION
