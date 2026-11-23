"""C02: real glyphs, physical packing scopes, shared roles and explicit live grids."""

from __future__ import annotations

import argparse
import copy
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def data():
    rows = []
    for cell, (category, when, cohort) in enumerate(
        [
            ("alpha", "2026-01-01", "left"),
            ("beta", "2026-07-01", "right"),
        ]
    ):
        for role, (temperature, precision, method) in enumerate(
            [
                (-10, 1, "A"),
                (0, 2, "B"),
                (10, 3, "A"),
            ]
        ):
            for predictor in range(3):
                observed = 1 + 0.5 * role + 0.2 * predictor + 0.08 * cell
                rows.append(
                    {
                        "category": category,
                        "date_category": when,
                        "predictor": predictor,
                        "observed": observed,
                        "replicate": observed + 0.03,
                        "temperature": temperature,
                        "precision": precision,
                        "method": method,
                        "cohort": cohort,
                        "id": f"original-{cell}-{role}-{predictor}",
                    }
                )
    return {name: [row[name] for row in rows] for name in rows[0]}


def mapping():
    return mp.SemanticSpec(
        scale_id="shared-observations",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-20, 20],
        size="precision",
        size_norm=[1, 3],
        sizes=[3, 7],
        style="method",
        markers=["s", "^"],
    )


def build_families():
    p = mp.plot(data()).theme("publication").size(16, 10).layout(2, 3)
    config = mapping()
    common = {
        "semantics": replace(config, legend=False),
        "cmap_kind": "sequential",
        "colorbar": True,
        "clabel": "Temperature (degrees C)",
    }
    point = {**common, "edge_color": "#334155", "line_width": 0.6}
    p.swarmplot(
        "category",
        "observed",
        pack_scope="replicates",
        panel=0,
        **{**point, "semantics": config},
    )
    p.swarmplot("category", "replicate", pack_scope="replicates", panel=0, **point)
    p.scatter("predictor", "observed", panel=1, **point)
    p.lineplot("predictor", "observed", errorbar=None, marker_size=4, panel=2, **common)
    p.stripplot("category", "observed", strip={"seed": 11}, panel=3, **point)
    p.ecdf("observed", panel=4, marker_size=4, **common)
    p.rug("observed", height=0.2, panel=5, **common)
    titles = [
        "Two declared members; true native glyphs",
        "Scatter: nominal diameter pt",
        "Line: stroke pt",
        "Strip: nominal diameter pt",
        "ECDF: stroke pt",
        "Rug: stroke pt / axes height",
    ]
    for panel, title in enumerate(titles):
        p.labels(title=title, panel=panel)
    for panel in [0, 1, 2, 3]:
        p.ylim(0.5, 4, panel=panel)
    p.legend(location="upper right", panel=0)
    p.labels(x="Declared category", y="Original measurement", panel=0)
    return p


def build_live():
    p = mp.plot(data()).theme("publication").size(20, 10)
    p.secondary_yaxis("Original measurement", scale="log").date_axis(
        "x", timezone="UTC"
    )
    config = mapping()
    for value in ["observed", "replicate"]:
        p.swarmplot(
            "date_category", value, axis="y2", pack_scope="members", semantics=config
        )
    p.labels(
        title="Live recipe: explicit whole-template edit",
        x="Declared date category (UTC)",
        y="Unused primary frame",
    )
    p.facet(col="cohort", col_order=["left", "empty", "right"], col_wrap=2, live=True)
    p.layout(2, 2, width_ratios=[3, 2])
    before = p.to_json()
    p.dispatch(mp.actions.SetTitle("A cell-local override", panel=0))
    local = p.to_json()
    reopened = mp.Plot.from_json(local)
    template = copy.deepcopy(reopened.spec.facet_template.template)
    for layer in template.layers:
        layer.pack_scope = "edited-members"
        layer.semantics.markers = ["D", "v"]
        layer.semantics.sizes = [4, 8]
        layer.semantics.legend = False
    reopened.facet_template(template)
    edited = reopened.to_json()
    reopened.store.undo()
    assert reopened.to_json() == local
    reopened.store.redo()
    assert reopened.to_json() == edited
    assert len(reopened.spec.panels) == 3
    assert reopened.spec.width_ratios == [3, 2]
    assert before != local != edited
    assert mp.apply(p.action_log) == p.spec
    assert reopened.spec.data.columns == data()
    return reopened


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_swarm")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, plot in [
        ("swarm_shared_families", build_families()),
        ("swarm_live_grid", build_live()),
    ]:
        mp.save_spec(plot.spec, directory / f"{name}.mplot.json")
        reopened = mp.Plot.from_json((directory / f"{name}.mplot.json").read_text())
        assert reopened.spec == plot.spec
        for extension in ["png", "svg", "pdf"]:
            plt.close(reopened.save(str(directory / f"{name}.{extension}")))
    print(
        "PASS C02 real glyphs/shared roles/scoped instances/date-y2/"
        "live-template/history/reopen/export"
    )


if __name__ == "__main__":
    main()
