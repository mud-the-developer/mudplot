"""Named figure-guide ownership; source membership never depends on artists."""

from __future__ import annotations

from ._density import DENSITY_TYPES, FIELD_TYPES, kde_config
from ._ecdf import finite_number
from ._semantics import _scale_signature, category_key, option_issues, valid_scale_id
from .spec import FacetTemplateSpec, PanelSpec, SemanticSpec, SharedGuideSpec

LOCATIONS = frozenset({"outside right", "outside top", "outside bottom"})


def requested_scope_ids(spec):
    """Requests select named scopes; they never duplicate scope membership."""
    if not isinstance(spec.shared_guides, list):
        return frozenset()
    return frozenset(
        request.scale_id
        for request in spec.shared_guides
        if isinstance(request, SharedGuideSpec)
        and valid_scale_id(request.scale_id)
        and request.kind is None
    )


RAW_GUIDE_TYPES = frozenset({"line", "scatter", "bar"})


def layer_scope(layer, kind):
    if kind == "raw":
        return layer.raw_guide_id
    if kind == "scalar":
        return getattr(layer.scalar_display, "scale_id", None)
    return getattr(layer.semantics, "scale_id", None)


def raw_guide_issues(layer):
    if layer.raw_guide_id is None:
        return []
    if (
        not valid_scale_id(layer.raw_guide_id)
        or layer.type not in RAW_GUIDE_TYPES
        or layer.semantics is not None
        or not layer.group
        or layer.c is not None
        or (
            layer.type == "line"
            and (
                layer.line is not None
                or layer.order is not None
                or layer.orient != "v"
                or layer.transforms is not None
            )
        )
    ):
        return ["raw_guide_id requires an eligible raw grouped line, scatter or bar"]
    return []


def scope_members(spec, scale_id, kind=None):
    """All persisted actual/template members, including reserved empty views."""
    for panel in spec.panels:
        for layer in panel.layers:
            if layer_scope(layer, kind) == scale_id:
                yield layer
    if isinstance(spec.facet_template, FacetTemplateSpec) and isinstance(
        spec.facet_template.template, PanelSpec
    ):
        for layer in spec.facet_template.template.layers:
            if layer_scope(layer, kind) == scale_id:
                yield layer


def shared_guide_issues(spec):
    requests = spec.shared_guides
    if requests is None:
        return []
    if not isinstance(requests, list):
        return ["shared_guides requires a list or None"]
    issues, seen = [], set()
    for index, request in enumerate(requests):
        where = f"shared_guides[{index}]"
        if not isinstance(request, SharedGuideSpec):
            issues.append(f"{where}: requires a strict SharedGuideSpec")
            continue
        if not valid_scale_id(request.scale_id):
            issues.append(f"{where}: scale_id must be a nonblank <=64-character name")
            continue
        if request.scale_id in seen:
            issues.append(
                f"{where}: duplicate named scale request {request.scale_id!r}"
            )
        seen.add(request.scale_id)
        if not isinstance(request.location, str) or request.location not in LOCATIONS:
            issues.append(f"{where}: location must be outside right/top/bottom")
        if request.title is not None and not isinstance(request.title, str):
            issues.append(f"{where}: title must be a string or None")
        if type(request.frame) is not bool:
            issues.append(f"{where}: frame must be boolean")
        from ._legend_style import legend_style_issues

        issues.extend(f"{where}: {issue}" for issue in legend_style_issues(request))
        anchor = request.bbox_to_anchor
        if anchor is not None and (
            not isinstance(anchor, (list, tuple))
            or len(anchor) != 2
            or not all(finite_number(value) for value in anchor)
        ):
            issues.append(
                f"{where}: bbox_to_anchor requires two finite figure fractions"
            )
        kind = request.kind
        if kind not in (None, "raw", "scalar"):
            issues.append(f"{where}: unsupported named guide kind")
            continue
        members = list(scope_members(spec, request.scale_id, kind))
        if not members:
            issues.append(f"{where}: no persisted owner for scale {request.scale_id!r}")
            continue
        if kind == "raw":
            try:
                signatures = {
                    (
                        layer.group,
                        tuple(category_key(v) for v in (layer.hue_order or ())),
                    )
                    for layer in members
                }
            except (TypeError, ValueError):
                signatures = set()
            if len(signatures) != 1 or any(
                raw_guide_issues(layer) for layer in members
            ):
                issues.append(f"{where}: raw group membership and order must agree")
            continue
        if kind == "scalar":
            from ._scalar_display import _key

            intentions = [layer for layer in members if layer.colorbar]
            labels = {
                (
                    layer.clabel or layer.c or "",
                    repr(getattr(layer.scalar_display, "colorbar_options", None)),
                )
                for layer in intentions
            }
            try:
                agree = len({_key(layer.scalar_display) for layer in members}) == 1
            except (TypeError, ValueError, AttributeError):
                agree = False
            if not agree or len(labels) > 1:
                issues.append(
                    f"{where}: scalar calibration and requested shared bar must agree"
                )
            continue
        signature, labels = None, set()
        for layer in members:
            config = layer.semantics
            problems = option_issues(config)
            if problems or not isinstance(config, SemanticSpec):
                issues.extend(f"{where}: {problem}" for problem in problems)
                continue
            settings = config.to_dict()
            if config.hue is not None and config.hue_kind == "numeric":
                settings["cmap_kind"] = layer.cmap_kind
            settings.pop("legend")
            settings.pop("scale_id")
            current = _scale_signature(settings)
            if signature is None:
                signature = current
            elif current != signature:
                issues.append(f"{where}: persisted scope mappings disagree")
            if (
                layer.colorbar
                and layer.type not in FIELD_TYPES
                and layer.type != "regplot"
            ):
                labels.add(layer.clabel if layer.clabel is not None else config.hue)
        if len(labels) > 1:
            issues.append(f"{where}: requested shared colourbar labels disagree")
    return issues


