"""Runnable weighted/unweighted/count-width/log-space violin comparison.

Synthetic seeded observations, not experimental measurements. Run from the
repository root with python examples/weighted_violin.py.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.collections import PolyCollection


def main():
    rng = np.random.default_rng(2026)
    raw = {"dose": [], "group": [], "value": [], "weight": []}
    for dose, offset in [("Low", 0), ("High", 0.4)]:
        for group, shift in [("Control", 0), ("Treatment", 0.25)]:
            values = np.exp(rng.normal(0.8 + offset + shift, 0.35, 18))
            weights = np.where(values > np.median(values), 4.0, 1.0)
            if dose == "High" and group == "Control":
                weights *= 0.4
            raw["dose"].extend([dose] * len(values))
            raw["group"].extend([group] * len(values))
            raw["value"].extend(values.tolist())
            raw["weight"].extend(weights.tolist())
    p = mp.plot(raw).theme("publication").layout(2, 2).size(10, 7)
    titles = [
        "Unweighted KDE / linear quartiles",
        "Relative-weight KDE / inverse-ECDF quartiles",
        "Count width = weight mass, NOT row count",
        "Horizontal / log10-fit weighted mean + median",
    ]
    for panel, title in enumerate(titles):
        horizontal = panel == 3
        weighted = panel > 0
        p.violin(
            "dose",
            "value",
            group="group",
            weights="weight" if weighted else None,
            order=["Low", "High"],
            hue_order=["Control", "Treatment"],
            split=True,
            inner="legacy" if horizontal else "quart",
            orient="h" if horizontal else "v",
            stat_scale="axis" if horizontal else "data",
            density_norm="count" if panel == 2 else "width",
            common_norm=panel == 2,
            cut=2,
            clip=(0.2, 30),
            points=101,
            alpha=0.6,
            edge_color="#334155",
            line_width=0.8,
            panel=panel,
            showmeans=True if horizontal else None,
            showextrema=False if horizontal else None,
        )
        p.labels(
            x="Response (log display)" if horizontal else "Dose",
            y="Dose" if horizontal else "Response",
            title=title,
            panel=panel,
        )
        p.legend(show=panel == 0, title="Group", panel=panel)
    p.xscale("log", panel=3)
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    fig = p.render()
    assert all(
        sum(isinstance(c, PolyCollection) for c in ax.collections) == 4
        for ax in fig.axes
    )
    plt.close(fig)
    out = Path(__file__).resolve().parents[1] / "docs" / "images"
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        plt.close(p.save(str(out / f"weighted_violin.{suffix}")))
    mp.save_spec(p.spec, out / "weighted_violin.mplot.json")
    assert not plt.get_fignums()
    print("OK weighted violin: covariance/ECDF marks/count mass/raw-log geometry")


if __name__ == "__main__":
    main()
