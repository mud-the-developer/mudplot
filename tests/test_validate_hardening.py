"""Additional validate()/reducer safety checks added during the hardening
pass: data integrity, bounds checking, and friendly errors for bad actions.
"""

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.spec import FigureSpec


def test_mismatched_column_lengths_caught():
    spec = FigureSpec()
    spec.data.columns = {"x": [1, 2, 3], "y": [1, 2]}
    issues = mp.validate(spec)
    assert any("mismatched lengths" in i for i in issues)


def test_equal_column_lengths_pass():
    spec = FigureSpec()
    spec.data.columns = {"x": [1, 2, 3], "y": [4, 5, 6]}
    assert mp.validate(spec) == []


def test_jagged_matrix_caught():
    spec = FigureSpec()
    spec.data.matrices = {"m": [[1, 2, 3], [4, 5]]}
    issues = mp.validate(spec)
    assert any("jagged rows" in i for i in issues)


def test_rectangular_matrix_passes():
    spec = FigureSpec()
    spec.data.matrices = {"m": [[1, 2, 3], [4, 5, 6]]}
    assert mp.validate(spec) == []


def test_empty_panels_caught():
    spec = FigureSpec(panels=[])
    issues = mp.validate(spec)
    assert any("no panels" in i for i in issues)


def test_invalid_spine_chars_caught():
    spec = FigureSpec()
    spec.theme.axes.spines = "LBX"
    issues = mp.validate(spec)
    assert any("spines" in i and "X" in i for i in issues)


def test_valid_spine_chars_pass():
    spec = FigureSpec()
    spec.theme.axes.spines = "LRTB"
    assert mp.validate(spec) == []


def test_alpha_out_of_range_caught():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y", alpha=2.0)
    issues = mp.validate(p.spec)
    assert any("alpha" in i for i in issues)


def test_alpha_boundary_values_pass():
    for a in (0.0, 1.0, 0.5):
        p = mp.plot({"x": [1], "y": [2]}).line("x", "y", alpha=a)
        assert mp.validate(p.spec) == []


def test_text_at_wrong_length_caught():
    p = mp.plot({}).text("hi", at=[1, 2, 3])
    issues = mp.validate(p.spec)
    assert any("'at'" in i for i in issues)


def test_annotate_to_wrong_length_caught():
    p = mp.plot({}).annotate("x", at=[0, 0], to=[1, 1, 1])
    issues = mp.validate(p.spec)
    assert any("'to'" in i for i in issues)


def test_set_colorbar_out_of_range_raises_valueerror():
    spec = mp.plot({"x": [1], "y": [2]}).line("x", "y").spec
    with pytest.raises(ValueError, match="out of range"):
        mp.reduce(spec, A.SetColorbar(layer_index=9))


def test_set_colorbar_negative_index_raises():
    spec = mp.plot({"x": [1], "y": [2]}).line("x", "y").spec
    with pytest.raises(ValueError, match="out of range"):
        mp.reduce(spec, A.SetColorbar(layer_index=-1))


def test_set_colorbar_valid_index_works():
    spec = mp.plot({"x": [1], "y": [2]}).line("x", "y").spec
    out = mp.reduce(spec, A.SetColorbar(layer_index=0, label="v"))
    assert out.panels[0].layers[0].colorbar is True
    assert out.panels[0].layers[0].clabel == "v"


def test_set_encoding_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetEncoding(params={"font": "nope"}))


def test_set_encoding_accepts_known_fields():
    out = mp.reduce(FigureSpec(), A.SetEncoding(params={"redundant_encoding": False}))
    assert out.theme.redundant_encoding is False


def test_set_font_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetFont(params={"colour": "red"}))


def test_set_axes_style_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetAxesStyle(params={"nonsense": 1}))


def test_set_grid_style_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetGridStyle(params={"nonsense": 1}))


def test_set_ticks_style_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetTicksStyle(params={"nonsense": 1}))


def test_set_palette_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        mp.reduce(FigureSpec(), A.SetPalette(params={"nonsense": 1}))
