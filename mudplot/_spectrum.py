"""Finite N11 contracts; NumPy and native artists are imported only at effects."""

from __future__ import annotations

import math
from dataclasses import fields
from typing import Any, NamedTuple

from .spec import LayerSpec, SpectrumSpec

MAX_SPECTRAL_SAMPLES = 1_000_000
MAX_SPECTRAL_FFT = 65_536
MAX_SPECTRAL_COMPLEX_CELLS = 1_048_576
SPECTRUM_KINDS = (
    "spectrogram",
    "psd",
    "csd",
    "coherence",
    "magnitude",
    "angle",
    "phase",
)
WHOLE_KINDS = ("magnitude", "angle", "phase")
WINDOWS = ("boxcar", "hann", "hamming", "blackman")


def finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def dimensions(config, length):
    n = (
        length
        if config.kind in WHOLE_KINDS
        else (256 if config.nfft is None else config.nfft)
    )
    m = n if config.pad_to is None else config.pad_to
    count = (
        1 if config.kind in WHOLE_KINDS else 1 + (length - n) // (n - config.overlap)
    )
    return n, m, count


def spectrum_issues(columns, layer, panel):
    """Validate all allocation dimensions and samples without optional providers."""
    issues = []
    config = layer.spectrum
    if not isinstance(config, SpectrumSpec):
        return ["spectrum requires SpectrumSpec with explicit fs"]
    if not finite(config.fs) or config.fs <= 0:
        issues.append("fs must be positive finite nonbool samples/second (Hz)")
    for name, choices in (
        ("kind", SPECTRUM_KINDS),
        ("window", WINDOWS),
        ("detrend", ("none", "mean", "linear")),
        ("sides", ("onesided", "twosided")),
        ("scaling", ("density", "spectrum")),
        ("scale", ("linear", "dB")),
    ):
        if getattr(config, name) not in choices:
            issues.append(f"{name} must be one of {choices}")
    for name in ("nfft", "pad_to"):
        value = getattr(config, name)
        if value is not None and (
            type(value) is not int or not 3 <= value <= MAX_SPECTRAL_FFT
        ):
            issues.append(f"{name} must be integer in [3,{MAX_SPECTRAL_FFT}] or None")
    if type(config.overlap) is not int or config.overlap < 0:
        issues.append("overlap must be a nonnegative integer")
    if config.kind in WHOLE_KINDS and (config.nfft is not None or config.overlap != 0):
        issues.append(
            "whole-signal magnitude/angle/phase require nfft=None and overlap=0"
        )
    if config.kind in (*WHOLE_KINDS, "coherence") and config.scaling != "density":
        issues.append(
            "scaling is only used by psd/csd/spectrogram; leave density otherwise"
        )
    if config.kind in ("coherence", "angle", "phase") and config.scale != "linear":
        issues.append("coherence and phase/angle require scale='linear'")
    if panel.projection != "2d" or layer.axis != "y" or panel.y2 is not None:
        issues.append("spectrum supports primary Cartesian 2-D axes without y2")
    if any(
        axis.scale != "linear" or axis.temporal is not None
        for axis in (panel.x, panel.y)
    ):
        issues.append(
            "derived spectral axes must be linear and nontemporal; "
            "use scale='dB' explicitly"
        )
    if panel.filters or panel.dropna:
        issues.append(
            "spectrum does not drop/select rows; fs requires complete ordered signals"
        )
    allowed = {
        "type",
        "x",
        "y",
        "spectrum",
        "label",
        "color",
        "line_width",
        "line_style",
        "alpha",
        "cmap_kind",
        "colorbar",
        "clabel",
        "citation",
        "href",
    }
    defaults = LayerSpec()
    for f in fields(layer):
        if f.name not in allowed and getattr(layer, f.name) != getattr(
            defaults, f.name
        ):
            issues.append(f"{f.name} is not supported for spectrum")
    image = config.kind == "spectrogram"
    signatures = {
        (other.spectrum.kind == "spectrogram", spectrum_labels(other.spectrum)[:2])
        for other in panel.layers
        if other.type == "spectrum" and isinstance(other.spectrum, SpectrumSpec)
    }
    if len(signatures) > 1 or any(
        other.type not in ("spectrum", "hline", "vline", "text", "annotate")
        for other in panel.layers
    ):
        issues.append(
            "spectral panels cannot mix derived units or raw-coordinate layers"
        )
    if image:
        for name in ("color", "line_width", "line_style", "label", "citation", "href"):
            if getattr(layer, name) is not None:
                issues.append(f"{name} is not used by spectrogram")
    elif layer.colorbar or layer.clabel is not None or layer.cmap_kind != "sequential":
        issues.append("colourmap/colourbar controls require spectrogram")
    if layer.cmap_kind not in ("sequential", "diverging"):
        issues.append("cmap_kind must be sequential or diverging")
    if type(layer.colorbar) is not bool:
        issues.append("colorbar must be bool")
    if not finite(layer.alpha) or not 0 <= layer.alpha <= 1:
        issues.append("alpha must be finite in [0,1]")
    if layer.line_width is not None and (
        not finite(layer.line_width) or not 0 <= layer.line_width <= 1000
    ):
        issues.append("line_width must be finite in [0,1000] points")
    if layer.line_style is not None and layer.line_style not in ("-", "--", "-.", ":"):
        issues.append("line_style must be a named dash pattern")
    paired = config.kind in ("csd", "coherence")
    if not paired and layer.y:
        issues.append("a second signal y is only used by csd/coherence")
    names = [layer.x, layer.y] if paired else [layer.x]
    lengths = []
    for name in names:
        if not isinstance(name, str) or not name or name not in columns:
            issues.append("each required signal must name an existing column")
            continue
        values = columns[name]
        lengths.append(len(values))
        if not 3 <= len(values) <= MAX_SPECTRAL_SAMPLES:
            issues.append(f"signal needs 3..{MAX_SPECTRAL_SAMPLES} samples per channel")
        if any(not finite(v) for v in values):
            issues.append(
                "samples must be finite real plain JSON numbers, not bool/missing; "
                "no rows are dropped"
            )
    if paired and len(set(lengths)) > 1:
        issues.append("csd/coherence signals must have equal paired lengths")
    if issues or not lengths:
        return issues
    n = (
        lengths[0]
        if config.kind in WHOLE_KINDS
        else (256 if config.nfft is None else config.nfft)
    )
    m = n if config.pad_to is None else config.pad_to
    if not 3 <= n <= MAX_SPECTRAL_FFT:
        return [
            *issues,
            f"effective FFT/window length must be in [3,{MAX_SPECTRAL_FFT}]",
        ]
    if config.overlap >= n:
        return [*issues, "overlap must be smaller than nfft"]
    if lengths[0] < n:
        return [
            *issues,
            "signal needs a full nfft window; short signals are not padded",
        ]
    if m < n:
        return [*issues, "pad_to must be at least the effective FFT/window length"]
    _, _, count = dimensions(config, lengths[0])
    if count * m > MAX_SPECTRAL_COMPLEX_CELLS:
        issues.append(
            f"spectral FFT grid exceeds {MAX_SPECTRAL_COMPLEX_CELLS} complex cells"
        )
    if config.kind == "coherence" and count < 2:
        issues.append(
            "coherence requires at least two complete segments (including overlap)"
        )
    if (
        not finite(config.fs / m)
        or config.fs / m <= 0
        or not finite(lengths[0] / config.fs)
        or not finite(1 / config.fs)
    ):
        issues.append("fs/FFT/time coordinates exceed finite representable resolution")
    return issues


