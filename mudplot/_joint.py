"""Pure joint main-view + paired histogram/KDE marginal composition."""

from __future__ import annotations

import copy
from dataclasses import replace

from ._ecdf import finite_number
from ._facet import _ordered, ordered_group_columns, panel_columns
from ._histogram import MAX_HISTOGRAM_BINS
from ._kde import option_issues as kde_option_issues
from ._temporal_data import prepare_temporal_layer
from .spec import (
    MAX_FIGURE_LAYERS,
    AxisSpec,
    ECDFSpec,
    HistogramSpec,
    KDESpec,
    LayerSpec,
    LegendSpec,
    PanelSpec,
    RegressionSpec,
)

JOINT_MAIN_TYPES = ("scatter", "regplot", "hist2d", "hexbin")

GRID_ECDF_STATS = {"count": "count", "probability": "proportion", "percent": "percent"}

JOINT_STATS = {
    "count": "Count",
    "density": "Density",
    "probability": "Probability",
    "percent": "Percent",
}


def grid_kde_config(kind, bins, stat, kde, *, weighted=False) -> KDESpec | None:
    """Validate distribution choices and return KDE settings only when selected."""
    if kind not in ("hist", "kde", "ecdf"):
        raise ValueError("grid distribution kind must be hist, kde or ecdf")
    if kind != "kde":
        if kde is not None:
            raise ValueError("KDE configuration requires kind='kde'")
        if kind == "ecdf" and (
            bins != 20 or not isinstance(stat, str) or stat not in GRID_ECDF_STATS
        ):
            raise ValueError(
                "ECDF grids require count/probability/percent "
                "and unused default bins=20"
            )
        return None
    if bins != 20 or stat != "density":
        raise ValueError("KDE grids require density and do not use histogram bins")
    config = (
        KDESpec()
        if kde is None
        else KDESpec.from_dict(kde.to_dict() if isinstance(kde, KDESpec) else kde)
    )
    if not isinstance(config, KDESpec):
        raise TypeError("KDE grid configuration must decode to KDESpec")
    issues = kde_option_issues(config)
    if config.cumulative or (config.weights is not None and not weighted):
        issues.append("KDE grids do not support cumulative or weighted raw views")
    if issues:
        raise ValueError("; ".join(issues))
    return config


