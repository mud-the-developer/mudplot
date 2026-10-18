"""Render a FigureSpec into a matplotlib Figure.

Pure-ish function: given the same spec it produces the same figure. All
matplotlib-specific logic lives here; the spec itself stays backend-agnostic.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import inspect
import itertools
import re
import warnings
from dataclasses import replace
from statistics import NormalDist
from typing import Any, cast

try:
    import numpy as np
except ModuleNotFoundError as error:
    if error.name != "numpy":
        raise
    raise ImportError("rendering requires NumPy; install 'mudplot[render]'") from error

from ._categorical import (
    DISTRIBUTION_TYPES,
    distribution_columns,
    distribution_levels,
    distribution_rows,
    native_category_geometry,
)
from ._ecdf import ecdf_config, ecdf_groups, ecdf_rows, empirical_steps
from ._facet import RAW_HUE_TYPES, ordered_group_columns, panel_columns
from ._histogram import histogram_groups, histogram_rows, histogram_summary
from ._kde import kde_groups, kde_rows, kde_summary
from ._kde2d import kde2d_config, kde2d_groups, kde2d_rows, kde2d_summary
from ._mpl_context import matplotlib_context
from ._semantics import (
    category_key,
    semantic_levels,
    semantic_rows,
    shared_scale_domains,
)
from ._stat import STAT_LAYER_TYPES, category_levels, stat_config, usable_rows
from .spec import FigureSpec, LayerSpec, PanelSpec
from .theme import spec_to_rcparams
from .validate import assert_valid

__all__ = ["render", "save"]

# layer types that draw one or more x/y series (and support ``group``)
_SERIES_TYPES = {
    "line",
    "regplot",
    "scatter",
    "stripplot",
    "stackplot",
    "hist2d",
    "hexbin",
    "quiver",
    "bar",
    "errorbar",
    "band",
}
_STAT_TYPES = STAT_LAYER_TYPES
# layer types that draw a distribution of a single column (support ``group``)
_DIST_TYPES = {"hist", "box", "boxenplot", "violin", "kde", "kde2d", "ecdf", "rug"}
# layer types that draw a 2-D matrix
_MATRIX_TYPES = {"heatmap", "clustermap", "contour", "contourf"}
# layer types only meaningful on a projection="3d" panel
_3D_TYPES = {"scatter3d", "line3d", "surface", "wireframe"}
# layer types with their own standalone drawing logic
_STANDALONE_TYPES = {"pie", "swarmplot"}

# -- reference metadata (citation / href) ----------------------------------
#
# A figure's legend entries and title can carry a BibTeX key and/or a URL.
# How that renders depends on the output format, so the active format is a
# render-time context rather than part of the (backend-agnostic) spec:
#
#   raster (png/pdf/...) -> plain text, references dropped
#   svg                  -> the text becomes a clickable link (href only)
#   pgf                  -> real \figcite{key} / \href{url}{...} macros, so
#                           the *paper's* bibliography and hyperref resolve
#                           them at compile time (see mudplot.tex.PREAMBLE)
#
# PGF text follows matplotlib's trusted TeX rules, not universal plain-text escaping.
# Reference macros belong to the document, so measure short sentinels and substitute
# them in the saved .pgf afterwards (see _substitute_pgf_references).
_FMT: contextvars.ContextVar[str] = contextvars.ContextVar("mudplot_fmt", default="")
# Markers must stay *short*: they sit in the text matplotlib measures while
# laying the figure out, so embedding a full URL there blows up the legend
# box (and can collapse the axes to zero size). Each marker is a small index
# into a per-render table instead, and its width stands in for the "[12]"
# the citation eventually renders as.
_REFS: contextvars.ContextVar[list[tuple[str, str]] | None] = contextvars.ContextVar(
    "mudplot_refs", default=None
)
# WYSIWYG layout for a citation is only exact for compact/numeric styles
# (e.g. "[12]"): the marker above stands in for that by default. Set
# FigureSpec.reference_measure_text to a representative example of your
# actual citation style (e.g. "(Fischler and Bolles, 1981)") to measure
# against *that* width instead -- see mudplot_v0.3_improvement_and_
# reference_repos.md P0-3. The text is stripped back out at PGF
# substitution time (see _substitute_pgf_references) and never emitted.
_REF_MEASURE: contextvars.ContextVar[str] = contextvars.ContextVar(
    "mudplot_ref_measure", default=""
)
# Plain ASCII (backtick/straight-quote), not guillemets: the previous
# choice («/») rendered fine under xelatex/lualatex (native Unicode text),
# but every real TeX install this was ever actually tested against also
# happened to default matplotlib's pgf.texsystem to one of those two --
# pdflatex's default OT1 font encoding has no guillemet glyph at all
# ("Command \guillemetleft unavailable in encoding OT1"), which a CI run
# exercising pdflatex for the first time caught immediately. Backtick/quote
# are plain 7-bit ASCII: present, unescaped, and require no fontenc/inputenc
# setup under OT1, T1, or full Unicode alike -- and, like the guillemets
# before them, aren't one of LaTeX's catcode-special characters, so pgf's
# own text escaping leaves them alone.
_MARK_OPEN, _MARK_CLOSE = "`", "'"
_PGF_REF_RE = re.compile(re.escape(_MARK_OPEN) + r"(\d+)" + re.escape(_MARK_CLOSE))


@contextlib.contextmanager
def _render_format(fmt: str, measure_text: str = ""):
    fmt_token = _FMT.set(fmt)
    refs_token = _REFS.set([])
    measure_token = _REF_MEASURE.set(measure_text)
    try:
        yield
    finally:
        _FMT.reset(fmt_token)
        _REFS.reset(refs_token)
        _REF_MEASURE.reset(measure_token)


def _mark(kind: str, value: str, *, widen: bool = False) -> str:
    refs = _REFS.get()
    assert refs is not None
    refs.append((kind, value))
    idx = len(refs) - 1
    # Only a citation's *rendered* width is uncertain (an href's URL never
    # appears in the visible text -- only the label it wraps does), so only
    # "cite" markers ever ask for the optional measurement filler -- and
    # only where the caller says it's safe to (see _decorate's ``widen``).
    measure = _REF_MEASURE.get() if widen else ""
    prefix = f" {measure}" if measure else ""
    return f"{prefix}{_MARK_OPEN}{idx}{_MARK_CLOSE}"


def _decorate(
    text: str | None,
    citation: str | None,
    href: str | None,
    *,
    widen: bool = True,
) -> str | None:
    """Annotate ``text`` with reference metadata for the active format.

    ``widen=True`` (legend entries) applies ``reference_measure_text`` as a
    same-line measurement filler (see ``_mark``). Panel titles pass
    ``widen=False``: a title can wrap (``wrap=True``) across multiple lines,
    which can split the filler and its sentinel into separate .pgf text
    blocks -- breaking the plain-text match that strips the filler back out
    (and leaking it into the final output). Legend entries don't wrap, so
    they stay contiguous.
    """
    if text is None or _FMT.get() != "pgf" or not (citation or href):
        return text
    if href:
        text = f"{_mark('href', href)}{text}{_mark('/href', '')}"
    if citation:
        text = f"{text}{_mark('cite', citation, widen=widen)}"
    return text


def _set_url(artist, href: str | None) -> None:
    """Make an artist clickable (SVG only -- other backends ignore urls)."""
    if href and _FMT.get() == "svg":
        artist.set_url(href)


def _link_legend_texts(legend_artist, panel: PanelSpec) -> None:
    """Point each legend entry's text at its href (SVG only).

    Ungrouped layers key by their (single) label; grouped layers key by
    each series' group value via ``layer.references`` (see
    ``ReferenceSpec``), since the group value *is* the legend text for
    each of that layer's series.
    """
    if legend_artist is None or _FMT.get() != "svg":
        return
    by_label: dict[str, str] = {}
    for layer in panel.layers:
        if layer.group is None:
            if layer.label and layer.href:
                by_label[layer.label] = layer.href
        elif layer.references:
            for key, ref in layer.references.items():
                if ref.href:
                    by_label[key] = ref.href
    for text in legend_artist.get_texts():
        _set_url(text, by_label.get(text.get_text()))


def _substitute_pgf_references(
    text: str, refs: list[tuple[str, str]], measure_text: str = ""
) -> str:
    """Replace the sentinels left by ``_decorate`` with real LaTeX macros.

    Runs after matplotlib's PGF text processing; surrounding text still follows
    the trusted TeX input rules, not a plain-text sandbox. A citation sentinel may be
    preceded by a measurement filler (see ``_mark``/``_REF_MEASURE``),
    which this strips out along with the sentinel itself -- it exists only
    to give matplotlib's layout pass a realistic width to measure against
    and must never reach the final output.
    """
    filler_re = re.escape(f" {measure_text}") if measure_text else ""
    pattern = re.compile(f"(?:{filler_re})?{_MARK_OPEN}(\\d+){_MARK_CLOSE}")

    def repl(m: re.Match) -> str:
        try:
            index = int(m.group(1))
        except ValueError:
            return m.group(0)
        if index >= len(refs):
            return m.group(0)
        kind, value = refs[index]
        if kind == "cite":
            return f"~\\figcite{{{value}}}"
        if kind == "href":
            return f"\\href{{{value}}}{{"
        return "}"

    return pattern.sub(repl, text)


_OUTSIDE_LEGEND_LOCS = {
    "outside right": {"loc": "center left", "bbox_to_anchor": (1.02, 0.5)},
    "outside top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.02), "ncol": 99},
    "outside bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.18)},
}

_SPINE_SIDES = {"L": "left", "R": "right", "T": "top", "B": "bottom"}


def _unique_stable(arr):
    seen = []
    for v in arr:
        if v not in seen:
            seen.append(v)
    return seen


def _float_array(values, where: str):
    try:
        return np.asarray(values, dtype=float)
    except OverflowError as error:
        raise ValueError(
            f"{where} contains a number outside the floating-point range"
        ) from error


def _col(data_cols, name):
    return _float_array(data_cols[name], f"column {name!r}")


def _x_values(ax, data_cols, name):
    """x-column values as plot-ready numeric positions.

    Numeric columns pass through unchanged. Categorical columns are mapped
    to evenly-spaced positions in first-seen order with automatic tick labels.

    Use Matplotlib's category registry so layers, twins and shared axes
    agree on the position of each category.
    """
    raw = data_cols[name]
    try:
        return np.asarray(raw, dtype=float)
    except OverflowError as error:
        raise ValueError(
            f"column {name!r} contains a number outside the floating-point range"
        ) from error
    except (ValueError, TypeError):
        present = np.asarray([value is not None for value in raw], dtype=bool)
        str_values = [str(value) for value in raw if value is not None]
        ax.xaxis.update_units(str_values)
        positions = np.full(len(raw), np.nan)
        positions[present] = np.asarray(ax.convert_xunits(str_values), dtype=float)
        return positions


def _series_masks(data_cols, layer: LayerSpec):
    """Yield (label, boolean-mask) for a layer, splitting by ``group``."""
    n = len(data_cols[layer.x])
    if layer.group is None:
        yield (
            _decorate(layer.label, layer.citation, layer.href),
            np.ones(n, dtype=bool),
        )
        return
    g = np.asarray(data_cols[layer.group], dtype=object)
    refs = layer.references or {}
    keys = _unique_stable(g) if layer.hue_order is None else layer.hue_order
    for key in keys:
        key_s = str(key)
        ref = refs.get(key_s)
        citation = ref.citation if ref else None
        href = ref.href if ref else None
        mask = (
            g == key
            if layer.hue_order is None
            else np.asarray(
                [
                    category_key(value) == category_key(key)
                    for value in data_cols[layer.group]
                ],
                dtype=bool,
            )
        )
        yield (_decorate(key_s, citation, href), mask)


def _continuous_cmap(kind: str):
    """A matplotlib Colormap built from our LCH sequential/diverging palettes."""
    from .color import palette as P

    pal = P.diverging(256) if kind == "diverging" else P.sequential(256)
    return pal.to_cmap()


def _color_norm(data_cols, layer):
    from matplotlib.colors import Normalize

    norm = Normalize()
    norm.autoscale(np.ma.masked_invalid(_col(data_cols, layer.c)))
    return norm


def _target_axes(ax, ax2, layer: LayerSpec):
    return ax2 if (layer.axis == "y2" and ax2 is not None) else ax


def _regression_fit(x, y, degree: int, confidence: float | None, *, at=None):
    """Return a numerically scaled polynomial fit and optional mean-fit CI."""
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", invalid="raise", divide="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        warnings.simplefilter("error", UserWarning)
        try:
            x = np.asarray(x, dtype=float)
            y = np.asarray(y, dtype=float)
            magnitude = float(np.max(np.abs(x))) or 1.0
            unit = x / magnitude
            center = float(unit.min()) / 2 + float(unit.max()) / 2
            scale = float(np.ptp(unit)) / 2
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("regression x range is numerically singular")
            x_scaled = (unit - center) / scale
            grid = (
                np.linspace(float(unit.min()), float(unit.max()), 200) * magnitude
                if at is None
                else np.asarray(at, dtype=float)
            )
            grid_scaled = (grid / magnitude - center) / scale
            # Covariance squares the response; normalize before it can under/overflow.
            response_scale = float(np.max(np.abs(y))) or 1.0
            response = y / response_scale
            interval = None
            if confidence is None:
                coefficients = np.polyfit(x_scaled, response, degree)
            else:
                coefficients, covariance = np.polyfit(
                    x_scaled, response, degree, cov=True
                )
                design = np.vander(grid_scaled, degree + 1)
                variance = np.einsum("ij,jk,ik->i", design, covariance, design)
                critical = NormalDist().inv_cdf(0.5 + confidence / 200)
                delta = critical * np.sqrt(np.maximum(variance, 0))
                fitted = np.polyval(coefficients, grid_scaled)
                interval = (
                    (fitted - delta) * response_scale,
                    (fitted + delta) * response_scale,
                )
            fitted = np.polyval(coefficients, grid_scaled) * response_scale
            if any(
                not np.isfinite(values).all()
                for values in [grid, fitted, *(interval or ())]
            ):
                raise ValueError("regression produced nonfinite predictions")
            return grid, fitted, interval
        except (
            TypeError,
            ValueError,
            FloatingPointError,
            np.linalg.LinAlgError,
            Warning,
        ) as e:
            raise ValueError(f"regplot fit failed: {e}") from e


def _y_errors(data_cols, layer: LayerSpec, mask):
    """Translate supplied absolute endpoints to Matplotlib error magnitudes."""
    if layer.yerr is not None:
        return _col(data_cols, layer.yerr)[mask]
    if layer.y_lower is not None and layer.y_upper is not None:
        center = _col(data_cols, layer.y)[mask]
        lower = _col(data_cols, layer.y_lower)[mask]
        upper = _col(data_cols, layer.y_upper)[mask]
        return np.asarray([center - lower, upper - center], dtype=float)
    return None


def _draw_series_layer(
    ax,
    ax2,
    data_cols,
    layer: LayerSpec,
    color_iter,
    theme,
    *,
    semantic_domain=None,
    semantic_guides=True,
):
    if layer.type == "scatter" and layer.semantics is not None:
        from ._scatter_semantics import draw_semantic_scatter

        return draw_semantic_scatter(
            ax,
            data_cols,
            layer,
            color_iter,
            domain=semantic_domain,
            guides=semantic_guides,
        )
    data_cols = ordered_group_columns(data_cols, layer)
    masks = list(_series_masks(data_cols, layer))
    # redundant marker/line-style encoding: only kicks in for *grouped*
    # (multi-series) layers, so a single clean line/scatter stays untouched.
    use_redundant = theme.redundant_encoding and layer.group is not None
    marker_cycle = (
        itertools.cycle(theme.markers) if use_redundant else itertools.repeat(None)
    )
    style_cycle = (
        itertools.cycle(theme.line_styles) if use_redundant else itertools.repeat("-")
    )
    hatch_cycle = (
        itertools.cycle(theme.hatches) if use_redundant else itertools.repeat(None)
    )
    target = _target_axes(ax, ax2, layer)

    x_all = _x_values(target, data_cols, layer.x)
    norm = _color_norm(data_cols, layer) if layer.c is not None else None
    if layer.type in {"hist2d", "hexbin"}:
        x = np.asarray(x_all, dtype=float)
        y = np.asarray(_col(data_cols, layer.y), dtype=float)
        if layer.type == "hist2d":
            image = target.hist2d(
                x,
                y,
                bins=layer.bins,
                density=layer.density,
                cmap=_continuous_cmap(layer.cmap_kind),
                alpha=layer.alpha,
            )[3]
        else:
            image = target.hexbin(
                x,
                y,
                gridsize=layer.gridsize,
                mincnt=layer.mincnt,
                cmap=_continuous_cmap(layer.cmap_kind),
                alpha=layer.alpha,
            )
        if layer.colorbar:
            target.figure.colorbar(image, ax=target, label=layer.clabel or "")
        return

    if layer.type == "quiver":
        x = np.asarray(x_all, dtype=float)
        y = np.asarray(_col(data_cols, layer.y), dtype=float)
        u = np.asarray(_col(data_cols, layer.u), dtype=float)
        v = np.asarray(_col(data_cols, layer.v), dtype=float)
        kwargs: dict[str, Any] = {
            "angles": "xy",
            "scale_units": "xy",
            "scale": layer.quiver_scale,
            "alpha": layer.alpha,
            "label": masks[0][0],
        }
        if layer.quiver_width is not None:
            kwargs["width"] = layer.quiver_width
        if layer.line_width is not None:
            kwargs["linewidth"] = layer.line_width
        if layer.c is not None:
            q = target.quiver(
                x,
                y,
                u,
                v,
                _col(data_cols, layer.c),
                cmap=_continuous_cmap(layer.cmap_kind),
                norm=norm,
                **kwargs,
            )
            if layer.colorbar:
                target.figure.colorbar(q, ax=target, label=layer.clabel or "")
        else:
            target.quiver(
                x,
                y,
                u,
                v,
                color=layer.color or next(color_iter),
                **kwargs,
            )
        return

    if layer.type == "stackplot":
        labels = [label for label, _mask in masks]
        x_groups = [x_all[mask] for _label, mask in masks]
        y_groups = [_col(data_cols, layer.y)[mask] for _label, mask in masks]
        colors = [layer.color or next(color_iter) for _label, _mask in masks]
        collections = target.stackplot(
            x_groups[0],
            *y_groups,
            labels=labels,
            colors=colors,
            linewidth=layer.line_width or 0,
            linestyle="solid" if layer.line_style is None else layer.line_style,
            alpha=layer.alpha,
        )
        if use_redundant:
            hatches = itertools.cycle(theme.hatches)
            for collection in collections:
                collection.set_hatch(next(hatches))
        return

    y_all = _col(data_cols, layer.y)
    if layer.hue_order is None:
        masks = [
            (label, mask)
            for label, mask in masks
            if np.any(np.isfinite(x_all[mask]) & np.isfinite(y_all[mask]))
        ]
    n_series = len(masks)
    sc = None
    jitter_rng = np.random.default_rng(0)  # deterministic export/re-render

    if (
        layer.type == "regplot"
        and layer.regression is not None
        and layer.regression.residual
        and any(np.any(mask) for _label, mask in masks)
    ):
        target.axhline(0, color="#6b7280", linewidth=0.75, linestyle="--")

    for series_i, (label, mask) in enumerate(masks):
        x = x_all[mask]
        y = y_all[mask]
        marker = next(marker_cycle) if layer.marker is None else layer.marker
        if layer.marker is None and layer.type in {
            "scatter",
            "regplot",
            "stripplot",
            "errorbar",
        }:
            marker = marker or "o"
        linestyle = next(style_cycle) if layer.line_style is None else layer.line_style
        if layer.hue_order is not None and not np.any(np.isfinite(x) & np.isfinite(y)):
            if not layer.color:
                next(color_iter)
            if layer.type == "bar":
                next(hatch_cycle)
            continue
        if layer.type == "line":
            color = layer.color or next(color_iter)
            target.plot(
                x,
                y,
                label=label,
                color=color,
                linewidth=layer.line_width,
                linestyle=linestyle,
                drawstyle=layer.drawstyle,
                marker=marker,
                markersize=layer.marker_size,
                alpha=layer.alpha,
            )
        elif layer.type == "regplot":
            color = layer.color or next(color_iter)
            config = layer.regression
            if config is None:
                grid, fitted, interval = _regression_fit(
                    x, y, layer.degree, layer.confidence
                )
            else:
                from ._regression_render import fit_regression

                grid, fitted, interval = fit_regression(
                    x, y, layer, _regression_fit, at=x if config.residual else None
                )
                if target.get_yscale() == "log" and any(
                    np.any(values <= 0) for values in [fitted, *(interval or ())]
                ):
                    raise ValueError(
                        "regression predictions/bands must be positive on log y"
                    )
                if config.residual:
                    with np.errstate(over="raise", invalid="raise"):
                        y = y - fitted
                    if not np.isfinite(y).all():
                        raise ValueError("regression residuals are not representable")
            if interval is not None:
                target.fill_between(
                    grid,
                    interval[0],
                    interval[1],
                    color=color,
                    alpha=min(layer.alpha, 0.2),
                    linewidth=0,
                )
            target.scatter(
                x,
                y,
                label=label,
                color=color,
                s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                marker=marker,
                alpha=layer.alpha,
            )
            if config is None or not config.residual:
                target.plot(
                    grid,
                    fitted,
                    color=color,
                    linewidth=layer.line_width,
                    linestyle=linestyle,
                    alpha=layer.alpha,
                )
        elif layer.type == "scatter":
            if layer.c is not None:
                values = _col(data_cols, layer.c)[mask]
                sc = target.scatter(
                    x,
                    y,
                    c=values,
                    cmap=_continuous_cmap(layer.cmap_kind),
                    norm=norm,
                    label=label,
                    s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                    marker=marker,
                    alpha=layer.alpha,
                )
            else:
                color = layer.color or next(color_iter)
                target.scatter(
                    x,
                    y,
                    label=label,
                    color=color,
                    s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                    marker=marker,
                    alpha=layer.alpha,
                )
        elif layer.type == "stripplot":
            color = layer.color or next(color_iter)
            jitter = 0.15 if layer.jitter is None else layer.jitter
            target.scatter(
                x + jitter_rng.uniform(-jitter, jitter, size=len(x)),
                y,
                label=label,
                color=color,
                s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                marker=marker,
                alpha=layer.alpha,
            )
        elif layer.type == "bar":
            color = layer.color or next(color_iter)
            hatch = next(hatch_cycle)
            span = 0.8 if layer.bar_width is None else layer.bar_width
            # Errorbars are drawn by the same bar() call, so they share the
            # actual dodged centers even with missing categories or twins.
            bar_w = span / n_series if n_series > 1 else span
            offset = (series_i - (n_series - 1) / 2) * bar_w
            yerr = _y_errors(data_cols, layer, mask)
            error_kw = {
                "ecolor": layer.error_color or "#30343b",
                "elinewidth": (
                    1.1 if layer.error_line_width is None else layer.error_line_width
                ),
                "capsize": 3.0 if layer.capsize is None else layer.capsize,
                "capthick": 1.1 if layer.capthick is None else layer.capthick,
                "alpha": layer.alpha,
            }
            target.bar(
                x + offset,
                y,
                width=bar_w * 0.92 if n_series > 1 else bar_w,
                label=label,
                color=color,
                edgecolor=layer.edge_color,
                linewidth=layer.line_width,
                hatch=hatch if n_series > 1 else None,
                alpha=layer.alpha,
                yerr=yerr,
                error_kw=error_kw,
            )
        elif layer.type == "errorbar":
            color = layer.color or next(color_iter)
            yerr = _y_errors(data_cols, layer, mask)
            xerr = _col(data_cols, layer.xerr)[mask] if layer.xerr else None
            target.errorbar(
                x,
                y,
                yerr=yerr,
                xerr=xerr,
                label=label,
                color=color,
                ecolor=layer.error_color,
                fmt=marker,
                markersize=4 if layer.marker_size is None else layer.marker_size,
                linewidth=layer.line_width,
                elinewidth=layer.error_line_width,
                capsize=2.0 if layer.capsize is None else layer.capsize,
                capthick=layer.capthick,
                alpha=layer.alpha,
            )
        elif layer.type == "band":
            color = layer.color or next(color_iter)
            lower = _col(data_cols, layer.y2)[mask] if layer.y2 else y
            target.fill_between(
                x,
                lower,
                y,
                label=label,
                color=color,
                alpha=layer.alpha if layer.alpha < 1 else 0.25,
                linewidth=0,
            )

    if sc is not None and layer.colorbar:
        target.figure.colorbar(sc, ax=target, label=layer.clabel or "")


def _draw_stat_ranges(ax, x, lower, upper, layer: LayerSpec, color):
    """Draw actual endpoints, even if they do not bracket the point estimate."""
    from matplotlib.container import ErrorbarContainer

    width = 1.1 if layer.error_line_width is None else layer.error_line_width
    capsize = 3.0 if layer.capsize is None else layer.capsize
    capthick = 1.1 if layer.capthick is None else layer.capthick
    horizontal = layer.orient == "h"
    draw = ax.hlines if horizontal else ax.vlines
    collection = draw(
        x,
        lower,
        upper,
        colors=color,
        linewidths=width,
        alpha=layer.alpha,
        zorder=2.5,
        label="_nolegend_",
    )
    caps = []
    if capsize > 0:
        for endpoints in (lower, upper):
            coordinates = (endpoints, x) if horizontal else (x, endpoints)
            caps.append(
                ax.plot(
                    *coordinates,
                    linestyle="none",
                    marker="|" if horizontal else "_",
                    markersize=2 * capsize,
                    markeredgewidth=capthick,
                    color=color,
                    alpha=layer.alpha,
                    zorder=2.5,
                    label="_nolegend_",
                )[0]
            )
    # Like native errorbar(fmt="none"), a range has no data-line artist;
    # Matplotlib's annotation incorrectly requires Line2D rather than None.
    errors = ErrorbarContainer(
        cast(Any, (None, tuple(caps), (collection,))),
        has_xerr=horizontal,
        has_yerr=not horizontal,
        label="_nolegend_",
    )
    ax.add_container(errors)
    return errors


def _draw_stat_layer(
    ax,
    ax2,
    data_cols,
    layer: LayerSpec,
    color_iter,
    theme,
    *,
    semantic_domain=None,
    semantic_guides=True,
):
    if layer.type == "lineplot" and layer.semantics is not None:
        from ._line_semantics import draw_semantic_lineplot

        return draw_semantic_lineplot(
            ax,
            data_cols,
            layer,
            color_iter,
            theme,
            domain=semantic_domain,
            guides=semantic_guides,
        )
    if layer.type == "lineplot":
        from ._lineplot import draw_lineplot

        return draw_lineplot(ax, data_cols, layer, color_iter, theme)
    from ._estimate import summarize

    target = _target_axes(ax, ax2, layer)
    horizontal = layer.orient == "h"
    value_scale = target.get_xscale() if horizontal else target.get_yscale()
    summary = summarize(data_cols, layer, value_scale=value_scale)
    config = stat_config(layer)
    labels = [str(category) for category in summary.categories]
    spacing = 1.0
    if layer.native_scale:
        positions, spacing, labels = _category_geometry(
            target, summary.categories, layer
        )
    else:
        category_axis = target.yaxis if horizontal else target.xaxis
        category_axis.update_units(labels)
        convert = target.convert_yunits if horizontal else target.convert_xunits
        positions = np.asarray(convert(labels), dtype=float)
        if layer.order is not None and np.any(np.diff(positions) <= 0):
            raise ValueError(
                "conflicting category order on a shared axis; use matching orders"
            )
    category_positions = dict(zip(summary.categories, positions, strict=True))
    category_ranks = (
        {
            c: j
            for j, c in enumerate(
                sorted(summary.categories, key=category_positions.__getitem__)
            )
        }
        if layer.native_scale
        else category_positions
    )
    bottoms = dict.fromkeys(summary.categories, 0.0)
    grouped = {group: [] for group in summary.groups}
    for point in summary.estimates:
        grouped[point.group].append(point)
    if config.errorbar is not None and any(p.lower is None for p in summary.estimates):
        warnings.warn(
            "statistical intervals omitted for groups with fewer than 2 observations "
            "or independent resampling units",
            UserWarning,
            stacklevel=2,
        )
    n_series = len(summary.groups)
    redundant = theme.redundant_encoding and layer.group is not None
    for i, group in enumerate(summary.groups):
        points = sorted(grouped[group], key=lambda p: category_positions[p.category])
        color = layer.color or next(color_iter)
        if not points:
            continue  # Reserve the hue's colour/dodge slot, but invent no legend entry.
        if layer.group is None:
            label = _decorate(layer.label, layer.citation, layer.href)
        else:
            key = str(group)
            ref = (layer.references or {}).get(key)
            label = _decorate(
                key, ref.citation if ref else None, ref.href if ref else None
            )
        x = np.asarray([category_positions[p.category] for p in points])
        y = np.asarray([p.value for p in points])
        bars = None
        if layer.type in {"barplot", "countplot"}:
            span = (0.8 if layer.bar_width is None else layer.bar_width) * spacing
            dodged = n_series > 1 and not layer.stack
            width = span / n_series if dodged else span
            if dodged:
                x = x + (i - (n_series - 1) / 2) * width
            gap = (0.08 if dodged else 0.0) if layer.gap is None else layer.gap
            base = (
                np.asarray([bottoms[p.category] for p in points])
                if layer.stack
                else 0
                if layer.baseline is None
                else layer.baseline
            )
            heights = y if layer.stack else y - base
            if np.any(~np.isfinite(heights)):
                raise ValueError("statistical bar span exceeds finite plotting range")
            drawn_width = width * (1 - gap)
            locations = x
            align = {}
            if layer.native_scale:
                low = _category_inverse(target, x - drawn_width / 2, layer)
                high = _category_inverse(target, x + drawn_width / 2, layer)
                drawn_width = high - low
                if np.any(~np.isfinite(drawn_width)) or np.any(drawn_width <= 0):
                    raise ValueError(
                        "native statistical bar geometry collapses or overflows"
                    )
                locations = low
                align = {"align": "edge"}
            geometry = (
                {"height": drawn_width, "left": base}
                if horizontal
                else {"width": drawn_width, "bottom": base}
            )
            hatch = theme.hatches[i % len(theme.hatches)] if redundant else None
            draw_bars = target.barh if horizontal else target.bar
            bars = draw_bars(
                locations,
                heights,
                **geometry,
                **align,
                color=color,
                edgecolor=layer.edge_color,
                linewidth=layer.line_width,
                hatch=hatch,
                alpha=layer.alpha,
                label=label,
            )
            if layer.stack:
                for p in points:
                    bottoms[p.category] += p.value
        else:
            span = (0.0 if layer.dodge is None else layer.dodge) * spacing
            x = x + (i - (n_series - 1) / 2) * span / n_series
            # Insert breaks instead of bridging a missing category cell.
            line_x, line_y = [], []
            previous = None
            for position, point in zip(x, points, strict=True):
                index = category_ranks[point.category]
                if previous is not None and index > previous + 1:
                    line_x.append(np.nan)
                    line_y.append(np.nan)
                line_x.append(
                    _category_inverse(target, [position], layer)[0]
                    if layer.native_scale
                    else position
                )
                line_y.append(point.value)
                previous = index
            marker = (
                layer.marker
                if layer.marker is not None
                else (theme.markers[i % len(theme.markers)] if redundant else "o")
            )
            style = (
                layer.line_style
                if layer.line_style is not None
                else (
                    theme.line_styles[i % len(theme.line_styles)] if redundant else "-"
                )
            )
            coordinates = (line_y, line_x) if horizontal else (line_x, line_y)
            target.plot(
                *coordinates,
                color=color,
                label=label,
                marker=marker,
                linestyle=style,
                markersize=5.0 if layer.marker_size is None else layer.marker_size,
                linewidth=1.25 if layer.line_width is None else layer.line_width,
                alpha=layer.alpha,
            )
        if layer.native_scale:
            x = _category_inverse(target, x, layer)
        valid = [j for j, p in enumerate(points) if p.lower is not None]
        if valid:
            error_color = layer.error_color or (color if bars is None else "#30343b")
            errors = _draw_stat_ranges(
                target,
                x[valid],
                [points[j].lower for j in valid],
                [points[j].upper for j in valid],
                layer,
                error_color,
            )
            if bars is not None:
                bars.errorbar = errors
        if bars is not None and layer.value_labels:
            if layer.stack:
                if layer.native_scale:
                    for position, point in zip(x, points, strict=True):
                        center = bottoms[point.category] - point.value / 2
                        coordinates = (
                            (center, position) if horizontal else (position, center)
                        )
                        target.annotate(
                            format(point.value, layer.label_format),
                            coordinates,
                            ha="center",
                            va="center",
                        )
                else:
                    target.bar_label(
                        bars,
                        labels=[format(p.value, layer.label_format) for p in points],
                        label_type="center",
                    )
            else:
                # Label each real endpoint independently: native bar_label zips
                # errors/rectangles and misaligns sparse singleton intervals.
                for position, point in zip(x, points, strict=True):
                    positive = point.value >= (
                        0 if layer.baseline is None else layer.baseline
                    )
                    endpoint = point.upper if positive else point.lower
                    edge = (
                        point.value
                        if endpoint is None
                        else (
                            max(point.value, endpoint)
                            if positive
                            else min(point.value, endpoint)
                        )
                    )
                    coordinates = (edge, position) if horizontal else (position, edge)
                    offset = (
                        (2 if positive else -2, 0)
                        if horizontal
                        else (0, 2 if positive else -2)
                    )
                    target.annotate(
                        format(point.value, layer.label_format),
                        coordinates,
                        xytext=offset,
                        textcoords="offset points",
                        ha=("left" if positive else "right")
                        if horizontal
                        else "center",
                        va="center"
                        if horizontal
                        else ("bottom" if positive else "top"),
                    )
    if layer.native_scale:
        _finish_category_axis(target, positions, spacing, labels, layer)


def _gaussian_kde(values: np.ndarray, n_points: int = 200):
    """Legacy NumPy Gaussian KDE: 1.06*sample-SD*n**(-1/5), 200 points.

    Retained for old specs/default calls, including the fallback for constants.
    This is NOT SciPy's default Scott factor or a numerical-parity claim.
    Opt-in weighted/configurable KDE uses the separate typed calculation.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    std = values.std(ddof=1) if n > 1 else 1.0
    bandwidth = 1.06 * std * n ** (-1 / 5) if std > 0 else 1.0
    lo, hi = values.min() - 3 * bandwidth, values.max() + 3 * bandwidth
    grid = np.linspace(lo, hi, n_points)
    # sum of Gaussian kernels centred at each sample, evaluated on the grid
    diffs = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * diffs**2).sum(axis=1) / (n * bandwidth * np.sqrt(2 * np.pi))
    return grid, density


