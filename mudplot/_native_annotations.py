"""Typed literal native artists; original data and coordinate frames stay separate."""

from ._components import _color, apply_component_style
from ._ecdf import finite_number
from .spec import AnnotationSpec, LiteralTableSpec, PatchSpec, PathEffectSpec

FRAMES = ("data", "axes", "figure")
PATH_CODES = {"MOVETO": 1, "LINETO": 2, "CURVE3": 3, "CURVE4": 4, "CLOSEPOLY": 79}
ARROWS = {"line": "-", "open": "->", "filled": "-|>"}
EFFECT_MARKS = {
    "line",
    "scatter",
    "hlines",
    "vlines",
    "hspan",
    "vspan",
    "band",
    "patch",
    "text",
    "annotate",
}


def effects_issues(layer):
    effects = layer.path_effects
    if effects is None:
        return
    if (
        layer.type not in EFFECT_MARKS
        or layer.semantics is not None
        or layer.c is not None
        or layer.line is not None
    ):
        raise ValueError(
            "named path effects apply only to their declared native artists"
        )
    if not isinstance(effects, (tuple, list)) or not 1 <= len(effects) <= 2:
        raise ValueError("path_effects needs one or two named declarations")
    seen = set()
    for cfg in effects:
        if (
            not isinstance(cfg, PathEffectSpec)
            or cfg.kind not in ("stroke", "shadow")
            or cfg.kind in seen
        ):
            raise ValueError("each of stroke/shadow may be declared once")
        seen.add(cfg.kind)
        if cfg.color is not None and not _color(cfg.color):
            raise ValueError("path effect color must use hex/basic/cycle color")
        if cfg.width is not None and (
            cfg.kind != "stroke"
            or not finite_number(cfg.width)
            or not 0 < cfg.width <= 72
        ):
            raise ValueError(
                "stroke width requires (0,72] points and belongs only to stroke"
            )
        if cfg.offset is not None and (
            not isinstance(cfg.offset, (list, tuple))
            or len(cfg.offset) != 2
            or any(not finite_number(v) or abs(v) > 72 for v in cfg.offset)
        ):
            raise ValueError(
                "path effect offset requires two values in [-72,72] points"
            )
        if cfg.alpha is not None and (
            not finite_number(cfg.alpha) or not 0 <= cfg.alpha <= 1
        ):
            raise ValueError("path effect alpha must lie in [0,1]")


def _pair(value):
    return isinstance(value, (tuple, list)) and len(value) == 2


def point(raw, frame, axes, *, declared_clock=True):
    from ._native_geometry import check_coordinate, coordinates

    if frame not in FRAMES or not _pair(raw):
        raise ValueError("native coordinates need a named frame and an x/y pair")
    if frame != "data":
        if not all(finite_number(v) and 0 <= v <= 1 for v in raw):
            raise ValueError("axes and figure coordinates require fractions in [0,1]")
        return tuple(float(v) for v in raw)
    if not declared_clock:
        # Editor SetLayerAt already delivers native axis coordinates, including
        # epoch-day display units when a clock is declared.
        return tuple(
            check_coordinate(v, axis.scale) for v, axis in zip(raw, axes, strict=True)
        )
    result = tuple(coordinates([v], axis)[0] for v, axis in zip(raw, axes, strict=True))
    if None in result:
        raise ValueError("literal data points cannot be missing")
    return result


