"""Pure line declarations, selected topology and resource-shape contracts."""

from __future__ import annotations

from dataclasses import dataclass

from ._ecdf import finite_number
from ._semantics import categorical, category_key
from ._stat import (
    explicit_line_inference,
    is_missing,
    new_stat_request,
    stat_config,
    unit_key,
)
from ._transforms import COLUMN_ARRAYS
from .spec import LayerSpec, LineSpec, SemanticSpec, StatSpec

MAX_UNIT_ROWS = 10_000
MAX_LINE_TARGETS = 4096
MAX_LINE_WORK = 2_000_000_000
MAX_LINE_STATE_BYTES = 268_435_456
MAX_LINE_CHOICES = 1_000_000


def categorical_predictor(layer: LayerSpec) -> bool:
    return isinstance(layer.line, LineSpec) and layer.line.predictor == "categorical"


def unit_request(layer: LayerSpec) -> bool:
    return (
        layer.type == "lineplot"
        and isinstance(layer.line, LineSpec)
        and layer.line.resampling == "unit"
    )


def line_option_issues(layer, panel=None):
    issues = []
    if layer.type == "line":
        if layer.orient not in ("v", "h"):
            issues.append("raw line orient must be v or h")
        if layer.stat is not None:
            issues.append("raw line does not estimate supplied observations")
        if layer.semantics is None and layer.cmap_kind != "sequential":
            issues.append("raw line cmap_kind requires numeric semantic hue")
        if panel is not None and layer.orient == "h" and panel.projection != "2d":
            issues.append("horizontal raw line requires Cartesian2D")
    config = layer.line
    if config is None:
        return issues
    if not isinstance(config, LineSpec):
        return [*issues, "line must be a LineSpec or None"]
    if layer.type not in {"line", "lineplot"}:
        issues.append("LineSpec only applies to line/lineplot")
    if layer.stat is not None and not isinstance(layer.stat, StatSpec):
        return [*issues, "line statistics require a typed StatSpec"]
    for name, allowed in (
        ("predictor", ("native", "categorical")),
        ("resampling", (None, "cell", "unit")),
        ("calibration", (None, "percentile", "max_deviation")),
        ("family", (None, "curve", "layer")),
    ):
        value = getattr(config, name)
        if value not in allowed or (value is not None and not isinstance(value, str)):
            issues.append(f"line.{name} must be one of {allowed}")
    inference = any(
        getattr(config, name) is not None
        for name in ("resampling", "calibration", "family")
    )
    if layer.type == "line" and inference:
        issues.append("raw line does not accept inference controls")
    if inference and stat_config(layer).errorbar != "ci":
        issues.append("explicit line inference controls require errorbar='ci'")
    if config.resampling == "unit" and stat_config(layer).units is None:
        issues.append("complete-unit line inference requires stat.units")
    if config.calibration == "max_deviation" and config.resampling != "unit":
        issues.append("max_deviation requires explicit resampling='unit'")
    if config.family is not None and config.calibration != "max_deviation":
        issues.append("line.family requires calibration='max_deviation'")
    if panel is not None:
        if panel.projection != "2d":
            issues.append("declared line coordinates require Cartesian2D")
        predictor_axis = (
            (panel.y2 if layer.axis == "y2" else panel.y)
            if layer.orient == "h"
            else panel.x
        )
        if (
            predictor_axis is not None
            and categorical_predictor(layer)
            and (
                predictor_axis.temporal is not None or predictor_axis.scale != "linear"
            )
        ):
            issues.append("categorical line predictors require a linear nonclock axis")
    if categorical_predictor(layer) and layer.native_scale:
        issues.append("categorical line predictor conflicts with native_scale=True")
    return issues


def line_rows(columns, layer, *, topology=False, barriers=False, candidates=None):
    """Select source rows before response omission; never reinterpret weights."""
    config = stat_config(layer)
    roles = (
        [getattr(layer.semantics, role) for role in ("hue", "size", "style")]
        if isinstance(layer.semantics, SemanticSpec)
        else []
    )
    roles = [name for name in roles if name is not None]
    statistical = layer.type == "lineplot"
    required = [layer.x, layer.y]
    required += [name for name in (layer.group, *roles) if name is not None]
    if statistical:
        required += [
            name for name in (config.weights, config.units) if name is not None
        ]
    if not required or any(
        not isinstance(name, str)
        or name not in columns
        or not isinstance(columns[name], COLUMN_ARRAYS)
        for name in required
    ):
        return []
    count = len(columns[required[0]])
    if any(len(columns[name]) != count for name in required):
        return []
    typed_plain = (
        not statistical
        or new_stat_request(layer)
        or explicit_line_inference(layer)
        or categorical_predictor(layer)
    )
    selections = [
        (layer.x, layer.order, typed_plain),
        (layer.group, layer.hue_order, typed_plain),
    ]
    if isinstance(layer.semantics, SemanticSpec):
        selections += [
            (
                getattr(layer.semantics, role),
                getattr(layer.semantics, role + "_order"),
                True,
            )
            for role in ("hue", "size", "style")
        ]
    selected = []
    for name, order, typed in selections:
        if order is not None:
            if name is None or not isinstance(order, (list, tuple)):
                return []
            try:
                selected.append(
                    (
                        name,
                        {category_key(value) for value in order} if typed else order,
                        typed,
                    )
                )
            except ValueError:
                return []
    rows = []
    for row in range(count) if candidates is None else candidates:
        try:
            if any(
                not (
                    barriers
                    and not statistical
                    and is_missing(columns[name][row])
                    and (name in roles or name == layer.x)
                )
                and (
                    (
                        not categorical(columns[name][row])
                        or category_key(columns[name][row]) not in order
                    )
                    if typed
                    else columns[name][row] not in order
                )
                for name, order, typed in selected
            ):
                continue
        except (TypeError, ValueError):
            continue
        missing_role = any(is_missing(columns[name][row]) for name in roles)
        if layer.group is not None and is_missing(columns[layer.group][row]):
            continue
        if missing_role:
            if barriers and not statistical:
                rows.append(row)
            continue
        if statistical:
            if is_missing(columns[layer.x][row]):
                continue
            if config.weights is not None:
                weight = columns[config.weights][row]
                if is_missing(weight) or (finite_number(weight) and weight == 0):
                    continue
            if config.units is not None and is_missing(columns[config.units][row]):
                continue
        if not topology and any(
            is_missing(columns[name][row]) for name in (layer.x, layer.y)
        ):
            continue
        rows.append(row)
    return rows


