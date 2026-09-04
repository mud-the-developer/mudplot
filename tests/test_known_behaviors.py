"""Documents intentional, order-dependent behaviours that could otherwise be
mistaken for bugs. These tests lock in the *documented* semantics so a future
change can't silently alter them without a test failure forcing a conscious
decision (and a docs update).
"""

import mudplot as mp


def test_theme_after_palette_resets_palette_customisation():
    # .theme(name) replaces the *entire* ThemeSpec (font/axes/grid/ticks/
    # palette) with the preset's defaults. Calling .palette(...) before
    # .theme(...) means that customisation is discarded -- this is
    # documented on Plot.theme(), not a bug. The fix is call order:
    # .theme(...) first, then .palette(...) on top.
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    default_hue = p.spec.theme.palette.hue_start

    lost = p.palette(hue_start=90).theme("boxed")
    assert lost.spec.theme.palette.hue_start == default_hue

    kept = (
        mp.plot({"x": [1], "y": [2]})
        .line("x", "y")
        .theme("boxed")
        .palette(hue_start=90)
    )
    assert kept.spec.theme.palette.hue_start == 90


def test_journal_after_size_resets_size():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    lost = p.size(9.0, 9.0).journal("ieee")
    assert lost.spec.size != [9.0, 9.0]

    kept = mp.plot({"x": [1], "y": [2]}).line("x", "y").journal("ieee").size(9.0, 9.0)
    assert kept.spec.size == [9.0, 9.0]
