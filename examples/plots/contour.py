import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 48), np.linspace(-2, 2, 34))
field = np.exp(-(x**2 + y**2) / 3) * np.cos(2 * x)
plot = (
    mp.plot()
    .matrix("field", field)
    .contour("field", levels=9, cmap_kind="diverging", clabel="Level")
    .labels(x="Column", y="Row", title="Contour lines")
    .size(4.5, 3.3)
)
