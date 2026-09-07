"""Theme presets and translation from ThemeSpec -> matplotlib rcParams.

The intuitive, grouped ``ThemeSpec`` (see ``mudplot.spec``) is the user-facing
model. This module owns the *only* place where those human-named options are
turned into matplotlib's flat ``rcParams`` dotted keys, keeping that
non-intuitive layer contained.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .spec import (
    AxesSpec,
    FontSpec,
    GridSpec,
    PaletteSpec,
    ThemeSpec,
    TicksSpec,
)

__all__ = [
    "AVAILABLE_JOURNALS",
    "AVAILABLE_THEMES",
    "JOURNAL_PROFILES",
    "JOURNAL_SIZES",
    "JournalProfile",
    "get_journal_profile",
    "journal_overrides",
    "spec_to_rcparams",
    "theme_preset",
]


# --------------------------------------------------------------------------
# Named presets  -> ThemeSpec
# --------------------------------------------------------------------------
def theme_preset(name: str) -> ThemeSpec:
    """Return a ThemeSpec for a named preset."""
    if name == "paper":
        return ThemeSpec(name="paper")
    if name == "paper-grid":
        t = ThemeSpec(name="paper-grid")
        t.grid.show = True
        return t
    if name == "minimal":
        t = ThemeSpec(name="minimal")
        t.axes.spines = "LB"
        t.ticks.direction = "out"
        return t
    if name == "boxed":
        t = ThemeSpec(name="boxed")
        t.axes.spines = "LRTB"
        t.ticks.direction = "in"
        t.ticks.top = True
        t.ticks.right = True
        return t
    raise ValueError(f"unknown theme preset: {name!r}")


AVAILABLE_THEMES = ("paper", "paper-grid", "minimal", "boxed")


# --------------------------------------------------------------------------
# Publication constraint profiles (P2-3)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class JournalProfile:
    """Publication-constraint and style profile for a journal.

    Pairs a style (fonts, linewidths, default figure size) with target TeX
    geometry (column/text widths) and publication preflight rules (minimum
    font size, recommended raster DPI, grayscale policy) into one coherent
    profile.
    """

    name: str
    columnwidth_pt: float
    textwidth_pt: float
    columns: int = 2
    font_family: str = "serif"
    base_font_pt: float = 8.0
    tick_font_pt: float = 7.0
    min_font_pt: float = 6.0
    line_width_pt: float = 0.5
    figure_size_in: list[float] = field(default_factory=lambda: [3.3, 2.5])
    recommended_dpi: int = 300
    max_legend_entries: int = 8
    grayscale_policy: str = "redundant"

    def to_dict(self) -> dict:
        return {
            "figure_size_in": list(self.figure_size_in),
            "base_font_pt": self.base_font_pt,
            "tick_font_pt": self.tick_font_pt,
            "min_font_pt": self.min_font_pt,
            "line_width_pt": self.line_width_pt,
            "columnwidth_pt": self.columnwidth_pt,
            "textwidth_pt": self.textwidth_pt,
            "columns": self.columns,
            "font_family": self.font_family,
            "recommended_dpi": self.recommended_dpi,
            "max_legend_entries": self.max_legend_entries,
            "grayscale_policy": self.grayscale_policy,
        }


JOURNAL_PROFILES: dict[str, JournalProfile] = {
    "nature": JournalProfile(
        name="nature",
        columnwidth_pt=250.38425196850392,  # 88 mm
        textwidth_pt=512.1496062992127,  # 180 mm
        columns=2,
        font_family="sans-serif",
        base_font_pt=7.0,
        tick_font_pt=6.0,
        min_font_pt=5.0,
        line_width_pt=0.5,
        figure_size_in=[3.5, 2.625],
        recommended_dpi=300,
        max_legend_entries=8,
        grayscale_policy="redundant",
    ),
    "ieee": JournalProfile(
        name="ieee",
        columnwidth_pt=252.0,
        textwidth_pt=516.0,
        columns=2,
        font_family="serif",
        base_font_pt=8.0,
        tick_font_pt=7.0,
        min_font_pt=6.0,
        line_width_pt=0.5,
        figure_size_in=[3.3, 2.5],
        recommended_dpi=300,
        max_legend_entries=8,
        grayscale_policy="redundant",
    ),
    "acm": JournalProfile(
        name="acm",
        columnwidth_pt=241.0,
        textwidth_pt=506.0,
        columns=2,
        font_family="serif",
        base_font_pt=9.0,
        tick_font_pt=8.0,
        min_font_pt=6.0,
        line_width_pt=0.5,
        figure_size_in=[3.33, 2.5],
        recommended_dpi=300,
        max_legend_entries=8,
        grayscale_policy="redundant",
    ),
    "revtex": JournalProfile(
        name="revtex",
        columnwidth_pt=246.0,
        textwidth_pt=510.0,
        columns=2,
        font_family="serif",
        base_font_pt=8.0,
        tick_font_pt=7.0,
        min_font_pt=6.0,
        line_width_pt=0.5,
        figure_size_in=[3.4, 2.5],
        recommended_dpi=300,
        max_legend_entries=8,
        grayscale_policy="redundant",
    ),
}


def get_journal_profile(name: str | JournalProfile) -> JournalProfile:
    """Return the :class:`JournalProfile` for a named journal preset."""
    if isinstance(name, JournalProfile):
        return name
    if not isinstance(name, str):
        raise TypeError(
            f"journal must be a name or JournalProfile, got {type(name).__name__}"
        )
    prof = JOURNAL_PROFILES.get(name.lower())
    if prof is None:
        raise ValueError(
            f"unknown journal profile {name!r}; choose from {sorted(JOURNAL_PROFILES)}"
        )
    return prof


AVAILABLE_JOURNALS = tuple(JOURNAL_PROFILES)

# Default figure size (inches) per journal. Applied to the *spec* itself
# (by the ``SetJournal`` reducer case), not via rcParams — see the note on
# ``journal_overrides`` above for why.
JOURNAL_SIZES: dict[str, list[float]] = {
    name: prof.figure_size_in for name, prof in JOURNAL_PROFILES.items()
}


# --------------------------------------------------------------------------
# Journal overrides (applied on top of a theme's rcParams)
# --------------------------------------------------------------------------
def journal_overrides(journal: str | None) -> dict:
    """rcParams overrides for a journal preset (fonts/linewidths only).

    Figure *size* is intentionally **not** an rcParam here: ``render()``
    always passes ``figsize=`` explicitly to ``plt.subplots()``, which would
    silently shadow a rcParams-only size override. See ``JOURNAL_SIZES`` /
    ``mudplot.actions.SetJournal`` for how the default size is actually
    applied (through the spec, not rcParams).

    This registry (a *style*: fonts/linewidths/default figure size, applied
    via ``.journal(name)``) is unified with ``mudplot.tex.TEX_PRESETS`` (a
    TeX document class's *column geometry*, applied via
    ``.tex_size(name, ...)``/``.preview(tex=name)``) via
    ``JOURNAL_PROFILES``. See ``mudplot.capabilities()["journal_profiles"]``
    for the machine-readable summary.
    """
    if journal is None:
        return {}
    j = journal.lower()
    if j == "nature":
        return {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7,
            "axes.labelsize": 7,
            "axes.titlesize": 8,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "axes.linewidth": 0.5,
        }
    if j == "ieee":
        return {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.5,
        }
    if j == "acm":
        return {
            "font.family": "serif",
            "font.serif": ["Linux Libertine", "Times New Roman", "DejaVu Serif"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.linewidth": 0.5,
        }
    if j == "revtex":
        return {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.5,
        }
    raise ValueError(f"unknown journal preset: {journal!r}")


# --------------------------------------------------------------------------
# ThemeSpec -> rcParams
# --------------------------------------------------------------------------
def _font_rc(f: FontSpec) -> dict:
    rc = {
        "font.family": f.family,
        "font.size": f.size,
        "axes.titlesize": f.title_size,
        "axes.labelsize": f.label_size,
        "xtick.labelsize": f.tick_size,
        "ytick.labelsize": f.tick_size,
        "legend.fontsize": f.tick_size,
        "text.usetex": f.use_tex,
    }
    return rc


def _axes_rc(a: AxesSpec) -> dict:
    return {
        "axes.linewidth": a.line_width,
        "axes.spines.left": "L" in a.spines,
        "axes.spines.right": "R" in a.spines,
        "axes.spines.top": "T" in a.spines,
        "axes.spines.bottom": "B" in a.spines,
    }


def _grid_rc(g: GridSpec) -> dict:
    return {
        "axes.grid": g.show,
        "axes.grid.axis": g.axis,
        "grid.linewidth": g.line_width,
        "grid.alpha": g.alpha,
    }


def _ticks_rc(t: TicksSpec) -> dict:
    return {
        "xtick.direction": t.direction,
        "ytick.direction": t.direction,
        "xtick.major.size": t.major_size,
        "ytick.major.size": t.major_size,
        "xtick.minor.size": t.minor_size,
        "ytick.minor.size": t.minor_size,
        "xtick.major.width": t.width,
        "ytick.major.width": t.width,
        "xtick.minor.visible": t.minor_visible,
        "ytick.minor.visible": t.minor_visible,
        "xtick.top": t.top,
        "ytick.right": t.right,
    }


def _palette_rc(p: PaletteSpec, n: int = 10) -> dict:
    from cycler import cycler

    from .color import palette as P

    if p.kind == "qualitative":
        if p.preset is not None:
            pal = P.preset_qualitative(p.preset, max(n, 1), cvd_safe=p.cvd_safe)
        else:
            pal = P.qualitative(
                max(n, 1),
                lightness=p.lightness,
                chroma=p.chroma,
                hue_start=p.hue_start,
                cvd_safe=p.cvd_safe,
            )
    elif p.kind == "sequential":
        pal = P.sequential(max(n, 2))
    elif p.kind == "diverging":
        pal = P.diverging(max(n, 2))
    else:
        raise ValueError(f"unknown palette kind: {p.kind!r}")
    return {"axes.prop_cycle": cycler("color", list(pal.hex))}


def spec_to_rcparams(
    theme: ThemeSpec, journal: str | None = None, n_colors: int = 10
) -> dict:
    """Flatten a ThemeSpec (+ optional journal) into matplotlib rcParams."""
    rc: dict = {
        "legend.frameon": False,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    }
    rc.update(_font_rc(theme.font))
    rc.update(_axes_rc(theme.axes))
    rc.update(_grid_rc(theme.grid))
    rc.update(_ticks_rc(theme.ticks))
    rc.update(_palette_rc(theme.palette, n=n_colors))
    rc.update(journal_overrides(journal))
    return rc
