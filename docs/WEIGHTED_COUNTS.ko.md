# 가중 countplot과 정규화 (v2)

[C06 계약](V2_SCOPE.ko.md)의 구현이다. v2 릴리스 후보 전체는 아직 진행 중이다.
[English](WEIGHTED_COUNTS.md)

```python
from pathlib import Path

import mudplot as mp

p = (
    mp.plot({"condition": ["A", "A", "B"], "frequency": [1, 2, 5]})
    .countplot("condition", weights="frequency", stat="percent")
    .labels(x="Condition", y="Declared frequency mass (%)")
)
mp.save_spec(p.spec, "counts.mplot.json")
p = mp.Plot.from_json(Path("counts.mplot.json").read_text(encoding="utf-8"))
p.save("counts.svg")
```

## 수치 계약

`weights=None`이면 기존 행 개수를 센다. 가중치 열을 명시한 `stat="count"`는
범주·hue 셀의 유효 가중치 합이다. 소수 가중치를 반올림하거나 가짜 행으로
확장하지 않는다. `probability`와 `proportion`은 선택한 분모로 나누며,
`percent`는 100을 곱한다. 위 예제는 0.375/0.625 또는 37.5/62.5이다.

모든 분모 범위는 **패널/facet별**로 적용한다.

| `normalize_scope` | 분모 |
| --- | --- |
| `None` 또는 `"all"` | 선택한 모든 유효 범주·hue의 합: 기존 기본값 |
| `"category"` | 해당 범주 안의 모든 유효 hue 합 |
| `"group"` | 해당 hue/group 안의 모든 유효 범주 합 |

뒤의 두 범위는 정규화 통계에만 적용하며, `"group"`에는 `group` 열도 필요하다.
원시 `stat="count"`의 의미를 조용히 바꾸지 않는다. figure 전체 분모나
`"hue"` 같은 별칭은 지원하지 않는다.

- 명시한 범주·hue 순서는 기여 행과 빈 슬롯을 선택하지만 원본 행 순서를 바꾸지 않는다.
- 필수 결측이나 가중치 0은 기여하지 않는다. 검증 경계의 비결측 가중치는
  유한한 비음수 숫자여야 하며 bool은 허용하지 않는다. 기존 입력·결측 처리는 유지한다.
- 데이터가 있는 선택 셀에 유효 양의 가중치가 없으면 오류이며 관측값 0으로
  만들지 않는다. 실제 선택 행이 없는 예약 facet은 표시를 만들지 않고,
  잘못된 통계 설정은 빈 facet에서도 검사한다.
- 일반 합은 보상 합산한다. 오버플로·서브노멀 경계에서는 표준 라이브러리의
  정확한 유리수 계산으로 표현 가능한 양의 정규화 값과 percent 배율을 보존한다.
  각 행을 먼저 축소해 0으로 만들지 않는다. 절대 합이 유한 범위를 넘으면 오류다.
- 신뢰구간·유의성 주장은 추론하지 않는다. 원본 측정값·알려진 단위를 보존한다.

## 명시적 log 값축 누적

log 값축에서 `stack=True`이면 각 범주의 **첫 양의 셀 질량보다 작은**
유한한 양의 `baseline`을 명시한다. 상단 좌표는 원본 누적합이다.
질량 2·3과 baseline 1이면 표시 구간은 1→2, 2→5이며 상단은 **5**이지 6이 아니다.
첫 구간은 명시한 표시 기준선에서 잘리지만, 라벨은 원본 구간 질량 2를 표시한다.

```python
import mudplot as mp

p = (
    mp.plot({"x": ["A", "A"], "g": ["u", "v"], "w": [2, 3]})
    .countplot("x", group="g", weights="w", stack=True, baseline=1)
    .yscale("log")
    .labels(x="Condition", y="Declared frequency mass")
)
p.save("log_counts.svg")
```

수직·수평과 native/log 범주 좌표에서 같다. 빈 hue 슬롯은 건너뛴다.
라벨은 원본 구간 값을 유지하고 실제 log 표시 구간의 중앙에 놓는다.
부적절한 baseline, 누적 상단 오버플로, 양의 구간 좌표 붕괴는 저장 전에 오류를 낸다.
가짜 geometry로 대체하지 않는다. baseline 단위는 선택한 통계와 같아야 한다
(예: percent이면 percentage point). 기준선을 합계에 더하거나 log 공간에서 곱하지 않는다.

count는 data-space 통계이며 axis-log count 추정은 계속 거부한다.
기존 주축·보조축 제한도 유지한다. 선형 누적은 기존 0 기준선을 유지하며
명시한 별도 표시 원점은 허용하지 않는다.

## 편집과 호환

`StatSpec.weights`와 선택적 `StatSpec.normalize_scope`가 Python·JSON·action·
고급 FigureSpec 편집에서 같은 계약을 보존한다.

```json
{"type":"countplot","x":"condition","group":"cohort","stat":{"estimator":"count","errorbar":null,"weights":"frequency","normalize":"percent","normalize_scope":"category"}}
```

새 선택 필드가 없는 기존 `0.1` 저장물을 계속 읽는다. schema 버전도 `0.1`이다.
다른 추가 기능과 마찬가지로 새 설정에는 새 reader가 필요하다. 새 scope가
미설정이면 생략해 기존 JSON 왕복에 필드를 덧붙이지 않는다. 다른 nullable 기본값은
그대로다. 필수 필드·core 의존성·callback은 추가하지 않았다.

[실행 예제](../examples/weighted_counts.py):

```sh
python examples/weighted_counts.py --out artifacts/weighted_counts
```

전체 분모의 선형 그림과 범주별 정규화 log 누적 그림을 PNG/SVG/PDF·JSON으로
명시적 opt-in smart 배치로 저장하고 재개방·상태·입력 보존을 검사한다. 회귀 검사는
`tests/test_weighted_counts.py`와 `tests/test_count_scopes.py`에 있다.
[배치 근거](review_evidence/v2_count_scopes.json)는 기능 검사와 최종 v2 검증을 구분한다.
