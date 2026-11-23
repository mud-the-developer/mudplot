"""Contrast scientific input coordinates with display and native move geometry."""

import copy
import math
from dataclasses import replace

import mudplot as mp
import pytest
from mudplot.actions import ReplaceLayer, SetData


def stage(role, name):
    return mp.TransformSpec(role, name)


def figure(plot):
    return plot.render()


def coords(ax, dim):
    return [
        float(v)
        for line in ax.lines
        for v in getattr(line, f"get_{dim}data")()
        if math.isfinite(v)
    ]


def test_weighted_log_then_z_not_log_after_mean_and_pure_replay():
    source = {
        "x": ["a", "a", "b", "b"],
        "v": [1, 10, 100, -1],
        "w": [1, 3, 2, 0],
        "id": [True, 1, "A", "B"],
    }
    p = mp.plot(source).pointplot(
        "x",
        "v",
        weights="w",
        errorbar=None,
        transforms=[stage("y", "log"), {"role": "y", "name": "standardize"}],
    )
    original = copy.deepcopy(source)
    saved = p.to_json()
    assert mp.validate(p.spec) == []
    assert mp.apply(p.action_log) == p.spec == mp.Plot.from_json(saved).spec
    q = figure(p)
    expected = [-math.sqrt(3 / 2) / 4, math.sqrt(3 / 2)]
    assert coords(q.axes[0], "y") == pytest.approx(expected)
    assert source == original == p.spec.data.columns and p.to_json() == saved


def test_histogram_density_before_dodge_and_stack():
    source = {
        "v": [2, 20, 3, 30, 1000, None, 0],
        "w": [1, 3, 2, 4, 7, 99, 0],
        "g": ["A", "A", "B", "B", "A", "A", "B"],
    }
    opts = {
        "weights": "w",
        "group": "g",
        "bins": [0, 1, 2],
        "stat": "density",
        "element": "step",
        "transforms": [stage("x", "log")],
    }
    d = figure(mp.plot(source).hist("v", multiple="dodge", **opts)).axes[0]
    assert d.get_ylabel() == "density (1/log10 input)"
    assert list(d.patches[0].get_data().edges) == [0, 0, 0.5, 1, 1, 1.5, 2]
    assert list(d.patches[0].get_data().values) == pytest.approx([0, 0.1, 0, 0, 0.3, 0])
    assert list(d.patches[1].get_data().values) == pytest.approx([0, 0.2, 0, 0, 0.4, 0])
    s = figure(mp.plot(source).hist("v", multiple="stack", **opts)).axes[0]
    assert list(s.patches[1].get_data().values) == pytest.approx([0.3, 0.7])
    assert list(s.patches[1].get_data().baseline) == pytest.approx([0.1, 0.3])


def test_count_stack_untouched_log_ordinate_and_derived_native_category():
    data = {"dose": [1, 1, 10, 10], "g": ["A", "B", "A", "B"], "w": [2, 3, 4, 5]}
    p = (
        mp.plot(data)
        .countplot(
            "dose",
            group="g",
            weights="w",
            native_scale=True,
            stack=True,
            baseline=1,
            transforms=[stage("x", "log")],
        )
        .axis_scale("y", "log", options={"base": 2})
    )
    ax = figure(p).axes[0]
    bars = [
        (round(b.get_x() + b.get_width() / 2, 8), b.get_y(), b.get_y() + b.get_height())
        for b in ax.patches
    ]
    assert set(bars) == {(0, 1, 2), (0, 2, 5), (1, 1, 4), (1, 4, 9)}


def test_seeded_native_strip_dodge_preserves_row_draws_on_twin():
    import numpy as np

    source = {"x": [1, 10, 1, 10], "y": [2, 4, 8, 16], "g": ["A", "A", "B", "B"]}
    p = (
        mp.plot(source)
        .secondary_yaxis("dose")
        .stripplot(
            "x",
            "y",
            native_scale=True,
            group="g",
            hue_order=["A", "B", "empty"],
            dodge=0.6,
            jitter=0.2,
            strip=mp.StripSpec(seed=17),
            orient="h",
            axis="y2",
            transforms=[stage("x", "log")],
        )
    )
    ax = next(a for a in figure(p).axes if a.get_ylabel() == "dose")
    shifted = np.add(
        np.add([0, 1, 0, 1], [-0.2, -0.2, 0, 0]),
        np.random.default_rng(17).uniform(-0.04, 0.04, 4),
    )
    actual = np.concatenate([c.get_offsets() for c in ax.collections])
    assert actual[:, 0].tolist() == [2, 4, 8, 16]
    assert actual[:, 1].tolist() == pytest.approx(shifted)
    assert p.spec.data.columns == source


