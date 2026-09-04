"""Declarative, serialisable plot specification.

``FigureSpec`` is the single source of truth for a figure. It contains only
plain data (numbers, strings, lists, nested dataclasses) so it can round-trip
through JSON/TOML and later be edited by a Rust (serde) frontend that shares
the same schema.

Nothing here touches matplotlib; rendering lives in ``mudplot.render``.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Union, get_args, get_origin

_UNION_ORIGINS = (Union, types.UnionType)

SPEC_VERSION = "0.1"


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


def _strip_optional(tp):
    """Union[X, None] -> X (leave other unions as-is)."""
    if get_origin(tp) in _UNION_ORIGINS:
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def _from_dict(cls, data: Any):
    if data is None:
        return None
    if is_dataclass(cls):
        hints = typing.get_type_hints(cls)
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            kwargs[f.name] = _from_dict(_strip_optional(hints[f.name]), data[f.name])
        return cls(**kwargs)
    origin = get_origin(cls)
    if origin in (list, tuple):
        (item_t,) = get_args(cls) or (Any,)
        seq = [_from_dict(item_t, v) for v in data]
        return tuple(seq) if origin is tuple else seq
    if origin is dict:
        return dict(data)
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
    # colour, so series stay distinguishable in greyscale print or for CVD
    # viewers even if two colours end up close together.
    redundant_encoding: bool = True
    markers: list[str] = field(
        default_factory=lambda: ["o", "s", "^", "D", "v", "P", "X", "*"]
    )
    line_styles: list[str] = field(default_factory=lambda: ["-", "--", "-.", ":"])


# --------------------------------------------------------------------------
# Data, layers, axes, panels
# --------------------------------------------------------------------------
@dataclass
class DataSpec(SpecBase):
    """Inline columnar data. (Later: external references / files.)"""

    columns: dict[str, list[float]] = field(default_factory=dict)
    # 2-D matrices for heatmap-style layers, keyed by name
    matrices: dict[str, list[list[float]]] = field(default_factory=dict)


@dataclass
class LayerSpec(SpecBase):
    # line | scatter | bar | errorbar | band | hline | vline | annotate | text
    type: str = "line"
    x: str = ""  # column name (unused for hline/vline/annotate/text)
    y: str = ""  # column name
    group: str | None = None  # column to split into series (hue)
    label: str | None = None
    color: str | None = None  # explicit hex override
    line_width: float | None = None
    line_style: str | None = None  # "-", "--", ":", "-."
    marker: str | None = None
    marker_size: float | None = None
    alpha: float = 1.0
    # error bars
    yerr: str | None = None  # column of symmetric y errors
    xerr: str | None = None  # column of symmetric x errors
    capsize: float | None = None
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
    # boxplot: ``x`` is the value column; ``group`` splits into boxes
    # continuous colour mapping (scatter): colour points by column ``c``
    c: str | None = None
    cmap_kind: str = "sequential"  # sequential | diverging
    colorbar: bool = False
    clabel: str | None = None
    # heatmap: references a DataSpec.matrices key
    matrix: str | None = None
    # route this layer onto the panel's secondary y-axis
    axis: str = "y"  # "y" | "y2"


@dataclass
class AxisSpec(SpecBase):
    label: str = ""
    scale: str = "linear"  # linear | log
    limits: list[float] | None = None  # [min, max]


@dataclass
class LegendSpec(SpecBase):
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
    title: str = ""
    label: str | None = None  # explicit panel tag, e.g. "a"; None -> auto
    legend: LegendSpec = field(default_factory=LegendSpec)


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
