"""Scaled numeric regression effects; optional models import only on demand."""

from __future__ import annotations

import warnings

import numpy as np


def _optional_fit(model, x, y, at, config):
    try:
        if model == "lowess":
            from statsmodels.nonparametric.smoothers_lowess import lowess

            return lowess(
                y,
                x,
                frac=config.frac,
                it=config.iterations,
                xvals=at,
                is_sorted=False,
                missing="none",  # finite values checked before optional effects
                return_sorted=False,
            )
        design = np.column_stack((np.ones(len(x)), x))
        prediction = np.column_stack((np.ones(len(at)), at))
        if model == "robust":
            from statsmodels.robust.norms import HuberT
            from statsmodels.robust.robust_linear_model import RLM

            # An exact line already minimizes every Huber loss; avoid a zero MAD fit.
            coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
            if np.max(np.abs(y - design @ coefficients)) <= 32 * np.finfo(float).eps:
                return prediction @ coefficients
            result = RLM(y, design, M=HuberT()).fit(maxiter=50, tol=1e-8)
            if result.fit_history.get("iteration", 0) >= 50:
                raise ValueError(
                    "robust regression did not converge within 50 iterations"
                )
            return result.predict(prediction)
        from statsmodels.genmod.families import Binomial
        from statsmodels.genmod.generalized_linear_model import GLM

        result = GLM(y, design, family=Binomial()).fit(maxiter=100, tol=1e-8)
        if not result.converged:
            raise ValueError(
                "logistic regression did not converge within 100 iterations"
            )
        return result.predict(prediction)
    except ImportError as error:
        raise ImportError(
            "robust/logistic/LOWESS effects require optional mudplot[regression]"
        ) from error


def fit_regression(x, y, layer, polynomial_fit, *, at=None, weights=None):
    """Return original-coordinate grid/response/CI; no mutation or global RNG."""
    config = layer.regression
    assert config is not None
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    model = config.model
    if weights is not None and (
        model not in ("poly", "logx") or layer.confidence is not None
    ):
        raise ValueError("weighted regression supports poly/logx point fits only")
    fit_options = {} if weights is None else {"weights": weights}
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", invalid="raise", divide="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        warnings.simplefilter("error", UserWarning)
        try:
            transformed = np.log(x) if model == "logx" else x
            magnitude = float(np.max(np.abs(transformed))) or 1.0
            unit = transformed / magnitude
            center = float(unit.min()) / 2 + float(unit.max()) / 2
            scale = (float(unit.max()) - float(unit.min())) / 2
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("regression x range is numerically singular")
            scaled = (unit - center) / scale
            points = None
            if at is not None:
                original_at = np.asarray(at, dtype=float)
                transformed_at = np.log(original_at) if model == "logx" else original_at
                points = (transformed_at / magnitude - center) / scale
            response_scale = float(np.max(np.abs(y))) or 1.0
            response = y / response_scale
            if model in ("poly", "logx"):
                grid, fitted, interval = polynomial_fit(
                    scaled,
                    response,
                    layer.degree,
                    layer.confidence,
                    at=points,
                    **fit_options,
                )
            else:
                grid = (
                    np.linspace(float(scaled.min()), float(scaled.max()), 200)
                    if points is None
                    else points
                )
                if any(
                    not np.isfinite(values).all() for values in (scaled, response, grid)
                ):
                    raise ValueError("optional regression inputs must be finite")
                fitted = _optional_fit(model, scaled, response, grid, config)
                interval = None
            raw_grid = (grid * scale + center) * magnitude
            if model == "logx":
                raw_grid = np.exp(raw_grid)
            fitted = np.asarray(fitted, dtype=float) * response_scale
            if interval is not None:
                interval = tuple(
                    np.asarray(bound) * response_scale for bound in interval
                )
            arrays = [raw_grid, fitted, *(interval or ())]
            if any(not np.isfinite(array).all() for array in arrays):
                raise ValueError("regression produced nonfinite predictions")
            return raw_grid, fitted, interval
        except (
            ValueError,
            FloatingPointError,
            np.linalg.LinAlgError,
            Warning,
        ) as error:
            raise ValueError(f"{model} regression fit failed: {error}") from error


