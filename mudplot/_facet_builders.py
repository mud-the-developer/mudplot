"""Finite figure-level conveniences built from the existing mark and facet actions."""

from dataclasses import replace

FACET_BUILDERS = {
    "relplot": {"scatter": "scatter", "line": "line", "lineplot": "lineplot"},
    "displot": {
        "hist": "hist",
        "kde": "kde",
        "ecdf": "ecdf",
        "rug": "rug",
        "hist2d": "hist2d",
        "kde2d": "kde2d",
        "ecdf2d": "ecdf2d",
    },
    "catplot": {
        "strip": "stripplot",
        "swarm": "swarmplot",
        "box": "box",
        "boxen": "boxenplot",
        "violin": "violin",
        "bar": "barplot",
        "point": "pointplot",
        "count": "countplot",
    },
    "lmplot": {"regplot": "regplot", "residplot": "residplot"},
}
_UNIVARIATE = frozenset({"hist", "kde", "ecdf", "rug", "countplot"})
_OPTIONAL_RESPONSE = frozenset({"box", "boxenplot", "violin"})


def build_facet(
    plot,
    family,
    x,
    y,
    *,
    kind,
    row=None,
    col=None,
    row_order=None,
    col_order=None,
    col_wrap=None,
    share_x="all",
    share_y="all",
    live=True,
    guide=True,
    **mark_options,
):
    """Dispatch to one registered mark; no persisted builder or second data table."""
    from ._shared_guides import RAW_GUIDE_TYPES, raw_guide_issues
    from .actions import ReplaceLayer
    from .spec import SharedGuideSpec
    from .store import Store
    from .validate import assert_valid

    choices = FACET_BUILDERS[family]
    if not isinstance(kind, str) or kind not in choices:
        raise ValueError(f"{family} kind must be one of {', '.join(choices)}")
    if type(guide) is not bool or type(live) is not bool:
        raise ValueError("facet guide and live must be bool")
    if "panel" in mark_options:
        raise ValueError("figure-level facet builders target the source panel")
    spec = plot.spec
    if len(spec.panels) != 1 or spec.panels[0].layers:
        raise ValueError("facet builders need one empty configured source panel")
    has_facets = row is not None or col is not None
    if not has_facets and (
        row_order is not None or col_order is not None or col_wrap is not None
    ):
        raise ValueError("facet orders and wrapping need a row or col")
    method = choices[kind]
    if method in _UNIVARIATE:
        if y is not None:
            raise ValueError(f"{kind} is univariate; omit y")
        args = (x,)
    else:
        if y is None and method not in _OPTIONAL_RESPONSE:
            raise ValueError(f"{kind} requires y")
        args = (x, y)
    if has_facets and method == "hist":
        # The faceted owner requires a declared statistic and shared literal edges.
        mark_options.setdefault(
            "stat", "density" if mark_options.get("density") else "count"
        )
    if has_facets and method == "kde" and "kde" not in mark_options:
        # Request the existing typed KDE path without changing its kernel.
        mark_options.setdefault("kernel", "gaussian")
    # The existing store remains the only writable owner. Preflight the
    # ordinary actions in a disposable store from the exact authored state.
    staged = type(plot)()
    staged._store = Store(spec)
    getattr(staged, method)(*args, **mark_options)
    if not has_facets:
        assert_valid(staged.spec)
        plot.store.dispatch_all(staged.store.history)
        return plot
    layer = staged.spec.panels[0].layers[0]
    if (
        guide
        and spec.panels[0].legend.show
        and layer.type in RAW_GUIDE_TYPES
        and layer.group
        and layer.semantics is None
    ):
        candidate = replace(layer, raw_guide_id="facet_raw_0")
        if not raw_guide_issues(candidate):
            staged.dispatch(ReplaceLayer(0, candidate))
    staged.facet(
        row=row,
        col=col,
        row_order=row_order,
        col_order=col_order,
        col_wrap=col_wrap,
        share_x=share_x,
        share_y=share_y,
        live=live,
    )
    if guide:
        spec = staged.spec
        layer = spec.panels[0].layers[0]
        requests: list[SharedGuideSpec] = list(spec.shared_guides or ())
        scope, guide_kind = None, None
        if layer.raw_guide_id is not None and layer.hue_order:
            scope, guide_kind = layer.raw_guide_id, "raw"
        elif layer.semantics is not None and (
            (spec.panels[0].legend.show and layer.semantics.legend) or layer.colorbar
        ):
            scope = layer.semantics.scale_id
        elif layer.scalar_display is not None and layer.colorbar:
            scope, guide_kind = layer.scalar_display.scale_id, "scalar"
        if scope is not None and all(r.scale_id != scope for r in requests):
            requests.append(
                SharedGuideSpec(scope, location="outside bottom", kind=guide_kind)
            )
            staged.shared_guides(requests)
    assert_valid(staged.spec)
    plot.store.dispatch_all(staged.store.history)
    return plot
