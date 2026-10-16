"""Render-only Gaussian KDE profiles, normalization and native violin artists.

No SciPy, RNG or sampling. Defaults use the old Matplotlib path; this module is
loaded only by the extended violin renderer. Clipping limits KDE support, not
fitting data or observations/summaries in the inner marks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.mlab import GaussianKDE

from ._ecdf import empirical_steps, finite_number
from ._kde import kde_summary
from ._violin_options import MAX_INNER_OBSERVATIONS
from .spec import KDESpec, LayerSpec


@dataclass(frozen=True)
class ViolinCell:
    observations: np.ndarray
    support: np.ndarray
    density: np.ndarray
    profile: np.ndarray
    bandwidth: float
    singular: bool
    weights: np.ndarray | None = None


def density_cell(
    values,
    *,
    weights=None,
    bw_method=None,
    bw_adjust=None,
    points=None,
    cut=None,
    clip=None,
):
    if weights is not None:
        return _weighted_density_cell(
            values,
            weights,
            bw_method=bw_method,
            bw_adjust=bw_adjust,
            points=points,
            cut=cut,
            clip=clip,
        )
    data = np.asarray(values, dtype=float)
    low, high = float(data.min()), float(data.max())
    singular = low == high
    if singular:
        bandwidth = 0.0
        support = np.repeat(low, 2 if points is None else points)
        density = np.ones(len(support))
        if clip is not None and (
            (clip[0] is not None and low < clip[0])
            or (clip[1] is not None and low > clip[1])
        ):
            raise ValueError(
                "violin clip does not intersect the observed singleton/constant"
            )
    else:
        if bw_method in (None, "scott"):
            factor = len(data) ** -0.2
        elif bw_method == "silverman":
            factor = (len(data) * 0.75) ** -0.2
        else:
            factor = float(bw_method)
        adjust = 1.0 if bw_adjust is None else bw_adjust
        try:
            kde = GaussianKDE(data, bw_method=factor * adjust)
        except (ValueError, np.linalg.LinAlgError, OverflowError) as exc:
            raise ValueError(
                "violin KDE cannot resolve finite bandwidth for these observations"
            ) from exc
        bandwidth = float(np.sqrt(np.asarray(kde.covariance)[0, 0]))
        if not np.isfinite(bandwidth) or bandwidth <= 0:
            raise ValueError("violin bandwidth must be positive and finite")
        extension = (0.0 if cut is None else cut) * bandwidth
        low, high = low - extension, high + extension
        if clip is not None:
            low = low if clip[0] is None else max(low, clip[0])
            high = high if clip[1] is None else min(high, clip[1])
        if not np.isfinite(low) or not np.isfinite(high) or low >= high:
            raise ValueError("violin KDE support is empty/nonfinite after cut/clip")
        # Convex interpolation does not overflow in high-low for finite extremes.
        t = np.linspace(0, 1, 100 if points is None else points)
        support = low * (1 - t) + high * t
        density = kde.evaluate(support)
        if not np.all(np.isfinite(density)) or density.max() <= 0:
            raise ValueError("violin KDE requires finite positive density")
    return ViolinCell(
        data, support, density, density / density.max(), bandwidth, singular
    )


def _weighted_density_cell(values, weights, **options):
    if len(values) != len(weights):
        raise ValueError("violin weights must match observation length")
    if not all(finite_number(w) and w >= 0 for w in weights):
        raise ValueError("violin weights must be finite nonnegative, not bool")
    pairs = [(v, w) for v, w in zip(values, weights, strict=True) if w > 0]
    if not pairs or len(pairs) > MAX_INNER_OBSERVATIONS:
        raise ValueError("weighted violin needs 1..10000 usable observations")
    if not all(finite_number(v) for v, _ in pairs):
        raise ValueError("weighted violin observations must be finite numbers")
    data = np.asarray([v for v, _ in pairs], dtype=float)
    mass = np.asarray([w for _, w in pairs], dtype=float)
    if data.min() == data.max():
        # Observed point mass: retain the legacy degenerate body, not a Gaussian.
        return replace(density_cell(data, **options), weights=mass)
    config = KDESpec(
        weights="w",
        common_norm=False,
        bw_method="scott" if options["bw_method"] is None else options["bw_method"],
        bw_adjust=1 if options["bw_adjust"] is None else options["bw_adjust"],
        gridsize=100 if options["points"] is None else options["points"],
        cut=0 if options["cut"] is None else options["cut"],
        clip=options["clip"],
    )
    curve = kde_summary(
        {"v": data.tolist(), "w": mass.tolist()},
        LayerSpec(type="kde", x="v", kde=config),
    )[0]
    density = np.asarray(curve.heights)
    if not density.size or density.max() <= 0:
        raise ValueError("weighted violin needs resolvable positive density")
    assert curve.bandwidth is not None
    return ViolinCell(
        data,
        np.asarray(curve.support),
        density,
        density / density.max(),
        curve.bandwidth,
        False,
        mass,
    )


def _quartiles(cell):
    if cell.weights is None:
        return np.percentile(cell.observations, [25, 50, 75])
    knots, cumulative = empirical_steps(cell.observations, cell.weights)
    return np.asarray(knots)[np.searchsorted(cumulative, [0.25, 0.5, 0.75])]


def _mean(cell):
    data = cell.observations
    if cell.weights is None:
        return float(np.sum(data / len(data)))
    scale = float(np.max(np.abs(data))) or 1.0
    mass = cell.weights / cell.weights.max()
    probabilities = mass / math.fsum(mass.tolist())
    anchor = float(data.min())
    if math.isfinite(float(data.max()) - anchor):
        offsets = [(float(v) - anchor) / scale for v in data]
        return (
            anchor
            + math.fsum(p * v for p, v in zip(probabilities, offsets, strict=True))
            * scale
        )
    return (
        math.fsum(
            p * (float(v) / scale) for p, v in zip(probabilities, data, strict=True)
        )
        * scale
    )


def _count_ratio(cell, comparison):
    if cell.weights is None:
        return len(cell.observations) / max(len(c.observations) for c in comparison)
    scale = max(float(c.weights.max()) for c in comparison)
    masses = [math.fsum((c.weights / scale).tolist()) for c in comparison]
    own = math.fsum((cell.weights / scale).tolist())
    ratio = own / max(masses)
    if ratio <= 0:
        raise ValueError("weighted violin count mass ratio is not representable")
    return ratio


def prepare_violin(cells, layer, *, log_value=False, weights=None):
    """Fit all cells before normalization; references are per hue or global."""
    clip = layer.clip
    if clip is not None:
        clip = [None if v is None else np.log10(v) if log_value else v for v in clip]
    profiles = {}
    for group, categories in cells.items():
        for category, values in categories.items():
            data = np.log10(values) if log_value else values
            profiles[group, category] = density_cell(
                data,
                weights=None if weights is None else weights[group][category],
                bw_method=layer.bw_method,
                bw_adjust=layer.bw_adjust,
                points=layer.points,
                cut=layer.cut,
                clip=clip,
            )
    references = {}
    for key, cell in profiles.items():
        refkey = None if layer.common_norm else key[0]
        references.setdefault(refkey, []).append(cell)
    for key, cell in list(profiles.items()):
        comparison = references[None if layer.common_norm else key[0]]
        if layer.density_norm == "count":
            ratio = _count_ratio(cell, comparison)
            profile = cell.profile * ratio
        elif layer.density_norm == "area" and not cell.singular:
            peak = max(c.density.max() for c in comparison if not c.singular)
            profile = cell.density / peak
        else:
            # Point masses have no finite KDE height/area: a degenerate native body.
            profile = cell.profile
        profiles[key] = replace(cell, profile=profile)
    return profiles


def violin_artists(ax, contexts, positions, width, layer):
    """Filled native collections, plus deterministic native inner lines/markers."""
    horizontal = layer.orient == "h"
    width = 0.5 if width is None else width  # legacy one-column violin default
    color = layer.edge_color or "#4b5563"
    linewidth = 0.8 if layer.line_width is None else layer.line_width
    linestyle = "-" if layer.line_style is None else layer.line_style
    marker = layer.marker or "o"
    markersize = 3 if layer.marker_size is None else layer.marker_size
    bodies = []

    def lines(segments, *, thick=1):
        if horizontal:
            segments = [np.asarray(s)[:, ::-1] for s in segments]
        collection = LineCollection(
            segments,
            colors=color,
            linewidths=linewidth * thick,
            linestyles=linestyle,
            label="_nolegend_",
        )
        ax.add_collection(collection)

    def points(categories, observations, *, white=False):
        x, y = (observations, categories) if horizontal else (categories, observations)
        ax.plot(
            x,
            y,
            linestyle="none",
            marker=marker,
            markersize=markersize,
            markerfacecolor="white" if white else color,
            markeredgecolor=color,
            markeredgewidth=linewidth,
            label="_nolegend_",
        )

    for center, (cell, side) in zip(positions, contexts, strict=True):
        half = width / 2 * cell.profile
        lower = center - half if side <= 0 else np.full(len(half), center)
        upper = center + half if side >= 0 else np.full(len(half), center)
        draw = ax.fill_between if horizontal else ax.fill_betweenx
        bodies.append(draw(cell.support, lower, upper))
        data = cell.observations
        # Split box/points sit inside their own half, not on the shared seam.
        inner_center = center + side * width * cell.profile.max() / 4

        def span(values, *, cell=cell, half=half, center=center, side=side):
            sizes = np.interp(values, cell.support, half, left=0, right=0)
            left = center - sizes if side <= 0 else np.repeat(center, len(sizes))
            right = center + sizes if side >= 0 else np.repeat(center, len(sizes))
            return [
                ((lo, value), (hi, value))
                for lo, hi, value in zip(left, right, values, strict=True)
            ]

        if layer.inner is None:
            continue
        if layer.inner == "point":
            points(np.repeat(inner_center, len(data)), data)
        elif layer.inner == "stick":
            lines(span(data))
        elif layer.inner == "quart":
            lines(span(_quartiles(cell)))
        elif layer.inner == "box":
            q1, median, q3 = _quartiles(cell)
            inside = data[
                (data >= q1 - 1.5 * (q3 - q1)) & (data <= q3 + 1.5 * (q3 - q1))
            ]
            whislo, whishi = min(q1, inside.min()), max(q3, inside.max())
            lines([((inner_center, whislo), (inner_center, whishi))])
            lines([((inner_center, q1), (inner_center, q3))], thick=3)
            points([inner_center], [median], white=True)
        else:  # legacy explicit mean/median/extrema on an extended density
            if layer.showmeans:
                lines(span([_mean(cell)]))
            if layer.showextrema:
                lines(span([data.min(), data.max()]))
                lines([((inner_center, data.min()), (inner_center, data.max()))])
            if layer.showmedians is None or layer.showmedians:
                median = (
                    float(np.median(data))
                    if cell.weights is None
                    else _quartiles(cell)[1]
                )
                lines(span([median]))
    return bodies
