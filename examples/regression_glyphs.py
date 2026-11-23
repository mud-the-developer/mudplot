"""Keep the weighted experiment while mapping each visible glyph by raw temperature."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    rows = {
        "distance": [1, 2, 3, 4, 5],
        "response": [2, 4, 13, 8, 16],
        "criterion_mass": [1, 1, 4, 1, 1],
        "use": ["Training"] * 4 + ["Held out"],
        "temperature": [10, 20, None, 40, 50],
    }
    roles = mp.SemanticSpec(
        hue="temperature",
        hue_kind="numeric",
        style="use",
        style_order=["Training", "Held out"],
        markers=["o", "s"],
        scale_id="temperature",
        legend=False,
    )
    sampling = {"train": {"use": "Training"}, "query": {"use": "Held out"}}
    p = mp.plot(rows).theme("paper").layout(1, 2).size(9.2, 4.65)
    p.regplot(
        "distance",
        "response",
        weights="criterion_mass",
        semantics=roles,
        regression={
            "sampling": sampling,
            "components": {"fit": {"color": "#37474f", "line_style": "--"}},
        },
        colorbar=True,
        clabel="Temperature (°C)",
        edge_color="#26394a",
        line_width=1,
    )
    p.residplot(
        "distance",
        "response",
        weights="criterion_mass",
        semantics=roles,
        regression={"sampling": sampling},
        edge_color="#26394a",
        line_width=1,
        panel=1,
    )
    p.labels(
        x="Distance (m)",
        y="Response (cm)",
        title="Weighted fit and hold-out prediction",
    )
    p.labels(
        x="Distance (m)",
        y="Observed minus fitted (cm)",
        title="Hold-out residual",
        panel=1,
    )
    p.xlim(0.55, 5.45).ylim(0, 19)
    p.xlim(0.55, 5.45, panel=1).ylim(-2.1, 0.45, panel=1)
    return p.shared_guides([{"scale_id": "temperature", "location": "outside bottom"}])


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    figure = build()
    (out / "regression-glyphs.mplot.json").write_text(
        figure.to_json(), encoding="utf-8"
    )
    for suffix in ("png", "svg", "pdf"):
        figure.save(str(out / f"regression-glyphs.{suffix}"))
