"""Finite pre-statistic coordinate projections; no source or kernel mutation."""

from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from math import copysign, isfinite, log10
from typing import get_args, get_type_hints

from .spec import TransformSpec

_TYPES = get_type_hints(TransformSpec)
ROLES = get_args(_TYPES["role"])
NAMES = get_args(_TYPES["name"])
# Listed logical roles exist before any orientation or secondary-y mapping.
ROLE_SUPPORT = {
    "line": "xy",
    "lineplot": "xy",
    "barplot": "xy",
    "pointplot": "xy",
    "countplot": "x",
    "stripplot": "xy",
    "hist": "x",
    "hist2d": "xy",
    "kde": "x",
    "kde2d": "xy",
    "ecdf": "x",
    "ecdf2d": "xy",
}
CHAINS = (("identity",), ("log",), ("standardize",), ("log", "standardize"))
CATEGORIES = frozenset({"barplot", "pointplot", "countplot", "stripplot"})


def decode_transforms(stages):
    if stages is None:
        return None
    if not isinstance(stages, (list, tuple)) or not 1 <= len(stages) <= 4:
        raise ValueError("transforms requires an array of 1..4 stages")
    return [
        stage if isinstance(stage, TransformSpec) else TransformSpec.from_dict(stage)
        for stage in stages
    ]


def stages_for(layer, role):
    return tuple(
        stage.name
        for stage in layer.transforms or ()
        if stage.role == role and stage.name != "identity"
    )


def projects(layer):
    return isinstance(layer.transforms, (list, tuple)) and any(
        isinstance(stage, TransformSpec) and stage.name != "identity"
        for stage in layer.transforms
    )


def axis_names(layer):
    return (layer.axis, "x") if layer.orient == "h" else ("x", layer.axis)


def option_issues(layer, panel=None):
    stages = layer.transforms
    if stages is None:
        return []
    if not isinstance(stages, (list, tuple)) or not 1 <= len(stages) <= 4:
        return ["transforms requires an array of 1..4 stages"]
    for stage in stages:
        if (
            not isinstance(stage, TransformSpec)
            or stage.role not in ROLES
            or stage.name not in NAMES
        ):
            return [
                (
                    "transforms requires typed x/y stages named identity, log or "
                    "standardize"
                )
            ]
        if stage.role not in ROLE_SUPPORT.get(layer.type, ""):
            return [f"{layer.type} has no supported transform input {stage.role}"]
    for role in ROLES:
        names = tuple(stage.name for stage in stages if stage.role == role)
        if names and names not in CHAINS:
            return [
                (
                    f"transforms.{role} requires identity, log, standardize or log "
                    "then standardize"
                )
            ]
    if not projects(layer):
        return []

    from ._line import categorical_predictor
    from ._stat import stat_config
    from ._strip import categorical_strip
    from .spec import Histogram2DSpec, HistogramSpec, KDE2DSpec, KDESpec

    config = {
        "hist": (layer.histogram, HistogramSpec),
        "hist2d": (layer.histogram2d, Histogram2DSpec),
        "kde": (layer.kde, KDESpec),
        "kde2d": (layer.kde2d, KDE2DSpec),
    }.get(layer.type)
    if config is not None and not isinstance(*config):
        return [f"nonidentity transforms require the named {layer.type} configuration"]
    if layer.type == "stripplot" and not categorical_strip(layer):
        return ["nonidentity strip transforms require categorical strip settings"]
    if stages_for(layer, "x") and (
        (layer.type in CATEGORIES and not layer.native_scale)
        or categorical_predictor(layer)
    ):
        return ["nonidentity predictor transforms require native numeric coordinates"]
    if (
        stages_for(layer, "y")
        and layer.type in {"barplot", "pointplot", "lineplot"}
        and getattr(stat_config(layer), "estimator", None) == "count"
    ):
        return ["count does not transform the response"]
    if panel is not None and panel.projection != "2d":
        return ["coordinate transforms require Cartesian 2-D axes"]

    for index, (role, axis_name) in enumerate(
        zip(ROLES, axis_names(layer), strict=True)
    ):
        if not stages_for(layer, role):
            continue
        axis = None if panel is None else getattr(panel, axis_name, None)
        if axis is not None and (axis.temporal is not None or axis.scale == "log"):
            return [
                f"transforms.{role} cannot share a temporal or logarithmic display axis"
            ]
        if layer.type in {"barplot", "pointplot", "lineplot", "kde"} and (
            (role == "x" if layer.type == "kde" else role == "y")
            and layer.stat_scale == "axis"
        ):
            return [f"transforms.{role} conflicts with stat_scale='axis'"]
        kde = (
            layer.kde2d
            if layer.type == "kde2d"
            else (layer.histogram2d.kde if layer.type == "hist2d" else None)
        )
        fits = getattr(kde, "fit_scales", None)
        if (
            isinstance(fits, (list, tuple))
            and index < len(fits)
            and fits[index] == "axis"
        ):
            return [f"transforms.{role} conflicts with the KDE axis-fit declaration"]
    return []


