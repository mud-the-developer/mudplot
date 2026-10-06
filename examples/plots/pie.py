import mudplot as mp

data = {
    "component": ["Compute", "Storage", "Network", "Other"],
    "share": [46, 28, 17, 9],
}
plot = (
    mp.plot(data)
    .pie("component", "share")
    .labels(title="Resource share")
    .size(4.2, 3.4)
)
