"""Opt-in, display-coordinate composition checks for the existing renderer."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace
from itertools import combinations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection, PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.container import BarContainer
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
from matplotlib.ticker import ScalarFormatter
from matplotlib.transforms import Bbox

from ._layout_render import native_axes, panel_legend
from ._lint import LintIssue, LintReport
from ._mpl_context import matplotlib_context
from ._recommend import numeric_warnings
from .color.convert import srgb_to_linear
from .theme import theme_preset

POLICIES = ("smart", "smart-print")


def prepare(spec, policy):
    if policy not in POLICIES:
        raise ValueError(f"layout_policy must be one of {POLICIES}, got {policy!r}")
    # Respect explicit styling; only promote the untouched default theme.
    theme = (
        theme_preset("publication")
        if spec.theme == theme_preset("paper")
        else spec.theme
    )
    return replace(spec, theme=theme)


def drawn_texts(figure):
    """Off-view ticks can be visible objects without actually being drawn."""
    excluded = set()
    for axes in native_axes(figure):
        for axis in (axes.xaxis, axes.yaxis):
            lower, upper = sorted(axis.get_view_interval())
            for tick in [*axis.get_major_ticks(), *axis.get_minor_ticks()]:
                if not lower <= tick.get_loc() <= upper:
                    excluded.update((tick.label1, tick.label2))
    return [
        text
        for text in figure.findobj(Text)
        if text not in excluded
        and (text.axes is None or text.axes.get_visible())
        and text.get_visible()
        and to_rgba(text.get_color(), text.get_alpha())[3] > 0
        and text.get_text().strip()
    ]


def _overlaps(a, b):
    return (
        min(a.x1, b.x1) - max(a.x0, b.x0) > 1 and min(a.y1, b.y1) - max(a.y0, b.y0) > 1
    )


def _inside(inner, outer, tolerance=1):
    return (
        inner.x0 >= outer.x0 - tolerance
        and inner.y0 >= outer.y0 - tolerance
        and inner.x1 <= outer.x1 + tolerance
        and inner.y1 <= outer.y1 + tolerance
    )


def _marker_hits(offsets, radii, box):
    return np.any(
        (offsets[:, 0] + radii > box.x0)
        & (offsets[:, 0] - radii < box.x1)
        & (offsets[:, 1] + radii > box.y0)
        & (offsets[:, 1] - radii < box.y1)
    )


def _visible_members(artist, count):
    if artist.get_hatch():
        return np.ones(count, dtype=bool)
    visible = np.zeros(count, dtype=bool)
    for colors in (artist.get_facecolor(), artist.get_edgecolor()):
        if len(colors):
            visible |= np.resize(colors[:, 3] > 0, count)
    return visible


def _artist_hit(artist, box, renderer):
    alpha = artist.get_alpha()
    if not artist.get_visible() or (
        alpha is not None and np.all(np.asarray(alpha) == 0)
    ):
        return False
    if artist.get_clip_on():
        box = Bbox.intersection(box, artist.axes.bbox)
        if box is None or box.width <= 0 or box.height <= 0:
            return False
    if isinstance(artist, Patch):
        filled = to_rgba(artist.get_facecolor())[3] > 0 or bool(artist.get_hatch())
        if not filled and (
            to_rgba(artist.get_edgecolor())[3] == 0 or artist.get_linewidth() == 0
        ):
            return False
        path = artist.get_transform().transform_path(artist.get_path())
        return path.intersects_bbox(box, filled=filled)
    if isinstance(artist, PathCollection):
        offsets = artist.get_offset_transform().transform(
            np.ma.filled(artist.get_offsets(), np.nan)
        )
        sizes = np.resize(artist.get_sizes(), len(offsets))
        radii = np.sqrt(np.maximum(sizes, 0)) * artist.figure.dpi / 144
        visible = _visible_members(artist, len(offsets))
        return bool(_marker_hits(offsets[visible], radii[visible], box))
    if isinstance(artist, (LineCollection, PolyCollection)):
        paths = artist.get_paths()
        return any(
            artist.get_transform()
            .transform_path(path)
            .intersects_bbox(box, filled=isinstance(artist, PolyCollection))
            for path, visible in zip(
                paths, _visible_members(artist, len(paths)), strict=True
            )
            if visible
        )
    if isinstance(artist, AxesImage):
        pixels = artist.get_array()
        if pixels is None or not np.ma.count(pixels):
            return False
        if pixels.ndim == 3 and pixels.shape[-1] == 4:
            opacity = pixels[..., 3]
            if alpha is not None:
                opacity = opacity * alpha
            if not np.any(opacity > 0):
                return False
    if isinstance(artist, Line2D):
        path = artist.get_transform().transform_path(artist.get_path())
        if (
            artist.get_linestyle() not in ("None", "none", "", " ")
            and to_rgba(artist.get_color(), alpha)[3] > 0
            and path.intersects_bbox(box, filled=False)
        ):
            return True
        if artist.get_marker() not in ("None", "none", "", " ") and any(
            to_rgba(color, alpha)[3] > 0
            for color in (
                artist.get_markerfacecolor(),
                artist.get_markeredgecolor(),
                artist.get_markerfacecoloralt()
                if artist.get_fillstyle() not in ("full", "none")
                else "none",
            )
        ):
            return bool(
                _marker_hits(
                    path.vertices,
                    artist.get_markersize() * artist.figure.dpi / 144,
                    box,
                )
            )
        return False
    return _overlaps(artist.get_window_extent(renderer), box)


def _axes(figure):
    return [ax for ax in figure.findobj(Axes) if ax.get_visible()]


def _legends(figure):
    return [
        legend
        for legend in [*(ax.get_legend() for ax in _axes(figure)), *figure.legends]
        if legend is not None and legend.get_visible()
    ]


def _collisions(figure, renderer):
    collisions = []
    for legend in _legends(figure):
        box = legend.get_window_extent(renderer)
        count = sum(
            _artist_hit(artist, box, renderer)
            for ax in _axes(figure)
            for artist in [*ax.patches, *ax.lines, *ax.collections, *ax.images]
        )
        if count:
            collisions.append((legend, count))
    return collisions


def _legend_key(legend):
    entries = []
    for text, handle in zip(legend.get_texts(), legend.legend_handles, strict=True):
        style = tuple(
            repr(getattr(handle, getter)())
            for getter in (
                "get_facecolor",
                "get_edgecolor",
                "get_color",
                "get_marker",
                "get_linestyle",
                "get_hatch",
            )
            if hasattr(handle, getter)
        )
        entries.append((text.get_text(), text.get_url(), type(handle).__name__, style))
    return legend.get_title().get_text(), tuple(entries)


@matplotlib_context()
def assess(figure, spec, *, min_font_pt=8.0):
    """Measure the configured physical canvas, not a resized preview or tight crop."""
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    issues = []

    def add(code, message, suggestion, *, panel=None, level="warning"):
        issues.append(LintIssue(level, message, code, suggestion, panel))

    collisions = _collisions(figure, renderer)
    if collisions:
        add(
            "legend-data",
            f"{len(collisions)} legend(s) overlap visible data artists.",
            'Render with layout_policy="smart" or place the legend outside.',
            level="error",
        )
    texts = drawn_texts(figure)
    boxes = [text.get_window_extent(renderer).frozen() for text in texts]
    pairs = [
        (left.get_text(), right.get_text())
        for (left, a), (right, b) in combinations(zip(texts, boxes, strict=True), 2)
        if _overlaps(a, b)
    ]
    if pairs:
        add(
            "text-overlap",
            f"{len(pairs)} text overlaps; first: {pairs[0]!r}.",
            "Shorten explicit labels, reduce ticks or increase the publication size.",
            level="error",
        )
    clipped = [
        text.get_text()
        for text, box in zip(texts, boxes, strict=True)
        if not _inside(box, figure.bbox)
    ]
    clipped += [
        "legend"
        for legend in _legends(figure)
        if not _inside(legend.get_window_extent(renderer), figure.bbox)
    ]
    if clipped:
        add(
            "clipped",
            f"Elements extend beyond the intended canvas: {clipped[:4]!r}.",
            "Shorten labels or increase size; tight crops change export size.",
            level="error",
        )
    smallest = min((text.get_fontsize() for text in texts), default=0)
    if texts and smallest < min_font_pt:
        add(
            "small-text",
            f"Smallest rendered text is {smallest:g} pt.",
            f"Use at least {min_font_pt:g} pt at the intended publication size.",
        )
    keys = [_legend_key(legend) for legend in _legends(figure)]
    duplicates = sum(count - 1 for count in Counter(keys).values())
    if duplicates:
        add(
            "duplicate-legend",
            f"{duplicates} legend(s) repeat identical encodings.",
            'Use layout_policy="smart" for one shared legend.',
        )
    from ._layout_render import panel_axes

    axes = panel_axes(figure)
    if not axes:
        axes = figure.axes[: len(spec.panels)]
    for index, (ax, panel) in enumerate(zip(axes, spec.panels, strict=True)):
        if ax.bbox.width / figure.dpi < 0.9 or ax.bbox.height / figure.dpi < 0.7:
            add(
                "crowded-panel",
                "Panel is too small for ordinary scientific labels.",
                "Use fewer panels per figure or increase the intended export size.",
                panel=index,
            )
        descriptions = [(panel.x, "x"), (panel.y, "y")]
        if panel.y2 is not None:
            descriptions.append((panel.y2, "y2"))
        for axis, name in descriptions:
            label = (axis.label or "").strip()
            columns = {
                getattr(layer, "y" if name == "y2" else name)
                for layer in panel.layers
                if name == "x" or layer.axis == name
            }
            raw_label = label in columns and "_" in label
            if (
                not label
                or raw_label
                or re.fullmatch(r"(x|y2?|value|metric|column[_ ]?\d*)", label, re.I)
            ):
                add(
                    "axis-description",
                    f"{name}-axis lacks a scientific description.",
                    "Supply a meaningful description and known units using "
                    + (
                        ".secondary_yaxis(label=...)." if name == "y2" else ".labels()."
                    ),
                    panel=index,
                )
        if re.fullmatch(
            r"(plot|figure|panel|untitled)([ _-]*\d*)", panel.title or "", re.I
        ):
            add(
                "generic-title",
                "Panel title is a generic placeholder.",
                "Name the scientific comparison or remove the redundant title.",
                panel=index,
            )
        data_axes = [ax]
        secondary = getattr(ax, "_mudplot_secondary_axis", None)
        if secondary is not None:
            data_axes.append(secondary)
        hatched = [
            patch
            for data_ax in data_axes
            for patch in (*data_ax.patches, *data_ax.collections)
            if patch.get_visible() and patch.get_hatch()
        ]
        if len(hatched) > 4 or any(len(patch.get_hatch()) > 2 for patch in hatched):
            add(
                "hatch-noise",
                "Repeated or dense hatches can obscure the measurements.",
                "Prefer direct labels; keep sparse hatches for print/accessibility.",
                panel=index,
            )
        names = dict.fromkeys(
            name for layer in panel.layers for name in (layer.x, layer.y) if name
        )
        for name in names:
            for code, message, suggestion in numeric_warnings(spec.data.columns[name]):
                add(code, f"{name}: {message}", suggestion, panel=index)
        collections = (
            (data_ax, collection)
            for data_ax in data_axes
            for collection in data_ax.collections
        )
        for data_ax, collection in collections:
            if not isinstance(collection, PathCollection):
                continue
            points = collection.get_offset_transform().transform(
                np.ma.filled(collection.get_offsets(), np.nan)
            )
            bounds = data_ax.bbox
            visible = (
                np.isfinite(points).all(axis=1)
                & (points[:, 0] >= bounds.x0)
                & (points[:, 0] <= bounds.x1)
                & (points[:, 1] >= bounds.y0)
                & (points[:, 1] <= bounds.y1)
            )
            points = points[visible]
            if len(points) > 50:
                diameter = max(2, np.sqrt(np.max(collection.get_sizes(), initial=0)))
                cells = np.floor(points / (diameter * figure.dpi / 72))
                fraction = 1 - len(np.unique(cells, axis=0)) / len(points)
                if fraction > 0.25:
                    add(
                        "overcrowded-data",
                        f"{fraction:.0%} of markers share display cells.",
                        "Use mp.recommend(): inspect trends, distributions or events; "
                        "do not silently aggregate or remove observations.",
                        panel=index,
                    )
    return LintReport(
        tuple(issues),
        {
            "size_inches": list(figure.get_size_inches()),
            "dpi": figure.dpi,
            "pixels": list(figure.canvas.get_width_height()),
            "min_font_pt": smallest,
            "legend_data_collisions": len(collisions),
            "text_overlaps": len(pairs),
            "clipped_elements": len(clipped),
            "duplicate_legends": duplicates,
        },
    )


def _direct_labels(ax, legend, *, print_safe):
    containers = [c for c in ax.containers if isinstance(c, BarContainer)]
    if (
        len(containers) != 2
        or len(legend.get_texts()) != 2
        or any(
            len(c.patches) != 1 or c.orientation != "vertical" or c.errorbar is not None
            for c in containers
        )
        or legend.get_title().get_text()
        or any(text.get_url() for text in legend.get_texts())
    ):
        return False
    if any(
        container.get_label() != text.get_text()
        for container, text in zip(containers, legend.get_texts(), strict=True)
    ):
        return False
    figure = ax.figure
    renderer = figure.canvas.get_renderer()
    if _overlaps(*(c.patches[0].get_window_extent(renderer) for c in containers)):
        return False
    legend.set_visible(False)
    original_texts = drawn_texts(figure)
    labels = []
    fits = True
    for container, text in zip(containers, legend.get_texts(), strict=True):
        bar = container.patches[0]
        if bar.get_height() == 0:
            fits = False
            break
        positive = bar.get_height() > 0
        top = bar.get_y() + bar.get_height()
        annotation = ax.annotate(
            text.get_text(),
            (bar.get_x() + bar.get_width() / 2, top),
            xytext=(0, 4 if positive else -4),
            textcoords="offset points",
            ha="center",
            va="bottom" if positive else "top",
            fontsize=text.get_fontsize(),
            clip_on=False,
        )
        labels.append(annotation)
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        box = annotation.get_window_extent(renderer)
        if not _inside(box, ax.bbox, tolerance=-1):
            annotation.set_position((0, -5 if positive else 5))
            annotation.set_verticalalignment("top" if positive else "bottom")
            face = np.asarray(to_rgba(bar.get_facecolor()))
            background = np.asarray(to_rgba(ax.get_facecolor()))
            canvas = np.asarray(to_rgba(figure.get_facecolor())[:3])
            background_rgb = background[:3] * background[3] + canvas * (
                1 - background[3]
            )
            displayed_rgb = face[:3] * face[3] + background_rgb * (1 - face[3])
            luminance = float(srgb_to_linear(displayed_rgb) @ [0.2126, 0.7152, 0.0722])
            black_contrast = (luminance + 0.05) / 0.05
            white_contrast = 1.05 / (luminance + 0.05)
            annotation.set_color(
                "black" if black_contrast >= white_contrast else "white"
            )
            figure.canvas.draw()
            box = annotation.get_window_extent(renderer)
            if not _inside(box, bar.get_window_extent(renderer), tolerance=-1):
                fits = False
                break
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    valid = (
        fits
        and len(labels) == 2
        and all(_inside(label.get_window_extent(renderer), ax.bbox) for label in labels)
        and not any(
            _overlaps(
                label.get_window_extent(renderer), other.get_window_extent(renderer)
            )
            for label in labels
            for other in [*original_texts, *labels]
            if label is not other
        )
    )
    if valid:
        legend.remove()
        if not print_safe:
            for container in containers:
                container.patches[0].set_hatch("")
        return True
    for label in labels:
        label.remove()
    legend.set_visible(True)
    return False


def apply_smart(figure, spec, policy):
    repairs = []
    from ._layout_render import panel_axes

    axes = panel_axes(figure)
    for ax, panel in zip(axes, spec.panels, strict=True):
        for axis, attribute, setter in (
            (panel.x, "x", ax.set_xlabel),
            (panel.y, "y", ax.set_ylabel),
        ):
            names = {
                getattr(layer, attribute)
                for layer in panel.layers
                if getattr(layer, attribute)
            }
            if not axis.label and len(names) == 1:
                label = re.sub(r"[_-]+", " ", names.pop())
                setter(label[:1].upper() + label[1:])
                repairs.append("Used a human-readable column name; units not inferred.")
        formatter = ax.yaxis.get_major_formatter()
        if isinstance(formatter, ScalarFormatter):
            formatter.set_powerlimits((-3, 4))
            formatter.set_useOffset(False)
        legend = panel_legend(ax)
        references = any(
            layer.citation or layer.href or layer.references for layer in panel.layers
        )
        if (
            legend is not None
            and not references
            and _direct_labels(ax, legend, print_safe=policy == "smart-print")
        ):
            repairs.append("Replaced a two-method bar legend with direct labels.")
    figure.canvas.draw()
    legends = _legends(figure)
    keys = [_legend_key(legend) for legend in legends]
    duplicate = len(set(keys)) < len(keys)
    if duplicate or _collisions(figure, figure.canvas.get_renderer()):
        entries = {}
        for legend in legends:
            title, keys = _legend_key(legend)
            for key, text, handle in zip(
                keys, legend.get_texts(), legend.legend_handles, strict=True
            ):
                entries.setdefault((title, key), (handle, text, legend.axes))
        labels = [f"{title}: {key[0]}" if title else key[0] for title, key in entries]
        repeated = Counter(labels)
        for i, ((_, _), (_, _, ax)) in enumerate(entries.items()):
            if repeated[labels[i]] > 1:
                context = ax.get_title() if ax is not None else ""
                labels[i] += f" ({context or f'panel {i + 1}'})"
        handles = [entry[0] for entry in entries.values()]
        urls = [entry[1].get_url() for entry in entries.values()]
        for legend in legends:
            legend.remove()
        placed = False
        for location in ("outside upper center", "outside lower center"):
            for columns in range(min(4, len(handles)), 0, -1):
                shared = figure.legend(
                    handles,
                    labels,
                    loc=location,
                    ncols=columns,
                    fontsize=spec.theme.font.tick_size,
                )
                for text, url in zip(shared.get_texts(), urls, strict=True):
                    text.set_url(url)
                figure.canvas.draw()
                renderer = figure.canvas.get_renderer()
                box = shared.get_window_extent(renderer)
                own_texts = [*shared.get_texts(), shared.get_title()]
                placed = _inside(box, figure.bbox) and not any(
                    _overlaps(box, text.get_window_extent(renderer))
                    for text in drawn_texts(figure)
                    if text not in own_texts
                )
                if placed or (location == "outside lower center" and columns == 1):
                    break
                shared.remove()
            if placed:
                break
        repairs.append("Moved colliding/repeated legends to one outside legend.")
    # A new draw after every repair is essential: constrained layout moves the data.
    report = assess(figure, spec)
    figure.mudplot_quality = {**report.to_dict(), "policy": policy, "repairs": repairs}
