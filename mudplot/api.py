"""High-level, intuitive user API.

The fluent builder is *sugar over actions*: each method dispatches an action to
a :class:`~mudplot.store.Store`, which runs the pure reducer. There is no hidden
mutable state — only the spec inside the store. This is the exact same update
path a future Rust/htmx editor would drive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from . import actions as A
from ._components import make_components
from ._stat import make_stat
from ._transforms import decode_transforms
from .reducer import reduce_all
from .spec import (
    AnnotationSpec,
    AxisTransformSpec,
    BarGeometrySpec,
    BivariateBinsSpec,
    BoxenBandComponentsSpec,
    BoxenHueComponentsSpec,
    BoxenSpec,
    BoxHueComponentsSpec,
    BoxMedianCISpec,
    BoxSummarySpec,
    Camera3DSpec,
    ClusterSpec,
    ComponentStyleSpec,
    DistributionComponentsSpec,
    ECDF2DSpec,
    ECDFSpec,
    ErrorMagnitudesSpec,
    FigureSpec,
    FillSpec,
    GridFieldSpec,
    HDRSpec,
    HeatmapSpec,
    Histogram2DSpec,
    HistogramSpec,
    KDE2DSpec,
    KDESpec,
    LayerSpec,
    LineSpec,
    LiteralTableSpec,
    PanelLayoutSpec,
    PanelPlacementSpec,
    PanelSpec,
    PatchSpec,
    PathEffectSpec,
    PieGeometrySpec,
    RegressionSpec,
    ScalarDisplaySpec,
    ScaleOptionsSpec,
    SecondaryAxisSpec,
    SegmentSpec,
    SemanticSpec,
    SharedGuideSpec,
    SpanSpec,
    SpatialSpec,
    SpectrumSpec,
    StairsSpec,
    StripSpec,
    TemporalSpec,
    TickSpec,
    TransformSpec,
    TriangulationSpec,
    VectorSpec,
    ViolinSpec,
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
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        line: LineSpec | dict | None = None,
        orient: str = "v",
        axis: str = "y",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Draw supplied source-order rows, duplicates and missing-path gaps.

        Independent roles map raw curves, never estimates. Size is stroke
        points; style owns real markers and declared dashes. LineSpec may
        declare categorical predictor slots, but never raw-line inference.
        """
        mapped = any(value is not None for value in (hue, size, style))
        if semantics is not None and mapped:
            raise ValueError("pass either semantics or hue/size/style keywords")
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else SemanticSpec(hue=hue, size=size, style=style)
            if mapped
            else None
        )
        declared = (
            LineSpec.from_dict(line.to_dict() if isinstance(line, LineSpec) else line)
            if line is not None
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="line",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    group=group,
                    label=label,
                    semantics=config,
                    line=declared,
                    orient=orient,
                    axis=axis,
                    order=order,
                    hue_order=hue_order,
                    **appearance,
                ),
                panel=panel,
            )
        )

    def stem(
        self,
        x: str,
        y: str,
        *,
        baseline: float | None = 0.0,
        orient: str = "v",
        group: str | None = None,
        hue_order: list[Any] | None = None,
        semantics: SemanticSpec | dict | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw supplied location/value rows as stems, without aggregation."""
        if isinstance(semantics, dict):
            semantics = SemanticSpec.from_dict(semantics)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stem",
                    x=x,
                    y=y,
                    baseline=baseline,
                    orient=orient,
                    group=group,
                    hue_order=hue_order,
                    semantics=semantics,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def stairs(
        self,
        values: str,
        edges: list[float] | list[int] | list[str] | list[float | str],
        *,
        baseline: float | None = 0.0,
        stairs: StairsSpec | dict | None = None,
        group: str | None = None,
        hue_order: list[Any] | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw supplied bin heights, or explicitly rebin a declared measure."""
        if isinstance(stairs, dict):
            stairs = StairsSpec.from_dict(stairs)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stairs",
                    x=values,
                    bins=edges,
                    baseline=baseline,
                    stairs=stairs,
                    group=group,
                    hue_order=hue_order,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def eventplot(
        self,
        x: str,
        *,
        offset: float = 0.0,
        length: float = 1.0,
        group: str | None = None,
        hue_order: list[Any] | None = None,
        lane_step: float | None = None,
        semantics: SemanticSpec | dict | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw disconnected raw-coordinate event ticks in optional group lanes."""
        if isinstance(semantics, dict):
            semantics = SemanticSpec.from_dict(semantics)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="eventplot",
                    x=x,
                    baseline=offset,
                    width=length,
                    group=group,
                    hue_order=hue_order,
                    lane_step=lane_step,
                    semantics=semantics,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def broken_barh(
        self,
        starts: str,
        durations: str,
        *,
        bottom: float = 0.0,
        height: float = 1.0,
        group: str | None = None,
        hue_order: list[Any] | None = None,
        lane_step: float | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw ordered start/duration intervals in optional raw-coordinate lanes."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="broken_barh",
                    x=starts,
                    y=durations,
                    baseline=bottom,
                    width=height,
                    group=group,
                    hue_order=hue_order,
                    lane_step=lane_step,
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
        semantics: SemanticSpec | dict | None = None,
        weights: str | None = None,
        degree: int = 1,
        confidence: float | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Fit original observations with independently owned native components.

        ``confidence`` is the sole optional coverage percentage. Legacy
        unweighted poly/logx normal bands are retained. Explicit
        ``regression.bootstrap`` selects uniform paired physical-case percentile
        inference, including weighted/advanced fits and full residual trends.
        Weights remain relative criterion masses, never sampling probabilities.
        Partial references and disjoint train/query selectors are persisted in
        ``regression``; no fitted values replace the source columns.
        """
        from ._regression import prepare_regression, weighted_option_issues

        config = prepare_regression(regression)
        if isinstance(semantics, dict):
            semantics = SemanticSpec.from_dict(semantics)
        if config is None and (
            semantics is not None or weights is not None or style.get("orient") == "h"
        ):
            config = RegressionSpec()
        problems = weighted_option_issues(config, confidence, weights)
        if problems:
            raise ValueError("; ".join(problems))
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="regplot",
                    regression=config,
                    semantics=semantics,
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
        scalar_display: ScalarDisplaySpec | dict | None = None,
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
                    scalar_display=self._scalar_display(scalar_display),
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
        semantics: SemanticSpec | dict | None = None,
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
            semantics=semantics,
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
        strip: StripSpec | dict | None = None,
        semantics: SemanticSpec | dict | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        dodge: float | None = None,
        native_scale: bool = False,
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Raw strips; opt-in category geometry has local named seeded jitter.

        Omitted controls preserve legacy raw-x jitter exactly. StripSpec,
        semantics or explicit order/orientation/native/dodge opts into slots.
        Jitter is then a half-width fraction of minimum axis category spacing;
        dodged hues instead use dodge * spacing / all reserved hue slots.
        """
        config = (
            StripSpec.from_dict(
                strip.to_dict() if isinstance(strip, StripSpec) else strip
            )
            if strip is not None
            else None
        )
        semantic_config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="stripplot",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    jitter=jitter,
                    group=group,
                    strip=cast(StripSpec | None, config),
                    semantics=cast(SemanticSpec | None, semantic_config),
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    dodge=dodge,
                    native_scale=native_scale,
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
        semantics: SemanticSpec | dict | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        warn_thresh: float | None = None,
        pack_scope: str | None = None,
        axis: str = "y",
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Pack native named glyphs from original measurements on every draw.

        x stays categorical in v/h; numeric/log/date and y2 use actual axis roles.
        Shared semantics map hue, nominal diameter points and named marker style.
        pack_scope explicitly joins compatible physical instances in one panel;
        omission leaves layers independent. Crowding retains rows with warnings.
        Facet live=True enables explicit whole-template transactions, not auto-load.
        """
        config = None
        if semantics is not None:
            data = (
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            config = SemanticSpec.from_dict(data)
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="swarmplot",
                    x=x,
                    y=y,
                    group=group,
                    semantics=config,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    warn_thresh=warn_thresh,
                    pack_scope=pack_scope,
                    axis=axis,
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
        bins: int | list | BivariateBinsSpec | dict = 20,
        density: bool = False,
        stat: str | None = None,
        weights: str | None = None,
        common_norm: bool | None = None,
        kde: KDE2DSpec | dict | None = None,
        histogram2d: Histogram2DSpec | dict | None = None,
        group: str | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        axis: str = "y",
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Paired bins with explicit in-bin mass statistics and optional full-fit KDE.

        No new options retain the old native histogram/spec. BivariateBinsSpec
        chooses logical x/y bins without reinterpreting an old flat list.
        A KDE overlay fits the same paired cohort BEFORE bin-range exclusions;
        its density/CDF is not rescaled into histogram count heights.
        """
        if isinstance(bins, (BivariateBinsSpec, dict)):
            bins = BivariateBinsSpec.from_dict(
                bins.to_dict() if isinstance(bins, BivariateBinsSpec) else bins
            )
        roles = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        config = (
            Histogram2DSpec.from_dict(
                histogram2d.to_dict()
                if isinstance(histogram2d, Histogram2DSpec)
                else histogram2d
            )
            if histogram2d is not None
            else None
        )
        if config is not None and (
            density
            or any(value is not None for value in (stat, weights, common_norm, kde))
        ):
            raise ValueError(
                "use Histogram2DSpec or histogram statistic options, not both"
            )
        if stat is not None and density:
            raise ValueError("use explicit stat or legacy density=True, not both")
        if config is None and (
            isinstance(bins, BivariateBinsSpec)
            or any(
                value is not None
                for value in (stat, weights, common_norm, kde, group, roles, hue_order)
            )
        ):
            overlay = (
                KDE2DSpec.from_dict(
                    kde.to_dict() if isinstance(kde, KDE2DSpec) else kde
                )
                if kde is not None
                else None
            )
            config = Histogram2DSpec(
                stat=("density" if density else "count") if stat is None else stat,
                weights=weights,
                common_norm=True if common_norm is None else common_norm,
                kde=overlay,
            )
            density = False
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hist2d",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    bins=bins,
                    density=density,
                    histogram2d=config,
                    group=group,
                    semantics=roles,
                    hue_order=hue_order,
                    orient=orient,
                    axis=axis,
                    label=label,
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
        vector: VectorSpec | dict | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw a 2-D vector field from position and component columns."""
        if isinstance(vector, dict):
            vector = VectorSpec.from_dict(vector)
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
                    vector=vector,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def _vector_layer(self, kind, vector, panel, **fields) -> Plot:
        if isinstance(vector, dict):
            vector = VectorSpec.from_dict(vector)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type=kind, vector=vector, **fields),
                panel=panel,
            )
        )

    def barbs(
        self,
        x: str,
        y: str,
        u: str,
        v: str,
        *,
        vector: VectorSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw native barbs in the declared raw component units."""
        return self._vector_layer("barbs", vector, panel, x=x, y=y, u=u, v=v, **style)

    def streamplot(self, *, vector: VectorSpec | dict, panel: int = 0, **style) -> Plot:
        """Draw native streamlines from two explicitly gridded component matrices."""
        return self._vector_layer("streamplot", vector, panel, **style)

    def quiver3d(
        self,
        x: str,
        y: str,
        z: str,
        u: str,
        v: str,
        w: str,
        *,
        vector: VectorSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw native three-component vectors on a Cartesian 3D panel."""
        return self._vector_layer(
            "quiver3d",
            vector,
            panel,
            x=x,
            y=y,
            z=z,
            u=u,
            v=v,
            w=w,
            **style,
        )

    def heatmap(
        self,
        matrix: str,
        *,
        heatmap: HeatmapSpec | dict | None = None,
        scalar_display: ScalarDisplaySpec | dict | None = None,
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
                    scalar_display=self._scalar_display(scalar_display),
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
        """Register a named matrix without changing observation columns.

        Null cells require an opt-in grid consumer or clustermap missing policy.
        """
        return self.dispatch(A.SetMatrix(name, [list(row) for row in values]))

    @staticmethod
    def _scalar_display(config):
        if isinstance(config, dict):
            return ScalarDisplaySpec.from_dict(config)
        return config

    def _grid_layer(
        self, kind, matrix, grid, panel, *, scalar_display=None, **style
    ) -> Plot:
        if isinstance(grid, dict):
            grid = GridFieldSpec.from_dict(grid)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type=kind,
                    matrix=matrix,
                    grid=grid,
                    scalar_display=self._scalar_display(scalar_display),
                    **style,
                ),
                panel=panel,
            )
        )

    def imshow(
        self,
        matrix: str | None = None,
        *,
        grid: GridFieldSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw a scalar matrix or explicit RGB(A) pixels."""
        return self._grid_layer("imshow", matrix, grid, panel, **style)

    def pcolor(
        self, matrix: str, *, grid: GridFieldSpec | dict, panel: int = 0, **style
    ) -> Plot:
        """Draw scalar cell polygons on a rectilinear grid."""
        return self._grid_layer("pcolor", matrix, grid, panel, **style)

    def pcolormesh(
        self, matrix: str, *, grid: GridFieldSpec | dict, panel: int = 0, **style
    ) -> Plot:
        """Draw a scalar quadrilateral mesh on a rectilinear grid."""
        return self._grid_layer("pcolormesh", matrix, grid, panel, **style)

    def spy(
        self, matrix: str, *, grid: GridFieldSpec | dict, panel: int = 0, **style
    ) -> Plot:
        """Mark visible dense matrix entries above a magnitude threshold."""
        return self._grid_layer("spy", matrix, grid, panel, **style)

    def contour(
        self,
        matrix: str,
        *,
        levels: int | list[float] | None = None,
        grid: GridFieldSpec | dict | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Contour lines of a 2-D matrix registered with ``.matrix(name, values)``."""
        return self._grid_layer(
            "contour",
            matrix,
            grid,
            panel,
            levels=levels,
            cmap_kind=cmap_kind,
            colorbar=colorbar,
            clabel=clabel,
            **style,
        )

    def contourf(
        self,
        matrix: str,
        *,
        levels: int | list[float] | None = None,
        grid: GridFieldSpec | dict | None = None,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Filled contours of a 2-D matrix registered with ``.matrix(name, values)``."""
        return self._grid_layer(
            "contourf",
            matrix,
            grid,
            panel,
            levels=levels,
            cmap_kind=cmap_kind,
            colorbar=colorbar,
            clabel=clabel,
            **style,
        )

    def _triangle_layer(self, kind, x, y, triangulation, panel, **style) -> Plot:
        if isinstance(triangulation, dict):
            triangulation = TriangulationSpec.from_dict(triangulation)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type=kind, x=x, y=y, triangulation=triangulation, **style),
                panel=panel,
            )
        )

    def triplot(
        self,
        x: str,
        y: str,
        *,
        triangulation: TriangulationSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw the native edges of visible explicit triangles."""
        return self._triangle_layer("triplot", x, y, triangulation, panel, **style)

    def tripcolor(
        self,
        x: str,
        y: str,
        *,
        triangulation: TriangulationSpec | dict,
        c: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Colour explicit triangles by declared face values or vertex averages."""
        return self._triangle_layer(
            "tripcolor", x, y, triangulation, panel, c=c, **style
        )

    def tricontour(
        self,
        x: str,
        y: str,
        c: str,
        *,
        triangulation: TriangulationSpec | dict,
        levels: list[float],
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw native isolines on explicit triangles with vertex scalars."""
        return self._triangle_layer(
            "tricontour", x, y, triangulation, panel, c=c, levels=levels, **style
        )

    def tricontourf(
        self,
        x: str,
        y: str,
        c: str,
        *,
        triangulation: TriangulationSpec | dict,
        levels: list[float],
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw native filled intervals on explicit triangles with vertex scalars."""
        return self._triangle_layer(
            "tricontourf", x, y, triangulation, panel, c=c, levels=levels, **style
        )

    def trisurf(
        self,
        x: str,
        y: str,
        z: str,
        *,
        triangulation: TriangulationSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw a native 3D surface with explicit XY triangles and vertex Z."""
        return self._triangle_layer("trisurf", x, y, triangulation, panel, z=z, **style)

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
        geometry: BarGeometrySpec | dict | None = None,
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
        if isinstance(geometry, dict):
            geometry = BarGeometrySpec.from_dict(geometry)
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
                    bar_geometry=geometry,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def barh(
        self,
        positions: str,
        values: str,
        *,
        geometry: BarGeometrySpec | dict | None = None,
        bar_width: float | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw supplied horizontal widths, with the baseline at left."""
        if isinstance(geometry, dict):
            geometry = BarGeometrySpec.from_dict(geometry)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="barh",
                    x=positions,
                    y=values,
                    bar_geometry=geometry,
                    bar_width=bar_width,
                    group=group,
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
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        orient: str = "v",
        axis: str = "y",
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Estimate raw observations per category/hue; do not pre-average data.

        Named estimators and SD/SE/PI/seeded percentile-bootstrap CI are
        explicit statistical settings. Existing ``bar()`` remains a
        primitive for already summarized values. Weighted means use paired-row
        bootstrap CI; units opt into two-stage (unit then within-unit) resampling.
        Missing/zero-weight rows are excluded. Callables are not stored in specs.
        """
        mapped = any(value is not None for value in (hue, size, style))
        if semantics is not None and mapped:
            raise ValueError("pass either semantics or hue/size/style keywords")
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else SemanticSpec(hue=hue, size=size, style=style)
            if mapped
            else None
        )
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="barplot",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    group=group,
                    semantics=config,
                    orient=orient,
                    axis=axis,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    baseline=baseline,
                    label=label,
                    stat=make_stat(
                        estimator, errorbar, n_boot, seed, weights=weights, units=units
                    ),
                    **appearance,
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
        axis: str = "y",
        stat_scale: str = "data",
        hue_order: list[Any] | None = None,
        error_style: str | None = None,
        error_alpha: float | None = None,
        label: str | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        line: LineSpec | dict | None = None,
        order: list[Any] | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Estimate per predictor/curve with explicit cell or whole-unit CI.

        Omitted LineSpec retains cell bootstrap. Unit resampling keeps complete
        original trajectories; max_deviation calibrates a finite-grid curve/
        layer family independently of ribbon/bars geometry. New unit min/max
        intervals are empirical envelopes, not population confidence.
        Raw supplied observations belong to .line(), never this estimator.
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
        declared = (
            LineSpec.from_dict(line.to_dict() if isinstance(line, LineSpec) else line)
            if line is not None
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="lineplot",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    group=group,
                    semantics=config,
                    orient=orient,
                    axis=axis,
                    line=declared,
                    order=order,
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
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        orient: str = "v",
        axis: str = "y",
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **appearance,
    ) -> Plot:
        """Raw-data estimates and intervals with optional connecting lines.

        ``dodge`` is a total category span for hue offsets (default zero).
        Use ``line_style="none"`` to omit connecting lines. Missing category
        cells break the line rather than bridging unobserved categories.
        """
        mapped = any(value is not None for value in (hue, size, style))
        if semantics is not None and mapped:
            raise ValueError("pass either semantics or hue/size/style keywords")
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else SemanticSpec(hue=hue, size=size, style=style)
            if mapped
            else None
        )
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="pointplot",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    group=group,
                    semantics=config,
                    orient=orient,
                    axis=axis,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    label=label,
                    dodge=dodge,
                    stat=make_stat(
                        estimator, errorbar, n_boot, seed, weights=weights, units=units
                    ),
                    **appearance,
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
        weights: str | None = None,
        normalize_scope: str | None = None,
        native_scale: bool = False,
        baseline: float | None = None,
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        semantics: SemanticSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Count observations or weight mass with an explicit denominator scope.

        ``stat``: count, probability/proportion, percent. ``weights`` names a
        finite nonnegative weight column. ``normalize_scope`` is all (default),
        category (within each category), or group (within each hue), per panel.
        No y column or inferred count interval is required.
        """
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="countplot",
                    semantics=SemanticSpec.from_dict(semantics)
                    if isinstance(semantics, dict)
                    else semantics,
                    transforms=decode_transforms(transforms),
                    x=x,
                    group=group,
                    native_scale=native_scale,
                    baseline=baseline,
                    label=label,
                    stat=make_stat(
                        "count",
                        None,
                        1000,
                        0,
                        normalize=stat,
                        weights=weights,
                        normalize_scope=normalize_scope,
                    ),
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
        magnitudes: ErrorMagnitudesSpec | dict | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Points with symmetric errors or absolute y interval endpoints.

        Use ``yerr`` OR paired ``y_lower``/``y_upper`` columns; intervals
        are supplied by the caller, never inferred from SD or sample size.
        """
        if isinstance(magnitudes, dict):
            magnitudes = ErrorMagnitudesSpec.from_dict(magnitudes)
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
                    error_magnitudes=magnitudes,
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
        orient: str = "v",
        fill: FillSpec | dict | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Shaded band (fill_between) from ``lower`` to ``upper`` columns."""
        if isinstance(fill, dict):
            fill = FillSpec.from_dict(fill)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="band",
                    x=x,
                    y=upper,
                    y2=lower,
                    orient=orient,
                    fill=fill,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def hlines(
        self,
        segments: SegmentSpec,
        *,
        axis: str = "y",
        label: str | None = None,
        native_style: ComponentStyleSpec | None = None,
        path_effects: list[PathEffectSpec] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Draw finite y-fixed series from native x start to x end."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hlines",
                    segments=segments,
                    axis=axis,
                    label=label,
                    native_style=native_style,
                    path_effects=path_effects,
                ),
                panel=panel,
            )
        )

    def vlines(
        self,
        segments: SegmentSpec,
        *,
        axis: str = "y",
        label: str | None = None,
        native_style: ComponentStyleSpec | None = None,
        path_effects: list[PathEffectSpec] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Draw finite x-fixed series from native y start to y end."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="vlines",
                    segments=segments,
                    axis=axis,
                    label=label,
                    native_style=native_style,
                    path_effects=path_effects,
                ),
                panel=panel,
            )
        )

    def hspan(
        self,
        span: SpanSpec,
        *,
        axis: str = "y",
        label: str | None = None,
        native_style: ComponentStyleSpec | None = None,
        path_effects: list[PathEffectSpec] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Shade a native y interval across an explicit fraction of the x axis."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hspan",
                    span=span,
                    axis=axis,
                    label=label,
                    native_style=native_style,
                    path_effects=path_effects,
                ),
                panel=panel,
            )
        )

    def vspan(
        self,
        span: SpanSpec,
        *,
        axis: str = "y",
        label: str | None = None,
        native_style: ComponentStyleSpec | None = None,
        path_effects: list[PathEffectSpec] | None = None,
        panel: int = 0,
    ) -> Plot:
        """Shade a native x interval across an explicit fraction of the y axis."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="vspan",
                    span=span,
                    axis=axis,
                    label=label,
                    native_style=native_style,
                    path_effects=path_effects,
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

    def patch(
        self,
        patch: PatchSpec,
        *,
        native_style: ComponentStyleSpec | None = None,
        path_effects: list[PathEffectSpec] | None = None,
        label: str | None = None,
        axis: str = "y",
        panel: int = 0,
    ) -> Plot:
        """Draw a bounded literal patch in its declared coordinate frame."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="patch",
                    patch=patch,
                    native_style=native_style,
                    label=label,
                    path_effects=path_effects,
                    axis=axis,
                ),
                panel=panel,
            )
        )

    def table(self, table: LiteralTableSpec, *, panel: int = 0) -> Plot:
        """Draw literal typed cells within a declared axes rectangle."""
        return self.dispatch(
            A.AddLayer(LayerSpec(type="table", table=table), panel=panel)
        )

    def text(
        self,
        text: str,
        at: list[float],
        *,
        annotation: AnnotationSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        if isinstance(annotation, dict):
            annotation = AnnotationSpec.from_dict(annotation)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="text", text=text, at=list(at), annotation=annotation, **style
                ),
                panel=panel,
            )
        )

    def annotate(
        self,
        text: str,
        at: list[float],
        *,
        to: list | None = None,
        annotation: AnnotationSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        if isinstance(annotation, dict):
            annotation = AnnotationSpec.from_dict(annotation)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="annotate",
                    text=text,
                    at=list(at),
                    to=list(to) if to else None,
                    annotation=annotation,
                    **style,
                ),
                panel=panel,
            )
        )

    def hist(
        self,
        x: str,
        *,
        bins: int | str | list = 20,
        discrete: bool | None = None,
        density: bool = False,
        stat: str | None = None,
        weights: str | None = None,
        common_norm: bool | None = None,
        cumulative: bool = False,
        multiple: str | None = None,
        element: str | None = None,
        fill: bool | None = None,
        group: str | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        semantics: SemanticSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Opt-in shared-bin weighted statistics, retaining legacy calls unchanged.

        Named bins and explicit statistics/geometry/style create HistogramSpec.
        Bins="discrete" is an integer-centered input-unit grid; discrete=True
        aliases it only with the default bin argument. Named rules are fixed v2
        definitions on usable observations, not weight magnitudes. Both preserve
        original row weights for statistics and reject unsafe derived edges.
        Density uses original raw bin widths; normalized
        mass includes only in-range rows. Cumulative density integrates mass.
        Grouped stack/dodge keep heights. Multiple='fill' normalizes existing
        per-bin heights after stat/common_norm/cumulative; cumulative fill is
        composition, not a CDF. Poly connects raw-bin centers (at least 2 bins).
        Fill=None retains filled bars/unfilled step/poly; bool overrides it.
        Without new options, density/group/bin behavior remains Matplotlib's.
        """
        if discrete is not None and type(discrete) is not bool:
            raise TypeError("histogram discrete must be boolean or None")
        if discrete:
            if type(bins) is not int or bins != 20:
                raise ValueError("discrete=True cannot combine with custom bins")
            bins = "discrete"
        elif discrete is False and isinstance(bins, str) and bins == "discrete":
            raise ValueError("discrete=False conflicts with bins=discrete")
        advanced = (
            isinstance(bins, str)
            or stat is not None
            or weights is not None
            or common_norm is not None
            or cumulative is not False
            or multiple is not None
            or element is not None
            or fill is not None
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
                fill=fill,
            )
            if advanced
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hist",
                    semantics=SemanticSpec.from_dict(semantics)
                    if isinstance(semantics, dict)
                    else semantics,
                    transforms=decode_transforms(transforms),
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
        weights: str | None = None,
        boxen: BoxenSpec | dict | None = None,
        band_components: list[BoxenBandComponentsSpec | dict] | None = None,
        hue_components: list[BoxenHueComponentsSpec | dict] | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue: str | None = None,
        size: str | None = None,
        style: str | None = None,
        axis: str = "y",
        label: str | None = None,
        panel: int = 0,
        **artist_style,
    ) -> Plot:
        """Letter-value bands, not confidence intervals or replicated weights.

        Unweighted quantiles are type7; explicit relative weights use LEFT
        inverse ECDF, physical-row Kish stopping and empirical interval masses.
        Typed band rank/side and exact raw-hue components inherit fieldwise.
        Semantic hue owns body colour, size outline stroke points, style body
        dash and actual observed flier glyphs. Clock/native/log/y2 views retain
        original source rows; explicit advanced work is bounded before drawing.
        """
        from dataclasses import replace

        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else SemanticSpec()
            if any(value is not None for value in (hue, size, style))
            else None
        )
        if config is not None:
            if not isinstance(config, SemanticSpec):
                raise TypeError("semantics must decode to SemanticSpec")
            for role, name in (("hue", hue), ("size", size), ("style", style)):
                if name is not None:
                    if getattr(config, role) is not None:
                        raise ValueError(f"{role} is already declared in semantics")
                    config = replace(config, **{role: name})
        options = (
            BoxenSpec.from_dict(
                boxen.to_dict() if isinstance(boxen, BoxenSpec) else boxen
            )
            if boxen is not None
            else BoxenSpec()
            if band_components is not None or hue_components is not None
            else None
        )
        if options is not None:
            if not isinstance(options, BoxenSpec):
                raise TypeError("boxen must decode to BoxenSpec")
            updates = {}
            for name, entries, model in (
                ("band_components", band_components, BoxenBandComponentsSpec),
                ("hue_components", hue_components, BoxenHueComponentsSpec),
            ):
                if entries is not None:
                    if getattr(options, name) is not None:
                        raise ValueError(f"{name} is already declared in boxen")
                    updates[name] = [
                        model.from_dict(
                            entry.to_dict() if isinstance(entry, model) else entry
                        )
                        for entry in entries
                    ]
            options = replace(options, **updates)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="boxenplot",
                    boxen=options,
                    weights=weights,
                    semantics=config,
                    axis=axis,
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
                    **artist_style,
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
        median_ci: BoxMedianCISpec | dict | None = None,
        cap_fraction: float | None = None,
        hue_components: list[BoxHueComponentsSpec | dict] | None = None,
        semantics: SemanticSpec | dict | None = None,
        axis: str = "y",
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
        from ._box import make_box

        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
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
                    box=make_box(
                        median_ci=median_ci,
                        cap_fraction=cap_fraction,
                        hue_components=hue_components,
                    ),
                    semantics=config,
                    axis=axis,
                    notch=notch,
                    showmeans=showmeans,
                    showfliers=showfliers,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def bxp(
        self,
        x: str,
        median: str | None = None,
        *,
        q1: str,
        q3: str,
        whislo: str,
        whishi: str,
        mean: str | None = None,
        cilo: str | None = None,
        cihi: str | None = None,
        fliers: str | None = None,
        group: str | None = None,
        orient: str = "v",
        order: list[Any] | None = None,
        hue_order: list[Any] | None = None,
        width: float | None = None,
        dodge: float | None = None,
        gap: float | None = None,
        native_scale: bool = False,
        stat_scale: str = "data",
        components: DistributionComponentsSpec | dict | None = None,
        cap_fraction: float | None = None,
        hue_components: list[BoxHueComponentsSpec | dict] | None = None,
        semantics: SemanticSpec | dict | None = None,
        notch: bool | None = None,
        showmeans: bool | None = None,
        showfliers: bool | None = None,
        axis: str = "y",
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Render supplied absolute summaries from existing data columns.

        ``bxp(category, median, ...)`` mirrors two-column ``box``.
        ``bxp(median, group=category, ...)`` mirrors its one-column form.
        Optional means/CI/fliers are unavailable unless explicitly supplied;
        a missing optional mark never silently discards an otherwise valid box.
        Fliers reference a column of finite absolute-value lists, not raw samples.
        """
        from ._box import make_box

        summary = BoxSummarySpec(
            q1=q1,
            q3=q3,
            whislo=whislo,
            whishi=whishi,
            mean=mean,
            cilo=cilo,
            cihi=cihi,
            fliers=fliers,
        )
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="box",
                    x=x,
                    y="" if median is None else median,
                    group=group,
                    orient=orient,
                    order=order,
                    hue_order=hue_order,
                    width=width,
                    dodge=dodge,
                    gap=gap,
                    native_scale=native_scale,
                    stat_scale=stat_scale,
                    components=make_components(components),
                    box=make_box(
                        summary=summary,
                        cap_fraction=cap_fraction,
                        hue_components=hue_components,
                    ),
                    semantics=config,
                    axis=axis,
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
        clip: list[float | str | None]
        | tuple[float | str | None, float | str | None]
        | None = None,
        violin: ViolinSpec | dict | None = None,
        components: DistributionComponentsSpec | dict | None = None,
        semantics: SemanticSpec | dict | None = None,
        axis: str = "y",
        showmeans: bool | None = None,
        showmedians: bool | None = None,
        showextrema: bool | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """One-column violins, or category x/value y violins with group-as-hue.

        Defaults preserve native median, width normalization and observed range.
        Opt into named inners, explicit paired multi-hue halves, typed per-hue
        components and independent shared roles. Size is body-outline stroke pt;
        style maps body dashes and only actual point/box-median glyphs.
        Weighted quartiles use inverse ECDF; count widths use relative mass.
        No replicated rows, callable kernels or inferred confidence intervals.
        """
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        options = (
            ViolinSpec.from_dict(
                violin.to_dict() if isinstance(violin, ViolinSpec) else violin
            )
            if violin is not None
            else None
        )
        if config is not None and not isinstance(config, SemanticSpec):
            raise TypeError("semantics must decode to SemanticSpec")
        if options is not None and not isinstance(options, ViolinSpec):
            raise TypeError("violin must decode to ViolinSpec")
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="violin",
                    violin=options,
                    components=make_components(components),
                    semantics=config,
                    axis=axis,
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
        semantics: SemanticSpec | dict | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Right-continuous empirical cumulative mass of raw column ``x``.

        Proportion/percent normalize within each curve; count sums weights (or
        observations). Complementary mass is strictly greater than each value.
        Ties jump together. Missing/zero-weight rows are excluded. Horizontal
        geometry keeps x as the observation argument. No intervals/censoring.
        """
        config = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="ecdf",
                    transforms=decode_transforms(transforms),
                    x=x,
                    ecdf=ECDFSpec(stat, complementary, weights),
                    group=group,
                    semantics=cast(SemanticSpec | None, config),
                    hue_order=hue_order,
                    orient=orient,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def ecdf2d(
        self,
        x: str,
        y: str,
        *,
        bounds: list | tuple,
        stat: str = "proportion",
        complementary: bool = False,
        weights: str | None = None,
        query_x: list | tuple | None = None,
        query_y: list | tuple | None = None,
        group: str | None = None,
        semantics: SemanticSpec | dict | None = None,
        hue_order: list | None = None,
        orient: str = "v",
        axis: str = "y",
        colorbar: bool = True,
        cmap_kind: str = "sequential",
        clabel: str | None = None,
        label: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Paired closed lower-orthant empirical mass on explicit finite bounds.

        The strict complement is X>qx OR Y>qy, not joint survival. Bounds and
        query grids never discard observations from the denominator. All source
        jumps inside the frame are retained as right-continuous native cells.
        """
        roles = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        frame = (
            [
                list(bound) if isinstance(bound, (list, tuple)) else bound
                for bound in bounds
            ]
            if isinstance(bounds, (list, tuple))
            else bounds
        )
        config = ECDF2DSpec(
            bounds=frame,
            stat=stat,
            complementary=complementary,
            weights=weights,
            query_x=list(query_x) if isinstance(query_x, tuple) else query_x,
            query_y=list(query_y) if isinstance(query_y, tuple) else query_y,
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="ecdf2d",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    ecdf2d=config,
                    group=group,
                    semantics=roles,
                    hue_order=hue_order,
                    orient=orient,
                    axis=axis,
                    colorbar=colorbar,
                    cmap_kind=cmap_kind,
                    clabel=clabel,
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
        kde: KDESpec | dict | None = None,
        semantics: SemanticSpec | dict | None = None,
        kernel: str | None = None,
        multiple: str | None = None,
        density_space: str | None = None,
        group: str | None = None,
        label: str | None = None,
        weights: str | None = None,
        bw_method: str | float | None = None,
        bw_adjust: float | None = None,
        gridsize: int | None = None,
        cut: float | None = None,
        clip: list[float | str | None] | tuple[float | str | None, ...] | None = None,
        common_norm: bool | None = None,
        common_grid: bool | None = None,
        cumulative: bool = False,
        fill: bool = False,
        warn_singular: bool | None = None,
        orient: str = "v",
        axis: str = "y",
        hue_order: list[Any] | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Source-preserving KDE with named kernels and explicit shared-grid modes.

        Omitted calls retain the legacy Gaussian fit. Typed Scott/Silverman and
        scalar factors scale physical-row reliability covariance. Cut/clip only
        restrict evaluation. Cumulative-fill is composition of CDF contributions,
        not a CDF; x remains the observation argument for either orientation.
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
                    kernel,
                    multiple,
                    density_space,
                )
            )
            or cumulative is not False
            or fill is not False
        )
        if kernel_options and kde is not None:
            raise ValueError("pass either kde=KDESpec or KDE keyword options, not both")
        config = (
            KDESpec.from_dict(kde.to_dict() if isinstance(kde, KDESpec) else kde)
            if kde is not None
            else None
        )
        roles = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        extended = (
            kernel_options
            or hue_order is not None
            or orient != "v"
            or "edge_color" in style
            or roles is not None
        )
        if extended and config is None:
            config = KDESpec(
                weights=weights,
                bw_method="scott" if bw_method is None else bw_method,
                bw_adjust=1.0 if bw_adjust is None else bw_adjust,
                gridsize=200 if gridsize is None else gridsize,
                cut=3.0 if cut is None else cut,
                clip=list(clip) if isinstance(clip, tuple) else clip,
                common_norm=True if common_norm is None else common_norm,
                common_grid=multiple in ("stack", "fill")
                if common_grid is None
                else common_grid,
                cumulative=cumulative,
                fill=fill,
                warn_singular=True if warn_singular is None else warn_singular,
                kernel=kernel,
                multiple=multiple,
                density_space=density_space,
            )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="kde",
                    transforms=decode_transforms(transforms),
                    x=x,
                    group=group,
                    label=label,
                    orient=orient,
                    hue_order=hue_order,
                    axis=axis,
                    kde=config,
                    semantics=roles,
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
        clip: list[list[float | str | None]] | tuple | None = None,
        common_norm: bool = True,
        common_grid: bool = False,
        levels: list[float] | tuple[float, ...] | None = None,
        fill: bool = False,
        warn_singular: bool = True,
        hue_order: list[Any] | None = None,
        semantics: SemanticSpec | dict | None = None,
        kernel: str | None = None,
        cumulative: bool | None = None,
        level_kind: str | None = None,
        fit_scales: list[str] | tuple[str, ...] | None = None,
        density_space: str | None = None,
        hdr: HDRSpec | dict | None = None,
        orient: str = "v",
        axis: str = "y",
        colorbar: bool = False,
        cmap_kind: str = "sequential",
        clabel: str | None = None,
        transforms: list[TransformSpec | dict] | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Paired named-kernel density, true joint CDF, or explicit full-model HDR.

        Omitted calls keep conditional finite-grid Gaussian contours. Mass levels
        are enclosed probabilities; density/cdf levels are actual field heights.
        Log fitting and raw-density Jacobian space are explicit. Full HDR reports
        requested/achieved conditional error, never a rebased visible-grid claim.
        """
        if "kde2d" in style:
            raise ValueError(
                "kde2d uses explicit keyword options; use AddLayer for config"
            )
        roles = (
            SemanticSpec.from_dict(
                semantics.to_dict()
                if isinstance(semantics, SemanticSpec)
                else semantics
            )
            if semantics is not None
            else None
        )
        full = (
            HDRSpec.from_dict(hdr.to_dict() if isinstance(hdr, HDRSpec) else hdr)
            if hdr is not None
            else None
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
            kernel=kernel,
            cumulative=cumulative,
            level_kind=level_kind,
            fit_scales=list(fit_scales)
            if isinstance(fit_scales, tuple)
            else fit_scales,
            density_space=density_space,
            hdr=full,
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="kde2d",
                    transforms=decode_transforms(transforms),
                    x=x,
                    y=y,
                    group=group,
                    label=label,
                    hue_order=hue_order,
                    kde2d=config,
                    semantics=roles,
                    orient=orient,
                    axis=axis,
                    colorbar=colorbar,
                    cmap_kind=cmap_kind,
                    clabel=clabel,
                    **style,
                ),
                panel=panel,
            )
        )

    def spectrum(
        self,
        x: str,
        y: str | None = None,
        *,
        fs: float,
        kind: str = "psd",
        nfft: int | None = None,
        pad_to: int | None = None,
        overlap: int = 0,
        window: str = "hann",
        detrend: str = "none",
        sides: str = "onesided",
        scaling: str = "density",
        scale: str = "linear",
        panel: int = 0,
        **style,
    ) -> Plot:
        """Derive a named spectrum without changing uniformly sampled source rows."""
        config = SpectrumSpec(
            fs=fs,
            kind=kind,
            nfft=nfft,
            pad_to=pad_to,
            overlap=overlap,
            window=window,
            detrend=detrend,
            sides=sides,
            scaling=scaling,
            scale=scale,
        )
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="spectrum", x=x, y=y or "", spectrum=config, **style),
                panel=panel,
            )
        )

    def rug(
        self,
        x: str,
        *,
        orient: str = "v",
        height: float | None = None,
        semantics: SemanticSpec | dict | None = None,
        axis: str = "y",
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Mark ``x`` observations on x (v) or target y (h), inside the axes.

        ``height`` is an axes fraction [0,1] (None keeps 0.04), stored as
        LayerSpec.width. Semantic size maps stroke points, style maps dashes.
        Only the observation axis supplies temporal units.
        """
        if isinstance(semantics, dict):
            semantics = cast(SemanticSpec, SemanticSpec.from_dict(semantics))
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="rug",
                    x=x,
                    group=group,
                    label=label,
                    orient=orient,
                    width=height,
                    semantics=semantics,
                    axis=axis,
                    **style,
                ),
                panel=panel,
            )
        )

    def pie(
        self,
        labels: str,
        values: str,
        *,
        geometry: PieGeometrySpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Pie chart: ``labels`` names the category column, ``values`` the sizes."""
        if isinstance(geometry, dict):
            geometry = PieGeometrySpec.from_dict(geometry)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="pie", x=labels, y=values, pie_geometry=geometry, **style
                ),
                panel=panel,
            )
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
        spatial: SpatialSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """3-D surface plot of a matrix; the panel must be ``projection3d()``."""
        if isinstance(spatial, dict):
            spatial = SpatialSpec.from_dict(spatial)
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="surface",
                    matrix=matrix,
                    cmap_kind=cmap_kind,
                    colorbar=colorbar,
                    clabel=clabel,
                    spatial=spatial,
                    **style,
                ),
                panel=panel,
            )
        )

    def wireframe(
        self,
        matrix: str,
        *,
        spatial: SpatialSpec | dict | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw grid lines using either unit indices or declared XY coordinates."""
        return self._spatial_layer("wireframe", spatial, panel, matrix=matrix, **style)

    def _spatial_layer(self, kind, spatial, panel, **fields) -> Plot:
        if isinstance(spatial, dict):
            spatial = SpatialSpec.from_dict(spatial)
        return self.dispatch(
            A.AddLayer(LayerSpec(type=kind, spatial=spatial, **fields), panel=panel)
        )

    def bar3d(
        self,
        x: str,
        y: str,
        z: str,
        *,
        spatial: SpatialSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw aligned raw anchors and signed height/positive footprint deltas."""
        return self._spatial_layer("bar3d", spatial, panel, x=x, y=y, z=z, **style)

    def contour3d(
        self,
        matrix: str,
        *,
        levels: list[float],
        spatial: SpatialSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Draw explicit native contour lines at Z levels or on a declared plane."""
        return self._spatial_layer(
            "contour3d", spatial, panel, matrix=matrix, levels=levels, **style
        )

    def contourf3d(
        self,
        matrix: str,
        *,
        levels: list[float],
        spatial: SpatialSpec | dict,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Project native filled bands to an explicit plane in a 3D panel."""
        return self._spatial_layer(
            "contourf3d", spatial, panel, matrix=matrix, levels=levels, **style
        )

    def voxels(self, *, spatial: SpatialSpec | dict, panel: int = 0, **style) -> Plot:
        """Draw strict [z][y][x] boolean occupancy on unit or declared edges."""
        return self._spatial_layer("voxels", spatial, panel, **style)

    def camera3d(self, camera: Camera3DSpec | dict | None, *, panel: int = 0) -> Plot:
        """Set or clear an existing 3D panel's camera without changing its limits."""
        if isinstance(camera, dict):
            camera = Camera3DSpec.from_dict(camera)
        return self.dispatch(A.SetCamera3D(camera, panel=panel))

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

    def panel_layout(
        self,
        layout: PanelLayoutSpec | dict,
        placements: dict[str, PanelPlacementSpec | dict],
        *,
        panel_ids: list[str] | None = None,
    ) -> Plot:
        """Replace complete final-ID geometry; explicitly new keys add empty panels."""
        if isinstance(layout, dict):
            layout = cast(PanelLayoutSpec, PanelLayoutSpec.from_dict(layout))
        places = {
            name: cast(PanelPlacementSpec, PanelPlacementSpec.from_dict(value))
            if isinstance(value, dict)
            else value
            for name, value in placements.items()
        }
        return self.dispatch(A.SetPanelLayout(layout, places, panel_ids))

    def mosaic(
        self,
        rows: list[list[str | None]],
        *,
        width_ratios: list[float] | None = None,
        height_ratios: list[float] | None = None,
    ) -> Plot:
        """Place named rectangular panel spans; null cells remain unoccupied."""
        return self.dispatch(A.SetMosaic(rows, width_ratios, height_ratios))

    def nest(
        self,
        rows: int,
        cols: int,
        *,
        row: int = 0,
        col: int = 0,
        row_span: int = 1,
        col_span: int = 1,
        grid_id: str | None = None,
        width_ratios: list[float] | None = None,
        height_ratios: list[float] | None = None,
    ) -> Plot:
        """Wrap the current grid, including pair/joint views, in a new outer grid."""
        return self.dispatch(
            A.NestLayout(
                rows,
                cols,
                row,
                col,
                row_span,
                col_span,
                grid_id,
                width_ratios,
                height_ratios,
            )
        )

    def place(self, panel_id: str, placement: PanelPlacementSpec | dict) -> Plot:
        """Move one identified panel without changing its content or index."""
        if isinstance(placement, dict):
            placement = cast(
                PanelPlacementSpec, PanelPlacementSpec.from_dict(placement)
            )
        return self.dispatch(A.SetPanelPlacement(panel_id, placement))

    def inset(
        self, parent: str, bounds: list[float], *, panel_id: str | None = None
    ) -> Plot:
        """Append an empty real panel in parent-axes fractional coordinates."""
        return self.dispatch(A.AddInset(parent, bounds, panel_id))

    def rename_panel(self, panel_id: str, new_id: str) -> Plot:
        """Rename an ID and all inset-parent references atomically."""
        return self.dispatch(A.RenamePanel(panel_id, new_id))

    def reorder_panels(self, panel_ids: list[str]) -> Plot:
        """Reorder indices by an exact ID permutation, preserving placement."""
        return self.dispatch(A.ReorderPanels(panel_ids))

    def remove_panel(self, panel_id: str) -> Plot:
        """Remove a leaf panel; parents and the final panel cannot be removed."""
        return self.dispatch(A.RemovePanel(panel_id))

    def relplot(self, x: str, y: str, *, kind: str = "scatter", **options) -> Plot:
        """Build a supplied scatter/line or an estimated line in fixed facets."""
        from ._facet_builders import build_facet

        return build_facet(self, "relplot", x, y, kind=kind, **options)

    def displot(
        self, x: str, y: str | None = None, *, kind: str = "hist", **options
    ) -> Plot:
        """Build a named histogram, KDE, ECDF or rug in fixed facets."""
        from ._facet_builders import build_facet

        return build_facet(self, "displot", x, y, kind=kind, **options)

    def catplot(
        self, x: str, y: str | None = None, *, kind: str = "strip", **options
    ) -> Plot:
        """Build one registered categorical mark or estimator in fixed facets."""
        from ._facet_builders import build_facet

        return build_facet(self, "catplot", x, y, kind=kind, **options)

    def lmplot(self, x: str, y: str, *, kind: str = "regplot", **options) -> Plot:
        """Build the existing regression or residual effect in fixed facets."""
        from ._facet_builders import build_facet

        return build_facet(self, "lmplot", x, y, kind=kind, **options)

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
        live: bool = False,
    ) -> Plot:
        """Materialize fixed cells, optionally retaining an explicit live recipe.

        With ``live=True``, :meth:`facet_template` replaces every intended cell.
        Ordinary panel edits remain local. Loading JSON/SetData never applies
        the stored template automatically or introduces new facet cells.
        """
        if type(live) is not bool:
            raise TypeError("live must be bool")
        action = A.SetLiveFacets if live else A.SetFacets
        return self.dispatch(
            action(
                row=row,
                col=col,
                row_order=row_order,
                col_order=col_order,
                col_wrap=col_wrap,
                share_x=share_x,
                share_y=share_y,
            )
        )

    def facet_template(
        self, template: PanelSpec | dict, *, reset_orders: bool = False
    ) -> Plot:
        """Explicitly replace all live cells, superseding local cell overrides.

        Omitted category/hue orders retain captured slots. Provide explicit orders
        or request reset_orders=True to resolve new slots from current data.
        Existing figure ratios/sharing and fixed selectors remain unchanged.
        """
        if isinstance(template, dict):
            template = cast(PanelSpec, PanelSpec.from_dict(template))
        if not isinstance(template, PanelSpec):
            raise TypeError("template must be PanelSpec or a panel dictionary")
        return self.dispatch(A.SetFacetTemplate(template, reset_orders))

    def joint(
        self,
        *,
        bins: int = 20,
        ratio: float = 3.0,
        marginal_stat: str = "density",
        marginal_kind: str = "hist",
        kde: KDESpec | dict | None = None,
        weights: str | None = None,
        complementary: bool | None = None,
        group: str | None = None,
        hue_order: list[str | bool | int | float] | None = None,
    ) -> Plot:
        """Add hist/KDE/ECDF marginals to a completed Cartesian center.

        Top-left is the center, right is y, and below is x. All use a common
        complete physical-row cohort. ``group``/``hue_order`` are for native
        hexbin; an optional named ``weights`` column is shared by all owners.
        """
        from ._joint import grid_kde_config

        config = grid_kde_config(marginal_kind, bins, marginal_stat, kde, weighted=True)
        return self.dispatch(
            A.SetJointGrid(
                bins=bins,
                ratio=ratio,
                marginal_stat=marginal_stat,
                marginal_kind=marginal_kind,
                kde=config,
                weights=weights,
                complementary=complementary,
                group=group,
                hue_order=hue_order,
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
        temporal: dict[str, TemporalSpec | dict] | None = None,
        corner: bool | None = None,
        weights: str | None = None,
        complementary: bool | None = None,
        semantics: SemanticSpec | dict | None = None,
    ) -> Plot:
        """Materialize numeric/explicit-temporal scatter and univariate diagonals.

        Each cell uses pairwise complete cases; original data stays intact.
        Named value axes share across rows/columns, never with diagonal density.
        """
        from ._joint import grid_kde_config
        from ._pair import temporal_configs

        config = grid_kde_config(diag_kind, bins, diag_stat, kde, weighted=True)
        if isinstance(semantics, dict):
            semantics = SemanticSpec.from_dict(semantics)
        clocks = temporal_configs(temporal, columns)
        return self.dispatch(
            A.SetPairGrid(
                columns=columns,
                group=group,
                hue_order=hue_order,
                bins=bins,
                diag_stat=diag_stat,
                diag_kind=diag_kind,
                kde=config,
                temporal=clocks,
                corner=corner,
                weights=weights,
                complementary=complementary,
                semantics=semantics,
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

    def date_axis(
        self,
        axis: str,
        *,
        timezone: str | None = None,
        unit: str | None = None,
        origin: str | None = None,
        panel: int = 0,
    ) -> Plot:
        """Declare ISO or explicit unit/origin numeric time on a linear axis.

        Bounds use UTC days since 1970. Naive input needs an explicit fixed zone.
        """
        return self.dispatch(
            A.SetTemporalAxis(
                axis,
                TemporalSpec(timezone=timezone, unit=unit, origin=origin),
                panel=panel,
            )
        )

    def axis_scale(
        self,
        axis: str,
        scale: str,
        *,
        options: ScaleOptionsSpec | dict | None = None,
        panel: int = 0,
    ) -> Plot:
        """Atomically replace the scale and its finite parameters; None clears."""
        if isinstance(options, dict):
            options = cast(ScaleOptionsSpec, ScaleOptionsSpec.from_dict(options))
        return self.dispatch(A.SetAxisScale(axis, scale, options, panel=panel))

    def xscale(
        self,
        scale: str,
        *,
        panel: int = 0,
        options: ScaleOptionsSpec | dict | None = None,
    ) -> Plot:
        if options is not None:
            return self.axis_scale("x", scale, options=options, panel=panel)
        return self.dispatch(A.SetScale("x", scale, panel=panel))

    def yscale(
        self,
        scale: str,
        *,
        panel: int = 0,
        options: ScaleOptionsSpec | dict | None = None,
    ) -> Plot:
        if options is not None:
            return self.axis_scale("y", scale, options=options, panel=panel)
        return self.dispatch(A.SetScale("y", scale, panel=panel))

    def ticks(
        self,
        axis: str,
        spec: TickSpec | dict | None,
        *,
        which: str = "major",
        panel: int = 0,
    ) -> Plot:
        """Set or clear one complete major/minor configuration, in axis units."""
        if isinstance(spec, dict):
            spec = cast(TickSpec, TickSpec.from_dict(spec))
        return self.dispatch(A.SetAxisTicks(axis, which, spec, panel=panel))

    def secondary_axis(
        self,
        axis: str,
        transform: AxisTransformSpec | dict | None,
        *,
        label: str | None = None,
        major_ticks: TickSpec | dict | None = None,
        minor_ticks: TickSpec | dict | None = None,
        panel: int = 0,
    ) -> Plot:
        """Derived top/right coordinates; never creates independent y2 data."""
        if transform is None:
            return self.dispatch(A.SetDerivedAxis(axis, None, panel=panel))
        if isinstance(transform, dict):
            transform = cast(AxisTransformSpec, AxisTransformSpec.from_dict(transform))
        if isinstance(major_ticks, dict):
            major_ticks = cast(TickSpec, TickSpec.from_dict(major_ticks))
        if isinstance(minor_ticks, dict):
            minor_ticks = cast(TickSpec, TickSpec.from_dict(minor_ticks))
        config = SecondaryAxisSpec(transform, label, major_ticks, minor_ticks)
        return self.dispatch(A.SetDerivedAxis(axis, config, panel=panel))

    def secondary_xaxis(
        self,
        transform: AxisTransformSpec | dict | None,
        *,
        label: str | None = None,
        major_ticks: TickSpec | dict | None = None,
        minor_ticks: TickSpec | dict | None = None,
        panel: int = 0,
    ) -> Plot:
        return self.secondary_axis(
            "x",
            transform,
            label=label,
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            panel=panel,
        )

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
        ncols: int | None = None,
        handler: str | None = None,
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
                ncols=ncols,
                handler=handler,
            )
        )

    def shared_guides(self, guides: list[SharedGuideSpec | dict] | None) -> Plot:
        """Replace figure-owned named-scope requests through the pure reducer.

        SemanticSpec.scale_id alone defines membership. None clears requests;
        an explicit empty list round-trips without consolidation.
        """
        if guides is not None and not isinstance(guides, list):
            raise TypeError("shared_guides requires a list or None")
        declared = (
            [
                SharedGuideSpec.from_dict(
                    item.to_dict() if isinstance(item, SharedGuideSpec) else item
                )
                for item in guides
            ]
            if guides is not None
            else None
        )
        return self.dispatch(A.SetSharedGuides(declared))

    # -- theme / palette ----------------------------------------------------
    def theme(self, name: str) -> Plot:
        """Apply a named theme preset.

        Order matters: this *replaces* the whole theme (font, axes, grid,
        ticks, palette) with the preset's defaults, so any earlier
        ``.palette(...)``/``.font(...)``/etc. customisation is discarded.
        Call ``.theme(...)`` first, then layer other style calls on top.
        """
        return self.dispatch(A.SetTheme(name))

    def context(self, name: str | None) -> Plot:
        """Change the render-local typography context without replacing the theme."""
        return self.dispatch(A.SetContext(name))

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
    def render(self, *, layout_policy: str | None = None):
        """Render unchanged by default; opt into ``smart`` or ``smart-print``."""
        from ._render import render

        return render(self.spec, layout_policy=layout_policy)

    def save(self, path: str, *, tight: bool = False, layout_policy: str | None = None):
        """Save at the configured size; ``tight=True`` crops to content instead."""
        from ._render import save

        return save(self.spec, path, tight=tight, layout_policy=layout_policy)

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


def relplot(data, x: str, y: str, **options) -> Plot:
    """Create a relational facet figure from one source table."""
    return plot(data).relplot(x, y, **options)


def displot(data, x: str, y: str | None = None, **options) -> Plot:
    """Create a distribution facet figure from one source table."""
    return plot(data).displot(x, y, **options)


def catplot(data, x: str, y: str | None = None, **options) -> Plot:
    """Create a categorical facet figure from one source table."""
    return plot(data).catplot(x, y, **options)


def lmplot(data, x: str, y: str, **options) -> Plot:
    """Create a regression facet figure from one source table."""
    return plot(data).lmplot(x, y, **options)


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
