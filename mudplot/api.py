"""High-level, intuitive user API.

The fluent builder is *sugar over actions*: each method dispatches an action to
a :class:`~mudplot.store.Store`, which runs the pure reducer. There is no hidden
mutable state — only the spec inside the store. This is the exact same update
path a future Rust/htmx editor would drive.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import actions as A
from .reducer import reduce_all
from .spec import FigureSpec, LayerSpec
from .store import Store

if TYPE_CHECKING:
    from .color.palette import Palette

__all__ = ["Plot", "apply", "color_palette", "plot"]


from .data import to_columns as _columns_from


class Plot:
    """Fluent builder that dispatches actions to an internal store.

    ``self.spec`` always reflects the current (pure-reduced) state.
    Call :meth:`render`, :meth:`save`, or :meth:`to_json` to materialise.
    """

    def __init__(self, data: Any = None, *, query: str | None = None):
        self._store = Store(FigureSpec())
        if data is not None or query is not None:
            self._store.dispatch(A.SetData(_columns_from(data, query=query)))

    @property
    def spec(self) -> FigureSpec:
        return self._store.state

    @property
    def store(self) -> Store:
        return self._store

    def dispatch(self, action: A.Action) -> Plot:
        self._store.dispatch(action)
        return self

    # -- agent-facing: JSON actions ----------------------------------------
    def apply(self, actions) -> Plot:
        """Apply a list of JSON/dict (or Action) actions in order."""
        for a in actions:
            self._store.dispatch(
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
        panel: int = 0,
        **style,
    ) -> Plot:
        """Scatter plot. Pass ``c`` (a column name) to colour points by a
        continuous value instead of ``group`` (categorical); set
        ``colorbar=True`` to draw the colour scale."""
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
                    **style,
                ),
                panel=panel,
            )
        )

    def heatmap(
        self,
        matrix: str,
        *,
        cmap_kind: str = "sequential",
        colorbar: bool = True,
        clabel: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Heatmap of a 2-D matrix previously added with ``.matrix(name, values)``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="heatmap",
                    matrix=matrix,
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
        self, x: str, y: str, *, label: str | None = None, panel: int = 0, **style
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="bar", x=x, y=y, label=label, **style), panel=panel
            )
        )

    def errorbar(
        self,
        x: str,
        y: str,
        *,
        yerr: str | None = None,
        xerr: str | None = None,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="errorbar",
                    x=x,
                    y=y,
                    yerr=yerr,
                    xerr=xerr,
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
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        return self.dispatch(
            A.AddLayer(
                LayerSpec(
                    type="hist",
                    x=x,
                    bins=bins,
                    density=density,
                    group=group,
                    label=label,
                    **style,
                ),
                panel=panel,
            )
        )

    def box(
        self,
        x: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Boxplot of column ``x``, optionally split into boxes by ``group``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="box", x=x, group=group, label=label, **style),
                panel=panel,
            )
        )

    def violin(
        self,
        x: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Violin plot of column ``x``, optionally split by ``group``."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="violin", x=x, group=group, label=label, **style),
                panel=panel,
            )
        )

    def kde(
        self,
        x: str,
        *,
        group: str | None = None,
        label: str | None = None,
        panel: int = 0,
        **style,
    ) -> Plot:
        """Kernel-density-estimate curve of column ``x`` (numpy-only Gaussian KDE)."""
        return self.dispatch(
            A.AddLayer(
                LayerSpec(type="kde", x=x, group=group, label=label, **style),
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

    def xscale(self, scale: str, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetScale("x", scale, panel=panel))

    def yscale(self, scale: str, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetScale("y", scale, panel=panel))

    def xlim(self, lo: float, hi: float, *, panel: int = 0) -> Plot:
        return self.dispatch(A.SetLimits("x", lo, hi, panel=panel))

    def ylim(self, lo: float, hi: float, *, panel: int = 0) -> Plot:
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

    def journal(self, name: str | None) -> Plot:
        """Apply a journal preset (fonts + conventional figure size).

        Like ``.theme(...)``, this sets values outright rather than merging;
        call it before other size/font customisation if you want your own
        values to stick.
        """
        return self.dispatch(A.SetJournal(name))

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
        label: str = "",
        *,
        scale: str = "linear",
        limits: list[float] | None = None,
        panel: int = 0,
    ) -> Plot:
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
        render/save -- not just a mock-column preview.
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

    def to_json(self, **kw) -> str:
        from .io import to_json

        return to_json(self.spec, **kw)

    @classmethod
    def from_json(cls, text: str) -> Plot:
        from .io import from_json

        obj = cls.__new__(cls)
        obj._store = Store(from_json(text))
        return obj


def plot(data: Any = None, *, query: str | None = None) -> Plot:
    """Start a new fluent plot.

    ``data`` may be a dict of columns, list of records/rows, pandas/polars
    DataFrame, numpy (structured or 2-D) array, pyarrow Table, an executed
    DB-API cursor, or a DB-API connection together with ``query=``.
    """
    return Plot(data, query=query)


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