def materialize_joint(
    spec,
    *,
    bins,
    ratio,
    marginal_stat,
    marginal_kind="hist",
    kde=None,
    weights=None,
    complementary=None,
    group=None,
    hue_order=None,
):
    """Keep source rows; all three views select the same complete x/y/group cases."""
    from .validate import assert_valid

    if len(spec.panels) != 1 or spec.panels[0].filters or spec.panels[0].dropna:
        raise ValueError("joint requires one unfiltered source panel")
    if len(spec.panels[0].layers) + 2 > MAX_FIGURE_LAYERS:
        raise ValueError(f"joint expansion exceeds {MAX_FIGURE_LAYERS} total layers")
    source = copy.deepcopy(spec.panels[0])
    if source.x.share_id is not None or source.y.share_id is not None:
        raise ValueError("joint requires axes without named sharing")
    if source.projection != "2d":
        raise ValueError("joint supports Cartesian 2D axes only")
    data_layers = [layer for layer in source.layers if layer.type in JOINT_MAIN_TYPES]
    if len(data_layers) != 1 or any(
        layer.type not in {*JOINT_MAIN_TYPES, "hline", "vline", "text", "annotate"}
        for layer in source.layers
    ):
        raise ValueError(
            "joint needs one completed scatter/regplot/hist2d/hexbin "
            "plus optional annotations"
        )
    layer = data_layers[0]
    if group is not None or hue_order is not None:
        if layer.type != "hexbin" or group is None or layer.group is not None:
            raise ValueError(
                "joint group/hue_order require an otherwise ungrouped hexbin center"
            )
        layer.group, layer.hue_order = group, hue_order
    if (
        weights is not None
        or complementary is not None
        or source.y2 is not None
        or layer.c is not None
        or layer.semantics is not None
        or layer.colorbar
        or layer.transforms is not None
        or layer.orient != "v"
        or layer.weights is not None
        or getattr(kde, "weights", None) is not None
        or getattr(layer.histogram2d, "weights", None) is not None
        or (layer.type in {"hist2d", "hexbin"} and layer.group is not None)
    ):
        _extended_joint(
            spec,
            source,
            layer,
            bins,
            ratio,
            marginal_stat,
            marginal_kind,
            kde,
            weights,
            complementary,
        )
        return
    if layer.type in ("hist2d", "hexbin") and (
        layer.group is not None
        or layer.hue_order is not None
        or layer.weights is not None
    ):
        raise ValueError("binned joint centers require ungrouped, unweighted raw x/y")
    if layer.type == "regplot" and layer.weights is not None:
        raise ValueError("joint does not support weighted regression marginals")
    if isinstance(layer.regression, RegressionSpec) and layer.regression.residual:
        raise ValueError("joint marginals use raw y, not residual responses")
    if (
        layer.semantics is not None
        or layer.c is not None
        or layer.axis != "y"
        or layer.colorbar
        or layer.clabel is not None
    ):
        raise ValueError("joint currently uses raw group mapping, not semantics/c/y2")
    if type(bins) is not int or not 1 <= bins <= MAX_HISTOGRAM_BINS:
        raise ValueError(f"joint bins must be an integer in [1,{MAX_HISTOGRAM_BINS}]")
    density = grid_kde_config(marginal_kind, bins, marginal_stat, kde)
    if not finite_number(ratio) or not 1 <= ratio <= 10:
        raise ValueError("joint ratio must be finite in [1,10]")
    if not isinstance(marginal_stat, str) or marginal_stat not in JOINT_STATS:
        raise ValueError(
            "joint marginal_stat must be count/density/probability/percent"
        )

    source.dropna = list(
        dict.fromkeys(
            [layer.x, layer.y] + ([layer.group] if layer.group is not None else [])
        )
    )
    spec.panels = [source]
    assert_valid(spec)
    selected = ordered_group_columns(panel_columns(spec.data.columns, source), layer)
    if not selected[layer.x]:
        raise ValueError("joint needs at least one complete selected x/y observation")
    coordinate_columns, coordinate_layer, _mask = prepare_temporal_layer(
        selected, layer, source
    )
    if any(
        not finite_number(value)
        for name in (coordinate_layer.x, coordinate_layer.y)
        for value in coordinate_columns[name]
    ):
        raise ValueError(
            "joint coordinates must be finite numeric, not bool/categories"
        )
    if layer.group is not None and layer.hue_order is None:
        layer.hue_order = _ordered(selected[layer.group])
    source.x.label = source.x.label or layer.x
    source.y.label = source.y.label or layer.y

    def marginal(name, orient):
        return LayerSpec(
            type=marginal_kind,
            x=name,
            group=layer.group,
            hue_order=copy.deepcopy(layer.hue_order),
            bins=bins,
            orient=orient,
            histogram=HistogramSpec(stat=marginal_stat)
            if marginal_kind == "hist"
            else None,
            kde=copy.deepcopy(density),
            ecdf=ECDFSpec(stat=GRID_ECDF_STATS[marginal_stat])
            if marginal_kind == "ecdf"
            else None,
            color=layer.color,
            alpha=min(layer.alpha, 0.6),
        )

    vertical = PanelSpec(
        layers=[marginal(layer.y, "h")],
        x=AxisSpec(label=JOINT_STATS[marginal_stat]),
        y=copy.deepcopy(source.y),
        legend=LegendSpec(show=False),
        dropna=list(source.dropna),
    )
    vertical.y.label = ""
    horizontal = PanelSpec(
        layers=[marginal(layer.x, "v")],
        x=copy.deepcopy(source.x),
        y=AxisSpec(label=JOINT_STATS[marginal_stat]),
        legend=LegendSpec(show=False),
        dropna=list(source.dropna),
    )
    source.x.label = ""
    spec.panels = [source, vertical, horizontal]
    if source.panel_id is not None:
        from ._layout import panel_ids

        panel_ids(spec)
    spec.layout = [2, 2]
    spec.width_ratios = [ratio, 1]
    spec.height_ratios = [ratio, 1]
    spec.share_x, spec.share_y = "col", "row"
    assert_valid(spec)