def _letter_value_artists(ax, values, positions, width, layer):
    """Native disjoint polygon bands with deterministic median and tail points."""
    from matplotlib.collections import PolyCollection

    from ._components import apply_component_style
    from ._letter_value import letter_value_summary

    edge = layer.edge_color or "#4b5563"
    stroke = 0.8 if layer.line_width is None else layer.line_width
    bodies = []
    horizontal = layer.orient == "h"
    for data, center in zip(values, positions, strict=True):
        summary = letter_value_summary(
            data,
            k_depth=layer.k_depth,
            width_method=layer.width_method,
            outlier_prop=layer.outlier_prop,
            trust_alpha=layer.trust_alpha,
        )
        vertices = []
        for (low, high), relative in zip(
            itertools.pairwise(summary.values), summary.widths, strict=True
        ):
            half = width * relative / 2
            rectangle = np.asarray(
                [
                    [center - half, low],
                    [center + half, low],
                    [center + half, high],
                    [center - half, high],
                ]
            )
            vertices.append(rectangle[:, ::-1] if horizontal else rectangle)
        body = PolyCollection(
            vertices,
            edgecolors=edge,
            linewidths=stroke,
            linestyles="-" if layer.line_style is None else layer.line_style,
        )
        ax.add_collection(body)
        bodies.append(body)
        if layer.showmedians is None or layer.showmedians:
            category = [center - width / 2, center + width / 2]
            value = [summary.median, summary.median]
            x, y = (value, category) if horizontal else (category, value)
            (median_artist,) = ax.plot(
                x,
                y,
                color=edge,
                linewidth=stroke,
                linestyle="-" if layer.line_style is None else layer.line_style,
                alpha=layer.alpha,
                solid_capstyle="butt",
            )
            if layer.components is not None:
                apply_component_style(median_artist, layer.components.median)
        if (layer.showfliers is None or layer.showfliers) and summary.fliers:
            category = np.full(len(summary.fliers), center)
            value = np.asarray(summary.fliers)
            x, y = (value, category) if horizontal else (category, value)
            (flier_artist,) = ax.plot(
                x,
                y,
                linestyle="none",
                color=edge,
                marker="d" if layer.marker is None else layer.marker,
                markersize=3 if layer.marker_size is None else layer.marker_size,
                markerfacecolor="none",
                markeredgewidth=stroke,
                alpha=layer.alpha,
            )
            if layer.components is not None:
                apply_component_style(flier_artist, layer.components.flier)
    ax.autoscale_view()
    return bodies


