# 원자료 통계: 가중 추정·공유 역할·live view

`barplot`·`pointplot` 및 지원하는 점별 `lineplot` 경로는 원자료와 이름 기반 `StatSpec`을 저장합니다. `.bar()`는 사전 계산 값 primitive로 유지합니다. 이 문서는 기존 C07 점별 동작이며 [원본 선·complete-unit 추론](LINE_WORKFLOW.ko.md)은 유한 grid 보정을 명시적으로 추가합니다. 임의 callable을 JSON에 숨기거나 무제한 upstream 동등성을 주장하지 않습니다.

[English](STATISTICAL_WORKFLOW.md) · [실행 가능한 합성 자료 예제](../examples/statistical_workflow.py)

```sh
python examples/statistical_workflow.py artifacts/v2_c07/examples
python -m mudplot render artifacts/v2_c07/examples/statistical_live_dates.mplot.json exact.png
```

## 추정량·구간의 과학적 의미

| 가중 estimator | 값 | 지원 errorbar |
|---|---|---|
| mean | sum(w*x)/sum(w) | None, SD, SE, PI, CI |
| median | 가중 경험 CDF의 관측 LEFT 역함수 Q(1/2) | None, SD, PI, CI |
| min/max | 양수 가중 선택 관측의 실제 극값 | None, SD, PI, CI |
| sum | 정규화 평균이 아닌 가중 총합 sum(w*x) | None, CI |
| count | 양수 선택 질량; 무가중이면 관측 행 수 | None |

기존 무가중 조합은 무가중 sum None/SD/PI/CI를 포함하여 유지합니다. SE는 **평균 전용**이며 평균 SE를 median/sum/극값의 불확실성으로 바꾸어 부르지 않습니다. Count CI를 만들지 않습니다. Median/극값 주변의 SD·PI도 관측 분포의 기술 구간이지 해당 추정량의 신뢰구간이 아닙니다.

- SD는 관측 표본의 퍼짐입니다. p=w/sum(w)에 대해 reliability 표본 분산 `sum(p*(x-mu)^2)/(1-sum(p^2))`를 사용합니다. 거의 같은 float 둘을 빼 분모를0으로 만드는 대신 canonical 정수 질량으로 계산합니다.
- SE는 SD/sqrt(n_eff), 물리 원본 행의 Kish n_eff=1/sum(p^2)입니다. 독립 가중 행 근사이며 cluster용 analytic SE가 아닙니다. 같은 값의 행도 tie 결합 **이전**에 독립 case입니다.
- PI는 관측 분위수입니다. 무가중은 기존 type7을 유지합니다. NEW 가중 PI는 LEFT Q(p)=min{x:CDF(x)>=p}이며 선언한 **percent**에서 `L=Fraction(level); p=(100-L)/200; upper=1-p`를 정확하게 만듭니다. x=[0,10,20], w=[1,38,1], level95의 결과는 정확한1/40·39/40 knot를 포함한 **[0,10]**입니다. float tail을 먼저 반올림하지 않습니다. 같은 가중치라도 무가중 type7과 다를 수 있으며 숨은 method 전환은 없습니다.
- CI는 요청한 추정량의 percentile bootstrap입니다. 원래 case를 균등 추출하고 값·가중치를 함께 옮깁니다. 가중치를 추출 확률로 쓰지 않습니다. Units는 독립 unit을 추출한 뒤 선택 unit 내부 행을 다시 추출하며 unit 평균을 미리 계산하지 않습니다. Units는 CI에만 사용합니다.

Unit ID는 표시 범주 라벨이 아닌 opaque 식별자이므로 빈 문자열을 포함한 모든 문자열을 허용합니다. 필수 None/NaN ID는 짝지어진 행과 함께 제외합니다. NEW는 bool True와 숫자1을 구별하되 숫자1과1.0의 동일성은 유지합니다. 일반 표시 category/role의 비어 있지 않은 문자열 규칙은 그대로입니다.

