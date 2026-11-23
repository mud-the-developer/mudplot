"""C02 native glyphs, physical instances, axes and redraw lifecycle."""

import io
import warnings
import xml.etree.ElementTree as ET

import mudplot as mp
import numpy as np
import pytest
from matplotlib.markers import MarkerStyle
from matplotlib.path import Path
from mudplot.spec import LayerSpec


def canonical(marker):
    style = MarkerStyle(marker)
    return style.get_path().transformed(style.get_transform())


def assert_paths(collection, names):
    actual = collection.get_paths()
    for index, name in enumerate(names):
        reference = canonical(name)
        np.testing.assert_array_equal(
            actual[index % len(actual)].vertices, reference.vertices
        )
        np.testing.assert_array_equal(
            actual[index % len(actual)].codes, reference.codes
        )


def native_instances(ax, collections, names):
    points, radii = [], []
    for collection, markers in zip(collections, names, strict=True):
        offsets = np.asarray(collection.get_offsets())
        points.extend(ax.transData.transform(offsets))
        areas = np.resize(collection.get_sizes(), len(offsets))
        widths = np.resize(collection.get_linewidths(), len(offsets))
        for marker, area, width in zip(markers, areas, widths, strict=True):
            box = canonical(marker).get_extents()
            radius = (
                0.5
                if marker == "o"
                else np.hypot(
                    max(abs(box.x0), abs(box.x1)), max(abs(box.y0), abs(box.y1))
                )
            )
            radii.append((radius * np.sqrt(area) + width / 2) * ax.figure.dpi / 72)
    return np.asarray(points), np.asarray(radii)


def assert_clear(ax, collections, names):
    points, radii = native_instances(ax, collections, names)
    pairs = np.triu_indices(len(points), 1)
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=2)
    required = radii[:, None] + radii[None, :]
    assert np.all(distances[pairs] >= required[pairs] - 1e-6)
    return points, radii


@pytest.mark.parametrize(
    "marker", ["o", "s", "D", "^", "v", "P", "X", "d", "p", "h", "8", "*"]
)
@pytest.mark.parametrize("orient", ["v", "h"])
def test_named_scalar_paths_and_strokes_match_native_glyphs(marker, orient):
    values = [1, 1, 1.001, 1.001, 1.01, 1.01]
    p = (
        mp.plot({"c": ["A"] * 6, "v": values})
        .swarmplot(
            "c",
            "v",
            marker=marker,
            marker_size=7,
            line_width=1.5,
            orient=orient,
        )
        .size(8, 5)
    )
    fig = p.render()
    ax = fig.axes[0]
    collection = ax.collections[0]
    assert_paths(collection, [marker] * 6)
    np.testing.assert_array_equal(collection.get_sizes(), [49])
    for dpi in [72, 300]:
        fig.set_dpi(dpi)
        fig.canvas.draw()
        points, radii = assert_clear(ax, [collection], [[marker] * 6])
        np.testing.assert_array_equal(
            np.asarray(collection.get_offsets())[:, 0 if orient == "h" else 1], values
        )
        category = int(orient == "h")
        low, high = ax.transData.transform(
            ([-0.4, 1], [0.4, 1]) if orient == "v" else ([1, -0.4], [1, 0.4])
        )[:, category]
        assert np.all(points[:, category] - radii >= min(low, high) - 1e-6)
        assert np.all(points[:, category] + radii <= max(low, high) + 1e-6)


def test_declared_members_keep_duplicate_instances_and_unscoped_layer_independence():
    data = {"c": ["A"] * 4, "v": [1] * 4, "s": [1, 2, 1, 2], "d": ["a", "b", "a", "b"]}
    config = {
        "size": "s",
        "sizes": [3, 7],
        "style": "d",
        "markers": ["s", "D"],
        "scale_id": "rows",
    }
    p = mp.plot(data).size(10, 6)
    p.swarmplot("c", "v", semantics=config, pack_scope="joint")
    p.swarmplot("c", "v", semantics=config, pack_scope="joint")
    p.swarmplot("c", "v", semantics=config)
    fig = p.render()
    ax = fig.axes[0]
    first, second, independent = ax.collections
    for collection in ax.collections:
        np.testing.assert_array_equal(
            np.asarray(collection.get_offsets())[:, 1], data["v"]
        )
        np.testing.assert_array_equal(collection.get_sizes(), [9, 49, 9, 49])
        assert_paths(collection, ["s", "D", "s", "D"])
    assert_clear(ax, [first, second], [["s", "D", "s", "D"]] * 2)
    # Same raw rows are drawn twice, not deduplicated into one physical member.
    assert len(first.get_offsets()) + len(second.get_offsets()) == 8
    assert not np.array_equal(first.get_offsets(), second.get_offsets())
    baseline = mp.plot(data).size(10, 6).swarmplot("c", "v", semantics=config)
    reference = baseline.render().axes[0].collections[0]
    np.testing.assert_allclose(
        independent.get_offsets(), reference.get_offsets(), atol=1e-12
    )
    assert p.spec.data.columns == data


