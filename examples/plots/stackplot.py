import mudplot as mp
import numpy as np

x = np.arange(8)
data = {
    "x": np.tile(x, 3),
    "value": np.r_[2 + 0.4 * x, 1.4 + 0.3 * np.sin(x), 0.8 + 0.2 * np.cos(x)],
    "component": np.repeat(["Compute", "Storage", "Network"], len(x)),
}
plot = (
    mp.plot(data)
    .stackplot("x", "value", group="component", alpha=0.85)
    .labels(x="Week", y="Usage", title="Resource composition")
    .legend(title="Component", location="outside right")
    .size(5.2, 3.2)
)
