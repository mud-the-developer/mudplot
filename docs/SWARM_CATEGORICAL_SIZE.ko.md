# Categorical size-only swarm

*[English](SWARM_CATEGORICAL_SIZE.md)* · [Numeric size](SWARM_SIZE.ko.md)

![합성순서별크기](images/swarm_categorical_size.png)

[실행source](../examples/swarm_categorical_size.py) · [편집spec](images/swarm_categorical_size.mplot.json)

```python
p = mp.plot(data).swarmplot(
    "category", "response", group="group", dodge=0,
    semantics={"size": "grade", "size_kind": "categorical",
               "size_order": ["small", "reserved", "medium", "large"],
               "sizes": [4, 10]},
)
```

기존SemanticSpec의categorical size는rank이지count/weight/추정된ordinal의미가아닙니다.
Size_order가없으면선택level의최초관측순서를유지하며사전/숫자순정렬은없습니다. 명시order는
행을선택하고미관측level도rank를예약합니다. 위small/reserved/medium/large지름은4/6/8/10pt이고
미관측reserved는guide/가짜관측을만들지않습니다. Domain한level은중간지름입니다.

Scatter/line과동일typedcategorykey/rankfraction을재사용하고bool과numeric은서로선택하지않습니다.
유한scalar/빈문자열아닌문자에서최대64개고유하고표시상명확한label이필요합니다. Malformedcategory를
sizeorder로숨기지않으며결측은category/value/group/size동일cohort에서제외합니다. 원본action/JSON행은유지합니다.

지름을Matplotlib면적pt²로제곱하고보정된개별반지름packing을사용합니다. Guide도동일rank/domain으로
만들며관측좌표/group인용·URL이없습니다. Group색은관측만표시하고non-dodged일때함께packing합니다.
Legend=False는크기guide만생략하고mapping은유지합니다. Numeric의clipping/중간값경로는변경하지않고
categorical에numeric size_norm을주면거절합니다.

PrimaryCartesianlayer에서semantic hue/style/date/y2/cross-familysharedscale/
동시scalar marker_size는계속거절합니다. 유효행2000상한은명시선택뒤적용하고양수면적표현불가는
artist전에실패합니다. Epsilon/source강제변환이나새model/action/specfield/의존성은없습니다.
성공Figure는호출자가소유하며close해야합니다. [Swarm-onlynamed size](SWARM_SHARED_SIZE.ko.md)는
pooledcategoricalrank를공유할수있습니다. [Facet/선택빈frame](SWARM_FACETS.ko.md)도지원합니다.

양editorrawJSON은보존하지만전용control/독립사람가독성·AT인증완료를주장하지않습니다.
자원상한은전체CPU/RAM/sandbox보장이아니며더넓은style/date/facet의미는남습니다.
