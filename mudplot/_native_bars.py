"""Supplied heights and literal wedge geometry, never estimates."""

import math
from collections import defaultdict
from decimal import Decimal
from struct import pack, unpack

from ._components import BODY_FIELDS, _color, apply_component_style, style_issues
from ._ecdf import finite_number
from ._semantics import category_key
from ._stat import is_missing
from .spec import BarGeometrySpec, PieGeometrySpec

VALUE_FORMATS = {"g", ".0f", ".1f", ".2f"}


def _format_value(value, fmt):
    if type(value) is int:
        return str(value) if fmt == "g" else format(Decimal(value), fmt)
    return format(value, fmt)


def _body_styles(styles, n, kind):
    if styles is not None:
        if not isinstance(styles, (list, tuple)) or len(styles) != n:
            raise ValueError(
                f"{kind} styles need one optional entry per original source row"
            )
        for item in styles:
            if item is not None:
                issues = style_issues(item, BODY_FIELDS, f"{kind} style", kind)
                if issues:
                    raise ValueError("; ".join(issues))
    return styles


def _texts(values, n, name):
    if (
        not isinstance(values, (list, tuple))
        or len(values) != n
        or any(
            value is not None and (not isinstance(value, str) or len(value) > 256)
            for value in values
        )
    ):
        raise ValueError(
            f"{name} need one bounded text or null per original source row"
        )
    return values


def bars(columns, layer, panel, ids):
    from ._native_geometry import (
        _defined_column,
        _durations,
        _value_axes,
        check_coordinate,
        cohorts,
        coordinates,
    )

    cfg = layer.bar_geometry if layer.bar_geometry is not None else BarGeometrySpec()
    if (
        not isinstance(cfg, BarGeometrySpec)
        or cfg.align not in ("center", "edge")
        or cfg.multiple not in ("dodge", "stack", "layer")
    ):
        raise ValueError("bar geometry requires named alignment and dodge/stack/layer")
    if cfg.labels is not None and cfg.value_format is not None:
        raise ValueError("choose a raw label column or height formatting, not both")
    if cfg.value_format is not None and cfg.value_format not in VALUE_FORMATS:
        raise ValueError("bar requires a named finite value format")
    if not finite_number(cfg.label_padding) or not 0 <= cfg.label_padding <= 72:
        raise ValueError("bar label padding requires 0..72 points")
    if any(
        getattr(layer, f) is not None
        for f in (
            "y_lower",
            "y_upper",
            "xerr",
            "yerr",
            "error_magnitudes",
            "error_color",
            "error_line_width",
            "capsize",
            "capthick",
        )
    ):
        raise ValueError(
            "typed bar geometry cannot combine with legacy bar uncertainty; add "
            "errorbar explicitly"
        )
    category = _defined_column(columns, layer.x)
    values = _defined_column(columns, layer.y)
    n = len(category)
    widths = 0.8 if layer.bar_width is None else layer.bar_width
    if not finite_number(widths) or widths <= 0:
        raise ValueError("native bar width must be finite and positive")
    axs = _value_axes(layer, panel)
    horizontal = layer.type == "barh"
    pos_axis, val_axis = axs[::-1] if horizontal else axs
    if val_axis.temporal is not None:
        raise ValueError("typed bar heights require a numeric value axis")
    if pos_axis.temporal is not None and layer.bar_width is not None:
        widths = _durations([widths], pos_axis)[0]
    widths = float(widths)
    if not widths > 0:
        raise ValueError("native bar width collapses after clock conversion")
    if isinstance(cfg.bottom, str):
        bottoms = _defined_column(columns, cfg.bottom)
    elif finite_number(cfg.bottom):
        bottoms = None
    else:
        raise ValueError("bar bottom must be finite or name a source column")
    labels = (
        None
        if cfg.labels is None
        else _texts(_defined_column(columns, cfg.labels), n, "bar labels")
    )
    styles = _body_styles(cfg.styles, n, "bar")
    groups = cohorts(columns, layer, ids)
    if len(groups) > 64:
        raise ValueError("native bar supports at most 64 raw groups")
    eligible = {
        i
        for _, rows in groups
        for i in rows
        if not is_missing(category[i])
        and not is_missing(values[i])
        and (bottoms is None or not is_missing(bottoms[i]))
    }
    slots = {}
    categorical = pos_axis.temporal is None and any(
        not finite_number(category[i]) for i in eligible
    )
    if categorical:
        if pos_axis.scale != "linear":
            raise ValueError(
                "literal native category bars require a linear position axis"
            )
        for i in ids:
            if i in eligible:
                key = category_key(category[i])
                slots.setdefault(key, (len(slots), str(category[i])))
    coord = {}
    for i in ids:
        if i in eligible:
            raw = category[i]
            if categorical:
                coord[i] = slots[category_key(raw)][0]
            else:
                coord[i] = coordinates([raw], pos_axis)[0]
    if categorical and len(slots) > 64:
        raise ValueError("native bars support at most 64 raw categories")
    stacked = cfg.multiple == "stack"
    widths /= max(1, len(groups)) if cfg.multiple == "dodge" else 1
    result = []
    anchors = {}
    running = defaultdict(list)
    for group_no, (key, rows) in enumerate(groups):
        seen = set()
        marks = []
        offset = (
            0.0
            if cfg.multiple != "dodge"
            else widths
            * (group_no - ((len(groups) - 1) / 2 if cfg.align == "center" else 0))
        )
        for i in rows:
            if i not in eligible:
                continue
            position = coord[i] + offset
            a = position - widths / 2 if cfg.align == "center" else position
            b = a + widths
            check_coordinate(a, pos_axis.scale)
            check_coordinate(b, pos_axis.scale)
            if not a < b:
                raise ValueError("native bar position width collapses")
            val = values[i]
            if not finite_number(val):
                raise ValueError("native bar height must be a finite signed number")
            val = float(val)
            base = check_coordinate(
                cfg.bottom if bottoms is None else bottoms[i], val_axis.scale
            )
            ident = coord[i] if not categorical else category_key(category[i])
            if stacked:
                if ident in seen:
                    raise ValueError(
                        "stack requires at most one row for each raw group/category"
                    )
                seen.add(ident)
                if anchors.setdefault(ident, base) != base:
                    raise ValueError(
                        "stacked groups must share the same explicit bottom per "
                        "category"
                    )
                side = (ident, val < 0)
                base = check_coordinate(
                    math.fsum((base, *running[side])), val_axis.scale
                )
                running[side].append(val)
            limit = check_coordinate(base + val, val_axis.scale)
            if val and limit == base:
                raise ValueError("native bar height collapses at endpoint precision")
            text = (
                labels[i]
                if labels is not None
                else _format_value(values[i], cfg.value_format)
                if cfg.value_format is not None
                else None
            )
            marks.append(
                (i, position, base, val, text, None if styles is None else styles[i])
            )
        result.append((key, marks))
    return cfg, widths, list(slots.values()), result