def _category_geometry(ax, categories, layer):
    """Working category coordinates; native logs use log10 geometry."""
    horizontal = layer.orient == "h"
    axis = ax.yaxis if horizontal else ax.xaxis
    labels = [str(c) for c in categories]
    if layer.native_scale:
        positions, spacing = native_category_geometry(categories, axis.get_scale())
        return np.asarray(positions), spacing, labels
    if layer.y:
        axis.update_units(labels)
        convert = ax.convert_yunits if horizontal else ax.convert_xunits
        positions = np.asarray(convert(labels), dtype=float)
        if layer.order is not None and np.any(np.diff(positions) <= 0):
            raise ValueError(
                "conflicting category order on a shared axis; use matching orders"
            )
        return positions, 1.0, labels
    return np.arange(1, len(categories) + 1, dtype=float), 1.0, labels


def _category_inverse(ax, values, layer):
    axis = ax.yaxis if layer.orient == "h" else ax.xaxis
    numbers = np.asarray(values, dtype=float)
    if layer.native_scale and axis.get_scale() == "log":
        with np.errstate(over="ignore", under="ignore"):
            numbers = np.power(10.0, numbers)
        if np.any(~np.isfinite(numbers)) or np.any(numbers <= 0):
            raise ValueError(
                "native log category geometry exceeds finite positive range"
            )
    if np.any(~np.isfinite(numbers)):
        raise ValueError("native category geometry exceeds finite plotting range")
    return numbers