def unit(layer, role, default):
    chain = stages_for(layer, role)
    return {
        ("log",): "log10 input",
        ("standardize",): "z(input)",
        ("log", "standardize"): "z(log10 input)",
    }.get(chain, default)


class ProjectedColumn(Sequence):
    """Sparse role-local values indexed by unchanged panel-local row ID."""

    __slots__ = ("size", "values")

    def __init__(self, size, values):
        self.size = size
        self.values = values

    def __len__(self):
        return self.size

    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self.values.get(row) for row in range(*i.indices(self.size))]
        if i < 0:
            i += self.size
        if not 0 <= i < self.size:
            raise IndexError(i)
        return self.values.get(i)

    def __iter__(self):
        get = self.values.get
        return (get(i) for i in range(self.size))


COLUMN_ARRAYS = (list, tuple, ProjectedColumn)


def _finite(value):
    from ._ecdf import finite_number

    if type(value) not in (int, float) or not finite_number(value):
        raise ValueError("transform inputs must be finite non-boolean numbers")
    return value


def _working(value, take_log):
    value = _finite(value)
    if not take_log:
        return value
    if value <= 0:
        raise ValueError("log transform requires positive selected coordinates")
    return log10(value)


def _project_role(values, rows, moments, order, stages, budget):
    from ._ecdf import sqrt_fraction
    from ._stat import is_missing

    take_log = stages[0] == "log"
    standardize = stages[-1] == "standardize"
    total, squares, variance = Fraction(0), Fraction(0), None
    if standardize and moments:
        for row in moments:
            z = Fraction(_working(values[row], take_log))
            if budget is not None:
                bits = max(
                    abs(z.numerator).bit_length(),
                    z.denominator.bit_length(),
                    abs(total.numerator).bit_length(),
                    squares.numerator.bit_length(),
                )
                budget.charge("coordinate_moments", 4, bits=bits * 2 + 2)
            total += z
            squares += z * z
        total /= len(moments)
        variance = squares / len(moments) - total * total
        if variance == 0:
            raise ValueError("standardize requires nonzero population variance")

    projected, distinct, log_keys = {}, {}, {}

    def place(raw):
        work = _working(raw, take_log)
        if take_log and log_keys.setdefault(work, raw) != raw:
            raise ValueError("distinct coordinates collapse in the log stage")

        if variance is not None:
            residual = Fraction(work) - total
            if budget is not None:
                bits = max(
                    abs(residual.numerator).bit_length(),
                    residual.denominator.bit_length(),
                    variance.numerator.bit_length(),
                    variance.denominator.bit_length(),
                )
                budget.charge("coordinate_standardization", 4, bits=bits * 4 + 2)
            result = copysign(
                sqrt_fraction(residual * residual / variance), -1 if residual < 0 else 1
            )
            if residual and result == 0:
                raise ValueError("nonzero standardized coordinate collapses")
        else:
            result = work
            if budget is not None:
                budget.charge("coordinate_log", 1)
        if not isfinite(result) or distinct.setdefault(result, raw) != raw:
            raise ValueError(
                "distinct projected coordinates collapse or exceed finite range"
            )
        return result

    if standardize and variance is None:
        return ProjectedColumn(len(values), {}), None
    for row in rows:
        raw = values[row]
        if not is_missing(raw):
            projected[row] = place(raw)
    converted = None if order is None else [place(raw) for raw in order]
    return ProjectedColumn(len(values), projected), converted


