"""Raw-coordinate event marks, not an axis-fraction rug or aggregated count."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import EventCollection


@pytest.mark.parametrize("line_width", [0, 2])
def test_event_marks_keep_source_duplicates_raw_geometry_and_style(line_width):
    source = {"event": [2.0, 1.0, 2.0]}
    p = mp.plot(source).eventplot(
        "event",
        offset=0.5,
        length=0.4,
        color="#225577",
        line_width=line_width,
        line_style="--",
        alpha=0.4,
        label="given",
    )
    before = copy.deepcopy(p.spec)
    assert (
        mp.validate(p.spec) == []
        and mp.from_json(p.to_json()) == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    figure = p.render()
    try:
        marks = figure.axes[0].collections[0]
        assert isinstance(marks, EventCollection)
        np.testing.assert_array_equal(marks.get_positions(), [1, 2, 2])
        np.testing.assert_allclose(
            marks.get_segments(),
            [[[1, 0.7], [1, 0.3]], [[2, 0.7], [2, 0.3]], [[2, 0.7], [2, 0.3]]],
        )
        assert (
            marks.get_lineoffset() == 0.5
            and marks.get_linelength() == 0.4
            and marks.get_alpha() == 0.4
            and marks.get_label() == "given"
        )
        np.testing.assert_allclose(marks.get_linewidth(), line_width)
        styles = marks.get_linestyle()
        assert isinstance(styles, list)
        assert (styles[0][1] is None) == (line_width == 0)
        assert figure.axes[0].get_legend() is not None
        assert p.spec == before and p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_single_event_default_length_and_secondary_axis():
    p = mp.plot({"event": [-2.0]}).secondary_yaxis().eventplot("event", axis="y2")
    figure = p.render()
    try:
        assert not figure.axes[0].collections
        marks = figure.axes[1].collections[0]
        assert isinstance(marks, EventCollection)
        np.testing.assert_array_equal(marks.get_segments(), [[[-2, 0.5], [-2, -0.5]]])
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "values", [[], [True], [None], ["1"], [float("nan")], [float("inf")]]
)
def test_invalid_events_fail_before_artists(values):
    p = mp.plot({"event": values}).eventplot("event")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "offset,length",
    [
        (True, 1),
        (float("inf"), 1),
        (0, 0),
        (0, -1),
        (0, True),
        (0, float("nan")),
        (0, float("inf")),
        (1e300, 1),
        (1.7e308, 1e308),
    ],
)
def test_nonrepresentable_or_invalid_mark_geometry_preserves_output(
    tmp_path, offset, length
):
    p = mp.plot({"event": [1, 2]}).eventplot("event", offset=offset, length=length)
    old = tmp_path / "old.png"
    old.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.save(old)
    assert old.read_bytes() == b"previous" and plt.get_fignums() == before


@pytest.mark.parametrize(
    "style",
    [
        {"orient": "h"},
        {"group": "event"},
        {"weights": "event"},
        {"semantics": {"hue": "event"}},
        {"density": True},
        {"colorbar": True},
        {"marker": "s"},
        {"line_width": True},
    ],
)
def test_unused_mappings_are_rejected(style):
    p = mp.plot({"event": [1, 2]}).eventplot("event", **style)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("axis", ["x", "y"])
def test_linear_only_subset_does_not_hide_log_geometry(axis):
    p = mp.plot({"event": [1, 2]}).eventplot("event", offset=2)
    if axis == "x":
        p.xscale("log")
    else:
        p.yscale("log")
    with pytest.raises(ValueError, match="linear"):
        p.render()


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_event_marks_reject_other_projections(projection):
    p = mp.plot({"event": [1, 2]}).eventplot("event")
    if projection == "polar":
        p.projection_polar()
    else:
        p.projection3d()
    with pytest.raises(ValueError):
        p.render()


def test_setdata_updates_events_without_aggregation_and_keeps_selection_limits():
    p = mp.plot({"event": [1, 2], "g": ["A", "B"]}).eventplot(
        "event", offset=-1, length=2
    )
    p.dispatch(mp.actions.SetData({"event": [3, 2, 3], "g": ["A", "B", "A"]}))
    figure = p.render()
    try:
        marks = figure.axes[0].collections[0]
        assert isinstance(marks, EventCollection)
        np.testing.assert_array_equal(marks.get_positions(), [2, 3, 3])
        assert mp.apply(p.action_log) == p.spec
    finally:
        plt.close(figure)
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
    spec = p.spec
    spec.panels[0].dropna = ["event"]
    assert any("does not support panel filters" in issue for issue in mp.validate(spec))


def test_event_budget_and_capability_are_explicit():
    p = mp.plot({"event": list(range(10001))}).eventplot("event")
    assert any("10000" in issue for issue in mp.validate(p.spec))
    assert mp.capabilities()["layers"]["eventplot"]["required"] == ["x"]
