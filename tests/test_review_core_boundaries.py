"""STATE-07/08/09: deterministic pure core and explicit reference boundaries."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.spec import LayerSpec


@pytest.mark.parametrize("index", [-1, 2, True, False, 0.0, 1.5, "0", None])
@pytest.mark.parametrize(
    "factory", [A.RemoveLayer, A.SetColorbar, lambda i: A.SetLayerAt(i, [0.4, 0.2])]
)
def test_invalid_layer_indices_never_select_a_different_target(factory, index):
    plot = (
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").text("safe", at=[0.2, 0.3])
    )
    before, history = plot.spec, plot.store.history
    action = factory(index)
    payload = copy.deepcopy(action)
    with pytest.raises(ValueError, match="layer_index"):
        plot.dispatch(action)
    assert plot.spec == before and plot.store.history == history and action == payload
    plot.dispatch(A.SetTitle("recovered"))
    assert plot.spec.panels[0].title == "recovered"


def test_missing_panels_extend_but_absent_layers_do_not_modify_existing_panels():
    initial = mp.plot({"x": [1], "y": [2]}).line("x", "y").spec
    result = mp.reduce(initial, A.SetTitle("new", panel=2))
    assert len(result.panels) == 3 and len(initial.panels) == 1
    assert result.panels[0] == initial.panels[0] and result.panels[2].title == "new"
    before = copy.deepcopy(initial)
    with pytest.raises(ValueError, match="panel 2"):
        mp.reduce(initial, A.RemoveLayer(0, panel=2))
    assert initial == before


@pytest.mark.parametrize(
    "layer", [LayerSpec(x="absent", y="y"), LayerSpec(type="heatmap", matrix="absent")]
)
def test_reduce_can_build_invalid_references_but_render_validates_before_effects(layer):
    initial = mp.plot({"x": [1], "y": [2]}).spec
    spec = mp.reduce(initial, A.AddLayer(layer))
    issues = mp.validate(spec)
    assert issues and any("absent" in issue for issue in issues)
    with pytest.raises(ValueError) as caught:
        mp.render(spec)
    assert all(issue in str(caught.value) for issue in issues)
    assert not initial.panels[0].layers


_CORE = r"""
import builtins,hashlib,json,os,random,sys,time
import mudplot as mp
from mudplot import actions as A
seed=int(os.environ['CORE_TEST_SEED'])
random.seed(seed)
time.time=lambda: float(seed*1000000)
original_import=builtins.__import__
blocked={'numpy','matplotlib','pandas','polars','pyarrow','scipy','statsmodels'}
def guarded(name,*args,**kwargs):
    assert name.split('.')[0] not in blocked, name
    return original_import(name,*args,**kwargs)
builtins.__import__=guarded
def audit(event,args):
    if event=='open':
        filename,mode,flags=args
        writes=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC
        assert str(filename).endswith(('.py','.pyc')) and not flags&writes, args
        return  # Python code imports are not data-file effects.
    forbidden={'os.listdir','os.scandir','os.system','subprocess.Popen'}
    assert event not in forbidden, event
    assert not event.startswith(('socket.','urllib.')), event
sys.addaudithook(audit)
before=random.getstate()
initial=mp.plot({'x':[1,2],'y':[2,3]}).line('x','y').spec
actions=[A.SetTheme('publication'),A.SetSize(4,3),A.SetTitle('stable'),A.SetPalette(params={'hue_start':37})]
results=[]
for theme in ('boxed','minimal','paper','publication'):
    mp.reduce(mp.FigureSpec(),A.SetTheme(theme))
    result=mp.reduce_all(initial,actions)
    assert mp.validate(result)==[]
    results.append(mp.to_json(result))
assert len(set(results))==1 and random.getstate()==before
assert mp.json_schema() and mp.capabilities()
assert not blocked.intersection(sys.modules)
print(json.dumps({'sha256':hashlib.sha256(results[0].encode()).hexdigest(),'rng_unchanged':True,'effects_blocked':True}))
"""


def test_core_hash_survives_fresh_process_cwd_clock_rng_and_interleaved_styles(
    tmp_path,
):
    root = Path(__file__).resolve().parents[1]
    results = []
    for seed in (0, 97):
        directory = tmp_path / str(seed)
        directory.mkdir()
        completed = subprocess.run(
            [sys.executable, "-S", "-c", _CORE],
            cwd=directory,
            env={
                **os.environ,
                "PYTHONPATH": str(root),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": str(seed),
                "CORE_TEST_SEED": str(seed),
            },
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        results.append(json.loads(completed.stdout))
    assert results[0] == results[1]


@pytest.mark.parametrize("index", [-1, True, False, 0.0, "0", None])
def test_invalid_panel_indices_and_unknown_wire_actions_preserve_state(index):
    plot = mp.plot({"x": [1], "y": [2]}).line("x", "y")
    before, history = plot.spec, plot.store.history
    with pytest.raises(ValueError, match="panel index"):
        plot.dispatch(A.SetTitle("wrong target", panel=index))
    assert plot.spec == before and plot.store.history == history
    with pytest.raises(ValueError, match="unknown action"):
        A.action_from_dict({"type": "NotAnAction"})
    assert plot.spec == before and plot.store.history == history


def test_previous_render_style_cannot_change_reducer_result():
    initial = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").spec
    action = A.SetTheme("publication")
    expected = mp.reduce(initial, action)
    mp.plot({"x": [1, 2], "y": [3, 2]}).line("x", "y").theme("boxed").render()
    assert mp.reduce(initial, action) == expected
