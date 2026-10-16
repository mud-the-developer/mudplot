"""Independent mappings, paired rows, non-data guides and old scatter regression."""

from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.markers import MarkerStyle
from mudplot._render import _continuous_cmap, _count_colors
from mudplot._semantics import (
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_rows,
)
from mudplot.spec import LayerSpec, SemanticSpec


def _data():
    return {
        "x": [1, 2, 3, 4, 5, 6],
        "y": [4, 1, 6, 2, 5, 3],
        "h": ["A", "B", "A", "B", "A", "B"],
        "m": [0, 2, 4, 6, 8, 10],
        "s": ["X", "X", "Y", "Y", "X", "Y"],
    }


def _collections(ax):
    return [c for c in ax.collections if isinstance(c, PathCollection)]


def _point_records(ax):
    result = {}
    for collection in _collections(ax):
        offsets = np.asarray(collection.get_offsets())
        sizes = np.asarray(collection.get_sizes())
        colors = np.asarray(collection.get_facecolor())
        for i, (x, y) in enumerate(offsets):
            result[x] = (y, sizes[i], colors[i], collection.get_paths()[0].vertices)
    return result


@pytest.mark.parametrize("hue", [None, "h"])
@pytest.mark.parametrize("size", [None, "m"])
@pytest.mark.parametrize("style", [None, "s"])
def test_roles_independent_and_raw_row_geometry_retained(hue, size, style):
    p = mp.plot(_data()).scatter("x", "y", hue=hue, size=size, style=style, alpha=0.45)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    collections = _collections(ax)
    assert len(collections) == (2 if style else 1)
    assert sum(len(np.asarray(c.get_offsets())) for c in collections) == 6
    if p.spec.panels[0].layers[0].semantics is None:
        # Completely ordinary scatter is still the old one-size-per-collection path.
        assert len(ax.lines) == 0 and collections[0].get_sizes()[0] == 36
        return
    records = _point_records(ax)
    for i, x in enumerate(_data()["x"]):
        assert records[x][0] == _data()["y"][i]
        assert records[x][1] == pytest.approx((3 + 6 * i / 5) ** 2 if size else 36)
        assert records[x][2][3] == 0.45
    if hue:
        np.testing.assert_array_equal(records[1][2], records[3][2])
        assert not np.array_equal(records[1][2], records[2][2])
    if style:
        for value, marker in [(1, "o"), (3, "s")]:
            shape = MarkerStyle(marker)
            expected = shape.get_path().transformed(shape.get_transform()).vertices
            np.testing.assert_array_equal(records[value][3], expected)
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("kind", ["sequential", "diverging"])
@pytest.mark.parametrize("norm", [None, [-5, 15]])
def test_numeric_hue_uses_global_declared_linear_bounds_not_style_local(kind, norm):
    p = mp.plot(_data()).scatter(
        "x",
        "y",
        semantics={"hue": "m", "hue_kind": "numeric", "hue_norm": norm, "style": "s"},
        cmap_kind=kind,
    )
    ax = p.render().axes[0]
    values = np.array(_data()["m"])
    low, high = (0, 10) if norm is None else norm
    t = np.clip((values - low) / (high - low), 0, 1)
    expected = _continuous_cmap(kind)(t)
    records = _point_records(ax)
    for i, x in enumerate(_data()["x"]):
        np.testing.assert_allclose(records[x][2], expected[i])
    assert _count_colors(p.spec) == 0
    assert len(ax.get_legend_handles_labels()[1]) == 5


@pytest.mark.parametrize("norm", [[2, 8], [-5, 15]])
def test_size_diameters_squared_and_bounds_clip_mapping_not_rows(norm):
    p = mp.plot(_data()).scatter(
        "x",
        "y",
        semantics={"size": "m", "size_norm": norm, "sizes": [0, 10], "style": "s"},
    )
    ax = p.render().axes[0]
    records = _point_records(ax)
    expected = (
        np.clip((np.array(_data()["m"]) - norm[0]) / (norm[1] - norm[0]), 0, 1) * 10
    )
    assert len(records) == 6
    for i, x in enumerate(_data()["x"]):
        assert records[x][1] == pytest.approx(expected[i] ** 2)
    guides = [l for l in ax.lines if str(l.get_label()).startswith("size:")]
    assert [l.get_markersize() for l in guides] == [0, 5, 10]
    np.testing.assert_array_equal(ax.dataLim.bounds, [1, 1, 5, 5])


