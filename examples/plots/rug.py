import mudplot as mp
import numpy as np

rng = np.random.default_rng(9)
values = np.r_[rng.normal(-0.6, 0.6, 45), rng.normal(0.9, 0.5, 45)]
data = {"value": values}
plot = (
    mp.plot(data)
    .kde("value", color="#777777", alpha=0.75)
    .rug("value", color="#ef6674", line_width=1.1, alpha=0.65)
    .labels(x="Value", y="Density", title="KDE with rug marks")
    .size(4.5, 3.2)
)
