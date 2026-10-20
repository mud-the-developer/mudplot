# Swarm facet과빈cell

*[English](SWARM_FACETS.md)* · [Size mapping](SWARM_SIZE.ko.md) · [Named size](SWARM_SHARED_SIZE.ko.md)

![빈cell과선택관측](images/swarm_facets.png)

[실행source](../examples/swarm_facets.py) · [편집spec](images/swarm_facets.mplot.json)

```python
p = (mp.plot(data)
     .swarmplot("category", "response", group="group", dodge=0,
                semantics={"size": "mass"})
     .facet(col="cohort", col_order=["empty", "left", "right"], col_wrap=2))
```

기존facetmaterialization의명시cell/category-hueslot/source-rowfilter를사용합니다. PrimaryCartesian의
scalar원/numeric-categoricalsize매핑을지원하고sizedfacet에는자동sharedsizeID를부여해선택원본rowunion으로
bounds/rank를정합니다. Cell별독립정규화가아니며missingsize도같은로컬cohort에서제외하고원본행/값/JSON/
actions/기존filter필드를다시쓰지않습니다.

명시필터의빈cohort는**frame-only**입니다. SwarmCollection/marker/관측group-proxy/sizeguide를만들지않고
이미알려진categoryslot만유지하며없는category는추정하지않습니다. Reserved-onlysemanticgrid에서빈numeric
정규화를계산하지않고일반unfilteredempty/all-missingSwarm은계속거절합니다. Paneldropna도같은선택계약이며
없는열은거절합니다.

빈첫layer가뒤populatedmember의namedguide를소비하지않고예약group색slot은유지합니다. 비어있지않은cell의
guide는pooledsize이고관측/URL/group색은로컬입니다. SetData로예약cell을채웠다비워도materializedfilters/
panels는유지합니다. 새category/facetlevel을자동추가하지않으며필요하면order갱신/재materialize해야합니다.

빈cell도옵션/열/native축/width-dodge/표현가능선언크기를검사합니다. Numericnative-log범주/방향/log값/
DPI/redraw의보정은유지하고layer유효행2000/namedpool고유행10000/sizelevel64/facetcell64/기존총layer확장상한을
보존합니다. 잘못된확장은Plot상태를바꾸지않습니다.

새model/action/specfield/의존성/버전은없고양editorrawfilteredJSON의metadata편집/undo-redo/cache를검사하지만
전용facet/sizecontrol완료는아닙니다. Y2/semantic-hue-style-date/임의marker/mixed-familysharedID는계속거절하며
다른plotfamily의빈cell동작을이Swarm전용검증경로로바꾸지않습니다.

성공Figure는호출자가close하고합성preview검토는독립사람가독성/AT인증이나전체CPU/RAM/sandbox보장이
아닙니다. 명시materialization이지새live-template mapper완료가아닙니다.
