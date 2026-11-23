"""Pure, finite N09 validation and prospective native resource admission."""

import math
from dataclasses import dataclass, fields
from itertools import pairwise

from ._components import _color
from ._ecdf import finite_number
from ._semantics import category_key
from ._stat import is_missing
from .spec import VectorSpec

MAX_VECTORS = 10_000
ROW_TYPES = {"quiver", "barbs", "quiver3d"}
VECTOR_TYPES = ROW_TYPES | {"streamplot"}
_OPTIONS = {
    "quiver": {
        "mask_column",
        "mode",
        "pivot",
        "scale_units",
        "width_units",
        "headwidth",
        "headlength",
        "headaxislength",
    },
    "barbs": {
        "mask_column",
        "pivot",
        "length",
        "half",
        "full",
        "flag",
        "rounding",
        "flip_barb",
    },
    "quiver3d": {"mask_column", "pivot", "length", "normalize", "arrow_length_ratio"},
    "streamplot": {
        "x_coords",
        "y_coords",
        "u_matrix",
        "v_matrix",
        "mask",
        "start_points",
        "density",
        "minlength",
        "maxlength",
        "integration_direction",
        "arrowsize",
    },
}


def uses_vector(layer):
    return layer.type in VECTOR_TYPES and (
        layer.type != "quiver" or layer.vector is not None
    )


@dataclass(frozen=True)
class VectorPlan:
    # Row lists contain (original local row index, typed group slot, values).
    rows: list
    groups: list
    options: dict
    vertices: int
    labels: int
    work: int
    retained: int
    temporary: int


def _number(value, name, low, high, *, strict=False):
    if not finite_number(value) or not (
        low < value <= high if strict else low <= value <= high
    ):
        raise ValueError(
            f"vector {name} must be finite in {'(' if strict else '['}{low},{high}]"
        )
    return float(value)


def _choice(value, default, allowed, name):
    value = default if value is None else value
    if value not in allowed:
        raise ValueError(f"unsupported vector {name}")
    return value


def _value(cfg, name, default, low, high, *, strict=False):
    value = getattr(cfg, name)
    return _number(default if value is None else value, name, low, high, strict=strict)


def _column(columns, name, role):
    if (
        not isinstance(name, str)
        or name not in columns
        or not isinstance(columns[name], (list, tuple))
    ):
        raise ValueError(f"vector {role} needs an existing row column")
    return columns[name]


def vector_members(columns, layer, candidates=None, *, order_only=False):
    """Typed raw grouping; explicit empty levels are preserved without marks."""
    from ._facet import MAX_FACET_PANELS, _ordered

    cfg = layer.vector
    table_len = len(next(iter(columns.values()), ()))
    rows = range(table_len) if candidates is None else candidates
    if not isinstance(cfg, VectorSpec):
        raise ValueError("row vectors require VectorSpec")
    group = None if layer.group is None else _column(columns, layer.group, "group")
    mask = (
        None
        if cfg.mask_column is None
        else _column(columns, cfg.mask_column, "mask_column")
    )
    fixed = layer.hue_order is not None
    if fixed and group is None:
        raise ValueError("vector hue_order requires a group column")
    levels = _ordered((), layer.hue_order) if fixed else [None] if group is None else []
    positions: dict[tuple[str, object], int] = (
        {}
        if group is None
        else {category_key(value): i for i, value in enumerate(levels)}
    )
    selected = []
    for i in rows:
        if mask is not None:
            if i >= len(mask) or type(mask[i]) is not bool:
                raise ValueError("vector mask column must contain aligned booleans")
            if mask[i]:
                continue
        slot = 0
        if group is not None:
            if i >= len(group):
                raise ValueError("vector group column is not row-aligned")
            value = group[i]
            if fixed and is_missing(value):
                continue
            key = category_key(value)
            if key not in positions:
                if fixed:
                    continue
                if len(levels) == MAX_FACET_PANELS:
                    raise ValueError("vector group exceeds 64 typed levels")
                positions[key] = len(levels)
                levels.append(value)
            slot = positions[key]
        if not order_only:
            if len(selected) == MAX_VECTORS:
                raise ValueError("vector layer exceeds 10000 selected rows")
            selected.append((i, slot))
    if group is not None and not fixed:
        _ordered(levels)
    return levels, selected


