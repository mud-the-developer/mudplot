"""KDE composition reuses existing fits, preserves cohorts and keeps hist defaults."""

from __future__ import annotations

import json
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from mudplot import actions as A
from mudplot._facet import panel_columns, panel_rows
from mudplot._kde import kde_summary


def data():
    return {
        "x": [1, 2, 3, 4, None, 6, 7, 8, 9, 10],
        "y": [2, 3, 5, 4, 7, None, 8, 10, 9, 11],
        "h": ["B"] * 5 + ["A"] * 5,
        "w": [1] * 10,
    }


def build(kind, **options):
    if kind == "joint":
        return mp.plot(data()).scatter("x", "y", group="h").joint(**options).size(7, 6)
    return mp.plot(data()).pair(["x", "y"], group="h", **options).size(7, 7)


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_joint_kde_fits_only_the_complete_xy_cohort_in_correct_orientation():
    cfg = mp.KDESpec(bw_method="silverman", bw_adjust=0.8, gridsize=31, cut=0)
    p = build("joint", marginal_kind="kde", kde=cfg)
    assert p.spec.data.columns == data()
    assert [panel_rows(p.spec.data.columns, panel) for panel in p.spec.panels] == [
        [0, 1, 2, 3, 6, 7, 8, 9]
    ] * 3
    axes = p.render().axes
    for index in (1, 2):
        panel = p.spec.panels[index]
        layer = panel.layers[0]
        assert layer.type == "kde" and layer.kde == cfg and layer.histogram is None
        expected = kde_summary(panel_columns(p.spec.data.columns, panel), layer)
        assert len(axes[index].lines) == len(expected) == 2
        for line, curve in zip(axes[index].lines, expected, strict=True):
            x, y = (
                (curve.heights, curve.support)
                if index == 1
                else (curve.support, curve.heights)
            )
            np.testing.assert_allclose(np.asarray(line.get_xdata(), dtype=float), x)
            np.testing.assert_allclose(np.asarray(line.get_ydata(), dtype=float), y)
    assert (
        sum(
            np.asarray(c.get_offsets()).shape[0]
            for c in axes[0].collections
            if isinstance(c, PathCollection)
        )
        == 8
    )


def test_pair_kde_diagonals_use_univariate_not_global_listwise_rows():
    p = build(
        "pair", diag_kind="kde", kde={"cut": 0, "gridsize": 31, "common_grid": True}
    )
    assert [panel_rows(p.spec.data.columns, panel) for panel in p.spec.panels] == [
        [0, 1, 2, 3, 5, 6, 7, 8, 9],
        [0, 1, 2, 3, 6, 7, 8, 9],
        [0, 1, 2, 3, 6, 7, 8, 9],
        [0, 1, 2, 3, 4, 6, 7, 8, 9],
    ]
    axes = p.render().axes
    assert p.spec.panels[0].y.share_id is p.spec.panels[3].y.share_id is None
    assert not axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    for index in (0, 3):
        panel = p.spec.panels[index]
        expected = kde_summary(
            panel_columns(p.spec.data.columns, panel), panel.layers[0]
        )
        for line, curve in zip(axes[index].lines, expected, strict=True):
            np.testing.assert_allclose(
                np.asarray(line.get_xdata(), dtype=float), curve.support
            )
            np.testing.assert_allclose(
                np.asarray(line.get_ydata(), dtype=float), curve.heights
            )


@pytest.mark.parametrize(
    "kind,key", [("joint", "marginal_kind"), ("pair", "diag_kind")]
)
def test_kde_options_are_copied_and_replay_as_plain_json(kind, key):
    config = {"bw_adjust": 0.7, "gridsize": 31, "cut": 0, "fill": True}
    before = dict(config)
    p = build(kind, **{key: "kde", "kde": config})
    assert config == before
    encoded = json.loads(json.dumps(p.action_log))
    assert encoded[-2]["kde"]["bw_adjust"] == 0.7
    assert mp.apply(encoded) == mp.Plot.from_json(p.to_json()).spec == p.spec
    cfg = mp.KDESpec(bw_adjust=0.7)
    q = build(kind, **{key: "kde", "kde": cfg})
    cfg.bw_adjust = 4
    assert all(
        layer.kde.bw_adjust == 0.7
        for panel in q.spec.panels
        for layer in panel.layers
        if layer.kde is not None
    )
    assert any(ax.collections for ax in p.render().axes)


