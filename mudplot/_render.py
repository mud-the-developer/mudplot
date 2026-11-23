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
import math
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

from ._axis_options import NEW_SCALES
from ._box import advanced_box
from ._boxen import advanced_boxen, prepare_boxen_plans
from ._categorical import (
    DISTRIBUTION_TYPES,
    ClockCategoryArgs,
    distribution_columns,
    distribution_levels,
    distribution_rows,
    native_category_geometry,
)
from ._ecdf import ecdf_config, ecdf_groups, ecdf_rows, empirical_steps
from ._facet import RAW_HUE_TYPES, ordered_group_columns, panel_columns, panel_rows
from ._histogram import histogram_groups, histogram_rows, histogram_summary
from ._kde import kde_groups, kde_rows, kde_summary
from ._kde2d import kde2d_config, kde2d_groups, kde2d_rows, kde2d_summary
from ._lanes import advanced_lanes, lane_members
from ._layout_render import native_axes, nested_tight_layout_engine
from ._mpl_context import matplotlib_context
from ._semantics import (
    ROLE_LAYER_TYPES,
    category_key,
    semantic_levels,
    semantic_rows,
    shared_scale_domains,
)
from ._spatial import SPATIAL_TYPES, uses_spatial
from ._stairs import advanced_stairs, stair_groups
from ._stat import (
    STAT_LAYER_TYPES,
    category_levels,
    new_stat_request,
    stat_config,
    stat_key,
    usable_rows,
)
from ._strip import categorical_strip
from ._tri_field import TRI_TYPES
from ._vector import uses_vector, vector_members
from ._violin_options import advanced_violin
from .spec import MAX_RENDER_PIXELS, FigureSpec, LayerSpec, PanelSpec
from .theme import spec_to_rcparams
from .validate import assert_valid

__all__ = ["render", "save"]

