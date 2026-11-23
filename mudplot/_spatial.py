"""Pure N10 ownership: raw coordinates, checked shapes and native reservations."""

from dataclasses import dataclass, fields
from itertools import pairwise
from math import isfinite

from ._components import _color
from ._ecdf import finite_number
from .spec import Camera3DSpec, SpatialSpec

SPATIAL_TYPES = {"bar3d", "contour3d", "contourf3d", "voxels"}
_GRID_TYPES = {"surface", "wireframe", "contour3d", "contourf3d"}
_OPTIONS = {
    "surface": {"x_coords", "y_coords"},
    "wireframe": {"x_coords", "y_coords"},
    "contour3d": {"x_coords", "y_coords", "direction", "offset"},
    "contourf3d": {"x_coords", "y_coords", "direction", "offset"},
    "bar3d": {"dx", "dy", "dz"},
    "voxels": {"x_coords", "y_coords", "z_coords", "occupancy"},
}
_MAX_ITEMS = 10_000
_COORD = 1e100  # differences, cross products and 3-D projection remain finite


@dataclass(frozen=True)
class SpatialReservation:
    vertices: int
    labels: int
    work: int
    retained: int
    temporary: int


def uses_spatial(layer):
    return layer.type in SPATIAL_TYPES or (
        layer.type in _GRID_TYPES and layer.spatial is not None
    )


def _coord(value):
    return finite_number(value) and abs(value) <= _COORD


def _array(value):
    return isinstance(value, (list, tuple))


def _axes(panel):
    if panel.projection != "3d" or any(
        axis is not None and (axis.temporal is not None or axis.scale != "linear")
        for axis in (panel.x, panel.y, panel.z)
    ):
        raise ValueError(
            "explicit 3D geometry and camera require linear numeric 3D axes"
        )


def validate_camera(panel):
    camera = panel.camera3d
    if not isinstance(camera, Camera3DSpec):
        raise ValueError("camera3d requires Camera3DSpec")
    _axes(panel)
    for name, limit in (("elevation", 180), ("azimuth", 360), ("roll", 360)):
        value = getattr(camera, name)
        if value is not None and (not finite_number(value) or abs(value) > limit):
            raise ValueError(f"camera3d {name} must be within ±{limit} degrees")
    if camera.vertical_axis not in (None, "x", "y", "z"):
        raise ValueError("camera3d vertical_axis must be x, y or z")
    if camera.projection not in (None, "persp", "ortho"):
        raise ValueError("camera3d projection must be persp or ortho")
    if camera.focal_length is not None and (
        camera.projection == "ortho"
        or not finite_number(camera.focal_length)
        or not 0.01 <= camera.focal_length <= 100
    ):
        raise ValueError(
            "camera3d focal_length must be in [0.01,100] and perspective only"
        )
    if camera.zoom is not None and (
        not finite_number(camera.zoom) or not 0.1 <= camera.zoom <= 4
    ):
        raise ValueError("camera3d zoom must be in [0.1,4]")
    if camera.box_aspect is not None and (
        not _array(camera.box_aspect)
        or len(camera.box_aspect) != 3
        or any(not finite_number(v) or not 0.01 <= v <= 100 for v in camera.box_aspect)
    ):
        raise ValueError(
            "camera3d box_aspect needs three positive ratios in [0.01,100]"
        )


def _coordinates(values, size, name):
    if not _array(values) or len(values) != size or not all(map(_coord, values)):
        raise ValueError(f"{name} requires {size} finite coordinates")
    if any(a >= b for a, b in pairwise(map(float, values))):
        raise ValueError(
            f"{name} must remain strictly increasing in native coordinates"
        )


def _reserve(budget, items, vertices, artists=1):
    budget.admit_grid(
        SpatialReservation(
            vertices,
            0,
            64 * items + 12 * vertices + 1024 * artists,
            80 * vertices + 8192 * artists,
            192 * items + 64 * vertices,
        )
    )