def _path_codes(authored, n):
    if not isinstance(authored, (list, tuple)) or len(authored) != n:
        raise ValueError("path needs exactly one explicit native code per vertex")
    codes = []
    pending = 0
    current = None
    drawn = False
    for code in authored:
        if not isinstance(code, str) or code not in PATH_CODES:
            raise ValueError("unknown native Path code")
        if pending:
            if code != current:
                raise ValueError(
                    "CURVE3/CURVE4 require two/three consecutive native vertices"
                )
            pending -= 1
        elif code == "MOVETO":
            if current is not None and not drawn:
                raise ValueError("every native subpath needs a drawing segment")
            current, drawn = code, False
        elif current is None:
            raise ValueError("native Path subpath must start with MOVETO")
        elif code == "CLOSEPOLY":
            if not drawn:
                raise ValueError("cannot close a subpath with no segment")
            current = None
        else:
            current, drawn = code, True
            pending = 1 if code == "CURVE3" else 2 if code == "CURVE4" else 0
        codes.append(PATH_CODES[code])
    if pending or (current is not None and not drawn):
        raise ValueError("native Path ended in an unfinished subpath or curve")
    return codes


def prepare_literal(layer, axes):
    if layer.type == "patch":
        cfg = layer.patch
        if (
            not isinstance(cfg, PatchSpec)
            or cfg.kind not in ("rectangle", "ellipse", "polygon", "path")
            or type(cfg.fill) is not bool
        ):
            raise ValueError("patch requires a typed rectangle/ellipse/polygon/path")
        if (
            not isinstance(cfg.vertices, (tuple, list))
            or not 2 <= len(cfg.vertices) <= 10000
        ):
            raise ValueError("patch needs 2..10000 points")
        if cfg.kind != "path" and cfg.codes is not None:
            raise ValueError("only an explicit native path accepts codes")
        if cfg.kind in ("rectangle", "ellipse") and len(cfg.vertices) != 2:
            raise ValueError("rectangle/ellipse need exactly two increasing corners")
        if cfg.kind == "polygon" and len(cfg.vertices) < 3:
            raise ValueError("polygon needs at least three points")
        codes = (
            _path_codes(cfg.codes, len(cfg.vertices)) if cfg.kind == "path" else None
        )
        vertices = [point(raw, cfg.coordinates, axes) for raw in cfg.vertices]
        if cfg.kind in ("rectangle", "ellipse") and not all(
            a < b and finite_number(b - a) for a, b in zip(*vertices, strict=True)
        ):
            raise ValueError(
                "rectangle/ellipse corners must define positive finite widths"
            )
        if (
            not cfg.fill
            and layer.native_style is not None
            and layer.native_style.color is not None
        ):
            raise ValueError(
                "unfilled patch style uses edge_color, not invisible face color"
            )
        return cfg, vertices, codes
    if layer.type == "table":
        cfg = layer.table
        if not isinstance(cfg, LiteralTableSpec) or layer.axis != "y":
            raise ValueError("table requires literal typed cells on primary axes")
        rows = cfg.cells
        if (
            not isinstance(rows, (list, tuple))
            or not 1 <= len(rows) <= 32
            or not isinstance(rows[0], (list, tuple))
            or not 1 <= len(rows[0]) <= 16
        ):
            raise ValueError("literal table needs 1..32 rows by 1..16 columns")
        cols = len(rows[0])
        for row in rows:
            _text_cells(row, cols)
        for headers, n in ((cfg.row_labels, len(rows)), (cfg.column_labels, cols)):
            if headers is not None:
                _text_cells(headers, n)
        bb = cfg.bbox
        if (
            not isinstance(bb, (list, tuple))
            or len(bb) != 4
            or not all(finite_number(v) for v in bb)
            or not (
                0 <= bb[0] < 1
                and 0 <= bb[1] < 1
                and 0 < bb[2] <= 1 - bb[0]
                and 0 < bb[3] <= 1 - bb[1]
            )
        ):
            raise ValueError("literal table bbox must fit its axes-fraction rectangle")
        if cfg.alignment not in ("left", "center", "right") or cfg.edges not in (
            "closed",
            "open",
            "horizontal",
            "vertical",
        ):
            raise ValueError("table requires a named text alignment and edge theme")
        _font_size(cfg.font_size)
        for attr in ("cell_color", "header_color", "text_color"):
            ink = getattr(cfg, attr)
            if ink is not None and not _color(ink):
                raise ValueError(f"table {attr} must use hex/basic/cycle color")
        if (
            cfg.header_color is not None
            and cfg.row_labels is None
            and cfg.column_labels is None
        ):
            raise ValueError("table header_color requires visible row/column headers")
        return cfg
    cfg = layer.annotation if layer.annotation is not None else AnnotationSpec()
    if (
        not isinstance(cfg, AnnotationSpec)
        or cfg.align not in ("left", "center", "right")
        or cfg.vertical_align not in ("baseline", "bottom", "center", "top")
    ):
        raise ValueError(
            "annotation requires typed finite text coordinates and alignment"
        )
    _font_size(cfg.font_size)
    if not finite_number(cfg.rotation) or not -360 <= cfg.rotation <= 360:
        raise ValueError("annotation rotation requires degrees in [-360,360]")
    if not isinstance(layer.text, str) or not layer.text or len(layer.text) > 1024:
        raise ValueError(
            "annotation requires nonempty literal text at most 1024 characters"
        )
    if cfg.arrow not in (None, "none", *ARROWS):
        raise ValueError("annotation requires a named arrow style")
    if (
        cfg.to_coordinates is not None or cfg.arrow not in (None, "none")
    ) and layer.to is None:
        raise ValueError("an explicit arrow target frame/style requires to")
    if layer.type == "text" and layer.to is not None:
        raise ValueError("plain text has no arrow target")
    at = point(layer.at, cfg.at_coordinates, axes, declared_clock=False)
    target_frame = cfg.to_coordinates or cfg.at_coordinates
    to = (
        None
        if layer.to is None
        else point(layer.to, target_frame, axes, declared_clock=False)
    )
    return cfg, at, to, target_frame