# Layer types drawing x/y series; grouping is kind-specific.
_SERIES_TYPES = {
    "line",
    "stem",
    "stairs",
    "eventplot",
    "broken_barh",
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
_MATRIX_TYPES = {
    "heatmap",
    "clustermap",
    "contour",
    "contourf",
    "imshow",
    "pcolor",
    "pcolormesh",
    "spy",
}
# layer types only meaningful on a projection="3d" panel
_3D_TYPES = SPATIAL_TYPES | {
    "scatter3d",
    "line3d",
    "surface",
    "wireframe",
    "trisurf",
    "quiver3d",
}
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
    A native Text can emit several independent ``pgftext`` groups. Balance
    each link inside those generated font/style envelopes, not across them;
    the final citation stays at its existing marker outside the link.
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

    if not any(kind == "href" for kind, _ in refs):
        return pattern.sub(repl, text)

    def native_payload(line: str, prefix: str | None = None):
        """Split only Matplotlib's generated text envelope, not user TeX."""
        content = line.rstrip("\r\n")
        newline = line[len(content) :]
        head, delimiter, body = content.partition("]{")
        if not head.startswith(r"\pgftext[") or not delimiter:
            raise ValueError("unrecognized native PGF reference text envelope")
        if prefix is None:
            opening = next(
                (
                    match
                    for match in pattern.finditer(body)
                    if int(match.group(1)) < len(refs)
                    and refs[int(match.group(1))][0] == "href"
                ),
                None,
            )
            if opening is None:
                raise ValueError("missing native PGF reference opening marker")
            # Everything before this first marker is generated by the native
            # backend: colour, font selection and its local catcode setup.
            prefix = body[: opening.start()]
        depth = 1 + prefix.count("{") - prefix.count("}")
        suffix = "}" * depth + "%"
        if depth < 1 or not body.startswith(prefix) or not body.endswith(suffix):
            raise ValueError("unrecognized native PGF reference font/style envelope")
        return (
            head + delimiter + prefix,
            body[len(prefix) : -len(suffix)],
            suffix + newline,
            prefix,
        )

    result = []
    active: tuple[str, str] | None = None
    for line in text.splitlines(keepends=True):
        markers = [
            (match, refs[int(match.group(1))])
            for match in pattern.finditer(line)
            if int(match.group(1)) < len(refs)
        ]
        closes = any(kind == "/href" for _, (kind, _) in markers)
        if active is not None and line.startswith(r"\pgftext["):
            href, prefix = active
            head, body, tail, _ = native_payload(line, prefix)
            body = f"\\href{{{href}}}{{" + pattern.sub(repl, body)
            result.append(head + body + ("" if closes else "}") + tail)
            if closes:
                active = None
        elif active is None:
            opening = next(
                (value for _, (kind, value) in markers if kind == "href"), None
            )
            if opening is not None and not closes:
                head, body, tail, prefix = native_payload(line)
                result.append(head + pattern.sub(repl, body) + "}" + tail)
                active = opening, prefix
            else:
                result.append(pattern.sub(repl, line))
        else:
            result.append(pattern.sub(repl, line))
    if active is not None:
        raise ValueError("unterminated native PGF reference")
    return "".join(result)


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


def _x_values(ax, data_cols, name, *, horizontal=False):
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
        axis = ax.yaxis if horizontal else ax.xaxis
        convert = ax.convert_yunits if horizontal else ax.convert_xunits
        axis.update_units(str_values)
        positions = np.full(len(raw), np.nan)
        positions[present] = np.asarray(convert(str_values), dtype=float)
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


def _regression_fit(
    x, y, degree: int, confidence: float | None, *, at=None, weights=None
):
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
            if weights is not None:
                if confidence is not None:
                    raise ValueError("weighted confidence bands are not supported")
                weight = np.asarray(weights, dtype=float)
                if (
                    weight.shape != x.shape
                    or not np.isfinite(weight).all()
                    or np.any(weight <= 0)
                ):
                    raise ValueError(
                        "selected regression weights must be finite positive"
                    )
                with np.errstate(under="ignore"):
                    relative = weight / float(weight.max())
                if np.any(relative <= 0):
                    raise ValueError(
                        "relative regression weights are not representable"
                    )
                coefficients = np.polyfit(
                    x_scaled, response, degree, w=np.sqrt(relative)
                )
            elif confidence is None:
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


def _scatter_outline(layer):
    options = {}
    if layer.edge_color is not None:
        options["edgecolors"] = layer.edge_color
    if layer.line_width is not None:
        options["linewidths"] = layer.line_width
    return options


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
    scalar=None,
):
    if layer.type == "stem":
        from ._stem_render import draw_stems

        return draw_stems(
            _target_axes(ax, ax2, layer),
            data_cols,
            layer,
            color_iter,
            domain=semantic_domain,
        )
    if layer.type == "line":
        from ._line import categorical_predictor

        if layer.semantics is not None:
            from ._line_semantics import draw_semantic_curves

            return draw_semantic_curves(
                _target_axes(ax, ax2, layer),
                data_cols,
                layer,
                color_iter,
                theme,
                domain=semantic_domain,
                guides=semantic_guides,
            )
        if (
            layer.orient == "h"
            or layer.line is not None
            or categorical_predictor(layer)
            or layer.order is not None
        ):
            from ._lineplot import draw_raw_lines

            return draw_raw_lines(
                _target_axes(ax, ax2, layer), data_cols, layer, color_iter, theme
            )
    if layer.type == "scatter" and layer.semantics is not None:
        from ._scatter_semantics import draw_semantic_scatter

        return draw_semantic_scatter(
            _target_axes(ax, ax2, layer),
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
    if layer.type == "stairs":
        return target.stairs(
            _col(data_cols, layer.x),
            layer.bins,
            baseline=0 if layer.baseline is None else layer.baseline,
            fill=False,
            color=layer.color or next(color_iter),
            linewidth=layer.line_width,
            linestyle=layer.line_style or "-",
            alpha=layer.alpha,
            label=_decorate(layer.label, layer.citation, layer.href),
        )

    if layer.type == "eventplot":
        return target.eventplot(
            _col(data_cols, layer.x),
            orientation="horizontal",
            lineoffsets=0 if layer.baseline is None else layer.baseline,
            linelengths=1 if layer.width is None else layer.width,
            colors=layer.color or next(color_iter),
            linewidths=layer.line_width,
            # Matplotlib 3.8 rejects zero-width dashed legend handles.
            linestyles="-" if layer.line_width == 0 else layer.line_style or "-",
            alpha=layer.alpha,
            label=_decorate(layer.label, layer.citation, layer.href),
        )

    if layer.type == "broken_barh":
        color = layer.color or next(color_iter)
        return target.broken_barh(
            np.column_stack((_col(data_cols, layer.x), _col(data_cols, layer.y))),
            (
                0 if layer.baseline is None else layer.baseline,
                1 if layer.width is None else layer.width,
            ),
            facecolors=color,
            edgecolors=layer.edge_color or color,
            linewidths=layer.line_width,
            linestyles="-" if layer.line_width == 0 else layer.line_style or "-",
            alpha=layer.alpha,
            label=_decorate(layer.label, layer.citation, layer.href),
        )

    x_all = _x_values(target, data_cols, layer.x)
    if scalar is not None:
        norm = scalar["norm"]
    else:
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
        if layer.native_style is not None and layer.native_style.marker is not None:
            marker = layer.native_style.marker
        if layer.hue_order is not None and not np.any(np.isfinite(x) & np.isfinite(y)):
            if not layer.color:
                next(color_iter)
            if layer.type == "bar":
                next(hatch_cycle)
            continue
        handle = None
        if layer.type == "line":
            color = layer.color or next(color_iter)
            (handle,) = target.plot(
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
            if layer.native_style is not None:
                from ._components import apply_component_style

                apply_component_style(handle, layer.native_style)
            if layer.path_effects is not None:
                from ._native_annotations import apply_path_effects

                apply_path_effects(handle, layer.path_effects)
        elif layer.type == "regplot":
            color = layer.color or next(color_iter)
            weights = None
            if layer.weights is not None:
                weights = _col(data_cols, layer.weights)[mask]
                positive = weights > 0
                x, y, weights = x[positive], y[positive], weights[positive]
            config = layer.regression
            if config is None:
                grid, fitted, interval = _regression_fit(
                    x, y, layer.degree, layer.confidence
                )
            else:
                from ._regression_render import fit_regression

                grid, fitted, interval = fit_regression(
                    x,
                    y,
                    layer,
                    _regression_fit,
                    at=x if config.residual else None,
                    weights=weights,
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
            outline = _scatter_outline(layer)
            if layer.c is not None:
                values = _col(data_cols, layer.c)[mask]
                sc = target.scatter(
                    x,
                    y,
                    c=values,
                    cmap=scalar["cmap"]
                    if scalar is not None
                    else _continuous_cmap(layer.cmap_kind),
                    norm=norm,
                    label=label,
                    s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                    marker=marker,
                    alpha=layer.alpha,
                    **({"plotnonfinite": True} if scalar is not None else {}),
                    **outline,
                )
            else:
                color = layer.color or next(color_iter)
                handle = target.scatter(
                    x,
                    y,
                    label=label,
                    color=color,
                    s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
                    marker=marker,
                    alpha=layer.alpha,
                    **outline,
                )
                if layer.native_style is not None:
                    from ._native_geometry_render import apply_scatter_style

                    apply_scatter_style(handle, layer.native_style)
                if layer.path_effects is not None:
                    from ._native_annotations import apply_path_effects

                    apply_path_effects(handle, layer.path_effects, body=True)
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
                **_scatter_outline(layer),
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
            handle = target.bar(
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
        if layer.raw_guide_id is not None and layer.hue_order:
            collector = getattr(target, "_mudplot_shared_guide_collector", None)
            if collector is not None:
                collector.add_raw(target, layer, layer.hue_order[series_i], handle)

    if sc is not None and layer.colorbar:
        if scalar is None:
            target.figure.colorbar(sc, ax=target, label=layer.clabel or "")
        else:
            from ._scalar_render import draw_scalar_bar

            draw_scalar_bar(target, layer, sc)


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
    curve_styles=None,
    advanced=None,
    prepared=None,
    hue_pools=None,
    slots=None,
):
    if (
        layer.type in {"lineplot", "barplot", "pointplot", "countplot"}
        and layer.semantics is not None
    ):
        from ._line_semantics import draw_semantic_curves

        return draw_semantic_curves(
            _target_axes(ax, ax2, layer),
            data_cols,
            layer,
            color_iter,
            theme,
            domain=semantic_domain,
            guides=semantic_guides,
            prepared=prepared,
        )
    if layer.type == "lineplot":
        from ._lineplot import draw_lineplot

        return draw_lineplot(
            _target_axes(ax, ax2, layer),
            data_cols,
            layer,
            color_iter,
            theme,
            prepared=prepared,
        )
    from ._estimate import summarize

    target = _target_axes(ax, ax2, layer)
    horizontal = layer.orient == "h"
    value_scale = target.get_xscale() if horizontal else target.get_yscale()
    summary = summarize(
        data_cols,
        layer,
        value_scale=value_scale,
        advanced=advanced,
        hue_pools=hue_pools,
    )
    if not summary.categories:
        return
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
    identity = stat_key if summary.typed else lambda value: value
    category_positions = dict(
        zip(map(identity, summary.categories), positions, strict=True)
    )
    category_ranks = (
        {
            category: index
            for index, category in enumerate(
                sorted(category_positions, key=category_positions.__getitem__)
            )
        }
        if layer.native_scale
        else category_positions
    )
    bottoms = dict.fromkeys(map(identity, summary.categories), 0.0)
    grouped = {identity(group): [] for group in summary.groups}
    for point in summary.estimates:
        grouped[identity(point.group)].append(point)
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
        points = sorted(
            grouped[identity(group)],
            key=lambda p: category_positions[identity(p.category)],
        )
        if curve_styles is not None and not points:
            continue
        mapped = None if curve_styles is None else curve_styles.get(group)
        color = (layer.color or next(color_iter)) if mapped is None else mapped["color"]
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
        if curve_styles is not None:
            label = "_nolegend_"
        x = np.asarray([category_positions[identity(p.category)] for p in points])
        y = np.asarray([p.value for p in points])
        bars = None
        if layer.type in {"barplot", "countplot"}:
            span = (0.8 if layer.bar_width is None else layer.bar_width) * spacing
            dodged = n_series > 1 and not layer.stack
            width = span / n_series if dodged else span
            if dodged:
                if slots is None:
                    x = x + (i - (n_series - 1) / 2) * width
                else:
                    start, fraction = slots[group]
                    width = span * fraction
                    x = x + span * (start - 0.5) + width / 2
            gap = (0.08 if dodged else 0.0) if layer.gap is None else layer.gap
            base = (
                np.asarray([bottoms[identity(p.category)] for p in points])
                if layer.stack
                else 0
                if layer.baseline is None
                else layer.baseline
            )
            heights = y if layer.stack else y - base
            if layer.stack:
                with np.errstate(over="ignore"):
                    top = base + y
                if np.any(~np.isfinite(top)):
                    raise ValueError(
                        "stacked count endpoint exceeds finite plotting range"
                    )
                if value_scale == "log":
                    baseline = layer.baseline
                    if baseline is None or not np.isfinite(baseline) or baseline <= 0:
                        raise ValueError(
                            "log stacked counts require a positive explicit baseline"
                        )
                    first = base == 0
                    if np.any(first & (y <= baseline)):
                        raise ValueError(
                            "log stack baseline must be below each first positive mass"
                        )
                    if np.any(top <= base):
                        raise ValueError("log stacked count coordinates collapse")
                    heights = np.where(first, y - baseline, y)
                    base = np.where(first, baseline, base)
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
                edgecolor=layer.edge_color
                if mapped is None
                else mapped.get("edge_color"),
                linewidth=layer.line_width if mapped is None else mapped["width"],
                **(
                    {}
                    if mapped is None
                    else {
                        "linestyle": "solid" if mapped["width"] == 0 else mapped["dash"]
                    }
                ),
                hatch=hatch,
                alpha=layer.alpha,
                label=label,
            )
            if mapped is not None:
                mapped["artist"] = bars.patches[0]
            if layer.stack:
                for p in points:
                    bottoms[identity(p.category)] += p.value
        else:
            span = (0.0 if layer.dodge is None else layer.dodge) * spacing
            x = x + (i - (n_series - 1) / 2) * span / n_series
            # Insert breaks instead of bridging a missing category cell.
            line_x, line_y = [], []
            previous = None
            for position, point in zip(x, points, strict=True):
                index = category_ranks[identity(point.category)]
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
            line_width = 1.25 if layer.line_width is None else layer.line_width
            marker_size = 5.0 if layer.marker_size is None else layer.marker_size
            if mapped is not None:
                marker, style = mapped["marker"], mapped["dash"]
                line_width, marker_size = mapped["width"], mapped["marker_size"]
            coordinates = (line_y, line_x) if horizontal else (line_x, line_y)
            (artist,) = target.plot(
                *coordinates,
                color=color,
                label=label,
                marker=marker,
                linestyle="None" if line_width == 0 else style,
                markersize=marker_size,
                linewidth=line_width,
                alpha=layer.alpha,
            )
            if mapped is not None:
                mapped["artist"] = artist
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
                if layer.native_scale or value_scale == "log":
                    for position, point, patch in zip(
                        x, points, bars.patches, strict=True
                    ):
                        center = bottoms[point.category] - point.value / 2
                        if value_scale == "log":
                            low = patch.get_x() if horizontal else patch.get_y()
                            high = bottoms[point.category]
                            center = np.sqrt(low) * np.sqrt(high)
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


def _letter_value_artists(ax, contexts, positions, width, layer):
    """Native disjoint polygon bands with deterministic median and tail points."""
    from matplotlib.collections import PolyCollection

    from ._components import apply_component_style

    edge = layer.edge_color or "#4b5563"
    stroke = 0.8 if layer.line_width is None else layer.line_width
    bodies = []
    horizontal = layer.orient == "h"
    for prepared, center in zip(contexts, positions, strict=True):
        summary, original_fliers, native_values, native_median = prepared
        vertices = []
        for (low, high), relative in zip(
            itertools.pairwise(summary.values), summary.widths, strict=True
        ):
            half = width * relative / 2
            if relative > 0 and (half <= 0 or center - half == center + half):
                raise ValueError(
                    "letter-value precision: positive category extent collapses"
                )
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
        cast(Any, body)._mudplot_boxen_value_coordinates = [
            (low, low, high, high, low)[: len(cast(Any, path.vertices))]
            for path, (low, high) in zip(
                body.get_paths(), itertools.pairwise(native_values), strict=True
            )
        ]
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
            median_artist._mudplot_boxen_value_coordinates = (
                native_median,
                native_median,
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
            flier_artist._mudplot_boxen_value_coordinates = original_fliers
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
        positions = np.asarray(positions)
        if getattr(axis, "_mudplot_temporal", None) is not None:
            _declare_category_slot_bounds(ax, positions, spacing, layer)
        return positions, spacing, labels
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
    ax,
    values,
    positions,
    width,
    labels,
    layer,
    violin_context=None,
    *,
    box_context=None,
    boxen_context=None,
):
    """Compute in declared coordinates then inverse-map native artist geometry."""
    from matplotlib.collections import LineCollection

    from ._components import finalize_component_stroke

    category_dim = int(layer.orient == "h")
    value_dim = 1 - category_dim
    scales = [ax.get_xscale(), ax.get_yscale()]
    inverse = [False, False]
    inverse[category_dim] = layer.native_scale and scales[category_dim] == "log"
    inverse[value_dim] = layer.stat_scale == "axis" and scales[value_dim] == "log"
    if layer.type == "boxenplot" and boxen_context is None:
        from ._boxen import _prepare_summary

        data = [
            _prepare_summary(data, None, layer, logarithmic=inverse[value_dim])
            for data in values
        ]
    else:
        data = (
            [np.log10(v) for v in values]
            if box_context is None
            and violin_context is None
            and boxen_context is None
            and inverse[value_dim]
            else values
        )
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

    def mapped(points, *, original_values=None):
        points = np.asarray(points, dtype=float).copy()
        for dim in range(2):
            if dim == value_dim and original_values is not None:
                points[:, dim] = original_values
            elif inverse[dim]:
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
            ax,
            data,
            positions,
            width,
            labels,
            layer,
            violin_context,
            box_context=box_context,
            boxen_context=boxen_context,
        )
        for patch in list(ax.patches)[starts[0] :]:
            finalize_component_stroke(patch, body=True)
            working = patch.get_path().vertices
            vertices = mapped(
                working,
                original_values=getattr(
                    patch, "_mudplot_boxen_value_coordinates", None
                ),
            )
            if boxen_context is not None and any(
                np.max(working[:, dim]) > np.min(working[:, dim])
                and np.max(vertices[:, dim]) <= np.min(vertices[:, dim])
                for dim in range(2)
            ):
                raise ValueError("positive boxen band geometry is unrepresentable")
            patch.get_path().vertices[:] = vertices
            geometry.append(vertices)
        for line in list(ax.lines)[starts[1] :]:
            finalize_component_stroke(line)
            vertices = mapped(
                line.get_xydata(),
                original_values=getattr(line, "_mudplot_boxen_value_coordinates", None),
            )
            line.set_data(vertices[:, 0], vertices[:, 1])
            geometry.append(vertices)
        for collection in list(ax.collections)[starts[2] :]:
            if isinstance(collection, LineCollection):
                segments = [mapped(v) for v in collection.get_segments()]
                collection.set_segments(segments)
                geometry.extend(segments)
            else:
                native_values = getattr(
                    collection, "_mudplot_boxen_value_coordinates", None
                )
                for index, path in enumerate(collection.get_paths()):
                    vertices = mapped(
                        path.vertices,
                        original_values=None
                        if native_values is None
                        else native_values[index],
                    )
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
    ax,
    values,
    positions,
    width,
    labels,
    layer,
    violin_context=None,
    *,
    box_context=None,
    boxen_context=None,
):
    """Native artists for deterministic summaries/KDE across Matplotlib 3.8+."""
    if boxen_context is not None:
        from ._boxen_render import native_boxen_artists

        return native_boxen_artists(ax, boxen_context, layer)
    if box_context is not None:
        from ._box_render import native_box_artists

        return native_box_artists(ax, box_context, layer)
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
    if not categories:
        return
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
        if not bodies:
            # Native showbox=False still draws its whiskers/medians/other marks.
            continue
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
            from ._components import finalize_component_stroke

            finalize_component_stroke(body, body=True)
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


