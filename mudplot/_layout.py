"""Pure, bounded panel placement and identity operations; no renderer imports."""

from __future__ import annotations

import copy
import math
import re
from collections import defaultdict

from .spec import (
    MAX_FIGURE_PANELS,
    MAX_LAYOUT_CELLS,
    MAX_LAYOUT_DEPTH,
    MAX_LAYOUT_GRIDS,
    GridCellSpec,
    InsetSpec,
    LayoutGridSpec,
    PanelLayoutSpec,
    PanelPlacementSpec,
    PanelSpec,
)

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")


def valid_id(value):
    return isinstance(value, str) and _NAME.fullmatch(value) is not None


def finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def next_id(used, prefix):
    index = 1
    while f"{prefix}{index}" in used:
        index += 1
    return f"{prefix}{index}"


def allocated_ids(spec):
    """Suggest deterministic IDs without opting a caller into stored identity."""
    used = {p.panel_id for p in spec.panels if p.panel_id is not None}
    result = []
    for panel in spec.panels:
        name = panel.panel_id
        if name is None:
            name = next_id(used, "panel")
            used.add(name)
        result.append(name)
    return result


def panel_ids(spec):
    for panel, name in zip(spec.panels, allocated_ids(spec), strict=True):
        panel.panel_id = name


def clear_geometry(spec):
    spec.panel_layout = None
    for panel in spec.panels:
        panel.placement = None


def implicit_grid(spec):
    """Resolve only admitted legacy dimensions before sharing or expansion."""
    layout = spec.layout
    if layout is None:
        return 1, max(len(spec.panels), 1)
    if (
        not isinstance(layout, (list, tuple))
        or len(layout) != 2
        or any(type(value) is not int or value <= 0 for value in layout)
    ):
        raise ValueError("layout must contain two positive integers")
    rows, columns = layout
    if rows > MAX_FIGURE_PANELS or columns > MAX_FIGURE_PANELS:
        raise ValueError(f"layout supports at most {MAX_FIGURE_PANELS} cells")
    cells = rows * columns
    if cells > MAX_FIGURE_PANELS:
        raise ValueError(f"layout supports at most {MAX_FIGURE_PANELS} cells")
    if cells < len(spec.panels):
        raise ValueError(
            f"layout {rows}x{columns} has {cells} slots but there are "
            f"{len(spec.panels)} panels"
        )
    return rows, columns


def explicit(spec):
    """Materialize the legacy grid without changing its cells or panel content."""
    if spec.panel_layout is not None:
        return
    from .validate import assert_valid

    assert_valid(spec)
    panel_ids(spec)
    rows, cols = implicit_grid(spec)
    root = LayoutGridSpec(
        "grid1",
        rows,
        cols,
        width_ratios=spec.width_ratios,
        height_ratios=spec.height_ratios,
    )
    for index, panel in enumerate(spec.panels):
        row, col = divmod(index, cols)
        panel.placement = PanelPlacementSpec(cell=GridCellSpec(root.grid_id, row, col))
    spec.panel_layout = PanelLayoutSpec([root])
    spec.layout = spec.width_ratios = spec.height_ratios = None


def find_panel(spec, name):
    for panel in spec.panels:
        if panel.panel_id == name:
            return panel
    raise ValueError(f"unknown panel ID {name!r}")


def rename(spec, name, replacement):
    if not valid_id(replacement):
        raise ValueError("panel ID must match [A-Za-z][A-Za-z0-9_.-]{0,63}")
    panel = find_panel(spec, name)
    if name != replacement and any(p.panel_id == replacement for p in spec.panels):
        raise ValueError(f"duplicate panel ID {replacement!r}")
    panel.panel_id = replacement
    for child in spec.panels:
        place = child.placement
        if place is not None and place.inset is not None and place.inset.parent == name:
            place.inset.parent = replacement


