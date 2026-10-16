"""Statistical native/log coordinates keep raw data, named inference and real bounds."""

from __future__ import annotations

import json
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation
from matplotlib.ticker import FixedLocator
from mudplot._estimate import summarize
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def _plot(kind, data, **options):
    p = mp.plot(data)
    getattr(p, kind)("c", *(["v"] if kind != "countplot" else []), **options)
    return p


def _edges(rect, orient):
    return (
        (rect.get_y(), rect.get_y() + rect.get_height())
        if orient == "h"
        else (rect.get_x(), rect.get_x() + rect.get_width())
    )


def _values(rect, orient):
    return (
        (rect.get_x(), rect.get_x() + rect.get_width())
        if orient == "h"
        else (rect.get_y(), rect.get_y() + rect.get_height())
    )


def _scales(p, orient, cat="linear", value="linear"):
    return p.xscale(value if orient == "h" else cat).yscale(
        cat if orient == "h" else value
    )


@pytest.mark.parametrize("kind", ["barplot", "countplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("category_scale", ["linear", "log"])
def test_native_bar_width_dodge_gaps_empty_hues_and_error_centers_use_axis_spacing(
    kind, orient, category_scale
):
    data = {
        "c": [10] * 4 + [30] * 4,
        "v": [1, 2, 4, 8] * 2,
        "h": ["A"] * 2 + ["B"] * 2 + ["A"] * 2 + ["B"] * 2,
    }
    options = {
        "native_scale": True,
        "orient": orient,
        "group": "h",
        "gap": 0.2,
        "order": [100, 10, 30],
        "hue_order": ["B", "empty", "A"],
        "bar_width": 0.6,
    }
    if kind != "countplot":
        options["errorbar"] = "pi"
    p = _scales(_plot(kind, data, **options), orient, cat=category_scale)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    containers = [c for c in ax.containers if isinstance(c, BarContainer)]
    assert len(containers) == 2 and ax.get_legend_handles_labels()[1] == ["B", "A"]
    transform = np.log10 if category_scale == "log" else np.asarray

    def inverse(z):
        return 10**z if category_scale == "log" else z

    coords = np.asarray(transform([10, 30, 100]))
    spacing = min(np.diff(coords))
    span = 0.6 * spacing
    width = span / 3 * 0.8
    for container, index in zip(containers, (0, 2), strict=True):
        for rect, center in zip(container, coords[:2], strict=True):
            displaced = center + (index - 1) * span / 3
            np.testing.assert_allclose(
                _edges(rect, orient),
                [inverse(displaced - width / 2), inverse(displaced + width / 2)],
            )
        assert container[0].get_hatch() != containers[1 - index // 2][0].get_hatch()
        if kind != "countplot":
            assert container.errorbar is not None
            segments = container.errorbar.lines[2][0].get_segments()
            expected = [
                inverse(center + (index - 1) * span / 3) for center in coords[:2]
            ]
            np.testing.assert_allclose(
                np.asarray(segments)[:, :, 1 if orient == "h" else 0],
                np.repeat(np.asarray(expected)[:, None], 2, axis=1),
            )
    category_axis = ax.yaxis if orient == "h" else ax.xaxis
    assert category_axis.get_scale() == category_scale
    if category_scale == "log":
        assert not isinstance(category_axis.get_major_locator(), FixedLocator)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("category_scale", ["linear", "log"])
def test_native_points_physical_order_reserved_gaps_and_numeric_overlays(
    orient, category_scale
):
    # 30 is a reserved hole; large physical distances without a hole must connect.
    data = {"c": [100, 100, 10, 10, 300, 300], "v": [4, 6, 1, 3, 7, 9]}
    p = _plot(
        "pointplot",
        data,
        native_scale=True,
        orient=orient,
        order=[300, 30, 100, 10],
        errorbar=None,
    )
    p = _scales(p, orient, cat=category_scale)
    ax = p.render().axes[0]
    xy = np.asarray(ax.lines[0].get_xydata())
    np.testing.assert_allclose(
        xy[:, 1 if orient == "h" else 0], [10, np.nan, 100, 300], equal_nan=True
    )
    np.testing.assert_allclose(
        xy[:, 0 if orient == "h" else 1], [2, np.nan, 5, 8], equal_nan=True
    )
    # A numeric primitive shares native units, not the legacy string converter.
    q = _scales(
        mp.plot(data)
        .pointplot("c", "v", native_scale=True, errorbar=None)
        .scatter("c", "v"),
        "v",
        cat=category_scale,
    )
    assert mp.validate(q.spec) == []
    np.testing.assert_array_equal(
        np.asarray(q.render().axes[0].collections[-1].get_offsets())[:, 0], data["c"]
    )


@pytest.mark.parametrize("orient", ["v", "h"])
def test_point_native_log_dodge_caps_and_inverted_limits(orient):
    data = {
        "c": [10] * 4 + [100] * 4,
        "v": [1, 2, 4, 8] * 2,
        "h": ["A"] * 2 + ["B"] * 2 + ["A"] * 2 + ["B"] * 2,
    }
    p = _scales(
        _plot(
            "pointplot",
            data,
            group="h",
            orient=orient,
            native_scale=True,
            dodge=0.4,
            errorbar="pi",
        ),
        orient,
        cat="log",
        value="log",
    )
    (p.ylim if orient == "h" else p.xlim)(300, 1)
    ax = p.render().axes[0]
    lines = [line for line in ax.lines if line.get_label() in ("A", "B")]
    for line, offset in zip(lines, (-0.1, 0.1), strict=True):
        values = np.asarray(line.get_xydata())[:, 1 if orient == "h" else 0]
        np.testing.assert_allclose(values, 10 ** (np.asarray([1, 2]) + offset))
    assert ax.yaxis_inverted() if orient == "h" else ax.xaxis_inverted()
    assert len([c for c in ax.containers if isinstance(c, ErrorbarContainer)]) == 2


@pytest.mark.parametrize(
    "estimator,interval",
    [
        (estimator, interval)
        for estimator in ("mean", "median", "min", "max")
        for interval in (None, "sd", "se", "pi", "ci")
        if interval != "se" or estimator == "mean"
    ],
)
def test_explicit_log_statistics_match_independent_formulas_not_raw_defaults(
    estimator, interval
):
    values = np.asarray([1.0, 2.0, 8.0, 32.0])
    logs = np.log10(values)
    p = mp.plot({"c": [10] * 4, "v": values.tolist()}).pointplot(
        "c",
        "v",
        stat_scale="axis",
        estimator=estimator,
        errorbar=interval,
        n_boot=97,
        seed=19,
    )
    p.yscale("log")
    assert mp.validate(p.spec) == []
    layer = p.spec.panels[0].layers[0]
    point = summarize(p.spec.data.columns, layer, value_scale="log").estimates[0]
    operation = {"mean": np.mean, "median": np.median, "min": np.min, "max": np.max}[
        estimator
    ]
    center = float(operation(logs))
    assert point.value == pytest.approx(10**center)
    if interval is None:
        assert point.lower is None and point.upper is None
    else:
        assert point.lower is not None and point.upper is not None
        if interval in ("sd", "se"):
            delta = np.std(logs, ddof=1) / (np.sqrt(4) if interval == "se" else 1)
            bounds = np.asarray([center - delta, center + delta])
        elif interval == "pi":
            bounds = np.quantile(logs, [0.025, 0.975], method="linear")
        else:
            indices = np.random.default_rng(19).integers(0, 4, size=(97, 4))
            boots = operation(logs[indices], axis=-1)
            bounds = np.quantile(boots, [0.025, 0.975], method="linear")
        np.testing.assert_allclose([point.lower, point.upper], 10**bounds, rtol=2e-14)
        ax = p.render().axes[0]
        errors = ax.containers[0]
        assert isinstance(errors, ErrorbarContainer)
        segment = errors.lines[2][0].get_segments()[0]
        np.testing.assert_allclose(np.asarray(segment)[:, 1], 10**bounds, rtol=2e-14)
    # Axis choice on a linear value axis remains the identity coordinate choice.
    raw = summarize(p.spec.data.columns, layer).estimates[0]
    assert raw.value == pytest.approx(float(operation(values)))


@pytest.mark.parametrize("units", [None, "u"])
def test_log_weighted_and_unit_ci_keep_original_row_pairs_private_seed_and_effective_n(
    units,
):
    data = {
        "c": [10] * 5,
        "v": [1, 10, 100, 1000, -99],
        "w": [1, 2, 1, 3, 0],
        "u": ["a", "a", "b", "b", "x"],
    }
    p = (
        mp.plot(data)
        .pointplot(
            "c", "v", weights="w", units=units, stat_scale="axis", n_boot=113, seed=7
        )
        .yscale("log")
    )
    assert mp.validate(p.spec) == []
    before = np.random.get_state()
    snapshot = p.to_json()
    point = summarize(
        p.spec.data.columns, p.spec.panels[0].layers[0], value_scale="log"
    ).estimates[0]
    logs = np.asarray([0.0, 1.0, 2.0, 3.0])
    weights = np.asarray([1.0, 2.0, 1.0, 3.0])
    rng = np.random.default_rng(7)
    boots = []
    if units is None:
        samples = rng.integers(0, 4, size=(113, 4))
    else:
        samples = []
        clusters = [np.asarray([0, 1]), np.asarray([2, 3])]
        for _ in range(113):
            selected = rng.integers(0, 2, size=2)
            samples.append(
                np.concatenate(
                    [clusters[j][rng.integers(0, 2, size=2)] for j in selected]
                )
            )
    for indices in samples:
        boots.append(np.average(logs[indices], weights=weights[indices]))
    assert point.n == 4 and point.n_units == (2 if units else None)
    assert point.value == pytest.approx(10 ** np.average(logs, weights=weights))
    assert point.lower is not None and point.upper is not None
    np.testing.assert_allclose(
        [point.lower, point.upper], 10 ** np.quantile(boots, [0.025, 0.975]), rtol=2e-14
    )
    assert p.to_json() == snapshot
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize("kind", ["barplot", "countplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("baseline", [0.1, 20.0])
def test_log_bars_explicit_baseline_endpoints_and_label_direction(
    kind, orient, baseline
):
    data = {"c": [10] * 4, "v": [1.0, 2.0, 4.0, 8.0]}
    options = {
        "baseline": baseline,
        "orient": orient,
        "value_labels": True,
        "native_scale": True,
    }
    if kind != "countplot":
        options.update(stat_scale="axis", errorbar="pi")
    p = _scales(_plot(kind, data, **options), orient, cat="log", value="log")
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    rect = ax.patches[0]
    center = 4 if kind == "countplot" else 10 ** np.mean(np.log10(data["v"]))
    np.testing.assert_allclose(_values(rect, orient), [baseline, center])
    label = ax.texts[0]
    assert isinstance(label, Annotation)
    positive = center >= baseline
    bounds = 10 ** np.quantile(np.log10(data["v"]), [0.025, 0.975])
    endpoint = (
        center
        if kind == "countplot"
        else (max(center, bounds[1]) if positive else min(center, bounds[0]))
    )
    np.testing.assert_allclose(
        label.xy, (endpoint, 10) if orient == "h" else (10, endpoint)
    )
    assert label.get_text() == format(center, "g")
    assert (
        label.get_horizontalalignment() == ("left" if positive else "right")
        if orient == "h"
        else label.get_verticalalignment() == ("bottom" if positive else "top")
    )


@pytest.mark.parametrize("orient", ["v", "h"])
def test_native_log_categories_stacked_global_percent_counts_and_center_labels(orient):
    data = {"c": [10, 10, 10, 100, 100], "h": ["A", "A", "B", "A", "B"]}
    p = _scales(
        _plot(
            "countplot",
            data,
            group="h",
            orient=orient,
            stat="percent",
            stack=True,
            native_scale=True,
            value_labels=True,
        ),
        orient,
        cat="log",
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    containers = [c for c in ax.containers if isinstance(c, BarContainer)]
    for container, expected in zip(
        containers, ([(0, 40), (0, 20)], [(40, 60), (20, 40)]), strict=True
    ):
        for rect, values in zip(container, expected, strict=True):
            np.testing.assert_allclose(_values(rect, orient), values)
    labels = [t for t in ax.texts if isinstance(t, Annotation)]
    assert len(labels) == len(ax.texts) == 4
    for text, category in zip(labels, [10, 100, 10, 100], strict=True):
        assert text.xy[1 if orient == "h" else 0] == pytest.approx(category)
    np.testing.assert_allclose(
        [t.xy[0 if orient == "h" else 1] for t in labels], [20, 10, 50, 30]
    )
    assert [t.get_text() for t in ax.texts] == ["40", "20", "20", "20"]


def test_raw_log_mean_unchanged_and_invalid_bounds_never_clipped(
    monkeypatch,
):
    data = {"c": [10, 10], "v": [1, 100]}
    p = mp.plot(data).pointplot("c", "v", errorbar=None).yscale("log")
    assert np.asarray(p.render().axes[0].lines[0].get_ydata())[0] == 50.5
    p = mp.plot(data).pointplot("c", "v", errorbar="sd").yscale("log")
    assert mp.validate(p.spec) == []  # pure core does not compute NumPy intervals
    import mudplot._render as renderer

    monkeypatch.setattr(
        renderer,
        "_draw_stat_ranges",
        lambda *a: pytest.fail("must reject before ranges"),
    )
    with pytest.raises(ValueError, match="interval endpoints must be positive"):
        p.render()


@pytest.mark.parametrize(
    "kind,options,cat,val,message",
    [
        ("barplot", {}, "linear", "log", "positive explicit baseline"),
        ("countplot", {"baseline": 0}, "linear", "log", "positive explicit baseline"),
        ("pointplot", {}, "log", "linear", "native_scale=True"),
        ("pointplot", {"native_scale": 1}, "linear", "linear", "must be boolean"),
        (
            "pointplot",
            {"native_scale": True, "dodge": 1.1},
            "linear",
            "linear",
            "native point dodge",
        ),
        (
            "barplot",
            {"native_scale": True, "bar_width": 1.1},
            "linear",
            "linear",
            "native bar_width",
        ),
        ("pointplot", {"stat_scale": "bad"}, "linear", "linear", "stat_scale"),
        (
            "pointplot",
            {"stat_scale": "axis", "estimator": "sum", "errorbar": None},
            "linear",
            "log",
            "not sum/count",
        ),
        (
            "pointplot",
            {"stat_scale": "axis", "estimator": "count", "errorbar": None},
            "linear",
            "log",
            "not sum/count",
        ),
        (
            "countplot",
            {"stat_scale": "axis"},
            "linear",
            "linear",
            "stat_scale is not supported",
        ),
        ("pointplot", {"baseline": 1}, "linear", "linear", "baseline is not supported"),
        ("barplot", {"baseline": True}, "linear", "linear", "finite raw-value"),
        ("barplot", {"baseline": float("inf")}, "linear", "linear", "finite raw-value"),
        (
            "countplot",
            {"stack": True, "baseline": 0.1},
            "linear",
            "log",
            "linear value axis",
        ),
        (
            "countplot",
            {"stack": True, "baseline": 0},
            "linear",
            "linear",
            "explicit baseline",
        ),
    ],
)
def test_unsupported_or_unsafe_combinations_fail_in_pure_validation(
    kind, options, cat, val, message
):
    p = _scales(_plot(kind, {"c": [10, 10], "v": [1, 4]}, **options), "v", cat, val)
    assert any(message in i for i in mp.validate(p.spec))
    with pytest.raises(ValueError, match=message):
        p.render()


@pytest.mark.parametrize(
    "categories", [["10", "30"], [True, False], [10, float("inf")], [0, 10], [-1, 10]]
)
def test_native_log_rejects_non_numeric_or_non_positive_levels(categories):
    p = (
        mp.plot({"c": categories, "v": [1, 4]})
        .pointplot("c", "v", native_scale=True, errorbar=None)
        .xscale("log")
    )
    assert mp.validate(p.spec)


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
def test_shared_mixed_modes_string_primitives_and_native_secondary_rejected(
    kind,
):
    data = {"c": [10, 10, 30, 30], "v": [1, 2, 3, 4], "s": ["a", "a", "b", "b"]}
    p = _plot(kind, data, native_scale=True)
    getattr(p, kind)("c", *(["v"] if kind != "countplot" else []), panel=0)
    assert any("mixes native and ordinal" in i for i in mp.validate(p.spec))
    p = _plot(kind, data, native_scale=True)
    p.scatter("s", "v")
    assert any("mix string series" in i for i in mp.validate(p.spec))
    p = _plot(kind, data, native_scale=True)
    p.secondary_yaxis("Secondary")
    layer = p.spec.panels[0].layers[0]
    spec = p.spec
    spec.panels[0].layers[0].axis = "y2"
    assert any("primary axes only" in i for i in mp.validate(spec))
    assert layer.native_scale


def test_selected_rows_exclude_missing_zero_weights_and_nonpositive_unselected_values():
    data = {"c": [10, 10, 30, 10, None], "v": [1, 4, -1, 0, 9], "w": [1, 1, 1, 0, 1]}
    p = (
        mp.plot(data)
        .pointplot(
            "c",
            "v",
            order=[10],
            weights="w",
            errorbar=None,
            native_scale=True,
            stat_scale="axis",
        )
        .xscale("log")
        .yscale("log")
    )
    assert mp.validate(p.spec) == []
    assert np.asarray(p.render().axes[0].lines[0].get_ydata())[0] == pytest.approx(2)
    q = (
        mp.plot({"c": [10, 10], "v": [-1, -2]})
        .pointplot("c", "v", estimator="count", errorbar=None)
        .yscale("log")
    )
    assert (
        mp.validate(q.spec) == []
        and np.asarray(q.render().axes[0].lines[0].get_ydata())[0] == 2
    )


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
def test_legacy_ordinal_zero_baseline_and_missing_field_defaults(
    kind,
):
    data = {"c": [10, 10, 30, 30], "v": [1, 3, 4, 6]}
    opts = {} if kind == "countplot" else {"errorbar": None}
    p = _plot(kind, data, **opts)
    ax = p.render().axes[0]
    assert p.spec.panels[0].layers[0].baseline is None
    if kind == "pointplot":
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), [0, 1])
    else:
        rectangles = [r for r in ax.patches if isinstance(r, Rectangle)]
        assert len(rectangles) == len(ax.patches) == 2
        np.testing.assert_allclose(
            [r.get_x() + r.get_width() / 2 for r in rectangles], [0, 1]
        )
        assert [r.get_y() for r in rectangles] == [0, 0]
    layer = LayerSpec.from_dict(
        {"type": kind, "x": "c", **({"y": "v"} if kind != "countplot" else {})}
    )
    assert (
        isinstance(layer, LayerSpec)
        and layer.baseline is None
        and not layer.native_scale
    )


def test_shape_errors_native_log_inverse_and_baseline_overflow_fail_clearly():
    for order in (cast(Any, 7), ["x", 10]):
        p = mp.plot({"c": [10, 10], "v": [1, 4]}).pointplot(
            "c", "v", order=order, native_scale=True
        )
        assert mp.validate(p.spec)
    p = (
        mp.plot({"c": [10, 10], "v": [1e-300, 1e300]})
        .pointplot("c", "v", stat_scale="axis", errorbar=("sd", 10))
        .yscale("log")
    )
    with pytest.raises(ValueError, match="inverse log statistics"):
        p.render()
    p = (
        mp.plot({"c": [1e308, 1e308], "v": [1, 4]})
        .barplot("c", "v", native_scale=True, errorbar=None)
        .xscale("log")
    )
    with pytest.raises(ValueError, match="finite positive range"):
        p.render()
    p = mp.plot({"c": [10, 10], "v": [1e308, 1e308]}).barplot(
        "c", "v", baseline=-1e308, errorbar=None
    )
    with np.errstate(over="ignore"), pytest.raises(ValueError, match="bar span"):
        p.render()


def test_editor_json_actions_schema_and_native_log_exports_repeat_without_global_rng(
    tmp_path,
):
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    session = EditorSession()
    session.dispatch_safe(A.SetData({"c": [10, 10, 30, 30], "v": [1, 4, 4, 16]}))
    before = np.random.get_state()
    session.dispatch_safe(A.SetScale("x", "log"))
    session.dispatch_safe(A.SetScale("y", "log"))
    fields = {
        "x": "c",
        "y": "v",
        "native_scale": True,
        "stat_scale": "axis",
        "baseline": 0.1,
        "value_labels": True,
        "stat": {"errorbar": "pi"},
    }
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {"layer_type": "barplot", "layer_json": json.dumps(fields)},
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    spec = session.store.state
    jsonschema.Draft202012Validator(mp.json_schema()).validate(spec.to_dict())
    p = mp.Plot.from_json(mp.to_json(spec))
    assert mp.apply([A.action_to_dict(a) for a in session.store.history]) == p.spec
    for fmt in ("png", "pdf", "svg"):
        one, two = tmp_path / f"one.{fmt}", tmp_path / f"two.{fmt}"
        plt.close(p.save(str(one)))
        plt.close(p.save(str(two)))
        assert one.read_bytes() == two.read_bytes()
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