class SpectrumResult(NamedTuple):
    frequencies: Any
    times: Any
    values: Any
    cross: Any = None  # physical complex CSD only; coherence cross stays private


def compute_spectrum(columns, layer):
    """Effect-only FFTs, with pre-sized work and no mutation of source/RNG."""
    import numpy as np

    c = layer.spectrum
    n, m, count = dimensions(c, len(columns[layer.x]))
    # Also guard direct internal callers before allocating a window or FFT grid.
    if (
        n < 3
        or n > MAX_SPECTRAL_FFT
        or m < n
        or m > MAX_SPECTRAL_FFT
        or count * m > MAX_SPECTRAL_COMPLEX_CELLS
    ):
        raise ValueError("spectral allocation dimensions exceed declared limits")
    window = {
        "boxcar": np.ones,
        "hann": np.hanning,
        "hamming": np.hamming,
        "blackman": np.blackman,
    }[c.window](n)
    gain = window.sum()
    energy = np.dot(window, window)
    if not np.isfinite(gain) or gain == 0 or not np.isfinite(energy) or energy <= 0:
        raise ValueError("degenerate spectral window has zero/nonfinite gain or energy")

    def coefficients(name):
        signal = np.asarray(columns[name], dtype=float)
        if c.kind == "coherence":
            # An unused trailing partial segment must not affect any arithmetic.
            consumed = (count - 1) * (n - c.overlap) + n
            signal = signal[:consumed]
            # Coherence is invariant under positive per-channel unit changes.
            # Bound coefficients before detrending/FFT and fourth-order products;
            # retain an exactly zero channel without inventing a positive floor.
            amplitude = np.max(np.abs(signal))
            if amplitude > 0:
                scaled = signal / amplitude
                if np.any((signal != 0) & (scaled == 0)):
                    raise ValueError(
                        "coherence input dynamic range exceeds floating-point "
                        "precision: "
                        "channel normalization would erase nonzero samples before FFT"
                    )
                signal = scaled
        segments = np.lib.stride_tricks.sliding_window_view(signal, n)[:: n - c.overlap]
        if c.detrend != "none":
            segments = segments - segments.mean(axis=1, keepdims=True)
            if c.detrend == "linear":
                t = np.arange(n, dtype=float) - (n - 1) / 2
                slopes = segments @ t / np.dot(t, t)
                segments = segments - slopes[:, None] * t
        values = segments * window
        if c.sides == "onesided":
            result = np.fft.rfft(values, n=m, axis=1)
        else:
            result = np.fft.fftshift(np.fft.fft(values, n=m, axis=1), axes=1)
        if not np.isfinite(result).all():
            raise ValueError(
                "spectral FFT overflow; derived coefficients are not finite"
            )
        if c.kind == "coherence":
            # Each bin's positive channel factor cancels in the ratio of
            # averaged cross/powers. Defined bins now have mean power >=1/count,
            # even when distinct frequencies differ by hundreds of decades.
            amplitudes = np.max(np.abs(result), axis=0)
            defined = amplitudes > 0
            np.divide(result.real, amplitudes, out=result.real, where=defined)
            np.divide(result.imag, amplitudes, out=result.imag, where=defined)
        return result

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        x = coefficients(layer.x)
        freqs = (
            np.fft.rfftfreq(m, 1 / c.fs)
            if c.sides == "onesided"
            else np.fft.fftshift(np.fft.fftfreq(m, 1 / c.fs))
        )
        times = (np.arange(count) * (n - c.overlap) + n / 2) / c.fs
        cross = None
        if c.kind in WHOLE_KINDS:
            z = x[0]
            if c.kind == "magnitude":
                values = np.abs(z) / abs(gain)
            else:
                values = np.ma.array(np.angle(z), mask=(np.abs(z) == 0))
                if c.kind == "phase":
                    # Unwrap contiguous defined bins in ascending frequency.
                    for run in np.ma.clump_unmasked(values):
                        values[run] = np.unwrap(values[run])
        else:
            power = np.abs(x) ** 2
            if c.kind in ("csd", "coherence"):
                y = coefficients(layer.y)
                cross = (x.conj() * y).mean(axis=0)
            if c.kind == "coherence":
                assert cross is not None
                denominator = power.mean(axis=0) * (np.abs(y) ** 2).mean(axis=0)
                values = np.ma.array(
                    np.abs(cross) ** 2 / denominator, mask=denominator == 0
                )
            else:
                factor = np.ones(x.shape[1])
                if c.sides == "onesided":
                    factor[1 : -1 if m % 2 == 0 else None] = 2
                normalization = (
                    c.fs * energy if c.scaling == "density" else abs(gain) ** 2
                )
                if not np.isfinite(normalization) or normalization <= 0:
                    raise ValueError(
                        "spectral normalization exceeds finite representable range"
                    )
                factor /= normalization
                if c.kind == "csd":
                    assert cross is not None
                    cross = cross * factor
                    values = np.abs(cross)
                elif c.kind == "spectrogram":
                    values = (power * factor).T
                else:
                    values = power.mean(axis=0) * factor
        if not np.isfinite(np.ma.asarray(values).compressed()).all():
            raise ValueError(
                "spectral arithmetic overflow; derived spectrum is not finite"
            )
        if c.scale == "dB":
            values = np.ma.array(values, mask=np.asarray(values) == 0)
            values = (20 if c.kind == "magnitude" else 10) * np.ma.log10(values)
    values = np.ma.asarray(values)
    # Overflow is an error. Zero computed coefficients/power yield derived gaps;
    # float64 window/detrend/FFT may round tiny true bins to zero. A mask is not
    # physical evidence of an exact zero or a high-dynamic-range accuracy guarantee.
    if not np.isfinite(values.compressed()).all() or (
        cross is not None and not np.isfinite(cross).all()
    ):
        raise ValueError("spectral arithmetic overflow; derived spectrum is not finite")
    if values.count() == 0:
        raise ValueError(
            "spectrum has no defined derived bins "
            "(zero power/coefficient or logarithm of zero)"
        )
    return SpectrumResult(freqs, times, values, cross if c.kind == "csd" else None)