def draw_prepared_regression(
    ax, prepared, color_iter, theme, *, raw_columns=None, visual_layer=None, domain=None
):
    """Draw actual declared quantities; independent styles never refit a model."""
    from ._components import apply_component_style
    from ._render import _decorate

    layer = prepared.layer
    config = layer.regression
    components = config.components
    fit_style = None if components is None else components.fit
    scatter_style = None if components is None else components.scatter
    show_fit = components is None or components.show_fit
    show_scatter = components is None or components.show_scatter
    horizontal = layer.orient == "h"
    residual = config.residual
    glyphs = None
    fit_colors = None
    if layer.semantics is not None:
        from ._regression_semantics_render import RegressionGlyphs

        # Reserve the scientific group's default ink before the point mapping
        # can consume any independent categorical colours.
        if layer.color is None:
            fit_colors = [next(color_iter) for _ in prepared.curves]
        glyphs = RegressionGlyphs(
            ax, prepared, visual_layer, raw_columns, color_iter, domain
        )

    def xy(predictor, response):
        return (response, predictor) if horizontal else (predictor, response)

    def check(predictor, response, bounds=None):
        for axis, values in (
            (ax.yaxis if horizontal else ax.xaxis, predictor),
            (ax.xaxis if horizontal else ax.yaxis, response),
        ):
            if axis.get_scale() == "log" and np.any(np.asarray(values) <= 0):
                raise ValueError("regression native log coordinates must be positive")
        response_axis = ax.xaxis if horizontal else ax.yaxis
        if (
            bounds is not None
            and response_axis.get_scale() == "log"
            and any(np.any(values <= 0) for values in bounds)
        ):
            raise ValueError("regression native confidence bounds must be positive")

    def band(grid, bounds, color, alpha):
        if bounds is not None and len(grid):
            draw = ax.fill_betweenx if horizontal else ax.fill_between
            return draw(
                grid,
                bounds[0],
                bounds[1],
                color=color,
                alpha=0.2 * alpha,
                linewidth=0,
                label="_nolegend_",
            )
        return None

    def bars(predictor, bounds, color, width, alpha, rows):
        if bounds is not None and len(predictor):
            artist = (ax.hlines if horizontal else ax.vlines)(
                predictor,
                bounds[0],
                bounds[1],
                color=color,
                linewidth=width,
                alpha=alpha,
                label="_nolegend_",
            )
            artist._mudplot_source_rows = rows
            return artist
        return None

    if residual and prepared.curves:
        (ax.axvline if horizontal else ax.axhline)(
            0, color="#6b7280", linewidth=0.75, linestyle="--", label="_nolegend_"
        )._mudplot_regression_role = "zero_reference"
    for index, curve in enumerate(prepared.curves):
        color = layer.color or (
            next(color_iter) if fit_colors is None else fit_colors[index]
        )
        marker = (
            layer.marker
            if layer.marker is not None
            else (
                theme.markers[index % len(theme.markers)]
                if theme.redundant_encoding and layer.group is not None
                else "o"
            )
        )
        label = str(curve.group) if layer.group is not None else layer.label
        if layer.label is not None and layer.group is not None:
            label = f"{layer.label}: {curve.group}"
        context_prefix = label

        def context(name, prefix=context_prefix):
            return _decorate(
                f"{prefix}: {name}" if prefix else name,
                layer.citation,
                layer.href,
            )

        label = _decorate(label, layer.citation, layer.href)
        width = 1.5 if layer.line_width is None else layer.line_width
        alpha = layer.alpha
        fit_color = (
            color if fit_style is None or fit_style.color is None else fit_style.color
        )
        fit_width = (
            width
            if fit_style is None or fit_style.line_width is None
            else fit_style.line_width
        )
        fit_alpha = (
            alpha if fit_style is None or fit_style.alpha is None else fit_style.alpha
        )
        check(
            curve.observation_x,
            curve.observation_y,
            curve.mean_bounds if residual else None,
        )
        check(curve.grid, curve.mean, curve.mean_bounds if not residual else None)
        check(curve.query_x, curve.query_mean, curve.query_bounds)
        check(curve.trend_grid, curve.trend_mean, curve.trend_bounds)
        if show_scatter and len(curve.observation_x):
            style = scatter_style
            size = 6 if layer.marker_size is None else layer.marker_size
            edge = layer.edge_color
            face = color
            glyph = marker
            edge_width = layer.line_width
            scatter_alpha = alpha
            if style is not None:
                face = style.color or face
                face = style.face_color if style.face_color is not None else face
                edge = style.edge_color if style.edge_color is not None else edge
                glyph = style.marker or glyph
                size = style.marker_size if style.marker_size is not None else size
                edge_width = (
                    style.marker_edge_width
                    if style.marker_edge_width is not None
                    else style.line_width
                    if style.line_width is not None
                    else edge_width
                )
                scatter_alpha = style.alpha if style.alpha is not None else alpha
            role = (
                "diagnostic"
                if residual
                else "adjusted_observation"
                if config.partial is not None
                else "observation"
            )
            points = xy(curve.observation_x, curve.observation_y)
            if glyphs is None:
                artist = ax.scatter(
                    *points,
                    label=label,
                    s=size**2,
                    marker=glyph,
                    facecolors=face,
                    edgecolors=edge,
                    linewidths=edge_width,
                    alpha=scatter_alpha,
                )
                artist._mudplot_source_rows = curve.observation_rows
                artist._mudplot_regression_role = role
            else:
                glyphs.draw(
                    index,
                    role,
                    points,
                    face=face,
                    edge=edge,
                    edgewidth=edge_width,
                    diameter=size,
                    marker=glyph,
                    alpha=scatter_alpha,
                )
        if show_fit:
            if residual:
                interval_artist = bars(
                    curve.observation_x,
                    curve.mean_bounds,
                    fit_color,
                    fit_width,
                    fit_alpha,
                    curve.observation_rows,
                )
                if interval_artist is not None:
                    interval_artist.set_label(context("Mapped mean-fit uncertainty"))
            elif len(curve.grid):
                artist = ax.plot(
                    *xy(curve.grid, curve.mean),
                    color=color,
                    label=context(
                        "Conditional fit"
                        if config.partial is not None
                        else "Huber fit"
                        if config.model == "robust"
                        else "LOWESS smoother"
                        if config.model == "lowess"
                        else "Mean fit"
                    )
                    if show_scatter
                    else label,
                    linewidth=width,
                    linestyle=layer.line_style or "-",
                    alpha=alpha,
                )[0]
                apply_component_style(artist, fit_style)
                artist._mudplot_regression_role = (
                    "conditional_fit" if config.partial is not None else "mean_fit"
                )
                band(curve.grid, curve.mean_bounds, fit_color, fit_alpha)
            if not residual and len(curve.query_x):
                points = xy(curve.query_x, curve.query_mean)
                if glyphs is None:
                    artist = ax.plot(
                        *points,
                        linestyle="None",
                        marker=marker,
                        markersize=6
                        if layer.marker_size is None
                        else layer.marker_size,
                        color=color,
                        alpha=alpha,
                        label=context("Query fitted responses"),
                    )[0]
                    apply_component_style(artist, fit_style)
                    artist.set_linestyle("None")
                    artist._mudplot_source_rows = curve.query_rows
                    artist._mudplot_regression_role = "query_mean_prediction"
                else:
                    style = fit_style
                    glyphs.draw(
                        index,
                        "query_mean_prediction",
                        points,
                        face=fit_color
                        if style is None or style.face_color is None
                        else style.face_color,
                        edge=layer.edge_color
                        if style is None or style.edge_color is None
                        else style.edge_color,
                        edgewidth=layer.line_width
                        if style is None or style.marker_edge_width is None
                        else style.marker_edge_width,
                        diameter=(6 if layer.marker_size is None else layer.marker_size)
                        if style is None or style.marker_size is None
                        else style.marker_size,
                        marker=marker
                        if style is None or style.marker is None
                        else style.marker,
                        alpha=fit_alpha,
                    )
                bars(
                    curve.query_x,
                    curve.query_bounds,
                    fit_color,
                    fit_width,
                    fit_alpha,
                    curve.query_rows,
                )
        if len(curve.trend_grid):
            trend = config.diagnostics.trend
            artist = ax.plot(
                *xy(curve.trend_grid, curve.trend_mean),
                color=color,
                linewidth=width,
                linestyle="-",
                alpha=alpha,
                label=context(f"Independent residual trend ({trend.model})"),
            )[0]
            apply_component_style(artist, trend.style)
            artist._mudplot_regression_role = "independent_residual_trend"
            band(
                curve.trend_grid,
                curve.trend_bounds,
                artist.get_color(),
                artist.get_alpha(),
            )
        if curve.caption:
            title_axes = getattr(ax, "_mudplot_semantic_guide_axis", ax)
            captions = getattr(title_axes, "_mudplot_inference_captions", [])
            if curve.caption not in captions:
                captions.append(curve.caption)
            title_axes._mudplot_inference_captions = captions
