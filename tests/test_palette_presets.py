"""Verifies the named palette presets and greyscale-safe fills.

Locks in the actual measured claim ("safe up to max_verified_n"), not an
assumption, and checks that bar/box/violin fills stay distinguishable in
black & white print via hatch patterns, independent of palette size.
"""

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import pytest
from mudplot.capabilities import PALETTE_PRESETS
from mudplot.color import palette as P


@pytest.mark.parametrize("name", sorted(PALETTE_PRESETS))
def test_preset_is_measured_safe_up_to_its_claimed_n(name):
    max_n = PALETTE_PRESETS[name]["max_verified_n"]
    for n in range(2, max_n + 1):
        pal = P.preset_qualitative(name, n)
        report = pal.report()
        assert report["cvd_safe"], f"{name} n={n} not CVD-safe: {report}"
        assert report["grayscale_safe"], f"{name} n={n} not greyscale-safe: {report}"


def test_unknown_preset_name_raises():
    with pytest.raises(ValueError, match="unknown palette preset"):
        P.preset_qualitative("does-not-exist", 3)


def test_color_palette_top_level_helper_supports_preset():
    pal = mp.color_palette(6, "qualitative", preset="paper")
    assert pal.hex == P.preset_qualitative("paper", 6).hex
    with pytest.raises(ValueError, match="only supported for kind='qualitative'"):
        mp.color_palette(5, "sequential", preset="paper")


def test_preset_overrides_individual_palette_fields():
    p = mp.plot({"x": [1], "y": [2], "g": ["a"]}).line("x", "y", group="g")
    p = p.palette(preset="vivid", hue_start=999, lightness=1)  # ignored: not
    # a preset_qualitative() kwarg -- SetPalette params must be valid
    # PaletteSpec fields regardless, so this exercises the same path a real
    # `.palette(preset="vivid")` call would.
    assert p.spec.theme.palette.preset == "vivid"
    fig = p.render()
    assert mp.validate(p.spec) == []
    assert fig.axes[0].lines


def test_unknown_preset_caught_by_validate_before_render():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y").palette(preset="nope")
    issues = mp.validate(p.spec)
    assert any("unknown palette preset" in i for i in issues)
    with pytest.raises(ValueError, match="invalid FigureSpec"):
        p.render()


def test_capabilities_and_docs_expose_presets_consistently():
    caps = mp.capabilities()
    assert set(caps["palette_presets"]) == set(PALETTE_PRESETS)
    for name, meta in PALETTE_PRESETS.items():
        assert caps["palette_presets"][name] == meta
    assert "paper" in mp.reference_markdown()


def test_grouped_bar_hatches_differ_per_series_regardless_of_palette_size():
    data = {
        "cat": ["A", "B"] * 3,
        "value": [1, 2, 3, 4, 5, 6],
        "g": ["x"] * 2 + ["y"] * 2 + ["z"] * 2,
    }
    p = mp.plot(data).bar("cat", "value", group="g")
    fig = p.render()
    hatches = {patch.get_hatch() for patch in fig.axes[0].patches}
    assert len(hatches) == 3


def test_grouped_box_and_violin_hatches_differ_per_series():
    data = {"value": [1, 2, 3, 4, 5, 6], "g": ["a", "a", "b", "b", "c", "c"]}
    box = mp.plot(data).box("value", group="g").render()
    box_hatches = {patch.get_hatch() for patch in box.axes[0].patches}
    assert len(box_hatches) == 3

    violin = mp.plot(data).violin("value", group="g").render()
    # violinplot() draws several collections (bodies + median/min/max bars);
    # only the body polygons carry the fill hatch.
    bodies = [c for c in violin.axes[0].collections if c.get_facecolor().size]
    body_hatches = {body.get_hatch() for body in bodies}
    assert len(body_hatches) == 3


def test_ungrouped_bar_box_violin_get_no_hatch():
    data = {"cat": ["A", "B"], "value": [1, 2]}
    bar = mp.plot(data).bar("cat", "value").render()
    assert all(p.get_hatch() is None for p in bar.axes[0].patches)

    dist = {"value": [1, 2, 3]}
    box = mp.plot(dist).box("value").render()
    assert all(p.get_hatch() is None for p in box.axes[0].patches)


def test_encoding_disabled_removes_hatches_too():
    data = {"cat": ["A", "B"] * 2, "value": [1, 2, 3, 4], "g": ["x", "x", "y", "y"]}
    p = mp.plot(data).bar("cat", "value", group="g").encoding(redundant_encoding=False)
    fig = p.render()
    assert all(patch.get_hatch() is None for patch in fig.axes[0].patches)


def test_empty_hatches_or_encoding_fields_caught_by_validate():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    p.dispatch(mp.actions.SetEncoding(params={"hatches": []}))
    assert any("hatches" in i for i in mp.validate(p.spec))
