"""SYNTHETIC C07 weighted inference, physical roles and explicit live edits.

The shared-role responses include declared deterministic tuple offsets; typed
True and numeric1 have different positive response factors in the live table.
Every mark uses the same source table, original IDs and weights: no display
jitter or mark-specific preprocessing is applied.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_estimators():
    columns = {
        "dose": ["Control"] * 3 + ["Treatment"] * 3,
        "response": [0, 10, 20, 0, 15, 30],
        "weight": [1, 38, 1] * 2,
        "id": [f"original-{i}" for i in range(6)],
    }
    plot = mp.plot(columns).theme("publication").size(16, 9).layout(2, 3)
    plot.font(size=10, title_size=13, label_size=11, tick_size=9)
    choices = [
        ("mean", "pi", "Mean / observation PI"),
        ("median", "pi", "Observed LEFT median / exact95% PI"),
        ("sum", "ci", "Weighted total / paired CI"),
        ("min", "pi", "Minimum / observation PI"),
        ("max", "pi", "Maximum / observation PI"),
        ("count", None, "Selected weight mass / no inferred CI"),
    ]
    for panel, (estimator, interval, title) in enumerate(choices):
        method = plot.barplot if panel in [0, 2, 5] else plot.pointplot
        method(
            "dose",
            "response",
            weights="weight",
            estimator=estimator,
            errorbar=interval,
            n_boot=401,
            seed=17,
            panel=panel,
        )
        unit = (
            "Response * weight mass"
            if estimator == "sum"
            else "Selected weight mass"
            if estimator == "count"
            else "Observed response (μm)"
        )
        plot.labels(title=title, x="Original dose group", y=unit, panel=panel)
        if estimator not in ["sum", "count"]:
            plot.ylim(-3, 34, panel=panel)
    return plot


def shared_table():
    rows = []
    for hue in [0, 1]:
        for size in [1, 3]:
            for method in ["First", "Second"]:
                for predictor, value in enumerate([1, 2, 3, 4, 5, 20], start=1):
                    for repeat, (offset, weight) in enumerate(
                        zip([0, 0.3, 0.6], [1, 2, 1], strict=True)
                    ):
                        rows.append(
                            {
                                "predictor": predictor,
                                "value": value
                                + offset
                                + 3 * hue
                                + 0.75 * (size - 1)
                                + (1.2 if method == "Second" else 0),
                                "hue": hue,
                                "size": size,
                                "method": method,
                                "weight": weight,
                                "id": f"{hue}-{size}-{method}-{predictor}-{repeat}",
                            }
                        )
    return {key: [row[key] for row in rows] for key in rows[0]}


def build_shared_roles():
    plot = mp.plot(shared_table()).theme("publication").size(20, 12).layout(2, 2)
    plot.font(size=10, title_size=14, label_size=11, tick_size=9)
    config = mp.SemanticSpec(
        scale_id="same-original-rows",
        hue="hue",
        hue_kind="numeric",
        hue_norm=[-1, 2],
        size="size",
        size_norm=[1, 3],
        sizes=[2, 4],
        style="method",
        markers=["D", "^"],
    )
    plot.barplot(
        "predictor",
        "value",
        weights="weight",
        semantics=config,
        native_scale=True,
        errorbar=None,
        alpha=0.7,
    )
    plot.pointplot(
        "predictor",
        "value",
        weights="weight",
        semantics=config,
        native_scale=True,
        errorbar=None,
        dodge=0.6,
        panel=1,
    )
    plot.lineplot(
        "predictor",
        "value",
        weights="weight",
        semantics=config,
        errorbar=None,
        marker_size=4,
        panel=2,
    )
    plot.boxenplot(
        "predictor",
        "value",
        weights="weight",
        semantics=config,
        native_scale=True,
        k_depth=1,
        marker_size=4,
        panel=3,
        colorbar=True,
        clabel="Original numeric hue",
    )
    titles = [
        "Bar: BODY outline stroke pt",
        "Point: actual marker DIAMETER pt",
        "Line: main stroke pt / real curves",
        "Boxen: BODY stroke / actual observed tails",
    ]
    for panel, title in enumerate(titles):
        plot.labels(
            title=title, x="Original predictor", y="Observed response (mm)", panel=panel
        ).ylim(0, 36, panel=panel).legend(location="upper left", panel=panel)
    return plot


def live_table():
    rows = []
    for cell, factor in [("left", 1), ("right", 1.5)]:
        for date in ["2026-01-01", "2026-07-01"]:
            for hue in [True, 1]:
                for index, (value, weight) in enumerate(
                    zip([1, 4, 9], [1, 38, 1], strict=True)
                ):
                    rows.append(
                        {
                            "date": date,
                            "value": factor * value * (1.8 if type(hue) is int else 1),
                            "weight": weight,
                            "hue": hue,
                            "cell": cell,
                            "id": f"{cell}-{date}-{type(hue).__name__}-{hue}-{index}",
                        }
                    )
    return {key: [row[key] for row in rows] for key in rows[0]}


def build_live_dates():
    columns = live_table()
    plot = mp.plot(columns).theme("publication").size(20, 10)
    plot.font(size=10, title_size=14, label_size=11, tick_size=9)
    plot.secondary_yaxis("Observed response (mm)", scale="log", limits=[0.5, 30])
    plot.axis_scale("y2", "log", options={"base": 2})
    plot.date_axis("x", timezone="UTC")
    plot.barplot(
        "date",
        "value",
        weights="weight",
        estimator="median",
        errorbar=("pi", 95),
        semantics={"hue": "hue", "hue_order": [True, 1]},
        axis="y2",
        baseline=0.5,
    )
    plot.labels(
        title="Explicit whole-template weighted inference",
        x="Observation date (UTC)",
        y="Unused primary frame",
    )
    plot.ticks(
        "x",
        {
            "locator": {
                "kind": "fixed",
                "values": mp.temporal_coordinates(
                    ["2026-01-01T00:00:00Z", "2026-07-01T00:00:00Z"]
                ),
            },
            "formatter": {"kind": "date", "pattern": "iso_date"},
        },
    )
    plot.legend(location="upper left")
    plot.facet(
        col="cell", col_order=["left", "empty", "right"], col_wrap=2, live=True
    ).layout(2, 2, width_ratios=[3, 2])
    local = copy.deepcopy(plot.spec.panels[0].layers[0])
    local.alpha = 0.35
    plot.dispatch(mp.actions.ReplaceLayer(0, local, panel=0))
    reopened = mp.Plot.from_json(plot.to_json())
    before = reopened.to_json()
    binding = reopened.spec.facet_template
    assert binding is not None
    template = copy.deepcopy(binding.template)
    layer = template.layers[0]
    layer.type = "pointplot"
    layer.baseline = None
    layer.marker = "D"
    layer.marker_size = 6
    layer.alpha = 0.9
    layer.stat = mp.StatSpec(
        estimator="mean", errorbar="ci", weights="weight", n_boot=101, seed=7
    )
    reopened.facet_template(template)
    after = reopened.to_json()
    reopened.store.undo()
    assert reopened.to_json() == before
    reopened.store.redo()
    assert reopened.to_json() == after
    assert reopened.spec.data.columns == columns and len(reopened.spec.panels) == 3
    return reopened


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_c07/examples")
    out = Path(parser.parse_args().directory)
    out.mkdir(parents=True, exist_ok=True)
    for name, builder in [
        ("statistical_estimators", build_estimators),
        ("statistical_shared_roles", build_shared_roles),
        ("statistical_live_dates", build_live_dates),
    ]:
        plot = builder()
        original = plot.to_json()
        mp.save_spec(plot.spec, out / (name + ".mplot.json"))
        reopened = mp.Plot.from_json(original)
        assert reopened.spec == plot.spec
        for extension in ["png", "svg", "pdf"]:
            plt.close(reopened.save(str(out / (name + "." + extension))))
    print(
        "PASS named quantities/exact LEFT PI/paired CI/main physical roles/"
        "live date-y2/history/reopen/PNG SVG PDF"
    )


if __name__ == "__main__":
    main()
