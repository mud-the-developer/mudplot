# Matplotlib / Seaborn 기능 지원 범위

*[English](FEATURE_COVERAGE.md)*

## 목표와 비교 기준

목표는 Matplotlib·Seaborn이 제공하는 **그래프와 통계 시각화의 사용 범위**를
mudplot에서도 지원하는 것입니다. 동시에 논문용 기본 스타일, 편집 가능한 spec,
재현 가능한 출력을 유지합니다. **그래프 이름이 있다는 것만으로 기능이 동등한
것은 아닙니다.**

현재 checkout(1.0.0 기반 + Unreleased bar·`publication`·v1.1 첫 원자료 통계 범위)을
공식 Seaborn **0.13.2**, Matplotlib **3.11.2** 문서와 정적으로 비교했습니다.
이 버전은 기능 비교 기준일 뿐 의존성 하한 변경이 아닙니다. 기존 1.x 계약의
Python 3.10 / Matplotlib 3.8 / NumPy 1.23 지원을 유지합니다.

판단 근거는 [layer registry](../mudplot/capabilities.py),
[직렬화 모델](../mudplot/spec.py), [공개 builder](../mudplot/api.py),
[renderer](../mudplot/_render.py)·[공통 통계 effect](../mudplot/_estimate.py)입니다.
[호환성 정책](COMPATIBILITY.ko.md)도 함께 적용합니다.

- **부분 지원:** 관련 그림은 그릴 수 있지만 주요 옵션·통계 계산·구성이 빠짐.
- **미지원:** 전용 선언적 기능이 없음. 사용자의 전처리·수동 조합은 구현으로 세지 않음.
- **Python 직접 사용:** 반환된 Matplotlib Figure/Axes에서 가능하지만
  spec·undo/redo·JSON·CLI·editor 왕복에는 반영되지 않음.

현재 등록 layer는 **37종**입니다. 기능명 개수만으로 지원률을 계산하지 않습니다.
아래 표는 주요 격차이며 upstream의 모든 인자를 열거한 완전한 명세는 아닙니다.

## 1. Seaborn 기능 비교

