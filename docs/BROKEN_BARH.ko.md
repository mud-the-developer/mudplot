# Numeric interval band

*[English](BROKEN_BARH.md)*

![합성겹친구간](images/plots/broken_barh.png)

[실행source](../examples/plots/broken_barh.py) · [편집spec](images/plots/broken_barh.mplot.json)

```python
p = (mp.plot({"start": [3, 1, 3], "duration": [1, 2, 0.5]})
       .broken_barh("start", "duration", bottom=1, height=1)
       .labels(x="Interval position", y="Raw band"))
```

각source행은[start,start+duration]구간이며rawyband는bottom부터bottom+height까지입니다.
겹침/반복행을병합·정렬·binning·추정하지않고source/JSON/actions·SetData를보존합니다.
이numeric구간primitive는범주형bar추정기나날짜timeline이아닙니다.

기존LayerSpec.x/y는start/duration열이름,baseline은bottom(기본0),width는height(기본1)이며
rawJSONNone도같은기본입니다. Row-aligned1..10,000유한숫자구간이필요하며bool/결측/날짜/범주는
지원하지않습니다. Duration/height는양수유한값이며렌더float좌표에서끝점을검사합니다.
Overflow/구별불가끝점(큰정수에서단위폭이사라지는경우포함)은artist전에거절하고역전/절삭/clamp하지않습니다.

첫범위는linearCartesianprimary/y2의단일filledband입니다. 색/edge색/dash/alpha와유한[0,1000]
line_width를적용하고0폭은그대로둡니다. Matplotlib3.8legend호환을위해0폭의보이지않는dash패턴만
제거하고source설정/양수폭dash는보존합니다. 성공Figure는호출자가소유하므로close하세요.

Group/hue/facet/dropna/semantic/weight/date/log/polar/3D는명시미지원이며자원상한은전체CPU/RAM/
sandbox보장이나독립사람가독성/AT인증이아닙니다. 기존rawaction을사용합니다.

```json
{"type":"AddLayer","layer":{"type":"broken_barh","x":"start","y":"duration","baseline":1,"width":1}}
```