def test_categorical_size_order_and_singleton_midpoint():
    p = mp.plot(_data()).scatter(
        "x",
        "y",
        semantics={
            "size": "h",
            "size_kind": "categorical",
            "size_order": ["empty", "B", "A"],
            "sizes": [2, 8],
        },
    )
    ax = p.render().axes[0]
    records = _point_records(ax)
    assert records[1][1] == 64 and records[2][1] == 25
    assert ax.get_legend_handles_labels()[1] == ["size: h=B", "size: h=A"]
    p = mp.plot({"x": [1, 2], "y": [2, 1], "h": ["A", "A"]}).scatter(
        "x", "y", semantics={"size": "h", "size_kind": "categorical"}
    )
    np.testing.assert_array_equal(
        _collections(p.render().axes[0])[0].get_sizes(), [36, 36]
    )


def test_orders_reserve_empty_color_marker_slots_without_ghost_data():
    config = SemanticSpec(
        hue="h",
        hue_order=["empty", "B", "A"],
        style="s",
        style_order=["absent", "Y", "X"],
        markers=["D", "s", "o"],
    )
    p = mp.plot(_data()).scatter("x", "y", semantics=config)
    assert _count_colors(p.spec) == 3
    ax = p.render().axes[0]
    assert len(_collections(ax)) == 2
    assert ax.get_legend_handles_labels()[1] == [
        "hue: h=B",
        "hue: h=A",
        "style: s=Y",
        "style: s=X",
    ]
    assert sum(len(np.asarray(c.get_offsets())) for c in _collections(ax)) == 6
    records = _point_records(ax)
    shape = MarkerStyle("s")
    np.testing.assert_array_equal(
        records[3][3], shape.get_path().transformed(shape.get_transform()).vertices
    )


def test_missing_selection_and_log_positivity_are_listwise():
    raw = {
        "x": [1, 2, -1, "bad", None, 6],
        "y": [2, 1, 3, 4, 5, 6],
        "h": ["A", "A", "B", "B", "A", "A"],
        "m": [1, 3, 2, 2, 3, None],
        "s": ["X"] * 6,
    }
    p = (
        mp.plot(raw)
        .scatter(
            "x",
            "y",
            semantics={"hue": "h", "hue_order": ["A"], "size": "m", "style": "s"},
        )
        .xscale("log")
        .yscale("log")
    )
    assert mp.validate(p.spec) == []
    assert semantic_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [0, 1]
    ax = p.render().axes[0]
    np.testing.assert_array_equal(_collections(ax)[0].get_offsets(), [[1, 2], [2, 1]])
    assert len(_collections(ax)[0].get_sizes()) == 2


@pytest.mark.parametrize("constant", [0, 7, 1e308, 5e-324, -5e-324])
def test_auto_constant_numeric_roles_use_midpoint_and_one_guide(constant):
    p = mp.plot({"x": [1, 2], "y": [2, 1], "z": [constant] * 2}).scatter(
        "x", "y", semantics={"hue": "z", "hue_kind": "numeric", "size": "z"}
    )
    ax = p.render().axes[0]
    body = _collections(ax)[0]
    np.testing.assert_array_equal(body.get_sizes(), [36, 36])
    np.testing.assert_allclose(
        np.asarray(body.get_facecolor())[0], _continuous_cmap("sequential")(0.5)
    )
    assert len(ax.get_legend_handles_labels()[1]) == 2


@pytest.mark.parametrize(
    "low,high,values,expected",
    [
        (-1e308, 1e308, [-1e308, 0, 1e308], [0, 0.5, 1]),
        (
            1e308,
            np.nextafter(1e308, np.inf),
            [1e308, np.nextafter(1e308, np.inf)],
            [0, 1],
        ),
        (-1, 1, [-5, 0, 5], [0, 0.5, 1]),
    ],
)
def test_stable_normalization_for_extremes_and_neighboring_low_bits(
    low, high, values, expected
):
    actual, bounds = numeric_mapping(values, [low, high])
    np.testing.assert_array_equal(actual, expected)
    assert bounds == (low, high)
    guides = numeric_guides(bounds)
    assert all(math.isfinite(v) for v in guides) and len(guides) == len(set(guides))
    assert len({str(v) for v in guides}) == len(guides)
    p = mp.plot(
        {"x": list(range(1, len(values) + 1)), "y": [1] * len(values), "z": values}
    ).scatter(
        "x",
        "y",
        semantics={
            "hue": "z",
            "hue_kind": "numeric",
            # The strict spec decoder consumes JSON scalars, not NumPy scalar types.
            "hue_norm": [float(low), float(high)],
            "size": "z",
            "size_norm": [float(low), float(high)],
        },
    )
    p.render()


