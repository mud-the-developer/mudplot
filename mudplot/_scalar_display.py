"""P01 raw scalar calibration. No optional provider or derived data here."""

import math
from dataclasses import dataclass
from itertools import pairwise

from ._components import _color
from ._ecdf import finite_number
from ._facet import panel_rows
from ._heatmap import colorbar_options_issues, linear_constant_bounds
from ._semantics import valid_scale_id
from ._stat import is_missing
from .spec import GridFieldSpec, HeatmapSpec, ScalarDisplaySpec

SCALAR_LAYER_TYPES = {"scatter", "heatmap", "imshow", "pcolor", "pcolormesh"}
COLORMAPS = (
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "cividis",
    "coolwarm",
    "RdBu",
    "Greys",
    "mudplot-sequential",
    "mudplot-diverging",
)
NORMS = ("linear", "log", "centered", "two_slope", "boundary")
EXTENSIONS = ("neither", "min", "max", "both")
MAX_SCALAR_ITEMS = 10_000


@dataclass(slots=True)
class ScalarRange:
    config: ScalarDisplaySpec
    bounds: tuple[float, float]


def _colors(colors, minimum):
    return (
        isinstance(colors, (list, tuple))
        and minimum <= len(colors) <= 64
        and all(
            _color(color) and color != "none" and not color.startswith("C")
            for color in colors
        )
    )


def palette_issues(palette):
    if palette.colors is None:
        return []
    if (
        palette.kind != "qualitative"
        or palette.preset is not None
        or not _colors(palette.colors, 1)
    ):
        return ["custom categorical palette needs 1..64 literal colours and no preset"]
    return []


def _number(value):
    return None if value is None else float(value)


def _options(layer, panel):
    cfg = layer.scalar_display
    if not isinstance(cfg, ScalarDisplaySpec) or layer.type not in SCALAR_LAYER_TYPES:
        raise ValueError(
            "scalar_display requires scatter-c, heatmap or an explicit scalar "
            "image/mesh"
        )
    if (
        layer.semantics is not None
        or layer.group is not None
        or layer.color is not None
        or layer.cmap_kind != "sequential"
    ):
        raise ValueError(
            "scalar_display cannot combine with mapped roles, groups, literal "
            "color or cmap_kind"
        )
    if layer.transforms is not None:
        raise ValueError(
            "scalar_display uses untransformed native coordinate selection"
        )
    if panel.projection != "2d" or layer.axis not in ("y", "y2"):
        raise ValueError("scalar_display requires Cartesian 2-D axes")
    target = panel.y2 if layer.axis == "y2" else panel.y
    if target is None or any(
        a.scale not in ("linear", "log")
        or (layer.type != "scatter" and a.temporal is not None)
        for a in (panel.x, target)
    ):
        raise ValueError(
            "scalar display requires linear/log axes; only scatter accepts clocks"
        )
    if layer.type == "scatter" and layer.c is None:
        raise ValueError("scalar_display scatter requires a c column")
    if layer.type != "scatter" and (
        layer.axis != "y" or panel.x.scale != "linear" or target.scale != "linear"
    ):
        raise ValueError("scalar matrices require primary linear axes")
    if layer.type in {"imshow", "pcolor", "pcolormesh"} and (
        not isinstance(layer.grid, GridFieldSpec) or layer.grid.pixels is not None
    ):
        raise ValueError("scalar_display cannot calibrate direct RGB(A) pixels")
    if layer.type == "heatmap" and layer.heatmap is not None:
        existing = layer.heatmap
        if (
            not isinstance(existing, HeatmapSpec)
            or existing.norm != "linear"
            or existing.robust
            or any(
                getattr(existing, name) is not None
                for name in (
                    "vmin",
                    "vmax",
                    "center",
                    "boundaries",
                    "gamma",
                    "linthresh",
                    "colorbar_options",
                )
            )
        ):
            raise ValueError(
                "scalar_display cannot compete with HeatmapSpec calibration, "
                "robust or colourbar options"
            )
    if type(layer.colorbar) is not bool or (
        layer.clabel is not None
        and (
            not layer.colorbar
            or not isinstance(layer.clabel, str)
            or len(layer.clabel) > 512
        )
    ):
        raise ValueError("scalar_display clabel requires colorbar and a bounded string")
    if cfg.cmap is not None and cfg.cmap not in COLORMAPS:
        raise ValueError("scalar_display cmap must be a registered name")
    if cfg.colors is not None and (cfg.cmap is not None or not _colors(cfg.colors, 2)):
        raise ValueError(
            "scalar_display requires a named map XOR 2..64 literal ramp colours"
        )
    for name in ("under", "over", "bad"):
        value = getattr(cfg, name)
        if value is not None and (not _color(value) or value.startswith("C")):
            raise ValueError(f"scalar_display {name} requires a literal colour")
    if cfg.scale_id is not None and not valid_scale_id(cfg.scale_id):
        raise ValueError(
            "scalar_display scale_id must be a nonblank name of at most 64 characters"
        )
    if cfg.norm not in NORMS:
        raise ValueError(
            "scalar_display norm must be linear/log/centered/two_slope/boundary"
        )
    for name in ("vmin", "vmax", "center"):
        value = getattr(cfg, name)
        if value is not None and not finite_number(value):
            raise ValueError(f"scalar_display {name} must be finite")
    fixed = cfg.vmin is not None and cfg.vmax is not None
    if (
        cfg.vmin is not None
        and cfg.vmax is not None
        and float(cfg.vmin) >= float(cfg.vmax)
    ):
        raise ValueError(
            "scalar_display fixed limits must remain strictly increasing in binary64"
        )
    if cfg.norm == "boundary":
        edges = cfg.boundaries
        if (
            not isinstance(edges, (list, tuple))
            or not 2 <= len(edges) <= 65
            or not all(map(finite_number, edges))
            or any(a >= b for a, b in pairwise(map(float, edges)))
            or any(v is not None for v in (cfg.vmin, cfg.vmax, cfg.center))
        ):
            raise ValueError(
                "boundary norm needs 2..65 native increasing edges and no center/range"
            )
    elif cfg.boundaries is not None:
        raise ValueError("boundaries require boundary norm")
    if cfg.norm in ("centered", "two_slope"):
        if (
            cfg.center is None
            or (cfg.norm == "two_slope" and not fixed)
            or ((cfg.vmin is None) != (cfg.vmax is None))
        ):
            raise ValueError(
                "centered needs a center and paired fixed bounds if any; "
                "two_slope needs all three"
            )
    elif cfg.center is not None:
        raise ValueError("center requires centered or two_slope norm")
    if cfg.norm == "log" and any(
        v is not None and v <= 0 for v in (cfg.vmin, cfg.vmax)
    ):
        raise ValueError("log scalar bounds must be positive")
    if cfg.colorbar_options is not None:
        if not layer.colorbar:
            raise ValueError("scalar display colourbar options require colorbar=True")
        problems = colorbar_options_issues(
            cfg.colorbar_options,
            norm=cfg.norm,
            boundaries=cfg.boundaries,
            vmin=cfg.vmin,
            vmax=cfg.vmax,
            scalar=True,
        )
        if problems:
            raise ValueError("; ".join(problems))


