"""DATA-01/06: real optional table libraries, without making them core dependencies."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal

import mudplot as mp
import numpy as np
import pytest
from mudplot.data import to_columns


@pytest.fixture(params=["pyarrow", "polars"])
def table_factory(request):
    if request.param == "pyarrow":
        pa = pytest.importorskip("pyarrow")
        return pa.table, lambda table: table.to_pydict()
    pl = pytest.importorskip("polars")
    return pl.DataFrame, lambda frame: frame.to_dict(as_series=False)


def test_table_scalars_keep_integer_precision_boolean_unicode_and_nulls(table_factory):
    create, snapshot = table_factory
    table = create(
        {
            "id": [2**53 + 1, 2**63 - 1, None],
            "value": [1.25, float("nan"), None],
            "group": ["Ω", "β", None],
            "flag": [True, False, None],
            "label": ["한글", "emoji 😀", ""],
        }
    )
    before = snapshot(table)
    plot = mp.plot(table)
    expected = {
        "id": [2**53 + 1, 2**63 - 1, None],
        "value": [1.25, None, None],
        "group": ["Ω", "β", None],
        "flag": [True, False, None],
        "label": ["한글", "emoji 😀", ""],
    }
    assert plot.spec.data.columns == expected
    assert [type(value) for value in plot.spec.data.columns["id"]] == [
        int,
        int,
        type(None),
    ]
    assert [type(value) for value in plot.spec.data.columns["flag"]] == [
        bool,
        bool,
        type(None),
    ]
    assert mp.Plot.from_json(plot.to_json()).spec.data.columns == expected
    np.testing.assert_equal(snapshot(table), before)


def test_table_dates_microseconds_and_utc_keep_iso_values_and_source(table_factory):
    create, snapshot = table_factory
    table = create(
        {
            "date": [date(2026, 1, 2), None],
            "time": [time(9, 30, 1, 123456), None],
            "timestamp": [
                datetime(2026, 1, 2, 9, 30, 1, 123456, tzinfo=timezone.utc),
                None,
            ],
        }
    )
    before = snapshot(table)
    expected = {
        "date": ["2026-01-02", None],
        "time": ["09:30:01.123456", None],
        "timestamp": ["2026-01-02T09:30:01.123456+00:00", None],
    }
    assert to_columns(table) == expected
    plot = mp.plot(table)
    assert mp.Plot.from_json(plot.to_json()).spec.data.columns == expected
    np.testing.assert_equal(snapshot(table), before)


def test_empty_optional_table_keeps_named_empty_columns(table_factory):
    create, snapshot = table_factory
    table = create({"x": [], "y": [], "g": []})
    before = snapshot(table)
    assert to_columns(table) == {"x": [], "y": [], "g": []}
    assert mp.Plot.from_json(mp.plot(table).to_json()).spec.data.columns == before
    np.testing.assert_equal(snapshot(table), before)


@pytest.mark.parametrize(
    "value", [float("inf"), -float("inf"), Decimal("1.1234567890123456789")]
)
def test_optional_tables_do_not_coerce_infinity_or_decimal_into_valid_json(
    table_factory, value
):
    create, snapshot = table_factory
    table = create({"value": [value]})
    before = snapshot(table)
    plot = mp.plot(table)
    assert plot.spec.data.columns["value"] == [value]
    assert type(plot.spec.data.columns["value"][0]) is type(value)
    with pytest.raises(ValueError, match=r"Decimal|finite"):
        plot.to_json()
    np.testing.assert_equal(snapshot(table), before)


def test_real_arrow_duplicate_names_fail_before_to_pydict_can_drop_data():
    pa = pytest.importorskip("pyarrow")
    table = pa.Table.from_arrays([pa.array([1]), pa.array([2])], names=["x", "x"])
    with pytest.raises(ValueError, match="PyArrow table column names must be unique"):
        to_columns(table)
    assert table.column(0).to_pylist() == [1] and table.column(1).to_pylist() == [2]
