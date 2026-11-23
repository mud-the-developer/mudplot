"""Actual Matplotlib hex lattice for the bounded, weighted grid view."""

import math

from ._semantics import category_key


def hex_issues(layer, panel):
    issues = []
    y = panel.y2 if layer.axis == "y2" else panel.y
    if y is None or panel.x.scale != "linear" or y.scale != "linear":
        issues.append("grid hexbin requires linear numeric or declared calendar axes")
    if layer.orient != "v" or layer.c is not None or layer.semantics is not None:
        issues.append(
            "grid hexbin takes native x/y, optional raw groups and a named weight"
        )
    if layer.group is not None and (
        layer.edge_color is not None or layer.line_width == 0
    ):
        issues.append("grouped hexbin owns a positive native group-outline stroke")
    return issues


def draw_hex_field(ax, columns, layer, panel, row_ids, color_iter):
    import numpy as np
    from matplotlib.colors import Normalize

    from ._facet import _ordered
    from ._field_render import figure_field_budget, retain_leases, statistic_colourbar
    from ._render import _continuous_cmap, _decorate

    xs, ys = columns[layer.x], columns[layer.y]
    if not len(xs):
        return
    budget = figure_field_budget(ax.figure, layer, panel)
    assert budget is not None
    weights = None if layer.weights is None else columns[layer.weights]
    groups = (
        [None]
        if layer.group is None
        else _ordered(columns[layer.group], layer.hue_order)
    )
    # These are the native scalar gridsize resolution and its two staggered sets.
    nx = layer.gridsize
    ny = max(1, int(nx / math.sqrt(3)))
    cells = (nx + 1) * (ny + 1) + nx * ny
    physical = max(1, layer.mincnt or 0)
    budget.charge("hex_native_lattice", len(groups) * (32 * len(xs) + 24 * cells))
    budget.admit_vertices(7 * cells * len(groups))
    retained = []
    artists = []
    peak = 0.0
    try:
        with budget.lease(240 * cells + 112 * len(xs) + 8192):

            def span(values):
                lo, hi = min(values), max(values)
                if lo == hi:
                    pad = abs(lo) * 0.1 if lo else 0.1
                    return lo - pad, hi + pad
                return lo, hi

            xlo, xhi = span(xs)
            ylo, yhi = span(ys)
            if not all(
                math.isfinite(v) for v in (xlo, xhi, ylo, yhi, xhi - xlo, yhi - ylo)
            ):
                raise ValueError("grid hexbin needs a finite native lattice extent")
            extent = (xlo, xhi, ylo, yhi)
            cmap = _continuous_cmap(layer.cmap_kind)
            norm = Normalize(0, 1)
            source_groups = None if layer.group is None else columns[layer.group]

            def reducer(values):
                if len(values) < physical:
                    return np.nan
                return len(values) if weights is None else math.fsum(values)

            for group in groups:
                edge = layer.edge_color if group is None else next(color_iter)
                ids = (
                    range(len(xs))
                    if source_groups is None
                    else [
                        i
                        for i, value in enumerate(source_groups)
                        if category_key(value) == category_key(group)
                    ]
                )
                if not ids:
                    continue
                lease = budget.lease(80 * cells + 40 * len(ids) + 8192)
                retained.append(lease)
                x = [xs[i] for i in ids]
                y = [ys[i] for i in ids]
                # Native reducer owns memberships; the borrowed coordinate C in
                # count mode supplies only list length, never scalar weights.
                c = x if weights is None else [weights[i] for i in ids]
                artist = ax.hexbin(
                    x,
                    y,
                    C=c,
                    reduce_C_function=reducer,
                    mincnt=0,
                    gridsize=(nx, ny),
                    extent=extent,
                    norm=norm,
                    cmap=cmap,
                    edgecolors=edge or "face",
                    linewidths=layer.line_width,
                    alpha=layer.alpha,
                )
                payload = artist.get_array()
                if not len(payload):
                    artist.remove()
                    retained.pop().close()
                    continue
                peak = max(peak, float(np.max(payload)))
                budget.emit_vertices(7 * len(payload))
                artist._mudplot_hex_field = {
                    "group": group,
                    "source_row_indices": tuple(row_ids[i] for i in ids),
                    "extent": extent,
                    "mincnt": physical,
                }
                if group is not None:
                    from matplotlib.lines import Line2D

                    # Real native outline sample, independent of scalar fill.
                    h = Line2D(
                        [],
                        [],
                        marker="h",
                        linestyle="None",
                        markerfacecolor="none",
                        markeredgecolor=edge,
                        markeredgewidth=(
                            layer.line_width if layer.line_width is not None else 1
                        ),
                        label=_decorate(str(group), None, None),
                    )
                    ax.add_line(h)
                artists.append(artist)
            if artists:
                norm.vmax = peak
                if layer.colorbar:
                    units = layer.clabel or (
                        "Weighted mass per hexagon"
                        if weights is not None
                        else "Count per hexagon"
                    )
                    statistic_colourbar(
                        ax,
                        artists[0],
                        units,
                        budget,
                        domain_only=True,
                        generated_units=(None, units) if not layer.clabel else None,
                    )
        retain_leases(ax.figure, retained)
    finally:
        for lease in retained:
            lease.close()
