import mudplot as mp
import numpy as np

rng = np.random.default_rng(4)
data = {
    "value": np.r_[rng.normal(-0.5, 0.75, 180), rng.normal(0.8, 0.55, 180)],
    "group": ["Control"] * 180 + ["Treatment"] * 180,
}
plot = (
    mp.plot(data)
    .hist(
        "value",
        bins=np.histogram_bin_edges(data["value"], bins=18).tolist(),
        density=True,
        group="group",
        alpha=0.55,
    )
    .labels(x="Value", y="Density", title="Grouped histogram")
    .legend()
    .size(4.5, 3.2)
)
