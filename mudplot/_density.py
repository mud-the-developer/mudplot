"""Pure paired-field contracts; source rows, domains and fit pools stay distinct."""

from __future__ import annotations

from dataclasses import replace

from ._ecdf import finite_number, source_rows
from ._histogram import MAX_BIVARIATE_BINS
from ._transforms import projects
from .spec import (
    BivariateBinsSpec,
    ECDF2DSpec,
    HDRSpec,
    Histogram2DSpec,
    KDE2DSpec,
    KDESpec,
    SemanticSpec,
)

FIELD_TYPES = frozenset({"hist2d", "kde2d", "ecdf2d"})
DENSITY_TYPES = FIELD_TYPES | {"kde"}
MAX_FIELD_ROWS = 10000
MAX_FIELDS = 256
MAX_JOINT_EDGES = 512
KERNELS = ("gaussian", "epanechnikov_product")
HISTOGRAM2D_STATS = (
    "count",
    "frequency",
    "probability",
    "proportion",
    "percent",
    "density",
)
DASHES = ("-", "--", "-.", ":")


def _increasing(values):
    from fractions import Fraction
    from itertools import pairwise

    return all(Fraction(a) < Fraction(b) for a, b in pairwise(values))


def observation_axes(layer, panel):
    """Axes of logical inputs, not the density/probability colour quantity."""
    target = panel.y2 if layer.axis == "y2" else panel.y
    return (target, panel.x) if layer.orient == "h" else (panel.x, target)


def kde_config(layer):
    if layer.type == "kde":
        return KDESpec() if layer.kde is None else layer.kde
    return KDE2DSpec() if layer.kde2d is None else layer.kde2d


def histogram2d_config(layer):
    return (
        Histogram2DSpec(stat="density" if layer.density else "count")
        if layer.histogram2d is None
        else layer.histogram2d
    )


def weight_column(layer):
    config = (
        layer.kde
        if layer.type == "kde"
        else layer.kde2d
        if layer.type == "kde2d"
        else layer.histogram2d
        if layer.type == "hist2d"
        else layer.ecdf2d
        if layer.type == "ecdf2d"
        else layer.ecdf
        if layer.type == "ecdf"
        else None
    )
    return getattr(config, "weights", None)


def kernel_name(config):
    return config.kernel or "gaussian"


def density_space(config):
    return config.density_space or "data"


def multiple(config):
    return config.multiple or "layer"


def level_kind(config):
    return config.level_kind or ("cdf" if config.cumulative else "mass")


def fit_scales(layer):
    if layer.type == "kde":
        return (layer.stat_scale,)
    config = layer.kde2d
    return (
        tuple(config.fit_scales)
        if isinstance(config, KDE2DSpec)
        and isinstance(config.fit_scales, (list, tuple))
        else ("data", "data")
    )


def new_density_request(layer, panel):
    """ONE persisted, actual-axis-aware NEW predicate; repairs aren't opt-ins."""
    if layer.type == "ecdf2d":
        return True
    if layer.type == "hist2d":
        return (
            layer.histogram2d is not None
            or isinstance(layer.bins, BivariateBinsSpec)
            or layer.semantics is not None
        )
    if layer.type not in {"kde", "kde2d"}:
        return False
    config = kde_config(layer)
    if not isinstance(config, (KDESpec, KDE2DSpec)):
        return False  # The owning option validator reports malformed source.
    if layer.semantics is not None or kernel_name(config) != "gaussian":
        return True
    if isinstance(config, KDESpec):
        if multiple(config) != "layer":
            return True
    elif config.cumulative or config.hdr is not None or level_kind(config) == "density":
        return True
    axes = observation_axes(layer, panel)
    return any(
        choice == "axis" and axis is not None and axis.scale == "log"
        for choice, axis in zip(fit_scales(layer), axes, strict=False)
    )


def bounded_density_request(layer, panel):
    return new_density_request(layer, panel) or (
        layer.type in DENSITY_TYPES and projects(layer)
    )


def density_adapter(layer, panel):
    """Native completion can need an adapter WITHOUT adding a costly-mode cap."""
    if bounded_density_request(layer, panel):
        return True
    if layer.type not in DENSITY_TYPES:
        return False
    if layer.type == "kde":
        return False  # Existing native univariate drawing already swaps onto y2.
    if layer.orient == "h":
        return True
    if layer.type == "hist2d":
        return bool(panel.filters or panel.dropna) or any(
            getattr(layer, name) is not None
            for name in ("color", "edge_color", "line_width", "line_style", "label")
        )
    if layer.type == "kde2d":
        return layer.axis == "y2" or layer.colorbar or layer.clabel is not None
    return False