@pytest.mark.parametrize(
    "orient,axis,category_kind,value_kind",
    [
        ("v", "y", "ordinal", "numeric"),
        ("h", "y", "log", "log"),
        ("v", "y2", "date", "log"),
        ("h", "y2", "date", "numeric"),
        ("v", "y2", "log", "date"),
        ("h", "y2", "log", "date"),
        ("v", "y", "date", "date"),
    ],
)
def test_joint_native_date_log_y2_redraws_keep_measurements_and_rng(
    orient, axis, category_kind, value_kind
):
    category = (
        ["A"] * 4
        if category_kind == "ordinal"
        else [10] * 4
        if category_kind == "log"
        else ["2026-01-01"] * 4
    )
    values = (
        [1, 1, 1.001, 1.001]
        if value_kind != "date"
        else ["2026-02-01", "2026-02-01", "2026-02-02", "2026-02-02"]
    )
    expected = values if value_kind != "date" else [20485, 20485, 20486, 20486]
    data = {
        "c": category,
        "v": values,
        "d": ["a", "b"] * 2,
        "id": ["r4", "r2", "r1", "r3"],
    }
    state = np.random.get_state()
    p = mp.plot(data).size(10, 6)
    if axis == "y2":
        p.secondary_yaxis("Observed")
    category_axis = "x" if orient == "v" else axis
    value_axis = axis if orient == "v" else "x"
    for name, kind in [(category_axis, category_kind), (value_axis, value_kind)]:
        if kind == "date":
            p.date_axis(name, timezone="UTC")
        elif kind == "log":
            p.dispatch(mp.actions.SetScale(name, "log"))
    config = {"style": "d", "markers": ["s", "^"]}
    for _ in range(2):
        p.swarmplot(
            "c",
            "v",
            orient=orient,
            axis=axis,
            native_scale=category_kind != "ordinal",
            pack_scope="s",
            semantics=config,
        )
    fig = p.render()
    ax = fig.axes[int(axis == "y2")]
    for dpi, size in [(72, (10, 6)), (300, (12, 7)), (72, (10, 6))]:
        fig.set_dpi(dpi)
        fig.set_size_inches(*size)
        fig.canvas.draw()
        assert_clear(ax, ax.collections, [["s", "^"] * 2] * 2)
        for collection in ax.collections:
            np.testing.assert_array_equal(
                np.asarray(collection.get_offsets())[:, 0 if orient == "h" else 1],
                expected,
            )
        first = [np.asarray(c.get_offsets()).copy() for c in ax.collections]
        fig.canvas.draw()
        for collection, before in zip(ax.collections, first, strict=True):
            np.testing.assert_allclose(collection.get_offsets(), before, atol=1e-12)
    ax.invert_xaxis()
    ax.invert_yaxis()
    fig.canvas.draw()
    assert_clear(ax, ax.collections, [["s", "^"] * 2] * 2)
    assert p.spec.data.columns == data
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


@pytest.mark.parametrize("mode", ["scope", "style"])
@pytest.mark.parametrize(
    "order,column,expected",
    [
        ([True], "c", [1]),
        ([1], "c", [2]),
        ([False], "c", [3]),
        ([0], "c", [4]),
        ([True], "g", [1]),
    ],
)
def test_advanced_orders_distinguish_boolean_and_numeric_cell_identities(
    mode, order, column, expected
):
    data = {
        "c": [True, 1, False, 0] if column == "c" else ["a"] * 4,
        "v": [1, 2, 3, 4],
        "g": [True, 1, False, 0],
        "shape": ["a"] * 4,
    }
    options = (
        {"pack_scope": "s"} if mode == "scope" else {"semantics": {"style": "shape"}}
    )
    if column == "c":
        options["order"] = order
    else:
        options.update(group="g", hue_order=order)
    p = mp.plot(data).swarmplot("c", "v", **options)
    collection = p.render().axes[0].collections[0]
    np.testing.assert_array_equal(np.asarray(collection.get_offsets())[:, 1], expected)


