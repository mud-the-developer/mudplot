"""Regression tests for bugs found during the stability/hardening audit.

Each test documents the bug it guards against so a future refactor can't
silently reintroduce it.
"""

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.data import to_columns
from mudplot.render import render
from mudplot.theme import JOURNAL_SIZES


def test_journal_actually_changes_figure_size():
    # BUG: .journal("ieee") documented a 3.3x2.5in default but render()
    # always passed spec.size explicitly to plt.subplots(), silently
    # shadowing the rcParams-only "figure.figsize" override -> the journal
    # preset never visibly took effect.
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").journal("ieee")
    assert p.spec.size == JOURNAL_SIZES["ieee"]
    fig = render(p.spec)
    w, h = fig.get_size_inches()
    assert (round(float(w), 2), round(float(h), 2)) == tuple(JOURNAL_SIZES["ieee"])


def test_journal_nature_size():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").journal("nature")
    assert p.spec.size == JOURNAL_SIZES["nature"]


def test_journal_none_does_not_reset_size():
    # clearing the journal shouldn't silently snap back to some other size
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4]})
        .line("x", "y")
        .journal("ieee")
        .size(5.0, 4.0)
        .journal(None)
    )
    assert p.spec.size == [5.0, 4.0]


def test_panel_label_uses_journal_overridden_title_size():
    # BUG: the panel "a)" / "b)" auto-label used spec.theme.font.title_size
    # directly, ignoring the journal's rcParams override of axes.titlesize,
    # so labels and titles could show mismatched font sizes.
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4]})
        .line("x", "y")
        .labels(title="t")
        .auto_label(True)
        .journal("nature")
    )
    fig = render(p.spec)
    ax = fig.axes[0]
    label_text = next(t for t in ax.texts if t.get_text() == "a)")
    assert label_text.get_fontsize() == fig.axes[0].title.get_fontsize()


def test_set_data_does_not_wipe_previously_registered_matrices():
    # BUG: the SetData reducer case replaced ``s.data`` with a brand new
    # DataSpec(columns=...), silently discarding any matrices already
    # registered via SetMatrix (e.g. .matrix("m", ...) called before a
    # later data refresh).
    p = mp.plot({}).matrix("m", [[1, 2], [3, 4]])
    assert p.spec.data.matrices == {"m": [[1, 2], [3, 4]]}
    p.dispatch(A.SetData({"x": [1, 2, 3]}))
    assert p.spec.data.matrices == {"m": [[1, 2], [3, 4]]}
    assert p.spec.data.columns == {"x": [1, 2, 3]}


def test_set_data_replaces_columns_wholesale():
    # SetData should still fully replace *columns* (not merge old + new).
    p = mp.plot({"a": [1, 2]})
    p.dispatch(A.SetData({"b": [3, 4]}))
    assert p.spec.data.columns == {"b": [3, 4]}


def test_flat_string_list_does_not_shred_into_characters():
    # BUG: a flat list of strings has __len__ per-element (like a numeric
    # "row" would), so it was being misdetected as rows-of-sequences and
    # shredded into one column *per character* instead of raising the same
    # "ambiguous flat list" error a flat list of numbers already gave.
    with pytest.raises(TypeError, match="flat list"):
        to_columns(["apple", "banana", "cherry"])


def test_flat_numeric_list_still_raises_consistently():
    with pytest.raises(TypeError, match="flat list"):
        to_columns([1, 2, 3])


def test_rows_of_tuples_with_strings_still_work():
    # regression guard: fixing the string case must not break legitimate
    # rows that merely *contain* strings alongside other values.
    assert to_columns([("apple", 1), ("banana", 2)]) == {
        "c0": ["apple", "banana"],
        "c1": [1, 2],
    }


def test_tex_preview_full_width_matches_true_rendered_size():
    # BUG: the full_width=True mock-page preview recomputed the embedded
    # figure's width as
    #   fraction * col_w * (textwidth_pt / columnwidth_pt)
    # instead of using the actual rendered size, introducing a spurious
    # extra textwidth/columnwidth factor that roughly doubled the figure
    # (and the whole mock page) versus what render() actually produces.
    from mudplot.tex import TEX_PRESETS, apply_tex

    p = mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]}).line("x", "y")
    ctx = TEX_PRESETS["ieee"]
    true_size = apply_tex(p.spec, ctx, full_width=True).size

    fig = p.preview(tex="ieee", fraction=1.0, full_width=True)
    col_w = ctx.textwidth_pt / 72.27
    margin = 0.18 * col_w
    expected_page_w = col_w + 2 * margin

    page_w, _page_h = fig.get_size_inches()
    assert page_w == pytest.approx(expected_page_w, rel=1e-6)
    # the embedded figure must not be wider than the true rendered width
    # would allow inside the mock column (with the old bug it was ~2x over)
    assert true_size[0] < expected_page_w * 1.1


