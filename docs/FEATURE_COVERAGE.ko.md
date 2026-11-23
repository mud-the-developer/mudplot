# Matplotlib / Seaborn 기능 지원 범위

*[English](FEATURE_COVERAGE.md)*

## 목표와 비교 기준

목표는 Matplotlib·Seaborn이 제공하는 **그래프와 통계 시각화의 사용 범위**를
mudplot에서도 지원하는 것입니다. 동시에 논문용 기본 스타일, 편집 가능한 spec,
재현 가능한 출력을 유지합니다. **그래프 이름이 있다는 것만으로 기능이 동등한
것은 아닙니다.**

이 표는 통계/native subset과 agent 품질 개선을 포함한 **1.1.0 로컬 후보의 기능 기준선**입니다.
v2 범위·인수조건·진행은 [V2 범위](V2_SCOPE.ko.md)에 기록하며, 미구현 v2 항목을
현재 지원으로 집계하지 않습니다. 공식 Seaborn **0.13.2**, Matplotlib **3.11.2** 문서와 정적으로 비교했습니다.
이 버전은 기능 비교 기준이며 자동 의존성 업그레이드를 뜻하지 않습니다.
v1.1 보안 예외는 Python >=3.11 / Matplotlib >=3.8 / NumPy >=1.23.5,
렌더 Pillow >=13.0.0을 사용하며 Python API/JSON/기본 렌더 계약은 유지합니다.

판단 근거는 [layer registry](../mudplot/capabilities.py),
[직렬화 모델](../mudplot/spec.py), [공개 builder](../mudplot/api.py),
[renderer](../mudplot/_render.py)·[공통 통계 effect](../mudplot/_estimate.py)입니다.
[호환성 정책](COMPATIBILITY.ko.md)도 함께 적용합니다.

- **부분 지원:** 관련 그림은 그릴 수 있지만 주요 옵션·통계 계산·구성이 빠짐.
- **미지원:** 전용 선언적 기능이 없음. 사용자의 전처리·수동 조합은 구현으로 세지 않음.
- **Python 직접 사용:** 반환된 Matplotlib Figure/Axes에서 가능하지만
  spec·undo/redo·JSON·CLI·editor 왕복에는 반영되지 않음.

현재 등록 layer는 bounded native stem/stairs/eventplot/broken_barh를 포함해
**41종**입니다. 기능명 개수만으로 지원률을 계산하지 않습니다.
아래 표는 주요 격차이며 upstream의 모든 인자를 열거한 완전한 명세는 아닙니다.

## 1. Seaborn 기능 비교

| 기능 | 현재 상태 | 부족한 범위 |
| --- | --- | --- |
| `scatterplot` | 부분: 독립 hue/size/style·공유 domain·명시 숫자 hue colourbar/정확한 상수·point 윤곽·기존 시간 경로 | 넓은 F01 계열 adapter/공유와 최종 고정 검증은 계속 필수이며 전체 동등성 아님 |
| `lineplot` | 선언 complete-unit percentile / 유한-grid max-deviation curve·layer family, numeric/date/categorical·v/h/y2, 원본 line hue/size/style·gap·saved/live facet·scale_id 소유 figure guide | 명목 선택-grid bootstrap이며 극값은 경험 envelope; 연속체/모집단 coverage나 전체 upstream 동등성 아님. 넓은 F01/F02/G01은 별도 |
| `histplot` | 단변량 가중 통계와 명시 Histogram2DSpec/BivariateBinsSpec: 6가지 셀 통계·불균등 실제 경계·빈 내부 정규화·같은 집계 전 코호트 전체 KDE, 기존 경로 보존 | 원자료/day 폭·면적만 사용하고 KDE를 count 높이로 바꾸지 않음. [과학/자원 계약](DENSITY_FIELDS.ko.md), 최종 동일 artifact 검증은 별도 |
| `kdeplot` | Gaussian/product-Epanechnikov H·공통-grid 1D layer/stack/fill·실제 결합 CDF·명시 유한 전체-model HDR와 기존 조건부 HDR; actual v/h/y2/clock·log10 fit/Jacobian 단위 | 방사형 커널 오해·2D stack 높이·임의 callback·보편적/원본 모집단 보장 없음. [전체 계약](DENSITY_FIELDS.ko.md), 최종 검증은 별도 |
| `ecdfplot` | 가중/tie 우연속 proportion/percent/count·strict 보완·raw 역할/실제 knot 마커; 명시 ecdf2d는 모든 매듭과 strict OR 보완·actual v/h/y2/clock 보존 | 유한 저장/query 경계가 분모를 바꾸지 않으며 생존/censoring/추론 없음. [계약](DENSITY_FIELDS.ko.md), 최종 제품 검증은 별도 |
| `rugplot` | D07 구현: x/y/y2 rug·axes-fraction 높이·v/h·관측 날짜/log·group/facet·공유 raw-row hue/stroke/dash | 기존 semantic/자원 상한·유한 named dash 계약 유지. 가중치/추론/point-marker 재해석 없음. 최종 고정 제품 검증은 별도 |
| `stripplot` | 부분: 인수한 C01 order/dodge/native/log/날짜/jitter와 독립 공유 hue/size/style adapter | C01 제한 인수는 종결, 다른 F01 계열·최종 제품 검증은 계속 필수 |
| `swarmplot` | C02 구현: 실제 named glyph·공유 hue/size/style·날짜/native/log/v-h/y2·호환 cross-layer scope·명시 live-template transaction | 기존 layer 2000행 유지, 새 panel/scope 물리 instance4000 상한·보수적 glyph/stroke packing·정확한 과밀 경고; 전체 검증 근거는 별도 |
| `boxplot` / `bxp` | C03 구현: 원자료 중앙값 bootstrap CI·column 참조 summary·최종 body cap 비율·typed hue별 component·공유 hue/body-stroke/flier-style·date/native/log/v-h/y2/facet/live | 제공한 mean/CI/flier만 표시, quartile에서 복원/bootstrap·임의 kwargs 없음. Advanced 상한cell256·source행10000 AND flier값10000. [전체 계약](BOX_WORKFLOW.ko.md), 검증 근거는 별도 |
| `violinplot` | C04 구현: 명시 paired 다중 hue 반쪽·mode별/정확한 hue별 native component·가중 Gaussian/inner/질량 정규화·공유 hue/BODY-stroke/style·date/native/log/v-h/y2/facet/live | [유한 과학/소유권 계약](VIOLIN_WORKFLOW.ko.md). Callback/임의 kernel·kwargs/새 nonlinear 통계 없음. Advanced 선택행10000·그리는 profile256·범주형64이며 연속 숫자값64 제한 아님. 전체 검증 근거는 별도 |
| `boxenplot` | C05 명시 범위: LEFT 상대 가중 분위수·정확한 경험 band/tail 질량·Kish 깊이·rank/side/raw-hue 구성 요소·BODY 색/윤곽pt/dash+실제 flier glyph·clock/native/log/y2/live/N13 | CI/KDE/가중 행 복제 추정·임의 kwargs·깊이 상향 없음; 깊이<=32 및 유한 원본/effect 작업 admission |
| `pointplot` | C07 명시 범위: 유한 가중 통계·정확 LEFT PI·canonical moment/산술·typed hue/실제 지름/style·date/native/log/v-h/y2·선택 공유 domain/live 편집 | 평균 전용SE·count 구간 없음·axis-log/calendar sum/count·비선형 통계 추측 없음. NEW-only 자원 상한, 기존 dense-line/weight/unit 승인 유지. [계약](STATISTICAL_WORKFLOW.ko.md) |
| `barplot` | C07 명시 범위: 가중 통계/짝지어진CI·정확 percent PI·BODY 윤곽pt/style·date/native/log/v-h/y2/live; precomputed bar 별도 | 너비/높이/질량은 SIZE가 아님. 양수 log/NEW달력 canonical-day baseline·유한 method/실제 소유 충돌·actual-work 승인. [계약](STATISTICAL_WORKFLOW.ko.md) |
| `countplot` | 부분: 전체 분모 count/비율/percent·native/log 범주 간격·명시적 log baseline·방향/gap/선형 stack/라벨 | 가중 count·log 값축 stack/stat_scale·추가 정규화/semantic/date |
| `regplot` | 다섯 모델의 상대가중 paired-case percentile·전체 basis/joint/two-stage partial·독립 fit/scatter 물리적 point 제어·명시적 원행 query 예측 | 명목상 점별 mean/operator 불확실성; precision/frequency/동시/prediction method나 광범위 F01/F02/G01 완료 아님. [과학/API/자원 계약](REGRESSION.ko.md) |
| `residplot` | 기존 residual flag·실제 raw/수학적 이진 deviance·사상한 mean 구간·독립 FULL-pipeline trend·원행 ID 유지 | 무한 진단 clip·fixed-fit trend·묵시 hold-out·인과 주장·날짜 duration 위장 없음. [범위](REGRESSION.ko.md) |
| `heatmap` | 마스크·사용자 주석·회전·정사각 셀 및 M01 색 보정 | P01 색 보정으로 대체할 수 있으나 M01 색 보정과 동시 사용 불가. [범위](HEATMAP.ko.md) |
| `clustermap` | 행/열 트리, 공통 관측 특성 결측 처리, 제공 condensed 거리, 정렬된 범주 트랙/범례, 원본 ID 기반 절단·선택 편집 | SciPy 선택 의존성, 보간/임의 callback/연속 트랙 자동 구간/공유·보조 축 없음. [범위](CLUSTERMAP.ko.md) |
| `relplot`/`displot`/`catplot`/`lmplot` | 기존 mark/action 기반의 제한된 빌더, live template, 셀별 추론과 원시/의미/스칼라 figure guide | 임의 callback이나 upstream 전체 동등성은 없음. [지원 종류](FACETS.ko.md) |
| `FacetGrid` | 저장 selector, 명시적 live template, 빈 예약 셀, 공유 축과 중첩 배치 | 임의 reactive map은 아님. [Facet 제한](FACETS.ko.md) |
| `PairGrid`/`pairplot` | 전체/아래 삼각형, 산점도와 typed histogram/KDE/ECDF 대각선, 실제 가중 행, 공유 의미 범위와 N13 중첩 | upstream 객체 전체가 아닌 명시된 [pair 범위](PAIR_GRID.ko.md) |
| `JointGrid`/`jointplot` | 쌍별 가중 histogram/KDE/ECDF, 스칼라 c/의미 산점도, 그룹 bin, 실제 측정 y2 연결과 N13 중첩 | 데카르트 중심 하나와 같은 관측의 주변 분포. [지원 역할](JOINT_GRID.ko.md) |
| 테마·팔레트·범례·despine | 이름 있는 테마·글자 크기 context, LCH 및 사용자 범주 팔레트, 범례 열·네이티브 handler | 임의 콜백이나 전역 설정 변경 없음 |
| `seaborn.objects` | 유한한 [좌표·통계·배치·축척 합성](COORDINATE_PIPELINE.ko.md) | 동일 object API는 미지원, 소스 검증은 별도 |

