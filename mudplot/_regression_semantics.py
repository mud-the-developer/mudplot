"""Pure raw-role admission for regression glyphs, never for model fitting."""

from ._components import _color
from ._ecdf import finite_number
from ._regression import (
    MAX_REGRESSION_ROWS,
    positive_regression_rows,
    regression_cohorts,
    regression_inputs,
)
from ._regression import (
    option_issues as regression_options,
)
from ._semantics import (
    MARKERS,
    MAX_CURVES,
    MAX_LEVELS,
    MAX_ROWS,
    categorical,
    category_key,
    option_issues,
    semantic_levels,
)
from ._stat import is_missing
from .spec import RegressionSpec, SemanticSpec

ROLES = ("hue", "size", "style")


def visibility(layer):
    config = layer.regression
    parts = config.components
    scatter = None if parts is None else parts.scatter
    fit = None if parts is None else parts.fit

    def visible(style):
        alpha = layer.alpha if style is None or style.alpha is None else style.alpha
        size = (
            layer.marker_size
            if style is None or style.marker_size is None
            else style.marker_size
        )
        marker = layer.marker if style is None or style.marker is None else style.marker
        return (
            alpha != 0
            and (layer.semantics.size is not None or size != 0)
            and (
                layer.semantics.style is not None or marker not in ("none", "None", "")
            )
        )

    return (
        (parts is None or parts.show_scatter) and visible(scatter),
        not config.residual and (parts is None or parts.show_fit) and visible(fit),
    )


def role_values(columns, config):
    """Compiled read-only access to physical role columns and their typed filters."""
    slots = []
    for role in ROLES:
        name = getattr(config, role)
        if name is None:
            continue
        if name not in columns or not isinstance(columns[name], (list, tuple)):
            raise ValueError(f"regression semantic {role} column {name!r} must exist")
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        order = getattr(config, f"{role}_order")
        allowed = None if order is None else {category_key(value) for value in order}
        slots.append((role, columns[name], kind, allowed))
    return slots


def eligible(slots, row):
    keep = True
    for role, values, kind, order in slots:
        if row >= len(values):
            raise ValueError(
                f"regression semantic source row {row}: {role} is not aligned"
            )
        value = values[row]
        if is_missing(value):
            keep = False
        elif kind == "numeric":
            if not finite_number(value):
                raise ValueError(
                    f"regression semantic source row {row}: numeric {role} needs "
                    "a finite number, not bool"
                )
        elif not categorical(value):
            raise ValueError(
                f"regression semantic source row {row}: invalid categorical {role}"
            )
        elif order is not None and category_key(value) not in order:
            keep = False
    return keep


def _science_glyph_rows(columns, layer, raw_columns, source_ids):
    """Get actual positive, visible cases with the existing R4 cohort owner."""
    show_obs, show_query = visibility(layer)
    slots = role_values(raw_columns, layer.semantics)
    obs, queries, batches = [], [], 0
    if not (show_obs or show_query):
        return obs, queries
    style = layer.semantics.style
    for cohort in regression_cohorts(columns, layer):
        train = positive_regression_rows(columns, cohort.train, layer.weights)
        if not train:
            continue
        query = positive_regression_rows(columns, cohort.query, layer.weights)
        observation = (
            query
            if layer.regression.residual and layer.regression.sampling is not None
            else train
        )
        for selected, destination, shown in (
            (observation, obs, show_obs),
            (query, queries, show_query),
        ):
            if not shown:
                continue
            styles = set()
            for row in selected:
                original = source_ids[row]
                if eligible(slots, original):
                    destination.append(original)
                    styles.add(
                        None
                        if style is None
                        else category_key(raw_columns[style][original])
                    )
                    if len(obs) + len(queries) > MAX_ROWS:
                        raise ValueError(
                            f"regression semantic glyphs exceed {MAX_ROWS} "
                            "selected rows"
                        )
            batches += len(styles)
            if batches > MAX_CURVES:
                raise ValueError(
                    f"regression semantic glyphs exceed {MAX_CURVES} native batches"
                )
    return obs, queries


