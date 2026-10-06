import mudplot as mp
import numpy as np

rng = np.random.default_rng(21)
conditions = ["Control", "Low", "High"]
data = {
    "condition": np.repeat(conditions, 24),
    "value": np.concatenate(
        [
            rng.normal(1.0, 0.12, 24),
            rng.normal(1.35, 0.16, 24),
            rng.normal(1.75, 0.2, 24),
        ]
    ),
}
plot = (
    mp.plot(data)
    .stripplot(
        "condition", "value", group="condition", jitter=0.18, marker_size=4, alpha=0.75
    )
    .labels(x="Condition", y="Response", title="Raw observations")
    .legend(show=False)
    .size(4.5, 3.2)
)
