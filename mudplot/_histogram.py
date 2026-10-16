"""Pure weighted-row contracts plus lazy numeric shared-bin histogram effects."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import chain

from ._ecdf import _cumulative, ecdf_groups, ecdf_rows
from .spec import ECDFSpec, HistogramSpec, LayerSpec

HISTOGRAM_STATS = (
    "count",
    "frequency",
    "probability",
    "proportion",
    "percent",
    "density",
)
HISTOGRAM_MULTIPLES = ("layer", "stack", "dodge")
HISTOGRAM_ELEMENTS = ("bars", "step")
NORMALIZED_STATS = ("probability", "proportion", "percent", "density")
MAX_HISTOGRAM_BINS = 10_000


def histogram_rows(columns: dict, layer: LayerSpec) -> list[int]:
    if not isinstance(layer.histogram, HistogramSpec):
        return []
    proxy = replace(layer, ecdf=ECDFSpec(weights=layer.histogram.weights))
    return ecdf_rows(columns, proxy)


def histogram_groups(columns: dict, layer: LayerSpec, rows: list[int]) -> list:
    return ecdf_groups(columns, layer, rows)


@dataclass(frozen=True)
class HistogramCurve:
    group: object
    heights: tuple[float, ...]  # empty reserves a hue slot without fake bars


@dataclass(frozen=True)
class HistogramResult:
    edges: tuple[float, ...]
    curves: tuple[HistogramCurve, ...]


def _mass(values) -> float:
    try:
        total = math.fsum(values)
    except OverflowError as exc:
        raise ValueError("histogram raw mass exceeds finite range") from exc
    if not math.isfinite(total):
        raise ValueError("histogram raw mass exceeds finite range")
    return total


def histogram_summary(columns: dict, layer: LayerSpec) -> HistogramResult:
    """Compute before drawing, independently of Matplotlib hist normalization.

    Half-open [left,right) bins except the closed final edge. Weights stay
    paired with selected rows. Automatic equal-width edges pool usable rows;
    explicit edges exclude out-of-range mass from every denominator.
    """
    import numpy as np

    config = layer.histogram
    if not isinstance(config, HistogramSpec):
        raise ValueError("histogram_summary requires HistogramSpec")
    rows = histogram_rows(columns, layer)
    groups = histogram_groups(columns, layer, rows)
    if not rows:
        return HistogramResult((), tuple(HistogramCurve(g, ()) for g in groups))
    values = np.asarray([columns[layer.x][i] for i in rows], dtype=float)
    try:
        with np.errstate(over="ignore", invalid="ignore"):
            if type(layer.bins) is int:
                edges = np.histogram_bin_edges(values, bins=layer.bins)
            else:
                edges = np.asarray(layer.bins, dtype=float)
            widths = np.diff(edges)
    except (ValueError, OverflowError) as exc:
        raise ValueError(
            "cannot derive finite histogram bin edges; provide edges"
        ) from exc
    if (
        np.any(~np.isfinite(edges))
        or np.any(~np.isfinite(widths))
        or np.any(widths <= 0)
    ):
        raise ValueError("derived histogram edges/widths must be finite increasing")
    indexes = np.searchsorted(edges, values, side="right") - 1
    indexes[values == edges[-1]] = len(widths) - 1
    grouped = {group: [] for group in groups}
    for row, index in zip(rows, indexes, strict=True):
        if not 0 <= index < len(widths):
            continue
        group = None if layer.group is None else columns[layer.group][row]
        weight = 1.0 if config.weights is None else float(columns[config.weights][row])
        grouped[group].append((int(index), weight))
    normalized = config.stat in NORMALIZED_STATS
    pooled = list(chain.from_iterable(grouped.values()))
    common_scale = max((weight for _, weight in pooled), default=1.0)
    common_total = math.fsum(weight / common_scale for _, weight in pooled)
    curves = []
    for group in groups:
        pairs = grouped[group]
        if not pairs:
            curves.append(HistogramCurve(group, ()))
            continue
        if normalized:
            scale = common_scale if config.common_norm else max(w for _, w in pairs)
            total = (
                common_total
                if config.common_norm
                else math.fsum(w / scale for _, w in pairs)
            )
        else:
            scale = 1.0
            total = _mass(weight for _, weight in pairs)
        buckets: list[list[float]] = [[] for _ in widths]
        for index, weight in sorted(pairs):
            buckets[index].append(weight / scale)
        if config.cumulative:
            # Do not round bin subtotals before prefixes: the ECDF expansion
            # preserves all row low bits, preventing nonmonotone binned CDFs.
            prefixes = _cumulative(list(chain.from_iterable(buckets)))
            cursor = 0
            mass = []
            for bucket in buckets:
                cursor += len(bucket)
                mass.append(prefixes[cursor - 1] if cursor else 0.0)
        else:
            mass = [math.fsum(bucket) for bucket in buckets]
        heights = np.asarray(mass, dtype=float)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            if normalized:
                heights /= total
                if config.stat == "percent":
                    heights *= 100.0
                elif config.stat == "density" and not config.cumulative:
                    heights /= widths
            elif config.stat == "frequency":
                heights /= widths
        if np.any(~np.isfinite(heights)) or np.any(heights < 0):
            raise ValueError("derived histogram heights must be finite nonnegative")
        curves.append(HistogramCurve(group, tuple(heights.tolist())))
    return HistogramResult(tuple(edges.tolist()), tuple(curves))
