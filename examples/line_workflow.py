"""Synthetic original trajectories, supplied rows and saved/live facet examples.

Run: python examples/line_workflow.py <owned-output-directory>
No external data, preprocessing, display jitter or optional provider is used.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import mudplot as mp


def trajectories():
    data = {
        name: [] for name in ("id", "time", "response", "subject", "condition", "mass")
    }
    for subject in range(4):
        for condition in ("control", "treated"):
            for time in (0, 1, 4):
                response = 2 + subject + (1 + subject / 4) * time
                if condition == "treated":
                    response += 2 + time / 2
                row = (
                    f"row-{len(data['id'])}",
                    time,
                    response,
                    f"subject-{subject}",
                    condition,
                    subject + 1,
                )
                for name, value in zip(data, row, strict=True):
                    data[name].append(value)
    return data


def complete_units(data):
    p = mp.plot(data).layout(1, 2).size(14, 6)
    mapping = mp.SemanticSpec(hue="condition", scale_id="original-trajectories")
    for panel, (calibration, title) in enumerate(
        (
            ("percentile", "Complete units: pointwise percentile"),
            ("max_deviation", "Complete units: finite-grid simultaneous"),
        )
    ):
        p.lineplot(
            "time",
            "response",
            units="subject",
            weights="mass",
            n_boot=399,
            seed=17,
            errorbar=("ci", 95),
            error_style="bars" if panel == 0 else "band",
            line=mp.LineSpec(resampling="unit", calibration=calibration),
            semantics=mapping,
            panel=panel,
        ).labels(x="Declared time", y="Response", title=title, panel=panel)
    p.shared_guides(
        [{"scale_id": "original-trajectories", "title": "Same original raw domain"}]
    )
    return p


def supplied_rows():
    data = {
        "id": list(range(10)),
        "time": [2, 1, 1, 3, 4, 5, 2, 1, 4, 5],
        "response": [2, 1, 3, None, 4, 6, 8, 7, 10, 12],
        "condition": ["A"] * 6 + ["B"] * 4,
        "stroke": [1] * 6 + [3] * 4,
        "method": ["circle"] * 6 + ["square"] * 4,
        "cell": ["north"] * 6 + ["south"] * 4,
    }
    mapping = mp.SemanticSpec(
        hue="condition",
        size="stroke",
        style="method",
        markers=["o", "s"],
        sizes=[0, 3],
        scale_id="supplied-domain",
    )
    return (
        mp.plot(data)
        .size(15, 6)
        .line("time", "response", line=mp.LineSpec(), semantics=mapping)
        .labels(
            x="Supplied predictor",
            y="Supplied response",
            title="Order, duplicates and missing barrier",
        )
        .facet(col="cell", col_order=["north", "south", "empty"], live=True)
        .shared_guides(
            [{"scale_id": "supplied-domain", "title": "Actual stroke / glyph contexts"}]
        )
    )


def named_effects():
    data = {
        "time": ["early", "early", "late", "late"] * 2,
        "response": [1, 2, 4, 6, 4, 5, 8, 10],
        "condition": ["control"] * 4 + ["treated"] * 4,
        "precision": [1] * 4 + [3] * 4,
        "method": ["circle"] * 4 + ["square"] * 4,
    }
    mapping = mp.SemanticSpec(
        hue="condition",
        size="precision",
        style="method",
        markers=["o", "s"],
        sizes=[1, 3],
        scale_id="named-effects",
    )
    p = mp.plot(data).layout(1, 3).size(15, 5)
    p.line(
        "time",
        "response",
        line={"predictor": "categorical"},
        semantics=mapping,
        panel=0,
    )
    p.barplot("time", "response", semantics=mapping, errorbar=None, panel=1)
    p.pointplot("time", "response", semantics=mapping, errorbar=None, panel=2)
    for panel, title in enumerate(("Supplied rows", "Bar means", "Point means")):
        p.labels(title=title, y="Response", panel=panel)
    return p.shared_guides(
        [
            {
                "scale_id": "named-effects",
                "title": "Raw precision: named native effects",
                "location": "outside right",
            }
        ]
    )


def calendar_log():
    data = {
        "id": list(range(6)),
        "date": ["2026-01-01", "2026-01-02", "2026-01-09"] * 2,
        "response": [1, None, 100, 100, None, 10000],
        "subject": ["a"] * 3 + ["b"] * 3,
    }
    return (
        mp.plot(data)
        .size(9, 6)
        .secondary_yaxis("Real UTC predictor")
        .date_axis("y2", timezone="UTC")
        .axis_scale("x", "log", options={"base": 2})
        .lineplot(
            "date",
            "response",
            units="subject",
            orient="h",
            axis="y2",
            stat_scale="axis",
            errorbar=("ci", 95),
            error_style="bars",
            n_boot=399,
            seed=17,
            line={"resampling": "unit", "calibration": "max_deviation"},
        )
        .labels(
            x="Response (a.u.; log10 fit, base2 display)",
            title="User title is retained",
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plots = {
        "complete_units": complete_units(trajectories()),
        "supplied_live": supplied_rows(),
        "calendar_y2_log": calendar_log(),
        "named_effects": named_effects(),
    }
    for name, plot in plots.items():
        (args.output / f"{name}.mplot.json").write_text(
            plot.to_json(), encoding="utf-8"
        )
        for suffix in ("png", "svg", "pdf"):
            plot.save(str(args.output / f"{name}.{suffix}"))
    live = plots["supplied_live"]
    local = copy.deepcopy(live.spec.panels[0].layers[0])
    local.marker_size = 8
    live.dispatch(mp.actions.ReplaceLayer(0, local, panel=0))
    (args.output / "supplied_local.mplot.json").write_text(
        live.to_json(), encoding="utf-8"
    )
    template = copy.deepcopy(live.spec.facet_template.template)
    template.title = "Explicit whole-template replacement"
    live.facet_template(template)
    (args.output / "supplied_whole_template.mplot.json").write_text(
        live.to_json(), encoding="utf-8"
    )
    (args.output / "meaning.json").write_text(
        json.dumps(
            {
                "synthetic": True,
                "complete_units": "original paired rows and masses, not unit means",
                "coverage": (
                    "nominal finite selected grid per curve; "
                    "not cross-panel or population guarantee"
                ),
                "supplied": (
                    "source order/duplicates/gaps; no estimation or display jitter"
                ),
                "calendar": (
                    "real UTC y2 predictor and log10 working response; "
                    "display base2 is independent"
                ),
                "facets": (
                    "local override and explicit whole-template transaction "
                    "remain distinct"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
