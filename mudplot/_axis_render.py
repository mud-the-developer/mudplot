"""N12 native effects: bounded location operations, clock-safe labels and units."""

from __future__ import annotations

import math
from datetime import UTC
from typing import Any, cast

import matplotlib.dates as dates
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.axis import Axis
from matplotlib.scale import LogitScale

from ._axis_options import (
    MAX_FIGURE_CONFIGURED_TICKS,
    MAX_FORMATTED_TICK_CHARACTERS,
    MAX_TICKS_PER_LEVEL,
    affine_parameters,
    check_conversion_bounds,
    configured,
    fixed_values,
    transform_units,
)
from ._layout import shared_groups, twin_value_groups
from ._temporal import temporal_timezone
from ._temporal_render import _CalendarLocator, _canonical_datetime
from .spec import AxisSpec


def _checked_logit_interval(locator, lo, hi, *, view=False):
    """Native logit policy, with a general complement-symmetric singular case."""
    lo, hi = sorted((float(lo), float(hi)))
    if not math.isfinite(lo) or not math.isfinite(hi):
        return ticker.LogitLocator.nonsingular(locator, lo, hi)
    if not 0 < lo <= hi < 1:
        message = (
            "native logit autoscale exceeds open-domain floating-point precision"
            if view
            else "logit geometry/view interval must lie strictly inside (0,1)"
        )
        raise ValueError(message)
    before = (lo, hi)
    if lo == hi:
        if view:
            raise ValueError("native logit view collapses at floating-point precision")
        tail = min(lo, 1 - lo)
        lo, hi = 0.1 * tail, 1 - 0.1 * tail
    else:
        lo, hi = ticker.LogitLocator.nonsingular(locator, lo, hi)
    if not 0 < lo < hi < 1 or not lo <= before[0] <= before[1] <= hi:
        raise ValueError(
            "logit interval cannot contain the data at floating-point precision"
        )
    if locator.axis is None:
        raise ValueError("logit provider is not bound to an axis")
    transform = locator.axis.get_transform()
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        forward = transform.transform(np.asarray([lo, hi]))
        restored = transform.inverted().transform(forward)
    if (
        not np.isfinite(forward).all()
        or not np.isfinite(restored).all()
        or not 0 < restored[0] < restored[1] < 1
    ):
        raise ValueError("native logit inverse exceeds open floating-point precision")
    return lo, hi


class _CheckedLogitLocator(ticker.LogitLocator):
    def nonsingular(self, lo, hi):
        return _checked_logit_interval(self, lo, hi)

    def view_limits(self, lo, hi):
        return _checked_logit_interval(self, lo, hi, view=True)


class _CheckedLogitScale(LogitScale):
    def set_default_locators_and_formatters(self, axis):
        super().set_default_locators_and_formatters(axis)
        axis.set_major_locator(_CheckedLogitLocator())
        axis.set_minor_locator(_CheckedLogitLocator(minor=True))


def checked_logit_scale(axis):
    """The native scale instance installs its policy BEFORE first autoscale."""
    return _CheckedLogitScale(axis, nonpositive="mask")


class _TickBudget:
    """Active location operations, not cached native Tick-object memory."""

    def __init__(self):
        self.counts = {}
        self.providers = []
        self.fingerprint = None
        self.refreshing = False
        self.secondaries = []
        self.secondary_views = {}

    def register(self, provider):
        self.providers.append(provider)
        self.fingerprint = None

    def refresh(self):
        if self.refreshing:
            return
        self.refreshing = True
        try:
            # Synchronize ALL derived visible intervals before planning totals.
            # Otherwise a parent zoom could temporarily mix old child counts
            # with new parent counts and falsely reject a valid active budget.
            for secondary, parent, name in self.secondaries:
                context = (
                    getattr(parent, "get_" + name + "scale")(),
                    *getattr(parent, "get_" + name + "lim")(),
                )
                if context != self.secondary_views.get(secondary):
                    secondary._set_lims()
                    self.secondary_views[secondary] = context
            fingerprint = tuple(
                (*provider.axis.get_view_interval(), *provider.axis.axes.bbox.bounds)
                for provider in self.providers
            )
            if fingerprint == self.fingerprint:
                return
            self.counts = {}
            for provider in self.providers:
                count = _preflight(
                    provider.inner,
                    provider.axis,
                    *provider.axis.get_view_interval(),
                )
                self.reserve(provider.key, count, provider.physical)
            self.fingerprint = fingerprint
        finally:
            self.refreshing = False

    def reserve(self, key, count, physical=1):
        if count > MAX_TICKS_PER_LEVEL:
            raise ValueError(
                f"configured locator exceeds {MAX_TICKS_PER_LEVEL} "
                "tick locations per level"
            )
        count = max(count * physical, self.counts.get(key, 0))
        total = sum(self.counts.values()) - self.counts.get(key, 0) + count
        if total > MAX_FIGURE_CONFIGURED_TICKS:
            raise ValueError(
                "configured physical axis/rank locations exceed "
                f"{MAX_FIGURE_CONFIGURED_TICKS}"
            )
        self.counts[key] = count


