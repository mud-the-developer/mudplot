"""Pure pairwise scatter/histogram grids; no global data deletion."""

from __future__ import annotations

import copy
from dataclasses import replace

from ._ecdf import finite_number
from ._facet import _ordered, ordered_group_columns
from ._histogram import MAX_HISTOGRAM_BINS
from ._joint import GRID_ECDF_STATS, JOINT_STATS, grid_kde_config
from ._stat import is_missing
from ._temporal import temporal_coordinates
from ._temporal_data import temporal_options
from .spec import (
    AxisSpec,
    ECDFSpec,
    HistogramSpec,
    KDESpec,
    LayerSpec,
    LegendSpec,
    PanelSpec,
    TemporalSpec,
)

MAX_PAIR_VARIABLES = 8


def temporal_configs(temporal, columns):
    if temporal is None:
        return None
    if not isinstance(temporal, dict) or any(name not in columns for name in temporal):
        raise ValueError("pair temporal declarations must name selected variables")
    result = {}
    for name, config in temporal.items():
        if isinstance(config, dict):
            config = TemporalSpec.from_dict(config)
        options = temporal_options(config)
        temporal_coordinates([], **options)
        result[name] = copy.deepcopy(config)
    return result


def materialize_pair(
    spec,
    *,
    columns,
    group,
    hue_order,
    bins,
    diag_stat,
    diag_kind="hist",
    kde=None,
    temporal=None,
    corner=None,
    weights=None,
    complementary=None,
    semantics=None,
):
    """Pairwise complete cases, univariate diagonals, live named value-axis links."""
    from .validate import assert_valid

    assert_valid(spec)
    if (
        len(spec.panels) != 1
        or replace(spec.panels[0], legend=LegendSpec(), panel_id=None, placement=None)
        != PanelSpec()
    ):
        raise ValueError(
            "pair requires one empty default panel; configure cell axes afterwards"
        )
    if (
        not isinstance(columns, (list, tuple))
        or not 2 <= len(columns) <= MAX_PAIR_VARIABLES
        or any(not isinstance(name, str) or not name for name in columns)
        or len(set(columns)) != len(columns)
    ):
        raise ValueError("pair requires 2..8 unique numeric column names")
    if any(name not in spec.data.columns for name in columns):
        raise ValueError("pair variables must exist in source columns")
    if group is not None and (
        not isinstance(group, str) or not group or group not in spec.data.columns
    ):
        raise ValueError("pair group must name an existing column")
    if group is None and hue_order is not None:
        raise ValueError("pair hue_order requires group")
    if type(bins) is not int or not 1 <= bins <= MAX_HISTOGRAM_BINS:
        raise ValueError(f"pair bins must be an integer in [1,{MAX_HISTOGRAM_BINS}]")
    if not isinstance(diag_stat, str) or diag_stat not in JOINT_STATS:
        raise ValueError("pair diag_stat must be count/density/probability/percent")

    clocks = temporal_configs(temporal, columns) or {}
    if any(
        value is not None
        for value in (
            corner,
            weights,
            complementary,
            semantics,
            getattr(kde, "weights", None),
        )
    ):
        _extended_pair(
            spec,
            columns,
            clocks,
            group,
            hue_order,
            bins,
            diag_stat,
            diag_kind,
            kde,
            corner,
            weights,
            complementary,
            semantics,
        )
        return
    density: KDESpec | None = grid_kde_config(diag_kind, bins, diag_stat, kde)
    data = spec.data.columns
    if group is not None:
        observed = [
            value
            for index, value in enumerate(data[group])
            if any(not is_missing(data[name][index]) for name in columns)
        ]
        hue_order = _ordered(observed, hue_order)
        if not hue_order:
            raise ValueError("pair has no selected grouped observations")
    selector = LayerSpec(type="scatter", group=group, hue_order=hue_order)
    selected = ordered_group_columns(data, selector)
    for name in columns:
        values = [value for value in selected[name] if not is_missing(value)]
        if name in clocks:
            values = temporal_coordinates(values, **temporal_options(clocks[name]))
        if not values or any(not finite_number(value) for value in values):
            raise ValueError(
                f"pair {name!r} needs finite numeric values, not bool/categories"
            )

    template = spec.panels[0]
    panels = []
    for row, y in enumerate(columns):
        for col, x in enumerate(columns):
            diagonal = row == col
            layer = LayerSpec(
                type=diag_kind if diagonal else "scatter",
                x=x,
                y="" if diagonal else y,
                group=group,
                hue_order=copy.deepcopy(hue_order),
                bins=bins if diagonal else 20,
                histogram=HistogramSpec(stat=diag_stat)
                if diagonal and diag_kind == "hist"
                else None,
                kde=copy.deepcopy(density) if diagonal else None,
                ecdf=ECDFSpec(stat=GRID_ECDF_STATS[diag_stat])
                if diagonal and diag_kind == "ecdf"
                else None,
            )
            required = list(
                dict.fromkeys(
                    [x] + ([] if diagonal else [y]) + ([group] if group else [])
                )
            )
            panels.append(
                PanelSpec(
                    layers=[layer],
                    dropna=required,
                    x=AxisSpec(
                        label=x,
                        share_id=f"pair_x_{col}",
                        temporal=copy.deepcopy(clocks.get(x)),
                    ),
                    y=AxisSpec(
                        label=JOINT_STATS[diag_stat] if diagonal else y,
                        share_id=None if diagonal else f"pair_y_{row}",
                        temporal=None if diagonal else copy.deepcopy(clocks.get(y)),
                    ),
                    legend=LegendSpec(show=False)
                    if diagonal
                    else copy.deepcopy(template.legend),
                )
            )
    spec.panels = panels
    if template.panel_id is not None:
        from ._layout import panel_ids

        panel_ids(spec)
    spec.layout = [len(columns), len(columns)]
    spec.width_ratios = spec.height_ratios = None
    spec.share_x = spec.share_y = "none"
    assert_valid(spec)


