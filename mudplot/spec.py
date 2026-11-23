"""Declarative, serialisable plot specification.

``FigureSpec`` is the single source of truth for a figure. It contains only
plain data (numbers, strings, lists, nested dataclasses) so it can round-trip
through JSON and be edited by the Rust (serde) frontend that shares the same
schema.

Nothing here touches matplotlib; rendering lives in ``mudplot._render``.
"""

from __future__ import annotations

import types
import typing
from collections.abc import Callable
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Literal, Union, get_args, get_origin

_UNION_ORIGINS = (Union, types.UnionType)

# The *package* version (``mudplot.__version__``) and the *spec* version
# below are independent numbers: not every release changes what a
# FigureSpec looks like on disk, and SPEC_VERSION is the one a Rust/agent
# consumer, or a saved ``.mplot.json``, actually needs to check
# compatibility against. Bump it only for changes to the *serialized*
# shape that an old loader could misinterpret (a field renamed/removed/
# repurposed) -- a new optional field with a safe default (like
# LayerSpec.references) does not need a bump, since old and new loaders
# both handle its absence the same way.
SPEC_VERSION = "0.1"
# Bound declarative expansion before panel/layer construction and native layouts.
MAX_FIGURE_PANELS = 256
MAX_FIGURE_LAYERS = 1024
# Bound owned effect work, not the stored source DPI or capped previews.
MAX_RENDER_PIXELS = 40_000_000
MAX_LAYOUT_GRIDS = 256
MAX_LAYOUT_CELLS = 1024
MAX_LAYOUT_DEPTH = 16

# A migration is a plain dict -> dict function (bumping the "version" key
# itself), keyed by the version it upgrades *from* -- kept dict->dict
# rather than dataclass->dataclass so the same table stays meaningful to
# a future non-Python (e.g. Rust/serde) implementation reading the same
# file format. Empty until SPEC_VERSION's first bump actually needs one.
MIGRATIONS: dict[str, Callable[[dict], dict]] = {}


def migrate_spec_dict(data: dict) -> dict:
    """Upgrade a saved spec dict to the current ``SPEC_VERSION``.

    Both an unrecognized *older* version (no migration registered for it)
    and any *newer* version than this mudplot understands fail loudly here
    rather than silently misinterpreting/dropping fields later.
    """
    if not isinstance(data, dict):
        raise TypeError("FigureSpec must be a JSON object")
    version = data.get("version", SPEC_VERSION)
    seen = set()
    while version != SPEC_VERSION:
        if version in seen:
            raise ValueError(f"circular spec migration detected at version {version!r}")
        seen.add(version)
        migrate = MIGRATIONS.get(version)
        if migrate is None:
            raise ValueError(
                f"don't know how to load spec version {version!r} "
                f"(this mudplot understands {SPEC_VERSION!r}); "
                "upgrade mudplot, or migrate the file by hand"
            )
        data = migrate(data)
        version = data.get("version", SPEC_VERSION)
    return data


