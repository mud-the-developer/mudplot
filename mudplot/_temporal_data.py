"""Pure role-specific coordinate views; never replace semantic/source columns."""

from contextlib import nullcontext
from dataclasses import replace

from ._categorical import ClockCategoryArgs, distribution_columns, distribution_rows
from ._ecdf import ecdf_rows
from ._facet import ordered_group_columns
from ._histogram import histogram_rows
from ._kde import kde_rows
from ._semantics import semantic_rows
from ._stat import (
    MAX_ADVANCED_STAT_CELLS,
    MAX_ADVANCED_STAT_ROWS,
    STAT_LAYER_TYPES,
    is_missing,
    new_stat_request,
    stat_config,
    usable_rows,
)
from ._strip import categorical_strip
from ._temporal import (
    exact_temporal_coordinates,
    temporal_coordinates,
    temporal_discrete_edges,
    temporal_durations,
)
from ._transforms import (
    ProjectedColumn,
    private_column,
    project_layer,
    projection_storage,
    projects,
)
from ._transforms import option_issues as transform_option_issues
from .spec import ECDFSpec, RegressionSpec, StatSpec, TemporalSpec

_CATEGORICAL = {"box", "violin", "boxenplot", "swarmplot"}
_UNIVARIATE = {"hist", "kde", "ecdf"}
_XY = {
    "line",
    "scatter",
    "stripplot",
    "regplot",
    "hist2d",
    "kde2d",
    "ecdf2d",
    "bar",
    "errorbar",
    "band",
    "hexbin",
    "stackplot",
    "rug",
    "stem",
    "stairs",
    "eventplot",
    "broken_barh",
}
_LITERAL = {"hline", "vline", "text", "annotate"}
TEMPORAL_LAYER_TYPES = frozenset(_XY | _CATEGORICAL | _UNIVARIATE | STAT_LAYER_TYPES)


def temporal_options(config):
    if not isinstance(config, TemporalSpec):
        raise ValueError("temporal axis requires TemporalSpec")
    return {"timezone": config.timezone, "unit": config.unit, "origin": config.origin}


def _temporal_bounds(bounds, config, *, exact=False):
    if not isinstance(bounds, (list, tuple)) or not any(
        isinstance(v, str) for v in bounds
    ):
        return bounds
    if any(v is not None and not isinstance(v, str) for v in bounds):
        raise ValueError(
            "temporal bounds must be all ISO strings or all day coordinates"
        )
    converter = exact_temporal_coordinates if exact else temporal_coordinates
    return converter(bounds, timezone=config.timezone)


def category_axis_for(layer, panel):
    return (
        (panel.y2 if layer.axis == "y2" else panel.y)
        if layer.orient == "h"
        else panel.x
    )


def category_clock(layer, panel):
    if not (
        layer.type in STAT_LAYER_TYPES | _CATEGORICAL | {"line"}
        or categorical_strip(layer)
    ):
        return None
    if layer.type in _CATEGORICAL and distribution_columns(layer)[0] is None:
        return None
    axis = category_axis_for(layer, panel)
    return None if axis is None else axis.temporal


def inferred_clock_order(values, clock):
    options = temporal_options(clock)
    representatives = {}
    for raw in values:
        if not is_missing(raw):
            key = exact_temporal_coordinates((raw,), **options)[0]
            representatives.setdefault(key, raw)
    return list(representatives.values())


def clock_order(layer, panel):
    """Canonical order, converter, and selection for an explicit/resolved clock."""
    clock = category_clock(layer, panel)
    if clock is None or layer.order is None:
        return None, None, None
    if not isinstance(layer.order, (list, tuple)):
        raise ValueError("temporal category order must be a sequence")
    options = temporal_options(clock)
    positions = exact_temporal_coordinates(layer.order, **options)
    if None in positions or len(set(positions)) != len(positions):
        raise ValueError("temporal category order has duplicate or missing instants")
    wanted = set(positions)

    def key(raw):
        return exact_temporal_coordinates((raw,), **options)[0]

    def matches(raw):
        try:
            return key(raw) in wanted
        except ValueError:
            # A valid explicit order excludes times outside its domain. An
            # unparseable observation cannot designate one of those instants.
            return False

    return [float(position) for position in positions], key, matches