@pytest.mark.parametrize("cumulative", [False, True])
def test_named_kde_is_fitted_to_log_coordinates(cumulative):
    p = mp.plot({"v": [1, 10], "w": [1, 3]}).kde(
        "v",
        weights="w",
        bw_method=math.sqrt(2),
        cut=0,
        gridsize=17,
        cumulative=cumulative,
        transforms=[stage("x", "log")],
    )
    ax = figure(p).axes[0]
    expected = (
        (0.5 + 3 * (0.5 * (1 + math.erf(-1 / math.sqrt(2))))) / 4
        if cumulative
        else (1 + 3 * math.exp(-0.5)) / (4 * math.sqrt(2 * math.pi))
    )
    assert coords(ax, "x")[0] == 0 and coords(ax, "x")[-1] == 1
    assert coords(ax, "y")[0] == pytest.approx(expected, rel=2e-12)
    assert ("density (1/log10 input)" not in ax.get_ylabel()) == cumulative


def test_empirical_ties_and_paired_clock_select_original_weights():
    source = {
        "x": [1, 10, 10, 1000, None],
        "y": ["2020-01-02T00:00:00Z"] * 2
        + ["2020-01-05T00:00:00Z"]
        + ["2020-01-01T00:00:00Z"] * 2,
        "w": [1, 3, 2, 4, 99],
    }
    p = (
        mp.plot(source)
        .date_axis("y")
        .ecdf2d(
            "x",
            "y",
            weights="w",
            colorbar=False,
            bounds=[[0, 2], [18262, 18265]],
            query_x=[1],
            query_y=[18263],
            transforms=[stage("x", "log")],
        )
    )
    ax = figure(p).axes[0]
    mesh = ax.collections[0]
    edges = mesh.get_coordinates()
    data = mesh.get_array().reshape(edges.shape[0] - 1, edges.shape[1] - 1)
    ix = list(edges[0, :, 0]).index(1)
    iy = list(edges[:, 0, 1]).index(18263)
    assert data[iy, ix] == pytest.approx(0.4)
    assert p.spec.data.columns == source
    q = mp.plot({"x": [1, 10, 10], "w": [1, 3, 2]}).ecdf(
        "x", weights="w", transforms=[stage("x", "log")]
    )
    assert coords(figure(q).axes[0], "y")[-1] == 1


def test_histogram_overlay_same_derived_physical_cohort():
    source = {
        "x": [1, 10, 100, 1000, 10000],
        "y": [1, 3, 1, 4, 2],
        "w": [1, 2, 3, 4, 5],
    }
    options = {
        "bins": mp.BivariateBinsSpec(x=[0, 1, 2], y=[0, 2, 5]),
        "weights": "w",
        "stat": "density",
        "kde": mp.KDE2DSpec(weights="w", levels=[0.7], gridsize=17),
        "colorbar": False,
    }
    p = mp.plot(source).hist2d("x", "y", transforms=[stage("x", "log")], **options)
    reference = mp.plot({**source, "x": [0, 1, 2, 3, 4]}).hist2d("x", "y", **options)
    import numpy as np

    for actual, expected in zip(
        figure(p).axes[0].collections,
        figure(reference).axes[0].collections,
        strict=True,
    ):
        np.testing.assert_allclose(actual.get_array(), expected.get_array())
        for a, b in zip(actual.get_paths(), expected.get_paths(), strict=True):
            np.testing.assert_allclose(a.vertices, b.vertices)
    assert p.spec.data.columns == source