# --------------------------------------------------------------------------
# Generic (de)serialisation for nested dataclasses
# --------------------------------------------------------------------------
class SpecBase:
    """Mixin giving dataclasses recursive ``to_dict`` / ``from_dict``."""

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> typing.Self:
        return typing.cast(typing.Self, _from_dict(cls, data))


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _to_dict(getattr(obj, f.name))
            for f in fields(obj)
            if not (f.metadata.get("omit_none") and getattr(obj, f.name) is None)
        }
    if isinstance(obj, (list, tuple)):
        return [_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj


def _from_dict(cls, data: Any):
    origin = get_origin(cls)
    if origin in _UNION_ORIGINS:
        choices = get_args(cls)
        if data is None and type(None) in choices:
            return None
        for choice in choices:
            if choice is type(None):
                continue
            try:
                return _from_dict(choice, data)
            except TypeError:
                pass
        raise TypeError(f"value {data!r} does not match {cls}")
    if data is None:
        if cls is Any or cls is type(None):
            return None
        raise TypeError(f"expected {cls}, got null")
    if isinstance(cls, type) and is_dataclass(cls):
        if not isinstance(data, dict):
            raise TypeError(f"{cls.__name__} must be a JSON object")
        if cls is FigureSpec and isinstance(data.get("panels"), (list, tuple)):
            panels = data["panels"]
            if len(panels) > MAX_FIGURE_PANELS:
                raise ValueError(
                    f"FigureSpec.panels supports at most {MAX_FIGURE_PANELS} panels"
                )
            layer_count = sum(
                len(panel["layers"])
                for panel in panels
                if isinstance(panel, dict)
                and isinstance(panel.get("layers"), (list, tuple))
            )
            if layer_count > MAX_FIGURE_LAYERS:
                raise ValueError(
                    f"FigureSpec supports at most {MAX_FIGURE_LAYERS} total layers"
                )
        if (
            cls is PanelSpec
            and isinstance(data.get("layers"), (list, tuple))
            and len(data["layers"]) > MAX_FIGURE_LAYERS
        ):
            raise ValueError(
                f"PanelSpec.layers supports at most {MAX_FIGURE_LAYERS} layers"
            )
        if (
            cls is PanelLayoutSpec
            and isinstance(data.get("grids"), (list, tuple))
            and len(data["grids"]) > MAX_LAYOUT_GRIDS
        ):
            raise ValueError(f"layout supports at most {MAX_LAYOUT_GRIDS} grids")
        if cls is LayerSpec:
            declared = data.get("transforms")
            if isinstance(declared, (list, tuple)) and not 1 <= len(declared) <= 4:
                raise ValueError("LayerSpec.transforms requires 1..4 stages")
        if getattr(cls, "_reject_unknown_fields", False):
            unknown = set(data) - {f.name for f in fields(cls)}
            if unknown:
                raise ValueError(f"unknown {cls.__name__} field(s): {sorted(unknown)}")
        hints = typing.get_type_hints(cls)
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            try:
                kwargs[f.name] = _from_dict(hints[f.name], data[f.name])
            except (TypeError, ValueError) as error:
                raise type(error)(f"{cls.__name__}.{f.name}: {error}") from error
        return cls(**kwargs)
    if origin in (list, tuple):
        if not isinstance(data, (list, tuple)):
            raise TypeError(f"expected an array for {cls}")
        (item_t,) = get_args(cls) or (Any,)
        seq = [_from_dict(item_t, value) for value in data]
        return tuple(seq) if origin is tuple else seq
    if origin is dict:
        if not isinstance(data, dict):
            raise TypeError(f"expected an object for {cls}")
        args = get_args(cls)
        key_t, val_t = args if len(args) == 2 else (Any, Any)
        return {
            _from_dict(key_t, key): _from_dict(val_t, value)
            for key, value in data.items()
        }
    if origin is Literal:
        if not any(type(data) is type(item) and data == item for item in get_args(cls)):
            raise TypeError(f"expected one of {get_args(cls)}, got {data!r}")
        return data
    if cls is Any:
        return data
    if cls is bool:
        if type(data) is not bool:
            raise TypeError(f"expected bool, got {type(data).__name__}")
    elif cls is int:
        if type(data) is not int:
            raise TypeError(f"expected int, got {type(data).__name__}")
    elif cls is float:
        if type(data) not in (int, float):
            raise TypeError(f"expected number, got {type(data).__name__}")
    elif cls is str and not isinstance(data, str):
        raise TypeError(f"expected str, got {type(data).__name__}")
    return data


# --------------------------------------------------------------------------
# Theme sub-specs  (intuitive, grouped, typed)
# --------------------------------------------------------------------------
@dataclass
class FontSpec(SpecBase):
    family: str = "sans-serif"
    size: float = 10.0
    title_size: float = 11.0
    label_size: float = 10.0
    tick_size: float = 8.5
    use_tex: bool = False


@dataclass
class AxesSpec(SpecBase):
    line_width: float = 0.8
    spines: str = "LB"  # any of L(eft) R(ight) T(op) B(ottom)
    spine_offset: float = 0.0  # outward offset in points ("despine" look)


@dataclass
class GridSpec(SpecBase):
    show: bool = False
    axis: str = "both"  # "x" | "y" | "both"
    line_width: float = 0.5
    alpha: float = 0.5


@dataclass
class TicksSpec(SpecBase):
    direction: str = "out"  # "in" | "out" | "inout"
    major_size: float = 3.0
    minor_size: float = 1.5
    width: float = 0.8
    minor_visible: bool = False
    top: bool = False
    right: bool = False


@dataclass
class PaletteSpec(SpecBase):
    kind: str = "qualitative"  # qualitative | sequential | diverging
    # A named, pre-verified preset (see mudplot.color.palette.PALETTE_PRESETS)
    # fully determines lightness/chroma/hue_start/lightness_jitter below,
    # overriding those four fields; leave None to set them individually.
    preset: str | None = None
    lightness: float = 65.0
    chroma: float = 55.0
    hue_start: float = 20.0
    cvd_safe: bool = True
    colors: list[str] | None = field(
        default=None, metadata={"omit_none": True, "minItems": 1, "maxItems": 64}
    )


@dataclass
class ThemeSpec(SpecBase):
    name: str = "paper"
    font: FontSpec = field(default_factory=FontSpec)
    axes: AxesSpec = field(default_factory=AxesSpec)
    grid: GridSpec = field(default_factory=GridSpec)
    ticks: TicksSpec = field(default_factory=TicksSpec)
    palette: PaletteSpec = field(default_factory=PaletteSpec)
    # redundant encoding: cycle marker/line-style per series *in addition* to
    # colour. Finite cycles complement it; they do not guarantee unlimited
    # categories or readability at every output size.
    redundant_encoding: bool = True
    markers: list[str] = field(
        default_factory=lambda: ["o", "s", "^", "D", "v", "P", "X", "*"]
    )
    line_styles: list[str] = field(default_factory=lambda: ["-", "--", "-.", ":"])
    # hatch patterns cycled per series for area fills (bar/box/violin), same
    # purpose as markers/line_styles: add cues when colours are similar.
    # These finite cycles repeat; inspect the actual physical output.
    hatches: list[str] = field(
        default_factory=lambda: ["", "//", "xx", "..", "\\\\", "oo"]
    )
    context: Literal["paper", "notebook", "talk", "poster"] | None = field(
        default=None, metadata={"omit_none": True}
    )


# --------------------------------------------------------------------------
# Data, layers, axes, panels
# --------------------------------------------------------------------------
@dataclass
class DataSpec(SpecBase):
    """Inline columnar data. (Later: external references / files.)"""

    columns: dict[str, list[Any]] = field(default_factory=dict)
    # 2-D matrices for heatmap-style layers, keyed by name
    matrices: dict[str, list[list[float | None]]] = field(default_factory=dict)


@dataclass
class ReferenceSpec(SpecBase):
    """Citation/link metadata for one legend entry, title, etc.

    Backend-dependent: plain text in raster output, a clickable link in
    SVG, and real \\figcite/\\href macros in PGF export (see
    ``mudplot.tex.PREAMBLE``). See ``LayerSpec.references`` for attaching
    a different one to each series of a ``group``-ed layer.
    """

    citation: str | None = None  # BibTeX key, e.g. "fischler_1981"
    href: str | None = None  # URL, e.g. a DOI or arXiv link


@dataclass
class StatSpec(SpecBase):
    """Named estimation settings; numerical work lives in the effect layer."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    estimator: str = "mean"  # mean | median | sum | min | max | count
    errorbar: str | None = "ci"  # sd | se | pi | ci; None disables intervals
    level: float | None = None  # SD/SE multiplier, or PI/CI coverage percent
    n_boot: int = 1000
    seed: int = 0  # explicit local RNG state, never global random state
    weights: str | None = None  # paired mass; finite estimator/inference matrix
    units: str | None = None  # unit column for two-stage hierarchical bootstrap CI
    normalize: str = "count"  # countplot: count | probability | proportion | percent
    # Omit the new default so legacy 0.1 JSON round trips without added fields.
    normalize_scope: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class LineSpec(SpecBase):
    """Explicit predictor coordinates and finite-grid line inference."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    predictor: str = "native"
    resampling: str | None = field(default=None, metadata={"omit_none": True})
    calibration: str | None = field(default=None, metadata={"omit_none": True})
    family: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class CondensedDistanceSpec(SpecBase):
    """Caller-owned dissimilarities in original condensed position order."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    label: str
    values: list[float]


@dataclass
class ClusterCutSpec(SpecBase):
    """Inclusive subtree-maximum height and optional original leaf anchor."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    height: float
    anchor: int | None = field(default=None, metadata={"omit_none": True})


@dataclass
class ClusterTrackLevelSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    key: str
    label: str
    color: str


@dataclass
class ClusterTrackSpec(SpecBase):
    """One ordered categorical track indexed in original matrix positions."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    id: str
    title: str
    values: list[str]
    levels: list[ClusterTrackLevelSpec]
    ratio: float | None = field(default=None, metadata={"omit_none": True})
    legend: bool | None = field(default=None, metadata={"omit_none": True})


@dataclass
class ClusterSpec(SpecBase):
    """Hierarchical matrix clustering; computed orders live only in effects."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    method: str = "average"
    metric: str = "euclidean"
    row_cluster: bool = True
    col_cluster: bool = True
    z_score: str | None = None  # row | col; sample SD
    standard_scale: str | None = None  # row | col; min-max
    optimal_ordering: bool = False
    row_linkage: list[list[float]] | None = None
    col_linkage: list[list[float]] | None = None
    row_colors: list[str] | None = None
    col_colors: list[str] | None = None
    dendrogram_ratio: float = 0.2  # relative to heatmap body
    tree_width: float = 0.8  # points
    tree_color: str = "#475569"
    missing: str | None = field(default=None, metadata={"omit_none": True})
    row_distances: CondensedDistanceSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    col_distances: CondensedDistanceSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    row_cut: ClusterCutSpec | None = field(default=None, metadata={"omit_none": True})
    col_cut: ClusterCutSpec | None = field(default=None, metadata={"omit_none": True})
    row_tracks: list[ClusterTrackSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )
    col_tracks: list[ClusterTrackSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )
    row_dendrogram_ratio: float | None = field(
        default=None, metadata={"omit_none": True}
    )
    col_dendrogram_ratio: float | None = field(
        default=None, metadata={"omit_none": True}
    )
    track_legend_side: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class RegressionBootstrapSpec(SpecBase):
    """Uniform paired physical-case percentile experiment, not weight sampling."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    n_boot: int = 1000
    seed: int = 0


@dataclass
class RegressionPartialSpec(SpecBase):
    """Complete nuisance design and fixed native conditional-curve reference."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    columns: list[str]
    reference: dict[str, float]
    method: str = "joint"


@dataclass
class RegressionSamplingSpec(SpecBase):
    """Explicit disjoint training/query selectors into the original source."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    train: dict[str, Any]
    query: dict[str, Any]


@dataclass
class RegressionTrendSpec(SpecBase):
    """Independently owned continuous-residual trend; full pipeline inference."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    model: str = "lowess"
    degree: int = 1
    frac: float = 2 / 3
    iterations: int = 3
    style: ComponentStyleSpec | None = field(default=None, metadata={"omit_none": True})


@dataclass
class RegressionDiagnosticsSpec(SpecBase):
    """Raw or mathematical binary deviance, conditional on actual observed y."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    kind: str = "raw"
    trend: RegressionTrendSpec | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class RegressionComponentsSpec(SpecBase):
    """Native fit/scatter properties; visibility never changes the experiment."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    fit: ComponentStyleSpec | None = field(default=None, metadata={"omit_none": True})
    scatter: ComponentStyleSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    show_fit: bool = True
    show_scatter: bool = True


@dataclass
class RegressionSpec(SpecBase):
    """Opt-in regression effects; None retains the legacy polynomial renderer."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    model: str = "poly"  # poly | logx | robust | logistic | lowess
    residual: bool = False  # diagnostic mode; raw unless explicitly declared otherwise
    frac: float = 2 / 3  # LOWESS neighbourhood fraction
    iterations: int = 3  # LOWESS robust reweighting iterations
    bootstrap: RegressionBootstrapSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    partial: RegressionPartialSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    sampling: RegressionSamplingSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    diagnostics: RegressionDiagnosticsSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    components: RegressionComponentsSpec | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class ColorbarOptionsSpec(SpecBase):
    """Placement and calibration in the scalar mappable's display units."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    location: str | None = field(default=None, metadata={"omit_none": True})
    ticks: list[float] | None = field(default=None, metadata={"omit_none": True})
    tick_format: str | None = field(default=None, metadata={"omit_none": True})
    fraction: float | None = field(default=None, metadata={"omit_none": True})
    pad: float | None = field(default=None, metadata={"omit_none": True})
    extend: Literal["neither", "min", "max", "both"] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class ScalarDisplaySpec(SpecBase):
    """Render-only scalar calibration shared by the existing native artists."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    cmap: str | None = None
    colors: list[str] | None = field(
        default=None, metadata={"minItems": 2, "maxItems": 64}
    )
    under: str | None = None
    over: str | None = None
    bad: str | None = None
    norm: Literal["linear", "log", "centered", "two_slope", "boundary"] = "linear"
    vmin: float | None = None
    vmax: float | None = None
    center: float | None = None
    boundaries: list[float] | None = field(
        default=None, metadata={"minItems": 2, "maxItems": 65}
    )
    scale_id: str | None = None
    colorbar_options: ColorbarOptionsSpec | None = None


@dataclass
class GridFieldSpec(SpecBase):
    """Explicit native numeric grid, image pixels, or contour controls."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    x: list[float] | None = None
    y: list[float] | None = None
    position: Literal["centers", "edges"] | None = None
    shading: Literal["flat", "nearest"] | None = None
    extent: list[float] | None = None
    origin: Literal["upper", "lower"] | None = None
    pixels: list[list[list[float]]] | None = None
    mask: list[list[bool]] | None = None
    threshold: float | None = None
    corner_mask: bool | None = None
    extend: Literal["neither", "min", "max", "both"] | None = None
    label_levels: list[float] | None = None
    label_format: Literal["g", ".1f", ".2f", ".3f"] | None = None
    label_inline: bool | None = None


@dataclass
class TriangulationSpec(SpecBase):
    """Explicit original-row connectivity and optional scalar/contour controls."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    triangles: list[list[int]]
    mask: list[bool] | None = None
    scalar_role: Literal["vertex", "face"] | None = None
    face_values: list[float] | None = None
    extend: Literal["neither", "min", "max", "both"] | None = None
    label_levels: list[float] | None = None
    label_format: Literal["g", ".1f", ".2f", ".3f"] | None = None
    label_inline: bool | None = None


@dataclass
class SpatialSpec(SpecBase):
    """Explicit Cartesian grid, box delta columns or voxel occupancy."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    x_coords: list[float] | None = None
    y_coords: list[float] | None = None
    z_coords: list[float] | None = None
    dx: str | None = None
    dy: str | None = None
    dz: str | None = None
    occupancy: list[list[list[bool]]] | None = None
    direction: str | None = None
    offset: float | None = None


@dataclass
class Camera3DSpec(SpecBase):
    """Native camera and display box; never supplies physical axis bounds."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    elevation: float | None = None
    azimuth: float | None = None
    roll: float | None = None
    vertical_axis: str | None = None
    projection: str | None = None
    focal_length: float | None = None
    box_aspect: list[float] | None = None
    zoom: float | None = None


@dataclass
class VectorSpec(SpecBase):
    """Finite, family-specific native vector controls."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    mask_column: str | None = None
    mode: Literal["data", "display"] | None = None
    pivot: Literal["tail", "middle", "tip"] | None = None
    scale_units: Literal["xy", "inches", "width", "dots"] | None = None
    width_units: Literal["inches", "width", "dots"] | None = None
    headwidth: float | None = None
    headlength: float | None = None
    headaxislength: float | None = None
    length: float | None = None
    half: float | None = None
    full: float | None = None
    flag: float | None = None
    rounding: bool | None = None
    flip_barb: bool | None = None
    normalize: bool | None = None
    arrow_length_ratio: float | None = None
    x_coords: list[float] | None = None
    y_coords: list[float] | None = None
    u_matrix: str | None = None
    v_matrix: str | None = None
    mask: list[list[bool]] | None = None
    start_points: list[list[float]] | None = None
    density: float | None = None
    minlength: float | None = None
    maxlength: float | None = None
    integration_direction: Literal["both", "forward", "backward"] | None = None
    arrowsize: float | None = None


@dataclass
class HeatmapSpec(SpecBase):
    """Opt-in matrix display controls; None retains legacy imshow defaults."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    norm: str = "linear"  # linear | log | symlog | power | boundary
    vmin: float | None = None
    vmax: float | None = None
    center: float | None = None  # diverging palette only; incompatible with log
    robust: bool = False  # visible-value 2nd/98th percentiles
    annot: bool = False
    fmt: str = "g"  # existing bounded numeric-format whitelist
    mask: list[list[bool]] | None = None
    xlabels: list[str] | None = None
    ylabels: list[str] | None = None
    square: bool = False
    annot_data: list[list[str]] | None = field(
        default=None, metadata={"omit_none": True}
    )
    xrotation: float | None = field(default=None, metadata={"omit_none": True})
    yrotation: float | None = field(default=None, metadata={"omit_none": True})
    linthresh: float | None = field(default=None, metadata={"omit_none": True})
    gamma: float | None = field(default=None, metadata={"omit_none": True})
    boundaries: list[float] | None = field(default=None, metadata={"omit_none": True})
    colorbar_options: ColorbarOptionsSpec | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class BivariateBinsSpec(SpecBase):
    """Unambiguous logical-x/logical-y bin choices; old flat lists stay unchanged."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    x: int | str | list[float | str]
    y: int | str | list[float | str]


@dataclass
class HDRSpec(SpecBase):
    """Full-model HDR with a requested absolute conditional-probability error."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    scope: str = "full"
    tolerance: float = 0.01


@dataclass
class KDESpec(SpecBase):
    """Named weighted univariate kernels/composition; None preserves legacy fit."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    weights: str | None = None  # relative row weights, not replicated samples
    bw_method: str | float = "scott"  # scott | silverman | positive covariance factor
    bw_adjust: float = 1.0
    gridsize: int = 200
    cut: float = 3.0  # support extends this many bandwidths beyond observed extremes
    clip: list[float | str | None] | None = None  # ISO only with a temporal value axis
    common_norm: bool = True  # selected usable mass, including skipped singular hues
    common_grid: bool = False  # shared support from pooled weighted fit
    cumulative: bool = False  # analytic mixture CDF from -infinity, not grid integral
    fill: bool = False
    warn_singular: bool = True  # no invented bandwidth for singleton/constant curves
    kernel: str | None = field(default=None, metadata={"omit_none": True})
    multiple: str | None = field(default=None, metadata={"omit_none": True})
    density_space: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class KDE2DSpec(SpecBase):
    """Named paired density/joint CDF; HDRSpec opts into full-model cell unions."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    weights: str | None = None
    bw_method: str | float = "scott"  # Scott/Silverman coincide in d=2: n_eff**(-1/6)
    bw_adjust: float = 1.0
    gridsize: int = 80  # nodes per logical input axis, not a fitted sample count
    cut: float = 3.0
    clip: list[list[float | str | None]] | None = None  # logical x/y evaluation bounds
    common_norm: bool = True  # all usable selected mass, including singular hues
    common_grid: bool = False  # pooled weighted support, conditional covariance
    levels: list[float] = field(default_factory=lambda: [0.5, 0.8, 0.95])
    fill: bool = False
    warn_singular: bool = True  # no jitter/regularization or fake 2-D density
    kernel: str | None = field(default=None, metadata={"omit_none": True})
    cumulative: bool | None = field(default=None, metadata={"omit_none": True})
    level_kind: str | None = field(default=None, metadata={"omit_none": True})
    fit_scales: list[str] | None = field(default=None, metadata={"omit_none": True})
    density_space: str | None = field(default=None, metadata={"omit_none": True})
    hdr: HDRSpec | None = field(default=None, metadata={"omit_none": True})


@dataclass
class StairsRebinSpec(SpecBase):
    """Explicit target edges and the physical measure of the supplied heights."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    edges: list[float | str] = field(metadata={"minItems": 2, "maxItems": 10001})
    measure: Literal["mass", "density"] = "mass"


@dataclass
class StairsSpec(SpecBase):
    """Opt-in native stairs geometry; None retains the supplied legacy path."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    fill: bool = False
    open: bool = False
    bin_index: str | None = None
    rebin: StairsRebinSpec | None = None


@dataclass
class HistogramSpec(SpecBase):
    """Opt-in shared-bin weighted histogram statistics; None retains legacy hist."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    stat: str = (
        "count"  # count | frequency | probability/proportion | percent | density
    )
    weights: str | None = None
    common_norm: bool = True  # normalized stats: pooled in-bin mass vs per-curve
    cumulative: bool = False  # density integrates mass, not sums density heights
    multiple: str = "layer"  # layer | stack | dodge | fill (post-height shares)
    element: str = "bars"  # bars | step | poly (raw-center segments)
    # Omission preserves filled bars and unfilled step/poly geometry.
    fill: bool | None = field(default=None, metadata={"omit_none": True})