_FAMILY_NAMES = {
    "line": "supplied line",
    "lineplot": "estimated line",
    "ecdf": "ECDF",
    "scatter": "scatter",
    "stripplot": "strip",
    "swarmplot": "swarm",
    "pointplot": "estimated point",
    "barplot": "estimated bar",
    "hist": "histogram",
    "countplot": "weighted count",
    "box": "box",
    "violin": "violin",
    "boxenplot": "boxen",
    "rug": "rug",
    "kde": "KDE",
    "kde2d": "joint KDE",
    "hist2d": "bivariate histogram",
    "ecdf2d": "joint empirical CDF",
}


def _effect_kind(layer):
    if layer.type in FIELD_TYPES:
        return "field"
    if layer.type == "kde" and kde_config(layer).fill:
        return "body"
    if layer.type in {"scatter", "stripplot", "swarmplot", "pointplot", "regplot"}:
        return "point"
    if layer.type in {"barplot", "countplot", "box", "violin", "boxenplot"}:
        return "body"
    if layer.type == "hist" and layer.histogram is not None:
        config = layer.histogram
        filled = config.element == "bars" if config.fill is None else config.fill
        if filled:
            return "body"
    return layer.type if layer.type in {"rug", "stem", "eventplot"} else "line"


def _style_key(value):
    """Native trait identity, never display-label deduplication."""
    if isinstance(value, dict):
        return tuple((key, _style_key(item)) for key, item in sorted(value.items()))
    if isinstance(value, (tuple, list)):
        return tuple(_style_key(item) for item in value)
    if hasattr(value, "tolist"):
        return _style_key(value.tolist())
    return value


def native_guide_key(handle, layer, role, value):
    """One actual-trait identity for panel and figure ownership, never labels."""
    from matplotlib.lines import Line2D

    if isinstance(handle, Line2D):
        traits = {
            "color": handle.get_color(),
            "width": handle.get_linewidth(),
            "dash": handle.get_linestyle(),
            "marker": handle.get_marker(),
            "diameter": handle.get_markersize(),
            "face": handle.get_markerfacecolor(),
            "edge": handle.get_markeredgecolor(),
            "edgewidth": handle.get_markeredgewidth(),
            "alpha": handle.get_alpha(),
        }
    else:
        traits = {
            key: getattr(handle, key)
            for key in (
                "box_body",
                "box_lines",
                "flier_marker",
                "body_style",
                "median_style",
                "flier_style",
                "inner_marker",
            )
            if hasattr(handle, key)
        }
        if not traits:
            traits = {
                "face": handle.get_facecolor(),
                "edge": handle.get_edgecolor(),
                "width": handle.get_linewidth(),
                "dash": handle.get_linestyle(),
                "alpha": handle.get_alpha(),
                "hatch": handle.get_hatch(),
            }
    return (
        role,
        category_key(value),
        _effect_kind(layer),
        type(handle).__name__,
        _style_key(traits),
    )


