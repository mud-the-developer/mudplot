"""DATA-03: missing observations stay aligned and never become named categories."""

from __future__ import annotations

import copy
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("x", [["A", None, "B"], ["2026-01-01", None, "2026-01-03"]])
@pytest.mark.parametrize("kind", ["line", "scatter"])
@pytest.mark.parametrize("ordered", [False, True])
def test_missing_categorical_x_never_creates_a_none_category(x, kind, ordered):
    raw = {"x": x, "y": [1, 99, 3], "g": ["A"] * 3}
    before = copy.deepcopy(raw)
    plot = mp.plot(raw)
    getattr(plot, kind)(
        "x", "y", group="g", **({"hue_order": ["A"]} if ordered else {})
    )
    assert mp.validate(plot.spec) == []
    ax = plot.render().axes[0]
    assert [text.get_text() for text in ax.get_xticklabels()] == [x[0], x[2]]
    if kind == "line":
        np.testing.assert_allclose(
            np.asarray(ax.lines[0].get_xdata(), dtype=float),
            [0, np.nan, 1],
            equal_nan=True,
        )
        np.testing.assert_allclose(
            np.asarray(ax.lines[0].get_ydata(), dtype=float), [1, 99, 3]
        )
    else:
        points = ax.collections[0]
        assert isinstance(points, PathCollection)
        np.testing.assert_allclose(
            np.ma.asarray(points.get_offsets()).compressed(), [0, 1, 1, 3]
        )
    assert plot.spec.data.columns == before and raw == before
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec


def test_literal_none_label_is_distinct_from_missing_x_across_shared_axes_and_twins():
    raw = {"x": ["A", None, "None"], "other": ["None", "B", None], "y": [1, 2, 3]}
    plot = mp.plot(raw).layout(1, 2).share(x="all").line("x", "y")
    plot.secondary_yaxis().line("other", "y", axis="y2")
    plot.line("other", "y", panel=1)
    figure = plot.render()
    axes = [axis for axis in figure.axes if axis.lines]
    assert len(axes) == 3
    assert all(
        [text.get_text() for text in axis.get_xticklabels()] == ["A", "None", "B"]
        for axis in axes
    )
    np.testing.assert_allclose(
        np.asarray(axes[0].lines[0].get_xdata(), dtype=float),
        [0, np.nan, 1],
        equal_nan=True,
    )
    for axis in axes[1:]:
        np.testing.assert_allclose(
            np.asarray(axis.lines[0].get_xdata(), dtype=float),
            [1, 2, np.nan],
            equal_nan=True,
        )


