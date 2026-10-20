import mudplot as mp

data = {"event": [0.3, 1.0, 1.2, 1.2, 2.8, 3.1]}
plot = (
    mp.plot(data)
    .eventplot("event", offset=2, length=1, line_width=1.4)
    .labels(
        x="Event position (a.u.)", y="Raw offset (a.u.)", title="Synthetic event train"
    )
    .legend(show=False)
    .size(4.5, 3.5)
)
