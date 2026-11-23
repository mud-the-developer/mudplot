"""Row membership and displayed axis roles for raw stem observations."""

from ._semantics import MAX_ROWS, categorical, category_key
from ._stat import is_missing
from .spec import SemanticSpec


def stem_axes(layer, panel):
    target = panel.y2 if layer.axis == "y2" else panel.y
    return (target, panel.x) if layer.orient == "h" else (panel.x, target)


def stem_has_fixed_order(layer):
    config = layer.semantics
    return layer.hue_order is not None or (
        isinstance(config, SemanticSpec)
        and any(
            getattr(config, f"{role}_order") is not None
            for role in ("hue", "size", "style")
        )
    )


def stem_rows(columns, layer, *, candidates=None):
    """Select original row indices before clock parsing or domain checks."""
    from ._facet import _ordered

    count = len(next(iter(columns.values()), ()))
    candidates = range(count) if candidates is None else candidates
    filters = []
    if layer.hue_order is not None:
        if not isinstance(layer.group, str) or layer.group not in columns:
            raise ValueError("stem hue_order requires an existing group column")
        filters.append((columns[layer.group], _ordered((), layer.hue_order), True))
    config = layer.semantics
    if isinstance(config, SemanticSpec):
        for role in ("hue", "size", "style"):
            name = getattr(config, role)
            order = getattr(config, f"{role}_order")
            if (
                isinstance(name, str)
                and name in columns
                and isinstance(order, (list, tuple))
                and all(categorical(v) for v in order)
            ):
                filters.append((columns[name], order, False))
    selectors = [
        (values, {category_key(v) for v in order}, group)
        for values, order, group in filters
    ]
    rows = []
    for i in candidates:
        if any(
            (
                category_key(values[i]) not in keys
                if categorical(values[i])
                else group and is_missing(values[i])
            )
            for values, keys, group in selectors
        ):
            continue
        if len(rows) == MAX_ROWS:
            raise ValueError(f"stem exceeds {MAX_ROWS} selected rows")
        rows.append(i)
    return rows


def stem_group_levels(columns, layer, rows):
    from ._facet import _ordered

    if layer.group is None:
        return []
    if not isinstance(layer.group, str) or layer.group not in columns:
        raise ValueError("stem group must name an existing column")
    groups = columns[layer.group]
    if any(not categorical(groups[i]) for i in rows):
        raise ValueError(
            "stem groups require nonempty strings, booleans or finite numbers"
        )
    return _ordered((groups[i] for i in rows), layer.hue_order)