def _finish_category_axis(ax, positions, spacing, labels, layer):
    horizontal = layer.orient == "h"
    if not layer.native_scale and (
        layer.type in {"violin", "boxenplot", "swarmplot"}
        or layer.y
        or layer.order is not None
    ):
        ticks = ax.set_yticks if horizontal else ax.set_xticks
        ticks(positions, labels=labels)
    if layer.y or layer.native_scale:
        bounds = _category_inverse(
            ax, [positions.min() - spacing / 2, positions.max() + spacing / 2], layer
        )
        limits = ax.get_ylim if horizontal else ax.get_xlim
        set_limits = ax.set_ylim if horizontal else ax.set_xlim
        low, high = limits()
        if low < high:
            set_limits(min(low, bounds[0]), max(high, bounds[1]))
        else:
            set_limits(max(low, bounds[1]), min(high, bounds[0]))


def _distribution_artists(
    ax, values, positions, width, labels, layer, violin_context=None
):
    """Compute in declared coordinates then inverse-map native artist geometry."""
    from matplotlib.collections import LineCollection

    category_dim = int(layer.orient == "h")
    value_dim = 1 - category_dim
    scales = [ax.get_xscale(), ax.get_yscale()]
    inverse = [False, False]
    inverse[category_dim] = layer.native_scale and scales[category_dim] == "log"
    inverse[value_dim] = layer.stat_scale == "axis" and scales[value_dim] == "log"
    data = [np.log10(v) for v in values] if inverse[value_dim] else values
    starts = len(ax.patches), len(ax.lines), len(ax.collections)
    old_lim = ax.dataLim.frozen()
    old_minpos = ax.dataLim.minpos.copy()
    old_ignore = ax.ignore_existing_data_limits
    locators = [
        (
            axis.get_major_locator(),
            axis.get_major_formatter(),
            axis.get_minor_locator(),
            axis.get_minor_formatter(),
        )
        for axis in (ax.xaxis, ax.yaxis)
    ]

    def mapped(points):
        points = np.asarray(points, dtype=float).copy()
        for dim in range(2):
            if inverse[dim]:
                with np.errstate(over="ignore", under="ignore"):
                    points[:, dim] = 10.0 ** points[:, dim]
            if np.any(~np.isfinite(points[:, dim])) or (
                scales[dim] == "log" and np.any(points[:, dim] <= 0)
            ):
                raise ValueError(
                    "distribution geometry must be finite and positive on log axes; "
                    "use stat_scale='axis' or adjust notch/width controls"
                )
        return points

    geometry = []
    try:
        if any(inverse):
            ax.set_xscale("linear")
            ax.set_yscale("linear")
        bodies = _native_distribution_artists(
            ax, data, positions, width, labels, layer, violin_context
        )
        for patch in list(ax.patches)[starts[0] :]:
            vertices = mapped(patch.get_path().vertices)
            patch.get_path().vertices[:] = vertices
            geometry.append(vertices)
        for line in list(ax.lines)[starts[1] :]:
            vertices = mapped(line.get_xydata())
            line.set_data(vertices[:, 0], vertices[:, 1])
            geometry.append(vertices)
        for collection in list(ax.collections)[starts[2] :]:
            if isinstance(collection, LineCollection):
                segments = [mapped(v) for v in collection.get_segments()]
                collection.set_segments(segments)
                geometry.extend(segments)
            else:
                for path in collection.get_paths():
                    vertices = mapped(path.vertices)
                    path.vertices[:] = vertices
                    geometry.append(vertices)
        ax.dataLim.set_points(old_lim.get_points())
        ax.dataLim._minpos = old_minpos
        ax.ignore_existing_data_limits = old_ignore
        for vertices in geometry:
            if len(vertices):
                ax.update_datalim(vertices)
    finally:
        if any(inverse):
            ax.set_xscale(scales[0])
            ax.set_yscale(scales[1])
            for axis, (major, fmt, minor, minor_fmt) in zip(
                (ax.xaxis, ax.yaxis), locators, strict=True
            ):
                axis.set_major_locator(major)
                axis.set_major_formatter(fmt)
                axis.set_minor_locator(minor)
                axis.set_minor_formatter(minor_fmt)
    ax.autoscale_view()
    return bodies


def _native_distribution_artists(
    ax, values, positions, width, labels, layer, violin_context=None
):
    """Native artists for deterministic summaries/KDE across Matplotlib 3.8+."""
    if violin_context is not None:
        from ._violin import violin_artists

        return violin_artists(ax, violin_context, positions, width, layer)
    if layer.type == "boxenplot":
        return _letter_value_artists(ax, values, positions, width, layer)
    draw = ax.boxplot if layer.type == "box" else ax.violinplot
    parameters = inspect.signature(draw).parameters
    kwargs: dict[str, Any] = {"positions": positions}
    if "orientation" in parameters:
        kwargs["orientation"] = "horizontal" if layer.orient == "h" else "vertical"
    else:
        kwargs["vert"] = layer.orient != "h"
    if width is not None:
        kwargs["widths"] = width
    if layer.type == "box":
        kwargs["patch_artist"] = True
        kwargs["manage_ticks"] = not bool(layer.y) and not layer.native_scale
        if not layer.y and not layer.native_scale:
            kwargs["tick_labels" if "tick_labels" in parameters else "labels"] = labels
        for name in ("whis", "notch", "showmeans", "showfliers"):
            if getattr(layer, name) is not None:
                kwargs[name] = getattr(layer, name)
        common = {
            name: value
            for name, value in (
                ("linewidth", layer.line_width),
                ("linestyle", layer.line_style),
            )
            if value is not None
        }
        outline = {**common}
        lines = {**common}
        fliers = {}
        if layer.edge_color is not None:
            outline["edgecolor"] = layer.edge_color
            lines["color"] = layer.edge_color
            fliers["markeredgecolor"] = layer.edge_color
        if layer.marker is not None:
            fliers["marker"] = layer.marker
        if layer.marker_size is not None:
            fliers["markersize"] = layer.marker_size
        kwargs.update(
            boxprops=outline,
            whiskerprops=lines,
            capprops=lines,
            medianprops=lines,
            flierprops=fliers,
        )
        import matplotlib as mpl

        # Serializable notches use the native deterministic Gaussian formula,
        # never an ambient rc bootstrap that draws from NumPy's global RNG.
        if layer.components is not None:
            if layer.components.body is not None:
                kwargs["showbox"] = True
            if layer.components.cap is not None:
                kwargs["showcaps"] = True
        with mpl.rc_context({"boxplot.bootstrap": None}):
            parts = draw(values, **kwargs)
        if layer.components is not None:
            from ._components import apply_component_style

            for role, key in (
                ("whisker", "whiskers"),
                ("cap", "caps"),
                ("median", "medians"),
                ("mean", "means"),
                ("flier", "fliers"),
            ):
                for artist in parts[key]:
                    apply_component_style(artist, getattr(layer.components, role))
        return parts["boxes"]
    kwargs["showmedians"] = True if layer.showmedians is None else layer.showmedians
    for name in ("showmeans", "showextrema", "bw_method", "points"):
        if getattr(layer, name) is not None:
            kwargs[name] = getattr(layer, name)
    parts = draw(values, **kwargs)
    for name, artist in parts.items():
        if name == "bodies":
            continue
        if layer.edge_color is not None:
            artist.set_color(layer.edge_color)
        if layer.line_width is not None:
            artist.set_linewidth(layer.line_width)
        if layer.line_style is not None:
            artist.set_linestyle(layer.line_style)
    return parts["bodies"]


def _draw_categorical_distribution(ax, columns, layer, color_iter, theme):
    category, value, hue = distribution_columns(layer)
    rows = distribution_rows(columns, layer)
    categories, groups = distribution_levels(columns, layer, rows)
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    if not layer.y and not layer.native_scale:
        # Legacy one-column distributions use one-based native coordinates.
        labels = [
            _decorate(layer.label, layer.citation, layer.href)
            if category is None
            else _decorate(
                str(c), (ref.citation if ref else None), (ref.href if ref else None)
            )
            for c in categories
            for ref in [(layer.references or {}).get(str(c))]
        ]
    index = {c: i for i, c in enumerate(categories)}
    cells = {group: {} for group in groups}
    weight_cells = {group: {} for group in groups}
    for row in rows:
        c = None if category is None else columns[category][row]
        g = None if hue is None else columns[hue][row]
        cells[g].setdefault(c, []).append(columns[value][row])
        if layer.weights is not None:
            weight_cells[g].setdefault(c, []).append(columns[layer.weights][row])
    redundant = theme.redundant_encoding and len(groups if layer.y else categories) > 1
    width = layer.width
    if (layer.y or layer.native_scale or layer.type == "boxenplot") and width is None:
        width = 0.8
    if layer.native_scale:
        width *= spacing
    gap = 0 if layer.gap is None else layer.gap
    if not layer.y and (
        width is not None or layer.gap is not None or layer.order is not None
    ):
        if width is None:
            width = (
                0.5
                if layer.type == "violin"
                else np.clip(0.15 * (len(categories) - 1), 0.15, 0.5)
            )
        width *= 1 - gap
    colors = [
        layer.color or next(color_iter) for _ in (groups if layer.y else categories)
    ]
    profiles = None
    if layer.type == "violin":
        from ._violin_options import extended_violin

        if extended_violin(layer):
            from ._violin import prepare_violin

            value_axis = ax.xaxis if layer.orient == "h" else ax.yaxis
            profiles = prepare_violin(
                cells,
                layer,
                weights=weight_cells if layer.weights is not None else None,
                log_value=(
                    layer.stat_scale == "axis" and value_axis.get_scale() == "log"
                ),
            )
    for i, group in enumerate(groups):
        points = sorted(cells[group], key=index.__getitem__)
        if not points:
            continue  # Consume the reserved hue slot without inventing a legend entry.
        x = np.asarray([positions[index[c]] for c in points])
        span = (
            (
                (width if width is not None else 0)
                if layer.dodge is None
                else layer.dodge * spacing
            )
            if layer.y
            else 0
        )
        dodged = (
            len(groups) > 1
            and span != 0
            and not (layer.type == "violin" and layer.split)
        )
        drawn_width = width
        if dodged:
            assert width is not None
            x += (i - (len(groups) - 1) / 2) * span / len(groups)
            drawn_width = width / len(groups)
        if layer.y:
            assert drawn_width is not None
            drawn_width *= 1 - gap
        bodies = _distribution_artists(
            ax,
            [cells[group][c] for c in points],
            x,
            drawn_width,
            [labels[index[c]] for c in points],
            layer,
            None
            if profiles is None
            else [
                (profiles[group, c], (-1 if i == 0 else 1) if layer.split else 0)
                for c in points
            ],
        )
        for c, body in zip(points, bodies, strict=True):
            style_index = i if layer.y else index[c]
            body_style = layer.components.body if layer.components is not None else None
            base_color = (
                body_style.color
                if body_style is not None and body_style.color is not None
                else colors[style_index]
            )
            if layer.type == "boxenplot" and base_color != "none":
                from matplotlib.colors import to_rgb

                rgb = np.asarray(to_rgb(base_color))
                n_bands = len(body.get_paths())
                depth = (n_bands + 1) // 2
                # Lighter outer tiers; identical central hue across cells.
                tints = [
                    0.55 * (1 - (min(j, n_bands - 1 - j) + 1) / depth)
                    for j in range(n_bands)
                ]
                body.set_facecolor([rgb * (1 - tint) + tint for tint in tints])
            else:
                body.set_facecolor(base_color)
            body.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)
            body.set_hatch(
                theme.hatches[style_index % len(theme.hatches)] if redundant else None
            )
            if layer.edge_color is not None:
                body.set_edgecolor(layer.edge_color)
            if layer.line_width is not None:
                body.set_linewidth(layer.line_width)
            if layer.line_style is not None:
                body.set_linestyle(layer.line_style)
            if body_style is not None:
                from ._components import apply_component_style

                # Base color already applied (boxen keeps its lighter tail tiers).
                apply_component_style(body, body_style, body=True, include_color=False)
        if layer.y:
            ref = (layer.references or {}).get(str(group))
            label = (
                _decorate(layer.label, layer.citation, layer.href)
                if hue is None
                else _decorate(
                    str(group), ref.citation if ref else None, ref.href if ref else None
                )
            )
            bodies[0].set_label(label)
    _finish_category_axis(ax, positions, spacing, labels, layer)


