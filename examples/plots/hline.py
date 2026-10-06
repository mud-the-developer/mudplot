import mudplot as mp
import numpy as np

x = np.arange(8)
data = {"x": x, "y": [0.7, 0.9, 1.1, 1.35, 1.2, 1.55, 1.7, 1.8]}
plot = (
    mp.plot(data)
    .line("x", "y", marker="o")
    .hline(1.5, label="Target", line_style="--", color="#555555")
    .labels(x="Run", y="Score", title="Horizontal threshold")
    .legend()
    .size(4.5, 3.2)
)
