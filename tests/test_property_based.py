"""Property-based tests (Hypothesis) for the invariants the docstrings and
prose already claim: reducer purity/immutability, JSON round-tripping,
spec-version migration idempotency, and the citation/href character-safety
rule. Complements the example-based tests elsewhere with a much wider,
randomised input space -- exactly the areas
mudplot_v0.3_improvement_and_reference_repos.md calls out as a good fit for
this (FigureSpec/reducer round-trip, reducer immutability, URL escaping,
malformed input).
"""

import copy
import string

import mudplot as mp
from hypothesis import given, settings
from hypothesis import strategies as st
from mudplot import actions as A
from mudplot.reducer import reduce
from mudplot.spec import FigureSpec, migrate_spec_dict
from mudplot.theme import AVAILABLE_JOURNALS, AVAILABLE_THEMES
from mudplot.validate import _CITATION_UNSAFE, _HREF_UNSAFE

_finite_float = st.floats(allow_nan=False, allow_infinity=False)
_positive_float = st.floats(
    min_value=1e-3, max_value=1e6, allow_nan=False, allow_infinity=False
)

# A curated slice of the action vocabulary: simple, single-field actions
# whose parameters are cheap to generate and whose *validity* doesn't depend
# on other spec state (unlike e.g. AddLayer's column names needing to exist
# in spec.data). This is deliberately not "every action" -- the goal is a
# realistic, wide-but-tractable sample of reducer traffic, not an exhaustive
# action-space fuzzer.
_simple_actions = st.one_of(
    st.builds(A.SetSize, width=_positive_float, height=_positive_float),
    st.builds(A.SetDpi, dpi=st.integers(min_value=1, max_value=2000)),
    st.builds(A.SetSuptitle, text=st.text(max_size=50)),
    st.builds(A.SetTheme, name=st.sampled_from(AVAILABLE_THEMES)),
    st.builds(A.SetJournal, name=st.sampled_from((*AVAILABLE_JOURNALS, None))),
    st.builds(A.SetAutoLabel, enabled=st.booleans()),
    st.builds(
        A.SetPanelLabel,
        label=st.one_of(st.none(), st.text(max_size=5)),
        panel=st.just(0),
    ),
    st.builds(
        A.SetTitle,
        text=st.text(max_size=50),
        panel=st.just(0),
        citation=st.none(),
        href=st.none(),
    ),
    st.builds(
        A.SetReferenceMeasureText, text=st.one_of(st.none(), st.text(max_size=30))
    ),
)


@given(action=_simple_actions)
@settings(max_examples=200)
def test_reduce_never_mutates_its_input_state(action):
    """The core reducer-purity contract: reduce(state, action) must not
    change ``state`` itself, regardless of which action or what it
    contains -- callers (Store, an agent replaying a log, ...) rely on
    being able to keep using their original reference afterwards.
    """
    before = FigureSpec()
    snapshot = copy.deepcopy(before)
    reduce(before, action)
    assert before.to_dict() == snapshot.to_dict()


@given(action=_simple_actions)
@settings(max_examples=200)
def test_reduce_never_mutates_its_input_action(action):
    """Same contract for the action payload itself (a caller may reuse/log
    the same Action object after dispatching it).
    """
    snapshot = copy.deepcopy(action)
    reduce(FigureSpec(), action)
    assert action == snapshot


@given(action=_simple_actions)
@settings(max_examples=200)
def test_reduce_output_is_always_json_round_trippable(action):
    """Whatever reduce() produces must itself still be a valid, lossless
    FigureSpec -- i.e. applying one more action can never corrupt the spec
    into something that no longer round-trips through JSON.
    """
    result = reduce(FigureSpec(), action)
    d = result.to_dict()
    assert FigureSpec.from_dict(copy.deepcopy(d)).to_dict() == d


@given(action=_simple_actions)
@settings(max_examples=200)
def test_migration_is_a_no_op_on_a_current_version_spec(action):
    """migrate_spec_dict() must be idempotent/a no-op for any spec already
    at SPEC_VERSION, no matter what a prior action put in it (there being
    no migrations registered yet doesn't change this -- an *identity*
    property, exercised here across many different resulting specs).
    """
    d = reduce(FigureSpec(), action).to_dict()
    once = migrate_spec_dict(copy.deepcopy(d))
    twice = migrate_spec_dict(copy.deepcopy(once))
    assert once == d
    assert twice == once


# -- citation/href character-safety invariant (P0-2's own rule, restated as
# a property instead of a fixed example list) ------------------------------

_unsafe_citation_chars = "".join(sorted(_CITATION_UNSAFE))
_unsafe_href_chars = "".join(sorted(_HREF_UNSAFE))
# A conservative safe alphabet: ASCII letters/digits plus common punctuation
# that legitimately appears in BibTeX keys and URLs and is *not* in either
# unsafe set (so this alphabet is safe for both fields at once).
_safe_alphabet = "".join(
    c
    for c in string.ascii_letters + string.digits + "_:-./?=@!'\",;+ "
    if c not in _CITATION_UNSAFE and c not in _HREF_UNSAFE
)


@given(st.text(alphabet=_safe_alphabet, min_size=1, max_size=80).filter(str.strip))
@settings(max_examples=200)
def test_any_string_over_the_safe_alphabet_passes_citation_and_href_validation(
    text,
):
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", citation=text, href=text)
    issues = mp.validate(p.spec)
    assert not any("citation" in i or "href" in i for i in issues)


@given(st.text(min_size=1, max_size=40).filter(lambda s: set(s) & _CITATION_UNSAFE))
@settings(max_examples=100)
def test_any_string_containing_an_unsafe_citation_char_is_rejected(text):
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", citation=text)
    issues = mp.validate(p.spec)
    assert any("citation" in i for i in issues)


@given(st.text(min_size=1, max_size=40).filter(lambda s: set(s) & _HREF_UNSAFE))
@settings(max_examples=100)
def test_any_string_containing_an_unsafe_href_char_is_rejected(text):
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", href=text)
    issues = mp.validate(p.spec)
    assert any("href" in i for i in issues)


# -- FigureSpec round-trip over a wider parameter space --------------------


@given(
    width=_positive_float,
    height=_positive_float,
    dpi=st.integers(min_value=1, max_value=2000),
    suptitle=st.text(max_size=100),
    theme=st.sampled_from(AVAILABLE_THEMES),
)
@settings(max_examples=100)
def test_builder_json_round_trip_over_random_figure_level_settings(
    width, height, dpi, suptitle, theme
):
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4]})
        .line("x", "y")
        .size(width, height)
        .dispatch(A.SetDpi(dpi))
        .suptitle(suptitle)
        .theme(theme)
    )
    restored = mp.Plot.from_json(p.to_json())
    assert restored.spec.to_dict() == p.spec.to_dict()
