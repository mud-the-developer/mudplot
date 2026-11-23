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
spectral = mp.plot({"raw": [1, 0, -1, 0]}).spectrum(
    "raw", fs=4, nfft=4, window="boxcar"
)
assert mp.validate(spectral.spec) == []
assert mp.Plot.from_json(spectral.to_json()).spec == spectral.spec
assert mp.apply(spectral.action_log) == spectral.spec
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
assert mp.HistogramSpec().fill is None
assert mp.HistogramSpec(fill=True).to_dict()["fill"] is True
assert mp.validate(mp.plot({"v":[1,2],"h":["A","B"]}).hist(
    "v", group="h", multiple="dodge").spec) == []

composition = mp.plot({"v":[1,2],"h":["A","B"]}).hist(
    "v", bins=[0,1.5,3], group="h", multiple="fill", element="poly")
assert mp.validate(composition.spec) == []
assert mp.Plot.from_json(composition.to_json()).spec == composition.spec
assert mp.apply(composition.action_log) == composition.spec

for bin_rule in ("auto","fd","stone","discrete"):
    binned = mp.plot({"v":[0,1,2],"h":["A","A","B"]}).hist(
        "v", bins=bin_rule, group="h")
    assert mp.validate(binned.spec) == []
    assert mp.Plot.from_json(binned.to_json()).spec == binned.spec
    assert mp.apply(binned.action_log) == binned.spec

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

# Rug observations, point-stroke/dash roles and explicit observation clocks stay
# pure for x, primary y and y2; perpendicular calendar units are not rug height.
rug_data = {"when": ["2026-01-03T00:00:00+02:00", "2026-01-01T00:00:00Z"],
            "m": [0, 2], "method": ["A", "B"], "id": ["late", "early"]}
for orient,axis,clock in (("v","y","x"), ("h","y","y"), ("h","y2","y2")):
    rug = mp.plot(rug_data)
    if axis == "y2":
        rug.secondary_yaxis("Observed date")
    rug.date_axis(clock, timezone="UTC")
    rug.date_axis("y" if orient == "v" else "x",
                  unit="s", origin="1980-01-01T00:00:00Z")
    rug.rug("when", orient=orient, axis=axis, height=.3, colorbar=True,
            semantics={"scale_id":"rug-pure", "hue":"m", "hue_kind":"numeric",
                       "size":"m", "sizes":[0,4], "style":"method",
                       "dashes":["--",":"]})
    assert mp.validate(rug.spec) == []
    assert mp.Plot.from_json(rug.to_json()).spec == rug.spec
    assert mp.apply(rug.action_log) == rug.spec
    assert rug.spec.data.columns == rug_data

# Explicit cross-layer instances and whole-template edits remain pure.
swarm_data = {"c":["2026-01-01"]*2, "v":[1,1.01], "h":[0,1],
              "s":[1,2], "d":["A","B"], "cohort":["left","right"], "id":["r2","r1"]}
live_swarm = mp.plot(swarm_data).secondary_yaxis("Observed")
live_swarm.date_axis("x",timezone="UTC")
for _ in range(2):
    live_swarm.swarmplot("c","v",axis="y2",pack_scope="members",semantics={
        "hue":"h","hue_kind":"numeric","size":"s","style":"d","markers":["s","D"]})
live_swarm.facet(col="cohort",col_order=["left","empty","right"],live=True)
template = live_swarm.spec.facet_template.template
for layer in template.layers:
    layer.semantics.markers = ["^","v"]
live_swarm.facet_template(template)
assert mp.validate(live_swarm.spec) == []
assert mp.Plot.from_json(live_swarm.to_json()).spec == live_swarm.spec
assert mp.apply(live_swarm.action_log) == live_swarm.spec
assert live_swarm.spec.data.columns == swarm_data

# Raw median inference and supplied summary clocks/roles/live recipes are pure.
import copy
raw_box = mp.plot({"c":["A"]*3,"v":[1,2,30]}).box(
    "c","v",median_ci={"level":90,"n_boot":31,"seed":7},cap_fraction=.7)
assert mp.validate(raw_box.spec) == []
assert mp.apply(raw_box.action_log) == raw_box.spec
box_table = {"c":["2026-01-01","2026-07-01"],"med":[2,4],
             "q1":[1,3],"q3":[3,5],"lo":[.5,2],"hi":[4,6],
             "cl":[1.5,3.5],"ch":[2.5,4.5],"out":[[5],[7]],
             "h":[True,1],"m":[1,3],"s":["A","B"],
             "cohort":["left","right"],"id":["original-b","original-a"]}
box_view = mp.plot(box_table).secondary_yaxis("Response").date_axis("x",timezone="UTC")
box_view.bxp("c","med",q1="q1",q3="q3",whislo="lo",whishi="hi",
             cilo="cl",cihi="ch",fliers="out",notch=True,axis="y2",cap_fraction=.7,
             semantics={"scale_id":"box-pure","hue":"h","size":"m","style":"s"},
             hue_components=[{"level":True,"components":{"cap":{"color":"red"}}},
                             {"level":1,"components":{"cap":{"color":"blue"}}}])
box_view.facet(col="cohort",col_order=["left","empty","right"],live=True)
template = copy.deepcopy(box_view.spec.facet_template.template)
template.layers[0].box.cap_fraction = 1
box_view.facet_template(template)
assert mp.validate(box_view.spec) == []
assert mp.Plot.from_json(box_view.to_json()).spec == box_view.spec
assert mp.apply(box_view.action_log) == box_view.spec
assert box_view.spec.data.columns == box_table