@pytest.mark.parametrize(
    "shape",
    [
        "mapping",
        "records",
        "rows",
        "numpy",
        "structured",
        "pandas",
        "sql",
        "cursor",
        "to_dict",
        "pyarrow",
        "arrow_chunks",
        "arrow_dictionary",
        "polars",
        "polars_categorical",
    ],
)
def test_adapter_values_and_layer_missing_cohorts_agree(shape):
    raw = {
        "x": [0, 0, 1, 1, 2, 2],
        "y": [1, None, 3, 5, None, 7],
        "g": ["A"] * 3 + ["B"] * 3,
    }
    rows = list(zip(*raw.values(), strict=True))
    connection = None
    options = {}
    if shape == "mapping":
        source = copy.deepcopy(raw)
        snapshot = copy.deepcopy(source)
    elif shape == "records":
        source = [dict(zip(raw, row, strict=True)) for row in rows]
        snapshot = copy.deepcopy(source)
    elif shape == "rows":
        source = copy.deepcopy(rows)
        snapshot = copy.deepcopy(source)
    elif shape == "numpy":
        source = np.array(rows, dtype=object)
        snapshot = source.copy()
    elif shape == "structured":
        source = np.array(rows, dtype=[("x", "i8"), ("y", "f8"), ("g", "U1")])
        snapshot = source.copy()
    elif shape == "pandas":
        pd = pytest.importorskip("pandas")
        source = pd.DataFrame(raw).astype({"x": "Int64", "y": "Float64", "g": "string"})
        snapshot = source.copy(deep=True)
    elif shape == "to_dict":

        class DictLike:
            def to_dict(self):
                return raw

        source = DictLike()
        snapshot = copy.deepcopy(raw)
    elif shape in ("pyarrow", "arrow_chunks", "arrow_dictionary"):
        pa = pytest.importorskip("pyarrow")
        source = pa.table(raw)
        if shape == "arrow_chunks":
            source = pa.concat_tables([source.slice(0, 3), source.slice(3, 3)])
            assert source.column("x").num_chunks == 2
        elif shape == "arrow_dictionary":
            source = source.set_column(2, "g", source.column("g").dictionary_encode())
        snapshot = source.slice(0)
    elif shape in ("polars", "polars_categorical"):
        pl = pytest.importorskip("polars")
        source = pl.DataFrame(raw)
        if shape == "polars_categorical":
            source = source.with_columns(pl.col("g").cast(pl.Categorical))
        snapshot = source.clone()
    else:
        assert shape in ("sql", "cursor")
        connection = sqlite3.connect(":memory:")
        connection.execute("create table observations(x int, y real, g text)")
        connection.executemany("insert into observations values (?,?,?)", rows)
        source = (
            connection.execute("select x,y,g from observations order by rowid")
            if shape == "cursor"
            else connection
        )
        if shape == "sql":
            options = {"query": "select x,y,g from observations order by rowid"}
        snapshot = rows
    try:
        plot = mp.plot(source, **options).layout(1, 3).size(12, 3)
        names = list(plot.spec.data.columns)
        expected = dict(zip(names, raw.values(), strict=True))
        assert plot.spec.data.columns == expected
        x, y, group = names
        plot.line(x, y, group=group).scatter(x, y, group=group, panel=1)
        plot.lineplot(x, y, group=group, errorbar=None, panel=2)
        raw_axis, point_axis, estimate_axis = plot.render().axes
        for line, expected_y in zip(
            raw_axis.lines, ([1, np.nan, 3], [5, np.nan, 7]), strict=True
        ):
            np.testing.assert_allclose(
                np.asarray(line.get_ydata(), dtype=float), expected_y, equal_nan=True
            )
        for points, expected_xy in zip(
            point_axis.collections, ([0, 1, 1, 3], [1, 5, 2, 7]), strict=True
        ):
            assert isinstance(points, PathCollection)
            np.testing.assert_allclose(
                np.ma.asarray(points.get_offsets()).compressed(), expected_xy
            )
        for line, expected_xy in zip(
            estimate_axis.lines, (([0, 1], [1, 3]), ([1, 2], [5, 7])), strict=True
        ):
            np.testing.assert_allclose(
                np.asarray(line.get_xdata(), dtype=float), expected_xy[0]
            )
            np.testing.assert_allclose(
                np.asarray(line.get_ydata(), dtype=float), expected_xy[1]
            )
        assert plot.spec.data.columns == expected
        assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
        if shape in ("mapping", "records", "rows"):
            assert source == snapshot
        elif shape in ("numpy", "structured"):
            assert isinstance(source, np.ndarray) and isinstance(snapshot, np.ndarray)
            for name in source.dtype.names or (None,):
                actual = source if name is None else source[name]
                original = snapshot if name is None else snapshot[name]
                np.testing.assert_equal(actual, original)
        elif shape == "pandas":
            pd.testing.assert_frame_equal(source, snapshot)
        elif shape in (
            "pyarrow",
            "arrow_chunks",
            "arrow_dictionary",
            "polars",
            "polars_categorical",
        ):
            equals = getattr(source, "equals", None)
            assert callable(equals) and equals(snapshot)
        elif shape == "to_dict":
            assert raw == snapshot
        else:
            assert connection is not None
            assert (
                connection.execute(
                    "select x,y,g from observations order by rowid"
                ).fetchall()
                == snapshot
            )
            if shape == "cursor":
                assert isinstance(source, sqlite3.Cursor)
                assert source.execute("select 1").fetchone() == (1,)
    finally:
        if connection is not None:
            connection.close()


def test_pandas_nat_x_is_missing_instead_of_a_literal_tick():
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame(
        {"x": pd.to_datetime(["2026-01-01", None, "2026-01-03"]), "y": [1, 99, 3]}
    )
    before = frame.copy(deep=True)
    plot = mp.plot(frame).line("x", "y")
    assert plot.spec.data.columns["x"] == [
        "2026-01-01T00:00:00",
        None,
        "2026-01-03T00:00:00",
    ]
    ax = plot.render().axes[0]
    assert len(ax.get_xticklabels()) == 2
    assert np.isnan(np.asarray(ax.lines[0].get_xdata(), dtype=float)[1])
    pd.testing.assert_frame_equal(frame, before)