def _scatter_values(columns, panel, layer, budget):
    names = layer.x, layer.y, layer.c
    if any(not isinstance(name, str) or name not in columns for name in names):
        raise ValueError("scalar scatter needs existing numeric x, y, c columns")
    x, y, values = (columns[name] for name in names)
    if len(x) != len(y) or len(x) != len(values):
        raise ValueError("scalar scatter roles must align to original rows")
    ids = panel_rows(columns, panel) if panel.filters or panel.dropna else range(len(x))
    if len(ids) > MAX_SCALAR_ITEMS:
        raise ValueError("scalar display exceeds 10000 selected rows")
    budget.admit(12 * len(ids), retained=16384 + 64 * len(ids), temporary=96 * len(ids))
    target = panel.y2 if layer.axis == "y2" else panel.y
    if panel.x.temporal is not None or target.temporal is not None:
        from ._temporal_data import prepare_temporal_layer

        selected = {name: [columns[name][i] for i in ids] for name in set(names)}
        coordinates, native, _ = prepare_temporal_layer(selected, layer, panel)
        x, y, values = coordinates[native.x], coordinates[native.y], selected[layer.c]
        ids = range(len(values))
    for row in ids:
        a, b = x[row], y[row]
        if is_missing(a) or is_missing(b):
            continue
        if not finite_number(a) or not finite_number(b):
            raise ValueError("scalar scatter positions must be finite numeric or null")
        if (panel.x.scale == "log" and a <= 0) or (target.scale == "log" and b <= 0):
            raise ValueError("scalar scatter log positions must be positive")
        if not is_missing(values[row]):
            yield values[row]


def _matrix_values(matrices, layer, budget):
    if not isinstance(layer.matrix, str):
        raise ValueError("scalar matrix requires an existing named matrix")
    matrix = matrices.get(layer.matrix)
    if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("scalar matrix requires a nonempty rectangular field")
    cells = len(matrix) * len(matrix[0])
    if layer.type != "heatmap" and cells > MAX_SCALAR_ITEMS:
        raise ValueError("scalar display exceeds 10000 native grid cells")
    if layer.type == "heatmap":
        # Borrow the matrix for one scalar scan; reserve actual image
        # conversion/mask/native workspace in the shared matrix ledger.
        budget.admit(8 * cells, retained=16384 + 16 * cells, temporary=48 * cells)
    else:
        budget.admit(3 * cells)
    holder = layer.heatmap if layer.type == "heatmap" else layer.grid
    mask = None if holder is None else holder.mask
    if mask is not None and (
        not isinstance(mask, (list, tuple))
        or len(matrix) != len(mask)
        or any(
            not isinstance(flags, (list, tuple))
            or len(row) != len(flags)
            or any(type(flag) is not bool for flag in flags)
            for row, flags in zip(matrix, mask, strict=True)
        )
    ):
        raise ValueError(
            "scalar matrix mask must be boolean and align to existing geometry"
        )
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value is not None and not finite_number(value):
                raise ValueError("scalar matrix cells must be finite numbers or null")
            if value is not None and (mask is None or not mask[i][j]):
                yield value