def spectrum_axis_units(config):
    """Finite derived dimensions for sharing; never infer units from data names."""
    if config.kind == "spectrogram":
        return "elapsed_seconds", "frequency_hz"
    if config.kind in ("angle", "phase"):
        response = "angle_radians"
    elif config.kind == "coherence":
        response = "proportion"
    elif config.kind == "magnitude":
        response = "spectral_amplitude"
    else:
        response = (
            "spectral_power_density"
            if config.scaling == "density"
            else "spectral_power"
        )
    if config.scale == "dB":
        response += "_db"
    return "frequency_hz", response


def spectrum_labels(c):
    unit = "Power density (signal²/Hz)" if c.scaling == "density" else "Power (signal²)"
    if c.kind == "csd":
        unit = (
            "Cross-power magnitude density (x·y/Hz)"
            if c.scaling == "density"
            else "Cross-power magnitude (x·y)"
        )
    if c.kind == "coherence":
        unit = "Magnitude-squared coherence"
    elif c.kind == "magnitude":
        unit = "Magnitude (|FFT|/|Σwindow|)"
    elif c.kind in ("angle", "phase"):
        unit = "Wrapped angle (rad)" if c.kind == "angle" else "Unwrapped phase (rad)"
    if c.scale == "dB":
        unit += " [dB re 1 declared unit]"
    return (
        ("Elapsed time (s)", "Frequency (Hz)", unit)
        if c.kind == "spectrogram"
        else ("Frequency (Hz)", unit, None)
    )


