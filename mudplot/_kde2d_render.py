"""Native bivariate kernel fields, shared with paired-histogram overlays.

ContourPy is Matplotlib's existing native contour backend, not a fitting or
integration provider. Planning its paths before adding artists lets the NEW
figure ledger admit actual closure vertices and retained geometry first.
"""

from __future__ import annotations

import itertools
import warnings
from typing import Any, cast

import numpy as np
from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.colors import Normalize
from matplotlib.path import Path

from ._components import finalize_component_stroke
from ._density import kde_config, level_kind
from ._density_input import prepare_input
from ._kde import kernel_query_grid, prepare_kernel_profiles
from ._kde2d import computed_conditional_levels, evaluate_computed_field
from ._kernel_math import IntervalMath, KernelPrecisionError
from .spec import KDE2DSpec

NativeContours = tuple[list[np.ndarray], list[np.ndarray]]


def _native_contours(x, y, values, levels, filled, budget):
    import contourpy

    cells = (len(x) - 1) * (len(y) - 1)
    levels = tuple(float(value) for value in levels)
    if filled and len(levels) < 2:
        raise ValueError("filled kernel fields require at least two distinct levels")
    generator_lease = None
    leases = []
    vertices, codes, scalars, path_counts = [], [], [], []
    if budget is not None:
        generator_lease = budget.array_lease((len(y), len(x)), copies=4)
    try:
        generator = contourpy.contour_generator(
            x=x,
            y=y,
            z=values,
            name="serial",
            corner_mask=False,
            line_type="SeparateCode",
            fill_type="OuterCode",
            quad_as_tri=False,
        )
        count_levels = len(levels) - 1 if filled else len(levels)
        for level_index in range(count_levels):
            # A finite quad has at most four line crossings, or twelve band
            # corners/crossings plus two closures. This is prospective storage,
            # NOT a fabricated actual-vertex tally or a separate public cap.
            upper_vertices = (14 if filled else 4) * cells
            upper_paths = 2 * cells
            temporary = []
            if budget is not None:
                budget.charge("native_quad_level_visits", cells)
                budget.admit_vertices(upper_vertices)
                temporary.extend(
                    (
                        budget.array_lease((upper_vertices, 2), copies=2),
                        budget.array_lease((upper_vertices,), dtype="uint8", copies=2),
                        budget.array_lease((0, 2), copies=max(upper_paths, 1)),
                        budget.array_lease(
                            (0,), dtype="uint8", copies=max(upper_paths, 1)
                        ),
                    )
                )
            try:
                if filled:
                    low, high = levels[level_index], levels[level_index + 1]
                    new_vertices, new_codes = cast(
                        NativeContours, generator.filled(low, high)
                    )
                    scalar = float((low / 2) + (high / 2))
                else:
                    scalar = levels[level_index]
                    new_vertices, new_codes = cast(
                        NativeContours, generator.lines(scalar)
                    )
                count = sum(len(points) for points in new_vertices)
                if count > upper_vertices or len(new_vertices) > upper_paths:
                    raise KernelPrecisionError(
                        "native contour expansion exceeded its admitted quad bound"
                    )
                if budget is not None:
                    leases.append(budget.native_path_lease(count, len(new_vertices)))
                    leases.append(budget.array_lease((count, 2)))
                    leases.append(budget.array_lease((count,), dtype="uint8"))
                    leases.append(budget.array_lease((len(new_vertices),)))
                for points, kinds in zip(new_vertices, new_codes, strict=True):
                    if not np.all(np.isfinite(points)):
                        raise KernelPrecisionError(
                            "native kernel contour coordinates are not finite"
                        )
                    vertices.append(points)
                    codes.append(kinds)
                    scalars.append(scalar)
                path_counts.append(len(new_vertices))
            finally:
                for lease in reversed(temporary):
                    lease.close()
        return vertices, codes, np.asarray(scalars), tuple(path_counts), leases
    except Exception:
        for lease in reversed(leases):
            lease.close()
        raise
    finally:
        if generator_lease is not None:
            generator_lease.close()


def _field_units(model, config, layer, panel):
    from ._density import observation_axes
    from ._transforms import unit as coordinate_unit

    if config.cumulative:
        return "joint CDF contribution"
    axes = observation_axes(layer, panel)
    units = [
        coordinate_unit(
            layer,
            "xy"[index],
            "log10 input"
            if logarithmic and config.density_space == "fit"
            else "day"
            if axis is not None and axis.temporal is not None
            else f"input{index + 1}",
        )
        for index, (axis, logarithmic) in enumerate(
            zip(axes, model.log_axes, strict=True)
        )
    ]
    return f"density (1/({units[0]} * {units[1]}))"