def tag_entry(ax, handle, layer, role, value, *, context=None):
    """Use the same native context key; scale_id remains the sole membership."""
    primary = getattr(ax, "_mudplot_semantic_guide_axis", ax)
    collector = getattr(primary, "_mudplot_shared_guide_collector", None)
    if layer.semantics is None:
        return
    request = (
        None if collector is None else collector.requests.get(layer.semantics.scale_id)
    )
    if request is None or request.kind is not None:
        scale_id = layer.semantics.scale_id
        if (
            layer.type in DENSITY_TYPES | {"stem", "eventplot", "regplot"}
            and scale_id is not None
        ):
            traits = native_guide_key(handle, layer, role, value)
            if layer.type == "regplot":
                assert context is not None
                key = (scale_id, context["family"], traits)
            else:
                key = (scale_id, traits)
            shown = getattr(primary, "_mudplot_native_role_guides", set())
            if key in shown:
                handle.remove()
                getattr(ax, "_mudplot_legend_handlers", {}).pop(handle, None)
            else:
                shown.add(key)
                primary._mudplot_native_role_guides = shown
        return
    assert collector is not None
    collector.add(ax, handle, layer, role, value, context)


class SharedGuideCollector:
    """One render-local native ownership pass; no serialized/shadow membership."""

    def __init__(self, spec, domains):
        self.spec = spec
        self.requests = {
            request.scale_id: request for request in (spec.shared_guides or [])
        }
        self.domains = domains
        self.entries = {name: {} for name in self.requests}
        self.families = {name: {} for name in self.requests}
        self.handlers = {}
        self.scalar_artists = {}
        self.axes = []
        self.legend_intent, self.colourbar_intent, self.colourbar_labels = {}, {}, {}
        self.cmap_kinds = {}
        for name in self.requests:
            if self.requests[name].kind is not None:
                continue
            members = [
                layer
                for panel in spec.panels
                for layer in panel.layers
                if isinstance(layer.semantics, SemanticSpec)
                and layer.semantics.scale_id == name
            ]
            self.legend_intent[name] = any(layer.semantics.legend for layer in members)
            regression_members = domains.get(name, {}).get("regression_members", ())
            bar_owners = [
                layer
                for layer in members
                if layer.colorbar
                and layer.type not in FIELD_TYPES
                and (layer.type != "regplot" or id(layer) in regression_members)
            ]
            self.colourbar_intent[name] = bool(bar_owners)
            self.cmap_kinds[name] = next((layer.cmap_kind for layer in members), None)
            self.colourbar_labels[name] = next(
                (
                    layer.clabel if layer.clabel is not None else layer.semantics.hue
                    for layer in bar_owners
                ),
                None,
            )

    def attach(self, ax):
        ax._mudplot_shared_guide_collector = self
        self.axes.append(ax)

    def add_scalar(self, ax, layer, artist):
        name = layer_scope(layer, "scalar")
        request = self.requests.get(name)
        if request is None or request.kind != "scalar":
            return False
        if artist.get_array() is not None and len(artist.get_array()):
            self.scalar_artists.setdefault(name, (ax, layer, artist))
        return True

    def add_raw(self, ax, layer, value, handle):
        name = layer.raw_guide_id
        request = self.requests.get(name)
        if request is None or request.kind != "raw" or handle is None:
            return
        key = category_key(value)
        self.entries[name].setdefault(key, handle)
        handle._mudplot_shared_raw_handle = True
        self.handlers.update(getattr(ax, "_mudplot_legend_handlers", {}))

    def _restore_context(self, handle, layer, role, kind, context):
        from matplotlib.colors import to_rgba
        from matplotlib.lines import Line2D

        if not isinstance(handle, Line2D) or context is None:
            return
        if isinstance(context, Line2D):
            context = {
                "color": context.get_color(),
                "diameter": context.get_markersize(),
                "marker": context.get_marker(),
                "edgecolor": context.get_markeredgecolor(),
                "edgewidth": context.get_markeredgewidth(),
                "edge_fixed": layer.edge_color is not None,
                "width": context.get_linewidth(),
                "dash": context.get_linestyle(),
                "alpha": context.get_alpha(),
            }
        if not isinstance(context, dict) or "color" not in context:
            return
        if role != "hue":
            color = to_rgba(context["color"])
            handle.set_color(color)
            handle.set_markerfacecolor(color)
        if role != "hue" or context.get("edge_fixed", False):
            handle.set_markeredgecolor(
                to_rgba(context.get("edgecolor", context["color"]))
            )
        else:
            handle.set_markeredgecolor(to_rgba(handle.get_markerfacecolor()))
        if "edgewidth" in context:
            handle.set_markeredgewidth(context["edgewidth"])
        if (role != "size" or kind != "point") and "diameter" in context:
            handle.set_markersize(context["diameter"])
        if (role != "size" or kind == "point") and "width" in context:
            handle.set_linewidth(context["width"])
        if role != "style" and "marker" in context:
            handle.set_marker(context["marker"])
        owns_dash = (
            layer.semantics.dashes is not None
            or layer.type
            in {
                "pointplot",
                "barplot",
                "rug",
                "eventplot",
            }
            | DENSITY_TYPES
        )
        if (role != "style" or not owns_dash) and "dash" in context:
            handle.set_linestyle(context["dash"])
        if "alpha" in context:
            handle.set_alpha(context["alpha"])
        if handle.get_linewidth() == 0:
            handle.set_linestyle("None")

    def add(self, ax, handle, layer, role, value, context):
        name = layer.semantics.scale_id
        kind = _effect_kind(layer)
        self._restore_context(handle, layer, role, kind, context)
        key = native_guide_key(handle, layer, role, value)
        column = getattr(layer.semantics, role)
        families = self.families[name].setdefault(key, [])
        family = (
            context["family"]
            if layer.type == "regplot"
            else _FAMILY_NAMES.get(layer.type, layer.type)
        )
        if family not in families:
            families.append(family)
        family_label = " / ".join(families)
        unit = {
            "point": "marker diameter, pt",
            "body": "body stroke, pt",
            "line": "line stroke, pt",
            "rug": "rug stroke, pt",
            "stem": "stem stroke, pt",
            "eventplot": "event tick stroke, pt",
            "field": "cell/contour outline stroke, pt",
        }[kind]
        label = (
            f"size ({family_label}; {unit}): {column}={value}"
            if role == "size"
            else f"{role} ({family_label}): {column}={value}"
        )
        self.handlers.update(getattr(ax, "_mudplot_legend_handlers", {}))
        self.entries[name].setdefault(key, handle).set_label(label)
        handle.remove()

    def finish(self, fig):
        from matplotlib.axes import Axes
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import ListedColormap, Normalize

        from ._render import _continuous_cmap
        from ._semantics import numeric_guides, numeric_mapping

        owned = []
        counts = {}
        for name, request in self.requests.items():
            kind = request.kind
            domain = self.domains.get(name)
            if kind is None and (domain is None or not domain["rows"]):
                continue
            handles = list(self.entries[name].values())
            if kind == "raw":
                order = next(
                    (
                        layer.hue_order
                        for layer in scope_members(self.spec, name, "raw")
                    ),
                    (),
                )
                handles = [
                    self.entries[name][category_key(v)]
                    for v in (order or ())
                    if category_key(v) in self.entries[name]
                ]
            bar_wanted = (
                name in self.scalar_artists
                if kind == "scalar"
                else self.colourbar_intent.get(name, False)
            )
            if not handles and not bar_wanted:
                continue
            side = None if request.bbox_to_anchor is not None else request.location
            ordinal = counts.get(side, 0)
            counts[side] = ordinal + 1
            same_side = sum(
                (None if item.bbox_to_anchor is not None else item.location) == side
                for item in self.requests.values()
            )
            if request.bbox_to_anchor is not None:
                x, y = request.bbox_to_anchor
                location, anchor = "center", (x, y)
                bar_bounds = (x - 0.10, y - 0.12, 0.20, 0.025)
            elif side == "outside right":
                y = 1 - (ordinal + 0.5) / same_side
                location = "center right"
                anchor = (0.98, y + (0.14 / same_side if bar_wanted else 0))
                bar_bounds = (0.74, y - 0.32 / same_side, 0.22, 0.025)
            else:
                x = (ordinal + 0.5) / same_side
                top = side == "outside top"
                location, anchor = (
                    ("upper center", (x, 0.98)) if top else ("lower center", (x, 0.02))
                )
                bar_bounds = (
                    x - 0.10 / same_side,
                    0.87 if top else 0.12,
                    0.20 / same_side,
                    0.025,
                )
            if handles:
                from ._legend_style import legend_handlers

                legend = fig.legend(
                    handles,
                    [handle.get_label() for handle in handles],
                    loc=location,
                    bbox_to_anchor=anchor,
                    bbox_transform=fig.transFigure,
                    title=request.title,
                    frameon=request.frame,
                    ncols=request.ncols
                    or (
                        1
                        if side == "outside right" or side is None
                        else min(4, len(handles))
                    ),
                    handler_map=legend_handlers(handles, request, self.handlers),
                )
                legend._mudplot_shared_guide_side = side
                legend._mudplot_shared_guide_scale_id = name
                owned.append(legend)
            if bar_wanted:
                if kind == "scalar":
                    from dataclasses import replace

                    from ._heatmap_render import draw_colourbar
                    from .spec import ColorbarOptionsSpec

                    ax, layer, owner = self.scalar_artists[name]
                    cax = Axes(fig, bar_bounds, zorder=5)
                    fig.add_artist(cax)
                    cax.set_in_layout(False)
                    cax.__dict__["_mudplot_shared_guide_side"] = side
                    cax.__dict__["_mudplot_shared_guide_scale_id"] = name
                    opts = replace(
                        layer.scalar_display.colorbar_options or ColorbarOptionsSpec(),
                        location="bottom",
                    )
                    if opts.ticks is None:
                        boundaries = layer.scalar_display.boundaries
                        if boundaries is not None:
                            ticks = [
                                boundaries[0],
                                boundaries[(len(boundaries) - 1) // 2],
                                boundaries[-1],
                            ]
                        else:
                            lo, hi = owner.get_clim()
                            ticks = [lo, float(owner.norm.inverse(0.5)), hi]
                        ticks = list(dict.fromkeys(ticks))
                        if opts.tick_format is not None:
                            labels = set()
                            unique = []
                            for tick in ticks:
                                text = format(tick, opts.tick_format)
                                if text not in labels:
                                    unique.append(tick)
                                    labels.add(text)
                            ticks = unique
                        opts = replace(opts, ticks=ticks)
                    draw_colourbar(
                        ax,
                        owner,
                        layer.clabel or layer.c or "",
                        cax=cax,
                        calibrated=True,
                        options=opts,
                    )
                    if request.title:
                        cax.set_title(request.title)
                    owned.append(cax)
                    continue
                config = domain["config"]
                values = [domain["columns"][config.hue][row] for row in domain["rows"]]
                _, bounds = numeric_mapping(values, config.hue_norm)
                if self.cmap_kinds[name] is None:
                    raise ValueError("shared colourbar has no actual persisted owner")
                cmap = _continuous_cmap(self.cmap_kinds[name])
                low, high = bounds
                # This is a figure-owned decoration, not a data axes' child.
                # Keep it outside the subplot engine: its measured strip is
                # reserved by shared_guide_bounds, not by a panel's title logic.
                cax = Axes(fig, bar_bounds, zorder=5)
                fig.add_artist(cax)
                cax.set_in_layout(False)
                cax.__dict__["_mudplot_shared_guide_side"] = side
                cax.__dict__["_mudplot_shared_guide_scale_id"] = name
                if low == high:
                    bar = fig.colorbar(
                        ScalarMappable(
                            norm=Normalize(0, 1), cmap=ListedColormap([cmap(0.5)])
                        ),
                        cax=cax,
                        orientation="horizontal",
                        boundaries=[0, 1],
                        values=[0.5],
                        ticks=[0.5],
                        label=self.colourbar_labels[name],
                    )
                    bar.set_ticklabels([str(low)])
                else:
                    guides = numeric_guides(bounds)
                    ticks, _ = numeric_mapping(guides, bounds)
                    bar = fig.colorbar(
                        ScalarMappable(norm=Normalize(0, 1), cmap=cmap),
                        cax=cax,
                        orientation="horizontal",
                        ticks=ticks,
                        label=self.colourbar_labels[name],
                    )
                    bar.set_ticklabels([str(value) for value in guides])
                if request.title and not handles:
                    cax.set_title(request.title)
                owned.append(cax)
        for ax in self.axes:
            ax._mudplot_shared_guide_collector = None
        self.axes.clear()
        self.entries.clear()
        self.families.clear()
        self.scalar_artists.clear()
        fig._mudplot_shared_guide_artists = owned


def shared_guide_bounds(fig, renderer, pad):
    """Native figure-guide strips participate in the existing layout rectangle."""
    left, bottom, right, top = 0.0, 0.0, 1.0, 1.0
    for artist in getattr(fig, "_mudplot_shared_guide_artists", ()):
        side = getattr(artist, "_mudplot_shared_guide_side", None)
        if side is None:
            continue
        bounds = artist.get_tightbbox(renderer).transformed(fig.transFigure.inverted())
        if side == "outside right":
            right = min(right, bounds.x0 - pad / fig.bbox.width)
        elif side == "outside top":
            top = min(top, bounds.y0 - pad / fig.bbox.height)
        else:
            bottom = max(bottom, bounds.y1 + pad / fig.bbox.height)
    return left, bottom, right, top
