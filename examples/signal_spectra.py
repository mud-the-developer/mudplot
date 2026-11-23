"""N11: raw ordered real signals, seven finite spectral workflows and replay."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot():
    fs = 128
    a = [
        math.sin(2 * math.pi * 12 * j / fs) + 0.3 * math.cos(2 * math.pi * 28 * j / fs)
        for j in range(512)
    ]
    b = [
        0.7 * math.sin(2 * math.pi * 12 * j / fs + 0.6)
        + 0.2 * math.cos(2 * math.pi * 21 * j / fs)
        for j in range(512)
    ]
    p = (
        mp.plot(
            {
                "signal_a": a,
                "signal_b": b,
                "row_id": [f"sample-{j}" for j in range(512)],
            }
        )
        .theme("publication")
        .size(25, 17)
        .layout(3, 3)
    )
    for panel, kind in enumerate(
        ("spectrogram", "psd", "csd", "coherence", "magnitude", "angle", "phase")
    ):
        whole = kind in ("magnitude", "angle", "phase")
        p.spectrum(
            "signal_a",
            "signal_b" if kind in ("csd", "coherence") else None,
            fs=fs,
            kind=kind,
            nfft=None if whole else 128,
            overlap=0 if whole else 64,
            window="hann",
            detrend="mean",
            colorbar=kind == "spectrogram",
            panel=panel,
        )
        p.labels(title=kind.upper(), panel=panel)
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_signal_spectra")
    out = Path(parser.parse_args().directory)
    out.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    accepted = p.to_json()
    layer = p.spec.panels[1].layers[0].to_dict()
    layer["spectrum"].update(window="hamming", pad_to=257)
    p.apply(
        [
            {"type": "RemoveLayer", "layer_index": 0, "panel": 1},
            {"type": "AddLayer", "layer": layer, "panel": 1},
        ]
    )
    edited = p.to_json()
    p.store.undo()
    p.store.undo()
    assert p.to_json() == accepted
    p.store.redo()
    p.store.redo()
    assert p.to_json() == edited and mp.apply(p.action_log) == p.spec
    mp.save_spec(p.spec, out / "signal_spectra.mplot.json")
    reopened = mp.Plot.from_json(
        mp.to_json(mp.load_spec(out / "signal_spectra.mplot.json"))
    )
    assert reopened.spec == p.spec
    for ext in ("png", "svg", "pdf"):
        plt.close(reopened.save(str(out / f"signal_spectra.{ext}")))
    print(
        "PASS seven N11 kinds / real signals / mixed-parity edit / history / "
        "reopen / PNG SVG PDF"
    )


if __name__ == "__main__":
    main()