@pytest.mark.parametrize("method", ["resampling-cell", "resampling-unit"])
def test_intervals_and_local_seed_match_independently_projected_physical_rows(method):
    from mudplot._line_inference import prepare_line_inference

    data = {
        "x": [1, 10, 1, 10, 1, 10],
        "y": [1, 10, 10, 100, 100, 1000],
        "w": [1, 2, 3, 4, 2, 1],
        "unit": ["a", "a", "b", "b", "c", "c"],
    }
    cfg = {
        "weights": "w",
        "units": "unit",
        "n_boot": 29,
        "seed": 17,
        "line": mp.LineSpec(resampling=method.split("-")[1]),
    }
    p = mp.plot(data).lineplot("x", "y", transforms=[stage("y", "log")], **cfg)
    control = mp.plot({**data, "y": [0, 1, 1, 2, 2, 3]}).lineplot("x", "y", **cfg)
    observed, _ = prepare_line_inference(p.spec)
    expected, _ = prepare_line_inference(control.spec)
    assert observed[(0, 0)].summary == expected[(0, 0)].summary
    assert observed[(0, 0)].source_rows == tuple(range(6))
    assert figure(p).axes[0].lines


def test_explicit_identity_keeps_legacy_output_and_scale_control():
    data = {"x": [1, 2, 3], "y": [2, 3, 4]}
    original = mp.plot(data).line("x", "y").xscale("log")
    identity = (
        mp.plot(data).line("x", "y", transforms=[stage("x", "identity")]).xscale("log")
    )
    assert "transforms" not in original.to_json()
    assert "transforms" in identity.to_json()
    for dim in ("x", "y"):
        assert coords(figure(identity).axes[0], dim) == coords(
            figure(original).axes[0], dim
        )


def test_reject_invalid_chain_conflicting_clock_scale_domain_and_units():
    p = mp.plot({"x": [1, 2], "y": [1, 2]})
    for stages in (
        [],
        [stage("y", "identity"), stage("y", "log")],
        [{"role": "y", "name": "bad"}],
        [stage("y", "log")] * 5,
    ):
        with pytest.raises((TypeError, ValueError)):
            p.line("x", "y", transforms=stages)
    assert not p.spec.panels[0].layers
    bad = mp.plot({"x": [0, 1], "y": [1, 2]}).line(
        "x", "y", transforms=[stage("x", "log")]
    )
    assert any("positive selected" in e for e in mp.validate(bad.spec))
    one = mp.plot({"x": [1, 2], "y": [2, 2]}).line(
        "x", "y", transforms=[stage("y", "standardize")]
    )
    assert any("nonzero population" in e for e in mp.validate(one.spec))
    warped = p.line("x", "y", transforms=[stage("x", "log")])
    assert any("incompatible" in e for e in mp.validate(warped.scatter("x", "y").spec))
    shared = (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y", transforms=[stage("x", "log")])
        .line("x", "y", panel=1)
    )
    shared_spec = replace(shared.spec, share_x="all")
    assert any(
        "shared x" in e and "incompatible" in e for e in mp.validate(shared_spec)
    )
    assert any(
        "logarithmic display" in e for e in mp.validate(shared.xscale("log").spec)
    )


def test_inferred_clock_alias_order_preserves_weighted_rows_live_history():
    a, b, later = (
        "2020-01-01T00:00:00Z",
        "2019-12-31T19:00:00-05:00",
        "2020-01-04T00:00:00Z",
    )
    data = {
        "t": [a, b, later, b, None, a],
        "y": [1, 10, 100, 9, -1000, -1000],
        "w": [1, 3, 2, 2, 9, 0],
        "site": ["left"] * 3 + ["right", "left", "left"],
        "id": list(range(6)),
    }
    p = (
        mp.plot(data)
        .date_axis("x")
        .pointplot("t", "y", native_scale=True, weights="w", errorbar=None)
        .axis_scale("y", "log", options={"base": 2})
        .facet(col="site", col_order=["left", "right", "empty"], live=True)
    )
    saved = p.to_json()
    assert [layer.layers[0].order for layer in p.spec.panels] == [[a, later]] * 3
    assert [coords(ax, "y") for ax in figure(p).axes] == [[7.75, 100], [9], []]
    layer = p.spec.panels[0].layers[0]
    p.dispatch(
        ReplaceLayer(
            0, replace(layer, stat=replace(layer.stat, estimator="median")), panel=0
        )
    )
    assert [coords(ax, "y") for ax in figure(p).axes] == [[10, 100], [9], []]
    assert p.store.undo() == mp.Plot.from_json(saved).spec
    p.store.redo()
    reopened = mp.Plot.from_json(p.to_json())
    template = reopened.spec.facet_template.template
    template.layers[0].order = None
    reopened.facet_template(template)
    assert reopened.to_json() == saved
    t3 = "2020-01-01T01:00:00+01:00"
    changed = {**data, "t": [a, b, later, t3, None, a]}
    reopened.dispatch(SetData(changed))
    assert [coords(ax, "y") for ax in figure(reopened).axes] == [[7.75, 100], [9], []]
    assert reopened.spec.data.columns == changed and p.spec.data.columns == data
    explicit = (
        mp.plot(data)
        .date_axis("x")
        .pointplot("t", "y", order=[a, b], weights="w", errorbar=None)
    )
    assert any("duplicate" in e for e in mp.validate(explicit.spec))