def _draw_strip_layer(
    ax,
    columns,
    layer,
    color_iter,
    theme,
    *,
    semantic_domain=None,
    semantic_guides=True,
):
    """Jitter category slots, never the measurement or stored source rows."""
    roles = layer.semantics
    rows = (
        distribution_rows(columns, layer)
        if roles is None
        else semantic_rows(columns, layer)
    )
    categories, groups = distribution_levels(columns, layer, rows)
    if roles is not None:
        pool = rows if semantic_domain is None else semantic_domain["rows"]
        pool_columns = (
            columns if semantic_domain is None else semantic_domain["columns"]
        )
        groups = semantic_levels(pool_columns, roles, "hue", pool)
    colors = (
        {group: layer.color or next(color_iter) for group in groups}
        if roles is None
        else {}
    )
    if not categories:
        return
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    span = 0 if layer.dodge is None else layer.dodge * spacing
    dodged = len(groups) > 1 and span != 0
    slot = span / len(groups) if dodged else spacing
    amplitude = (0.15 if layer.jitter is None else layer.jitter) * slot
    config = layer.strip
    jitter = (
        np.zeros(len(rows))
        if config is not None and config.jitter_policy == "none"
        else np.random.default_rng(0 if config is None else config.seed).uniform(
            -amplitude, amplitude, len(rows)
        )
    )
    indices = {category: i for i, category in enumerate(categories)}
    if roles is not None:
        from ._scatter_semantics import draw_semantic_scatter

        if not rows:
            _finish_category_axis(ax, positions, spacing, labels, layer)
            return
        hue_slots: dict[tuple[str, Any], int] = {
            category_key(value): i
            for i, value in enumerate(groups)
            if value is not None
        }
        names = []
        data = dict(columns)
        count = len(columns[layer.x])
        for name in ("__mudplot_strip_category", "__mudplot_strip_value"):
            while name in data:
                name += "_"
            names.append(name)
            data[name] = [None] * count
        category_name, value_name = names
        centers = np.asarray(
            [positions[indices[columns[layer.x][row]]] for row in rows]
        )
        if dodged:
            centers += np.asarray(
                [
                    (
                        hue_slots[category_key(columns[roles.hue][row])]
                        - (len(groups) - 1) / 2
                    )
                    * span
                    / len(groups)
                    for row in rows
                ]
            )
        locations = _category_inverse(ax, centers + jitter, layer)
        for row, location in zip(rows, locations, strict=True):
            data[category_name][row] = float(location)
            data[value_name][row] = columns[layer.y][row]
        x_name, y_name = (
            (value_name, category_name)
            if layer.orient == "h"
            else (category_name, value_name)
        )
        draw_semantic_scatter(
            ax,
            data,
            replace(layer, type="scatter", x=x_name, y=y_name, order=None, orient="v"),
            color_iter,
            domain=semantic_domain,
            guides=semantic_guides,
        )
        _finish_category_axis(ax, positions, spacing, labels, layer)
        return
    markers = (
        itertools.cycle(theme.markers)
        if theme.redundant_encoding and len(groups) > 1
        else itertools.repeat("o")
    )
    for i, group in enumerate(groups):
        marker = next(markers) if layer.marker is None else layer.marker
        selected = [
            j
            for j, row in enumerate(rows)
            if layer.group is None or columns[layer.group][row] == group
        ]
        if not selected:
            continue
        centers = np.asarray(
            [positions[indices[columns[layer.x][rows[j]]]] for j in selected]
        )
        if dodged:
            centers += (i - (len(groups) - 1) / 2) * span / len(groups)
        category = _category_inverse(ax, centers + jitter[selected], layer)
        values = np.asarray([columns[layer.y][rows[j]] for j in selected])
        x, y = (values, category) if layer.orient == "h" else (category, values)
        ref = (layer.references or {}).get(str(group))
        label = (
            _decorate(layer.label, layer.citation, layer.href)
            if layer.group is None
            else _decorate(
                str(group), ref.citation if ref else None, ref.href if ref else None
            )
        )
        ax.scatter(
            x,
            y,
            label=label,
            color=colors[group],
            s=(6 if layer.marker_size is None else layer.marker_size) ** 2,
            marker=marker,
            alpha=layer.alpha,
            **_scatter_outline(layer),
        )
    _finish_category_axis(ax, positions, spacing, labels, layer)


def _declare_category_slot_bounds(ax, positions, spacing, layer):
    """Shared temporal category extent, independent of absolute epoch origin."""
    horizontal = layer.orient == "h"
    anchors = np.zeros((2, 2), dtype=float)
    anchors[:, int(horizontal)] = _category_inverse(
        ax, [positions.min() - spacing / 2, positions.max() + spacing / 2], layer
    )
    ax.update_datalim(anchors, updatex=not horizontal, updatey=horizontal)
    ax._request_autoscale_view(axis="y" if horizontal else "x")


def _draw_swarm_layer(
    ax,
    columns,
    layer: LayerSpec,
    color_iter,
    *,
    semantic_domain=None,
    semantic_guides=True,
    scope_plan=None,
    coordinator=None,
):
    from ._categorical import swarm_levels, swarm_size_mapping, typed_swarm
    from ._swarm import SwarmCollection

    rows = distribution_rows(columns, layer)
    config = layer.semantics
    categories, groups = swarm_levels(columns, layer, rows)
    if (
        config is not None
        and config.hue is not None
        and config.hue_kind == "categorical"
        and semantic_domain is not None
    ):
        groups = semantic_levels(
            semantic_domain["columns"], config, "hue", semantic_domain["rows"]
        )
    if scope_plan is not None:
        categories, groups = scope_plan["categories"], scope_plan["groups"]
    mapped_hue = config is not None and config.hue is not None
    advanced = typed_swarm(layer)

    def key(value):
        return category_key(value) if advanced and value is not None else value

    if not rows:
        if not layer.color and not mapped_hue:
            for _ in groups:
                next(color_iter)
        if categories:
            positions, spacing, labels = _category_geometry(ax, categories, layer)
            _finish_category_axis(ax, positions, spacing, labels, layer)
        return
    horizontal = layer.orient == "h"
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    width = (0.8 if layer.width is None else layer.width) * spacing
    span = width if layer.dodge is None else layer.dodge * spacing
    dodged = len(groups) > 1 and span != 0
    cell_width = (span / len(groups) if dodged else width) * (
        1 - (0 if layer.gap is None else layer.gap)
    )
    colors = (
        {} if mapped_hue else {key(g): layer.color or next(color_iter) for g in groups}
    )
    offsets, faces, urls = [], [], []
    indices = {key(c): i for i, c in enumerate(categories)}
    group_indices = {key(g): i for i, g in enumerate(groups)}
    cells, observed = {}, set()
    hue = (
        config.hue
        if config is not None
        and config.hue is not None
        and config.hue_kind == "categorical"
        else layer.group
        if not mapped_hue
        else None
    )
    for row in rows:
        c = columns[layer.x][row]
        g = columns[hue][row] if hue is not None else None
        observed.add(key(g))
        center = positions[indices[key(c)]]
        if dodged:
            center += (
                (group_indices[key(g)] - (len(groups) - 1) / 2) * span / len(groups)
            )
        cell = (key(c), key(g) if dodged else None)
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
        faces.append(colors[key(g)] if not mapped_hue else "#4b5563")
        ref = (layer.references or {}).get(str(g))
        urls.append((ref.href if ref else None) if layer.group else layer.href)
    size = 6 if layer.marker_size is None else layer.marker_size
    diameters = markers = role_context = size_guides = None
    if config is not None:
        from ._swarm_semantics import appearance

        mapped_colors, diameters, markers, role_context = appearance(
            columns, layer, rows, color_iter, domain=semantic_domain
        )
        if mapped_colors is not None:
            faces = mapped_colors
        if config.size is not None:
            size = (config.sizes[0] + config.sizes[1]) / 2
            if config.hue is None and config.style is None:
                _, size_guides = swarm_size_mapping(
                    columns, config, rows, domain=semantic_domain
                )
    line_width = 0.5 if layer.line_width is None else layer.line_width
    edge = layer.edge_color or "white"
    collection = SwarmCollection(
        offsets,
        [(np.asarray(ids, dtype=int), lo, hi) for ids, lo, hi in cells.values()],
        horizontal=horizontal,
        size=size,
        line_width=line_width,
        warn_thresh=0.05 if layer.warn_thresh is None else layer.warn_thresh,
        marker=layer.marker or "o",
        markers=markers,
        coordinator=coordinator,
        cell_keys=list(cells),
        facecolors=faces,
        edgecolors=edge,
        alpha=layer.alpha,
        offset_transform=ax.transData,
        label="_nolegend_",
        zorder=2,
    )
    if diameters is not None:
        collection.set_sizes(np.square(diameters))
    collection.set_urls(urls)
    ax.add_collection(collection)
    ax.autoscale_view()
    _finish_category_axis(ax, positions, spacing, labels, layer)
    # Legacy group legends retain their appearance; mapped hues have role guides.
    if not mapped_hue:
        for group in groups:
            if key(group) not in observed:
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
                marker = layer.marker or "o"
                if markers is not None:
                    marker = next(
                        markers[i]
                        for i, row in enumerate(rows)
                        if hue is None or key(columns[hue][row]) == key(group)
                    )
                ax.plot(
                    [],
                    [],
                    linestyle="none",
                    marker=marker,
                    markersize=size,
                    markeredgewidth=line_width,
                    markeredgecolor=edge,
                    color=colors[key(group)],
                    alpha=layer.alpha,
                    label=label,
                )
    elif layer.label:
        ax.plot(
            [],
            [],
            linestyle="none",
            marker="None",
            label=_decorate(layer.label, layer.citation, layer.href),
        )
    native_contexts = None
    primary = getattr(ax, "_mudplot_semantic_guide_axis", ax)
    collector = getattr(primary, "_mudplot_shared_guide_collector", None)
    if (
        config is not None
        and collector is not None
        and config.scale_id in collector.requests
        and rows
    ):
        from matplotlib.collections import PathCollection

        assert role_context is not None
        actual_faces = cast(PathCollection, collection).get_facecolor()
        native_contexts = [
            {
                "color": actual_faces[min(i, len(actual_faces) - 1)]
                if len(actual_faces)
                else "none",
                "diameter": float(diameters[i])
                if diameters is not None
                else float(size),
                "marker": markers[i] if markers is not None else layer.marker or "o",
                "edgecolor": edge,
                "edge_fixed": True,
                "edgewidth": line_width,
                "width": 0,
                "dash": "None",
                "alpha": collection.get_alpha(),
            }
            for i in range(len(rows))
        ]
        role_context["native_contexts"] = native_contexts
        role_context["actual_values"] = {
            role: [columns[getattr(config, role)][row] for row in rows]
            for role in ("hue", "size", "style")
            if getattr(config, role) is not None
        }
    if config is not None and (config.hue is not None or config.style is not None):
        from ._swarm_semantics import guides

        guides(ax, layer, role_context, show=semantic_guides)
    elif config is not None and config.legend and semantic_guides:
        assert size_guides is not None
        for value, diameter in size_guides:
            handle = ax.plot(
                [],
                [],
                linestyle="none",
                marker=layer.marker or "o",
                markersize=diameter,
                markeredgewidth=line_width,
                markeredgecolor=edge,
                color=layer.color or "#4b5563",
                alpha=layer.alpha,
                label=f"size: {config.size}={value}",
            )[0]
            if native_contexts is not None:
                from ._shared_guides import tag_entry

                index = next(
                    (
                        i
                        for i, row in enumerate(rows)
                        if category_key(columns[config.size][row])
                        == category_key(value)
                    ),
                    0,
                )
                tag_entry(
                    ax, handle, layer, "size", value, context=native_contexts[index]
                )