def _bounds(cfg, raw):
    if cfg.norm == "boundary":
        return float(cfg.boundaries[0]), float(cfg.boundaries[-1])
    low = raw[0] if cfg.vmin is None else float(cfg.vmin)
    high = raw[1] if cfg.vmax is None else float(cfg.vmax)
    if cfg.norm == "centered":
        center = float(cfg.center)
        if cfg.vmin is None:
            if raw[0] == math.inf:
                raise ValueError(
                    "centered scalar calibration needs finite visible data or "
                    "fixed bounds"
                )
            span = max(abs(low - center), abs(high - center)) or (
                abs(center) * 0.05 or 0.5
            )
            low, high = center - span, center + span
        elif not math.isclose(center - low, high - center, rel_tol=1e-15, abs_tol=0):
            raise ValueError(
                "fixed centered scalar bounds must be symmetric about the center"
            )
    if low == high and math.isfinite(low):
        a, b = (
            (low / 10, min(high * 10, float.fromhex("0x1.fffffffffffffp1023")))
            if cfg.norm == "log"
            else linear_constant_bounds(low)
        )
        if cfg.vmin is None and (cfg.norm != "log" or a > 0):
            low = a
        if cfg.vmax is None:
            high = b
    if not (math.isfinite(low) and math.isfinite(high) and low < high):
        raise ValueError(
            "scalar calibration needs finite visible data or increasing fixed bounds"
        )
    if cfg.norm == "log":
        if low <= 0 or math.log10(low) >= math.log10(high):
            raise ValueError("native log scalar range must stay positive and distinct")
    elif not math.isfinite(high - low):
        raise ValueError("scalar colour range span is not representable")
    if cfg.center is not None and not low < float(cfg.center) < high:
        raise ValueError("scalar bounds must strictly straddle the center")
    return low, high


def _key(cfg):
    # Guide placement/options are local; identity applies only to calibration.
    return (
        cfg.norm,
        cfg.cmap or ("viridis" if cfg.colors is None else None),
        tuple(cfg.colors or ()),
        cfg.under,
        cfg.over,
        cfg.bad,
        _number(cfg.vmin),
        _number(cfg.vmax),
        _number(cfg.center),
        tuple(map(float, cfg.boundaries or ())),
    )


def scalar_plans(spec, budget):
    scopes, entries = {}, []
    for pi, panel in enumerate(spec.panels):
        for li, layer in enumerate(panel.layers):
            cfg = layer.scalar_display
            if cfg is None:
                continue
            where = f"panel {pi} layer {li} ({layer.type}) scalar display"
            try:
                _options(layer, panel)
                base = scopes.setdefault(
                    cfg.scale_id if cfg.scale_id is not None else id(layer),
                    [cfg, math.inf, -math.inf],
                )
                if _key(cfg) != _key(base[0]):
                    raise ValueError(
                        f"named range {cfg.scale_id!r} requires identical "
                        "calibration and colormap"
                    )
                values = (
                    _scatter_values(spec.data.columns, panel, layer, budget)
                    if layer.type == "scatter"
                    else _matrix_values(spec.data.matrices, layer, budget)
                )
                for value in values:
                    value = float(value)
                    if cfg.norm == "log" and value <= 0:
                        raise ValueError(
                            "log scalar display requires positive selected values"
                        )
                    base[1], base[2] = min(base[1], value), max(base[2], value)
                entries.append((id(layer), cfg, base, where))
            except (ValueError, KeyError, TypeError, IndexError) as error:
                raise ValueError(f"{where}: {error}") from error
    result, pooled = {}, {}
    for key, cfg, base, where in entries:
        try:
            if id(base) not in pooled:
                pooled[id(base)] = ScalarRange(base[0], _bounds(base[0], base[1:]))
            plan = pooled[id(base)]
            bar = cfg.colorbar_options
            if bar is not None and bar.ticks is not None:
                ticks = list(map(float, bar.ticks))
                low, high = plan.bounds
                if (
                    ticks[0] < low
                    or ticks[-1] > high
                    or any(a >= b for a, b in pairwise(ticks))
                ):
                    raise ValueError(
                        "colourbar ticks must be distinct inside the resolved "
                        "raw domain"
                    )
                if bar.tick_format is not None and len(
                    {format(v, bar.tick_format) for v in ticks}
                ) != len(ticks):
                    raise ValueError(
                        "colourbar tick formatting merges distinct raw values"
                    )
            result[key] = plan
        except ValueError as error:
            raise ValueError(f"{where}: {error}") from error
    return result
