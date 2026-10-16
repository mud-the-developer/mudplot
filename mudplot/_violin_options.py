"""Pure, serializable contracts for the extended violin subset."""

from __future__ import annotations

import math
from numbers import Real

INNER_STYLES = ("legacy", "box", "quart", "point", "stick")
DENSITY_NORMALIZATIONS = ("width", "area", "count")
MAX_INNER_OBSERVATIONS = 10000
MARKERS = ("o", "d", "D", "s", "^", "v", "+", "x", ".", "*")


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
            not isinstance(layer.marker, str) or layer.marker not in MARKERS
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
