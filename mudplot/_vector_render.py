"""Native vector effects for pre-admitted N09 plans."""

import numpy as np


def draw_vectors(ax, spec, layer, plan, color_iter):
    from matplotlib.lines import Line2D

    from ._render import _decorate

    color = layer.color
    kind = layer.type
    if kind == "streamplot":
        cfg = layer.vector
        u = np.asarray(spec.data.matrices[cfg.u_matrix], dtype=float)
        v = np.asarray(spec.data.matrices[cfg.v_matrix], dtype=float)
        hidden = np.isnan(u)
        if cfg.mask is not None:
            hidden |= np.asarray(cfg.mask, dtype=bool)
        ink = color or next(color_iter)
        before = len(ax.patches)
        artists = ax.streamplot(
            np.asarray(cfg.x_coords, dtype=float),
            np.asarray(cfg.y_coords, dtype=float),
            np.ma.array(u, mask=hidden, copy=False),
            np.ma.array(v, mask=hidden, copy=False),
            color=ink,
            linewidth=layer.line_width,
            **plan.options,
        )
        artists.lines.set_alpha(layer.alpha)
        artists.lines.set_label(_decorate(layer.label, layer.citation, layer.href))
        for arrow in ax.patches[before:]:
            arrow.set_alpha(layer.alpha)
        return artists
    palette = [color or next(color_iter) for _ in plan.groups]
    if not plan.rows:
        return None
    options = dict(plan.options)
    if layer.line_width is not None:
        options["linewidth"] = layer.line_width
    batch = np.asarray([values for _, _, values in plan.rows], dtype=float)
    colors = [palette[slot] for _, slot, _ in plan.rows]
    label = _decorate(layer.label, layer.citation, layer.href)
    if kind == "quiver":
        q = ax.quiver(
            *batch.T,
            color=colors,
            alpha=layer.alpha,
            label=label if layer.group is None else "_nolegend_",
            **options,
        )
        if options["angles"] == "xy":
            pivot = {"tail": 0, "middle": 0.5, "tip": 1}[options["pivot"]]
            points = batch[:, :2]
            direction = batch[:, 2:]
            ax.update_datalim(points - pivot * direction)
            ax.update_datalim(points + (1 - pivot) * direction)
            ax.autoscale_view()
    elif kind == "barbs":
        q = ax.barbs(
            *batch.T,
            barbcolor=colors,
            flagcolor=colors,
            alpha=layer.alpha,
            label=label if layer.group is None else "_nolegend_",
            **options,
        )
    else:
        # Native shaft rows precede the two adjacent head segments per row.
        q = ax.quiver(
            *batch.T,
            color=colors + [ink for ink in colors for _ in range(2)],
            alpha=layer.alpha,
            label=label if layer.group is None else "_nolegend_",
            **options,
        )
    if layer.group is not None:
        shown = {slot for _, slot, _ in plan.rows}
        for slot in range(len(plan.groups)):
            if slot in shown:
                proxy = Line2D(
                    [],
                    [],
                    color=palette[slot],
                    alpha=layer.alpha,
                    label=_decorate(str(plan.groups[slot]), layer.citation, layer.href),
                )
                ax.add_line(proxy)
    return q
