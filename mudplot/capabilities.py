"""Machine-readable description of what the engine can do.

Designed for AI agents: a single ``capabilities()`` call returns everything an
agent needs to plan a figure — layer types and their fields, available themes /
journals / TeX presets / palette kinds, and the full action vocabulary. Pure
and dependency-free.
"""

from __future__ import annotations

from dataclasses import MISSING, fields

from . import actions as _actions
from ._box import MAX_BOX_CELLS, MAX_BOX_FLIERS, MAX_BOX_ROWS
from ._boxen import (
    MAX_BOXEN_CELLS,
    MAX_BOXEN_FLIERS,
    MAX_BOXEN_POLYGONS,
    MAX_BOXEN_ROWS,
)
from ._categorical import MAX_SWARM_POINTS
from ._components import component_markers
from ._density import KERNELS, MAX_FIELD_ROWS, MAX_FIELDS, MAX_JOINT_EDGES
from ._ecdf import ECDF_STATS
from ._facet import FACET_LAYER_TYPES, FILTERED_Y2_LAYER_TYPES, MAX_FACET_PANELS
from ._field_budget import (
    MAX_FIELD_BYTES,
    MAX_FIELD_PAIR_ELEMENTS,
    MAX_FIELD_VERTICES,
    MAX_FIELD_WORK,
)
from ._hdr import MAX_HDR_ACTIVE_CELLS, MAX_HDR_LAMBDA_UPDATES
from ._histogram import (
    HISTOGRAM_BIN_RULES,
    HISTOGRAM_ELEMENTS,
    HISTOGRAM_MULTIPLES,
    HISTOGRAM_STATS,
    MAX_BIVARIATE_BINS,
    MAX_HISTOGRAM_BINS,
)
from ._kde import MAX_KDE_POINTS
from ._kde2d import (
    JOINT_CDF_ABSOLUTE_ERROR,
    MAX_KDE2D_LEVELS,
    MAX_KDE2D_POINTS,
    MAX_KDE2D_ROWS,
)
from ._letter_value import DEPTH_METHODS, MAX_LETTER_DEPTH, WIDTH_METHODS
from ._native_annotations import EFFECT_MARKS
from ._semantics import MARKERS, MAX_CURVES, MAX_LEVELS, MAX_ROWS
from ._stat import (
    COUNT_SCOPES,
    COUNT_STATS,
    ESTIMATORS,
    INTERVAL_LEVELS,
    INTERVAL_METHODS,
    MAX_ACTIVE_SAMPLE_ELEMENTS,
    MAX_ADVANCED_STAT_CELLS,
    MAX_ADVANCED_STAT_ROWS,
    MAX_BOOTSTRAPS,
    MAX_RESAMPLING_WORK,
)
from ._swarm_scope import MAX_SCOPE_INSTANCES
from ._temporal_data import TEMPORAL_LAYER_TYPES
from ._transforms import CHAINS, NAMES, ROLE_SUPPORT
from ._violin_options import MAX_INNER_OBSERVATIONS, MAX_VIOLIN_PROFILES
from .spec import (
    MAX_FIGURE_LAYERS,
    MAX_FIGURE_PANELS,
    MAX_LAYOUT_CELLS,
    MAX_LAYOUT_DEPTH,
    MAX_LAYOUT_GRIDS,
    MAX_RENDER_PIXELS,
    BivariateBinsSpec,
    BoxenBandComponentsSpec,
    BoxenHueComponentsSpec,
    BoxenSpec,
    Camera3DSpec,
    ECDF2DSpec,
    ECDFSpec,
    GridCellSpec,
    GridFieldSpec,
    HDRSpec,
    Histogram2DSpec,
    HistogramSpec,
    InsetSpec,
    KDE2DSpec,
    KDESpec,
    LayoutGridSpec,
    PanelLayoutSpec,
    PanelPlacementSpec,
    SemanticSpec,
    SpatialSpec,
    StairsRebinSpec,
    StairsSpec,
    StatSpec,
    TriangulationSpec,
    VectorSpec,
    ViolinHueComponentsSpec,
    ViolinSpec,
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
    "spectrum": {
        "required": ["x", "spectrum"],
        "optional": [
            "y",
            "label",
            "color",
            "line_width",
            "line_style",
            "alpha",
            "cmap_kind",
            "colorbar",
            "clabel",
            "citation",
            "href",
        ],
    },
    "line": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "semantics",
            "line",
            "native_style",
            "orient",
            "order",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "orient",
            "group",
            "hue_order",
            "semantics",
            "colorbar",
            "clabel",
            "cmap_kind",
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
            "stairs",
            "group",
            "hue_order",
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
            "group",
            "hue_order",
            "lane_step",
            "semantics",
            "colorbar",
            "clabel",
            "cmap_kind",
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
            "group",
            "hue_order",
            "lane_step",
        ],
    },
    "regplot": {
        "required": ["x", "y"],
        "optional": [
            "regression",
            "semantics",
            "edge_color",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "orient",
        ],
    },
    "scatter": {
        "required": ["x", "y"],
        "optional": [
            "semantics",
            "native_style",
            "group",
            "hue_order",
            "label",
            "color",
            "marker",
            "edge_color",
            "line_width",
            "marker_size",
            "alpha",
            "c",
            "scalar_display",
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
            "strip",
            "semantics",
            "cmap_kind",
            "colorbar",
            "clabel",
            "edge_color",
            "line_width",
            "orient",
            "order",
            "dodge",
            "native_scale",
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
            "pack_scope",
            "axis",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "vector",
            "group",
            "hue_order",
        ],
    },
    "barbs": {
        "required": ["x", "y", "u", "v", "vector"],
        "optional": [
            "color",
            "line_width",
            "alpha",
            "axis",
            "group",
            "hue_order",
            "label",
        ],
    },
    "streamplot": {
        "required": ["vector"],
        "optional": ["color", "line_width", "alpha", "label"],
    },
    "quiver3d": {
        "required": ["x", "y", "z", "u", "v", "w", "vector"],
        "optional": ["color", "line_width", "alpha", "group", "hue_order", "label"],
    },
    "bar": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "bar_width",
            "bar_geometry",
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
    "barh": {
        "required": ["x", "y"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "bar_width",
            "bar_geometry",
            "edge_color",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "barplot": {
        "required": ["x", "y"],
        "optional": [
            "semantics",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "semantics",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "line",
            "order",
            "native_scale",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "axis",
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
            "error_magnitudes",
            "native_style",
        ],
    },
    "band": {
        "required": ["x", "y", "y2"],
        "optional": [
            "group",
            "hue_order",
            "label",
            "color",
            "alpha",
            "axis",
            "orient",
            "fill",
            "native_style",
            "line_width",
        ],
    },
    "hlines": {
        "required": ["segments"],
        "optional": [
            "native_style",
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "vlines": {
        "required": ["segments"],
        "optional": [
            "native_style",
            "label",
            "color",
            "line_style",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "hspan": {
        "required": ["span"],
        "optional": ["native_style", "label", "color", "alpha", "axis"],
    },
    "vspan": {
        "required": ["span"],
        "optional": ["native_style", "label", "color", "alpha", "axis"],
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
        "optional": ["color", "alpha", "axis", "annotation", "path_effects"],
    },
    "annotate": {
        "required": ["text", "at"],
        "optional": ["to", "color", "alpha", "axis", "annotation", "path_effects"],
    },
    "patch": {
        "required": ["patch"],
        "optional": [
            "native_style",
            "path_effects",
            "label",
            "color",
            "edge_color",
            "line_width",
            "alpha",
            "axis",
        ],
    },
    "table": {"required": ["table"], "optional": []},
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
            "axis",
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
            "boxen",
            "weights",
            "semantics",
            "axis",
            "colorbar",
            "clabel",
            "cmap_kind",
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
            "box",
            "semantics",
            "axis",
            "cmap_kind",
            "colorbar",
            "clabel",
        ],
    },
    "hist2d": {
        "required": ["x", "y"],
        "optional": [
            "bins",
            "histogram2d",
            "group",
            "hue_order",
            "semantics",
            "orient",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
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
            "scalar_display",
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
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels", "grid"],
    },
    "contourf": {
        "required": ["matrix"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "levels", "grid"],
    },
    "imshow": {
        "required": ["grid"],
        "optional": [
            "matrix",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "scalar_display",
        ],
    },
    "pcolor": {
        "required": ["matrix", "grid"],
        "optional": [
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "edge_color",
            "line_width",
            "scalar_display",
        ],
    },
    "pcolormesh": {
        "required": ["matrix", "grid"],
        "optional": [
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "edge_color",
            "line_width",
            "scalar_display",
        ],
    },
    "spy": {
        "required": ["matrix", "grid"],
        "optional": ["alpha", "color", "marker", "marker_size"],
    },
    "triplot": {
        "required": ["x", "y", "triangulation"],
        "optional": ["color", "line_width", "line_style", "alpha", "label"],
    },
    "tripcolor": {
        "required": ["x", "y", "triangulation"],
        "optional": [
            "c",
            "cmap_kind",
            "colorbar",
            "clabel",
            "alpha",
            "edge_color",
            "line_width",
        ],
    },
    "tricontour": {
        "required": ["x", "y", "c", "triangulation", "levels"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "tricontourf": {
        "required": ["x", "y", "c", "triangulation", "levels"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "trisurf": {
        "required": ["x", "y", "z", "triangulation"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "violin": {
        "required": ["x"],
        "optional": [
            "y",
            "violin",
            "components",
            "semantics",
            "axis",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "semantics",
            "cmap_kind",
            "colorbar",
            "clabel",
            "marker",
            "marker_size",
            "group",
            "hue_order",
            "orient",
            "label",
            "color",
            "line_width",
            "line_style",
            "alpha",
            "axis",
        ],
    },
    "ecdf2d": {
        "required": ["x", "y", "ecdf2d"],
        "optional": [
            "group",
            "hue_order",
            "semantics",
            "orient",
            "axis",
            "label",
            "color",
            "edge_color",
            "line_width",
            "line_style",
            "alpha",
            "cmap_kind",
            "colorbar",
            "clabel",
        ],
    },
    "kde": {
        "required": ["x"],
        "optional": [
            "kde",
            "semantics",
            "stat_scale",
            "cmap_kind",
            "colorbar",
            "clabel",
            "group",
            "hue_order",
            "orient",
            "label",
            "color",
            "alpha",
            "line_width",
            "line_style",
            "edge_color",
            "axis",
        ],
    },
    "kde2d": {
        "required": ["x", "y"],
        "optional": [
            "kde2d",
            "semantics",
            "orient",
            "axis",
            "cmap_kind",
            "colorbar",
            "clabel",
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
            "orient",
            "width",
            "axis",
            "semantics",
            "cmap_kind",
            "colorbar",
            "clabel",
        ],
    },
    "pie": {
        "required": ["x", "y"],
        "optional": ["color", "alpha", "pie_geometry"],
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
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "spatial"],
    },
    "wireframe": {
        "required": ["matrix"],
        "optional": ["color", "alpha", "spatial"],
    },
    "bar3d": {
        "required": ["x", "y", "z", "spatial"],
        "optional": ["color", "alpha"],
    },
    "contour3d": {
        "required": ["matrix", "levels", "spatial"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha", "line_width"],
    },
    "contourf3d": {
        "required": ["matrix", "levels", "spatial"],
        "optional": ["cmap_kind", "colorbar", "clabel", "alpha"],
    },
    "voxels": {
        "required": ["spatial"],
        "optional": ["color", "edge_color", "line_width", "alpha"],
    },
}

for _kind in sorted(EFFECT_MARKS):
    if "path_effects" not in LAYER_TYPES[_kind]["optional"]:
        LAYER_TYPES[_kind]["optional"].append("path_effects")

for _kind in ("hist", "countplot"):
    LAYER_TYPES[_kind]["optional"].extend(
        key
        for key in ("semantics", "colorbar", "clabel", "line_style", "cmap_kind")
        if key not in LAYER_TYPES[_kind]["optional"]
    )

for _name in ROLE_SUPPORT:
    LAYER_TYPES[_name]["optional"].append("transforms")

COORDINATE_PIPELINE = {
    "roles": {name: list(roles) for name, roles in ROLE_SUPPORT.items()},
    "names": list(NAMES),
    "per_role_chains": [list(chain) for chain in CHAINS],
    "max_stages": 4,
    "order": [
        "select original rows",
        "transform coordinates",
        "estimate",
        "owning native move",
        "display scale",
    ],
    "stat_authority": [
        "stat",
        "line",
        "histogram",
        "histogram2d",
        "kde",
        "kde2d",
        "ecdf",
        "ecdf2d",
    ],
    "move_authority": {
        "stripplot": ["strip.jitter_policy", "strip.seed", "jitter", "dodge"],
        "barplot": ["bar_width", "gap"],
        "pointplot": ["dodge"],
        "countplot": ["stack", "baseline"],
        "hist": ["histogram.multiple"],
        "kde": ["kde.multiple", "kde.common_grid"],
    },
    "display_authority": ["PanelSpec.x", "PanelSpec.y", "PanelSpec.y2", "SemanticSpec"],
    "units": (
        "log is base 10; standardize uses selected physical-row population moments; "
        "bins/clip/bounds/limits use projected units"
    ),
    "constraints": (
        "Nonidentity requires a numeric native role and the named hist/KDE "
        "configuration; no same-role clock, log display, or axis fit. "
        "Order/hue/weights/units retain source meanings. Null/omitted does not "
        "change legacy behavior."
    ),
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
    from ._axis_options import (
        DATE_PATTERNS,
        FORMATTERS,
        LOCATORS,
        MAX_FIGURE_CONFIGURED_TICKS,
        MAX_FORMATTED_TICK_CHARACTERS,
        MAX_TICKS_PER_LEVEL,
        SCALES,
        TRANSFORMS,
    )
    from ._cluster import CLUSTER_METHODS, CLUSTER_METRICS, MAX_CLUSTER_DIMENSION
    from ._facet_builders import FACET_BUILDERS
    from ._heatmap import COLORBAR_LOCATIONS, HEATMAP_NORMS, MAX_HEATMAP_ANNOTATIONS
    from ._legend_style import HANDLERS
    from ._line import (
        MAX_LINE_CHOICES,
        MAX_LINE_STATE_BYTES,
        MAX_LINE_TARGETS,
        MAX_LINE_WORK,
        MAX_UNIT_ROWS,
    )
    from ._matrix_budget import (
        MAX_MATRIX_MANAGED,
        MAX_MATRIX_SCIPY_FRAME,
        MAX_MATRIX_WORK,
    )
    from ._pair import MAX_PAIR_VARIABLES
    from ._regression import MAX_LOWESS_ROWS, MAX_REGRESSION_ROWS, REGRESSION_MODELS
    from ._scalar_display import COLORMAPS, EXTENSIONS, NORMS, SCALAR_LAYER_TYPES
    from .spec import (
        AxisTransformSpec,
        ClusterCutSpec,
        ClusterSpec,
        ClusterTrackLevelSpec,
        ClusterTrackSpec,
        ColorbarOptionsSpec,
        CondensedDistanceSpec,
        FormatterSpec,
        HeatmapSpec,
        LineSpec,
        LocatorSpec,
        RegressionBootstrapSpec,
        RegressionComponentsSpec,
        RegressionDiagnosticsSpec,
        RegressionPartialSpec,
        RegressionSamplingSpec,
        RegressionSpec,
        RegressionTrendSpec,
        ScalarDisplaySpec,
        ScaleOptionsSpec,
        SecondaryAxisSpec,
        SharedGuideSpec,
        TickSpec,
    )
    from .tex import TEX_PRESETS
    from .theme import CONTEXT_SCALES

    return {
        "live_facet_templates": {
            "opt_in": "Plot.facet(live=True) / SetLiveFacets",
            "field": (
                "FigureSpec.facet_template; omitted by legacy materialized defaults"
            ),
            "edit": (
                "Plot.facet_template / SetFacetTemplate explicitly replaces all fixed"
                " cells"
            ),
            "saved_views": (
                "materialized panels/local overrides remain authoritative on load"
            ),
            "selectors": (
                "resolved creation orders/selectors frozen; SetData never adds cells"
            ),
            "orders": (
                "same-channel category/hue slots retained; explicit orders/reset "
                "recapture"
            ),
            "local_edits": (
                "ordinary panel actions local; later whole replacement supersedes "
                "overrides"
            ),
            "layout": (
                "N13 nesting/rename/reorder/placement preserve frozen typed selectors; "
                "whole-template replacement retains actual stable IDs and placements"
            ),
            "detach": (
                "removing a live cell leaves saved views; replacing facets/joint/pair "
                "or extending/changing the implicit grid detaches the live recipe"
            ),
            "validation": (
                "all generated frozen-selector views checked; no phantom unfiltered "
                "layer"
            ),
            "limits": (
                "existing64 cells/total layers/row domains and swarm per-layer/scope "
                "bounds"
            ),
        },
        "axis_controls": {
            "status": (
                "N12 isolated implementation; "
                "qualification/integration tracked separately"
            ),
            "fields": {
                model.__name__: _action_fields(model)
                for model in (
                    ScaleOptionsSpec,
                    LocatorSpec,
                    FormatterSpec,
                    TickSpec,
                    AxisTransformSpec,
                    SecondaryAxisSpec,
                )
            },
            "api": "ticks / axis_scale / secondary_xaxis / secondary_axis",
            "actions": ["SetAxisTicks", "SetAxisScale", "SetDerivedAxis"],
            "scales": list(SCALES),
            "locators": list(LOCATORS),
            "formatters": list(FORMATTERS),
            "date_patterns": list(DATE_PATTERNS),
            "transforms": list(TRANSFORMS),
            "axis_fields": ["scale_options", "major_ticks", "minor_ticks"],
            "panel_fields": ["secondary_x", "secondary_y"],
            "legacy": (
                "all new fields appended/None/omit_none; old SetScale JSON "
                "unchanged; independent y2 not repurposed"
            ),
            "tick_units": (
                "axis coordinates; fixed temporal positions are UTC days since "
                "1970, not source timestamp units"
            ),
            "fixed": (
                "finite nonbool strictly increasing/distinct after float "
                "conversion; literal labels require matching fixed positions"
            ),
            "formats": (
                "safe finite named notation/precision; no user format templates, "
                "width, eval, attribute lookup or serialized callbacks"
            ),
            "numeric_precision": (
                "0..12 decimals; general precision1..12; "
                "literal prefix/suffix/unit<=32 characters"
            ),
            "ordinal": (
                "auto preserves existing category locations/labels; only "
                "auto/none/fixed compatible, never numeric half-category ticks"
            ),
            "calendar": (
                "explicit TemporalSpec clock; UTC/fixed offset; named "
                "year/month/week/day/hour/minute/second/microsecond and auto"
            ),
            "calendar_precision": (
                "N12 date/auto/concise use canonical datetime/timedelta, not "
                "distant-epoch num2date rounding; fixed AUTO is date+6-digit "
                "ISO timestamp; old no-opt-in policies unchanged"
            ),
            "concise_policy": (
                "Matplotlib3.8 finite level/zero/offset/trailing-zero policy with "
                "canonical datetimes; fixed temporal positions supported; adapted-"
                "policy license/changes in bundled _matplotlib_notice.txt"
            ),
            "new_scales": (
                "symlog/asinh/logit: finite Cartesian raw numeric geometry; "
                "unsupported statistical/categorical/projection combinations reject"
            ),
            "domain_view": (
                "pure paired x/y (band x/y/y2) view ignores native missing/"
                "nonfinite gaps only for domain checks; source/native parsing/"
                "paths/order remain unchanged"
            ),
            "native_collection_limits": (
                "new-scale bar/errorbar/stem/broken_barh restore prior native "
                "DataLim/minpos/ignore then union actual raw new artist geometry, "
                "including embedded bar errors, for Matplotlib3.8 correctness. "
                "Event exception only actual logit Y-lane half-length geometry; "
                "other event/legacy log/linear paths unchanged, no fake origin"
            ),
            "log_parameters": (
                "base/subs apply everywhere existing log is valid; native log10 "
                "category spacing is multiplicatively equivalent. Scale subs are "
                "minor policy; automatic major locations remain base powers and "
                "explicit locator subs can override either rank"
            ),
            "logit_domain": (
                "strict open(0,1); constant p view uses native0.1 widening on "
                "min(p,1-p), contains data/complement symmetric; unrepresentable "
                "native inverse/domain precision errors, no epsilon/clipping"
            ),
            "secondary": (
                "derived top x/right y only; analytic closed registry with "
                "declared units, view-only conversion; linear/log parents; "
                "right derived y conflicts with independent y2"
            ),
            "secondary_precision": (
                "validate actual visible bounds on every native refresh, "
                "including later zoom; target ULP propagated through analytic "
                "inverse; collapse/nonfinite/domain failures reject"
            ),
            "secondary_date": (
                "unix_seconds converts canonical UTC1970 day*86400, never "
                "source input unit/origin or Matplotlib global epoch"
            ),
            "sharing": (
                "existing legal all/row/col/share_id groups; mixed named/figure "
                "modes remain rejected; exact explicit conflicts reject; None "
                "inheritance only new options in effective view, "
                "no source/clock mutation"
            ),
            "editor": (
                "both UIs keep granular fields; linear/log inverse correct for all "
                "bases; new nonlinear DATA drag disabled per actual target with "
                "reason, unaffected primary handles survive nonlinear y2; "
                "title/legend fractions remain"
            ),
            "max_ticks_per_level": MAX_TICKS_PER_LEVEL,
            "max_figure_configured_ticks": MAX_FIGURE_CONFIGURED_TICKS,
            "max_formatted_tick_characters": MAX_FORMATTED_TICK_CHARACTERS,
            "resource_scope": (
                "physical axis/rank active-location/format operations, shared "
                "inheritance included; preflight before native grids/rules/"
                "requested expansion; repeated calls replace counts; "
                "not cached-Tick RAM bound/SLA or old-limit increase"
            ),
        },
        "signal_spectra": {
            "api": "Plot.spectrum / LayerSpec.spectrum / SpectrumSpec",
            "required": "fs: finite positive nonbool samples/second (Hz)",
            "kinds": [
                "spectrogram",
                "psd",
                "csd",
                "coherence",
                "magnitude",
                "angle",
                "phase",
            ],
            "windows": ["boxcar", "hann", "hamming", "blackman"],
            "detrend": ["none", "mean", "linear"],
            "sides": ["onesided", "twosided"],
            "scaling": ["density", "spectrum"],
            "scale": ["linear", "dB"],
            "segmented": (
                "nfft=None means 256; full windows only; trailing partial retained "
                "but unused"
            ),
            "whole": "magnitude/angle/phase use entire signal; nfft=None, overlap=0",
            "padding": (
                "pad_to >= effective window length; actual FFT parity defines Nyquist"
            ),
            "source": (
                "real plain JSON samples; missing/nonfinite/bool reject; no row "
                "dropping"
            ),
            "csd": (
                "display abs(mean(conj(FFT_x)*FFT_y)); computed phase is not set to "
                "zero"
            ),
            "phase": (
                "radians in ascending frequency order; zero coefficients undefined "
                "gaps; unwrap contiguous defined runs"
            ),
            "coherence": (
                ">=2 complete windows; zero-power bins undefined; no significance claim"
            ),
            "coherence_numeric": (
                "positive consumed-prefix channel scaling before detrend/FFT, then "
                "per-frequency maxima across segment vectors before powers/cross; "
                "exact zero bins stay zero; physical CSD unchanged"
            ),
            "line_references": (
                "nonempty labels/citation/href validated by shared core helpers; "
                "native SVG links and PGF figcite/href"
            ),
            "scalar_color": (
                "shared finite named/hex colour contract; clabel requires a "
                "spectrogram colourbar"
            ),
            "zero_stroke": (
                "line_width=0 uses native no-line style, retaining exact "
                "frequency/value artist data"
            ),
            "coherence_precision": (
                "if channel normalization would erase nonzero consumed samples, raise"
                " floating-point precision error before FFT; unused trailing partial "
                "never influences normalization"
            ),
            "undefined": "derived gaps; all undefined rejects; no positive floor",
            "axes": (
                "primary Cartesian linear nontemporal; no "
                "groups/semantics/weights/selectors"
            ),
            "max_samples_per_channel": 1_000_000,
            "max_fft": 65_536,
            "max_complex_cells": 1_048_576,
            "fft_precision_limit": (
                "zero computed coefficient/power yields derived gaps; float64 "
                "window/detrend/FFT may round tiny true bins to zero; masks are "
                "not physical proof of exact zeros or high-dynamic-range "
                "exact/relative accuracy"
            ),
        },
        "spec_version": _spec_version(),
        "temporal_axes": {
            "status": "F02 in progress; Cartesian statistics/distributions connected",
            "api": "Plot.date_axis / SetTemporalAxis / AxisSpec.temporal",
            "layers": sorted(TEMPORAL_LAYER_TYPES),
            "literal_layers": ["hline", "vline", "text", "annotate"],
            "literal_units": "canonical day coordinates; "
            "temporal_coordinates converts explicit inputs",
            "density_units": "per day for each temporal observation dimension",
            "uncertainty": "absolute endpoints share the declared clock; numeric "
            "error columns use input unit without origin, ISO errors use days",
            "interval_duration": "input numeric unit without origin; "
            "days for ISO starts",
            "native_literals": "stair edges, baselines, event offsets/lengths and "
            "interval band geometry use canonical axis units; ISO stair edges allowed",
            "bounds": "numeric plotting bounds use days; "
            "ISO bin edges for hist and clips for univariate KDE/violin",
            "axes": ["x", "y", "y2"],
            "projection": "Cartesian 2-D, linear scale only",
            "timezones": "UTC or fixed offsets; naive inputs require explicit timezone",
            "coordinate_unit": "UTC days since 1970; bounds use the same coordinates",
            "numeric_input": "explicit s/ms/us/ns/day unit and ISO origin required",
            "precision": "microseconds; unsupported precision/float collapse rejects",
            "source": "raw values, ordering, semantic columns and row IDs preserved",
            "unsupported": "other layer families reject until connected; "
            "F02 not complete",
        },
        "layers": LAYER_TYPES,
        "coordinate_pipeline": COORDINATE_PIPELINE,
        "projections": list(PROJECTIONS),
        "themes": list(AVAILABLE_THEMES),
        "contexts": {"action": "SetContext", "font_factors": CONTEXT_SCALES},
        "custom_categorical_palette": {"field": "PaletteSpec.colors", "max_colors": 64},
        "legend_display": {"ncols_max": 8, "handlers": list(HANDLERS)},
        "facets": {
            "builders": FACET_BUILDERS,
            "action": "SetFacets",
            "fields": _action_fields(_actions.SetFacets),
            "panel_selector": "filters: exact JSON scalar matches on up to two columns",
            "max_panels": MAX_FACET_PANELS,
            "supported_layers": sorted(FACET_LAYER_TYPES),
            "supported_y2_layers": sorted(FILTERED_Y2_LAYER_TYPES),
            "scalar_display_y2": (
                "scatter-c through named P01 scalar calibration; actual x/y2 clocks "
                "remain independent of raw c"
            ),
            "template": (
                "one completed unfiltered Cartesian2D panel; y2 is eligible only "
                "when every layer belongs to supported_y2_layers and its own "
                "coordinate/clock contract is satisfied"
            ),
            "ordering": "first-seen/explicit levels; row-major; col-only wrap",
            "statistics": "row selection before cell-local estimation/normalization",
            "semantics": "pooled original selected row IDs; named shared domains",
            "layout": (
                "materialized edits are panel-local; opt-in live recipes replace "
                "all fixed cells only through explicit SetFacetTemplate; "
                "compatible N13 placement preserves selectors and cell ownership"
            ),
            "data_updates": "selectors/orders persist; rebuild to add new levels",
            "raw_groups": "hue_order selects/reserves; raw rows/gaps/values kept",
            "limits": (
                "no matrices/3D/polar; legacy scatter-c becomes a pooled P01 "
                "scalar display in facets; y2 uses supported_y2_layers, "
                "not a blanket prohibition; semantic/statistic colourbars follow "
                "the actual family contract; hist needs typed config and common "
                "explicit edges; kde needs KDESpec"
            ),
        },
        "joint_grid": {
            "action": "SetJointGrid",
            "fields": _action_fields(_actions.SetJointGrid),
            "main": ["scatter", "regplot", "hist2d", "hexbin"],
            "marginals": "hist count/density/probability/percent, KDE density, "
            "or ECDF count/probability/percent",
            "layout": "main top-left, y right, x below; no fourth axes",
            "selection": "common dynamic complete x/y/raw roles (including scatter c); "
            "positive named weight",
            "temporal": "explicit clocks follow their original observation "
            "into its marginal",
            "sharing": "x to bottom; primary y or actual y2 to right value-y; "
            "statistic axes independent",
            "binned": "typed grouped hist2d; weighted/grouped native hexbin "
            "on one pooled lattice",
            "hexbin_mincnt": (
                "positive physical occupancy, independent of weighted mass"
            ),
            "limits": "one Cartesian 2D center plus annotations; hexbin linear "
            "or calendar coordinates; "
            "extended regression excludes residuals and train/query splits",
        },
        "pair_grid": {
            "action": "SetPairGrid",
            "fields": _action_fields(_actions.SetPairGrid),
            "max_variables": MAX_PAIR_VARIABLES,
            "cells": "raw scatter off diagonal; typed hist/KDE/ECDF diagonal; "
            "lower N13 corner optional",
            "selection": "pairwise complete rows; diagonal variable-only rows; "
            "typed raw roles and optional positive weight",
            "sharing": "named x columns/y off-diagonal rows; statistic axes "
            "independent; supported named semantic scope",
            "temporal": "explicit per-variable clocks on value axes only; "
            "source spellings retained",
            "limits": "2..8 variables; ECDF (including strict complement) needs "
            "non-density stat and unused default bins",
        },
        "named_axis_sharing": {
            "field": "AxisSpec.share_id",
            "action": "SetAxisShare",
            "axes": ["x", "y"],
            "limits": "primary Cartesian; one grid-only y2 link to right value-y; "
            "figure mode none; same scale and limits",
        },
        "native_planar_geometry": {
            "style": {
                "line": [
                    "color",
                    "edge_color",
                    "face_color",
                    "line_width",
                    "line_style",
                    "marker",
                    "marker_size",
                    "marker_edge_width",
                    "alpha",
                ],
                "scatter": [
                    "color",
                    "edge_color",
                    "face_color",
                    "line_width",
                    "line_style",
                    "marker",
                    "marker_size",
                    "alpha",
                ],
                "objects": "ComponentStyleSpec; each mark admits only native traits",
            },
            "segments": (
                "hlines/vlines use finite raw x/y endpoints, not reference fractions"
            ),
            "error_magnitudes": (
                "paired nonnegative asymmetric x/y columns with native endpoint checks"
            ),
            "band": (
                "native vertical/horizontal fill, Boolean where, pre/post/mid, "
                "interpolation"
            ),
            "span": "raw data interval with cross-axis fractions",
            "bars": (
                "bar/barh explicit baseline and align; grouped dodge/layer or signed "
                "stack"
            ),
            "pie": (
                "literal labels/values, wedge/annotation settings and finite formatting"
            ),
            "frames": ["data", "axes", "figure"],
            "patches": ["rectangle", "ellipse", "polygon", "path"],
            "path_codes": ["MOVETO", "LINETO", "CURVE3", "CURVE4", "CLOSEPOLY"],
            "path_effects": ["stroke", "shadow"],
            "tables": "rectangular literal cells and headers; bbox in axes fractions",
            "drag": (
                "Cartesian data text only; axes/figure anchors use stored coordinate "
                "edits"
            ),
        },
        "grid_field": {
            "fields": _action_fields(GridFieldSpec),
            "limits": "primary linear numeric Cartesian; 10000 cells/pixels, "
            "512 explicit levels; figure reservations apply",
            "mesh": "flat requires edges; nearest requires centers; pcolor omits "
            "masked cells, QuadMesh retains masked slots without visible edges",
            "image": "named scalar matrix or inline unit RGB(A) pixels; direct "
            "pixels have per-pixel alpha and no scalar colourbar",
        },
        "triangulation": {
            "fields": _action_fields(TriangulationSpec),
            "topology": "explicit zero-based vertex IDs; True masks a triangle; "
            "no auto triangulation or row reindexing",
            "limits": "10000 vertices, 10000 triangles, 50000 sweep pair visits; "
            "shared finite matrix path and contour budgets",
            "scalar_roles": ["vertex", "face"],
            "surface": "trisurf uses the same XY topology and vertex Z in Cartesian 3D",
        },
        "vector": {
            "fields": _action_fields(VectorSpec),
            "limits": "10000 selected row vectors or grid cells; linear numeric axes",
            "quiver": "None retains legacy; data uses xy scale=1; display is explicit",
            "streamplot": "uniform grids, paired null/mask, at most 64 explicit seeds; "
            "bounded native stepping; length in axes coordinates",
            "barbs": "staff length in points; increments in raw component units",
            "quiver3d": "length scales raw components or sets normalized 3D length",
        },
        "spatial": {
            "fields": _action_fields(SpatialSpec),
            "axes": "primary linear numeric Cartesian 3D",
            "surface": "named Z with explicit nonuniform x/y; full resolution",
            "bar3d": "raw anchors, positive XY footprints and signed Z deltas",
            "contours": (
                "explicit levels in the native direction; optional projection offset"
            ),
            "voxels": "boolean [z][y][x], optional all-three explicit edge vectors",
        },
        "camera3d": {
            "action": "SetCamera3D",
            "fields": _action_fields(Camera3DSpec),
            "bounds": "native display-only camera; never sets data limits",
        },
        "scalar_display": {
            "fields": _action_fields(ScalarDisplaySpec),
            "layers": sorted(SCALAR_LAYER_TYPES),
            "colormaps": list(COLORMAPS),
            "norms": list(NORMS),
            "shared_ranges": (
                "one named raw domain; identical calibration, local guides"
            ),
            "colorbar_options": _action_fields(ColorbarOptionsSpec),
            "extensions": list(EXTENSIONS),
            "coordinates": (
                "numeric Cartesian; no clock, direct RGB(A) or semantic roles"
            ),
        },
        "heatmap": {
            "fields": _action_fields(HeatmapSpec),
            "defaults": HeatmapSpec().to_dict(),
            "norms": list(HEATMAP_NORMS),
            "norm_options": {
                "symlog": "positive linthresh; native base 10 and linscale 1",
                "power": "positive gamma; clipped native mapping",
                "boundary": "finite increasing edges; one swatch per half-open bin",
            },
            "colorbar_options": {
                "fields": _action_fields(ColorbarOptionsSpec),
                "locations": list(COLORBAR_LOCATIONS),
                "units": "explicit display-value ticks; fraction/pad relative to body",
            },
            "center": "linear diverging TwoSlope; inferred bounds symmetric",
            "robust": "unmasked finite-value 2nd/98th percentiles",
            "mask": "same-shaped booleans; hidden values excluded from norm/text",
            "annotations": (
                "raw bounded-format values or same-shaped annot_data strings <=512; "
                "requires annot=True, masks hide text; alpha-aware contrast"
            ),
            "tick_rotations": "optional finite xrotation/yrotation [-360,360] degrees",
            "cluster_annotations": "reordered with original row/column identities",
            "max_annotations": MAX_HEATMAP_ANNOTATIONS,
            "borders": "typed layer line_width/edge_color in points",
            "legacy": "heatmap=None retains old imshow display",
            "limits": (
                "finite rectangular matrix; cell coordinates remain linear indices"
            ),
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
            "missing": "complete_features; actual null, "
            "common observed original features per named fit",
            "distances": {
                "fields": _action_fields(CondensedDistanceSpec),
                "order": "original condensed SciPy order; caller-owned across refresh",
            },
            "cuts": {
                "fields": _action_fields(ClusterCutSpec),
                "rule": "inclusive subtree-max height; optional original-index anchor",
            },
            "tracks": {
                "fields": _action_fields(ClusterTrackSpec),
                "levels": _action_fields(ClusterTrackLevelSpec),
                "limits": "ordered categorical tracks and legends; "
                "no continuous auto-binning",
            },
        },
        "matrix_resources": {
            "scope": "new matrix options only, per figure; "
            "reservations, not process RSS",
            "work_credits": MAX_MATRIX_WORK,
            "managed_bytes": MAX_MATRIX_MANAGED,
            "serial_scipy_frame_bytes": MAX_MATRIX_SCIPY_FRAME,
        },
        "stem": {
            "orientation": "x names locations, y names heads; h plots the "
            "locations on primary/twin y and heads on x; row order retained",
            "baseline": "one raw scalar, default zero; positive on log value axes",
            "max_rows": MAX_ROWS,
            "limits": "Cartesian primary/y2; explicit temporal and numeric axes, "
            "typed groups, fixed facets and shared hue/size/style; no weights",
            "size_unit": "stem stroke width in pt; not head diameter",
        },
        "stairs": {
            "values": "x names supplied heights, bins stores the common source grid",
            "geometry": "vertical supplied windows or explicit conservative rebin; "
            "closed/open/fill; raw baseline defaults to zero",
            "fields": _action_fields(StairsSpec),
            "defaults": StairsSpec().to_dict(),
            "rebin_fields": _action_fields(StairsRebinSpec),
            "rebin_measures": ["mass", "density"],
            "max_rows": MAX_ROWS,
            "limits": "Cartesian primary/y2; groups/fixed facets, date and log "
            "domains; no weights, mapped semantics or estimators",
        },
        "eventplot": {
            "positions": (
                "unconnected native vertical ticks, source rows and duplicates retained"
            ),
            "geometry": "baseline is center and width is full length; typed group slot "
            "adds i * lane_step in raw units; None overlays",
            "max_rows": MAX_ROWS,
            "limits": "Cartesian primary/y2; fixed groups/facets, dates/log and "
            "row-aligned hue, stroke size in pt and dash; no weights or horizontal",
        },
        "broken_barh": {
            "intervals": "x=start, y=positive duration; rows/overlaps retained",
            "band": "baseline=bottom, width=positive raw height; group slot adds "
            "i * lane_step in raw units; None overlays; source paint order",
            "max_rows": MAX_ROWS,
            "limits": "Cartesian primary/y2; fixed groups/facets, dates/log; "
            "elapsed duration uses the X clock unit without origin; "
            "no weights or semantics",
        },
        "regression": {
            "fields": _action_fields(RegressionSpec),
            "defaults": RegressionSpec().to_dict(),
            "models": list(REGRESSION_MODELS),
            "declarations": {
                "bootstrap": {
                    "fields": _action_fields(RegressionBootstrapSpec),
                    "defaults": RegressionBootstrapSpec().to_dict(),
                    "law": "uniform paired positive physical cases; "
                    "original criterion masses",
                },
                "partial": {
                    "fields": _action_fields(RegressionPartialSpec),
                    "methods": ["joint", "two_stage"],
                },
                "sampling": {
                    "fields": _action_fields(RegressionSamplingSpec),
                    "selectors": "existing typed equality filters, "
                    "explicit disjoint train/query",
                },
                "diagnostics": {
                    "fields": _action_fields(RegressionDiagnosticsSpec),
                    "kinds": ["raw", "deviance"],
                },
                "trend": {
                    "fields": _action_fields(RegressionTrendSpec),
                    "models": ["poly", "logx", "robust", "lowess"],
                    "inference": "FULL primary+nuisance+trend; "
                    "root confidence/bootstrap only",
                },
                "components": {
                    "fields": _action_fields(RegressionComponentsSpec),
                    "style": "existing ComponentStyleSpec; "
                    "actual fit/scatter ownership",
                },
            },
            "residual": "existing residplot flag; actual in-sample or explicit query "
            "raw/deviance diagnostic; independently owned continuous trend",
            "semantics": "observed/adjusted/query/diagnostic point face, diameter pt, "
            "and marker only; raw visible original row roles never change a fit cohort",
            "optional": "mudplot[regression], statsmodels>=0.14.1",
            "confidence": "sole Layer.confidence; explicit uniform "
            "paired physical-case "
            "bootstrap for weighted/advanced/residual inference; nominal pointwise, "
            "not simultaneous or future-observation uncertainty",
            "grouping": "typed original physical rows; explicit disjoint train/query; "
            "per-cell fits; all B retained and any required "
            "undefined replicate rejects",
            "max_rows": MAX_REGRESSION_ROWS,
            "max_lowess_rows": MAX_LOWESS_ROWS,
            "failures": "required missing/nonfinite/singular/separated/unconverged, "
            "erased positive mass or positive native span, and infinite finite-native "
            "diagnostics raise atomically; no retry/clipping/listwise omission",
            "legacy": "omitted controls retain existing point arithmetic/admission "
            "and unweighted poly/logx approximate normal mean bands",
            "weights": "relative criterion masses for all five models; original "
            "canonical CDF-left weighted MAD; weighted Huber/LOWESS operators "
            "are selected by weights, not by CI presence",
            "partial": "full design/sole intercept and residual DF for poly/logx; "
            "joint conditional Huber/logit; explicit LOWESS two_stage with add-back",
            "axes": "logical predictor/response on actual v/h primary/y2; raw/ln "
            "fitting is display independent; calendar ln uses canonical UTC-day origin",
            "diagnostic_calibration": "mean-response type7 first, then raw/deviance "
            "map conditional on fixed observed y; full-pipeline trend is separate",
            "new_admission": {
                "logical_work_invocation_and_figure": 6_000_000_000,
                "complete_design_columns": 19,
                "numerical_managed_provider_reserve_bytes": 268_435_456,
                "scope": "conservative numerical admission estimate; not RSS, "
                "native artists or a universal opaque-provider allocation bound",
                "seed": "nonnegative arbitrary integer; variable words/state and w*w "
                "conversion work charged before Generator construction",
            },
            "limits": "no precision/frequency/wild/BCa/simultaneous/prediction method, "
            "fixed-fit trend, result store/API/command or new duration clock; "
            "unsupported calendar-response residual/trend remains refused",
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
            "axes": (
                "bar/point primary or declared y2,vertical/horizontal,native/date/log; "
                "line/count retain their separately declared predictor/target subsets"
            ),
            "unknown_stat_options": "rejected, never silently ignored",
            "category_scale": "ordinal default; explicit numeric native/log "
            "or temporal elapsed",
            "stat_scale": "raw default; axis log mean/median/min/max + inverse",
            "log_intervals": "SD/SEM/PI/CI in declared space; no endpoint clipping",
            "axis_log_estimators": ["mean", "median", "min", "max"],
            "baseline": "bar/count raw endpoint base; log needs explicit positive base",
            "bar_endpoint": "estimate, not baseline+estimate; labels show estimate",
            "log_stack": "countplot raw cumulative tops; positive explicit baseline "
            "below each first mass; no offset/multiplicative stacking",
            "native_sizes": "bar_width in (0,1], point dodge [0,1] times min spacing",
            "orientations": ["v", "h"],
            "category_argument": "x remains categorical, y remains the value even in h",
            "empty_levels": "reserve slots, never invent estimates or legend entries",
            "stack": "countplot only; additive counts/proportions/percentages",
            "missing_rows": "drop missing required rows; countplot needs no y",
            "singleton_intervals": "omitted with a render warning",
            "weights": True,
            "weighted_methods": {
                "mean": [None, "sd", "se", "pi", "ci"],
                "median": [None, "sd", "pi", "ci"],
                "min": [None, "sd", "pi", "ci"],
                "max": [None, "sd", "pi", "ci"],
                "sum": [None, "ci"],
                "count": [None],
            },
            "unit_identity": (
                "opaque strings including empty; missing None/NaN exclude paired rows; "
                "NEW bool/numeric identity is typed"
            ),
            "weighted_total_dimension": (
                "response value*weight-mass in the existing N13 opt-in sharing gate; "
                "unweighted sums remain value"
            ),
            "weighted_quantiles": (
                "LEFT observed values; canonical integer/dyadic mass,"
                "not replicated data"
            ),
            "weighted_PI_percent": (
                "exact Fraction(level):p=(100-level)/200,upper1-p; "
                "legacy unweighted type7 unchanged"
            ),
            "weighted_spread": (
                "reliability sample SD; "
                "mean SE=SD/sqrt(physical-row Kish effective size)"
            ),
            "pointwise_CI": (
                "uniform original-case pairs; percentile estimator distribution,"
                "not simultaneous inference"
            ),
            "canonical_arithmetic": (
                "canonical source values before binary64; finite dyadic sums/means "
                "and moments,strict native interval collapse rejects"
            ),
            "new_only_bounds": {
                "selected_rows": MAX_ADVANCED_STAT_ROWS,
                "drawn_pointwise_cells": MAX_ADVANCED_STAT_CELLS,
                "actual_resampling_work": MAX_RESAMPLING_WORK,
                "active_sample_elements": MAX_ACTIVE_SAMPLE_ELEMENTS,
                "work": (
                    "unit-choice+case instances; seed-dependent whole-effect "
                    "rejection before row chunks/artists/commit; no prefix CI"
                ),
                "predicate": (
                    "new weighted combination OR bar/point semantics OR newly "
                    "admitted bar/point target; never old weights/units/dense plain "
                    "or semantic line alone"
                ),
                "storage": (
                    "O(rows+units+n_boot),bounded compact case counts; "
                    "no SLA/RSS promise"
                ),
            },
            "roles": {
                "barplot": (
                    "hue BODY fill,size BODY outline points,style BODY dash; "
                    "real nondata patch guides"
                ),
                "pointplot": (
                    "hue marker/connecting line,size actual marker diameter points,"
                    "style actual glyph+dash"
                ),
                "error_components": (
                    "error widths/caps and point connecting stroke remain "
                    "independent of mapped main size"
                ),
                "domains": (
                    "raw role tuples/typed identity,original-row domain dedup,"
                    "mark-specific physical guides"
                ),
            },
            "zero_weights": "excluded from estimation and resampling",
            "repeated_measures": True,
            "unit_resampling": "resample units, then rows within each selected unit",
            "unit_point_estimate": "observation-weighted, not an equal-unit mean",
            "count_statistics": list(COUNT_STATS),
            "count_normalization_scopes": list(COUNT_SCOPES),
            "count_denominator": "usable selected row/weight mass, per panel: "
            "all (default), within category, or within group",
            "callable_estimators": False,
        },
        "scatter_semantics": {
            "fields": _action_fields(SemanticSpec),
            "defaults": SemanticSpec().to_dict(),
            "roles": "independent hue/size/style, not inferred redundant grouping",
            "scale_id": "named figure pool, identical settings except legend",
            "shared_rows": "unique member rows in original table order",
            "shared_guides": (
                "panel-owned by default; explicit FigureSpec.shared_guides "
                "consolidates matching scale_id guides; dataset labels stay local"
            ),
            "shared_palette": "one reserved colour block per name, legacy cannot shift",
            "sharing_limits": (
                "pool <=10000 original rows; categorical levels <=64; sufficient "
                "distinct markers/dashes only for the actual mapped native traits"
            ),
            "hue": "categorical LCH slots or explicit numeric linear mapping",
            "size": (
                "mark-specific physical point units in family_units; "
                "never probability mass, bin width or observation data units"
            ),
            "style": (
                "categorical native glyphs and/or dashes as declared per family; "
                "no fabricated point glyphs for stroke-only or field mappings"
            ),
            "orders": "selected/reserved levels; missing rows drop listwise",
            "norms": "selected global bounds or explicit mapping-only clipped bounds",
            "constant": "numeric auto-constant maps midpoint, one numeric guide",
            "colorbar": (
                "optional numeric-hue guide, independent of legend; field statistic "
                "colourbars are separate real mappables, not raw-hue guides"
            ),
            "colorbar_coordinates": (
                "non-data normalized[0,1] guide with exact raw-value tick labels; "
                "same clipped mapping/cmap as marks, no observation-axis changes"
            ),
            "colorbar_constant": "solid midpoint swatch, one exact observed-value tick",
            "colorbar_label": "clabel string <=512 only with requested numeric-hue bar",
            "colorbar_shared_labels": (
                "requested members require identical effective labels"
            ),
            "outline": "scatter edge_color and line_width[0,1000] physical points",
            "legend": "observed categories / numeric mapping guides, no plotted data",
            "max_levels": MAX_LEVELS,
            "max_rows": MAX_ROWS,
            "markers": list(MARKERS),
            "limits": (
                "Cartesian2D; native/log/clock/orientation/y2 eligibility is "
                "family-specific, including supplied and estimated lines; no "
                "legacy c, and legacy group only in its declared compatible route"
            ),
            "legacy": "semantics=None leaves existing group/c/marker calls unchanged",
            "family_units": {
                "scatter": "marker diameter in points; native area=diameter**2",
                "stripplot": "marker diameter in points; category-only jitter/dodge",
                "swarmplot": "nominal diameter points; native glyph/stroke bounds",
                "line": "supplied-curve stroke points; markers remain independent",
                "lineplot": "main stroke width in points",
                "barplot": (
                    "BODY outline stroke width in points,not bar width/height/mass"
                ),
                "countplot": "BODY outline stroke in points, not mass or bar width",
                "hist": (
                    "BODY outline / main stroke in points, not bin width or density"
                ),
                "pointplot": (
                    "actual marker diameter in points; "
                    "connecting/error strokes independent"
                ),
                "ecdf": "step-curve stroke width in points",
                "rug": "individual stroke width in points; height=axes fraction",
                "boxenplot": (
                    "BODY outline stroke points; flier size remains independent"
                ),
                "box": (
                    "BODY outline stroke points; whisker/cap/median strokes and "
                    "mean/flier diameters remain independent"
                ),
                "violin": (
                    "BODY outline stroke points; inner strokes and actual "
                    "point/box-median glyph diameters remain independent"
                ),
                "kde": "main density/CDF stroke points, including a filled outline",
                "hist2d": "actual cell outline stroke points, not area/count/mass",
                "kde2d": "actual contour/cell outline stroke points, not field mass",
                "ecdf2d": "actual joint-CDF cell outline stroke points, not mass",
            },
            "curve_partition": (
                "raw line/lineplot/ECDF keep each distinct RAW role tuple separate; "
                "mapping-bound clipping never merges curves"
            ),
        },
        "lineplot": {
            "coordinates": (
                "native numeric/declared real-clock predictors; optional categorical "
                "LineSpec; actual primary/y2 targets, vertical/horizontal"
            ),
            "default": (
                "mean/seeded per-cell pointwise CI; native_scale=False stays numeric"
            ),
            "line_defaults": LineSpec().to_dict(),
            "calibrations": {
                "percentile": "pointwise bootstrap percentile, not simultaneous",
                "max_deviation": (
                    "exact ceil(Fraction(level)*B/100) upper empirical maximum score "
                    "over finite curve/layer grid; explicit complete units required"
                ),
            },
            "units": (
                "unit mode repeats complete original paired rows/masses, "
                "no within-unit draws/unit means; "
                "cell mode retains C07 unit-then-row schedule"
            ),
            "identity": (
                "explicit non-None inference controls use typed units: True!=1, "
                "False!=0, numeric1==1.0, opaque strings including empty; "
                "omitted/predictor-only identity remains inherited"
            ),
            "undefined": (
                "all B retained; undefined simultaneous target gives +Infinity; "
                "infinite selected rank rejects whole finite band; "
                "pointwise requires all defined"
            ),
            "families": ["curve", "layer"],
            "coverage": (
                "nominal bootstrap only; no continuum, finite-sample "
                "or population guarantee"
            ),
            "extrema": (
                "NEW complete-unit min/max percentile AND max_deviation "
                "are empirical-only envelopes, with mandatory nonregular "
                "warning/caption; not endpoint confidence"
            ),
            "topology": (
                "native grids per raw curve before response omission "
                "plus reservations; categorical pooled ordinal slots; "
                "explicit/grouped missing cells split paths"
            ),
            "geometry": (
                "error_style band/bars independent of calibration; ribbons monotonic"
            ),
            "semantics": (
                "shared raw hue/size/style; line size is physical stroke points"
            ),
            "max_semantic_curves": MAX_CURVES,
            "new_whole_unit_limits": {
                "selected_trajectory_rows": MAX_UNIT_ROWS,
                "structural_slots": MAX_LINE_TARGETS,
                "estimable_targets": MAX_LINE_TARGETS,
                "logical_work": MAX_LINE_WORK,
                "active_int64_choices": MAX_LINE_CHOICES,
            },
            "new_working_state_bytes": MAX_LINE_STATE_BYTES,
            "new_figure_work": (
                "sum actual whole-unit B(U+N+K) + explicit cell C07 unit/case work "
                "+ cell bootstrap reductions; limit2000000000; physical repeats count"
            ),
            "resource_scope": (
                "persisted explicit inference only, on every render; raw mapping, "
                "predictor-only, omitted and non-CI views gain no new inference caps"
            ),
        },
        "raw_line": {
            "meaning": "supplied observations/order/duplicates/gaps, never estimation",
            "roles": (
                "independent hue/stroke-size/marker-style, original shared domains"
            ),
            "barriers": (
                "missing coordinates or semantic keys remain continuity barriers"
            ),
        },
        "shared_guides": {
            "field": "optional FigureSpec.shared_guides list; omitted None",
            "request": SharedGuideSpec("scope").to_dict(),
            "membership": (
                "SemanticSpec.scale_id (default), LayerSpec.raw_guide_id "
                "(kind=raw), or ScalarDisplaySpec.scale_id (kind=scalar); "
                "persisted owners, no panel_ids or label inference"
            ),
            "api": "Plot.shared_guides / authoritative SetSharedGuides list/None",
            "locations": ["outside right", "outside top", "outside bottom"],
            "anchor": "trusted finite [x,y] figure fractions, not clamped",
            "ownership": (
                "only matching semantic guides/colourbars consolidated; dataset labels "
                "and unrelated scales retained; named actual mark-family "
                "effect contexts/units, merging only equivalent native traits"
            ),
            "empty": (
                "persisted owner required; empty selected scope valid "
                "without fake artists"
            ),
        },
        "rug": {
            "coordinates": "x column is observations; v=shared x, h=target y/y2",
            "height": "height stores width; None=0.04; non-bool [0,1] axes fraction",
            "anchor": "vertical bottom inward; horizontal left / y2 right inward",
            "semantics": "shared raw rows; size=stroke points, style=named dashes",
            "dashes": "SemanticSpec.dashes or default -, --, -., :; no cycling",
            "rows": "one collection; no pooling, estimation or curve-count cap",
            "limits": "observation data limits only; perpendicular log/date allowed",
            "temporal": "observation clock only; height never date/density/mass",
        },
        "render_budget": {"max_canvas_pixels": MAX_RENDER_PIXELS},
        "figure_structure": {
            "max_panels": MAX_FIGURE_PANELS,
            "max_layout_cells": MAX_FIGURE_PANELS,
            "max_layers": MAX_FIGURE_LAYERS,
            "max_explicit_grid_nodes": MAX_LAYOUT_GRIDS,
            "max_explicit_grid_cells": MAX_LAYOUT_CELLS,
            "max_layout_depth": MAX_LAYOUT_DEPTH,
        },
        "panel_layout": {
            "fields": {
                model.__name__: _action_fields(model)
                for model in (
                    GridCellSpec,
                    InsetSpec,
                    PanelPlacementSpec,
                    LayoutGridSpec,
                    PanelLayoutSpec,
                )
            },
            "field": "FigureSpec.panel_layout",
            "native_layout_policy": (
                "uniform native tight engine for explicit panel_layout, selected "
                "before axes/colourbars; legacy constrained/3D paths unchanged; "
                "unfittable decoration warnings retained"
                "; measured axis-label/eligible tick-decoration diagnostics, "
                "axis-side union broadphase, never all tick pairs"
            ),
            "sharing_role_boundary": (
                "new role checks require explicit panel_layout or stored panel IDs; "
                "all existing validation remains global, legacy sharing retained"
            ),
            "identity": "PanelSpec.panel_id; deterministic allocation on opt-in only",
            "placement": (
                "PanelSpec.placement: exactly one grid cell/span or parent inset"
            ),
            "grids": (
                "one root; nested native GridSpec/subgridspec; ratios stored unchanged"
            ),
            "mosaic": (
                "rectangular repeated IDs; null empty positions; "
                "normalizes to placements"
            ),
            "inset": (
                "native child axes; contained nonoverlapping siblings; "
                "all 2d/polar/3d combinations"
            ),
            "sharing": (
                "one component resolver; row/col matches immediate grid and exact "
                "span; insets singleton unless all/named; known statistical/spectral "
                "dimensions kept separate"
            ),
            "new_panels": (
                "complete placements cover all existing final IDs; extra named keys "
                "add empty panels in lexicographic ID order, never object-key order"
            ),
            "vector_identity": "identified native SVG axes use mudplot-panel-ID groups",
            "edits": [
                "SetPanelLayout",
                "SetMosaic",
                "NestLayout",
                "SetPanelPlacement",
                "AddInset",
                "RenamePanel",
                "ReorderPanels",
                "RemovePanel",
            ],
            "legacy": (
                "panel_layout omitted retains regular-grid geometry "
                "and index action semantics"
            ),
            "limits": (
                "bounded IDs <=64; no opaque artists/callbacks/kwargs; explicit "
                "expansion needs complete placements; unrepresentable extents reject"
            ),
        },
        "bivariate_density": {
            "models": {
                model.__name__: _action_fields(model)
                for model in (BivariateBinsSpec, Histogram2DSpec, ECDF2DSpec, HDRSpec)
            },
            "max_bins_per_axis": MAX_BIVARIATE_BINS,
            "max_hexbin_gridsize": MAX_BIVARIATE_BINS,
            "histogram2d": {
                "statistics": list(HISTOGRAM_STATS),
                "bins": (
                    "BivariateBinsSpec requires logical x/y counts, existing named "
                    "rules or explicit numeric/clock edges; old flat lists keep "
                    "their existing meaning"
                ),
                "cohort": "positive complete paired rows BEFORE bin-range tally",
                "denominator": (
                    "both coordinates in range; common_norm=True pooled, False "
                    "effective-hue pool, never a separate size/style-tuple pool"
                ),
                "geometry": "H(nx,ny) displayed H.T against true nonuniform edges",
                "kde_overlay": (
                    "SAME pre-tally paired cohort, including out-of-bin rows; "
                    "parent weights inherit/match, common_norm agrees; independent "
                    "full-fit density/CDF levels, never count-height rescaling"
                ),
            },
            "joint_ecdf": {
                "statistics": list(ECDF_STATS),
                "definition": "paired P(X<=qx AND Y<=qy), ties before float",
                "complement": "strict X>qx OR Y>qy, not AND survival",
                "bounds": (
                    "required finite bounds; every interior source knot and query "
                    "retained; bounds/queries do not remove denominator rows"
                ),
                "max_edges_per_axis": MAX_JOINT_EDGES,
                "geometry": "right-continuous rectangular cells, no smoothing",
                "prefix": "canonical exact integer Fenwick/prefix mass, bit-aware work",
            },
            "statistic_guides": (
                "actual field collection ScalarMappable/raw values/norm; separate "
                "normalized non-data calibration with exact raw labels, never "
                "a semantic hue bar or a norm-changing tiny-range expansion"
            ),
            "coordinates": (
                "logical paired columns retain order/IDs; actual Cartesian2D "
                "primary/y2, v/h and declared per-coordinate clocks; explicit "
                "temporal bin/clip/bound/query numbers are canonical UTC days, "
                "not timestamp input units; ISO bounds use the declared zone"
            ),
            "new_resources": {
                "selected_positive_complete_physical_rows_per_layer": MAX_FIELD_ROWS,
                "raw_tuple_fields_per_layer": MAX_FIELDS,
                "categorical_levels": MAX_LEVELS,
                "composite_units_per_NEW_figure": MAX_FIELD_WORK,
                "working_retained_geometry_artist_bytes": MAX_FIELD_BYTES,
                "all_live_numerical_pair_elements": MAX_FIELD_PAIR_ELEMENTS,
                "native_path_vertices_including_closure": MAX_FIELD_VERTICES,
                "scope": (
                    "persisted bivariate-stat/bin-pair/SEM/joint-ECDF or named "
                    "nonlegacy kernel/multiple/actual-log-fit/joint-CDF/full-HDR; "
                    "geometry-only and identity Gaussian requests gain no new "
                    "guard; existing D01/C07 ledgers remain separate"
                ),
                "meaning": (
                    "one figure-wide actual composite cost proxy, including "
                    "owned outward/special-function/scaled/native/limb-sensitive "
                    "integer work; not FLOPs/RSS/SLA, no per-field/level reset"
                ),
                "raster": (
                    "backend RGBA buffers stay outside this allowance under40M pixels"
                ),
                "failure": "whole effect rejects prospectively; no truncated output",
            },
        },
        "histogram": {
            "fields": _action_fields(HistogramSpec),
            "defaults": HistogramSpec().to_dict(),
            "statistics": list(HISTOGRAM_STATS),
            "multiple": list(HISTOGRAM_MULTIPLES),
            "elements": list(HISTOGRAM_ELEMENTS),
            "max_bins": MAX_HISTOGRAM_BINS,
            "legacy": "histogram=None preserves old density/group/bin/alpha effects",
            "bins": "shared integer count, explicit raw edges, or finite rule name",
            "bin_rules": [*HISTOGRAM_BIN_RULES, "discrete"],
            "bin_rule_definition": "fixed v2 classic NumPy1.23 equations; "
            "auto uses FD/Sturges, independent of installed NumPy version",
            "bin_rule_weights": "usable observations once for edges; "
            "positive weight magnitudes affect heights/mass only",
            "discrete": "bins=discrete or hist(discrete=True); integer-centered "
            "input-unit grid, temporal numeric declared unit or ISO clock-day",
            "bin_allocation": "derived count checked before allocation; "
            "over-budget/nonfinite/collapsed/half-unit precision errors reject",
            "membership": "[left,right), final edge closed; outside mass excluded",
            "weights": "finite nonnegative paired rows; missing/zero weights dropped",
            "normalization": "in-bin mass: common_norm=True pooled, False per-curve",
            "width": "density/frequency divide raw data bin widths, not log widths",
            "cumulative": "count/mass sums; density integrates mass; no frequency; "
            "multiple=fill is cumulative composition, not CDF",
            "axes": "Cartesian2D v/h; vertical-only y2 mass axis; positive raw "
            "observation log, linear heights",
            "fill": "None keeps filled bars/unfilled step/poly; "
            "explicit bool changes geometry only",
            "style": "filled colors/hatches or outline strokes/dashes; "
            "exact alpha/width",
            "step": "native stairs; layer/stack/dodge/fill; "
            "edge_color overrides stroke",
            "poly": "native raw-bin/slot-center segments; >=2 representable centers; "
            "None is an unfilled line; bool fill controls native area",
            "composition": "multiple=fill divides existing heights by their bin sum "
            "after stat/common_norm/cumulative; dimensionless, not raw-mass override",
            "geometry": "grouped stack/dodge keep heights; dodge splits raw bin width "
            "including reserved empty hues",
            "precision": "scaled mass/prefixes; nonfinite/collapsed geometry fails",
            "limits": (
                "this univariate HistogramSpec has no bivariate stat/KDE or "
                "horizontal y2; use Histogram2DSpec for paired statistics"
            ),
        },
        "kde": {
            "fields": _action_fields(KDESpec),
            "defaults": KDESpec().to_dict(),
            "max_points": MAX_KDE_POINTS,
            "legacy": "kde=None keeps 1.06*sample-SD*n**(-1/5)/200-point fit",
            "weights": "nonnegative relative row mass, not sample replication",
            "bandwidth": "unbiased weighted SD times factor*bw_adjust; effective n",
            "methods": ["scott", "silverman", "positive covariance factor"],
            "kernels": list(KERNELS),
            "multiple": ["layer", "stack", "fill"],
            "rows": "paired missing/zero weights/hue deselection excluded",
            "normalization": (
                "all selected physical mass, including singular skipped tuples; "
                "effective hue only unless common_norm=True pools globally"
            ),
            "clip": "evaluation only; never trims fit rows or renormalizes tails",
            "common_grid": (
                "persisted shared support with separate per-curve fits; "
                "required for stack/fill, no hidden interpolation"
            ),
            "cumulative": (
                "chosen kernel CDF from minus infinity; stacked contributions "
                "and fill composition are labelled as such, not population CDFs"
            ),
            "singular": "skip without fake bandwidth; warn_singular controls warning",
            "axes": (
                "Cartesian2D v/h with observations on the actual x/y/y2 target; "
                "typed/new density/CDF ordinate linear, never a date clock; "
                "omitted legacy ordinate behavior retained"
            ),
            "density_units": (
                "default raw data/day units; explicit stat_scale=axis uses log10 "
                "only on the actual log observation axis, independent of display "
                "base; density_space=data includes Jacobian, fit is working units"
            ),
            "style": "actual line/fill stroke points and dashes, no invented glyphs",
            "limits": (
                "finite named kernels/bandwidth only; explicit clocks for dates; "
                "no inferred symlog/asinh/logit statistical fit or callbacks"
            ),
            "precision": "scaled sums/covariance, bounded chunks; invalid derived fail",
        },
        "kde2d": {
            "fields": _action_fields(KDE2DSpec),
            "defaults": KDE2DSpec().to_dict(),
            "max_points_per_axis": MAX_KDE2D_POINTS,
            "max_usable_rows": MAX_KDE2D_ROWS,
            "max_levels": MAX_KDE2D_LEVELS,
            "kernels": list(KERNELS),
            "weights": "canonical paired relative mass; physical Kish before ties",
            "covariance": (
                "unbiased full covariance; gaussian or variance-one Cholesky "
                "epanechnikov_product, explicitly nonradial"
            ),
            "bandwidth": "d=2 Scott=Silverman=n_eff**(-1/6); finite scalar factor",
            "normalization": (
                "selected full cohort, including skipped singular fields; "
                "effective-hue/global pool, not each size/style tuple"
            ),
            "support": "cut/clip choose evaluation/view only, never trim or rebase fit",
            "level_kinds": ["mass", "density", "cdf"],
            "conditional_default": (
                "absent HDRSpec retains finite-grid trapezoidal mass ranking "
                "with all tied heights; conditional, not full-space coverage"
            ),
            "cumulative": (
                "true original-law joint lower-orthant CDF; no finite-grid "
                "subtraction/renormalization or Jacobian; common_norm amplitude "
                "remains an explicit contribution"
            ),
            "joint_cdf_absolute_error": JOINT_CDF_ABSOLUTE_ERROR,
            "fit_scales": (
                "logical per-input data/axis; actual log uses log10, never display "
                "base; density_space data/fit is explicit; no absolute-clock log fit"
            ),
            "singular": "no jitter/regularization/fake bandwidth or observations",
            "axes": "actual Cartesian2D primary/y2, v/h, declared input clocks",
            "style": "real native contours/cells, physical outline points/dashes",
            "full_hdr": {
                "opt_in": (
                    "HDRSpec(scope=full,tolerance=0.01); absent stays conditional"
                ),
                "conditional_tolerance": "0<tolerance<=0.05; absolute probability",
                "method": (
                    "one fitted source-enclosed whitening chart/root; unknown "
                    "strictly ordered cutoffs, adaptive rectangle mass bounds, "
                    "disjoint earliest-band guaranteed-inside native cell unions"
                ),
                "working_active_cells_per_current_level": MAX_HDR_ACTIVE_CELLS,
                "max_lambda_updates": MAX_HDR_LAMBDA_UPDATES,
                "initial_trial_in_addition": True,
                "statement": (
                    "support/numeric/source-transform/classification/native/clip "
                    "allocations remain separate; bounded conditional target and "
                    "region symmetric-difference error under declared IEEE/"
                    "computed-model assumptions, not an exact infinite-source law"
                ),
                "visibility": "actual clipped probability is reported, not called p",
                "failure": (
                    "unresolved order/precision/tolerance/resource rejects the "
                    "whole effect; no level dropping/conditional fallback"
                ),
            },
            "limits": "no 2D stack/fill ordinate, CDF+mass-HDR or arbitrary callbacks",
            "precision": (
                "canonical source/mass before float; full-exponent scaled and "
                "outward primitives; unresolved derived coordinates stay errors"
            ),
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
            "axes": (
                "Cartesian2D v/h; observations use actual x or target y/y2 clock; "
                "positive observation log and linear non-calendar mass axis"
            ),
            "precision": (
                "canonical dyadic source/mass before ties; percent unit combined "
                "before final float, strict complement from exact right mass"
            ),
            "semantics": "shared raw hue/size/style tuples; size=stroke points",
            "markers": (
                "filled named markers at actual right-continuous knots only; "
                "never the prepended boundary sentinel; explicit marker_size points"
            ),
            "unknown": (
                "reject ignored options; no fit/intervals/censoring; explicit "
                "paired empirical fields use ecdf2d, not an inferred univariate option"
            ),
        },
        "distribution_components": {
            "box": ["body", "whisker", "cap", "median", "mean", "flier"],
            "boxenplot": ["body", "median", "flier"],
            "violin": {
                "legacy": ["body", "mean", "median", "extrema"],
                "box": ["body", "whisker", "box", "median"],
                "quart": ["body", "quartile"],
                "point": ["body", "point"],
                "stick": ["body", "stick"],
                "None": ["body"],
            },
            "defaults": "None inherits existing layer/native/hue/tier defaults",
            "precedence": "component overrides layer shorthand; body color keeps tiers",
            "colors": "hex RGB/RGBA, basic names, C0..C9 or none",
            "stroke": "named styles; finite sizes in [0,1000]",
            "alpha": "fraction [0,1], exact override including 0/1",
            "hatch": "body only; <=32 native symbols; empty disables redundant hatch",
            "mean": (
                "box requires showmeans=True; violin legacy component may "
                "enable None, explicit False rejects"
            ),
            "hidden": "reject styles for explicitly hidden median/fliers",
            "unknown": "reject unknown component/property keys; no arbitrary kwargs",
        },
        "box_workflow": {
            "api": "Plot.box / Plot.bxp; same box layer, optional LayerSpec.box",
            "summary": (
                "existing median/q1/q3/whislo/whishi columns; optional mean/CI/fliers"
            ),
            "summary_order": (
                "whislo <= q1 <= median <= q3 <= whishi; absolute observation units"
            ),
            "summary_missing": (
                "only required fields drop rows; optional missing marks keep box"
            ),
            "availability": (
                "requested showmeans/notch/showfliers need supplied marks; no "
                "reconstruction"
            ),
            "fliers": (
                "list-valued column; [] supplied none, None unavailable; strictly "
                "outside whiskers"
            ),
            "median_ci": (
                "raw median percentile bootstrap; level(0,100), n_boot1..100000, seed"
            ),
            "seed": (
                "existing nonbool nonnegative int; private same-seed cell schedule"
            ),
            "singleton": "retain box, warn and omit requested bootstrap notch",
            "cap_fraction": (
                "finite nonbool[0,1] of FINAL dodge/gap body width in category "
                "working coordinates; 0 retains caps"
            ),
            "native_defaults": (
                "raw absent whis/visibility inherit actual rc; requested caps "
                "enable caps not body"
            ),
            "per_hue": (
                "typed raw-key entries, bool != number; known/reserved "
                "categorical hue only"
            ),
            "hue_role": "BODY facefill only; component colors/edges independent",
            "size_role": (
                "BODY outline stroke pt only, not width/mass/marker diameter/"
                "other component strokes"
            ),
            "style_role": (
                "BODY dash AND real FLIER glyph via serialized markers, "
                "default cycle included"
            ),
            "precedence": (
                "native/theme -> layer -> owned mappings -> global components -> "
                "per-hue fields; mapped-property conflicts reject"
            ),
            "guides": (
                "actual native box/line styles; shared normalized raw-label huebar"
            ),
            "geometry": (
                "v/h/native/log/inversion/date category+observation/y2/facet/live"
            ),
            "live": (
                "same explicit recipe; effective category source owns slots, "
                "literal orders remain literal"
            ),
            "max_drawn_cells": MAX_BOX_CELLS,
            "max_selected_source_rows": MAX_BOX_ROWS,
            "max_total_declared_flier_values": MAX_BOX_FLIERS,
            "bounds": (
                "separate row AND flier bounds before native work; "
                "legacy no-new-request limits unchanged"
            ),
            "unsupported": (
                "bootstrap from quartiles, arbitrary kwargs/callbacks, unknown "
                "or numeric-per-value hue overrides"
            ),
        },
        "violin": {
            "fields": {
                model.__name__: _action_fields(model)
                for model in (ViolinSpec, ViolinHueComponentsSpec)
            },
            "max_selected_source_rows": MAX_INNER_OBSERVATIONS,
            "max_drawn_profiles": MAX_VIOLIN_PROFILES,
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
            "paired_split": (
                "ViolinSpec split_policy=paired: frozen hue pairs in separate "
                "half-body lanes; odd final left half; H=1 valid"
            ),
            "semantic_roles": (
                "raw tuples partition fits; hue owns body fill, size=body outline "
                "stroke pt, style=body dashes and actual point/box-median glyphs"
            ),
            "normalization_pool": (
                "effective hue, not the size/style tuple; common_norm=True global"
            ),
            "components": (
                "native body/whisker/box/quartile/point/stick/mean/median/extrema "
                "traits; strict raw categorical per-hue overrides"
            ),
            "advanced_limits": (
                "10000 selected source rows and256 drawn profiles/layer; "
                "categorical levels64; numeric hue/size not capped at64"
            ),
            "axes": (
                "applicable primary/y2, v/h, native/log and category/measurement "
                "clocks; no inferred nonlinear statistics"
            ),
            "bw_adjust": "finite multiplier in (0,1000], default 1",
            "cut": "finite in [0,10] bandwidths, default 0",
            "clip": (
                "raw absolute measurement support bounds, finite/None or "
                "calendar literals through the actual target clock; no row trim"
            ),
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
            "fields": {
                model.__name__: _action_fields(model)
                for model in (
                    BoxenSpec,
                    BoxenBandComponentsSpec,
                    BoxenHueComponentsSpec,
                )
            },
            "max_selected_positive_instances_per_advanced_layer": MAX_BOXEN_ROWS,
            "max_drawn_cells_per_advanced_layer": MAX_BOXEN_CELLS,
            "max_actual_advanced_band_polygons_per_figure": MAX_BOXEN_POLYGONS,
            "max_requested_advanced_flier_instances_per_figure": MAX_BOXEN_FLIERS,
            "advanced_bounds": (
                "effect-native-expansion admission, not SLA/RSS/marker-size promise; "
                "source validation does not fit summaries; render derives once, "
                "admits actual budgets before native allocation and reuses geometry; "
                "repeated physical uses count; hidden unrequested fliers excluded "
                "from drawing work, never from summary tails; "
                "legacy admission unchanged"
            ),
            "weighted_quantiles": (
                "LEFT inverse empirical CDF, exact canonical relative weights; "
                "endpoints min/max; no equality midpoint or replicated rows"
            ),
            "weighted_depth": (
                "physical-row Kish n_eff stopping, exact binary-exponent comparisons; "
                "non-CI heuristic; tie splitting can change depth"
            ),
            "weighted_mass": (
                "empirical [low,high), last closed; duplicate internal edges empty; "
                "band plus strict-tail mass exactly one"
            ),
            "band_components": (
                "central rank0, lower/upper ranks1..31; rank stable across named "
                "depth; layer/hue components then layer-band then hue-band fieldwise"
            ),
            "semantic_roles": (
                "actual body hue without mapped tail tint; size=BODY outline stroke "
                "pt; style=body dash and only actual observed flier glyph"
            ),
            "shared_raw_domains": (
                "matching scale_id/config pools selected original row IDs with "
                "scatter/line/other accepted marks; normalization is shared, "
                "physical stroke/diameter units and guides remain mark-specific"
            ),
            "depth_methods": list(DEPTH_METHODS),
            "max_depth": MAX_LETTER_DEPTH,
            "depth_default": "tukey",
            "named_depths": "bounded to 1..32; explicit integers in 1..32",
            "width_methods": list(WIDTH_METHODS),
            "width_default": "exponential",
            "quantiles": "unweighted type7, correctly rounded finite interpolation",
            "area_widths": "probability mass / band height, normalized within cell",
            "zero_height_area": "zero width; all-constant cells use exponential",
            "outlier_prop": "(0,1), proportion rule only; default 0.007",
            "trust_alpha": "[1e-12,1), trustworthy rule only; default 0.05",
            "tail_points": "raw rows strictly outside outer letter values, not IQR",
            "full_depth": "outer endpoints are min/max, no tail points",
            "width": "total category span in (0,1]; default 0.8",
            "dodge": "total hue span <=width; None auto, 0 overlays hues",
            "flier_markers": list(component_markers("boxenplot")),
            "flier_marker_context": (
                "scalar LayerSpec.marker and actual flier components"
            ),
            "semantic_style_markers": list(MARKERS),
            "semantic_style_marker_context": (
                "existing filled-only SemanticSpec cycle, distinct capacity; "
                "not the broader scalar/component flier glyph contract"
            ),
            "flier_defaults": "hollow diamond, 3pt; median/tails shown",
            "stroke_sizes": "line_width/marker_size finite in [0,1000] points",
            "axes": "Cartesian2D v/h, native numeric/date/log, value clocks and y2",
            "stat_scale": "data default; axis opts into log10 quantiles/area heights",
            "missing_rows": "listwise drop; empty slots have no invented summaries",
            "intervals": "distribution quantiles, not confidence intervals",
            "unknown_options": "reject rather than ignore",
        },
        "strip_categories": {
            "opt_in": (
                "StripSpec, semantics or explicit orient/order/dodge/native_scale"
            ),
            "legacy": "omitted controls preserve raw-x jitter and old JSON",
            "jitter_policies": ["uniform", "none"],
            "seed": "local NumPy generator; integer in [0,2**32-1], default 0",
            "jitter": "half-width fraction [0,0.5], default 0.15",
            "jitter_units": (
                "minimum category axis spacing; dodge*spacing/hue_slots when dodged"
            ),
            "dodge": "total span fraction [0,1]; None/0 overlays hues",
            "native": "minimum numeric/date spacing; log10 spacing on numeric log axes",
            "orders": "select/reserve category and hue slots, including empty levels",
            "orientation": "x remains category and y measurement for v/h",
            "rows": (
                "listwise category/value/hue missing exclusion; "
                "retain source observations"
            ),
            "semantics": (
                "independent hue/size/style with pooled original-row domains; "
                "category/hue order selection and reserved actual hue slots"
            ),
        },
        "swarm": {
            "max_observations": MAX_SWARM_POINTS,
            "packing": (
                "stable display-space native glyph bounds; repack from originals "
                "every draw"
            ),
            "markers": list(MARKERS),
            "marker_size": "positive points <=1000; default 6, reject with mapped size",
            "size_semantics": (
                "shared numeric/categorical diameter points; never weights"
            ),
            "size_order": "categorical row selection, reserved ranks, observed guides",
            "size_cohort": "drop missing size with category/value/hue; source retained",
            "size_scale_id": "shared mixed-family original-row mapping domains",
            "size_pool": "deduplicated original rows <=10000; categorical levels <=64",
            "size_scope": "hue/size/style; explicit observation clocks; v/h and y2",
            "facet_empty": "selected empty cells are frames without data or guides",
            "line_width": "points in [0,1000]; default 0.5",
            "category_scale": "ordinal or native numeric/log/date; x is category in h",
            "value_scales": ["linear", "positive log", "explicit linear temporal"],
            "width": "total category span in (0,1]; default 0.8",
            "dodge": "total hue span <=width; None auto, 0 jointly packs hues",
            "overcrowding": "keep all rows at gutters; greedy packing is not optimal",
            "warn_thresh": "fraction in [0,1]; default 0.05; warn once per collection",
            "unknown_options": "reject rather than ignore",
            "pack_scope": (
                "explicit panel-local compatible members only; None independent"
            ),
            "max_scope_instances": MAX_SCOPE_INSTANCES,
            "scope_instances": "physical drawn instances, never deduplicated by row ID",
            "scope_compatibility": (
                "target axis/orientation/category/order/native/width/dodge/gap; "
                "dodged hue column/order match"
            ),
            "scope_budget": (
                "profiled operation bound, not SLA or raised per-layer limit"
            ),
            "glyph_bounds": (
                "exact old circle radius; conservative native path bbox circles plus "
                "round strokes for other glyphs"
            ),
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