def test_hline_vline_respect_secondary_axis():
    # BUG: hline/vline/text/annotate always drew on the primary axis,
    # silently ignoring an explicit axis="y2" -- unlike every other layer
    # type, which already routed correctly via _target_axes.
    data = {"x": [1, 2, 3], "y": [1, 4, 9], "y2col": [10, 40, 90]}
    p = (
        mp.plot(data)
        .secondary_yaxis("Y2")
        .line("x", "y")
        .line("x", "y2col", axis="y2")
        .hline(50, axis="y2")
        .vline(2, axis="y2")
    )
    fig = render(p.spec)
    ax, ax2 = fig.axes[0], fig.axes[1]
    assert any(abs(ln.get_ydata()[0] - 50) < 1e-9 for ln in ax2.lines)
    assert not any(abs(ln.get_ydata()[0] - 50) < 1e-9 for ln in ax.lines)


def test_hline_on_primary_axis_by_default():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").hline(3.5)
    fig = render(p.spec)
    assert len(fig.axes) == 1
    assert any(abs(ln.get_ydata()[0] - 3.5) < 1e-9 for ln in fig.axes[0].lines)


def test_heatmap_with_y2_axis_is_rejected_by_validate():
    # heatmap (and hist/box) don't actually support secondary-axis routing
    # in the renderer, so silently accepting axis="y2" on them would be a
    # different flavour of the same bug -- validate() should say so clearly.
    p = mp.plot({}).matrix("m", [[1, 2], [3, 4]]).heatmap("m", axis="y2")
    issues = mp.validate(p.spec)
    assert any("not supported for 'heatmap'" in i for i in issues)


def test_qualitative_palette_min_delta_e_is_fast_for_moderate_n():
    # BUG: _min_pairwise_worstcase used a pure-Python O(n^2) double loop
    # (one delta_e2000 call per pair, per vision condition) to compute the
    # palette's own reported min_delta_e -- for n=1000 this took well over
    # a minute. It's now fully vectorised.
    import time

    from mudplot.color import palette as P

    start = time.monotonic()
    pal = P.qualitative(30)
    elapsed = time.monotonic() - start
    assert elapsed < 5.0, f"qualitative(30) took {elapsed:.1f}s -- expected < 5s"
    assert pal.min_delta_e() > 0


def test_qualitative_n_exceeding_candidates_raises_instead_of_duplicating():
    # BUG: requesting more colours than n_candidates made farthest-point
    # sampling silently repeat already-picked indices once it ran out of
    # distinct candidates, returning a palette with duplicate colours
    # instead of failing loudly.
    from mudplot.color import palette as P

    with pytest.raises(ValueError, match="exceeds n_candidates"):
        P.qualitative(1000, n_candidates=720)


def test_qualitative_at_exactly_n_candidates_has_no_duplicates():
    from mudplot.color import palette as P

    pal = P.qualitative(50, n_candidates=100)
    assert len(set(pal.hex)) == len(pal.hex)


def test_store_does_not_alias_the_passed_in_spec():
    # BUG: Store(spec) kept a direct reference to the caller's FigureSpec
    # instead of defensively copying it, so mutating the original object
    # after construction (even before any dispatch()) silently leaked into
    # store.state -- breaking the "no hidden mutable state" guarantee.
    from mudplot.store import Store

    spec = mp.FigureSpec()
    store = Store(spec)
    spec.suptitle = "externally mutated"
    assert store.state.suptitle == ""


def test_store_undo_replay_unaffected_by_external_mutation():
    from mudplot import actions as A
    from mudplot.store import Store

    spec = mp.FigureSpec()
    store = Store(spec)
    store.dispatch(A.SetTitle("first"))
    spec.panels[0].title = "tampered"  # mutate the original after construction
    store.undo()
    # replay must be based on the store's own defensive copy, not the
    # (now-tampered) external object
    assert store.state.panels[0].title == ""


def test_remove_layer_removes_the_correct_one():
    # completeness gap: layers could be added but not removed, which is an
    # asymmetry an interactive editor (or an agent correcting a mistake)
    # would hit immediately.
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4]})
        .line("x", "y")
        .scatter("x", "y")
        .bar("x", "y")
    )
    p.remove_layer(1)
    assert [ly.type for ly in p.spec.panels[0].layers] == ["line", "bar"]


def test_remove_layer_out_of_range_raises_clearly():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    with pytest.raises(ValueError, match="out of range"):
        mp.reduce(p.spec, A.RemoveLayer(layer_index=5))


