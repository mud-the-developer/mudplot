import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 36), np.linspace(-2, 2, 24))
field = np.sin(x) * np.cos(1.5 * y)
plot = (
    mp.plot()
    .matrix("field", field)
    .heatmap("field", cmap_kind="diverging", clabel="Amplitude")
    .labels(x="Column", y="Row", title="Matrix heatmap")
    .size(4.5, 3.3)
)
