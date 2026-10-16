import mudplot as mp
import numpy as np

rng = np.random.default_rng(19)
data = {"dose": [], "response": [], "method": []}
for method, shift in (("A", 0), ("B", 0.25)):
    for dose, step in (("Low", 0), ("High", 0.6)):
        data["dose"].extend([dose] * 22)
        data["method"].extend([method] * 22)
        data["response"].extend(
            np.exp(rng.normal(shift + step, 0.16, 22)).round(2).tolist()
        )
plot = (
    mp.plot(data)
    .theme("publication")
    .swarmplot(
        "dose",
        "response",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        marker_size=4,
        edge_color="#ffffff",
        line_width=0.4,
        gap=0.1,
    )
    .yscale("log")
    .labels(x="Dose", y="Response (log scale)", title="Display-space swarm packing")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