def density_rows(columns, layer, panel):
    new = new_density_request(layer, panel)
    limit = MAX_FIELD_ROWS if bounded_density_request(layer, panel) else None
    if isinstance(layer.semantics, SemanticSpec):
        from ._semantics import semantic_rows

        return semantic_rows(columns, layer, row_limit=limit)
    return source_rows(
        columns,
        layer,
        coordinates=(layer.x,) if layer.type == "kde" else (layer.x, layer.y),
        weights=weight_column(layer),
        typed_hue=new,
        row_limit=limit,
    )


def field_groups(columns, layer, rows, *, typed=True):
    """Original physical row partitions; a shared role domain is not a fit pool."""
    from ._semantics import category_key, levels, semantic_partition

    if isinstance(layer.semantics, SemanticSpec):
        ids, curves = semantic_partition(columns, layer.semantics, rows)
        groups = [
            {
                "index": index,
                "roles": curve,
                "hue": curve.get("hue"),
                "pool": category_key(curve["hue"]) if "hue" in curve else None,
                "rows": [],
            }
            for index, curve in enumerate(curves)
        ]
        for row, index in zip(rows, ids, strict=True):
            groups[index]["rows"].append(row)
        return groups
    if layer.group is None:
        return [
            {"index": 0, "roles": {}, "hue": None, "pool": None, "rows": list(rows)}
        ]
    values = (
        list(layer.hue_order)
        if layer.hue_order is not None
        else levels(columns[layer.group][row] for row in rows)
        if typed
        else list(dict.fromkeys(columns[layer.group][row] for row in rows))
    )
    lookup = {
        category_key(value) if typed else value: index
        for index, value in enumerate(values)
    }
    groups = [
        {"index": index, "roles": {}, "hue": value, "pool": index, "rows": []}
        for index, value in enumerate(values)
    ]
    for row in rows:
        value = columns[layer.group][row]
        index = lookup[category_key(value) if typed else value]
        groups[index]["rows"].append(row)
    return groups


def kde_extra_issues(config, *, bivariate=False):
    issues = []
    if config.kernel is not None and config.kernel not in KERNELS:
        issues.append("kernel must be gaussian or epanechnikov_product")
    if config.density_space is not None and config.density_space not in ("data", "fit"):
        issues.append("density_space must be data or fit")
    if not bivariate:
        if config.multiple is not None and config.multiple not in (
            "layer",
            "stack",
            "fill",
        ):
            issues.append("multiple must be layer, stack or fill")
        if config.multiple in ("stack", "fill") and config.common_grid is not True:
            issues.append("stack/fill require persisted common_grid=True")
        return issues
    if config.cumulative is not None and type(config.cumulative) is not bool:
        issues.append("cumulative must be boolean or None")
    if config.level_kind is not None and config.level_kind not in (
        "mass",
        "density",
        "cdf",
    ):
        issues.append("level_kind must be mass, density or cdf")
    if config.cumulative and level_kind(config) != "cdf":
        issues.append("cumulative fields use cdf levels, not HDR mass/density levels")
    if not config.cumulative and level_kind(config) == "cdf":
        issues.append("cdf levels require cumulative=True")
    if config.fit_scales is not None and (
        not isinstance(config.fit_scales, (list, tuple))
        or len(config.fit_scales) != 2
        or any(value not in ("data", "axis") for value in config.fit_scales)
    ):
        issues.append("fit_scales needs logical x/y choices data or axis")
    if config.hdr is not None:
        if not isinstance(config.hdr, HDRSpec):
            issues.append("hdr must be HDRSpec or None")
        else:
            if config.hdr.scope != "full":
                issues.append(
                    "HDRSpec.scope must be full; omit it for conditional geometry"
                )
            if (
                not finite_number(config.hdr.tolerance)
                or not 0 < config.hdr.tolerance <= 0.05
            ):
                issues.append("full HDR tolerance must be finite in (0,.05]")
        if config.cumulative:
            issues.append("a joint CDF is not a full-support HDR")
    return issues