def pie(columns, layer, panel, ids):
    from ._native_geometry import _defined_column, _value_axes

    cfg = layer.pie_geometry
    if not isinstance(cfg, PieGeometrySpec):
        raise ValueError("pie geometry requires PieGeometrySpec")
    if (
        layer.axis != "y"
        or any(
            axis.temporal is not None or axis.scale != "linear"
            for axis in _value_axes(layer, panel)
        )
        or layer.group is not None
    ):
        raise ValueError(
            "typed pie requires primary linear Cartesian axes and ungrouped rows"
        )
    labels, raw = (_defined_column(columns, k) for k in (layer.x, layer.y))
    n = len(raw)
    if n > 64:
        raise ValueError("typed pie supports at most 64 supplied wedges")
    _body_styles(cfg.styles, n, "pie")
    if cfg.annotations is not None:
        _texts(cfg.annotations, n, "pie annotations")
    if any(
        type(getattr(cfg, k)) is not bool
        for k in ("counterclock", "normalize", "labels", "rotate_labels")
    ):
        raise ValueError("pie flags must be true or false")
    if (
        not all(
            finite_number(v)
            for v in (
                cfg.start_angle,
                cfg.radius,
                cfg.label_distance,
                cfg.value_distance,
            )
        )
        or not -360 <= cfg.start_angle <= 360
        or not 0 < cfg.radius <= 10
        or not 0 <= cfg.label_distance <= 2
        or not 0 <= cfg.value_distance <= 2
    ):
        raise ValueError(
            "pie angle/radius/label and value distances are outside finite bounds"
        )
    if (
        not isinstance(cfg.center, (list, tuple))
        or len(cfg.center) != 2
        or any(not finite_number(v) or abs(v) > 10 for v in cfg.center)
    ):
        raise ValueError("pie center must be two finite coordinates in [-10,10]")
    if cfg.width is not None and (
        not finite_number(cfg.width) or not 0 < cfg.width <= cfg.radius
    ):
        raise ValueError("pie wedge width must be positive and at most the radius")
    if cfg.explode is not None and (
        not isinstance(cfg.explode, (list, tuple))
        or len(cfg.explode) != n
        or any(not finite_number(v) or not 0 <= v <= 1 for v in cfg.explode)
    ):
        raise ValueError(
            "pie explode needs one finite fraction in [0,1] per source row"
        )
    if cfg.text_color is not None and not _color(cfg.text_color):
        raise ValueError("pie text_color requires hex/basic/cycle color")
    if cfg.text_size is not None and (
        not finite_number(cfg.text_size) or not 0 < cfg.text_size <= 100
    ):
        raise ValueError("pie text_size must be in (0,100] points")
    if (
        cfg.value not in (None, "raw", "percent")
        or cfg.value_format not in VALUE_FORMATS
    ):
        raise ValueError("pie value annotation needs raw/percent and a named format")
    marks = []
    for i in ids:
        value = raw[i]
        label = labels[i]
        if is_missing(value) or is_missing(label):
            continue
        category_key(label)
        if len(str(label)) > 256 or not finite_number(value) or not value >= 0:
            raise ValueError(
                "pie needs finite nonnegative supplied values and bounded labels"
            )
        marks.append((i, value, str(label)))
    if not marks:
        return cfg, [], 0.0
    total = math.fsum(v for _, v, _ in marks)
    if not total > 0 or (not cfg.normalize and total > 1):
        raise ValueError("pie needs positive mass and total <= 1 when normalize=False")
    fractions = [v / total if cfg.normalize else v for _, v, _ in marks]
    if any(
        v and not unpack(">f", pack(">f", f))[0]
        for (_, v, _), f in zip(marks, fractions, strict=True)
    ):
        raise ValueError("pie wedge fraction collapses at native precision")
    return cfg, marks, total