def _row_plan(columns, panel, layer, cfg, row_ids):
    kind = layer.type
    spatial = kind == "quiver3d"
    needed = ("x", "y", "z", "u", "v", "w") if spatial else ("x", "y", "u", "v")
    arrays = [_column(columns, getattr(layer, role), role) for role in needed]
    if len({len(col) for col in arrays}) != 1:
        raise ValueError("vector coordinate and component columns must align")
    levels, members = vector_members(columns, layer, row_ids)
    if not members and not (
        panel.filters or panel.dropna or layer.hue_order or cfg.mask_column
    ):
        raise ValueError("vector layer needs observations")
    options = {}
    if kind == "quiver":
        mode = _choice(cfg.mode, "data", ("data", "display"), "mode")
        options["angles"] = "xy" if mode == "data" else "uv"
        options["scale_units"] = _choice(
            cfg.scale_units,
            "xy" if mode == "data" else "inches",
            ("xy",) if mode == "data" else ("inches", "width", "dots"),
            "scale_units",
        )
        options["units"] = _choice(
            cfg.width_units, "width", ("width", "inches", "dots"), "width_units"
        )
        options["scale"] = (
            1
            if layer.quiver_scale is None
            else _number(layer.quiver_scale, "scale", 1e-6, 1e6)
        )
        if mode == "data" and options["scale"] != 1:
            raise ValueError(
                "data quiver fixes scale=1; change supplied components to change "
                "displacement"
            )
        if layer.quiver_width is not None:
            options["width"] = _number(
                layer.quiver_width,
                "width",
                1e-6,
                1 if options["units"] == "width" else 100,
            )
        for name, default in (
            ("headwidth", 3),
            ("headlength", 5),
            ("headaxislength", 4.5),
        ):
            options[name] = _value(cfg, name, default, 1, 12)
        if options["headaxislength"] > options["headlength"]:
            raise ValueError("quiver headaxislength must not exceed headlength")
        options["pivot"] = _choice(
            cfg.pivot, "tail", ("tail", "middle", "tip"), "pivot"
        )
        options["minlength"] = 0
    elif kind == "barbs":
        options["length"] = _value(cfg, "length", 7, 1, 72)
        options["pivot"] = _choice(cfg.pivot, "tip", ("tip", "middle"), "pivot")
        increments = [
            _value(cfg, k, d, 1e-100, 1e100)
            for k, d in (("half", 5), ("full", 10), ("flag", 50))
        ]
        if not increments[0] < increments[1] < increments[2]:
            raise ValueError("barb increments must strictly increase: half, full, flag")
        options["barb_increments"] = dict(
            zip(("half", "full", "flag"), increments, strict=True)
        )
        for name, default in (("rounding", True), ("flip_barb", False)):
            value = getattr(cfg, name)
            if value is not None and type(value) is not bool:
                raise ValueError(f"barb {name} must be boolean")
            options[name] = default if value is None else value
    else:
        options["length"] = _value(cfg, "length", 1, 1e-100, 1e100)
        options["arrow_length_ratio"] = _value(
            cfg, "arrow_length_ratio", 0.3, 0, 1, strict=True
        )
        options["pivot"] = _choice(
            cfg.pivot, "tail", ("tail", "middle", "tip"), "pivot"
        )
        if cfg.normalize is not None and type(cfg.normalize) is not bool:
            raise ValueError("3D quiver normalize must be boolean")
        options["normalize"] = cfg.normalize is True
    rows, verts = [], 0
    dimensions = 3 if spatial else 2
    lower, upper = [math.inf] * dimensions, [-math.inf] * dimensions
    for i, slot in members:
        if any(i >= len(col) or not finite_number(col[i]) for col in arrays):
            raise ValueError(
                "selected vector coordinates and components must be finite "
                "numeric, not bool"
            )
        values = [float(col[i]) for col in arrays]
        tail, components = values[:dimensions], values[dimensions:]
        magnitude = math.hypot(*components)
        # Both 3D normalization and native Barb magnitude square components.
        raw_square = sum(v * v for v in components)
        if not math.isfinite(raw_square) or (magnitude and not raw_square):
            raise ValueError(
                "vector component magnitude is not representable by native arithmetic"
            )
        endpoints = [(value, value) for value in tail]
        if kind == "barbs":
            half = options["barb_increments"]["half"]
            if magnitude / half > 64:
                raise ValueError(
                    "barb magnitude exceeds 64 half-increments of native path work"
                )
            verts += 22 + 4 * (math.ceil(magnitude / half) + 1)
        else:
            if not magnitude:
                continue  # No fake dot or arrow for a zero displacement.
            factor = (
                (
                    options["length"] / magnitude
                    if options["normalize"]
                    else options["length"]
                )
                if spatial
                else 1
            )
            delta = [v * factor for v in components]
            if (
                kind == "quiver"
                and options["angles"] == "uv"
                and magnitude / options["scale"] > 10000
            ):
                raise ValueError(
                    "display vector length exceeds the native geometry envelope"
                )
            if kind == "quiver" and options["angles"] == "xy":
                # Native angle estimation transforms anchor + UV even for tip/middle.
                probe = [v + d for v, d in zip(tail, delta, strict=True)]
                if not all(map(math.isfinite, probe)) or probe == tail:
                    raise ValueError(
                        "quiver native angle coordinate collapses or overflows"
                    )
            if spatial or options["angles"] == "xy":
                pivot = {"tail": 0, "middle": 0.5, "tip": 1}[options["pivot"]]
                endpoints = [
                    (v - pivot * d, v + (1 - pivot) * d)
                    for v, d in zip(tail, delta, strict=True)
                ]
                if not all(
                    math.isfinite(a) and math.isfinite(b) for a, b in endpoints
                ) or all(a == b for a, b in endpoints):
                    raise ValueError(
                        "vector anchored displacement collapses or overflows"
                    )
                if spatial and any(
                    not math.isfinite(abs(v) + 2 * abs(d))
                    for v, d in zip(tail, delta, strict=True)
                ):
                    raise ValueError("3D arrowhead extent overflows")
            verts += 8 if not spatial else 6
        for axis, (start, stop) in enumerate(endpoints):
            lower[axis] = min(lower[axis], start, stop)
            upper[axis] = max(upper[axis], start, stop)
        rows.append((i, slot, values))
    if rows and any(
        not math.isfinite(b - a) for a, b in zip(lower, upper, strict=True)
    ):
        raise ValueError("vector coordinate extent is not representable")
    return VectorPlan(
        rows,
        levels,
        options,
        verts,
        len(levels) if layer.group is not None else 0,
        len(members) * 64 + verts * 4,
        16384 + len(rows) * 192 + verts * 64,
        verts * 64 + len(rows) * 192,
    )


