"""Pure contracts and duck-typed setters for named distribution components.

No optional import, arbitrary kwargs or callbacks. Setters run only on real
artists supplied by the renderer; validation and JSON remain dependency-free.
"""

from __future__ import annotations

import math
import re
from dataclasses import fields
from numbers import Real

from ._semantics import MARKERS as SEMANTIC_MARKERS
from .spec import ComponentStyleSpec, DistributionComponentsSpec

BOX_COMPONENTS = ("body", "whisker", "cap", "median", "mean", "flier")
BOXEN_COMPONENTS = ("body", "median", "flier")
LINE_FIELDS = {"color", "line_width", "line_style", "alpha"}
BODY_FIELDS = LINE_FIELDS | {"edge_color", "hatch"}
MARK_FIELDS = LINE_FIELDS | {
    "edge_color",
    "face_color",
    "marker",
    "marker_size",
    "marker_edge_width",
}
MARKERS = ("none", "o", "d", "D", "s", "^", "v", "+", "x", ".", "*")
VIOLIN_COMPONENT_MARKERS = (*MARKERS, "P", "X")
BOXEN_FLIER_MARKERS = (
    *MARKERS,
    *(marker for marker in SEMANTIC_MARKERS if marker not in MARKERS),
)
NAMED_COLORS = {
    "none",
    "black",
    "white",
    "red",
    "green",
    "blue",
    "yellow",
    "orange",
    "purple",
    "pink",
    "brown",
    "gray",
    "grey",
    "cyan",
    "magenta",
    "navy",
    "teal",
    "olive",
}


def _color(value):
    return isinstance(value, str) and (
        value in NAMED_COLORS
        or re.fullmatch(r"C[0-9]", value) is not None
        or re.fullmatch(
            r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value
        )
        is not None
    )


def _finite(value):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (ValueError, OverflowError):
        return False


def component_markers(layer_type):
    """Registered native component glyphs; not the filled semantic-cycle contract."""
    if layer_type == "boxenplot":
        return BOXEN_FLIER_MARKERS
    if layer_type == "violin":
        return VIOLIN_COMPONENT_MARKERS
    return MARKERS


def make_components(
    value: DistributionComponentsSpec | dict | None,
) -> DistributionComponentsSpec | None:
    if isinstance(value, dict):
        parsed = DistributionComponentsSpec.from_dict(value)
        if not isinstance(parsed, DistributionComponentsSpec):
            raise TypeError("components must be a distribution component object")
        return parsed
    return value


def merge_components(base, override):
    """Fieldwise native traits; omission inherits without mutating either spec."""
    if base is None:
        return override
    if override is None:
        return base
    from dataclasses import replace

    merged = {}
    for component in fields(DistributionComponentsSpec):
        current = getattr(base, component.name)
        changed = getattr(override, component.name)
        merged[component.name] = (
            current
            if changed is None
            else changed
            if current is None
            else replace(
                current,
                **{
                    prop.name: getattr(changed, prop.name)
                    for prop in fields(ComponentStyleSpec)
                    if getattr(changed, prop.name) is not None
                },
            )
        )
    return DistributionComponentsSpec(**merged)


def component_traits(layer):
    """Native traits of components that actually exist in this family/mode."""
    if layer.type == "violin":
        modes = {
            "legacy": {
                "mean": LINE_FIELDS,
                "median": LINE_FIELDS,
                "extrema": LINE_FIELDS,
            },
            "box": {"whisker": LINE_FIELDS, "box": LINE_FIELDS, "median": MARK_FIELDS},
            "quart": {"quartile": LINE_FIELDS},
            "point": {"point": MARK_FIELDS},
            "stick": {"stick": LINE_FIELDS},
            None: {},
        }
        mode = (
            layer.inner
            if layer.inner is None or isinstance(layer.inner, str)
            else False
        )
        return {"body": BODY_FIELDS, **modes.get(mode, {})}
    roles = (
        BOX_COMPONENTS
        if layer.type == "box"
        else (BOXEN_COMPONENTS if layer.type == "boxenplot" else ())
    )
    return {
        role: BODY_FIELDS
        if role == "body"
        else (MARK_FIELDS if role in ("mean", "flier") else LINE_FIELDS)
        for role in roles
    }


