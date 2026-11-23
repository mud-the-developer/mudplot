"""Draw validated supplied/rebinned windows with native Matplotlib step patches."""

from collections.abc import Sequence
from typing import Protocol, cast

from matplotlib.patches import StepPatch

from ._stairs import plan_stairs


class _OpenStepPatch(Protocol):
    def __call__(
        self,
        values: Sequence[float],
        edges: Sequence[float],
        *,
        baseline: None,
        fill: bool,
        edgecolor: str,
        **style: str | float | None,
    ) -> StepPatch: ...


def draw_stairs(ax, columns, layer, panel, row_ids, color_iter):
    from ._render import _decorate

    config, baseline, groups = plan_stairs(columns, layer, panel, row_ids)
    style = layer.line_style or "-"
    if not layer.line_width and layer.line_width is not None:
        style = "-"
    needs_autoscale = False
    for group, windows in groups:
        color = layer.color or next(color_iter)
        label = _decorate(layer.label, layer.citation, layer.href)
        if group is not None:
            label = _decorate(str(group), layer.citation, layer.href)
        for window in windows:
            options = {
                "linewidth": layer.line_width,
                "linestyle": style,
                "alpha": layer.alpha,
                "label": label,
            }
            if config.open:
                patch = cast(_OpenStepPatch, StepPatch)(
                    window.heights,
                    window.edges,
                    baseline=None,
                    fill=False,
                    edgecolor=color,
                    **options,
                )
                ax.add_patch(patch)
                needs_autoscale = True
            else:
                ax.stairs(
                    window.heights,
                    window.edges,
                    baseline=baseline,
                    fill=config.fill,
                    color=color,
                    **options,
                )
            label = "_nolegend_"
    if needs_autoscale:
        ax.autoscale_view()
