"""DATA-05: preserve supported timestamp precision, offsets and missing values."""

from __future__ import annotations

import os
import subprocess
import sys

import mudplot as mp
import numpy as np
import pytest
from mudplot.data import to_columns

PRECISE = [
    ("ns", "1970-01-01T00:00:01.123456789"),
    ("ps", "1970-01-01T00:00:01.123456789012"),
    ("fs", "1970-01-01T00:00:01.123456789012345"),
    ("as", "1970-01-01T00:00:01.123456789012345678"),
]


@pytest.mark.parametrize("unit,expected", PRECISE)
@pytest.mark.parametrize(
    "shape",
    [
        "scalar",
        "zero_dim",
        "column",
        "object_column",
        "records",
        "rows",
        "array2d",
        "structured",
    ],
)
def test_numpy_high_precision_time_is_iso_not_an_epoch_integer(unit, expected, shape):
    values = np.array([expected, "NaT"], dtype=f"datetime64[{unit}]")
    before = values.copy()
    name = "at"
    if shape == "scalar":
        source = {name: values[0]}
    elif shape == "zero_dim":
        source = {name: np.array(values[0])}
    elif shape == "column":
        source = {name: values}
    elif shape == "object_column":
        source = {name: np.array([values[0], values[1]], dtype=object)}
    elif shape == "records":
        source = [{name: value} for value in values]
    elif shape == "structured":
        source = np.array(
            [(value,) for value in values], dtype=[(name, f"datetime64[{unit}]")]
        )
    else:
        name = "c0"
        source = (
            [[value] for value in values] if shape == "rows" else values.reshape(2, 1)
        )
    normalized = {
        name: [expected] if shape in ("scalar", "zero_dim") else [expected, None]
    }
    assert to_columns(source) == normalized
    plot = mp.plot(source)
    assert mp.Plot.from_json(plot.to_json()).spec.data.columns == normalized
    np.testing.assert_array_equal(values, before)


@pytest.mark.parametrize(
    "unit,expected",
    [
        ("D", "2026-01-02"),
        ("s", "2026-01-02T09:30:01"),
        ("ms", "2026-01-02T09:30:01.123000"),
        ("us", "2026-01-02T09:30:01.123456"),
    ],
)
@pytest.mark.parametrize("scalar", [False, True])
def test_existing_numpy_coarse_precision_format_is_preserved(unit, expected, scalar):
    value = np.datetime64(expected, unit)
    assert to_columns(
        {"at": value if scalar else [value, np.datetime64("NaT", unit)]}
    ) == {"at": [expected] if scalar else [expected, None]}


def test_plain_2d_array_protocol_does_not_require_numpy_dtype_metadata():
    class Rows:
        ndim = 2

        def tolist(self):
            return [[1, 2], [3, 4]]

    assert to_columns(Rows()) == {"c0": [1, 3], "c1": [2, 4]}


def test_two_dimensional_datetime_column_is_rejected_instead_of_collapsing_cells():
    values = np.array([["2026-01-01T00:00:00.123456789"]], dtype="datetime64[ns]")
    with pytest.raises(ValueError, match="datetime columns must be scalar or 1-D"):
        to_columns({"at": values})
    assert to_columns(values) == {"c0": ["2026-01-01T00:00:00.123456789"]}


def test_nonlossless_polars_formatter_is_rejected_before_emitting_values():
    class Datetime:
        time_unit = "ns"
        time_zone = None

    class Series:
        __module__ = "polars.probe"

        def __init__(self):
            self.dtype = Datetime()
            self.dt = self
            self.str = self

        def to_string(self, fmt):
            assert fmt == "%Y-%m-%dT%H:%M:%S%.9f"
            return self

        def to_datetime(self, **kwargs):
            assert kwargs["time_unit"] == "ns"
            return self

        def equals(self, original):
            return False

        def to_list(self):
            raise AssertionError("lossy values must never be emitted")

    with pytest.raises(ValueError, match="not lossless"):
        to_columns({"at": Series()})