SD/SE level은 양수 배수(기본1), PI/CI는 coverage percent(기본95)입니다. None은 구간을 끕니다. 관측/독립 unit이 부족한 cell은 추정값을 유지하고 경고와 함께 구간을 생략하며 bootstrap work는0입니다. 진짜 atom의 구간은 접힐 수 있지만 서로 다른 canonical endpoint가 native 반올림으로 구별되지 않으면 오류로 거부합니다. 가짜0폭 불확실성을 만들지 않고 큰 정수 전체를 금지하지도 않습니다. 구간은 중심을 포함하도록 clip하지 않습니다.

## Canonical 값·행 보존

정렬·보간·SUM/MEAN·moment 계산은 binary64 좌표 변환 **이전**의 유한 정수/binary-float와 정확한 정수 질량을 사용합니다. MaxAbs 정규화로 관측한 잔차를 지우지 않습니다. 예를 들어 [1e300,-1e300,1e-300]의 합은 표현 가능한1e-300을 유지합니다. Letter-value와 같은 순수 canonical 경계를 재사용하며 비공개 CDF를 복제하지 않습니다. 요청한 결과가 유한 native 범위를 벗어나면 오류이며0/epsilon/uniform-weight 대체값을 넣지 않습니다. 모든 동적 범위의 native 좌표가 완전 정확하다는 약속은 아닙니다.

필수 결측과 가중치0은 짝지어진 case로 제외하고 음수/잘못된 비유한/bool 가중치는 거부합니다. 원본 열·행 ID·순서·clock·선언 단위는 바꾸지 않습니다. NEW 범주/역할은 True와1을 구별합니다. 표시 매핑이 clip되어 같아져도 서로 다른 raw role tuple의 통계를 합치지 않습니다. 공유 정규화 domain에서만 원본 행 ID를 중복 제거하며 실제 cell/그려진 case/bootstrap 반복은 제거하지 않습니다.

## 역할·물리 단위

```python
cfg = mp.SemanticSpec(hue="temperature", hue_kind="numeric",
                      size="precision", sizes=[2, 4], style="method",
                      markers=["D", "^"], scale_id="original-rows")
p.barplot("dose", "response", weights="weight", estimator="median",
          errorbar=("pi", 95), semantics=cfg)
p.pointplot("dose", "response", semantics=cfg, errorbar=None)
```

Typed SemanticSpec·dict·저장 JSON은 같은 엄격한 정책입니다. 독립 mapped hue와 두 번째 legacy group/hue-order는 충돌하지만 legacy group은 독립 size/style과 공존할 수 있습니다. 실제 매핑 소유 속성을 scalar로 덮으면 거부하며 error/cap/다른 stroke 속성은 독립입니다.

- HUE: bar BODY fill 및 실제 point/연결선 색. 숫자 hue는 기존 nondata[0,1] colourbar와 정확한 raw label·상수 midpoint swatch를 사용합니다.
- SIZE: **bar BODY 윤곽 stroke pt**와 **pointplot 실제 marker 지름 pt**입니다. Lineplot은 MAIN LINE stroke pt입니다. Bar 너비/높이/면적/질량이나 오차·연결선 굵기가 아닙니다.
- STYLE: 실제 bar dash, point glyph와 연결 dash입니다. 저장한 named cycle은 충분히 구별 가능해야 합니다. Dash-only bar에 쓰지 않는 marker 용량을 요구하지 않습니다. 가짜 관측/원형 bar 대용 범례/전역 문자열 label 중복 제거를 하지 않습니다.

맞는 scale_id는 같은 RAW domain을 공유하되 계열별 단위/guide는 유지합니다. Zero/no-line은 독립 fill/glyph/segment/marker edge를 최소 renderer에서도 보존합니다. Guide는 실제 native main 문맥의 독립 zero/nonzero 연결 stroke·BODY fill/edge·실제 glyph/지름을 상속하고 해당 guide가 소유한 역할만 바꿉니다. Data 좌표를 갖지 않으며 dataLim을 바꾸지 않습니다.

