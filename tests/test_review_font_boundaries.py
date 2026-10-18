"""LAY-04/07: observe real font availability/glyph diagnostics, don't ship fonts."""

import hashlib
import json
import logging
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib import font_manager, ft2font

CJK_FAMILIES = ("Noto Sans KR", "Malgun Gothic")


def available(name):
    try:
        return Path(
            font_manager.findfont(
                font_manager.FontProperties(family=[name]), fallback_to_default=False
            )
        )
    except ValueError:
        return None


def base(family, title="한글 제목 \N{MINUS SIGN} Ω $x_1$"):
    return (
        mp.plot({"x": [-1, 0, 1], "y": [1, 2, 3]})
        .line("x", "y", label="그룹 Ω")
        .font(family=family)
        .labels(title=title, x="가로축 \N{MINUS SIGN}", y="세로축 Ω")
        .size(5, 3)
    )


def test_missing_family_fallback_is_logged_and_does_not_rewrite_spec(caplog):
    family = "mudplot-font-not-installed-23913"
    with pytest.raises(ValueError):
        font_manager.findfont(
            font_manager.FontProperties(family=[family]), fallback_to_default=False
        )
    p = base(family, "missing-family ASCII \N{MINUS SIGN} Ω")
    before = p.to_json()
    with caplog.at_level(logging.WARNING, logger="matplotlib"):
        resolved = font_manager.findfont(font_manager.FontProperties(family=[family]))
        fig = p.render()
    try:
        assert Path(resolved).is_file()
        assert any(
            family in record.getMessage() and "not found" in record.getMessage()
            for record in caplog.records
        )
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_missing_hangul_glyphs_are_detectable_in_bundled_font(caplog):
    family = "DejaVu Sans"
    path = available(family)
    assert path is not None
    face = ft2font.FT2Font(str(path))
    assert not face.get_char_index(ord("한"))
    with (
        caplog.at_level(logging.WARNING, logger="matplotlib"),
        warnings.catch_warnings(record=True) as caught,
    ):
        warnings.simplefilter("always")
        fig = base(family).render()
    try:
        messages = [str(w.message) for w in caught] + [
            record.getMessage() for record in caplog.records
        ]
        assert any(
            ("Glyph" in m and "missing" in m) or "does not have a glyph" in m
            for m in messages
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("family", CJK_FAMILIES)
def test_installed_cjk_font_records_coverage_bbox_and_detectable_missing_symbols(
    family, request, caplog
):
    path = available(family)
    if path is None:
        pytest.skip(f"system font {family} is not installed; no font download")
    face = ft2font.FT2Font(str(path))
    chars = {c: face.get_char_index(ord(c)) for c in "한글제목\N{MINUS SIGN}Ω"}
    assert chars["한"] and chars["글"]
    p = base(family)
    before = p.to_json()
    with (
        caplog.at_level(logging.WARNING, logger="matplotlib"),
        warnings.catch_warnings(record=True) as caught,
    ):
        warnings.simplefilter("always")
        fig = p.render()
    try:
        bb = (
            fig.axes[0]
            .title.get_window_extent()
            .transformed(fig.transFigure.inverted())
        )
        messages = sorted(
            set(
                [str(w.message) for w in caught]
                + [record.getMessage() for record in caplog.records]
            )
        )
        if not chars["\N{MINUS SIGN}"]:
            assert any("8722" in m or "2212" in m for m in messages)
        assert (
            p.to_json() == before
            and bb.x0 >= -0.001
            and bb.x1 <= 1.001
            and bb.y1 <= 1.001
        )
        request.node.user_properties.append(
            (
                "font_observation",
                json.dumps(
                    {
                        "family": family,
                        "font_file": path.name,
                        "font_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "coverage_char_indices": chars,
                        "title_bbox": [float(v) for v in bb.extents],
                        "messages": messages,
                    }
                ),
            )
        )
    finally:
        plt.close(fig)


def test_available_cjk_title_and_long_group_stay_inside_or_warn_actionably():
    family = next((name for name in CJK_FAMILIES if available(name) is not None), None)
    if family is None:
        pytest.skip("no selected system CJK family; missing-glyph path is separate")
    p = (
        mp.plot(
            {
                "x": [1, 2, 3, 4],
                "y": [2, 3, 2, 4],
                "g": ["매우 긴 그룹 이름 with words"] * 2
                + ["another long group name"] * 2,
            }
        )
        .line("x", "y", group="g")
        .labels(title="한글 제목과 여러 단어를 함께 보여주는 좁은 그림")
        .font(family=family)
        .size(3.4, 2.2)
        .legend(location="outside right")
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = p.render()
    try:
        artists = [fig.axes[0].title, fig.axes[0].get_legend()]
        boxes = [
            artist.get_window_extent().transformed(fig.transFigure.inverted())
            for artist in artists
        ]
        inside = all(
            b.x0 >= -0.001 and b.x1 <= 1.001 and b.y0 >= -0.001 and b.y1 <= 1.001
            for b in boxes
        )
        assert inside or any("fixed canvas" in str(w.message) for w in caught)
        assert fig.get_size_inches() == pytest.approx([3.4, 2.2])
    finally:
        plt.close(fig)
