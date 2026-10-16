"""Two reading tasks, two charts, reviewed at 700px and 320px web widths.

Run: python examples/publication_showcase.py [output-directory]
The four-panel prototype is retained as a rejected baseline, not a quality target.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.text import Text
from matplotlib.transforms import Bbox
from mudplot import actions as A
from mudplot.color import convert as cv
from mudplot.color import cvd

ROOT = Path(__file__).resolve().parents[1]
METHODS = ["Reference", "Method A", "Method B"]
REPLICATES = 12
WIDTHS = (700, 320)
KINDS = ("response", "endpoint")


def synthetic_data() -> dict[str, list]:
    """Preserve the prototype's independent replicates, row order and seed."""
    rng = np.random.default_rng(2026)
    columns: dict[str, list] = {
        "time": [],
        "response": [],
        "method": [],
        "endpoint": [],
    }
    for method, gain in zip(METHODS, (0.45, 0.8, 1.15), strict=True):
        for time in np.linspace(0, 12, 9):
            values = rng.normal(
                0.18 + gain * (1 - np.exp(-time / 3.5)), 0.065, REPLICATES
            )
            for value in values:
                columns["time"].append(float(time))
                columns["response"].append(float(value))
                columns["method"].append(method)
                columns["endpoint"].append(float(value) if time == 12 else None)
    return columns


def build_plot(kind: str = "response", *, width_px: int = 700) -> mp.Plot:
    """Explicit web layouts, not a general responsive-label placement engine."""
    if kind not in KINDS or width_px not in WIDTHS:
        raise ValueError("use response/endpoint and a 700px or 320px layout")
    columns = synthetic_data()
    p = (
        mp.plot(columns)
        .theme("publication")
        .palette(preset=None, lightness=48, chroma=55, hue_start=20, cvd_safe=True)
        .font(size=12, label_size=12, title_size=14, tick_size=12)
        .size(width_px / 100, 4 if kind == "response" else 3)
        .dispatch(A.SetDpi(200))
        .legend(False)
        .grid_style(
            show=True,
            axis="y" if kind == "response" else "x",
            line_width=0.4,
            alpha=0.18,
        )
    )
    if kind == "response":
        p.lineplot(
            "time",
            "response",
            group="method",
            hue_order=METHODS,
            errorbar=("ci", 95),
            n_boot=399,
            seed=17,
            line_width=1.8,
            error_alpha=0.12,
        )
        p.labels(x="Time (h)", title="Response over time (a.u.)")
        p.xlim(0, 12).ylim(0, 1.6)
        # shortcut: positions fit these three separated curves; re-layout for new data.
        for method in METHODS:
            endpoint = np.mean(
                [
                    value
                    for group, value in zip(
                        columns["method"], columns["endpoint"], strict=True
                    )
                    if group == method and value is not None
                ]
            )
            p.text(
                method,
                [10.3 if width_px == 700 else 7.9, float(endpoint) + 0.08],
                color="#222222",
            )
    else:
        p.pointplot(
            "method",
            "endpoint",
            group="method",
            order=METHODS,
            hue_order=METHODS,
            orient="h",
            errorbar=("ci", 95),
            n_boot=399,
            seed=17,
            line_style="none",
            marker_size=3,
            error_color="#475569",
            error_line_width=1.3,
            capsize=3,
        )
        p.labels(x="Mean response (a.u.)", title="Response at 12 h")
        endpoints = [value for value in columns["endpoint"] if value is not None]
        lower = float(np.floor(min(endpoints) * 10) / 10 - 0.1)
        upper = float(np.ceil(max(endpoints) * 10) / 10 + 0.1)
        p.xlim(lower, upper).ylim(-0.5, 2.5)
    return p


def _drawn_texts(figure) -> list[Text]:
    """Off-view ticks can be visible objects without being drawn into the PNG."""
    excluded = set()
    for axes in figure.axes:
        for axis in (axes.xaxis, axes.yaxis):
            lower, upper = sorted(axis.get_view_interval())
            for tick in [*axis.get_major_ticks(), *axis.get_minor_ticks()]:
                if not lower <= tick.get_loc() <= upper:
                    excluded.update((tick.label1, tick.label2))
    return [
        text
        for text in figure.findobj(Text)
        if text not in excluded
        and text.get_visible()
        and text.get_alpha() != 0
        and text.get_text().strip()
    ]


