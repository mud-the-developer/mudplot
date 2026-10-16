"""Synthetic independent hue/size/style, global bounds and honest guide legends."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def main():
    rng = np.random.default_rng(2026)
    n = 48
    raw = {
        "x": np.exp(rng.normal(0.6, 0.3, n)).tolist(),
        "y": np.exp(rng.normal(0.8, 0.3, n)).tolist(),
        "h": ["A" if i % 2 else "B" for i in range(n)],
        "m": np.linspace(0, 10, n).tolist(),
        "s": ["X" if i % 3 else "Y" for i in range(n)],
    }
    p = mp.plot(raw).theme("publication").layout(2, 2).size(12, 8)
    configs = [
        mp.SemanticSpec(hue="h", size="m", style="s", size_norm=[0, 10]),
        mp.SemanticSpec(hue="m", hue_kind="numeric", hue_norm=[0, 10], style="s"),
        mp.SemanticSpec(
            hue="h",
            hue_order=["empty", "B", "A"],
            size="h",
            size_kind="categorical",
            size_order=["B", "A"],
            style="s",
            style_order=["absent", "Y", "X"],
            markers=["D", "s", "o"],
        ),
        mp.SemanticSpec(
            hue="h", size="m", size_norm=[2, 8], sizes=[0, 10], style="s", legend=False
        ),
    ]
    titles = [
        "Independent category hue / numeric size / style",
        "Numeric hue: ONE global norm, not per style",
        "Reserved order / categorical size / no ghost rows",
        "Log coordinates / clipped size mapping, rows kept",
    ]
    for panel, (config, title) in enumerate(zip(configs, titles, strict=True)):
        p.scatter("x", "y", semantics=config, alpha=0.7, panel=panel)
        p.labels(x="Observed x", y="Observed y", title=title, panel=panel)
        p.legend(
            location="outside right", title="Mapping guides (not data)", panel=panel
        )
    p.xscale("log", panel=3).yscale("log", panel=3)
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    fig = p.render()
    assert all(
        sum(len(np.asarray(c.get_offsets())) for c in ax.collections) == n
        for ax in fig.axes
    )
    plt.close(fig)
    out = Path(__file__).resolve().parents[1] / "docs/images"
    for suffix in ("png", "svg"):
        plt.close(p.save(str(out / f"scatter_semantics.{suffix}")))
    mp.save_spec(p.spec, out / "scatter_semantics.mplot.json")
    assert not plt.get_fignums()
    print("OK independent scatter roles/global mapping/guide-only legends")


if __name__ == "__main__":
    main()