def bivariate_bin_issues(bins):
    """Keep NumPy's old flat-list interpretation; typed pairs are unambiguous."""
    from ._histogram_bins import HISTOGRAM_BIN_RULES

    if isinstance(bins, BivariateBinsSpec):
        choices = (bins.x, bins.y)
    elif type(bins) is int:
        choices = (bins, bins)
    elif isinstance(bins, (list, tuple)) and len(bins) >= 2:
        if len(bins) == 2 and any(type(value) is not int for value in bins):
            return [
                "old two-element bins are integer counts; "
                "use BivariateBinsSpec for edges"
            ]
        choices = tuple(bins) if len(bins) == 2 else (bins, bins)
    else:
        return ["histogram2d bins need a count, old flat list, or BivariateBinsSpec"]
    issues = []
    for choice in choices:
        if type(choice) is int:
            if not 1 <= choice <= MAX_BIVARIATE_BINS:
                issues.append("histogram2d supports1..512 bins per logical axis")
        elif isinstance(choice, str):
            if not isinstance(bins, BivariateBinsSpec) or choice not in (
                *HISTOGRAM_BIN_RULES,
                "discrete",
            ):
                issues.append("named/discrete bivariate choices use BivariateBinsSpec")
        elif isinstance(choice, (list, tuple)):
            if not 2 <= len(choice) <= MAX_BIVARIATE_BINS + 1:
                issues.append("histogram2d edge arrays need2..513 endpoints")
            elif all(finite_number(value) for value in choice):
                if not _increasing(choice):
                    issues.append("histogram2d edges must strictly increase")
            elif not all(isinstance(value, str) and value for value in choice):
                issues.append(
                    "histogram2d edges must be finite or declared ISO literals"
                )
        else:
            issues.append("bivariate bin counts are non-bool integers; use typed edges")
    return issues


def histogram2d_issues(layer):
    config = histogram2d_config(layer)
    if not isinstance(config, Histogram2DSpec):
        return ["histogram2d must be Histogram2DSpec or None"]
    issues = bivariate_bin_issues(layer.bins)
    if config.stat not in HISTOGRAM2D_STATS:
        issues.append(
            "histogram2d stat must be count/frequency/probability/"
            "proportion/percent/density"
        )
    if type(config.common_norm) is not bool:
        issues.append("histogram2d common_norm must be boolean")
    if config.weights is not None and (
        not isinstance(config.weights, str) or not config.weights
    ):
        issues.append("histogram2d weights must be a nonempty column name")
    if layer.histogram2d is not None and layer.density:
        issues.append("use the typed stat or legacy density=True, not both")
    if config.kde is not None:
        if not isinstance(config.kde, KDE2DSpec):
            issues.append("histogram2d kde must be KDE2DSpec or None")
        else:
            from ._kde2d import option_issues

            issues.extend(option_issues(config.kde))
            if config.kde.weights is not None and config.kde.weights != config.weights:
                issues.append(
                    "histogram2d KDE weights must inherit or match the parent"
                )
            if config.kde.common_norm != config.common_norm:
                issues.append("histogram2d KDE common_norm must match the parent")
    return issues


def inherited_kde(layer):
    config = histogram2d_config(layer)
    return (
        replace(config.kde, weights=config.weights) if config.kde is not None else None
    )


def ecdf2d_option_issues(config):
    if not isinstance(config, ECDF2DSpec):
        return ["ecdf2d must be ECDF2DSpec"]
    issues = []
    if config.stat not in ("proportion", "percent", "count"):
        issues.append("joint ECDF stat must be proportion, percent or count")
    if type(config.complementary) is not bool:
        issues.append("joint ECDF complementary must be boolean")
    if config.weights is not None and (
        not isinstance(config.weights, str) or not config.weights
    ):
        issues.append("joint ECDF weights must be a nonempty column name")
    if not isinstance(config.bounds, (list, tuple)) or len(config.bounds) != 2:
        return [*issues, "joint ECDF needs logical x/y finite bounds"]
    for bound in config.bounds:
        if not isinstance(bound, (list, tuple)) or len(bound) != 2:
            issues.append("each joint ECDF bound needs two endpoints")
        elif any(
            not finite_number(value) and not (isinstance(value, str) and value)
            for value in bound
        ):
            issues.append(
                "joint ECDF bounds must be finite numbers or declared clock literals"
            )
        elif all(finite_number(value) for value in bound) and not _increasing(bound):
            issues.append("joint ECDF bounds must increase")
    for name in ("query_x", "query_y"):
        values = getattr(config, name)
        if values is None:
            continue
        if (
            not isinstance(values, (list, tuple))
            or not values
            or len(values) > MAX_JOINT_EDGES
        ):
            issues.append("joint ECDF query arrays need 1..512 finite values")
        elif any(
            not finite_number(value) and not (isinstance(value, str) and value)
            for value in values
        ):
            issues.append(
                "joint ECDF queries must be finite numbers or declared clock literals"
            )
        elif all(finite_number(value) for value in values) and not _increasing(values):
            issues.append(
                "joint ECDF query coordinates must increase without duplicates"
            )
    return issues


