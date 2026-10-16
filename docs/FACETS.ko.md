# 자동 facet: 첫 지원 범위

*[English](FACETS.md)*

Facet은 같은 원자료를 나누어 **동일한 질문**을 비교하는 기능입니다. 서로 다른
그래프를 모으는 기능이나 Seaborn figure-level 전체 동등성이 아닙니다.

![Site별 합성 반응 곡선](images/faceted_responses.png)

[편집 spec](images/faceted_responses.mplot.json) ·
[SVG](images/faceted_responses.svg) · [PDF](images/faceted_responses.pdf) ·
[실행 코드](../examples/faceted_responses.py)

이 예제의 목표 표시는 데스크톱 900px이며 임의의 모바일 축소판이 아닙니다.
모든 값은 합성이며 site마다 방법/시점당 독립 관측 6개입니다. 음영은 평균의
점별 95% percentile-bootstrap CI로, SD·동시 신뢰대·site를 합친 추정값이 아닙니다.

## 먼저 템플릿을 만든 뒤 분할

```python
p = (mp.plot(raw)
       .lineplot("time", "response", group="method", errorbar=("ci", 95),
                 n_boot=399, seed=17)
       .labels(x="Time (h)", y="Mean response (a.u.)")
       .legend(False)
       .suptitle("Response by site")
       .facet(col="site", col_order=["North", "South"])
       .size(9, 3.6))
p.legend(location="upper left", panel=0)
```

`facet()`은 완성된 단일 unfiltered 패널을 복사합니다. Layer·축·제목·reference·
명시적 panel label을 유지하며 셀 제목에 facet key를 추가합니다. 전체 그림 크기는
자동으로 늘리지 않으므로 직접 정하세요. 전체 질문은 suptitle에 두면 긴 제목이
셀마다 반복되지 않습니다. 범례도 복사하므로 예제처럼 반복을 명시적으로 숨깁니다.

```python
p.facet(row="batch", col="site", row_order=["B", "A"],
        col_order=["North", "South"], share_x="all", share_y="row")
# 또는 새 단일 템플릿에서:
p.facet(col="site", col_wrap=2)
```

같은 plot에 연속 호출하는 코드가 아니라 대안입니다. Row/col은 row-major이며
wrap은 col-only에만 적용되고 마지막 줄의 빈 칸에 padding 패널을 만들지 않습니다.
공유 축은 기본 all이며 기존 `none`/`all`/`row`/`col` 규칙을 따릅니다. Order로
선택하거나 빈 셀까지 예약할 수 있고 최대 64셀/level입니다. Key는 빈 값이 아닌
JSON 문자열·bool·유한 숫자이며 bool/숫자는 구분합니다. 표시 이름이 중복되면
오류이고 결측 facet key의 행은 제외합니다.

## 원자료와 통계

원래 `FigureSpec.data`는 그대로 두고 셀에 정확한 선택을 저장합니다.

```json
{"filters": {"batch": "A", "site": "North"}}
```

선택한 뒤 좌표와 셀별 통계를 처리합니다. 가중 행 쌍·x별 unit 재표본화·count·
정규화·KDE fit도 해당 셀 안에서 계산합니다. 축/semantic 공유가 셀 간 추정값을
합친다는 뜻은 아닙니다.

Typed category/hue 자리는 선택된 셀 전체의 level을 예약합니다. 독립 scatter/
lineplot semantic은 이름 있는 공통 domain을 사용하며, 셀 안의 index가 아니라
**원래 행 ID**의 합집합을 사용합니다. Layer가 반복돼도 중복 집계하지 않고 선택
밖 facet은 mapping 범위에서 제외합니다. 범례의 pooled mapping guide는 추가 관측이 아닙니다.

현재 방식은 **materialized grid**입니다. 이후 layer/label/축 편집은 기존 수동
layout처럼 명시적 panel index를 따릅니다. `SetData`는 저장된 selector/order
안의 관측을 갱신하지만 새로운 facet/hue/category level을 추가하지 않습니다.
Grid 구성을 바꾸려면 새 단일 템플릿에서 다시 만드세요. `.facet(...).scatter(...)`
방식의 mapping API가 아니므로 layer를 먼저 추가해야 합니다.

## Raw 그룹의 의미를 유지

