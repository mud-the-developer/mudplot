"""Independent curve roles, pointwise bands and named line/scatter scopes."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def main():
    raw = {name: [] for name in ("t", "y", "method", "style", "mass", "weight", "unit")}
    for method, shift, mass in (("A", 0, 0), ("B", 1, 10)):
        for style, offset in (("X", 0), ("Y", 0.4)):
            for t in (1, 2, 4):
                for rep in range(3):
                    for name, value in {
                        "t": t,
                        "y": 1 + shift + offset + 0.4 * t + (0.1 * (rep - 1)),
                        "method": method,
                        "style": style,
                        "mass": mass,
                        "weight": rep + 1,
                        "unit": f"u{rep}",
                    }.items():
                        raw[name].append(value)
    p = mp.plot(raw).layout(1, 3).size(15, 4.5).theme("publication")
    cfg = mp.SemanticSpec(
        hue="method", size="mass", sizes=[1, 3], style="style", dashes=["-", "--"]
    )
    p.lineplot("t", "y", semantics=cfg, errorbar="sd", error_alpha=0.15, panel=0)
    p.labels(
        x="Time", y="Response", title="Independent hue / width / marker+dash", panel=0
    )
    numeric = mp.SemanticSpec(hue="mass", hue_kind="numeric", style="style")
    p.lineplot(
        "t",
        "y",
        semantics=numeric,
        weights="weight",
        units="unit",
        n_boot=200,
        seed=7,
        error_style="bars",
        orient="h",
        panel=1,
    )
    p.labels(
        x="Response", y="Time", title="Global numeric hue / within-x unit CI", panel=1
    )
    shared = mp.SemanticSpec(
        scale_id="study", hue="method", size="mass", sizes=[1, 3], style="style"
    )
    p.lineplot("t", "y", semantics=shared, errorbar="sd", panel=2)
    p.scatter("t", "y", semantics=shared, alpha=0.35, panel=2)
    p.labels(
        x="Time",
        y="Response",
        title="Shared line + scatter (distinct pt meanings)",
        panel=2,
    )
    for panel in range(3):
        p.legend(
            location="outside right", title="Mapping guides (not data)", panel=panel
        )
    assert mp.validate(p.spec) == []
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    out = Path(__file__).resolve().parents[1] / "docs/images"
    for ext in ("png", "svg"):
        plt.close(p.save(str(out / f"line_semantics.{ext}")))
    mp.save_spec(p.spec, out / "line_semantics.mplot.json")
    assert not plt.get_fignums()
    print("OK line tuple estimates/widths/dashes/pointwise shared domains")


if __name__ == "__main__":
    main()