def _draw_ecdf_layer(
    ax, columns, layer: LayerSpec, color_iter, theme, *, curve_styles=None
):
    config = ecdf_config(layer)
    rows = ecdf_rows(columns, layer)
    groups = ecdf_groups(columns, layer, rows)
    redundant = theme.redundant_encoding and len(groups) > 1
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    refs = layer.references or {}
    for group in groups:
        mapped = None if curve_styles is None else curve_styles[group]
        color, style = (
            (layer.color or next(color_iter), next(styles))
            if mapped is None
            else (mapped["color"], mapped["dash"])
        )
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
        if mapped is not None:
            label = "_nolegend_"
        marker = layer.marker if mapped is None else mapped["marker"]
        width = layer.line_width if mapped is None else mapped["width"]
        marker_options = {}
        if marker is not None:
            marker_options["marker"] = marker
            marker_options["markevery"] = slice(1, None)
        if layer.marker_size is not None:
            marker_options["markersize"] = layer.marker_size
        x, y = (knots, mass) if layer.orient == "v" else (mass, knots)
        (line,) = ax.plot(
            x,
            y,
            drawstyle="steps-post" if layer.orient == "v" else "steps-pre",
            label=label,
            color=color,
            linestyle=(
                style
                if mapped is not None or layer.line_style is None
                else layer.line_style
            ),
            linewidth=width,
            alpha=layer.alpha,
            **marker_options,
        )
        if width == 0:
            if marker not in (None, "None", ""):
                line.set_linestyle("None")
            else:
                line.set_visible(False)


def _draw_histogram_layer(
    ax,
    columns,
    layer: LayerSpec,
    color_iter,
    theme,
    *,
    curve_styles=None,
    hue_pools=None,
    slots=None,
):
    result = histogram_summary(columns, layer, hue_pools=hue_pools)
    if not result.edges:
        return
    config = layer.histogram
    assert config is not None  # summary already rejects an untyped configuration
    filled = config.element == "bars" if config.fill is None else config.fill
    stacked = config.multiple in ("stack", "fill")
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
            if slots is not None:
                fraction, width = slots[curve.group]
                start = edges[:-1] + widths * fraction
                stop = edges[:-1] + widths * (fraction + width)
            if np.any(stop <= start):
                raise ValueError("derived histogram dodge bins must be increasing")
        if config.element == "poly":
            centers = start + (stop - start) / 2
            if len(centers) < 2 or np.any((centers <= start) | (centers >= stop)):
                raise ValueError(
                    "histogram poly requires two representable bin centers"
                )
        geometry.append((start, stop, baseline))
        if stacked and curve.heights:
            heights = np.asarray(curve.heights, dtype=float)
            with np.errstate(over="ignore", invalid="ignore"):
                top = baseline + heights
            if np.any(~np.isfinite(top)) or np.any((heights > 0) & (top <= baseline)):
                raise ValueError(
                    "derived histogram stacked tops must be finite and "
                    "increase for nonzero bins"
                )
            baseline = top
    if config.element == "poly" and any(curve.heights for curve in result.curves):
        bounds = np.array([[edges[0], 0], [edges[-1], 0]])
        ax.update_datalim(bounds if layer.orient == "v" else bounds[:, ::-1])
    redundant = theme.redundant_encoding and len(result.curves) > 1
    hatches = itertools.cycle(theme.hatches) if redundant else itertools.repeat(None)
    refs = layer.references or {}
    styles = itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
    for curve, (start, stop, baseline) in zip(result.curves, geometry, strict=True):
        span = stop - start
        color, hatch, line_style = (
            layer.color or next(color_iter),
            next(hatches),
            next(styles),
        )
        if not curve.heights:
            continue
        # Native fallback hatches can stay opaque at zero artist alpha.
        if layer.alpha == 0:
            hatch = None
        if layer.group is None:
            label = _decorate(layer.label, layer.citation, layer.href)
        else:
            ref = refs.get(str(curve.group))
            label = _decorate(
                str(curve.group),
                ref.citation if ref else None,
                ref.href if ref else None,
            )
        mapped = None if curve_styles is None else curve_styles[curve.group]
        line_width, edge_color = layer.line_width, layer.edge_color
        if mapped is not None:
            color, line_width, line_style = (
                mapped["color"],
                mapped["width"],
                mapped["dash"],
            )
            edge_color = mapped.get("edge_color") if filled else layer.edge_color
            label = "_nolegend_"
        if config.element == "poly":
            centers = start + span / 2
            top = baseline + np.asarray(curve.heights)
            if filled:
                draw = ax.fill_between if layer.orient == "v" else ax.fill_betweenx
                artist = draw(
                    centers,
                    top,
                    baseline,
                    facecolor=color,
                    edgecolor=edge_color,
                    hatch=hatch,
                    linewidth=line_width,
                    linestyle="-" if line_width == 0 else line_style,
                    alpha=layer.alpha,
                    label=label,
                )
            else:
                x, y = (centers, top) if layer.orient == "v" else (top, centers)
                (artist,) = ax.plot(
                    x,
                    y,
                    color=edge_color or color,
                    linewidth=line_width,
                    linestyle="-" if line_width == 0 else line_style,
                    alpha=layer.alpha,
                    label=label,
                )
                if line_width == 0:
                    artist.set_visible(False)
            sticky = (
                artist.sticky_edges.y if layer.orient == "v" else artist.sticky_edges.x
            )
            sticky.append(0)
            if mapped is not None:
                mapped.update(artist=artist, filled=filled)
            continue
        if config.element == "step":
            step_heights = baseline + np.asarray(curve.heights)
            step_edges = edges
            if config.multiple == "dodge":
                zeros = np.zeros_like(widths)
                step_heights = np.column_stack((zeros, step_heights, zeros)).ravel()
                step_edges = np.append(
                    np.column_stack((edges[:-1], start, stop)).ravel(), edges[-1]
                )
            fill_style = {"facecolor": color, "hatch": hatch} if filled else {}
            artist = ax.stairs(
                step_heights,
                step_edges,
                baseline=baseline if stacked else 0,
                orientation="vertical" if layer.orient == "v" else "horizontal",
                fill=filled,
                **fill_style,
                edgecolor=edge_color or (None if filled else color),
                linewidth=line_width,
                linestyle="-" if line_width == 0 else line_style,
                alpha=layer.alpha,
                label=label,
            )
            if mapped is not None:
                mapped.update(artist=artist, filled=filled)
            continue
        style = {
            "align": "edge",
            "color": color,
            "hatch": hatch if filled else None,
            "fill": filled,
            "label": label,
            "alpha": layer.alpha,
            "edgecolor": edge_color or (None if filled else color),
            "linewidth": line_width,
        }
        if not filled or mapped is not None:
            style["linestyle"] = "-" if line_width == 0 else line_style
        if layer.orient == "v":
            artist = ax.bar(start, curve.heights, width=span, bottom=baseline, **style)
        else:
            artist = ax.barh(start, curve.heights, height=span, left=baseline, **style)
        if mapped is not None:
            mapped.update(artist=artist.patches[0], filled=filled)


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
        from ._rug import draw_rug_collection

        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            color = layer.color or next(color_iter)
            linestyle = (
                next(style_cycle) if layer.line_style is None else layer.line_style
            )
            if layer.hue_order is not None and not np.isfinite(values).any():
                continue
            draw_rug_collection(
                ax,
                values,
                layer,
                colors=color,
                widths=layer.line_width,
                dashes="-" if layer.line_width == 0 else linestyle,
                label=label,
            )