def save_and_assess(plot: mp.Plot, path: Path, *, display_width_px: int) -> dict:
    """Save the actual PNG, then measure text at its intended CSS display width."""
    if path.suffix.lower() != ".png" or display_width_px <= 0:
        raise ValueError("PNG and a positive display width are required")
    figure = plot.save(str(path))
    try:
        height, width = plt.imread(path).shape[:2]
        # Restore export DPI without a new draw; use the saved PNG's layout state.
        figure.set_dpi(plot.spec.dpi)
        if figure.canvas.get_width_height() != (width, height):
            raise ValueError("saved PNG and assessment canvas dimensions differ")
        scale = display_width_px / width
        texts = _drawn_texts(figure)
        boxes = [text.get_window_extent().frozen() for text in texts]
        content = [*boxes, *(axes.bbox for axes in figure.axes)]
        bounds = Bbox.union(content).extents if content else None
        inside = bounds is not None and bool(
            np.isfinite(bounds).all()
            and bounds[0] >= -1
            and bounds[1] >= -1
            and bounds[2] <= width + 1
            and bounds[3] <= height + 1
        )
        overlaps = []
        for left, right in combinations(range(len(texts)), 2):
            a, b = boxes[left], boxes[right]
            dx = min(a.x1, b.x1) - max(a.x0, b.x0)
            dy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if dx * scale > 1 and dy * scale > 1:
                overlaps.append([texts[left].get_text(), texts[right].get_text()])
        smallest = min(
            (
                text.get_fontproperties().get_size_in_points()
                * plot.spec.dpi
                / 72
                * scale
                for text in texts
            ),
            default=0,
        )
        return {
            "source_pixels": [width, height],
            "display_pixels": [display_width_px, round(height * scale)],
            "min_display_font_px": smallest,
            "font_floor_14px_ok": smallest >= 14,
            "content_bounds_ok": inside,
            "overlapping_text": overlaps,
            "text_overlap_ok": not overlaps,
            "lint": [
                {"level": issue.level, "message": issue.message}
                for issue in plot.lint(min_font_pt=8)
            ],
        }
    finally:
        plt.close(figure)


def render_examples(directory: str | Path) -> dict:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    charts = {}
    for width in WIDTHS:
        for kind in KINDS:
            name = f"visual_{kind}" + ("_mobile" if width == 320 else "")
            plot = build_plot(kind, width_px=width)
            mp.assert_valid(plot.spec)
            assert (
                mp.Plot.from_json(plot.to_json()).spec
                == mp.apply(plot.action_log)
                == plot.spec
            )
            report = save_and_assess(
                plot, destination / f"{name}.png", display_width_px=width
            )
            charts[name] = report
            assert report["font_floor_14px_ok"] and report["content_bounds_ok"]
            assert report["text_overlap_ok"], report["overlapping_text"]
            if width == 700:
                for extension in ("pdf", "svg"):
                    plt.close(plot.save(str(destination / f"{name}.{extension}")))
            mp.save_spec(plot.spec, destination / f"{name}.mplot.json")

    rgb = plt.imread(destination / "visual_response.png")[..., :3]
    luminance = cv.srgb_to_linear(rgb) @ np.array([0.2126, 0.7152, 0.0722])
    gray = cv.linear_to_srgb(np.repeat(luminance[..., None], 3, axis=-1))
    plt.imsave(destination / "visual_response_gray.png", gray)
    for vision in ("protan", "deutan"):
        plt.imsave(
            destination / f"visual_response_{vision}.png",
            np.clip(cvd.simulate(rgb, vision), 0, 1),
        )
    report = {
        "scope": "Web PNG font/bounds/text-box checks; not aesthetic certification.",
        "independent_human_review": "not_run",
        "model_judge": "not_run",
        "font_reference": "https://service-manual.ons.gov.uk/data-visualisation/build-specifications/typography",
        "charts": charts,
    }
    (destination / "visual_quality.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print("OK: separate response/endpoint charts at 700px and 320px; QA is not a score")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", type=Path, default=ROOT / "docs" / "images"
    )
    render_examples(parser.parse_args().directory)