def test_bool_categories_are_distinct_from_numeric_but_not_ambiguous_string_labels():
    p = mp.plot({"x": [1, 2, 3], "y": [3, 2, 1], "h": [True, 1, 1.0]}).scatter(
        "x", "y", hue="h"
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert ax.get_legend_handles_labels()[1] == ["hue: h=True", "hue: h=1"]
    colors = np.asarray(_collections(ax)[0].get_facecolor())
    assert not np.array_equal(colors[0], colors[1])
    np.testing.assert_array_equal(colors[1], colors[2])
    p = mp.plot({"x": [1, 2], "y": [2, 1], "h": [True, "True"]}).scatter(
        "x", "y", hue="h"
    )
    assert any("ambiguous" in issue for issue in mp.validate(p.spec))
    assert category_key(True) != category_key(1)


@pytest.mark.parametrize(
    "field,value",
    [
        ("hue", True),
        ("hue", "absent"),
        ("hue", ""),
        ("hue_kind", "auto"),
        ("hue_order", ["A", "A"]),
        ("hue_order", []),
        ("hue_order", 3),
        ("hue_norm", [1, 1]),
        ("hue_norm", [0, float("inf")]),
        ("hue_norm", [True, 2]),
        ("size_norm", [5, 1]),
        ("size_norm", [0]),
        ("sizes", [-1, 5]),
        ("sizes", [1, 1001]),
        ("sizes", [5, 5]),
        ("sizes", [True, 5]),
        ("markers", ["o", "o"]),
        ("markers", ["x"]),
        ("markers", []),
        ("markers", ["bogus"]),
        ("style_order", ["Y", "Y"]),
        ("style_order", [{}]),
        ("legend", 1),
    ],
)
def test_invalid_configs_rejected_not_ignored(field, value):
    config = SemanticSpec(hue="h", size="m", style="s")
    setattr(config, field, value)
    p = mp.plot(_data()).dispatch(
        mp.actions.AddLayer(LayerSpec(type="scatter", x="x", y="y", semantics=config))
    )
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "config",
    [
        SemanticSpec(),
        SemanticSpec(hue="h", size_norm=[0, 1]),
        SemanticSpec(size="m", hue_kind="numeric"),
        SemanticSpec(hue="h", hue_norm=[0, 1]),
        SemanticSpec(size="m", size_kind="categorical", size_norm=[0, 1]),
        SemanticSpec(size="m", style_order=["X"]),
        SemanticSpec(hue="h", sizes=[1, 5]),
        SemanticSpec(size="m", markers=["o"]),
    ],
)
def test_unbound_or_kind_mismatched_options_fail(config):
    p = mp.plot(_data()).scatter("x", "y", semantics=config)
    assert mp.validate(p.spec)


@pytest.mark.parametrize(
    "override",
    [
        {"group": "h"},
        {"c": "m"},
        {"color": "#123456"},
        {"marker_size": 5},
        {"marker": "s"},
        {"colorbar": True},
        {"clabel": "z"},
        {"axis": "y2"},
        {"edge_color": "#123456"},
        {"line_width": 1},
        {"cmap_kind": "diverging"},
        {"references": {"A": mp.Reference(href="https://example.org")}},
    ],
)
def test_conflicting_legacy_or_scalar_overrides_fail(override):
    p = mp.plot(_data()).scatter("x", "y", hue="h", size="m", style="s", **override)
    assert mp.validate(p.spec)


@pytest.mark.parametrize("role", ["hue", "size"])
@pytest.mark.parametrize("bad", [True, float("inf"), "bad"])
def test_numeric_role_values_not_coerced(role, bad):
    raw = _data()
    raw["m"][2] = bad
    config = (
        SemanticSpec(hue="m", hue_kind="numeric")
        if role == "hue"
        else SemanticSpec(size="m", size_kind="numeric")
    )
    p = mp.plot(raw).scatter("x", "y", semantics=config)
    assert mp.validate(p.spec)


def test_bounds_limits_misplaced_config_and_shared_axes():
    raw = {"x": list(range(10001)), "y": [1] * 10001, "h": ["A"] * 10001}
    p = mp.plot(raw).scatter("x", "y", hue="h")
    assert any("10000" in v for v in mp.validate(p.spec))
    raw = {"x": list(range(65)), "y": [1] * 65, "h": list(range(65))}
    p = mp.plot(raw).scatter("x", "y", hue="h")
    assert any("limit" in v for v in mp.validate(p.spec))
    # Aggregated lineplot now has its own tested semantic path; raw line doesn't.
    for kind in ("line", "hist", "violin"):
        p = mp.plot(_data()).dispatch(
            mp.actions.AddLayer(
                LayerSpec(type=kind, x="x", y="y", semantics=SemanticSpec(hue="h"))
            )
        )
        assert any("semantics" in v for v in mp.validate(p.spec))
    p = mp.plot(_data()).scatter("x", "y", hue="h").pointplot("x", "y", errorbar=None)
    assert any("native and ordinal" in v for v in mp.validate(p.spec))


