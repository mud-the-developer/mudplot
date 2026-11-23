"""D07 rugs: axes-fraction heights, stroke semantics, observation clocks and y2."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "observation": [1, 2, 4, 3, 5, 6],
        "response": [3, 2, 5, 4, 6, 5],
        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-05",
            "2026-01-03",
            "2026-01-07",
            "2026-01-09",
        ],
        "temperature": [-10, -6, -2, 2, 6, 10],
        "precision": [1, 2, 3, 1, 2, 3],
        "method": ["A"] * 3 + ["B"] * 3,
        "id": ["a3", "a1", "a2", "b2", "b3", "b1"],
    }
    p = mp.plot(data).theme("publication").size(18, 9).layout(2, 2)
    p.kde("observation", color="#626262", label="Pooled density", panel=0)
    p.rug("observation", group="method", height=0.12, line_width=2, panel=0)
    p.labels(
        title="Rug height is not density", x="Observed value", y="Density", panel=0
    )
    shared = mp.SemanticSpec(
        scale_id="observations",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-10, 10],
        size="precision",
        size_norm=[1, 3],
        sizes=[1, 4],
    )
    common = {
        "semantics": shared,
        "cmap_kind": "diverging",
        "colorbar": True,
        "clabel": "Temperature (degrees C)",
    }
    p.scatter(
        "observation",
        "response",
        panel=1,
        **{**common, "semantics": replace(shared, legend=False)},
    )
    p.rug("observation", height=0.13, panel=1, **common)
    p.rug("response", orient="h", height=0.13, panel=1, **common)
    p.labels(
        title="Shared hue; stroke points, not marker area",
        x="Observed value",
        y="Response",
        panel=1,
    )
    p.legend(location="center right", panel=1)
    p.line("observation", "response", color="#626262", panel=2)
    p.secondary_yaxis("Observation date (UTC)", panel=2)
    p.date_axis("y2", timezone="UTC", panel=2)
    p.rug(
        "date",
        orient="h",
        axis="y2",
        height=0.18,
        panel=2,
        semantics=replace(shared, legend=False),
        cmap_kind="diverging",
    )
    p.labels(
        title="Horizontal y2: right edge inward",
        x="Unrelated numeric predictor",
        y="Primary response",
        panel=2,
    )
    p.rug(
        "date",
        height=0.22,
        panel=3,
        semantics={"style": "method", "dashes": ["-", "--"]},
        line_width=2,
    )
    p.date_axis("x", timezone="UTC", panel=3)
    p.ylim(0, 1, panel=3)
    p.labels(
        title="Irregular dates; named dash strokes",
        x="Observed date (UTC)",
        y="Axes-fraction rug extent",
        panel=3,
    )
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_rug")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    before = p.to_json()
    p.dispatch(mp.actions.RemoveLayer(0, panel=3))
    edited_layer = replace(
        mp.Plot.from_json(before).spec.panels[3].layers[0], width=0.3
    )
    p.dispatch(mp.actions.AddLayer(edited_layer, panel=3))
    p.store.undo()
    p.store.undo()
    assert p.to_json() == before
    p.store.redo()
    p.store.redo()
    assert p.spec.panels[3].layers[0].width == 0.3
    assert p.spec == mp.apply(p.action_log)
    mp.save_spec(p.spec, directory / "rug_workflow.mplot.json")
    reopened = mp.Plot.from_json(
        mp.to_json(mp.load_spec(directory / "rug_workflow.mplot.json"))
    )
    assert reopened.spec == p.spec
    for extension in ("png", "svg", "pdf"):
        plt.close(reopened.save(str(directory / f"rug_workflow.{extension}")))
    facets = mp.plot(p.spec.data.columns).theme("publication").size(11, 3)
    facets.rug("observation", orient="h", height=0.15, group="method")
    facets.facet(col="method", col_order=["A", "empty", "B"])
    mp.save_spec(facets.spec, directory / "rug_facets.mplot.json")
    for extension in ("png", "svg", "pdf"):
        plt.close(facets.save(str(directory / f"rug_facets.{extension}")))
    print(
        "PASS D07 source/actions/edit/undo/redo/save/reopen/PNG/SVG/PDF "
        "and empty facets"
    )


if __name__ == "__main__":
    main()
