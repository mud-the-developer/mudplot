"""C04: weighted paired halves, native inner traits, shared roles and live dates."""

from __future__ import annotations

import argparse
import copy
import math
from dataclasses import replace
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def paired_table():
    rows = []
    for category in ["Early", "Late"]:
        for hue in range(5):
            for observation in range(17):
                rows.append(
                    {
                        "season": category,
                        "treatment": f"Treatment {hue + 1}",
                        "response": 2
                        + hue * 0.65
                        + (category == "Late") * 0.8
                        + 0.65 * math.sin(observation * 0.71)
                        + observation * 0.025,
                        "weight": 1 + (observation + hue) % 4,
                        "id": f"{category}-{hue}-{observation}",
                    }
                )
    return {name: [row[name] for row in rows] for name in rows[0]}


def build_paired():
    plot = mp.plot(paired_table()).theme("publication").size(16, 7).layout(1, 2)
    plot.font(size=11, title_size=14, label_size=12, tick_size=10)
    common = {
        "group": "treatment",
        "hue_order": [f"Treatment {i + 1}" for i in range(5)],
        "weights": "weight",
        "split": True,
        "violin": {
            "split_policy": "paired",
            "hue_components": [
                {"level": "Treatment 5", "components": {"body": {"hatch": "//"}}}
            ],
        },
        "width": 0.9,
        "gap": 0.18,
        "points": 129,
        "density_norm": "count",
        "common_norm": True,
        "bw_method": "silverman",
        "bw_adjust": 0.8,
        "cut": 0.4,
        "components": {
            "body": {"alpha": 0.85, "edge_color": "#263445", "line_width": 0.8}
        },
    }
    plot.violin("season", "response", inner="quart", panel=0, **common)
    plot.violin("season", "response", inner="box", panel=1, **common)
    for panel, inner in enumerate(
        ["Weighted quartile spans", "Weighted inner boxes / real median glyphs"]
    ):
        plot.labels(
            title=inner,
            x="Season: three declared pair lanes; fifth is left-only",
            y="Observed response (mm)",
            panel=panel,
        )
        plot.ylim(0.8, 8, panel=panel).legend(
            location="upper left", title="Relative weighted mass", panel=panel
        )
    return plot


def role_table():
    rows = []
    for hue in [0, 1]:
        for size in [1, 3]:
            for method in ["First", "Second"]:
                for predictor, value in enumerate([1, 2, 3, 4, 5, 20], start=1):
                    rows.append(
                        {
                            "category": "Observed cohort",
                            "predictor": predictor,
                            "response": value
                            + hue * 2
                            + size * 0.2
                            + (method == "Second") * 0.15,
                            "temperature": hue,
                            "precision": size,
                            "method": method,
                            "weight": 1 + predictor % 3,
                            "id": f"{hue}-{size}-{method}-{predictor}",
                        }
                    )
    return {name: [row[name] for row in rows] for name in rows[0]}


def build_shared_roles():
    plot = mp.plot(role_table()).theme("publication").size(24, 12).layout(2, 3)
    plot.font(size=10, title_size=14, label_size=11, tick_size=9)
    config = mp.SemanticSpec(
        scale_id="same-original-rows",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-1, 2],
        size="precision",
        size_norm=[1, 3],
        sizes=[2, 4],
        style="method",
        markers=["D", "^"],
    )
    common = {
        "semantics": replace(config, legend=False),
        "cmap_kind": "sequential",
        "colorbar": True,
        "clabel": "Temperature (degrees C)",
    }
    plot.violin(
        "category",
        "response",
        inner="box",
        weights="weight",
        marker_size=4,
        components={
            "body": {"alpha": 0.9},
            "whisker": {"line_width": 0.8},
            "box": {"line_width": 1.4},
        },
        panel=0,
        **{**common, "semantics": config},
    )
    plot.box(
        "category",
        "response",
        showmeans=True,
        cap_fraction=0.7,
        marker_size=4,
        components={
            "body": {"alpha": 0.9},
            "whisker": {"line_width": 0.8},
            "median": {"line_width": 1},
        },
        panel=1,
        **common,
    )
    plot.scatter(
        "predictor", "response", edge_color="#263445", line_width=0.5, panel=2, **common
    )
    plot.lineplot(
        "predictor",
        "response",
        weights="weight",
        errorbar=None,
        marker_size=4,
        panel=3,
        **common,
    )
    plot.ecdf("response", weights="weight", marker_size=4, panel=4, **common)
    plot.rug("response", height=0.22, panel=5, **common)
    titles = [
        "Violin: BODY outline pt / real median glyph",
        "Box: BODY outline pt / actual outlier glyph",
        "Scatter: nominal diameter pt",
        "Line: stroke pt / six observed points per curve",
        "Weighted ECDF: stroke pt / genuine steps",
        "Rug: stroke pt / axes-fraction height",
    ]
    for panel, title in enumerate(titles):
        plot.labels(title=title, panel=panel)
    for panel in [0, 1]:
        plot.xlim(-0.6, 2.8 if panel == 0 else 0.6, panel=panel).ylim(
            0, 28, panel=panel
        )
        plot.labels(
            x=(
                "One selected cohort; right-hand room for guides"
                if panel == 0
                else "One selected cohort; actual outliers retained"
            ),
            y="Observed response (mm)",
            panel=panel,
        )
    plot.legend(location="upper right", panel=0)
    for panel in [2, 3]:
        plot.ylim(0, 28, panel=panel).labels(
            x="Original predictor", y="Observed response (mm)", panel=panel
        )
    plot.labels(x="Observed response (mm)", y="Weighted cumulative mass", panel=4)
    plot.labels(
        x="Observed response (mm)", y="Unused perpendicular data frame", panel=5
    )
    return plot


