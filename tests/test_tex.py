import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot.spec import FigureSpec
from mudplot.tex import PT_PER_INCH, TEX_PRESETS, apply_tex, figsize_for


def test_figsize_matches_column_width():
    ctx = TEX_PRESETS["ieee"]
    w, h = figsize_for(ctx, fraction=1.0, aspect=0.5)
    assert w == ctx.columnwidth_pt / PT_PER_INCH
    assert h == w * 0.5


def test_figsize_full_width_uses_textwidth():
    ctx = TEX_PRESETS["ieee"]
    w, _ = figsize_for(ctx, full_width=True)
    assert w == ctx.textwidth_pt / PT_PER_INCH


def test_apply_tex_is_pure_and_sizes():
    spec = FigureSpec()
    before = spec.to_dict()
    ctx = TEX_PRESETS["nature"]
    out = apply_tex(spec, ctx, fraction=0.5)
    assert spec.to_dict() == before  # input untouched
    assert out.theme.font.family == ctx.family
    exp_w = 0.5 * ctx.columnwidth_pt / PT_PER_INCH
    assert abs(out.size[0] - exp_w) < 1e-9


def test_tex_preview_returns_figure():
    x = np.linspace(0, 1, 10)
    p = mp.plot({"x": list(x), "y": list(x**2)}).line("x", "y").labels(x="X", y="Y")
    fig = p.preview(tex="ieee")
    assert fig is not None
    assert len(fig.axes) >= 1


def test_unknown_tex_preset_raises():
    import pytest

    with pytest.raises(ValueError):
        mp.plot({"x": [1], "y": [2]}).line("x", "y").preview(tex="does-not-exist")
