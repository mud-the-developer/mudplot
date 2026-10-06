import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 70)
data = {"x": x, "y": np.sin(x)}
plot = (
    mp.plot(data)
    .line("x", "y")
    .annotate("maximum", [2.2, 1.18], to=[np.pi / 2, 1.0])
    .labels(x="Phase", y="Signal", title="Arrow annotation")
    .ylim(-1.2, 1.35)
    .size(4.5, 3.2)
)
