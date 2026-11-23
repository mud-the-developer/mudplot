"""N11 scientific boundaries: independent direct DFTs, not FFT-provider echoes."""

import cmath
import math
import shutil
from dataclasses import replace

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._spectrum import compute_spectrum


def direct_dft(signal, n, m, overlap, window, detrend):
    """Small scalar reference, independent of production NumPy FFT/window code."""
    windows = {
        "boxcar": lambda j: 1,
        "hann": lambda j: 0.5 - 0.5 * math.cos(2 * math.pi * j / (n - 1)),
        "hamming": lambda j: 0.54 - 0.46 * math.cos(2 * math.pi * j / (n - 1)),
        "blackman": lambda j: (
            0.42
            - 0.5 * math.cos(2 * math.pi * j / (n - 1))
            + 0.08 * math.cos(4 * math.pi * j / (n - 1))
        ),
    }
    w = [windows[window](j) for j in range(n)]
    out = []
    for start in range(0, len(signal) - n + 1, n - overlap):
        v = signal[start : start + n]
        if detrend != "none":
            mean = sum(v) / n
            v = [a - mean for a in v]
            if detrend == "linear":
                t = [j - (n - 1) / 2 for j in range(n)]
                slope = sum(a * b for a, b in zip(v, t, strict=True)) / sum(
                    b * b for b in t
                )
                v = [a - slope * b for a, b in zip(v, t, strict=True)]
        out.append(
            [
                sum(
                    v[j] * w[j] * cmath.exp(-2j * math.pi * k * j / m) for j in range(n)
                )
                for k in range(m)
            ]
        )
    return np.asarray(out), w


