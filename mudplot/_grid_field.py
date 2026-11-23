"""N07 finite grid contracts; no provider dependencies."""

import math
import sys
from dataclasses import dataclass
from itertools import pairwise
from typing import SupportsFloat, cast

from ._ecdf import finite_number
from ._heatmap import linear_constant_bounds
from .spec import GridFieldSpec

MESH_TYPES = frozenset({"pcolor", "pcolormesh"})
CONTOUR_TYPES = frozenset({"contour", "contourf"})
NEW_GRID_TYPES = MESH_TYPES | {"imshow", "spy"}
GRID_TYPES = NEW_GRID_TYPES | CONTOUR_TYPES
MAX_GRID_CELLS = 10_000
MAX_GRID_LEVELS = 512
MAX_GRID_LABELS = 4096
LABEL_FORMATS = {"g": "%g", ".1f": "%.1f", ".2f": "%.2f", ".3f": "%.3f"}


def uses_grid(layer):
    return layer.type in NEW_GRID_TYPES or (
        layer.type in CONTOUR_TYPES and layer.grid is not None
    )


@dataclass(frozen=True)
class GridPlan:
    config: GridFieldSpec
    data: list | tuple
    rows: int
    cols: int
    depth: int
    limits: tuple[float, float] | None
    vertices: int
    labels: int
    work: int
    retained: int
    temporary: int


def _shape(data):
    if not isinstance(data, (list, tuple)) or not data or len(data) > MAX_GRID_CELLS:
        raise ValueError(
            "grid requires a nonempty rectangle with at most 10000 cells/pixels"
        )
    if not isinstance(data[0], (list, tuple)) or not data[0]:
        raise ValueError("grid requires a nonempty rectangle")
    m, n = len(data), len(data[0])
    if m * n > MAX_GRID_CELLS:
        raise ValueError("grid exceeds 10000 cells/pixels")
    if any(not isinstance(row, (list, tuple)) or len(row) != n for row in data):
        raise ValueError("grid requires rectangular rows")
    return m, n


def _vector(values, count, name, *, nearest=False):
    if (
        not isinstance(values, (list, tuple))
        or len(values) != count
        or not all(map(finite_number, values))
    ):
        raise ValueError(f"grid {name} requires {count} finite coordinates")
    coords = list(map(float, values))
    if any(not a < b or not math.isfinite(b - a) for a, b in pairwise(coords)):
        raise ValueError(f"grid {name} coordinates must strictly increase in binary64")
    if nearest:
        if count < 2:
            raise ValueError("nearest grid requires at least two centers on each axis")
        ends = [coords[0] - (coords[1] - coords[0]) / 2]
        ends.extend(a + (b - a) / 2 for a, b in pairwise(coords))
        ends.append(coords[-1] + (coords[-1] - coords[-2]) / 2)
        if any(
            not math.isfinite(a) or not a < b or not math.isfinite(b)
            for a, b in pairwise(ends)
        ):
            raise ValueError(f"nearest grid {name} edges overflow or collapse")
        if not math.isfinite(ends[-1] - ends[0]):
            raise ValueError(f"nearest grid {name} edge extent must be representable")
    if count > 1 and not math.isfinite(coords[-1] - coords[0]):
        raise ValueError(f"grid {name} extent must be representable")
    return coords


def contour_options(layer, cfg, cells):
    """Shared declared line/filled levels and prospective native paths."""
    kind = layer.type.removeprefix("tri")
    if cfg.extend is not None and (
        kind != "contourf" or cfg.extend not in ("neither", "min", "max", "both")
    ):
        raise ValueError("extend is a filled contour boundary option")
    has_labels = any(
        v is not None for v in (cfg.label_levels, cfg.label_format, cfg.label_inline)
    )
    if has_labels and (kind != "contour" or cfg.label_levels is None):
        raise ValueError("labels require an explicit subset of line contour levels")
    levels = layer.levels
    minimum = 1 if kind == "contour" else 2
    if (
        not isinstance(levels, (tuple, list))
        or not minimum <= len(levels) <= MAX_GRID_LEVELS
    ):
        raise ValueError(f"grid contour needs {minimum}..512 explicit levels")
    if kind == "contour" and layer.colorbar and len(levels) < 2:
        raise ValueError("a line contour colourbar needs at least two declared levels")
    native_levels = _vector(levels, len(levels), "levels")
    # The native filled extension intervals use +/-1e250 sentinels
    # inside the contour generator, not infinity.
    if (cfg.extend in ("min", "both") and native_levels[0] <= -1e250) or (
        cfg.extend in ("max", "both") and native_levels[-1] >= 1e250
    ):
        raise ValueError("filled contour extension would invert a native band")
    if (
        layer.colorbar
        and max(abs(native_levels[0]), abs(native_levels[-1])) > sys.float_info.max / 4
    ):
        raise ValueError("native contour colourbar boundaries are too large")
    bands = (
        len(levels)
        if kind == "contour"
        else len(levels)
        - 1
        + {"min": 1, "max": 1, "both": 2}.get(cfg.extend or "neither", 0)
    )
    labels = 0
    crossings = cells * bands
    # A quad yields at most two line segments per level. Filled bands may
    # use both boundary crossings, corners and close codes: reserve 32
    # vertices per quad-band, plus path/array overhead below.
    vertices = crossings * (8 if kind == "contour" else 32)
    if has_labels:
        chosen = cfg.label_levels
        if not isinstance(chosen, (tuple, list)) or not 1 <= len(chosen) <= len(levels):
            raise ValueError("label levels require a nonempty ordered level subset")
        if not set(_vector(chosen, len(chosen), "label levels")) <= set(native_levels):
            raise ValueError("label levels must be a subset of declared contour levels")
        if cfg.label_format is not None and cfg.label_format not in LABEL_FORMATS:
            raise ValueError("grid contour label format must be g, .1f, .2f or .3f")
        if cfg.label_inline is not None and type(cfg.label_inline) is not bool:
            raise ValueError("grid contour label_inline must be boolean")
        labels = 2 * cells * len(chosen)
        if labels > MAX_GRID_LABELS:
            raise ValueError("grid contour exceeds 4096 prospective labels")
    return crossings, vertices, labels


