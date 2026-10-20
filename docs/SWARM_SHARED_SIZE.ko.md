# Named shared Swarm sizes

*[English](SWARM_SHARED_SIZE.md)* · [Numeric](SWARM_SIZE.ko.md) · [Categorical](SWARM_CATEGORICAL_SIZE.ko.md)

![로컬관측과공유크기](images/swarm_shared_size.png)

[실행source](../examples/swarm_shared_size.py) · [편집spec](images/swarm_shared_size.mplot.json)

```python
p.swarmplot("category", "left", panel=0,
            semantics={"size": "mass", "scale_id": "shared_mass"})
p.swarmplot("category", "right", panel=1,
            semantics={"size": "mass", "scale_id": "shared_mass"})
```

Named domain은**크기mapping만**공유하며관측/색/좌표/인용이나cross-layer충돌보장은공유하지않습니다.
각member의category/value/group/size결측cohort와명시선택은유지하고원본rowID를union/중복제거/
source순으로정렬합니다. Mass0/5/10의left[0,10],right[5,10]은기본지름3..9에서area가각각[9,81]/[36,81]이고
독립정규화right[9,81]이아닙니다.

Numeric bounds/categorical rank는pooled선택행을사용합니다. Categorical은source최초순서나동일명시order와
예약slot을사용하고guide는로컬에없어도pooled관측level을표시하되관측좌표/groupURL을만들지않습니다.
Panel마다named domain의sizeguide는한번이고앞memberlegend=False가뒤enabledguide를숨기지않습니다.
Group색guide는로컬관측그대로이며shared semantic hue로바뀌지않습니다.

Scale_id/legend외semantic설정은동일해야하며충돌은실패합니다. Swarm named domain에scatter/line을
섞으면거절하고기존scatter/line/이름없는Swarmlocal경로는유지합니다. Layer유효행2000/독립pooled고유행10000/
최대64명확한categoricallevel을artist전에검사하고pooledarea underflow도순수검증해기존출력파일을보호합니다.

PrimaryCartesianSwarm은명시facet/filter/dropna선택을지원하고[선택된빈cell](SWARM_FACETS.ko.md)은
관측/guide없는frame입니다. 일반unfilteredemptylayer는거절하며y2/semantic-hue-style-date/mixed-familydomain/
scalar marker_size동시지정도계속거절합니다. 수동panel과서로다른로컬cohort는가능하며
새model/action/specfield/의존성/버전은없습니다. 양editorrawJSON은보존하지만전용UIcontrol완료는아닙니다.

성공Figure는호출자가close하고합성예제는독립사람가독성/AT인증이아닙니다. 행상한은전체CPU/RAM/sandbox
보장이아니며더넓은shared/facet계약은별도작업입니다.
