import sqlite3
from datetime import date, datetime, time, timezone

import mudplot as mp
import pytest
from mudplot.data import to_columns


def test_none_and_dict():
    assert to_columns(None) == {}
    assert to_columns({"x": [1, 2], "y": [3, 4]}) == {"x": [1, 2], "y": [3, 4]}


def test_list_of_records():
    recs = [{"x": 1, "y": 4}, {"x": 2, "y": 5}]
    assert to_columns(recs) == {"x": [1, 2], "y": [4, 5]}
    assert to_columns([{1: 4}, {1: 5}]) == {"1": [4, 5]}


def test_records_ragged_keys_fill_none():
    recs = [{"x": 1}, {"x": 2, "y": 9}]
    assert to_columns(recs) == {"x": [1, 2], "y": [None, 9]}


def test_list_of_rows_autonames():
    assert to_columns([[1, 4], [2, 5]]) == {"c0": [1, 2], "c1": [4, 5]}


def test_flat_list_is_rejected():
    with pytest.raises(TypeError):
        to_columns([1, 2, 3])


def test_sqlite_connection_with_query():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table t(x int, y int)")
    conn.executemany("insert into t values (?,?)", [(1, 4), (2, 5)])
    cols = to_columns(
        conn, query="select x, y from t where x > ? order by x", params=(1,)
    )
    assert cols == {"x": [2], "y": [5]}


def test_sqlite_executed_cursor():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table t(a int, b int)")
    conn.execute("insert into t values (7, 8)")
    cur = conn.execute("select a, b from t")
    assert to_columns(cur) == {"a": [7], "b": [8]}


def test_numpy_structured_array():
    np = pytest.importorskip("numpy")
    arr = np.array([(1, 4.0), (2, 5.0)], dtype=[("x", "i4"), ("y", "f8")])
    assert to_columns(arr) == {"x": [1, 2], "y": [4.0, 5.0]}


def test_numpy_2d_array_autonames():
    np = pytest.importorskip("numpy")
    assert to_columns(np.array([[1, 4], [2, 5]])) == {"c0": [1, 2], "c1": [4, 5]}


def test_numpy_scalars_become_plain_json_values():
    np = pytest.importorskip("numpy")
    assert to_columns(
        {
            "count": np.int64(2),
            "when": np.datetime64("2026-01-01"),
            "missing": np.float64("nan"),
        }
    ) == {"count": [2], "when": ["2026-01-01"], "missing": [None]}


def test_pandas_dataframe():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert to_columns(df) == {"x": [1, 2], "y": [3, 4]}


def test_arrow_protocol_takes_precedence_over_dataframe_duck_typing():
    class ArrowLike:
        columns = (object(),)

        def __getitem__(self, key):
            raise AssertionError("Arrow tables must use to_pydict")

        def to_pydict(self):
            return {"x": [date(2026, 1, 1), None], "y": [1.0, float("nan")]}

    assert to_columns(ArrowLike()) == {
        "x": ["2026-01-01", None],
        "y": [1.0, None],
    }


def test_common_missing_and_temporal_values_are_json_safe():
    data = {
        "x": [date(2026, 1, 1), datetime(2026, 1, 2, 3, tzinfo=timezone.utc)],
        "y": [1.0, float("nan")],
        "at": [time(9, 30), time(10, 45)],
    }
    p = mp.plot(data).line("x", "y")
    assert p.spec.data.columns == {
        "x": ["2026-01-01", "2026-01-02T03:00:00+00:00"],
        "y": [1.0, None],
        "at": ["09:30:00", "10:45:00"],
    }
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert p.render().axes[0].lines


def test_pandas_nullable_and_datetime_columns_cross_json_and_render_boundaries():
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame(
        {
            "x": pd.date_range("2026-01-01", periods=3),
            "y": pd.Series([1, pd.NA, 3], dtype="Int64"),
            "g": pd.Series(["first", pd.NA, "last"], dtype="string"),
        }
    )
    line = mp.plot(frame).line("x", "y")
    grouped = mp.plot(frame).scatter("x", "y", group="g")

    assert line.spec.data.columns == {
        "x": [
            "2026-01-01T00:00:00",
            "2026-01-02T00:00:00",
            "2026-01-03T00:00:00",
        ],
        "y": [1, None, 3],
        "g": ["first", None, "last"],
    }
    for plot in (line, grouped):
        assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
        figure = plot.render()
        assert figure.axes
    assert figure.axes[0].get_legend_handles_labels()[1] == ["first", "last"]


def test_plot_accepts_parameterized_query():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table t(x int, y int)")
    conn.execute("insert into t values (1, 2)")
    p = mp.plot(conn, query="select x, y from t where x = ?", params=(1,)).line(
        "x", "y"
    )
    assert p.spec.data.columns == {"x": [1], "y": [2]}


def test_unsupported_type_raises():
    with pytest.raises(TypeError):
        to_columns(object())
