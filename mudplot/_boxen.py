"""C05 finite letter-value contracts, using the shared original-row planner.

No native imports. Summaries are prepared once at the render/preview EFFECT
boundary, never during declaration validation or stored/global cached state.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, replace
from fractions import Fraction

from . import _components
from ._box import BOX_DASHES
from ._categorical import (
    distribution_channels,
    distribution_columns,
    distribution_plan,
    sample_rows,
)
from ._components import component_issues, component_markers, merge_components
from ._ecdf import canonical_type7, finite_number
from ._letter_value import (
    LetterValueSummary,
    _area_widths,
    letter_value_summary,
)
from ._letter_value import option_issues as letter_option_issues
from ._semantics import (
    MAX_LEVELS,
    categorical,
    category_key,
    levels,
    numeric_mapping,
    semantic_levels,
)
from ._semantics import option_issues as semantic_option_issues
from .spec import (
    BoxenBandComponentsSpec,
    BoxenHueComponentsSpec,
    BoxenSpec,
    ComponentStyleSpec,
    DistributionComponentsSpec,
    LayerSpec,
    SemanticSpec,
)

MAX_BOXEN_ROWS = 10000
MAX_BOXEN_CELLS = 256
MAX_BOXEN_POLYGONS = 32768
MAX_BOXEN_FLIERS = 1000000


def _new_glyph(marker):
    return isinstance(marker, str) and (
        marker == "none"
        or (
            marker in component_markers("boxenplot")
            and marker not in _components.MARKERS
        )
    )


def advanced_boxen(layer):
    return layer.type == "boxenplot" and (
        layer.boxen is not None
        or layer.weights is not None
        or layer.semantics is not None
        or layer.axis == "y2"
        or _new_glyph(layer.marker)
        or (
            isinstance(layer.components, DistributionComponentsSpec)
            and isinstance(layer.components.flier, ComponentStyleSpec)
            and _new_glyph(layer.components.flier.marker)
            and layer.components.flier.marker != "none"
        )
    )


def boxen_config(layer):
    return layer.boxen if isinstance(layer.boxen, BoxenSpec) else BoxenSpec()


def band_target(summary, index):
    central = summary.depth - 1
    return abs(index - central), (
        "lower" if index < central else "upper" if index > central else "central"
    )


def boxen_hues(columns, layer, rows):
    _, _, hue = distribution_channels(layer)
    config = layer.semantics
    if hue is None:
        return [None]
    if isinstance(config, SemanticSpec) and config.hue is not None:
        return semantic_levels(columns, config, "hue", rows)
    return (
        list(layer.hue_order)
        if layer.hue_order is not None
        else levels(columns[hue][row] for row in rows)
    )


def hue_override(layer, hue):
    if hue is not None:
        for entry in boxen_config(layer).hue_components or ():
            if category_key(entry.level) == category_key(hue):
                return entry
    return None


def merged_boxen_components(layer, hue):
    entry = hue_override(layer, hue)
    return merge_components(
        layer.components, None if entry is None else entry.components
    )


def merged_band_body(layer, hue, rank, side):
    components = merged_boxen_components(layer, hue)
    result = None if components is None else components.body
    entry = hue_override(layer, hue)
    for bands in (
        boxen_config(layer).band_components,
        None if entry is None else entry.band_components,
    ):
        for band in bands or ():
            if band.rank == rank and band.side == side:
                merged = merge_components(
                    DistributionComponentsSpec(body=result),
                    DistributionComponentsSpec(body=band.body),
                )
                result = merged.body
    return result


def _band_issues(layer, bands):
    if bands is None:
        return []
    if not isinstance(bands, (list, tuple)) or len(bands) > 63:
        return ["boxen band_components needs at most63 typed rank/side entries"]
    issues, seen = [], set()
    for band in bands:
        if not isinstance(band, BoxenBandComponentsSpec):
            issues.append("boxen band_components needs typed entries")
            continue
        valid = (
            type(band.rank) is int
            and 0 <= band.rank <= 31
            and isinstance(band.side, str)
            and (
                (band.rank == 0 and band.side == "central")
                or (band.rank > 0 and band.side in ("lower", "upper"))
            )
        )
        if not valid:
            issues.append("boxen band needs central rank0 or lower/upper rank1..31")
        else:
            key = band.rank, band.side
            if key in seen:
                issues.append("boxen band rank/side targets must be unique")
            seen.add(key)
            if type(layer.k_depth) is int and band.rank >= layer.k_depth:
                issues.append("boxen band rank does not exist at explicit k_depth")
        if not isinstance(band.body, ComponentStyleSpec):
            issues.append("boxen band body must be a ComponentStyleSpec")
        else:
            issues.extend(
                component_issues(
                    replace(
                        layer, components=DistributionComponentsSpec(body=band.body)
                    )
                )
            )
    return issues


def boxen_option_issues(layer):
    issues = letter_option_issues(
        layer.k_depth, layer.width_method, layer.outlier_prop, layer.trust_alpha
    )
    if layer.boxen is not None and not isinstance(layer.boxen, BoxenSpec):
        return [*issues, "boxen must be a BoxenSpec"]
    issues.extend(component_issues(layer))
    options = boxen_config(layer)
    issues.extend(_band_issues(layer, options.band_components))
    entries = options.hue_components
    if entries is not None:
        if not isinstance(entries, (list, tuple)) or len(entries) > MAX_LEVELS:
            return [*issues, "boxen hue_components needs at most64 typed entries"]
        seen = set()
        for entry in entries:
            if not isinstance(entry, BoxenHueComponentsSpec) or not categorical(
                entry.level
            ):
                issues.append("boxen hue_components needs typed raw scalar levels")
                continue
            key = category_key(entry.level)
            if key in seen:
                issues.append("boxen component hue keys must be unique")
            seen.add(key)
            if entry.components is None and not entry.band_components:
                issues.append("boxen hue entry needs components or band_components")
            if entry.components is not None:
                issues.extend(
                    component_issues(replace(layer, components=entry.components))
                )
            issues.extend(_band_issues(layer, entry.band_components))
    if layer.marker is not None and (
        not isinstance(layer.marker, str)
        or layer.marker not in component_markers("boxenplot")
    ):
        issues.append("boxen marker must be a registered observed flier glyph")
    if layer.marker is not None and layer.showfliers is False:
        issues.append("boxen marker requires requested fliers")
    if layer.weights is not None and (
        not isinstance(layer.weights, str) or not layer.weights
    ):
        issues.append("boxen weights must be a nonempty column name")
    return issues


def boxen_semantic_issues(columns, layer, panel):
    config = layer.semantics
    issues = semantic_option_issues(config)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    _, _, legacy_hue = distribution_columns(layer)
    if layer.c is not None or (
        config.hue is not None
        and (legacy_hue is not None or layer.hue_order is not None)
    ):
        issues.append("mapped boxen hue cannot combine with independent legacy hue/c")
    if panel.projection != "2d":
        issues.append("boxen semantics require Cartesian2D")
    for role, name in (
        ("hue", "color"),
        ("size", "line_width"),
        ("style", "line_style"),
    ):
        if getattr(config, role) is not None and getattr(layer, name) is not None:
            issues.append(f"{name} cannot override mapped boxen body {role}")
    if config.style is not None and layer.marker is not None:
        issues.append("marker cannot override mapped boxen flier glyph")
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if numeric_hue and layer.cmap_kind not in ("sequential", "diverging"):
        issues.append("numeric boxen hue requires registered colormap kind")
    if not numeric_hue and (
        layer.colorbar or layer.clabel is not None or layer.cmap_kind != "sequential"
    ):
        issues.append("boxen colorbar/colormap requires numeric hue")
    if type(layer.colorbar) is not bool:
        issues.append("boxen colorbar must be boolean")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append("boxen clabel requires colorbar and bounded text")
    rows = sample_rows(columns, layer)
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        if not isinstance(name, str) or name not in columns:
            issues.append(f"boxen semantic {role} column must exist")
            continue
        values = [columns[name][row] for row in rows]
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        if kind == "numeric":
            if any(not finite_number(value) for value in values):
                issues.append(f"boxen numeric {role} must be finite nonbool")
            elif values:
                try:
                    numeric_mapping(values, getattr(config, role + "_norm"))
                except ValueError as error:
                    issues.append(str(error))
        elif any(not categorical(value) for value in values):
            issues.append(f"boxen {role} needs finite nonempty categorical levels")
        else:
            selected = semantic_levels(columns, config, role, rows)
            if len(selected) > MAX_LEVELS or len({str(v) for v in selected}) != len(
                selected
            ):
                issues.append(f"boxen categorical {role} has too many/ambiguous levels")
            if role == "style" and len(selected) > len(config.dashes or BOX_DASHES):
                issues.append("boxen style needs enough distinct body dashes")
    components = [layer.components]
    bodies = []
    for entry in boxen_config(layer).hue_components or ():
        if isinstance(entry, BoxenHueComponentsSpec):
            components.append(entry.components)
            bodies.extend(band.body for band in entry.band_components or ())
    bodies.extend(band.body for band in boxen_config(layer).band_components or ())
    for styles in components:
        if not isinstance(styles, DistributionComponentsSpec):
            continue
        bodies.append(styles.body)
        if (
            config.style is not None
            and styles.flier is not None
            and styles.flier.marker is not None
        ):
            issues.append("flier component marker conflicts with mapped boxen glyph")
    for body in bodies:
        if not isinstance(body, ComponentStyleSpec):
            continue
        for role, name in (
            ("hue", "color"),
            ("size", "line_width"),
            ("style", "line_style"),
        ):
            if getattr(config, role) is not None and getattr(body, name) is not None:
                issues.append(f"band/body {name} conflicts with mapped boxen {role}")
    return issues


def boxen_issues(columns, layer, panel, *, allow_empty=False):
    issues = boxen_option_issues(layer)
    if issues:
        return issues
    if panel.projection != "2d":
        issues.append("advanced boxen requires Cartesian2D")
    response = panel.y2 if layer.axis == "y2" else panel.y
    value_axis = panel.x if layer.orient == "h" else response
    if (
        layer.stat_scale == "axis"
        and value_axis is not None
        and value_axis.scale not in ("linear", "log")
    ):
        issues.append("boxen stat_scale='axis' supports linear/log value transforms")
    category, value, hue = distribution_channels(layer)
    config = layer.semantics
    if config is not None:
        issues.extend(boxen_semantic_issues(columns, layer, panel))
    required = [
        name for name in (category, value, hue, layer.weights) if name is not None
    ]
    if isinstance(config, SemanticSpec):
        required.extend(
            getattr(config, role)
            for role in ("hue", "size", "style")
            if getattr(config, role) is not None
        )
    if any(not isinstance(name, str) or name not in columns for name in required):
        return [*issues, "boxen required columns must exist"]
    if any(not isinstance(columns[name], (list, tuple)) for name in required):
        return [*issues, "boxen columns must be arrays"]
    if len({len(columns[name]) for name in required}) > 1:
        return [*issues, "boxen columns must have equal lengths"]
    rows = sample_rows(columns, layer)
    if len(rows) > MAX_BOXEN_ROWS:
        return [
            *issues,
            "advanced boxen selected positive source instances exceed10000",
        ]
    if any(not finite_number(columns[value][row]) for row in rows):
        issues.append("boxen observations must be finite nonbool")
    if layer.weights is not None and any(
        not finite_number(columns[layer.weights][row])
        or columns[layer.weights][row] < 0
        for row in rows
    ):
        issues.append("boxen weights must be finite nonnegative nonbool")
    if any(
        name is not None and any(not categorical(columns[name][row]) for row in rows)
        for name in (category, hue)
    ):
        issues.append("boxen category/hue needs finite nonempty scalars")
    if issues:
        return issues
    categories, _, cells = distribution_plan(columns, layer, rows=rows)
    if len(cells) > MAX_BOXEN_CELLS:
        issues.append("advanced boxen drawn raw-tuple samplecells exceed256")
    if len(categories) > MAX_LEVELS:
        issues.append("boxen category levels exceed64")
    hues = boxen_hues(columns, layer, rows)
    numeric_hue = (
        isinstance(config, SemanticSpec)
        and config.hue is not None
        and config.hue_kind == "numeric"
    )
    if not numeric_hue and len(hues) > MAX_LEVELS:
        issues.append("boxen categorical hue levels exceed64")
    entries = boxen_config(layer).hue_components or ()
    if entries and (hue is None or numeric_hue):
        issues.append("boxen per-hue components require independent categorical hue")
    known = {category_key(item) for item in hues if item is not None}
    explicit_hues = layer.hue_order is not None or (
        isinstance(config, SemanticSpec) and config.hue_order is not None
    )
    if not rows and not known and not explicit_hues and isinstance(hue, str):
        # Recognize a dormant raw key in an all-zero/missing cohort without
        # adding it to the actual mapping/statistic/guide domain.
        known = {category_key(item) for item in columns[hue] if categorical(item)}
    if rows or known or explicit_hues or not allow_empty:
        for entry in entries:
            if category_key(entry.level) not in known:
                issues.append("boxen component hue level is not in the declared domain")
    return issues


@dataclass(frozen=True)
class BoxenCell:
    cell: dict
    summary: LetterValueSummary
    original_fliers: tuple[int | float, ...]
    native_values: tuple[float, ...]
    native_median: float


@dataclass(frozen=True)
class BoxenPlan:
    columns: dict
    layer: LayerSpec
    categories: list
    groups: list
    cells: tuple[BoxenCell, ...]


def _prepare_summary(values, weights, layer, *, logarithmic=False):
    """One fit plus exact order certificates at the existing geometry boundary.

    LEFT quantiles/masses/tail membership are invariant under a monotone log.
    For type7, raw rank interpolation certifies positive BAND ordering only,
    NOT a different tail estimator; the statistic still interpolates log10 values.
    No second full summary, estimator option or source mutation is involved.
    """
    weighted = weights is not None
    working = (
        [math.log10(value) for value in values]
        if logarithmic and not weighted
        else values
    )
    summary = letter_value_summary(
        working,
        weights=weights,
        k_depth=layer.k_depth,
        width_method=(
            None
            if logarithmic and weighted and layer.width_method == "area"
            else layer.width_method
        ),
        outlier_prop=layer.outlier_prop,
        trust_alpha=layer.trust_alpha,
    )
    assert summary.exact_values is not None
    order = summary.exact_values
    original_fliers = summary.fliers
    if logarithmic and not weighted:
        ordered = sorted(values)
        order = tuple(canonical_type7(ordered, p) for p in summary.percentiles)
        original_fliers = tuple(
            value
            for value, coordinate in zip(values, working, strict=True)
            if coordinate < summary.values[0] or coordinate > summary.values[-1]
        )
    if logarithmic and weighted:
        # Exact LEFT coordinates are observed source values, not a lossy
        # exp(log(observation)) round trip (which can even overflow at maxfinite).
        native_values = tuple(float(value) for value in summary.values)
        native_median = float(summary.median)
        coordinates = tuple(math.log10(value) for value in summary.values)
        summary = replace(
            summary,
            values=coordinates,
            median=math.log10(summary.median),
            exact_values=tuple(Fraction(value) for value in coordinates),
        )
    else:
        native_values = tuple(
            _native_value(value, inverse_log=logarithmic) for value in summary.values
        )
        native_median = _native_value(summary.median, inverse_log=logarithmic)
    if logarithmic:
        summary = replace(
            summary, fliers=tuple(math.log10(value) for value in original_fliers)
        )
    coordinates = tuple(float(value) for value in summary.values)
    for i, (low, high) in enumerate(itertools.pairwise(order)):
        if high > low and not (
            coordinates[i + 1] > coordinates[i]
            and native_values[i + 1] > native_values[i]
        ):
            raise ValueError(
                "letter-value precision: positive statistical span collapses "
                "in native binary64 coordinates"
            )
    if layer.showfliers is not False:
        for value in original_fliers:
            native = _native_value(value)
            coordinate = math.log10(value) if logarithmic else native
            below = (
                Fraction(value) < order[0]
                if weighted
                else coordinate < coordinates[0]
                if logarithmic
                else value < summary.values[0]
            )
            if not (
                (coordinate < coordinates[0] and native < native_values[0])
                if below
                else (coordinate > coordinates[-1] and native > native_values[-1])
            ):
                raise ValueError(
                    "letter-value precision: observed strict-tail ordering "
                    "collapses in native binary64 coordinates"
                )
    if (
        not weighted
        and layer.width_method == "area"
        and any(
            high > low and width == 0
            for (low, high), width in zip(
                zip(summary.values[:-1], summary.values[1:], strict=True),
                summary.widths,
                strict=True,
            )
        )
    ):
        raise ValueError(
            "letter-value precision: positive area width is unrepresentable"
        )
    if logarithmic and weighted and layer.width_method == "area":
        assert summary.masses is not None
        summary = replace(
            summary,
            widths=tuple(_area_widths(summary.masses, summary.values, summary.widths)),
        )
    return summary, original_fliers, native_values, native_median


def _native_value(value, *, inverse_log=False):
    try:
        result = 10.0 ** float(value) if inverse_log else float(value)
    except OverflowError as error:
        raise ValueError(
            "letter-value precision: native coordinate is unrepresentable"
        ) from error
    if not math.isfinite(result) or (inverse_log and result <= 0):
        raise ValueError("letter-value precision: native coordinate is unrepresentable")
    return result


def prepare_boxen_plans(spec, *, domains):
    """Derive ONCE, admit actual figure work, then reuse before native allocation.

    Declaration validation deliberately does not call this effect preparation:
    a valid saved source can exceed an owned rendering budget.
    """
    from ._facet import panel_columns
    from ._temporal_data import prepare_temporal_layer

    prepared = {}
    polygons = fliers = 0
    for pi, panel in enumerate(spec.panels):
        columns = None
        for li, source_layer in enumerate(panel.layers):
            if not advanced_boxen(source_layer):
                continue
            if columns is None:
                columns = panel_columns(spec.data.columns, panel)
            view, layer, _ = prepare_temporal_layer(columns, source_layer, panel)
            rows = sample_rows(view, layer)
            categories, groups, cells = distribution_plan(view, layer, rows=rows)
            _, value, _ = distribution_channels(layer)
            response = panel.y2 if layer.axis == "y2" else panel.y
            value_axis = panel.x if layer.orient == "h" else response
            logarithmic = layer.stat_scale == "axis" and value_axis.scale == "log"
            summaries = []
            for cell in cells:
                prepared_summary = _prepare_summary(
                    [view[value][row] for row in cell["rows"]],
                    None
                    if layer.weights is None
                    else [view[layer.weights][row] for row in cell["rows"]],
                    layer,
                    logarithmic=logarithmic,
                )
                summary = prepared_summary[0]
                polygons += len(summary.widths)
                if layer.showfliers is not False:
                    fliers += len(summary.fliers)
                _check_work(polygons, fliers)
                summaries.append(BoxenCell(cell, *prepared_summary))
            prepared[pi, li] = BoxenPlan(
                view, layer, categories, groups, tuple(summaries)
            )
    _check_actual_glyphs(prepared, domains)
    return prepared


def _check_work(polygons, fliers):
    if polygons > MAX_BOXEN_POLYGONS:
        raise ValueError("advanced boxen actual band polygons exceed32768 per figure")
    if fliers > MAX_BOXEN_FLIERS:
        raise ValueError(
            "advanced boxen requested flier instances exceed1000000 per figure"
        )


def _check_actual_glyphs(prepared, domains):
    for plan in prepared.values():
        layer, config = plan.layer, plan.layer.semantics
        if (
            not isinstance(config, SemanticSpec)
            or config.style is None
            or layer.showfliers is False
            or not any(cell.summary.fliers for cell in plan.cells)
        ):
            continue
        if config.scale_id is not None:
            domain = domains[config.scale_id]
            columns, rows = domain["columns"], domain["rows"]
        else:
            columns, rows = plan.columns, sample_rows(plan.columns, layer)
        selected = [
            category_key(value)
            for value in semantic_levels(columns, config, "style", rows)
        ]
        for cell in plan.cells:
            if cell.summary.fliers:
                index = selected.index(category_key(cell.cell["roles"]["style"]))
                if index >= len(config.markers):
                    raise ValueError(
                        "boxen style needs a registered glyph "
                        "for each actual flier style"
                    )