def scalar_bounds(low, high, colorbar):
    """Resolve a finite display domain before native artist allocation."""
    if not math.isfinite(low) or not math.isfinite(high - low):
        raise ValueError("scalar grid needs a finite visible colour domain")
    if low == high:
        low, high = linear_constant_bounds(low)
        if max(abs(low), abs(high)) < 1e21 * sys.float_info.min:
            low, high = -0.5, 0.5
    if not (math.isfinite(low) and math.isfinite(high - low) and low < high):
        raise ValueError("grid scalar display padding must be finite and increasing")
    if colorbar:
        # Native raw bars sum adjacent boundary values on both providers;
        # nonsingular can otherwise silently change the artist's norm.
        magnitude = max(abs(low), abs(high))
        if (
            magnitude > sys.float_info.max / 4
            or magnitude < 1e21 * sys.float_info.min
            or (high - low) / magnitude <= 1e-15
        ):
            raise ValueError(
                "raw grid colourbar domain is not representable without expansion"
            )
    return low, high


def prepare_grid(matrices, layer, panel):
    kind, cfg = layer.type, layer.grid
    if not isinstance(cfg, GridFieldSpec):
        raise ValueError(f"{kind} requires a typed GridFieldSpec")
    if (
        panel.projection != "2d"
        or layer.axis != "y"
        or any(
            a.scale != "linear" or a.temporal is not None for a in (panel.x, panel.y)
        )
    ):
        raise ValueError("grid requires primary linear numeric Cartesian coordinates")
    if panel.filters or panel.dropna:
        raise ValueError("grid matrices are independent of panel row selectors")
    if not finite_number(layer.alpha) or not 0 <= layer.alpha <= 1:
        raise ValueError("grid alpha must be finite in [0,1]")
    if type(layer.colorbar) is not bool or (
        layer.clabel is not None
        and (
            not layer.colorbar
            or not isinstance(layer.clabel, str)
            or len(layer.clabel) > 512
        )
    ):
        raise ValueError("grid clabel requires a colourbar and a bounded string")
    direct = cfg.pixels is not None
    if direct and (kind != "imshow" or layer.matrix is not None):
        raise ValueError("direct RGB(A) is imshow-only and excludes a matrix")
    if (direct or kind == "spy") and (
        layer.colorbar or layer.cmap_kind != "sequential"
    ):
        raise ValueError("direct RGB(A) and spy do not use scalar cmap or colourbar")
    if not direct and (
        not isinstance(layer.matrix, str) or layer.matrix not in matrices
    ):
        raise ValueError(
            "grid requires an existing named matrix or direct imshow pixels"
        )
    data = cfg.pixels if direct else matrices[layer.matrix]
    m, n = _shape(data)
    assert isinstance(data, (list, tuple))
    cells = m * n
    mask = cfg.mask
    if mask is not None and (
        not isinstance(mask, (list, tuple))
        or len(mask) != m
        or any(
            not isinstance(row, (list, tuple))
            or len(row) != n
            or any(type(flag) is not bool for flag in row)
            for row in mask
        )
    ):
        raise ValueError("grid mask must be a same-shaped boolean matrix")
    if kind in MESH_TYPES | CONTOUR_TYPES:
        if cfg.extent is not None or cfg.origin is not None:
            raise ValueError(
                "grid extent/origin are image or spy options, not coordinate vectors"
            )
        if kind in MESH_TYPES:
            if (cfg.position, cfg.shading) not in (
                ("edges", "flat"),
                ("centers", "nearest"),
            ):
                raise ValueError("mesh needs explicit edges/flat or centers/nearest")
        elif cfg.position != "centers" or cfg.shading is not None or min(m, n) < 2:
            raise ValueError(
                "contours require explicit center coordinates and "
                "at least 2\u00d72 samples"
            )
        edge = int(cfg.position == "edges")
        for vec, length, name in ((cfg.x, n + edge, "X"), (cfg.y, m + edge, "Y")):
            _vector(vec, length, name, nearest=cfg.shading == "nearest")
    elif any(v is not None for v in (cfg.x, cfg.y, cfg.position, cfg.shading)):
        raise ValueError("image and spy do not use mesh coordinate vectors")
    if cfg.origin is not None and cfg.origin not in ("upper", "lower"):
        raise ValueError("grid origin must be upper or lower")
    if cfg.extent is not None:
        if (
            kind != "imshow"
            or not isinstance(cfg.extent, (list, tuple))
            or len(cfg.extent) != 4
        ):
            raise ValueError("extent requires four imshow boundaries")
        _vector(cfg.extent[:2], 2, "extent X")
        _vector(cfg.extent[2:], 2, "extent Y")
    if cfg.threshold is not None and (
        kind != "spy" or not finite_number(cfg.threshold) or cfg.threshold < 0
    ):
        raise ValueError("spy threshold must be finite and nonnegative")
    if cfg.corner_mask is not None and (
        kind not in CONTOUR_TYPES or type(cfg.corner_mask) is not bool
    ):
        raise ValueError("corner_mask requires a contour and an actual boolean")
    crossings = vertices = labels = 0
    if kind in CONTOUR_TYPES:
        crossings, vertices, labels = contour_options(layer, cfg, (m - 1) * (n - 1))
    elif any(
        v is not None
        for v in (cfg.extend, cfg.label_levels, cfg.label_format, cfg.label_inline)
    ):
        raise ValueError("contour options require a contour layer")
    if kind in MESH_TYPES:
        if layer.line_width is not None and (
            not finite_number(layer.line_width) or not 0 <= layer.line_width <= 1000
        ):
            raise ValueError("mesh line width must be finite in [0,1000]")
        if layer.edge_color is not None:
            from ._components import _color

            if not _color(layer.edge_color):
                raise ValueError("mesh edge colour must be a supported literal color")
    if kind == "spy":
        if layer.marker is not None and layer.marker not in ("s", "o", ".", "x", "+"):
            raise ValueError("spy uses a finite named marker")
        if layer.marker_size is not None and (
            not finite_number(layer.marker_size) or not 0 <= layer.marker_size <= 1000
        ):
            raise ValueError("spy marker size must be finite in [0,1000]")
        if layer.color is not None:
            from ._components import _color

            if not _color(layer.color):
                raise ValueError("spy needs a supported literal color")

    depth = 0
    low, high = math.inf, -math.inf
    hidden = 0
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            masked = mask is not None and mask[i][j]
            if direct:
                if (
                    not isinstance(value, (list, tuple))
                    or len(value) not in (3, 4)
                    or (depth and len(value) != depth)
                    or any(not finite_number(v) or not 0 <= v <= 1 for v in value)
                ):
                    raise ValueError(
                        "direct pixels require uniform RGB/RGBA channels in [0,1]"
                    )
                depth = len(value)
            elif value is not None and not finite_number(value):
                raise ValueError("grid cells require finite scalars or actual null")
            elif value is not None and not masked:
                scalar = float(cast(SupportsFloat, value))
                low, high = min(low, scalar), max(high, scalar)
            hidden += masked or value is None
    if (
        hidden
        and kind == "pcolormesh"
        and layer.edge_color is not None
        and layer.edge_color != "none"
        and layer.line_width != 0
    ):
        raise ValueError("masked QuadMesh does not support visible cell edges")
    if (
        hidden
        and kind == "pcolor"
        and layer.scalar_display is not None
        and layer.scalar_display.bad not in (None, "none")
    ):
        raise ValueError(
            "pcolor omits masked cells; use pcolormesh for visible bad colour"
        )
    limits = (
        None
        if direct or kind == "spy" or layer.scalar_display is not None
        else scalar_bounds(low, high, layer.colorbar)
    )
    corners = (m + 1) * (n + 1) if kind in MESH_TYPES else 0
    if kind == "pcolor":
        vertices = 5 * (cells - hidden)
    elif kind == "pcolormesh":
        vertices = 5 * cells
    retained = (
        16384
        + cells * (40 if direct else 16)
        + 32 * corners
        + vertices * 24
        + labels * 8192
    )
    temporary = (
        cells * (80 if direct else 32) + 64 * corners + vertices * 32 + 64 * crossings
    )
    return GridPlan(
        cfg,
        data,
        m,
        n,
        depth,
        limits,
        vertices,
        labels,
        8 * cells + 32 * corners + 64 * crossings,
        retained,
        temporary,
    )
