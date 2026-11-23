"""Pure, serializable contracts for the extended violin subset."""

from __future__ import annotations

import math
from dataclasses import replace
from numbers import Real

from ._categorical import (
    distribution_channels,
    distribution_columns,
    distribution_plan,
    sample_rows,
)
from ._components import component_issues, merge_components
from ._semantics import MARKERS as SEMANTIC_MARKERS
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
    DistributionComponentsSpec,
    SemanticSpec,
    ViolinHueComponentsSpec,
    ViolinSpec,
)

INNER_STYLES = ("legacy", "box", "quart", "point", "stick")
DENSITY_NORMALIZATIONS = ("width", "area", "count")
MAX_INNER_OBSERVATIONS = 10000
MARKERS = ("o", "d", "D", "s", "^", "v", "+", "x", ".", "*")
MAX_VIOLIN_PROFILES = 256
VIOLIN_DASHES = ("-", "--", ":", "-.")


def advanced_violin(layer):
    return layer.type == "violin" and (
        layer.violin is not None
        or layer.semantics is not None
        or layer.components is not None
        or layer.axis == "y2"
        or layer.line_style == "none"
        or (
            isinstance(layer.marker, str)
            and layer.marker in SEMANTIC_MARKERS
            and layer.marker not in MARKERS
        )
    )


def violin_config(layer):
    return layer.violin if isinstance(layer.violin, ViolinSpec) else ViolinSpec()


def violin_hues(columns, layer, rows):
    """Effective hue slots, independent of size/style tuple partitioning."""
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


def merged_violin_components(layer, hue):
    result = layer.components
    if hue is None:
        return result
    for entry in violin_config(layer).hue_components or []:
        if category_key(entry.level) == category_key(hue):
            result = merge_components(result, entry.components)
    return result


def _finite(value):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (ValueError, OverflowError):
        return False


def extended_violin(layer):
    return (
        layer.weights is not None
        or layer.inner != "legacy"
        or layer.split
        or layer.density_norm != "width"
        or layer.common_norm
        or layer.bw_adjust is not None
        or layer.cut is not None
        or layer.clip is not None
    )


def option_issues(layer):
    issues = []
    if layer.inner is not None and not (
        isinstance(layer.inner, str) and layer.inner in INNER_STYLES
    ):
        issues.append("inner must be legacy, box, quart, point, stick or None")
    if (
        not isinstance(layer.density_norm, str)
        or layer.density_norm not in DENSITY_NORMALIZATIONS
    ):
        issues.append("density_norm must be width, area or count")
    for name in ("split", "common_norm"):
        if type(getattr(layer, name)) is not bool:
            issues.append(f"{name} must be boolean")
    if (
        type(layer.common_norm) is bool
        and layer.common_norm
        and isinstance(layer.density_norm, str)
        and layer.density_norm == "width"
    ):
        issues.append("common_norm requires density_norm='area' or 'count'")
    if (not isinstance(layer.inner, str) or layer.inner != "legacy") and any(
        getattr(layer, name) is not None
        for name in ("showmeans", "showmedians", "showextrema")
    ):
        issues.append("showmeans/showmedians/showextrema require inner='legacy'")
    if (
        type(layer.split) is bool
        and layer.split
        and layer.dodge is not None
        and not (_finite(layer.dodge) and layer.dodge == 0)
    ):
        issues.append("split requires automatic/zero dodge (shared category center)")
    if layer.bw_adjust is not None and (
        not _finite(layer.bw_adjust) or not 0 < layer.bw_adjust <= 1000
    ):
        issues.append("bw_adjust must be finite in (0,1000]")
    if layer.cut is not None and (not _finite(layer.cut) or not 0 <= layer.cut <= 10):
        issues.append("cut must be finite in [0,10] bandwidth units")
    if layer.clip is not None:
        valid = isinstance(layer.clip, (list, tuple)) and len(layer.clip) == 2
        if valid:
            lo, hi = layer.clip
            valid = all(v is None or _finite(v) for v in (lo, hi))
            if valid and lo is not None and hi is not None:
                valid = lo < hi
        if not valid:
            issues.append("clip must be [lower,upper] finite increasing bounds or None")
    if layer.marker is not None or layer.marker_size is not None:
        if not (isinstance(layer.inner, str) and layer.inner in ("box", "point")):
            issues.append("marker/marker_size require inner='box' or 'point'")
        if layer.marker is not None and (
            not isinstance(layer.marker, str)
            or layer.marker not in (*MARKERS, *SEMANTIC_MARKERS)
        ):
            issues.append("unsupported violin inner marker")
    for name in ("line_width", "marker_size"):
        number = getattr(layer, name)
        if number is not None and (
            not _finite(number)
            or not 0 <= number <= 1000
            or (name == "marker_size" and number == 0)
        ):
            issues.append(f"{name} must be finite <=1000 (marker_size positive)")
    return issues