deprecated `distplot`, 온라인 예제 데이터 다운로드, notebook 팔레트 widget,
전역 상태 alias는 그래프·통계 기능 동등성의 선행 조건이 아닙니다. 이런 utility
개수로 그래프 지원률을 부풀리거나 격차를 숨기지 않습니다.

### 독립 lineplot 매핑

같은 strict SemanticSpec/열 키워드로 원본 역할 tuple별 곡선/predictor 셀을
나누며 숫자 clip이 서로 다른 곡선을 합치지 않습니다. 기존 named 추정·점별 구간/
가중-unit CI 유지, 전체 path 추론이 아닙니다. Sizes는 main stroke 두께 points이지
marker 면적/불확실성 크기가 아닙니다. 독립 filled marker·선택적 서로 다른 named
dash와 엄격한 override, 역할/통계 결측·0행 짝처리·v/h/정렬/raw/log-fit/면 결측을
유지합니다. Line/scatter shared ID는 geometry별 비데이터 guide를 표시하고 label/
limit을 보존합니다. 행10000/원본곡선256/level64/충분한 glyph/dash,48개 수식/도형/
bootstrap/타입/core/editor/JSON/export/RNG 테스트입니다. Raw line/date/y2/colorbar/
넓은 추론은 남고 [자동 facet materialization](FACETS.ko.md)은 별도 범위로 지원합니다.
[실행 비교](../examples/line_semantics.py).

### 이름 기반 figure 공통 scatter 척도

SemanticSpec.scale_id로 figure 범위를 정하고 None은 기존 layer-local입니다.
설정이 맞는 member의 선택 row ID를 중복 없이 원 table 순서로 모으며 가짜
관측을 추가하지 않습니다. 역할/종류/순서/범위/지름/marker/숫자 hue cmap은
같아야 하고 legend만 달라도 됩니다. 패널 결측 좌표가 색 슬롯/크기/marker/
숫자 범위를 초기화하지 않으며 다른 이름은 독립입니다. 이름당 범주 색 block은
한 번만 예약하고 기존 항목보다 앞에 고정합니다. 비데이터 guide는 pooled 범주의
calibration이며 패널당 한 번, dataset label은 따로 유지합니다. Pooled 행/level/
marker 한계와 member간 모호한 라벨도 개별 검사 뒤 숨기지 않고 검증합니다.
36개 테스트로 범주/숫자 매핑·mask/합집합/순서/중복·한계/cmap/타입 충돌·기존
palette 분리·범례 규칙/상수/subnormal·기존 JSON/core/editor/export/RNG를
검증했습니다. [자동 facet materialization](FACETS.ko.md)은 별도 범위로 지원하며
line 확장은 위에 설명했습니다.
[실행 예제](../examples/shared_semantics.py).

### 독립 scatter 매핑 범위

SemanticSpec/dict 또는 hue/size/style 열 키워드로 선택하며 기존 호출은 유지합니다.
Hue는 기본 범주형/숫자 명시, size는 기본 숫자/범주 명시, style은 서로 다른 filled
이름 marker의 범주입니다. Order는 선택/예약, 결측은 숫자/log 검사 전에 행 쌍으로
제외합니다. Bool/숫자 범주는 분리하고 모호한 문자열 라벨은 거부합니다. 선택 전체
행에 선형 범위를 공유하며 명시적 범위는 매핑만 clip하고 행/style별 척도는 바꾸지
않습니다. 지름 points를 보간 후 제곱해 native 면적으로 넘기며 정확한 0도 보이지
않는 행을 보존하고 양수 면적 underflow는 오류입니다. 상수/subnormal은 중간값과
한 guide, 크기를 맞춘 차이로 극단/인접 low bits를 유지합니다. 관측 범주와 숫자
calibration guide의 역할 라벨은 data limit/가짜 관측을 추가하지 않습니다. Global
reference는 명시적 label이 필요합니다. 행10000/level64/충분한 marker·primary숫자2D,
기존 group/c/스칼라 역할 충돌은 거부합니다. 명시 숫자 hue colourbar와 point
윤곽은 아래 F01 증분에서 지원하며 문서화한 시간/y2 제약과 넓은 계열 adapter는
계속 남습니다. 원래 85개 subset 검사는 역사적 근거이지 F01 전체 인수가 아닙니다.
[실행 예제](../examples/scatter_semantics.py).

### 원본 선과 추정 선

Omitted/predictor-only lineplot은 기존 C07 cell별 점별 percentile,
unit-then-row draw와 binary64 반복값/tail 경계를 유지합니다.
명시적 `LineSpec(resampling="unit")`은 짝지어진 원본 trajectory/질량 전체를
반복합니다. Percentile은 점별이며 max_deviation은 bars/ribbon과 독립적으로
유한 curve 또는 선택 layer family의 정확한 상위 경험 maximum을 보정합니다.
Complete-unit min/max는 두 calibration 모두 nonregular 경험 envelope입니다.

숫자/date native grid는 응답 결측을 버리기 전 해당 raw curve와 명시적 예약으로
만들고 categorical은 pooled typed ordinal slot을 사용합니다. 실제 primary/y2·
v/h의 간격과 grouped gap을 유지합니다. 원본 선은 관측 순서/중복/장벽과 실제
stroke/marker를 보존하며 추정하지 않습니다. Figure guide는 저장 scale_id만
membership으로 쓰고 실제 이름 있는 mark family/native 문맥을 구별합니다.
[과학/API/자원 계약](LINE_WORKFLOW.ko.md) ·
[실행 가능한 합성 예제](../examples/line_workflow.py).

### 짝지은 필드·실제 누적 법칙·전체 모델 HDR

`hist2d`는 strict `Histogram2DSpec`과 논리 x/y를 명확히 고르는
`BivariateBinsSpec`을 받습니다. Count/frequency/probability/proportion/percent/
density는 짝지은 빈 내부 질량과 실제 원자료/day 면적을 쓰며 log 표시 면적을
쓰지 않습니다. KDE는 **집계 전의 같은 코호트**를 받아 빈 밖 관측값도 적합에
유지합니다. 자체 전체 밀도/CDF를 count 높이에 맞춰 바꾸지 않습니다. 통계의
실제 mappable·원시 값·색상 막대는 semantic hue 막대와 구분합니다.

`kde2d`는 물리 행의 가중 전체 공분산·Kish·Scott/Silverman 의미를 유지합니다.
Gaussian과 Cholesky product-Epanechnikov를 명시하며 후자는 방사형이 아닙니다.
원래 적합 법칙의 결합 CDF·절대 밀도 레벨·actual primary/y2/v-h/clock·선언
log10 fit/Jacobian 단위를 지원하되 비선형 통계를 추론하지 않습니다.
`HDRSpec`이 없으면 기존 유한 격자 조건부 HDR입니다. 명시 full 모드는 모든
미지 순서 절단값을 적합 법칙에 대해 보정하고, 최초 밴드가 겹치지 않는
내부 보장 네이티브 셀 합집합을 만듭니다. 목표 질량·HDR 대칭차·원본/변환·
네이티브·실제 클리핑 오차를 구분하며, 보이는 확률을 목표 p라고 부르지 않습니다.
유한 IEEE/계산 모델 경계이지 보편적 원본 모집단·매끄러운 contour·출판 QA
보장이 아닙니다.

`ecdf2d`는 proportion/percent/count 리터럴과 내부 원본 매듭·질의를 모두
보존합니다. 하위 영역은 AND이고 strict 보완은 OR이지 joint survival이
아닙니다. Bounds/query는 분모 행을 지우지 않습니다. 동점·최종 반올림 전
정규 질량을 유지하며 percent 단위와 엄격한 오른쪽 꼬리도 먼저 결합합니다.

NEW 필드는 figure 전체의 합성 작업2B/256MiB/동시 pair 스칼라1M/네이티브
정점2M 예산을 공유합니다. 기존 경로와 D01/C07 경계는 별도입니다. 실패를
허용오차 축소·레벨 생략·부분 원본/출력·조건부 fallback으로 대신하지 않습니다.
[과학/API/자원 계약](DENSITY_FIELDS.ko.md) ·
[전체 실행 예제](../examples/density_fields.py).
설치/DOM/동일 artifact 최종 검증은 별도 게이트입니다.

### 가중 단변량 커널과 구성비

`kde` 생략 호출은 기존 비가중1.06*sample-SD*n**(-1/5)·200-point·상수
fallback을 유지합니다. 명시 KDESpec은 짝지은 상대 질량, 물리 행 불편
공분산/Kish, Scott/Silverman 또는 유한 스칼라 H를 씁니다. Cut/clip은
평가만 제한하고 특이 튜플에 jitter를 만들지 않습니다. 공통 정규화는
유효 hue/전체 풀이지 size/style 튜플별 풀이 아닙니다.

Gaussian과 분산1 product-Epanechnikov는 공통 그리드의 layer/stack/fill을
지원합니다. Stack은 기여를 더하며 누적 stack/fill도 모집단 CDF가 아닌
기여·구성비로 표시합니다. 압축 커널의 진짜 0 영역은 간격으로 유지합니다.
Actual v/h/y2/clock과 명시 log10 fit의 data/fit 밀도 단위를 지원합니다.
임의 커널/callback·symlog/asinh/logit 통계 추론은 없습니다. SIZE는 실제
선 두께 pt이며 가짜 필드 point glyph를 만들지 않습니다.
[전체 계약](DENSITY_FIELDS.ko.md) ·
[기존 Gaussian 비교](../examples/kde_semantics.py).

### 가중 히스토그램 첫 범위

새 옵션은 strict HistogramSpec이며 None은 기존 density/group/bin/alpha effect를
유지합니다. Count=질량, frequency=질량/원자료 폭, probability/proportion=질량/
분모, percent=100배, density=질량/(분모*원자료 폭)입니다. Bin 안 질량만 분모로
사용하며 common_norm=True는 선택 hue 전체, False는 곡선별입니다. [left,right),
마지막 경계만 포함하고 정수 equal-width bins는 유효 행을 모아 공통 경계를
만듭니다. 명시적 edges도 원자료 폭을 공유합니다. 필요한 결측/0 가중치를
제외하고 유한 non-bool 관측값·비음수 가중치와 행 쌍을 유지합니다.

