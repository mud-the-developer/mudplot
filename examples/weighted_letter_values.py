"""Run: python examples/weighted_letter_values.py [output_directory].

Relative weighted letter values, stable raw-hue/rank components and independently
mapped BODY colour/outline/dash plus actual observed flier glyphs. No CI or KDE.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        name: []
        for name in (
            "dose",
            "dose_native",
            "response",
            "group",
            "weight",
            "calibration",
            "stroke",
            "protocol",
        )
    }
    values = [0.4, 0.8, 1, 1.2, 1.4, 1.8, 2.2, 3, 4, 8, 9, 11]
    weights = [1, 2, 3, 4, 3, 2, 2, 1, 1, 0.2, 0.1, 0.1]
    for group, effect, calibration, stroke, protocol in (
        ("Control", 0, 0, 0.6, "A"),
        ("Treated", 0.6, 1, 1.6, "B"),
    ):
        for dose, native, shift in (("Low", 1, 0), ("High", 4, 1.8)):
            count = len(values)
            data["dose"].extend([dose] * count)
            data["dose_native"].extend([native] * count)
            data["response"].extend(value + effect + shift for value in values)
            data["group"].extend([group] * count)
            data["weight"].extend(weights)
            data["calibration"].extend([calibration] * count)
            data["stroke"].extend([stroke] * count)
            data["protocol"].extend([protocol] * count)
    p = mp.plot(data).theme("publication").size(11, 5.4)
    p.mosaic([["bands", "mapped"]], width_ratios=[1.1, 1])
    p.boxenplot(
        "dose",
        "response",
        group="group",
        weights="weight",
        k_depth=3,
        order=["Low", "High"],
        hue_order=["Control", "Treated"],
        gap=0.16,
        marker_size=2.5,
        band_components=[
            {"rank": 0, "side": "central", "body": {"line_width": 1, "hatch": ""}},
            {"rank": 1, "side": "lower", "body": {"hatch": "/"}},
        ],
        hue_components=[
            {"level": "Control", "components": {"body": {"color": "#306a9c"}}},
            {
                "level": "Treated",
                "components": {"body": {"color": "#b86d27"}},
                "band_components": [
                    {"rank": 1, "side": "lower", "body": {"hatch": "x", "alpha": 0.9}}
                ],
            },
        ],
        panel=0,
    )
    p.labels(
        x="Dose",
        y=r"Response $\Sigma^2$ (a.u.)",
        title="Weighted letter values\nraw hue + stable band rank",
        panel=0,
    )
    p.title_reference(
        citation="lv",
        href="https://vita.had.co.nz/papers/letter-value-plot.pdf",
        panel=0,
    )
    p.legend(title="Group; relative weights", location="outside bottom", panel=0)
    p.boxenplot(
        "dose_native",
        "response",
        weights="weight",
        k_depth=2,
        orient="h",
        native_scale=True,
        width_method="area",
        gap=0.12,
        semantics={
            "hue": "calibration",
            "hue_kind": "numeric",
            "hue_norm": [0, 1],
            "size": "stroke",
            "sizes": [0.5, 1.2],
            "style": "protocol",
            "markers": ["o", "s"],
            "dashes": ["-", "--"],
            "legend": False,
        },
        components={
            "flier": {"marker_size": 2.5, "edge_color": "#333333", "face_color": "none"}
        },
        colorbar=True,
        clabel="Calibration (unitless)",
        panel=1,
    )
    p.labels(
        x=r"Response $\Sigma^2$ (a.u.)",
        y="Native dose (mg)",
        title="Mapped channels\ncolour / outline / dash + glyph",
        panel=1,
    )
    p.legend(False, panel=1)
    p.reference_style(measure_text="[1]")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    destination = Path(parser.parse_args().directory)
    destination.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    mp.assert_valid(p.spec)
    for fmt in ("png", "svg", "pdf"):
        plt.close(p.save(str(destination / f"weighted_letter_values.{fmt}")))
    mp.save_spec(p.spec, destination / "weighted_letter_values.mplot.json")
    print(
        "OK: relative weighted bands, raw-hue/rank ownership "
        "and actual mapped body/flier effects"
    )


if __name__ == "__main__":
    main()
