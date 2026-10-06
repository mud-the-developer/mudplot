import mudplot as mp
import numpy as np

x = np.linspace(0, 10, 80)
data = {"time": x, "signal": 1 / (1 + np.exp(-(x - 5)))}
plot = (
    mp.plot(data)
    .line("time", "signal")
    .vline(5, label="Intervention", line_style="--", color="#555555")
    .labels(x="Time", y="Response", title="Event marker")
    .legend()
    .size(4.5, 3.2)
)