def test_unknown_duplicate_config_fields_and_canonical_tuple_choices():
    with pytest.raises(ValueError, match="unknown"):
        mp.plot(_data()).scatter("x", "y", semantics={"hue": "h", "surprise": True})
    with pytest.raises(ValueError, match="either"):
        mp.plot(_data()).scatter("x", "y", hue="h", semantics={"size": "m"})
    config = {"size": "m", "sizes": (2, 8), "size_norm": (0, 10)}
    p = mp.plot(_data()).scatter("x", "y", semantics=config)
    canonical = p.spec.panels[0].layers[0].semantics
    assert canonical is not None and canonical.sizes == [2, 8]
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_guide_roles_are_no_data_and_visible_labels_do_not_collide():
    p = mp.plot(_data()).scatter(
        "x",
        "y",
        semantics={"hue": "h", "style": "h"},
        label="Dataset",
        href="https://example.org",
    )
    ax = p.render().axes[0]
    assert all(len(np.asarray(line.get_xdata())) == 0 for line in ax.lines)
    labels = ax.get_legend_handles_labels()[1]
    assert labels == ["Dataset", "hue: h=A", "hue: h=B", "style: h=A", "style: h=B"]
    assert len(labels) == len(set(labels))
    np.testing.assert_array_equal(ax.dataLim.bounds, [1, 1, 5, 5])
    p = mp.plot(_data()).scatter("x", "y", semantics={"hue": "h", "legend": False})
    assert p.render().axes[0].get_legend_handles_labels() == ([], [])


def test_legacy_marker_group_continuous_color_and_old_json_unchanged():
    p = mp.plot(_data()).scatter("x", "y", group="h", marker_size=5)
    assert p.spec.panels[0].layers[0].semantics is None
    ax = p.render().axes[0]
    assert len(_collections(ax)) == 2 and ax.get_legend_handles_labels()[1] == [
        "A",
        "B",
    ]
    assert all(c.get_sizes()[0] == 25 for c in _collections(ax))
    p = mp.plot(_data()).scatter("x", "y", c="m", colorbar=True)
    assert len(p.render().axes) == 2
    raw = p.spec.to_dict()
    raw["panels"][0]["layers"][0].pop("semantics")
    assert mp.Plot.from_json(json.dumps(raw)).spec == p.spec


@pytest.mark.parametrize(
    "field,value",
    [
        ("sizes", np.array([3, 9])),
        ("markers", np.array(["o", "s"])),
        ("hue_kind", np.array(["numeric", "categorical"])),
    ],
)
def test_invalid_programmatic_array_options_report_issues_not_ambiguous_truth(
    field, value
):
    config = SemanticSpec(hue="h")
    setattr(config, field, value)
    p = mp.plot(_data()).dispatch(
        mp.actions.AddLayer(LayerSpec(type="scatter", x="x", y="y", semantics=config))
    )
    assert mp.validate(p.spec)


def test_direct_tuple_defaults_keep_same_contract():
    config = SemanticSpec(hue="h")
    for field, value in (
        ("sizes", (3, 9)),
        ("markers", ("o", "s", "D", "^", "v", "P", "X")),
    ):
        setattr(config, field, value)
    p = mp.plot(_data()).dispatch(
        mp.actions.AddLayer(LayerSpec(type="scatter", x="x", y="y", semantics=config))
    )
    assert mp.validate(p.spec) == []


def test_positive_size_area_underflow_fails_not_silently_hides_data():
    p = mp.plot(_data()).scatter(
        "x", "y", semantics={"size": "m", "sizes": [1e-300, 2e-300]}
    )
    assert mp.validate(p.spec) == []  # Derived area is a render-only check.
    with pytest.raises(ValueError, match="area is not representable"):
        p.render()


def test_schema_editor_exports_and_global_rng_unchanged(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(_data()).scatter(
        "x", "y", hue="h", size="m", style="s", label="Data", href="https://example.org"
    )
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.error is None and session.png.startswith(b"\x89PNG")
    before = np.random.get_state()
    for suffix in ("png", "svg", "pdf"):
        a, b = tmp_path / f"a.{suffix}", tmp_path / f"b.{suffix}"
        plt.close(p.save(str(a)))
        plt.close(p.save(str(b)))
        assert a.read_bytes() == b.read_bytes()
    assert "https://example.org" in (tmp_path / "a.svg").read_text(encoding="utf-8")
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