@pytest.mark.parametrize("operation", ["hide", "remove", "move"])
def test_native_membership_changes_repack_only_drawn_axes_members(operation):
    data = {"c": ["a"] * 4, "v": [1, 1, 1.01, 1.01]}
    p = mp.plot(data).size(10, 5).layout(1, 2)
    for _ in range(2):
        p.swarmplot("c", "v", marker="s", pack_scope="s", panel=0)
    fig = p.render()
    ax, other = fig.axes
    survivor, member = ax.collections
    if operation == "hide":
        member.set_visible(False)
    else:
        member.remove()
        if operation == "move":
            other.add_collection(member)
            other.set_xlim(-0.5, 0.5)
            other.set_ylim(ax.get_ylim())
    fig.canvas.draw()
    reference = (
        mp.plot(data)
        .size(10, 5)
        .layout(1, 2)
        .swarmplot("c", "v", marker="s")
        .render()
        .axes[0]
    )
    actual = ax.transData.transform(survivor.get_offsets())[:, 0]
    expected = reference.transData.transform(reference.collections[0].get_offsets())[
        :, 0
    ]
    actual -= ax.transData.transform([[0, 1]])[0, 0]
    expected -= reference.transData.transform([[0, 1]])[0, 0]
    np.testing.assert_allclose(actual, expected, atol=1e-8)
    assert_clear(ax, [survivor], [["s"] * 4])
    if operation == "move":
        assert_clear(other, [member], [["s"] * 4])
        np.testing.assert_array_equal(np.asarray(member.get_offsets())[:, 1], data["v"])


def test_shared_native_path_edits_and_size_linewidth_cycles_repack_fresh_geometry():
    p = (
        mp.plot({"c": ["a"] * 4, "v": [1] * 4})
        .swarmplot("c", "v", marker="s")
        .size(10, 6)
    )
    fig = p.render()
    ax = fig.axes[0]
    collection = ax.collections[0]
    path = canonical("s")
    mutable = Path(path.vertices.copy(), path.codes)
    collection.set_paths([mutable] * 4)
    collection.set_sizes([16, 36])
    collection.set_linewidth([0, 1])
    fig.canvas.draw()
    initial = np.asarray(collection.get_offsets()).copy()
    mutable.vertices[:, 0] *= 2
    fig.canvas.draw()
    points = ax.transData.transform(collection.get_offsets())
    box = mutable.get_extents()
    radius = np.hypot(max(abs(box.x0), abs(box.x1)), max(abs(box.y0), abs(box.y1)))
    radii = (
        (
            np.sqrt(np.resize(collection.get_sizes(), 4)) * radius
            + np.resize(collection.get_linewidths(), 4) / 2
        )
        * fig.dpi
        / 72
    )
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=2)
    pairs = np.triu_indices(4, 1)
    assert np.all(distances[pairs] >= (radii[:, None] + radii[None, :])[pairs] - 1e-6)
    assert np.ptp(np.asarray(collection.get_offsets())[:, 0]) > np.ptp(initial[:, 0])
    np.testing.assert_array_equal(np.asarray(collection.get_offsets())[:, 1], [1] * 4)


def test_scope_budget_counts_duplicate_physical_rows_and_rejects_before_output(
    tmp_path,
):
    n = 2000
    data = {"c": ["a"] * n, "v": list(range(n)), "one": [1] + [None] * (n - 1)}
    p = mp.plot(data).size(6, 12)
    for _ in range(2):
        p.swarmplot("c", "v", marker_size=1, line_width=0, pack_scope="s")
    ax = p.render().axes[0]
    assert sum(len(c.get_offsets()) for c in ax.collections) == 4000
    p.swarmplot("c", "one", pack_scope="s")
    output = tmp_path / "keep.png"
    output.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="4000"):
        p.save(str(output))
    assert output.read_bytes() == b"previous output"


