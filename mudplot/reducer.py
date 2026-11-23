"""Pure reducer: ``reduce(state, action) -> new_state``.

No side effects, no input mutation. A deep copy of the incoming spec is taken
and the (isolated) copy is updated, so callers can rely on the original state
being untouched — the essential property of a pure reducer.
"""

from __future__ import annotations

import copy
from dataclasses import fields as dc_fields
from dataclasses import replace
from typing import Literal, cast

from . import actions as A
from .spec import (
    MAX_FIGURE_LAYERS,
    MAX_FIGURE_PANELS,
    AxisSpec,
    FigureSpec,
    LayerSpec,
    PanelSpec,
)
from .theme import JOURNAL_SIZES, theme_preset

__all__ = ["reduce", "reduce_all"]

# SetEncoding may only touch these ThemeSpec fields (not font/axes/grid/
# ticks/palette/name, which each already have a dedicated action).
_ENCODING_FIELDS = {"redundant_encoding", "markers", "line_styles", "hatches"}


def _ensure_panel(spec: FigureSpec, index: int) -> None:
    if type(index) is not int or index < 0:
        raise ValueError("panel index must be a non-negative integer")
    if index >= MAX_FIGURE_PANELS:
        raise ValueError(f"figure supports at most {MAX_FIGURE_PANELS} panels")
    if spec.panel_layout is not None and index >= len(spec.panels):
        raise ValueError(
            "explicit layout expansion requires SetPanelLayout/SetMosaic or AddInset"
        )
    if index >= len(spec.panels):
        spec.facet_template = None
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
    return replace(obj, **copy.deepcopy(params))


def admit_transform_action(action):
    """Check the finite declaration before a typed action is defensively copied."""
    match action:
        case A.AddLayer(layer=layer) | A.ReplaceLayer(layer=layer):
            layers = (layer,)
        case A.SetFacetTemplate(template=template) if isinstance(template, PanelSpec):
            layers = template.layers
        case _:
            return
    from ._transforms import option_issues

    for layer in layers:
        if isinstance(layer, LayerSpec) and layer.transforms is not None:
            problems = option_issues(layer)
            if problems:
                raise ValueError("; ".join(problems))


def _edit_twin_peers(spec, panel, axis, *fields):
    """Keep one named native value link when existing axis controls are used."""
    if axis not in ("y", "y2") or spec.panels[panel].grid_cohort is not True:
        return
    from ._layout import twin_value_groups

    for members in twin_value_groups(spec):
        if (panel, axis) not in members:
            continue
        source = getattr(spec.panels[panel], axis)
        for peer, name in members:
            if (peer, name) != (panel, axis):
                target = getattr(spec.panels[peer], name)
                for field in fields:
                    setattr(target, field, copy.deepcopy(getattr(source, field)))
        return


