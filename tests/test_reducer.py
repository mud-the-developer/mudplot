import copy

import mudplot as mp
from mudplot import actions as A
from mudplot.reducer import reduce, reduce_all
from mudplot.spec import FigureSpec, LayerSpec
from mudplot.store import Store


def test_reduce_does_not_mutate_input():
    s0 = FigureSpec()
    snapshot = copy.deepcopy(s0)
    s1 = reduce(s0, A.SetSize(5, 4))
    assert s0.to_dict() == snapshot.to_dict()  # original untouched
    assert s1.size == [5, 4]
    assert s1 is not s0


def test_reduce_is_deterministic():
    s0 = FigureSpec()
    a = A.AddLayer(LayerSpec(type="line", x="a", y="b"))
    assert reduce(s0, a).to_dict() == reduce(s0, a).to_dict()


def test_reduce_all_folds_actions():
    s = reduce_all(
        FigureSpec(),
        [
            A.SetSize(3, 2),
            A.SetAxisLabel("x", "X"),
            A.SetTitle("t"),
            A.SetScale("y", "log"),
        ],
    )
    assert s.size == [3, 2]
    assert s.panels[0].x.label == "X"
    assert s.panels[0].title == "t"
    assert s.panels[0].y.scale == "log"


def test_set_palette_action():
    s = reduce(FigureSpec(), A.SetPalette(kind="sequential", params={"hue_start": 90}))
    assert s.theme.palette.kind == "sequential"
    assert s.theme.palette.hue_start == 90


def test_add_panel_extends():
    s = reduce(FigureSpec(), A.AddPanel())
    assert len(s.panels) == 2


def test_unknown_action_raises():
    import pytest

    with pytest.raises(TypeError):
        reduce(FigureSpec(), object())


def test_store_dispatch_and_subscribe():
    store = Store(FigureSpec())
    seen = []
    store.subscribe(lambda state, action: seen.append(type(action).__name__))
    store.dispatch(A.SetSize(4, 3))
    store.dispatch(A.SetTitle("hi"))
    assert seen == ["SetSize", "SetTitle"]
    assert store.state.size == [4, 3]
    assert store.state.panels[0].title == "hi"


def test_builder_uses_reducer_path():
    # Builder is sugar over actions -> the spec must reflect dispatches.
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").labels(x="X").theme("boxed")
    assert p.spec.panels[0].layers[0].x == "x"
    assert p.spec.panels[0].x.label == "X"
    assert p.spec.theme.axes.spines == "LRTB"
