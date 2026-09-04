import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot._render import render


def _spec_plot():
    x = np.linspace(0, 1, 20)
    data = {
        "x": list(x) * 2,
        "y": list(x**2) + list(x**0.5),
        "g": ["a"] * 20 + ["b"] * 20,
    }
    return mp.plot(data).line("x", "y", group="g").labels(x="X", y="Y")


def test_render_returns_figure():
    fig = render(_spec_plot().spec)
    assert fig is not None
    assert len(fig.axes) == 1


def test_render_is_deterministic_colors():
    p = _spec_plot()
    fig1 = render(p.spec)
    fig2 = render(p.spec)
    c1 = [ln.get_color() for ln in fig1.axes[0].lines]
    c2 = [ln.get_color() for ln in fig2.axes[0].lines]
    assert c1 == c2


def test_render_group_produces_two_series():
    fig = render(_spec_plot().spec)
    assert len(fig.axes[0].lines) == 2


def test_save_writes_file(tmp_path):
    path = tmp_path / "out.png"
    mp.save(_spec_plot().spec, str(path))
    assert path.exists() and path.stat().st_size > 0