def declaration_issues(layer, panel):
    config = layer.semantics
    issues = option_issues(config)
    if issues or not isinstance(config, SemanticSpec):
        return issues
    if not isinstance(layer.regression, RegressionSpec):
        return ["regression semantics requires a typed RegressionSpec"]
    if (
        panel.projection != "2d"
        or layer.axis not in ("y", "y2")
        or (layer.axis == "y2" and panel.y2 is None)
    ):
        issues.append(
            "regression semantic glyphs require Cartesian primary or enabled y2"
        )
    if config.dashes is not None:
        issues.append("regression semantic style maps point markers, not dashes")
    if layer.c is not None:
        issues.append("regression semantics does not accept legacy c")
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if type(layer.colorbar) is not bool or (
        (layer.colorbar or layer.clabel is not None) and not numeric_hue
    ):
        issues.append("regression semantic colorbar/clabel requires numeric hue")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append(
            "regression semantic clabel requires colorbar and a <=512-character string"
        )
    if layer.cmap_kind not in (
        ("sequential", "diverging") if numeric_hue else ("sequential",)
    ):
        issues.append("regression cmap_kind applies only to numeric hue")
    if layer.edge_color is not None and not _color(layer.edge_color):
        issues.append("regression semantic edge_color must be a bounded color")
    if layer.marker_size is not None and (
        not finite_number(layer.marker_size) or not 0 <= layer.marker_size <= 1000
    ):
        issues.append(
            "regression marker_size must be a finite diameter in [0,1000] points"
        )
    if layer.line_width is not None and (
        not finite_number(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append("regression outline line_width must be in [0,1000] points")
    return issues


def _component_issues(layer, *, show_obs, show_query):
    config = layer.semantics
    issues = []
    if show_obs or show_query:
        if config.style is not None and layer.marker is not None:
            issues.append("regression marker conflicts with mapped point style")
        if config.size is not None and layer.marker_size is not None:
            issues.append("regression marker_size conflicts with mapped point size")
    parts = layer.regression.components
    scatter = None if parts is None else parts.scatter
    fit = None if parts is None else parts.fit
    if config.hue is not None and config.style is None:
        for shown, component in ((show_obs, scatter), (show_query, fit)):
            marker = (
                layer.marker
                if component is None or component.marker is None
                else component.marker
            )
            if shown and marker is not None and marker not in MARKERS:
                issues.append(
                    "mapped regression face hue requires a named filled marker"
                )
                break
    if show_obs and scatter is not None:
        if config.hue is not None and (
            scatter.color is not None or scatter.face_color is not None
        ):
            issues.append(
                "regression.components.scatter color/face_color conflicts with "
                "mapped point hue"
            )
        if config.size is not None and scatter.marker_size is not None:
            issues.append(
                "regression.components.scatter marker_size conflicts with mapped "
                "point size"
            )
        if config.style is not None and scatter.marker is not None:
            issues.append(
                "regression.components.scatter marker conflicts with mapped point style"
            )
    # Fit stroke color/width/dash remain independent. Explicit marker traits
    # on that component historically also control its actual query glyphs.
    if show_query and fit is not None:
        if config.hue is not None and fit.face_color is not None:
            issues.append(
                "regression.components.fit face_color conflicts with mapped query hue"
            )
        if config.size is not None and fit.marker_size is not None:
            issues.append(
                "regression.components.fit marker_size conflicts with mapped query size"
            )
        if config.style is not None and fit.marker is not None:
            issues.append(
                "regression.components.fit marker conflicts with mapped query style"
            )
    return issues


def mapping_issues(columns, config, rows):
    issues = []
    for role in ROLES:
        if getattr(config, role) is None:
            continue
        if role == "style" or getattr(config, f"{role}_kind") == "categorical":
            levels = semantic_levels(columns, config, role, rows)
            if len(levels) > MAX_LEVELS or len({str(v) for v in levels}) != len(levels):
                issues.append(
                    f"regression semantic {role} levels exceed limit or have "
                    "ambiguous labels"
                )
            if role == "style" and len(levels) > len(config.markers):
                issues.append(
                    "regression semantic style levels require enough distinct markers"
                )
    return issues


def glyph_support(raw_columns, layer, panel):
    """Validate visual traits and return only drawable, original physical IDs."""
    problems = declaration_issues(layer, panel)
    if problems:
        return problems, []
    if regression_options(layer.regression, layer.degree, layer.confidence):
        return [], []  # The scientific owner reports invalid model declarations.
    try:
        from ._facet import panel_filter_issues

        if panel_filter_issues(raw_columns, panel):
            return [], []
        columns, working, ids = regression_inputs(raw_columns, panel, layer)
        if len(ids) > MAX_REGRESSION_ROWS:
            return [], []  # The R4 owner reports the row cap.
        obs, queries = _science_glyph_rows(columns, working, raw_columns, ids)
        rows = sorted(obs + queries)
        problems = _component_issues(
            layer, show_obs=bool(obs), show_query=bool(queries)
        )
        problems.extend(mapping_issues(raw_columns, layer.semantics, rows))
        return problems, rows
    except (ValueError, TypeError, KeyError, IndexError) as error:
        return [str(error)], []
