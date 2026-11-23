"""Native subplot slots and measured matrix guide bounds, in logical panel scope."""

from __future__ import annotations

from matplotlib.transforms import Bbox


def align_axis(axes, body, *, horizontal, ratio=None):
    def locate(_axes, _renderer):
        slot = axes.get_position(original=True)
        box = body.get_position()
        if ratio is None:
            return (
                Bbox.from_extents(box.x0, slot.y0, box.x1, slot.y1)
                if horizontal
                else Bbox.from_extents(slot.x0, box.y0, slot.x1, box.y1)
            )
        elif horizontal:
            y = ratio * box.height
        else:
            x = ratio * box.width
        if horizontal:
            return Bbox.from_bounds(
                box.x0, slot.y0 + (slot.height - y) / 2, box.width, y
            )
        return Bbox.from_bounds(slot.x0 + (slot.width - x) / 2, box.y0, x, box.height)

    axes.set_axes_locator(locate)


def matrix_slots(body, *, left=(), right=(), top=(), bottom=()):
    """Place owned side slots nearest-to-farthest outside the logical body."""
    columns = [*reversed(left), ("body", 1), *right]
    rows = [*reversed(top), ("body", 1), *bottom]
    yi, xi = len(top), len(left)
    slot = body.get_subplotspec()
    if slot is None:
        raise ValueError("matrix decorations require a logical subplot cell")
    grid = slot.subgridspec(
        len(rows),
        len(columns),
        height_ratios=[v for _, v in rows],
        width_ratios=[v for _, v in columns],
        wspace=0,
        hspace=0,
    )
    body.set_subplotspec(grid[yi, xi])
    slots = {}
    for position, (name, _) in enumerate(columns):
        if name not in ("body", "pad"):
            slots[name] = (grid[yi, position], False, position)
    for position, (name, _) in enumerate(rows):
        if name not in ("body", "pad"):
            slots[name] = (grid[position, xi], True, position)
    return grid, slots


def side_plot(body, slots, name, ratio=None):
    slot, horizontal, _ = slots[name]
    owner = body.figure.add_subplot(slot)
    owner._mudplot_matrix_decoration = True
    owner._mudplot_matrix_panel = body
    align_axis(owner, body, horizontal=horizontal, ratio=ratio)
    return owner


def plot_colorbar_slot(body, side, fraction, pad):
    # The native layout engine separately reserves ticks/labels; these ratios
    # reserve the requested thickness and minimum blank pad in the data frame.
    _, slots = matrix_slots(body, **{side: [("pad", pad), ("bar", fraction)]})
    return side_plot(body, slots, "bar", fraction)


def fit_matrix_legends(fig):
    """Measure native legends and fit one owned lane per declaring panel."""
    lanes = getattr(fig, "_mudplot_matrix_legend_lanes", ())
    if not lanes:
        return
    for _ in range(2):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for body, owner, grid, horizontal, pos, legends in lanes:
            box = body.get_window_extent(renderer)
            sizes = [legend.get_window_extent(renderer).size for legend in legends]
            pad = fig.dpi * 0.035
            if horizontal:
                # Pack the declared order into horizontal rows, with no elision.
                x = y = row_height = 0.0
                centers = []
                for w, h in sizes:
                    if x and x + w > box.width:
                        y += row_height + pad
                        x = row_height = 0.0
                    centers.append((x + w / 2, y, h))
                    x += w + pad
                    row_height = max(row_height, h)
                height = y + row_height + pad * 2
                ratios = list(grid.get_height_ratios())
                ratios[pos] = height / max(box.height, 1)
                grid.set_height_ratios(ratios)
                for legend, (x, top, h) in zip(legends, centers, strict=True):
                    legend.set_bbox_to_anchor(
                        (x / box.width, 1 - (top + h / 2 + pad) / height),
                        transform=owner.transAxes,
                    )
            else:
                width = max(w for w, _ in sizes) + pad * 2
                total = sum(h + pad for _, h in sizes)
                ratios = list(grid.get_width_ratios())
                ratios[pos] = width / max(box.width, 1)
                grid.set_width_ratios(ratios)
                top = (box.height + total) / 2
                for legend, (w, h) in zip(legends, sizes, strict=True):
                    legend.set_bbox_to_anchor(
                        ((w / 2 + pad) / width, (top - h / 2) / box.height),
                        transform=owner.transAxes,
                    )
                    top -= h + pad


def check_matrix_layout(fig):
    """Check actual advanced guide geometry; leave legacy warnings alone."""
    from ._layout_render import native_axes

    renderer = fig.canvas.get_renderer()
    axes = list(native_axes(fig))
    bound = fig.bbox
    decorations = []
    for ax in axes:
        if not getattr(ax, "_mudplot_matrix_decoration", False):
            continue
        box = ax.get_tightbbox(renderer)
        if box is not None:
            decorations.append((ax, box))

    def intersects(a, b):
        overlap = Bbox.intersection(a, b)
        return overlap is not None and overlap.width > 1 and overlap.height > 1

    for owner, box in decorations:
        if (
            box.width <= 0
            or box.height <= 0
            or box.x0 < bound.x0 - 1
            or box.x1 > bound.x1 + 1
            or box.y0 < bound.y0 - 1
            or box.y1 > bound.y1 + 1
        ):
            raise ValueError(
                "matrix guide does not fit the configured figure; "
                "enlarge or reposition it"
            )
        logical = getattr(owner, "_mudplot_matrix_panel", None)
        if logical is not None and intersects(box, logical.get_window_extent(renderer)):
            raise ValueError(
                "matrix guide overlaps its data frame; enlarge or reposition it"
            )
        if (
            getattr(owner, "_colorbar", None) is not None
            and logical is not None
            and intersects(box, logical.get_tightbbox(renderer))
        ):
            raise ValueError(
                "matrix colourbar overlaps body labels; widen the pad or reposition it"
            )
        for other in axes:
            if other is owner or other is logical:
                continue
            if getattr(other, "_mudplot_matrix_panel", None) is logical:
                # Same-panel perpendicular track/tree slots share an alignment
                # edge, but guides/legends must not overlap the data frame.
                continue
            if hasattr(other, "_mudplot_panel") and intersects(
                box, other.get_window_extent(renderer)
            ):
                raise ValueError(
                    "matrix guide overlaps another logical panel; "
                    "enlarge or reposition it"
                )
    for body, owner, _, _, _, legends in getattr(
        fig, "_mudplot_matrix_legend_lanes", ()
    ):
        boxes = [legend.get_window_extent(renderer) for legend in legends]
        peers = [
            body.get_tightbbox(renderer),
            *(
                box
                for candidate, box in decorations
                if candidate is not owner
                and getattr(candidate, "_mudplot_matrix_panel", None) is body
            ),
        ]
        for i, box in enumerate(boxes):
            if any(
                intersects(box, peer)
                for peer in (*peers, *boxes[:i])
                if peer is not None
            ):
                raise ValueError(
                    "matrix track legend overlaps matrix decorations; "
                    "enlarge or reposition it"
                )
