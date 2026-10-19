"""High-level, intuitive user API.

The fluent builder is *sugar over actions*: each method dispatches an action to
a :class:`~mudplot.store.Store`, which runs the pure reducer. There is no hidden
mutable state — only the spec inside the store. This is the exact same update
path a future Rust/htmx editor would drive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import actions as A
from ._components import make_components
from ._stat import make_stat
from .reducer import reduce_all
from .spec import (
    ClusterSpec,
    DistributionComponentsSpec,
    ECDFSpec,
    FigureSpec,
    HeatmapSpec,
    HistogramSpec,
    KDE2DSpec,
    KDESpec,
    LayerSpec,
    RegressionSpec,
    SemanticSpec,
)
from .store import Store

if TYPE_CHECKING:
    from .color.palette import Palette
    from .theme import JournalProfile

__all__ = ["Plot", "apply", "color_palette", "plot"]


from .data import to_columns as _columns_from


class Plot:
    """Fluent builder that dispatches actions to an internal store.

    ``self.spec`` always reflects the current (pure-reduced) state.
    Call :meth:`render`, :meth:`save`, or :meth:`to_json` to materialise.
    """

    def __init__(self, data: Any = None, *, query: str | None = None, params: Any = ()):
        self._store = Store(FigureSpec())
        if data is not None or query is not None:
            self._store._dispatch(
                A.SetData(_columns_from(data, query=query, params=params))
            )

    @property
    def spec(self) -> FigureSpec:
        return self._store.state

    @property
    def store(self) -> Store:
        return self._store

    def dispatch(self, action: A.Action) -> Plot:
        self._store._dispatch(action)
        return self

    # -- agent-facing: JSON actions ----------------------------------------
    def apply(self, actions) -> Plot:
        """Apply a list of JSON/dict (or Action) actions in order."""
        for a in actions:
            self._store._dispatch(
                a if not isinstance(a, dict) else A.action_from_dict(a)
            )
        return self

    @property
    def action_log(self) -> list[dict]:
        """The dispatched actions as JSON-ready dicts (build history)."""
        return [A.action_to_dict(a) for a in self._store.history]

    # -- data-drawing layers ------------------------------------------------
    def line(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="line", x=x, y=y, group=group, label=label, **style),
                panel=panel,
            )
        )

    def stem(
        self,
        x: str,
        y: str,
        *,
        baseline: float = 0.0,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw vertical numeric stems without reordering or aggregating rows."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stem", x=x, y=y, baseline=baseline, label=label, **style
                ),
                panel=panel,
            )
        )

    def stairs(
        self,
        values: str,
        edges: list[float],
        *,
        baseline: float = 0.0,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw supplied bin heights with explicit edges, without re-estimation."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stairs",
                    x=values,
                    bins=edges,
                    baseline=baseline,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def regplot(
        self,
        x: str,
        y: str,
        *,
        regression: RegressionSpec | dict | None = None,
        weights: str | None = None,
        degree: int = 1,
        confidence: float | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Scatter plus a polynomial fit and optional mean-fit confidence band.

        ``confidence`` is a percentage (for example ``95``) using a normal
        approximation; it is disabled by default rather than implying
        uncertainty the caller did not request. ``weights`` selects relative
        poly/logx point fitting only; weighted confidence bands are rejected.
        """
        from ._regression import prepare_regression, weighted_option_issues

        config = prepare_regression(regression)
        if weights is not None and config is None:
            config = RegressionSpec()
        problems = weighted_option_issues(config, confidence, weights)
        if problems:
            raise ValueError("; ".join(problems))
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="regplot",
                    regression=config,
                    weights=weights,
                    x=x,
                    y=y,
                    degree=degree,
                    confidence=confidence,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def scatter(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        label: str | None = None,
        c: str | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = False,
        clabel: str | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Legacy group/c scatter, or independent opt-in hue/size/style roles.

        Advanced kinds/orders/linear bounds/diameters/markers use SemanticSpec
        or its strict dict. Numeric guides are mappings, not invented samples.
        Do not combine legacy group/c or scalar overrides with mapped roles.
        """
        mapped = any(value is not None for value in (hue, size, style))
        if semantics is not None and mapped:
            raise ValueError("pass either semantics or hue/size/style keywords")
        if semantics is not None:
            data = (
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            config = SemanticSpec.from_dict(data)
        else:
            config = SemanticSpec(hue=hue, size=size, style=style) if mapped else None
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="scatter",
                    x=x,
                    y=y,
                    group=group,
                    label=label,
                    c=c,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    semantics=config,
                    **appearance,
                ),
                panel=panel,
            )
        )

    def residplot(
        self,
        x: str,
        y: str,
        *,
        degree: int = 1,
        regression: RegressionSpec | dict | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Raw response residuals from a fitted model, with a zero reference guide."""
        from ._regression import prepare_regression

        config = prepare_regression(regression, residual=True)
        return self.regplot(
            x,
            y,
            degree=degree,
            regression=config,
            group=group,
            label=label,
            panel=panel,
            **style,
        )

    def stripplot(
        self,
        x: str,
        y: str,
        *,
        jitter: float = 0.15,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Plot raw observations with deterministic horizontal jitter."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stripplot",
                    x=x,
                    y=y,
                    jitter=jitter,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def swarmplot(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        warn_thresh: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Pack circular observations in display space on every draw.

        x stays categorical, y numeric; positive log-value axes are supported.
        Numeric dodge is the hue span (None auto, 0 packs hues together).
        Overcrowding retains all rows and warns, not a fake jitter approximation.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="swarmplot",
                    x=x,
                    y=y,
                    group=group,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    warn_thresh=warn_thresh,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def stackplot(
        self,
        x: str,
        y: str,
        *,
        group: str,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Stack long-form ``y`` series grouped by ``group`` over shared ``x``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="stackplot", x=x, y=y, group=group, **style),
                panel=panel,
            )
        )

    def hist2d(
        self,
        x: str,
        y: str,
        *,
        bins: int | list[float] = 20,
        density: bool = False,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Bin two numeric columns, with at most 512 bins per axis."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hist2d",
                    x=x,
                    y=y,
                    bins=bins,
                    density=density,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def hexbin(
        self,
        x: str,
        y: str,
        *,
        gridsize: int = 30,
        mincnt: int | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Bin two numeric columns, with gridsize in 1..512."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hexbin",
                    x=x,
                    y=y,
                    gridsize=gridsize,
                    mincnt=mincnt,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def quiver(
        self,
        x: str,
        y: str,
        u: str,
        v: str,
        *,
        c: str | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = False,
        clabel: str | None = None,
        scale: float | None = None,
        width: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw a 2-D vector field from position and component columns."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="quiver",
                    x=x,
                    y=y,
                    u=u,
                    v=v,
                    c=c,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    quiver_scale=scale,
                    quiver_width=width,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def heatmap(
        self,
        matrix: str,
        *,
        heatmap: HeatmapSpec | dict | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Heatmap of a registered matrix; opt-in controls use HeatmapSpec/dict."""
        config = None
        if heatmap is not None:
            config = HeatmapSpec.from_dict(
                heatmap.to_dict() if isinstance(heatmap, HeatmapSpec) else heatmap
            )
            if not isinstance(config, HeatmapSpec):
                raise TypeError("heatmap must decode to HeatmapSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="heatmap",
                    matrix=matrix,
                    heatmap=config,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def clustermap(
        self,
        matrix: str,
        *,
        cluster: ClusterSpec | dict | None = None,
        heatmap: HeatmapSpec | dict | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Hierarchical matrix heatmap with effect-time row/column dendrograms."""
        config = ClusterSpec.from_dict(
            {}
            if cluster is None
            else cluster.to_dict()
            if isinstance(cluster, ClusterSpec)
            else cluster
        )
        display = HeatmapSpec.from_dict(
            {}
            if heatmap is None
            else heatmap.to_dict()
            if isinstance(heatmap, HeatmapSpec)
            else heatmap
        )
        if not isinstance(config, ClusterSpec) or not isinstance(display, HeatmapSpec):
            raise TypeError(
                "clustermap settings must decode to ClusterSpec/HeatmapSpec"
            )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="clustermap",
                    matrix=matrix,
                    cluster=config,
                    heatmap=display,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def matrix(self, name: str, values) -> Plot:
        """Register a 2-D matrix (list of rows) under ``name`` for ``.heatmap()``
        (also used by ``.contour()``/``.contourf()``/``.surface()``/``.wireframe()``).
        """
        return self.dispatch(A.SetMatrix(name, [list(row) for row in values]))

    def contour(
        self,
        matrix: str,
        *,
        levels: int | list[float] | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Contour lines of a 2-D matrix registered with ``.matrix(name, values)``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="contour",
                    matrix=matrix,
                    levels=levels,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def contourf(
        self,
        matrix: str,
        *,
        levels: int | list[float] | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Filled contours of a 2-D matrix registered with ``.matrix(name, values)``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="contourf",
                    matrix=matrix,
                    levels=levels,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def bar(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        yerr: str | None = None,
        y_lower: str | None = None,
        y_upper: str | None = None,
        bar_width: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Bars with optional caller-supplied uncertainty, dodged by group.

        ``yerr`` names a column of symmetric error magnitudes (e.g. SD).
        Alternatively, ``y_lower``/``y_upper`` name absolute endpoints of
        a precomputed interval (e.g. 95% CI), not error magnitudes. No
        statistical estimation is performed. ``bar_width`` controls the
        total category span (default 0.8), divided between grouped bars.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="bar",
                    x=x,
                    y=y,
                    group=group,
                    yerr=yerr,
                    y_lower=y_lower,
                    y_upper=y_upper,
                    bar_width=bar_width,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def barplot(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        estimator: str = "mean",
        errorbar: str | tuple[str, float] | None = "ci",
        n_boot: int = 1000,
        seed: int = 0,
        weights: str | None = None,
        units: str | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        baseline: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Estimate raw observations per category/hue; do not pre-average data.

        Named estimators and SD/SE/PI/seeded percentile-bootstrap CI are
        explicit statistical settings. Existing ``bar()`` remains a
        primitive for already summarized values. Weighted means use paired-row
        bootstrap CI; units opt into two-stage (unit then within-unit) resampling.
        Missing/zero-weight rows are excluded. Callables are not stored in specs.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="barplot",
                    x=x,
                    y=y,
                    group=group,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    baseline=baseline,
                    label=label,
                    stat=make_stat(
                        estimator, errorbar, n_boot, seed, weights=weights, units=units
                    ),
                    **style,
                ),
                panel=panel,
            )
        )

    def lineplot(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        estimator: str = "mean",
        errorbar: str | tuple[str, float] | None = "ci",
        n_boot: int = 1000,
        seed: int = 0,
        weights: str | None = None,
        units: str | None = None,
        sort: bool = True,
        orient: str = "v",
        stat_scale: str = "data",
        hue_order: list[Any] | None = None,
        error_style: str | None = None,
        error_alpha: float | None = None,
        label: str | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Numeric-x cell estimates with pointwise bands/bars, not simultaneous CI.

        Raw .line() is unchanged. Units resample within each x cell, not entire
        longitudinal curves. sort=False uses per-hue first-observed x order;
        nonmonotonic bands fail clearly (use sorting or bars). Independent roles
        partition raw tuples; size maps stroke widths in points, style markers
        and optional named dashes. Numeric guides aren't extra observations.
        """
        mapped = any(value is not None for value in (hue, size, style))
        if semantics is not None and mapped:
            raise ValueError("pass either semantics or hue/size/style keywords")
        if semantics is not None:
            data = (
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            config = SemanticSpec.from_dict(data)
        else:
            config = SemanticSpec(hue=hue, size=size, style=style) if mapped else None
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="lineplot",
                    x=x,
                    y=y,
                    group=group,
                    semantics=config,
                    orient=orient,
                    sort=sort,
                    stat_scale=stat_scale,
                    hue_order=hue_order,
                    error_style=error_style,
                    error_alpha=error_alpha,
                    label=label,
                    stat=make_stat(
                        estimator, errorbar, n_boot, seed, weights=weights, units=units
                    ),
                    **appearance,
                ),
                panel=panel,
            )
        )

    def pointplot(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        estimator: str = "mean",
        errorbar: str | tuple[str, float] | None = "ci",
        n_boot: int = 1000,
        seed: int = 0,
        weights: str | None = None,
        units: str | None = None,
        dodge: float | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Raw-data estimates and intervals with optional connecting lines.

        ``dodge`` is a total category span for hue offsets (default zero).
        Use ``line_style="none"`` to omit connecting lines. Missing category
        cells break the line rather than bridging unobserved categories.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="pointplot",
                    x=x,
                    y=y,
                    group=group,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    label=label,
                    dodge=dodge,
                    stat=make_stat(
                        estimator, errorbar, n_boot, seed, weights=weights, units=units
                    ),
                    **style,
                ),
                panel=panel,
            )
        )

    def countplot(
        self,
        x: str,
        *,
        group: str | None = None,
        stat: str = "count",
        native_scale: bool = False,
        baseline: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Count observations or globally normalized proportions/percentages.

        ``stat``: count, probability/proportion, percent. The denominator is all
        usable selected observations (not each hue/category separately).
        No y column or inferred count interval is required.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="countplot",
                    x=x,
                    group=group,
                    native_scale=native_scale,
                    baseline=baseline,
                    label=label,
                    stat=make_stat("count", None, 1000, 0, normalize=stat),
                    **style,
                ),
                panel=panel,
            )
        )

    def errorbar(
        self,
        x: str,
        y: str,
        *,
        yerr: str | None = None,
        xerr: str | None = None,
        y_lower: str | None = None,
        y_upper: str | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Points with symmetric errors or absolute y interval endpoints.

        Use ``yerr`` OR paired ``y_lower``/``y_upper`` columns; intervals
        are supplied by the caller, never inferred from SD or sample size.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="errorbar",
                    x=x,
                    y=y,
                    yerr=yerr,
                    xerr=xerr,
                    y_lower=y_lower,
                    y_upper=y_upper,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def band(
        self,
        x: str,
        lower: str,
        upper: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Shaded band (fill_between) from ``lower`` to ``upper`` columns."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="band",
                    x=x,
                    y=upper,
                    y2=lower,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def hline(
        self, value: float, *, label: str | None = None, panel: int = 0, **style
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="hline", value=value, label=label, **style), panel=panel
            )
        )

    def vline(
        self, value: float, *, label: str | None = None, panel: int = 0, **style
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="vline", value=value, label=label, **style), panel=panel
            )
        )

    def text(self, text: str, at: list[float], *, panel: int = 0, **style) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="text", text=text, at=list(at), **style), panel=panel
            )
        )

    def annotate(
        self,
        text: str,
        at: list[float],
        *,
        to: list | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="annotate",
                    text=text,
                    at=list(at),
                    to=list(to) if to else None,
                    **style,
                ),
                panel=panel,
            )
        )

    def hist(
        self,
        x: str,
        *,
        bins: int | list = 20,
        density: bool = False,
        stat: str | None = None,
        weights: str | None = None,
        common_norm: bool | None = None,
        cumulative: bool = False,
        multiple: str | None = None,
        element: str | None = None,
        group: str | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Opt-in shared-bin weighted statistics, retaining legacy calls unchanged.

        Explicit statistics/geometry/style options create HistogramSpec.
        Density uses original raw bin widths; normalized
        mass includes only in-range rows. Cumulative density integrates mass.
        Grouped stack/dodge change geometry, not heights or normalization.
        Element='step' draws unfilled native stairs with layer/stack (not dodge).
        Without new options, density/group/bin behavior remains Matplotlib's.
        """
        advanced = (
            stat is not None
            or weights is not None
            or common_norm is not None
            or cumulative is not False
            or multiple is not None
            or element is not None
            or orient != "v"
            or hue_order is not None
            or any(style.get(key) is not None for key in ("line_width", "edge_color"))
        )
        config = (
            HistogramSpec(
                stat if stat is not None else "density" if density else "count",
                weights,
                True if common_norm is None else common_norm,
                cumulative,
                "layer" if multiple is None else multiple,
                "bars" if element is None else element,
            )
            if advanced
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hist",
                    x=x,
                    bins=bins,
                    density=density,
                    histogram=config,
                    group=group,
                    hue_order=hue_order,
                    orient=orient,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def boxenplot(
        self,
        x: str,
        y: str | None = None,
        *,
        group: str | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        k_depth: str | int | None = None,
        components: DistributionComponentsSpec | dict | None = None,
        width_method: str | None = None,
        outlier_prop: float | None = None,
        trust_alpha: float | None = None,
        showfliers: bool | None = None,
        showmedians: bool | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Letter-value bands of raw observations, not confidence intervals.

        One column uses group-as-category; x/y use category x/value y and hue.
        Depth defaults to tukey; named depths cap at 32, explicit depths 1..32.
        Widths are exponential/linear/area. Numeric native/log axes are supported.
        stat_scale='axis' opts into log-space summaries; default 'data' stays raw.
        Fliers are raw observations outside outer letter values, not IQR rules.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="boxenplot",
                    x=x,
                    y="" if y is None else y,
                    group=group,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    k_depth=k_depth,
                    components=make_components(components),
                    width_method=width_method,
                    outlier_prop=outlier_prop,
                    trust_alpha=trust_alpha,
                    showfliers=showfliers,
                    showmedians=showmedians,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def box(
        self,
        x: str,
        y: str | None = None,
        *,
        group: str | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        whis: float | list[float] | tuple[float, float] | None = None,
        components: DistributionComponentsSpec | dict | None = None,
        notch: bool | None = None,
        showmeans: bool | None = None,
        showfliers: bool | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """One-column boxes, or category x/value y boxes with group-as-hue.

        Numeric dodge is the total hue span (0 overlays hues); None auto-dodges.
        whis is an IQR multiplier or an ordered percentile pair, not a CI.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="box",
                    x=x,
                    y="" if y is None else y,
                    group=group,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    whis=list(whis) if isinstance(whis, tuple) else whis,
                    components=make_components(components),
                    notch=notch,
                    showmeans=showmeans,
                    showfliers=showfliers,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def violin(
        self,
        x: str,
        y: str | None = None,
        *,
        group: str | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        bw_method: str | float | None = None,
        points: int | None = None,
        weights: str | None = None,
        inner: str | None = "legacy",
        split: bool = False,
        density_norm: str = "width",
        common_norm: bool = False,
        bw_adjust: float | None = None,
        cut: float | None = None,
        clip: list[float | None] | tuple[float | None, float | None] | None = None,
        showmeans: bool | None = None,
        showmedians: bool | None = None,
        showextrema: bool | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """One-column violins, or category x/value y violins with group-as-hue.

        Defaults preserve native median, width normalization and observed range.
        Opt into named inner styles, two-hue split, area/count normalization,
        bandwidth adjustment, bounded support and paired relative weights.
        Weighted quartiles use inverse weighted ECDF; count widths use total mass.
        No replicated rows, callable kernels or inferred confidence intervals.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="violin",
                    weights=weights,
                    x=x,
                    y="" if y is None else y,
                    group=group,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    bw_method=bw_method,
                    points=points,
                    inner=inner,
                    split=split,
                    density_norm=density_norm,
                    common_norm=common_norm,
                    bw_adjust=bw_adjust,
                    cut=cut,
                    clip=list(clip) if isinstance(clip, tuple) else clip,
                    showmeans=showmeans,
                    showmedians=showmedians,
                    showextrema=showextrema,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def ecdf(
        self,
        x: str,
        *,
        stat: str = "proportion",
        complementary: bool = False,
        weights: str | None = None,
        group: str | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Right-continuous empirical cumulative mass of raw column ``x``.

        Proportion/percent normalize within each curve; count sums weights (or
        observations). Complementary mass is strictly greater than each value.
        Ties jump together. Missing/zero-weight rows are excluded. Horizontal
        geometry keeps x as the observation argument. No intervals/censoring.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="ecdf",
                    x=x,
                    ecdf=ECDFSpec(stat, complementary, weights),
                    group=group,
                    hue_order=hue_order,
                    orient=orient,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def kde(
        self,
        x: str,
        *,
        group: str | None = None,
        label: str | None = None,
        weights: str | None = None,
        bw_method: str | float | None = None,
        bw_adjust: float | None = None,
        gridsize: int | None = None,
        cut: float | None = None,
        clip: list[float | None] | tuple[float | None, ...] | None = None,
        common_norm: bool | None = None,
        common_grid: bool | None = None,
        cumulative: bool = False,
        fill: bool = False,
        warn_singular: bool | None = None,
        orient: str = "v",
        hue_order: list[Any] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Gaussian KDE; new options opt into typed weighted fitting/evaluation.

        Legacy calls retain the old 1.06*sample-SD*n**(-1/5),200-point curve.
        Typed bandwidth factors scale unbiased weighted covariance, with Scott/
        Silverman based on effective sample size. Cut/clip bound evaluation, not
        fit rows. Cumulative is the full analytic Gaussian-mixture CDF, not a
        rebased grid integral/ECDF. x remains the observation column in h.
        """
        kernel_options = (
            any(
                value is not None
                for value in (
                    weights,
                    bw_method,
                    bw_adjust,
                    gridsize,
                    cut,
                    clip,
                    common_norm,
                    common_grid,
                    warn_singular,
                )
            )
            or cumulative is not False
            or fill is not False
        )
        if kernel_options and "kde" in style:
            raise ValueError("pass either kde=KDESpec or KDE keyword options, not both")
        extended = (
            kernel_options
            or hue_order is not None
            or orient != "v"
            or "edge_color" in style
        )
        if extended:
            style.setdefault(
                "kde",
                KDESpec(
                    weights=weights,
                    bw_method="scott" if bw_method is None else bw_method,
                    bw_adjust=1.0 if bw_adjust is None else bw_adjust,
                    gridsize=200 if gridsize is None else gridsize,
                    cut=3.0 if cut is None else cut,
                    clip=list(clip) if isinstance(clip, tuple) else clip,
                    common_norm=True if common_norm is None else common_norm,
                    common_grid=False if common_grid is None else common_grid,
                    cumulative=cumulative,
                    fill=fill,
                    warn_singular=True if warn_singular is None else warn_singular,
                ),
            )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="kde",
                    x=x,
                    group=group,
                    label=label,
                    orient=orient,
                    hue_order=hue_order,
                    **style,
                ),
                panel=panel,
            )
        )

    def kde2d(
        self,
        x: str,
        y: str,
        *,
        group: str | None = None,
        label: str | None = None,
        weights: str | None = None,
        bw_method: str | float = "scott",
        bw_adjust: float = 1.0,
        gridsize: int = 80,
        cut: float = 3.0,
        clip: list[list[float | None]] | tuple | None = None,
        common_norm: bool = True,
        common_grid: bool = False,
        levels: list[float] | tuple[float, ...] | None = None,
        fill: bool = False,
        warn_singular: bool = True,
        hue_order: list[Any] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Weighted bivariate Gaussian highest-density contours, not confidence CI.

        Levels are increasing enclosed fractions of trapezoidal mass WITHIN the
        evaluated grid, not absolute density/full-space guarantees. Cut/clip
        never trim fit rows. Scott/Silverman use effective n**(-1/6) in d=2.
        Relative weights, conditional covariance, raw-coordinate densities even
        on log display. Singular groups skip without artificial regularization.
        """
        if "kde2d" in style:
            raise ValueError(
                "kde2d uses explicit keyword options; use AddLayer for config"
            )
        bounds = (
            [
                list(bound) if isinstance(bound, (list, tuple)) else bound
                for bound in clip
            ]
            if isinstance(clip, (list, tuple))
            else clip
        )
        config = KDE2DSpec(
            weights=weights,
            bw_method=bw_method,
            bw_adjust=bw_adjust,
            gridsize=gridsize,
            cut=cut,
            clip=bounds,
            common_norm=common_norm,
            common_grid=common_grid,
            levels=[0.5, 0.8, 0.95]
            if levels is None
            else list(levels)
            if isinstance(levels, (list, tuple))
            else levels,
            fill=fill,
            warn_singular=warn_singular,
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="kde2d",
                    x=x,
                    y=y,
                    group=group,
                    label=label,
                    hue_order=hue_order,
                    kde2d=config,
                    **style,
                ),
                panel=panel,
            )
        )

    def rug(
        self,
        x: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Mark individual observations from column ``x`` along the x-axis."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="rug", x=x, group=group, label=label, **style),
                panel=panel,
            )
        )

    def pie(self, labels: str, values: str, *, panel: int = 0, **style) -> Plot:
        """Pie chart: ``labels`` names the category column, ``values`` the sizes."""
        return self.dispatch(
            A.AddLayer(LayerSpec(type="pie", x=labels, y=values, **style), panel=panel)
        )

    def scatter3d(
        self,
        x: str,
        y: str,
        z: str,
        *,
        group: str | None = None,
        label: str | None = None,
        c: str | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = False,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """3-D scatter plot; the panel must be set to ``projection3d()`` first."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="scatter3d",
                    x=x,
                    y=y,
                    z=z,
                    group=group,
                    label=label,
                    c=c,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def line3d(
        self,
        x: str,
        y: str,
        z: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """3-D line plot; the panel must be set to ``projection3d()`` first."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="line3d", x=x, y=y, z=z, group=group, label=label, **style
                ),
                panel=panel,
            )
        )

    def surface(
        self,
        matrix: str,
        *,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """3-D surface plot of a matrix; the panel must be ``projection3d()``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="surface",
                    matrix=matrix,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def wireframe(self, matrix: str, *, panel: int = 0, **style) -> Plot:
        """3-D wireframe plot of a matrix; the panel must be ``projection3d()``."""
        return self.dispatch(
            A.AddLayer(LayerSpec(type="wireframe", matrix=matrix, **style), panel=panel)
        )

    def projection3d(self, *, panel: int = 0) -> Plot:
        """Switch a panel to a 3-D projection (for scatter3d/line3d/surface/
        wireframe layers)."""
        return self.dispatch(A.SetProjection("3d", panel=panel))

    def projection_polar(self, *, panel: int = 0) -> Plot:
        """Switch a panel to polar coordinates for line/scatter/bar layers."""
        return self.dispatch(A.SetProjection("polar", panel=panel))

    def zlabel(
        self,
        label: str = "",
        *,
        scale: str = "linear",
        limits: list[float] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Configure the z-axis of a ``projection3d()`` panel."""
        return self.dispatch(
            A.SetZAxis(label=label, scale=scale, limits=limits, panel=panel)
        )

    def remove_layer(self, layer_index: int, *, panel: int = 0) -> Plot:
        """Remove the layer at ``layer_index`` from ``panel`` (0-indexed)."""
        return self.dispatch(A.RemoveLayer(layer_index, panel=panel))

    def set_layer_at(
        self, layer_index: int, at: list[float], *, panel: int = 0
    ) -> Plot:
        """Reposition a ``text``/``annotate`` layer's anchor (data coords),
        e.g. after dragging it in the interactive editor."""
        return self.dispatch(A.SetLayerAt(layer_index, at, panel=panel))

    # -- multi-panel --------------------------------------------------------
    def layout(
        self,
        rows: int,
        cols: int,
        *,
        width_ratios: list[float] | None = None,
        height_ratios: list[float] | None = None,
    ) -> Plot:
        return self.dispatch(
            A.SetLayout(
                rows, cols, width_ratios=width_ratios, height_ratios=height_ratios
            )
        )

    def facet(
        self,
        *,
        row: str | None = None,
        col: str | None = None,
        row_order: list | None = None,
        col_order: list | None = None,
        col_wrap: int | None = None,
        share_x: str = "all",
        share_y: str = "all",
    ) -> Plot:
        """Materialize a row/column grid from one completed template panel.

        Cells keep exact selectors over the unchanged source table. Statistics
        are cell-local; semantic mapping domains are shared across selected cells.
        Build layers first; later edits address explicit panel indices. Orders
        reserve empty cells. New levels after SetData require rebuilding the grid.
        """
        return self.dispatch(
            A.SetFacets(
                row=row,
                col=col,
                row_order=row_order,
                col_order=col_order,
                col_wrap=col_wrap,
                share_x=share_x,
                share_y=share_y,
            )
        )

    def joint(
        self,
        *,
        bins: int = 20,
        ratio: float = 3.0,
        marginal_stat: str = "density",
        marginal_kind: str = "hist",
        kde: KDESpec | dict | None = None,
    ) -> Plot:
        """Add hist/KDE/ECDF marginals to scatter/regplot or ungrouped binned data.

        Main panel is top-left, y marginal right, x marginal below. Original
        data remains intact; all views use dynamic complete x/y/group cases.
        """
        from ._joint import grid_kde_config

        config = grid_kde_config(marginal_kind, bins, marginal_stat, kde)
        return self.dispatch(
            A.SetJointGrid(
                bins=bins,
                ratio=ratio,
                marginal_stat=marginal_stat,
                marginal_kind=marginal_kind,
                kde=config,
            )
        )

    def pair(
        self,
        columns: list[str],
        *,
        group: str | None = None,
        hue_order: list | None = None,
        bins: int = 20,
        diag_stat: str = "density",
        diag_kind: str = "hist",
        kde: KDESpec | dict | None = None,
    ) -> Plot:
        """Materialize a numeric scatter matrix with hist/KDE/ECDF diagonals.

        Each cell uses pairwise complete cases; original data stays intact.
        Named value axes share across rows/columns, never with diagonal density.
        """
        from ._joint import grid_kde_config

        config = grid_kde_config(diag_kind, bins, diag_stat, kde)
        return self.dispatch(
            A.SetPairGrid(
                columns=columns,
                group=group,
                hue_order=hue_order,
                bins=bins,
                diag_stat=diag_stat,
                diag_kind=diag_kind,
                kde=config,
            )
        )

    def share_axis(self, axis: str, share_id: str | None, *, panel: int = 0) -> Plot:
        """Link selected primary Cartesian axes by name; figure sharing must be none."""
        return self.dispatch(A.SetAxisShare(axis=axis, share_id=share_id, panel=panel))

    def suptitle(self, text: str) -> Plot:
        return self.dispatch(A.SetSuptitle(text))

    def panel_label(self, label: str | None, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetPanelLabel(label, panel=panel))

    def auto_label(self, enabled: bool = True) -> Plot:
        """Auto-tag multi-panel figures a), b), c)... in the top-left corner."""
        return self.dispatch(A.SetAutoLabel(enabled))

    # -- axes / labels ------------------------------------------------------
    def labels(
        self,
        x: str | None = None,
        y: str | None = None,
        title: str | None = None,
        *,
        panel: int = 0,
    ) -> Plot:
        if x is not None:
            self.dispatch(A.SetAxisLabel("x", x, panel=panel))
        if y is not None:
            self.dispatch(A.SetAxisLabel("y", y, panel=panel))
        if title is not None:
            self.dispatch(A.SetTitle(title, panel=panel))
        return self

    def title_reference(
        self, *, citation: str | None = None, href: str | None = None, panel: int = 0
    ) -> Plot:
        """Attach a BibTeX key and/or URL to the panel title.

        Rendered per output format: plain text in raster output, a clickable
        link in SVG, and real ``\\figcite{key}`` / ``\\href{url}{...}`` macros
        in a ``.pgf`` export, so the paper's own bibliography and hyperref
        resolve them (see :data:`mudplot.PREAMBLE`).
        """
        panel_spec = self.spec.panels[panel] if panel < len(self.spec.panels) else None
        title = panel_spec.title if panel_spec else ""
        return self.dispatch(
            A.SetTitle(title, panel=panel, citation=citation, href=href)
        )

    def title_position(self, position: list[float] | None, *, panel: int = 0) -> Plot:
        """Pin the panel title to an exact ``[x, y]`` axes-fraction spot
        (e.g. after dragging it in the interactive editor). ``None``
        restores matplotlib's default (centred above the axes)."""
        return self.dispatch(A.SetTitlePosition(position, panel=panel))

    def reference_style(self, *, measure_text: str | None = None) -> Plot:
        """Control how PGF export *measures* a citation for layout purposes.

        WYSIWYG layout for a citation is only exact for compact/numeric
        styles (e.g. ``"[12]"``): matplotlib lays out the figure before the
        document's own bibliography resolves ``\\figcite{key}``, so it has
        no way to know the real rendered width of e.g. an author-year
        citation (``"(Fischler and Bolles, 1981)"``) ahead of time. Pass a
        representative example of your citation style to measure against
        that width instead of the compact default; the text itself is never
        emitted to output. ``None`` restores the compact default.
        """
        return self.dispatch(A.SetReferenceMeasureText(measure_text))

    def xscale(self, scale: str, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetScale("x", scale, panel=panel))

    def yscale(self, scale: str, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetScale("y", scale, panel=panel))

    def xlim(
        self, lo: float | None = None, hi: float | None = None, *, panel: int = 0
    ) -> Plot:
        """Set x bounds; omit both values to restore automatic limits."""
        return self.dispatch(A.SetLimits("x", lo, hi, panel=panel))

    def ylim(
        self, lo: float | None = None, hi: float | None = None, *, panel: int = 0
    ) -> Plot:
        """Set y bounds; omit both values to restore automatic limits."""
        return self.dispatch(A.SetLimits("y", lo, hi, panel=panel))

    def legend(
        self,
        show: bool = True,
        *,
        title: str | None = None,
        location: str = "best",
        frame: bool = False,
        panel: int = 0,
        bbox_to_anchor: list[float] | None = None,
    ) -> Plot:
        """``bbox_to_anchor=[x, y]`` (figure-fraction, 0..1) pins the legend
        to an exact spot, overriding ``location`` (e.g. after dragging it in
        the interactive editor). Leave it ``None`` for the usual named
        locations."""
        return self.dispatch(
            A.SetLegend(
                show=show,
                title=title,
                location=location,
                frame=frame,
                panel=panel,
                bbox_to_anchor=bbox_to_anchor,
            )
        )

    # -- theme / palette ----------------------------------------------------
    def theme(self, name: str) -> Plot:
        """Apply a named theme preset.

        Order matters: this *replaces* the whole theme (font, axes, grid,
        ticks, palette) with the preset's defaults, so any earlier
        ``.palette(...)``/``.font(...)``/etc. customisation is discarded.
        Call ``.theme(...)`` first, then layer other style calls on top.
        """
        return self.dispatch(A.SetTheme(name))

    def journal(self, name) -> Plot:
        """Apply a journal preset (fonts + conventional figure size).

        ``name`` can be a string (e.g. ``"nature"``, ``"ieee"``, ``"acm"``,
        ``"revtex"``) or a :class:`~mudplot.JournalProfile`.

        Sets the conventional size; later ``.size()``/``.tex_size()`` wins for
        geometry. While active, the journal's registered rc font/linewidth keys
        override theme fields regardless of action order. Use ``.journal(None)``
        to clear that style override without changing the current size; explicit
        per-field font values then apply.
        """
        jname = getattr(name, "name", name)
        return self.dispatch(A.SetJournal(jname))

    def palette(self, kind: str | None = None, **params) -> Plot:
        return self.dispatch(A.SetPalette(kind=kind, params=params))

    def font(self, **params) -> Plot:
        return self.dispatch(A.SetFont(params=params))

    def axes_style(self, **params) -> Plot:
        """e.g. ``.axes_style(spine_offset=6, spines="LB")`` ("despine" look)."""
        return self.dispatch(A.SetAxesStyle(params=params))

    def grid_style(self, **params) -> Plot:
        return self.dispatch(A.SetGridStyle(params=params))

    def ticks_style(self, **params) -> Plot:
        return self.dispatch(A.SetTicksStyle(params=params))

    def encoding(self, **params) -> Plot:
        """e.g. ``.encoding(redundant_encoding=True)`` to cycle marker/line-style
        per series in addition to colour (helps greyscale print & CVD viewers).
        """
        return self.dispatch(A.SetEncoding(params=params))

    def share(self, x: str | None = None, y: str | None = None) -> Plot:
        """Share axes across panels: "none" | "all" | "row" | "col"."""
        return self.dispatch(A.SetShare(x=x, y=y))

    def secondary_yaxis(
        self,
        label: str | None = "",
        *,
        scale: str = "linear",
        limits: list[float] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Configure y2; pass ``None`` as the label to remove it."""
        return self.dispatch(
            A.SetSecondaryAxis(label=label, scale=scale, limits=limits, panel=panel)
        )

    def size(self, width: float, height: float) -> Plot:
        return self.dispatch(A.SetSize(width, height))

    def tex_size(
        self,
        preset,
        *,
        columns: int = 1,
        fraction: float = 1.0,
        aspect: float = 0.618,
        font_scale: float = 0.9,
    ) -> Plot:
        """Size (and font-match) the figure for a TeX document column layout.

        ``preset`` is a name from ``mp.TEX_PRESETS`` (e.g. ``"ieee"``,
        ``"nature"``) or a ``TexContext``. ``columns=1`` sizes to a single
        column's width; ``columns=2`` spans the full text width (for a
        double-column-spanning ``figure*`` in a two-column document, or a
        wide figure in a single-column one). This is the same sizing
        ``preview(tex=...)`` uses, but applied to the actual figure you
        render/save -- not just a mock-column preview. An active journal still
        has its registered rc style priority; clear it for custom TeX font fields.
        """
        from .tex import _resolve_ctx, _tex_actions

        if columns not in (1, 2):
            raise ValueError(f"columns must be 1 or 2, got {columns!r}")
        ctx = _resolve_ctx(preset)
        actions = _tex_actions(
            ctx,
            fraction=fraction,
            aspect=aspect,
            full_width=(columns == 2),
            font_scale=font_scale,
        )
        self._store.dispatch_all(actions)
        return self

    # -- materialise (effects) ---------------------------------------------
    def render(self):
        from ._render import render

        return render(self.spec)

    def save(self, path: str, *, tight: bool = False):
        """Save at the configured size; ``tight=True`` crops to content instead."""
        from ._render import save

        return save(self.spec, path, tight=tight)

    def preview(self, tex: str | None = None, **kw):
        """Preview the plot; if ``tex`` names a TeX context, use WYSIWYG sizing."""
        from .tex import tex_preview

        return tex_preview(self.spec, tex, **kw)

    def lint(self, *, journal: str | JournalProfile | None = None, **kw):
        """Publication-preflight checks (see ``mudplot.lint_figure``):
        page-width fit for a named ``journal``, minimum text size, palette
        CVD/greyscale safety, redundant encoding, legend size, and
        reference-metadata validity. Returns a ``LintReport`` of
        ok/warning/error findings -- print it, or check ``report.ok``.
        """
        from ._lint import lint_figure

        return lint_figure(self.spec, journal=journal, **kw)

    def to_json(self, **kw) -> str:
        from .io import to_json

        return to_json(self.spec, **kw)

    @classmethod
    def from_json(cls, text: str) -> Plot:
        from .io import from_json

        obj = cls.__new__(cls)
        obj._store = Store(from_json(text))
        return obj


def plot(data: Any = None, *, query: str | None = None, params: Any = ()) -> Plot:
    """Start a new fluent plot.

    ``data`` may be a dict of columns, list of records/rows, pandas/polars
    DataFrame, numpy (structured or 2-D) array, pyarrow Table, an executed
    DB-API cursor, or a DB-API connection together with parameterized
    ``query=`` and ``params=``.
    """
    return Plot(data, query=query, params=params)


def apply(actions, spec: FigureSpec | None = None) -> FigureSpec:
    """Reduce a list of JSON/dict (or Action) actions into a FigureSpec.

    The primary agent entry point: an agent emits actions as JSON and gets back
    a fully-formed spec (pure, no side effects). Render with ``mp.save`` /
    ``mp.render``.
    """
    parsed = [a if not isinstance(a, dict) else A.action_from_dict(a) for a in actions]
    return reduce_all(spec if spec is not None else FigureSpec(), parsed)


def color_palette(
    n: int, kind: str = "qualitative", *, preset: str | None = None, **params
) -> Palette:
    """Generate a palette (thin wrapper over :mod:`mudplot.color.palette`).

    ``preset`` (``qualitative`` only) selects a named, pre-verified parameter
    set (see ``mudplot.capabilities()["palette_presets"]``); it overrides
    ``lightness``/``chroma``/``hue_start``/``lightness_jitter`` in ``params``.
    """
    from .color import palette as _palette

    if kind == "qualitative":
        if preset is not None:
            return _palette.preset_qualitative(preset, n, **params)
        return _palette.qualitative(n, **params)
    if preset is not None:
        raise ValueError(
            f"preset is only supported for kind='qualitative', got {kind!r}"
        )
    if kind == "sequential":
        return _palette.sequential(n, **params)
    if kind == "diverging":
        return _palette.diverging(n, **params)
    raise ValueError(f"unknown palette kind: {kind!r}")
