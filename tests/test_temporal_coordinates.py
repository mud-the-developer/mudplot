"""Pure F02 groundwork; axis/render integration is not claimed by these tests."""

import copy
import os
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

import pytest
from mudplot._temporal import DAY_MICROSECONDS, temporal_coordinates, temporal_timezone


def _us(value):
    return round(Fraction(value) * DAY_MICROSECONDS)


def test_irregular_dates_preserve_order_missing_rows_and_source_values():
    source = ["2026-01-02", None, "2026-01-01", "2026-01-11"]
    original = copy.deepcopy(source)
    actual = temporal_coordinates(source, timezone="UTC")
    assert actual == [20455, None, 20454, 20464]
    assert source == original and len(actual) == len(source)


@pytest.mark.parametrize(
    "value", ["2026-01-01", "2026-01-01T00:00:00", "2026-01-01 00:00"]
)
def test_naive_dates_require_explicit_timezone(value):
    with pytest.raises(
        ValueError, match="naive temporal values require an explicit timezone"
    ):
        temporal_coordinates([value])
    assert temporal_coordinates([value], timezone="UTC") == [20454]


def test_aware_offsets_use_instants_not_wall_clock_and_keep_source_spelling():
    source = [
        "2026-01-01T01:00:00+01:00",
        "2026-01-01T00:00:00Z",
        "2025-12-31T19:00:00-05:00",
    ]
    assert temporal_coordinates(source) == [20454] * 3
    assert temporal_coordinates(source, timezone="+05:30") == [20454] * 3
    assert source[0].endswith("+01:00")


def test_explicit_zone_resolves_naive_values_even_in_an_aware_column():
    source = ["2026-01-01T05:30", "2026-01-01T00:00:00Z"]
    assert temporal_coordinates(source, timezone="+05:30") == [20454, 20454]
    with pytest.raises(ValueError, match="naive"):
        temporal_coordinates(source)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1970-01-01T00:00:00.000001Z", 1),
        ("1969-12-31T23:59:59.999999Z", -1),
        ("1970-01-01T00:00:00+00:00:00.000001", -1),
        ("1970-01-01T00:00:00-00:00:00.000001", 1),
        ("1970-01-01T00:00:00.123456000Z", 123456),
        ("1970-01-01T00:00:00,5Z", 500000),
    ],
)
def test_microseconds_and_fractional_zero_offsets_are_not_silently_discarded(
    value, expected
):
    result = temporal_coordinates([value])
    assert result[0] == float(Fraction(expected, DAY_MICROSECONDS))
    assert _us(result[0]) == expected


@pytest.mark.parametrize(
    "value",
    [
        "1970-01-01T00:00:00.000000001Z",
        "1970-01-01T00:00:00.123456001Z",
        "1970-01-01T00:00:00+00:00:00.000000001",
        "1970-01-01T00:00:00+01:00:00.123456001",
    ],
)
def test_nonzero_submicrosecond_iso_precision_fails_clearly(value):
    with pytest.raises(ValueError, match="precision finer than microseconds"):
        temporal_coordinates([value])


@pytest.mark.parametrize(
    "value",
    [
        "20260101",
        "2026-W01-1",
        "2026-01",
        "2026-13-01",
        "2026-02-29",
        "2026-01-01T24:00:00Z",
        "2026-01-01T00:00:60Z",
        "2026-01-01T00:00.5Z",
        "2026-01-01T00:00:00+24:00",
        "2026-01-01T00:00:00+01:60",
        "2026-01-01T00:00:00-00:00",
        "2026-01-01T00:00:00Z trailing",
        "2026-01-01T00:00:00[Europe/Paris]",
        0,
        True,
    ],
)
def test_invalid_or_unsupported_iso_is_not_guessed(value):
    with pytest.raises(ValueError):
        temporal_coordinates([value], timezone="UTC")


@pytest.mark.parametrize(
    ("unit", "value"),
    [
        ("s", 86400),
        ("ms", 86400000),
        ("us", 86400000000),
        ("ns", 86400000000000),
        ("day", 1),
    ],
)
def test_numeric_inputs_require_declared_unit_and_origin(unit, value):
    result = temporal_coordinates([0, value], unit=unit, origin="2026-01-01T00:00:00Z")
    assert result == [20454, 20455]
    with pytest.raises(ValueError, match="require an ISO origin"):
        temporal_coordinates([value], unit=unit)
    with pytest.raises(ValueError, match="must be date/datetime strings"):
        temporal_coordinates([value])


