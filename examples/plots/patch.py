import mudplot as mp

plot = (
    mp.plot()
    .patch(
        mp.PatchSpec("polygon", [[1, 1], [4, 1], [3, 3], [1, 2]]),
        native_style=mp.ComponentStyleSpec(
            color="#7eb4bd", edge_color="#254d55", line_width=1.4
        ),
    )
    .xlim(0, 5)
    .ylim(0, 4)
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