def reduce(state: FigureSpec, action: A.Action) -> FigureSpec:
    """Apply ``action`` without mutating inputs.

    The mutable dataclass graph is defensively copied, so work scales with the
    full spec, including inline data; this is not a persistent/zero-copy model.
    """
    # ponytail: full-spec copying keeps aliasing rules simple; move to
    # structural sharing only if profiles show large inline specs dominate.
    admit_transform_action(action)
    s = copy.deepcopy(state)
    from . import _layout

    structural = True
    match action:
        case A.SetPanelLayout(layout=layout, placements=places, panel_ids=ids):
            _layout.replace_layout(s, layout, places, ids)
        case A.SetMosaic(rows=rows, width_ratios=wr, height_ratios=hr):
            _layout.mosaic(s, rows, wr, hr)
        case A.NestLayout():
            _layout.nest(
                s, **{f.name: getattr(action, f.name) for f in dc_fields(action)}
            )
        case A.SetPanelPlacement(panel_id=name, placement=place):
            _layout.explicit(s)
            _layout.find_panel(s, name).placement = copy.deepcopy(place)
        case A.AddInset(parent=parent, bounds=bounds, panel_id=name):
            _layout.add_inset(s, parent, bounds, name)
        case A.RenamePanel(panel_id=name, new_id=replacement):
            _layout.panel_ids(s)
            _layout.rename(s, name, replacement)
        case A.ReorderPanels(panel_ids=names):
            _layout.reorder(s, names)
        case A.RemovePanel(panel_id=name):
            if s.facet_template is not None:
                from ._facet import _selector_signature

                removed = _layout.find_panel(s, name)
                signature = _selector_signature(removed.filters)
                if any(
                    signature == _selector_signature(selector)
                    for selector in s.facet_template.selectors
                ):
                    # Removing a live cell leaves materialized saved views,
                    # not an incomplete future whole-template transaction.
                    s.facet_template = None
            _layout.remove(s, name)
        case _:
            structural = False
    if structural:
        from .validate import assert_valid

        assert_valid(s)
        return s

    match action:
        case A.SetSize(width=w, height=h):
            s.size = [w, h]
        case A.SetDpi(dpi=d):
            s.dpi = d
        case A.SetSharedGuides(guides=guides):
            s.shared_guides = copy.deepcopy(guides)
        case A.SetData(columns=cols):
            # Update columns in place rather than replacing ``s.data``
            # wholesale, so any matrices registered via SetMatrix (e.g.
            # before a later data refresh) aren't silently discarded.
            s.data.columns = {str(k): copy.deepcopy(list(v)) for k, v in cols.items()}
        case A.SetTheme(name=name):
            s.theme = theme_preset(name)
        case A.SetContext(name=name):
            from .theme import CONTEXT_SCALES

            if name is not None and name not in CONTEXT_SCALES:
                raise ValueError("context must be paper, notebook, talk or poster")
            s.theme.context = cast(
                "Literal['paper', 'notebook', 'talk', 'poster'] | None", name
            )
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
            s.theme = replace(s.theme, **copy.deepcopy(params))
        case A.SetShare(x=shx, y=shy):
            if shx is not None:
                s.share_x = shx
            if shy is not None:
                s.share_y = shy
        case A.AddPanel():
            _ensure_panel(s, len(s.panels))
        case A.SetLayout(rows=r, cols=c, width_ratios=wr, height_ratios=hr):
            if any(type(v) is not int or v <= 0 for v in (r, c)):
                raise ValueError("layout rows and cols must be positive integers")
            _layout.clear_geometry(s)
            same_live_grid = s.facet_template is not None and s.layout == [r, c]
            if not same_live_grid:
                s.facet_template = None
                _ensure_panel(s, r * c - 1)
            s.layout = [r, c]
            if wr is not None or not same_live_grid:
                s.width_ratios = list(wr) if wr else None
            if hr is not None or not same_live_grid:
                s.height_ratios = list(hr) if hr else None
        case A.SetLiveFacets():
            from ._facet import materialize_live_facets

            _layout.clear_geometry(s)

            materialize_live_facets(
                s,
                **{
                    field.name: getattr(action, field.name)
                    for field in dc_fields(action)
                },
            )
        case A.SetFacetTemplate(template=template, reset_orders=reset):
            from ._facet import replace_facet_template

            replace_facet_template(s, template, reset_orders=reset)
        case A.SetFacets():
            from ._facet import materialize_facets

            _layout.clear_geometry(s)

            s.facet_template = None
            materialize_facets(
                s,
                **{
                    field.name: getattr(action, field.name)
                    for field in dc_fields(action)
                },
            )
        case A.SetJointGrid():
            from ._joint import materialize_joint

            _layout.clear_geometry(s)

            s.facet_template = None
            materialize_joint(
                s,
                **{
                    field.name: getattr(action, field.name)
                    for field in dc_fields(action)
                },
            )
        case A.SetPairGrid():
            from ._pair import materialize_pair

            _layout.clear_geometry(s)

            s.facet_template = None
            materialize_pair(
                s,
                **{
                    field.name: getattr(action, field.name)
                    for field in dc_fields(action)
                },
            )
        case A.SetAxisShare(axis=axis, share_id=name, panel=pi):
            if axis not in ("x", "y"):
                raise ValueError("named axis sharing requires x or y")
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).share_id = name
        case A.AddLayer(layer=layer, panel=pi):
            _ensure_panel(s, pi)
            if sum(len(panel.layers) for panel in s.panels) >= MAX_FIGURE_LAYERS:
                raise ValueError(f"figure supports at most {MAX_FIGURE_LAYERS} layers")
            s.panels[pi].layers.append(copy.deepcopy(layer))
        case A.ReplaceLayer(layer_index=li, layer=layer, panel=pi):
            if type(pi) is not int or not (0 <= pi < len(s.panels)):
                raise ValueError(
                    "ReplaceLayer: panel must name an existing integer index"
                )
            if type(li) is not int or not (0 <= li < len(s.panels[pi].layers)):
                raise ValueError(
                    "ReplaceLayer: layer_index must name an existing integer index"
                )
            if not isinstance(layer, LayerSpec):
                raise ValueError("ReplaceLayer: layer must be a typed LayerSpec")
            s.panels[pi].layers[li] = copy.deepcopy(layer)
        case A.RemoveLayer(layer_index=li, panel=pi):
            _ensure_panel(s, pi)
            n_layers = len(s.panels[pi].layers)
            if type(li) is not int or not (0 <= li < n_layers):
                raise ValueError(
                    f"RemoveLayer: layer_index {li} out of range for panel "
                    f"{pi} ({n_layers} layer(s))"
                )
            del s.panels[pi].layers[li]
        case A.SetAxisLabel(axis=axis, text=text, panel=pi):
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).label = text
        case A.SetTitle(text=text, panel=pi, citation=cite, href=href):
            _ensure_panel(s, pi)
            s.panels[pi].title = text
            s.panels[pi].title_citation = cite
            s.panels[pi].title_href = href
        case A.SetTitlePosition(position=pos, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].title_position = list(pos) if pos is not None else None
        case A.SetTemporalAxis(axis=axis, temporal=temporal, panel=pi):
            _ensure_panel(s, pi)
            if axis not in ("x", "y", "y2"):
                raise ValueError("SetTemporalAxis requires x, y or y2")
            target = getattr(s.panels[pi], axis)
            if target is None:
                raise ValueError("SetTemporalAxis requires an enabled axis")
            target.temporal = copy.deepcopy(temporal)
        case A.SetScale(axis=axis, scale=scale, panel=pi):
            _ensure_panel(s, pi)
            getattr(s.panels[pi], axis).scale = scale
            from ._axis_options import axis_issues, configured

            target = getattr(s.panels[pi], axis)
            if configured(target):
                problems = axis_issues(target)
                if problems:
                    raise ValueError("; ".join(problems))
            _edit_twin_peers(s, pi, axis, "scale")
        case A.SetAxisScale(axis=axis, scale=scale, options=options, panel=pi):
            from ._axis_options import axis_issues

            _ensure_panel(s, pi)
            target = (
                getattr(s.panels[pi], axis, None) if axis in ("x", "y", "y2") else None
            )
            if target is None:
                raise ValueError("SetAxisScale requires an enabled x/y/y2 axis")
            target.scale = scale
            target.scale_options = copy.deepcopy(options)
            problems = axis_issues(target)
            if problems:
                raise ValueError("; ".join(problems))
            _edit_twin_peers(s, pi, axis, "scale", "scale_options")
        case A.SetAxisTicks(axis=axis, which=which, ticks=ticks, panel=pi):
            from ._axis_options import axis_issues

            _ensure_panel(s, pi)
            target = (
                getattr(s.panels[pi], axis, None) if axis in ("x", "y", "y2") else None
            )
            if target is None or which not in ("major", "minor"):
                raise ValueError("SetAxisTicks requires enabled x/y/y2 and major/minor")
            setattr(target, which + "_ticks", copy.deepcopy(ticks))
            problems = axis_issues(target)
            if problems:
                raise ValueError("; ".join(problems))
        case A.SetDerivedAxis(axis=axis, secondary=secondary, panel=pi):
            from ._axis_options import secondary_issues

            _ensure_panel(s, pi)
            if axis not in ("x", "y"):
                raise ValueError("SetDerivedAxis requires primary x or y")
            if axis == "y" and secondary is not None and s.panels[pi].y2 is not None:
                raise ValueError("derived secondary_y conflicts with independent y2")
            problems = secondary_issues(secondary, getattr(s.panels[pi], axis))
            if problems:
                raise ValueError("; ".join(problems))
            setattr(s.panels[pi], "secondary_" + axis, copy.deepcopy(secondary))
        case A.SetLimits(axis=axis, lo=lo, hi=hi, panel=pi):
            _ensure_panel(s, pi)
            if lo is None and hi is None:
                limits = None
            elif lo is None or hi is None:
                raise ValueError("SetLimits requires both lo and hi, or neither")
            else:
                limits = [lo, hi]
            getattr(s.panels[pi], axis).limits = limits
            _edit_twin_peers(s, pi, axis, "limits")
        case A.SetLegend(
            show=show,
            title=title,
            location=loc,
            frame=fr,
            panel=pi,
            bbox_to_anchor=bta,
            ncols=ncols,
            handler=handler,
        ):
            _ensure_panel(s, pi)
            leg = s.panels[pi].legend
            leg.show, leg.title, leg.location, leg.frame = show, title, loc, fr
            leg.bbox_to_anchor = list(bta) if bta is not None else None
            if handler not in (None, "line-pair", "scatter-pair"):
                raise ValueError(
                    "legend handler must be line-pair, scatter-pair or null"
                )
            leg.ncols = ncols
            leg.handler = cast("Literal['line-pair', 'scatter-pair'] | None", handler)
        case A.SetSuptitle(text=text):
            s.suptitle = text
        case A.SetReferenceMeasureText(text=text):
            s.reference_measure_text = text
        case A.SetPanelLabel(label=label, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].label = label
        case A.SetAutoLabel(enabled=enabled):
            s.auto_label_panels = enabled
        case A.SetSecondaryAxis(label=label, scale=scale, limits=limits, panel=pi):
            _ensure_panel(s, pi)
            target = s.panels[pi].y2
            if target is not None and target.share_id is not None:
                if (
                    label is None
                    or scale not in ("linear", target.scale)
                    or (limits is not None and list(limits) != target.limits)
                ):
                    raise ValueError(
                        "edit linked y2 values with SetLimits or SetAxisScale"
                    )
                target.label = label
            else:
                s.panels[pi].y2 = (
                    None
                    if label is None
                    else AxisSpec(
                        label=label,
                        scale=scale,
                        limits=list(limits) if limits is not None else None,
                    )
                )
        case A.SetProjection(projection=proj, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].projection = proj
            if proj != "3d":
                s.panels[pi].z = None
                s.panels[pi].camera3d = None
        case A.SetZAxis(label=label, scale=scale, limits=limits, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].z = AxisSpec(
                label=label,
                scale=scale,
                limits=list(limits) if limits is not None else None,
            )
        case A.SetCamera3D(camera=camera, panel=pi):
            _ensure_panel(s, pi)
            s.panels[pi].camera3d = copy.deepcopy(camera)
        case A.SetColorbar(layer_index=li, show=show, label=label, panel=pi):
            _ensure_panel(s, pi)
            n_layers = len(s.panels[pi].layers)
            if type(li) is not int or not (0 <= li < n_layers):
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
        case A.SetLayerAt(layer_index=li, at=at, panel=pi):
            _ensure_panel(s, pi)
            n_layers = len(s.panels[pi].layers)
            if type(li) is not int or not (0 <= li < n_layers):
                raise ValueError(
                    f"SetLayerAt: layer_index {li} out of range for panel "
                    f"{pi} ({n_layers} layer(s))"
                )
            layer = s.panels[pi].layers[li]
            if layer.type not in ("text", "annotate"):
                raise ValueError(
                    f"SetLayerAt: layer {li} is a {layer.type!r} layer; "
                    "only 'text'/'annotate' layers have a repositionable 'at'"
                )
            layer.at = list(at)
        case _:
            raise TypeError(f"unknown action: {action!r}")

    from ._line import line_option_issues
    from ._regression import (
        configured_regression,
        option_issues,
        weighted_option_issues,
    )

    for panel in s.panels:
        for layer in panel.layers:
            if layer.line is not None:
                problems = line_option_issues(layer)
                if problems:
                    raise ValueError("; ".join(problems))
            if configured_regression(layer):
                if layer.type != "regplot":
                    raise ValueError("regression declarations require regplot")
                problems = option_issues(
                    layer.regression, layer.degree, layer.confidence
                )
                problems.extend(
                    weighted_option_issues(
                        layer.regression, layer.confidence, layer.weights
                    )
                )
                if problems:
                    raise ValueError("; ".join(problems))
    if s.shared_guides is not None:
        from ._shared_guides import shared_guide_issues

        problems = shared_guide_issues(s)
        if problems:
            raise ValueError("; ".join(problems))
    from ._native_geometry import extended_geometry

    if any(
        panel.grid_cohort is True
        or any(
            layer.native_style is not None
            or layer.path_effects is not None
            or extended_geometry(layer)
            for layer in panel.layers
        )
        for panel in s.panels
    ):
        from .validate import assert_valid

        assert_valid(s)
    return s


def reduce_all(state: FigureSpec, actions) -> FigureSpec:
    """Fold a sequence of actions over the state."""
    for action in actions:
        state = reduce(state, action)
    return state
