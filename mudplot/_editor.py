"""Renderer-bound editor metadata, imported only at the rendering boundary.

Measure positions from the saved preview's artists, never from panel order.
Text anchors use Matplotlib numeric data coordinates, including UTC days on
temporal axes. Source timestamps and observations are not converted or edited.
"""

from __future__ import annotations

import math
from dataclasses import replace

from ._layout import allocated_ids
from ._layout_render import native_axes, panel_legend
from ._mpl_context import matplotlib_context


def extract_layout(spec, fig, index: int) -> dict:
    if not 0 <= index < len(spec.panels):
        return {}
    ax = next(
        (a for a in native_axes(fig) if getattr(a, "_mudplot_panel", None) == index),
        None,
    )
    if ax is None:
        return {}
    panel = spec.panels[index]
    # PNG truncates fractional size * DPI. Normalize against the saved canvas,
    # keeping each native coordinate frame distinct from image fractions.
    width, height = fig.canvas.get_width_height()

    def image_bbox(transform):
        low, high = transform.transform(((0, 0), (1, 1)))
        return [
            float(low[0] / width),
            float(low[1] / height),
            float(high[0] / width),
            float(high[1] / height),
        ]

    result = {
        "is_3d": panel.projection == "3d",
        "panel": index,
        "panel_id": panel.panel_id,
        "suggested_panel_id": allocated_ids(spec)[index],
        "panel_bbox": image_bbox(ax.transAxes),
        "figure_bbox": image_bbox(fig.transFigure),
        "image_size": [width, height],
        "xlim": list(ax.get_xlim()),
        "ylim": list(ax.get_ylim()),
        "xscale": ax.get_xscale(),
        "yscale": ax.get_yscale(),
        "text_layers": [],
        "handles": [],
        "data_drag_disabled": panel.projection != "2d",
    }
    order = getattr(ax, "_mudplot_cluster_order", None)
    if order is not None and len(panel.layers) == 1:
        layer = panel.layers[0]
        cluster, display = layer.cluster, layer.heatmap
        derived = getattr(ax, "_mudplot_matrix_cuts", {})
        cuts = {}
        for name, plural, label_field in (
            ("row", "rows", "ylabels"),
            ("col", "cols", "xlabels"),
        ):
            count = len(order[plural])
            if count < 2 or (
                cluster is not None and not getattr(cluster, name + "_cluster")
            ):
                continue
            labels = None if display is None else getattr(display, label_field)
            config = None if cluster is None else getattr(cluster, name + "_cut")
            cuts[name] = {
                "items": [
                    {"index": i, "label": str(i) if labels is None else labels[i]}
                    for i in range(count)
                ],
                "height": None if config is None else config.height,
                "anchor": None if config is None else config.anchor,
                "partition": derived.get(name),
            }
        if cuts:
            result["matrix_cuts"] = cuts

    def handle(kind, display_point, *, layer_index=None):
        x, y = display_point[0] / width, display_point[1] / height
        if not all(math.isfinite(float(v)) for v in (x, y)):
            return
        result["handles"].append(
            {
                "kind": kind,
                "imgx": float(x),
                "imgy": float(y),
                "panel_id": panel.panel_id,
                "panel": index,
                "layer_index": layer_index,
            }
        )

    legend = panel_legend(ax)
    if legend is not None:
        box = legend.get_window_extent(fig.canvas.get_renderer())
        center = ((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2)
        handle("legend", center)
    title = getattr(ax, "_mudplot_title_artist", None)
    if title is not None and panel.projection != "3d":
        handle("title", title.get_transform().transform(title.get_position()))
    # Never approximate non-Cartesian data transforms by Cartesian interpolation.
    # Polar titles retain axes fractions; legends retain figure fractions.
    if panel.projection != "2d":
        return result
    secondary = getattr(ax, "_mudplot_secondary_axis", None)
    reasons = []
    for target_name, target in (("primary", ax), ("y2", secondary)):
        if target is None:
            continue
        unsupported = [
            f"{name}={getattr(target, 'get_' + name + 'scale')()}"
            for name in ("x", "y")
            if getattr(target, "get_" + name + "scale")() not in ("linear", "log")
        ]
        reason = (
            f"{target_name} data-anchor dragging is unavailable for "
            + ", ".join(unsupported)
            + "; edit coordinates with JSON."
            if unsupported
            else None
        )
        if reason:
            reasons.append(reason)
            if target_name == "primary":
                result["data_drag_disabled"] = True
        for artist in target.texts:
            layer_index = getattr(artist, "_mudplot_layer_index", None)
            if layer_index is None:
                continue
            layer = panel.layers[layer_index]
            entry = {"index": layer_index, "type": layer.type, "at": list(layer.at)}
            if target is secondary:
                entry.update(ylim=list(target.get_ylim()), yscale=target.get_yscale())
            result["text_layers"].append(entry)
            frame = getattr(artist, "_mudplot_annotation_frame", None)
            if frame is not None:
                entry["coordinates"] = frame
                if frame != "data":
                    entry["drag_disabled_reason"] = (
                        f"{frame}-fraction anchors are editable through stored "
                        "values, not data drags."
                    )
                    continue
            if reason:
                entry["drag_disabled_reason"] = reason
                continue
            handle(
                "layer-at",
                artist.get_transform().transform(artist.get_position()),
                layer_index=layer_index,
            )
            if (
                result["handles"]
                and result["handles"][-1]["layer_index"] == layer_index
            ):
                result["handles"][-1].update(
                    bbox=image_bbox(target.transAxes),
                    xlim=list(target.get_xlim()),
                    ylim=list(target.get_ylim()),
                    xscale=target.get_xscale(),
                    yscale=target.get_yscale(),
                    label=f"{layer.type} layer {layer_index + 1}",
                )
    if reasons:
        result["data_drag_reason"] = " ".join(reasons)
    return result


@matplotlib_context()
def render_preview(spec):
    """Return PNG and all panel metadata from one bounded native figure render."""
    import io

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from ._render import _preview_dpi, _save_figure, render
    from .validate import assert_valid

    assert_valid(spec)
    preview = replace(spec, dpi=_preview_dpi(spec))
    fig = render(preview)
    try:
        buffer = io.BytesIO()
        _save_figure(fig, preview, buffer, "png")
        layouts = [extract_layout(spec, fig, i) for i in range(len(spec.panels))]
        return buffer.getvalue(), layouts
    finally:
        plt.close(fig)