@pytest.mark.parametrize(
    "change",
    [
        {"orient": "h"},
        {"width": 0.6},
        {"gap": 0.2},
        {"dodge": 0},
        {"axis": "y2"},
        {"x": "other"},
    ],
)
def test_incompatible_declared_members_reject_instead_of_splitting(change):
    data = {"c": ["a", "a"], "other": ["a", "a"], "v": [1, 1]}
    p = mp.plot(data).secondary_yaxis("Other").swarmplot("c", "v", pack_scope="s")
    layer = p.spec.panels[0].layers[0].to_dict()
    layer.update(change)
    p.dispatch(mp.actions.AddLayer(LayerSpec.from_dict(layer)))
    with pytest.raises(ValueError):
        p.render()


def test_overcrowded_named_glyphs_keep_rows_measurements_and_native_svg_instances():
    p = mp.plot({"c": ["a"] * 8, "v": [1] * 8}).size(3, 2)
    for marker in ["s", "D"]:
        p.swarmplot(
            "c",
            "v",
            marker=marker,
            marker_size=12,
            width=0.1,
            pack_scope="s",
            warn_thresh=0,
        )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = p.render()
    crowded = [collection.crowded_count for collection in fig.axes[0].collections]
    assert all(0 < count <= 8 for count in crowded)
    assert sum(issubclass(w.category, UserWarning) for w in caught) == len(crowded)
    with warnings.catch_warnings(record=True) as repeated:
        warnings.simplefilter("always")
        fig.canvas.draw()
    assert not any(issubclass(w.category, UserWarning) for w in repeated)
    for i, collection in enumerate(fig.axes[0].collections):
        np.testing.assert_array_equal(
            np.asarray(collection.get_offsets())[:, 1], [1] * 8
        )
        collection.set_gid(f"observations-{i}")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="svg")
    document = ET.fromstring(buffer.getvalue())
    for i in range(2):
        group = next(
            node
            for node in document.iter()
            if node.attrib.get("id") == f"observations-{i}"
        )

        def drawn_geometry(node):
            tag = node.tag.rsplit("}", 1)[-1]
            if tag in {"defs", "clipPath"}:
                return 0
            own = int(tag in {"use", "path", "circle", "ellipse", "polygon"})
            return own + sum(drawn_geometry(child) for child in node)

        assert drawn_geometry(group) == 8


@pytest.mark.parametrize("family", ["swarm", "strip"])
@pytest.mark.parametrize("orient,axis", [("v", "y"), ("h", "y"), ("h", "y2")])
def test_single_temporal_category_declared_slot_has_origin_independent_native_extent(
    family, orient, axis
):
    def render_category(when):
        p = mp.plot({"c": [when], "v": [1]}).size(8, 4)
        if axis == "y2":
            p.secondary_yaxis("Category")
        if family == "strip":
            p.stripplot(
                "c", "v", orient=orient, axis=axis, strip={"jitter_policy": "none"}
            )
        else:
            p.swarmplot("c", "v", orient=orient, axis=axis)
        p.date_axis("x" if orient == "v" else axis, timezone="UTC")
        return p.render().axes[int(axis == "y2")]

    ax = render_category("2026-01-01")
    reference = render_category("1970-01-01")
    bounds = ax.get_xlim() if orient == "v" else ax.get_ylim()
    origin_bounds = reference.get_xlim() if orient == "v" else reference.get_ylim()
    np.testing.assert_allclose(
        np.asarray(bounds) - 20454, origin_bounds, rtol=0, atol=1e-9
    )
    measurement = 1 if orient == "v" else 0
    for target in [ax, reference]:
        np.testing.assert_array_equal(
            np.asarray(target.collections[0].get_offsets())[:, measurement], [1]
        )
    np.testing.assert_allclose(
        np.asarray(ax.collections[0].get_offsets())[:, int(orient == "h")],
        [20454],
        rtol=0,
        atol=1e-10,
    )


