"""C03 pure contracts: raw row cohorts, columnar summaries and native box work."""

from __future__ import annotations

import itertools
from dataclasses import fields, replace

from ._categorical import (
    distribution_channels,
    distribution_columns,
    distribution_plan,
    sample_rows,
)
from ._components import component_issues, merge_components
from ._ecdf import finite_number
from ._semantics import (
    MARKERS,
    MAX_LEVELS,
    categorical,
    category_key,
    numeric_mapping,
    semantic_levels,
)
from ._semantics import (
    option_issues as semantic_option_issues,
)
from ._stat import MAX_BOOTSTRAPS
from .spec import (
    BoxHueComponentsSpec,
    BoxMedianCISpec,
    BoxSpec,
    BoxSummarySpec,
    DistributionComponentsSpec,
    SemanticSpec,
)

MAX_BOX_CELLS = 256
MAX_BOX_ROWS = 10_000
MAX_BOX_FLIERS = 10_000
BOX_DASHES = ("-", "--", ":", "-.")


def advanced_box(layer):
    return layer.type == "box" and (
        layer.box is not None or layer.semantics is not None or layer.axis == "y2"
    )


def make_box(
    *, summary=None, median_ci=None, cap_fraction=None, hue_components=None
) -> BoxSpec | None:
    if all(
        value is None for value in (summary, median_ci, cap_fraction, hue_components)
    ):
        return None
    value = BoxSpec(
        summary=summary,
        median_ci=median_ci,
        cap_fraction=cap_fraction,
        hue_components=hue_components,
    )
    decoded = BoxSpec.from_dict(value.to_dict())
    if not isinstance(decoded, BoxSpec):
        raise TypeError("box controls must decode to BoxSpec")
    return decoded


def box_config(layer):
    return layer.box if isinstance(layer.box, BoxSpec) else BoxSpec()


def summary_columns(layer, *, optional=False):
    summary = box_config(layer).summary
    if not isinstance(summary, BoxSummarySpec):
        return []
    roles = ("q1", "q3", "whislo", "whishi")
    if optional:
        roles += ("mean", "cilo", "cihi", "fliers")
    return [
        (role, getattr(summary, role))
        for role in roles
        if getattr(summary, role) is not None
    ]


def box_rows(columns, layer, *, category_matches=None):
    """Optional unavailable summary marks never remove a valid samplecell."""
    return sample_rows(
        columns,
        layer,
        required=[name for _, name in summary_columns(layer)],
        limit=MAX_BOX_ROWS,
        category_matches=category_matches,
    )


def _key(value):
    return None if value is None else category_key(value)


def merged_components(layer, hue):
    """Global component properties, then fieldwise matching raw-hue properties."""
    result = layer.components
    for entry in box_config(layer).hue_components or []:
        if not isinstance(entry, BoxHueComponentsSpec) or not categorical(entry.level):
            continue
        if _key(entry.level) != _key(hue):
            continue
        result = merge_components(result, entry.components)
    return result


def box_option_issues(layer):
    problems = []
    config = layer.box
    if config is not None and not isinstance(config, BoxSpec):
        return ["box must be a BoxSpec"]
    config = box_config(layer)
    summary = config.summary
    if summary is not None and not isinstance(summary, BoxSummarySpec):
        problems.append("box.summary must be a BoxSummarySpec")
    if isinstance(summary, BoxSummarySpec):
        for field in fields(BoxSummarySpec):
            value = getattr(summary, field.name)
            if value is None and field.name in ("mean", "cilo", "cihi", "fliers"):
                continue
            if not isinstance(value, str) or not value:
                problems.append("summary fields must reference nonempty column names")
    if config.cap_fraction is not None and (
        not finite_number(config.cap_fraction) or not 0 <= config.cap_fraction <= 1
    ):
        problems.append("box.cap_fraction must be finite nonbool in [0,1]")
    ci = config.median_ci
    if ci is not None:
        if not isinstance(ci, BoxMedianCISpec):
            problems.append("box.median_ci must be a BoxMedianCISpec")
        else:
            if not finite_number(ci.level) or not 0 < ci.level < 100:
                problems.append("median CI level must be finite in (0,100)")
            if type(ci.n_boot) is not int or not 1 <= ci.n_boot <= MAX_BOOTSTRAPS:
                problems.append(f"median CI n_boot must be in [1,{MAX_BOOTSTRAPS}]")
            if isinstance(ci.seed, bool) or not isinstance(ci.seed, int) or ci.seed < 0:
                problems.append("median CI seed must be a nonnegative integer")
        if layer.notch is False:
            problems.append("median bootstrap CI conflicts with notch=False")
        if summary is not None:
            problems.append(
                "supplied quartiles cannot bootstrap missing raw observations"
            )
    if summary is not None and layer.whis is not None:
        problems.append("supplied whiskers cannot be replaced by whis")
    entries = config.hue_components
    if entries is not None:
        if not isinstance(entries, (list, tuple)) or len(entries) > MAX_LEVELS:
            problems.append(
                f"hue_components must contain at most {MAX_LEVELS} typed entries"
            )
        else:
            seen = set()
            for entry in entries:
                if (
                    not isinstance(entry, BoxHueComponentsSpec)
                    or not categorical(entry.level)
                    or not isinstance(entry.components, DistributionComponentsSpec)
                ):
                    problems.append(
                        "hue_components require raw scalar level and typed components"
                    )
                    continue
                key = category_key(entry.level)
                if key in seen:
                    problems.append("hue_components raw levels must be unique")
                seen.add(key)
                problems.extend(
                    component_issues(replace(layer, components=entry.components))
                )
    problems.extend(component_issues(layer))
    return problems


