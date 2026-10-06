import mudplot as mp
import numpy as np

x = np.linspace(0, 6, 70)
mean = np.sin(x) * np.exp(-x / 9)
spread = 0.12 + 0.03 * x
data = {"x": x, "mean": mean, "lower": mean - spread, "upper": mean + spread}
plot = (
    mp.plot(data)
    .band("x", "lower", "upper", label="Range", alpha=0.25)
    .line("x", "mean", label="Mean")
    .labels(x="Time", y="Signal", title="Uncertainty band")
    .legend()
    .size(4.5, 3.2)
)
