"""Pure pairwise scatter/histogram grids; no global data deletion."""

from __future__ import annotations

import copy
from dataclasses import replace

from ._ecdf import finite_number
from ._facet import _ordered, ordered_group_columns
from ._histogram import MAX_HISTOGRAM_BINS
from ._joint import JOINT_STATS, grid_kde_config
from ._stat import is_missing
from .spec import AxisSpec, HistogramSpec, KDESpec, LayerSpec, LegendSpec, PanelSpec

MAX_PAIR_VARIABLES = 8


def materialize_pair(
    spec, *, columns, group, hue_order, bins, diag_stat, diag_kind="hist", kde=None
):
    """Pairwise complete cases, univariate diagonals, live named value-axis links."""
    from .validate import assert_valid

    assert_valid(spec)
    if (
        len(spec.panels) != 1
        or replace(spec.panels[0], legend=LegendSpec()) != PanelSpec()
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
                if diagonal and density is None
                else None,
                kde=copy.deepcopy(density) if diagonal else None,
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
                    x=AxisSpec(label=x, share_id=f"pair_x_{col}"),
                    y=AxisSpec(
                        label=JOINT_STATS[diag_stat] if diagonal else y,
                        share_id=None if diagonal else f"pair_y_{row}",
                    ),
                    legend=LegendSpec(show=False)
                    if diagonal
                    else copy.deepcopy(template.legend),
                )
            )
    spec.panels = panels
    spec.layout = [len(columns), len(columns)]
    spec.width_ratios = spec.height_ratios = None
    spec.share_x = spec.share_y = "none"
    assert_valid(spec)
