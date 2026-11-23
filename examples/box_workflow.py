"""C03: raw median CI, supplied columns, physical cap/stroke units and live views."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.cbook import boxplot_stats

CI = {"level": 90, "n_boot": 1001, "seed": 19}


def observation_table() -> dict[str, list[Any]]:
    """Supplied summaries occupy original representative rows, never a copied table."""
    data: dict[str, list[Any]] = {}
    for phase, when, cohort, shift in (
        ("Winter", "2026-01-01", "left", 0),
        ("Summer", "2026-07-01", "right", 0.4),
    ):
        for method, factor, temperature, precision in (
            ("Control", 1, -10, 1),
            ("Calibrated", 1.2, 10, 3),
        ):
            values = np.asarray([1, 1.1, 1.3, 1.5, 1.7, 3.8]) * factor + shift
            native = boxplot_stats(values, bootstrap=None)[0]
            # Independent client computation: the bxp API never bootstraps quartiles.
            rng = np.random.default_rng(CI["seed"])
            medians = np.median(
                values[rng.integers(0, len(values), size=(CI["n_boot"], len(values)))],
                axis=1,
            )
            low, high = np.quantile(medians, [0.05, 0.95], method="linear")
            native["cilo"], native["cihi"] = float(low), float(high)
            for index, value in enumerate(values):
                row = {
                    "phase": phase,
                    "when": when,
                    "cohort": cohort,
                    "observed": float(value),
                    "predictor": index,
                    "method": method,
                    "temperature": temperature,
                    "precision": precision,
                    "id": f"original-{phase}-{method}-{index}",
                    "summary_median": float(native["med"]) if index == 0 else None,
                }
                for role in (
                    "q1",
                    "q3",
                    "whislo",
                    "whishi",
                    "mean",
                    "cilo",
                    "cihi",
                    "fliers",
                ):
                    row["summary_" + role] = (
                        (
                            native[role].tolist()
                            if role == "fliers"
                            else float(native[role])
                        )
                        if index == 0
                        else None
                    )
                for name, item in row.items():
                    data.setdefault(name, []).append(item)
    return data


def per_hue():
    return [
        {
            "level": "Control",
            "components": {
                "cap": {"color": "#007f87", "line_width": 1.6},
                "body": {"color": "#2899a6"},
            },
        },
        {
            "level": "Calibrated",
            "components": {
                "cap": {"color": "#8b3f8f", "line_width": 1.6},
                "body": {"color": "#a66aaf"},
            },
        },
    ]


def supplied(plot, category, *, panel=0, **options: Any):
    return plot.bxp(
        category,
        "summary_median",
        q1="summary_q1",
        q3="summary_q3",
        whislo="summary_whislo",
        whishi="summary_whishi",
        mean="summary_mean",
        cilo="summary_cilo",
        cihi="summary_cihi",
        fliers="summary_fliers",
        panel=panel,
        **options,
    )


def build_summary_pair():
    plot = mp.plot(observation_table()).theme("publication").size(16, 7).layout(1, 2)
    plot.font(size=11, title_size=15, label_size=12, tick_size=10)
    common: dict[str, Any] = {
        "group": "method",
        "hue_order": ["Control", "Calibrated"],
        "gap": 0.2,
        "cap_fraction": 0.8,
        "showmeans": True,
        "components": {
            "body": {"alpha": 0.9},
            "median": {"color": "#172033", "line_width": 1.3},
        },
        "hue_components": per_hue(),
    }
    plot.box("phase", "observed", median_ci=CI, panel=0, **common)
    supplied(plot, "phase", notch=True, panel=1, **common)
    for panel, title in enumerate(
        (
            "Raw observations: seeded 90% median CI",
            "Supplied columns: identical native geometry",
        )
    ):
        plot.labels(
            title=title, x="Declared season", y="Measured response (mm)", panel=panel
        )
        plot.ylim(0.5, 6.5, panel=panel).legend(
            title="Actual per-hue cap/body styles", location="upper left", panel=panel
        )
    return plot


def shared_mapping():
    return mp.SemanticSpec(
        scale_id="same-original-rows",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-20, 20],
        size="precision",
        size_norm=[1, 3],
        sizes=[2, 4],
        style="method",
        markers=["D", "^"],
    )


def build_shared_roles():
    plot = mp.plot(observation_table()).theme("publication").size(16, 8).layout(1, 2)
    plot.font(size=11, title_size=14, label_size=12, tick_size=10)
    config = shared_mapping()
    common: dict[str, Any] = {
        "semantics": config,
        "cmap_kind": "sequential",
        "colorbar": True,
        "clabel": "Temperature (degrees C)",
        "edge_color": "#334155",
    }
    plot.box(
        "phase",
        "observed",
        median_ci=CI,
        cap_fraction=0.8,
        components={
            "body": {"alpha": 1},
            "median": {"line_width": 1.2},
            "whisker": {"line_width": 0.7},
        },
        panel=0,
        **common,
    )
    plot.scatter("predictor", "observed", line_width=0.6, panel=1, **common)
    plot.labels(
        title="Box: BODY stroke pt; dash / real flier glyph",
        x="Season",
        y="Measured response (mm)",
        panel=0,
    )
    plot.labels(
        title="Scatter: nominal diameter pt; same raw row domains",
        x="Original replicate index",
        y="Measured response (mm)",
        panel=1,
    )
    for panel in range(2):
        plot.ylim(0.5, 9, panel=panel).legend(location="upper left", panel=panel)
    return plot


def build_live_dates():
    plot = mp.plot(observation_table()).theme("publication").size(20, 10)
    plot.font(size=11, title_size=14, label_size=12, tick_size=10)
    plot.date_axis("x", timezone="UTC")
    supplied(
        plot,
        "when",
        group="method",
        hue_order=["Control", "Calibrated"],
        showmeans=True,
        notch=True,
        cap_fraction=0.25,
        gap=0.2,
        components={"body": {"alpha": 0.9}},
        hue_components=per_hue(),
    )
    plot.labels(
        title="Saved views; explicit whole-template cap edit",
        x="Declared date category (UTC)",
        y="Measured response (mm)",
    )
    plot.ylim(0.5, 6.5).legend(title="Method / actual cap style", location="upper left")
    plot.facet(
        col="cohort", col_order=["left", "empty", "right"], col_wrap=2, live=True
    )
    plot.layout(2, 2, width_ratios=[3, 2])
    plot.dispatch(mp.actions.SetTitle("A cell-local title", panel=0))
    local = plot.to_json()
    plot = mp.Plot.from_json(local)
    template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, plot.spec.facet_template).template
    )
    cast(mp.BoxSpec, template.layers[0].box).cap_fraction = 1
    plot.facet_template(template)
    edited = plot.to_json()
    plot.store.undo()
    assert plot.to_json() == local
    plot.store.redo()
    assert plot.to_json() == edited
    assert plot.spec.data.columns == observation_table()
    return plot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_box")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(exist_ok=True, parents=True)
    for name, plot in (
        ("box_summaries", build_summary_pair()),
        ("box_shared_roles", build_shared_roles()),
        ("box_live_dates", build_live_dates()),
    ):
        mp.save_spec(plot.spec, directory / (name + ".mplot.json"))
        reopened = mp.Plot.from_json((directory / (name + ".mplot.json")).read_text())
        assert reopened.spec == plot.spec
        for extension in ("png", "svg", "pdf"):
            plt.close(reopened.save(str(directory / (name + "." + extension))))
    print(
        "PASS complete C03 raw/supplied/median CI/caps/per-hue/roles/date/"
        "live/history/reopen/native exports"
    )


if __name__ == "__main__":
    main()
