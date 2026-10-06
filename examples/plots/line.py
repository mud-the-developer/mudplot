import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 80)
data = {
    "x": np.tile(x, 2),
    "signal": np.r_[np.sin(x), 0.65 * np.cos(x)],
    "series": ["sin"] * len(x) + ["cos"] * len(x),
}
plot = (
    mp.plot(data)
    .line("x", "signal", group="series")
    .labels(x="Phase (rad)", y="Signal", title="Grouped line")
    .legend(title="Series")
    .size(4.5, 3.2)
)