def _draw_swarm_layer(ax, columns, layer: LayerSpec, color_iter):
    from ._swarm import SwarmCollection

    rows = distribution_rows(columns, layer)
    categories, groups = distribution_levels(columns, layer, rows)
    horizontal = layer.orient == "h"
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    width = (0.8 if layer.width is None else layer.width) * spacing
    span = width if layer.dodge is None else layer.dodge * spacing
    dodged = len(groups) > 1 and span != 0
    cell_width = (span / len(groups) if dodged else width) * (
        1 - (0 if layer.gap is None else layer.gap)
    )
    colors = {g: layer.color or next(color_iter) for g in groups}
    offsets = []
    faces = []
    urls = []
    indices = {c: i for i, c in enumerate(categories)}
    group_indices = {g: i for i, g in enumerate(groups)}
    cells = {}
    observed = set()
    for row in rows:
        c = columns[layer.x][row]
        g = columns[layer.group][row] if layer.group is not None else None
        observed.add(g)
        center = positions[indices[c]]
        if dodged:
            center += (group_indices[g] - (len(groups) - 1) / 2) * span / len(groups)
        cell = (c, g if dodged else None)
        if cell not in cells:
            lower, upper = _category_inverse(
                ax, [center - cell_width / 2, center + cell_width / 2], layer
            )
            cells[cell] = ([], lower, upper)
        cells[cell][0].append(len(offsets))
        raw_center = float(_category_inverse(ax, [center], layer)[0])
        offsets.append(
            [columns[layer.y][row], raw_center]
            if horizontal
            else [raw_center, columns[layer.y][row]]
        )
        faces.append(colors[g])
        ref = (layer.references or {}).get(str(g))
        urls.append((ref.href if ref else None) if layer.group else layer.href)
    size = 6 if layer.marker_size is None else layer.marker_size
    line_width = 0.5 if layer.line_width is None else layer.line_width
    edge = layer.edge_color or "white"
    collection = SwarmCollection(
        offsets,
        [(np.asarray(ids, dtype=int), lo, hi) for ids, lo, hi in cells.values()],
        horizontal=horizontal,
        size=size,
        line_width=line_width,
        warn_thresh=0.05 if layer.warn_thresh is None else layer.warn_thresh,
        facecolors=faces,
        edgecolors=edge,
        alpha=layer.alpha,
        offset_transform=ax.transData,
        label="_nolegend_",
        zorder=2,
    )
    collection.set_urls(urls)
    ax.add_collection(collection)
    ax.autoscale_view()
    _finish_category_axis(ax, positions, spacing, labels, layer)
    # Legend-only proxies have no coordinates/observations. One collection lets
    # non-dodged hues pack together instead of colliding across separate swarms.
    for group in groups:
        if group not in observed:
            continue
        ref = (layer.references or {}).get(str(group))
        label = (
            _decorate(layer.label, layer.citation, layer.href)
            if layer.group is None
            else _decorate(
                str(group), ref.citation if ref else None, ref.href if ref else None
            )
        )
        if label is not None:
            ax.plot(
                [],
                [],
                linestyle="none",
                marker="o",
                markersize=size,
                markeredgewidth=line_width,
                markeredgecolor=edge,
                color=colors[group],
                alpha=layer.alpha,
                label=label,
            )


def _draw_ecdf_layer(ax, columns, layer: LayerSpec, color_iter, theme):
    config = ecdf_config(layer)
    rows = ecdf_rows(columns, layer)
    groups = ecdf_groups(columns, layer, rows)
    redundant = theme.redundant_encoding and len(groups) > 1
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    refs = layer.references or {}
    for group in groups:
        color, style = layer.color or next(color_iter), next(styles)
        selected = [
            i for i in rows if layer.group is None or columns[layer.group][i] == group
        ]
        if not selected:
            continue
        values = [columns[layer.x][i] for i in selected]
        weights = (
            None
            if config.weights is None
            else [columns[config.weights][i] for i in selected]
        )
        knots, mass = empirical_steps(
            values, weights, stat=config.stat, complementary=config.complementary
        )
        if layer.group is None:
            label = _decorate(layer.label, layer.citation, layer.href)
        else:
            key = str(group)
            ref = refs.get(key)
            label = _decorate(
                key, ref.citation if ref else None, ref.href if ref else None
            )
        x, y = (knots, mass) if layer.orient == "v" else (mass, knots)
        (line,) = ax.plot(
            x,
            y,
            drawstyle="steps-post" if layer.orient == "v" else "steps-pre",
            label=label,
            color=color,
            linestyle=style if layer.line_style is None else layer.line_style,
            linewidth=layer.line_width,
            alpha=layer.alpha,
        )
        if layer.line_width == 0:
            # Matplotlib 3.8 rejects all-zero scaled dash patterns even for
            # transparent lines. Keep data/style/width and legend metadata,
            # but do not draw a zero-width stroke (including its legend proxy).
            line.set_visible(False)


def _draw_histogram_layer(ax, columns, layer: LayerSpec, color_iter, theme):
    result = histogram_summary(columns, layer)
    if not result.edges:
        return
    config = layer.histogram
    assert config is not None  # summary already rejects an untyped configuration
    edges = np.asarray(result.edges, dtype=float)
    widths = np.diff(edges)
    value_axis = ax.xaxis if layer.orient == "v" else ax.yaxis
    if value_axis.get_scale() == "log" and np.any(edges <= 0):
        raise ValueError(
            "derived log histogram bin edges must be positive; provide edges"
        )
    # Check every group before drawing, including empty reserved dodge slots.
    geometry = []
    baseline = np.zeros_like(widths)
    for slot, curve in enumerate(result.curves):
        start, stop = edges[:-1], edges[1:]
        if config.multiple == "dodge":
            step = widths / len(result.curves)
            start = edges[:-1] + slot * step
            stop = (
                edges[1:]
                if slot == len(result.curves) - 1
                else edges[:-1] + (slot + 1) * step
            )
            if np.any(stop <= start):
                raise ValueError("derived histogram dodge bins must be increasing")
        geometry.append((start, stop - start, baseline))
        if config.multiple == "stack" and curve.heights:
            heights = np.asarray(curve.heights, dtype=float)
            with np.errstate(over="ignore", invalid="ignore"):
                top = baseline + heights
            if np.any(~np.isfinite(top)) or np.any((heights > 0) & (top <= baseline)):
                raise ValueError(
                    "derived histogram stacked tops must be finite and "
                    "increase for nonzero bins"
                )
            baseline = top
    redundant = theme.redundant_encoding and len(result.curves) > 1
    hatches = itertools.cycle(theme.hatches) if redundant else itertools.repeat(None)
    refs = layer.references or {}
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    for curve, (start, span, baseline) in zip(result.curves, geometry, strict=True):
        color, hatch, line_style = (
            layer.color or next(color_iter),
            next(hatches),
            next(styles),
        )
        if not curve.heights:
            continue
        if layer.group is None:
            label = _decorate(layer.label, layer.citation, layer.href)
        else:
            ref = refs.get(str(curve.group))
            label = _decorate(
                str(curve.group),
                ref.citation if ref else None,
                ref.href if ref else None,
            )
        if config.element == "step":
            ax.stairs(
                baseline + np.asarray(curve.heights),
                edges,
                baseline=baseline if config.multiple == "stack" else 0,
                orientation="vertical" if layer.orient == "v" else "horizontal",
                fill=False,
                edgecolor=layer.edge_color or color,
                linewidth=layer.line_width,
                linestyle="-" if layer.line_width == 0 else line_style,
                alpha=layer.alpha,
                label=label,
            )
            continue
        style = {
            "align": "edge",
            "color": color,
            "hatch": hatch,
            "label": label,
            "alpha": layer.alpha,
            "edgecolor": layer.edge_color,
            "linewidth": layer.line_width,
        }
        if layer.orient == "v":
            ax.bar(start, curve.heights, width=span, bottom=baseline, **style)
        else:
            ax.barh(start, curve.heights, height=span, left=baseline, **style)


def _draw_kde_layer(ax, columns, layer: LayerSpec, color_iter, theme):
    config = layer.kde
    curves = kde_summary(columns, layer)
    assert config is not None  # summary already rejects an untyped configuration
    value_axis = ax.xaxis if layer.orient == "v" else ax.yaxis
    if value_axis.get_scale() == "log" and any(
        point <= 0 for curve in curves for point in curve.support
    ):
        raise ValueError(
            "derived log KDE support must be positive; provide clip or cut"
        )
    redundant = theme.redundant_encoding and len(curves) > 1
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    hatches = itertools.cycle(theme.hatches) if redundant else itertools.repeat(None)
    refs = layer.references or {}
    for curve in curves:
        color, style, hatch = (
            layer.color or next(color_iter),
            next(styles),
            next(hatches),
        )
        if curve.singular and config.warn_singular:
            warnings.warn(
                f"KDE skipped singular/insufficient group {curve.group!r}; "
                "no continuous density or bandwidth was invented",
                UserWarning,
                stacklevel=3,
            )
        if not curve.support:
            continue
        if layer.group is None:
            label = _decorate(layer.label, layer.citation, layer.href)
        else:
            ref = refs.get(str(curve.group))
            label = _decorate(
                str(curve.group),
                ref.citation if ref else None,
                ref.href if ref else None,
            )
        if config.fill:
            draw = ax.fill_between if layer.orient == "v" else ax.fill_betweenx
            draw(
                curve.support,
                0,
                curve.heights,
                color=color,
                alpha=layer.alpha,
                edgecolor=layer.edge_color or color,
                linewidth=layer.line_width,
                linestyle="-"
                if layer.line_width == 0
                else (style if layer.line_style is None else layer.line_style),
                hatch=hatch,
                label=label,
            )
        else:
            x, y = (
                (curve.support, curve.heights)
                if layer.orient == "v"
                else (curve.heights, curve.support)
            )
            (line,) = ax.plot(
                x,
                y,
                color=color,
                alpha=layer.alpha,
                label=label,
                linewidth=layer.line_width,
                linestyle=style if layer.line_style is None else layer.line_style,
            )
            if layer.line_width == 0:
                line.set_visible(False)  # all-zero dashes are invalid in Matplotlib3.8