def component_issues(layer):
    components = layer.components
    if components is None:
        return []
    if not isinstance(components, DistributionComponentsSpec):
        return [
            "components must be a DistributionComponentsSpec (builder accepts dict)"
        ]
    traits = component_traits(layer)
    issues = []
    for component_field in fields(DistributionComponentsSpec):
        role = component_field.name
        style = getattr(components, role)
        if style is None:
            continue
        if role not in traits:
            issues.append(f"components.{role} is not supported for {layer.type}")
            continue
        issues.extend(
            style_issues(style, traits[role], f"components.{role}", layer.type)
        )
    if (
        components.mean is not None
        and layer.type == "box"
        and not (type(layer.showmeans) is bool and layer.showmeans)
    ):
        issues.append("components.mean requires showmeans=True")
    if components.flier is not None and (
        type(layer.showfliers) is bool and not layer.showfliers
    ):
        issues.append("components.flier requires visible fliers")
    if (
        components.median is not None
        and layer.type == "boxenplot"
        and type(layer.showmedians) is bool
        and not layer.showmedians
    ):
        issues.append("components.median requires visible medians")
    if layer.type == "violin" and layer.inner == "legacy":
        for role, flag in (
            ("mean", "showmeans"),
            ("median", "showmedians"),
            ("extrema", "showextrema"),
        ):
            if getattr(components, role) is not None and getattr(layer, flag) is False:
                issues.append(f"components.{role} conflicts with {flag}=False")
    return issues


def style_issues(style, allowed, prefix, layer_type):
    """Validate the one persisted native-style vocabulary for an actual mark."""
    if not isinstance(style, ComponentStyleSpec):
        return [f"{prefix} must be a ComponentStyleSpec"]
    issues = []
    for item in fields(ComponentStyleSpec):
        value = getattr(style, item.name)
        if value is None:
            continue
        path = f"{prefix}.{item.name}"
        if item.name not in allowed:
            issues.append(f"{path} is not supported for this mark")
        elif item.name in ("color", "edge_color", "face_color"):
            if not _color(value):
                issues.append(f"{path} requires hex/basic/cycle color")
        elif item.name in ("line_width", "marker_size", "marker_edge_width"):
            if (
                not _finite(value)
                or not 0 <= value <= 1000
                or (item.name == "marker_size" and value == 0)
            ):
                issues.append(
                    f"{path} must be finite in [0,1000] (marker_size positive)"
                )
        elif item.name == "alpha":
            if not _finite(value) or not 0 <= value <= 1:
                issues.append(f"{path} must be a finite fraction in [0,1]")
        elif item.name == "line_style":
            if not isinstance(value, str) or value not in (
                "-",
                "--",
                ":",
                "-.",
                "none",
            ):
                issues.append(f"{path} requires a named line style")
        elif item.name == "marker":
            if not isinstance(value, str) or value not in component_markers(layer_type):
                issues.append(f"{path} requires a named marker")
        elif item.name == "hatch" and (
            not isinstance(value, str)
            or len(value) > 32
            or any(char not in "/\\|+-xXoO.*" for char in value)
        ):
            issues.append(f"{path} must be a bounded native hatch (empty disables)")
    return issues


def set_component_linestyle(artist, value):
    """Canonical native no-stroke representation for lines and collections."""
    absent = value == "none"
    artist.set_linestyle("None" if absent else value)
    if absent and hasattr(artist, "get_paths"):
        # Collections have dash patterns but no Line2D no-line drawing switch.
        # Keep all paths/segments and independent fill, with zero actual stroke.
        artist.set_linewidth(0)


def finalize_component_stroke(artist, *, body=False):
    """Represent zero stroke natively without hiding independent marker/fill."""
    widths = artist.get_linewidth()
    zero = widths == 0 if isinstance(widths, Real) else all(v == 0 for v in widths)
    if zero:
        artist.set_linestyle("solid" if body else "None")


def apply_component_style(artist, style, *, body=False, include_color=True):
    if style is None:
        return
    if include_color and style.color is not None:
        (artist.set_facecolor if body else artist.set_color)(style.color)
    if style.edge_color is not None:
        (artist.set_edgecolor if body else artist.set_markeredgecolor)(style.edge_color)
    if style.face_color is not None:
        artist.set_markerfacecolor(style.face_color)
    if style.line_width is not None:
        artist.set_linewidth(style.line_width)
    if style.line_style is not None:
        set_component_linestyle(artist, style.line_style)
    if style.marker is not None:
        artist.set_marker(style.marker)
    if style.marker_size is not None:
        artist.set_markersize(style.marker_size)
    if style.marker_edge_width is not None:
        artist.set_markeredgewidth(style.marker_edge_width)
    if style.alpha is not None:
        artist.set_alpha(style.alpha)
    if style.hatch is not None:
        artist.set_hatch(style.hatch)
    finalize_component_stroke(artist, body=body)
