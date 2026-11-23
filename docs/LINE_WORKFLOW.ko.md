# 원본 선과 complete-unit 추론

[English](LINE_WORKFLOW.md) · [통계 추정량](STATISTICAL_WORKFLOW.ko.md) · [Facet](FACETS.ko.md)

원본 `.line()`과 추정 `.lineplot()`은 다릅니다. 원본 선은 선택한 관측·순서·중복 predictor·연속성 장벽을 보존합니다. Lineplot은 predictor cell마다 측정을 추정합니다. 기존 기본값은 cell별 점별 percentile CI와 numeric native 좌표이며 `native_scale=False`를 범주형 간격으로 재해석하지 않습니다.

## 과학적 추출 실험을 선언하기

```python
import mudplot as mp

p = mp.plot({
    "time": [0, 1, 0, 1], "response": [1, 4, 3, 8],
    "subject": ["a", "a", "b", "b"],
}).lineplot(
    "time", "response", units="subject", n_boot=1999, seed=17,
    errorbar=("ci", 95), error_style="bars",
    line=mp.LineSpec(resampling="unit", calibration="max_deviation", family="curve"),
).labels(title="My experiment").size(8, 5)
p.save("complete-units.svg")
```

엄격한 선택형 `LineSpec`은 `LayerSpec.line`에 저장합니다.

| 필드 | 값 | 의미 |
|---|---|---|
| predictor | native(기본), categorical | 실제 숫자/명시한 실시간 clock 또는 pooled ordinal slot |
| resampling | None, cell, unit | 기존 cell별 실험 또는 원본 trajectory 전체 추출 |
| calibration | None, percentile, max_deviation | 점별 percentile 또는 유한 grid 동시 maximum 보정 |
| family | None, curve, layer | raw curve 하나(기본) 또는 선택한 layer의 모든 curve/target |

명시한 non-None 추론 필드는 모두 CI 전용입니다. Max_deviation은 명시적 `resampling="unit"`과 `StatSpec.units`도 필요하며 family는 max_deviation에만 사용합니다. Predictor-only 선언은 기존에 유효한 구간 방법 및 None과 함께 사용합니다. Raw line은 predictor만 받고 추론 필드는 거부합니다. Band 별칭은 없습니다. `error_style="band"|"bars"`는 calibration과 독립인 표시 geometry입니다. Units는 여전히 CI 전용입니다.

### Complete-unit 반복에 포함되는 것

선택 panel/layer에서 유효한 양수 질량 원본 행을 고르고, 최초 원본 순서로 typed unit 합집합을 만듭니다. 유한 predictor trajectory의 응답이 전부 결측인 unit도 포함합니다. 한 반복마다 U개 unit 중 U번 균등 복원 추출합니다. 선택 unit의 **모든 원본 행과 짝지어진 질량**을 모든 predictor/raw curve에 같은 횟수로 반복합니다. 중복 원본 행도 물리 case입니다. Unit 내부 재추출·unit 평균·가중 확률 추출·숨은 보간·조건부 재시도는 없습니다. 불균형 trajectory의 행/질량 기여도도 그대로이며 평균은 반복한 원본 총합의 비율이지 unit 평균들의 평균이 아닙니다.

선언한 unit은 독립적으로 교환 가능한 표집 객체여야 하며 선택한 고정 grid와 결측 과정에 과학적 근거가 있어야 합니다. Informative missingness, unit 사이 의존성, 결과를 보고 고른 grid를 고치지 않습니다. Mean/median/sum 해석에는 해당 추정량의 regularity·support·moment 가정도 필요합니다. Sum은 선언한 반복-unit 총합이며 숨은 동일 가중 subject 평균이 아닙니다.

Working 좌표의 원래 추정량을 theta(c,j), complete-unit 반복 추정량을 theta_b(c,j)라 하면, 요청한 family F마다 정확하게 다음 score를 구합니다.

`D_b = max((c,j) in F) abs(theta_b(c,j) - theta(c,j))`.

Level L percent와 B 반복에서 오름차순 score의 `ceil(Fraction(L)*B/100)`번째 값을 선택합니다. 같은 working 단위에서 theta(c,j) +/- q를 만든 뒤 native 좌표로 역변환합니다. 비-studentized 경험 maximum 보정의 상위 경험 rank 질량은 L/100 이상입니다. 이는 **명목상 유한-grid bootstrap 추론**이며 연속체·유한 표본·모집단 coverage 보장이 아닙니다. Curve family는 다른 hue를 포괄하지 않고 layer family도 해당 선택 layer의 유한 curve/target 합집합에만 적용합니다. Layer·panel·facet·figure를 넘는 coverage는 없습니다.

`calibration="percentile"`은 target별 bootstrap 추정량의 type7 분위수를 따로 구합니다. 점별이지 동시 구간이 아니며 보간 tail에는 maximum score의 상위 경험 rank 질량 보장이 없습니다. Complete-unit percentile은 정확한 canonical 보간을 사용합니다. 명시적 cell/percentile은 기존 cell별 two-stage schedule과 binary64 반복값/확률 경계를 유지하며 complete-unit 실험으로 몰래 바뀌지 않습니다.

