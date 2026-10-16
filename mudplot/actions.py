"""Actions: pure data describing an intended change to a FigureSpec.

Actions carry no behaviour. They are consumed by ``mudplot.reducer.reduce``
which returns a new state. The same actions can be produced by the Python
fluent API today and by a Rust/htmx editor later.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import cast

from .spec import KDESpec, LayerSpec, SpecBase, _from_dict

__all__ = [
    "ACTION_REGISTRY",
    "Action",
    "AddLayer",
    "AddPanel",
    "RemoveLayer",
    "SetAutoLabel",
    "SetAxesStyle",
    "SetAxisLabel",
    "SetAxisShare",
    "SetColorbar",
    "SetData",
    "SetDpi",
    "SetEncoding",
    "SetFacets",
    "SetFont",
    "SetGridStyle",
    "SetJointGrid",
    "SetJournal",
    "SetLayerAt",
    "SetLayout",
    "SetLegend",
    "SetLimits",
    "SetMatrix",
    "SetPairGrid",
    "SetPalette",
    "SetPanelLabel",
    "SetProjection",
    "SetReferenceMeasureText",
    "SetScale",
    "SetSecondaryAxis",
    "SetShare",
    "SetSize",
    "SetSuptitle",
    "SetTheme",
    "SetTicksStyle",
    "SetTitle",
    "SetTitlePosition",
    "SetZAxis",
    "action_from_dict",
    "action_to_dict",
]


# -- figure-level ----------------------------------------------------------
@dataclass(frozen=True)
class SetSize:
    width: float
    height: float


@dataclass(frozen=True)
class SetDpi:
    dpi: int


@dataclass(frozen=True)
class SetData:
    columns: dict


@dataclass(frozen=True)
class SetTheme:
    name: str


@dataclass(frozen=True)
class SetJournal:
    name: str | None


@dataclass(frozen=True)
class SetPalette:
    kind: str | None = None
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SetFont:
    params: dict = field(default_factory=dict)  # e.g. {"size": 8, "family": "serif"}


@dataclass(frozen=True)
class SetAxesStyle:
    params: dict = field(default_factory=dict)  # e.g. {"spine_offset": 6}


@dataclass(frozen=True)
class SetGridStyle:
    params: dict = field(default_factory=dict)  # e.g. {"show": True}


@dataclass(frozen=True)
class SetTicksStyle:
    params: dict = field(default_factory=dict)  # e.g. {"direction": "in"}


@dataclass(frozen=True)
class SetEncoding:
    # redundant marker/line-style cycling in addition to colour
    params: dict = field(default_factory=dict)  # e.g. {"redundant_encoding": True}


@dataclass(frozen=True)
class SetShare:
    x: str | None = None  # "none" | "all" | "row" | "col"
    y: str | None = None


@dataclass(frozen=True)
class SetSecondaryAxis:
    label: str | None = ""
    scale: str = "linear"
    limits: list[float] | None = None
    panel: int = 0


@dataclass(frozen=True)
class SetProjection:
    projection: str  # "2d" | "polar" | "3d"
    panel: int = 0


@dataclass(frozen=True)
class SetZAxis:
    label: str = ""
    scale: str = "linear"
    limits: list[float] | None = None
    panel: int = 0


@dataclass(frozen=True)
class SetColorbar:
    layer_index: int
    show: bool = True
    label: str | None = None
    panel: int = 0


@dataclass(frozen=True)
class SetMatrix:
    name: str
    values: list  # list of rows (list[list[float]])


@dataclass(frozen=True)
class AddPanel:
    pass


@dataclass(frozen=True)
class SetLayout:
    rows: int
    cols: int
    width_ratios: list[float] | None = None
    height_ratios: list[float] | None = None


@dataclass(frozen=True)
class SetFacets:
    row: str | None = None
    col: str | None = None
    row_order: list[str | bool | int | float] | None = None
    col_order: list[str | bool | int | float] | None = None
    col_wrap: int | None = None
    share_x: str = "all"
    share_y: str = "all"


@dataclass(frozen=True)
class SetJointGrid:
    bins: int = 20
    ratio: float = 3.0
    marginal_stat: str = "density"
    marginal_kind: str = "hist"
    kde: KDESpec | None = None


@dataclass(frozen=True)
class SetPairGrid:
    columns: list[str]
    group: str | None = None
    hue_order: list[str | bool | int | float] | None = None
    bins: int = 20
    diag_stat: str = "density"
    diag_kind: str = "hist"
    kde: KDESpec | None = None


@dataclass(frozen=True)
class SetAxisShare:
    axis: str
    share_id: str | None
    panel: int = 0


# -- panel-level -----------------------------------------------------------
@dataclass(frozen=True)
class AddLayer:
    layer: LayerSpec
    panel: int = 0


@dataclass(frozen=True)
class RemoveLayer:
    layer_index: int
    panel: int = 0


@dataclass(frozen=True)
class SetAxisLabel:
    axis: str  # "x" | "y"
    text: str
    panel: int = 0


@dataclass(frozen=True)
class SetTitle:
    text: str
    panel: int = 0
    # Optional reference metadata for the title (BibTeX key / URL); see
    # LayerSpec.citation for how each output format renders it.
    citation: str | None = None
    href: str | None = None


@dataclass(frozen=True)
class SetTitlePosition:
    # Explicit [x, y] axes-fraction override; None restores the default
    # (centred above the axes).
    position: list[float] | None
    panel: int = 0


@dataclass(frozen=True)
class SetLayerAt:
    """Reposition a ``text``/``annotate`` layer's anchor point (data coords).

    Used by the interactive editor's draggable annotation handles; equally
    usable by an agent that wants to nudge a callout without rebuilding the
    whole layer.
    """

    layer_index: int
    at: list[float]
    panel: int = 0


@dataclass(frozen=True)
class SetScale:
    axis: str  # "x" | "y"
    scale: str  # "linear" | "log"
    panel: int = 0


@dataclass(frozen=True)
class SetLimits:
    axis: str  # "x" | "y"
    lo: float | None  # None/None restores automatic limits
    hi: float | None
    panel: int = 0


@dataclass(frozen=True)
class SetLegend:
    show: bool = True
    title: str | None = None
    location: str = "best"
    frame: bool = False
    panel: int = 0
    # Explicit [x, y] figure-fraction override (0..1); None leaves
    # ``location`` in charge (or clears a previous override, if it was set).
    bbox_to_anchor: list[float] | None = None


@dataclass(frozen=True)
class SetSuptitle:
    text: str


@dataclass(frozen=True)
class SetReferenceMeasureText:
    # See FigureSpec.reference_measure_text -- None restores the compact
    # default measurement.
    text: str | None


@dataclass(frozen=True)
class SetPanelLabel:
    label: str | None
    panel: int = 0


@dataclass(frozen=True)
class SetAutoLabel:
    enabled: bool = True


Action = (
    SetPairGrid
    | SetAxisShare
    | SetJointGrid
    | SetFacets
    | SetLayout
    | SetSize
    | SetDpi
    | SetData
    | SetTheme
    | SetJournal
    | SetPalette
    | SetFont
    | AddPanel
    | AddLayer
    | RemoveLayer
    | SetAxisLabel
    | SetTitle
    | SetScale
    | SetLimits
    | SetLegend
    | SetReferenceMeasureText
    | SetSuptitle
    | SetPanelLabel
    | SetAutoLabel
    | SetAxesStyle
    | SetGridStyle
    | SetTicksStyle
    | SetEncoding
    | SetShare
    | SetSecondaryAxis
    | SetProjection
    | SetZAxis
    | SetColorbar
    | SetMatrix
    | SetTitlePosition
    | SetLayerAt
)

# --------------------------------------------------------------------------
# JSON <-> action (agent-facing): actions are addressed by their class name
# --------------------------------------------------------------------------
_ACTION_CLASSES = (
    SetSize,
    SetDpi,
    SetData,
    SetTheme,
    SetJournal,
    SetPalette,
    SetFont,
    AddPanel,
    SetLayout,
    SetFacets,
    SetJointGrid,
    SetPairGrid,
    SetAxisShare,
    AddLayer,
    RemoveLayer,
    SetAxisLabel,
    SetTitle,
    SetScale,
    SetLimits,
    SetLegend,
    SetReferenceMeasureText,
    SetSuptitle,
    SetPanelLabel,
    SetAutoLabel,
    SetAxesStyle,
    SetGridStyle,
    SetTicksStyle,
    SetEncoding,
    SetShare,
    SetSecondaryAxis,
    SetProjection,
    SetZAxis,
    SetColorbar,
    SetMatrix,
    SetTitlePosition,
    SetLayerAt,
)
ACTION_REGISTRY: dict[str, type] = {cls.__name__: cls for cls in _ACTION_CLASSES}


def action_to_dict(action) -> dict:
    """Serialise an action to a JSON-ready dict tagged with ``type``."""
    out: dict = {"type": type(action).__name__}
    for f in fields(action):
        val = getattr(action, f.name)
        if isinstance(val, SpecBase):
            val = val.to_dict()
        out[f.name] = val
    return out


def action_from_dict(data: dict) -> Action:
    """Build an action from a ``{"type": ..., ...}`` dict (agent-facing)."""
    if not isinstance(data, dict):
        raise TypeError("action must be a JSON object")
    if not all(isinstance(key, str) for key in data):
        raise TypeError("action object keys must be strings")
    d = dict(data)
    name = d.pop("type", None)
    if not isinstance(name, str):
        raise TypeError("action type must be a string")
    cls = ACTION_REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"unknown action type {name!r}; valid: {sorted(ACTION_REGISTRY)}"
        )
    valid = {f.name for f in fields(cls)}
    unknown = set(d) - valid
    if unknown:
        raise ValueError(
            f"unknown field(s) {sorted(unknown)} for action {name!r}; "
            f"valid fields: {sorted(valid)}"
        )
    return cast(Action, _from_dict(cls, d))