def _font_size(value):
    if value is not None and (not finite_number(value) or not 0 < value <= 100):
        raise ValueError("font size must be in (0,100] points")


def _text_cells(row, n):
    if (
        not isinstance(row, (list, tuple))
        or len(row) != n
        or any(not isinstance(t, str) or len(t) > 256 for t in row)
    ):
        raise ValueError(
            "table cells and headers must be rectangular literal text (<=256 "
            "characters)"
        )


def literal_size(layer):
    if layer.type == "patch":
        return (
            len(layer.patch.vertices)
            if isinstance(layer.patch, PatchSpec)
            and isinstance(layer.patch.vertices, (list, tuple))
            else 0
        )
    if layer.type == "table":
        if (
            not isinstance(layer.table, LiteralTableSpec)
            or not isinstance(layer.table.cells, (list, tuple))
            or not layer.table.cells
            or not isinstance(layer.table.cells[0], (list, tuple))
        ):
            return 0
        return (len(layer.table.cells) + int(layer.table.column_labels is not None)) * (
            len(layer.table.cells[0]) + int(layer.table.row_labels is not None)
        )
    return 1


def apply_path_effects(artist, effects, *, body=False):
    if effects is None:
        return
    from matplotlib import patheffects
    from matplotlib.colors import to_rgba

    native = []
    for cfg in effects:
        if cfg.kind == "stroke":
            kw = {"foreground": cfg.color or "white", "linewidth": cfg.width or 2.0}
            if cfg.alpha is not None:
                kw["alpha"] = cfg.alpha
            effect = patheffects.Stroke(offset=cfg.offset or (0, 0), **kw)
        elif body:
            effect = patheffects.SimplePatchShadow(
                offset=cfg.offset or (2, -2),
                shadow_rgbFace=to_rgba(cfg.color or "black")[:3],
                alpha=0.3 if cfg.alpha is None else cfg.alpha,
            )
        else:
            effect = patheffects.SimpleLineShadow(
                offset=cfg.offset or (2, -2),
                shadow_color=cfg.color or "black",
                alpha=0.3 if cfg.alpha is None else cfg.alpha,
            )
        native.append(effect)
    artist.set_path_effects([*native, patheffects.Normal()])