def density_semantic_issues(columns, layer, panel):
    from ._semantics import (
        MAX_LEVELS,
        categorical,
        option_issues,
        semantic_levels,
        semantic_partition,
    )

    config = layer.semantics
    issues = option_issues(config)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    if layer.group is not None or layer.hue_order is not None or layer.c is not None:
        issues.append(
            "independent field roles cannot combine with legacy group/hue_order/c"
        )
    if panel.projection != "2d":
        issues.append("density/empirical field roles require Cartesian2D axes")
    if config.hue is not None and layer.color is not None:
        issues.append("color cannot override mapped field hue")
    if config.size is not None and layer.line_width is not None:
        issues.append("line_width cannot override mapped outline/stroke size")
    if config.style is not None and layer.line_style is not None:
        issues.append("line_style cannot override mapped field dashes")
    if layer.marker is not None or layer.marker_size is not None:
        issues.append("density fields have no observed point glyphs")
    if layer.references is not None:
        issues.append(
            "independent field roles use layer reference metadata, "
            "not legacy group references"
        )
    if (layer.citation is not None or layer.href is not None) and not layer.label:
        issues.append("a semantic field reference needs an explicit layer label")
    try:
        rows = density_rows(columns, layer, panel)
    except ValueError as error:
        return [*issues, str(error)]
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        if not isinstance(name, str) or name not in columns:
            issues.append("semantic field role columns must exist")
            continue
        values = [columns[name][row] for row in rows]
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        if kind == "numeric":
            if any(not finite_number(value) for value in values):
                issues.append("numeric field roles need finite numbers, not bool")
        elif any(not categorical(value) for value in values):
            issues.append(
                "categorical field roles need nonempty strings or finite scalars"
            )
        else:
            selected = semantic_levels(columns, config, role, rows)
            if len(selected) > MAX_LEVELS or len(
                {str(value) for value in selected}
            ) != len(selected):
                issues.append("field role levels exceed64 or have ambiguous labels")
            if role == "style" and len(selected) > len(config.dashes or DASHES):
                issues.append("field style needs enough distinct named dashes")
    if not issues:
        _ids, curves = semantic_partition(columns, config, rows)
        if len(curves) > MAX_FIELDS:
            issues.append("field layers support at most256 distinct raw-role fields")
    if layer.type == "kde":
        numeric_hue = config.hue is not None and config.hue_kind == "numeric"
        if (layer.colorbar or layer.clabel is not None) and not numeric_hue:
            issues.append("univariate KDE semantic colorbar needs numeric hue")
    if type(layer.colorbar) is not bool:
        issues.append("field colorbar must be boolean")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append("field clabel needs colorbar and a<=512character string")
    return issues