# Axis controls, named conversion, and typed actions remain pure-core operations.
axis_view = mp.plot({"x": [1, 2, 4], "y": [.1, .5, .9]}).line("x", "y")
axis_view.xscale("log", options={"base": 2, "subs": [1.5]})
axis_view.yscale("logit")
axis_view.ticks("x", {"locator": {"kind": "fixed", "values": [1, 2, 4]}})
axis_view.secondary_axis("x", {"kind": "seconds_milliseconds"})
assert mp.validate(axis_view.spec) == []
assert mp.Plot.from_json(axis_view.to_json()).spec == axis_view.spec
assert mp.apply(axis_view.action_log) == axis_view.spec

# New violin components/roles and explicit live/nested transactions stay pure.
import copy
violin_table = {"c": ["A"]*6, "v": [1,4,9]*2, "h": [True]*3+[1]*3,
                "w": [1,3,2]*2, "cell": ["left"]*3+["right"]*3,
                "id": ["a","b","c","d","e","f"]}
violin_view = mp.plot(violin_table).violin(
    "c", "v", weights="w", inner="box", split=True,
    violin=mp.ViolinSpec(split_policy="paired", hue_components=[
        mp.ViolinHueComponentsSpec(True,
            mp.DistributionComponentsSpec(whisker=mp.ComponentStyleSpec(color="red")))
    ]),
    semantics=mp.SemanticSpec(hue="h"),
    components=mp.DistributionComponentsSpec(body=mp.ComponentStyleSpec(alpha=.9)),
).facet(col="cell", col_order=["left","empty","right"], live=True)
violin_template = copy.deepcopy(violin_view.spec.facet_template.template)
violin_template.layers[0].inner = "point"
violin_template.layers[0].violin.hue_components = []
violin_template.layers[0].components = mp.DistributionComponentsSpec(
    point=mp.ComponentStyleSpec(marker_size=5, line_style="none"))
violin_view.facet_template(violin_template)
assert mp.validate(violin_view.spec) == []
assert mp.Plot.from_json(violin_view.to_json()).spec == violin_view.spec
assert mp.apply(violin_view.action_log) == violin_view.spec
assert violin_view.spec.data.columns == violin_table
nested_violin = mp.Plot.from_json(violin_view.to_json()).mosaic(
    [["left","empty","right"]]
).nest(1,1).inset("left", [.1,.1,.3,.3], panel_id="detail")
assert mp.validate(nested_violin.spec) == []
assert mp.Plot.from_json(nested_violin.to_json()).spec == nested_violin.spec

# Weighted letter-value replacement and NEW statistical roles/clocks use the
# same pure reducer/codec; no scientific effect is imported to validate source.
weighted_letters = mp.plot({"v": [0,10,20], "w": [1,38,1]}).boxenplot(
    "v", weights="w", k_depth=1,
    boxen=mp.BoxenSpec(band_components=[
        mp.BoxenBandComponentsSpec(0, "central", mp.ComponentStyleSpec(hatch="/"))
    ]))
letter_layer = copy.deepcopy(weighted_letters.spec.panels[0].layers[0])
letter_layer.k_depth = 2
weighted_letters.dispatch(A.ReplaceLayer(0, letter_layer))
assert mp.validate(weighted_letters.spec) == []
assert mp.Plot.from_json(weighted_letters.to_json()).spec == weighted_letters.spec
assert mp.apply(weighted_letters.action_log) == weighted_letters.spec
secondary_letters = (mp.plot({"v": [0,10,20], "w": [1,38,1],
                             "cell": ["left","left","right"], "id": ["a","b","c"]})
    .secondary_yaxis("Letter response")
    .boxenplot("v", weights="w", axis="y2", k_depth=1)
    .facet(col="cell", col_order=["left","empty","right"], live=True))
secondary_layer = copy.deepcopy(secondary_letters.spec.panels[0].layers[0])
secondary_layer.showmedians = False
secondary_letters.dispatch(A.ReplaceLayer(0, secondary_layer))
assert mp.validate(secondary_letters.spec) == []
assert mp.Plot.from_json(secondary_letters.to_json()).spec == secondary_letters.spec
assert mp.apply(secondary_letters.action_log) == secondary_letters.spec
stat_table = {"date": ["2026-01-01"]*6, "v": [0,10,20]*2, "w": [1,38,1]*2,
              "h": [True]*3+[1]*3, "cell": ["left"]*3+["right"]*3,
              "id": ["a","b","c","d","e","f"]}
stat_view = (mp.plot(stat_table).secondary_yaxis("Observed response")
    .date_axis("x", timezone="UTC")
    .pointplot("date", "v", weights="w", estimator="median", errorbar=("pi",95),
               semantics=mp.SemanticSpec(hue="h", hue_order=[True,1]), axis="y2")
    .facet(col="cell", col_order=["left","empty","right"], live=True))
stat_template = copy.deepcopy(stat_view.spec.facet_template.template)
stat_template.layers[0].stat.estimator = "mean"
stat_view.facet_template(stat_template)
stat_layer = copy.deepcopy(stat_view.spec.panels[0].layers[0])
stat_layer.marker = "D"
stat_view.dispatch(A.ReplaceLayer(0, stat_layer))
assert mp.validate(stat_view.spec) == []
assert mp.Plot.from_json(stat_view.to_json()).spec == stat_view.spec
assert mp.apply(stat_view.action_log) == stat_view.spec
assert stat_view.spec.data.columns == stat_table

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