누적 density는 높이 합이 아닌 질량 적분이며 누적 frequency는 미지원입니다.
공통 누적 끝은 그룹 질량 비중, 별도 정규화는 1/100입니다. 크기를 맞춘 비율 합·
독립 bin 합과 반올림하지 않은 행 prefix로 작은 질량과 단조를 보존합니다. Raw
곡선 총합·계산 폭/높이는 유한이어야 합니다. 빈 곡선은 도형/범례 없이 hue 색상/
해칭/선 모양 자리만 유지합니다. Cartesian2D 막대/step·v/h·양수 관측 log·명시적 날짜축과 수직 y2에서도 원자료 폭이며
높이 축은 선형이며 alpha/outline/reference를 지원합니다. Multiple='layer'는
원래 bin을 겹치고, 그룹별 'stack'은 hue 순서대로 높이를 쌓으며 'dodge'는 빈
예약/범위 밖 hue까지 포함한 모든 자리로 원자료 폭을 나눕니다. 높이·정규화·
누적 의미는 그대로입니다. Density/frequency 분모는 원래 bin 폭이므로 dodge는
높이 보정 없이 표시 면적을 줄입니다. 곡선별 정규화 후 stack도 원래 분포들을
더하며 pooled 분포로 재정규화하지 않습니다. Stack의 비유한/소실 양수 증가분과
해상도 부족 dodge 자리는 모든 도형 생성 전에 거부합니다. Element='step'은 관측
hue당 하나의 native stairs 도형입니다. Layer는 0에 닫히고 stack은 절대 윗선과
이전 baseline을 둘러쌉니다. 경계/높이/통계는 그대로이며 빈 hue의 테마 선 모양/
색상 자리·edge_color 선 색상과 0까지 정확한 alpha/두께를 지원합니다.
Dodge step은 원래 bin의 hue 자리에 같은 높이를 배치하고 나머지는 0-baseline 도형으로
연결합니다. 새 관측값·질량은 추가하지 않습니다. Fill=None은 기존 채운 막대·빈 step을
보존하고 이전 JSON에서는 생략됩니다. 명시적 True/False는 도형만 바꿉니다. 채운
step은 그룹 면 색·해칭, outline은 해칭 없는 그룹 선 색·테마 dash를 사용합니다.
Multiple=fill은 기존 stat/common_norm/cumulative 높이를 bin별 그룹 높이 합으로
나눕니다. 빈 bin은 0이며 원시 질량을 대신 쓰지 않는 무차원 구성비입니다. 누적 fill은
CDF가 아니며 감소할 수도 있습니다. Poly는 원자료 bin/슬롯 중심을 native 직선/면으로
잇고 최소 두 개의 표현 가능한 중심이 필요합니다. Raw bin 범위·0 baseline을 유지하며
관측값 추정·jitter를 추가하지 않습니다. None은 선, True는 면입니다.
[모드 예제](../examples/histogram_modes.py). 단변량 HistogramSpec에는
KDE/2변량/구간/callback을 붙이지 않습니다.
짝지은 통계와 같은 코호트 KDE는 위의 Histogram2DSpec을 사용합니다.
In-range 분모는 명시적으로 유지하며 upstream 전체 동등성이 아닙니다.
[실행 예제](../examples/histogram_statistics.py).

### ECDF 첫 범위

전용 ecdf는 원자료와 strict `ECDFSpec`(stat/complementary/weights)을 저장합니다.
Right-continuous F(t)=sum(w for X<=t)/sum(w)의 분모는 각 곡선이고 percent는
100*F, count는 누적 가중 질량(가중치가 없으면 행 개수)입니다. 보완형은 X>=t가
아닌 X>t이며 censoring/생존 추정량이 아닙니다. 반복값을 한 완전한 jump로 표시하며
v는 post, h는 좌표를 바꾼 pre step입니다. x 인자는 계속 관측 열입니다. 유한
관측 범위·최솟값의 전체 jump만 표시하고 무한 좌표·꼬리는 만들지 않습니다.
독립 indicator 합과 native Matplotlib 경로의 오른쪽 극한을 검증했지만 전체 수치
동등성을 주장하지 않습니다.

