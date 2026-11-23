"""N08 explicit connectivity admission. No NumPy or Matplotlib on the core path."""

import heapq
import math
from dataclasses import dataclass

from ._components import _color
from ._ecdf import finite_number
from ._grid_field import contour_options, scalar_bounds
from .spec import TriangulationSpec

TRI_TYPES = frozenset({"triplot", "tripcolor", "tricontour", "tricontourf", "trisurf"})
MAX_TRI_ROWS = 10_000
MAX_TRI_PAIR_VISITS = 50_000


@dataclass(frozen=True)
class TrianglePlan:
    x: list
    y: list
    triangles: list
    mask: list | tuple | None
    values: list | None
    limits: tuple | None
    vertices: int
    labels: int
    work: int
    retained: int
    temporary: int


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _edges(face):
    a, b, c = face
    return ((a, b), (b, c), (c, a))


def _on(a, b, p):
    return all(min(x, y) <= z <= max(x, y) for x, y, z in zip(a, b, p, strict=True))


def _check_pair(points, face, other):
    for a, b in _edges(face):
        for c, d in _edges(other):
            if (a == c and b == d) or (a == d and b == c):
                continue  # Opposite incidence already checked at construction.
            A, B, C, D = (points[i] for i in (a, b, c, d))
            ab_c, ab_d = _orient(A, B, C), _orient(A, B, D)
            cd_a, cd_b = _orient(C, D, A), _orient(C, D, B)
            if ab_c * ab_d < 0 and cd_a * cd_b < 0:
                raise ValueError("triangles cross in the XY plane")
            for p, u, v, side in (
                (c, a, b, ab_c),
                (d, a, b, ab_d),
                (a, c, d, cd_a),
                (b, c, d, cd_b),
            ):
                if (
                    side == 0
                    and p not in (u, v)
                    and _on(points[u], points[v], points[p])
                ):
                    raise ValueError("triangles meet at a nonconforming edge junction")
    for a, b in ((face, other), (other, face)):
        for p in a:
            if p not in b and all(
                _orient(points[u], points[v], points[p]) > 0 for u, v in _edges(b)
            ):
                raise ValueError("triangles overlap in the XY plane")


def _raw_column(columns, name, count=None):
    if not isinstance(name, str) or name not in columns:
        raise ValueError("triangulation needs an existing vertex column")
    values = columns[name]
    if (
        not isinstance(values, (list, tuple))
        or not 3 <= len(values) <= MAX_TRI_ROWS
        or (count is not None and len(values) != count)
    ):
        raise ValueError("triangulation requires 3..10000 aligned vertices")
    return values


def _columns(columns, name, count=None):
    return _numeric(_raw_column(columns, name, count))


def _numeric(values):
    if not all(map(finite_number, values)):
        raise ValueError("triangulation vertex values must be finite numeric, not bool")
    converted = list(map(float, values))
    if not math.isfinite(max(converted) - min(converted)):
        raise ValueError("triangulation vertex span must be representable")
    return converted