def draw_spectrum(ax, columns, layer, color_iter, cmap):
    result = compute_spectrum(columns, layer)
    if layer.spectrum.kind == "spectrogram":
        # Native pcolormesh edges are explicit bin-centre midpoints. One segment
        # has one hop-wide time cell, not a fabricated extra measurement.
        import numpy as np

        n, m, _ = dimensions(layer.spectrum, len(columns[layer.x]))
        dt = (n - layer.spectrum.overlap) / layer.spectrum.fs
        df = layer.spectrum.fs / m
        tedges = np.r_[result.times - dt / 2, result.times[-1] + dt / 2]
        fedges = np.r_[result.frequencies - df / 2, result.frequencies[-1] + df / 2]
        artist = ax.pcolormesh(
            tedges,
            fedges,
            result.values,
            shading="flat",
            cmap=cmap,
            alpha=layer.alpha,
            rasterized=False,
        )
        if layer.colorbar:
            ax.figure.colorbar(
                artist, ax=ax, label=layer.clabel or spectrum_labels(layer.spectrum)[2]
            )
    else:
        (artist,) = ax.plot(
            result.frequencies,
            result.values,
            color=layer.color or next(color_iter),
            linewidth=layer.line_width,
            linestyle="none" if layer.line_width == 0 else layer.line_style or "-",
            alpha=layer.alpha,
            label=layer.label,
        )
    artist._mudplot_spectrum = result
    return artist