@dataclass
class Histogram2DSpec(SpecBase):
    """Paired weighted bins; optional KDE fits the same pre-tally source cohort."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    stat: str = "count"
    weights: str | None = field(default=None, metadata={"omit_none": True})
    common_norm: bool = True
    kde: KDE2DSpec | None = field(default=None, metadata={"omit_none": True})


@dataclass
class ECDFSpec(SpecBase):
    """Empirical cumulative mass, not a fitted estimator or confidence band."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    stat: str = "proportion"  # proportion | percent | count (sum of weights)
    complementary: bool = False  # strict greater-than mass, not >=
    weights: str | None = None  # finite nonnegative row weights; zeros excluded


@dataclass
class ECDF2DSpec(SpecBase):
    """Closed lower-orthant empirical mass on an explicit finite display frame."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    bounds: list[list[float | str]]
    stat: str = "proportion"
    complementary: bool = False
    weights: str | None = field(default=None, metadata={"omit_none": True})
    query_x: list[float | str] | None = field(
        default=None, metadata={"omit_none": True}
    )
    query_y: list[float | str] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class ComponentStyleSpec(SpecBase):
    """Safe named artist properties, not arbitrary Matplotlib kwargs."""

    _reject_unknown_fields = True
    color: str | None = None  # body base fill or component stroke
    edge_color: str | None = None  # body/marker outline
    face_color: str | None = None  # actual marker fill, including violin inner glyphs
    line_width: float | None = None
    line_style: str | None = None
    marker: str | None = None
    marker_size: float | None = None
    marker_edge_width: float | None = None
    alpha: float | None = None
    hatch: str | None = None  # body only; empty string disables redundant hatch


@dataclass
class SegmentSpec(SpecBase):
    """Equal-length native data coordinates for finite h/v segments."""

    _reject_unknown_fields = True
    at: list[float | str]
    start: list[float | str]
    end: list[float | str]


@dataclass
class ErrorMagnitudesSpec(SpecBase):
    """Two named lower/upper nonnegative duration columns per applicable axis."""

    _reject_unknown_fields = True
    x: list[str] | None = field(default=None, metadata={"omit_none": True})
    y: list[str] | None = field(default=None, metadata={"omit_none": True})


@dataclass
class FillSpec(SpecBase):
    """Native data bands with a strict Boolean mask and optional step topology."""

    _reject_unknown_fields = True
    where: str | None = field(default=None, metadata={"omit_none": True})
    step: Literal["pre", "post", "mid"] | None = field(
        default=None, metadata={"omit_none": True}
    )
    interpolate: bool = False


@dataclass
class SpanSpec(SpecBase):
    """One native value interval; orthogonal edges are closed axes fractions."""

    _reject_unknown_fields = True
    start: float | str
    end: float | str
    fractions: list[float] = field(default_factory=lambda: [0.0, 1.0])


CoordinateFrame = Literal["data", "axes", "figure"]


@dataclass
class PathEffectSpec(SpecBase):
    """Named native stroke or shadow in physical points."""

    _reject_unknown_fields = True
    kind: Literal["stroke", "shadow"]
    color: str | None = field(default=None, metadata={"omit_none": True})
    width: float | None = field(default=None, metadata={"omit_none": True})
    offset: list[float] | None = field(default=None, metadata={"omit_none": True})
    alpha: float | None = field(default=None, metadata={"omit_none": True})


@dataclass
class PatchSpec(SpecBase):
    """Literal Cartesian patch; path commands use native named codes."""

    _reject_unknown_fields = True
    kind: Literal["rectangle", "ellipse", "polygon", "path"]
    vertices: list[list[float | str]]
    codes: list[Literal["MOVETO", "LINETO", "CURVE3", "CURVE4", "CLOSEPOLY"]] | None = (
        field(default=None, metadata={"omit_none": True})
    )
    coordinates: CoordinateFrame = "data"
    fill: bool = True


@dataclass
class LiteralTableSpec(SpecBase):
    """Native text cells with an explicit rectangle in axes fractions."""

    _reject_unknown_fields = True
    cells: list[list[str]]
    bbox: list[float]
    row_labels: list[str] | None = field(default=None, metadata={"omit_none": True})
    column_labels: list[str] | None = field(default=None, metadata={"omit_none": True})
    alignment: Literal["left", "center", "right"] = "center"
    edges: Literal["closed", "open", "horizontal", "vertical"] = "closed"
    font_size: float | None = field(default=None, metadata={"omit_none": True})
    cell_color: str | None = field(default=None, metadata={"omit_none": True})
    header_color: str | None = field(default=None, metadata={"omit_none": True})
    text_color: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class AnnotationSpec(SpecBase):
    """Independent text/arrow target frames; no callback transform."""

    _reject_unknown_fields = True
    at_coordinates: CoordinateFrame = "data"
    to_coordinates: CoordinateFrame | None = field(
        default=None, metadata={"omit_none": True}
    )
    arrow: Literal["none", "line", "open", "filled"] | None = field(
        default=None, metadata={"omit_none": True}
    )
    align: Literal["left", "center", "right"] = "left"
    vertical_align: Literal["baseline", "bottom", "center", "top"] = "baseline"
    font_size: float | None = field(default=None, metadata={"omit_none": True})
    rotation: float = 0.0


@dataclass
class BarGeometrySpec(SpecBase):
    """Supplied bar heights, physical baselines and optional raw-row labels."""

    _reject_unknown_fields = True
    bottom: float | str = 0.0
    align: Literal["center", "edge"] = "center"
    multiple: Literal["dodge", "stack", "layer"] = "dodge"
    styles: list[ComponentStyleSpec | None] | None = field(
        default=None, metadata={"omit_none": True}
    )
    labels: str | None = field(default=None, metadata={"omit_none": True})
    value_format: Literal["g", ".0f", ".1f", ".2f"] | None = field(
        default=None, metadata={"omit_none": True}
    )
    label_padding: float = 3.0


@dataclass
class PieGeometrySpec(SpecBase):
    """Finite native wedge, text and supplied-value annotation controls."""

    _reject_unknown_fields = True
    start_angle: float = 0.0
    counterclock: bool = True
    normalize: bool = True
    radius: float = 1.0
    center: list[float] = field(default_factory=lambda: [0.0, 0.0])
    width: float | None = field(default=None, metadata={"omit_none": True})
    explode: list[float] | None = field(default=None, metadata={"omit_none": True})
    styles: list[ComponentStyleSpec | None] | None = field(
        default=None, metadata={"omit_none": True}
    )
    labels: bool = True
    label_distance: float = 1.1
    rotate_labels: bool = False
    text_color: str | None = field(default=None, metadata={"omit_none": True})
    text_size: float | None = field(default=None, metadata={"omit_none": True})
    value: Literal["raw", "percent"] | None = field(
        default=None, metadata={"omit_none": True}
    )
    value_format: Literal["g", ".0f", ".1f", ".2f"] = ".1f"
    value_distance: float = 0.6
    annotations: list[str | None] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class DistributionComponentsSpec(SpecBase):
    """Named native distribution components; absent fields inherit defaults."""

    _reject_unknown_fields = True
    body: ComponentStyleSpec | None = None
    whisker: ComponentStyleSpec | None = None
    cap: ComponentStyleSpec | None = None
    median: ComponentStyleSpec | None = None
    mean: ComponentStyleSpec | None = None
    flier: ComponentStyleSpec | None = None
    box: ComponentStyleSpec | None = field(default=None, metadata={"omit_none": True})
    quartile: ComponentStyleSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    point: ComponentStyleSpec | None = field(default=None, metadata={"omit_none": True})
    stick: ComponentStyleSpec | None = field(default=None, metadata={"omit_none": True})
    extrema: ComponentStyleSpec | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class BoxSummarySpec(SpecBase):
    """Column references; median uses the box layer's existing value column."""

    _reject_unknown_fields = True
    q1: str
    q3: str
    whislo: str
    whishi: str
    mean: str | None = field(default=None, metadata={"omit_none": True})
    cilo: str | None = field(default=None, metadata={"omit_none": True})
    cihi: str | None = field(default=None, metadata={"omit_none": True})
    fliers: str | None = field(default=None, metadata={"omit_none": True})


