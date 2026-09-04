import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot._render import render


def _xy(n=20):
    x = np.linspace(0, 1, n)
    return {
        "x": list(x),
        "y": list(x**2),
        "lo": list(x**2 - 0.1),
        "hi": list(x**2 + 0.1),
        "err": [0.05] * n,
        "g": ["a"] * n,
    }


def test_errorbar_layer():
    fig = render(mp.plot(_xy()).errorbar("x", "y", yerr="err").spec)
    assert len(fig.axes[0].containers) >= 1  # errorbar container present


def test_band_layer_draws_fill():
    fig = render(mp.plot(_xy()).band("x", "lo", "hi").line("x", "y").spec)
    assert len(fig.axes[0].collections) >= 1  # PolyCollection from fill_between


def test_hline_vline():
    fig = render(mp.plot(_xy()).line("x", "y").hline(0.5).vline(0.5).spec)
    # 1 data line + 2 reference lines
    assert len(fig.axes[0].lines) == 3


def test_text_and_annotate():
    p = (
        mp.plot(_xy())
        .line("x", "y")
        .text("hi", at=[0.2, 0.5])
        .annotate("peak", at=[0.5, 0.6], to=[0.9, 0.9])
    )
    fig = render(p.spec)
    assert len(fig.axes[0].texts) >= 2


def test_multi_panel_layout():
    data = _xy()
    p = mp.plot(data).layout(1, 2).line("x", "y", panel=0).scatter("x", "y", panel=1)
    fig = render(p.spec)
    assert len(fig.axes) == 2
    assert len(p.spec.panels) == 2


def test_layout_action_roundtrip():
    p = mp.plot(_xy()).layout(2, 2).line("x", "y", panel=3)
    rebuilt = mp.Plot.from_json(p.to_json())
    assert rebuilt.spec.layout == [2, 2]
    assert len(rebuilt.spec.panels) == 4


def test_new_layer_fields_serialize():
    p = mp.plot(_xy()).errorbar("x", "y", yerr="err", capsize=3)
    d = p.spec.panels[0].layers[0].to_dict()
    assert d["yerr"] == "err"
    assert d["capsize"] == 3
