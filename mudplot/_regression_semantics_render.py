"""Native point-only application of the shared raw semantic mappings."""

from collections import defaultdict

import numpy as np
from matplotlib.lines import Line2D

from ._regression_semantics import ROLES, eligible, role_values, visibility
from ._scatter_semantics import draw_semantic_colourbar, marker_areas
from ._semantics import (
    MARKERS,
    categorical_fractions,
    category_key,
    numeric_mapping,
    semantic_levels,
)
from ._shared_guides import tag_entry

_FAMILIES = {
    "observation": "regression observations",
    "adjusted_observation": "adjusted regression observations",
    "query_mean_prediction": "query fitted responses",
    "diagnostic": "regression diagnostics",
}


class RegressionGlyphs:
    """Calibrate once across actual glyphs; no fitted values enter the mapping."""

    def __init__(self, ax, prepared, layer, columns, color_iter, domain):
        from ._render import _continuous_cmap

        self.ax = ax
        self.layer = layer
        self.config = config = layer.semantics
        self.raw = columns
        self.batches = {}
        self.traits = {}
        self.guide_targets = {}
        self.seen = set()
        self.observation_role = (
            "diagnostic"
            if layer.regression.residual
            else "adjusted_observation"
            if layer.regression.partial is not None
            else "observation"
        )
        show_obs, show_query = visibility(layer)
        slots = role_values(columns, config)
        by_role = defaultdict(set)
        for index, curve in enumerate(prepared.curves):
            for kind, shown, ids in (
                (self.observation_role, show_obs, curve.observation_rows),
                ("query_mean_prediction", show_query, curve.query_rows),
            ):
                if not shown:
                    continue
                kept = [(i, row) for i, row in enumerate(ids) if eligible(slots, row)]
                if kept:
                    self.batches[index, kind] = kept
                    by_role[kind].update(row for _, row in kept)
        if not by_role:
            return
        rows = sorted(set().union(*by_role.values()))
        mapping = rows if domain is None else domain["rows"]
        for role in ROLES:
            column = getattr(config, role)
            if column is None:
                continue
            raw = columns[column]
            kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
            vals = [raw[row] for row in rows]
            if kind == "categorical":
                levels = semantic_levels(columns, config, role, mapping)
                keys = [category_key(value) for value in levels]
                if role == "hue":
                    if domain is None:
                        mapped = [next(color_iter) for _ in levels]
                    else:
                        import matplotlib.pyplot as plt

                        palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
                        start = domain["offset"]
                        mapped = palette[start : start + len(levels)]
                elif role == "style":
                    mapped = config.markers
                else:
                    mapped = self._diameters(categorical_fractions(levels, levels))
                lookup = dict(zip(keys, mapped[: len(keys)], strict=True))
                traits = [lookup[category_key(value)] for value in vals]
            else:
                _, bounds = numeric_mapping(
                    [raw[row] for row in mapping], getattr(config, f"{role}_norm")
                )
                fractions, _ = numeric_mapping(vals, bounds)
                if role == "hue":
                    cmap = _continuous_cmap(layer.cmap_kind)
                    traits = cmap(fractions)
                    draw_semantic_colourbar(ax, layer, bounds, cmap)
                else:
                    traits = self._diameters(fractions)
            self.traits[role] = dict(zip(rows, traits, strict=True))
            if not config.legend or (
                role == "hue" and kind == "numeric" and layer.colorbar
            ):
                continue
            for effect, live in by_role.items():
                values = [raw[row] for row in live]
                if kind == "numeric":
                    values = [min(values), max(values)]
                self.guide_targets[effect, role] = {
                    category_key(value) for value in values
                }

    def _diameters(self, fractions):
        low, high = self.config.sizes
        return [low * (1 - t) + high * t for t in fractions]

    def draw(self, index, kind, xy, *, face, edge, edgewidth, diameter, marker, alpha):
        kept = self.batches.get((index, kind))
        if not kept:
            return
        hue, size, style = (self.traits.get(role) for role in ROLES)
        if hue is not None and style is None and marker not in MARKERS:
            marker = "o"  # Only an implicit theme fallback reaches this case.
        batches = defaultdict(list)
        for i, row in kept:
            batches[marker if style is None else style[row]].append((i, row))
        for glyph, selected in batches.items():
            indices, rows = zip(*selected, strict=True)
            indices = list(indices)
            diameters = np.asarray(
                [diameter if size is None else size[row] for row in rows], dtype=float
            )
            areas = marker_areas(diameters)
            colors = face if hue is None else [hue[row] for row in rows]
            native = self.ax.scatter(
                xy[0][indices],
                xy[1][indices],
                s=areas,
                marker=glyph,
                facecolors=colors,
                edgecolors=edge,
                linewidths=edgewidth,
                alpha=alpha,
                label="_nolegend_",
            )
            native._mudplot_source_rows = rows
            native._mudplot_regression_role = kind
            self._guides(native, rows, diameters, glyph, kind, edge is not None)

    def _guides(self, native, rows, diameters, glyph, effect, fixed_edge):
        if not self.guide_targets:
            return
        faces, edges, widths = (
            native.get_facecolors(),
            native.get_edgecolors(),
            native.get_linewidths(),
        )
        family = _FAMILIES[effect]
        for role in ROLES:
            targets = self.guide_targets.get((effect, role))
            if not targets:
                continue
            column = getattr(self.config, role)
            for i, row in enumerate(rows):
                if not diameters[i]:
                    # A zero endpoint can calibrate but cannot supply a glyph key.
                    continue
                value = self.raw[column][row]
                key = category_key(value)
                if key not in targets or (effect, role, key) in self.seen:
                    continue
                self.seen.add((effect, role, key))
                face = faces[min(i, len(faces) - 1)] if len(faces) else "none"
                edge = edges[min(i, len(edges) - 1)] if len(edges) else "none"
                width = widths[min(i, len(widths) - 1)]
                label = (
                    f"{role} "
                    f"({family}{'; marker diameter, pt' if role == 'size' else ''}): "
                    f"{column}={value}"
                )
                # This legend key copies a visible native point, not its data.

                handle = Line2D(
                    [],
                    [],
                    color=face,
                    linestyle="None",
                    linewidth=0,
                    marker=glyph,
                    markersize=diameters[i],
                    markerfacecolor=face,
                    markeredgecolor=edge,
                    markeredgewidth=width,
                    alpha=native.get_alpha(),
                    label=label,
                )
                self.ax.add_line(handle)
                tag_entry(
                    self.ax,
                    handle,
                    self.layer,
                    role,
                    value,
                    context={
                        "family": family,
                        "color": face,
                        "edgecolor": edge,
                        "edge_fixed": fixed_edge,
                        "edgewidth": width,
                        "diameter": diameters[i],
                        "marker": glyph,
                        "width": 0,
                        "dash": "None",
                        "alpha": native.get_alpha(),
                    },
                )