def _axis(values, name):
    if (
        not isinstance(values, (tuple, list))
        or not 2 <= len(values) <= MAX_VECTORS
        or not all(map(finite_number, values))
    ):
        raise ValueError(f"streamplot needs a finite increasing {name} grid")
    first, last = float(values[0]), float(values[-1])
    span = last - first
    if not 1e-100 <= span <= 1e100:
        raise ValueError(
            f"streamplot {name} span is not in the finite native stepping envelope"
        )
    step = span / (len(values) - 1)
    if any(
        not (
            float(a) < float(b)
            and math.isclose(float(b) - float(a), step, rel_tol=1e-10)
        )
        for a, b in pairwise(values)
    ):
        raise ValueError(f"streamplot {name} coordinates must be uniformly increasing")
    if max(abs(first), abs(last)) / step > 1e12:
        raise ValueError(f"streamplot {name} local grid spacing is not well resolved")
    return span, step


def _stream_plan(budget, matrices, cfg):
    sx, dx = _axis(cfg.x_coords, "X")
    sy, dy = _axis(cfg.y_coords, "Y")
    nx, ny = len(cfg.x_coords), len(cfg.y_coords)
    cells = nx * ny
    if cells > MAX_VECTORS:
        raise ValueError("streamplot exceeds 10000 grid vectors")
    budget.admit(16 * cells, temporary=256 * cells)
    sources = []
    for name in (cfg.u_matrix, cfg.v_matrix):
        if not isinstance(name, str) or name not in matrices:
            raise ValueError("streamplot requires two named component matrices")
        block = matrices[name]
        if (
            not isinstance(block, (list, tuple))
            or len(block) != ny
            or any(
                not isinstance(row, (list, tuple)) or len(row) != nx for row in block
            )
        ):
            raise ValueError("streamplot matrices must match Y\u00d7X coordinate shape")
        sources.append(block)
    mask = cfg.mask
    if mask is not None and (
        not isinstance(mask, (list, tuple))
        or len(mask) != ny
        or any(
            not isinstance(row, (list, tuple))
            or len(row) != nx
            or any(type(flag) is not bool for flag in row)
            for row in mask
        )
    ):
        raise ValueError("streamplot needs a same-shaped boolean grid mask")
    density = _value(cfg, "density", 1, 0.25, 1)
    minlength = _value(cfg, "minlength", 0.1, 0, 4)
    maxlength = _value(cfg, "maxlength", 4, 0, 4, strict=True)
    direction = _choice(
        cfg.integration_direction,
        "both",
        ("both", "forward", "backward"),
        "integration_direction",
    )
    if minlength >= maxlength:
        raise ValueError("streamplot needs minlength < maxlength")
    options = {
        "density": density,
        "minlength": minlength,
        "maxlength": maxlength,
        "integration_direction": direction,
        "arrowsize": _value(cfg, "arrowsize", 1, 0.1, 4),
    }
    u, v = sources
    velocity = {}
    stationary = False
    minimum = math.inf
    max_delta = 0.0
    for i in range(ny):
        for j in range(nx):
            a, b = u[i][j], v[i][j]
            if (a is None) != (b is None) or any(
                z is not None and not finite_number(z) for z in (a, b)
            ):
                raise ValueError(
                    "streamplot components require finite numbers or paired null"
                )
            if a is None or (mask is not None and mask[i][j]):
                continue
            point = float(a) / sx, float(b) / sy
            speed = math.hypot(*point)
            if speed and not 1e-100 <= speed <= 1e100:
                raise ValueError(
                    "streamplot normalized velocity outside finite native "
                    "stepping range"
                )
            if speed == 0 and (a != 0 or b != 0):
                raise ValueError(
                    "streamplot normalized velocity loses a nonzero component"
                )
            stationary |= speed == 0
            if speed:
                minimum = min(minimum, speed)
            for near in ((i - 1, j), (i, j - 1)):
                if near in velocity:
                    x, y = velocity[near]
                    max_delta = max(max_delta, math.hypot(point[0] - x, point[1] - y))
            velocity[i, j] = point
    if not velocity:
        raise ValueError("streamplot needs at least one visible vector")
    if stationary and minimum != math.inf:
        raise ValueError(
            "streamplot mixed stationary nodes require an explicit mask for "
            "bounded native stepping"
        )
    starts = cfg.start_points
    occupancy = int(30 * density)
    attempts = occupancy**2
    if starts is not None:
        if not isinstance(starts, (tuple, list)) or not 1 <= len(starts) <= 64:
            raise ValueError("streamplot requires 1..64 explicit seed points")
        for p in starts:
            if (
                not isinstance(p, (list, tuple))
                or len(p) != 2
                or not all(map(finite_number, p))
                or not cfg.x_coords[0] <= p[0] <= cfg.x_coords[-1]
                or not cfg.y_coords[0] <= p[1] <= cfg.y_coords[-1]
            ):
                raise ValueError(
                    "streamplot seeds must be finite data-coordinate pairs "
                    "within the grid"
                )
            i = min(ny - 1, math.floor((p[1] - cfg.y_coords[0]) / dy))
            j = min(nx - 1, math.floor((p[0] - cfg.x_coords[0]) / dx))
            if any(
                (a, b) not in velocity
                for a in (i, min(i + 1, ny - 1))
                for b in (j, min(j + 1, nx - 1))
            ):
                raise ValueError("streamplot seed touches a masked interpolation cell")
        attempts = len(starts)
        options["start_points"] = starts
    # Native derivative is interp(u,v)/interp(node_speed) in normalized axes;
    # its norm <=1. The positive speed floor bounds the quotient Lipschitz
    # constant by 2*neighbor_delta*(nx+ny)/min_speed. Heun/Euler error <= L ds²/2;
    # reserve a stricter .001 error threshold and bound rejected .85 shrinks.
    max_step = min(1 / occupancy, 0.1)
    gradient = 0 if stationary else 2 * max_delta * (nx + ny) / minimum
    safe = max_step if gradient == 0 else min(max_step, math.sqrt(0.001 / gradient))
    retries = 2 + math.ceil(math.log(max_step / safe) / -math.log(0.85))
    steps = 4 if stationary else math.ceil(maxlength / safe) + 8
    points = attempts * steps * retries
    if points > 250_000:
        raise ValueError("streamplot exceeds 250000 prospective native stepping visits")
    # Four vertices per trajectory point covers both provider representations;
    # separately reserve native arrow objects and Python point workspaces.
    verts = 4 * points + 16 * attempts
    return VectorPlan(
        [],
        [],
        options,
        verts,
        0,
        1024 * points,
        64 * cells + 112 * points + 16384 * attempts,
        128 * cells + 192 * points,
    )


