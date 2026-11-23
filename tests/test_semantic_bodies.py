"""Native body heights are independent of semantic styling and reserved slots."""

import mudplot as mp
import pytest


@pytest.fixture
def table():
    return {
        "x": [0.1, 0.2, 0.3, 1.5, 4],
        "cat": ["A", "A", "A", "B", "B"],
        "h": [10, 10, 20, 20, 10],
        "w": [1, 3, 2, 4, 9],
        "style": ["a", "b", "a", "a", "a"],
    }


def bodies(axes):
    from matplotlib.patches import Rectangle

    return [p for p in axes.patches if isinstance(p, Rectangle)]


@pytest.mark.parametrize("orient", ["v", "h"])
def test_hist_in_range_and_hue_denominator(table, orient):
    from matplotlib import pyplot as plt

    for common in (True, False):
        role = mp.SemanticSpec(hue="h", hue_kind="numeric", style="style")
        p = mp.plot(table).hist(
            "x",
            bins=[0, 1, 3],
            weights="w",
            stat="density",
            multiple="dodge",
            semantics=role,
            orient=orient,
            common_norm=common,
        )
        figure = p.render()
        try:
            get = "get_height" if orient == "v" else "get_width"
            heights = [getattr(b, get)() for b in bodies(figure.axes[0])]
            expected = (
                [0.1, 0, 0.3, 0, 0.2, 0.2]
                if common
                else [0.25, 0, 0.75, 0, 1 / 3, 1 / 3]
            )
            assert heights == pytest.approx(expected)
        finally:
            plt.close(figure)
        assert p.spec == mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec
        assert p.spec.data.columns == table


def test_weighted_count_uses_effective_hue_not_tuple(table):
    from matplotlib import pyplot as plt

    p = mp.plot(table).countplot(
        "cat",
        weights="w",
        stat="proportion",
        normalize_scope="group",
        semantics=mp.SemanticSpec(hue="h", hue_kind="numeric", style="style"),
    )
    figure = p.render()
    try:
        assert [b.get_height() for b in bodies(figure.axes[0])] == pytest.approx(
            [1 / 13, 9 / 13, 3 / 13, 1 / 3, 2 / 3]
        )
    finally:
        plt.close(figure)
    assert not mp.validate(p.spec)


def test_unfilled_hist_and_count_reject_competing_hue(table):
    role = mp.SemanticSpec(hue="h", hue_kind="numeric")
    p = mp.plot(table).hist(
        "x", stat="count", element="step", edge_color="black", semantics=role
    )
    assert any("edge_color cannot override" in e for e in mp.validate(p.spec))
    q = mp.plot(table).countplot("cat", group="style", semantics=role)
    assert any("conflicts with legacy group" in e for e in mp.validate(q.spec))


@pytest.mark.parametrize("twin", [False, True])
def test_clocked_hist_and_empty_reservation(twin):
    from matplotlib import pyplot as plt

    source = {
        "date": ["2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"],
        "h": [True, 1],
        "mass": [2, 3],
    }
    p = mp.plot(source)
    if twin:
        p.secondary_yaxis("Mass").date_axis("x")
    else:
        p.date_axis("y")
    p.hist(
        "date",
        stat="count",
        bins=[18261, 18264],
        orient="v" if twin else "h",
        axis="y2" if twin else "y",
        weights="mass",
        multiple="dodge",
        semantics=mp.SemanticSpec(hue="h", hue_order=[True, 1, "reserved"]),
    )
    figure = p.render()
    try:
        axis = (
            next(ax for ax in figure.axes if ax.get_ylabel() == "Mass")
            if twin
            else figure.axes[0]
        )
        bars = bodies(axis)
        assert [
            bar.get_height() if twin else bar.get_width() for bar in bars
        ] == pytest.approx([2, 3])
        assert [bar.get_x() if twin else bar.get_y() for bar in bars] == pytest.approx(
            [18261, 18262]
        )
    finally:
        plt.close(figure)
    assert p.spec.data.columns == source
