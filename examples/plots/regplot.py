import mudplot as mp
import numpy as np

rng = np.random.default_rng(7)
x = np.linspace(-2.5, 2.5, 48)
data = {"x": x, "y": 0.4 + 0.7 * x + 0.35 * x**2 + rng.normal(0, 0.55, len(x))}
plot = (
    mp.plot(data)
    .regplot("x", "y", degree=2, confidence=95, marker_size=4)
    .labels(x="Input", y="Response", title="Polynomial regression")
    .size(4.5, 3.2)
)