def advanced_option_issues(layer):
    issues = option_issues(layer)
    if layer.violin is not None and not isinstance(layer.violin, ViolinSpec):
        return [*issues, "violin must be a ViolinSpec"]
    config = violin_config(layer)
    if config.split_policy not in (None, "paired"):
        issues.append("violin split_policy must be paired or None")
    if config.split_policy is not None and layer.split is not True:
        issues.append("paired split_policy requires split=True")
    if issues:
        return issues
    issues.extend(component_issues(layer))
    entries = config.hue_components
    if entries is not None:
        if not isinstance(entries, (list, tuple)) or len(entries) > MAX_LEVELS:
            return [*issues, "violin hue_components needs at most64 typed entries"]
        seen = set()
        for entry in entries:
            if (
                not isinstance(entry, ViolinHueComponentsSpec)
                or not categorical(entry.level)
                or not isinstance(entry.components, DistributionComponentsSpec)
            ):
                issues.append(
                    "violin hue_components needs raw scalar level and typed components"
                )
                continue
            key = category_key(entry.level)
            if key in seen:
                issues.append("violin hue_components levels must be unique typed keys")
            seen.add(key)
            issues.extend(component_issues(replace(layer, components=entry.components)))
    return issues


def violin_semantic_issues(columns, layer, panel):
    config = layer.semantics
    issues = semantic_option_issues(config)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    _, _, legacy_hue = distribution_columns(layer)
    if layer.c is not None or (
        config.hue is not None
        and (legacy_hue is not None or layer.hue_order is not None)
    ):
        issues.append("mapped violin hue cannot combine with independent legacy hue/c")
    if panel.projection != "2d":
        issues.append("violin semantics require Cartesian2D")
    for role, name in (
        ("hue", "color"),
        ("size", "line_width"),
        ("style", "line_style"),
    ):
        if getattr(config, role) is not None and getattr(layer, name) is not None:
            issues.append(f"{name} cannot override mapped violin body {role}")
    glyphs = layer.inner in ("point", "box")
    if config.style is not None and glyphs and layer.marker is not None:
        issues.append("marker cannot override mapped violin inner glyph")
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if numeric_hue and layer.cmap_kind not in ("sequential", "diverging"):
        issues.append("numeric violin hue requires registered colormap kind")
    if not numeric_hue and (
        layer.colorbar or layer.clabel is not None or layer.cmap_kind != "sequential"
    ):
        issues.append("violin colorbar/colormap requires numeric hue")
    if type(layer.colorbar) is not bool:
        issues.append("violin colorbar must be boolean")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append("violin clabel requires colorbar and bounded text")
    rows = sample_rows(columns, layer)
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        if not isinstance(name, str) or name not in columns:
            issues.append(f"violin semantic {role} column must exist")
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        values = [columns[name][row] for row in rows]
        if kind == "numeric":
            if any(not _finite(value) for value in values):
                issues.append(f"violin numeric {role} must be finite nonbool")
            elif values:
                try:
                    numeric_mapping(values, getattr(config, role + "_norm"))
                except ValueError as error:
                    issues.append(str(error))
        elif any(not categorical(value) for value in values):
            issues.append(f"violin {role} needs nonempty finite categorical levels")
        else:
            selected = semantic_levels(columns, config, role, rows)
            if len(selected) > MAX_LEVELS or len(
                {str(value) for value in selected}
            ) != len(selected):
                issues.append(
                    f"violin categorical {role} has too many/ambiguous levels"
                )
            if role == "style":
                if len(selected) > len(config.dashes or VIOLIN_DASHES):
                    issues.append("violin style needs enough distinct body dashes")
                if glyphs and (
                    len(selected) > len(config.markers)
                    or any(marker not in SEMANTIC_MARKERS for marker in config.markers)
                ):
                    issues.append(
                        "violin style needs enough registered actual inner glyphs"
                    )
    components = [layer.components] + [
        entry.components
        for entry in violin_config(layer).hue_components or []
        if isinstance(entry, ViolinHueComponentsSpec)
    ]
    for styles in components:
        if not isinstance(styles, DistributionComponentsSpec):
            continue
        body = styles.body
        if body is not None:
            for role, name in (
                ("hue", "color"),
                ("size", "line_width"),
                ("style", "line_style"),
            ):
                if (
                    getattr(config, role) is not None
                    and getattr(body, name) is not None
                ):
                    issues.append(
                        f"components.body.{name} conflicts with mapped violin {role}"
                    )
        mark = (
            styles.point
            if layer.inner == "point"
            else styles.median
            if layer.inner == "box"
            else None
        )
        if config.style is not None and mark is not None and mark.marker is not None:
            issues.append("inner component marker conflicts with mapped violin glyph")
    return issues