def replace_layout(spec, layout, placements, ids=None):
    """Complete payload keys and references always name final IDs."""
    if ids is not None:
        if not isinstance(ids, list) or len(ids) != len(spec.panels):
            raise ValueError("panel_ids must name every panel in current index order")
        if any(not valid_id(name) for name in ids) or len(set(ids)) != len(ids):
            raise ValueError("panel_ids must contain unique valid panel IDs")
        for panel, name in zip(spec.panels, ids, strict=True):
            panel.panel_id = name
    else:
        panel_ids(spec)
    if not isinstance(placements, dict) or any(
        not valid_id(name) for name in placements
    ):
        raise ValueError("placements must use valid final panel IDs")
    existing = {p.panel_id for p in spec.panels}
    if not existing <= set(placements):
        raise ValueError("placements must name every existing final panel ID")
    if len(placements) > MAX_FIGURE_PANELS:
        raise ValueError(f"figure supports at most {MAX_FIGURE_PANELS} panels")
    for name in sorted(set(placements) - existing):
        spec.panels.append(PanelSpec(panel_id=name))
    for panel in spec.panels:
        panel.placement = copy.deepcopy(placements[panel.panel_id])
    spec.panel_layout = copy.deepcopy(layout)
    spec.layout = spec.width_ratios = spec.height_ratios = None


def mosaic(spec, rows, width_ratios=None, height_ratios=None):
    if (
        not isinstance(rows, list)
        or not rows
        or not isinstance(rows[0], list)
        or not rows[0]
        or any(not isinstance(row, list) or len(row) != len(rows[0]) for row in rows)
    ):
        raise ValueError("mosaic must be a nonempty rectangular list of rows")
    if len(rows) * len(rows[0]) > MAX_LAYOUT_CELLS:
        raise ValueError(f"layout supports at most {MAX_LAYOUT_CELLS} aggregate cells")
    cells = {}
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            if name is None:
                continue
            if not valid_id(name):
                raise ValueError("mosaic entries must be valid panel IDs or null")
            cells.setdefault(name, []).append((r, c))
    existing = {p.panel_id: p for p in spec.panels if p.panel_id is not None}
    if not set(existing) <= set(cells):
        raise ValueError(
            "mosaic must retain every existing panel ID; rename/remove explicitly"
        )
    anonymous = [p for p in spec.panels if p.panel_id is None]
    if spec.panel_layout is not None and anonymous:
        raise ValueError("explicit layout panels must have IDs")
    new_count = sum(name not in existing for name in cells)
    if len(cells) > MAX_FIGURE_PANELS or new_count < len(anonymous):
        raise ValueError("mosaic must cover every panel within the 256-panel limit")
    for name, points in cells.items():
        r0, c0 = min(r for r, _ in points), min(c for _, c in points)
        r1, c1 = max(r for r, _ in points) + 1, max(c for _, c in points) + 1
        if len(points) != (r1 - r0) * (c1 - c0):
            raise ValueError(f"mosaic panel {name!r} must occupy a rectangle")
        if name in existing:
            panel = existing[name]
        elif anonymous:
            panel = anonymous.pop(0)
            panel.panel_id = name
        else:
            panel = PanelSpec(panel_id=name)
            spec.panels.append(panel)
        panel.placement = PanelPlacementSpec(
            cell=GridCellSpec("grid1", r0, c0, r1 - r0, c1 - c0)
        )
    spec.panel_layout = PanelLayoutSpec(
        [
            LayoutGridSpec(
                "grid1",
                len(rows),
                len(rows[0]),
                width_ratios=copy.deepcopy(width_ratios),
                height_ratios=copy.deepcopy(height_ratios),
            )
        ]
    )
    spec.layout = spec.width_ratios = spec.height_ratios = None


def nest(
    spec,
    rows,
    cols,
    row=0,
    col=0,
    row_span=1,
    col_span=1,
    grid_id=None,
    width_ratios=None,
    height_ratios=None,
):
    explicit(spec)
    used = {grid.grid_id for grid in spec.panel_layout.grids}
    name = next_id(used, "grid") if grid_id is None else grid_id
    if not valid_id(name) or name in used:
        raise ValueError("new grid ID must be valid and not already used")
    root = next(grid for grid in spec.panel_layout.grids if grid.cell is None)
    root.cell = GridCellSpec(name, row, col, row_span, col_span)
    spec.panel_layout.grids.append(
        LayoutGridSpec(
            name,
            rows,
            cols,
            width_ratios=copy.deepcopy(width_ratios),
            height_ratios=copy.deepcopy(height_ratios),
        )
    )


