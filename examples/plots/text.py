import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 70)
data = {"x": x, "y": np.sin(x)}
plot = (
    mp.plot(data)
    .line("x", "y")
    .text("peak region", [1.65, 1.08], color="#333333")
    .labels(x="Phase", y="Signal", title="Placed text")
    .ylim(-1.2, 1.3)
    .size(4.5, 3.2)
)
