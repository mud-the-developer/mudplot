"""Scoped calendar ticks for canonical 1970-day coordinates, no epoch mutation."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import matplotlib.dates as dates
import matplotlib.ticker as ticker
import numpy as np

from ._temporal import temporal_timezone

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _canonical_datetime(value, zone):
    """The F02 day clock at its supported precision, never native epoch rounding."""
    try:
        return (_EPOCH + timedelta(days=float(value))).astimezone(zone)
    except (ValueError, OverflowError) as error:
        raise ValueError("temporal view exceeds supported calendar range") from error


class _CalendarLocator(ticker.Locator):
    def __init__(self, zone, inner=None):
        super().__init__()
        self.inner = dates.AutoDateLocator(tz=zone) if inner is None else inner
        self.shift = float(dates.date2num(_EPOCH))
        self._n12_unit = "auto"
        self._n12_interval = 1

    def set_axis(self, axis):
        super().set_axis(axis)
        self.inner.set_axis(axis)

    def __call__(self):
        if self.axis is None:
            raise ValueError("temporal locator has no bound axis")
        return self.tick_values(*self.axis.get_view_interval())

    def tick_values(self, vmin, vmax):
        try:
            low = _canonical_datetime(vmin, self.inner.tz)
            high = _canonical_datetime(vmax, self.inner.tz)
        except (ValueError, OverflowError) as error:
            raise ValueError(
                "temporal view exceeds supported calendar range"
            ) from error
        # AutoDateLocator takes datetimes despite the inherited float-only stub.
        return np.asarray(cast(Any, self.inner).tick_values(low, high)) - self.shift

    def nonsingular(self, vmin, vmax):
        low, high = self.inner.nonsingular(vmin + self.shift, vmax + self.shift)
        return low - self.shift, high - self.shift


class _CalendarFormatter(ticker.Formatter):
    def __init__(self, locator, zone):
        self.locator = locator
        self.inner = dates.AutoDateFormatter(locator.inner, tz=zone)

    def __call__(self, value, pos=None):
        return self.inner(value + self.locator.shift, pos)


def apply_temporal_axis(axis, config):
    zone = temporal_timezone(config.timezone) or UTC
    locator = _CalendarLocator(zone)
    axis.set_major_locator(locator)
    axis.set_major_formatter(_CalendarFormatter(locator, zone))