def admit_vector(budget, spec, layer, panel, columns, row_ids=None):
    cfg = layer.vector
    kind = layer.type
    if not isinstance(cfg, VectorSpec):
        raise ValueError(f"{kind} requires VectorSpec")
    for item in fields(cfg):
        if item.name not in _OPTIONS[kind] and getattr(cfg, item.name) is not None:
            raise ValueError(f"{item.name} is not supported for {kind}")
    target = panel.y2 if layer.axis == "y2" else panel.y
    if (
        panel.projection != ("3d" if kind == "quiver3d" else "2d")
        or layer.axis not in ("y", "y2")
        or (layer.axis == "y2" and kind not in ("quiver", "barbs"))
        or target is None
    ):
        raise ValueError(
            f"{kind} requires an applicable Cartesian primary or enabled twin axis"
        )
    axes = (
        (panel.x, target)
        if kind != "quiver3d" or panel.z is None
        else (panel.x, target, panel.z)
    )
    if any(a.scale != "linear" or a.temporal is not None for a in axes):
        raise ValueError(
            "typed vectors require linear numeric axes, not log/date transforms"
        )
    if (
        layer.c is not None
        or layer.colorbar
        or layer.clabel is not None
        or layer.cmap_kind != "sequential"
    ):
        raise ValueError(
            "typed vectors use literal or group colours, not scalar colour mappings"
        )
    if layer.color is not None and not _color(layer.color):
        raise ValueError("vector color must be a supported literal color")
    _number(layer.alpha, "alpha", 0, 1)
    if layer.line_width is not None:
        _number(layer.line_width, "line_width", 0, 1000, strict=kind == "streamplot")
    if kind == "streamplot" and (
        layer.group is not None
        or layer.hue_order is not None
        or panel.filters
        or panel.dropna
    ):
        raise ValueError(
            "streamplot grids do not accept row grouping or panel selectors"
        )
    plan = (
        _stream_plan(budget, spec.data.matrices, cfg)
        if kind == "streamplot"
        else _row_plan(columns, panel, layer, cfg, row_ids)
    )
    budget.admit_grid(plan)
    return plan
