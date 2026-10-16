import mudplot as mp
import numpy as np

rng = np.random.default_rng(28)
data = {
    "value": np.round(
        np.r_[rng.lognormal(0, 0.45, 60), rng.lognormal(0.4, 0.5, 80)], 1
    ),
    "weight": rng.integers(1, 5, 140),
    "group": ["Control"] * 60 + ["Treatment"] * 80,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .ecdf("value", weights="weight", group="group", line_width=1.8)
    .labels(
        x="Observed value", y="Within-curve proportion", title="Weighted empirical CDF"
    )
    .legend()
    .size(4.5, 3.2)
)