def draw_bars(ax, layer, prepared, colors):
    from ._render import _decorate

    cfg, width, slots, groups = prepared
    horizontal = layer.type == "barh"
    for key, marks in groups:
        ink = layer.color or next(colors)
        if not marks:
            continue
        _, pos, base, value, text, styles = zip(*marks, strict=True)
        label = _decorate(
            layer.label if key is None else str(key), layer.citation, layer.href
        )
        options = {
            "align": cfg.align,
            "color": ink,
            "label": label,
            "alpha": layer.alpha,
            "edgecolor": layer.edge_color,
            "linewidth": layer.line_width,
        }
        bars = (
            ax.barh(pos, value, height=width, left=base, **options)
            if horizontal
            else ax.bar(pos, value, width=width, bottom=base, **options)
        )
        for patch, style in zip(bars, styles, strict=True):
            apply_component_style(patch, style, body=True)
        if any(v is not None for v in text):
            ax.bar_label(
                bars,
                labels=["" if v is None else v for v in text],
                padding=cfg.label_padding,
            )
    if slots:
        positions, labels = zip(*slots, strict=True)
        if cfg.align == "edge":
            span = width * (len(groups) if cfg.multiple == "dodge" else 1)
            positions = [p + span / 2 for p in positions]
        (ax.set_yticks if horizontal else ax.set_xticks)(positions, labels=labels)


def draw_pie(ax, layer, prepared, colors):
    cfg, marks, total = prepared
    if not marks:
        return
    ids, values, labels = zip(*marks, strict=True)
    textprops = {}
    if cfg.text_color is not None:
        textprops["color"] = cfg.text_color
    if cfg.text_size is not None:
        textprops["fontsize"] = cfg.text_size
    vector = [v / total for v in values] if cfg.normalize else values
    pieces = ax.pie(
        vector,
        normalize=cfg.normalize,
        colors=[layer.color or next(colors) for _ in values],
        startangle=cfg.start_angle,
        counterclock=cfg.counterclock,
        radius=cfg.radius,
        center=tuple(cfg.center),
        explode=None if cfg.explode is None else [cfg.explode[i] for i in ids],
        labels=labels if cfg.labels else None,
        labeldistance=cfg.label_distance,
        rotatelabels=cfg.rotate_labels,
        textprops=textprops,
        pctdistance=cfg.value_distance,
        autopct=None if cfg.value is None else "%1.1f",
        wedgeprops={"width": cfg.width},
    )
    for index, (i, value, _) in enumerate(marks):
        wedge = pieces[0][index]
        wedge.set_alpha(layer.alpha)
        if cfg.styles is not None:
            apply_component_style(wedge, cfg.styles[i], body=True)
        if cfg.value is not None:
            text = pieces[2][index]
            result = (
                value
                if cfg.value == "raw"
                else 100 * (value / total if cfg.normalize else value)
            )
            text.set_text(
                _format_value(result, cfg.value_format)
                + ("%" if cfg.value == "percent" else "")
            )
        if cfg.annotations is not None and cfg.annotations[i] is not None:
            angle = math.radians((wedge.theta1 + wedge.theta2) / 2)
            direction = math.cos(angle), math.sin(angle)
            x, y = wedge.center
            xy = tuple(
                a + cfg.radius * d for a, d in zip((x, y), direction, strict=True)
            )
            point = tuple(15 * d for d in direction)
            ax.annotate(
                cfg.annotations[i],
                xy,
                xytext=point,
                xycoords="data",
                textcoords="offset points",
                va="center",
                ha="left" if direction[0] >= 0 else "right",
                arrowprops={"arrowstyle": "-", "color": cfg.text_color or "#30343b"},
                **textprops,
            )
    pad = cfg.radius * (max(1.12, cfg.label_distance + 0.18) if cfg.labels else 1.16)
    extent_x = [piece.center[0] for piece in pieces[0]]
    extent_y = [piece.center[1] for piece in pieces[0]]
    ax.set_xlim(min(extent_x) - pad, max(extent_x) + pad)
    ax.set_ylim(min(extent_y) - pad, max(extent_y) + pad)