def _draw_kde2d_layer(ax, columns, layer: LayerSpec, color_iter, theme):
    from matplotlib.colors import to_rgb
    from matplotlib.container import BarContainer
    from matplotlib.patches import Rectangle

    config = kde2d_config(layer)
    fields = kde2d_summary(columns, layer)
    if any(
        (ax.xaxis.get_scale() == "log" and any(v <= 0 for v in field.x))
        or (ax.yaxis.get_scale() == "log" and any(v <= 0 for v in field.y))
        for field in fields
    ):
        raise ValueError(
            "derived log KDE2D support must be positive; provide clip or cut"
        )
    redundant = theme.redundant_encoding and len(fields) > 1
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    hatches = itertools.cycle(theme.hatches) if redundant else itertools.repeat(None)
    refs = layer.references or {}
    for field in fields:
        color, style, hatch = (
            layer.color or next(color_iter),
            next(styles),
            next(hatches),
        )
        if field.singular and config.warn_singular:
            warnings.warn(
                f"KDE2D skipped singular/insufficient group {field.group!r}; "
                "no jitter or artificial covariance",
                UserWarning,
                stacklevel=3,
            )
        if not field.density:
            continue
        ref = refs.get(str(field.group)) if layer.group is not None else None
        label = (
            _decorate(layer.label, layer.citation, layer.href)
            if layer.group is None
            else _decorate(
                str(field.group),
                ref.citation if ref else None,
                ref.href if ref else None,
            )
        )
        density = np.asarray(field.density)
        linestyle = (
            "-"
            if layer.line_width == 0
            else (style if layer.line_style is None else layer.line_style)
        )
        if config.fill:
            rgb = to_rgb(color)
            amounts = np.linspace(0.65, 0.1, len(field.thresholds))
            shades = (
                ["none"] * len(amounts)
                if color == "none"
                else [tuple(c * (1 - a) + a for c in rgb) for a in amounts]
            )
            ax.contourf(
                field.x,
                field.y,
                density,
                levels=[*field.thresholds, float(density.max())],
                colors=shades,
                alpha=layer.alpha,
                hatches=[hatch] * len(amounts),
            )
        ax.contour(
            field.x,
            field.y,
            density,
            levels=field.thresholds,
            colors=[layer.edge_color or color if config.fill else color],
            alpha=layer.alpha,
            linewidths=layer.line_width,
            linestyles=linestyle,
        )
        # ContourSet legend support differs between mpl3.8 and3.11. Explicit
        # native legend-only proxies don't invent data or alter contour limits.
        if config.fill:
            patch = Rectangle(
                (0, 0),
                0,
                0,
                facecolor=color,
                edgecolor=layer.edge_color or color,
                linewidth=layer.line_width,
                hatch=hatch,
                alpha=layer.alpha,
            )
            ax.add_container(BarContainer([patch], label=label))
        else:
            (proxy,) = ax.plot(
                [],
                [],
                color=color,
                linestyle=linestyle,
                linewidth=layer.line_width,
                alpha=layer.alpha,
                label=label,
            )
            if layer.line_width == 0:
                proxy.set_visible(False)


def _draw_dist_layer(ax, data_cols, layer: LayerSpec, color_iter, theme):
    if layer.type == "kde2d":
        _draw_kde2d_layer(ax, data_cols, layer, color_iter, theme)
        return
    if layer.type == "kde" and layer.kde is not None:
        _draw_kde_layer(ax, data_cols, layer, color_iter, theme)
        return
    if layer.type == "hist" and layer.histogram is not None:
        _draw_histogram_layer(ax, data_cols, layer, color_iter, theme)
        return
    if layer.type == "ecdf":
        _draw_ecdf_layer(ax, data_cols, layer, color_iter, theme)
        return
    if layer.type in DISTRIBUTION_TYPES:
        _draw_categorical_distribution(ax, data_cols, layer, color_iter, theme)
        return
    data_cols = ordered_group_columns(data_cols, layer)
    masks = list(_series_masks(data_cols, layer))
    # Same rationale as the marker/line-style cycle in _draw_series_layer:
    # a hatch pattern per series keeps grouped fills (bar-like area charts)
    # distinguishable in black & white print or full achromatopsia, where
    # colour alone (even equal-lightness colour) carries no information.
    use_redundant = theme.redundant_encoding and len(masks) > 1
    hatch_cycle = (
        itertools.cycle(theme.hatches) if use_redundant else itertools.repeat(None)
    )
    style_cycle = (
        itertools.cycle(theme.line_styles) if use_redundant else itertools.repeat("-")
    )
    if layer.type == "hist":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            ax.hist(
                values,
                bins=layer.bins,
                density=layer.density,
                label=label,
                color=layer.color or next(color_iter),
                hatch=next(hatch_cycle),
                alpha=layer.alpha if layer.alpha < 1 else 0.6,
            )
    elif layer.type == "kde":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            grid, density = _gaussian_kde(values)
            ax.plot(
                grid,
                density,
                label=label,
                color=layer.color or next(color_iter),
                linewidth=layer.line_width,
                linestyle=next(style_cycle)
                if layer.line_style is None
                else layer.line_style,
                alpha=layer.alpha,
            )
    elif layer.type == "rug":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            color = layer.color or next(color_iter)
            linestyle = (
                next(style_cycle) if layer.line_style is None else layer.line_style
            )
            if layer.hue_order is not None and not np.isfinite(values).any():
                continue
            ax.vlines(
                values,
                0,
                0.04,
                transform=ax.get_xaxis_transform(),
                label=label,
                colors=color,
                linewidths=layer.line_width,
                linestyles=linestyle,
                alpha=layer.alpha,
            )


def _draw_matrix_layer(ax, spec: FigureSpec, layer: LayerSpec):
    from ._heatmap_render import draw_colourbar, draw_heatmap

    assert layer.matrix is not None
    matrix = _float_array(spec.data.matrices[layer.matrix], f"matrix {layer.matrix!r}")
    cmap = _continuous_cmap(layer.cmap_kind)
    if layer.type == "clustermap":
        from ._cluster_render import draw_clustermap

        draw_clustermap(ax, matrix, layer, cmap)
        return
    if layer.type == "heatmap":
        if layer.heatmap is None:
            im = ax.imshow(matrix, aspect="auto", cmap=cmap, alpha=layer.alpha)
        else:
            im = draw_heatmap(ax, matrix, layer, cmap)
    elif layer.type == "contour":
        im = ax.contour(matrix, levels=layer.levels or 8, cmap=cmap, alpha=layer.alpha)
    elif layer.type == "contourf":
        im = ax.contourf(matrix, levels=layer.levels or 8, cmap=cmap, alpha=layer.alpha)
    else:
        raise ValueError(f"unknown matrix layer type: {layer.type!r}")
    if layer.colorbar:
        if layer.type == "heatmap" and layer.heatmap is not None:
            draw_colourbar(ax, im, layer.clabel or "")
        else:
            ax.figure.colorbar(im, ax=ax, label=layer.clabel or "")


def _draw_pie_layer(ax, data_cols, layer: LayerSpec, color_iter):
    values = _col(data_cols, layer.y)
    raw_labels = data_cols[layer.x]
    labels = [str(v) for v in raw_labels]
    colors = (
        [layer.color] * len(values)
        if layer.color
        else [next(color_iter) for _ in values]
    )
    wedges, _texts = ax.pie(
        values, labels=labels, colors=colors, wedgeprops={"alpha": layer.alpha}
    )
    # ax.pie() sets each wedge's legend label to the slice label too, so the
    # generic "draw a legend if there are any labelled handles" logic in
    # _draw_panel would add a second, redundant legend on top of the
    # on-wedge labels already drawn above. Pie charts conventionally use
    # one or the other, not both -- suppress the legend-registration half.
    for wedge in wedges:
        wedge.set_label("_nolegend_")
    ax.set_aspect("equal")


def _draw_marker_layer(ax, ax2, layer: LayerSpec, color_iter):
    # hline/vline/text/annotate can also target the secondary y-axis (e.g. a
    # threshold line drawn against the y2 scale) -- route consistently with
    # the series layers instead of silently always drawing on the primary
    # axis regardless of ``layer.axis``.
    target = _target_axes(ax, ax2, layer)
    color = layer.color or next(color_iter)
    if layer.type == "hline":
        target.axhline(
            layer.value,
            label=layer.label,
            color=color,
            linestyle="--" if layer.line_style is None else layer.line_style,
            linewidth=layer.line_width,
            alpha=layer.alpha,
        )
    elif layer.type == "vline":
        target.axvline(
            layer.value,
            label=layer.label,
            color=color,
            linestyle="--" if layer.line_style is None else layer.line_style,
            linewidth=layer.line_width,
            alpha=layer.alpha,
        )
    elif layer.type == "text":
        assert layer.at is not None
        artist = target.text(
            layer.at[0], layer.at[1], layer.text or "", color=color, alpha=layer.alpha
        )
        # Data-coordinate text confuses constrained_layout's space-reservation
        # solve (its position isn't known until the axes limits are, which
        # are themselves part of what's being solved) -- exclude it, same as
        # matplotlib's own docs recommend for in-axes annotations.
        artist.set_in_layout(False)
    elif layer.type == "annotate":
        assert layer.at is not None
        # Preserve default RGBA colour opacity; non-default alpha overrides both parts.
        alpha = None if layer.alpha == 1 else layer.alpha
        artist = target.annotate(
            layer.text or "",
            xy=tuple(layer.to or layer.at),
            xytext=tuple(layer.at),
            color=color,
            alpha=alpha,
            arrowprops={"arrowstyle": "->", "color": color, "alpha": alpha}
            if layer.to
            else None,
        )
        artist.set_in_layout(False)
    else:
        raise ValueError(f"unknown layer type: {layer.type!r}")


def _draw_3d_layer(ax, spec: FigureSpec, layer: LayerSpec, color_iter):
    data_cols = spec.data.columns
    if layer.type in ("scatter3d", "line3d"):
        masks = list(_series_masks(data_cols, layer))
        norm = _color_norm(data_cols, layer) if layer.c is not None else None
        sc = None
        for label, mask in masks:
            x = _col(data_cols, layer.x)[mask]
            y = _col(data_cols, layer.y)[mask]
            z = _col(data_cols, layer.z)[mask]
            if layer.type == "scatter3d":
                if layer.c is not None:
                    values = _col(data_cols, layer.c)[mask]
                    sc = ax.scatter(
                        x,
                        y,
                        z,
                        c=values,
                        cmap=_continuous_cmap(layer.cmap_kind),
                        norm=norm,
                        label=label,
                        s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                        marker="o" if layer.marker is None else layer.marker,
                        alpha=layer.alpha,
                    )
                else:
                    color = layer.color or next(color_iter)
                    ax.scatter(
                        x,
                        y,
                        z,
                        label=label,
                        color=color,
                        s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                        marker="o" if layer.marker is None else layer.marker,
                        alpha=layer.alpha,
                    )
            else:  # line3d
                color = layer.color or next(color_iter)
                ax.plot(
                    x,
                    y,
                    z,
                    label=label,
                    color=color,
                    linewidth=layer.line_width,
                    linestyle="-" if layer.line_style is None else layer.line_style,
                    marker=layer.marker,
                    markersize=layer.marker_size,
                    alpha=layer.alpha,
                )
        if sc is not None and layer.colorbar:
            ax.figure.colorbar(sc, ax=ax, label=layer.clabel or "")
    elif layer.type in ("surface", "wireframe"):
        assert layer.matrix is not None
        matrix = _float_array(
            spec.data.matrices[layer.matrix], f"matrix {layer.matrix!r}"
        )
        ny, nx = matrix.shape
        xs, ys = np.meshgrid(np.arange(nx), np.arange(ny))
        if layer.type == "surface":
            surf = ax.plot_surface(
                xs,
                ys,
                matrix,
                cmap=_continuous_cmap(layer.cmap_kind),
                alpha=layer.alpha,
            )
            if layer.colorbar:
                ax.figure.colorbar(surf, ax=ax, label=layer.clabel or "")
        else:
            color = layer.color or next(color_iter)
            ax.plot_wireframe(xs, ys, matrix, color=color, alpha=layer.alpha)


def _apply_axis(ax, axis_spec, set_label, set_scale, set_limits):
    set_label(axis_spec.label)
    # Setting even the existing linear scale resets categorical tick locators.
    if axis_spec.scale != "linear":
        set_scale(axis_spec.scale)
    if axis_spec.limits:
        set_limits(axis_spec.limits)