## Clock·축·고정 view

가로에서도 x는 category/predictor 인자이고 y는 측정입니다. Bar/point는 primary 또는 실제 선언한 y2를 v/h로 사용합니다. 가로 y2의 범주는 y2, 측정은 공유 x에 위치합니다. Numeric/date native slot·order/dodge/gap·inverted limits·DPI/layout·다른 layer는 공통 geometry를 사용합니다. 단일 date의 선언 slot은 epoch 크기에 따라 frame이 늘어나는 일을 막고 측정 limits는 바꾸지 않습니다.

Log 측정은 관측/결과/endpoint가 양수여야 하고 bar는 명시적인 양수 baseline을 요구합니다. Data 통계는 raw를 계산해 log에 표시합니다. Axis 통계는 mean/median/min/max를 **log10**에서 계산·역변환합니다. N12 base2 표시 설정이 통계 정의를 바꾸지 않습니다. Axis/log SUM/COUNT는 곱/거듭제곱으로 해석하지 않고 거부합니다. Raw scale의 symlog/asinh/logit에서 새로운 통계적 의미를 추측하지 않습니다.

Category clock과 measurement clock은 다릅니다. 달력 응답 mean/median/min/max/구간은 canonical UTC day, SD/SE 폭은 기간입니다. 달력 SUM/COUNT는 거부합니다. NEW 달력 bar는 temporal 숫자 bounds처럼 명시적인 canonical-day baseline을 사용하며 초/밀도 단위로 몰래 바꾸지 않습니다. 기존 비확장 요청은 clock이 있다는 이유만으로 NEW가 되지 않습니다.

Facet/live recipe는 고정 selector·ID·해결한 slot을 유지합니다. 셀별 ReplaceLayer는 로컬이며 명시적 whole-template transaction은 populated/예약-empty 모두에서 로컬 override를 대체합니다. 순수 JSON load는 저장한 recipe와 선택된 materialized view·로컬 override를 그대로 읽습니다. Render나 편집기 preview 재열기는 저장한 관측·seed로 요청 통계를 결정적으로 다시 계산할 뿐 whole-template 교체를 실행하지 않습니다. 그리지 않는 recipe를 전체 원자료를 그리는 물리 layer로 세지 않고, 실제 선택 view/옵션을 commit 전에 검증합니다. 제외된 잘못된 행은 가짜 관측이 아닙니다. Source refill·ratio·N13 nesting/placement도 같은 graph를 사용합니다.

명시적 N13 geometry나 저장 panel ID는 기존 단위 공유 gate를 적용합니다. 가중 SUM 응답은 value×weight-mass로 평균/원자료 value나 COUNT mass와 다릅니다. 호환 가중 total끼리, 무가중 sum과 value끼리는 공유할 수 있으며 category 축 공유가 응답 단위를 바꾸지 않습니다. 기존 no-N13 gate는 유지합니다. 새 물리 단위 API나 열 이름에 따른 단위 추측은 없습니다.

보조 y축에 실제 데이터가 그려지면 통합 범례를 그 보조축에 배치하여 두 축의
마크 위에 표시합니다. 보조축이 비어 있으면 기본축이 범례를 유지합니다.
네이티브 `best`는 빈 영역을 보장하지 않으며, 명시적 위치 지정과 그림 비율
좌표 드래그를 사용할 수 있습니다.

## C07 NEW에만 적용되는 자원 정책

Persisted NEW predicate는 새 가중 추정/구간 조합, bar/point SemanticSpec, 또는 구체적으로 새로 허용한 bar/point target-axis 경로의 합집합입니다. 기존 weightedmean None/CI·unitsCI·countplot mass·무가중/plain/기존 semantic dense line은 해당 필드나 산술 수정만으로 새 상한을 받지 않습니다. 진짜 새 line 통계는 predictor×raw-role 점별 cell을 세며 기존 curve vertex를 제한하지 않습니다.