def _range_count(start, stop, step):
    if not all(math.isfinite(float(v)) for v in (start, stop, step)) or step <= 0:
        raise ValueError("tick spacing exceeds finite floating-point precision")
    ratio = (stop - start) / step
    if not math.isfinite(ratio):
        raise ValueError("tick grid exceeds finite location bounds")
    return max(0, math.ceil(ratio))


def _calendar_count(inner, lo, hi):
    try:
        low = _canonical_datetime(lo, inner.inner.tz)
        high = _canonical_datetime(hi, inner.inner.tz)
    except (OverflowError, ValueError) as error:
        raise ValueError(
            "configured calendar view exceeds supported clock range"
        ) from error
    native = inner.inner
    parameters: Any = native  # Native parameter attributes lack complete stubs.
    if isinstance(native, dates.AutoDateLocator):
        # AutoDateLocator chooses a frequency/interval before building its rule.
        # Counts are bounded by its requested max plus boundary candidates.
        return max(parameters.maxticks.values()) + 4
    interval = getattr(inner, "_n12_interval", 1)
    unit = getattr(inner, "_n12_unit", "day")
    if unit == "year":
        return (high.year - low.year) // interval + 3
    if unit == "month":
        return ((high.year - low.year) * 12 + high.month - low.month) // interval + 3
    seconds = (high - low).total_seconds()
    step = {
        "week": 604800,
        "day": 86400,
        "hour": 3600,
        "minute": 60,
        "second": 1,
        "microsecond": 1e-6,
    }[unit] * interval
    return _range_count(0, seconds, step) + 4


