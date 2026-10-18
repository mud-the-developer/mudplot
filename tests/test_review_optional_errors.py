"""Installed-core optional boundaries must give actionable, accurate guidance."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_PROGRAM = r"""
import pathlib,sys
import mudplot as mp
p=mp.plot({'x':[1,2],'y':[2,3]}).line('x','y')
before=p.spec
path=pathlib.Path('preserved.png');path.write_bytes(b'previous output')
operations={
 'color':lambda:mp.color,
 'render':lambda:mp.render(p.spec),
 'plot-render':lambda:p.render(),
 'save':lambda:mp.save(p.spec,str(path)),
 'plot-save':lambda:p.save(str(path)),
 'preview':lambda:mp.tex_preview(p.spec),
}
try:
    operations[sys.argv[1]]()
except ImportError as error:
    extra='color' if sys.argv[1]=='color' else 'render'
    assert 'mudplot['+extra+']' in str(error), str(error)
    assert 'install' in str(error).lower(), str(error)
    assert isinstance(error.__cause__,ModuleNotFoundError)
else:
    raise AssertionError('optional effect unexpectedly ran without dependencies')
assert p.spec==before and mp.validate(p.spec)==[]
assert path.read_bytes()==b'previous output'
assert not {'numpy','matplotlib'}.intersection(sys.modules)
assert mp.from_json(p.to_json())==before
"""


@pytest.mark.parametrize(
    "operation", ["color", "render", "plot-render", "save", "plot-save", "preview"]
)
def test_missing_optional_effects_explain_the_install_extra_without_changing_state(
    tmp_path, operation
):
    result = subprocess.run(
        [sys.executable, "-S", "-c", _PROGRAM, operation],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("surface", ["cli", "cmap", "cycler"])
def test_color_only_mpl_adapters_and_cli_explain_the_render_extra(tmp_path, surface):
    script = r"""
import builtins,contextlib,io,pathlib,sys
import mudplot as mp
from mudplot.__main__ import main
p=mp.plot({'x':[1,2],'y':[2,3]}).line('x','y')
palette=mp.color.sequential(3) if sys.argv[1]!='cli' else None
pathlib.Path('input.json').write_text(p.to_json(),encoding='utf-8')
pathlib.Path('preserved.png').write_bytes(b'previous output')
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in {'matplotlib','cycler'}:
        raise ModuleNotFoundError('missing optional',name=name.split('.')[0])
    return original(name,*args,**kwargs)
builtins.__import__=guarded
if sys.argv[1]=='cli':
    output=io.StringIO()
    with contextlib.redirect_stderr(output):
        assert main(['render','input.json','preserved.png'])==1
    assert 'mudplot[render]' in output.getvalue(),output.getvalue()
else:
    try:getattr(palette,'to_cmap' if sys.argv[1]=='cmap' else 'as_mpl_cycler')()
    except ImportError as error:assert 'mudplot[render]' in str(error),str(error)
    else:raise AssertionError('missing mpl adapter unexpectedly worked')
assert pathlib.Path('preserved.png').read_bytes()==b'previous output'
"""
    result = subprocess.run(
        [sys.executable, "-c", script, surface],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("effect", ["render", "color"])
def test_unrelated_transitive_missing_module_keeps_its_original_diagnostic(effect):
    script = r"""
import builtins,sys
import mudplot as mp
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in {'numpy','matplotlib'}:
        raise ModuleNotFoundError('transitive failure',name='unrelated_transitive')
    return original(name,*args,**kwargs)
builtins.__import__=guarded
try:
    getattr(mp,sys.argv[1])
except ModuleNotFoundError as error:
    assert error.name=='unrelated_transitive'
    assert 'mudplot[' not in str(error)
else:
    raise AssertionError('transitive failure must not be hidden')
"""
    result = subprocess.run(
        [sys.executable, "-S", "-c", script, effect],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