def live_table():
    rows = []
    for cell in ["left", "right"]:
        for category in ["2026-01-01", "2026-07-01"]:
            for hue in [True, 1]:
                for i in range(7):
                    rows.append(
                        {
                            "date": category,
                            "response": 1
                            + i * 0.25
                            + (category == "2026-07-01") * 0.5
                            + (type(hue) is int) * 0.45
                            + (cell == "right") * 0.3,
                            "hue": hue,
                            "cell": cell,
                            "id": f"{cell}-{category}-{type(hue).__name__}-{i}",
                        }
                    )
    return {name: [row[name] for row in rows] for name in rows[0]}


def build_live_dates():
    table = live_table()
    plot = mp.plot(table).theme("publication").size(20, 10)
    plot.font(size=11, title_size=14, label_size=12, tick_size=10)
    plot.secondary_yaxis("Original response (mm)").date_axis("x", timezone="UTC")
    plot.violin(
        "date",
        "response",
        axis="y2",
        inner="box",
        split=True,
        marker_size=5,
        semantics={"hue": "hue", "hue_order": [True, 1], "legend": False},
        components={
            "body": {"alpha": 0.85, "edge_color": "#263445", "line_width": 1.1}
        },
        violin={
            "split_policy": "paired",
            "hue_components": [
                {
                    "level": True,
                    "components": {
                        "whisker": {"color": "#205072"},
                        "median": {"edge_color": "#205072", "face_color": "white"},
                    },
                },
                {
                    "level": 1,
                    "components": {
                        "whisker": {"color": "#8c3d35"},
                        "median": {"edge_color": "#8c3d35", "face_color": "white"},
                    },
                },
            ],
        },
    )
    plot.labels(
        title="Explicit live recipe: bool True and numeric 1 remain distinct",
        x="Date category (UTC)",
        y="Unused primary frame",
    )
    fixed = mp.temporal_coordinates(["2026-01-01T00:00:00Z", "2026-07-01T00:00:00Z"])
    plot.ticks(
        "x",
        {
            "locator": {"kind": "fixed", "values": fixed},
            "formatter": {"kind": "date", "pattern": "iso_date"},
        },
    )
    plot.facet(
        col="cell", col_order=["left", "empty", "right"], col_wrap=2, live=True
    ).layout(2, 2, width_ratios=[3, 2])
    plot.dispatch(mp.actions.SetTitle("A saved cell-local title", panel=0))
    reopened = mp.Plot.from_json(plot.to_json())
    before = reopened.to_json()
    template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, reopened.spec.facet_template).template
    )
    template.title = "Whole-template edit replaces prior cell-local title"
    components = cast(mp.DistributionComponentsSpec, template.layers[0].components)
    cast(mp.ComponentStyleSpec, components.body).alpha = 0.95
    components.box = mp.ComponentStyleSpec(line_width=1.8)
    reopened.facet_template(template)
    edited = reopened.to_json()
    reopened.store.undo()
    assert reopened.to_json() == before
    reopened.store.redo()
    assert reopened.to_json() == edited
    assert reopened.spec.data.columns == table and len(reopened.spec.panels) == 3
    return reopened


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_violin")
    output = Path(parser.parse_args().directory)
    output.mkdir(parents=True, exist_ok=True)
    for name, plot in [
        ("violin_paired_profiles", build_paired()),
        ("violin_shared_roles", build_shared_roles()),
        ("violin_live_dates", build_live_dates()),
    ]:
        mp.save_spec(plot.spec, output / (name + ".mplot.json"))
        reopened = mp.Plot.from_json((output / (name + ".mplot.json")).read_text())
        assert reopened.spec == plot.spec
        for extension in ["png", "svg", "pdf"]:
            plt.close(reopened.save(str(output / (name + "." + extension))))
    print(
        "PASS C04 paired weighted profiles/native inner traits/shared roles/"
        "date-y2/live edit/history/reopen/PNG SVG PDF"
    )


if __name__ == "__main__":
    main()