def draw_kernel_fields(
    ax,
    columns,
    layer,
    panel,
    color_iter,
    theme,
    *,
    curve_styles=None,
    input_plan=None,
    row_ids=None,
):
    from ._field_render import (
        _frame_bounds,
        _reference,
        _tinted_cmap,
        field_guide,
        field_stroke_width,
        figure_field_budget,
        retain_leases,
        statistic_colourbar,
    )
    from ._render import _continuous_cmap, _set_url

    config = kde_config(layer)
    if not isinstance(config, KDE2DSpec):
        raise ValueError("bivariate native fields require KDE2DSpec")
    budget = (
        figure_field_budget(ax.figure, layer, panel)
        if input_plan is None
        else input_plan.budget
    )
    cohort = (
        prepare_input(columns, layer, panel, budget)
        if input_plan is None
        else input_plan
    )
    plan = None
    pending = []
    styles = {} if curve_styles is None else curve_styles
    try:
        plan = prepare_kernel_profiles(
            columns,
            layer,
            panel,
            config,
            input_plan=cohort,
            arithmetic=IntervalMath(cohort.budget),
        )
        base_cmap = _continuous_cmap(layer.cmap_kind)
        if curve_styles is None:
            dashes = (
                itertools.cycle(theme.line_styles)
                if theme.redundant_encoding and len(plan.profiles) > 1
                else itertools.repeat("-")
            )
            for profile in plan.profiles:
                styles[profile.index] = {
                    "color": layer.color or next(color_iter),
                    "width": field_stroke_width(layer),
                    "dash": layer.line_style or next(dashes),
                    "edge_color": layer.edge_color,
                }
        fitted = False
        for profile in plan.profiles:
            model = profile.model
            if model is None:
                if profile.singular and config.warn_singular:
                    warnings.warn(
                        f"KDE2D skipped singular/insufficient field {profile.hue!r}; "
                        "no covariance or observations were invented",
                        UserWarning,
                        stacklevel=3,
                    )
                continue
            fitted = True
            style = styles[profile.index]
            color, width, dash = style["color"], style["width"], style["dash"]
            tinted = (
                layer.group is not None
                or layer.color is not None
                or (layer.semantics is not None and layer.semantics.hue is not None)
            )
            cmap = _tinted_cmap(color) if tinted else base_cmap
            label, _citation, href = _reference(layer, profile)
            field = None
            try:
                if config.hdr is not None:
                    from ._hdr import solve_full_hdr
                    from ._hdr_render import HDRCollection

                    region = solve_full_hdr(model, config)
                    grid = kernel_query_grid(
                        model if plan.pooled is None else plan.pooled, config
                    )
                    bounds = tuple((values[0], values[-1]) for values in grid)
                    maximum = max(
                        (level.cutoff for level in region.levels), default=1.0
                    )
                    norm = Normalize(0, maximum)
                    try:
                        artist = HDRCollection(
                            ax,
                            region,
                            config,
                            layer,
                            bounds,
                            cmap=cmap,
                            norm=norm,
                            style=style,
                        )
                    except Exception:
                        region.close()
                        raise
                    ax.add_collection(artist, autolim=False)
                    _frame_bounds(ax, grid[0], grid[1], layer.orient)
                    # The real collection owns its original law for native
                    # visibility/coordinate certificates; no second fit/copy.
                    profile.model = None
                    if plan.pooled is model:
                        plan.pooled = None
                    metadata = artist._mudplot_hdr
                    metadata["source_row_indices"] = tuple(
                        row if row_ids is None else row_ids[row] for row in profile.rows
                    )
                else:
                    field = evaluate_computed_field(
                        model, config, grid_model=plan.pooled
                    )
                    logical_x, logical_y = field.x, field.y
                    x, y, values = (
                        (logical_x, logical_y, np.asarray(field.values).T)
                        if layer.orient == "v"
                        else (logical_y, logical_x, np.asarray(field.values))
                    )
                    for scale, grid in zip(
                        (ax.get_xscale(), ax.get_yscale()), (x, y), strict=True
                    ):
                        if scale == "log" and min(grid) <= 0:
                            raise ValueError(
                                "derived log KDE support must be positive; use cut/clip"
                            )
                    kind = level_kind(config)
                    included = integral = None
                    if kind == "mass":
                        levels, included, integral = computed_conditional_levels(
                            model, field, config
                        )
                    else:
                        levels = tuple(config.levels)
                    maximum = float(np.max(values))
                    norm = Normalize(0, maximum if maximum > 0 else 1)
                    vertices, codes, scalars, path_counts, leases = _native_contours(
                        x, y, values, levels, config.fill, budget
                    )
                    pending.extend(leases)
                    if config.fill:
                        artist = PolyCollection(
                            [],
                            array=scalars,
                            cmap=cmap,
                            norm=norm,
                            edgecolors=style.get("edge_color")
                            or ("face" if width else "none"),
                            linewidths=width,
                            linestyles="solid" if width == 0 else dash,
                            alpha=layer.alpha,
                            label="_nolegend_",
                            antialiaseds=False,
                        )
                        artist.set_verts_and_codes(vertices, codes)
                    else:
                        paths = [
                            Path(points, kinds)
                            for points, kinds in zip(vertices, codes, strict=True)
                        ]
                        artist = PathCollection(
                            paths,
                            array=scalars,
                            cmap=cmap,
                            norm=norm,
                            facecolors="none",
                            edgecolors=style.get("edge_color"),
                            linewidths=width,
                            linestyles="solid" if width == 0 else dash,
                            alpha=layer.alpha,
                            label="_nolegend_",
                        )
                    ax.add_collection(artist, autolim=False)
                    _frame_bounds(ax, logical_x, logical_y, layer.orient)
                    metadata = {
                        "source_row_indices": tuple(
                            row if row_ids is None else row_ids[row]
                            for row in profile.rows
                        ),
                        "kernel": model.kernel,
                        "cumulative": bool(config.cumulative),
                        "density_space": config.density_space or "data",
                        "amplitude": str(model.amplitude),
                        "logical_query_x": logical_x,
                        "logical_query_y": logical_y,
                        "absolute_cdf_error": field.absolute_error,
                        "source_law_error": model.source_tv,
                        "level_kind": kind,
                        "native_levels": levels,
                        "paths_per_requested_level_or_band": path_counts,
                        "conditional_grid_included": included,
                        "conditional_grid_integral_scaled": integral,
                        "empty_level_sets_are_not_rebased": True,
                    }
                    cast(Any, artist)._mudplot_kernel_field = metadata
                    if budget is not None:
                        pending.append(budget.account(metadata))
                    retain_leases(ax.figure, pending)
                    pending.clear()
                finalize_component_stroke(artist, body=bool(config.fill))
                artist.update_scalarmappable()
                _set_url(artist, href)
                if artist.get_url() is not None:
                    artist.set_urls([artist.get_url()])
                serial = getattr(ax.figure, "_mudplot_field_serial", 0)
                artist.set_gid(f"mudplot-kernel-field-{serial}")
                ax.figure._mudplot_field_serial = serial + 1
                style.update(artist=artist, filled=bool(config.fill))
                native_colors = (
                    artist.get_facecolor() if config.fill else artist.get_edgecolor()
                )
                if len(native_colors):
                    representative = (
                        int(np.argmax(np.asarray(artist.get_array())))
                        if len(np.asarray(artist.get_array()))
                        else 0
                    )
                    style["color"] = native_colors[
                        min(representative, len(native_colors) - 1)
                    ]
                    edges = artist.get_edgecolor()
                    style["edge"] = (
                        edges[min(representative, len(edges) - 1)]
                        if len(edges)
                        else "none"
                    )
                if layer.colorbar:
                    name = label
                    if layer.semantics is not None:
                        name = (
                            ", ".join(
                                f"{key}={value}" for key, value in profile.roles.items()
                            )
                            or layer.label
                        )
                    units = layer.clabel or _field_units(model, config, layer, panel)
                    if config.hdr is not None:
                        units = "full HDR cutoff " + units
                    statistic_colourbar(
                        ax,
                        artist,
                        f"{name}: {units}" if name else units,
                        budget,
                        href=href,
                        generated_units=(name, units) if not layer.clabel else None,
                    )
                if curve_styles is None and (
                    layer.group is not None or (layer.label and not layer.colorbar)
                ):
                    handle = field_guide(ax, style, label)
                    _set_url(handle, href)
            finally:
                if field is not None:
                    field.close()
        if (
            not fitted
            and config.clip is not None
            and all(
                bound is not None and all(value is not None for value in bound)
                for bound in config.clip
            )
        ):
            _frame_bounds(ax, config.clip[0], config.clip[1], layer.orient)
        return styles
    finally:
        for lease in reversed(pending):
            lease.close()
        if plan is not None:
            plan.close()
        if input_plan is None:
            cohort.close()