@pytest.mark.parametrize("n,m", [(7, 7), (8, 8), (7, 8), (8, 9), (7, 12)])
@pytest.mark.parametrize(
    "window,detrend,sides",
    [
        ("boxcar", "none", "onesided"),
        ("hann", "mean", "onesided"),
        ("hamming", "linear", "twosided"),
        ("blackman", "none", "twosided"),
    ],
)
def test_welch_cross_density_window_parity_and_trailing_reference(
    n, m, window, detrend, sides
):
    x = [math.sin(j * 0.7) + j * 0.03 for j in range(23)]
    y = [math.cos(j * 0.4) - 0.2 * x[j] for j in range(23)]
    overlap = 3
    a, w = direct_dft(x, n, m, overlap, window, detrend)
    b, _ = direct_dft(y, n, m, overlap, window, detrend)
    indices = (
        list(range((m + 1) // 2, m)) + list(range((m + 1) // 2))
        if sides == "twosided"
        else list(range(m // 2 + 1))
    )
    # fftshift even M starts at M/2, odd at (M+1)/2.
    if sides == "twosided" and m % 2 == 0:
        indices = list(range(m // 2, m)) + list(range(m // 2))
    factor = [
        2 if sides == "onesided" and k != 0 and not (m % 2 == 0 and k == m // 2) else 1
        for k in indices
    ]
    for scaling in ("density", "spectrum"):
        denominator = (
            20 * sum(v * v for v in w) if scaling == "density" else sum(w) ** 2
        )
        expected = np.mean(a.conj() * b, axis=0)[indices] * factor / denominator
        p = mp.plot({"a": x, "b": y}).spectrum(
            "a",
            "b",
            fs=20,
            kind="csd",
            nfft=n,
            pad_to=m,
            overlap=overlap,
            window=window,
            detrend=detrend,
            sides=sides,
            scaling=scaling,
        )
        result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
        np.testing.assert_allclose(result.cross, expected, atol=3e-14, rtol=3e-12)
        np.testing.assert_allclose(
            result.values, np.abs(expected), atol=3e-14, rtol=3e-12
        )
        assert np.all(np.diff(result.frequencies) > 0)
        psd_layer = replace(
            p.spec.panels[0].layers[0],
            y="",
            spectrum=replace(p.spec.panels[0].layers[0].spectrum, kind="psd"),
        )
        power = compute_spectrum(p.spec.data.columns, psd_layer)
        np.testing.assert_allclose(
            power.values,
            np.mean(np.abs(a) ** 2, axis=0)[indices] * factor / denominator,
            atol=3e-14,
        )


@pytest.mark.parametrize("m", [8, 9, 16, 17])
def test_parseval_exact_sine_density_and_spectrum_units(m):
    signal = [0, 1, 0, -1, 0, 1, 0, -1]
    p = mp.plot({"a": signal}).spectrum("a", fs=8, nfft=8, pad_to=m, window="boxcar")
    result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert float(result.values.sum()) * 8 / m == pytest.approx(0.5)
    if m == 8:
        assert result.frequencies[np.argmax(result.values)] == 2
        assert result.values[2] == pytest.approx(0.5)


def test_coherence_averages_cross_spectra_not_segment_coherences_and_accepts_overlap():
    x = [1, 0, -1, 0, 1, 0, -1, 0]
    y = [1, 0, -1, 0, -1, 0, 1, 0]
    p = mp.plot({"a": x, "b": y}).spectrum(
        "a", "b", fs=4, kind="coherence", nfft=4, window="boxcar"
    )
    result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert result.values[1] == pytest.approx(0)
    assert result.values.mask.tolist() == [True, False, True]
    q = mp.plot({"a": [1, 2, 3, 1, 4], "b": [2, 1, 4, 3, 1]}).spectrum(
        "a", "b", fs=4, kind="coherence", nfft=4, overlap=3, window="boxcar"
    )
    assert mp.validate(q.spec) == []
    a, _ = direct_dft(q.spec.data.columns["a"], 4, 4, 3, "boxcar", "none")
    b, _ = direct_dft(q.spec.data.columns["b"], 4, 4, 3, "boxcar", "none")
    expected = np.abs(np.mean(a.conj() * b, axis=0)) ** 2 / (
        np.mean(np.abs(a) ** 2, axis=0) * np.mean(np.abs(b) ** 2, axis=0)
    )
    np.testing.assert_allclose(
        compute_spectrum(q.spec.data.columns, q.spec.panels[0].layers[0]).values,
        expected[:3],
    )


@pytest.mark.parametrize("kind", ["magnitude", "angle", "phase"])
@pytest.mark.parametrize("sides", ["onesided", "twosided"])
def test_whole_spectrum_impulse_magnitude_and_phase_order(kind, sides):
    signal = [0, 0, 1, 0, 0, 0, 0, 0]
    p = mp.plot({"a": signal}).spectrum(
        "a", fs=8, kind=kind, window="boxcar", sides=sides
    )
    result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
    frequency = result.frequencies
    angle = -2 * np.pi * frequency * 2 / 8
    expected = (
        np.ones(len(frequency)) / 8
        if kind == "magnitude"
        else np.angle(np.exp(1j * angle))
    )
    if kind == "phase":
        # Shifted impulse has a known linear phase, modulo its first-bin branch.
        expected = angle - 2 * np.pi * math.floor((angle[0] + np.pi) / (2 * np.pi))
    if kind == "angle":
        np.testing.assert_allclose(
            np.exp(1j * result.values), np.exp(1j * expected), atol=1e-14
        )
    else:
        np.testing.assert_allclose(result.values, expected, atol=1e-14)


def test_exact_zero_phase_gaps_db_masks_and_linear_zeros():
    for kind in ("angle", "phase"):
        p = mp.plot({"a": [1, 0, -1, 0, 1, 0, -1, 0]}).spectrum(
            "a", fs=8, kind=kind, window="boxcar"
        )
        result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
        assert result.values.mask.tolist() == [True, True, False, True, True]
    p = mp.plot({"a": [-1, 0, 1, 0, 1, 0, -1, 0]}).spectrum(
        "a", fs=8, kind="phase", window="boxcar"
    )
    result = compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert result.values.mask.tolist() == [True, False, True, False, True]
    np.testing.assert_allclose(
        result.values.compressed(), [-3 * np.pi / 4, 3 * np.pi / 4]
    )
    p = mp.plot({"a": [0] * 8}).spectrum("a", fs=8, nfft=4, window="boxcar")
    assert np.all(
        compute_spectrum(p.spec.data.columns, p.spec.panels[0].layers[0]).values == 0
    )
    for kind in ("psd", "magnitude", "angle", "phase", "coherence"):
        q = mp.plot({"a": [0] * 8, "b": [0] * 8}).spectrum(
            "a",
            "b" if kind == "coherence" else None,
            fs=8,
            kind=kind,
            nfft=None if kind in ("magnitude", "angle", "phase") else 4,
            window="boxcar",
            scale="dB" if kind in ("psd", "magnitude") else "linear",
        )
        with pytest.raises(ValueError, match="no defined"):
            q.render()


def test_spectrogram_native_cells_time_frequency_and_declared_labels():
    p = mp.plot({"a": [1, 0, -1, 0, 1, 0, -1, 0, 99]}).spectrum(
        "a", fs=4, kind="spectrogram", nfft=4, window="boxcar", colorbar=True
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        mesh = ax.collections[0]
        coords = mesh.get_coordinates()
        np.testing.assert_allclose(coords[0, :, 0], [0, 1, 2])
        np.testing.assert_allclose(coords[:, 0, 1], [-0.5, 0.5, 1.5, 2.5])
        np.testing.assert_allclose(
            mesh.get_array().reshape(3, 2), [[0, 0], [0.5, 0.5], [0, 0]]
        )
        assert (
            ax.get_xlabel() == "Elapsed time (s)"
            and ax.get_ylabel() == "Frequency (Hz)"
        )
        assert fig.axes[1].get_ylabel() == "Power density (signal²/Hz)"
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "options",
    [
        {"fs": True},
        {"fs": 0},
        {"fs": float("inf")},
        {"nfft": 2},
        {"nfft": True},
        {"pad_to": 3},
        {"overlap": 4},
        {"overlap": True},
        {"window": "callable"},
        {"detrend": "unknown"},
        {"sides": "default"},
        {"scaling": "bogus"},
        {"scale": "log"},
        {"kind": "angle", "nfft": 4},
        {"kind": "coherence"},
        {"colorbar": True},
        {"marker": "o"},
        {"group": "a"},
    ],
)
def test_invalid_options_reject_before_any_figure(options):
    kwargs = {"fs": 4, "nfft": 4, **options}
    p = mp.plot({"a": [1, 2, 3, 4], "b": [4, 3, 2, 1]}).spectrum("a", **kwargs)
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "signal",
    [
        [],
        [1, 2],
        [1, None, 3, 4],
        [1, True, 3, 4],
        [1, float("nan"), 3, 4],
        [1, float("inf"), 3, 4],
        [1, "2", 3, 4],
    ],
)
def test_missing_or_invalid_samples_never_drop_or_retime(signal):
    p = mp.plot({"a": signal}).spectrum("a", fs=4, nfft=4)
    assert mp.validate(p.spec)


def test_fft_grid_and_paired_shape_limits_are_preallocation_errors():
    for p in (
        mp.plot({"a": [1] * 65537}).spectrum("a", fs=1, kind="magnitude"),
        mp.plot({"a": [1] * 80}).spectrum("a", fs=1, nfft=3, pad_to=65536, overlap=2),
        mp.plot({"a": [1] * 8, "b": [1] * 7}).spectrum(
            "a", "b", fs=1, kind="csd", nfft=4
        ),
    ):
        with pytest.raises(ValueError):
            p.render()
    with pytest.raises(TypeError):
        mp.SpectrumSpec.from_dict({"kind": "psd"})


@pytest.mark.parametrize(
    "a,b", [(1, 1), (1e-100, 1e-100), (1e100, 1e100), (1e-100, 1e100), (1e-300, 1e300)]
)
def test_coherence_amplitude_units_do_not_create_false_undefined_bins(a, b):
    p = mp.plot({"a": [a, 0, -a, 0] * 2, "b": [b, 0, -b, 0] * 2}).spectrum(
        "a", "b", fs=4, kind="coherence", nfft=4, window="boxcar"
    )
    fig = p.render()
    try:
        line = fig.axes[0].lines[0]
        np.testing.assert_array_equal(line.get_xdata(), [0, 1, 2])
        assert line.get_ydata().mask.tolist() == [True, False, True]
        assert line.get_ydata()[1] == pytest.approx(1)
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "style",
    [
        {"color": "not-a-color"},
        {"color": True},
        {"label": 42},
        {"clabel": 42, "colorbar": True},
        {"clabel": "unused"},
        {"citation": "unlabelled2026"},
        {"href": "https://example.org/unlabelled"},
    ],
)
def test_spectral_metadata_errors_reject_before_native_artists(style):
    p = mp.plot({"s": [0, 1, 0, -1] * 2}).spectrum(
        "s",
        fs=4,
        nfft=4,
        window="boxcar",
        kind="spectrogram" if "clabel" in style else "psd",
        **style,
    )
    assert mp.validate(p.spec)
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


def test_spectral_svg_reference_is_linked_without_visible_citation_key(tmp_path):
    path = tmp_path / "spectrum.svg"
    p = mp.plot({"s": [0, 1, 0, -1] * 2}).spectrum(
        "s",
        fs=4,
        nfft=4,
        window="boxcar",
        label="Measured",
        citation="known2026",
        href="https://example.org/signal",
    )
    plt.close(p.save(str(path)))
    svg = path.read_text()
    assert 'xlink:href="https://example.org/signal"' in svg
    assert "known2026" not in svg


@pytest.mark.skipif(
    shutil.which(plt.rcParams["pgf.texsystem"]) is None,
    reason="native PGF export requires the declared TeX engine",
)
def test_spectral_pgf_legend_honours_citation_and_hyperlink(tmp_path):
    path = tmp_path / "spectrum.pgf"
    p = mp.plot({"s": [0, 1, 0, -1] * 2}).spectrum(
        "s",
        fs=4,
        nfft=4,
        window="boxcar",
        label="Measured",
        citation="known2026",
        href="https://example.org/signal",
    )
    plt.close(p.save(str(path)))
    pgf = path.read_text()
    assert r"\figcite{known2026}" in pgf
    assert r"\href{https://example.org/signal}{" in pgf
    assert "Measured" in pgf and "«" not in pgf and "»" not in pgf


def test_spectral_pgf_native_legend_carries_resolvable_reference_metadata():
    from mudplot._render import _substitute_pgf_references

    p = mp.plot({"s": [0, 1, 0, -1] * 2}).spectrum(
        "s",
        fs=4,
        nfft=4,
        window="boxcar",
        label="Measured",
        citation="known2026",
        href="https://example.org/signal",
    )
    fig = mp.render(p.spec, fmt="pgf")
    try:
        native_label = fig.axes[0].get_legend().get_texts()[0].get_text()
        assert native_label == fig.axes[0].lines[0].get_label()
        resolved = _substitute_pgf_references(native_label, fig._mudplot_refs)
        assert resolved == (
            r"\href{https://example.org/signal}{Measured}~\figcite{known2026}"
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("amplitude", [1e-100, 1e-300])
def test_coherence_preserves_defined_low_power_frequency_bins(amplitude):
    # Exact four-sample DFT is [2a, 2, -2a]: every bin is nonzero.
    p = mp.plot({"s": [1, amplitude, -1, amplitude] * 2}).spectrum(
        "s", "s", fs=4, kind="coherence", nfft=4, window="boxcar"
    )
    fig = p.render()
    try:
        line = fig.axes[0].lines[0]
        np.testing.assert_array_equal(line.get_xdata(), [0, 1, 2])
        assert not np.ma.getmaskarray(line.get_ydata()).any()
        np.testing.assert_allclose(line.get_ydata(), [1, 1, 1])
    finally:
        plt.close(fig)


def test_zero_width_dashed_spectrum_retains_data_without_drawing_stroke(tmp_path):
    p = mp.plot({"s": [0, 1, 0, -1] * 2}).spectrum(
        "s",
        fs=4,
        nfft=4,
        window="boxcar",
        line_width=0,
        line_style="--",
        color="#e71245",
    )
    for extension in ("png", "svg"):
        path = tmp_path / f"zero-stroke.{extension}"
        fig = p.save(str(path))
        try:
            line = fig.axes[0].lines[0]
            np.testing.assert_array_equal(line.get_xydata(), [[0, 0], [1, 0.5], [2, 0]])
            assert line.get_linewidth() == 0
            assert fig.axes[0].get_xlabel() == "Frequency (Hz)"
        finally:
            plt.close(fig)
    assert "stroke: #e71245" not in (tmp_path / "zero-stroke.svg").read_text()
    from PIL import Image

    with Image.open(tmp_path / "zero-stroke.png") as image:
        pixels = np.asarray(image.convert("RGB"))
    # Axes/text stay neutral; the specifically requested red signal adds no ink.
    assert not np.any(
        (pixels[..., 0] > 150) & (pixels[..., 1] < 100) & (pixels[..., 2] < 150)
    )


def test_coherence_unused_trailing_partial_cannot_erase_consumed_signal():
    signal = [1e-100, 0, -1e-100, 0] * 2 + [1e300]
    p = mp.plot({"s": signal}).spectrum(
        "s", "s", fs=4, kind="coherence", nfft=4, window="boxcar"
    )
    fig = p.render()
    try:
        line = fig.axes[0].lines[0]
        np.testing.assert_array_equal(line.get_xdata(), [0, 1, 2])
        assert line.get_ydata().mask.tolist() == [True, False, True]
        assert line.get_ydata()[1] == pytest.approx(1)
    finally:
        plt.close(fig)


def test_coherence_unrepresentable_channel_scaling_is_precision_error_not_gap():
    p = mp.plot({"s": [1e300, 1e-300, -1e300, 1e-300] * 2}).spectrum(
        "s", "s", fs=4, kind="coherence", nfft=4, window="boxcar"
    )
    with pytest.raises(ValueError, match="precision"):
        p.render()
