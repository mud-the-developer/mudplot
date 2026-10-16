import mudplot as mp
import numpy as np

rng = np.random.default_rng(83)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.4)):
    for dose, effect in (("Low", 0), ("High", 0.9)):
        data["dose"].extend([dose] * 128)
        data["method"].extend([method] * 128)
        data["value"].extend(rng.normal(1 + shift + effect, 0.4, 128).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .boxenplot(
        "dose",
        "value",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        k_depth=4,
        width_method="exponential",
        gap=0.15,
        edge_color="#4b5563",
        line_width=0.7,
        marker_size=2.5,
    )
    .labels(x="Dose", y="Response", title="Letter values / quantiles, not CI")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