`line`/`scatter`/`bar`/`errorbar`/`band`/`stripplot`/`regplot`/`rug`의 group 기반
facet을 지원합니다. Facet은 선택한 셀의 hue 자리를 자동 예약합니다. 명시적
`hue_order=[...]`도 좌표 변환·오차 검증·회귀 fit 전에 raw 그룹을 선택/재정렬/
예약합니다. 결측 group key는 제외하고 최대 64개의 구분 가능한 비어 있지 않은
JSON 문자열·bool·유한 숫자만 허용합니다.

Raw line의 입력 순서·중복/비단조 x·좌표의 결측 구간을 그대로 유지합니다. 미리
계산한 막대와 연결된 오차 열도 다시 추정하지 않습니다. 빈 그룹도 색/선/marker/
hatch·막대 dodge 자리는 소비하지만 가짜 artist나 범례를 만들지 않습니다. 실제
회귀 그룹에는 여전히 충분한 유한/서로 다른 x가 필요하고 빈 예약 그룹은 fit하지
않습니다. `hue_order=None`인 기존 raw 기본 동작은 그대로입니다.

```python
raw = {"x": [2, 1, 1, 1, 2], "y": [8, 4, 5, 2, 3],
       "method": ["B", "B", "B", "A", "A"],
       "site": ["North"] * 3 + ["South"] * 2}
p = (mp.plot(raw).line("x", "y", group="method", hue_order=["B", "A"])
       .facet(col="site").size(8, 3))
# North의 x=[2,1,1], y=[8,4,5]를 두 점의 평균으로 바꾸지 않습니다.
```

## 지원 밖 조합은 변환하지 않고 거부

- Primary Cartesian 2-D 행 기반 layer만 지원합니다. 행렬/3-D/polar/보조축/
  pie/stackplot/vector/count-map facet은 이번 범위에 없습니다.
- Raw 그룹 궤적이나 미리 계산한 막대를 자동으로 lineplot/barplot으로 바꾸지
  않습니다. 중복 x 원자료와 평균 추정의 의미는 다릅니다. Stackplot/vector/
  count-map facet은 아직 미지원입니다.
- Legacy `c`/colorbar는 미지원입니다. 공통 numeric SemanticSpec hue를 사용합니다.
- Hist는 typed HistogramSpec(`stat="density"` 등)과 공통의 명시적 bin 경계가
  필요합니다. 기존 hist 동작을 바꾸지 않습니다. KDE는 typed KDESpec 옵션이
  필요하며 셀별 bandwidth/밀도를 계산합니다. 단일값/특이 셀은 기존 규칙으로
  건너뛸 수 있습니다.
- Source layer 자체가 먼저 유효해야 합니다. 임의 query 문자열·callable·predicate
  실행·live template mapping은 지원하지 않습니다.
  [Numeric pair matrix](PAIR_GRID.ko.md)는 별도 데이터 구성 작업입니다.
  [Joint histogram 구성](JOINT_GRID.ko.md)은 별도 terminal 작업이며 facet/joint
  중첩 grid는 미지원입니다.

## JSON/action/에디터

```json
{"type": "SetFacets", "col": "site", "share_x": "all", "share_y": "all"}
```

기존 reducer/Store 경로의 dependency-free action이며 Python·CLI·에디터 raw-action
폼에서 재생할 수 있습니다. 먼저 단일 템플릿과 해당 열이 있어야 합니다. 또는 위의
편집 spec을 에디터에서 열어 셀 선택·기존 panel control로 편집할 수 있습니다.
Spec version이나 layer 종류를 추가한 것은 아닙니다.

```bash
uv run python -m examples.faceted_responses
uv run pytest -q tests/test_facets.py tests/test_raw_group_order.py tests/test_shared_semantics.py
```

선택 행 ID·독립 셀·셀별 가중 CI·공통 mapping·빈 자리·잘못된 action의 상태/이력
보존·기존 spec·JSON/action/schema/editor·PNG/PDF/SVG 재현성·global RNG 비사용을
검사합니다. 모든 facet 배치의 가독성 인증은 아니므로 [읽기 기준](VISUAL_QUALITY.ko.md)으로
최종 크기·라벨·guide·빈/특이 셀을 확인해야 합니다.