@dataclass(frozen=True)
class LineStructure:
    categories: list
    groups: list
    grids: dict
    cells: dict
    rows: list[int]
    usable_rows: list[int]
    roles: list[dict]
    topology_cells: dict

    @property
    def slots(self):
        return sum(len(grid) for grid in self.grids.values())


def line_structure(columns, layer):
    """Reuse shared categorical grouping, with per-curve native topology."""
    from ._categorical import distribution_plan

    rows = line_rows(columns, layer, topology=True)
    if not categorical_predictor(layer):
        rows = [row for row in rows if finite_number(columns[layer.x][row])]
    categories, groups, cells = distribution_plan(
        columns, layer, rows=rows, max_cells=len(rows) + 1
    )
    if not groups and layer.group is None and layer.semantics is None:
        groups = [{"key": (None, ()), "hue": None, "roles": {}}]
    keys = [group["key"] for group in groups]
    by_key = {group["key"]: group["hue"] for group in groups}
    grids = {key: [] for key in keys}
    actual = {}
    topology_cells = {}
    usable = []
    for cell in sorted(cells, key=lambda cell: cell["rows"][0]):
        group = cell["group"]
        category = cell["category"]
        grids[group].append(category)
        topology_cells[(group, category_key(category))] = cell["rows"]
        selected = [
            row for row in cell["rows"] if not is_missing(columns[layer.y][row])
        ]
        if selected:
            actual[(group, category_key(category))] = selected
            usable.extend(selected)
    for key in keys:
        if categorical_predictor(layer):
            grid = categories
        elif layer.order is not None:
            grid = list(layer.order)
        else:
            grid = grids[key]
        grids[key] = list(grid)
    # Source rows, not grouped traversal order, define unit sampling order.
    usable.sort()
    return LineStructure(
        categories,
        [(key, by_key[key]) for key in keys],
        grids,
        actual,
        rows,
        usable,
        [group["roles"] for group in groups],
        topology_cells,
    )


def whole_unit_shape(structure, columns, layer):
    """Known complete-unit work; topology and estimable cells stay distinct."""
    config = stat_config(layer)
    units = {unit_key(columns[config.units][row], True) for row in structure.rows}
    n, u, k = len(structure.rows), len(units), len(structure.cells)
    if n > MAX_UNIT_ROWS:
        raise ValueError("complete-unit selected trajectory rows exceed10000")
    if structure.slots > MAX_LINE_TARGETS or k > MAX_LINE_TARGETS:
        raise ValueError("complete-unit structural/estimable targets exceed4096")
    work = config.n_boot * (u + n + k) if k else 0
    if work > MAX_LINE_WORK:
        raise ValueError("complete-unit logical work exceeds2000000000")
    return n, u, k, work


def line_data_issues(columns, layer, panel):
    """Declared geometry and whole-unit cohorts, with no numerical imports."""
    issues = line_option_issues(layer, panel)
    if issues or layer.line is None:
        return issues
    rows = line_rows(columns, layer, topology=True)
    if categorical_predictor(layer):
        from ._semantics import levels

        values = (
            layer.order
            if layer.order is not None
            else [columns[layer.x][row] for row in rows]
        )
        try:
            selected = levels(values)
            if len(selected) > 64:
                issues.append("categorical line predictor levels exceed64")
            if len({str(value) for value in selected}) != len(selected):
                issues.append("categorical predictor display labels are ambiguous")
        except ValueError as error:
            issues.append(str(error))
    elif any(
        not is_missing(columns[layer.x][row])
        and not finite_number(columns[layer.x][row])
        and (layer.type != "lineplot" or not is_missing(columns[layer.y][row]))
        for row in rows
    ):
        issues.append("native line predictors require finite numeric coordinates")
    if unit_request(layer) and not issues:
        try:
            structure = line_structure(columns, layer)
            whole_unit_shape(structure, columns, layer)
            config = stat_config(layer)
            for target_rows in structure.cells.values():
                contributors = {
                    unit_key(columns[config.units][row], True) for row in target_rows
                }
                if len(contributors) < 2:
                    issues.append(
                        "complete-unit targets require at least2 contributing units"
                    )
                    break
        except (KeyError, TypeError, ValueError) as error:
            issues.append(str(error))
    return issues


def known_line_work(columns, layer, *, structure=None):
    """Pure lower/known charge for actual stored explicit inference only."""
    if not explicit_line_inference(layer):
        return 0
    if structure is None:
        structure = line_structure(columns, layer)
    if unit_request(layer):
        return whole_unit_shape(structure, columns, layer)[3]
    config, total = stat_config(layer), 0
    for rows in structure.cells.values():
        if len(rows) < 2:
            continue
        if config.units is None:
            total += config.n_boot * (len(rows) + 1)
        else:
            units = {unit_key(columns[config.units][row], True) for row in rows}
            if len(units) >= 2:
                total += config.n_boot * (2 * len(units) + 1)
    return total
