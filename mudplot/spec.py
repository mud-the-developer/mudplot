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
from typing import Any, Union, get_args, get_origin

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
    def from_dict(cls, data: dict):
        return _from_dict(cls, data)


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _to_dict(getattr(obj, f.name)) for f in fields(obj)}
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
        if getattr(cls, "_reject_unknown_fields", False):
            unknown = set(data) - {f.name for f in fields(cls)}
            if unknown:
                raise ValueError(f"unknown {cls.__name__} field(s): {sorted(unknown)}")
        hints = typing.get_type_hints(cls)
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            kwargs[f.name] = _from_dict(hints[f.name], data[f.name])
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


# --------------------------------------------------------------------------
# Data, layers, axes, panels
# --------------------------------------------------------------------------
@dataclass
class DataSpec(SpecBase):
    """Inline columnar data. (Later: external references / files.)"""

    columns: dict[str, list[Any]] = field(default_factory=dict)
    # 2-D matrices for heatmap-style layers, keyed by name
    matrices: dict[str, list[list[float]]] = field(default_factory=dict)


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
    weights: str | None = None  # nonnegative weights; mean and bootstrap CI only
    units: str | None = None  # unit column for two-stage hierarchical bootstrap CI
    normalize: str = "count"  # countplot: count | probability | proportion | percent


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


@dataclass
class RegressionSpec(SpecBase):
    """Opt-in regression effects; None retains the legacy polynomial renderer."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    model: str = "poly"  # poly | logx | robust | logistic | lowess
    residual: bool = False  # observed y minus fitted response, not deviance residuals
    frac: float = 2 / 3  # LOWESS neighbourhood fraction
    iterations: int = 3  # LOWESS robust reweighting iterations


@dataclass
class HeatmapSpec(SpecBase):
    """Opt-in matrix display controls; None retains legacy imshow defaults."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    norm: str = "linear"  # linear | log
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


@dataclass
class KDESpec(SpecBase):
    """Opt-in weighted univariate Gaussian KDE; None keeps the legacy effect."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    weights: str | None = None  # relative row weights, not replicated samples
    bw_method: str | float = "scott"  # scott | silverman | positive covariance factor
    bw_adjust: float = 1.0
    gridsize: int = 200
    cut: float = 3.0  # support extends this many bandwidths beyond observed extremes
    clip: list[float | None] | None = None  # bounds evaluation, never drops fit rows
    common_norm: bool = True  # selected usable mass, including skipped singular hues
    common_grid: bool = False  # shared support from pooled weighted fit
    cumulative: bool = False  # analytic mixture CDF from -infinity, not grid integral
    fill: bool = False
    warn_singular: bool = True  # no invented bandwidth for singleton/constant curves


@dataclass
class KDE2DSpec(SpecBase):
    """Weighted Gaussian contours; levels enclose conditional finite-grid mass."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    weights: str | None = None
    bw_method: str | float = "scott"  # Scott/Silverman coincide in d=2: n_eff**(-1/6)
    bw_adjust: float = 1.0
    gridsize: int = 80  # nodes per raw-coordinate axis
    cut: float = 3.0
    clip: list[list[float | None]] | None = None  # [[xlo,xhi],[ylo,yhi]] eval only
    common_norm: bool = True  # all usable selected mass, including singular hues
    common_grid: bool = False  # pooled weighted support, conditional covariance
    levels: list[float] = field(default_factory=lambda: [0.5, 0.8, 0.95])
    fill: bool = False
    warn_singular: bool = True  # no jitter/regularization or fake 2-D density


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
    multiple: str = "layer"  # layer | stack | dodge; heights keep original bin units
    element: str = "bars"  # bars | step; unfilled steps support layer/stack only


@dataclass
class ECDFSpec(SpecBase):
    """Empirical cumulative mass, not a fitted estimator or confidence band."""

    _reject_unknown_fields: typing.ClassVar[bool] = True
    stat: str = "proportion"  # proportion | percent | count (sum of weights)
    complementary: bool = False  # strict greater-than mass, not >=
    weights: str | None = None  # finite nonnegative row weights; zeros excluded


