"""Pure explicit cross-layer swarm membership, slot and resource planning."""

from ._categorical import distribution_rows, swarm_levels
from ._semantics import category_key
from .spec import SemanticSpec

MAX_SCOPE_INSTANCES = 4000


def scope_name_issues(layer):
    name = layer.pack_scope
    if name is None:
        return []
    if layer.type != "swarmplot":
        return ["pack_scope only applies to swarmplot"]
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name) > 64
        or any(ord(c) < 32 for c in name)
    ):
        return ["pack_scope must be a nonempty <=64-character name without controls"]
    return []


def _ordered_union(sequences):
    result, seen = [], set()
    for sequence in sequences:
        for value in sequence:
            key = None if value is None else category_key(value)
            if key not in seen:
                seen.add(key)
                result.append(value)
    return result


def _order_signature(order):
    return None if order is None else tuple(category_key(v) for v in order)


def _hue(layer):
    config = layer.semantics
    if isinstance(config, SemanticSpec) and config.hue is not None:
        return config.hue if config.hue_kind == "categorical" else None
    return layer.group


def _geometry_signature(layer, panel):
    from ._temporal_data import category_axis_for, clock_order

    axis = category_axis_for(layer, panel)
    native = layer.native_scale or (axis is not None and axis.temporal is not None)
    resolved, _, _ = clock_order(layer, panel)
    width = 0.8 if layer.width is None else layer.width
    return (
        layer.axis,
        layer.orient,
        layer.x,
        native,
        _order_signature(layer.order if resolved is None else resolved),
        width,
        width if layer.dodge is None else layer.dodge,
        0 if layer.gap is None else layer.gap,
    )


def scope_plans(columns, panel, *, domains=None):
    """Resolve one compatible category/hue slot union per declared panel scope.

    Physical rows are counted per member, never deduplicated by original row ID.
    This runs during pure validation, before renderer coordinates/paths exist.
    Render planning repeats the same pure contract using canonical temporal views.
    """
    from ._temporal_data import clock_selector, prepare_temporal_layer

    members = {}
    issues = []
    for index, layer in enumerate(panel.layers):
        problems = scope_name_issues(layer)
        issues.extend(f"layer {index}: {problem}" for problem in problems)
        if problems or layer.pack_scope is None:
            continue
        members.setdefault(layer.pack_scope, []).append((index, layer))
    plans = {}
    for name, selected in members.items():
        try:
            first = selected[0][1]
            signature = _geometry_signature(first, panel)
            # Count before building category unions or any effect-side arrays.
            count = sum(
                len(
                    distribution_rows(
                        columns, layer, category_matches=clock_selector(layer, panel)
                    )
                )
                for _, layer in selected
            )
            if count > MAX_SCOPE_INSTANCES:
                issues.append(
                    f"pack_scope {name!r}: {count} physical instances exceed "
                    f"{MAX_SCOPE_INSTANCES}; existing 2000-per-layer bound also applies"
                )
                continue
            prepared = []
            for index, layer in selected:
                actual = _geometry_signature(layer, panel)
                if actual != signature:
                    raise ValueError(
                        "members require identical target axis/orientation/category "
                        "column/order/native mode/width/dodge/gap"
                    )
                view, converted, _ = prepare_temporal_layer(columns, layer, panel)
                rows = distribution_rows(view, converted)
                categories, groups = swarm_levels(view, converted, rows)
                config = layer.semantics
                domain = (domains or {}).get(getattr(config, "scale_id", None))
                if (
                    domain is not None
                    and config.hue is not None
                    and config.hue_kind == "categorical"
                ):
                    from ._semantics import semantic_levels

                    groups = semantic_levels(
                        domain["columns"], config, "hue", domain["rows"]
                    )
                prepared.append((index, layer, categories, groups))
            categories = _ordered_union(item[2] for item in prepared)
            groups = _ordered_union(item[3] for item in prepared)
            dodged = len(groups) > 1 and first.dodge != 0
            if dodged:
                config = first.semantics
                hue_order = (
                    config.hue_order
                    if isinstance(config, SemanticSpec) and config.hue is not None
                    else first.hue_order
                )
                hue_signature = (_hue(first), _order_signature(hue_order))
                for _, layer, _, _ in prepared:
                    config = layer.semantics
                    order = (
                        config.hue_order
                        if isinstance(config, SemanticSpec) and config.hue is not None
                        else layer.hue_order
                    )
                    if (_hue(layer), _order_signature(order)) != hue_signature:
                        raise ValueError(
                            "dodged members require identical hue column/order"
                        )
            plans[name] = {
                "categories": categories,
                "groups": groups,
                "members": [index for index, _ in selected],
                "instances": count,
            }
        except (ValueError, TypeError, KeyError) as error:
            issues.append(f"pack_scope {name!r}: {error}")
    return plans, issues