def _draw_matrix_layer(ax, spec: FigureSpec, layer: LayerSpec):
    from ._heatmap import advanced_heatmap
    from ._heatmap_render import draw_colourbar, draw_heatmap

    admission = getattr(ax.figure, "_mudplot_matrix_admission", None)
    if admission is not None and id(layer) in admission.grids:
        from ._grid_render import draw_grid

        return draw_grid(ax, layer, admission.grids[id(layer)])
    if admission is not None and id(layer) not in admission.layers:
        admission = None

    assert layer.matrix is not None
    matrix = _float_array(spec.data.matrices[layer.matrix], f"matrix {layer.matrix!r}")
    if layer.scalar_display is not None:
        from ._scalar_render import draw_scalar_bar, scalar_style

        options = scalar_style(ax, layer)
        if layer.heatmap is None:
            im = ax.imshow(
                np.ma.masked_invalid(matrix),
                aspect="auto",
                alpha=layer.alpha,
                **options,
            )
        else:
            im = draw_heatmap(
                ax,
                matrix,
                layer,
                options["cmap"],
                nulls=np.isnan(matrix),
                scalar_norm=options["norm"],
            )
        draw_scalar_bar(ax, layer, im)
        return
    cmap = _continuous_cmap(layer.cmap_kind)
    if layer.type == "clustermap":
        from ._cluster_render import draw_clustermap

        draw_clustermap(ax, matrix, layer, cmap, admission=admission)
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
            cax = None
            if advanced_heatmap(layer.heatmap):
                from ._heatmap_render import bar_geometry
                from ._matrix_layout import plot_colorbar_slot

                cax = plot_colorbar_slot(ax, *bar_geometry(layer.heatmap))
            draw_colourbar(ax, im, layer.clabel or "", cax=cax, config=layer.heatmap)
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


def _draw_marker_layer(ax, ax2, layer: LayerSpec, color_iter, layer_index: int):
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
        artist._mudplot_layer_index = layer_index
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
        artist._mudplot_layer_index = layer_index
    else:
        raise ValueError(f"unknown layer type: {layer.type!r}")


def _draw_3d_layer(ax, spec: FigureSpec, layer: LayerSpec, color_iter):
    if uses_spatial(layer):
        from ._spatial_render import draw_spatial

        assert id(layer) in ax.figure._mudplot_matrix_admission.spatial
        return draw_spatial(ax, spec, layer, color_iter)
    if layer.type == "quiver3d":
        from ._vector_render import draw_vectors

        return draw_vectors(
            ax,
            spec,
            layer,
            ax.figure._mudplot_matrix_admission.vectors[id(layer)],
            color_iter,
        )
    if layer.type == "trisurf":
        from ._tri_render import draw_triangles

        admission = ax.figure._mudplot_matrix_admission
        return draw_triangles(ax, layer, admission.triangles[id(layer)])
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


def _set_native_scale(ax, axis_spec, set_scale, which):
    if axis_spec.scale == "logit":
        from ._axis_render import checked_logit_scale

        set_scale(checked_logit_scale(getattr(ax, which + "axis")))
    else:
        from ._axis_options import scale_kwargs

        set_scale(axis_spec.scale, **scale_kwargs(axis_spec))


def _apply_axis(ax, axis_spec, set_label, set_scale, set_limits, *, which):
    set_label(axis_spec.label)
    # Setting even the existing linear scale resets categorical tick locators.
    if axis_spec.scale != "linear":
        _set_native_scale(ax, axis_spec, set_scale, which)
    if axis_spec.limits:
        set_limits(axis_spec.limits)
    if axis_spec.temporal is not None:
        from ._temporal_render import apply_temporal_axis

        apply_temporal_axis(getattr(ax, f"{which}axis"), axis_spec.temporal)


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
        kw = {
            "loc": "center",
            "bbox_to_anchor": tuple(leg.bbox_to_anchor),
            "bbox_transform": fig.transFigure,
        }
        auto = False
    else:
        kw = dict(_OUTSIDE_LEGEND_LOCS.get(leg.location, {"loc": leg.location}))
        auto = leg.location in _OUTSIDE_LEGEND_LOCS
    if leg.ncols is not None:
        kw.pop("ncol", None)
        kw["ncols"] = leg.ncols
    return kw, auto


def _apply_title(ax, panel: PanelSpec) -> None:
    captions = getattr(ax, "_mudplot_inference_captions", ())
    if not panel.title and not captions:
        return
    title_text = _decorate(
        panel.title, panel.title_citation, panel.title_href, widen=False
    )
    if captions:
        title_text = "\n".join([text for text in (title_text, *captions) if text])
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
    ax._mudplot_title_artist = artist


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

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim, which="x")
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim, which="y")
    if panel.z is not None:
        _apply_axis(ax, panel.z, ax.set_zlabel, ax.set_zscale, ax.set_zlim, which="z")
    if panel.camera3d is not None:
        from ._spatial_render import apply_camera

        apply_camera(ax, panel.camera3d)
    _apply_title(ax, panel)

    handles, labels = _unique_legend_handles(*_raw_legend_handles(ax))
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(leg, fig=ax.figure)
        if leg.handler is not None:
            from ._legend_style import legend_handlers

            kw["handler_map"] = legend_handlers(handles, leg)
        legend_artist = ax.legend(
            handles, labels, title=leg.title, frameon=leg.frame, **kw
        )
        legend_artist._mudplot_auto_margin = auto_margin
        _link_legend_texts(legend_artist, panel)


