"""Guard: the declarative core must run without numpy / matplotlib.

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

# Bar intervals, styling and the publication preset stay in the pure core.
q = (mp.plot({"x": [0], "mean": [1], "lo": [0.8], "hi": [1.1]})
       .theme("publication")
       .bar("x", "mean", y_lower="lo", y_upper="hi", bar_width=0.6,
            error_line_width=1, capsize=0))
assert mp.validate(q.spec) == []
assert mp.Plot.from_json(q.to_json()).spec == q.spec

# Distribution grouping/options remain pure until explicit rendering.
r = (mp.plot({"cat": ["A", "A"], "v": [1, 3], "hue": ["u", "u"]})
       .box("cat", "v", group="hue", whis=(0, 100), orient="h")
       .violin("cat", "v", bw_method="silverman", points=51)
       .boxenplot("cat", "v", group="hue", k_depth="trustworthy", trust_alpha=.01,
                  width_method="area")
       .swarmplot("cat", "v", group="hue", orient="h", dodge=0, warn_thresh=0))
assert mp.validate(r.spec) == []
assert mp.Plot.from_json(r.to_json()).spec == r.spec
assert mp.apply(r.action_log) == r.spec

# Native/log geometry and explicit statistic coordinates stay pure too.
s = (mp.plot({"c": [10, 10], "v": [1, 9]})
       .boxenplot("c", "v", native_scale=True, stat_scale="axis")
       .swarmplot("c", "v", native_scale=True).xscale("log").yscale("log"))
assert mp.validate(s.spec) == []
assert mp.Plot.from_json(s.to_json()).spec == s.spec
assert mp.apply(s.action_log) == s.spec

# Named violin transforms are also pure until rendering.
t = (mp.plot({"c": [10]*4, "v": [1,2,3,4], "h": ["A"]*2+["B"]*2})
       .violin("c", "v", group="h", inner="quart", split=True,
               density_norm="count", common_norm=True, bw_adjust=.7,
               cut=2, clip=(.5,8)))
assert mp.validate(t.spec) == []
assert mp.Plot.from_json(t.to_json()).spec == t.spec
assert mp.apply(t.action_log) == t.spec

# Relative weighted violin grouping remains pure too; fitting is render-only.
tw = (mp.plot({"c": [10]*3, "v": [1,4,9], "w": [1,3,2]})
        .violin("c", "v", weights="w", inner="quart", density_norm="count"))
assert mp.validate(tw.spec) == []
assert mp.Plot.from_json(tw.to_json()).spec == tw.spec
assert mp.apply(tw.action_log) == tw.spec

# Typed named component styles also remain dependency-free.
u = (mp.plot({"c": [10]*4, "v": [1,2,3,8]})
       .box("c", "v", showmeans=True, components={
           "body": {"alpha": 1}, "mean": {"marker": "s"},
           "median": {"color": "#ff8800"}}))
assert mp.validate(u.spec) == []
assert mp.Plot.from_json(u.to_json()).spec == u.spec
assert mp.apply(u.action_log) == u.spec
assert mp.DistributionComponentsSpec(body=mp.ComponentStyleSpec(alpha=1))

# Statistical native/log geometry and explicit baseline are declarative too.
v = (mp.plot({"c": [10,10,30,30], "v": [1,4,4,16]})
       .barplot("c", "v", native_scale=True, stat_scale="axis", baseline=.1)
       .pointplot("c", "v", native_scale=True, stat_scale="axis")
       .countplot("c", native_scale=True, baseline=.1).xscale("log").yscale("log"))
assert mp.validate(v.spec) == []
assert mp.Plot.from_json(v.to_json()).spec == v.spec
assert mp.apply(v.action_log) == v.spec

# Numeric-x line estimates defer inference and native bands to rendering.
vl = (mp.plot({"x": [1,1,10,10], "y": [1,4,4,16],
               "w": [1,2,1,2], "u": ["A","B"]*2})
        .lineplot("x", "y", weights="w", units="u", n_boot=11, seed=3,
                  stat_scale="axis").xscale("log").yscale("log"))
assert mp.validate(vl.spec) == []
assert mp.Plot.from_json(vl.to_json()).spec == vl.spec
assert mp.apply(vl.action_log) == vl.spec

# ECDF raw data, weights and typed options stay pure too.
w = (mp.plot({"v": [1,2,2,4], "w": [1,2,1,3], "h": ["A"]*4})
       .ecdf("v", weights="w", group="h", complementary=True,
             hue_order=["empty", "A"], orient="h").yscale("log"))
assert mp.validate(w.spec) == []
assert mp.Plot.from_json(w.to_json()).spec == w.spec
assert mp.apply(w.action_log) == w.spec
assert mp.ECDFSpec().stat == "proportion"

# Typed histogram statistics share row contracts but defer numeric bins/effects.
z = (mp.plot({"v": [1,2,2,4], "w": [1,2,1,3], "h": ["A"]*4})
       .hist("v", bins=[0,2,4], stat="density", weights="w", group="h",
             common_norm=False, cumulative=True, orient="h", multiple="stack",
             element="step"))
assert mp.validate(z.spec) == []
assert mp.Plot.from_json(z.to_json()).spec == z.spec
assert mp.apply(z.action_log) == z.spec
assert mp.HistogramSpec().stat == "count"
assert mp.HistogramSpec().multiple == "layer"
assert mp.HistogramSpec().element == "bars"
assert mp.validate(mp.plot({"v":[1,2],"h":["A","B"]}).hist(
    "v", group="h", multiple="dodge").spec) == []

# Gaussian KDE configs, paired validation and row scales defer all fitting.
aa = (mp.plot({"v": [1,2,2,4], "w": [1,2,1,3], "h": ["A"]*4})
        .kde("v", weights="w", group="h", bw_method="silverman", bw_adjust=.8,
             gridsize=51, cut=2, clip=[.1,None], common_grid=True,
             common_norm=False, cumulative=True, fill=True, orient="h")
        .yscale("log"))
assert mp.validate(aa.spec) == []
assert mp.Plot.from_json(aa.to_json()).spec == aa.spec
assert mp.apply(aa.action_log) == aa.spec
assert mp.KDESpec().bw_method == "scott"

# 2-D kernel fitting/contour quadrature are also render-only effects.
bb = mp.plot({"x": [1,2,4,3], "y": [1,4,2,3], "w": [1,2,1,3]}).kde2d(
    "x","y", weights="w", gridsize=31, levels=(.5,.9),
    clip=((.1,None),(.1,None)), fill=True, common_grid=True,
).xscale("log").yscale("log")
assert mp.validate(bb.spec) == []
assert mp.Plot.from_json(bb.to_json()).spec == bb.spec
assert mp.apply(bb.action_log) == bb.spec
assert mp.KDE2DSpec().levels == [.5,.8,.95]

# Independent semantic rows and options remain stdlib-only before rendering.
cc = mp.plot({"x": [1,2,3], "y": [3,1,2], "h": ["A","B","A"],
              "m": [0,5,10], "s": ["X","Y","X"]}).scatter(
    "x", "y", semantics=mp.SemanticSpec(hue="h", size="m", style="s"),
)
assert mp.validate(cc.spec) == []
assert mp.Plot.from_json(cc.to_json()).spec == cc.spec
assert mp.apply(cc.action_log) == cc.spec
assert mp.SemanticSpec().hue_kind == "categorical"

# Named figure pooling/config matching also remains dependency-free.
dd = mp.plot({"a": [1,2,None], "b": [None,2,3], "y": [1,2,3],
              "h": ["A","B","C"], "m": [0,5,10]}).layout(1,2)
for index,name in enumerate(("a","b")):
    dd.scatter(name,"y",semantics=mp.SemanticSpec(scale_id="study",hue="h",size="m"),panel=index)
assert mp.validate(dd.spec) == []
assert mp.Plot.from_json(dd.to_json()).spec == dd.spec
assert mp.apply(dd.action_log) == dd.spec

# Semantic curve partition and paired inference selection is also stdlib-only.
ee = mp.plot({"t":[1,1,2,2],"y":[1,3,3,5],"h":["A"]*4,
              "s":["X"]*4,"m":[0]*4}).lineplot(
    "t","y",semantics=mp.SemanticSpec(hue="h",size="m",sizes=[1,3],style="s",dashes=["-"]),errorbar="sd")
assert mp.validate(ee.spec) == []
assert mp.Plot.from_json(ee.to_json()).spec == ee.spec
assert mp.apply(ee.action_log) == ee.spec

# Agent-facing surface must also stay dependency-free.
mp.capabilities()
mp.json_schema()
mp.apply([{"type": "SetSize", "width": 4, "height": 3}])
A.action_to_dict(A.action_from_dict({"type": "SetTitle", "text": "t"}))

assert "numpy" not in sys.modules, "numpy leaked into the dependency-free core"
assert "matplotlib" not in sys.modules, (
    "matplotlib leaked into the dependency-free core"
)
print("OK")
"""


def test_declarative_core_has_no_third_party_deps():
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"
