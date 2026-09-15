import copy
from typing import cast

import mudplot as mp
import pytest
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


def test_limits_can_return_to_automatic():
    fixed = reduce(FigureSpec(), A.SetLimits("x", 1.0, 2.0))
    assert fixed.panels[0].x.limits == [1.0, 2.0]
    automatic = reduce(fixed, A.SetLimits("x", None, None))
    assert automatic.panels[0].x.limits is None
    with pytest.raises(ValueError, match="both lo and hi"):
        reduce(fixed, A.SetLimits("x", 1.0, None))


def test_secondary_axis_can_be_removed():
    configured = reduce(FigureSpec(), A.SetSecondaryAxis("Y2", scale="log"))
    assert configured.panels[0].y2 is not None
    cleared = reduce(configured, A.SetSecondaryAxis(None))
    assert cleared.panels[0].y2 is None


@pytest.mark.parametrize("projection", ["2d", "polar"])
def test_switching_to_a_non_3d_projection_clears_z_axis_configuration(projection):
    spec = reduce(FigureSpec(), A.SetProjection("3d"))
    spec = reduce(spec, A.SetZAxis("Z", limits=[0, 1]))
    spec = reduce(spec, A.SetProjection(projection))
    assert spec.panels[0].projection == projection
    assert spec.panels[0].z is None


def test_unknown_action_raises():
    with pytest.raises(TypeError):
        reduce(FigureSpec(), cast(A.Action, object()))


def test_store_dispatch_and_subscribe():
    store = Store(FigureSpec())
    seen = []
    store.subscribe(lambda state, action: seen.append(type(action).__name__))
    store.dispatch(A.SetSize(4, 3))
    store.dispatch(A.SetTitle("hi"))
    assert seen == ["SetSize", "SetTitle"]
    assert store.state.size == [4, 3]
    assert store.state.panels[0].title == "hi"


def test_builder_can_restore_automatic_limits_and_remove_secondary_axis():
    p = (
        mp.plot()
        .xlim(0, 1)
        .ylim(-1, 1)
        .secondary_yaxis("Y2")
        .xlim()
        .ylim()
        .secondary_yaxis(None)
    )
    panel = p.spec.panels[0]
    assert panel.x.limits is None
    assert panel.y.limits is None
    assert panel.y2 is None


def test_builder_uses_reducer_path():
    # Builder is sugar over actions -> the spec must reflect dispatches.
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").labels(x="X").theme("boxed")
    assert p.spec.panels[0].layers[0].x == "x"
    assert p.spec.panels[0].x.label == "X"
    assert p.spec.theme.axes.spines == "LRTB"