def _geometry(columns, layer, cfg, budget):
    raw_x = _raw_column(columns, layer.x)
    raw_y = _raw_column(columns, layer.y, len(raw_x))
    triangles = cfg.triangles
    if (
        not isinstance(triangles, (list, tuple))
        or not 1 <= len(triangles) <= MAX_TRI_ROWS
    ):
        raise ValueError("triangulation requires 1..10000 explicit triangles")
    n, t = len(raw_x), len(triangles)
    budget.admit(64 * n + 128 * t, temporary=2048 * n + 512 * t)
    mask = cfg.mask
    if mask is not None and (
        not isinstance(mask, (list, tuple))
        or len(mask) != len(triangles)
        or any(type(v) is not bool for v in mask)
        or all(mask)
    ):
        raise ValueError(
            "triangle mask must be one boolean per triangle and leave a visible face"
        )
    x, y = _numeric(raw_x), _numeric(raw_y)
    if len(set(zip(x, y, strict=True))) != len(x):
        raise ValueError("triangulation XY vertices must be distinct in binary64")
    # A common power-of-two scale makes each predicate exact on the same
    # binary64 coordinates given to the provider; at most ~2100 bits per XY.
    ratios = [a.as_integer_ratio() for a in (*x, *y)]
    scale = max(d for _, d in ratios)
    units = [n * (scale // d) for n, d in ratios]
    points = list(zip(units[: len(x)], units[len(x) :], strict=True))
    faces, seen, incidence, boxes = [], set(), {}, []
    for row in triangles:
        if (
            not isinstance(row, (list, tuple))
            or len(row) != 3
            or any(type(v) is not int or not 0 <= v < len(x) for v in row)
            or len(set(row)) != 3
        ):
            raise ValueError(
                "triangle connectivity requires three distinct zero-based "
                "integer vertex IDs (not bool)"
            )
        a, b, c = row
        key = tuple(sorted(row))
        if key in seen:
            raise ValueError("duplicate triangle face")
        seen.add(key)
        det = _orient(points[a], points[b], points[c])
        # Require the same sign for the provider's ordinary binary64 area
        # formula too, so exact nonzero triangles cannot collapse there.
        native = (x[b] - x[a]) * (y[c] - y[a]) - (y[b] - y[a]) * (x[c] - x[a])
        if (
            not det
            or not math.isfinite(native)
            or not native
            or (native > 0) != (det > 0)
        ):
            raise ValueError("triangle has zero or unrepresentable signed area")
        face = (a, b, c) if det > 0 else (a, c, b)
        for u, v in _edges(face):
            edge = min(u, v), max(u, v)
            previous = incidence.get(edge)
            if previous is None:
                incidence[edge] = u < v
            elif previous == (u < v) or previous == 2:
                raise ValueError(
                    "triangle edge has more than two or same-sided incidences"
                )
            else:
                incidence[edge] = 2
        xx, yy = [x[i] for i in face], [y[i] for i in face]
        boxes.append((min(xx), max(xx), min(yy), max(yy), len(faces)))
        faces.append(face)

    # First pass counts and bounds actual active-box visits (including
    # y-disjoint boxes). Only after admission do we run exact pair predicates.
    ordered = sorted(boxes)
    ends, visits = [], 0
    for left, right, _, _, i in ordered:
        while ends and ends[0][0] < left:
            heapq.heappop(ends)
        visits += len(ends)
        if visits > MAX_TRI_PAIR_VISITS:
            raise ValueError("triangulation exceeds 50000 active-box pair visits")
        heapq.heappush(ends, (right, i))
    budget.admit(2048 * visits)
    ends.clear()
    active = {}
    for left, right, lo, hi, i in ordered:
        while ends and ends[0][0] < left:
            active.pop(heapq.heappop(ends)[1])
        for j, (a, b) in active.items():
            if lo <= b and a <= hi:
                _check_pair(points, faces[i], faces[j])
        active[i] = lo, hi
        heapq.heappush(ends, (right, i))
    return x, y, faces, mask


def admit_triangles(budget, columns, layer, panel):
    cfg = layer.triangulation
    kind = layer.type
    surface = kind == "trisurf"
    if not isinstance(cfg, TriangulationSpec):
        raise ValueError("explicit triangle marks require TriangulationSpec")
    axes = (
        (panel.x, panel.y, panel.z)
        if surface and panel.z is not None
        else (panel.x, panel.y)
    )
    if (
        panel.projection != ("3d" if surface else "2d")
        or layer.axis != "y"
        or any(a is None or a.scale != "linear" or a.temporal is not None for a in axes)
    ):
        raise ValueError(
            "triangle marks require linear numeric Cartesian axes (3D only for trisurf)"
        )
    if panel.filters or panel.dropna:
        raise ValueError(
            "triangle indices address original rows; panel selectors are unsupported"
        )
    if not finite_number(layer.alpha) or not 0 <= layer.alpha <= 1:
        raise ValueError("triangle alpha must be finite in [0,1]")
    if type(layer.colorbar) is not bool or (
        layer.clabel is not None
        and (
            not layer.colorbar
            or not isinstance(layer.clabel, str)
            or len(layer.clabel) > 512
        )
    ):
        raise ValueError("triangle clabel requires a colourbar and a bounded string")
    for name in ("color", "edge_color"):
        value = getattr(layer, name)
        if value is not None and not _color(value):
            raise ValueError("triangle style needs a supported literal colour")
    if layer.line_style is not None and layer.line_style not in ("-", "--", "-.", ":"):
        raise ValueError("triangle linestyle must be a supported named dash")
    x, y, faces, mask = _geometry(columns, layer, cfg, budget)
    active = [i for i in range(len(faces)) if mask is None or not mask[i]]
    values = None
    limits = None
    crossings = labels = 0
    verts = 6 * len(active)
    if kind == "tripcolor":
        if cfg.scalar_role == "face":
            values = cfg.face_values
            if (
                layer.c is not None
                or not isinstance(values, (list, tuple))
                or len(values) != len(faces)
                or not all(map(finite_number, values))
            ):
                raise ValueError(
                    "face scalar requires one finite inline face value per "
                    "triangle and no vertex c"
                )
            calibrated = [float(values[i]) for i in active]
        elif cfg.scalar_role == "vertex" and cfg.face_values is None:
            values = _columns(columns, layer.c, len(x))
            calibrated = [_mean(values, faces[i]) for i in active]
        else:
            raise ValueError("tripcolor requires explicit vertex or face scalar role")
    elif kind in ("tricontour", "tricontourf"):
        if cfg.scalar_role != "vertex" or cfg.face_values is not None:
            raise ValueError(
                "triangular contours require the explicit vertex scalar role"
            )
        values = _columns(columns, layer.c, len(x))
        calibrated = [values[j] for i in active for j in faces[i]]
        crossings, verts, labels = contour_options(layer, cfg, len(active))
    else:
        if (
            cfg.scalar_role is not None
            or cfg.face_values is not None
            or layer.c is not None
        ):
            raise ValueError(
                "geometry-only triangle marks do not take independent scalars"
            )
        if surface:
            values = _columns(columns, layer.z, len(x))
            calibrated = [_mean(values, faces[i]) for i in active]
    if kind not in ("tricontour", "tricontourf") and any(
        v is not None
        for v in (cfg.extend, cfg.label_levels, cfg.label_format, cfg.label_inline)
    ):
        raise ValueError("contour options require triangular contours")
    if kind != "triplot":
        limits = scalar_bounds(min(calibrated), max(calibrated), layer.colorbar)
    n, t = len(x), len(faces)
    plan = TrianglePlan(
        x,
        y,
        faces,
        mask,
        values,
        limits,
        verts,
        labels,
        64 * crossings,
        16384 + 32 * n + 64 * t + 24 * verts + 8192 * labels,
        64 * n + 256 * t + 32 * verts + 64 * crossings,
    )
    budget.admit_grid(plan)
    return plan


def _mean(values, face):
    a, b, c = (values[i] for i in face)
    mean = ((a + b) + c) / 3
    if not math.isfinite(mean):
        raise ValueError("native triangle vertex mean overflows")
    return mean
