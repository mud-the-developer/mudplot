"""DATA-07: parameter forwarding and the lifetime of owned versus borrowed cursors."""

from __future__ import annotations

import sqlite3

import pytest
from mudplot.data import to_columns


@pytest.mark.parametrize("failure", [None, "execute", "fetch", "shape", "duplicate"])
def test_connection_query_closes_only_its_own_cursor_even_on_failure(failure):
    events = []
    query = "select x from observations where label = ?"
    params = ("x'); drop table observations; --",)

    class Cursor:
        description = (("x",), ("x",)) if failure == "duplicate" else (("x",),)

        def execute(self, statement, values):
            assert statement is query and values is params
            events.append("execute")
            if failure == "execute":
                raise RuntimeError("execute failed")

        def fetchall(self):
            events.append("fetch")
            if failure == "fetch":
                raise RuntimeError("fetch failed")
            return [[1, 2]] if failure == "shape" else [[1]]

        def close(self):
            events.append("cursor-close")

    class Connection:
        def cursor(self):
            events.append("cursor")
            return Cursor()

        def close(self):
            raise AssertionError("caller owns connection")

        def commit(self):
            raise AssertionError("adapter must not commit")

        def rollback(self):
            raise AssertionError("adapter must not roll back")

    if failure is None:
        assert to_columns(Connection(), query=query, params=params) == {"x": [1]}
    else:
        with pytest.raises((RuntimeError, ValueError)):
            to_columns(Connection(), query=query, params=params)
    assert events[-1] == "cursor-close" and events.count("cursor-close") == 1


def test_minimal_connection_cursor_without_close_keeps_duck_protocol_support():
    class Cursor:
        description = (("x",),)

        def execute(self, query, params):
            assert query == "select ? as x" and params == (1,)

        def fetchall(self):
            return [[1]]

    class Connection:
        def cursor(self):
            return Cursor()

    assert to_columns(Connection(), query="select ? as x", params=(1,)) == {"x": [1]}


@pytest.mark.parametrize("execute_fails", [False, True])
def test_owned_cursor_close_failure_is_not_silently_swallowed(execute_fails):
    class Cursor:
        description = (("x",),)

        def execute(self, query, params):
            if execute_fails:
                raise ValueError("execute failed")

        def fetchall(self):
            return [[1]]

        def close(self):
            raise RuntimeError("close failed")

    class Connection:
        def cursor(self):
            return Cursor()

    with pytest.raises(RuntimeError, match="close failed") as caught:
        to_columns(Connection(), query="select x")
    if execute_fails:
        assert isinstance(caught.value.__context__, ValueError)
        assert str(caught.value.__context__) == "execute failed"


def test_borrowed_cursor_is_not_closed_and_remains_reusable():
    connection = sqlite3.connect(":memory:")
    cursor = connection.execute("select 1 as x")
    try:
        assert to_columns(cursor) == {"x": [1]}
        assert cursor.execute("select 2 as y").fetchone() == (2,)
        assert connection.execute("select 3").fetchone() == (3,)
    finally:
        cursor.close()
        connection.close()


def test_sqlite_named_values_are_bound_without_commit_or_connection_close():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("create table observations(id int, label text, value real)")
        probe = "quoted ' value; --"
        connection.executemany(
            "insert into observations values (?,?,?)",
            [(1, probe, None), (2, "other", 4.5)],
        )
        assert connection.in_transaction
        columns = to_columns(
            connection,
            query="select id,label,value from observations where label = :label",
            params={"label": probe},
        )
        assert columns == {"id": [1], "label": [probe], "value": [None]}
        assert connection.in_transaction
        assert connection.execute("select count(*) from observations").fetchone() == (
            2,
        )
    finally:
        connection.close()