def _legend_kwargs(leg, *, fig) -> tuple[dict, bool]:
    """Build ax.legend() placement kwargs, honouring a dragged/explicit
    ``bbox_to_anchor`` override in figure-fraction coordinates (independent
    of the axes' own position, so it stays put if the axes later resize).

    Returns ``(kwargs, auto_margin)``: ``auto_margin`` tells the caller
    whether ``_autofit`` should reserve canvas space for this legend. An
    explicit ``bbox_to_anchor`` (e.g. dragged in the interactive editor) is
    trusted as-is -- the user may deliberately want it overlapping the plot
    -- so only the named "outside ..." locations get automatic margin.
    """
    if leg.bbox_to_anchor is not None:
        return {
            "loc": "center",
            "bbox_to_anchor": tuple(leg.bbox_to_anchor),
            "bbox_transform": fig.transFigure,
        }, False
    kw = dict(_OUTSIDE_LEGEND_LOCS.get(leg.location, {"loc": leg.location}))
    return kw, leg.location in _OUTSIDE_LEGEND_LOCS


def _apply_title(ax, panel: PanelSpec) -> None:
    if not panel.title:
        return
    title_text = _decorate(
        panel.title, panel.title_citation, panel.title_href, widen=False
    )
    if panel.title_position is not None:
        # A real ax.set_title() is specially managed by constrained_layout
        # (which recomputes its y-offset transform on every draw, silently
        # discarding any manual set_position()); a plain axes-fraction
        # text artist isn't, so a drag/explicit override uses that instead.
        import matplotlib.pyplot as plt

        fontsize = plt.rcParams["axes.titlesize"]
        artist = ax.text(
            *panel.title_position,
            title_text,
            transform=ax.transAxes,
            fontsize=fontsize,
            wrap=True,
        )
        artist.set_in_layout(False)
    else:
        title_axes = getattr(ax, "_mudplot_cluster_title_axes", ax)
        artist = title_axes.set_title(title_text, wrap=True)
    _set_url(artist, panel.title_href)


def _apply_despine(ax, theme_axes):
    for char, side in _SPINE_SIDES.items():
        if char in theme_axes.spines and theme_axes.spine_offset and side in ax.spines:
            ax.spines[side].set_position(("outward", theme_axes.spine_offset))


def _raw_legend_handles(ax, ax2=None):
    handles, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        other_handles, other_labels = ax2.get_legend_handles_labels()
        handles, labels = handles + other_handles, labels + other_labels
    return handles, labels


def _mark_legend_source(layer: LayerSpec, handles, previous) -> None:
    if (
        layer.type not in ("line", "scatter", "line3d", "scatter3d")
        or not layer.label
        or layer.group is not None
        or layer.semantics is not None
    ):
        return
    key = (
        layer.axis,
        layer.x,
        layer.y,
        layer.z,
        layer.label,
        layer.citation,
        layer.href,
    )
    for handle in handles:
        if id(handle) not in previous:
            handle._mudplot_legend_source = key


def _unique_legend_handles(handles, labels):
    seen = set()
    result_handles, result_labels = [], []
    for handle, label in zip(handles, labels, strict=True):
        key = getattr(handle, "_mudplot_legend_source", None)
        if key is None or key not in seen:
            result_handles.append(handle)
            result_labels.append(label)
            if key is not None:
                seen.add(key)
    return result_handles, result_labels


def _draw_panel_3d(ax, spec: FigureSpec, panel: PanelSpec):
    import matplotlib.pyplot as plt

    prop = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0"])
    color_iter = itertools.cycle(prop)

    for layer in panel.layers:
        previous = {id(handle) for handle in _raw_legend_handles(ax)[0]}
        _draw_3d_layer(ax, spec, layer, color_iter)
        _mark_legend_source(layer, _raw_legend_handles(ax)[0], previous)

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim)
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim)
    if panel.z is not None:
        _apply_axis(ax, panel.z, ax.set_zlabel, ax.set_zscale, ax.set_zlim)
    _apply_title(ax, panel)

    handles, labels = _unique_legend_handles(*_raw_legend_handles(ax))
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(leg, fig=ax.figure)
        legend_artist = ax.legend(
            handles, labels, title=leg.title, frameon=leg.frame, **kw
        )
        legend_artist._mudplot_auto_margin = auto_margin
        _link_legend_texts(legend_artist, panel)


def _draw_panel(ax, spec: FigureSpec, panel: PanelSpec, *, domains=None):
    import matplotlib.pyplot as plt

    if panel.projection == "3d":
        _draw_panel_3d(ax, spec, panel)
        return
    if panel.filters or panel.dropna:
        spec = replace(
            spec,
            data=replace(spec.data, columns=panel_columns(spec.data.columns, panel)),
        )

    prop = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0"])
    domains = {} if domains is None else domains
    shared_colors = sum(d["colors"] for d in domains.values())
    color_iter = itertools.cycle(prop[shared_colors:] or prop)
    shown_scales = set()
    theme = spec.theme

    # Geometry and optional axis-space statistics need the declared transforms
    # before drawing, not only during final labels/limits application.
    ax.set_xscale(panel.x.scale)
    ax.set_yscale(panel.y.scale)
    ax2 = ax.twinx() if panel.y2 is not None else None

    for layer in panel.layers:
        previous = {id(handle) for handle in _raw_legend_handles(ax, ax2)[0]}
        if layer.type in ("scatter", "lineplot") and layer.semantics is not None:
            scale_id = layer.semantics.scale_id
            guide_key = (scale_id, layer.type)
            show_guides = scale_id is None or guide_key not in shown_scales
            if scale_id is not None and layer.semantics.legend:
                shown_scales.add(guide_key)
            draw = _draw_stat_layer if layer.type == "lineplot" else _draw_series_layer
            draw(
                ax,
                ax2,
                spec.data.columns,
                layer,
                color_iter,
                theme,
                semantic_domain=domains.get(scale_id),
                semantic_guides=show_guides,
            )
        elif layer.type == "swarmplot":
            _draw_swarm_layer(ax, spec.data.columns, layer, color_iter)
        elif layer.type in _STAT_TYPES:
            _draw_stat_layer(ax, ax2, spec.data.columns, layer, color_iter, theme)
        elif layer.type in _SERIES_TYPES:
            _draw_series_layer(ax, ax2, spec.data.columns, layer, color_iter, theme)
        elif layer.type in _DIST_TYPES:
            _draw_dist_layer(ax, spec.data.columns, layer, color_iter, theme)
        elif layer.type in _MATRIX_TYPES:
            _draw_matrix_layer(ax, spec, layer)
        elif layer.type in _STANDALONE_TYPES:
            _draw_pie_layer(ax, spec.data.columns, layer, color_iter)
        else:
            _draw_marker_layer(ax, ax2, layer, color_iter)
        _mark_legend_source(layer, _raw_legend_handles(ax, ax2)[0], previous)

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim)
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim)
    if panel.y2 is not None:
        assert ax2 is not None
        _apply_axis(ax2, panel.y2, ax2.set_ylabel, ax2.set_yscale, ax2.set_ylim)
    _apply_title(ax, panel)
    _apply_despine(ax, theme.axes)

    handles, labels = _unique_legend_handles(*_raw_legend_handles(ax, ax2))
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(leg, fig=ax.figure)
        legend_artist = ax.legend(
            handles, labels, title=leg.title, frameon=leg.frame, **kw
        )
        legend_artist._mudplot_auto_margin = auto_margin
        if ax2 is not None and auto_margin and leg.location == "outside right":
            legend_artist._mudplot_secondary_axis = ax2
        _link_legend_texts(legend_artist, panel)


def _panel_label(index: int) -> str:
    # a, b, c, ... z, aa, ab, ... (spreadsheet-style, in case of >26 panels)
    letters = ""
    n = index
    while True:
        n, r = divmod(n, 26)
        letters = chr(97 + r) + letters
        if n == 0:
            break
        n -= 1
    return letters


def _apply_panel_label(ax, spec: FigureSpec, panel: PanelSpec, index: int):
    import matplotlib.pyplot as plt

    label = panel.label
    if label is None and spec.auto_label_panels:
        label = _panel_label(index)
    if label:
        # Read the *effective* title size from the active rcParams rather
        # than spec.theme.font.title_size directly: a journal preset
        # overrides the theme's font sizes via rcParams (see theme.py), and
        # this function runs inside that rc_context, so this keeps panel
        # labels visually consistent with the (possibly journal-overridden)
        # panel titles instead of silently ignoring the override.
        fontsize = plt.rcParams.get("axes.titlesize", spec.theme.font.title_size)
        text = ax.text2D if panel.projection == "3d" else ax.text
        text(
            -0.12,
            1.05,
            f"{label})",
            transform=ax.transAxes,
            fontsize=fontsize,
            fontweight="bold",
            ha="left",
            va="bottom",
        )


def _grid_shape(spec: FigureSpec) -> tuple[int, int]:
    if spec.layout:
        return spec.layout[0], spec.layout[1]
    return 1, len(spec.panels)


def _count_colors(spec: FigureSpec, *, domains=None) -> int:
    domains = shared_scale_domains(spec) if domains is None else domains
    shared_colors = sum(d["colors"] for d in domains.values())
    counts = []
    for p in spec.panels:
        columns = panel_columns(spec.data.columns, p)
        count = 0
        for lyr in p.layers:
            if lyr.color or lyr.type in _MATRIX_TYPES | {
                "surface",
                "hist2d",
                "hexbin",
            }:
                continue
            if lyr.type in {"scatter", "scatter3d", "quiver"} and lyr.c is not None:
                continue
            if lyr.type in RAW_HUE_TYPES and isinstance(lyr.hue_order, (list, tuple)):
                count += len(lyr.hue_order)
            elif lyr.type in ("scatter", "lineplot") and lyr.semantics is not None:
                config = lyr.semantics
                if config.hue is None:
                    count += 1
                elif config.hue_kind == "categorical" and config.scale_id is None:
                    rows = semantic_rows(columns, lyr)
                    count += len(semantic_levels(columns, config, "hue", rows))
            elif lyr.type == "pie":
                count += len(columns[lyr.y])
            elif lyr.type == "hist" and lyr.histogram is not None:
                rows = histogram_rows(columns, lyr)
                count += len(histogram_groups(columns, lyr, rows))
            elif lyr.type == "kde2d":
                rows = kde2d_rows(columns, lyr)
                count += len(kde2d_groups(columns, lyr, rows))
            elif lyr.type == "kde" and lyr.kde is not None:
                rows = kde_rows(columns, lyr)
                count += len(kde_groups(columns, lyr, rows))
            elif lyr.type == "ecdf":
                rows = ecdf_rows(columns, lyr)
                count += len(ecdf_groups(columns, lyr, rows))
            elif lyr.type in DISTRIBUTION_TYPES | {"swarmplot"}:
                rows = distribution_rows(columns, lyr)
                categories, groups = distribution_levels(columns, lyr, rows)
                count += len(groups if lyr.y else categories)
            elif lyr.group and lyr.group in columns:
                if lyr.type in _STAT_TYPES:
                    rows = usable_rows(columns, lyr)
                    count += len(category_levels(columns, lyr, rows)[1])
                else:
                    count += len(_unique_stable(columns[lyr.group]))
            else:
                count += 1
        counts.append(count)
    return shared_colors + max(counts, default=1)


def _link_shared_axes(axes_grid, rows: int, cols: int, mode: str, axis: str) -> None:
    """Emulate plt.subplots(sharex=...)'s "none"/"all"/"row"/"col" modes,
    but after the fact -- needed because 3-D-capable panels are built with
    fig.add_subplot() one at a time instead of plt.subplots(), which is the
    only way to give each panel its own projection.
    """
    if mode == "none":
        return

    def link(ax, base):
        (ax.sharex if axis == "x" else ax.sharey)(base)

    if mode == "all":
        base = next((a for row in axes_grid for a in row if a is not None), None)
        if base is None:
            return
        for row in axes_grid:
            for ax in row:
                if ax is not None and ax is not base:
                    link(ax, base)
    elif mode == "row":
        for row in axes_grid:
            base = next((a for a in row if a is not None), None)
            if base is None:
                continue
            for ax in row:
                if ax is not None and ax is not base:
                    link(ax, base)
    elif mode == "col":
        for c in range(cols):
            column = [axes_grid[r][c] for r in range(rows)]
            base = next((a for a in column if a is not None), None)
            if base is None:
                continue
            for ax in column:
                if ax is not None and ax is not base:
                    link(ax, base)


def _link_named_axes(axes, panels, axis: str) -> None:
    groups = {}
    for ax, panel in zip(axes, panels, strict=True):
        name = getattr(panel, axis).share_id
        if name is None:
            continue
        base = groups.setdefault(name, ax)
        if ax is not base:
            (ax.sharex if axis == "x" else ax.sharey)(base)