@pytest.mark.parametrize(
    "kind,key,stat",
    [("joint", "marginal_kind", "marginal_stat"), ("pair", "diag_kind", "diag_stat")],
)
@pytest.mark.parametrize(
    "bad",
    [
        {"kind": "bad"},
        {"kind": "hist", "kde": {"cut": 0}},
        {"kind": "kde", "bins": 30},
        {"kind": "kde", "stat": "count"},
        {"kind": "kde", "kde": {"weights": "w"}},
        {"kind": "kde", "kde": {"cumulative": True}},
        {"kind": "kde", "kde": {"bw_adjust": -1}},
        {"kind": "kde", "kde": {"unknown": True}},
    ],
)
def test_invalid_distribution_combinations_do_not_mutate_state(kind, key, stat, bad):
    p = mp.plot(data())
    if kind == "joint":
        p.scatter("x", "y", group="h")
    before, history = p.to_json(), p.action_log
    args = {
        key if name == "kind" else stat if name == "stat" else name: value
        for name, value in bad.items()
    }
    with pytest.raises((ValueError, TypeError)):
        p.joint(**args) if kind == "joint" else p.pair(["x", "y"], group="h", **args)
    assert p.to_json() == before and p.action_log == history


def test_singular_kde_marginals_warn_and_do_not_invent_a_density():
    raw = {"x": [1, 1, 1, 2, 3, 4], "y": [2, 3, 4, 5, 6, 7], "h": ["A"] * 3 + ["B"] * 3}
    p = (
        mp.plot(raw)
        .scatter("x", "y", group="h")
        .joint(marginal_kind="kde", kde={"cut": 0})
        .size(7, 6)
    )
    with pytest.warns(UserWarning, match="KDE skipped singular"):
        axes = p.render().axes
    assert (
        sum(
            np.asarray(c.get_offsets()).shape[0]
            for c in axes[0].collections
            if isinstance(c, PathCollection)
        )
        == 6
    )
    assert len(axes[2].lines) == 1 and axes[2].lines[0].get_label() == "B"


@pytest.mark.parametrize(
    "kind,key", [("joint", "marginal_kind"), ("pair", "diag_kind")]
)
def test_histogram_default_specs_remain_identical(kind, key):
    assert build(kind).spec == build(kind, **{key: "hist"}).spec


@pytest.mark.parametrize(
    "kind,key", [("joint", "marginal_kind"), ("pair", "diag_kind")]
)
@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_kde_grid_exports_reproduce_without_global_rng(tmp_path, kind, key, extension):
    state = np.random.get_state()
    p = build(kind, **{key: "kde", "kde": {"gridsize": 31, "cut": 0}})
    a, b = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(a)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(b)))
    assert a.read_bytes() == b.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_kde_grid_action_and_validation_remain_optional_dependency_free():
    script = (
        "import sys,json; import mudplot as m; "
        "d={'x':[1,2,3],'y':[2,3,4]}; "
        "p=m.plot(d).scatter('x','y').joint(marginal_kind='kde',kde={'cut':0}); "
        "q=m.plot(d).pair(['x','y'],diag_kind='kde'); "
        "assert m.validate(p.spec)==m.validate(q.spec)==[]; "
        "assert m.apply(json.loads(json.dumps(p.action_log)))==p.spec; "
        "assert m.apply(q.action_log)==q.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)


def test_kde_spec_action_serializes_through_registry():
    action = A.SetJointGrid(marginal_kind="kde", kde=mp.KDESpec(cut=0, gridsize=31))
    encoded = json.loads(json.dumps(A.action_to_dict(action)))
    assert A.action_from_dict(encoded) == action
