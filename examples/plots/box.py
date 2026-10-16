import mudplot as mp
import numpy as np

rng = np.random.default_rng(5)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.55)):
    for dose, effect in (("Low", 0), ("High", 1)):
        data["dose"].extend([dose] * 40)
        data["method"].extend([method] * 40)
        data["value"].extend(rng.normal(1 + shift + effect, 0.35, 40).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .box(
        "dose",
        "value",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        whis=(5, 95),
        gap=0.16,
        showmeans=True,
        edge_color="#4b5563",
        line_width=0.8,
    )
    .labels(x="Dose", y="Value", title="Nested boxes / 5-95% whiskers")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
