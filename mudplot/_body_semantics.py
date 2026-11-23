"""Typed raw tuples for weighted histogram and count body effects."""

from dataclasses import replace

from ._categorical import sample_rows
from ._semantics import MAX_CURVES, MAX_LEVELS, category_key, levels, semantic_levels


def body_rows(columns, layer, *, category_matches=None):
    cfg = layer.histogram if layer.type == "hist" else layer.stat
    weight = getattr(cfg, "weights", None)
    return sample_rows(
        columns,
        replace(layer, y=layer.x),
        weight_column=weight,
        category_matches=category_matches,
    )


def body_plan(columns, layer, rows, domain=None):
    cfg = layer.semantics
    roles = [
        (r, getattr(cfg, r))
        for r in ("hue", "size", "style")
        if getattr(cfg, r) is not None
    ]
    hue = cfg.hue or layer.group
    pool, source = (
        (rows, columns) if domain is None else (domain["rows"], domain["columns"])
    )
    if cfg.hue is not None and cfg.hue_kind == "categorical":
        outer = semantic_levels(source, cfg, "hue", pool)
    elif layer.hue_order is not None:
        outer = layer.hue_order
    elif hue is not None:
        outer = levels(columns[hue][i] for i in rows)
    else:
        outer = [None]
    if hue is not None and cfg.hue_kind != "numeric" and len(outer) > MAX_LEVELS:
        raise ValueError("categorical body hue exceeds 64 levels")

    def key(value):
        return None if value is None else category_key(value)

    reserved: dict[
        tuple[str, object] | None,
        dict[tuple, tuple[dict[str, object], object, list[int]]],
    ] = {key(v): {} for v in outer}
    for i in rows:
        h = None if hue is None else columns[hue][i]
        values = {r: columns[name][i] for r, name in roles}
        entry = reserved.setdefault(key(h), {}).setdefault(
            tuple(key(v) for v in values.values()), (values, h, [])
        )
        entry[2].append(i)
    order = {
        r: {key(v): i for i, v in enumerate(getattr(cfg, r + "_order") or ())}
        for r, _ in roles
    }
    groups, curves, pools, slots = {}, [], {}, {}
    for outer_index, (h, inner) in enumerate(reserved.items()):
        entries = sorted(
            inner.values(),
            key=lambda e: tuple(
                order[r].get(key(v), len(order[r])) for r, v in e[0].items()
            ),
        )
        width = 1 / (len(reserved) * max(1, len(entries)))
        for j, entry in enumerate(entries or [None]):
            i = len(pools)
            if i >= MAX_CURVES:
                raise ValueError("semantic body slots exceed 256")
            pools[i] = h
            slots[i] = (outer_index / len(reserved) + j * width, width)
            if entry is not None:
                values, raw_hue, members = entry
                curves.append(dict(values, _index=i, legacy_hue=raw_hue))
                groups.update((row, i) for row in members)
    return groups, curves, pools, slots