def density_temporal_options(layer, changes, role, clock, selected, *, exact):
    """Map logical-input options through the SAME existing clock/bin parser."""
    from fractions import Fraction

    from ._temporal import DAY_MICROSECONDS, temporal_discrete_edges
    from ._temporal_data import _temporal_bounds, temporal_options

    index = 0 if role == "x" else 1

    def bounds(values):
        return _temporal_bounds(values, clock, exact=exact)

    bins = changes.get("bins", layer.bins)
    if layer.type == "hist2d" and isinstance(bins, BivariateBinsSpec):
        choice = getattr(bins, role)
        if isinstance(choice, str) and choice == "discrete":
            choice = temporal_discrete_edges(
                [value for value in selected if value is not None],
                **temporal_options(clock),
            )
            if exact:
                # The existing clock precision admission proves this roundtrip
                # recovers the exact generated integer-microsecond edge.
                choice = [
                    Fraction(
                        round(Fraction(value) * DAY_MICROSECONDS), DAY_MICROSECONDS
                    )
                    for value in choice
                ]
            if not choice:
                choice = "discrete"  # An empty selected view constructs no bins.
        elif isinstance(choice, (list, tuple)):
            choice = bounds(choice)
        changes["bins"] = replace(bins, **{role: choice})

    def clipped(config):
        if config is None or config.clip is None:
            return config
        if not isinstance(config.clip, (list, tuple)) or len(config.clip) != 2:
            raise ValueError("bivariate KDE clip needs logical x/y bound pairs")
        clip = list(config.clip)
        clip[index] = bounds(clip[index])
        return replace(config, clip=clip)

    if layer.type == "kde2d":
        config = changes.get("kde2d", layer.kde2d)
        if config is not None:
            changes["kde2d"] = clipped(config)
    elif layer.type == "hist2d":
        config = changes.get("histogram2d", layer.histogram2d)
        if config is not None and config.kde is not None:
            changes["histogram2d"] = replace(config, kde=clipped(config.kde))
    elif layer.type == "ecdf2d":
        config = changes.get("ecdf2d", layer.ecdf2d)
        if not isinstance(config, ECDF2DSpec):
            raise ValueError("joint ECDF requires ECDF2DSpec")
        if not isinstance(config.bounds, (list, tuple)) or len(config.bounds) != 2:
            raise ValueError("joint ECDF needs logical x/y bounds")
        frame = [
            bounds(values) if i == index else values
            for i, values in enumerate(config.bounds)
        ]
        query_name = "query_x" if role == "x" else "query_y"
        changes["ecdf2d"] = replace(
            config,
            bounds=frame,
            **{query_name: bounds(getattr(config, query_name))},
        )