def add_inset(spec, parent, bounds, name=None):
    if len(spec.panels) >= MAX_FIGURE_PANELS:
        raise ValueError(f"figure supports at most {MAX_FIGURE_PANELS} panels")
    explicit(spec)
    find_panel(spec, parent)
    used = {p.panel_id for p in spec.panels}
    name = next_id(used, "panel") if name is None else name
    if not valid_id(name) or name in used:
        raise ValueError("new panel ID must be valid and not already used")
    spec.panels.append(
        PanelSpec(
            panel_id=name,
            placement=PanelPlacementSpec(
                inset=InsetSpec(parent, copy.deepcopy(bounds))
            ),
        )
    )


def remove(spec, name):
    explicit(spec)
    panel = find_panel(spec, name)
    if len(spec.panels) == 1:
        raise ValueError("cannot remove the final panel")
    if any(
        p.placement.inset is not None and p.placement.inset.parent == name
        for p in spec.panels
    ):
        raise ValueError("cannot remove a panel referenced by an inset")
    spec.panels.remove(panel)


def reorder(spec, names):
    explicit(spec)
    if (
        not isinstance(names, list)
        or len(names) != len(spec.panels)
        or len(set(names)) != len(names)
        or set(names) != {p.panel_id for p in spec.panels}
    ):
        raise ValueError("panel_ids must be an exact permutation of existing IDs")
    lookup = {p.panel_id: p for p in spec.panels}
    spec.panels = [lookup[name] for name in names]


def _cell_rectangle(cell, grids):
    if not isinstance(cell, GridCellSpec) or not valid_id(cell.grid):
        raise ValueError("cell must reference a valid grid ID")
    if cell.grid not in grids:
        raise ValueError(f"missing grid {cell.grid!r}")
    if any(
        type(v) is not int for v in (cell.row, cell.col, cell.row_span, cell.col_span)
    ):
        raise ValueError("cell indices/spans must be integers, not booleans")
    if cell.row < 0 or cell.col < 0 or cell.row_span < 1 or cell.col_span < 1:
        raise ValueError("cell indices must be nonnegative and spans positive")
    grid = grids[cell.grid]
    if cell.row + cell.row_span > grid.rows or cell.col + cell.col_span > grid.cols:
        raise ValueError("cell span is outside its grid bounds")
    return (cell.col, cell.row, cell.col + cell.col_span, cell.row + cell.row_span)