| 기능 | 현재 상태 | 부족한 범위 |
| --- | --- | --- |
| `scatterplot` | 부분: 기존 group/c·typed 독립 범주/숫자 hue/size·범주 style·순서/전체 범위/비데이터 guide 범례 | semantic colorbar/outline/date/y2·line/facet 공통 매핑·추가 norm; 지름→면적 의미를 명시하며 전체 동등성 아님 |
| `lineplot` | 부분: 숫자 x별 named 점별 추정/가중/x별 unit CI·독립 원본 hue/size/style 곡선·stroke두께/marker-dash/공통범위, 원자료 line 유지 | 전체 궤적/동시 구간·날짜/범주x/y2/raw-line매핑/colorbar/자동facet; upstream 전체 수치 동등성 아님 |
| `histplot` | 부분: 명시적 가중 공통-bin count/frequency/확률/percent/density·공통/곡선별 정규화·누적 적분·그룹 stack/dodge·layer/stack step·v/h/관측 log, 기존 hist 보존 | step+dodge/채운 step·fill/poly/discrete/자동 규칙·2변량 가중 통계/KDE/날짜/y2; 원자료 폭만 |
| `kdeplot` | 부분: typed 가중 단변량 밀도/CDF·2변량 전체 공분산/native 등고선/채우기·bandwidth/범위/grid/공통 질량·격자 조건부 HDR/raw-unit log 표시, 기존 fit 보존 | 2D 누적/colorbar/절대 수준/전체 공간 HDR 보장/multiple/다른 커널/callable/날짜/y2/log fit; 자체 의미이며 upstream 전체 수치 동등성 아님 |
| `ecdfplot` | 부분: 반복값/가중 right-continuous ECDF·strict 보완형·곡선별 proportion/percent/count·그룹/순서/선·v/h·양수 log 관측값 | 연속 hue/size/style/date·y2/2-D·임의 kwargs; 유한 관측 범위만 표시 |
| `rugplot` | 부분: x축 눈금 | y축, 높이·방향·semantic 옵션 |
| `stripplot` | 부분: 재현 가능한 x jitter, group | 범주×hue 중첩, dodge/order/native scale, 가로 방향·jitter 옵션 |
| `swarmplot` | 부분: 매 draw 원형 packing, 순서/hue/dodge/방향·layout/DPI/양수 log 값, 숫자 native/log 범주·numeric/categoricalsize매핑/guide; 과밀 행 보존/보고 | Style/date/shared/facet의미·임의marker/다른layer충돌; 유효 행 2000개 상한 |
| `boxplot` | 부분: 범주×hue/배치/native log·IQR/분위수 whisker/notch·mean/fliers·독립 typed body/whisker/cap/median/mean/flier 스타일·data/axis 통계 | precomputed bxp·bootstrap median CI·cap 배치·임의/hue별 kwargs |
| `violinplot` | 부분: 범주×hue/native log·상대 가중 Gaussian/역 ECDF 표시/질량 폭·bandwidth/grid/범위·inner 4종/None·두 hue split·width/area/count·명시적 data/axis fit | callable KDE·임의 hue split/inner kwargs·추가 size/style; 가중 step 분위수와 기존 선형 분위수는 다름 |
| `boxenplot` | 부분: 셀별 letter value/깊이/폭·범주/hue/native log·독립 typed body/median/flier 스타일·data/axis 분위수 | 가중치·임의/띠별/hue별 구성 요소 kwargs·추가 매핑; 이름 깊이 최대 32 |
| `pointplot` | 부분: raw/log-fit 추정/구간·가중/단위 CI·native/log 간격·순서/hue/방향/dodge·빈 셀 선 끊기 | axis log sum/count·추가 추정/semantic/style/date·native/log y2 |
| `barplot` | 부분: raw/log-fit 추정/구간·가중/단위 CI·native/log 간격·양수 log baseline·방향/gap/라벨; precomputed bar 별도 | axis log sum/count·추가 추론/semantic/date·native/log y2 |
| `countplot` | 부분: 전체 분모 count/비율/percent·native/log 범주 간격·명시적 log baseline·방향/gap/선형 stack/라벨 | 가중 count·log 값축 stack/stat_scale·추가 정규화/semantic/date |
| `regplot` | 부분: 기존 다항식 + 설정형 poly/log-x/Huber/binomial-logit/LOWESS·선택rawgroup·상대가중poly/logx점적합/rawresidual;advanced는optionalextra | WeightedCI/bootstrap/advanced-modelCI·partial residualization·추가 fit/scatter. [범위](REGRESSION.ko.md) 참고 |
| `residplot` | 부분: regplot residual mode·원래 y-row prediction·zero guide·group/facet별 fit | 별도 residual trend·out-of-sample/deviance 진단·추론. [범위](REGRESSION.ko.md) 참고 |
| `heatmap` | 부분: legacy imshow + opt-in mask/원자료 주석·포맷/행열 label·명시/robust/log/중심 색상 범위·정사각 셀/경계 | 사용자 annotation 행렬·추가 norm/rotation/colourbar·clustering. [범위](HEATMAP.ko.md) 참고 |
| `clustermap` | 부분: 행/열 linkage·제공 트리/optimal leaf·정렬 dendrogram/mask/label/색 strip·sample z-score/min-max, optional SciPy | 여러 색 track/legend·결측·interactive cut·custom metric/layout. [범위](CLUSTERMAP.ko.md) 참고 |
| `relplot`/`displot`/`catplot`/`lmplot` | 부분 구성: 지원하는 2-D 템플릿의 terminal facet()·row/col 분할·wrap/공통 축·semantic domain | 전체 builder군·live template mapping·legacy c/colorbar·figure 통합 범례·추론 확장 |
| `FacetGrid` | 부분: row/col materialization·공통 축/semantic domain·raw group | Live mapping·넓은 grid 설정. [Facet 제한](FACETS.ko.md) 참고 |
| `PairGrid`/`pairplot` | 부분: numeric pair matrix·raw scatter·histogram/KDE/ECDF대각선·쌍별결측·이름기반값축 | Corner/semantic/가중/complementaryCDF/중첩grid. [Pair 범위](PAIR_GRID.ko.md) 참고 |
| `JointGrid`/`jointplot` | 부분: raw scatter/regplot 또는ungroupedhist2d/hexbin(colorbar=False)과pairedhistogram/KDE/ECDF연결·원자료보존 | Semantic/c/가중/complementaryCDF/groupedbinned·중첩구성·추가layout. [Joint 범위](JOINT_GRID.ko.md) 참고 |
| 테마·팔레트·범례·despine | 부분 | 추가 context, upstream 팔레트/colormap 선택, 범례 열·공통 매핑 |
| `seaborn.objects` | 일부 mark와 비슷한 기능만 있음 | 통계 transform/move/scale 합성; 동일 object API는 미지원 |

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
group/c/스칼라 충돌·colorbar/outline/date/y2/line/facet은 첫 범위에서 거부합니다.
넓은 제어는 계획에 유지하고 기존 c/colorbar는 작동합니다.85개 테스트로 수식/
도형/전체 범위/mask/엄격한 JSON/타입/editor/export/기존 호출/RNG를 검증했습니다.
[실행 예제](../examples/scatter_semantics.py).