@pytest.mark.parametrize(
    ("unit", "value", "expected_us"),
    [
        ("s", 0.1, 100000),
        ("s", 0.000001, 1),
        ("ms", 0.001, 1),
        ("us", 1.0, 1),
        ("ns", 1000.0, 1),
        ("day", 0.1, 8640000000),
    ],
)
def test_numeric_float_microsecond_representatives_roundtrip_input_value(
    unit, value, expected_us
):
    source = [value]
    result = temporal_coordinates(source, unit=unit, origin="1970-01-01T00:00:00Z")
    assert _us(result[0]) == expected_us and source == [value]


@pytest.mark.parametrize(
    ("unit", "value"),
    [("s", 1e-7), ("ms", 0.0001), ("us", 0.1), ("ns", 1), ("ns", 1001)],
)
def test_numeric_submicrosecond_information_is_not_rounded_away(unit, value):
    with pytest.raises(ValueError, match="precision finer than microseconds"):
        temporal_coordinates([value], unit=unit, origin="1970-01-01T00:00:00Z")


def test_large_integral_numeric_timestamps_keep_low_bits_before_float_conversion():
    source = [10**18, 10**18 + 1000]
    result = temporal_coordinates(source, unit="ns", origin="1970-01-01T00:00:00Z")
    assert [_us(value) for value in result] == [n // 1000 for n in source]
    assert result[1] > result[0]
    assert source == [10**18, 10**18 + 1000]


@pytest.mark.parametrize(
    "value", [True, "1", float("nan"), float("inf"), float("-inf")]
)
def test_numeric_input_rejects_boolean_coercions_and_nonfinite_values(value):
    with pytest.raises(ValueError, match="finite non-boolean numbers"):
        temporal_coordinates([value], unit="s", origin="1970-01-01T00:00:00Z")


@pytest.mark.parametrize(
    "options",
    [
        {"unit": "seconds", "origin": "1970-01-01T00:00:00Z"},
        {"unit": []},
        {"origin": "1970-01-01T00:00:00Z"},
        {"unit": "s"},
        {"unit": "s", "origin": "1970-01-01"},
        {"timezone": "Europe/Paris"},
        {"timezone": True},
        {"timezone": ""},
        {"timezone": "Z"},
        {"timezone": "+24:00"},
        {"timezone": "-00:00"},
    ],
)
def test_bad_configuration_fails_even_for_an_empty_selected_column(options):
    with pytest.raises(ValueError):
        temporal_coordinates([], **options)


@pytest.mark.parametrize(
    "value", ["0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"]
)
def test_offsets_outside_supported_calendar_range_fail(value):
    with pytest.raises(ValueError, match="supported calendar range"):
        temporal_coordinates([value])


def test_nonstring_timezone_cannot_select_utc_through_equality():
    class UTCish:
        def __eq__(self, other):
            return other == "UTC"

    with pytest.raises(ValueError, match="timezone must be UTC or a fixed offset"):
        temporal_coordinates(["1970-01-01"], timezone=UTCish())


def test_extreme_numeric_ranges_and_float_day_precision_are_explicit_errors():
    with pytest.raises(ValueError, match="supported calendar range"):
        temporal_coordinates([10**500], unit="s", origin="1970-01-01T00:00:00Z")
    with pytest.raises(ValueError, match="precision collapses"):
        temporal_coordinates(["9999-01-01T00:00:00.000001Z"])


@pytest.mark.parametrize(
    ("unit", "value"),
    [
        ("s", 86400),
        ("ms", 86400000),
        ("us", 86400000000),
        ("ns", 86400000000000),
        ("day", 1),
    ],
)
def test_duration_units_do_not_add_a_timestamp_origin(unit, value):
    from mudplot._temporal import temporal_durations

    source = [value, None, 0, -value]
    assert temporal_durations(source, unit=unit) == [1, None, 0, -1]
    assert source == [value, None, 0, -value]


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 0.0000001])
def test_duration_precision_and_numeric_boundary_are_validated(value):
    from mudplot._temporal import temporal_durations

    with pytest.raises(ValueError):
        temporal_durations([value], unit="s")


@pytest.mark.parametrize("value", [10**500, -(10**500)])
def test_duration_overflow_is_a_descriptive_valueerror(value):
    from mudplot._temporal import temporal_durations

    with pytest.raises(
        ValueError, match="temporal duration row 1: exceeds finite day range"
    ):
        temporal_durations([None, value])


def test_no_host_timezone_or_optional_dependency_is_used(tmp_path):
    code = (
        "import sys;from mudplot._temporal import temporal_coordinates as c;"
        "assert c(['2026-01-01T00:00:00Z'])==[20454];"
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=tmp_path,
        env={
            **os.environ,
            "TZ": "Pacific/Honolulu",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        },
        check=True,
    )
    assert temporal_timezone("UTC") is UTC
    zone = temporal_timezone("+05:30")
    assert zone is not None and zone.utcoffset(None).total_seconds() == 19800
    assert datetime(1970, 1, 1, tzinfo=UTC).isoformat().endswith("+00:00")
