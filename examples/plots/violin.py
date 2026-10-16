import mudplot as mp
import numpy as np

rng = np.random.default_rng(6)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.45)):
    for dose, effect in (("Low", 0), ("High", 1)):
        data["dose"].extend([dose] * 50)
        data["method"].extend([method] * 50)
        data["value"].extend(rng.normal(1 + shift + effect, 0.3, 50).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .violin(
        "dose",
        "value",
        group="method",
        orient="h",
        order=["Low", "High"],
        hue_order=["B", "A"],
        bw_method="silverman",
        points=100,
        gap=0.12,
        showextrema=False,
        edge_color="#4b5563",
        line_width=0.8,
    )
    .labels(x="Value", y="Dose", title="Horizontal nested violins")
    .legend(title="Method", location="lower right")
    .size(4.5, 3.2)
)