### 숫자 x별 집계선 범위

Lineplot은 predictor/hue 셀별 공통 named 추정·가중 평균/행 쌍 CI·x 안의
계층적 unit bootstrap을 사용합니다. 점별 구간이지 동시 신뢰대역/전체 궤적
resampling이 아닙니다. Native 선·면/오차막대는 숫자 predictor 간격을 유지하며
가로는 표시만 바꿉니다. 기본 오름차순, 명시하면 hue별 첫 관측 순서입니다.
면은 단조 x를 요구하고 구간 없는 셀에서 끊으며 가짜 singleton CI가 없습니다.
Data/log10 response fit·양수 raw/log predictors·계산 끝점 오류를 지원하고 clip하지
않습니다. 면 alpha는 정확히 덮어쓰며 기본 .2*line alpha, cap/stroke는 bars만
받습니다. 공유 계약의 결측/0 행 처리·local seed를 쓰며 새 의존성/global RNG가
없습니다. 독립 추정/구간/bootstrap/unit/도형/엄격한 설정/core/JSON/editor/export
테스트 66개와 기존 line 기본값/순서 회귀를 검증했습니다. 날짜/범주 x/y2/dodge/
order/callable은 미지원이며 opt-in 독립 매핑은 위 범위에 설명했습니다.
[실행 비교](../examples/line_estimates.py).

### 가중 2변량 KDE 조건부 격자 HDR 범위

Kde2d/KDE2DSpec은 x/y 가중 행 쌍·전체 unbiased 공분산·effective n과
2D Scott=Silverman=`n_eff**(-1/6)`을 사용합니다. 가중치는 복제 횟수가 아니며
cut/clip은 평가만 제한합니다. 공통 질량에는 건너뛴 단일값 hue를 포함하고
공통 격자는 pooled 범위/조건부 공분산입니다. 부족/일직선/수치 rank 결손을
경고로 선택하며 가짜 bandwidth/jitter/등고선/범례 없이 건너뜁니다.

Levels는 유한 격자 안의 trapezoidal node 고밀도 질량을 포함하는 조건부 비율이며
동률을 모두 셉니다. Clip/격자 변경은 문턱을 바꾸지만 밀도를 재정규화하지
않습니다. 근사 영역이지 신뢰구간/전체 공간 확률 보장이 아니며 해결되지 않는
동률/극단 문턱은 오류입니다. Native 선/단색 단계별 면·정확한 alpha/outline/width·
hue dash/hatch/reference와 데이터 없는 명시적 범례 proxy를 지원합니다. 두
관측 축 모두 양수 관측/범위로 raw-unit log 표시하며 Jacobian/log fit은 없습니다.
크기를 맞춘 중심 공분산·안정적인 곱/비율·bounded 32×1024 point-row 평가를
사용하며 SciPy/전체 격자×행 행렬이 없습니다. 유효 행 10000·축당 node 256·(0,1)
levels 16을 제한하고 범위/밀도/격자 질량/문턱 오류를 알립니다. 누적/orient/날짜/
y2/colorbar/다른 커널/callable/절대 문턱/자동 보정/stack/multiple/kwargs는 미지원입니다.
[실행 예제](../examples/kde2d_semantics.py).