def _grid(budget, matrices, layer, cfg):
    if not isinstance(layer.matrix, str):
        raise ValueError("explicit 3D grid requires a named Z matrix")
    matrix = matrices.get(layer.matrix)
    if (
        not _array(matrix)
        or len(matrix) < 2
        or not _array(matrix[0])
        or len(matrix[0]) < 2
    ):
        raise ValueError("explicit 3D grid needs a named Z matrix at least 2\u00d72")
    ny, nx = len(matrix), len(matrix[0])
    if nx * ny > _MAX_ITEMS:
        raise ValueError("3D grid exceeds 10000 vertices")
    _coordinates(cfg.x_coords, nx, "x_coords")
    _coordinates(cfg.y_coords, ny, "y_coords")
    if layer.type in ("contour3d", "contourf3d"):
        levels = layer.levels
        if (
            not _array(levels)
            or not (2 if layer.type == "contourf3d" else 1) <= len(levels) <= 512
        ):
            raise ValueError(
                "3D contours need explicit levels (1..512 lines, 2..512 filled "
                "boundaries)"
            )
        _coordinates(levels, len(levels), "levels")
        if cfg.direction not in (None, "x", "y", "z"):
            raise ValueError("3D contour direction must be x, y or z")
        if cfg.offset is not None and not _coord(cfg.offset):
            raise ValueError("3D contour offset must be finite")
        # Up to two line segments per grid cell and multiple filled-ring edges;
        # count every level against every cell, not only surviving native paths.
        vertices = 16 * (nx - 1) * (ny - 1) * len(levels)
        artists = len(levels)
    elif layer.type == "wireframe":
        vertices, artists = 2 * nx * ny, 1
    else:
        vertices, artists = 5 * (nx - 1) * (ny - 1), 1
    _reserve(budget, nx * ny, vertices, artists)
    low, high = float("inf"), -float("inf")
    for row in matrix:
        if not _array(row) or len(row) != nx or not all(map(_coord, row)):
            raise ValueError(
                "3D Z matrix must be rectangular and finite; null is not supported"
            )
        low, high = min(low, float(min(row))), max(high, float(max(row)))
    direction = cfg.direction or "z"
    if layer.type in ("contour3d", "contourf3d") and direction != "z":
        # The physical footprint is (Y,Z) or (Z,X). Each strip must traverse
        # Z in one consistent direction to make that lateral chart injective.
        lines = matrix if direction == "x" else zip(*matrix, strict=True)
        last = matrix[0][-1] if direction == "x" else matrix[-1][0]
        rising = float(matrix[0][0]) < float(last)
        for line in lines:
            if any(a >= b if rising else a <= b for a, b in pairwise(map(float, line))):
                raise ValueError(
                    f"folded or degenerate lateral {direction} contour chart"
                )
        coords = cfg.x_coords if direction == "x" else cfg.y_coords
        low, high = float(coords[0]), float(coords[-1])
    if layer.type == "contour3d" and not any(
        low < float(v) < high for v in layer.levels
    ):
        raise ValueError(
            "3D line contours need a level strictly inside the "
            f"{direction.upper()} range"
        )
    if layer.type == "contourf3d" and (
        float(layer.levels[-1]) < low or float(layer.levels[0]) > high
    ):
        raise ValueError(
            f"3D filled levels do not intersect the {direction.upper()} range"
        )


