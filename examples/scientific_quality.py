"""Four synthetic failures, exported at their actual publication size (300 DPI).

The time and metric definitions below are authored synthetic metadata, not units
inferred by mudplot. The trend example explicitly accepts a recommendation; the
smart layout policy itself never changes scatter geometry or measurements.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
from mudplot._quality import assess


def _publication(plot, width=3.5):
    return plot.size(width, 2.6).theme("publication").dispatch(mp.actions.SetDpi(300))


def build_examples():
    bars = _publication(
        mp.plot({"method": ["A", "B"], "score": [0.97, 0.99]})
        .bar("method", "score", group="method")
        .labels(x="Method", y="Measured score", title="Two-method comparison")
        .ylim(0, 1)
        .legend(location="upper right")
    ).encoding(hatches=["///", "xxx"])
    data = {
        "time": [0, 1, 2] * 2,
        "response": [1, 2, 3, 2, 3, 4],
        "method": ["A"] * 3 + ["B"] * 3,
    }
    shared = mp.plot(data).layout(1, 2)
    for panel in range(2):
        shared.line("time", "response", group="method", panel=panel)
        shared.labels(x="Elapsed time (s)", y="Response (a.u.)", panel=panel)
    shared = _publication(shared, width=7)
    times = [i / 4 for i in range(240)]
    temporal = {
        "elapsed": times * 2,
        "response": [0.4 + 0.03 * math.sin(i / 11) + i / 1000 for i in range(240)]
        + [0.6 + 0.03 * math.sin(i / 11) + i / 1000 for i in range(240)],
        "method": ["A"] * 240 + ["B"] * 240,
    }
    scatter = _publication(
        mp.plot(temporal).scatter("elapsed", "response", group="method")
    )
    trend = _publication(
        mp.plot(temporal).line("elapsed", "response", group="method", marker="")
    )
    for plot in (scatter, trend):
        plot.labels(
            x="Elapsed time (s)",
            y="Normalized response",
            title="Synthetic trajectories",
        )
    tiny = _publication(
        mp.plot(
            {
                "internal_step": list(range(8)),
                "raw_metric": [0, 1e-12, 0, 2e-12, 1e-12, 0, 3e-12, 0],
            }
        )
        .line("internal_step", "raw_metric")
        .labels(x="internal_step", y="raw_metric", title="Panel 1")
    )
    described = mp.Plot.from_json(tiny.to_json()).labels(
        x="Calibration step", y="Normalized residual", title="Calibration residual"
    )
    return {
        "legend_collision": (
            bars,
            bars,
            "Layout only: direct method labels; no hatches.",
        ),
        "shared_legend": (shared, shared, "Layout only: deduplicate shared encodings."),
        "temporal_scatter": (
            scatter,
            trend,
            "Author accepts a time-trend recommendation; no aggregation.",
        ),
        "metric_semantics": (
            tiny,
            described,
            "Author supplies synthetic metric descriptions; zeros retained.",
        ),
    }


def render_examples(directory):
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    cases = {}
    for name, (before, after, decision) in build_examples().items():
        before_data = {
            key: list(values) for key, values in before.spec.data.columns.items()
        }
        assert before_data == {
            key: list(values) for key, values in after.spec.data.columns.items()
        }
        case = {"author_decision": decision, "data_changed": False}
        for phase, plot in (("before", before), ("after", after)):
            filename = f"{name}_{phase}.png"
            figure = plot.save(
                str(destination / filename),
                layout_policy="smart" if phase == "after" else None,
            )
            try:
                report = assess(figure, plot.spec).to_dict()
                height, width = plt.imread(destination / filename).shape[:2]
                assert [width, height] == report["measurements"]["pixels"]
                assert report["measurements"]["min_font_pt"] >= 8
                if phase == "after":
                    assert not any(i["level"] == "error" for i in report["issues"]), (
                        report
                    )
                    report["repairs"] = cast(Any, figure).mudplot_quality["repairs"]
                case[phase] = {"file": filename, **report}
            finally:
                plt.close(figure)
        if name == "temporal_scatter":
            case["recommendation"] = mp.recommend(
                before_data, x="elapsed", y="response", group="method", time=True
            )
        cases[name] = case
    report = {"synthetic": True, "dpi": 300, "cases": cases}
    (destination / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", default="docs/images/scientific_quality"
    )
    args = parser.parse_args()
    render_examples(args.directory)
    print(f"wrote publication-size before/after figures and report to {args.directory}")
