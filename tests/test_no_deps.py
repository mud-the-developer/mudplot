"""Guard: the pure engine must import and run without numpy / matplotlib.

Runs in a fresh subprocess so the check is not polluted by other tests that
already imported the effect layer.
"""

import subprocess
import sys

_SCRIPT = r"""
import sys
import mudplot as mp
from mudplot import actions as A

# Core usage: build, reduce, serialize, TeX sizing -- all dependency-free.
p = (mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]})
       .line("x", "y").labels(x="X", y="Y").theme("paper")
       .layout(1, 2).errorbar("x", "y", panel=1))
js = p.to_json()
mp.Plot.from_json(js)
mp.reduce(mp.FigureSpec(), A.SetSize(3, 2))
mp.figsize_for(mp.TEX_PRESETS["ieee"])

# Agent-facing surface must also stay dependency-free.
mp.capabilities()
mp.json_schema()
mp.apply([{"type": "SetSize", "width": 4, "height": 3}])
A.action_to_dict(A.action_from_dict({"type": "SetTitle", "text": "t"}))

assert "numpy" not in sys.modules, "numpy leaked into the pure core"
assert "matplotlib" not in sys.modules, "matplotlib leaked into the pure core"
print("OK")
"""


def test_pure_core_has_no_third_party_deps():
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"