def test_explicit_dates_and_units_resolve_per_actual_native_axis():
    b = "2019-12-31T19:00:00-05:00"
    p = mp.plot(
        {
            "ms": [0, 0, 259200000],
            "s": [1, 1, 259201],
            "y": [1, 10, 100],
            "w": [1, 3, 2],
        }
    )
    p.date_axis("x", unit="ms", origin=b).pointplot(
        "ms", "y", weights="w", errorbar=None, order=[0, 259200000]
    )
    p.date_axis("x", unit="s", origin="2019-12-31T23:59:59Z", panel=1)
    p.pointplot("s", "y", weights="w", errorbar=None, order=[1, 259201], panel=1)
    from mudplot._render import render

    native = render(replace(p.spec, share_x="all"))
    assert [coords(ax, "x") for ax in native.axes] == [[18262, 18265]] * 2
    assert [coords(ax, "y") for ax in native.axes] == [[7.75, 100]] * 2
    assert native.axes[0].get_xlim() == native.axes[1].get_xlim()


def test_raw_line_preserves_chronological_duplicates_and_barriers_on_actual_twin():
    import numpy as np

    a = "2020-01-01T00:00:00Z"
    b = "2019-12-31T19:00:00-05:00"
    later = "2020-01-04T00:00:00Z"
    data = {
        "time": [a, b, None, later],
        "value": [1, 10, 100, 1000],
        "site": ["left", "left", "left", "left"],
    }
    p = (
        mp.plot(data)
        .secondary_yaxis("Time")
        .date_axis("y2")
        .line(
            "time",
            "value",
            order=[a, later],
            orient="h",
            axis="y2",
            transforms=[stage("y", "log")],
        )
    )
    target = next(a for a in figure(p).axes if a.get_ylabel() == "Time")
    np.testing.assert_allclose(
        target.lines[0].get_ydata(), [18262, 18262, np.nan, 18265]
    )
    np.testing.assert_allclose(target.lines[0].get_xdata(), [0, 1, np.nan, 3])
    assert p.spec.data.columns == data


def test_complete_unit_clock_selection_retains_an_allmissing_response_unit():
    from mudplot._line_inference import prepare_line_inference

    a, b = "2020-01-01T00:00:00Z", "2019-12-31T19:00:00-05:00"
    data = {"t": [a, b, b], "v": [1, 10, None], "unit": ["A", "B", "C"]}
    p = (
        mp.plot(data)
        .date_axis("x")
        .lineplot(
            "t",
            "v",
            order=[a],
            units="unit",
            n_boot=5,
            seed=22,
            errorbar=("ci", 20),
            line=mp.LineSpec(resampling="unit", calibration="max_deviation"),
            transforms=[stage("y", "log")],
        )
    )
    plans, work = prepare_line_inference(p.spec)
    assert plans[(0, 0)].source_rows == (0, 1, 2)
    assert plans[(0, 0)].summary.estimates[0].value == 0.5
    assert work["whole_unit"] == 5 * (3 + 3 + 1) and work["coordinates"] >= 3


def test_exact_z_with_overflowing_raw_variance_and_private_raw_ref():
    p = mp.plot({"x": [1, 2], "y": [-1e300, 1e300]}).line(
        "x",
        "y",
        transforms=[stage("y", "standardize")],
    )
    assert coords(figure(p).axes[0], "y") == [-1, 1]

    bad = mp.plot({"x": [1, 2], "y": [1, 2]}).line(
        "x",
        "y",
        group="__mudplot_projected_x",
        transforms=[stage("x", "log")],
    )
    assert any("column" in issue for issue in mp.validate(bad.spec))