def density_issues(columns, layer, panel):
    """Pure contracts for resolved field adapters; legacy omitted routes stay old."""
    from dataclasses import fields

    from ._components import _color
    from ._semantics import category_key
    from .capabilities import LAYER_TYPES
    from .spec import LayerSpec

    issues = []
    if layer.type == "hist2d":
        issues.extend(histogram2d_issues(layer))
        config = histogram2d_config(layer)
        if not isinstance(config, Histogram2DSpec):
            return issues
    elif layer.type == "ecdf2d":
        config = layer.ecdf2d
        issues.extend(ecdf2d_option_issues(config))
        if not isinstance(config, ECDF2DSpec):
            return issues
    else:
        config = kde_config(layer)
        if layer.type == "kde" and isinstance(config, KDESpec):
            from ._kde import option_issues

            issues.extend(option_issues(config))
        elif layer.type == "kde2d" and isinstance(config, KDE2DSpec):
            from ._kde2d import option_issues as option_issues_2d

            issues.extend(option_issues_2d(config))
        else:
            return ["density configuration has the wrong typed model"]
        if layer.edge_color is not None and not config.fill:
            issues.append("density edge_color requires a filled body")
    allowed = (
        set(LAYER_TYPES[layer.type]["required"])
        | set(LAYER_TYPES[layer.type]["optional"])
        | {"type", "citation", "href", "references"}
    )
    defaults = LayerSpec()
    for item in fields(LayerSpec):
        if item.name not in allowed and getattr(layer, item.name) != getattr(
            defaults, item.name
        ):
            issues.append(
                f"{item.name} is not supported for this density/empirical field"
            )
    if panel.projection != "2d":
        issues.append("density/empirical fields require Cartesian2D axes")
    if layer.orient not in ("v", "h"):
        issues.append("field orientation must be v or h")
    if layer.axis not in ("y", "y2") or (layer.axis == "y2" and panel.y2 is None):
        issues.append("field target must be a configured primary or secondary y-axis")
    if (
        layer.type in ("hist2d", "ecdf2d")
        and layer.group is None
        and (layer.citation is not None or layer.href is not None)
        and not layer.label
    ):
        issues.append("cell-field references require a visible layer label")
    for name in ("color", "edge_color"):
        if getattr(layer, name) is not None and not _color(getattr(layer, name)):
            issues.append(f"{name} must be a bounded native colour name or hex")
    if layer.line_width is not None and (
        not finite_number(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append("field outline/stroke width must be in[0,1000] points")
    if layer.line_style is not None and layer.line_style not in DASHES:
        issues.append("field line_style must be a named dash pattern")
    if type(layer.colorbar) is not bool:
        issues.append("field colorbar must be boolean")
    if layer.clabel is not None and not layer.colorbar:
        issues.append("clabel requires its requested colourbar")
    if layer.type == "kde" and layer.stat_scale not in ("data", "axis"):
        issues.append("univariate KDE stat_scale must be data or axis")
    axes = observation_axes(layer, panel)
    if layer.type == "kde":
        ordinate = axes[1]
        if ordinate is not None and (
            ordinate.scale != "linear" or ordinate.temporal is not None
        ):
            issues.append("KDE density/CDF/composition ordinate must be linear numeric")
        numeric_hue = (
            isinstance(layer.semantics, SemanticSpec)
            and layer.semantics.hue is not None
            and layer.semantics.hue_kind == "numeric"
        )
        if (
            layer.colorbar
            or layer.clabel is not None
            or layer.cmap_kind != defaults.cmap_kind
        ) and not numeric_hue:
            issues.append(
                "univariate KDE colour calibration requires independent numeric hue"
            )
        axes = axes[:1]
    coordinates = (layer.x,) if layer.type == "kde" else (layer.x, layer.y)
    for name in (*coordinates, weight_column(layer), layer.group):
        if name is not None and (
            not isinstance(name, str) or not name or name not in columns
        ):
            issues.append("field observation/weight/group columns must exist")
    try:
        rows = density_rows(columns, layer, panel)
    except ValueError as error:
        return [*issues, str(error)]
    for name, axis in zip(coordinates, axes, strict=True):
        if not isinstance(name, str) or name not in columns:
            continue
        values = [columns[name][row] for row in rows]
        if any(not finite_number(value) for value in values):
            issues.append("selected field coordinates must be finite native numbers")
        elif (
            axis is not None
            and axis.scale == "log"
            and any(value <= 0 for value in values)
        ):
            issues.append("log-displayed field observations must be positive")
        if axis is not None and axis.scale not in ("linear", "log"):
            issues.append("these field statistics support linear/log observation axes")
    for choice, axis in zip(
        fit_scales(layer) if layer.type in ("kde", "kde2d") else (), axes, strict=False
    ):
        if (
            choice == "axis"
            and axis is not None
            and axis.scale == "log"
            and axis.temporal is not None
        ):
            issues.append(
                "absolute calendar coordinates cannot be logarithmically fitted"
            )
    weight = weight_column(layer)
    if (
        isinstance(weight, str)
        and weight in columns
        and any(
            not finite_number(columns[weight][row]) or columns[weight][row] < 0
            for row in rows
        )
    ):
        issues.append("field weights must be finite nonnegative numbers, not bool")
    if layer.hue_order is not None and layer.group is None:
        issues.append("legacy field hue_order requires group")
    if isinstance(layer.group, str) and layer.group in columns:
        selected = [columns[layer.group][row] for row in rows]
        order = layer.hue_order
        if order is not None and (not isinstance(order, (list, tuple)) or not order):
            issues.append("field hue_order must be a nonempty list")
        elif new_density_request(layer, panel):
            try:
                keys = [
                    category_key(value)
                    for value in (selected if order is None else order)
                ]
                if len(set(keys)) > 64 or (
                    order is not None and len(set(keys)) != len(keys)
                ):
                    issues.append(
                        "categorical field hue order needs at most64 "
                        "distinct typed levels"
                    )
            except ValueError as error:
                issues.append(str(error))
        elif any(
            not isinstance(value, (str, bool)) and not finite_number(value)
            for value in selected
        ):
            issues.append("legacy density groups require strings or finite scalars")
        elif (
            bounded_density_request(layer, panel)
            and len(set(selected if order is None else order)) > 64
        ):
            issues.append("transformed field hue order supports at most64 levels")
    if layer.type == "hist2d" and isinstance(layer.bins, BivariateBinsSpec):
        for choice in (layer.bins.x, layer.bins.y):
            if isinstance(choice, (list, tuple)) and any(
                not finite_number(value) for value in choice
            ):
                issues.append(
                    "histogram clock edges require a declared coordinate clock"
                )
    if layer.type == "ecdf2d" and isinstance(config, ECDF2DSpec):
        for index, bound in enumerate(
            config.bounds if isinstance(config.bounds, (list, tuple)) else ()
        ):
            if not isinstance(bound, (list, tuple)) or len(bound) != 2:
                continue
            if not all(finite_number(value) for value in bound):
                issues.append(
                    "joint ECDF clock bounds require a declared coordinate clock"
                )
                continue
            queries = (
                getattr(config, ("query_x", "query_y")[index]) if index < 2 else None
            )
            if queries is not None and any(
                not finite_number(value) or value < bound[0] or value > bound[1]
                for value in queries
            ):
                issues.append(
                    "joint ECDF queries must be finite and within their bounds"
                )
    return issues
