"""Consistency between the two independently-maintained journal-ish
registries: ``theme.AVAILABLE_JOURNALS``/``journal_overrides`` (a style:
fonts/linewidths/default figure size, applied via ``.journal(name)``) and
``tex.TEX_PRESETS`` (a TeX document class's column geometry, applied via
``.tex_size(name, ...)``/``.preview(tex=name)``).

They're allowed to overlap only partially by design ("article"/"revtex"/
"acm" are generic TeX document classes with no house style), but every
*journal* theme should also have a matching TeX geometry -- otherwise
``.journal("some_journal")`` would produce fonts with no corresponding
``.tex_size("some_journal")`` to actually place the figure at the right
physical size, which defeats the point of naming it after a real journal.
"""

import mudplot as mp
from mudplot.tex import TEX_PRESETS
from mudplot.theme import AVAILABLE_JOURNALS, JOURNAL_SIZES, journal_overrides


def test_every_journal_theme_has_a_matching_tex_preset():
    missing = set(AVAILABLE_JOURNALS) - set(TEX_PRESETS)
    assert not missing, (
        f"journal theme(s) {sorted(missing)} have no matching "
        "mudplot.tex.TEX_PRESETS entry -- .tex_size(name) would fail for a "
        "name .journal(name) accepts"
    )


def test_every_journal_theme_has_a_default_figure_size():
    missing = set(AVAILABLE_JOURNALS) - set(JOURNAL_SIZES)
    assert not missing


def test_journal_profiles_are_exposed_and_match_the_underlying_registries():
    profiles = mp.capabilities()["journal_profiles"]
    assert set(profiles) == set(AVAILABLE_JOURNALS) & set(TEX_PRESETS)
    for name, profile in profiles.items():
        ctx = TEX_PRESETS[name]
        rc = journal_overrides(name)
        assert profile["figure_size_in"] == JOURNAL_SIZES[name]
        assert profile["base_font_pt"] == rc["font.size"]
        assert profile["columnwidth_pt"] == ctx.columnwidth_pt
        assert profile["columns"] == ctx.columns


def test_journal_and_tex_size_compose_to_a_coherent_figure():
    """The actual end-to-end promise: naming the same journal in both
    calls should produce one coherent, correctly-sized, correctly-fonted
    figure -- not two unrelated settings that happen to share a string.
    """
    for name in AVAILABLE_JOURNALS:
        p = (
            mp.plot({"x": [1, 2], "y": [3, 4]})
            .line("x", "y")
            .journal(name)
            .tex_size(name)
        )
        assert mp.validate(p.spec) == []
        fig = mp.render(p.spec)
        import matplotlib.pyplot as plt

        plt.close(fig)