@dataclass
class BoxMedianCISpec(SpecBase):
    """Seeded percentile bootstrap of raw sample medians, not observation PI."""

    _reject_unknown_fields = True
    level: float = 95.0
    n_boot: int = 1000
    seed: int = 0


@dataclass
class BoxHueComponentsSpec(SpecBase):
    """An exact raw hue key and fieldwise component overrides."""

    _reject_unknown_fields = True
    level: Any
    components: DistributionComponentsSpec


@dataclass
class BoxSpec(SpecBase):
    """Opt-in box summaries, median inference and bounded native geometry."""

    _reject_unknown_fields = True
    summary: BoxSummarySpec | None = field(default=None, metadata={"omit_none": True})
    median_ci: BoxMedianCISpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    cap_fraction: float | None = field(default=None, metadata={"omit_none": True})
    hue_components: list[BoxHueComponentsSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class ViolinHueComponentsSpec(SpecBase):
    """An exact raw categorical hue and fieldwise native component overrides."""

    _reject_unknown_fields = True
    level: Any
    components: DistributionComponentsSpec


@dataclass
class ViolinSpec(SpecBase):
    """Opt-in paired half-profile lanes and typed per-hue native components."""

    _reject_unknown_fields = True
    split_policy: str | None = field(default=None, metadata={"omit_none": True})
    hue_components: list[ViolinHueComponentsSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class BoxenBandComponentsSpec(SpecBase):
    """Stable central/lower/upper rank, independent of a cell's named depth."""

    _reject_unknown_fields = True
    rank: int
    side: str
    body: ComponentStyleSpec


@dataclass
class BoxenHueComponentsSpec(SpecBase):
    """Exact raw hue; omitted native traits inherit fieldwise."""

    _reject_unknown_fields = True
    level: Any
    components: DistributionComponentsSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    band_components: list[BoxenBandComponentsSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class BoxenSpec(SpecBase):
    """Weighted/rank-resolved letter-value effects, not a confidence model."""

    _reject_unknown_fields = True
    band_components: list[BoxenBandComponentsSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )
    hue_components: list[BoxenHueComponentsSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class SemanticSpec(SpecBase):
    """Independent roles with mark-dependent size effects in physical points."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    scale_id: str | None = None  # named figure scope; None keeps layer-local maps
    hue: str | None = None
    hue_kind: str = "categorical"  # categorical | numeric
    hue_order: list[Any] | None = None
    hue_norm: list[float] | None = None  # mapping bounds, never row selection
    size: str | None = None
    size_kind: str = "numeric"  # categorical | numeric
    size_order: list[Any] | None = None
    size_norm: list[float] | None = None
    # Marker diameter, line stroke or body outline, in physical points.
    sizes: list[float] = field(default_factory=lambda: [3.0, 9.0])
    style: str | None = None  # always categorical; not inferred from hue
    style_order: list[Any] | None = None
    markers: list[str] = field(
        default_factory=lambda: ["o", "s", "D", "^", "v", "P", "X"]
    )
    dashes: list[str] | None = None  # lineplot style dashes; None maps markers only
    legend: bool = True  # observed categorical levels / numeric mapping guides


@dataclass
class StripSpec(SpecBase):
    """Opt-in categorical strips; jitter is a fraction of a reserved hue slot."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    jitter_policy: str = "uniform"  # uniform | none
    seed: int = 0  # local generator, never process-global RNG


@dataclass
class SpectrumSpec(SpecBase):
    """Real uniformly sampled signals; frequencies in Hz, phase in radians."""

    fs: float
    _reject_unknown_fields: typing.ClassVar[bool] = True
    kind: str = "psd"
    nfft: int | None = None
    pad_to: int | None = None
    overlap: int = 0
    window: str = "hann"
    detrend: str = "none"
    sides: str = "onesided"
    scaling: str = "density"
    scale: str = "linear"


@dataclass
class TransformSpec(SpecBase):
    """A named pre-statistic operation on one logical input coordinate."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    role: Literal["x", "y"]
    name: Literal["identity", "log", "standardize"]


@dataclass
class LayerSpec(SpecBase):
    # line | stem | stairs | scatter | bar | errorbar | band | hline | vline
    # | eventplot | broken_barh | annotate | text
    # | hist | box | heatmap | violin | kde | ecdf | rug | regplot | stripplot
    # | stackplot | hist2d | hexbin | quiver | pie | contour | contourf
    # | scatter3d
    # | line3d | surface | wireframe
    type: str = "line"
    x: str = ""  # column name (unused for hline/vline/annotate/text)
    y: str = ""  # column name
    group: str | None = None  # column to split into series (hue)
    semantics: SemanticSpec | None = None  # independent roles; None keeps legacy roles
    label: str | None = None
    # Reference metadata for the legend entry (see mudplot.tex.PREAMBLE).
    # Backend-dependent: plain text in raster output, a clickable link in
    # SVG, and real \figcite/\href macros in PGF export.
    citation: str | None = None  # BibTeX key, e.g. "fischler1981"
    href: str | None = None  # URL, e.g. a DOI or arXiv link
    # Per-group override of the above, keyed by the group value (as a
    # string), e.g. {"RANSAC": ReferenceSpec(citation="fischler_1981")} for
    # a layer with group="method". Only meaningful together with ``group``;
    # a group value missing from this dict gets no reference decoration.
    references: dict[str, ReferenceSpec] | None = None
    color: str | None = None  # explicit hex override
    line_width: float | None = None
    line_style: str | None = None  # "-", "--", ":", "-."
    drawstyle: str = "default"  # default | steps | steps-pre/mid/post (line only)
    marker: str | None = None
    marker_size: float | None = None
    jitter: float | None = None  # stripplot x jitter; None uses 0.15
    alpha: float = 1.0
    # bar geometry / outlines (bar_width is the total span of a category)
    bar_width: float | None = None
    baseline: float | None = None  # raw bar/band bottom, stem/stairs/event offset
    edge_color: str | None = None
    # Raw-data statistical layers; None selects documented type defaults.
    stat: StatSpec | None = None
    sort: bool = True  # lineplot only; otherwise preserve first-observed x order
    error_style: str | None = None  # lineplot: band (default) | bars
    error_alpha: float | None = None  # band opacity; default 0.2 * line alpha
    ecdf: ECDFSpec | None = None  # ecdf only; None selects ECDFSpec defaults
    dodge: float | None = None  # total span for point/distribution hue offsets
    orient: str = "v"  # v | h; two-column builders keep x categorical
    native_scale: bool = False  # numeric category coordinates, distributions/statistics
    stat_scale: str = "data"  # summary/KDE coordinates: data | axis (log10)
    order: list[Any] | None = None  # selected category levels, in display order
    hue_order: list[Any] | None = None  # selected hue levels, in display order
    gap: float | None = None  # fraction of allocated statistical bar span (0..1)
    stack: bool = False  # countplot only; additive counts/proportions
    value_labels: bool = False  # barplot/countplot value labels
    label_format: str = "g"  # a bounded whitelist of numeric format choices
    # error bars: caller-supplied magnitudes OR absolute y interval bounds
    yerr: str | None = None  # column of symmetric y errors (e.g. SD)
    xerr: str | None = None  # column of symmetric x errors (errorbar only)
    y_lower: str | None = None  # absolute lower endpoint, paired with y_upper
    y_upper: str | None = None  # absolute upper endpoint, paired with y_lower
    error_color: str | None = None
    error_line_width: float | None = None
    capsize: float | None = None  # points; zero explicitly removes caps
    capthick: float | None = None  # cap stroke width in points
    # band / fill_between: fills between column ``y`` (upper) and ``y2`` (lower)
    y2: str | None = None
    # reference lines (hline uses ``value`` on y; vline on x)
    value: float | None = None
    # annotate / text
    text: str | None = None
    at: list[float] | None = None  # [x, y] position in data coords
    to: list[float] | None = None  # arrow target for annotate
    # histogram
    bins: (
        int
        | str
        | list[float]
        | list[int]
        | list[str]
        | list[float | str]
        | BivariateBinsSpec
    ) = 20
    density: bool = False
    histogram: HistogramSpec | None = None  # hist only; None preserves legacy effects
    kde: KDESpec | None = None  # kde only; None preserves legacy fit/defaults
    kde2d: KDE2DSpec | None = None  # kde2d only; None uses KDE2DSpec defaults
    # bivariate count plots
    gridsize: int = 30
    mincnt: int | None = None
    # regression: polynomial degree and optional normal-approximation CI (%)
    degree: int = 1
    confidence: float | None = None
    regression: RegressionSpec | None = None  # opt-in models/residuals
    # box/violin: one column keeps x-as-value; optional y enables category/hue.
    # None preserves legacy native defaults (violin medians remain enabled).
    width: float | None = None  # distribution width, event length or band height
    whis: float | list[float] | None = None  # box IQR multiplier or percentiles
    components: DistributionComponentsSpec | None = None
    notch: bool | None = None
    showmeans: bool | None = None
    showfliers: bool | None = None
    showmedians: bool | None = None
    showextrema: bool | None = None
    bw_method: str | float | None = None  # violin: scott/silverman/positive factor
    points: int | None = None  # violin KDE grid, default 100
    # Violin: preserve the old median/width/range behavior unless opted in.
    inner: str | None = "legacy"  # legacy | box | quart | point | stick | None
    split: bool = False  # exactly two selected/reserved hue levels
    density_norm: str = "width"  # width | area | count
    common_norm: bool = False  # shared across hues (otherwise within hue)
    bw_adjust: float | None = None  # positive bandwidth multiplier, default 1
    cut: float | None = None  # support extension in bandwidths, default 0
    clip: list[float | str | None] | None = None  # numeric days or ISO on time axes
    weights: str | None = None  # violin/boxenplot/regplot: relative paired weights
    warn_thresh: float | None = None  # swarm overlap warning fraction, default 0.05
    # Letter-value tail stopping and relative band widths (boxenplot only).
    k_depth: str | int | None = None  # tukey/proportion/trustworthy/full or 1..32
    width_method: str | None = None  # exponential (default) | linear | area
    outlier_prop: float | None = None  # proportion depth only, default 0.007
    trust_alpha: float | None = None  # trustworthy depth only, default 0.05
    # continuous colour mapping (scatter): colour points by column ``c``
    c: str | None = None
    cmap_kind: str = "sequential"  # sequential | diverging
    colorbar: bool = False
    clabel: str | None = None
    # heatmap / contour / contourf / surface / wireframe: references a
    # DataSpec.matrices key
    matrix: str | None = None
    heatmap: HeatmapSpec | None = None  # opt-in; legacy matrix display unchanged
    cluster: ClusterSpec | None = None  # clustermap only; fitted at render time
    # contour / contourf: number of levels, or explicit level values
    levels: int | list[float] | None = None
    # route this layer onto the panel's secondary y-axis
    axis: str = "y"  # "y" | "y2"
    # vector fields
    u: str | None = None
    v: str | None = None
    quiver_scale: float | None = None
    quiver_width: float | None = None
    # 3-D layers (scatter3d / line3d): the z column
    z: str | None = None
    strip: StripSpec | None = field(default=None, metadata={"omit_none": True})
    pack_scope: str | None = field(default=None, metadata={"omit_none": True})
    spectrum: SpectrumSpec | None = field(default=None, metadata={"omit_none": True})
    box: BoxSpec | None = field(default=None, metadata={"omit_none": True})
    violin: ViolinSpec | None = field(default=None, metadata={"omit_none": True})
    boxen: BoxenSpec | None = field(default=None, metadata={"omit_none": True})
    histogram2d: Histogram2DSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    ecdf2d: ECDF2DSpec | None = field(default=None, metadata={"omit_none": True})
    line: LineSpec | None = field(default=None, metadata={"omit_none": True})
    transforms: list[TransformSpec] | None = field(
        default=None, metadata={"omit_none": True, "minItems": 1, "maxItems": 4}
    )
    stairs: StairsSpec | None = field(default=None, metadata={"omit_none": True})
    lane_step: float | None = field(default=None, metadata={"omit_none": True})
    grid: GridFieldSpec | None = field(default=None, metadata={"omit_none": True})
    triangulation: TriangulationSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    vector: VectorSpec | None = field(default=None, metadata={"omit_none": True})
    w: str | None = field(default=None, metadata={"omit_none": True})
    spatial: SpatialSpec | None = field(default=None, metadata={"omit_none": True})
    scalar_display: ScalarDisplaySpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    raw_guide_id: str | None = field(default=None, metadata={"omit_none": True})
    native_style: ComponentStyleSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    segments: SegmentSpec | None = field(default=None, metadata={"omit_none": True})
    error_magnitudes: ErrorMagnitudesSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    fill: FillSpec | None = field(default=None, metadata={"omit_none": True})
    span: SpanSpec | None = field(default=None, metadata={"omit_none": True})
    bar_geometry: BarGeometrySpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    pie_geometry: PieGeometrySpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    patch: PatchSpec | None = field(default=None, metadata={"omit_none": True})
    table: LiteralTableSpec | None = field(default=None, metadata={"omit_none": True})
    annotation: AnnotationSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    path_effects: list[PathEffectSpec] | None = field(
        default=None, metadata={"omit_none": True, "minItems": 1, "maxItems": 2}
    )


@dataclass
class TemporalSpec(SpecBase):
    """Explicit input clock; plot/statistical coordinates are UTC days since 1970."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    timezone: str | None = None  # aware inputs only unless a fixed zone is declared
    unit: str | None = None  # numeric input: s | ms | us | ns | day
    origin: str | None = None  # required ISO origin for numeric input


@dataclass
class ScaleOptionsSpec(SpecBase):
    """Finite native parameters; the scale family remains AxisSpec.scale."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    base: float | None = None
    subs: list[float] | None = None
    linthresh: float | None = None
    linscale: float | None = None
    linear_width: float | None = None


@dataclass
class LocatorSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    kind: str = "auto"
    values: list[float] | None = None
    step: float | None = None
    offset: float | None = None
    nbins: int | None = None
    integer: bool | None = None
    prune: str | None = None
    count: int | None = None
    subdivisions: int | None = None
    subs: list[float] | None = None
    unit: str | None = None
    interval: int | None = None
    weekday: int | None = None


@dataclass
class FormatterSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    kind: str = "auto"
    labels: list[str] | None = None
    scientific: bool | None = None
    use_offset: bool | None = None
    powerlimits: list[int] | None = None
    mathtext: bool | None = None
    notation: str | None = None
    precision: int | None = None
    prefix: str | None = None
    suffix: str | None = None
    xmax: float | None = None
    decimals: int | None = None
    unit: str | None = None
    separator: str | None = None
    style: str | None = None
    label_only_base: bool | None = None
    half: str | None = None
    use_overline: bool | None = None
    pattern: str | None = None


@dataclass
class TickSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    locator: LocatorSpec | None = None
    formatter: FormatterSpec | None = None
    rotation: float | None = None


@dataclass
class AxisTransformSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    kind: str
    factor: float | None = None
    offset: float | None = None
    source_unit: str | None = None
    target_unit: str | None = None
    reverse: bool = False


@dataclass
class SecondaryAxisSpec(SpecBase):
    """Derived top/right axis, distinct from independent PanelSpec.y2."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    transform: AxisTransformSpec
    label: str | None = None
    major_ticks: TickSpec | None = None
    minor_ticks: TickSpec | None = None


@dataclass
class AxisSpec(SpecBase):
    label: str = ""
    scale: str = "linear"  # linear | log
    limits: list[float] | None = None  # [min, max]
    share_id: str | None = None  # named primary Cartesian sharing group
    temporal: TemporalSpec | None = field(default=None, metadata={"omit_none": True})
    scale_options: ScaleOptionsSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    major_ticks: TickSpec | None = field(default=None, metadata={"omit_none": True})
    minor_ticks: TickSpec | None = field(default=None, metadata={"omit_none": True})


@dataclass
class LegendSpec(SpecBase):
    # Explicit [x, y] figure-fraction override (0..1), e.g. from dragging the
    # legend in the interactive editor. None -> use ``location`` as usual.
    bbox_to_anchor: list[float] | None = None
    show: bool = True
    title: str | None = None
    location: str = "best"
    frame: bool = False
    ncols: int | None = field(default=None, metadata={"omit_none": True})
    handler: Literal["line-pair", "scatter-pair"] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class SharedGuideSpec(SpecBase):
    """One figure-owned guide for all persisted members of a named scale."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    scale_id: str
    location: str = "outside right"
    title: str | None = None
    frame: bool = False
    bbox_to_anchor: list[float] | None = None
    ncols: int | None = field(default=None, metadata={"omit_none": True})
    handler: Literal["line-pair", "scatter-pair"] | None = field(
        default=None, metadata={"omit_none": True}
    )
    kind: Literal["raw", "scalar"] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class GridCellSpec(SpecBase):
    """Zero-based cell/span in a named layout grid."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    grid: str
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1


@dataclass
class InsetSpec(SpecBase):
    """A real child panel in parent-axes [left, bottom, width, height] fractions."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    parent: str
    bounds: list[float]


@dataclass
class PanelPlacementSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    cell: GridCellSpec | None = field(default=None, metadata={"omit_none": True})
    inset: InsetSpec | None = field(default=None, metadata={"omit_none": True})


@dataclass
class LayoutGridSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    grid_id: str
    rows: int
    cols: int
    cell: GridCellSpec | None = field(default=None, metadata={"omit_none": True})
    width_ratios: list[float] | None = field(default=None, metadata={"omit_none": True})
    height_ratios: list[float] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class PanelLayoutSpec(SpecBase):
    _reject_unknown_fields: typing.ClassVar[bool] = True
    grids: list[LayoutGridSpec]


@dataclass
class PanelSpec(SpecBase):
    layers: list[LayerSpec] = field(default_factory=list)
    x: AxisSpec = field(default_factory=AxisSpec)
    y: AxisSpec = field(default_factory=AxisSpec)
    y2: AxisSpec | None = None  # secondary y-axis; None -> not created
    z: AxisSpec | None = None  # 3-D z-axis config; only used if projection="3d"
    projection: str = "2d"  # "2d" | "polar" | "3d"
    title: str = ""
    # Explicit [x, y] axes-fraction override for the title (e.g. from
    # dragging it in the interactive editor). None -> matplotlib's default
    # (centred above the axes).
    title_position: list[float] | None = None
    # Reference metadata for the panel title (same backend rules as
    # LayerSpec.citation/href).
    title_citation: str | None = None
    title_href: str | None = None
    label: str | None = None  # explicit panel tag, e.g. "a"; None -> auto
    legend: LegendSpec = field(default_factory=LegendSpec)
    filters: dict[str, Any] = field(default_factory=dict)  # exact row/col selections
    dropna: list[str] = field(default_factory=list)  # shared complete-case view
    secondary_x: SecondaryAxisSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    secondary_y: SecondaryAxisSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    panel_id: str | None = field(default=None, metadata={"omit_none": True})
    placement: PanelPlacementSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    camera3d: Camera3DSpec | None = field(default=None, metadata={"omit_none": True})
    grid_cohort: Literal[True] | None = field(
        default=None, metadata={"omit_none": True}
    )


@dataclass
class FacetTemplateSpec(SpecBase):
    """Frozen cell recipe for explicit whole-template transactions, not rendering."""

    template: PanelSpec
    selectors: list[dict[str, Any]]
    _reject_unknown_fields: typing.ClassVar[bool] = True
    row: str | None = None
    col: str | None = None
    row_order: list[Any] = field(default_factory=list)
    col_order: list[Any] = field(default_factory=list)
    col_wrap: int | None = None


@dataclass
class FigureSpec(SpecBase):
    version: str = SPEC_VERSION
    size: list[float] = field(default_factory=lambda: [3.5, 2.625])  # inches
    dpi: int = 300
    theme: ThemeSpec = field(default_factory=ThemeSpec)
    data: DataSpec = field(default_factory=DataSpec)
    suptitle: str = ""
    auto_label_panels: bool = False  # tag multi-panel figures a), b), c)...
    width_ratios: list[float] | None = None
    height_ratios: list[float] | None = None
    panels: list[PanelSpec] = field(default_factory=lambda: [PanelSpec()])
    layout: list[int] | None = None  # [rows, cols]; None -> 1 x n_panels
    share_x: str = "none"  # "none" | "all" | "row" | "col"
    share_y: str = "none"  # "none" | "all" | "row" | "col"
    journal: str | None = None  # nature | ieee | None
    # WYSIWYG layout for a citation is only exact for compact/numeric styles
    # (e.g. "[12]"): matplotlib lays out the figure *before* the document's
    # own bibliography resolves \figcite{key}, so it has no way to know the
    # real rendered width of e.g. an author-year citation ("(Fischler and
    # Bolles, 1981)") ahead of time. Set this to a representative example of
    # your citation style (e.g. "(Fischler and Bolles, 1981)") to make PGF
    # export measure legend/title layout against *that* width instead of the
    # compact default -- purely a measurement aid, never emitted to output.
    reference_measure_text: str | None = None
    facet_template: FacetTemplateSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    panel_layout: PanelLayoutSpec | None = field(
        default=None, metadata={"omit_none": True}
    )
    shared_guides: list[SharedGuideSpec] | None = field(
        default=None, metadata={"omit_none": True}
    )

    @classmethod
    def from_dict(cls, data: dict) -> FigureSpec:
        """Like ``SpecBase.from_dict``, but upgrades an older on-disk
        ``version`` first (see ``migrate_spec_dict``). This is the one
        entry point (``.mplot.json`` load, ``Plot.from_json``, the
        dashboard editor's "open a spec" action) that ever sees a spec's
        raw ``version`` field, since nested sub-specs don't carry one.
        """
        return typing.cast("FigureSpec", super().from_dict(migrate_spec_dict(data)))