### 가중 단변량 Gaussian KDE 첫 범위

Strict KDESpec을 명시하며 None은 기존 비가중1.06*sample-SD*n**(-1/5)·200-point/
상수 fallback을 유지합니다. 상대 행 가중치는 복제 횟수가 아니며 unbiased
covariance와 effective n=1/sum(p**2)를 정의합니다. Scott/Silverman 또는 양수
공분산 factor·bw_adjust·bounded grid/cut/clip을 지원합니다. Common_norm 분모는
건너뛴 단일값 hue도 포함한 유효 선택 질량 전체 또는 각 곡선입니다. Cut/clip은
평가 범위만 제한하며 fit 행/꼬리 정규화를 바꾸지 않습니다. 실수축 전체 면적/
끝은 비중/1이지만 표시 꼬리는 잘릴 수 있습니다. Common_grid는 pooled 가중
범위와 곡선별 대역폭을 사용합니다. 누적은 -infinity부터의 해석적 Gaussian CDF
합이며 격자 시작점/적분 합/정확한 경험적 CDF가 아닙니다.

결측/0 가중치/선택 밖 hue를 함께 제외하고 non-bool 유한 숫자 관측값·비음수
가중치를 요구합니다. 빈 hue는 색상/스타일 자리만 예약하고 단일값 그룹은 경고를
선택하며 가짜 bandwidth/CDF/범례 없이 건너뜁니다. 가중치/중심 좌표의 크기·양수
cross-product 공분산 보정·인접 값 low bits·정확한 bounded 양수 합으로 극단 값을
다루고 계산 범위/대역폭/높이가 비유한/빈/해상도 부족이면 오류로 알립니다.
Primary2D 선/채우기 v-h·정확한 alpha/outline/width·hue dash/hatch/reference를
지원합니다. Log 표시에서도 관측/평가 범위 양수와 원자료 밀도 단위이며
Jacobian/log fit 없이 높이 축은 선형입니다. 2변량/contour/stack/multiple/날짜/y2/
callable/다른 커널/stat_scale/구간/kwargs는 이 단변량 KDE API에서 미지원입니다.
[실행 예제](../examples/kde_semantics.py).

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
해칭/선 모양 자리만 유지합니다. Primary2D 막대/step·v/h·양수 관측 log 축에서도 원자료 폭이며
높이 축은 선형이며 alpha/outline/reference를 지원합니다. Multiple='layer'는
원래 bin을 겹치고, 그룹별 'stack'은 hue 순서대로 높이를 쌓으며 'dodge'는 빈
예약/범위 밖 hue까지 포함한 모든 자리로 원자료 폭을 나눕니다. 높이·정규화·
누적 의미는 그대로입니다. Density/frequency 분모는 원래 bin 폭이므로 dodge는
높이 보정 없이 표시 면적을 줄입니다. 곡선별 정규화 후 stack도 원래 분포들을
더하며 pooled 분포로 재정규화하지 않습니다. Stack의 비유한/소실 양수 증가분과
해상도 부족 dodge 자리는 모든 도형 생성 전에 거부합니다. Element='step'은 관측
hue당 하나의 빈 native stairs 윤곽입니다. Layer는 0에 닫히고 stack은 절대 윗선과
이전 baseline을 둘러쌉니다. 경계/높이/통계는 그대로이며 빈 hue의 테마 선 모양/
색상 자리·edge_color 선 색상과 0까지 정확한 alpha/두께를 지원합니다.
Step+dodge·채운 step·임의 step dash·fill/poly/discrete/자동 bin 추정/KDE/2변량/
날짜/y2/구간/임의 kwargs는 미지원입니다.
In-range 분모를 명시한 첫 범위이며 upstream 전체 동등성이 아닙니다.
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
값·가중치는 bool을 제외한 유한 숫자, 가중치는 비음수입니다. 비율은 크기를 맞춘
행 질량을 float expansion으로 누적하여 중간 tie 반올림의 비단조를 피하고,
보완형은 1-F가 아닌 오른쪽 합으로 작은 꼬리를 보존합니다. Proportion/percent는
가중치 총합 overflow를 피하고 raw count overflow는 곡선별로 오류입니다. 빈 hue에는
도형/범례를 만들지 않으며 순서로 공통 색상/선 자리를 예약합니다. Primary
Cartesian2D·v/h·양수 log 관측 축/선형 질량 축·정해진 선/alpha 스타일·reference
metadata 하위 범위입니다. Bin/KDE/fit·구간/Kaplan-Meier/censoring·마커·날짜/
2-D/y2/연속 semantic 매핑·임의 kwargs는 미지원입니다.
[실행 예제](../examples/ecdf_semantics.py),
[Matplotlib 기준](https://matplotlib.org/3.8.0/api/_as_gen/matplotlib.axes.Axes.ecdf.html),
[Seaborn 기준](https://seaborn.pydata.org/generated/seaborn.ecdfplot.html).

### 공통 통계: 첫 v1.1 구현 범위

기존 `.bar()`는 **미리 계산된 값**을 그리는 의미를 유지합니다. 새 `barplot`,
`pointplot`, `countplot`은 원자료와 `StatSpec`을 저장하고 공통 NumPy effect에서
수치를 계산합니다. mean/median/sum/min/max/count estimator와 SD·표본평균의
SEM·관측값 PI·seeded percentile-bootstrap CI를 지원합니다. count는 구간을
사용하지 않고 SEM은 선택한 통계 좌표의 평균에만 적용합니다(기본 raw 산술평균,
명시적 log 평균은 아래 범위). 기본 bootstrap은 독립 행이며,
`weights`는 평균의 값·가중치 쌍 CI, `units`는 단위→단위 내부 행의 2단계
bootstrap을 지원합니다. 가중치는 추출 확률이 아니며 0 가중치 행은 제외합니다.
점 추정값은 관측 행 기준이며 동일 가중 단위 평균이 아닙니다. 필요한 열의
결측 행은 제외하고 관측값·단위가 2개 미만이면 구간을 경고와 함께 생략합니다.
`order`/`hue_order`로 범주를 선택·정렬하고 빈 자리를 유지합니다. 선형축의
가로 방향·bar gap/값 라벨·count 비율/percent·stack을 지원하며 count 분모는
범주·hue 전체의 선택된 유효 행입니다.
**부분 구현이지 Seaborn 전체 동등성이 아닙니다.** Native/log는 아래 범위로
확장했고 임의 callable estimator·추가 추론/매핑은 남아 있습니다.

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
맞게 실제 구간 끝을 피합니다. 누적 count는 선형 값축·baseline 생략만 지원하되
native/log 범주·전체 분모·중심 라벨은 유지합니다. 새 범위는 primary 2-D만,
기존 선형 ordinal y2는 유지합니다. 자동 scale 추론·callable·전체 동등성은 아닙니다.
[실행 예제](../examples/statistical_scales.py).

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
서로 다른 레이어의 충돌 보장은 아닙니다. 과밀 시 gutter에 행을 보존하므로
겹칠 수 있고 warn_thresh 기본 .05, 0이면 모든 과밀을 알립니다.
숫자 native/log 범주 축은 지원하며 임의shape/style/date매핑·y2는아직미지원입니다.

Opt-in `semantics={"size": "mass"}`는선택layer-localdomain과정확한지름guide의numeric역할하나를
추가합니다. Missing size도category/value/hue와같은cohort에서제외하고norm은filter가아닌clipping입니다.
Facet/dropna/namedscale/semantic-hue-style은이subset에서거절합니다. [정확한범위](SWARM_SIZE.ko.md).
Categoricalsize는관측/명시levelrank와size_order선택·예약크기/관측만guide를사용합니다. Bool/numeric은
별도key이고최대64개명확한label입니다. [Categorical범위](SWARM_CATEGORICAL_SIZE.ko.md).

반환Matplotlibcollection의native `set_sizes`(면적pt²)/linewidth배열(pt)편집은각쌍의반지름합과
각점의gutter여유로실제DPI/layout/scale에서다시배치합니다. 보존행개수이하의비어있지않은유한비음수
배열을지원하고짧은배열은순환하며긴배열은점을추가하지않고거절합니다. 표현불가packing기하는offset변경
전에실패하고oversized/충돌행은보존·한번씩세며기존warn-once를유지합니다. Artist편집만해당하며
LayerSpec/JSON을변경하지않습니다. 위별도numericSemanticSpec매핑이직렬화할size열의declarative경로입니다.

### 첫 letter-value 범위

`boxenplot(value, group=category)` 또는 `boxenplot(category, value, group=hue)`는
선형 보간한 원자료 분위수이지 신뢰구간이 아닙니다. tukey/proportion/
trustworthy/full의 네 규칙은 Seaborn 0.13.2의
[LetterValues 수식](https://github.com/mwaskom/seaborn/blob/v0.13.2/seaborn/_statistics.py)을
따릅니다. 이름 깊이는 최대 32, 정수는 1..32이며 Full은 min/max까지 포함합니다.
Exponential/linear는 깊이를 폭에 반영하고 area는 full의 확장 꼬리까지 실제
확률 질량/띠 높이를 셀별 정규화합니다. 높이 0인 area 띠의 폭은 0, 모두 같은
값이면 exponential 폭입니다. 이 반복값/full-area 정책을 명시하며 upstream과
모든 수치가 같다고 주장하지 않습니다. 중앙값과 바깥 실제 관측점의 가시성·
스타일을 지원하며 순서의 빈 자리·셀별 공통 hue 색상/해칭을 유지합니다.
숫자 native/log 축과 명시적 data/axis 통계를 지원하며
weights/units·임의 구성 요소 kwargs는 아직 미지원입니다. [실행 가능한 비교](../examples/letter_value_categories.py).

### Box/violin 범주형 하위 범위

한 열 `.box(value, group=category)` / `.violin(value, group=category)`의
native 1-based 위치는 유지합니다. y를 추가하면 범주 x/값 y, group=hue로
중첩하며 방향은 인자 의미를 바꾸지 않습니다. 필요한 결측 행은 함께 제외하고
order의 빈 자리에는 도형을 만들지 않습니다. 숫자 dodge는 전체 hue offset 폭
(None 자동·0 겹침), gap은 할당된 body 폭을 줄이는 비율입니다. whisker는
native IQR/분위수 규칙의 관측값 끝점이지 CI가 아닙니다. notch는 결정론적
Gaussian median 근사입니다. violin은 native Gaussian KDE·각 violin 폭
정규화·관측 min/max 범위입니다. 숫자 native/log 범주와 양수 log 값의
primary 축을 지원하지만 upstream 전체 동등성을 뜻하지 않습니다.

### 독립 box/boxen 구성 요소 첫 범위

Box는 typed body/whisker/cap/median/mean/flier, boxen은 body/median/flier만
지원합니다. 생략 속성은 기존 native/layer/hue를 유지하고 구성 요소가 shorthand를
덮어쓰되 관측값·통계·좌표는 바꾸지 않습니다. Body 색은 hue 기반색을 대체하면서
letter-value tint 계층을 유지합니다. Alpha는 정확히 0/1도 적용하고 빈 hatch는
중복 해칭을 끕니다. 선 stroke와 marker 채움/윤곽은 독립입니다. Mean은
showmeans=True가 필요하며 숨긴 flier/boxen median의 스타일은 거부합니다.
명시적 body/cap 스타일은 ambient rc에서 숨긴 box artist도 활성화합니다.
알 수 없는 nested 키/타입·역할/값 제약은 설정을 버리는 대신 오류로 알립니다.
색상/선/marker/크기를 제한하며 callback·임의 kwargs·precomputed bxp·띠/hue별
매핑·새 추론은 없습니다. JSON/schema/actions/editor·가로/세로/native log·
좌표 보존을 새 테스트 48개로 검증했습니다.
[실행 예제](../examples/distribution_components.py).

### Violin inner/밀도 첫 범위

이름 기반 box/quart/point/stick 또는 None inner, 선택·예약 hue 정확히 두 개의
split, width/area/count·대역폭/범위 제어를 JSON/actions/editor/render에 연결했습니다.
기본 legacy 중앙값/width/cut0를 유지하며 showmean/median/extrema 플래그는
legacy에서만 지원합니다. Point/stick은 유효 선택 행 10000개까지 샘플링 없이 보존합니다.

Area는 fitted-coordinate 공통 peak 기준이지 잘린 도형 면적의 동일성 보장이
아닙니다. Count는 peak 정규화 후 셀 n/기준 최대 n을 곱합니다. Common_norm=False는
hue 내 범주, True는 전체 셀/hue를 비교하며 area/count에서만 지원합니다. Cut은
[0,10] bandwidth, clip은 원자료 finite/None 경계로 support만 제한하고 fit 행/
개수/inner 관측값은 제외하지 않습니다. Split 반쪽은 공통 seam을 유지하고 gap은
바깥 폭만 줄이며 양수 dodge는 거부합니다. 빈/단일 값 셀은 정직하게 처리하고 모든
native 도형의 log 역변환을 적용합니다. Callable KDE·임의 hue split·inner kwargs·
추가 매핑은 아직 미지원이며 상대 가중 KDE/표시는 아래 별도 범위입니다. [실행 예제](../examples/violin_semantics.py).

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
| line/scatter/step/errorbar/band | 부분 | 전체 artist 옵션, 유한 hlines/vlines, 일반 fill/span, 가로 band, 비대칭 x 오차 |
| bar/pie | 부분 | barh, stacking/bottom/align, 막대별 스타일·값 라벨, pie annotation·wedge/text 옵션 |
| stem | 부분: 수직numericprimary/y2/rawbaseline·원본순서/반복위치·양수log | Horizontal/group/facet/semantic미지원. [범위](STEM.ko.md) |
| stairs | 부분: 주어진높이/명시N+1edge·수직outline/rawbaseline/linearprimary-y2 | Rebinning/fill/open/log/group/facet미지원. [범위](STAIRS.ko.md) |
| eventplot | 부분: 단일numerictrain·수직rawoffset/length·linearprimary-y2 | Group/facet/log/date미지원. [범위](EVENTPLOT.ko.md) |
| broken_barh | 부분: start/duration·단일rawbottom/heightband·겹침보존·linearprimary-y2 | Date/group/facet/log미지원. [범위](BROKEN_BARH.ko.md) |
| hist/box/violin/ECDF | 부분: 전용 가중 ECDF·proportion/percent/count·보완형·v/h, 그룹 histogram stack/dodge·빈 layer/stack step | Histogram step+dodge/채운 step/fill/poly/discrete/자동 bin/2변량, precomputed box 통계와 추가 분포 옵션 |
| image/contour | 부분 | 좌표 grid/extent, mask, RGB(A) 이미지, pcolor/pcolormesh/spy와 contour 상세 설정 |
| triangulated field | 미지원 | triplot/tripcolor/tricontour/tricontourf/trisurf |
| vector field | 부분: 2D quiver | streamplot/barbs, 추가 vector 설정과 3D quiver |
| 3D | 부분: scatter/line/단위 grid surface/wireframe | 명시적 surface 좌표, trisurf·bar·contour·quiver·voxel, camera/aspect |
| 신호·스펙트럼 | 미지원 | spectrogram, PSD/CSD/coherence, magnitude/phase spectrum |
| 축·레이아웃 | 부분: 일반 grid·비율·공유 축·y2·polar/3D | 실제 시간축(현재 ISO 문자열은 범주), locator/formatter, 추가 scale 설정, 보조 x축, inset/nested/mosaic |
| 색상·범례 | 부분: LCH colormap·자동 선형 정규화 | named/custom cmap, 고정/공유 vmin/vmax, log/centered norm, colorbar 위치·눈금, 범례 열·handler |
| 주석·patch·table | 부분: text/annotate·기준선 | 임의 patch/path/span/table, 좌표 transform·path effects |
| animation/widget/event callback/임의 artist | Python 직접 사용 | 별도 interaction 범위이며 자동으로 JSON 편집 기능이 되지는 않음 |

가능한 기능은 native Matplotlib을 활용하고 plotting engine을 다시 만들지
않습니다. 아직 필요하지 않은 두 번째 renderer 추상화도 만들지 않습니다.
새 API가 의존성 하한보다 늦게 도입되었다면 명시적인 guard/fallback이나
version gate가 필요하며 하한을 조용히 올리지 않습니다.

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
