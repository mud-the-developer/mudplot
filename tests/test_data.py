import sqlite3

import mudplot as mp
import pytest
from mudplot.data import to_columns


def test_none_and_dict():
    assert to_columns(None) == {}
    assert to_columns({"x": [1, 2], "y": [3, 4]}) == {"x": [1, 2], "y": [3, 4]}


def test_list_of_records():
    recs = [{"x": 1, "y": 4}, {"x": 2, "y": 5}]
    assert to_columns(recs) == {"x": [1, 2], "y": [4, 5]}


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
    cols = to_columns(conn, query="select x, y from t order by x")
    assert cols == {"x": [1, 2], "y": [4, 5]}


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


def test_pandas_dataframe():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert to_columns(df) == {"x": [1, 2], "y": [3, 4]}


def test_plot_accepts_query():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table t(x int, y int)")
    conn.execute("insert into t values (1, 2)")
    p = mp.plot(conn, query="select x, y from t").line("x", "y")
    assert p.spec.data.columns == {"x": [1], "y": [2]}


def test_unsupported_type_raises():
    with pytest.raises(TypeError):
        to_columns(object())
