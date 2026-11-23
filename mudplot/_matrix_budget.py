"""Prospective NEW matrix reservations. No density accounting or RSS promise."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field

from ._cluster import advanced_cluster, common_features, named_fit
from ._field_budget import MAX_FIELD_VERTICES
from ._grid_field import prepare_grid, uses_grid
from ._heatmap import advanced_heatmap
from ._spatial import admit_spatial, uses_spatial
from ._tri_field import TRI_TYPES, admit_triangles
from ._vector import admit_vector, uses_vector
from .spec import ClusterSpec, HeatmapSpec

MAX_MATRIX_WORK = 838_860_800
MAX_MATRIX_MANAGED = 96 * 1024**2
MAX_MATRIX_SCIPY_FRAME = 16 * 1024**2

# Reservation weights, not claims about provider object sizes.
_AXES = 128 * 1024
_ARTIST = 16 * 1024
_TEXT = 8 * 1024
_LEGEND_ENTRY = 40 * 1024


@dataclass
class MatrixAdmission:
    work: int = 0
    retained: int = 0
    temporary: int = 0
    opaque_peak: int = 0
    active_frame: int = 0
    features: dict = field(default_factory=dict)
    layers: set = field(default_factory=set)
    grids: dict = field(default_factory=dict)
    triangles: dict = field(default_factory=dict)
    vectors: dict = field(default_factory=dict)
    spatial: set = field(default_factory=set)
    scalars: dict = field(default_factory=dict)
    native_geometry: dict = field(default_factory=dict)
    grid_vertices: int = 0
    grid_labels: int = 0

    def admit(self, work, retained=0, temporary=0):
        self.work += work
        self.retained += retained
        self.temporary = max(self.temporary, temporary)
        if self.work > MAX_MATRIX_WORK:
            raise ValueError("NEW matrix figure exceeds 838860800 work credits")
        if self.retained + self.temporary > MAX_MATRIX_MANAGED:
            raise ValueError("NEW matrix figure exceeds 96 MiB managed reservation")

    def admit_grid(self, grid):
        self.grid_vertices += grid.vertices
        self.grid_labels += grid.labels
        if self.grid_vertices > MAX_FIELD_VERTICES:
            raise ValueError("native grids exceed 2000000 prospective path vertices")
        if self.grid_labels > 4096:
            raise ValueError("native grids exceed 4096 prospective labels")
        self.admit(grid.work, grid.retained, grid.temporary)

    @contextmanager
    def scipy_frame(self, n):
        size = max(1024**2, 64 * n * n)
        if self.active_frame or size > MAX_MATRIX_SCIPY_FRAME:
            raise ValueError(
                "NEW matrix SciPy frame exceeds the serial 16 MiB reservation"
            )
        self.active_frame = size
        self.opaque_peak = max(self.opaque_peak, size)
        try:
            yield
        finally:
            self.active_frame = 0


def _array(elements, itemsize, copies=1):
    # Alignment and ndim 1..3 ndarray/header and short owner shells.
    return copies * (256 + elements * itemsize)


def _text_bytes(strings):
    return sum(3 * len(s.encode("utf-8")) for s in strings)


def _layer_admission(plan, panel, layer, matrix):
    cluster = layer.cluster or ClusterSpec() if layer.type == "clustermap" else None
    display = layer.heatmap or HeatmapSpec()
    rows, cols = len(matrix), len(matrix[0])
    cells = rows * cols
    # Before walking cell contents: visible image data plus explicit artist mask;
    # temporary conversion, gather, validity and native image copies.
    plan.admit(
        4 * cells,
        _ARTIST + _array(cells, 8) + _array(cells, 1),
        _array(cells, 8, 4) + _array(cells, 1, 6),
    )
    visible = visible_nulls = 0
    text = 0
    for i, row in enumerate(matrix):
        mask = display.mask[i] if display.mask is not None else None
        for j, value in enumerate(row):
            if mask is not None and mask[j]:
                continue
            if value is None:
                visible_nulls += 1
            else:
                visible += 1
                if display.annot and display.annot_data is not None:
                    text += 3 * len(display.annot_data[i][j].encode("utf-8"))
    if display.robust:
        plan.admit(2 * visible)
    if display.annot:
        plan.admit(visible, visible * _TEXT + text, _array(visible * 2, 8))
    if visible_nulls:
        plan.admit(
            visible_nulls,
            _ARTIST + _array(visible_nulls * 4, 8) + 256 * visible_nulls,
            _array(visible_nulls * 6, 8),
        )
    for count, labels, axis in (
        (cols, display.xlabels, panel.x),
        (rows, display.ylabels, panel.y),
    ):
        ticks = count if labels is not None or cluster is not None else 16
        if layer.line_width:
            ticks += count + 1
        for tick_spec in (axis.major_ticks, axis.minor_ticks):
            if tick_spec is not None:
                if tick_spec.locator is not None:
                    ticks += (
                        len(tick_spec.locator.values)
                        if tick_spec.locator.values is not None
                        else 512
                    )
                if (
                    tick_spec.formatter is not None
                    and tick_spec.formatter.labels is not None
                ):
                    text = _text_bytes(tick_spec.formatter.labels)
                    plan.admit(0, text)
        plan.admit(ticks, ticks * _TEXT + _text_bytes(labels or ()))
    if layer.colorbar:
        bar = display.colorbar_options
        ticks = len(bar.ticks) if bar is not None and bar.ticks is not None else 5
        bins = len(display.boundaries) - 1 if display.boundaries is not None else 256
        plan.admit(
            ticks + bins,
            _AXES + ticks * _TEXT + _ARTIST + _array(bins * 16, 8),
            _array(bins * 16, 8, 2),
        )
    if cluster is None:
        return
    if cluster.z_score or cluster.standard_scale:
        plan.admit(cells, temporary=_array(cells, 8, 6) + _array(cells, 1, 6))
    for index, (name, n, p) in enumerate((("row", rows, cols), ("col", cols, rows))):
        enabled = getattr(cluster, name + "_cluster") and n > 1
        tracks = getattr(cluster, name + "_tracks") or ()
        legacy = getattr(cluster, name + "_colors") is not None
        cut = getattr(cluster, name + "_cut")
        tree = getattr(cluster, name + "_linkage")
        external = getattr(cluster, name + "_distances")
        if enabled:
            plan.admit(n, _AXES + _ARTIST + _array((n - 1) * 8, 8) + 256 * (n - 1))
            pairs = n * (n - 1) // 2
            fit = named_fit(cluster, name, n)
            build, optimal = tree is None, cluster.optimal_ordering
            if fit and cluster.missing == "complete_features":
                features = common_features(matrix, name)
                plan.features[id(layer), index] = features
                p = len(features)
            work = pairs * p if fit else pairs if external is not None else 0
            work += 4 * n * n * (build + optimal)
            work += n**3 * (
                optimal + (build and cluster.method in ("median", "centroid"))
            )
            temp = _array(cells, 8, 4) + _array(cells, 1, 6) + _array((n - 1) * 4, 8, 3)
            if fit or external is not None:
                temp += _array(pairs, 8, 2) + _array(n * p, 8, 2)
            plan.admit(work, _array((n - 1) * 4, 8), temp)
            if cut is not None:
                plan.admit(n, _ARTIST * 2 + _array(n * 8, 8) + 384 * n + _TEXT)
        if tracks or legacy:
            plan.admit(
                n if legacy else 0,
                _AXES + (_ARTIST + _array(n * 4, 8) if legacy else 0),
            )
        for track in tracks:
            entries = len(track.levels)
            plan.admit(
                n + entries,
                _ARTIST + _array(4 * n, 1) + _array(entries * 4, 1),
                _array(n, 8) + _array(4 * n, 1, 2),
            )
            if track.legend is not False:
                plan.admit(
                    entries,
                    _ARTIST
                    + _TEXT
                    + entries * _LEGEND_ENTRY
                    + _text_bytes(
                        [track.title, *(level.label for level in track.levels)]
                    ),
                )
    if visible_nulls or any(
        track.legend is not False
        for tracks in (cluster.row_tracks, cluster.col_tracks)
        for track in tracks or ()
    ):
        plan.admit(1, _AXES + (_LEGEND_ENTRY if visible_nulls else 0))


def matrix_admission(spec):
    """Prospective aggregate admission from borrowed, already validated inputs."""
    plan = MatrixAdmission()
    from ._native_geometry import extended_geometry, prepare, reserve
    from ._scalar_display import scalar_plans

    plan.scalars = scalar_plans(spec, plan)
    for panel in spec.panels:
        for layer in panel.layers:
            if layer.path_effects is not None or extended_geometry(layer):
                reserve(plan, spec.data.columns, layer)
            if extended_geometry(layer):
                from ._facet import panel_rows

                columns = spec.data.columns
                selected = (
                    panel_rows(columns, panel)
                    if panel.filters or panel.dropna
                    else None
                )
                plan.native_geometry[id(layer)] = prepare(
                    columns, layer, panel, selected
                )
            elif uses_grid(layer):
                grid = prepare_grid(spec.data.matrices, layer, panel)
                plan.admit_grid(grid)
                plan.grids[id(layer)] = grid
            elif layer.type in TRI_TYPES:
                plan.triangles[id(layer)] = admit_triangles(
                    plan, spec.data.columns, layer, panel
                )
            elif uses_vector(layer):
                from ._facet import panel_rows

                plan.vectors[id(layer)] = admit_vector(
                    plan,
                    spec,
                    layer,
                    panel,
                    spec.data.columns,
                    panel_rows(spec.data.columns, panel)
                    if panel.filters or panel.dropna
                    else None,
                )
            elif uses_spatial(layer):
                admit_spatial(plan, spec, panel, layer)
                plan.spatial.add(id(layer))
            elif layer.type in ("heatmap", "clustermap") and (
                advanced_heatmap(layer.heatmap) or advanced_cluster(layer.cluster)
            ):
                plan.layers.add(id(layer))
                _layer_admission(plan, panel, layer, spec.data.matrices[layer.matrix])
    return (
        plan
        if (
            plan.layers
            or plan.grids
            or plan.triangles
            or plan.vectors
            or plan.spatial
            or plan.scalars
            or plan.native_geometry
        )
        else None
    )