### 이름 기반 추정량·결측 support·atom

Mean/median/sum은 위 가정 아래 complete-unit percentile과 max_deviation을 지원합니다. Complete-unit min/max는 **두 calibration 모두 경험 envelope 전용**입니다. 점별 경험 bootstrap percentile envelope 또는 동시 경험 deviation envelope이며, nonregular 경고·caption을 출력하고 모집단 endpoint confidence라고 주장하지 않습니다. Count는 None만 지원합니다. 기존 점별/기술 workflow도 유지합니다. 무가중 sum은 None/SD/PI/CI, 가중 sum은 None/CI입니다. SE는 평균 전용이고 SD·PI는 추정량 불확실성이 아닌 관측 분포를 기술합니다.

추정 가능한 target마다 기여 unit이 최소2개 필요합니다. 예약 slot이나 전부 결측인 target에 추정값을 만들지 않으며 coverage target에도 넣지 않습니다. 진짜 empty 선택 facet에는 family가 없고 추론 work도0입니다. 동시 target 하나라도 반복에서 정의되지 않으면 그 family score는 +Infinity입니다. **B개를 모두 유지**합니다. 선택 rank가 무한이면 유한 band 전체를 거부하고, 유한 rank이면 undefined 횟수를 보고합니다. Complete-unit percentile은 모든 target이 B번 모두 정의되어야 하며 아니면 transaction 전체를 거부합니다. Finite-only percentile·B 변경·전부 결측 topology unit 제거·support가 나올 때까지 재추출은 없습니다.

진짜 경험 atom은0폭일 수 있지만 모집단 불확실성이0이라는 뜻은 아닙니다. 서로 다른 canonical endpoint가 native 반올림에서 겹치면 가짜 확신 대신 오류로 거부합니다.

공유 cell/C07 역-log effect 경계도 양의 working 구간이 같은 native endpoint로
반올림되면 거부합니다. 이 정확성 수정으로 기존 경로의 가짜0폭 구간이 새로
거부될 수 있지만 표본·working 추정/percentile·추출 schedule은 바꾸지 않습니다.
Working 폭이 진짜0인 경험 atom은 계속 유효합니다.

## 좌표·topology·원본 식별성

가로에서도 x 인자는 predictor, y는 측정입니다. 실제 primary/y2 및 v/h의 숫자·범주·명시한 실시간 clock 경로는 각 target 축을 사용합니다. Native 숫자/date 구조 grid는 응답 결측을 버리기 **전에 raw curve별로** 만들고 명시한 예약을 추가합니다. A의 x=[1,3], B의 x=[2,4]는 각각 연결된 불규칙 선을 유지합니다. 다른 curve의 관측을 결측 vertex로 만들지 않습니다. 같은 curve 안의 unit들은 그 curve의 구조 합집합에 기여합니다. Categorical은 pooled 선언 ordinal slot을 쓰며 선택 group의 빈 slot은 진짜 gap입니다.

명시적 결측 응답과 grouped missing cell은 기존 추정값·seed 순서·admission을 바꾸지 않고 경로/ribbon을 끊습니다. Raw의 결측 좌표/semantic key는 장벽이지만 다른 알려진 role의 행은 가짜 결측 관측이 아닙니다. Raw line은 lineplot처럼 보이도록 원본을 정렬·평균·중복 제거하지 않습니다.

`stat_scale="data"`는 log 표시에서도 raw 값을 추정합니다. 적용 가능한 log 응답의 `stat_scale="axis"`는 표시 base와 무관하게 log10 working 좌표에서 계산한 뒤 역변환합니다. Log 관측/endpoint는 양수여야 합니다. Log-working sum/count를 곱/거듭제곱으로 바꾸지 않고 거부합니다. 달력 응답은 canonical UTC-day native 단위이며 달력 sum/count도 거부합니다. Predictor clock이 숫자 응답을 달력으로 바꾸지 않습니다. Callback이나 다른 primitive scale의 통계 의미 추측은 없습니다.

Persisted 명시적 추론 필드는 NEW typed unit identity를 선택합니다. True와1, False와0은 다르고 숫자1과1.0은 같습니다. 빈 문자열을 포함한 opaque string ID는 유효하고 필수 None/NaN은 paired 행과 함께 제외합니다. Omitted-LineSpec 및 predictor-only 추론은 기존 C07 unit identity와 수치를 유지합니다. 저장한 non-None 필드로 결정하며 호출 keyword 유무는 사용하지 않습니다. 원본 열/ID는 JSON·action·재열기 후에도 보존합니다.

Complete-unit은 로컬 명시적 PCG64를 사용하고 최초 선택 unit 순서, replicate-major 균등 int64 draw, 최대1M active choice chunk를 따릅니다. Sort·DPI·ribbon style·guide 편집은 stream을 바꾸지 않습니다. Current/minimum의 실제 실행 case가 parity 근거이며 모든 미래 NumPy/architecture를 보장하지 않습니다.

## Raw 매핑과 figure 소유 guide