def projection_storage(columns, layer, row_count):
    """Prospective owned projection bytes, excluding borrowed source leaves."""
    import sys

    count = row_count + len(layer.order or ())
    ref = sys.getsizeof((None,)) - sys.getsizeof(())
    number = sys.getsizeof(0.0) + sys.getsizeof(max(len(columns.get(layer.x, ())), 1))
    # Two role maps, collision maps, old/new resize overlap and sparse clocks.
    size = 6 * sys.getsizeof({}) + (12 * len(columns) + 32) * ref
    size += count * (6 * number + 40 * ref + 2 * sys.getsizeof(Fraction(0)))
    if any("standardize" in stages_for(layer, role) for role in ROLES):
        # Finite binary64 inputs have at most 2098 aligned dyadic bits.
        # Widen for squared sums, centering, ratios and scaled exact roots.
        bits = 12 * (2098 + max(1, row_count).bit_length())
        limbs = (bits + sys.int_info.bits_per_digit - 1) // sys.int_info.bits_per_digit
        size += 32 * (sys.getsizeof(0) + limbs * sys.int_info.sizeof_digit)
    return size


def private_column(columns, layer, stem):
    """Do not make an invalid raw reference accidentally resolve to scratch."""
    names = {
        name
        for name in (layer.x, layer.y, layer.group, layer.c)
        if isinstance(name, str)
    }
    for config in (
        layer,
        layer.stat,
        layer.semantics,
        layer.histogram,
        layer.histogram2d,
        layer.kde,
        layer.kde2d,
        layer.ecdf,
        layer.ecdf2d,
    ):
        for attr in ("hue", "size", "style", "weights", "units"):
            name = getattr(config, attr, None)
            if isinstance(name, str):
                names.add(name)
    while stem in columns or stem in names:
        stem += "_"
    return stem


def project_layer(view, layer, rows, moments=None, *, budget=None):
    """Apply projections in the already-private per-layer column dictionary."""
    if moments is None:
        moments = rows
    changes = {}
    for role in ROLES:
        stages = stages_for(layer, role)
        if not stages:
            continue
        name = getattr(layer, role)
        if not isinstance(name, str) or name not in view:
            raise ValueError(f"transforms.{role} requires an existing source column")
        alias = private_column(view, layer, f"__mudplot_projected_{role}")
        order = (
            layer.order
            if role == "x" and layer.type in CATEGORIES | {"line", "lineplot"}
            else None
        )
        view[alias], resolved = _project_role(
            view[name], rows, moments, order, stages, budget
        )
        changes[role] = alias
        if order is not None:
            changes["order"] = resolved
    return view, replace(layer, **changes)


