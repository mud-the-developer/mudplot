# Swarm 관측값·packing scope·명시적 live facet transaction

*[English](SWARM_FACETS.md)* · [숫자 size](SWARM_SIZE.ko.md) · [공유 domain](SWARM_SHARED_SIZE.ko.md)

C02는 실제 native named glyph·독립 공유 hue/size/style·명시 cross-layer packing·
선택 live-template transaction을 추가합니다. 이전 materialized grid/SetData 부분집합은
보존하며 그것을 새 live 단위의 완료로 부르지 않습니다. Package 1.1.0·schema 0.1·
의존성 하한은 바꾸지 않습니다.

## 관측값과 공유 역할

```python
mapping = {
    "scale_id": "observations", "hue": "temperature", "hue_kind": "numeric",
    "size": "precision", "sizes": [3, 7],
    "style": "method", "markers": ["s", "^"]
}
p = (mp.plot(data)
     .swarmplot("category", "measurement", semantics=mapping, pack_scope="members")
     .swarmplot("category", "replicate", semantics=mapping, pack_scope="members"))
```

남은 관측값을 원본 순서의 개별 native glyph로 그리며 추정·가중치·역할 tuple 평균·
행 pooling은 없습니다. Category/측정값/필수 역할의 결측을 같은 행에서 제외합니다.
숫자/범주 hue·size와 범주 style·선택/예약 order는 scatter/lineplot/strip/ECDF/rug와
기존 raw-row domain·논리 panel guide를 공유합니다. 매핑 domain은 원본 row ID를
중복 제거합니다.

Size는 native **명목 지름 parameter(points)**이며 제곱해 면적으로 전달합니다.
실제 glyph 범위는 path에 따라 다릅니다. 질량이나 stroke 두께가 아닙니다.
Line/ECDF/rug는 같은 매핑 물리값을 stroke points로 사용합니다. 유한 named filled
marker는 `o s D ^ v P X d p h 8 *`이며 style별 서로 다른 선택이 충분해야 하고
순환하지 않습니다. 매핑 size/marker/hue를 scalar marker_size/marker/color로
덮어쓰면 거부합니다. 기존 group/hue_order와 size-only 또는 size/style 조합은
유지하며 semantic hue와 기존 색/group 채널의 충돌은 거부합니다. `c`·가중치·추론·
임의 Path/callback·사용하지 않는 옵션은 직렬화 제어가 아닙니다.

V/h·y/y2의 실제 category/측정 축 clock을 사용합니다. 기본 문자열은 ordinal이고
native 숫자/log/날짜는 원본 관측·단위·UTC 간격을 보존하며 log 값은 양수여야 합니다.
날짜 category의 선언 slot 범위만 autoscale 전에 category dataLim에 기여하므로
단일 날짜가 epoch 크기의 가짜 viewport를 만들지 않습니다. 독립 측정 범위는
유지합니다. Category slot이 없는 단일 날짜 raw line의 framing은 바꾸지 않습니다.

## 명시 cross-layer packing

`pack_scope=None`이면 semantic scale ID가 같아도 layer끼리 독립적입니다. 최대
64자의 비어 있지 않은 control-free 이름으로 같은 논리 panel·실제 target axes의
호환 member를 명시합니다. 같은 이름에서 y/y2 target·방향·category 열/order/native
배치·width/dodge/gap을 섞으면 거부하며 dodge한 hue 열/order도 같아야 합니다.
다른 panel은 함께 packing하지 않고 category/hue slot union은 draw 전에 정합니다.

기존 **layer마다 유효 2,000행 상한**은 유지합니다. 새 연산 상한은 **panel/scope마다
물리 instance 4,000개**이며 native point 구성 전에 pure 검증합니다. 같은 원본 행을
두 layer가 그리면 packing에는 **두 개**로 세고 domain 정규화만 ID를 중복 제거합니다.
최악 cell 작업/할당 측정에 근거한 연산 상한이지 SLA·sandbox 보장·layer 상한 증가나
Store history 최적화로 정당화한 제한 완화가 아닙니다.

