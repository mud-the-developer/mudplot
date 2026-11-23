"""Extended pair/joint cohort derivation from ordinary saved mark declarations."""

from ._density import weight_column
from ._ecdf import finite_number
from ._semantics import category_key, option_issues
from ._stat import is_missing
from .spec import SemanticSpec

ANNOTATIONS = frozenset({"hline", "vline", "text", "annotate"})


def grid_owner(panel):
    layers = [layer for layer in panel.layers if layer.type not in ANNOTATIONS]
    if len(layers) != 1 or layers[0].type not in {
        "scatter",
        "regplot",
        "hist2d",
        "hexbin",
        "hist",
        "kde",
        "ecdf",
    }:
        raise ValueError(
            "a grid cohort needs exactly one scientific owner plus annotations"
        )
    layer = layers[0]
    required = (
        [layer.x] if layer.type in {"hist", "kde", "ecdf"} else [layer.x, layer.y]
    )
    if layer.c is not None:
        required.append(layer.c)
    if not all(name in panel.dropna for name in required):
        raise ValueError(
            "grid cohort dropna must keep its original owner coordinate requirements"
        )
    return layer


def grid_weight(layer):
    if layer.type == "hist":
        return getattr(layer.histogram, "weights", None)
    if layer.type in {"scatter", "hexbin", "regplot"}:
        return layer.weights
    return weight_column(layer)


def common_weight(columns, *declarations):
    names = set()
    for value in declarations:
        if value is not None:
            if not isinstance(value, str) or not value or value not in columns:
                raise ValueError("grid weights must name an original source column")
            names.add(value)
    if len(names) > 1:
        raise ValueError(
            "center, overlay and marginals must share the same named weight"
        )
    return next(iter(names), None)


def grid_rows(columns, owner, candidates):
    """Physical row IDs. Test raw role selection before admitting weights/clocks."""
    config = owner.semantics
    requirements = []
    if owner.group is not None:
        requirements.append((owner.group, owner.hue_order, False))
    if config is not None:
        if not isinstance(config, SemanticSpec):
            raise ValueError("grid roles require a typed SemanticSpec")
        issues = option_issues(config)
        if issues:
            raise ValueError("; ".join(issues))
        for role in ("hue", "size", "style"):
            col = getattr(config, role)
            numeric = role != "style" and getattr(config, role + "_kind") == "numeric"
            if col is not None:
                requirements.append((col, getattr(config, role + "_order"), numeric))
    checks = []
    for name, order, numeric in requirements:
        if name not in columns:
            raise ValueError("grid grouping/mapping must name original source columns")
        allowed = None if order is None else {category_key(value) for value in order}
        checks.append((columns[name], allowed, numeric))
    weight = common_weight(columns, grid_weight(owner))
    values = None if weight is None else columns[weight]
    selected = []
    for row in candidates:
        admitted = True
        for series, allowed, _numeric in checks:
            v = series[row]
            if is_missing(v):
                admitted = False
                break
            if allowed is not None and category_key(v) not in allowed:
                admitted = False
                break
        if not admitted:
            continue
        if values is not None:
            w = values[row]
            if is_missing(w):
                continue
            if not finite_number(w) or w < 0:
                raise ValueError(
                    "selected grid weights must be finite nonnegative numbers"
                )
            if w == 0:
                continue
        for series, _, numeric in checks:
            if numeric:
                if not finite_number(series[row]):
                    raise ValueError(
                        "selected numeric grid roles must be finite numbers, not bool"
                    )
            else:
                category_key(series[row])
        selected.append(row)
    return selected