def violin_issues(columns, layer, panel, *, allow_empty=False):
    issues = advanced_option_issues(layer)
    if issues:
        return issues
    if panel.projection != "2d":
        issues.append("advanced violin requires Cartesian2D")
    category, value, hue = distribution_channels(layer)
    config = layer.semantics
    if config is not None:
        issues.extend(violin_semantic_issues(columns, layer, panel))
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
        return [*issues, "violin required columns must exist"]
    if any(not isinstance(columns[name], (list, tuple)) for name in required):
        return [*issues, "violin columns must be arrays"]
    if len({len(columns[name]) for name in required}) > 1:
        return [*issues, "violin columns must have equal lengths"]
    rows = sample_rows(columns, layer)
    if len(rows) > MAX_INNER_OBSERVATIONS:
        return [*issues, "advanced violin selected source rows exceed10000"]
    if not rows and not allow_empty:
        issues.append(
            "no usable advanced violin observations after selection/missing exclusion"
        )
    if any(not _finite(columns[value][row]) for row in rows):
        issues.append("violin observations must be finite nonbool")
    if layer.weights is not None and any(
        not _finite(columns[layer.weights][row]) or columns[layer.weights][row] < 0
        for row in rows
    ):
        issues.append("violin weights must be finite nonnegative nonbool")
    if any(
        name is not None and any(not categorical(columns[name][row]) for row in rows)
        for name in (category, hue)
    ):
        issues.append("violin category/hue needs nonempty finite scalars")
    if issues:
        return issues
    categories, _, cells = distribution_plan(columns, layer, rows=rows)
    if len(cells) > MAX_VIOLIN_PROFILES:
        issues.append("advanced violin drawn profiles exceed256")
    hues = violin_hues(columns, layer, rows)
    if len(categories) > MAX_LEVELS:
        issues.append("violin category levels exceed64")
    numeric_hue = (
        isinstance(config, SemanticSpec)
        and config.hue is not None
        and config.hue_kind == "numeric"
    )
    if not numeric_hue and len(hues) > MAX_LEVELS:
        issues.append("violin categorical hue levels exceed64")
    if layer.split:
        if hue is None or numeric_hue:
            issues.append("split violin requires an independent categorical hue")
        elif violin_config(layer).split_policy is None and len(hues) != 2:
            issues.append(
                "legacy split violin requires exactly two selected hue levels"
            )
    entries = violin_config(layer).hue_components or []
    if entries and (hue is None or numeric_hue):
        issues.append("violin per-hue components require independent categorical hue")
    known = {category_key(item) for item in hues if item is not None}
    for entry in entries:
        if category_key(entry.level) not in known:
            issues.append("violin component hue level is not in declared hue domain")
    return issues