@pytest.mark.parametrize("zone", ["UTC", "Pacific/Honolulu"])
def test_timestamp_normalization_does_not_depend_on_process_timezone_or_locale(zone):
    script = (
        "import numpy as n; from datetime import datetime,timezone,timedelta; "
        "from mudplot.data import to_columns; "
        "assert to_columns({'at':n.array("
        "['2026-01-01T00:00:00.123456789'],dtype='datetime64[ns]')})"
        "=={'at':['2026-01-01T00:00:00.123456789']}; "
        "assert to_columns({'at':[datetime(2026,1,1,"
        "tzinfo=timezone(timedelta(hours=5,minutes=30)))]})"
        "=={'at':['2026-01-01T00:00:00+05:30']}"
    )
    subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "TZ": zone, "LC_ALL": "C"},
        check=True,
        timeout=20,
    )


def test_date_strings_do_not_silently_become_supported_numeric_lineplot_coordinates():
    plot = mp.plot(
        {"at": [np.datetime64("2026-01-01T00:00:00.123456789")], "value": [1]}
    ).lineplot("at", "value", errorbar=None)
    assert any(
        "numeric finite category" in problem for problem in mp.validate(plot.spec)
    )


def test_timestamp_epoch_number_is_not_coerced_without_a_datetime_dtype():
    assert to_columns({"at": np.array([1767346201123456789], dtype="int64")}) == {
        "at": [1767346201123456789]
    }


@pytest.mark.parametrize(
    "zone,expected",
    [
        (None, "2026-01-02T09:30:01.123456789"),
        ("UTC", "2026-01-02T09:30:01.123456789+00:00"),
        ("Asia/Kolkata", "2026-01-02T15:00:01.123456789+05:30"),
        ("America/New_York", "2026-01-02T04:30:01.123456789-05:00"),
    ],
)
def test_pandas_nanoseconds_and_timezone_offsets_are_preserved(zone, expected):
    pd = pytest.importorskip("pandas")
    series = pd.Series(pd.to_datetime([1767346201123456789, None], unit="ns", utc=True))
    series = series.dt.tz_convert(zone) if zone else series.dt.tz_localize(None)
    frame = pd.DataFrame({"at": series})
    before = frame.copy(deep=True)
    assert to_columns(frame) == {"at": [expected, None]}
    plot = mp.plot(frame)
    assert mp.Plot.from_json(plot.to_json()).spec.data.columns == {
        "at": [expected, None]
    }
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize(
    "zone,expected",
    [
        (None, "2026-01-02T09:30:01.123456789"),
        ("UTC", "2026-01-02T09:30:01.123456789+00:00"),
        ("Asia/Kolkata", "2026-01-02T15:00:01.123456789+05:30"),
    ],
)
def test_polars_nanoseconds_use_lossless_native_formatting(zone, expected):
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame(
        {
            "at": pl.Series(
                [1767346201123456789, None], dtype=pl.Datetime("ns", time_zone=zone)
            )
        }
    )
    before = frame.clone()
    assert to_columns(frame) == {"at": [expected, None]}
    assert mp.Plot.from_json(mp.plot(frame).to_json()).spec.data.columns == {
        "at": [expected, None]
    }
    assert frame.equals(before)


def test_polars_dst_changes_keep_both_offsets_and_nanoseconds():
    pl = pytest.importorskip("polars")
    values = [1772953199123456789, 1772953200123456789]
    frame = pl.DataFrame(
        {"at": pl.Series(values, dtype=pl.Datetime("ns", time_zone="America/New_York"))}
    )
    assert to_columns(frame) == {
        "at": [
            "2026-03-08T01:59:59.123456789-05:00",
            "2026-03-08T03:00:00.123456789-04:00",
        ]
    }


@pytest.mark.parametrize(
    "zone,expected",
    [
        (None, "2026-01-02T09:30:01.123456789"),
        ("UTC", "2026-01-02T09:30:01.123456789+00:00"),
        ("Asia/Kolkata", "2026-01-02T15:00:01.123456789+05:30"),
    ],
)
def test_arrow_supported_nanosecond_conversion_retains_values(zone, expected):
    pa = pytest.importorskip("pyarrow")
    pytest.importorskip("pandas")
    table = pa.table(
        {"at": pa.array([1767346201123456789, None], type=pa.timestamp("ns", tz=zone))}
    )
    assert to_columns(table) == {"at": [expected, None]}
    assert mp.Plot.from_json(mp.plot(table).to_json()).spec.data.columns == {
        "at": [expected, None]
    }
