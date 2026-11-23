# Numeric size-only swarm

*[English](SWARM_SIZE.md)*

![합성크기매핑](images/swarm_size_semantics.png)

[실행예제](../examples/swarm_size_semantics.py) · [편집spec](images/swarm_size_semantics.mplot.json)

```python
p = mp.plot(data).swarmplot(
    "category", "response", group="group", dodge=0,
    semantics={"size": "mass", "size_norm": [0, 10], "sizes": [3, 9]},
)
```

기존SemanticSpec의numeric size열하나를지원합니다. Sizes는**point단위지름**이고선형매핑뒤
제곱해Matplotlib면적pt²가됩니다. 위bounds의mass0/5/10은실제area9/36/81이며개별관측매핑이지
그룹count/density/weight가아닙니다.

Category/value/group/size결측을동일행에서제외하고명시category/hue순서의선택rowID를packing·area/
observedguide·유효행2,000상한에공유합니다. Missing size는보간하지않고원본data/actions/JSON행은
고치지않습니다. 선택된bool/Inf/문자size는거절하고선택밖invalidsize는plot에영향을주지않습니다.
단strictJSON은전체source어디든비유한숫자가있으면여전히거절합니다.

기본은 한 layer의 선택 cohort domain이며 [named shared scale](SWARM_SHARED_SIZE.ko.md)은 pooled 크기를
opt-in지원합니다. Size_norm은clipping이지행filter가아닙니다.
좁고큰숫자/넓은유한범위는기존stable정규화를쓰고상수domain은중간지름·한guide를사용합니다.
같은mapping의guide원은관측좌표가없고legend=False는sizeguide만생략하며크기매핑은그대로입니다.
Legacygroup색guide는panellegend설정으로제어하고대표지름은중간값입니다. Sizeguide는group인용/URL을
상속하지않습니다.

최종DPI/layout/scale의실제반지름·stroke·gutter로packing하고기존orientation/dodge/nativecategory를
유지합니다. 양수 지름의 면적 underflow는 artist 전에 거절합니다. 이 size-only 예제의
기존 원/group 경로는 유지하며 [전체 C02 계약](SWARM_FACETS.ko.md)은 실제 named glyph·
hue/style·혼합 계열 domain·날짜/y2·명시 packing/live-template transaction도 지원합니다.
Scalar marker_size와 mapped size 동시 지정은 계속 거부하고 size를 질량/가중치로 바꾸지
않습니다. 의존성/버전 변경 없이 기존 생략 제어/JSON을 보존합니다. 성공 Figure는
호출자가 close해야 합니다.

합성 예제는 독립 사람 가독성/AT 인증이나 전체 CPU/RAM 보장이 아닙니다. 넓은 F01/G01 관문은 별도입니다.
