import mudplot as mp

no_ticks = mp.TickSpec(locator=mp.LocatorSpec(kind="none"))
plot = (
    mp.plot()
    .table(
        mp.LiteralTableSpec(
            [["2.3", "m"], ["4", "samples"]],
            [0.12, 0.25, 0.76, 0.5],
            row_labels=["Span", "Run"],
            column_labels=["Value", "Unit"],
            font_size=12,
            header_color="#dcebee",
        )
    )
    .ticks("x", no_ticks)
    .ticks("y", no_ticks)
    .size(4.8, 3.6)
)