def test_cli_gives_clean_error_not_traceback_for_missing_file(tmp_path):
    # BUG: the CLI let FileNotFoundError / JSONDecodeError / etc. propagate
    # as raw Python tracebacks instead of a clean stderr message + exit
    # code 1, which is much harder for shell scripts/agents to parse.
    import subprocess
    import sys as _sys

    missing = tmp_path / "does_not_exist.json"
    result = subprocess.run(
        [_sys.executable, "-m", "mudplot", "validate", str(missing)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "error:" in result.stderr


def test_lazy_render_attribute_survives_repeated_access():
    # BUG: mudplot's lazy `__getattr__` (PEP 562) resolved `mp.render` via
    # importlib.import_module("mudplot.render"), but importing a submodule
    # has the side effect of binding it onto the parent package's namespace
    # under its own name -- i.e. it set mudplot.render = <submodule>
    # directly in mudplot.__dict__, silently shadowing the *function* we'd
    # just resolved. The first mp.render(...) call worked (it used the
    # freshly-resolved function directly), but every subsequent access
    # found the submodule sitting in __dict__ instead of the function,
    # failing with "'module' object is not callable". This also affected
    # `mp.save` (backed by the same submodule) in either access order.
    import subprocess
    import sys

    # A fresh subprocess is required: within this test session mudplot is
    # already imported and its lazy attributes may already be resolved by
    # earlier tests, which would make an in-process repro order-dependent.
    script = (
        "import mudplot as mp\n"
        "import matplotlib; matplotlib.use('Agg')\n"
        "p = mp.plot({'x':[1,2],'y':[3,4]}).line('x','y')\n"
        "mp.render(p.spec)\n"  # first access -- always worked
        "mp.render(p.spec)\n"  # second access -- used to break
        "mp.save(p.spec, '/tmp/_mudplot_lazy_test.png')\n"
        "mp.render(p.spec)\n"  # after save() -- also used to break
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def test_lazy_attributes_stay_functions_regardless_of_access_order():
    import subprocess
    import sys

    orders = [
        "render,render,render",
        "save,render,save,render",
        "tex_preview,render,render",
        "render,save,render,save",
    ]
    for order in orders:
        script = (
            "import mudplot as mp\n"
            f"names = {order!r}.split(',')\n"
            "kinds = [type(getattr(mp, n)).__name__ for n in names]\n"
            "assert all(k == 'function' for k in kinds), (names, kinds)\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True
        )
        assert result.returncode == 0, f"{order}: {result.stderr}"


def test_grouped_bars_are_dodged_not_overlapping():
    # BUG: grouped bar charts drew every group's bars at the exact same x
    # position with the same width, so shorter bars were completely hidden
    # behind taller ones instead of being placed side-by-side -- a real
    # data-integrity/readability problem, not just cosmetics.
    data = {"x": [1, 2, 3] * 2, "y": [10, 20, 15, 5, 8, 25], "g": ["A"] * 3 + ["B"] * 3}
    p = mp.plot(data).bar("x", "y", group="g")
    fig = render(p.spec)
    xs = sorted({round(float(patch.get_x()), 3) for patch in fig.axes[0].patches})
    # 3 x-positions * 2 groups = 6 distinct (dodged) bar positions, not 3
    assert len(xs) == 6


def test_categorical_x_bar_chart_does_not_crash():
    # BUG: `_col()` forced dtype=float unconditionally, so a very common
    # case -- a bar chart with string category labels on x, e.g.
    # {"category": ["control", "treatment"], ...} -- crashed with
    # "could not convert string to float" instead of working the way plain
    # matplotlib (which has native categorical-axis support) would.
    data = {"category": ["control", "treatment", "placebo"], "value": [10, 25, 12]}
    p = mp.plot(data).bar("category", "value")
    fig = render(p.spec)
    ax = fig.axes[0]
    assert [t.get_text() for t in ax.get_xticklabels()] == [
        "control",
        "treatment",
        "placebo",
    ]
    assert len(ax.patches) == 3


def test_categorical_x_grouped_bar_chart_dodges_and_labels_correctly():
    data = {
        "category": ["control", "treatment", "placebo"] * 2,
        "value": [10, 25, 12, 8, 30, 15],
        "sex": ["M"] * 3 + ["F"] * 3,
    }
    p = mp.plot(data).bar("category", "value", group="sex")
    fig = render(p.spec)
    ax = fig.axes[0]
    assert [t.get_text() for t in ax.get_xticklabels()] == [
        "control",
        "treatment",
        "placebo",
    ]
    assert len(ax.patches) == 6


def test_categorical_x_line_and_scatter_do_not_crash():
    data = {"category": ["a", "b", "c"], "y": [1, 2, 3]}
    render(mp.plot(data).line("category", "y").spec)
    render(mp.plot(data).scatter("category", "y").spec)


def test_numeric_x_bar_chart_unaffected_by_categorical_support():
    # regression guard: adding categorical-x support must not change
    # behaviour for the (much more common) plain-numeric-x case.
    p = mp.plot({"x": [1, 2, 3], "y": [10, 20, 30]}).bar("x", "y")
    fig = render(p.spec)
    ax = fig.axes[0]
    xs = sorted(patch.get_x() + patch.get_width() / 2 for patch in ax.patches)
    assert xs == pytest.approx([1.0, 2.0, 3.0])


def test_ungrouped_bar_is_not_dodged():
    p = mp.plot({"x": [1, 2, 3], "y": [10, 20, 15]}).bar("x", "y")
    fig = render(p.spec)
    widths = {round(float(patch.get_width()), 3) for patch in fig.axes[0].patches}
    assert widths == {0.8}  # matplotlib's default bar width, unchanged


def test_cli_gives_clean_error_for_malformed_json(tmp_path):
    import subprocess
    import sys as _sys

    bad = tmp_path / "bad.json"
    bad.write_text("not json at all")
    result = subprocess.run(
        [_sys.executable, "-m", "mudplot", "validate", str(bad)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "error:" in result.stderr
