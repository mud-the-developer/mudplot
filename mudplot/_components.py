"""Pure contracts and duck-typed setters for named distribution components.

No optional import, arbitrary kwargs or callbacks. Setters run only on real
artists supplied by the renderer; validation and JSON remain dependency-free.
"""

from __future__ import annotations

import math
import re
from dataclasses import fields
from numbers import Real

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


def make_components(
    value: DistributionComponentsSpec | dict | None,
) -> DistributionComponentsSpec | None:
    if isinstance(value, dict):
        parsed = DistributionComponentsSpec.from_dict(value)
        if not isinstance(parsed, DistributionComponentsSpec):
            raise TypeError("components must be a distribution component object")
        return parsed
    return value


def component_issues(layer):
    components = layer.components
    if components is None:
        return []
    if not isinstance(components, DistributionComponentsSpec):
        return [
            "components must be a DistributionComponentsSpec (builder accepts dict)"
        ]
    supported = BOX_COMPONENTS if layer.type == "box" else BOXEN_COMPONENTS
    issues = []
    for role in BOX_COMPONENTS:
        style = getattr(components, role)
        if style is None:
            continue
        if role not in supported:
            issues.append(f"components.{role} is not supported for {layer.type}")
            continue
        if not isinstance(style, ComponentStyleSpec):
            issues.append(f"components.{role} must be a ComponentStyleSpec")
            continue
        allowed = (
            BODY_FIELDS
            if role == "body"
            else MARK_FIELDS
            if role in ("mean", "flier")
            else LINE_FIELDS
        )
        for field in fields(ComponentStyleSpec):
            value = getattr(style, field.name)
            if value is None:
                continue
            path = f"components.{role}.{field.name}"
            if field.name not in allowed:
                issues.append(f"{path} is not supported for {role}")
            elif field.name in ("color", "edge_color", "face_color"):
                if not _color(value):
                    issues.append(f"{path} requires hex/basic/cycle color")
            elif field.name in ("line_width", "marker_size", "marker_edge_width"):
                if (
                    not _finite(value)
                    or not 0 <= value <= 1000
                    or (field.name == "marker_size" and value == 0)
                ):
                    issues.append(
                        f"{path} must be finite in [0,1000] (marker_size positive)"
                    )
            elif field.name == "alpha":
                if not _finite(value) or not 0 <= value <= 1:
                    issues.append(f"{path} must be a finite fraction in [0,1]")
            elif field.name == "line_style":
                if not isinstance(value, str) or value not in (
                    "-",
                    "--",
                    ":",
                    "-.",
                    "none",
                ):
                    issues.append(f"{path} requires a named line style")
            elif field.name == "marker":
                if not isinstance(value, str) or value not in MARKERS:
                    issues.append(f"{path} requires a named marker")
            elif field.name == "hatch" and (
                not isinstance(value, str)
                or len(value) > 32
                or any(char not in "/\\|+-xXoO.*" for char in value)
            ):
                issues.append(f"{path} must be a bounded native hatch (empty disables)")
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
    return issues


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
        artist.set_linestyle(style.line_style)
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
