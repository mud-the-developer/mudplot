"""Pure explicit temporal coordinates; source columns are never rewritten."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime, timedelta, timezone
from fractions import Fraction

DAY_MICROSECONDS = 86_400_000_000
TEMPORAL_UNITS = ("s", "ms", "us", "ns", "day")
_UNIT_MICROSECONDS = {
    "s": Fraction(1_000_000),
    "ms": Fraction(1_000),
    "us": Fraction(1),
    "ns": Fraction(1, 1_000),
    "day": Fraction(DAY_MICROSECONDS),
}
_EPOCH = datetime(1970, 1, 1)
_ISO = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"(?:[T ](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2})"
    r"(?::(?P<second>[0-9]{2})(?:[.,](?P<fraction>[0-9]+))?)?"
    r"(?P<offset>Z|[+-][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:[.,][0-9]+)?)?)?)?"
)
_OFFSET = re.compile(
    r"(?P<sign>[+-])(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2})"
    r"(?::(?P<second>[0-9]{2})(?:[.,](?P<fraction>[0-9]+))?)?"
)


def _delta_microseconds(value: timedelta) -> int:
    return (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds


_MIN_INSTANT = _delta_microseconds(datetime.min - _EPOCH)
_MAX_INSTANT = _delta_microseconds(datetime.max - _EPOCH)


def _fraction_microseconds(digits: str | None) -> int:
    if not digits:
        return 0
    if digits[6:].strip("0"):
        raise ValueError("temporal precision finer than microseconds is unsupported")
    return int(digits[:6].ljust(6, "0"))


def _offset_microseconds(value: str) -> int:
    match = _OFFSET.fullmatch(value)
    if match is None:
        raise ValueError("timezone must be UTC or a fixed +/-HH:MM[:SS] offset")
    hour, minute = int(match["hour"]), int(match["minute"])
    second = int(match["second"] or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError("fixed timezone offset is outside its supported range")
    result = (hour * 3_600 + minute * 60 + second) * 1_000_000
    result += _fraction_microseconds(match["fraction"])
    if match["sign"] == "-":
        if result == 0:
            raise ValueError("unknown negative-zero UTC offset is unsupported")
        result = -result
    return result


def temporal_timezone(value: str | None):
    """None allows aware inputs only; display defaults to UTC, never host-local."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("timezone must be UTC or a fixed offset")
    if value == "UTC":
        return UTC
    return timezone(timedelta(microseconds=_offset_microseconds(value)))


def _iso_instant(value, zone) -> int:
    if not isinstance(value, str):
        raise ValueError("ISO temporal coordinates must be date/datetime strings")
    match = _ISO.fullmatch(value)
    if match is None:
        raise ValueError("unsupported ISO calendar date/datetime spelling")
    try:
        stamp = datetime(
            int(match["year"]),
            int(match["month"]),
            int(match["day"]),
            int(match["hour"] or 0),
            int(match["minute"] or 0),
            int(match["second"] or 0),
            _fraction_microseconds(match["fraction"]),
        )
    except ValueError as error:
        raise ValueError(f"invalid temporal date/datetime: {error}") from error
    offset = match["offset"]
    if offset == "Z":
        offset_us = 0
    elif offset is not None:
        offset_us = _offset_microseconds(offset)
    elif zone is not None:
        offset_us = _delta_microseconds(zone.utcoffset(None))
    else:
        raise ValueError("naive temporal values require an explicit timezone")
    return _delta_microseconds(stamp - _EPOCH) - offset_us


def _numeric_microseconds(value, factor: Fraction) -> int:
    if type(value) not in (int, float) or (
        isinstance(value, float) and not math.isfinite(value)
    ):
        raise ValueError("numeric temporal values must be finite non-boolean numbers")
    exact = Fraction(value) * factor
    result = round(exact)
    if isinstance(value, int):
        supported = exact.denominator == 1
    else:
        # A microsecond-grid representative must roundtrip the input float value.
        supported = float(Fraction(result) / factor) == value
    if not supported:
        raise ValueError(
            "numeric temporal precision finer than microseconds is unsupported"
        )
    return result


def temporal_durations(values, *, unit="day"):
    """Convert declared numeric durations to days without adding an origin."""
    if not isinstance(unit, str) or unit not in TEMPORAL_UNITS:
        raise ValueError(f"unknown temporal duration unit {unit!r}")
    result = []
    for index, value in enumerate(values):
        if value is None:
            result.append(None)
            continue
        try:
            microseconds = _numeric_microseconds(value, _UNIT_MICROSECONDS[unit])
            days = float(Fraction(microseconds, DAY_MICROSECONDS))
            if round(Fraction(days) * DAY_MICROSECONDS) != microseconds:
                raise ValueError("precision collapses in float days")
            result.append(days)
        except OverflowError as error:
            raise ValueError(
                f"temporal duration row {index}: exceeds finite day range"
            ) from error
        except ValueError as error:
            raise ValueError(f"temporal duration row {index}: {error}") from error
    return result