필요한 x/group/weights 결측 및 0 가중치를 log 양수 검사 전에 제외합니다.
값·가중치는 bool을 제외한 유한 숫자, 가중치는 비음수입니다. 비율은 원본과
행 질량을 동점 집계·최종 float 반올림 전의 정규 dyadic 표현으로 유지합니다.
Percent 단위도 먼저 결합하고 strict 보완은 정확한 오른쪽 질량을 씁니다.
Raw count overflow는 곡선별 오류입니다. 빈 hue는 도형/범례를 만들지 않으며
순서로 공통 색상/선 자리를 예약합니다. Actual Cartesian v/h primary/y2
관측 clock·양수 관측 log/선형 질량·실제 knot 마커·독립 raw 역할을 지원합니다.
명시적인 짝지은 누적 필드는 위의 ecdf2d를 씁니다. 추론 구간/censoring/
Kaplan-Meier/KDE/callback을 자동 해석하지 않습니다.
[실행 예제](../examples/ecdf_semantics.py),
[Matplotlib 기준](https://matplotlib.org/3.8.0/api/_as_gen/matplotlib.axes.Axes.ecdf.html),
[Seaborn 기준](https://seaborn.pydata.org/generated/seaborn.ecdfplot.html).

### 공통 통계: 첫 v1.1 구현 범위

기존 `.bar()`는 **미리 계산된 값**을 그리는 의미를 유지합니다. 새 `barplot`,
`pointplot`, `countplot`은 원자료와 `StatSpec`을 저장하고 공통 NumPy effect에서
수치를 계산합니다. mean/median/sum/min/max/count estimator와 SD·표본평균의
SEM·관측값 PI·seeded percentile-bootstrap CI를 지원합니다. count는 구간을
사용하지 않고 SEM은 선택한 통계 좌표의 평균에만 적용합니다(기본 raw 산술평균,
명시적 log 평균은 아래 범위). Bootstrap은 원래 case를 균등하게 짝지어 추출하며
가중 확률이나 unit 평균이 아닙니다. 가중 mean은 SD/SE/PI/CI, 관측 LEFT
median/min/max는 SD/PI/CI, total은 CI, count mass는 구간 없이 사용합니다.
SD/SE는 canonical reliability variance/물리행 Kish, NEW 가중 PI는 정확한
percent target입니다. 결측/0은 쌍으로 제외하고 부족한 관측/unit은 정직하게 생략합니다.
`order`/`hue_order`로 범주를 선택·정렬하고 빈 자리를 유지합니다. 선형축의
가로 방향·bar gap/값 라벨·count 비율/percent·stack을 지원하며 count 분모는
범주·hue 전체의 선택된 유효 행입니다.
유한 명시 범위이지 Seaborn 전체 동등성이 아닙니다. [C07 계약](STATISTICAL_WORKFLOW.ko.md)에
실제 mark 단위·typed ID·canonical 잔차/endpoint 수정과 NEW-only 선택10000행/
점별256cell/실제2Bwork·1M active chunk를 설명합니다. 기존 weight/units/plain/
semantic dense-line이라는 이유만으로 상한을 붙이지 않고 prefix CI/숨은 생략/
SLA·RSS 약속을 만들지 않습니다.

### 통계 native/log 첫 범위

Bar/point/count는 native_scale=True로 유한 숫자 실제 범주 위치를 선택합니다.
Order는 위치를 선택·예약하고 폭/dodge는 축 좌표의 최소 간격 비율입니다.
Log 범주에서는 log10, 단일 범주에서는 간격1이며 native bar_width는 (0,1],
point dodge는 [0,1]입니다. 빈 point 셀은 선을 끊되 실제 간격만으로 끊지는 않습니다.
Hue/색상 빈 자리·공통 축의 불일치도 명시적으로 처리합니다.

Stat_scale='data'는 log 값축에서도 원자료 추정이고 'axis'만 log10의
mean/median/min/max·SD/SEM/PI/CI를 계산한 뒤 역변환합니다. 가중치/단위는
원자료 행 쌍을 유지하며 log sum/count를 곱/거듭제곱으로 해석하지 않고 거부합니다.
선택·결측 제외 후 log 관측값은 양수여야 하며 count는 log-fit을 하지 않습니다.
계산 구간이 비양수거나 역변환 overflow면 도형을 만들기 전에 오류로 알립니다.

비누적 bar/count baseline은 원자료 단위의 유한 값(선형 기본0)이고 log는 명시적
양수입니다. 도형 끝은 baseline+추정값이 아닌 추정값이며 라벨은 baseline 방향에
맞게 실제 구간 끝을 피합니다. C06 log stack은 명시적 양수 baseline·cumulative top과
기존 정규화 범위를 유지합니다. Bar/point는 실제 primary/y2/v-h/date/native/log,
line/count는 각자 별도 target 범위입니다. 자동 비선형 통계·callable·전체 parity는
아닙니다. [C07 실행 예제](../examples/statistical_workflow.py).

필수 구분·검증:

- SD는 관측값 산포, SE/SEM은 추정량/평균의 불확실성입니다.
- PI는 관측값의 percentile interval, bootstrap CI는 재표본화한 **추정값**의
  구간입니다. 평균의 CI를 `1.96 * SD`로 대신하지 않습니다.
- estimator, method, level, bootstrap 횟수·seed를 명시적으로 저장합니다.
  결측치, `ddof`, 빈 그룹·관측값 1개, 가중치, 반복 측정 재표본화 규칙을
  문서화하고 검증해야 합니다.
- 현재 bar/errorbar의 절대 구간은 중심값을 포함해야 합니다. 일반적인 PI가
  선택한 추정값을 포함한다는 보장은 없습니다. 새 통계 range mark는 이런 구간도
  임의 clipping이나 음수 오차 크기 변환 없이 정직하게 표시합니다.
- 현재의 간단한 KDE와 정규근사 회귀 band는 Seaborn과 같은 통계 의미·수치라는
  보장이 없습니다. 이름이 같더라도 참조 데이터로 비교해야 합니다.

### 첫 swarm 범위

`swarmplot(category, value, group=hue)`는 seeded jitter가 아니라 매 draw
원형 marker의 화면 좌표를 배치합니다. marker/선 두께, DPI, 현재 limits/
layout, 가로 방향·양수 log 값축 변환을 검증했습니다. 값은 그대로 유지하며
순서의 빈 자리 보존·non-dodged hue 공동 배치를 지원합니다. 결정론적
greedy O(n^2 log n)이며 레이어당 유효 행 2000개로 제한합니다. 최적 배치나
최적해 보장은 아닙니다. 명시 호환 `pack_scope` member는 axes draw마다 한 번 함께
배치하고 이름 없는 layer는 독립입니다. 새 연산 상한은 panel/scope 물리 instance
4000개이며 같은 원본 행을 두 번 그리면 두 개로 셉니다. 과밀/과대 행도 gutter에
보존하고 warn_thresh 기본.05·collection마다 한 번 경고합니다. 실제 named glyph·
독립 hue/size/style·날짜·양수 log·v/h/y2는 원본 관측을 유지합니다.

Size-only numeric/categorical 및 기존 group 조합은 보존합니다. Size는 명목 지름
points이지 질량/가중치가 아닙니다. 필수 역할 결측은 공동 제외하고 norm은 매핑을
clip합니다. 호환 mixed-family ID는 scatter/lineplot/strip/ECDF/rug와 원본 row domain을
중복 제거하여 공유하며 mark별 지름/stroke 단위를 구분합니다.
[전체 scope/live-grid 계약](SWARM_FACETS.ko.md)·[숫자 size](SWARM_SIZE.ko.md)·
[공유 domain](SWARM_SHARED_SIZE.ko.md)을 참고하세요.
Categoricalsize는관측/명시levelrank와size_order선택·예약크기/관측만guide를사용합니다. Bool/numeric은
별도key이고최대64개명확한label입니다. [Categorical범위](SWARM_CATEGORICAL_SIZE.ko.md).

반환Matplotlibcollection의native `set_sizes`(면적pt²)/linewidth배열(pt)편집은각쌍의반지름합과
각점의gutter여유로실제DPI/layout/scale에서다시배치합니다. 보존행개수이하의비어있지않은유한비음수
배열을지원하고짧은배열은순환하며긴배열은점을추가하지않고거절합니다. 표현불가packing기하는offset변경
전에실패하고oversized/충돌행은보존·한번씩세며기존warn-once를유지합니다. Artist편집만해당하며
LayerSpec/JSON을변경하지않습니다. 위별도numericSemanticSpec매핑이직렬화할size열의declarative경로입니다.

### Letter values: 명시적 가중 C05 workflow

비가중 `boxenplot`은 type7을 유지하며 subnormal을 포함한 보간을 한 번만
올바르게 반올림합니다. 가중치는 행 복제 횟수가 아니라 상대 질량입니다.
Canonical 정수/binary-float 값을 미리 float로 반올림하지 않습니다. 비가중
꼬리는 최종 올바르게 반올림한 type7 경계로, 가중 LEFT 꼬리는 정확한 관측
canonical 경계로 분류합니다. 반올림 전 띠 정보는 양수 span의 native 정밀도
손실 검사이지 다른 type7 꼬리/area 추정이 아닙니다. 실제 요청 꼬리의 순서를
binary64가 표시할 수 없으면 명시 실패하며 숨긴 미요청 꼬리로 가짜 비상수성을
만들지 않습니다. Epsilon/자동 rescale/일괄 large-int 금지는 없습니다.

LEFT 역 경험 CDF는 누적 질량이 정확히 경계에 닿으면 그 관측값을 반환하며
두 값의 중간값을 넣지 않습니다. 따라서 같은 명시 가중치라도 비가중
type7과 다를 수 있습니다. 네 이름 깊이 수식의 n을 물리 행 기준
Kish n_eff=(sum w)^2/sum(w^2)로 대체하고 지수 경계는 정확히 비교합니다.
이는 신뢰구간/독립 관측 주장 아닌 집중도 기반 정지 heuristic입니다.
반복값의 가중치를 행으로 나누면 n_eff/깊이/꼬리가 달라질 수 있습니다.
정수 k와 기존 깊이32 한도는 유지합니다.

가중 area는 경험 `[low,high)` 구간이며 마지막만 오른쪽 닫힘입니다.
중복 내부 경계는 빈 구간, 마지막 높이0 구간은 원자 질량을 소유할 수 있고
띠 질량+엄격한 바깥 꼬리 질량은 정확히1입니다. 높이/질량0의 area 폭은0,
모든 경계가 같으면 exponential 퇴화 도형을 유지할 뿐 분산/무한 밀도를
만들지 않습니다. 양수 도형을 표현할 수 없으면 clamp/삭제 대신 거부합니다.
비가중 area는 기존 명목 percentile 질량을 유지합니다.

Strict append/omit-none `BoxenSpec`, `BoxenBandComponentsSpec`,
`BoxenHueComponentsSpec`은 central rank0, 바깥 방향 lower/upper rank1..31을
사용합니다. 이름 깊이 변화에도 rank 의미가 같고 explicit k의 불가능한 rank,
중복 target/알 수 없는 필드는 거부합니다. Raw typed hue(bool!=숫자)와 속성별
layer→hue→band→hue-band 우선순위로 실제 순서 있는 polygon의 fill/edge/hatch를
제어합니다. 매핑 HUE는 실제 BODY 색이며 꼬리 tint를 덧씌우지 않습니다.
비매핑 기본 tint는 유지하되 명시 band.color는 최종 색입니다. Size는 BODY
윤곽 pt만, style은 BODY dash와 실제 관측 FLIER glyph만 소유합니다.
모든 tier의 매핑 충돌을 거부하고 없는 glyph의 범례를 만들지 않습니다.
C03/C04의 같은 선택행/tuple cell/shared-domain/trait/no-line/native inverse
규칙을 사용하며 mapper/KDE 층을 복제하지 않습니다.
맞는 SemanticSpec/scale_id는 boxen/scatter/line과 기존 C04 계열에서 원본 행을
중복 없이 모은 RAW 정규화 domain을 공유할 수 있습니다. BODY 윤곽/점 지름/
곡선 stroke의 물리 단위와 보이는 guide는 계열별이며 공유 자체를 금지하지
않습니다. 반복 Boxen view의 실제 작업량은 중복 제거하지 않습니다. Scalar와
flier component는 기존+/x/. 및 P/X/p/h/8 등록 glyph를 공유하지만 filled-only
semantic cycle은 별도이며 unfilled scalar glyph로 넓히지 않습니다.


필요 결측은 함께, 명시 가중치0은 제외하며 선택된 음수/비유한/bool 가중치는
거부합니다. 모든 양수 실제 꼬리 행·반복값·원본 순서/ID는 보존합니다.
Primary/y2·가로/세로·numeric/native/date/log·선형 값 clock·data/log-axis 통계·
저장/live cell·N13 중첩/inset을 공개 선언으로 조합합니다. 가중치에 clock 의미를
주지 않으며 미지원 비선형 axis 통계는 거부합니다.

원본 검증은 옵션/참조/type/선택 유한 값/행/cell/정적 rank를 검사하며 fit하지
않습니다. 기존 render/preview에서 summary를 한 번 계산해 native 생성 전
실제 band/flier effect 예산을 검사하고 도형에 재사용합니다. 새 advanced 한도:
layer당 양수 물리 행10000/cell256, figure당 실제 띠 polygon32768/요청 flier
instance1000000. 반복 사용·alpha0/marker-none도 작업에 세며 hidden 미요청
artist만 생략할 수 있고 summary 꼬리는 삭제하지 않습니다. Figure 총 source
행 한도/표본 추출/삭제/SLA/RAM/marker-size 보장은 없습니다. 기존 admission,
깊이32/패널256/layer1024/렌더40M픽셀은 유지합니다.

양쪽 UI는 접힌 populated 전체 `ReplaceLayer` actionJSON을 제공합니다.
이미 있는 nonbool 정수 panel/layer 인덱스의 authoritative 교체이며 순서/수/
data/recipe를 바꾸지 않습니다. 정상 preview 후 commit하고 실패 시 spec/PNG/
history를 유지합니다. Undo/redo/reopen과 cell-local 편집 후 명시 전체 template의
덮어쓰기 규칙도 유지합니다. 전체 v2/REL01 완료 주장이 아닙니다.
[전체 수학/소유권 정책](REFERENCE.md#letter-value-distributions),
[가중 실행 예제](../examples/weighted_letter_values.py),
[기존 비가중 비교](../examples/letter_value_categories.py)를 참고하세요.

### Box/violin 범주형 하위 범위

한 열 `.box(value, group=category)` / `.violin(value, group=category)`의
native 1-based 위치는 유지합니다. y를 추가하면 범주 x/값 y, group=hue로
중첩하며 방향은 인자 의미를 바꾸지 않습니다. 필요한 결측 행은 함께 제외하고
order의 빈 자리에는 도형을 만들지 않습니다. 숫자 dodge는 전체 hue offset 폭
(None 자동·0 겹침), gap은 할당된 body 폭을 줄이는 비율입니다. whisker는
native IQR/분위수 규칙의 관측 끝점이지 CI가 아닙니다. Bootstrap을 요청하지 않은
notch는 기존 Gaussian 근사를 유지합니다. Violin은 native Gaussian KDE·각 폭/
관측 min/max를 사용합니다. C03은 아래 box 경로를 추가하지만 다른 계열의
미지원 조합을 바꾸거나 upstream 전체 동등성을 주장하지 않습니다.

### 독립 box/boxen 구성 요소 첫 범위

Box는 typed body/whisker/cap/median/mean/flier, boxen은 body/median/flier만
지원합니다. 생략 속성은 기존 native/layer/hue를 유지하고 구성 요소가 shorthand를
덮어쓰되 관측값·통계·좌표는 바꾸지 않습니다. Body 색은 hue 기반색을 대체하면서
letter-value tint 계층을 유지합니다. Alpha는 정확히 0/1도 적용하고 빈 hatch는
중복 해칭을 끕니다. 선 stroke와 marker 채움/윤곽은 독립입니다. Mean은
showmeans=True가 필요하며 숨긴 flier/boxen median의 스타일은 거부합니다.
명시적 body/cap 스타일은 ambient rc에서 숨긴 box artist도 활성화합니다.
알 수 없는 nested 키/타입·역할/값 제약은 설정을 버리는 대신 오류로 알립니다.
색상/선/marker/크기를 제한하고 callback·임의 kwargs는 없습니다. Boxen의 띠/hue별
매핑은 이 범위 밖입니다. Box는 C03의 typed hue별 component·columnar summary를
추가하되 기존 무요청 raw 기본값은 유지합니다.
[실행 예제](../examples/distribution_components.py).

### C03 전체 box workflow

[과학/단위/소유권 계약](BOX_WORKFLOW.ko.md)과
[raw/supplied/공유 역할/live 예제](../examples/box_workflow.py)를 참고하세요.
`bxp`는 기존 column·ID·선택 mark의 unavailable 상태를 보존합니다. Raw 중앙값
CI는 private seeded 행 재표본화이며 whisker/관측값 PI가 아닙니다. Cap은 dodge/gap
이후 body 폭 비율이고 0도 geometry를 보존합니다. Size는 BODY outline stroke pt만,
style은 기본 cycle 포함 직렬화 marker의 실제 flier glyph와 BODY dash만 소유합니다.
다른 구성 요소는 독립이며 매핑 충돌은 거절하고 실제 box guide를 사용합니다.
Native/date/log/v-h/y2·고정 cell live·빈 예약 view는 기존 경계를 공유합니다.
새 advanced 상한은 그리는 cell256·선택행10000 AND 별도 flier10000이고 이전
상한은 그대로입니다. 넓은 F01/F02/G01·최종 고정 제품 검증은 별도입니다.


### C04 violin workflow

[전체 과학/단위/소유권 계약](VIOLIN_WORKFLOW.ko.md)과
[짝/공유 계열/live 실행 예제](../examples/violin_workflow.py)를 참고하세요.
기존 생략 경로·두 hue split은 유지하고 명시 paired는 고정 반쪽 lane·예약 hue·
홀수 마지막 왼쪽 반쪽을 사용하며 가짜 관측을 만들지 않습니다. Inner mode별
native trait를 구분하고 raw key True/1을 보존하며 Box/boxen의 새 미지원 role은
무시하지 않고 거부합니다. HUE는 body fill·SIZE는 BODY 윤곽 point·STYLE은 body
dash와 실제 inner glyph만 소유합니다. Raw tuple별 fit의 정규화는 effective
hue/전체 pool이고 참조는 pool별 한 번이며 weights는 상대 질량입니다.
Raw 비확장 inner의 실제 native flag/color/span 기본 우선순위를 유지합니다.
Target/clock/log/native/live도 단일 selector/domain/recipe를 재사용합니다.
Advanced는 선택행10000·그리는 profile256·범주형 level/override64·support1000이고
연속 숫자 역할 값은64로 제한하지 않습니다. Callable/임의 kwargs/새 nonlinear
통계·sampling·넓은 다른 row 완료를 추가하지 않습니다.

### 가중 violin 범위

Weights는 선택한 관측 행과 유한 비음수 상대 질량을 짝지으며 결측/0 가중치를
양수 검사 전에 제외합니다. Gaussian unbiased 공분산/effective n으로 Scott/
Silverman 대역폭을 정하고 행을 복제하지 않습니다. Quart/box/median은 동률을
모두 세는 역 가중 ECDF(보간 없음)이며 동일 가중치도 기존 선형 분위수와 다를
수 있습니다. 평균은 선언한 좌표에서 가중 계산하고 point/stick은 양수 행을
한 번만 표시합니다. Count 폭은 행 개수/effective n이 아닌 총 가중 질량이며
공통 배율에 불변입니다(참조 셀 간 비교 가능한 단위 필요). Area는 공통 fitted
밀도 척도이지 잘린 면적 동일성 보장이 아닙니다. Cut/clip은 fit/inner 행을
자르거나 보이는 꼬리를 정규화하지 않습니다. 상수/단일값은 가짜 bandwidth 없는
관측 퇴화 도형이며 count 참조에 그 질량도 포함합니다. 행 10000·grid 1000·
2048-row bounded kernel·크기를 맞춘 공분산/질량/평균을 사용하고 계산된 범위/
밀도/질량 비율 오류를 알립니다. 기존 비가중 fit/표시를 유지하며 SciPy/새 의존성/
callable/다른 커널/신뢰구간 추론은 없습니다. 새 테스트 78개로 독립 수식·극단
단위/가중치/low bits/chunk·native 스타일/split/log·schema/actions/editor/export/
RNG를 검증했습니다. [실행 예제](../examples/weighted_violin.py).

### 분포 native/log 첫 범위

Box/violin/boxen/swarm은 `native_scale=True`로 유한한 숫자 범주 좌표를
선택하며 bool/문자열/날짜는 제외합니다. Order는 실제 위치를 선택·예약하고
물리적 순서를 바꾸지 않습니다. Width/dodge는 최소 선택·예약 간격 비율이며
native log에서는 log10 좌표, 범주 하나에서는 간격 1을 사용합니다. 기존
ordinal/one-based 기본값을 유지하며 공통 축의 mode/scale 충돌은 거부합니다.

요약의 기본 `stat_scale='data'`는 원자료 통계를 유지하며 'axis'만 명시적으로
log10 분위수/KDE와 모든 도형 역변환을 선택합니다. Swarm은 원값을 유지합니다.
Log 값/범주는 양수여야 하고 유한 범위를 넘는 도형을 조용히 clip하지 않습니다.
통계 bar/point/count도 위 하위 범위에서 같은 간격을 쓰며 추가 매핑은 남아 있습니다.
[실행 예제](../examples/native_categorical_scales.py).

## 2. Matplotlib 기능 비교

| 기능군 | 현재 상태 | 부족한 범위 |
| --- | --- | --- |
| line/scatter/step/errorbar/band | 네이티브 스타일, 유한 가로/세로 선분, x/y 비대칭 오차, 마스크/스텝/보간된 가로·세로 띠 및 구간 | 명시된 유한 옵션과 단위만 지원. [범위](NATIVE_GEOMETRY.ko.md) |
| bar/pie | 네이티브 수직/수평 막대, 명시 기준값·정렬·부호 누적, 행별 스타일/레이블, 원형 조각·글자·값·주석 | 공급한 값과 유한 서식만 지원. [범위](NATIVE_GEOMETRY.ko.md) |
| stem | 원본 행과 기준선·수직/수평 기본 또는 보조 축·고정 그룹/패싯·색/두께/마커 공유 범례 | 날짜/로그는 명시적 축 규칙을 따름. 추정·가중치 미지원. [범위](STEM.ko.md) |
| stairs | 제공 높이 또는 보존적 재구간화, 열린 경로/채우기, 고정 그룹·패싯, 날짜/로그, 기본·보조 축 | 가로 방향·가중치·추정·의미 매핑 미지원. [범위](STAIRS.ko.md) |
| eventplot | 원본 이벤트 표식, 고정 그룹·패싯, 날짜/로그 및 기본·보조 축, 공유 색/두께/점선 | 가중치·발생률 추정·가로 표시 미지원. [범위](EVENTPLOT.ko.md) |
| broken_barh | 원본 순서 구간 띠, 고정 그룹·패싯, 날짜와 경과 기간, 로그 및 기본·보조 축 | 통계·의미 매핑 미지원. [범위](BROKEN_BARH.ko.md) |
| hist/box/violin/ECDF | 부분: 전용 가중 ECDF·proportion/percent/count·보완형·v/h, 그룹 histogram stack/dodge/fill·명시 fill/outline bars/step/poly | Histogram 2변량, precomputed box 통계와 추가 분포 옵션 |
| image/contour | N07 직교 격자 mesh/image, RGB(A), 마스크, `spy`, 등고선 및 스칼라 image/mesh의 P01 색 보정 | 기본 선형 숫자 축. 곡선 격자·등고선·직접 픽셀은 별도. [격자 계약](HEATMAP.ko.md) |
| triangulated field | N08: 명시 연결과 마스크를 사용하는 `triplot`, `tripcolor`, `tricontour`/`tricontourf`, `trisurf` | 자동 삼각분할·패싯 재인덱싱 미지원 |
| vector field | N09: 네이티브 평면·공간 quiver, barbs, 균일 격자 streamplot | 유한한 숫자 축·네이티브 적분, 크기의 의미 매핑 없음 |
| 3D | N10: 비균일 전체 해상도 surface/wireframe, 부호 있는 막대, 투영 등고선, voxel, 카메라·종횡비; N08 `trisurf`, N09 `quiver3d` 재사용 | 선형 숫자 축, 자동 리샘플링·시간/로그·임의 카메라 콜백 없음 |
| 신호·스펙트럼 | N11: spectrogram·Welch PSD/CSD magnitude/coherence·전체 magnitude/wrapped angle/unwrapped phase 및 typed FFT/window/detrend/sides/scaling | 기본 Cartesian 선형·비시간 축; y2/group/weights/행 선택 제외. 아래 계약 참조, 통합 검증은 별도 |
| 축·레이아웃 | N12 typed 눈금·scale·이름 기반 derived axes; N13 안정적 ID·native inset/nested/mosaic·span/ratio/빈 자리·공통 sharing component | [N13 계약](PANEL_LAYOUTS.ko.md)의 유한 완전 geometry·부모 내부/형제 비겹침 inset·명시적 차원 공유 적용. 임의 transform/kwargs 제외; isolated 검증은 통합/전체 v2 완료가 아님 |
| 색상·범례 | P01 네이티브 named/custom cmap, under/over/bad, 고정·공유 원시 범위, 개별 색상표, context와 범례 옵션 | F01 역할과 별도. 아래 스칼라 표시 계약 참조 |
| 주석·patch·table | 데이터/축/그림 좌표 리터럴 패치·경로, 공통 span, 네이티브 표, 혼합 좌표 주석과 획/그림자 | 네이티브 데이터 앵커만 끌기 지원. [범위](NATIVE_GEOMETRY.ko.md) |
| animation/widget/event callback/임의 artist | Python 직접 사용 | 별도 interaction 범위이며 자동으로 JSON 편집 기능이 되지는 않음 |

### 명시적 삼각형 필드

`TriangulationSpec(triangles=[[0, 1, 2], [0, 2, 3]], mask=[False, True])`의
인덱스는 원본 X/Y 열의 행 번호입니다. 불리언이 아닌 0부터 시작하는 정수를
사용합니다. `True`인 면은 제외하며 하나 이상의 면이 남아야 합니다.
유한하고 서로 다른 XY 정점, 표현 가능한 양의 면적이 필요합니다. 중복 면,
교차·겹침, T자 접합은 거부하며 같은 전체 변이나 정점에서 만날 수 있습니다.
시계 방향은 그릴 때만 보정하며 저장 순서는 변경하지 않습니다. `SetData`는
인덱스를 다시 매기지 않습니다. 새 좌표도 같은 조건을 충족해야 합니다.

- `triplot`은 표시할 삼각형의 변만 그립니다. 가짜 정점 마커는 없습니다.
- `tripcolor`의 `scalar_role="vertex"`는 열 `c`의 세 정점 값 평균을,
  `"face"`는 원본 삼각형별 `face_values`를 씁니다. 정점과 면 개수가
  같아도 역할을 추론하지 않습니다.
- `tricontour`와 `tricontourf`는 정점 역할, 열 `c`, 명시적 오름차순
  레벨을 요구합니다. 빈 레벨도 보존하고 실제 선에만 라벨을 그립니다.
  채움과 `extend`는 네이티브 등고선 경계를 따릅니다.
- 3D `trisurf`는 같은 XY 연결과 정점 높이 `z`를 사용합니다. 색은 표시
  삼각형의 평균 높이입니다. 별도 스칼라·카메라·벡터 기능은 포함하지 않습니다.

선형 숫자 축만 지원합니다. 마스킹된 면에만 연결된 정점도 네이티브 자동
축 범위에 들어갈 수 있습니다. 레이어당 정점·삼각형 각각 10,000개, 정확한
교차 검사 전 후보 쌍 방문 50,000개와 그림 단위 행렬·경로 예산을 검사합니다.
자동 삼각분할이나 패싯 재인덱싱은 하지 않습니다.
[PNG/SVG/PDF 실행 예제](../examples/triangle_workflow.py).

### 네이티브 벡터 필드

`VectorSpec`을 지정하지 않은 `quiver`는 기존 렌더링과 저장 방식을 유지합니다.
새 벡터는 선형 숫자 직교 축을 사용합니다. 평면 quiver와 barbs는 활성화된
Y2를 사용할 수 있고 `quiver3d`는 3D 패널이 필요합니다. `mask_column`은
불리언 열(`True` 제외)입니다. `group`/`hue_order`는 원본 행 순서를 유지하며
타입을 구별합니다. 평면 행 벡터는 고정 패싯을 사용할 수 있습니다. 부호 있는
성분을 허용하되 변위가 0인 quiver에는 화살표를 만들지 않습니다. 0인 barb에는
네이티브 정온 기호를 사용합니다.

- `quiver(mode="data")`는 데이터 변위와 `xy` 방향·단위, 배율 1을
  사용합니다. `display`는 화면 방향과 인치·축 너비·도트 길이 단위를
  사용합니다. `pivot`은 고정점, `width_units`는 별도의 몸통 너비 단위입니다.
- Barbs의 `length`는 pt이며 `half`, `full`, `flag`는 제공된 성분 단위의
  증가량입니다. 풍속 단위를 추론하지 않으며 반 증가량 64개를 넘으면 거부합니다.
- `quiver3d`는 원본 X/Y/Z/U/V/W 열을 사용합니다. `length`는 원시 성분에
  곱하는 배율입니다. `normalize=True`이면 세 좌표와 같은 단위의 길이입니다.
- `streamplot`은 균일한 `x_coords`, `y_coords`와 Y×X 형태의
  `u_matrix`, `v_matrix`를 사용합니다. 마스크와 짝지은 null은 0으로
  대체하지 않습니다. 씨앗은 데이터 좌표이며 최대 64개, 마스킹된 보간
  셀에는 놓을 수 없습니다. `density`와 `arrowsize`는 무차원입니다.
  `minlength`/`maxlength`는 정규화된 축 길이입니다. 값이 모두 0이면
  경로가 없고, 정지와 이동 노드가 섞이면 네이티브 적분 예산을 위해
  정지 노드를 명시적으로 마스킹해야 합니다. 행 그룹·선택자는 지원하지 않습니다.

레이어당 선택된 행 또는 격자 벡터 10,000개와 그림 단위 작업·메모리·경로
상한을 적용합니다. 예산을 넘기는 적분은 경로를 자르지 않고 제공자 호출
전에 거부합니다. 제공자 버전 간 수치 경로 동일성을 보장하지 않습니다.
[PNG/SVG/PDF 실행 예제](../examples/vector_workflow.py).

### 명시적 3D 기하

`projection3d()`는 네이티브 3D 패널을 선택합니다. `surface`와
`wireframe`의 `SpatialSpec`은 `[y][x]` 순서의 Z 행렬과 엄격히 증가하는
`x_coords`, `y_coords`를 연결합니다. 네이티브 기본 샘플 수보다 큰 격자도
모든 셀 또는 와이어를 그립니다. `spatial`을 생략하면 기존 단위 인덱스와
네이티브 기본 샘플링을 유지합니다.

- `bar3d`의 X/Y/Z는 원본 앵커이며 `dx`/`dy`는 양의 바닥 폭, `dz`는
  부호 있는 0이 아닌 차이입니다. 음의 막대도 두 끝점을 보존하며 모두
  자동 축 범위에 반영됩니다. 표면 조명은 사용하지 않습니다.
- `contour3d`/`contourf3d`는 원래 XY/Z를 사용합니다. 방향 `z`, `x`,
  `y`에 따라 각각 XY·YZ·ZX 차트에서 실제 Z·X·Y 등고값을 계산합니다.
  측면 차트는 생략되는 원래 X 또는 Y 방향에서 Z가 일관되게 단조여야
  합니다. 선은 실제 범위 내부에 한 개 이상의 명시 레벨이 필요하며,
  채워진 밴드는 명시 경계값을 사용합니다. 선택적 절대 `offset`은 한 평면에
  투영합니다. 생략하면 선은 레벨, 밴드는 중간값 위치를 사용합니다.
  사용자 고정 범위는 우선합니다.
- `voxels`는 `[z][y][x]` 불리언 점유 배열을 사용합니다. `True`인
  셀의 네이티브 노출 면만 조명을 적용해 그립니다. 세 축 모두에 각
  차원보다 한 개 많은 모서리를 지정하거나 모두 생략해 단위를 사용합니다.
- `camera3d`와 같은 `SetCamera3D` 액션은 각도(도), 위쪽 축, 투시/직교,
  상자 비율, 확대를 지정합니다. 초점 거리는 투시에만 적용합니다. `None`은
  네이티브 기본값으로 복원하며 카메라는 데이터나 고정 축 범위를 바꾸지 않습니다.

선형 숫자 기본 축만 지원하며 행 선택·시간·로그는 지원하지 않습니다.
네이티브 수로 변환한 뒤 겹치는 좌표·레벨 또는 접힌 차트는 그리기 전에
거부합니다. 레이어당 최대 10,000개 격자 정점·막대·복셀과 그림 단위
공유 작업·메모리·경로 상한을 적용합니다.
[PNG/SVG/PDF 실행 예제](../examples/spatial_workflow.py).

### 스칼라 표시와 가이드

`context("paper"|"notebook"|"talk"|"poster")`는 렌더링 내부 글자
크기에 1, 1.15, 1.4, 1.75를 적용합니다. 저널 설정은 우선하며 명시
마커 지름·선 굵기·좌표는 그대로입니다. `palette(colors=[...])`는
1–64개 리터럴 범주색을 선언 순서대로 반복합니다.

`ScalarDisplaySpec`은 `scatter(c=...)`, `heatmap`, 스칼라 `imshow`,
`pcolor`, `pcolormesh`의 실제 색을 제어합니다. 이름 있는 맵 또는
2–64개 등간격 램프 색을 고르고 `under`·`over`·`bad`를 지정할 수
있습니다. `pcolor`는 마스크 셀을 생략하므로 색을 표시하려면
`pcolormesh`를 사용합니다. 산점도의 유한 위치에 색 값만 없으면
`bad`를 사용합니다. F01·직접 RGB(A)·등고선·삼각형·통계·시간
좌표는 별도입니다. M01 색 보정과 경쟁할 수 없지만 마스크와 주석은
유지합니다.

같은 `scale_id`와 동일한 보정 선언은 선택된 원시 값을 공유합니다.
`linear`/`log`의 경계는 고정하거나 추론하며 로그 색 보정에는 양수만
사용합니다. `centered`는 지정 중심의 대칭 범위, `two_slope`는
`vmin < center < vmax`, `boundary`는 2–65개 엄격히 증가하는 경계로
반열린 구간을 사용합니다. 색상표 위치·원시 눈금·확장은 개별 설정입니다.
범례는 `ncols=1..8`과 실제 손잡이의 `line-pair`/`scatter-pair`를
지원합니다. [PNG/SVG/PDF 실행 예제](../examples/scalar_display.py).

가능한 기능은 native Matplotlib을 활용하고 plotting engine을 다시 만들지
않습니다. 아직 필요하지 않은 두 번째 renderer 추상화도 만들지 않습니다.
새 API가 의존성 하한보다 늦게 도입되었다면 명시적인 guard/fallback이나
version gate가 필요하며 하한을 조용히 올리지 않습니다.

### 저장 가능한 유한 축 제어 — N12

`AxisSpec` 뒤에 선택적 scale_options/major_ticks/minor_ticks, `PanelSpec`
뒤에 secondary_x/secondary_y를 추가합니다. 미지정 필드는 기존 0.1 JSON에
넣지 않습니다. Builder/action/검증/schema/capabilities는 NumPy/Matplotlib
없이 동작하고 effect는 native Matplotlib ≥3.8을 사용합니다.

```python
p.axis_scale("x", "symlog", options={"base": 10, "linthresh": 1, "linscale": 1})
p.ticks("x", {"locator": {"kind": "multiple", "step": 2, "offset": .5},
              "formatter": {"kind": "number", "notation": "fixed", "precision": 1}})
p.secondary_xaxis({"kind": "celsius_fahrenheit"}, label="온도 (°F)")
```

각 줄은 독립 예시이며 multiple은 선형 숫자 축에서만 유효합니다.
ticks(axis,spec,which="major"|"minor",panel=...)는 한 rank 전체 교체,
None은 해제입니다. axis_scale(...,options=None)은 scale과 parameter를
원자적으로 교체/해제합니다. 기존 SetScale은 무관한 필드를 보존하고
호환되지 않는 option은 삭제하지 않고 거부합니다. 공유 새 설정은 None만
상속하며 명시 충돌은 오류입니다. 기존 named/figure share 혼합 금지는 유지합니다.

- Locator는 auto/none/fixed/multiple(step·offset)/max_n(integer·prune)/
  linear/auto_minor/log/symlog/asinh/logit/calendar입니다. Max_n 1–128bins,
  linear 2–128개, 균등 minor 2–32분할. Calendar는 auto/year/month/week/day/
  hour/minute/second/microsecond, interval 1–1,000,000, weekday 0–6,
  target 2–128입니다. Fixed는 bool/nonfinite/float 변환 후 중복·collapse를
  거부합니다. Ordinal auto는 기존 위치·label을 유지하며 auto/none/fixed만 허용합니다.
- Formatter는 auto/none/fixed/scalar/number(general/fixed/scientific)/
  percent/engineering/log/logit/date/concise_date입니다. 소수 0–12자리,
  general 1–12자리, prefix/suffix/unit ≤32자, fixed 쌍 literal ≤128자입니다.
  임의 format template/width/eval/callback/속성 보간은 없습니다.
- Log base>1·순서 있는 subs는 기존 log가 유효한 통계/native 범주에서도
  지원합니다. Scale subs는 **minor** 정책이고 locator subs는 각 rank에
  명시 override합니다. Symlog 기본 base10/linthresh2/linscale1,
  asinh 기본 linear_width1/정수 base10(2–1024), 폭은 좌표 단위입니다.
  새 계열은 지원 raw 숫자 Cartesian/applicable y2만 허용하며 통계/ordinal/
  polar/3D는 거부합니다. Logit은 grouped rectangle 실제 끝점까지 열린
  (0,1)을 확인합니다. 상수 p는 min(p,1−p)에 native0.1 widening으로
  자료 포함/보완 대칭을 유지하거나 view/inverse 정밀도 오류를 냅니다.
  유효한 명시 limits는 덮어쓰지 않습니다.
- 보조 view는 명시 단위 affine·Celsius↔Fahrenheit·radians↔degrees·
  seconds↔milliseconds·hertz↔period·양수 reciprocal·canonical day→Unix
  seconds입니다. Unix 외에는 reverse=True로 역방향을 고릅니다.
  **실제 보이는 좌표**만 변환하고 원본 표본/단위/ID를 유지합니다.
  Parent는 linear/log, derived 오른쪽 y와 독립 y2는 충돌합니다.
  매 refresh/zoom/tightbbox에서 domain/nonfinite/collapse·target ULP
  역함수 감도 기반 정밀도를 확인합니다. View 밖 0은 양수 reciprocal에서
  허용하며 epsilon/clip/직렬화된 사용자 함수는 없습니다.
- 새 전용 상한은 확장 전 physical 축/rank당 후보512개, figure 설정된
  active 연산 합계16,384개, 출력 문자열512자입니다. 공유 상속·보조 축도
  실제 개수로 세며 반복 호출은 예약을 교체합니다. Cached Tick RAM 상한/
  SLA/메모리 sandbox나 기존 unrelated 상한 변경은 아닙니다.
- 시간 fixed 위치는 source unit/origin이 아닌 UTC1970일입니다. N12
  date/auto/concise는 canonical datetime+명시 clock으로 2100년20/21µs를
  구별합니다. Fixed auto/subsecond는 날짜+6자리, concise는 calendar/fixed
  위치에서 Matplotlib3.8 유한 level/zero/offset/trailing-zero 정책입니다.
  표현 불가능한 native grid는 오류입니다. Global epoch/no-N12 정책은
  유지하며 F02 전체 완료 주장은 아닙니다.
- 양쪽 editor의 label/limit 편집은 parameter를 유지하고 generic typed
  JSON/action을 지원합니다. 비선형 DATA drag는 실제 primary/y2 대상별로
  이유와 함께 비활성화하고 무관한 primary·제목·범례는 유지합니다.
  Linear/log는 모든 base에서 올바른 inverse이며 선형 오해 fallback이 없습니다.

[실행 가능한 여섯 패널](../examples/axis_controls.py)은 PNG/SVG/PDF·JSON과
scale 편집·undo/redo·재개방을 제공합니다. Isolated 검증·상위 통합·다른 v2
필수 항목은 구분합니다.

## 3. 선언적 지원과 Python 직접 사용을 분리

### 제품의 선언적 지원

Python·CLI·JSON·editor를 거쳐 데이터/옵션이 검증·렌더·저장·편집될 때 제품이
지원한다고 부릅니다. 이름 기반 transform과 직렬화 가능한 옵션은 이 경로에
추가합니다. 모르는 옵션을 조용히 버리지 않고 명확하게 거부합니다.

기능 수를 늘리기 위해 JSON에 pickle 함수, `eval`/`exec`, callback, opaque
Matplotlib 객체를 넣으면 안 됩니다. optional adapter가 필요하면 effect 경계에
두며 reducer/spec/validation core의 필수 의존성 0을 유지합니다.
clustering·LOWESS·robust/logistic·Seaborn adapter에는 선택형 통계 의존성이
정당화될 수 있지만, **이 로드맵에서 새 의존성을 추가하지는 않았습니다.**

### 지금도 가능한 Python 직접 사용

`Plot.render()`가 실제 Matplotlib Figure를 반환하므로 다음은 이미 가능합니다.

```python
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import mudplot as mp

plot = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y")
figure = plot.render()
try:
    axis = figure.axes[0]
    axis.axvspan(0.4, 0.8, color="#64748b", alpha=0.15)
    axis.xaxis.set_major_locator(MaxNLocator(4))
    figure.savefig("native.svg")
finally:
    plt.close(figure)
```

Seaborn이 설치되어 있으면 axes-level 함수에 `ax=`로 같은 Axes를 넘길 수도
있습니다. figure-level 함수는 자신의 figure/grid를 만들므로 이 방식과 다릅니다.

**주의:** 직접 수정은 spec·undo/redo·JSON에 저장되지 않습니다. `Plot.save()`는
spec에서 새 그림을 렌더링하므로 수정이 사라집니다. 수정한 Figure 자체를
저장해야 합니다. 직접 `figure.savefig()`를 호출한 출력에는 mudplot의
atomic/deterministic export 보장이 적용되지 않습니다. 유용한 확장 경로지만
이것을 모든 기능의 선언적 지원이라고 주장하면 안 됩니다.

## 4. 개발 순서

예상 완료일이나 구현 완료 표시가 아니라, 다음 개발 배치의 우선순위입니다.

1. **통계 계산·고수준 그래프:** mean/median/count, SD/SE/PI/seeded bootstrap CI,
   원자료용 barplot/pointplot/countplot. 명시적인 작은 범위부터 구현하고
   weights/units를 참조 테스트와 함께 확장합니다. 기존 `.bar()` 의미는 보존합니다.
2. **범주형 완성도:** 가로 방향, order/hue order, dodge/gap, stack/값 라벨,
   box/violin 옵션, swarm·letter-value 추가 의미. 첫 범위는 구현했지만
   통계 native/log 첫 범위도 구현; 추가 매핑/구성 요소는 남아 있음.
3. **관계·분포 완성도:** 독립 hue/size/style, line의 평균·구간,
   추가 histogram/분포 표현. ECDF·가중 histogram·설정 가능한 가중 단변량/2변량 KDE 첫 범위는 구현했습니다.
4. **자동 구성:** 데이터 기반 facet·공통 semantic scale, pair/joint grid와
   대각선·주변 분포.
5. **고급 통계·행렬:** heatmap 옵션, residual/robust/logistic/LOWESS,
   선택형 clustered heatmap.
6. **나머지 Matplotlib 기능군:** 이산·이벤트·신호·vector·mesh·triangle·3D,
   축·정규화·colorbar·범례·주석·레이아웃 확장. barh/stairs처럼 작고 앞 단계에
   도움이 되는 primitive는 먼저 구현할 수 있습니다.

## 5. 지원 완료의 기준

각 기능·옵션마다 다음이 필요합니다.

1. 데이터·옵션·통계 의미, upstream과의 차이, 의존성/version 경계와 오류 규칙.
2. spec/action, reducer 격리, JSON/schema 왕복과 실제 구현에 맞는 capabilities.
3. renderer·Python builder·사용 가능한 editor 경로와 미지원 조합의 명확한 오류.
4. 통계/수치 참조 테스트, artist 위치·스타일, 그룹·다중 패널·결측치 검증.
5. 실행 가능한 예제·검토한 PNG/vector 출력, 폰트·여백·범례·접근성의 일관성.
6. 같은 환경의 재현성, 최소 지원 환경·현재 locked 환경과 lint/type/schema/packaging.

**그래프 종류·옵션·통계·구성의 지원 정도를 따로 보고해야 합니다.** 주요 옵션이나
자동 통계가 없는 기능군을 전체 지원이라고 표시하지 않습니다.

## 공식 참고 자료

- [Seaborn API](https://seaborn.pydata.org/api.html)
- [Seaborn 통계와 오차막대](https://seaborn.pydata.org/tutorial/error_bars.html)
- [Seaborn axes-level / figure-level 구분](https://seaborn.pydata.org/tutorial/function_overview.html)
- [Matplotlib plot types](https://matplotlib.org/stable/plot_types/index.html)
- [Matplotlib Axes API](https://matplotlib.org/stable/api/axes_api.html)

## 고정 히스토그램 bin 규칙

Typed 단변량 `hist`는 `bins="auto"`, `"fd"`, `"doane"`, `"scott"`,
`"stone"`, `"rice"`, `"sturges"`, `"sqrt"`, `"discrete"`를 받는다.
8개 이름 규칙은 설치된 NumPy 버전 대신 고정된 classic NumPy 1.23 정의를
쓴다. `[0, 1, 2, 3, 100]`의 `auto`는 43개 bin이다.
결측 행·가중치 0·hue 제외를 먼저 적용하며 사용 가능한 관측값은 각각 한 번만
경계 선택에 참여한다. 양수 가중치 크기는 높이에만 적용한다.
유도된 bin 수가 10,000을 넘으면 할당 전에 거부하며 축소하지 않는다.

일반 discrete 값은 정수여야 하며 정수 중심·폭 1인 bin은 빈 셀도 포함한다.
`discrete=True`는 기본 `bins=20`만 canonical `bins="discrete"`로 바꾼다.
사용자 지정 bins와 충돌하며 `False`/`None`은 기존 기본값을 유지한다
(명시적 `bins="discrete", discrete=False`는 충돌).
시간 단위 제한은 [시간축](TEMPORAL_AXES.ko.md), 편집 가능한 JSON과
PNG/SVG/PDF 예제는 `examples/histogram_binning.py`를 참고한다.

## 범주 strip 계약 (C01 제한 기능 인수)

`strip=StripSpec(jitter_policy="uniform", seed=0)` 또는 명시적인
order/orientation/native/dodge로 범주 geometry를 선택합니다. 새 제어를 생략하면
기존 raw-x jitter·JSON을 그대로 유지하며 `hue_order`만 지정하는 동작도 불변입니다.
가로 방향에서도 x는 범주, y는 관측값입니다. 범주/값/group 결측은 함께 제외하되
원본 관측값·순서는 변경하지 않습니다. Order는 빈 범주·hue 슬롯도 예약합니다.
Dodge None/0은 hue를 겹치며 양수 [0,1]은 최소 범주 간격의 전체 hue span입니다.
기준 간격은 ordinal 1, native 숫자의 최소 간격, log10 축의 최소 log 간격,
날짜는 canonical day입니다. 모든 예약 hue가 span을 균등 분할합니다.
`jitter` [0,.5]는 dodge 시 hue 슬롯, 아니면 범주 간격에 대한 반폭 비율입니다.
`uniform`은 그 범위에서 local seed로 생성하고 `none`은 0을 더합니다.
Seed는 bool 아닌 [0,2**32-1] 정수이며 global RNG·관측값은 바뀌지 않습니다.
명시 날짜는 [시간 계약](TEMPORAL_AXES.ko.md)을 재사용하고 문자열 기본값을
자동 날짜로 바꾸지 않습니다. [실행 예제](../examples/strip_categories.py)는
편집 가능한 JSON·PNG/SVG/PDF를 저장합니다.
[제한 종결 근거](review_evidence/v2_strip_categories_closure.json)는 실제
Rust/browser history·재개방·설치 최소 환경 API/CLI와 고정 소스 계보를 기록합니다.
F01·REL01·v2 전체 완료는 아닙니다.

## F01 숫자 hue guide 증분 (진행 중)

Scatter/lineplot의 명시 숫자 hue에 `colorbar=True`를 지정할 수 있으며 `clabel`은
요청한 bar에만 최대 512자 문자열로 지정합니다. 음수 값·domain도 유효합니다.
Guide는 관측 축이 아닌 [0,1] 좌표에서 mark와 동일한 안정적 clipped mapping/
colormap을 쓰고 원래 값의 정확한 tick 문자열을 표시합니다. 관측 좌표·축 범위·
원자료는 불변입니다. 상수는 가짜 연속 범위 대신 midpoint 단색 swatch·정확한 tick
하나를 표시하며 이웃/extreme/subnormal 경계도 반올림으로 label을 합치지 않습니다.

그리기 전에 논리 panel/shared scope의 요청을 모아 앞선 member와 primary/y2를
포함해 숫자 hue calibration legend를 bar 하나로 대체합니다. Dataset/size/style
guide는 유지하고 `legend=False`도 요청 bar를 숨기지 않습니다. 빈 local view에는
bar를 만들지 않으며 shared 요청의 유효 label은 일치해야 합니다.
Scatter `edge_color`와 [0,1000] point `line_width`는 mapped 지름·면적과 독립적인
윤곽이며 생략 시 native 기본값입니다. [실행 예제](../examples/semantic_colourbars.py)는
JSON·PNG/SVG/PDF를 저장합니다. 아래 strip/ECDF 증분이 4계열 workflow를 추가하며
나머지 모든 명명한 계열 adapter·설치/browser·최종 관문은 계속 필수입니다.

증분의 정확한 source/검사/실패 계보는
[F01 guide 근거](review_evidence/v2_semantic_colourbars.json)에 기록합니다.

## F01 strip·경험 곡선 adapter (진행 중)

`stripplot(..., semantics=SemanticSpec(...))`는 남은 관측값에 독립 hue/size/style을
적용합니다. Size는 point 지름이며 C01 native/log/날짜 범주·순서·예약 hue 슬롯·
local jitter는 범주 좌표에만 적용합니다. 숫자 norm은 외관만 clip하며 가짜 hue
슬롯이나 측정값을 만들지 않습니다. 역할 결측·범주/역할 order가 같은 cohort를 선택합니다.

`ecdf(..., semantics=...)`는 서로 다른 raw 역할 tuple을 곡선으로 나눈 뒤 같은
행의 가중치·반복값·보완 누적을 계산합니다. Size는 point stroke이며 이름 marker/
dash를 씁니다. Marker는 관측 knot의 우연속 값(보완형은 X>t)에만 있고 맨 앞
경계 sentinel에는 없습니다. 같은 색으로 clip돼도 곡선을 합치지 않습니다.
기존 v/h·양수 관측 log·명시 날짜·수직 y2 계약을 유지합니다. 가로 ECDF+y2는
이 부분집합에서 명시 거부하며 추가 F02/D06 필수 작업으로 남고 추론은 추가하지 않습니다.

[4계열 예제](../examples/shared_semantic_families.py)는 같은 선언 pool의
scatter/lineplot/strip/가중 ECDF를 JSON·PNG/SVG/PDF로 저장합니다. 기존 호출의
기본값은 유지하며 새 LayerSpec.strip은 기존 constructor 뒤에 배치해 positional
alpha의 실제 opacity를 보존합니다. 원래 C01 종결은 역사적 snapshot으로 유지하고
다른 모든 적용 계열 adapter·F01 전체 검증은 계속 필수입니다.


### Rug 관측 표시 — D07

`plot.rug(observation, orient="v", height=None, semantics=None, axis="y")`는
원본 열을 관측값으로 유지합니다. 수직 rug는 공유 x축의 아래쪽에서 안으로,
수평 rug는 기본 y축의 왼쪽 또는 y2축의 오른쪽에서 안으로 뻗습니다. y2를
선택하기 전에 `secondary_yaxis`를 설정합니다. `height`는 bool이 아닌 유한
`[0,1]` **axes fraction**이며 None은 기존 native 0.04입니다. JSON/editor에서는
기존 `LayerSpec.width`를 사용하며 새 필드나 기본 JSON 모양을 추가하지 않습니다.
높이 0도 길이 0인 segment를 보존합니다.

데이터 범위와 날짜 변환은 관측축에만 적용합니다. Rug를 겹쳐도 독립 밀도/값축의
dataLim과 자동 범위는 변하지 않으며 수직 방향의 다른 축은 log/날짜여도 됩니다.
Fraction을 밀도·질량·날짜 기간·데이터 좌표로 해석하지 않습니다.

`SemanticSpec`/strict dict의 hue는 숫자/범주 색, size는 물리 **stroke 두께
points**, style은 이름 있는 dash를 매핑합니다. `dashes`를 생략하면
`-`, `--`, `-.`, `:` 순서이며 서로 다른 패턴이 부족하면 순환하지 않고 거부합니다.
공통 marker 목록은 rug나 guide를 filled point로 바꾸지 않습니다. 매핑 stroke
0도 native solid zero-width로 모든 행/segment를 유지하며 Matplotlib 3.8에서도
내보냅니다. 매핑 역할의 scalar color/line_width/line_style 덮어쓰기 및 독립
역할과 legacy group/c의 충돌은 거부합니다.

Semantic rug 하나는 native vectorized collection 하나이며 중복·원본 순서를
유지하고 pooling/추정/256-curve 상한을 적용하지 않습니다. 공유 scale ID는 원래
row ID domain·정규화·논리 panel colourbar 계획을 재사용하며 guide에는 관측
데이터가 없습니다. 역할 결측·명시 order로 선택해도 원본 값/ID/단위는 바꾸지
않습니다. 10,000 semantic 행 및 기존 legacy/자원 상한을 유지하고 기본축 facet의
예약 빈 cell도 지원합니다. 가중치·추론/bootstrap·임의 native kwargs는 rug
옵션이 아닙니다. 실제 [API/action/history/재개방/내보내기 예제](../examples/rug_workflow.py)를
참고하세요.

### 신호 스펙트럼 — N11

`plot.spectrum(signal, second=None, fs=..., kind="psd", nfft=None,
pad_to=None, overlap=0, window="hann", detrend="none", sides="onesided",
scaling="density", scale="linear")`는 원본 실수 표본·행 ID·순서를 보존합니다.
Python/JSON 모두 양수·유한·nonbool Hz 표본율 fs가 필수입니다. 음수 진폭은
유효하며 bool/결측/비유한 표본은 삭제/대체 없이 오류입니다. 두 번째 신호는
CSD/coherence만 쓰며 길이가 같아야 합니다.

분할 spectrogram/psd/csd/coherence의 생략 nfft는 256이며 완전한 window만
씁니다. 간격은 nfft-overlap, 남은 불완전 구간은 원본에 남지만 계산하지 않습니다.
짧은 신호를 자동 padding하지 않습니다. magnitude/angle/phase는 전체 길이를
쓰므로 nfft=None·overlap=0입니다. 길이 3 이상 symmetric NumPy window
boxcar/hann/hamming/blackman, window별 선행 detrend none/mean/linear를
지원합니다. pad_to>=window 길이, nonbool 정수 overlap은 [0,N)입니다.
Coherence에는 겹친 window도 포함해 완전 구간이 2개 이상 필요합니다.

Density는 |FFT|²/(fs*sum(window²)), spectrum은 |FFT|²/|sum(window)|²입니다.
One-sided의 DC는 배가하지 않고 실제 padded FFT 길이 M이 짝수일 때만
Nyquist를 배가하지 않습니다. 나머지 양수 주파수는 2배이며 two-sided는
음수부터 양수까지 오름차순입니다. CSD는 정규화 mean(conj(X)*Y)를 계산하고
절댓값을 표시합니다. 복소 위상은 0으로 조작하지 않고 effect 결과에 유지하며
원본 JSON 표본에 넣지 않습니다. Coherence는
|mean(conj(X)*Y)|²/(mean(|X|²)*mean(|Y|²))이지 구간 coherence 평균이 아닙니다.
부동소수점 오차 내 [0,1] 무차원량이며 겹친 window의 독립성/유의성은 주장하지
않습니다. Magnitude는 |FFT|/|sum(window)|이며 peak 진폭이 아닙니다.

Angle은 wrapped, phase는 unwrapped 라디안이며 주파수 오름차순입니다.
정확한 영 계수는 미정의 gap이고 연속 유효 구간마다 따로 unwrap합니다.
분모 0인 coherence도 gap입니다. 선형 power 0은 유효합니다. dB는 power/
CSD 절댓값에 10log10, magnitude에 20log10(선언 단위 1 기준)을 적용합니다.
0은 gap이지 임의 양수 floor가 아닙니다. 전부 미정의면 오류입니다.
Magnitude/angle/phase/coherence는 scaling을 쓰지 않아 density를 유지해야
하며 phase/coherence는 dB를 금지합니다.

기본 라벨은 Hz·경과 초·전력/밀도·coherence·라디안이며 원본 열 이름이 아닙니다.
명시한 사용자 라벨은 유지합니다. Spectrogram native cell은 주파수 중점 경계/
시간 hop 폭이며 cmap_kind/colorbar/clabel/alpha를 지원합니다. 선은 color/
line_width/line_style/alpha/label/reference, 미사용 제어는 오류입니다.
여러 panel을 지원하되 단위가 다른 spectral/raw 좌표를 한 panel에 섞지 않습니다.
현재 계약은 기본 Cartesian 선형·비시간 축이며 y2/group/semantics/weights/
행 filter 제외입니다. 향후 조합까지 수학적으로 불가능하다는 뜻은 아닙니다.
전용 사전 할당 상한은 채널당 표본 1,000,000, FFT/window/pad 길이 65,536,
segments*pad_to 복소 cell 1,048,576입니다. 한 complex128 grid 최대 16 MiB
외 bounded buffer가 있습니다. SLA/RAM sandbox/기존 상한 변경/절삭이 아닙니다.
Core builder/검증/JSON/capability는 무의존성을 유지합니다. 실행 예제
examples/signal_spectra.py와 Rust 등록 layer/JSON form에서 같은 옵션을 씁니다.


N11 수치 검토 보정: coherence만 실제 소비한 prefix의 각 nonzero 채널을
양수 최대 절댓값으로 나눈 뒤 detrend/FFT합니다. Prefix 끝은
`(segment_count-1)*(nfft-overlap)+nfft`이며 쓰지 않는 trailing 표본은 원본에
보존·검증하지만 scaling에 영향을 주지 않습니다. Scaling으로 소비된 nonzero
표본이 지워지면 FFT **전에** 명시적 floating-point precision 오류를 내며
수학적 영/미정의 bin으로 주장하지 않습니다. Float64 연산 경계이지 임의
정밀도 FFT 지원이 아닙니다. 이후 주파수별 private segment 계수 벡터를 양수
최대 절댓값으로 나눈 뒤 cross/power를 평균합니다. 각 채널·주파수 계수는
무차원 비율에서 상쇄되며 유효 bin의 mean power는 1/segment_count 이상이어서
주파수 간 진폭이 수백 decade 차이여도 계산된 nonzero 계수의 곱 underflow로 인한
가짜 gap을 피합니다. 계산된 영 채널/bin은 0이며 floor/clip/jitter/원본 수정이 없습니다. 물리 단위의 복소
cross-spectrum은 CSD에만 반환하며 원래 단위를 유지합니다. Width 0 선은
native no-line style로 표시하되 모든 주파수/값 artist data를 보존하여
minimum 버전의 all-zero dash 오류를 피합니다. 선 색상은 공통 finite
named/hex 검증, label/clabel은 nonempty
문자열입니다. clabel은 요청한 spectrogram colourbar에만 적용합니다.
Citation/href는 선 label을 요구하고 기존 safe-reference 검증과 SVG link/
PGF macro를 재사용합니다.
Float64 window/detrend/FFT 자체는 작은 실제 bin을 영으로 반올림할 수 있습니다.
미정의 mask는 물리적으로 정확한 영의 증거가 아니며 큰 dynamic range에서
정확/상대 FFT 오차를 보장하지 않습니다. 주파수별 정규화는 이미 계산한 nonzero
계수의 곱 underflow를 막는 것이지 FFT 내부 cancellation을 없애는 기능이 아닙니다.

