"""Layer-local vs named figure-shared scatter scopes, synthetic observations."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def main():
    rng = np.random.default_rng(2026)
    n = 32
    raw = {
        "left": np.linspace(1, 2, 16).tolist() + [None] * 16,
        "right": [None] * 16 + np.linspace(2, 3, 16).tolist(),
        "y": rng.normal(2, 0.25, n).tolist(),
        "h": ["A" if i % 2 else "B" for i in range(16)]
        + ["B" if i % 2 else "C" for i in range(16)],
        "m": np.linspace(0, 4, 16).tolist() + np.linspace(6, 10, 16).tolist(),
        "s": ["X" if i % 3 else "Y" for i in range(n)],
    }
    p = mp.plot(raw).theme("publication").layout(2, 2).size(12, 8)
    for panel in range(4):
        shared = panel >= 2
        x = "left" if panel % 2 == 0 else "right"
        cfg = mp.SemanticSpec(
            scale_id="study" if shared else None, hue="h", size="m", style="s"
        )
        p.scatter(x, "y", semantics=cfg, alpha=0.8, panel=panel)
        p.labels(
            x="Observed x",
            y="Response",
            title=(
                "Named study: pooled A/B/C + [0,10]"
                if shared
                else "Layer-local: selected colours/range"
            ),
            panel=panel,
        )
        p.legend(
            location="outside right", title="Mapping guides (not data)", panel=panel
        )
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    fig = p.render()
    assert all(
        sum(len(np.asarray(c.get_offsets())) for c in ax.collections) == 16
        for ax in fig.axes
    )
    assert (
        fig.axes[2].get_legend_handles_labels()[1]
        == fig.axes[3].get_legend_handles_labels()[1]
    )
    plt.close(fig)
    out = Path(__file__).resolve().parents[1] / "docs/images"
    for suffix in ("png", "svg"):
        plt.close(p.save(str(out / f"shared_semantics.{suffix}")))
    mp.save_spec(p.spec, out / "shared_semantics.mplot.json")
    assert not plt.get_fignums()
    print(
        "OK local vs named pooled semantic domains: rows/colours/sizes/markers/guides"
    )


if __name__ == "__main__":
    main()
