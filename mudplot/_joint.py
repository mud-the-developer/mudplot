"""Pure joint main-view + paired histogram/KDE marginal composition."""

from __future__ import annotations

import copy

from ._ecdf import finite_number
from ._facet import _ordered, ordered_group_columns, panel_columns
from ._histogram import MAX_HISTOGRAM_BINS
from ._kde import option_issues as kde_option_issues
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


def grid_kde_config(kind, bins, stat, kde) -> KDESpec | None:
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
    if config.cumulative or config.weights is not None:
        issues.append("KDE grids do not support cumulative or weighted raw views")
    if issues:
        raise ValueError("; ".join(issues))
    return config


def materialize_joint(
    spec, *, bins, ratio, marginal_stat, marginal_kind="hist", kde=None
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
    if source.projection != "2d" or source.y2 is not None:
        raise ValueError("joint supports primary Cartesian 2D axes only")
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
    if layer.type in ("hist2d", "hexbin") and (
        layer.group is not None
        or layer.hue_order is not None
        or layer.weights is not None
    ):
        raise ValueError("binned joint centers require ungrouped, unweighted raw x/y")
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
    if any(
        not finite_number(value)
        for name in (layer.x, layer.y)
        for value in selected[name]
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
    spec.layout = [2, 2]
    spec.width_ratios = [ratio, 1]
    spec.height_ratios = [ratio, 1]
    spec.share_x, spec.share_y = "col", "row"
    assert_valid(spec)