def clock_selector(layer, panel):
    return clock_order(layer, panel)[2]


def select_line_rows(
    columns, layer, panel, *, candidates=None, barriers=False, topology=True
):
    """Selected native-clock order uses instants, not ISO offset spellings."""
    from ._line import line_rows

    _, _, matches = clock_order(layer, panel)
    selected = line_rows(
        columns,
        replace(layer, order=None) if matches is not None else layer,
        topology=topology,
        barriers=barriers,
        candidates=candidates,
    )
    if matches is None:
        return selected
    return [
        row
        for row in selected
        if (is_missing(columns[layer.x][row]) and layer.type == "line")
        or matches(columns[layer.x][row])
    ]


def prepare_temporal_layer(
    columns, layer, panel, *, field_budget=None, coordinate_leases=None
):
    from ._density import (
        DENSITY_TYPES,
        FIELD_TYPES,
        MAX_FIELD_ROWS,
        MAX_FIELDS,
        bounded_density_request,
        density_adapter,
        density_rows,
        density_temporal_options,
        field_groups,
        new_density_request,
        weight_column,
    )
    from .spec import ECDF2DSpec, Histogram2DSpec, KDE2DSpec, KDESpec

    problems = transform_option_issues(layer, panel)
    if problems:
        raise ValueError("; ".join(problems))
    projection = projects(layer)
    resolved_order, clock_key, category_matches = clock_order(layer, panel)
    clock_args: ClockCategoryArgs = (
        {} if clock_key is None else {"category_key_for": clock_key}
    )
    bounded_stats = (
        layer.stat is None or isinstance(layer.stat, StatSpec)
    ) and new_stat_request(layer, panel)
    if projection and layer.type in {"barplot", "pointplot", "lineplot"}:
        bounded_stats = bounded_stats or not (
            layer.type == "lineplot"
            and getattr(layer.line, "resampling", None) == "unit"
        )
    early_rows = None

    density = layer.type in DENSITY_TYPES
    density_selected = None
    exact_density = density and density_adapter(layer, panel)
    if density:
        field, expected = {
            "kde": ("kde", KDESpec),
            "kde2d": ("kde2d", KDE2DSpec),
            "hist2d": ("histogram2d", Histogram2DSpec),
            "ecdf2d": ("ecdf2d", ECDF2DSpec),
        }[layer.type]
        config = getattr(layer, field)
        if (config is not None and not isinstance(config, expected)) or (
            layer.type == "ecdf2d" and config is None
        ):
            raise ValueError(f"{field} requires {expected.__name__}")
        construction = nullcontext()
        if field_budget is not None:
            from ._density_input import _construction_bytes

            construction = field_budget.lease(_construction_bytes(columns, layer))
        with construction:
            density_selected = density_rows(columns, layer, panel)
            if bounded_density_request(layer, panel):
                if len(density_selected) > MAX_FIELD_ROWS:
                    raise ValueError(
                        "NEW paired fields exceed10000 selected physical rows"
                    )
                groups = field_groups(
                    columns,
                    layer,
                    density_selected,
                    typed=new_density_request(layer, panel),
                )
                if len(groups) > MAX_FIELDS:
                    raise ValueError("NEW paired fields exceed256 raw-role fields")
                del groups
            if field_budget is not None:
                assert coordinate_leases is not None
                coordinate_leases.append(
                    field_budget.lease(
                        projection_storage(columns, layer, len(density_selected))
                    )
                )
    if (
        layer.type in STAT_LAYER_TYPES
        and (layer.stat is None or isinstance(layer.stat, StatSpec))
        and bounded_stats
    ):
        from ._categorical import distribution_plan

        advanced = new_stat_request(layer, panel)
        if projection and layer.type == "lineplot":
            stat_rows = select_line_rows(columns, layer, panel, topology=False)
        else:
            stat_rows = usable_rows(
                columns,
                layer,
                advanced=advanced,
                limit=MAX_ADVANCED_STAT_ROWS,
                category_matches=category_matches,
            )
        if len(stat_rows) > MAX_ADVANCED_STAT_ROWS:
            raise ValueError("NEW statistical selected rows exceed10000")
        if advanced or getattr(layer.line, "predictor", None) == "categorical":
            cells = len(
                distribution_plan(columns, layer, rows=stat_rows, **clock_args)[2]
            )
        else:
            try:
                cells = len(
                    {
                        (
                            columns[layer.x][i]
                            if clock_key is None
                            else clock_key(columns[layer.x][i]),
                            None if layer.group is None else columns[layer.group][i],
                        )
                        for i in stat_rows
                    }
                )
            except TypeError as error:
                raise ValueError(
                    "selected statistical categories and groups must be scalar"
                ) from error
        if cells > MAX_ADVANCED_STAT_CELLS:
            raise ValueError("NEW statistical drawn pointwise cells exceed256")
        if layer.type != "lineplot":
            early_rows = stat_rows
    if layer.type == "box":
        from ._box import (
            MAX_BOX_CELLS,
            MAX_BOX_ROWS,
            advanced_box,
            box_option_issues,
            box_rows,
        )
        from ._categorical import distribution_plan

        if advanced_box(layer):
            problems = box_option_issues(layer)
            if problems:
                raise ValueError("; ".join(problems))
            rows = box_rows(columns, layer, category_matches=category_matches)
            if len(rows) > MAX_BOX_ROWS:
                raise ValueError("advanced box selected source row limit exceeded")
            if (
                len(distribution_plan(columns, layer, rows=rows, **clock_args)[2])
                > MAX_BOX_CELLS
            ):
                raise ValueError("advanced box drawn samplecell limit exceeded")
            early_rows = rows
    if layer.type == "violin":
        from ._categorical import distribution_plan, sample_rows
        from ._violin_options import (
            MAX_INNER_OBSERVATIONS,
            MAX_VIOLIN_PROFILES,
            advanced_option_issues,
            advanced_violin,
        )

        if advanced_violin(layer):
            # Clock clip bounds are parsed below; other options/resource work
            # are checked before constructing numerical coordinate views.
            problems = advanced_option_issues(replace(layer, clip=None))
            if problems:
                raise ValueError("; ".join(problems))
            rows = sample_rows(columns, layer, category_matches=category_matches)
            if len(rows) > MAX_INNER_OBSERVATIONS:
                raise ValueError("advanced violin selected source rows exceed10000")
            if (
                len(distribution_plan(columns, layer, rows=rows, **clock_args)[2])
                > MAX_VIOLIN_PROFILES
            ):
                raise ValueError("advanced violin drawn profiles exceed256")
            early_rows = rows
    if layer.type == "boxenplot":
        from ._boxen import (
            MAX_BOXEN_CELLS,
            MAX_BOXEN_ROWS,
            advanced_boxen,
            boxen_option_issues,
        )
        from ._categorical import distribution_plan, sample_rows

        if advanced_boxen(layer):
            problems = boxen_option_issues(layer)
            if problems:
                raise ValueError("; ".join(problems))
            rows = sample_rows(columns, layer, category_matches=category_matches)
            if len(rows) > MAX_BOXEN_ROWS:
                raise ValueError(
                    "advanced boxen selected positive instances exceed10000"
                )
            if (
                len(distribution_plan(columns, layer, rows=rows, **clock_args)[2])
                > MAX_BOXEN_CELLS
            ):
                raise ValueError("advanced boxen drawn raw-tuple samplecells exceed256")
            early_rows = rows
    statistical = layer.type in STAT_LAYER_TYPES
    line_family = layer.type in {"line", "lineplot"}
    categorical = layer.type in _CATEGORICAL or categorical_strip(layer)
    univariate = layer.type in _UNIVARIATE
    oriented = (
        statistical
        or categorical
        or univariate
        or line_family
        or layer.type in FIELD_TYPES
        or (layer.type == "regplot" and layer.regression is not None)
    )
    horizontal = (oriented or layer.type == "rug") and layer.orient == "h"
    category_axis = category_axis_for(layer, panel) if horizontal else panel.x
    value_axis = panel.x if horizontal else panel.y2 if layer.axis == "y2" else panel.y
    if layer.type == "stem":
        from ._stem import stem_axes

        category_axis, value_axis = stem_axes(layer, panel)
    category_role = "x" if statistical or line_family else None
    response_role = "y"
    native_changes = {}
    native_clock = None
    if layer.type == "stairs" and panel.x.temporal is not None:
        native_clock = panel.x.temporal
        temporal_coordinates([], **temporal_options(native_clock))
        native_changes["bins"] = _temporal_bounds(layer.bins, native_clock)
    if (
        layer.type == "stackplot"
        and value_axis is not None
        and value_axis.temporal is not None
    ):
        raise ValueError("stacked sums cannot be temporal")
    if layer.type == "stairs":
        requests = [("x", value_axis)]
    elif layer.type == "rug":
        requests = [("x", category_axis)]
    elif layer.type in ("eventplot", "broken_barh"):
        requests = [("x", panel.x)]
    elif univariate:
        # The observation axis and mass/density axis are not interchangeable.
        if value_axis is not None and value_axis.temporal is not None:
            raise ValueError("mass/probability/density axes cannot be temporal")
        requests = [("x", category_axis)]
    elif categorical:
        category, _, _ = distribution_columns(layer)
        category_role = ("x" if layer.y else "group") if category is not None else None
        response_role = "y" if layer.y else "x"
        requests = [(response_role, value_axis)]
        if category_role is not None:
            requests.append((category_role, category_axis))
        elif category_axis is not None and category_axis.temporal is not None:
            raise ValueError("temporal categories require an explicit category column")
    else:
        requests = [("x", category_axis), ("y", value_axis)]
        if layer.type in ("bar", "errorbar", "band"):
            endpoints = ("y2",) if layer.type == "band" else ("y_lower", "y_upper")
            requests.extend(
                (role, value_axis)
                for role in endpoints
                if getattr(layer, role) is not None
            )
    requests = [
        (role, axis.temporal)
        for role, axis in requests
        if axis is not None and axis.temporal is not None
    ]
    if (
        layer.type == "boxenplot"
        and layer.weights is not None
        and any(getattr(layer, role) == layer.weights for role, _ in requests)
    ):
        raise ValueError("boxen weights cannot be a declared temporal coordinate")
    if not requests and not projection:
        return (
            columns,
            replace(layer, **native_changes) if native_changes else layer,
            None,
        )
    if panel.projection != "2d":
        raise ValueError("temporal axes require Cartesian 2-D projection")
    if layer.type in _LITERAL:
        for _, config in requests:
            temporal_coordinates([], **temporal_options(config))
        return columns, layer, None
    if layer.type not in TEMPORAL_LAYER_TYPES and not categorical:
        raise ValueError(
            f"temporal coordinates are not connected for {layer.type!r} yet"
        )
    names = [layer.x, layer.y, layer.group]
    if layer.type != "scatter" or layer.scalar_display is None:
        names.append(layer.c)
    if layer.type == "band":
        names.append(layer.y2)
    if layer.semantics is not None and layer.type != "regplot":
        names.extend(
            getattr(layer.semantics, role, None) for role in ("hue", "size", "style")
        )
    regression_weight = layer.weights if layer.type == "regplot" else None
    density_weight = weight_column(layer) if density else None
    if density_weight is not None:
        names.append(density_weight)
    if regression_weight is not None:
        names.append(regression_weight)
    needed = [name for name in names if isinstance(name, str) and name in columns]
    if any(not isinstance(columns[name], (list, tuple)) for name in needed):
        raise ValueError("temporal role columns must be sequences")
    selected_rows = None
    if layer.type == "stem":
        from ._stem import stem_rows

        selected_rows = set(stem_rows(columns, layer))
    elif density:
        assert density_selected is not None
        selected_rows = set(density_selected)
    elif line_family:
        if layer.type == "lineplot" and (
            layer.stat is not None and not isinstance(layer.stat, StatSpec)
        ):
            raise ValueError("stat must be a StatSpec")
        selected_rows = set(
            select_line_rows(columns, layer, panel, barriers=layer.type == "line")
        )
    elif statistical:
        if layer.stat is not None and not isinstance(layer.stat, StatSpec):
            raise ValueError("stat must be a StatSpec")
        # The same physical rows admit shape and feed the prepared coordinates.
        advanced = new_stat_request(layer, panel)
        selected_rows = set(
            early_rows
            if early_rows is not None
            else usable_rows(
                columns,
                layer if advanced else replace(layer, semantics=None),
                advanced=advanced,
                category_matches=category_matches,
            )
        )
    elif categorical:
        selected_rows = set(
            early_rows
            if early_rows is not None
            else distribution_rows(columns, layer, category_matches=category_matches)
        )
    elif univariate:
        legacy = (layer.type == "hist" and layer.histogram is None) or (
            layer.type == "kde" and layer.kde is None
        )
        if legacy:
            selected_rows = set(ecdf_rows(columns, replace(layer, ecdf=ECDFSpec())))
        else:
            selector = {"hist": histogram_rows, "kde": kde_rows, "ecdf": ecdf_rows}[
                layer.type
            ]
            selected_rows = set(selector(columns, layer))
    regression_roles = None
    if layer.type == "regplot" and isinstance(layer.regression, RegressionSpec):
        from ._regression import new_regression, regression_cohorts

        if new_regression(layer) or layer.orient == "h":
            cohorts = regression_cohorts(columns, layer)
            training = {row for cohort in cohorts for row in cohort.train}
            query = {row for cohort in cohorts for row in cohort.query}
            selected_rows = training | query
            regression_roles = (training, query)
    if (
        layer.hue_order is not None
        and regression_roles is None
        and not (
            statistical
            or categorical
            or univariate
            or line_family
            or layer.type in {"kde2d", "stem"}
        )
    ):
        tag = "__mudplot_temporal_rows"
        while tag in columns:
            tag += "_"
        size = len(columns[needed[0]]) if needed else 0
        selected_rows = set(
            ordered_group_columns({**columns, tag: list(range(size))}, layer)[tag]
        )
    if (
        layer.semantics is not None
        and not line_family
        and layer.type not in {"stem", "regplot"}
    ):
        semantic_selection = set(
            semantic_rows(columns, layer, category_matches=category_matches)
        )
        selected_rows = (
            semantic_selection
            if selected_rows is None
            else selected_rows & semantic_selection
        )
    result = dict(columns)
    changes = dict(native_changes)
    observation_mask = None
    sparse_rows = None
    if projection:
        sparse_rows = (
            density_selected
            if density
            else [
                i
                for i in range(len(columns.get(layer.x, ())))
                if selected_rows is None or i in selected_rows
            ]
        )
    for role, config in requests:
        temporal_options(config)
        name = getattr(layer, role)
        if not isinstance(name, str) or name not in columns:
            raise ValueError(f"temporal {role} requires an existing coordinate column")
        values = columns[name]
        if not isinstance(values, (list, tuple)):
            raise ValueError("temporal coordinate column must be a sequence")
        if any(len(columns[key]) != len(values) for key in needed):
            raise ValueError("temporal role columns must have the same length")
        error_field = "xerr" if role == "x" else "yerr" if role == "y" else None
        if layer.type == "regplot" and role == "y" and layer.regression is not None:
            regression = layer.regression
            if not isinstance(regression, RegressionSpec):
                raise ValueError("regression must be a RegressionSpec")
            if regression.residual or regression.model == "logistic":
                raise ValueError(
                    "calendar regression response cannot represent "
                    "residuals or probabilities"
                )
        if univariate or (categorical and role == response_role):
            if layer.type == "hist":
                if isinstance(layer.bins, str):
                    changes["bins"] = layer.bins
                    if layer.bins == "discrete":
                        selected = [
                            value
                            for i, value in enumerate(columns[layer.x])
                            if selected_rows is None or i in selected_rows
                        ]
                        edges = temporal_discrete_edges(
                            selected, **temporal_options(config)
                        )
                        if edges:
                            changes["bins"] = edges
                else:
                    changes["bins"] = _temporal_bounds(layer.bins, config)
            if layer.kde is not None:
                changes["kde"] = replace(
                    layer.kde,
                    clip=_temporal_bounds(layer.kde.clip, config, exact=exact_density),
                )
            if layer.clip is not None:
                changes["clip"] = _temporal_bounds(layer.clip, config)
        if statistical and role == response_role:
            if layer.type == "countplot":
                raise ValueError("count value axes cannot be temporal")
            if stat_config(layer).estimator not in ("mean", "median", "min", "max"):
                raise ValueError(
                    "temporal response supports mean/median/min/max, not sum/count"
                )
        if role == category_role:
            if layer.type not in {"line", "lineplot"}:
                changes["native_scale"] = True
            if resolved_order is not None:
                changes["order"] = resolved_order
        if sparse_rows is not None:
            converter = (
                exact_temporal_coordinates if exact_density else temporal_coordinates
            )
            selected = [
                None if is_missing(values[i]) else values[i] for i in sparse_rows
            ]
            if layer.type in FIELD_TYPES:
                density_temporal_options(
                    layer, changes, role, config, selected, exact=exact_density
                )
            alias = private_column(result, layer, f"__mudplot_temporal_{role}")
            result[alias] = ProjectedColumn(
                len(values),
                dict(
                    zip(
                        sparse_rows,
                        converter(selected, **temporal_options(config)),
                        strict=True,
                    )
                ),
            )
            changes[role] = alias
            continue
        observation_mask = [
            not any(
                is_missing(columns[key][i])
                for key in needed
                if not (line_family and key in {layer.x, layer.y})
                and not (
                    regression_roles is not None
                    and key == layer.y
                    and not getattr(layer.regression, "residual", False)
                    and i not in regression_roles[0]
                )
            )
            and (selected_rows is None or i in selected_rows)
            and (
                regression_weight is None
                or regression_weight not in columns
                or columns[regression_weight][i] != 0
            )
            for i in range(len(values))
        ]
        selected = [
            value if observation_mask[i] else None for i, value in enumerate(values)
        ]
        if layer.type in FIELD_TYPES:
            density_temporal_options(
                layer, changes, role, config, selected, exact=exact_density
            )
        alias = f"__mudplot_temporal_{role}"
        while alias in result:
            alias += "_"
        converter = (
            exact_temporal_coordinates if exact_density else temporal_coordinates
        )
        result[alias] = converter(selected, **temporal_options(config))
        changes[role] = alias
        if layer.type == "broken_barh" and role == "x":
            duration_alias = "__mudplot_temporal_duration"
            while duration_alias in result:
                duration_alias += "_"
            if not isinstance(layer.y, str) or layer.y not in columns:
                raise ValueError(
                    "temporal intervals require an existing duration column"
                )
            durations = columns[layer.y]
            if not isinstance(durations, (list, tuple)) or len(durations) != len(
                values
            ):
                raise ValueError("temporal duration column must have matching length")
            result[duration_alias] = temporal_durations(
                [
                    durations[i] if value is not None else None
                    for i, value in enumerate(selected)
                ],
                unit=config.unit or "day",
            )
            changes["y"] = duration_alias
        if error_field is not None and getattr(layer, error_field) is not None:
            error_name = getattr(layer, error_field)
            if not isinstance(error_name, str) or error_name not in columns:
                raise ValueError("temporal uncertainty requires an existing column")
            error_values = columns[error_name]
            if not isinstance(error_values, (list, tuple)) or len(error_values) != len(
                values
            ):
                raise ValueError(
                    "temporal uncertainty column must have matching length"
                )
            error_alias = f"__mudplot_temporal_{error_field}"
            while error_alias in result:
                error_alias += "_"
            result[error_alias] = temporal_durations(
                [
                    error_values[i] if value is not None else None
                    for i, value in enumerate(selected)
                ],
                unit=config.unit or "day",
            )
            changes[error_field] = error_alias
    if observation_mask is not None:
        for field in ("xerr", "yerr", "y_lower", "y_upper"):
            name = getattr(layer, field)
            if (
                name is None
                or field in changes
                or not isinstance(name, str)
                or name not in columns
            ):
                continue
            values = columns[name]
            if not isinstance(values, (list, tuple)) or len(values) != len(
                observation_mask
            ):
                raise ValueError(
                    "temporal uncertainty column must have matching length"
                )
            alias = f"__mudplot_temporal_{field}"
            while alias in result:
                alias += "_"
            result[alias] = [
                value if observation_mask[i] else None for i, value in enumerate(values)
            ]
            changes[field] = alias
    if (
        layer.type == "box"
        and layer.box is not None
        and layer.box.summary is not None
        and value_axis is not None
        and value_axis.temporal is not None
    ):
        result, summary = _summary_temporal_columns(
            columns, result, layer, selected_rows, value_axis.temporal
        )
        changes["box"] = replace(layer.box, summary=summary)
    prepared = replace(layer, **changes)
    if projection:
        rows = sparse_rows
        assert rows is not None
        moments = None
        if line_family:
            roles = [
                getattr(layer.semantics, role, None)
                for role in ("hue", "size", "style")
            ]
            complete = [
                i
                for i in rows
                if all(
                    not is_missing(columns[name][i])
                    for name in (layer.x, layer.y, *roles)
                    if name is not None
                )
            ]
            if layer.type == "line":
                rows = complete
            else:
                moments = complete
        result, prepared = project_layer(
            result,
            prepared,
            rows,
            moments,
            budget=field_budget,
        )
    return result, prepared, observation_mask