Axes-owned coordinator가 실제 붙어 있고 보이는 member를 draw pass마다 한 번
packing합니다. Layout·범위/역전·DPI·backend·live grid 변경은 불변 원본 측정값에서
다시 계산하며 RNG·누적 drift가 없습니다. Native size/linewidth 배열 순환은 유지합니다.
Remove/hide/move한 member는 이전 axes를 차지하지 않고 이동한 artist는 현재 axes에서
다시 packing합니다.

이전 원은 정확한 기존 반지름/위치를 유지합니다. 다른 glyph는 실제 named Path를
그리며 native path bbox를 감싼 원과 round stroke 경계로 보수적으로 계산합니다.
원의 Bézier control hull을 과대 적용하지 않습니다. 같은 실제 Path 범위는 한 call에서
한 번만 계산하고 다음 draw에서는 새 geometry를 읽습니다. Greedy packing은 최적해가
아니며 과밀/과대 관측도 gutter에 모두 유지하고 정확한 clearance 경고를 냅니다.
Warn threshold는 [0,1], 기본 0.05·collection마다 한 번이며 crowded_count는 현재
계산값입니다. 숨긴 downsampling이나 관측 삭제가 없습니다.

## 기존 materialization과 명시 live 편집의 차이

```python
p.facet(col="cohort", col_order=["left", "empty", "right"], col_wrap=2, live=True)
p.layout(2, 2, width_ratios=[2, 1])  # 고정 3개 cell; 가짜 네 번째 panel 없음.
template = p.spec.facet_template.template
for layer in template.layers:
    layer.semantics.markers = ["D", "v"]
p.facet_template(template)  # 모든 cell에 대한 명시 SetFacetTemplate transaction.
```

기본 `.facet()`/SetFacets의 기존 materialized JSON과 동작은 그대로입니다. `live=True`는
SetLiveFacets와 선택 `FigureSpec.facet_template`에 typed PanelSpec template·해결한
row/col order·고정 selector를 보관하며 원본 데이터를 복사하거나 새 layout/ID 계층을
만들지 않습니다.

저장 template는 **명시 transaction의 recipe**이지 자동 reactive renderer가 아닙니다.
로드하면 저장한 materialized view와 로컬 override를 그대로 사용합니다. 기존 per-cell
편집은 로컬이고 이후 SetFacetTemplate는 의도한 모든 cell을 명시적으로 교체하여 로컬
layer/axis override를 덮어씁니다. Undo는 그 override를 복원합니다. 저장/재개방 자체는
적용하지 않지만 재개방 후 명시 template 편집도 모든 cell에 적용됩니다.

기존 category/hue order는 같은 선언 채널에 유지합니다. 새 order 또는 자동 order를
요청한 `reset_orders=True`는 현재 데이터에서 slot을 다시 정할 수 있습니다. 새 hue/group
채널은 관계없는 이전 label 대신 자기 수준을 사용합니다. SetData는 고정 예약 cell을
채우거나 비워도 새 facet cell/ID를 만들지 않습니다. 모든 생성 view를 고정 selector 안에서
검증하므로 제외 cohort의 잘못된 값이나 두 cell 각각 1,500행인 전체 3,000행은 그리지
않는 가짜 unfiltered template layer로 검증하지 않습니다. 선택한 cell의 잘못된 데이터는
거부합니다. 빈 cell에 collection·관측 guide를 만들지 않습니다.

전체 template 편집 뒤에도 현재 figure ratio/sharing을 보존합니다. 호환 ratio-only 편집은
덜 채운 wrapped grid와 recipe를 유지하며 명시 구조 layout/facet/joint/pair 교체나 panel
확장은 binding을 해제합니다. 일관성 없는 recipe/selector/layout은 binding을 조용히
버리지 않고 거부합니다. 기존 64-cell·총 layer·domain 및 cell별 swarm 상한은 유지합니다.
Swarm-only y2 facet을 지원하며 다른 G01 조합은 계속 필수입니다. 이 재사용 G01 증분은
G01 전체나 전역 E01/REL01의 종결이 아닙니다.

[전체 실행 예제](../examples/swarm_workflow.py)는 편집 JSON·PNG/SVG/PDF에 공유 계열과
날짜/y2/live grid를 저장합니다. 성공 Figure는 호출자가 close해야 하며 합성 preview를
독립 사람 가독성/접근성 인증이나 전체 CPU/RAM 보장으로 부르지 않습니다.