def _extended_pair(
    spec,
    columns,
    clocks,
    group,
    hue_order,
    bins,
    stat,
    kind,
    kde,
    corner,
    weights,
    complementary,
    semantics,
):
    from ._facet import panel_rows
    from ._grid_cohort import common_weight
    from ._joint import (
        aggregate_grid_view,
        grid_roles,
        grid_stat_label,
        strict_grid_options,
    )
    from .spec import GridCellSpec, LayoutGridSpec, PanelLayoutSpec, PanelPlacementSpec

    if corner is not None and type(corner) is not bool:
        raise ValueError("pair corner must be bool")
    strict_grid_options(kind, complementary)
    roles = grid_roles(semantics, group, hue_order, "pair_roles")
    kde = grid_kde_config(kind, bins, stat, kde, weighted=True)
    weight = common_weight(spec.data.columns, weights, getattr(kde, "weights", None))
    stat_label = grid_stat_label(stat, weight, complementary)
    default = spec.panels[0]
    panels = []
    for row, y in enumerate(columns):
        for col, x in enumerate(columns):
            if corner and col > row:
                continue
            diagonal = row == col
            layer = (
                aggregate_grid_view(
                    x, "v", kind, bins, stat, kde, roles, weight, complementary
                )
                if diagonal
                else LayerSpec(
                    type="scatter",
                    x=x,
                    y=y,
                    semantics=copy.deepcopy(roles),
                    weights=weight,
                )
            )
            panel = PanelSpec(
                layers=[layer],
                dropna=[x] if diagonal else [x, y],
                grid_cohort=True,
                x=AxisSpec(
                    label=x,
                    share_id=f"pair_x_{col}",
                    temporal=copy.deepcopy(clocks.get(x)),
                ),
                y=AxisSpec(
                    label=stat_label if diagonal else y,
                    share_id=None if diagonal else f"pair_y_{row}",
                    temporal=None if diagonal else copy.deepcopy(clocks.get(y)),
                ),
                legend=LegendSpec(show=False)
                if diagonal
                else copy.deepcopy(default.legend),
            )
            if diagonal and not panel_rows(spec.data.columns, panel):
                raise ValueError(f"pair {x!r} needs selected observations")
            if corner:
                panel.panel_id = f"pair_{row}_{col}"
                panel.placement = PanelPlacementSpec(
                    cell=GridCellSpec("pair", row, col)
                )
            panels.append(panel)
    spec.panels = panels
    n = len(columns)
    spec.layout = None if corner else [n, n]
    spec.panel_layout = (
        PanelLayoutSpec([LayoutGridSpec("pair", n, n)]) if corner else None
    )
    spec.width_ratios = spec.height_ratios = None
    spec.share_x = spec.share_y = "none"
    if not corner and default.panel_id is not None:
        from ._layout import panel_ids

        panel_ids(spec)
    if roles is not None and roles.legend and default.legend.show:
        from .spec import SharedGuideSpec

        assert roles.scale_id is not None
        spec.shared_guides = [
            SharedGuideSpec(roles.scale_id, location="outside bottom")
        ]