def check_temporal_error_endpoint(center, magnitude, endpoint, *, subtract):
    """Admit the actual native float endpoint against exact clock/duration ticks."""
    instant = round(Fraction(center) * DAY_MICROSECONDS)
    duration = round(Fraction(magnitude) * DAY_MICROSECONDS)
    expected = instant - duration if subtract else instant + duration
    if not _MIN_INSTANT <= expected <= _MAX_INSTANT:
        raise ValueError(
            "temporal error endpoint is outside the supported calendar range"
        )
    if round(Fraction(endpoint) * DAY_MICROSECONDS) != expected:
        raise ValueError("temporal error endpoint collapses in float day coordinates")


def temporal_coordinates(values, *, timezone=None, unit=None, origin=None):
    """UTC float days with the established microsecond precision admission."""
    return _coordinate_view(
        values, timezone=timezone, unit=unit, origin=origin, exact=False
    )


def exact_temporal_coordinates(values, *, timezone=None, unit=None, origin=None):
    """Canonical rational days for source-before-float statistical plans.

    The SAME input clock/calendar/precision policy applies. This effect view
    never replaces the caller's source columns or changes the public float API.
    """
    return _coordinate_view(
        values, timezone=timezone, unit=unit, origin=origin, exact=True
    )


def _coordinate_view(values, *, timezone, unit, origin, exact):
    zone = temporal_timezone(timezone)
    if unit is None:
        if origin is not None:
            raise ValueError("temporal origin requires an explicit numeric unit")
        origin_us = 0
    else:
        if not isinstance(unit, str) or unit not in TEMPORAL_UNITS:
            raise ValueError(f"unknown temporal unit {unit!r}")
        if not isinstance(origin, str):
            raise ValueError("numeric temporal coordinates require an ISO origin")
        origin_us = _iso_instant(origin, zone)
        if not _MIN_INSTANT <= origin_us <= _MAX_INSTANT:
            raise ValueError("temporal origin is outside the supported calendar range")
    result = []
    for index, value in enumerate(values):
        if value is None:
            result.append(None)
            continue
        try:
            instant = (
                _iso_instant(value, zone)
                if unit is None
                else origin_us + _numeric_microseconds(value, _UNIT_MICROSECONDS[unit])
            )
            if not _MIN_INSTANT <= instant <= _MAX_INSTANT:
                raise ValueError(
                    "temporal instant is outside the supported calendar range"
                )
            canonical = Fraction(instant, DAY_MICROSECONDS)
            coordinate = float(canonical)
            if round(Fraction(coordinate) * DAY_MICROSECONDS) != instant:
                raise ValueError(
                    "temporal precision collapses in float day coordinates"
                )
            result.append(canonical if exact else coordinate)
        except (ValueError, OverflowError) as error:
            raise ValueError(f"temporal row {index}: {error}") from error
    return result


def temporal_discrete_edges(values, *, timezone=None, unit=None, origin=None):
    """Bounded input-unit integer grid; ISO grids use display-clock midnights."""
    from ._histogram_bins import discrete_bounds

    temporal_coordinates([], timezone=timezone, unit=unit, origin=origin)
    if unit is not None:
        bounds = discrete_bounds(values)
        if bounds is None:
            return []
        low, _, count = bounds
        return temporal_coordinates(
            [low + i for i in range(count + 1)],
            timezone=timezone,
            unit=unit,
            origin=origin,
        )
    zone = temporal_timezone(timezone)
    offset = 0 if zone is None else _delta_microseconds(zone.utcoffset(None))
    days = []
    for index, value in enumerate(values):
        if value is None:
            continue
        try:
            instant = _iso_instant(value, zone)
            if not _MIN_INSTANT <= instant <= _MAX_INSTANT:
                raise ValueError(
                    "temporal instant is outside the supported calendar range"
                )
            local = instant + offset
            if local % DAY_MICROSECONDS:
                raise ValueError(
                    "discrete ISO values must be midnight in the display clock"
                )
            days.append(local // DAY_MICROSECONDS)
        except (ValueError, OverflowError) as error:
            raise ValueError(f"temporal discrete row {index}: {error}") from error
    bounds = discrete_bounds(days)
    if bounds is None:
        return []
    low, _, count = bounds
    return temporal_coordinates(
        [low + i for i in range(count + 1)],
        timezone=timezone or "UTC",
        unit="day",
        origin="1970-01-01",
    )