def axis_signatures(columns, layer, panel):
    """Return data-axis dimensions of this prepared layer, not guide styling."""
    from ._categorical import DISTRIBUTION_TYPES, distribution_rows
    from ._density import DENSITY_TYPES, density_rows, kde_config, multiple
    from ._ecdf import ecdf_rows
    from ._histogram import histogram_rows
    from ._line import line_rows
    from ._semantics import semantic_rows
    from ._stat import (
        STAT_LAYER_TYPES,
        is_missing,
        new_stat_request,
        stat_config,
        usable_rows,
    )
    from ._strip import categorical_strip
    from .spec import SemanticSpec

    kind = layer.type
    if kind in {"hline", "vline", "annotate", "text"}:
        return ()
    y_present = kind not in {"hist", "kde", "ecdf", "countplot", "rug"}
    x, y = (
        columns.get(name, ()) if isinstance(name, str) else ()
        for name in (layer.x, layer.y)
    )
    if kind in {"heatmap", "clustermap", "contour", "contourf"}:
        return (("x", ()), (layer.axis, ()))
    if kind in DENSITY_TYPES:
        try:
            observed = bool(density_rows(columns, layer, panel))
        except ValueError:
            return ()  # The owning validation branch reports the malformed cohort.
    elif kind == "hist" and layer.histogram is not None:
        observed = bool(histogram_rows(columns, layer))
    elif kind == "ecdf" and layer.semantics is None:
        observed = bool(ecdf_rows(columns, layer))
    elif kind == "line":
        observed = bool(line_rows(columns, layer))
    elif kind == "stem":
        from ._stem import stem_rows

        try:
            observed = bool(stem_rows(columns, layer))
        except ValueError:
            return ()  # The owning stem validator reports membership errors.
    elif isinstance(layer.semantics, SemanticSpec):
        observed = bool(semantic_rows(columns, layer))
    elif kind in STAT_LAYER_TYPES:
        observed = bool(
            usable_rows(columns, layer, advanced=new_stat_request(layer, panel))
        )
    elif kind in DISTRIBUTION_TYPES | {"swarmplot"} or categorical_strip(layer):
        observed = bool(distribution_rows(columns, layer))
    elif y_present and y:
        observed = any(
            not is_missing(a) and not is_missing(b) for a, b in zip(x, y, strict=False)
        )
    else:
        observed = any(not is_missing(value) for value in x)
    if not observed:
        return ()
    x_axis, y_axis = axis_names(layer)
    x_chain, y_chain = (stages_for(layer, role) for role in ROLES)
    if kind == "rug":
        return ((x_axis, ()),)
    if kind == "hist":
        cfg = layer.histogram
        ratio = (
            layer.density
            if cfg is None
            else (
                cfg.stat in {"density", "frequency"}
                and not cfg.cumulative
                and cfg.multiple != "fill"
            )
        )
        if ratio:
            y_chain = ("per", *x_chain)
    elif kind == "kde":
        cfg = kde_config(layer)
        if not cfg.cumulative and multiple(cfg) != "fill":
            y_chain = ("per", *x_chain)
    elif kind in {"barplot", "pointplot", "lineplot"}:
        cfg = stat_config(layer)
        if y_chain and cfg.estimator == "sum" and cfg.weights is not None:
            y_chain = ("total", *y_chain)
    return ((x_axis, x_chain), (y_axis, y_chain))


def sharing_issues(spec, views):
    from ._layout import shared_groups

    def mixed(signatures):
        # A legacy reciprocal raw unit is not itself a projection request.
        return len(signatures) > 1 and any(
            any(name in {"log", "standardize"} for name in key) for key in signatures
        )

    for index, signatures in enumerate(views):
        for axis in ("x", "y", "y2"):
            if mixed(signatures.get(axis, ())):
                yield (
                    f"panel {index} {axis} mixes incompatible coordinate pipeline units"
                )
    for axis in ("x", "y"):
        for group in shared_groups(spec, axis):
            if len(group) > 1 and mixed(
                {key for index in group for key in views[index].get(axis, ())}
            ):
                yield f"shared {axis} axes have incompatible coordinate pipeline units"
    from ._layout import twin_value_groups

    for members in twin_value_groups(spec):
        if mixed(
            {key for index, role in members for key in views[index].get(role, ())}
        ):
            yield "named twin value axes have incompatible coordinate pipeline units"
