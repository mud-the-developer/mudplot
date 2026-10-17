"""DATA-06: normalize supported scalars, never silently coerce unsupported objects."""

from __future__ import annotations

from decimal import Decimal

import mudplot as mp
import numpy as np
import pytest
from mudplot.data import to_columns


@pytest.mark.parametrize(
    "value,expected",
    [
        (np.int8(-3), -3),
        (np.int64(-(2**63)), -(2**63)),
        (np.uint64(2**64 - 1), 2**64 - 1),
        (np.float16(1.25), 1.25),
        (np.float32(1.25), 1.25),
        (np.float64(1.25), 1.25),
        (np.bool_(True), True),
        (np.bool_(False), False),
        (np.str_("한글 Ω 😀"), "한글 Ω 😀"),
        (np.float16("nan"), None),
        (np.float32("nan"), None),
        (np.float64("nan"), None),
        (np.longdouble("nan"), None),
        (np.datetime64("NaT", "ns"), None),
        (np.timedelta64("NaT", "ns"), None),
    ],
)
@pytest.mark.parametrize("shape", ["mapping", "records", "object-array"])
def test_supported_numpy_scalars_cross_json_with_correct_builtin_values(
    value, expected, shape
):
    if shape == "mapping":
        source = {"value": [value]}
    elif shape == "records":
        source = [{"value": value}]
    else:
        source = {"value": np.array([value], dtype=object)}
    plot = mp.plot(source)
    restored = mp.Plot.from_json(plot.to_json()).spec.data.columns["value"][0]
    assert type(restored) is type(expected) and restored == expected


@pytest.mark.parametrize(
    "value",
    [
        Decimal("1.1234567890123456789"),
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        np.longdouble("1.1234567890123456789"),
        complex(1, 2),
        np.complex128(complex(float("nan"), 0)),
    ],
)
@pytest.mark.parametrize("shape", ["mapping", "records", "object-array"])
def test_unsupported_scalars_remain_objects_until_explicit_json_rejection(value, shape):
    source = (
        {"value": [value]}
        if shape == "mapping"
        else [{"value": value}]
        if shape == "records"
        else {"value": np.array([value], dtype=object)}
    )
    columns = to_columns(source)
    assert columns["value"][0] is value
    spec = mp.FigureSpec()
    spec.data.columns = columns
    with pytest.raises(ValueError) as caught:
        mp.to_json(spec)
    assert type(value).__name__ in str(caught.value)


def test_nonreflexive_custom_object_is_not_treated_as_missing_or_stringified():
    class Value:
        def __ne__(self, other):
            raise AssertionError("unknown objects are not missing-value sentinels")

        def __str__(self):
            raise AssertionError("unknown objects must not be stringified")

    value = Value()
    columns = to_columns({"value": [value]})
    assert columns["value"][0] is value
    spec = mp.FigureSpec()
    spec.data.columns = columns
    with pytest.raises(ValueError, match="Value is not a JSON value"):
        mp.to_json(spec)


def test_fresh_same_type_item_result_does_not_recurse_forever():
    calls = []

    class Value:
        def item(self):
            calls.append("item")
            return Value()

    value = Value()
    assert to_columns({"value": [value]})["value"][0] is value
    assert calls == ["item"]


def test_item_conversion_cycle_is_not_followed_through_unsupported_classes():
    calls = []

    class First:
        def item(self):
            calls.append("first")
            return Second()

    class Second:
        def item(self):
            calls.append("second")
            return First()

    value = First()
    assert to_columns({"value": [value]})["value"][0] is value
    assert calls == ["first"]


def test_item_protocol_returning_a_plain_supported_value_stays_supported():
    class Value:
        def item(self):
            return 2**80 + 1

    assert to_columns({"value": [Value()]}) == {"value": [2**80 + 1]}


def test_pandas_known_missing_scalars_remain_null():
    pd = pytest.importorskip("pandas")
    plot = mp.plot({"value": pd.Series([pd.NA, pd.NaT], dtype=object)})
    assert plot.spec.data.columns == {"value": [None, None]}
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