def _align_secondary_legends(fig, pad_px: float) -> bool:
    from matplotlib.transforms import ScaledTranslation

    renderer = fig.canvas.get_renderer()
    moved = False
    for ax in fig.axes:
        legend = ax.get_legend()
        secondary = getattr(legend, "_mudplot_secondary_axis", None)
        if secondary is None or ax.bbox.width <= 0:
            continue
        texts = [
            secondary.yaxis.label,
            secondary.yaxis.get_offset_text(),
            *secondary.get_yticklabels(),
        ]
        edge = max(
            (
                text.get_window_extent(renderer).x1
                for text in texts
                if text.get_visible() and text.get_text()
            ),
            default=ax.bbox.x1,
        )
        shift = edge + pad_px - legend.get_window_extent(renderer).x0
        if shift > 1:
            # Keep the decoration gap physical while constrained layout resizes axes.
            offset = (edge + pad_px - ax.bbox.x1) / fig.dpi
            transform = ax.transAxes + ScaledTranslation(offset, 0, fig.dpi_scale_trans)
            legend.set_bbox_to_anchor((1, 0.5), transform=transform)
            moved = True
    return moved


def _autofit(fig, pad_inches: float = 0.02) -> None:
    """Fit automatic text where possible and warn about remaining bounds/overlaps,
    while keeping the figure at its exact configured size (needed for TeX
    column-width placement -- see ``mudplot.tex``).

    Two stages, using matplotlib's own accurate text-measurement renderer.
    Secondary right-axis legend gaps settle in at most three preliminary draws:

    1. Reserve canvas space for any *named* "outside ..." legend (not an
       explicit/dragged ``bbox_to_anchor``, which is trusted as-is) by
       shrinking the constrained-layout engine's working rectangle --
       constrained_layout still does its own tick-label-aware spacing
       *inside* that smaller rectangle, so this doesn't reimplement that.
    2. Panel titles/suptitle already wrap (``wrap=True``) at the figure
       width via matplotlib's native text layout; this only needs to ask
       for a redraw after step 1 changes that width.
    """
    pad_px = pad_inches * fig.dpi
    for _ in range(3):
        fig.canvas.draw()
        if not _align_secondary_legends(fig, pad_px):
            break
    renderer = fig.canvas.get_renderer()
    fig_w, fig_h = fig.bbox.width, fig.bbox.height

    left, bottom, right, top = 0.0, 0.0, 1.0, 1.0
    changed = False
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is None or not getattr(legend, "_mudplot_auto_margin", False):
            continue
        bb = legend.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        if bb.x1 > 1:
            right = min(right, 1 - (bb.x1 - 1) - pad_px / fig_w)
            changed = True
        if bb.x0 < 0:
            left = max(left, -bb.x0 + pad_px / fig_w)
            changed = True
        if bb.y1 > 1:
            top = min(top, 1 - (bb.y1 - 1) - pad_px / fig_h)
            changed = True
        if bb.y0 < 0:
            bottom = max(bottom, -bb.y0 + pad_px / fig_h)
            changed = True

    if (
        changed
        and fig.get_layout_engine() is not None
        and right > left
        and top > bottom
    ):
        fig.get_layout_engine().set(rect=(left, bottom, right - left, top - bottom))

    # Re-draw so wrapped titles measure against the (possibly now smaller)
    # available width; harmless no-op if nothing changed above.
    fig.canvas.draw()
    if _align_secondary_legends(fig, pad_px):
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    automatic = [ax.title for ax in fig.axes if ax.title.get_text()]
    if fig._suptitle is not None and fig._suptitle.get_text():
        automatic.append(fig._suptitle)
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is not None and getattr(legend, "_mudplot_auto_margin", False):
            automatic.append(legend)
    boxes = [artist.get_window_extent(renderer) for artist in automatic]
    outside = any(
        bb.x0 < fig.bbox.x0 - 1
        or bb.y0 < fig.bbox.y0 - 1
        or bb.x1 > fig.bbox.x1 + 1
        or bb.y1 > fig.bbox.y1 + 1
        for bb in boxes
    )
    overlap = any(
        min(a.x1, b.x1) - max(a.x0, b.x0) > 1 and min(a.y1, b.y1) - max(a.y0, b.y0) > 1
        for index, a in enumerate(boxes)
        for b in boxes[index + 1 :]
    )
    if outside or overlap:
        warnings.warn(
            "automatic layout text cannot fit the fixed canvas without clipping or "
            "overlap; add explicit line breaks, increase figure size or reduce text/"
            "font size. Canvas size is unchanged; "
            "manual positions remain caller-owned.",
            UserWarning,
            stacklevel=2,
        )


@matplotlib_context()
def render(spec: FigureSpec, *, fmt: str = ""):
    """Build and return a matplotlib Figure for ``spec``.

    ``fmt`` is the output format the figure is destined for ("svg", "pgf",
    ...), which only affects how layer/title reference metadata
    (``citation``/``href``) is rendered; ``save()`` sets it from the file
    extension.

    Raises ``ValueError`` (with all issues listed) if ``spec`` is invalid —
    see :mod:`mudplot.validate`.
    """
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as error:
        if error.name not in ("numpy", "matplotlib"):
            raise
        raise ImportError(
            "rendering requires 'mudplot[render]'; install it first"
        ) from error

    assert_valid(spec)
    domains = shared_scale_domains(spec)

    rc = spec_to_rcparams(
        spec.theme, spec.journal, n_colors=max(_count_colors(spec, domains=domains), 3)
    )

    with plt.rc_context(rc), _render_format(fmt, spec.reference_measure_text or ""):
        rows, cols = _grid_shape(spec)
        gridspec_kw = {}
        if spec.width_ratios:
            gridspec_kw["width_ratios"] = spec.width_ratios
        if spec.height_ratios:
            gridspec_kw["height_ratios"] = spec.height_ratios

        # Built with fig.add_subplot() (one call per panel) rather than
        # plt.subplots(), which can't give individual panels their own
        # projection (needed for 3-D panels mixed with 2-D ones).
        #
        # constrained_layout (+ _autofit below) gives precise, overlap-free
        # spacing for 2-D panels, but matplotlib's 3-D Axes don't support it
        # well (e.g. the z-axis label routinely gets clipped) -- fall back
        # to the older tight_layout() pass for any figure containing a 3-D
        # panel rather than regress that case.
        has_3d = any(p.projection == "3d" for p in spec.panels)
        fig = plt.figure(
            figsize=tuple(spec.size),
            dpi=spec.dpi,
            layout=None if has_3d else "constrained",
        )
        # Interactive HiDPI backends may round inches to device pixels.
        fig.set_size_inches((spec.size[0], spec.size[1]), forward=False)
        try:
            gs = fig.add_gridspec(rows, cols, **gridspec_kw)
            axes_grid: list[list[object | None]] = [[None] * cols for _ in range(rows)]
            panel_axes = []
            for i, panel in enumerate(spec.panels):
                r, c = divmod(i, cols)
                projection = None if panel.projection == "2d" else panel.projection
                ax = fig.add_subplot(gs[r, c], projection=projection)
                if projection == "polar":
                    cast(Any, ax).set_rlabel_position(90)
                if projection is None:
                    axes_grid[r][c] = ax
                # Which panel this Axes came from. fig.axes also collects
                # twin/colorbar axes created later, so position in that list
                # is not the panel index -- tools that map a rendered Axes
                # back to its spec (e.g. the editor's drag handles) need
                # this rather than guessing.
                cast(Any, ax)._mudplot_panel = i
                panel_axes.append(ax)

            # Share the 2-D subset, even when other panels are 3-D.
            _link_shared_axes(axes_grid, rows, cols, spec.share_x, "x")
            _link_shared_axes(axes_grid, rows, cols, spec.share_y, "y")
            _link_named_axes(panel_axes, spec.panels, "x")
            _link_named_axes(panel_axes, spec.panels, "y")

            for i, (ax, panel) in enumerate(zip(panel_axes, spec.panels, strict=False)):
                _draw_panel(ax, spec, panel, domains=domains)
                _apply_panel_label(ax, spec, panel, i)

            if spec.suptitle:
                fig.suptitle(spec.suptitle, wrap=True)
            if has_3d:
                fig.tight_layout()
            else:
                _autofit(fig)
            if any(
                layer.type == "clustermap"
                for panel in spec.panels
                for layer in panel.layers
            ):
                from ._cluster_render import freeze_layout

                freeze_layout(fig)
            # Reference table for this figure's markers, needed after the
            # render context exits (see save()'s .pgf post-processing).
            cast(Any, fig)._mudplot_refs = list(_REFS.get() or [])
            cast(Any, fig)._mudplot_ref_measure = spec.reference_measure_text or ""
        except Exception:
            plt.close(fig)
            raise
    return fig


def _require_texsystem() -> None:
    """PGF export shells out to a real TeX engine (matplotlib measures text
    with it), so fail with an actionable message rather than the backend's
    bare FileNotFoundError deep in a savefig call.
    """
    import shutil

    import matplotlib as mpl

    texsystem = mpl.rcParams["pgf.texsystem"]
    if shutil.which(texsystem) is None:
        raise RuntimeError(
            f".pgf export needs a TeX installation: {texsystem!r} was not found "
            "on PATH. Install TeX Live/MacTeX, or point "
            "matplotlib.rcParams['pgf.texsystem'] at an available engine "
            "(e.g. 'pdflatex'). Other formats (.pdf/.svg/.png) need no TeX."
        )


def _preview_dpi(spec: FigureSpec, *, max_dimension: int = 2000) -> float:
    """Bound editor preview pixels without changing the saved FigureSpec."""
    return min(spec.dpi, max_dimension / max(spec.size))


def _save_figure(fig, spec: FigureSpec, destination, fmt: str, *, tight=False) -> None:
    """Save deterministic bytes for the supported publication formats."""
    import matplotlib.pyplot as plt

    rc: dict[str, Any] = {"savefig.bbox": None}
    kwargs: dict[str, Any] = {
        "dpi": spec.dpi,
        "bbox_inches": "tight" if tight else None,
        "pad_inches": 0.05,
    }
    if fmt:
        kwargs["format"] = fmt
    if fmt == "pdf":
        kwargs["metadata"] = {"CreationDate": None, "ModDate": None}
    elif fmt == "svg":
        from .io import to_json

        rc["svg.image_inline"] = True
        digest = hashlib.sha256(
            to_json(spec, indent=None, sort_keys=True).encode()
        ).hexdigest()
        rc["svg.hashsalt"] = f"mudplot-{digest}"
        kwargs["metadata"] = {"Date": None}
    with plt.rc_context(cast(Any, rc)):
        fig.savefig(destination, **kwargs)


@matplotlib_context()
def save(spec: FigureSpec, path: str, *, tight: bool = False):
    """Save at the exact spec size; ``tight=True`` opts into content cropping.

    The extension picks the backend, including ``.pgf`` for LaTeX-native
    export (where ``citation``/``href`` metadata becomes real \\figcite /
    \\href macros -- see :data:`mudplot.tex.PREAMBLE`).

    Returns an open Figure, owned by the caller, on success.
    """
    import pathlib

    try:
        import matplotlib as mpl
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as error:
        if error.name not in ("numpy", "matplotlib"):
            raise
        raise ImportError(
            "rendering requires 'mudplot[render]'; install it first"
        ) from error

    from .io import _atomic_destination

    destination = pathlib.Path(path)
    fmt = destination.suffix.lstrip(".").lower()
    if not fmt:
        fmt = str(mpl.rcParams["savefig.format"])
        destination = destination.with_name(f"{destination.name}.{fmt}")
    if fmt == "pgf":
        _require_texsystem()
    fig = render(spec, fmt=fmt)
    try:
        if fmt == "pgf":
            # ponytail: PGF may emit sidecar PNGs; stage the whole bundle if
            # transactional PGF export becomes necessary.
            _save_figure(fig, spec, destination, fmt, tight=tight)
            destination.write_bytes(
                _substitute_pgf_references(
                    destination.read_text(encoding="utf-8"),
                    getattr(fig, "_mudplot_refs", []),
                    getattr(fig, "_mudplot_ref_measure", ""),
                ).encode("utf-8")
            )
        else:
            with _atomic_destination(destination) as temporary:
                _save_figure(fig, spec, temporary, fmt, tight=tight)
    except BaseException:
        plt.close(fig)
        raise
    return fig
