"""Synthetic raw/weighted/log-space numeric-x pointwise interval comparison."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def main():
    rng = np.random.default_rng(2026)
    raw = {"time": [], "response": [], "method": [], "weight": [], "unit": []}
    for method, shift in [("Control", 0), ("Treatment", 0.25)]:
        for time in (0.5, 1, 2, 4):
            values = np.exp(rng.normal(0.3 + 0.25 * time + shift, 0.3, 6))
            raw["time"].extend([time] * 6)
            raw["response"].extend(values.tolist())
            raw["method"].extend([method] * 6)
            raw["weight"].extend([1, 1, 2, 2, 3, 3])
            raw["unit"].extend(["A", "A", "B", "B", "C", "C"])
    p = mp.plot(raw).theme("publication").layout(1, 3).size(15, 4)
    p.lineplot("time", "response", group="method", n_boot=251, seed=19)
    p.labels(x="Time", y="Response", title="Raw means / pointwise CI")
    p.legend(title="Method", location="upper left")
    p.lineplot(
        "time",
        "response",
        group="method",
        weights="weight",
        units="unit",
        n_boot=251,
        seed=19,
        error_style="bars",
        capsize=3,
        panel=1,
    )
    p.labels(x="Time", y="Response", title="Weighted / within-x unit CI", panel=1)
    p.legend(show=False, panel=1)
    p.lineplot(
        "time",
        "response",
        group="method",
        errorbar="se",
        stat_scale="axis",
        error_alpha=0.3,
        panel=2,
    )
    p.xscale("log", panel=2).yscale("log", panel=2)
    p.labels(
        x="Time (log display)",
        y="Response (log display)",
        title="Log10-fit / pointwise SEM",
        panel=2,
    )
    p.legend(show=False, panel=2)
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    out = Path(__file__).resolve().parents[1] / "docs/images"
    for suffix in ("png", "svg"):
        plt.close(p.save(str(out / f"line_estimates.{suffix}")))
    mp.save_spec(p.spec, out / "line_estimates.mplot.json")
    assert not plt.get_fignums()
    print("OK raw/weighted/log-space line estimates, POINTWISE not simultaneous")


if __name__ == "__main__":
    main()