@pytest.mark.parametrize("orient,axis", [("v", "y"), ("v", "y2"), ("h", "y2")])
def test_temporal_slot_bounds_do_not_contaminate_coexisting_measurement_limits(
    orient, axis
):
    data = {"date": ["2026-01-01"] * 2, "value": [100, 200]}
    base = mp.plot(data).size(8, 5)
    if axis == "y2":
        base.secondary_yaxis("Observed")
    base.line(
        "date" if orient == "v" else "value",
        "value" if orient == "v" else "date",
        axis=axis,
    )
    base.date_axis("x" if orient == "v" else axis, timezone="UTC")
    p = mp.Plot.from_json(base.to_json()).swarmplot(
        "date", "value", orient=orient, axis=axis
    )
    reference, ax = (
        base.render().axes[int(axis == "y2")],
        p.render().axes[int(axis == "y2")],
    )
    measurement = 1 if orient == "v" else 0
    np.testing.assert_array_equal(
        ax.dataLim.get_points()[:, measurement],
        reference.dataLim.get_points()[:, measurement],
    )
    assert (ax.get_ylim() if orient == "v" else ax.get_xlim()) == (
        reference.get_ylim() if orient == "v" else reference.get_xlim()
    )


def test_six_families_share_row_domains_colours_and_mark_specific_physical_units():
    data = {
        "c": ["a"] * 8,
        "x": [0, 1, 2, 3] * 2,
        "v": [1, 1, 2, 2, 3, 3, 4, 4],
        "h": [-1, -1, 1, 1] * 2,
        "m": [1, 3] * 4,
        "d": ["A", "B"] * 4,
        "id": list(range(8)),
    }
    config = {
        "scale_id": "all",
        "hue": "h",
        "hue_kind": "numeric",
        "size": "m",
        "sizes": [3, 7],
        "style": "d",
        "markers": ["s", "D"],
    }
    p = mp.plot(data).size(15, 9).layout(2, 3)
    common = {"semantics": config, "colorbar": True}
    p.swarmplot("c", "v", pack_scope="joint", panel=0, **common)
    p.swarmplot("c", "v", pack_scope="joint", panel=0, **common)
    p.scatter("x", "v", panel=1, **common)
    p.lineplot("x", "v", errorbar=None, panel=2, **common)
    p.stripplot("c", "v", strip={"jitter_policy": "none"}, panel=3, **common)
    p.ecdf("v", panel=4, **common)
    p.rug("v", panel=5, **common)
    fig = p.render()
    panels = [ax for ax in fig.axes if ax.get_label() != "<colorbar>"]
    swarm, scatter, lines, strip, ecdf, rug = panels
    first = swarm.collections[0]
    np.testing.assert_array_equal(first.get_sizes(), [9, 49] * 4)
    assert_paths(first, ["s", "D"] * 4)
    for index, marker in enumerate(["s", "D"]):
        selected = np.array(
            [i for i, value in enumerate(data["d"]) if value == ["A", "B"][index]]
        )
        np.testing.assert_allclose(
            first.get_facecolors()[selected],
            scatter.collections[index].get_facecolors(),
        )
        np.testing.assert_allclose(
            first.get_facecolors()[selected], strip.collections[index].get_facecolors()
        )
        np.testing.assert_array_equal(
            scatter.collections[index].get_sizes(), [9 if index == 0 else 49] * 4
        )
        for ax in [lines, ecdf]:
            observed = [
                line
                for line in ax.lines
                if len(line.get_xdata()) and line.get_marker() == marker
            ]
            assert {line.get_linewidth() for line in observed} == {
                3 if index == 0 else 7
            }
    np.testing.assert_array_equal(rug.collections[0].get_linewidths(), [3, 7] * 4)
    np.testing.assert_allclose(first.get_facecolors(), rug.collections[0].get_colors())
    assert len([ax for ax in fig.axes if ax.get_label() == "<colorbar>"]) == 6
    assert p.spec.data.columns == data and mp.apply(p.action_log) == p.spec


def test_mixed_family_domain_row_bound_deduplicates_ids_not_physical_instances():
    n = 9000
    data = {
        "c": ["a"] * n,
        "x": list(range(n)),
        "v": list(range(n)),
        "swarm": list(range(1000)) + [None] * (n - 1000),
        "size": [1] * n,
    }
    config = {"size": "size", "sizes": [0.5, 1], "scale_id": "rows"}
    p = mp.plot(data).size(12, 5).layout(1, 2)
    for _ in range(2):
        p.swarmplot("c", "swarm", semantics=config, pack_scope="instances", panel=0)
    p.scatter("x", "v", semantics=config, panel=1)
    fig = p.render()
    assert [len(c.get_offsets()) for c in fig.axes[0].collections] == [1000, 1000]
    assert len(fig.axes[1].collections[0].get_offsets()) == n
    np.testing.assert_array_equal(
        fig.axes[0].collections[0].get_sizes(), [0.75**2] * 1000
    )