NEW layer는 **선택 양수·완전 물리 원본10000행 AND 그리는 점별 cell256개**까지입니다. 기존 범주형64 level은 연속 숫자의 서로 다른 값64개 제한이 아닙니다. Bootstrap100000/facet64/panel256/layer1024/40M pixel 및 floor는 유지합니다.

Active random/sample array는 최대1M element이고 원래 case multiplicity를 compact하게 저장하여 O(rows+units+n_boot) 공간과 원래 local seed schedule을 유지합니다. Singleton/1M보다 큰 기존 unit도 행을 버리지 않고 stream합니다. NEW CI의 **실제 unit-choice+sampled-case work 합계는 layer별2,000,000,000**입니다. Ordinary chunk 크기를 생성 전에, unit choice를 draw 전에, 뽑은 multiplicity의 row work를 row chunk 전에 승인합니다. 초과하면 native artist/editor commit 전에 요청 전체가 실패합니다. Prefix CI·낮춘 n_boot·masked resample·가중확률 추출은 없습니다. Actual-work 승인은 seed에 따라 달라질 수 있습니다. 기존 경로에는 새 work/row/cell 상한을 붙이지 않습니다.

Ordinary 최대가1B case여도 hierarchy는 그렇지 않습니다. 10000행/불균형5001 unit은 한 반복25,005,000행·100000반복에서 uncapped2.5005e12 case를 요청할 수 있습니다. 유한 메모리/work 정책이지 SLA/RSS/보편적 지연시간 약속이 아니며 figure 전체 곱셈도 숨기지 않습니다.

D01 complete-unit 상한·저장 선언 identity 경계·NEW-only figure/working-state ledger는 [line workflow](LINE_WORKFLOW.ko.md#유한-new-추론-자원)에 따릅니다. Omitted/predictor-only 또는 저렴한 raw/no-inference view를 재분류하거나 기존 C07 local kernel/정책을 대체하지 않습니다.

## 실제 소비자 workflow·근거

두 로컬 UI의 등록 layer control과 채워진 ReplaceLayer JSON은 같은 reducer/candidate admission을 사용합니다. 잘못된 과학/자원 요청은 승인 Spec/현재 완성 PNG/history를 보존하고 CLI 실패도 이전 완성 출력을 남깁니다. 실제 undo/redo·save/reopen·재열기 후 편집·PNG/SVG/PDF는 source test와 구별해 검증합니다. DOM의 실제 표시 PNG decoded RGBA가 현재 revision과 같은지 확인하며 URL/placeholder만 검사하지 않습니다. Rust PNG 다운로드는 기존 capped preview이고 같은 다운로드 JSON의 설치 CLI/API가 정확한 요청 DPI를 만듭니다.

실행 예제·current/minimum source/installed/native/Rust/static/generated/optional-dependency 거부 Python-S·실제 UI·실제 offline PGF/glyph/citation/URI는 별도 cohort입니다. 실패/수정/원래 artifact/provider 제한은 합산·재분류하지 않습니다. 이 workflow는 전체 F01/F02/D01/G01/E01/Q01/DOC01/REL01/v2 완료가 아닙니다.

`examples/statistical_workflow.py`는 명시적인 **합성 자료**입니다. 공유 표에는 raw hue/size/style tuple별 결정적 응답 차이를, live 표에는 bool True와 숫자1에 서로 다른 양수 응답 배율을 선언합니다. 같은 원본 ID·가중치·표를 모든 mark가 사용하며 display jitter나 mark별 전처리로 곡선을 벌리지 않습니다. 여섯 추정량의 손계산 기준 자료는 별도로 유지합니다.