@dataclass
class ComponentStyleSpec(SpecBase):
    """Safe named artist properties, not arbitrary Matplotlib kwargs."""

    _reject_unknown_fields = True
    color: str | None = None  # body base fill or component stroke
    edge_color: str | None = None  # body/marker outline
    face_color: str | None = None  # marker fill (mean/flier only)
    line_width: float | None = None
    line_style: str | None = None
    marker: str | None = None
    marker_size: float | None = None
    marker_edge_width: float | None = None
    alpha: float | None = None
    hatch: str | None = None  # body only; empty string disables redundant hatch


@dataclass
class DistributionComponentsSpec(SpecBase):
    """Independent box/boxen component styles; absent fields inherit defaults."""

    _reject_unknown_fields = True
    body: ComponentStyleSpec | None = None
    whisker: ComponentStyleSpec | None = None
    cap: ComponentStyleSpec | None = None
    median: ComponentStyleSpec | None = None
    mean: ComponentStyleSpec | None = None
    flier: ComponentStyleSpec | None = None


@dataclass
class SemanticSpec(SpecBase):
    """Independent roles: scatter diameters or lineplot stroke widths in points."""

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
    sizes: list[float] = field(default_factory=lambda: [3.0, 9.0])  # diameters, pt
    style: str | None = None  # always categorical; not inferred from hue
    style_order: list[Any] | None = None
    markers: list[str] = field(
        default_factory=lambda: ["o", "s", "D", "^", "v", "P", "X"]
    )
    dashes: list[str] | None = None  # lineplot style dashes; None maps markers only
    legend: bool = True  # observed categorical levels / numeric mapping guides


@dataclass
class LayerSpec(SpecBase):
    # line | scatter | bar | errorbar | band | hline | vline | annotate | text
    # | hist | box | heatmap | violin | kde | ecdf | rug | regplot | stripplot
    # | stackplot | hist2d | hexbin | quiver | pie | contour | contourf
    # | scatter3d
    # | line3d | surface | wireframe
    type: str = "line"
    x: str = ""  # column name (unused for hline/vline/annotate/text)
    y: str = ""  # column name
    group: str | None = None  # column to split into series (hue)
    semantics: SemanticSpec | None = None  # scatter only; None keeps legacy roles
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
    baseline: float | None = None  # nonstack statistical bars: raw baseline (default 0)
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
    bins: int | list[float] = 20
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
    width: float | None = None
    whis: float | list[float] | None = None  # box IQR multiplier or percentiles
    components: DistributionComponentsSpec | None = None  # box/boxen only
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
    clip: list[float | None] | None = None  # KDE support bounds, raw value units
    weights: str | None = None  # violin only; relative paired row weights
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


@dataclass
class AxisSpec(SpecBase):
    label: str = ""
    scale: str = "linear"  # linear | log
    limits: list[float] | None = None  # [min, max]
    share_id: str | None = None  # named primary Cartesian sharing group


@dataclass
class LegendSpec(SpecBase):
    # Explicit [x, y] figure-fraction override (0..1), e.g. from dragging the
    # legend in the interactive editor. None -> use ``location`` as usual.
    bbox_to_anchor: list[float] | None = None
    show: bool = True
    title: str | None = None
    location: str = "best"
    frame: bool = False


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

    @classmethod
    def from_dict(cls, data: dict) -> FigureSpec:
        """Like ``SpecBase.from_dict``, but upgrades an older on-disk
        ``version`` first (see ``migrate_spec_dict``). This is the one
        entry point (``.mplot.json`` load, ``Plot.from_json``, the
        dashboard editor's "open a spec" action) that ever sees a spec's
        raw ``version`` field, since nested sub-specs don't carry one.
        """
        return typing.cast("FigureSpec", super().from_dict(migrate_spec_dict(data)))