def _preflight(inner, axis, lo, hi):
    """Bound BEFORE native arange/linspace/date-rule allocation."""
    # Version-qualified native ticker parameters, absent from Matplotlib stubs.
    parameters: Any = inner
    if isinstance(inner, ticker.NullLocator):
        return 0
    if isinstance(inner, ticker.FixedLocator):
        return len(parameters.locs)
    lo, hi = sorted((float(lo), float(hi)))
    if not math.isfinite(lo) or not math.isfinite(hi) or lo == hi:
        raise ValueError("configured tick view needs finite distinct limits")
    if isinstance(inner, _CalendarLocator):
        return _calendar_count(inner, lo, hi)
    if isinstance(inner, ticker.LinearLocator):
        return inner.numticks
    if isinstance(inner, ticker.MultipleLocator):
        step = parameters._edge.step
        offset = getattr(inner, "_offset", 0)
        if not math.isfinite(lo - offset) or lo + step == lo:
            raise ValueError(
                "multiple tick spacing collapses at floating-point precision"
            )
        return _range_count(lo, hi, step) + 3
    if isinstance(inner, ticker.AutoMinorLocator):
        major = axis.get_majorticklocs()
        if len(major) < 2:
            return 0
        intervals = np.diff(major)
        step = float(intervals[0])
        if step <= 0 or not np.allclose(intervals, step, rtol=1e-10, atol=0):
            raise ValueError("auto_minor requires uniformly spaced major ticks")
        subdivisions = inner.ndivs
        subdivisions = 5 if subdivisions in (None, "auto") else subdivisions
        substep = step / subdivisions
        if substep <= 0 or lo + substep == lo:
            raise ValueError("minor tick spacing collapses at floating-point precision")
        return _range_count(lo, hi, substep) + 3
    if isinstance(inner, ticker.LogLocator):
        if lo <= 0:
            raise ValueError("configured logarithmic tick view must be positive")
        base = parameters._base
        low, high = math.log(lo) / math.log(base), math.log(hi) / math.log(base)
        decades = math.floor(high) - math.ceil(low)
        numticks = parameters.numticks
        n = 9 if numticks == "auto" else numticks
        stride = max(decades // n + 1, 1)
        if stride >= decades:
            stride = max(1, decades - 1)
        subs = parameters._subs
        if isinstance(subs, str):
            if decades > 10 or base < 3:
                if subs == "auto":
                    return 0
                subcount = 1
            else:
                subcount = _range_count(2 if subs == "auto" else 1, base, 1)
        else:
            subcount = len(subs)
        # Native LogLocator first allocates its subs array, even when striding
        # will suppress minor ticks; enormous bases must be stopped here too.
        if subcount > MAX_TICKS_PER_LEVEL:
            return subcount
        ranges = _range_count(
            math.floor(low) - stride, math.ceil(high) + 2 * stride, stride
        )
        return max(12, ranges * max(subcount, 1))
    if isinstance(inner, ticker.SymmetricalLogLocator):
        threshold, base = parameters._linthresh, parameters._base
        if -threshold <= lo <= hi <= threshold:
            return 3

        def exponents(a, b):
            return math.floor(math.log(a) / math.log(base)), math.ceil(
                math.log(b) / math.log(base)
            )

        a = (
            exponents(abs(min(-threshold, hi)), abs(lo) + 1)
            if lo < -threshold
            else (0, 0)
        )
        c = exponents(max(threshold, lo), hi + 1) if hi > threshold else (0, 0)
        center = int(lo < threshold and hi > -threshold)
        total = (a[1] - a[0]) + (c[1] - c[0]) + center
        stride = max(total // (inner.numticks - 1), 1)
        count = _range_count(*a, stride) + _range_count(*c, stride)
        return count * len(parameters._subs) + center
    if isinstance(inner, ticker.AsinhLocator):
        return (inner.numticks + 1) * (len(inner.subs) if inner.subs is not None else 1)
    if isinstance(inner, ticker.LogitLocator):
        if not 0 < lo < hi < 1:
            raise ValueError("logit tick view must lie strictly inside (0,1)")
        low = (
            math.floor(math.log10(lo))
            if lo < 0.5
            else 0
            if lo < 0.9
            else -math.ceil(math.log10(1 - lo))
        )
        high = (
            math.ceil(math.log10(hi))
            if hi <= 0.5
            else 1
            if hi <= 0.9
            else -math.floor(math.log10(1 - hi))
        )
        # The widest minor candidate construction is eight per ideal interval.
        if parameters._minor:
            bins = parameters._nbins
            nbins = axis.get_tick_space() if bins == "auto" else bins
            return (
                high - low + 1
                if high - low - 1 > max(2, nbins)
                else max(0, high - low) * 8
            )
        return max(12, high - low + 1)
    if isinstance(inner, ticker.MaxNLocator):
        span = hi - lo
        if not math.isfinite(span) or span <= 0:
            raise ValueError("linear tick view exceeds finite spacing precision")
        bins = parameters._nbins
        return (9 if bins == "auto" else bins) + 4
    # Native categorical locators expose a finite mapping, not an arange grid.
    if hasattr(inner, "_units"):
        return len(inner._units)
    raise ValueError(
        "configured tick control does not support native locator "
        f"{type(inner).__name__}"
    )


class _BoundedLocator(ticker.Locator):
    def __init__(self, inner, budget, key, physical):
        self.inner, self.budget, self.key, self.physical = inner, budget, key, physical

        self.logit_policy = inner if isinstance(inner, _CheckedLogitLocator) else None

    def set_axis(self, axis):
        super().set_axis(axis)
        self.inner.set_axis(axis)

        if self.logit_policy is not None:
            self.logit_policy.set_axis(axis)

    def _locations(self, lo, hi, *, requested=False):
        if self.axis is None:
            raise ValueError("configured locator is not bound to an axis")
        self.budget.refresh()
        if not requested:
            lo, hi = self.axis.get_view_interval()
        previous = self.budget.counts.get(self.key, 0)
        predicted = _preflight(self.inner, self.axis, lo, hi)
        try:
            self.budget.reserve(self.key, predicted, self.physical)
            values = np.asarray(
                self.inner.tick_values(lo, hi) if requested else self.inner(),
                dtype=float,
            )
            if not np.isfinite(values).all():
                raise ValueError("configured tick locations exceed finite precision")
            if len(np.unique(values)) != len(values):
                raise ValueError(
                    "configured tick positions collapse after float conversion"
                )
            self.budget.reserve(self.key, len(values), self.physical)
            return values
        finally:
            if requested:
                # Reading another interval must not alter the active-view budget.
                self.budget.counts[self.key] = previous

    def __call__(self):
        if self.axis is None:
            raise ValueError("configured locator is not bound to an axis")
        return self._locations(*self.axis.get_view_interval())

    def tick_values(self, lo, hi):
        if isinstance(self.inner, ticker.AutoMinorLocator):
            raise NotImplementedError("AutoMinorLocator does not support tick_values")
        return self._locations(lo, hi, requested=True)

    def _logit(self):
        if self.axis is not None and cast(Axis, self.axis).get_scale() == "logit":
            if self.logit_policy is None:
                self.logit_policy = _CheckedLogitLocator()
                self.logit_policy.set_axis(self.axis)
            return self.logit_policy
        return None

    def nonsingular(self, lo, hi):
        policy = self._logit()
        return (
            policy.nonsingular(lo, hi)
            if policy is not None
            else self.inner.nonsingular(lo, hi)
        )

    def view_limits(self, lo, hi):
        policy = self._logit()
        return (
            policy.view_limits(lo, hi)
            if policy is not None
            else self.inner.view_limits(lo, hi)
        )


class _BoundedFormatter(ticker.Formatter):
    def __init__(self, inner):
        self.inner = inner

    def set_axis(self, axis):
        super().set_axis(axis)
        self.inner.set_axis(axis)

    def set_locs(self, locs):
        self.inner.set_locs(locs)

    @staticmethod
    def _check(value):
        if len(value) > MAX_FORMATTED_TICK_CHARACTERS:
            raise ValueError(
                f"formatted tick exceeds {MAX_FORMATTED_TICK_CHARACTERS} characters"
            )
        return value

    def __call__(self, value, pos=None):
        return self._check(self.inner(value, pos))

    def format_ticks(self, values):
        return [self._check(text) for text in self.inner.format_ticks(values)]

    def get_offset(self):
        return self._check(self.inner.get_offset())

    def format_data(self, value):
        return self._check(self.inner.format_data(value))

    def format_data_short(self, value):
        return self._check(self.inner.format_data_short(value))


class _NumberFormatter(ticker.Formatter):
    def __init__(self, config):
        self.prefix, self.suffix = config.prefix or "", config.suffix or ""
        self.format = (
            "."
            + str(3 if config.precision is None else config.precision)
            + {"general": "g", "fixed": "f", "scientific": "e"}[
                config.notation or "general"
            ]
        )

    def __call__(self, value, pos=None):
        return self.prefix + format(float(value), self.format) + self.suffix


class _CanonicalConcise(dates.ConciseDateFormatter):
    """Matplotlib 3.8 concise policy with canonical datetimes, not num2date.

    Adapted policy copyright (c) 2012- Matplotlib Development Team.
    Attribution, license and change summary: _matplotlib_notice.txt.
    """

    def __init__(self, locator, zone):
        super().__init__(
            locator,
            tz=zone,
            usetex=False,
            formats=["%Y", "%b", "%d", "%H:%M", "%H:%M", "%S.%f"],
            zero_formats=["", "%Y", "%b", "%b-%d", "%H:%M", "%H:%M"],
            offset_formats=[
                "",
                "%Y",
                "%Y-%b",
                "%Y-%b-%d",
                "%Y-%b-%d",
                "%Y-%b-%d %H:%M",
            ],
        )
        self.zone = zone

    def __call__(self, value, pos=None):
        return _canonical_datetime(value, self.zone).isoformat(
            sep=" ", timespec="microseconds"
        )

    def format_data_short(self, value):
        return self(value)

    def format_ticks(self, values):
        datetimes = [_canonical_datetime(value, self.zone) for value in values]
        if not datetimes:
            self.offset_string = ""
            return []
        components = [date.timetuple()[:6] for date in datetimes]
        show_offset = self.show_offset
        level = 5
        for candidate in range(5, -1, -1):
            distinct = {parts[candidate] for parts in components}
            if len(distinct) > 1:
                level = candidate
                if candidate < 2 and 1 in distinct:
                    show_offset = False
                break
        zero = (0, 1, 1, 0, 0, 0)
        labels = []
        for date, parts in zip(datetimes, components, strict=True):
            boundary = (
                parts[level] == zero[level]
                if level < 5
                else date.second == date.microsecond == 0
            )
            pattern = self.zero_formats[level] if boundary else self.formats[level]
            labels.append(date.strftime(pattern))
        if level >= 5:
            trailing = min(
                (
                    len(label) - len(label.rstrip("0"))
                    for label in labels
                    if "." in label
                ),
                default=0,
            )
            if trailing:
                labels = [
                    label[:-trailing].rstrip(".") if "." in label else label
                    for label in labels
                ]
        self.offset_string = (
            datetimes[-1].strftime(self.offset_formats[level]) if show_offset else ""
        )
        return labels


class _ClockFormatter(ticker.Formatter):
    """Finite patterns and 3.8 auto-unit policy on the canonical F02 clock."""

    def __init__(self, zone, pattern=None, locator=None, detailed=False):
        self.zone, self.pattern = zone, pattern
        self.locator, self.detailed = locator, detailed

    def __call__(self, value, pos=None):
        date = _canonical_datetime(value, self.zone)
        if self.detailed:
            return date.isoformat(sep="\n", timespec="microseconds")
        if self.locator is not None:
            unit = self.locator.inner._get_unit()
            formats = (
                (1 / 86_400_000_000, "%M:%S.%f"),
                (1 / 86400, "%H:%M:%S"),
                (1 / 1440, "%d %H:%M"),
                (1 / 24, "%m-%d %H"),
                (1, "%Y-%m-%d"),
                (30, "%Y-%m"),
                (365, "%Y"),
            )
            return date.strftime(
                next(
                    (pattern for scale, pattern in formats if scale >= unit),
                    "%Y-%m-%d",
                )
            )
        day = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
        time = f"{date.hour:02d}:{date.minute:02d}:{date.second:02d}"
        return {
            "iso_date": day,
            "iso_datetime": day + "\n" + time,
            "time": time,
            "month": day[:7],
            "year": day[:4],
            "subsecond": day + "\n" + time + f".{date.microsecond:06d}",
        }[self.pattern or "iso_date"]

    def format_ticks(self, values):
        return [self(value, i) for i, value in enumerate(values)]

    def format_data_short(self, value):
        return _canonical_datetime(value, self.zone).isoformat(
            sep=" ", timespec="microseconds"
        )


def _calendar(config, axis_spec, which):
    zone = temporal_timezone(axis_spec.temporal.timezone) or UTC
    unit = (config.unit or "auto") if config is not None else "auto"
    n = (config.interval or 1) if config is not None else 1
    count = (
        (config.count or (8 if which == "major" else 32))
        if config is not None
        else (8 if which == "major" else 32)
    )
    if unit == "auto":
        native = dates.AutoDateLocator(tz=zone, minticks=min(3, count), maxticks=count)
    elif unit == "year":
        native = dates.YearLocator(base=n, tz=zone)
    elif unit == "month":
        native = dates.MonthLocator(interval=n, tz=zone)
    elif unit == "week":
        native = dates.WeekdayLocator(
            byweekday=0 if config is None or config.weekday is None else config.weekday,
            interval=n,
            tz=zone,
        )
    else:
        native = {
            "day": dates.DayLocator,
            "hour": dates.HourLocator,
            "minute": dates.MinuteLocator,
            "second": dates.SecondLocator,
            "microsecond": dates.MicrosecondLocator,
        }[unit](interval=n, tz=zone)
    result = _CalendarLocator(zone, native)
    result._n12_unit, result._n12_interval = unit, n
    return result


def _native_locator(config, axis_spec, which, existing, ordinal=False):
    if config is None:
        return existing
    kind = config.kind
    options = axis_spec.scale_options
    base = 10 if options is None or options.base is None else options.base
    subs = (
        config.subs
        if config.subs is not None
        else options.subs
        if options is not None and which == "minor"
        else None
    )
    if kind == "auto":
        if axis_spec.temporal is not None:
            return _calendar(None, axis_spec, which)
        if (
            ordinal
            or isinstance(existing, ticker.FixedLocator)
            or hasattr(existing, "_units")
        ):
            return existing
        if axis_spec.scale == "linear":
            return (
                ticker.AutoLocator() if which == "major" else ticker.AutoMinorLocator(4)
            )
        kind = axis_spec.scale
    if kind == "none":
        return ticker.NullLocator()
    if kind == "fixed":
        return ticker.FixedLocator(fixed_values(config.values))
    if kind == "multiple":
        return ticker.MultipleLocator(config.step, offset=config.offset or 0)
    if kind == "linear":
        return ticker.LinearLocator(config.count or 5)
    if kind == "max_n":
        return ticker.MaxNLocator(
            config.nbins or 8,
            integer=config.integer or False,
            prune=None if config.prune in (None, "none") else config.prune,
        )
    if kind == "auto_minor":
        return ticker.AutoMinorLocator(config.subdivisions or 4)
    if kind == "log":
        return ticker.LogLocator(
            base=base,
            subs=(1,) if which == "major" and subs is None else subs,
            numticks=9,
        )
    if kind == "symlog":
        threshold = (
            2 if options is None or options.linthresh is None else options.linthresh
        )
        return ticker.SymmetricalLogLocator(base=base, linthresh=threshold, subs=subs)
    if kind == "asinh":
        width = (
            1
            if options is None or options.linear_width is None
            else options.linear_width
        )
        return ticker.AsinhLocator(
            width, numticks=config.count or 11, base=base, subs=subs
        )
    if kind == "logit":
        return _CheckedLogitLocator(minor=which == "minor", nbins=9)
    if kind == "calendar":
        return _calendar(config, axis_spec, which)
    raise ValueError("unsupported locator kind")


def _native_formatter(config, axis_spec, locator, which, existing, refresh_auto=False):
    if config is None or config.kind == "auto":
        if axis_spec.temporal is not None and (config is not None or refresh_auto):
            zone = temporal_timezone(axis_spec.temporal.timezone) or UTC
            return _ClockFormatter(
                zone,
                locator=locator if isinstance(locator, _CalendarLocator) else None,
                detailed=not isinstance(locator, _CalendarLocator),
            )
        return existing
    kind = config.kind
    if kind == "none":
        return ticker.NullFormatter()
    if kind == "fixed":
        return ticker.FixedFormatter(config.labels)
    if kind == "number":
        return _NumberFormatter(config)
    if kind == "scalar":
        formatter = ticker.ScalarFormatter(
            useOffset=True if config.use_offset is None else config.use_offset,
            useMathText=config.mathtext or False,
            useLocale=False,
        )
        formatter.set_scientific(
            True if config.scientific is None else config.scientific
        )
        limits = config.powerlimits
        formatter.set_powerlimits((-5, 6) if limits is None else (limits[0], limits[1]))
        return formatter
    if kind == "percent":
        return ticker.PercentFormatter(
            xmax=1 if config.xmax is None else config.xmax,
            decimals=1 if config.decimals is None else config.decimals,
        )
    if kind == "engineering":
        return ticker.EngFormatter(
            unit=config.unit or "",
            places=config.precision,
            sep=" " if config.separator is None else config.separator,
            usetex=False,
            useMathText=False,
        )
    if kind == "log":
        base = (
            10
            if axis_spec.scale_options is None or axis_spec.scale_options.base is None
            else axis_spec.scale_options.base
        )
        return {
            "plain": ticker.LogFormatter,
            "exponent": ticker.LogFormatterExponent,
            "mathtext": ticker.LogFormatterMathtext,
            "scientific": ticker.LogFormatterSciNotation,
        }[config.style or "scientific"](
            base=base, labelOnlyBase=config.label_only_base or False
        )
    if kind == "logit":
        return ticker.LogitFormatter(
            minor=which == "minor",
            one_half="0.5" if config.half == "decimal" else r"\frac{1}{2}",
            use_overline=config.use_overline or False,
        )
    zone = temporal_timezone(axis_spec.temporal.timezone) or UTC
    if kind == "date":
        return _ClockFormatter(zone, pattern=config.pattern)
    if kind == "concise_date":
        native = locator.inner if isinstance(locator, _CalendarLocator) else locator
        return _CanonicalConcise(native, zone)
    raise ValueError("unsupported formatter kind")


def _install(axis, config, budget, key, physical):
    major = axis.get_major_locator()
    ordinal = isinstance(major, ticker.FixedLocator) or hasattr(major, "_units")
    for which in ("major", "minor"):
        ticks = getattr(config, which + "_ticks")
        native = getattr(axis, "get_" + which + "_locator")()
        formatter = getattr(axis, "get_" + which + "_formatter")()
        locator = _native_locator(
            None if ticks is None else ticks.locator, config, which, native, ordinal
        )
        formatter = _native_formatter(
            None if ticks is None else ticks.formatter,
            config,
            locator,
            which,
            formatter,
            refresh_auto=ticks is not None and ticks.locator is not None,
        )
        bounded = _BoundedLocator(locator, budget, (key, which), physical)
        getattr(axis, "set_" + which + "_locator")(bounded)
        budget.register(bounded)
        getattr(axis, "set_" + which + "_formatter")(_BoundedFormatter(formatter))
        if ticks is not None and ticks.rotation is not None:
            axis.set_tick_params(which=which, labelrotation=ticks.rotation)


def _conversion_functions(config, parent, name):
    kind = config.kind
    if kind in ("hertz_period", "reciprocal"):
        factor, offset = (1 if kind == "hertz_period" else float(config.factor)), 0
    else:
        factor, offset = affine_parameters(config)
    previous = None

    def convert(values, inverse=False):
        nonlocal previous
        scale = getattr(parent, "get_" + name + "scale")()
        bounds = getattr(parent, "get_" + name + "lim")()
        current = (scale, *bounds)
        if current != previous:
            if scale not in ("linear", "log"):
                raise ValueError(
                    "native secondary conversion requires linear/log parent"
                )
            check_conversion_bounds(bounds, config, scale)
            previous = current
        values = np.asarray(values, dtype=float)
        inverse = inverse != config.reverse
        if kind in ("hertz_period", "reciprocal"):
            # Native transforms probe points outside the visible view. Undefined
            # probes remain NaN, never a fabricated zero/positive floor. The
            # ACTUAL visible bounds were checked above on every refresh.
            result = np.full_like(values, np.nan)
            np.divide(factor, values, out=result, where=values > 0)
            return result
        return (values - offset) / factor if inverse else values * factor + offset

    return lambda x: convert(x), lambda x: convert(x, True)


def capture_raw_limits(ax):
    """Snapshot native limits before a qualified nonlinear collection primitive."""
    return (
        ax.dataLim.frozen(),
        ax.dataLim.minpos.copy(),
        ax.ignore_existing_data_limits,
        (len(ax.patches), len(ax.lines), len(ax.collections)),
    )


def restore_raw_limits(ax, state):
    """Union actual new RAW artist coordinates, never display-space bounds.

    Matplotlib3.8 collection get_datalim can return nonlinear-transformed values.
    Follow the existing distribution-artist snapshot/minpos/ignore convention;
    leave every native artist, transform, source row and missing-path gap intact.
    """
    from matplotlib.collections import LineCollection, QuadMesh
    from matplotlib.patches import Rectangle
    from matplotlib.path import Path

    old_lim, old_minpos, old_ignore, starts = state
    ax.dataLim.set_points(old_lim.get_points())
    ax.dataLim._minpos = old_minpos
    ax.ignore_existing_data_limits = old_ignore

    def union(vertices):
        if len(vertices):
            points = np.asarray(vertices, dtype=float)
            points = points[np.isfinite(points).all(axis=1)]
            if len(points):
                ax.update_datalim(points)

    for patch in list(ax.patches)[starts[0] :]:
        if isinstance(patch, Rectangle):
            union(patch.get_bbox().get_points())
    for line in list(ax.lines)[starts[1] :]:
        union(line.get_xydata())
    for collection in list(ax.collections)[starts[2] :]:
        if isinstance(collection, LineCollection):
            for segment in collection.get_segments():
                union(segment)
        elif isinstance(collection, QuadMesh):
            # The shared coordinate grid has the SAME raw union without
            # allocating one cached Path/view per quad merely to find limits.
            union(cast(np.ndarray, collection.get_coordinates()).reshape(-1, 2))
        else:
            for path in collection.get_paths():
                vertices = path.vertices
                if path.codes is not None:
                    vertices = vertices[path.codes != Path.CLOSEPOLY]
                union(vertices)


def _check_logit_primitives(ax):
    """Validate actual dodged primitive endpoints, not conservative raw spans."""
    from matplotlib.patches import Rectangle

    for patch in ax.patches:
        if not isinstance(patch, Rectangle):
            continue
        if not patch.get_data_transform().contains_branch(ax.transData):
            continue
        bounds = patch.get_bbox()
        coordinates = (bounds.x0, bounds.x1, bounds.y0, bounds.y1)
        if not all(math.isfinite(value) for value in coordinates):
            continue  # Existing native missing-path behavior.
        for name, values in (("x", coordinates[:2]), ("y", coordinates[2:])):
            if getattr(ax, "get_" + name + "scale")() == "logit" and any(
                not 0 < value < 1 for value in values
            ):
                raise ValueError(
                    "logit primitive geometry must lie strictly inside (0,1)"
                )


def _install_mixed_y_ticks(axes, config, budget, key):
    """Bound the shared ticker by the shortest physical y axis."""
    owner = min(axes, key=lambda ax: ax.bbox.height)
    axis = owner.yaxis
    _install(axis, config, budget, key, len(axes))
    for peer in axes:
        if peer is owner:
            continue
        for which in ("major", "minor"):
            ticks = getattr(config, which + "_ticks")
            if ticks is not None and ticks.rotation is not None:
                peer.yaxis.set_tick_params(which=which, labelrotation=ticks.rotation)
    return axis


def install_axes(fig, spec, panel_axes):
    """Install only opt-in N12 effects; legacy axis objects are left untouched."""
    budget = _TickBudget()
    installed = []
    for ax in panel_axes:
        _check_logit_primitives(ax)
        twin = getattr(ax, "_mudplot_secondary_axis", None)
        if twin is not None:
            _check_logit_primitives(twin)
    mixed = set()
    for members in twin_value_groups(spec):
        index, role = members[0]
        mixed.update(members)
        config = getattr(spec.panels[index], role)
        if configured(config):
            axes = [
                panel_axes[i]._mudplot_secondary_axis if name == "y2" else panel_axes[i]
                for i, name in members
            ]
            installed.append(
                _install_mixed_y_ticks(axes, config, budget, ("twin", index))
            )
    for name in ("x", "y"):
        for members in shared_groups(spec, name):
            if (members[0], name) in mixed:
                continue
            config = getattr(spec.panels[members[0]], name)
            if not configured(config):
                continue
            # One shared locator is bound to a canonical narrow axis, not the
            # last rendered member. Its positions count once PER physical axis.
            index = min(
                members,
                key=lambda i: (
                    panel_axes[i].bbox.width
                    if name == "x"
                    else panel_axes[i].bbox.height
                ),
            )
            axis = getattr(panel_axes[index], name + "axis")
            _install(axis, config, budget, ("primary", name, index), len(members))
            installed.append(axis)
            for i in members:
                ticks = (config.major_ticks, config.minor_ticks)
                for which, item in zip(("major", "minor"), ticks, strict=True):
                    if item is not None and item.rotation is not None:
                        getattr(panel_axes[i], name + "axis").set_tick_params(
                            which=which, labelrotation=item.rotation
                        )
    for i, (ax, panel) in enumerate(zip(panel_axes, spec.panels, strict=True)):
        if panel.projection != "2d":
            for name in ("x", "y", "z"):
                config = getattr(panel, name)
                if config is not None and configured(config):
                    target = getattr(ax, name + "axis")
                    _install(target, config, budget, ("native", name, i), 1)
                    installed.append(target)
        twin = getattr(ax, "_mudplot_secondary_axis", None)
        if twin is not None and (i, "y2") not in mixed and configured(panel.y2):
            _install(twin.yaxis, panel.y2, budget, ("y2", i), 1)
            installed.append(twin.yaxis)
        for name in ("x", "y"):
            config = getattr(panel, "secondary_" + name)
            if config is None:
                continue
            parent = getattr(panel, name)
            limits = (ax.get_xlim if name == "x" else ax.get_ylim)()
            check_conversion_bounds(limits, config.transform, parent.scale)
            functions = _conversion_functions(config.transform, ax, name)
            secondary = (ax.secondary_xaxis if name == "x" else ax.secondary_yaxis)(
                "top" if name == "x" else "right", functions=functions
            )
            secondary._set_lims()
            target = getattr(secondary, name + "axis")
            label = (
                transform_units(config.transform)[1]
                if config.label is None
                else config.label
            )
            (secondary.set_xlabel if name == "x" else secondary.set_ylabel)(label)
            axis_config = AxisSpec(
                scale=parent.scale,
                scale_options=parent.scale_options,
                major_ticks=config.major_ticks,
                minor_ticks=config.minor_ticks,
            )
            _install(target, axis_config, budget, ("derived", name, i), 1)
            budget.secondaries.append((secondary, ax, name))
            installed.append(target)
            ax.__dict__["_mudplot_derived_" + name] = secondary
    # Preflight every physical configuration before requested tick expansion.
    # Later repeated draw/autofit calls replace counts, never accumulate them.
    for axis in installed:
        for which in ("major", "minor"):
            locator = getattr(axis, "get_" + which + "_locator")()
            if isinstance(locator, _BoundedLocator):
                locator()
    fig._mudplot_tick_budget = budget