def box_semantic_issues(columns, layer, panel):
    config = layer.semantics
    problems = semantic_option_issues(config)
    if not isinstance(config, SemanticSpec) or problems:
        return problems
    _category, _value, legacy_hue = distribution_columns(layer)
    if legacy_hue is not None or layer.c is not None or layer.hue_order is not None:
        problems.append("box semantics cannot combine with independent legacy hue/c")
    if panel.projection != "2d":
        problems.append("box semantics require Cartesian 2D axes")
    if config.hue is not None and layer.color is not None:
        problems.append("color cannot override mapped box body fill")
    if config.size is not None and layer.line_width is not None:
        problems.append("line_width cannot override mapped box body stroke")
    if config.style is not None and (
        layer.line_style is not None or layer.marker is not None
    ):
        problems.append(
            "line_style/marker cannot override mapped box body dashes/flier glyph"
        )
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if numeric_hue and layer.cmap_kind not in ("sequential", "diverging"):
        problems.append("numeric box hue requires a registered colormap kind")
    if (
        layer.colorbar or layer.clabel is not None or layer.cmap_kind != "sequential"
    ) and not numeric_hue:
        problems.append("box colourbar/colormap requires mapped numeric hue")
    if type(layer.colorbar) is not bool:
        problems.append("box colorbar must be boolean")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        problems.append("box clabel requires colorbar and a bounded string")
    rows = box_rows(columns, layer)
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        if not isinstance(name, str) or name not in columns:
            problems.append(f"box semantic {role} column must exist")
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        values = [columns[name][row] for row in rows]
        if kind == "numeric":
            if any(not finite_number(v) for v in values):
                problems.append(f"box numeric {role} must be finite nonbool")
            elif values:
                try:
                    numeric_mapping(values, getattr(config, role + "_norm"))
                except ValueError as error:
                    problems.append(str(error))
        elif any(not categorical(v) for v in values):
            problems.append(f"box {role} levels must be nonempty finite scalars")
        else:
            selected = semantic_levels(columns, config, role, rows)
            if len(selected) > MAX_LEVELS or len({str(v) for v in selected}) != len(
                selected
            ):
                problems.append(f"box {role} has too many/ambiguous levels")
            if role == "style":
                dashes = BOX_DASHES if config.dashes is None else config.dashes
                if len(selected) > len(dashes) or len(selected) > len(config.markers):
                    problems.append(
                        "box style needs enough distinct dashes and flier markers"
                    )
                if any(marker not in MARKERS for marker in config.markers):
                    problems.append(
                        "box style requires registered native flier markers"
                    )
    styles = [layer.components] + [
        entry.components
        for entry in box_config(layer).hue_components or []
        if isinstance(entry, BoxHueComponentsSpec)
    ]
    for components in styles:
        if not isinstance(components, DistributionComponentsSpec):
            continue
        body, flier = components.body, components.flier
        if body is not None:
            if config.hue is not None and body.color is not None:
                problems.append("components.body.color cannot override mapped fill")
            if config.size is not None and body.line_width is not None:
                problems.append(
                    "components.body.line_width cannot override mapped stroke"
                )
            if config.style is not None and body.line_style is not None:
                problems.append(
                    "components.body.line_style cannot override mapped dashes"
                )
        if config.style is not None and flier is not None and flier.marker is not None:
            problems.append("components.flier.marker cannot override mapped glyph")
    return problems


