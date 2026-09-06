"""TeX-aware sizing and WYSIWYG preview.

Papers are written in TeX, so a figure should be judged at the *exact* size
and font it will have in the final document. ``TexContext`` captures a document
class's column/text widths (in TeX points) and body font size; the helpers here
size a spec accordingly and render a preview that places the figure inside a
mock text column with a caption.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import actions as A
from .reducer import reduce_all
from .spec import FigureSpec

__all__ = [
    "PREAMBLE",
    "TEX_PRESETS",
    "TexContext",
    "apply_tex",
    "figsize_for",
    "tex_preview",
]

# Paste into the preamble of the document that \input's a .pgf export.
#
# A PGF figure carrying reference metadata emits \figcite{key} rather than
# \cite{key} directly, so the *document* decides what a figure citation
# means (\cite, \citep, \autocite, a footnote, or nothing at all when the
# figure is reused somewhere without a bibliography).
PREAMBLE = r"""% mudplot: resolve figure citations/links against this document
\providecommand{\figcite}[1]{\cite{#1}}
\usepackage{hyperref}  % only needed if a figure uses href metadata
"""

# LaTeX point: 1 pt = 1/72.27 inch (matplotlib's "point" is 1/72 -> keep this
# conversion explicit and separate).
PT_PER_INCH = 72.27
MM_PER_INCH = 25.4


@dataclass(frozen=True)
class TexContext:
    """Geometry of a target TeX document."""

    name: str
    columnwidth_pt: float  # \the\columnwidth
    textwidth_pt: float  # \the\textwidth
    fontsize_pt: float = 10.0  # document body font size
    columns: int = 1
    family: str = "serif"


def _mm(pt_mm: float) -> float:
    return pt_mm / MM_PER_INCH * PT_PER_INCH  # mm -> pt


# Common document classes. Widths are typical defaults; users can override.
TEX_PRESETS: dict[str, TexContext] = {
    # article, 10pt, default geometry (~345pt text width, single column)
    "article": TexContext("article", 345.0, 345.0, 10.0, columns=1),
    # IEEEtran two-column
    "ieee": TexContext("ieee", 252.0, 516.0, 10.0, columns=2),
    # REVTeX 4 (aps) two-column
    "revtex": TexContext("revtex", 246.0, 510.0, 10.0, columns=2),
    # Nature: single column 88 mm, double column 180 mm
    "nature": TexContext(
        "nature", _mm(88.0), _mm(180.0), 7.0, columns=2, family="sans-serif"
    ),
    # ACM sigconf-ish
    "acm": TexContext("acm", 241.0, 506.0, 9.0, columns=2),
}


def figsize_for(
    ctx: TexContext,
    fraction: float = 1.0,
    aspect: float = 0.618,
    *,
    full_width: bool = False,
) -> list[float]:
    """Figure size in inches for a given TeX context.

    ``fraction`` scales the column (or text) width; ``aspect`` = height/width
    (default golden ratio). Set ``full_width`` to span the full text width
    (e.g. a double-column figure).
    """
    base_pt = ctx.textwidth_pt if full_width else ctx.columnwidth_pt
    w = fraction * base_pt / PT_PER_INCH
    return [w, w * aspect]


def _tex_actions(
    ctx: TexContext,
    *,
    fraction: float = 1.0,
    aspect: float = 0.618,
    full_width: bool = False,
    font_scale: float = 0.9,
) -> list[A.Action]:
    """The SetSize/SetFont actions that size a spec to ``ctx``.

    Shared by :func:`apply_tex` (pure, spec -> spec) and
    ``Plot.tex_size()`` (dispatches through the Store, so it participates
    in the fluent API's action_log/undo like every other builder method).
    """
    w, h = figsize_for(ctx, fraction, aspect, full_width=full_width)
    body = ctx.fontsize_pt * font_scale
    return [
        A.SetSize(w, h),
        A.SetFont(
            params={
                "family": ctx.family,
                "size": body,
                "label_size": body,
                "title_size": body + 1,
                "tick_size": body - 1,
            }
        ),
    ]


def apply_tex(
    spec: FigureSpec,
    ctx: TexContext,
    *,
    fraction: float = 1.0,
    aspect: float = 0.618,
    full_width: bool = False,
    font_scale: float = 0.9,
) -> FigureSpec:
    """Return a new spec sized to ``ctx`` with document-matching fonts.

    Pure: dispatches sizing/font actions through the reducer.
    """
    actions = _tex_actions(
        ctx,
        fraction=fraction,
        aspect=aspect,
        full_width=full_width,
        font_scale=font_scale,
    )
    return reduce_all(spec, actions)


def _resolve_ctx(tex) -> TexContext:
    if isinstance(tex, TexContext):
        return tex
    if isinstance(tex, str):
        if tex not in TEX_PRESETS:
            raise ValueError(
                f"unknown TeX preset {tex!r}; choose from {list(TEX_PRESETS)}"
            )
        return TEX_PRESETS[tex]
    raise TypeError("tex must be a preset name or a TexContext")


def tex_preview(
    spec: FigureSpec,
    tex=None,
    *,
    fraction: float = 1.0,
    aspect: float = 0.618,
    full_width: bool = False,
    caption: str = "Figure 1. Caption text goes here.",
    show_context: bool = True,
):
    """Render a WYSIWYG preview of ``spec`` as it would appear in a TeX column.

    If ``tex`` is None, just renders the spec at its own size. Otherwise the
    figure is sized to the TeX context and (when ``show_context``) embedded in
    a mock text column with placeholder body text and the caption.

    Returns the preview matplotlib Figure.
    """
    import io as _io

    import matplotlib.pyplot as plt

    from ._render import render

    if tex is None:
        return render(spec)

    ctx = _resolve_ctx(tex)
    sized = apply_tex(
        spec, ctx, fraction=fraction, aspect=aspect, full_width=full_width
    )

    # Render the actual figure to an image buffer at its true size.
    fig = render(sized)
    if not show_context:
        return fig
    try:
        with _io.BytesIO() as buf, plt.rc_context({"savefig.bbox": None}):
            fig.savefig(buf, format="png", dpi=sized.dpi, bbox_inches=None)
            buf.seek(0)
            img = plt.imread(buf)
    finally:
        plt.close(fig)

    # Build the mock column: column width in inches + side margins.
    col_w = (ctx.textwidth_pt if full_width else ctx.columnwidth_pt) / PT_PER_INCH
    margin = 0.18 * col_w
    page_w = col_w + 2 * margin

    # BUG (fixed): this used to be re-derived as
    # ``fraction * col_w * (textwidth_pt / columnwidth_pt if full_width else 1)``,
    # which only matched the actual rendered width in the (default)
    # column-width case; for ``full_width=True`` it introduced an extra,
    # spurious ``textwidth/columnwidth`` factor that inflated the figure
    # (and the whole mock page) to roughly double its true size, breaking
    # the WYSIWYG guarantee. ``sized.size[0]`` is already the exact
    # rendered width in inches, so just use that directly.
    fig_w = sized.size[0]
    img_h_per_w = img.shape[0] / img.shape[1]
    fig_h = fig_w * img_h_per_w

    line_h = ctx.fontsize_pt / PT_PER_INCH * 1.6  # body line spacing
    n_top, n_bot = 4, 6
    cap_lines = 2
    total_h = (
        margin
        + n_top * line_h
        + 0.10 * col_w
        + fig_h
        + 0.06 * col_w
        + cap_lines * line_h
        + 0.10 * col_w
        + n_bot * line_h
        + margin
    )

    out, ax = plt.subplots(figsize=(page_w, total_h), dpi=150)
    # Data coordinates are inches; default subplot margins would shrink
    # the entire preview (including the supposedly true-size figure).
    out.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, page_w)
    ax.set_ylim(0, total_h)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.axis("off")
    # page background
    ax.add_patch(
        plt.Rectangle(
            (0, 0), page_w, total_h, facecolor="white", edgecolor="#cccccc", lw=1
        )
    )

    def body_lines(y, n, indent_last=False):
        for i in range(n):
            w = col_w * (0.55 if (indent_last and i == n - 1) else 1.0)
            ax.add_patch(
                plt.Rectangle(
                    (margin, y), w, line_h * 0.35, facecolor="#d9d9d9", edgecolor="none"
                )
            )
            y += line_h
        return y

    y = margin
    y = body_lines(y, n_top, indent_last=True)
    y += 0.10 * col_w

    # figure image, centred in the column
    x0 = margin + (col_w - fig_w) / 2
    ax.imshow(img, extent=(x0, x0 + fig_w, y + fig_h, y), aspect="auto", zorder=3)
    y += fig_h + 0.06 * col_w

    # caption text at document font size
    ax.text(
        margin,
        y,
        caption,
        ha="left",
        va="top",
        fontsize=ctx.fontsize_pt,
        family=ctx.family,
        wrap=True,
        color="#222222",
    )
    y += cap_lines * line_h + 0.10 * col_w
    body_lines(y, n_bot)

    ax.set_title(
        f"TeX preview — {ctx.name}  "
        f"(col {ctx.columnwidth_pt:.0f}pt, {ctx.fontsize_pt:.0f}pt, "
        f"frac {fraction:g})",
        fontsize=9,
        y=0.98,
        va="top",
    )
    return out
