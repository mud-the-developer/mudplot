import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 48), np.linspace(-2, 2, 34))
field = np.sin(x) * np.exp(-0.35 * y**2)
plot = (
    mp.plot()
    .matrix("field", field)
    .contourf("field", levels=12, cmap_kind="diverging", clabel="Amplitude")
    .labels(x="Column", y="Row", title="Filled contours")
    .size(4.5, 3.3)
)