def _summary_temporal_columns(source, result, layer, selected_rows, clock):
    """All supplied endpoints are absolute values on the observation clock."""
    from ._box import MAX_BOX_FLIERS, summary_columns

    rows = set() if selected_rows is None else selected_rows
    summary = layer.box.summary
    total = 0
    if summary.fliers is not None and summary.fliers in source:
        for row in rows:
            values = source[summary.fliers][row]
            if values is not None:
                if not isinstance(values, (list, tuple)):
                    raise ValueError("declared fliers must be lists or unavailable")
                total += len(values)
                if total > MAX_BOX_FLIERS:
                    raise ValueError("box total declared flier value limit exceeded")
    changes = {}
    for role, name in summary_columns(layer, optional=True):
        if not isinstance(name, str) or name not in source:
            raise ValueError("summary temporal fields require existing columns")
        raw = source[name]
        alias = "__mudplot_temporal_box_" + role
        while alias in result:
            alias += "_"
        if role == "fliers":
            converted = [None] * len(raw)
            for row in rows:
                if raw[row] is not None:
                    converted[row] = temporal_coordinates(
                        raw[row], **temporal_options(clock)
                    )
        else:
            converted = temporal_coordinates(
                [value if index in rows else None for index, value in enumerate(raw)],
                **temporal_options(clock),
            )
        result[alias] = converted
        changes[role] = alias
    return result, replace(summary, **changes)