def _overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def layout_issues(spec):
    """Validate the full bounded graph before allocating native layout objects."""
    issues = []
    names = [p.panel_id for p in spec.panels if p.panel_id is not None]
    if any(not valid_id(name) for name in names):
        issues.append("panel IDs must match [A-Za-z][A-Za-z0-9_.-]{0,63}")
    if len({name for name in names if isinstance(name, str)}) != len(names):
        issues.append("panel IDs must be unique")
    layout = spec.panel_layout
    if layout is None:
        try:
            implicit_grid(spec)
        except ValueError as error:
            issues.append(str(error))
        if any(p.placement is not None for p in spec.panels):
            issues.append("panel placement requires panel_layout")
        return issues
    if not isinstance(layout, PanelLayoutSpec) or not isinstance(layout.grids, list):
        return [*issues, "panel_layout must be PanelLayoutSpec with a grid list"]
    if (
        spec.layout is not None
        or spec.width_ratios is not None
        or spec.height_ratios is not None
    ):
        issues.append(
            "panel_layout cannot mix legacy layout/width_ratios/height_ratios"
        )
    if len(names) != len(spec.panels):
        issues.append("explicit layout requires an ID for every panel")
    if not 1 <= len(layout.grids) <= MAX_LAYOUT_GRIDS:
        return [*issues, f"layout requires 1..{MAX_LAYOUT_GRIDS} grids"]
    grids = {}
    total = 0
    for grid in layout.grids:
        if not isinstance(grid, LayoutGridSpec) or not valid_id(grid.grid_id):
            issues.append("layout grids require valid grid IDs")
            continue
        if grid.grid_id in grids:
            issues.append(f"duplicate grid ID {grid.grid_id!r}")
        grids[grid.grid_id] = grid
        if any(type(v) is not int or v < 1 for v in (grid.rows, grid.cols)):
            issues.append("grid rows/cols must be positive integers")
            continue
        total += grid.rows * grid.cols
        for key, count in (("width_ratios", grid.cols), ("height_ratios", grid.rows)):
            ratios = getattr(grid, key)
            if ratios is not None and (
                not isinstance(ratios, (list, tuple))
                or len(ratios) != count
                or not all(finite(v) and v > 0 for v in ratios)
            ):
                issues.append(
                    f"grid {grid.grid_id!r} {key} needs {count} positive finite entries"
                )
    if total > MAX_LAYOUT_CELLS:
        issues.append(f"layout supports at most {MAX_LAYOUT_CELLS} aggregate cells")
    if issues:
        return issues
    roots = [g for g in layout.grids if g.cell is None]
    if len(roots) != 1:
        issues.append("layout requires exactly one root grid")
    parents = {}
    rectangles = defaultdict(list)
    for grid in layout.grids:
        node = ("grid", grid.grid_id)
        parents[node] = None
        if grid.cell is not None:
            try:
                box = _cell_rectangle(grid.cell, grids)
                parents[node] = ("grid", grid.cell.grid)
                rectangles[parents[node]].append((node, box))
            except ValueError as error:
                issues.append(f"grid {grid.grid_id!r}: {error}")
    panels = {p.panel_id: p for p in spec.panels}
    for panel in spec.panels:
        node = ("panel", panel.panel_id)
        place = panel.placement
        if not isinstance(place, PanelPlacementSpec) or (place.cell is None) == (
            place.inset is None
        ):
            issues.append(
                f"panel {panel.panel_id!r} needs exactly one cell or inset placement"
            )
            continue
        try:
            if place.cell is not None:
                box = _cell_rectangle(place.cell, grids)
                parent = ("grid", place.cell.grid)
            else:
                inset = place.inset
                if not isinstance(inset, InsetSpec) or inset.parent not in panels:
                    raise ValueError("inset requires an existing parent panel ID")
                bounds = inset.bounds
                if (
                    not isinstance(bounds, (list, tuple))
                    or len(bounds) != 4
                    or not all(finite(v) for v in bounds)
                ):
                    raise ValueError("inset bounds need four finite numbers")
                x, y, w, h = bounds
                if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
                    raise ValueError(
                        "inset bounds must be positive and contained in parent axes"
                    )
                if x + w <= x or y + h <= y:
                    raise ValueError(
                        "inset bounds have unrepresentable positive extent"
                    )
                box = (x, y, x + w, y + h)
                parent = ("panel", inset.parent)
            parents[node] = parent
            rectangles[parent].append((node, box))
        except (ValueError, TypeError) as error:
            issues.append(f"panel {panel.panel_id!r}: {error}")
    for siblings in rectangles.values():
        for index, (node, box) in enumerate(siblings):
            for other, other_box in siblings[index + 1 :]:
                if _overlap(box, other_box):
                    issues.append(
                        f"overlapping sibling placements: {node!r} and {other!r}"
                    )
    # Iterative ancestry walks: no native recursion or cell-sized allocation.
    depths = {}
    invalid = set()
    for node in parents:
        if node in depths or node in invalid:
            continue
        chain = []
        seen = set()
        current = node
        while current is not None and current not in depths and current not in invalid:
            if current in seen:
                issues.append("cyclic layout parent references")
                invalid.update(chain)
                break
            if current not in parents:
                issues.append("layout parent is missing or unreachable")
                invalid.update(chain)
                break
            seen.add(current)
            chain.append(current)
            current = parents[current]
        else:
            if current in invalid:
                invalid.update(chain)
                continue
            depth = depths.get(current, 0)
            for member in reversed(chain):
                depth += 1
                depths[member] = depth
                if depth > MAX_LAYOUT_DEPTH:
                    issues.append(f"layout depth exceeds {MAX_LAYOUT_DEPTH}")
    return list(dict.fromkeys(issues))