def transform(ax, name):
    return (
        ax.transData
        if name == "data"
        else ax.transAxes
        if name == "axes"
        else ax.figure.transFigure
    )


def draw_literal(ax, layer, prepared, colors, index):
    from matplotlib.patches import Ellipse, PathPatch, Polygon, Rectangle
    from matplotlib.path import Path

    from ._render import _decorate, _set_url

    if layer.type == "patch":
        cfg, vertices, codes = prepared
        ink = layer.color or next(colors)
        kw = {
            "fill": cfg.fill,
            "facecolor": ink if cfg.fill else "none",
            "edgecolor": layer.edge_color or ("none" if cfg.fill else ink),
            "linewidth": layer.line_width,
            "alpha": layer.alpha,
            "transform": transform(ax, cfg.coordinates),
            "label": _decorate(layer.label, layer.citation, layer.href),
        }
        if cfg.kind in ("rectangle", "ellipse"):
            (x, y), (u, v) = vertices
            artist = (
                Rectangle((x, y), u - x, v - y, **kw)
                if cfg.kind == "rectangle"
                else Ellipse((x + (u - x) / 2, y + (v - y) / 2), u - x, v - y, **kw)
            )
        elif cfg.kind == "polygon":
            artist = Polygon(vertices, closed=True, **kw)
        else:
            artist = PathPatch(Path(vertices, codes), **kw)
        apply_component_style(artist, layer.native_style, body=True)
        apply_path_effects(artist, layer.path_effects, body=cfg.fill)
        _set_url(artist, layer.href)
        if cfg.coordinates == "figure":
            artist.set_clip_on(False)
            ax.figure.add_artist(artist)
        else:
            ax.add_patch(artist)
        return
    if layer.type == "table":
        cfg = prepared
        cells = cfg.cells
        if cfg.row_labels is not None:
            cells = [
                [label, *row] for label, row in zip(cfg.row_labels, cells, strict=True)
            ]
        head = cfg.column_labels
        if head is not None and cfg.row_labels is not None:
            head = ["", *head]
        table = ax.table(
            cellText=cells,
            colLabels=head,
            bbox=cfg.bbox,
            cellLoc=cfg.alignment,
            edges=cfg.edges,
        )
        if cfg.font_size is not None:
            table.auto_set_font_size(False)
            table.set_fontsize(cfg.font_size)
        for (i, j), cell in table.get_celld().items():
            header = (head is not None and i == 0) or (
                cfg.row_labels is not None and j == 0
            )
            color = (
                cfg.header_color
                if header and cfg.header_color is not None
                else cfg.cell_color
            )
            if color is not None:
                cell.set_facecolor(color)
            if cfg.text_color is not None:
                cell.get_text().set_color(cfg.text_color)
        return
    cfg, at, to, target_frame = prepared
    color = layer.color or next(colors)
    values = {
        "color": color,
        "alpha": layer.alpha,
        "horizontalalignment": cfg.align,
        "verticalalignment": cfg.vertical_align,
        "rotation": cfg.rotation,
        "fontsize": cfg.font_size,
    }
    textframe = transform(ax, cfg.at_coordinates)
    if layer.type == "text":
        artist = ax.text(*at, layer.text, transform=textframe, **values)
    else:
        arrow = cfg.arrow or ("open" if to is not None else "none")
        artist = ax.annotate(
            layer.text,
            xy=to or at,
            xytext=at,
            xycoords=transform(ax, target_frame),
            textcoords=textframe,
            annotation_clip=False,
            arrowprops=None
            if arrow == "none"
            else {"arrowstyle": ARROWS[arrow], "color": color, "alpha": layer.alpha},
            **values,
        )
    _set_url(artist, layer.href)
    artist.set_in_layout(False)
    apply_path_effects(artist, layer.path_effects, body=True)
    artist._mudplot_layer_index = index
    artist._mudplot_annotation_frame = cfg.at_coordinates