def box_issues(columns, layer, panel, *, allow_empty=False):
    """Validate selected physical work before native artists/bootstrap allocation."""
    problems = box_option_issues(layer)
    if problems:
        return problems
    config = box_config(layer)
    category, value, hue = distribution_channels(layer)
    required = [name for name in (category, value, hue) if name is not None]
    required.extend(name for _, name in summary_columns(layer, optional=True))
    for name in required:
        if (
            not isinstance(name, str)
            or not name
            or name not in columns
            or not isinstance(columns[name], (list, tuple))
        ):
            problems.append(
                "box coordinate/summary references must name existing columns"
            )
    if problems:
        return problems
    if len({len(columns[name]) for name in required}) > 1:
        return ["box columns must have equal lengths"]
    rows = box_rows(columns, layer)
    if len(rows) > MAX_BOX_ROWS:
        return [f"advanced box supports at most {MAX_BOX_ROWS} selected source rows"]
    if not rows and not allow_empty:
        problems.append("no usable selected box observations")
    for name in (category, hue):
        if name is not None and any(
            not categorical(columns[name][row]) for row in rows
        ):
            problems.append("box categories/hues require nonempty finite scalars")
    if any(not finite_number(columns[value][row]) for row in rows):
        problems.append("box measurement/median values must be finite nonbool")
    if layer.semantics is not None:
        problems.extend(box_semantic_issues(columns, layer, panel))
    if problems:
        return problems
    _categories, groups, cells = distribution_plan(columns, layer, rows=rows)
    if len(cells) > MAX_BOX_CELLS:
        return [f"advanced box supports at most {MAX_BOX_CELLS} drawn samplecells"]
    entries = config.hue_components or []
    if entries:
        sem = layer.semantics
        if hue is None or (
            isinstance(sem, SemanticSpec)
            and sem.hue is not None
            and sem.hue_kind != "categorical"
        ):
            problems.append("per-hue components require a categorical effective hue")
        else:
            known = {_key(group["hue"]) for group in groups}
            if any(_key(entry.level) not in known for entry in entries):
                problems.append(
                    "per-hue component level must be observed or explicitly reserved"
                )
    summary = config.summary
    if isinstance(summary, BoxSummarySpec):
        if bool(summary.cilo) != bool(summary.cihi):
            problems.append("supplied CI requires both endpoint references")
        if any(len(cell["rows"]) != 1 for cell in cells):
            problems.append("supplied box samplecells must have one unique summary row")
        total_fliers = 0
        value_axis = (
            panel.x
            if layer.orient == "h"
            else (panel.y2 if layer.axis == "y2" else panel.y)
        )
        log_value = value_axis is not None and value_axis.scale == "log"
        for row in rows:
            ordered = [
                columns[getattr(summary, role)][row] for role in ("whislo", "q1")
            ]
            ordered += [columns[value][row]]
            ordered += [
                columns[getattr(summary, role)][row] for role in ("q3", "whishi")
            ]
            if any(not finite_number(v) for v in ordered) or any(
                a > b for a, b in itertools.pairwise(ordered)
            ):
                problems.append(
                    "supplied whiskers/quartiles/median must be finite and ordered"
                )
                continue
            if log_value and ordered[0] <= 0:
                problems.append(
                    "log summary whiskers/quartiles/median must be positive"
                )
            mean = None if summary.mean is None else columns[summary.mean][row]
            if mean is not None and not finite_number(mean):
                problems.append("supplied mean must be finite or unavailable")
            if layer.showmeans is True and mean is None:
                problems.append("requested summary mean is unavailable")
            if (
                log_value
                and layer.showmeans is True
                and finite_number(mean)
                and mean is not None
                and mean <= 0
            ):
                problems.append("requested log summary mean must be positive")
            low = None if summary.cilo is None else columns[summary.cilo][row]
            high = None if summary.cihi is None else columns[summary.cihi][row]
            if (low is None) != (high is None):
                problems.append("summary CI endpoints must be available together")
            elif low is not None and (
                not finite_number(low) or not finite_number(high) or low > high
            ):
                problems.append("summary CI endpoints must be finite and ordered")
            if layer.notch is True and (low is None or high is None):
                problems.append("requested summary confidence interval is unavailable")
            if (
                log_value
                and layer.notch is True
                and low is not None
                and finite_number(low)
                and low <= 0
            ):
                problems.append("requested log summary CI must be positive")
            fliers = None if summary.fliers is None else columns[summary.fliers][row]
            if fliers is not None:
                if not isinstance(fliers, (list, tuple)):
                    problems.append("declared fliers must be lists or unavailable")
                else:
                    total_fliers += len(fliers)
                    if total_fliers > MAX_BOX_FLIERS:
                        return [
                            f"box supports at most {MAX_BOX_FLIERS} total "
                            "declared flier values"
                        ]
                    if any(
                        not finite_number(v) or ordered[0] <= v <= ordered[-1]
                        for v in fliers
                    ):
                        problems.append(
                            "declared fliers must be finite strictly outside "
                            "closed whiskers"
                        )
                    if (
                        log_value
                        and layer.showfliers is not False
                        and any(finite_number(v) and v <= 0 for v in fliers)
                    ):
                        problems.append(
                            "requested log declared fliers must be positive"
                        )
            if layer.showfliers is True and fliers is None:
                problems.append("requested declared fliers are unavailable")
    return problems