def shared_groups(spec, axis_name):
    """The sole primary-Cartesian sharing component convention."""
    groups = {}
    mode = getattr(spec, "share_" + axis_name)
    columns = implicit_grid(spec)[1]
    for index, panel in enumerate(spec.panels):
        if panel.projection != "2d":
            continue
        name = getattr(panel, axis_name).share_id
        key = ("single", index)
        if isinstance(name, str) and name:
            key = ("named", name)
        elif mode == "all":
            key = ("all",)
        elif mode in ("row", "col"):
            if spec.panel_layout is None:
                key = (mode, index // columns if mode == "row" else index % columns)
            elif (
                isinstance(panel.placement, PanelPlacementSpec)
                and panel.placement.cell is not None
            ):
                cell = panel.placement.cell
                start = cell.row if mode == "row" else cell.col
                span = cell.row_span if mode == "row" else cell.col_span
                key = (mode, cell.grid, start, span)
        groups.setdefault(key, []).append(index)
    return list(groups.values())


def panel_axis_roles(columns, panel, axis_name):
    """Infer declared statistical dimensions, never physical units from names."""
    from ._box import advanced_box, box_rows
    from ._categorical import DISTRIBUTION_TYPES, distribution_rows
    from ._density import (
        FIELD_TYPES,
        density_rows,
        density_space,
        fit_scales,
        kde_config,
        multiple,
        observation_axes,
    )
    from ._ecdf import ecdf_rows
    from ._facet import ordered_group_columns
    from ._histogram import histogram_rows
    from ._semantics import semantic_rows
    from ._spectrum import spectrum_axis_units
    from ._stat import (
        STAT_LAYER_TYPES,
        is_missing,
        new_stat_request,
        stat_config,
        usable_rows,
    )
    from ._temporal_data import clock_selector, select_line_rows

    selected_axis = axis_name
    if axis_name == "y2":
        axis_name = "y"
    roles = set()
    for layer in panel.layers:
        if selected_axis in ("y", "y2") and layer.axis != selected_axis:
            continue
        response = "x" if layer.orient == "h" else "y"
        if layer.type == "spectrum":
            roles.add(spectrum_axis_units(layer.spectrum)[0 if axis_name == "x" else 1])
        elif layer.type in ("hist", "kde", "ecdf"):
            if layer.type == "hist" and layer.histogram is not None:
                selected = histogram_rows(columns, layer)
                config = layer.histogram
                role = config.stat
                if config.multiple == "fill" or (
                    config.cumulative and role == "density"
                ):
                    role = "proportion"
                if role == "count" and config.weights is not None:
                    role = "mass"
            elif layer.type == "kde":
                selected = density_rows(columns, layer, panel)
                config = kde_config(layer)
                role = (
                    "proportion"
                    if config is not None and config.cumulative
                    else "density"
                )
                if multiple(config) == "fill":
                    role = "composition"
                elif (
                    role == "density"
                    and density_space(config) == "fit"
                    and any(
                        choice == "axis" and axis is not None and axis.scale == "log"
                        for choice, axis in zip(
                            fit_scales(layer),
                            observation_axes(layer, panel),
                            strict=False,
                        )
                    )
                ):
                    role = "density[fit]"
            else:
                selected = (
                    semantic_rows(columns, layer)
                    if layer.type == "ecdf" and layer.semantics is not None
                    else ecdf_rows(columns, layer)
                )
                if layer.type == "hist":
                    role = "density" if layer.density else "count"
                elif layer.type == "kde":
                    role = "density"
                else:
                    role = layer.ecdf.stat if layer.ecdf is not None else "proportion"
                    if (
                        role == "count"
                        and layer.ecdf is not None
                        and layer.ecdf.weights
                    ):
                        role = "mass"
            if selected:
                roles.add(
                    ("proportion" if role == "probability" else role)
                    if axis_name == response
                    else "value"
                )
        elif layer.type in FIELD_TYPES:
            if density_rows(columns, layer, panel):
                # Probability/density/count is COLOUR; both positions are values.
                roles.add("value")
        elif layer.type in STAT_LAYER_TYPES:
            selected = (
                select_line_rows(columns, layer, panel)
                if layer.type == "lineplot" and clock_selector(layer, panel) is not None
                else usable_rows(
                    columns,
                    layer,
                    advanced=new_stat_request(layer, panel),
                    category_matches=clock_selector(layer, panel),
                )
            )
            if selected:
                config = stat_config(layer)
                role = "value"
                if (
                    config.estimator == "sum"
                    and config.weights is not None
                    and axis_name == response
                ):
                    role = "value*mass"
                if config.estimator == "count" and axis_name == response:
                    role = config.normalize
                    if role == "count" and config.weights is not None:
                        role = "mass"
                    if role == "probability":
                        role = "proportion"
                roles.add(role)
        elif advanced_box(layer):
            if box_rows(columns, layer, category_matches=clock_selector(layer, panel)):
                roles.add("value")
        elif layer.type in DISTRIBUTION_TYPES or layer.type == "swarmplot":
            if distribution_rows(
                columns, layer, category_matches=clock_selector(layer, panel)
            ):
                roles.add("value")
        elif layer.type == "regplot" and layer.regression is not None:
            from ._regression import regression_cohorts

            try:
                cohorts = regression_cohorts(columns, layer)
            except (ValueError, TypeError, KeyError):
                continue  # The authoritative regression validator reports this input.
            config = layer.regression
            selected = [
                row
                for cohort in cohorts
                for row in (
                    cohort.query
                    if config.residual and config.sampling is not None
                    else cohort.train
                )
            ]
            if selected:
                kind = None if config.diagnostics is None else config.diagnostics.kind
                roles.add(
                    "deviance"
                    if axis_name == response and kind == "deviance"
                    else "value"
                )
        elif layer.type not in ("text", "annotate", "hline", "vline"):
            if layer.semantics is not None and layer.type in ("scatter", "lineplot"):
                if semantic_rows(columns, layer):
                    roles.add("value")
                continue
            selected = ordered_group_columns(columns, layer)
            name = getattr(layer, axis_name, "")
            if name in selected and any(not is_missing(v) for v in selected[name]):
                roles.add("value")
    return roles


def sharing_role_issues(spec):
    from ._facet import panel_columns, panel_filter_issues

    issues = []
    for name in ("x", "y"):
        for members in shared_groups(spec, name):
            if len(members) < 2:
                continue
            roles = set()
            for index in members:
                panel = spec.panels[index]
                if panel_filter_issues(spec.data.columns, panel):
                    continue
                columns = panel_columns(spec.data.columns, panel)
                roles.update(panel_axis_roles(columns, panel, name))
            if len(roles) > 1:
                issues.append(
                    f"shared {name} axes have incompatible "
                    "value/statistical dimensions: " + ", ".join(sorted(roles))
                )
    return issues


def twin_value_groups(spec):
    """Named Cartesian links with one actual y2 and primary value-y peers."""
    groups = {}
    for index, panel in enumerate(spec.panels):
        y2 = panel.y2
        if y2 is not None and isinstance(y2.share_id, str) and y2.share_id:
            groups.setdefault(y2.share_id, []).append((index, "y2"))
    for index, panel in enumerate(spec.panels):
        name = panel.y.share_id
        if isinstance(name, str) and name in groups:
            groups[name].append((index, "y"))
    return groups.values()


def twin_value_issues(spec):
    from ._facet import panel_columns, panel_filter_issues

    issues = []
    for members in twin_value_groups(spec):
        index, role = members[0]
        base = getattr(spec.panels[index], role)
        if (
            spec.share_y != "none"
            or len(members) < 2
            or sum(role == "y2" for _, role in members) != 1
            or len({i for i, _ in members}) != len(members)
        ):
            issues.append(
                "named twin value sharing needs one y2 and separate primary y peers"
            )
            continue
        for i, name in members:
            panel = spec.panels[i]
            axis = getattr(panel, name)
            if panel.grid_cohort is not True or panel.projection != "2d":
                issues.append(
                    "named twin value sharing requires Cartesian grid cohorts"
                )
                continue
            if any(
                getattr(axis, k) != getattr(base, k)
                for k in (
                    "scale",
                    "scale_options",
                    "temporal",
                    "limits",
                    "major_ticks",
                    "minor_ticks",
                )
            ):
                issues.append(
                    "named twin value axes have conflicting "
                    "scales, clocks, limits or ticks"
                )
                continue
            if not panel_filter_issues(spec.data.columns, panel):
                columns = panel_columns(spec.data.columns, panel)
                if panel_axis_roles(columns, panel, name) - {"value"}:
                    issues.append(
                        "named twin value sharing cannot link a statistic axis"
                    )
    return list(dict.fromkeys(issues))
