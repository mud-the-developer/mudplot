"""Pure reducer: ``reduce(state, action) -> new_state``.

No side effects, no input mutation. A deep copy of the incoming spec is taken
and the (isolated) copy is updated, so callers can rely on the original state
being untouched — the essential property of a pure reducer.
"""

from __future__ import annotations

import copy
from dataclasses import fields as dc_fields
from dataclasses import replace

from . import actions as A
from .spec import AxisSpec, FigureSpec, PanelSpec
from .theme import JOURNAL_SIZES, theme_preset

__all__ = ["reduce", "reduce_all"]

# SetEncoding may only touch these ThemeSpec fields (not font/axes/grid/
# ticks/palette/name, which each already have a dedicated action).
_ENCODING_FIELDS = {"redundant_encoding", "markers", "line_styles", "hatches"}


def _ensure_panel(spec: FigureSpec, index: int) -> None:
    if type(index) is not int or index < 0:
        raise ValueError("panel index must be a non-negative integer")
    while len(spec.panels) <= index:
        spec.panels.append(PanelSpec())


def _safe_replace(obj, params: dict, action_name: str):
    """``dataclasses.replace`` with a friendly error on unknown field names.

    Without this, an agent (or typo) passing e.g. ``{"colour": "..."}`` to
    ``.font(colour=...)`` would get a raw, unhelpfully-worded ``TypeError``
    deep inside ``dataclasses.replace`` instead of a clear, actionable
    message naming the valid fields.
    """
    valid = {f.name for f in dc_fields(obj)}
    unknown = set(params) - valid
    if unknown:
        raise ValueError(
            f"{action_name}: unknown field(s) {sorted(unknown)}; "
            f"valid fields: {sorted(valid)}"
        )
    return replace(obj, **params)


def reduce(state: FigureSpec, action: A.Action) -> FigureSpec:
    """Return a new FigureSpec resulting from applying ``action`` to ``state``."""
    s = copy.deepcopy(state)
    action = copy.deepcopy(action)

    match action:
        case A.SetSize(width=w, height=h):
            s.size = [w, h]
        case A.SetDpi(dpi=d):
            s.dpi = d
        case A.SetData(columns=cols):
            # Update columns in place rather than replacing ``s.data``
            # wholesale, so any matrices registered via SetMatrix (e.g.
            # before a later data refresh) aren't silently discarded.
            s.data.columns = {str(k): list(v) for k, v in cols.items()}
        case A.SetTheme(name=name):
            s.theme = theme_preset(name)
        case A.SetJournal(name=name):
            s.journal = name
            # A journal preset also implies its conventional figure size
            # (rcParams alone can't do this: render() always passes an
            # explicit figsize= that would otherwise shadow it silently).
            if name is not None and name in JOURNAL_SIZES:
                s.size = list(JOURNAL_SIZES[name])
        case A.SetPalette(kind=kind, params=params):
            new = _safe_replace(s.theme.palette, dict(params.items()), "SetPalette")
            if kind is not None:
                new = replace(new, kind=kind)
            s.theme.palette = new
        case A.SetFont(params=params):
            s.theme.font = _safe_replace(s.theme.font, params, "SetFont")
        case A.SetAxesStyle(params=params):
            s.theme.axes = _safe_replace(s.theme.axes, params, "SetAxesStyle")
        case A.SetGridStyle(params=params):
            s.theme.grid = _safe_replace(s.theme.grid, params, "SetGridStyle")
        case A.SetTicksStyle(params=params):
            s.theme.ticks = _safe_replace(s.theme.ticks, params, "SetTicksStyle")
        case A.SetEncoding(params=params):
            unknown = set(params) - _ENCODING_FIELDS
            if unknown:
                raise ValueError(
                    f"SetEncoding: unknown field(s) {sorted(unknown)}; valid "
                    f"fields: {sorted(_ENCODING_FIELDS)}"
                )
            s.theme = replace(s.theme, **params)
        case A.SetShare(x=shx, y=shy):
            if shx is not None:
                s.share_x = shx
            if shy is not None:
                s.share_y = shy
        case A.AddPanel():
            s.panels.append(PanelSpec())
        case A.SetLayout(rows=r, cols=c, width_ratios=wr, height_ratios=hr):
            if any(type(v) is not int or v <= 0 for v in (r, c)):
                raise ValueError("layout rows and cols must be positive integers")
            s.layout = [r, c]
            s.width_ratios = list(wr) if wr else None
            s.height_ratios = list(hr) if hr else None
            while len(s.panels) < r * c:
                s.panels.append(PanelSpec())
        case A.AddLayer(layer=layer, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].layers.append(copy.deepcopy(layer))
        case A.RemoveLayer(layer_index=li, panel=pi):
            _ensure_panel(s, pi)
            n_layers = len(s.panels[pi].layers)
            if not (0 <= li < n_layers):
                raise ValueError(
                    f"RemoveLayer: layer_index {li} out of range for panel "
                    f"{pi} ({n_layers} layer(s))"
                )
            del s.panels[pi].layers[li]
        case A.SetAxisLabel(axis=axis, text=text, panel=pi):
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).label = text
        case A.SetTitle(text=text, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].title = text
        case A.SetScale(axis=axis, scale=scale, panel=pi):
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).scale = scale
        case A.SetLimits(axis=axis, lo=lo, hi=hi, panel=pi):
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).limits = [lo, hi]
        case A.SetLegend(show=show, title=title, location=loc, frame=fr, panel=pi):
            _ensure_panel(s, pi)
            leg = s.panels[pi].legend
            leg.show, leg.title, leg.location, leg.frame = show, title, loc, fr
        case A.SetSuptitle(text=text):
            s.suptitle = text
        case A.SetPanelLabel(label=label, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].label = label
        case A.SetAutoLabel(enabled=enabled):
            s.auto_label_panels = enabled
        case A.SetSecondaryAxis(label=label, scale=scale, limits=limits, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].y2 = AxisSpec(label=label, scale=scale, limits=limits)
        case A.SetProjection(projection=proj, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].projection = proj
        case A.SetZAxis(label=label, scale=scale, limits=limits, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].z = AxisSpec(label=label, scale=scale, limits=limits)
        case A.SetColorbar(layer_index=li, show=show, label=label, panel=pi):
            _ensure_panel(s, pi)
            n_layers = len(s.panels[pi].layers)
            if not (0 <= li < n_layers):
                raise ValueError(
                    f"SetColorbar: layer_index {li} out of range for panel "
                    f"{pi} ({n_layers} layer(s))"
                )
            layer = s.panels[pi].layers[li]
            layer.colorbar = show
            if label is not None:
                layer.clabel = label
        case A.SetMatrix(name=name, values=values):
            s.data.matrices[name] = [list(row) for row in values]
        case _:
            raise TypeError(f"unknown action: {action!r}")

    return s


def reduce_all(state: FigureSpec, actions) -> FigureSpec:
    """Fold a sequence of actions over the state."""
    for action in actions:
        state = reduce(state, action)
    return state
