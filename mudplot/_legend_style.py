"""Finite native legend styles on existing artist handles only."""

HANDLERS = ("line-pair", "scatter-pair")


def legend_style_issues(config):
    issues = []
    if config.ncols is not None and (
        type(config.ncols) is not int or not 1 <= config.ncols <= 8
    ):
        issues.append("legend ncols must be an integer within 1..8")
    if config.handler is not None and config.handler not in HANDLERS:
        issues.append("legend handler must be line-pair or scatter-pair")
    return issues


def legend_handlers(handles, config, existing=None):
    """Opt in per real matching handle; preserve other native/custom owners."""
    handlers = {} if existing is None else existing
    if config.handler is None:
        return handlers
    from matplotlib.collections import PathCollection
    from matplotlib.legend_handler import HandlerLine2D, HandlerPathCollection
    from matplotlib.lines import Line2D

    if config.handler == "line-pair":
        artist_type, handler = Line2D, HandlerLine2D(numpoints=2)
    else:
        # Native y-offset defaults follow legend.scatterpoints (one); supply
        # two offsets so the provider retains both authored handler positions.
        artist_type, handler = (
            PathCollection,
            HandlerPathCollection(numpoints=2, yoffsets=[0.375, 0.375]),
        )
    return {
        **handlers,
        **{artist: handler for artist in handles if isinstance(artist, artist_type)},
    }