def _bars(budget, columns, layer, cfg):
    names = (layer.x, layer.y, layer.z, cfg.dx, cfg.dy, cfg.dz)
    if any(not isinstance(name, str) or name not in columns for name in names):
        raise ValueError("bar3d requires three anchors and three named delta columns")
    cols = tuple(columns[name] for name in names)
    n = len(cols[0])
    if not 1 <= n <= _MAX_ITEMS or any(len(col) != n for col in cols):
        raise ValueError("bar3d needs 1..10000 original aligned rows")
    _reserve(budget, n, 30 * n)
    for x, y, z, dx, dy, dz in zip(*cols, strict=True):
        if not all(map(_coord, (x, y, z, dx, dy, dz))) or dx <= 0 or dy <= 0 or dz == 0:
            raise ValueError(
                "bar3d needs finite positive XY footprint and nonzero signed Z delta"
            )
        for base, delta in ((x, dx), (y, dy), (z, dz)):
            end = float(base) + float(delta)
            if end == float(base) or not _coord(end):
                raise ValueError(
                    "bar3d endpoint collapses or exceeds the coordinate envelope"
                )


def _voxels(budget, cfg):
    occupied = cfg.occupancy
    if (
        not _array(occupied)
        or not occupied
        or not _array(occupied[0])
        or not occupied[0]
        or not _array(occupied[0][0])
        or not occupied[0][0]
    ):
        raise ValueError(
            "voxels require a nonempty boolean occupancy grid in [z][y][x] order"
        )
    nz, ny, nx = len(occupied), len(occupied[0]), len(occupied[0][0])
    if nx * ny * nz > _MAX_ITEMS:
        raise ValueError("voxels exceed 10000 cells")
    axes = (cfg.x_coords, cfg.y_coords, cfg.z_coords)
    if any(axis is not None for axis in axes):
        steps = []
        for axis, size, name in zip(
            axes, (nx, ny, nz), ("x_coords", "y_coords", "z_coords"), strict=True
        ):
            _coordinates(axis, size + 1, name)
            min_step = float("inf")
            max_step = 0.0
            for a, b in pairwise(map(float, axis)):
                min_step, max_step = min(min_step, b - a), max(max_step, b - a)
            steps.append((min_step, max_step))
        # Native shading squares face normals, which are products of two
        # edge lengths. Reject loss of a normal before provider allocation.
        for i, j in ((0, 1), (0, 2), (1, 2)):
            lo = steps[i][0] * steps[j][0]
            hi = steps[i][1] * steps[j][1]
            if not lo * lo or not isfinite(hi * hi):
                raise ValueError(
                    "voxel edge spans cannot produce finite native face normals"
                )
    cells = nx * ny * nz
    nodes = (nx + 1) * (ny + 1) * (nz + 1)
    budget.admit(8 * cells, temporary=80 * nodes)
    active = 0
    for slab in occupied:
        if not _array(slab) or len(slab) != ny:
            raise ValueError("voxels occupancy must be rectangular [z][y][x]")
        for row in slab:
            if (
                not _array(row)
                or len(row) != nx
                or any(type(value) is not bool for value in row)
            ):
                raise ValueError(
                    "voxels occupancy must be rectangular and strictly boolean"
                )
            active += sum(row)
    # Native voxels can create one collection per occupied cell, at most six faces.
    _reserve(budget, cells + nodes, 30 * active, active)


def admit_spatial(budget, spec, panel, layer):
    cfg = layer.spatial
    if not isinstance(cfg, SpatialSpec):
        raise ValueError(f"{layer.type} requires SpatialSpec")
    _axes(panel)
    if panel.filters or panel.dropna or layer.axis != "y":
        raise ValueError(
            "explicit 3D geometry does not accept row selectors or a twin axis"
        )
    for item in fields(cfg):
        if (
            item.name not in _OPTIONS[layer.type]
            and getattr(cfg, item.name) is not None
        ):
            raise ValueError(f"{item.name} is not supported for {layer.type}")
    for color in (layer.color, layer.edge_color):
        if color is not None and not _color(color):
            raise ValueError("spatial geometry requires a supported literal colour")
    if layer.type in _GRID_TYPES:
        _grid(budget, spec.data.matrices, layer, cfg)
    elif layer.type == "bar3d":
        _bars(budget, spec.data.columns, layer, cfg)
    else:
        _voxels(budget, cfg)