def _draw_panel(
    ax,
    spec: FigureSpec,
    panel: PanelSpec,
    *,
    domains=None,
    boxen_plans=None,
    line_plans=None,
    regression_plans=None,
    guide_collector=None,
):
    import matplotlib.pyplot as plt

    from ._density import (
        DENSITY_TYPES,
        FIELD_TYPES,
        bounded_density_request,
        density_adapter,
    )

    raw_regression_columns = spec.data.columns
    source_rows = (
        panel_rows(spec.data.columns, panel)
        if panel.filters or panel.dropna
        else range(len(next(iter(spec.data.columns.values()), ())))
    )
    row_ids = source_rows
    ax._mudplot_source_rows = source_rows

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
    _set_native_scale(ax, panel.x, ax.set_xscale, "x")
    _set_native_scale(ax, panel.y, ax.set_yscale, "y")
    ax.xaxis._mudplot_temporal = panel.x.temporal
    ax.yaxis._mudplot_temporal = panel.y.temporal
    ax2 = None
    if panel.y2 is not None:
        ax2 = ax.twinx()
        _set_native_scale(ax2, panel.y2, ax2.set_yscale, "y")
        ax2.xaxis._mudplot_temporal = panel.x.temporal
        ax2.yaxis._mudplot_temporal = panel.y2.temporal
        ax2._mudplot_semantic_guide_axis = ax
        ax2._mudplot_source_rows = source_rows
    if guide_collector is not None:
        guide_collector.attach(ax)
        if ax2 is not None:
            guide_collector.attach(ax2)
    ax._mudplot_secondary_axis = ax2

    from ._temporal_data import prepare_temporal_layer
    from ._transforms import projects, stages_for
    from ._transforms import unit as coordinate_unit

    # Resolve guide intent before drawing any member. A later requested bar
    # replaces earlier numeric-hue calibration too, without altering the spec.
    colourbar_intents = {
        layer.semantics.scale_id: (
            layer.clabel if layer.clabel is not None else layer.semantics.hue
        )
        for layer in panel.layers
        if layer.semantics is not None
        and layer.semantics.scale_id is not None
        and layer.colorbar
        and layer.type not in FIELD_TYPES
        and (
            layer.type != "regplot"
            or id(layer)
            in domains.get(layer.semantics.scale_id, {}).get("regression_members", ())
        )
    }

    scope_slots, scope_artists = {}, {}
    if any(layer.pack_scope is not None for layer in panel.layers):
        from ._swarm import SwarmScope
        from ._swarm_scope import scope_plans

        scope_slots, problems = scope_plans(spec.data.columns, panel, domains=domains)
        if problems:
            raise ValueError("; ".join(problems))
        for name, plan in scope_slots.items():
            if plan["instances"]:
                member = panel.layers[plan["members"][0]]
                scope_artists[name] = SwarmScope(_target_axes(ax, ax2, member))

    from ._native_geometry import extended_geometry

    coordinate_leases = []
    for layer_index, layer in enumerate(panel.layers):
        scalar = (
            ax.figure._mudplot_scalar_maps[id(layer)]
            if layer.type == "scatter" and layer.scalar_display is not None
            else None
        )
        for lease in coordinate_leases:
            lease.close()
        coordinate_leases.clear()
        if extended_geometry(layer):
            from ._native_geometry_render import draw_geometry

            draw_geometry(
                _target_axes(ax, ax2, layer),
                layer,
                ax.figure._mudplot_matrix_admission.native_geometry[id(layer)],
                color_iter,
                layer_index,
            )
            continue
        layer_columns = None
        prepared_regression = (
            None if regression_plans is None else regression_plans.get(layer_index)
        )
        if prepared_regression is not None:
            from ._regression_render import draw_prepared_regression

            visual_layer = layer
            if (
                layer.semantics is not None
                and layer.semantics.scale_id in colourbar_intents
            ):
                visual_layer = replace(
                    layer,
                    colorbar=True,
                    clabel=colourbar_intents[layer.semantics.scale_id],
                )

            previous = {id(handle) for handle in _raw_legend_handles(ax, ax2)[0]}
            draw_prepared_regression(
                _target_axes(ax, ax2, layer),
                prepared_regression,
                color_iter,
                theme,
                raw_columns=raw_regression_columns,
                visual_layer=visual_layer,
                domain=None
                if layer.semantics is None
                else domains.get(layer.semantics.scale_id),
            )
            _mark_legend_source(layer, _raw_legend_handles(ax, ax2)[0], previous)
            continue
        if (
            layer.semantics is not None
            and layer.type not in FIELD_TYPES
            and layer.semantics.scale_id in colourbar_intents
        ):
            layer = replace(
                layer,
                colorbar=True,
                clabel=colourbar_intents[layer.semantics.scale_id],
            )
        if advanced_stairs(layer, panel):
            from ._stairs_render import draw_stairs

            previous = {id(handle) for handle in _raw_legend_handles(ax, ax2)[0]}
            draw_stairs(
                _target_axes(ax, ax2, layer),
                spec.data.columns,
                layer,
                panel,
                row_ids,
                color_iter,
            )
            _mark_legend_source(layer, _raw_legend_handles(ax, ax2)[0], previous)
            continue
        if (
            guide_collector is not None
            and layer.semantics is not None
            and layer.semantics.scale_id in guide_collector.requests
            and guide_collector.requests[layer.semantics.scale_id].kind is None
        ):
            name = layer.semantics.scale_id
            layer = replace(
                layer,
                semantics=replace(
                    layer.semantics, legend=guide_collector.legend_intent[name]
                ),
                colorbar=(
                    layer.colorbar
                    if layer.type in FIELD_TYPES
                    else guide_collector.colourbar_intent[name]
                ),
                clabel=(
                    layer.clabel
                    if layer.type in FIELD_TYPES
                    else guide_collector.colourbar_labels[name]
                ),
            )
        if advanced_lanes(layer, panel):
            from ._lanes_render import draw_lanes

            previous = {id(handle) for handle in _raw_legend_handles(ax, ax2)[0]}
            draw_lanes(
                _target_axes(ax, ax2, layer),
                spec.data.columns,
                layer,
                panel,
                color_iter,
                domain=domains.get(getattr(layer.semantics, "scale_id", None)),
            )
            _mark_legend_source(layer, _raw_legend_handles(ax, ax2)[0], previous)
            continue
        prepared_boxen = None if boxen_plans is None else boxen_plans.get(layer_index)
        if prepared_boxen is not None:
            layer_columns, observation_mask = prepared_boxen.columns, None
            layer = replace(
                prepared_boxen.layer, colorbar=layer.colorbar, clabel=layer.clabel
            )
        elif (
            projects(layer)
            and layer.type == "lineplot"
            and line_plans is not None
            and layer_index in line_plans
        ):
            layer_columns, observation_mask = spec.data.columns, None
        else:
            coordinate_budget = None
            if projects(layer) and layer.type in DENSITY_TYPES:
                from ._field_render import figure_field_budget

                coordinate_budget = figure_field_budget(ax.figure, layer, panel)
            layer_columns, layer, observation_mask = prepare_temporal_layer(
                spec.data.columns,
                layer,
                panel,
                field_budget=coordinate_budget,
                coordinate_leases=coordinate_leases,
            )
        if observation_mask is not None and layer.type in {"bar", "errorbar"}:
            layer_columns = {
                name: [value for i, value in enumerate(values) if observation_mask[i]]
                for name, values in layer_columns.items()
            }
        previous = {id(handle) for handle in _raw_legend_handles(ax, ax2)[0]}
        raw_limits = None
        # Eventplot's native Y-lane hint uses full length, not its actual half
        # extents. Only logit lane views need the qualified geometry rebuild.
        event_lane_logit = (
            layer.type == "eventplot"
            and _target_axes(ax, ax2, layer).get_yscale() == "logit"
        )
        native_stem = (
            layer.type == "stem" and layer.group is None and layer.semantics is None
        )
        if (
            layer.type in ("bar", "errorbar", "broken_barh")
            or native_stem
            or event_lane_logit
        ):
            target = _target_axes(ax, ax2, layer)
            if target.get_xscale() in NEW_SCALES or target.get_yscale() in NEW_SCALES:
                from ._axis_render import capture_raw_limits

                raw_limits = capture_raw_limits(target)
        if layer.type in ROLE_LAYER_TYPES and layer.semantics is not None:
            scale_id = layer.semantics.scale_id
            geometry = (
                "point"
                if layer.type in {"scatter", "stripplot", "swarmplot"}
                else "density_curve"
                if layer.type == "kde"
                else "curve"
                if layer.type in {"line", "lineplot", "ecdf"}
                else "field"
                if layer.type in FIELD_TYPES
                else layer.type
            )
            guide_key = (scale_id, geometry)
            show_guides = scale_id is None or guide_key not in shown_scales
            if layer.type in DENSITY_TYPES:
                # Field outlines/fills are resolved before native-trait dedup.
                show_guides = True
            if (
                guide_collector is not None
                and scale_id in guide_collector.legend_intent
            ):
                show_guides = True  # Every actual member contributes its context.
            if (
                scale_id is not None
                and layer.semantics.legend
                and layer.type not in DENSITY_TYPES
                and (
                    distribution_rows(layer_columns, layer)
                    if layer.type in {"swarmplot", "box", "violin", "boxenplot"}
                    else semantic_rows(layer_columns, layer)
                    if layer.type
                    in {"stripplot", "ecdf", "rug", "barplot", "pointplot"}
                    else True
                )
            ):
                shown_scales.add(guide_key)
            if layer.type == "boxenplot":
                from ._boxen_render import draw_boxen

                draw_boxen(
                    _target_axes(ax, ax2, layer),
                    prepared_boxen,
                    layer,
                    color_iter,
                    theme,
                    domain=domains.get(scale_id),
                    guides=show_guides,
                )
            elif layer.type == "violin":
                from ._violin_render import draw_violins

                draw_violins(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    theme,
                    domain=domains.get(scale_id),
                    guides=show_guides,
                )
            elif layer.type == "box":
                from ._box_render import draw_boxes

                draw_boxes(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    theme,
                    domain=domains.get(scale_id),
                    guides=show_guides,
                )
            elif layer.type == "swarmplot":
                _draw_swarm_layer(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    semantic_domain=domains.get(scale_id),
                    semantic_guides=show_guides,
                    scope_plan=scope_slots.get(layer.pack_scope),
                    coordinator=scope_artists.get(layer.pack_scope),
                )
            elif layer.type == "stripplot":
                _draw_strip_layer(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    theme,
                    semantic_domain=domains.get(scale_id),
                    semantic_guides=show_guides,
                )
            elif layer.type == "rug":
                from ._rug import draw_semantic_rug

                draw_semantic_rug(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    domain=domains.get(scale_id),
                    guides=show_guides,
                )
            elif layer.type in {"hist", "ecdf", "hist2d", "ecdf2d", "kde", "kde2d"}:
                from ._line_semantics import draw_semantic_curves

                rendered = draw_semantic_curves(
                    _target_axes(ax, ax2, layer),
                    layer_columns,
                    layer,
                    color_iter,
                    theme,
                    domain=domains.get(scale_id),
                    guides=show_guides,
                    panel=panel,
                    row_ids=row_ids,
                )
                if rendered and scale_id is not None and layer.semantics.legend:
                    shown_scales.add(guide_key)
            else:
                if layer.type == "lineplot":
                    _draw_stat_layer(
                        ax,
                        ax2,
                        layer_columns,
                        layer,
                        color_iter,
                        theme,
                        semantic_domain=domains.get(scale_id),
                        semantic_guides=show_guides,
                        prepared=None
                        if line_plans is None
                        else line_plans.get(layer_index),
                    )
                    continue
                draw = (
                    _draw_stat_layer
                    if layer.type in _STAT_TYPES
                    else _draw_series_layer
                )
                draw(
                    ax,
                    ax2,
                    layer_columns,
                    layer,
                    color_iter,
                    theme,
                    semantic_domain=domains.get(scale_id),
                    semantic_guides=show_guides,
                )
        elif advanced_boxen(layer):
            from ._boxen_render import draw_boxen

            draw_boxen(
                _target_axes(ax, ax2, layer),
                prepared_boxen,
                layer,
                color_iter,
                theme,
            )
        elif advanced_violin(layer):
            from ._violin_render import draw_violins

            draw_violins(
                _target_axes(ax, ax2, layer), layer_columns, layer, color_iter, theme
            )
        elif advanced_box(layer):
            from ._box_render import draw_boxes

            draw_boxes(
                _target_axes(ax, ax2, layer), layer_columns, layer, color_iter, theme
            )
        elif layer.type == "spectrum":
            from ._spectrum import draw_spectrum

            artist = draw_spectrum(
                ax,
                layer_columns,
                replace(
                    layer, label=_decorate(layer.label, layer.citation, layer.href)
                ),
                color_iter,
                _continuous_cmap(layer.cmap_kind),
            )
            _set_url(artist, layer.href)
        elif layer.type == "swarmplot":
            _draw_swarm_layer(
                _target_axes(ax, ax2, layer),
                layer_columns,
                layer,
                color_iter,
                scope_plan=scope_slots.get(layer.pack_scope),
                coordinator=scope_artists.get(layer.pack_scope),
            )
        elif categorical_strip(layer):
            _draw_strip_layer(
                _target_axes(ax, ax2, layer), layer_columns, layer, color_iter, theme
            )
        elif layer.type in DENSITY_TYPES and density_adapter(layer, panel):
            from ._field_render import draw_density_fields

            draw_density_fields(
                _target_axes(ax, ax2, layer),
                layer_columns,
                layer,
                panel,
                color_iter,
                theme,
                row_ids=row_ids,
            )
        elif layer.type in _STAT_TYPES:
            _draw_stat_layer(
                ax,
                ax2,
                layer_columns,
                layer,
                color_iter,
                theme,
                advanced=new_stat_request(layer, panel),
                prepared=None if line_plans is None else line_plans.get(layer_index),
            )
        elif uses_vector(layer):
            from ._vector_render import draw_vectors

            draw_vectors(
                _target_axes(ax, ax2, layer),
                spec,
                layer,
                ax.figure._mudplot_matrix_admission.vectors[id(layer)],
                color_iter,
            )
        elif layer.type == "hexbin" and panel.grid_cohort is True:
            from ._hex_field import draw_hex_field

            draw_hex_field(
                _target_axes(ax, ax2, layer),
                layer_columns,
                layer,
                panel,
                row_ids,
                itertools.cycle(prop),
            )
        elif layer.type in _SERIES_TYPES:
            series_colors = (
                itertools.cycle(prop) if layer.raw_guide_id is not None else color_iter
            )
            _draw_series_layer(
                ax,
                ax2,
                layer_columns,
                layer,
                series_colors,
                theme,
                scalar=scalar,
            )
        elif layer.type in _DIST_TYPES:
            _draw_dist_layer(
                _target_axes(ax, ax2, layer), layer_columns, layer, color_iter, theme
            )
        elif layer.type in TRI_TYPES:
            from ._tri_render import draw_triangles

            admission = ax.figure._mudplot_matrix_admission
            draw_triangles(ax, layer, admission.triangles[id(layer)], color_iter)
        elif layer.type in _MATRIX_TYPES:
            _draw_matrix_layer(ax, spec, layer)
        elif layer.type in _STANDALONE_TYPES:
            _draw_pie_layer(ax, layer_columns, layer, color_iter)
        else:
            _draw_marker_layer(ax, ax2, layer, color_iter, layer_index)
        if raw_limits is not None:
            from ._axis_render import restore_raw_limits

            restore_raw_limits(_target_axes(ax, ax2, layer), raw_limits)
        _mark_legend_source(layer, _raw_legend_handles(ax, ax2)[0], previous)

    for lease in coordinate_leases:
        lease.close()
    layer_columns = None

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim, which="x")
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim, which="y")
    spectral = next((layer for layer in panel.layers if layer.type == "spectrum"), None)
    if spectral is not None:
        from ._spectrum import spectrum_labels

        xlabel, ylabel, _ = spectrum_labels(spectral.spectrum)
        if not panel.x.label:
            ax.set_xlabel(xlabel)
        if not panel.y.label:
            ax.set_ylabel(ylabel)
    if panel.y2 is not None:
        assert ax2 is not None
        _apply_axis(
            ax2, panel.y2, ax2.set_ylabel, ax2.set_yscale, ax2.set_ylim, which="y"
        )
    density_labels = {}
    for member in panel.layers:
        if member.type == "kde" and bounded_density_request(member, panel):
            from ._field_render import density_ordinate_label

            response = "x" if member.orient == "h" else member.axis
            density_labels.setdefault(response, set()).add(
                density_ordinate_label(member, panel)
            )
        elif member.type == "hist" and stages_for(member, "x"):
            config = member.histogram
            if (
                config
                and not config.cumulative
                and config.multiple != "fill"
                and config.stat in {"density", "frequency"}
            ):
                response = "x" if member.orient == "h" else member.axis
                value = (
                    "density"
                    if config.stat == "density"
                    else "mass"
                    if config.weights
                    else "count"
                )
                density_labels.setdefault(response, set()).add(
                    f"{value} (1/{coordinate_unit(member, 'x', 'input')})"
                )
    for name, labels in density_labels.items():
        settings = getattr(panel, name)
        if settings is not None and not settings.label and len(labels) == 1:
            target = ax2 if name == "y2" else ax
            assert target is not None
            (target.set_xlabel if name == "x" else target.set_ylabel)(
                next(iter(labels))
            )
    _apply_title(ax, panel)
    _apply_despine(ax, theme.axes)

    handles, labels = _unique_legend_handles(*_raw_legend_handles(ax, ax2))
    if guide_collector is not None:
        local = [
            (handle, label)
            for handle, label in zip(handles, labels, strict=True)
            if not getattr(handle, "_mudplot_shared_raw_handle", False)
        ]
        handles, labels = map(list, zip(*local, strict=True)) if local else ([], [])
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(leg, fig=ax.figure)
        handlers = {
            **getattr(ax, "_mudplot_legend_handlers", {}),
            **getattr(ax2, "_mudplot_legend_handlers", {}),
        }
        if leg.handler is not None:
            from ._legend_style import legend_handlers

            handlers = legend_handlers(handles, leg, handlers)
        if handlers:
            kw["handler_map"] = handlers
        legend_owner = ax2 if ax2 is not None and ax2.has_data() else ax
        legend_artist = legend_owner.legend(
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


def _count_colors(spec: FigureSpec, *, domains=None, regression_plans=None) -> int:
    from ._temporal_data import clock_order, select_line_rows

    domains = shared_scale_domains(spec) if domains is None else domains
    shared_colors = sum(d["colors"] for d in domains.values())
    counts = []
    for pi, p in enumerate(spec.panels):
        columns = panel_columns(spec.data.columns, p)
        count = 0
        for li, lyr in enumerate(p.layers):
            if lyr.type == "regplot" and lyr.semantics is not None:
                if lyr.color is None and regression_plans is not None:
                    count += len(regression_plans[pi, li].curves)
                config = lyr.semantics
                if (
                    config.hue is not None
                    and config.hue_kind == "categorical"
                    and config.scale_id is None
                ):
                    from ._regression_semantics import glyph_support

                    _, rows = glyph_support(spec.data.columns, lyr, p)
                    if rows:
                        count += len(
                            semantic_levels(spec.data.columns, config, "hue", rows)
                        )
                continue
            if lyr.color or lyr.type in _MATRIX_TYPES | {
                "surface",
                "contour3d",
                "contourf3d",
                "hist2d",
                "hexbin",
            }:
                continue
            if lyr.type in {"scatter", "scatter3d", "quiver"} and lyr.c is not None:
                continue
            _, clock_key, category_matches = clock_order(lyr, p)
            clock_args: ClockCategoryArgs = (
                {} if clock_key is None else {"category_key_for": clock_key}
            )
            if advanced_stairs(lyr, p):
                count += len(
                    stair_groups(
                        columns, lyr, range(len(columns[lyr.x])), retain_rows=False
                    )
                )
            elif lyr.type == "stem":
                from ._stem import stem_group_levels, stem_rows

                rows = stem_rows(columns, lyr)
                config = lyr.semantics
                if config is None or config.hue is None:
                    count += len(stem_group_levels(columns, lyr, rows)) or bool(rows)
                elif config.hue_kind == "categorical" and config.scale_id is None:
                    count += len(semantic_levels(columns, config, "hue", rows))
            elif advanced_lanes(lyr, p):
                config = lyr.semantics
                if config is None or config.hue is None:
                    count += len(lane_members(columns, lyr, order_only=True)[0])
                elif config.hue_kind == "categorical" and config.scale_id is None:
                    count += len(
                        semantic_levels(
                            columns, config, "hue", semantic_rows(columns, lyr)
                        )
                    )
            elif uses_vector(lyr):
                count += (
                    1
                    if lyr.type == "streamplot"
                    else len(vector_members(columns, lyr, order_only=True)[0])
                )
            elif lyr.type in RAW_HUE_TYPES and isinstance(lyr.hue_order, (list, tuple)):
                count += len(lyr.hue_order)
            elif (
                lyr.type
                in {
                    "scatter",
                    "lineplot",
                    "stripplot",
                    "ecdf",
                    "rug",
                    "swarmplot",
                    "box",
                    "violin",
                    "boxenplot",
                    "barplot",
                    "pointplot",
                }
                and lyr.semantics is not None
            ):
                config = lyr.semantics
                if config.hue is None:
                    if lyr.type in {"violin", "boxenplot"}:
                        from ._boxen import boxen_hues
                        from ._violin_options import violin_hues

                        rows = distribution_rows(
                            columns, lyr, category_matches=category_matches
                        )
                        from ._categorical import distribution_plan

                        categories, _, _ = distribution_plan(
                            columns, lyr, rows=rows, **clock_args
                        )
                        from ._categorical import distribution_channels

                        count += len(
                            categories
                            if not lyr.y and distribution_channels(lyr)[2] is None
                            else (
                                boxen_hues if lyr.type == "boxenplot" else violin_hues
                            )(columns, lyr, rows)
                        )
                    elif lyr.type == "swarmplot" and lyr.group is not None:
                        from ._categorical import swarm_levels

                        rows = distribution_rows(
                            columns, lyr, category_matches=category_matches
                        )
                        count += len(swarm_levels(columns, lyr, rows)[1])
                    elif lyr.type in {"barplot", "pointplot"} and lyr.group is not None:
                        advanced = new_stat_request(lyr, p)
                        rows = usable_rows(
                            columns,
                            lyr,
                            advanced=advanced,
                            category_matches=category_matches,
                        )
                        count += len(
                            category_levels(columns, lyr, rows, advanced=advanced)[1]
                        )
                    else:
                        count += 1
                elif config.hue_kind == "categorical" and config.scale_id is None:
                    rows = (
                        select_line_rows(columns, lyr, p)
                        if lyr.type == "lineplot" and category_matches is not None
                        else semantic_rows(
                            columns, lyr, category_matches=category_matches
                        )
                    )
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
            elif advanced_box(lyr) or advanced_violin(lyr) or advanced_boxen(lyr):
                from ._categorical import distribution_plan

                rows = distribution_rows(
                    columns, lyr, category_matches=category_matches
                )
                categories, groups, _ = distribution_plan(
                    columns, lyr, rows=rows, **clock_args
                )
                count += len(groups if lyr.y else categories)
            elif lyr.type in DISTRIBUTION_TYPES | {"swarmplot"}:
                rows = distribution_rows(
                    columns, lyr, category_matches=category_matches
                )
                categories, groups = distribution_levels(columns, lyr, rows)
                count += len(groups if lyr.y else categories)
            elif lyr.group and lyr.group in columns:
                if lyr.type in _STAT_TYPES:
                    advanced = new_stat_request(lyr, p)
                    rows = (
                        select_line_rows(columns, lyr, p)
                        if lyr.type == "lineplot" and category_matches is not None
                        else usable_rows(
                            columns,
                            lyr,
                            advanced=advanced,
                            category_matches=category_matches,
                        )
                    )
                    count += len(
                        category_levels(columns, lyr, rows, advanced=advanced)[1]
                    )
                else:
                    count += len(_unique_stable(columns[lyr.group]))
            else:
                count += 1
        counts.append(count)
    return shared_colors + max(counts, default=1)


def _align_secondary_legends(fig, pad_px: float) -> bool:
    from matplotlib.transforms import ScaledTranslation

    renderer = fig.canvas.get_renderer()
    moved = False
    for ax in native_axes(fig):
        legend = ax.get_legend()
        secondary = getattr(legend, "_mudplot_secondary_axis", None)
        if legend is None or secondary is None or ax.bbox.width <= 0:
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
       shrinking the native engine's working rectangle. Tight layout uses
       endpoints; constrained layout uses width/height. The native engine
       retains ownership of tick/label spacing inside that rectangle.
    2. Panel titles/suptitle already wrap (``wrap=True``) at the figure
       width via matplotlib's native text layout; this only needs to ask
       for a redraw after step 1 changes that width.
    """
    from matplotlib.artist import Artist
    from matplotlib.layout_engine import TightLayoutEngine

    pad_px = pad_inches * fig.dpi
    for _ in range(3):
        fig.canvas.draw()
        if not _align_secondary_legends(fig, pad_px):
            break
    renderer = fig.canvas.get_renderer()
    fig_w, fig_h = fig.bbox.width, fig.bbox.height

    left, bottom, right, top = 0.0, 0.0, 1.0, 1.0
    changed = False
    for ax in native_axes(fig):
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
    from ._shared_guides import shared_guide_bounds

    guide_rect = shared_guide_bounds(fig, renderer, pad_px)
    if guide_rect != (0.0, 0.0, 1.0, 1.0):
        left, bottom = max(left, guide_rect[0]), max(bottom, guide_rect[1])
        right, top = min(right, guide_rect[2]), min(top, guide_rect[3])
        changed = True

    if (
        changed
        and fig.get_layout_engine() is not None
        and right > left
        and top > bottom
    ):
        engine = fig.get_layout_engine()
        rect = (
            (left, bottom, right, top)
            if isinstance(engine, TightLayoutEngine)
            else (left, bottom, right - left, top - bottom)
        )
        engine.set(rect=rect)

    # Re-draw so wrapped titles measure against the (possibly now smaller)
    # available width; harmless no-op if nothing changed above.
    fig.canvas.draw()
    if _align_secondary_legends(fig, pad_px):
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    statistic_guides = getattr(fig, "_mudplot_statistic_guide_check", None)
    if statistic_guides is not None:
        statistic_guides.set_visible(True)
        statistic_guides.draw(renderer)
    automatic: list[Artist] = [
        ax.title for ax in native_axes(fig) if ax.title.get_text()
    ]
    if fig._suptitle is not None and fig._suptitle.get_text():
        automatic.append(fig._suptitle)
    for ax in native_axes(fig):
        legend = ax.get_legend()
        if legend is not None and getattr(legend, "_mudplot_auto_margin", False):
            automatic.append(legend)
    tight = isinstance(fig.get_layout_engine(), TightLayoutEngine)
    eligible = set()
    if tight:
        from ._quality import drawn_texts

        eligible = {id(text) for text in drawn_texts(fig)}
        for ax in native_axes(fig):
            for name in ("xaxis", "yaxis", "zaxis"):
                axis = getattr(ax, name, None)
                if axis is not None and id(axis.label) in eligible:
                    automatic.append(axis.label)
        automatic = list({id(artist): artist for artist in automatic}.values())
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
    tick_overlap = False
    if tight and boxes and not outside and not overlap:
        from matplotlib.transforms import Bbox

        def intersects(a, b):
            return (
                min(a.x1, b.x1) - max(a.x0, b.x0) > 1
                and min(a.y1, b.y1) - max(a.y0, b.y0) > 1
            )

        # Reuse drawn_texts eligibility; never compare all tick pairs. One
        # union per native axis/side rejects unrelated decoration candidates.
        for ax in native_axes(fig):
            for axis in (ax.xaxis, ax.yaxis):
                ticks = [*axis.get_major_ticks(), *axis.get_minor_ticks()]
                for side in ("label1", "label2"):
                    members = [
                        getattr(tick, side).get_window_extent(renderer)
                        for tick in ticks
                        if id(getattr(tick, side)) in eligible
                    ]
                    if not members:
                        continue
                    broad = Bbox.union(members)
                    if any(
                        intersects(decoration, broad)
                        and any(intersects(decoration, member) for member in members)
                        for decoration in boxes
                    ):
                        tick_overlap = True
                        break
                if tick_overlap:
                    break
            if tick_overlap:
                break
    if outside or overlap or tick_overlap:
        warnings.warn(
            "automatic layout text cannot fit the fixed canvas without clipping or "
            "overlap; add explicit line breaks, increase figure size or reduce text/"
            "font size. Canvas size is unchanged; "
            "manual positions remain caller-owned.",
            UserWarning,
            stacklevel=2,
        )


@matplotlib_context()
def render(spec: FigureSpec, *, fmt: str = "", layout_policy: str | None = None):
    """Build and return a matplotlib Figure for ``spec``.

    ``fmt`` is the output format the figure is destined for ("svg", "pgf",
    ...), which only affects how layer/title reference metadata
    (``citation``/``href``) is rendered; ``save()`` sets it from the file
    extension.

    Raises ``ValueError`` if ``spec`` is invalid (with all issues listed) or
    owned canvas work exceeds the 40-million-pixel effect budget. The source
    DPI is not clamped; editor previews use their existing capped copy.
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
    _check_render_budget(spec.size, spec.dpi)
    if layout_policy is not None:
        from ._quality import prepare

        spec = prepare(spec, layout_policy)
    from ._axis_options import configured, effective_panels

    axis_controls = any(
        configured(axis)
        for panel in spec.panels
        for axis in (panel.x, panel.y, panel.y2, panel.z)
        if axis is not None
    ) or any(
        panel.secondary_x is not None or panel.secondary_y is not None
        for panel in spec.panels
    )
    if axis_controls:
        panels, _ = effective_panels(spec)
        spec = replace(spec, panels=panels)
    from ._matrix_budget import matrix_admission

    matrix_plan = matrix_admission(spec)
    domains = shared_scale_domains(spec)
    from ._regression_inference import prepare_regressions

    regression_plans, regression_work = prepare_regressions(spec, _regression_fit)
    boxen_plans = prepare_boxen_plans(spec, domains=domains)
    from ._line_inference import prepare_line_inference

    line_plans, line_work = prepare_line_inference(spec)
    from ._shared_guides import SharedGuideCollector

    guide_collector = (
        SharedGuideCollector(spec, domains) if spec.shared_guides else None
    )

    rc = spec_to_rcparams(
        spec.theme,
        spec.journal,
        n_colors=max(
            _count_colors(spec, domains=domains, regression_plans=regression_plans), 3
        ),
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
            layout=(
                nested_tight_layout_engine()
                if spec.panel_layout is not None
                and (
                    matrix_plan is None
                    or not matrix_plan.layers
                    or not all(panel.projection == "2d" for panel in spec.panels)
                )
                else None
                if has_3d
                else "constrained"
            ),
        )
        # Interactive HiDPI backends may round inches to device pixels.
        fig.set_size_inches((spec.size[0], spec.size[1]), forward=False)
        try:
            _check_render_budget(fig.get_size_inches(), fig.dpi)
            if matrix_plan is not None and matrix_plan.scalars:
                from ._scalar_render import native_scalar_maps

                fig.__dict__["_mudplot_scalar_maps"] = native_scalar_maps(
                    matrix_plan.scalars
                )
            if matrix_plan is not None:
                fig.__dict__["_mudplot_matrix_admission"] = matrix_plan
            from ._layout_render import (
                build_axes,
                check_extents,
                link_axes,
                link_twin_values,
                tag_axes,
            )

            if spec.panel_layout is not None:
                panel_axes = build_axes(fig, spec)
            else:
                gs = fig.add_gridspec(rows, cols, **gridspec_kw)
                panel_axes = []
                for i, panel in enumerate(spec.panels):
                    r, c = divmod(i, cols)
                    projection = None if panel.projection == "2d" else panel.projection
                    ax = fig.add_subplot(gs[r, c], projection=projection)
                    tag_axes(ax, i, panel)
                    panel_axes.append(ax)
            link_axes(panel_axes, spec)

            for i, (ax, panel) in enumerate(zip(panel_axes, spec.panels, strict=False)):
                _draw_panel(
                    ax,
                    spec,
                    panel,
                    domains=domains,
                    boxen_plans={
                        li: plan for (pi, li), plan in boxen_plans.items() if pi == i
                    },
                    line_plans={
                        li: plan for (pi, li), plan in line_plans.items() if pi == i
                    },
                    regression_plans={
                        li: plan
                        for (pi, li), plan in regression_plans.items()
                        if pi == i
                    },
                    guide_collector=guide_collector,
                )
                _apply_panel_label(ax, spec, panel, i)
            link_twin_values(panel_axes, spec)
            if axis_controls:
                from ._axis_render import install_axes

                install_axes(fig, spec, panel_axes)
            if guide_collector is not None:
                guide_collector.finish(fig)

            if spec.suptitle:
                fig.suptitle(spec.suptitle, wrap=True)
            if matrix_plan is not None and matrix_plan.layers:
                from ._matrix_layout import fit_matrix_legends

                fit_matrix_legends(fig)
            if has_3d and spec.panel_layout is None:
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
            if layout_policy is not None:
                from ._quality import apply_smart

                apply_smart(fig, spec, layout_policy)
            if spec.panel_layout is not None:
                fig.canvas.draw()
                check_extents(panel_axes)
            if matrix_plan is not None:
                if matrix_plan.layers:
                    from ._matrix_layout import check_matrix_layout

                    fig.canvas.draw()
                    check_matrix_layout(fig)
                # The live admission is not a persisted result or data owner.
                fig.__dict__["_mudplot_matrix_work"] = matrix_plan.work
                del fig.__dict__["_mudplot_matrix_admission"]
            # Reference table for this figure's markers, needed after the
            # render context exits (see save()'s .pgf post-processing).
            cast(Any, fig)._mudplot_refs = list(_REFS.get() or [])
            cast(Any, fig)._mudplot_ref_measure = spec.reference_measure_text or ""
            cast(Any, fig)._mudplot_line_inference_work = line_work
            cast(Any, fig)._mudplot_regression_work = regression_work
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


def _check_render_budget(size, dpi) -> None:
    dpi = float(dpi)
    width, height = (float(value) * dpi for value in size)
    if (
        not math.isfinite(width)
        or not math.isfinite(height)
        or width * height > MAX_RENDER_PIXELS
    ):
        raise ValueError(
            f"render canvas exceeds {MAX_RENDER_PIXELS} pixels; reduce size or DPI"
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
    _check_render_budget(fig.get_size_inches(), fig.dpi)
    _check_render_budget(fig.get_size_inches(), spec.dpi)
    if tight:
        bbox = fig.get_tightbbox()
        if bbox is not None:
            pad = kwargs["pad_inches"]
            _check_render_budget(
                (bbox.width + 2 * pad, bbox.height + 2 * pad), spec.dpi
            )
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


def _save_destination(path):
    import pathlib

    import matplotlib as mpl

    destination = pathlib.Path(path)
    if not destination.suffix:
        destination = destination.with_name(
            f"{destination.name}.{mpl.rcParams['savefig.format']}"
        )
    return destination


@matplotlib_context()
def save(
    spec: FigureSpec,
    path: str,
    *,
    tight: bool = False,
    layout_policy: str | None = None,
):
    """Save at the exact spec size; ``tight=True`` opts into content cropping.

    The extension picks the backend, including ``.pgf`` for LaTeX-native
    export (where ``citation``/``href`` metadata becomes real \\figcite /
    \\href macros -- see :data:`mudplot.tex.PREAMBLE`).

    Returns an open Figure, owned by the caller, on success.
    """
    import pathlib
    import tempfile

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as error:
        if error.name not in ("numpy", "matplotlib"):
            raise
        raise ImportError(
            "rendering requires 'mudplot[render]'; install it first"
        ) from error

    from .io import _atomic_destination, _publish_bundle

    destination = _save_destination(path)
    fmt = destination.suffix.lstrip(".").lower()
    if fmt == "pgf":
        _require_texsystem()
    fig = (
        render(spec, fmt=fmt)
        if layout_policy is None
        else render(spec, fmt=fmt, layout_policy=layout_policy)
    )
    try:
        if fmt == "pgf":
            with tempfile.TemporaryDirectory(
                prefix=".mudplot-pgf-", dir=destination.resolve().parent
            ) as directory:
                stage = pathlib.Path(directory)
                staged = stage / destination.name
                _save_figure(fig, spec, staged, fmt, tight=tight)
                staged.write_bytes(
                    _substitute_pgf_references(
                        staged.read_text(encoding="utf-8"),
                        getattr(fig, "_mudplot_refs", []),
                        getattr(fig, "_mudplot_ref_measure", ""),
                    ).encode("utf-8")
                )
                sidecars = sorted(
                    p for p in stage.iterdir() if p.is_file() and p != staged
                )
                _publish_bundle([*sidecars, staged], destination.parent)
        else:
            with _atomic_destination(destination) as temporary:
                _save_figure(fig, spec, temporary, fmt, tight=tight)
    except BaseException:
        plt.close(fig)
        raise
    return fig
