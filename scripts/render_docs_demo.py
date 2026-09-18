"""Regenerate the documented demos: python -m scripts.render_docs_demo.

Uses synthetic, seeded pandas data, not experimental measurements.
Assertions check the exported images and the actual Matplotlib artists.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pandas as pd  # provided by the dev extra used to regenerate docs
from matplotlib.container import ErrorbarContainer
from mpl_toolkits.mplot3d import Axes3D
from mudplot import actions as A

OUT = Path(__file__).resolve().parents[1] / "docs" / "images"


def simulate_bw_print(src: Path, dst: Path) -> None:
    """Save a true-greyscale (relative-luminance) copy of a rendered PNG.

    Same conversion ``Palette.grayscale_srgb()`` uses for swatches (linear
    sRGB -> relative luminance -> sRGB), applied to a whole figure, so this
    is an honest simulation of flat black & white print/photocopy -- not
    just a trust-me claim about the colours.
    """
    rgb = plt.imread(src)[..., :3].astype(np.float64)
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    y = linear @ np.array([0.2126, 0.7152, 0.0722])
    y = np.where(y <= 0.0031308, y * 12.92, 1.055 * y ** (1 / 2.4) - 0.055)
    plt.imsave(dst, np.clip(y, 0, 1), cmap="gray", vmin=0, vmax=1)


def export(plot, name):
    """Save actual library output, plus editable JSON and a vector PDF."""
    assert mp.validate(plot.spec) == []
    rebuilt = mp.Plot.from_json(plot.to_json())
    assert rebuilt.spec.to_dict() == plot.spec.to_dict()
    mp.save_spec(plot.spec, OUT / f"{name}.mplot.json")
    fig = plot.save(OUT / f"{name}.png")
    expected = (
        round(plot.spec.size[1] * plot.spec.dpi),
        round(plot.spec.size[0] * plot.spec.dpi),
    )
    assert plt.imread(OUT / f"{name}.png").shape[:2] == expected
    plt.close(plot.save(OUT / f"{name}.pdf"))
    print(f"OK {name}: {expected[1]} x {expected[0]} px; JSON round-trip; PDF")
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    time = np.linspace(0, 12, 24)
    data = pd.concat(
        [
            pd.DataFrame(
                {
                    "time": time,
                    "response": offset
                    + amplitude * (1 - np.exp(-time / 4))
                    + rng.normal(0, 0.035, len(time)),
                    "condition": name,
                    "temperature": np.linspace(20 + 10 * i, 28 + 10 * i, len(time)),
                }
            )
            for i, (name, offset, amplitude) in enumerate(
                [
                    ("Control", 0.2, 0.5),
                    ("Treatment A", 0.3, 0.8),
                    ("Treatment B", 0.4, 1.1),
                ]
            )
        ],
        ignore_index=True,
    )
    p = (
        mp.plot(data)
        .layout(2, 2)
        .size(9, 6.5)
        .dispatch(A.SetDpi(150))
        .auto_label()
        .line("time", "response", group="condition", marker_size=3)
        .labels(x="Time (h)", y="Response (a.u.)", title="Response trajectories")
        .legend(location="lower right")
        .scatter(
            "time",
            "response",
            group="condition",
            c="temperature",
            colorbar=True,
            clabel="Temperature (deg C)",
            marker_size=4,
            panel=1,
        )
        .labels(x="Time (h)", y="Response (a.u.)", title="Shared colour scale", panel=1)
        .legend(show=False, panel=1)
        .violin("response", group="condition", panel=2)
        .labels(y="Response (a.u.)", title="Distribution across sampled times", panel=2)
        .kde("response", group="condition", panel=3)
        .labels(x="Response (a.u.)", y="Density", title="Gaussian KDE", panel=3)
        .legend(show=False, panel=3)
    )
    fig = export(p, "pandas_demo")
    assert len(fig.axes) == 5  # four panels, one shared colorbar
    scatter = fig.axes[1].collections
    assert len(scatter) == 3
    assert all(s.norm is scatter[0].norm for s in scatter)
    np.testing.assert_allclose(scatter[0].get_clim(), [20, 48])
    np.testing.assert_allclose(
        np.asarray(fig.axes[0].lines[0].get_ydata(), dtype=float),
        data.response[:24].to_numpy(),
    )
    plt.close(fig)

    categories = pd.DataFrame(
        {
            "order_a": ["Control", "Low dose", "High dose"],
            "order_b": ["High dose", "Control", "Low dose"],
            "mean_a": [1.0, 1.25, 1.5],
            "mean_b": [1.8, 1.1, 1.5],
            "err_a": [0.04, 0.06, 0.08],
            "err_b": [0.09, 0.05, 0.07],
        }
    )
    p = (
        mp.plot(categories)
        .size(5, 3.5)
        .dispatch(A.SetDpi(150))
        .errorbar(
            "order_a",
            "mean_a",
            yerr="err_a",
            label="Experiment A",
            marker="o",
            marker_size=6,
            capsize=3,
        )
        .errorbar(
            "order_b",
            "mean_b",
            yerr="err_b",
            label="Experiment B",
            marker="s",
            marker_size=6,
            capsize=3,
        )
        .labels(y="Response (a.u.)", title="Before editing")
    )
    before = p.to_json()
    plt.close(export(p, "editing_before"))
    p.theme("boxed").labels(title="After editing: aligned categories")
    p.legend(location="upper left").ylim(0.9, 2.0)
    edited = p.to_json()
    p.labels(title="Temporary edit")
    p.store.undo()
    assert p.to_json() == edited
    p.store.redo()
    assert p.spec.panels[0].title == "Temporary edit"
    p.store.undo()
    assert p.to_json() == edited and edited != before
    fig = export(p, "editing_after")
    errorbars = fig.axes[0].containers[1]
    assert isinstance(errorbars, ErrorbarContainer)
    np.testing.assert_array_equal(errorbars.lines[0].get_xdata(), [2, 0, 1])
    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == [
        "Control",
        "Low dose",
        "High dose",
    ]
    plt.close(fig)
    print("OK category positions; undo/redo restores exact JSON")

    x, y = np.meshgrid(np.arange(24), np.arange(20))
    field = np.sin(x / 5) * np.cos(y / 5)
    p = (
        mp.plot()
        .matrix("field", field)
        .layout(1, 2)
        .size(9, 3.8)
        .dispatch(A.SetDpi(150))
        .auto_label()
        .heatmap("field", cmap_kind="diverging", clabel="Amplitude")
        .labels(x="Column index", y="Row index", title="Synthetic field")
        .projection3d(panel=1)
        .surface("field", cmap_kind="diverging", colorbar=False, panel=1)
        .labels(x="Column index", y="Row index", title="Same field in 3-D", panel=1)
        .xlim(0, 23, panel=1)
        .ylim(0, 19, panel=1)
        .zlabel("Amplitude", limits=[-1, 1], panel=1)
    )
    fig = export(p, "fields_demo")
    field_3d = fig.axes[1]
    assert isinstance(field_3d, Axes3D)
    np.testing.assert_allclose(field_3d.get_xlim(), [0, 23])
    np.testing.assert_allclose(field_3d.get_zlim(), [-1, 1])
    assert field_3d.texts[0].get_text() == "b)"
    plt.close(fig)

    # -- palette safety: named preset under normal/CVD/true-greyscale vision --
    from mudplot.capabilities import PALETTE_PRESETS
    from mudplot.color import palette as P
    from mudplot.color.preview import preview

    fig, axes = plt.subplots(3, 1, figsize=(6.5, 6.6))
    for ax, name in zip(axes, ["paper", "vivid", "soft"], strict=True):
        n = PALETTE_PRESETS[name]["max_verified_n"]
        pal = P.preset_qualitative(name, n)
        preview(pal, ax=ax)
        report = pal.report()
        assert report["cvd_safe"] and report["grayscale_safe"]
    fig.tight_layout()
    fig.savefig(OUT / "palette_presets.png", dpi=150)
    plt.close(fig)
    print("OK palette_presets: each preset measured safe at its max_verified_n")

    # -- grouped bar: colour + hatch, verified readable after B&W conversion --
    bars = pd.DataFrame(
        {
            "dose": ["Control", "Low", "High"] * 3,
            "response": [1.0, 1.6, 2.1, 0.9, 1.9, 2.6, 1.1, 1.4, 1.8],
            "cell_line": ["HEK293"] * 3 + ["HeLa"] * 3 + ["CHO"] * 3,
        }
    )
    p = (
        mp.plot(bars)
        .size(5, 3.5)
        .dispatch(A.SetDpi(150))
        .palette(preset="paper")
        .bar("dose", "response", group="cell_line")
        .labels(y="Response (a.u.)", title="Grouped bars: colour + hatch encoding")
        .legend(title="Cell line")
    )
    fig = export(p, "bar_hatched")
    hatches = {patch.get_hatch() for patch in fig.axes[0].patches}
    assert len(hatches) == 3, hatches
    plt.close(fig)
    simulate_bw_print(OUT / "bar_hatched.png", OUT / "bar_hatched_bw.png")
    print("OK bar_hatched: 3 distinct hatches; B&W-print simulation saved")

    print(f"Verified with pandas {pd.__version__}, Matplotlib {matplotlib.__version__}")
    assert not plt.get_fignums()


if __name__ == "__main__":
    main()