def strict_grid_options(kind, complementary):
    if complementary is not None and type(complementary) is not bool:
        raise ValueError("complementary must be bool")
    if complementary and kind != "ecdf":
        raise ValueError("strict complement requires ECDF marginals or diagonals")


def grid_roles(semantics, group, order, name):
    from ._semantics import option_issues
    from .spec import SemanticSpec

    if semantics is not None and group is not None:
        raise ValueError("use one grid SemanticSpec or one raw group")
    if semantics is None and group is not None:
        semantics = SemanticSpec(hue=group, hue_order=order)
    if semantics is None:
        return None
    if not isinstance(semantics, SemanticSpec):
        raise ValueError("grid semantics must be a SemanticSpec")
    issues = option_issues(semantics)
    if issues:
        raise ValueError("; ".join(issues))
    return replace(semantics, scale_id=semantics.scale_id or name)


def grid_stat_label(stat, weights, complementary):
    if complementary:
        return {
            "count": "Mass above" if weights is not None else "Count above",
            "probability": "Survival probability",
            "percent": "Survival (%)",
        }[stat]
    if weights is not None and stat == "count":
        return "Weighted mass"
    return JOINT_STATS[stat]


def aggregate_grid_view(
    name, orient, kind, bins, stat, kde, roles, weight, complementary
):
    return LayerSpec(
        type=kind,
        x=name,
        orient=orient,
        bins=bins,
        semantics=copy.deepcopy(roles),
        histogram=HistogramSpec(stat=stat, weights=weight) if kind == "hist" else None,
        kde=None if kde is None else replace(kde, weights=weight),
        ecdf=ECDFSpec(
            stat=GRID_ECDF_STATS[stat],
            complementary=bool(complementary),
            weights=weight,
        )
        if kind == "ecdf"
        else None,
    )


