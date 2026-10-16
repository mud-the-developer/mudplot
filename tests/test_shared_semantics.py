"""Figure-named role domains: pooled rows, colour identity and honest guides."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from mudplot import actions as A
from mudplot._render import _continuous_cmap, _count_colors
from mudplot._semantics import shared_scale_domains
from mudplot.spec import SemanticSpec


def _data():
    return {
        "left": [1, 2, None, None],
        "right": [None, None, 3, 4],
        "all": [1, 2, 3, 4],
        "y": [1, 2, 3, 4],
        "h": ["A", "B", "B", "C"],
        "m": [0, 2, 8, 10],
        "s": ["X", "Y", "Y", "X"],
    }


def _points(ax):
    result = {}
    for c in ax.collections:
        if not isinstance(c, PathCollection):
            continue
        xy = np.asarray(c.get_offsets())
        colors = np.asarray(c.get_facecolor())
        sizes = np.asarray(c.get_sizes())
        for i, pair in enumerate(xy):
            result[int(pair[0])] = (sizes[i], colors[i], c.get_paths()[0].vertices)
    return result


def _plot(
    *, kind="categorical", role="both", name: str | None = "study", same_panel=False
):
    p = mp.plot(_data()).layout(1, 1 if same_panel else 2)
    for index, x in enumerate(("left", "right")):
        cfg = SemanticSpec(
            scale_id=name,
            hue="m" if kind == "numeric" else "h",
            hue_kind=kind,
            style="s",
            size="m" if role == "both" else None,
        )
        p.scatter(x, "y", semantics=cfg, panel=0 if same_panel else index)
    return p


@pytest.mark.parametrize("kind", ["categorical", "numeric"])
@pytest.mark.parametrize("same_panel", [False, True])
def test_pooled_domains_survive_missing_rows_and_align_colours_sizes_markers(
    kind, same_panel
):
    p = _plot(kind=kind, same_panel=same_panel)
    assert mp.validate(p.spec) == []
    domains = shared_scale_domains(p.spec)
    assert domains["study"]["rows"] == [0, 1, 2, 3]
    fig = p.render()
    records = {key: value for ax in fig.axes for key, value in _points(ax).items()}
    assert sorted(records) == [1, 2, 3, 4]
    for index, x in enumerate([1, 2, 3, 4]):
        assert records[x][0] == pytest.approx((3 + 6 * _data()["m"][index] / 10) ** 2)
    if kind == "categorical":
        np.testing.assert_array_equal(records[2][1], records[3][1])
        assert not np.array_equal(records[1][1], records[4][1])
        assert _count_colors(p.spec) == 3
    else:
        for index, x in enumerate([1, 2, 3, 4]):
            np.testing.assert_allclose(
                records[x][1], _continuous_cmap("sequential")(_data()["m"][index] / 10)
            )
        assert _count_colors(p.spec) == 0
    np.testing.assert_array_equal(records[2][2], records[3][2])
    labels = fig.axes[0].get_legend_handles_labels()[1]
    assert len(labels) == len(set(labels))
    assert all(len(np.asarray(line.get_xdata())) == 0 for line in fig.axes[0].lines)
    if not same_panel:
        assert fig.axes[1].get_legend_handles_labels()[1] == labels
        np.testing.assert_array_equal(fig.axes[0].dataLim.bounds, [1, 1, 1, 1])
        np.testing.assert_array_equal(fig.axes[1].dataLim.bounds, [3, 3, 1, 1])
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_unshared_default_remains_layer_local():
    p = _plot(name=None)
    assert shared_scale_domains(p.spec) == {}
    a, b = p.render().axes
    assert [v[0] for v in _points(a).values()] == [9, 81]
    assert sorted(v[0] for v in _points(b).values()) == [9, 81]
    assert a.get_legend_handles_labels()[1] != b.get_legend_handles_labels()[1]


@pytest.mark.parametrize("role", ["hue", "size", "style"])
def test_independent_role_domains_share_all_categories(role):
    p = mp.plot(_data()).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        cfg = SemanticSpec(scale_id="domain")
        if role == "size":
            cfg.size_kind = "categorical"
        setattr(cfg, role, "h" if role != "style" else "s")
        p.scatter(x, "y", semantics=cfg, panel=index)
    assert mp.validate(p.spec) == []
    a, b = p.render().axes
    assert a.get_legend_handles_labels()[1] == b.get_legend_handles_labels()[1]
    if role == "size":
        assert _points(a)[1][0] == 9 and _points(a)[2][0] == 36
        assert _points(b)[3][0] == 36 and _points(b)[4][0] == 81


@pytest.mark.parametrize(
    "change",
    [
        {"hue": "m"},
        {"hue_kind": "numeric"},
        {"hue_order": ["B", "A", "C"]},
        {"size_norm": [0, 20]},
        {"sizes": [2, 8]},
        {"markers": ["s", "o"]},
        {"style_order": ["Y", "X"]},
        {"size": None},
    ],
)
def test_same_id_requires_identical_mapping_contract(change):
    p = _plot()
    invalid = p.spec
    config = invalid.panels[1].layers[0].semantics
    assert config is not None
    for name, value in change.items():
        setattr(config, name, value)
    issues = mp.validate(invalid)
    assert issues
    with pytest.raises(ValueError):
        mp.render(invalid)


def test_numeric_shared_colormap_mismatch_is_not_silently_different_hue_scale():
    p = _plot(kind="numeric")
    spec = p.spec
    spec.panels[1].layers[0].cmap_kind = "diverging"
    assert any("identical" in issue for issue in mp.validate(spec))
    spec.panels[1].layers[0].cmap_kind = "not-a-map"
    assert any("cmap_kind" in issue for issue in mp.validate(spec))


@pytest.mark.parametrize("name", ["", True, 123, "a" * 65, "bad\nname"])
def test_invalid_scale_names_report_validation(name):
    cfg = SemanticSpec(hue="h")
    cfg.scale_id = name
    p = mp.plot(_data()).dispatch(
        A.AddLayer(mp.spec.LayerSpec(type="scatter", x="all", y="y", semantics=cfg))
    )
    assert mp.validate(p.spec)


def test_different_ids_are_independent_and_unique_row_pool_has_no_duplication():
    p = _plot()
    spec = p.spec
    config = spec.panels[1].layers[0].semantics
    assert config is not None
    config.scale_id = "other"
    assert set(shared_scale_domains(spec)) == {"study", "other"}
    fig = mp.render(spec)
    assert sorted(v[0] for v in _points(fig.axes[1]).values()) == [9, 81]
    p = mp.plot(_data())
    cfg = SemanticSpec(scale_id="same", hue="h")
    for _ in range(5):
        p.scatter("all", "y", semantics=cfg)
    assert shared_scale_domains(p.spec)["same"]["rows"] == [0, 1, 2, 3]
    assert _count_colors(p.spec) == 3
    assert len(p.render().axes[0].get_legend_handles_labels()[1]) == 3


@pytest.mark.parametrize("leading_legend", [False, True])
def test_legend_suppression_does_not_erase_later_shared_guides(leading_legend):
    p = mp.plot(_data())
    for index, x in enumerate(("left", "right")):
        p.scatter(
            x,
            "y",
            semantics=SemanticSpec(
                scale_id="s", hue="h", legend=leading_legend if index == 0 else True
            ),
            label=f"Data{index}",
        )
    assert mp.validate(p.spec) == []
    labels = p.render().axes[0].get_legend_handles_labels()[1]
    assert labels.count("hue: h=A") == 1 and labels.count("hue: h=C") == 1
    assert "Data0" in labels and "Data1" in labels


def test_pooled_label_collision_and_marker_limit_fail_even_when_members_alone_valid():
    raw = {"left": [1, None], "right": [None, 2], "y": [1, 2], "h": [True, "True"]}
    p = mp.plot(raw).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        p.scatter(x, "y", semantics=SemanticSpec(scale_id="g", hue="h"), panel=index)
    assert any("ambiguous" in v for v in mp.validate(p.spec))
    raw = {
        "left": [1, 2, 3, 4] + [None] * 4,
        "right": [None] * 4 + [5, 6, 7, 8],
        "y": list(range(8)),
        "h": list(range(8)),
    }
    p = mp.plot(raw).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        p.scatter(x, "y", semantics=SemanticSpec(scale_id="g", style="h"), panel=index)
    assert any("pooled style" in v for v in mp.validate(p.spec))


def test_pooled_rows_and_category_limits_and_invalid_data_do_not_raise_in_validator():
    n = 12000
    raw = {
        "left": list(range(6000)) + [None] * 6000,
        "right": [None] * 6000 + list(range(6000)),
        "y": [1] * n,
        "m": list(range(n)),
    }
    p = mp.plot(raw).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        p.scatter(x, "y", semantics=SemanticSpec(scale_id="g", size="m"), panel=index)
    assert any("pooled rows" in v for v in mp.validate(p.spec))
    spec = _plot().spec
    spec.data.columns["h"][0] = {"bad": 1}
    assert mp.validate(spec)


def test_legacy_palette_entries_do_not_shift_shared_hue_colours():
    p = _plot()
    spec = p.spec
    # Add legacy before one shared layer; the named scale still owns its colours.
    spec.panels[0].layers.insert(
        0, mp.spec.LayerSpec(type="scatter", x="all", y="y", label="legacy")
    )
    assert mp.validate(spec) == [] and _count_colors(spec) == 4
    a, b = mp.render(spec).axes
    ca = [c for c in a.collections if isinstance(c, PathCollection)][1:]
    shared = {
        int(v[0]): np.asarray(c.get_facecolor())[i]
        for c in ca
        for i, v in enumerate(np.asarray(c.get_offsets()))
    }
    np.testing.assert_array_equal(shared[2], _points(b)[3][1])


def test_panel_reorder_keeps_one_scope_domains_in_original_row_order():
    p = _plot()
    first = _points(p.render().axes[0])
    spec = p.spec
    spec.panels.reverse()
    assert shared_scale_domains(spec)["study"]["rows"] == [0, 1, 2, 3]
    last = _points(mp.render(spec).axes[1])
    for key in first:
        np.testing.assert_array_equal(first[key][1], last[key][1])
        assert first[key][0] == last[key][0]


@pytest.mark.parametrize("constant", [0, 5e-324, -5e-324, 1e308])
def test_pooled_constants_have_one_true_guide_even_at_subnormal_scale(constant):
    p = _plot(kind="numeric")
    spec = p.spec
    spec.data.columns["m"] = [constant] * 4
    assert mp.validate(spec) == []
    for ax in mp.render(spec).axes:
        labels = ax.get_legend_handles_labels()[1]
        assert len([label for label in labels if label.startswith("hue:")]) == 1
        assert len([label for label in labels if label.startswith("size:")]) == 1


def test_pooled_category_limit_applies_to_union_not_each_member():
    n = 70
    raw = {
        "left": list(range(35)) + [None] * 35,
        "right": [None] * 35 + list(range(35)),
        "y": [1] * n,
        "h": list(range(n)),
    }
    p = mp.plot(raw).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        p.scatter(x, "y", semantics=SemanticSpec(scale_id="g", hue="h"), panel=index)
    assert any("pooled levels" in issue for issue in mp.validate(p.spec))


def test_typed_boolean_order_is_not_numeric_order_in_shared_signature():
    raw = {"left": [1, None], "right": [None, 2], "y": [1, 2], "h": [True, 1]}
    p = mp.plot(raw).layout(1, 2)
    for index, x in enumerate(("left", "right")):
        p.scatter(
            x,
            "y",
            semantics=SemanticSpec(
                scale_id="g", hue="h", hue_order=[True, 1] if index == 0 else [1, True]
            ),
            panel=index,
        )
    assert any("identical" in issue for issue in mp.validate(p.spec))


def test_old_semantic_json_default_editor_and_repeatable_exports(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = _plot(kind="numeric")
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
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    old = mp.plot(_data()).scatter("all", "y", hue="h").spec.to_dict()
    old["panels"][0]["layers"][0]["semantics"].pop("scale_id")
    restored = mp.Plot.from_json(json.dumps(old)).spec.panels[0].layers[0].semantics
    assert restored is not None and restored.scale_id is None