Raw line은 기존 `SemanticSpec`으로 독립 hue·size·style을 지원합니다. Hue는 실제 색, size는 main stroke pt, style은 실제 marker/dash입니다. 같은 raw domain이라도 mark에 따라 body 윤곽 pt·point 지름 pt·line stroke pt이므로 서로 같은 단위가 아닙니다. Guide는 실제 native 문맥을 상속하고 소유 trait만 바꾸며0 stroke에서도 독립 fill/glyph를 유지합니다. 숫자 hue의 정규화 nondata colourbar·정확한 raw label·상수 midpoint도 공유합니다.

```python
mapping = mp.SemanticSpec(hue="condition", size="precision", style="method",
                         markers=["o", "s"], scale_id="original-rows")
p.line("time", "response", semantics=mapping)
p.shared_guides([mp.SharedGuideSpec("original-rows", location="outside right",
                                  title="Shared raw mapping")])
```

`SemanticSpec.scale_id`가 **유일한 저장 membership authority**입니다. 엄격한 `SharedGuideSpec(scale_id, location="outside right", title=None, frame=False, bbox_to_anchor=None)`은 예약 empty facet을 포함하여 해당 이름의 호환 저장 member/template 모두를 대상으로 합니다. 이름마다 요청은 하나입니다. Panel-ID 목록·암묵적인 label 일치·FacetGuide 별칭·두 번째 live store는 없습니다. 별도 guide가 필요한 family는 다른 scale_id를 사용합니다.

`FigureSpec.shared_guides`는 선택형 omit-None list입니다. `Plot.shared_guides(typed_or_dict_list_or_None)`은 전체 authoritative `SetSharedGuides` action입니다. Outside right/top/bottom 또는 신뢰하는 유한 [x,y] figure-fraction anchor를 사용하며 anchor를 clamp하지 않습니다. Panel LegendSpec은 바꾸지 않습니다. 저장한 semantic legend/colourbar intent를 유지하면서 일치하는 소유 guide만 억제하고 모든 matching member의 effect별 실제 문맥을 모읍니다. Dataset label legend와 다른 scale은 남습니다. Mapping/label 충돌·중복/소유자 없는 요청은 atomic하게 거부합니다. Empty 선택 자료에 가짜 artist를 만들지 않습니다. 마지막 저장 소유자를 제거하려면 요청부터 비워야 하며 호환 latent live template도 소유자입니다.

Saved/local facet view가 권위 있는 현재 상태입니다. Local 편집은 해당 셀만, 명시적 SetFacetTemplate은 frozen cell 모두의 override를 대체하며 선택 행·N13 ID/nesting/placement·scale membership을 보존합니다. SetData/reopen은 몰래 재확장하지 않습니다. Live cell 제거 시 불완전 live transaction 대신 saved view로 남깁니다. 두 editor에는 채워진 layer·whole-template·shared-guide authoritative JSON control과 기존 undo/redo/download/reopen이 있습니다. 이 increment로 전체 F01/F02/G01이 끝나는 것은 아닙니다.

## 유한 NEW 추론 자원

Persisted 명시적 추론 필드만 D01 NEW work를 선택합니다. Raw 매핑·predictor-only·omitted·no-inference·SD/SE/PI에는 설명 없는 새 추론 row/cell/work 상한을 붙이지 않습니다. Guide만 편집해도 옛 layer가 NEW가 되지는 않지만, 매 render는 저장한 실제 NEW invocation을 모두 청구합니다.

Complete-unit layer는 선택 trajectory N<=10000행, 구조/예약 R<=4096 slot, 추정 가능 K<=4096 target, 기존 B<=100000입니다. RNG/native 이전에 보수적 `W_unit=B*(U+N+K)<=2000000000`을 승인합니다. NEW-only figure ledger는 실제 W_unit 호출과 명시적 cell/percentile의 C07 실제 unit/case work 및 bootstrap estimator reduction을 합칩니다. 상한은2000000000이고 component별로 구분하며 CPU/SLA 단위가 아닙니다. 알 수 없는 cell work는 다음 chunk 전에 승인하며 prefix/축소 CI를 공개하지 않습니다. C07 local used/work 상한과 수치 kernel은 그대로입니다.

NEW 추론 working-state의 보수적 허용량은268435456 byte입니다. 실제 product 구조와 canonical int/Fraction bit bound로 plan·heap/list 여유·control·active choice/scratch·넓은 임시 product·현재 score/endpoint·이미 남은 NEW summary를 포함합니다. 정확한 bounded smaller-tail heap은 필요한 order statistic만 유지하고 B×family/target 행렬이나 float 유한 score를 저장하지 않습니다. 끝난 heap/plan은 해제합니다. Source-data/native/RSS sandbox가 아닙니다. 기존 semantic row/curve/category, facet64, panel256, layer1024,40M pixel 상한은 유지하며 D03–D06의 다른 metric으로 바꾸지 않습니다.

전체 v2 release 전까지 schema0.1/package1.1.0입니다. 기존 dependency/provider/security floor와 Linux-only 검증 범위를 유지하며 다른 OS·물리 인쇄를 주장하지 않습니다.