def _extended_joint(
    spec,
    source,
    layer,
    bins,
    ratio,
    stat,
    kind,
    kde,
    requested,
    complementary,
):
    from ._facet import panel_rows
    from ._grid_cohort import common_weight, grid_weight
    from .spec import Histogram2DSpec, ScalarDisplaySpec, SharedGuideSpec

    if type(bins) is not int or not 1 <= bins <= MAX_HISTOGRAM_BINS:
        raise ValueError(f"joint bins must be an integer in [1,{MAX_HISTOGRAM_BINS}]")
    if not finite_number(ratio) or not 1 <= ratio <= 10:
        raise ValueError("joint ratio must be finite in [1,10]")
    if not isinstance(stat, str) or stat not in JOINT_STATS:
        raise ValueError(
            "joint marginal_stat must be count/density/probability/percent"
        )
    strict_grid_options(kind, complementary)
    density = grid_kde_config(kind, bins, stat, kde, weighted=True)
    if isinstance(layer.regression, RegressionSpec) and (
        layer.regression.residual or layer.regression.sampling is not None
    ):
        raise ValueError(
            "extended joint requires raw paired regression "
            "without residuals or train/query splits"
        )
    if layer.axis not in ("y", "y2") or (layer.axis == "y2") != (source.y2 is not None):
        raise ValueError("joint requires the actual center measurement axis")
    if source.y2 is not None and source.y2.share_id is not None:
        raise ValueError("joint requires axes without named sharing")
    if layer.c is not None and layer.type != "scatter":
        raise ValueError("joint legacy c is supported only by scatter")
    if layer.type == "hexbin" and layer.semantics is not None:
        raise ValueError(
            "joint hexbin takes a raw categorical group, not point mappings"
        )
    if layer.type == "hexbin" and layer.orient != "v":
        raise ValueError("hexbin uses native x/y geometry")
    overlay = getattr(layer.histogram2d, "kde", None)
    weight = common_weight(
        spec.data.columns,
        requested,
        grid_weight(layer),
        getattr(density, "weights", None),
        getattr(overlay, "weights", None),
    )
    roles = grid_roles(layer.semantics, layer.group, layer.hue_order, "joint_roles")
    center_group = layer.group
    if roles is not None and layer.type in {"scatter", "hist2d"}:
        layer.semantics = copy.deepcopy(roles)
        layer.group = layer.hue_order = None
    if layer.type == "hist2d":
        cfg = layer.histogram2d or Histogram2DSpec(
            stat="density" if layer.density else "count"
        )
        layer.histogram2d = replace(cfg, weights=weight)
    elif layer.type in {"scatter", "hexbin", "regplot"}:
        layer.weights = weight
    if layer.c is not None:
        if roles is not None:
            raise ValueError(
                "joint scalar c cannot compete with a hue/semantic mapping"
            )
        if layer.scalar_display is None:
            layer.scalar_display = ScalarDisplaySpec(cmap=f"mudplot-{layer.cmap_kind}")
            layer.cmap_kind = "sequential"
    source.dropna = list(
        dict.fromkeys([layer.x, layer.y] + ([layer.c] if layer.c is not None else []))
    )
    source.grid_cohort = True
    selected = panel_rows(spec.data.columns, source)
    if not selected:
        raise ValueError("joint needs at least one complete selected x/y observation")
    if center_group is not None and roles is not None and roles.hue_order is None:
        order = _ordered(spec.data.columns[center_group][i] for i in selected)
        roles = replace(roles, hue_order=order)
        if layer.semantics is not None and layer.semantics.hue == center_group:
            layer.semantics = copy.deepcopy(roles)
        else:
            layer.hue_order = list(order)
    # The binned horizontal owner swaps logical x/y; native scatter does not.
    swap = layer.orient == "h" and layer.type in {"regplot", "hist2d"}
    xn, yn = (layer.y, layer.x) if swap else (layer.x, layer.y)
    target = source.y2 if source.y2 is not None else source.y
    source.x.share_id, target.share_id = "joint_x", "joint_y"
    source.x.label = source.x.label or xn
    target.label = target.label or yn
    xaxis, yaxis = copy.deepcopy(source.x), copy.deepcopy(target)
    source.x.label = yaxis.label = ""
    stat_label = grid_stat_label(stat, weight, complementary)
    right = aggregate_grid_view(
        yn, "h", kind, bins, stat, density, roles, weight, complementary
    )
    bottom = aggregate_grid_view(
        xn, "v", kind, bins, stat, density, roles, weight, complementary
    )
    for marginal, logical in (
        (right, "x" if swap else "y"),
        (bottom, "y" if swap else "x"),
    ):
        if layer.transforms is not None:
            marginal.transforms = [
                replace(step, role="x")
                for step in layer.transforms
                if step.role == logical
            ] or None
        marginal.alpha = min(layer.alpha, 0.6)
        if roles is not None and roles.hue_kind == "numeric":
            marginal.cmap_kind = layer.cmap_kind
    spec.panels = [
        source,
        PanelSpec(
            layers=[right],
            x=AxisSpec(label=stat_label),
            y=yaxis,
            legend=LegendSpec(show=False),
            dropna=list(source.dropna),
            grid_cohort=True,
        ),
        PanelSpec(
            layers=[bottom],
            x=xaxis,
            y=AxisSpec(label=stat_label),
            legend=LegendSpec(show=False),
            dropna=list(source.dropna),
            grid_cohort=True,
        ),
    ]
    if source.panel_id is not None:
        from ._layout import panel_ids

        panel_ids(spec)
    spec.layout = [2, 2]
    spec.width_ratios = [ratio, 1]
    spec.height_ratios = [ratio, 1]
    spec.share_x = spec.share_y = "none"
    if roles is not None and (
        (roles.legend and source.legend.show)
        or (layer.type in {"scatter", "regplot"} and layer.colorbar)
    ):
        assert roles.scale_id is not None
        spec.shared_guides = [
            SharedGuideSpec(roles.scale_id, location="outside bottom")
        ]
