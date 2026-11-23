import mudplot as mp

plot = (
    mp.plot()
    .matrix("u", [[1] * 4 for _ in range(3)])
    .matrix("v", [[0] * 4 for _ in range(3)])
    .streamplot(
        vector=mp.VectorSpec(
            x_coords=[0, 1, 2, 3],
            y_coords=[0, 1, 2],
            u_matrix="u",
            v_matrix="v",
            start_points=[[0.1, 0.35], [0.1, 1], [0.1, 1.65]],
            integration_direction="forward",
        ),
        color="#225761",
    )
    .xlim(0, 3.2)
    .ylim(0, 2)
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
