# v1.1 개발 진행표

*[English](V1_1_PLAN.md)*

목표는 **v1.1**이며 [기능 비교표](FEATURE_COVERAGE.ko.md)의 그래프·통계 사용
범위를 확장합니다. 개발 중인 계획이지 릴리스 발표나 upstream 전체 동등성
달성 표시는 아닙니다. 실제 release gate 전에는 package/editor 버전을 1.0.0으로
유지합니다. 이 진행표 자체가 tag 생성이나 배포 승인은 아닙니다.

## 순서별 배치

- [x] **B0 — Bar 시각적 기반:** 제공된 SD·비대칭 구간, 독립 오차선/캡,
  publication 테마, 재현 가능한 비교 이미지.
- [x] **B1a — 공통 통계·원자료 첫 범위:** 이름 기반 estimator,
  SD/평균 SEM/PI/seeded bootstrap CI, barplot/pointplot/countplot.
  추정값 밖의 구간, 결측치·관측값 1개, JSON/editor, 수치·artist·참조
  테스트와 실제 예제 검증(2-D 선형·ordinal 축).
- [x] **B1b — 통계 확장 범위:** 값·가중치 쌍의 평균/CI,
  단위→단위 내부 행의 2단계 재표본화와 명시적인 가정,
  count/proportion/percent 정규화. 안전한 이름 기반 계산만 사용.
- [x] **B2a — 통계 레이어의 범주형 배치:** 가로 방향, order/hue order,
  빈 범주 자리 보존, dodge/gap, 누적 count와 bar/count 숫자 라벨.
- [x] **B2b1 — 첫 box/violin 범위:** 선택형 범주/값 열, hue 중첩,
  순서/방향/width/gap/숫자 dodge, native box 요약·결정론적 notch,
  violin 대역폭/grid·mean/median/extrema 옵션.
- [x] **B2b2 — 첫 swarm 범위:** 매 draw의 원형 화면 좌표 packing,
  방향/순서/hue/dodge, 실제 layout/DPI·양수 log 값축,
  모든 행 보존과 명시적 과밀 보고.
- [x] **B2b3 — 첫 letter-value 범위:** boxenplot 선형 보간 분위수,
  이름/정수 깊이·네 가지 규칙, exponential/linear/area 폭, 중앙값/꼬리 표시,
  범주/hue 배치와 엄격한 옵션 검증.
- [x] **B2b4 — 분포 native/log 첫 범위:** box/violin/boxen/swarm 숫자 native
  범주·log 좌표 간격·양수 log 값축, 명시적 data/axis 통계·KDE,
  기존 기본값 보존과 공통 축 충돌 검증.
- [x] **B2b5 — Violin 의미 첫 범위:** inner 4종/None, 두 hue split,
  area/count/width와 정규화 기준, 대역폭 배율·범위 제한 cut/clip.
  기본값·log/빈/단일 값 보존과 엄격한 옵션 검증.
- [x] **B2b6 — 독립 구성 요소 첫 범위:** typed box body/whisker/cap/median/mean/
  flier·boxen body/median/flier 스타일, 역할/값/가시성 검증, 기존 default·hue/tint
  계층·native/log 통계와 좌표 보존.
- [x] **B2b7 — 통계 native/log 첫 범위:** bar/point/count 숫자 실제 위치·간격,
  양수 log 값·명시적 log-fit 추정/구간·원자료 baseline·count/라벨 의미,
  엄격한 제한과 기존 ordinal 기본값 보존.
- [x] **B2b8 — 가중 violin:** 상대 공분산/effective n·역 가중 ECDF 표시·
  질량 폭·행 쌍/native log 도형. 새 테스트 78개와 실제 TeX, Rust1.99/브라우저
  bridge 검증, 전체1923/최소1468 통과.
- [ ] **B2b — 범주형 나머지:** 추가 구성 요소·semantic·swarm
  size/style/date 매핑 옵션.
- [x] **B3a — ECDF 첫 범위:** 유한 가중 empirical step·반복값/오른쪽 극한,
  strict 보완형·곡선별 proportion/percent/count·그룹 색상/선 자리,
  v/h/log 관측 축·typed pure/JSON/editor 계약.
- [x] **B3b — Histogram 통계 첫 범위:** typed 공통 bins/가중 행 쌍,
  6종 통계·전체/곡선별 in-range 정규화·누적 적분·v/h/raw log,
  기존 기본값 보존과 새 테스트 95개.
- [x] **B3c — 설정 가능한 가중 단변량 Gaussian KDE:** strict 명시적
  bandwidth/grid/cut/clip·상대 공분산/effective n·전체/곡선별 질량/공통 grid·
  해석적 누적/채우기/v-h/raw-log 단위·단일값 skip·기존 동작과 새 테스트 125개.
- [x] **B3d — 가중 2변량 Gaussian KDE:** strict kde2d/전체 공분산·x/y
  가중 행 쌍/raw grid/log 표시·조건부 격자 HDR 등고선/채우기,
  특이값 자동 보정 없음. 새 module 129개+registry-param 1개.
- [x] **B3e — 숫자 x별 집계선:** 별도 lineplot·공유 named 점별 구간·x별
  가중/unit CI·정렬/면/막대/raw-log 계약. 테스트66개, 전체1990/최소1534와
  Rust1.99/실제 브라우저/bridge/TeX 검증 통과.
- [x] **B3f — 독립 scatter 매핑:** strict SemanticSpec·행 쌍 hue/size/style·
  명시적 종류/순서/전체 범위/비데이터 guide.85개 테스트와 전체2075/최소1619,
  Rust1.99/브라우저/TeX 검증 통과.
- [x] **B3g — 이름 기반 figure 공통 scatter 척도:** row ID 합집합·설정 일치/
  전체 범위/색 block·pooled 비데이터 guide 패널별 1회.36개 테스트와
  전체2111/최소1655, Rust1.99/브라우저/TeX 통과.
- [x] **B3h — 독립 lineplot 매핑:** 원본 tuple 곡선/공통범위·두께/marker/
  선택적 dash·행쌍 점별추론.48개 테스트, 전체2159/최소1703과
  Rust1.99/브라우저/TeX 통과. 승인한 foreground 재검증으로 exit receipt를
  확보했으며 이전 중단 로그는 통과 증거로 바꾸지 않고 보존합니다.
- [x] **B3i — Histogram 그룹 배치:** 명시적 layer/stack/dodge·원래 가중
  높이/정규화·빈 hue 순서 자리·v/h/raw-log bins를 유지하고 모든 도형 생성 전
  overflow/해상도 부족을 검사합니다. 새 회귀 테스트 48개.
- [x] **B3j — Histogram step 윤곽:** layer/stack의 빈 native stairs·기존
  가중 높이/경계·v/h/raw-log·빈 hue 선 모양 자리와 정확한 stroke를 지원합니다.
  새 회귀 테스트 43개와 엄격한 조합 검증.
- [x] **B4a — 자동 facet 첫 범위:** row/col/wrap materialization·panel filter·
  안정적인 선택 순서·셀별 추론·원래 행 ID 기반 공통 semantic domain과
  pure/action/JSON/schema/editor·실행 예제. [제한](FACETS.ko.md) 참고;
  FacetGrid/pair/joint 전체 동등성이 아닙니다.
- [x] **B4b — Raw group facet:** 기존 raw layer 8종의 hue 순서/자리를
  안정적으로 유지하며 통계 그래프로 자동 변환하지 않습니다. 중복/비단조 궤적·
  결측 구간·제공한 막대/오차·기본 unordered 동작을 보존합니다.
- [x] **B4c — Joint histogram 첫 범위:** terminal raw scatter/regplot과
  정렬된 세 패널·동적 쌍 `dropna`·원자료 보존·group 자리·density/측정값 축
  분리. [지원 범위](JOINT_GRID.ko.md) 참고.
- [x] **B4d — Numeric pair grid:** 쌍별 scatter/대각선 histogram·group 순서·
  동적 완전 관측·density y를 제외한 이름 기반 primary 값축 공유. API/action/
  schema/editor·예제 포함. [범위](PAIR_GRID.ko.md) 참고.
- [x] **B4e — 설정형 KDE grid:** Joint KDE 주변 분포·pair KDE 대각선,
  strict 복사 KDESpec·density/관측/축 보존·특이값 skip. Histogram 기본값은 유지하고
  grid의 weights/CDF는 명시적으로 거부합니다.
- [ ] **B3 — 관계·분포 나머지:** facet 조합 확장/넓은 line 추론,
  추가 histogram/KDE 표현과 semantic 설정.
- [ ] **B4 — 자동 구성 나머지:** live facet mapping/통합 guide·추가 pair/joint kind.
- [x] **B5a — Typed heatmap 표시:** mask/원자료 주석/label·linear/log/중심/
  robust 범위·정사각/경계·안전한 유한 colourbar. 기존 기본값/행렬을 유지합니다.
  [범위](HEATMAP.ko.md) 참고.
- [x] **B5b — 설정형 회귀:** raw residual/log-x/Huber/binomial-logit/LOWESS·
  conditioning·셀/group별 fit·optional statsmodels extra. 기존 polynomial과
  의존성 없는 구성은 유지합니다. [범위](REGRESSION.ko.md) 참고.
- [x] **B5c — 군집 heatmap:** optional SciPy 행/열 트리/optimal leaf·제공 linkage
  검증·표시 metadata/색 strip 정렬·z-score/min-max. 원자료를 유지합니다.
  [범위](CLUSTERMAP.ko.md) 참고.
- [ ] **B5 — 고급 통계·행렬:** 추가 heatmap/clustering 설정·가중/bootstrap/advanced-model
  CI·residual 진단/설정.
- [ ] **B6 — Matplotlib 범위:** 나머지 primitive/신호/vector/mesh/triangle/3D,
  축·정규화·범례·레이아웃 확장.

B1b는 B1a를 확장한 범위이며 upstream 전체 동등성이 아닙니다. weights는
평균과 구간 없음/값·가중치 쌍 CI만 지원하며 추출 확률이 아닙니다. units는
bootstrap CI만 지원하고, 추정값은 동일 단위 평균이 아닌 관측값 가중 결과입니다.
결측치/0 가중치 행은 제외하고 유효 행·단위가 2개 미만이면 경고 후 구간을
생략합니다. count 비율의 분모는 선택한 모든 유효 행입니다. 임의 callable과
미지원 조합은 명시적으로 거부합니다. 다른 배치를 돕는 작은 primitive는
먼저 추가할 수 있습니다. 이름 추가만으로 완료 표시하지 않습니다.

## 현재 체크포인트

**리뷰 5차에서 Rust JSON 계약 차이 두 건을 수정했습니다.** FIND-004는 serde
arbitrary_precision이 literal 예약-key object를 숫자로 바꾸는 문제, FIND-005는
Python이 현재 기본값으로 처리하는 version 생략을 Rust가 거부하는 문제입니다.
각각 unit exit101과 HTTP 실패를 먼저 재현했고 공통 경계에서 수정했습니다.
원본 property 이름 token 검사로 큰 정수/일반 문자열을 유지하며 version은 내장
기본값에서 가져오고 null/unknown을 허용하지 않습니다.

공유 fixture의 음성 spec19/action11·정상 spec2를 API/CLI/Python session/HTTP/
Rust JSON/raw/open에서 대조합니다. Version 외 음성 입력에는0.1을 명시하고
정상 suptitle은 서로 다르게 하여 다른 오류/stale state가 결과를 가리지 못하도록
corpus 자체에도 회귀 검사를 넣었습니다. Sdist의 smoke fixture 포함도 확인합니다.

기록한 Agg 계약은 **597통과, Windows조건2skip**, Rust native all-targets는
**lib13+main1통과/의도한 helper1ignored**이며 실제 HTTP/browser corpus도 통과했습니다.
Clippy-Dwarnings/fmt·Ruff200파일/format·Pyright·activeLSP6경로·계약·clean
sdist→wheel도 통과합니다. Compiler1.99 결과이지 MSRV1.88 검증이 아닙니다.
[대장](REVIEW_CHECKLIST_STATUS.md)에 환경/log/명령·종료 증거를 기록했고 JSON-02/06/07을
PASS로 닫아 **PASS11/RUNNING14/OPEN125**입니다. 전체 검토/릴리스/OS/보안/성능
보장은 아니며 version/tag/배포는 유지합니다. 전체 suite/최소환경/MSRV/Linux는 남았습니다.

### 이전 리뷰 4차

**리뷰 4차에서 DATA-02의 조용한 데이터 손실을 수정했습니다.** Positional ragged
row와 cursor description/행 길이 불일치를 pivot 전에 index/실제 수/기대 수가 있는
오류로 처리합니다. 수정 전7fail/1pass fixture를 확보했고 정상 값/순서/입력은
유지하며 padding/truncation/coercion은 넣지 않았습니다. [대장](REVIEW_CHECKLIST_STATUS.md)의
FIND-003을 참고하세요.

기록한 Agg 계약 검사는 **404통과, Windows조건2skip**, 최소 Python3.10/NumPy1.23
adapter는 **25통과, 2142deselected, 경고13**입니다. Ruff199파일/format·Pyright·
activeLSP4경로·계약 sync도 통과했습니다. Adapter의 missing→null과 strict
NaN/Infinity/범위 오류를 분리하고 큰 좌표/style/size의 출력/editor 실패 뒤 원래
파일/state/history/preview 보존과 복구를 확인했습니다. JSON-05는 PASS, DATA-02의
전체 형식/필수 열 매핑은 RUNNING으로 유지합니다. 상태는 **PASS8/RUNNING17/OPEN125**로
전체 검토/릴리스 승인이 아닙니다.

한 초기 회귀는 backend 미설정으로 Tk/Tcl 오류가 났고 제품 결함/통과로 세지 않았습니다.
Agg 재실행과 manifest는 phase4 증거에 기록했습니다. 원문 체크리스트·version/의존성/
tag/배포는 그대로이며 전체 suite/최소환경/MSRV/Linux/GUI/보안 감사는 남았습니다.

### 이전 리뷰 2/3차

**리뷰 2/3차의 한정 계약 검증을 마쳤습니다.** [증거 대장](REVIEW_CHECKLIST_STATUS.md)은
PASS7/RUNNING17/OPEN126입니다. 재귀적인 동일/상이 duplicate 거부 JSON-03,
signed 정수 구조 보존 JSON-04, 단일 파일 실패 격리 OUT-03을 Python/API/CLI/
editor/Rust/HTTP 실제 증거로 PASS 처리했습니다. JSON-06/07·OUT-04의 더 넓은
필드/플랫폼/자원 조건은 RUNNING입니다.

FIND-001(Rust registry 기대36/실제37, exit101)을 재현하고 연결 검사를 수정했습니다.
FIND-002는 Windows 읽기 전용 대상의 replace 실패 때 staging에도 읽기 전용 속성이
복사되어 .tmp가 남는 문제이며 JSON/PNG/PDF/SVG 네 경우 수정 전 실패를 확보했습니다.
io._atomic_destination에서 POSIX mode 복사만 non-Windows로 제한해 원본 bytes/
읽기 전용 속성을 유지하고 무관한 파일을 chmod하지 않습니다. 실제 Win32 delete-sharing
잠금·읽기 전용·잘못된 경로/디렉터리에서도 bytes/staging/Figure 보존을 확인했습니다.

기록한 2차는 Python338통과/Windows2skip·Rust lib11통과/의도한 helper1ignored와
실제 HTTP/browser fixture/state/preview 검증을 통과했습니다. Production 수정 후
3차는 **354통과, Windows조건2skip**이며 Ruff197파일/format·Pyright·계약·clean
sdist→wheel도 exit0입니다. 실제 Windows 잠금/읽기전용8경우도 통과합니다.
Manifest/JUnit/명령·종료/log/실제 수정 전 실패 요약은 대장의 temp 경로에 있습니다.
체크리스트 원문 SHA는 그대로입니다. Version/tag/배포는 바꾸지 않았고 이 대상 실행을
전체 suite/최소환경/MSRV/Linux/보안감사/성능/릴리스 gate 승인으로 확대하지 않습니다.

### 이전 리뷰 1차와 clustermap 통합

**사용자 리뷰 체크리스트를 반영했습니다.** 2026-10-16 원문은 그대로 보존하고
[150-ID 증거 대장](REVIEW_CHECKLIST_STATUS.md)에 구현/테스트 후보와 실제 결과를
분리했습니다. HEAD는 기준 c4f40ab와 같고 로컬 미커밋/새 파일은 별도 지문으로
기록합니다. Batch/listener/출력 실패 회귀 17개를 추가했고 기록한 core-contract
대상 검사는 **127 통과, Windows 조건 2 skip, exit0**입니다. 환경/tree hash·
JUnit·명령/종료 receipt는 대장의 temp 증거 경로에 있습니다. BASE-01과
STATE-04/05/06만 PASS이며 RUNNING20/OPEN126입니다. 이 범위에서 새 production
결함은 재현되지 않았으나 전체 150개 검증/릴리스 승인을 뜻하지 않습니다.

**리뷰 전 B5c clustermap 통합도 마무리했습니다.** [범위](CLUSTERMAP.ko.md) ·
[예제](images/clustered_profiles.png). Optional SciPy 행/열 linkage·검증된 제공
트리·optimal leaf·표시 표준화·label/mask/색 strip 정렬을 지원하고 원자료는
보존합니다. Nested GridSpec으로 보조 axes/제목 잘림을 해결하고 vector의 미세
위치차로 SVG clip ID가 바뀌지 않도록 배치를 고정했습니다. Registry37종이지
전체 plotting/통계 동등성을 뜻하지 않습니다.

당시 완료한 대상 검사는 **1240 통과, Windows2 skip**, Python 실제 브라우저
**30 통과**, 최소 Python3.10/NumPy1.23/Matplotlib3.8/SciPy1.10/
statsmodels0.14.1의 cluster+regression은 **92 통과, 2050 deselected, 경고13**
입니다. 새 리뷰 전용 테스트를 추가하기 전 결과이며 전체 체크리스트 실행이 아닙니다.
Rust HTTP/브라우저·Ruff/Pyright·계약·sdist→wheel/-S smoke·의존성 일치도 확인했습니다.
예전 데모22개에는 cluster=None만 넣어 의미가 같음을 assert했습니다. 선택 cluster
extra(SciPy>=1.10, all/dev 포함)를 추가했지만 필수 core는 비어 있고 package/
editor1.0.0·spec0.1·공개 자산/tag는 유지합니다. 전체 suite/최소환경·MSRV·보안
감사·Linux·TeX·성능·release provenance는 남아 있습니다.

### 이전 B5b 설정형 회귀

**B5b 설정형 회귀를 통합했습니다.** [API/제한](REGRESSION.ko.md) ·
[Residual 예제](images/regression_residual.png) ·
[Logistic 예제](images/regression_logistic.png) ·
[소스](../examples/regression_modes.py). Opt-in RegressionSpec의 poly/log-x/Huber/
binomial-logit/LOWESS와 원래 행 순서의 observed-minus-in-sample-fit/zero guide인
residplot을 제공합니다. Group/facet 선택 뒤 fit하며 원자료를 보존합니다. Residual
joint 템플릿은 raw-y 주변 분포를 잘못 표시하지 않도록 거부합니다. 기존
regression=None은 유지합니다.

명시적 optional regression extra(statsmodels>=0.14.1, all/dev 포함)를 추가하고
root/script lock을 갱신했습니다. 필수 core 의존성은 비어 있고 poly/residual/log-x는
기존 render만 사용합니다. Effect에서만 import하며 finite/model/수렴/분리 검사로
실패 시 기존 출력을 보존합니다. 설치 statsmodels의 explicit xvals/missing='raise'
무조건 오류 때문에 finite 검증 뒤 missing='none'을 쓰며 vendor는 수정하지 않았습니다.
Jitter/regularization/callable fallback은 넣지 않았습니다.

현재 core/render/schema/reducer/통계/property/Python-editor 대상 검사는 **1184
통과, Windows 조건 2 skip**, Python 실제 브라우저는 회귀 5종 열기·편집·SVG를
포함해 **29 통과**입니다. 최소 Python3.10/NumPy1.23/Matplotlib3.8/
statsmodels0.14.1의 회귀 검사는 **46 통과, 2050 deselected, 경고 13개**이며
전체 최소 환경은 아닙니다. 현재 statsmodels0.15.0 effect도 통과합니다. Rust
HTTP/실제 브라우저에서 5종 raw AddLayer 설정/PNG/SVG를 확인했고 uv pip check도
선택 의존성 환경이 일치함을 확인했습니다.

Ruff/Pyright·변경 경로 12개 active LSP·생성 계약·sdist→wheel/-S smoke를
통과했습니다. 계약/데모/갤러리를 재생성하고 남은 예전 데모 spec 22개에는 nullable
regression만 추가해 의미가 같음을 assert하고 raw JSON을 보존했습니다. 합성 질문별
그림 5개는 700px 글꼴/경계/글자 QA를 통과했지만 독립 가독성 평가는 아닙니다.
Package/editor1.0.0·spec0.1·공개 자산/tag/배포는 그대로이고 이번 기능은 Unreleased
source 범위입니다. 전체 Python/최소환경·Rust unit/MSRV·의존성 보안 감사는 미실행입니다.
가중/bootstrap/advanced CI·residual trend/진단·clustering과 B2b/B3/B4/B5/B6는 남았습니다.

### 이전 B5a typed heatmap

**B5a typed heatmap 옵션을 통합했습니다.** [API/제한](HEATMAP.ko.md) ·
[예제](images/heatmap_controls.png) · [편집 spec](images/heatmap_controls.mplot.json).
Opt-in HeatmapSpec으로 mask·원자료 주석/label·명시/log/중심/robust 색상 범위·
정사각 셀·경계를 지원합니다. 원래 유한 행렬을 바꾸지 않고 hidden 값을 색상 통계/
글자에서 제외합니다. Typed colourbar는 큰 값/아주 작은 log에서 안전한 명시 경계/
값을 사용합니다. Heatmap=None 기본 동작·layer 종류·필수 의존성은 유지합니다.

브라우저에서 기존 native 폼 fallback 문제도 확인했습니다. 연결 전 폼이 GET
URL을 썼고 POST로 바꾸면 no-referrer 때문에 null Origin으로 거부됐습니다.
공통 폼에 명시적 POST action과 same-origin referrer 정책(외부 전송 없음)을
적용했습니다. 기존 cross-origin/null-Origin 차단은 유지하며 JS를 끈 POST/Undo와
heatmap 열기·편집·SVG에서 전체 설정/원자료 보존을 확인했습니다.

현재 core/render/schema/reducer/통계/property/Python-editor 대상 검사는 **1138
통과, Windows 조건 2 skip**, Python 실제 브라우저는 **24 통과**입니다. 최소
Python 3.10·NumPy 1.23·Matplotlib 3.8 heatmap 검사는 **37 통과,
2013 deselected, 경고 15개**이며 전체 최소 환경은 아닙니다. Rust HTTP/실제
브라우저에서 typed mask/주석 action·행렬 보존·PNG/SVG를 확인했습니다. Ruff/
Pyright/active LSP/생성 계약 동기화·sdist→wheel/-S smoke도 통과했습니다.
계산 span 오류 때 기존 출력이 유지되는지도 검사합니다.

계약/데모/갤러리를 재생성하고 남은 예전 데모 spec 22개에는 nullable heatmap
설정만 추가해 의미가 같음을 assert하며 raw JSON 필드를 보존했습니다. 합성
예제는 선택한 700px 글꼴/경계/글자 QA를 통과했지만 독립 가독성/접근성 인증은
아닙니다. Package/editor1.0.0·spec0.1·tag/배포/의존성은 그대로이며 전체 Python/
최소환경·Rust unit/MSRV/의존성 감사는 남았습니다. 사용자 annotation 행렬·
clustering/추가 norm과 B2b/B3/B4/B5/B6 나머지 기능은 미완료입니다.

### 이전 B4e 설정형 KDE grid

**B4e 설정형 KDE grid를 통합했습니다.** Joint의 `marginal_kind='kde'`와 pair의
`diag_kind='kde'`에서 strict KDESpec/dict의 bandwidth/grid/support/정규화/fill을
사용하고 histogram 기본값은 유지합니다. 관측·원자료·축은 그대로이고 특이 fit은
기존 경고/skip 규칙을 따릅니다. Density만 지원하며 기본 밖 hist bins/stat·weights·
cumulative KDE는 거부합니다. [Joint](JOINT_GRID.ko.md) · [Pair](PAIR_GRID.ko.md) ·
[합성 예제 소스](../examples/kde_grids.py) 참고.

현재 core/render/KDE/schema/reducer/통계/property 대상 검사는 **965 통과,
Windows 조건 2 skip**, Python 실제 브라우저는 hist/KDE 열기·편집·SVG를 포함해
**22 통과**입니다. Python 3.10·NumPy 1.23·Matplotlib 3.8의 KDE-grid 검사는
**31 통과, 1982 deselected, 경고 13개**이며 전체 최소 환경은 아닙니다. Rust
HTTP/실제 브라우저에서 설정형 KDE joint/pair action·원자료·PNG/SVG를 확인했습니다.
Global Pyright와 변경 경로 10개의 active LSP는 clean입니다. 이전 imported helper
타입 보고는 KDESpec 경계에서 narrowing 후 재검증해 해결했으며 숨기지 않았습니다.

Ruff·생성 계약·데모/갤러리 재생성·sdist→wheel/-S import를 통과했습니다. 중첩
KDESpec action도 plain JSON으로 직렬화하며 wheel smoke는 optional dependency
없이 KDE grid를 재생합니다. 합성 편집/vector 예제 두 개가 선택한 700px 글꼴/
경계/글자 기준을 통과했지만 독립 가독성 인증은 아닙니다. Spec/의존성/package·
editor version/tag/배포는 유지합니다. 전체 Python/최소환경·Rust unit/MSRV/의존성
감사는 재실행하지 않았고 weighted/CDF/semantic/c/중첩 grid와 B2b/B3/B5/B6는 남았습니다.

### 이전 B4d pair matrix 통합

**B4d numeric pair matrix와 이름 기반 값축을 통합했습니다.**
[API/제한](PAIR_GRID.ko.md) · [이미지](images/pair_observations.png) ·
[편집 spec](images/pair_observations.mplot.json). `pair()`/`SetPairGrid`로 numeric
변수 2..8개의 raw scatter 행렬·typed histogram 대각선을 만들고 쌍별/단변량
완전 관측과 원자료를 유지합니다. `AxisSpec.share_id`와 `SetAxisShare`/
`share_axis()`는 측정값 축을 연결하되 대각선 density/count y는 공유하지 않습니다.
이름 공유와 figure 공유 mode·scale/명시 limits 충돌을 거부하고 기존 unnamed 축
동작은 유지합니다.

현재 core/render/schema/reducer/통계/property 대상 검사는 **809 통과, Windows
조건 2 skip**, Python 실제 브라우저는 **20 통과**입니다. Pair 파일의 9셀 열기·
셀 편집·SVG를 포함합니다. Python 3.10·NumPy 1.23·Matplotlib 3.8의 pair 검사는
**34 통과, 1948 deselected, 경고 13개**이며 전체 최소 환경은 아닙니다. Rust
HTTP/실제 브라우저에서 pair action→이름 축→PNG/SVG를 확인했습니다. Ruff/
Pyright/생성 계약 동기화·sdist→wheel 재빌드/import도 통과하고 wheel `-S` smoke는
optional dependency 없이 pair/joint 구성과 action 재생을 검사합니다.

900px 합성 예제를 확인하고 선택한 글꼴/경계/글자 겹침 기준을 통과했지만 독립
가독성 평가는 아닙니다. 데모/계약을 재생성하고 남은 예전 데모 spec 22개에는
nullable 이름 축 기본값만 추가해 파싱 의미가 같음을 assert했습니다. 원자료/
스타일은 버리지 않았습니다. Spec 0.1·package/editor 1.0.0·의존성·tag·배포는
유지하며 전체 Python/최소환경·Rust unit/MSRV·의존성 감사는 재실행하지 않았습니다.

Corner/KDE/semantic/가중/중첩 pair·추가 joint kind·통합 범례/live mapping과
나머지 B2b/B3/B5/B6 기능은 미완료입니다.

### 이전 B4c joint histogram 구성

**B4c joint histogram 구성을 통합했습니다.** [API/제한](JOINT_GRID.ko.md) ·
[이미지](images/joint_observations.png) · [편집 spec](images/joint_observations.mplot.json).
`joint()`/`SetJointGrid`는 raw scatter/regplot과 x/y 주변 histogram을 세 패널로
만들며 padding axes가 없습니다. Optional `PanelSpec.dropna=[]`로 원자료를 그대로
두고 같은 완전 관측 x/y/group 행을 동적으로 선택합니다. 공통 측정값 축이 density/
count 축과 섞이지 않으며 원래 label/style/reference·group 자리를 유지합니다.
Pair grid·semantic/c/가중/KDE/hexbin joint kind·중첩 grid는 남아 있습니다.

현재 core/render/schema/reducer/통계 대상 검사는 **761 통과, Windows 조건 2 skip**,
Python 실제 브라우저는 **19 통과**입니다. Joint 파일 열기·선택 패널 정확히 3개·
주변 분포만 편집·SVG를 포함합니다. 최소 Python 3.10·NumPy 1.23·Matplotlib 3.8의
joint 검사는 **41 통과, 1907 deselected, 경고 193개**이며 전체 최소 환경은
아닙니다. Rust HTTP/실제 브라우저 smoke에서 SetJointGrid·원자료·쌍 selector·
PNG/SVG를 확인했고 Ruff·Pyright·생성 계약·sdist→wheel 재빌드/import도 통과했습니다.
Wheel의 `-S` smoke는 optional dependency 없이 joint 구성/action 재생을 검사합니다.

데모/갤러리·계약을 재생성하고 남은 예전 데모 spec 22개에는 빈 `dropna`만 추가해
파싱 의미가 같음을 assert하고 raw JSON 필드를 보존했습니다. 예제 이미지를 확인하고
선택한 700px의 글꼴/경계/글자 겹침 기준을 통과했으나 독립 가독성 평가는 아닙니다.
계산 log-bin 오류 때 기존 출력을 유지하며 dropna semantic pool도 원래 행 ID를
보존하는지 검사했습니다.

의존성/version(package·editor 1.0.0, spec 0.1)/tag/배포는 바꾸지 않았습니다.
**아래 전체 2398 통과 기록은 joint 변경 전입니다.** B4c에서는 전체 Python/최소환경·
Rust unit/MSRV·의존성 감사를 재실행하지 않았고 B2b–B6와 릴리스 조건은 미완료입니다.

### 이전 B4b raw group facet

**B4b raw group facet을 구현했습니다.** [원자료 의미와 제한](FACETS.ko.md) 참고.
Line/scatter/bar/errorbar/band/stripplot/regplot/rug에서 셀별로 빠진 그룹까지
hue 자리를 예약합니다. 입력 궤적 순서·중복 x·결측 구간·제공한 막대 값과 연결된
오차를 유지하며 통계 builder로 자동 변환하지 않습니다. Unordered 기본값도 유지합니다.

현재 locked 전체 Python 검사는 **2398 통과, Windows 조건 2 skip, 경고 1개**이며
exit 0입니다(브라우저/TeX 포함). 앞서 중단된 시도는 통과로 세지 않았고 완료된
재실행을 근거로 합니다. 경고는 기존 극단 유한 ECDF 질량의 native ticker overflow입니다.
Raw/facet 대상 검사는 **82 통과**, Python 3.10·NumPy 1.23·Matplotlib 3.8의
raw-order 검사는 **31 통과, 1876 deselected, 경고 201개**입니다. 전체 최소 환경을
재실행한 것은 아닙니다. Rust HTTP/실제 브라우저 smoke에서 희소 raw group·원자료
보존·예약 hue 순서·통계 설정 미추가와 PNG/SVG 출력을 확인했습니다.

Ruff lint/format·Pyright·생성 계약 동기화·데모/갤러리 재생성·sdist→wheel 재빌드/
import를 통과했습니다. 의존성/spec version/package·editor version/tag/배포는
그대로입니다. 전체 최소환경·Rust unit·MSRV·의존성 감사는 남아 있고 legacy
c/colorbar facet·live mapping·통합 guide·pair/joint와 다른 B2b/B3/B5/B6는 미완료입니다.

### 이전 B4a facet 범위

**B4a 자동 facet 첫 범위를 구현했습니다.** [API/제한](FACETS.ko.md) ·
[이미지](images/faceted_responses.png) · [편집 spec](images/faceted_responses.mplot.json).
`facet()`/`SetFacets`로 row/col/wrap 셀과 panel filter·공통 축·semantic domain을
만들고 셀별로 통계를 계산합니다. 원자료를 유지하며 범주/hue 자리와 원래 행 ID를
보존합니다. Python/action/JSON/schema/editor import/raw action 경로와 Rust의
HTTP/실제 브라우저 action→필터 패널→PNG/SVG도 확인했습니다. B4/B2b–B6 전체
완료는 아니며 legacy grouped series/c·live mapping·통합 guide·pair/joint grid와
다른 계획 기능은 명시적으로 남아 있습니다.

현재 locked 전체 Python 검사는 **2367 통과, Windows 조건 2 skip, 경고 1개**입니다
(기존 실제 브라우저·TeX matrix 포함). 경고는 극단적인 유한 ECDF 질량의 기존
native ticker overflow입니다. Python 3.10·NumPy 1.23·Matplotlib 3.8의 facet
대상 검사는 **51 통과, 1825 deselected, 경고 185개**이며 전체 최소 환경을 다시
돌린 것은 아닙니다. Ruff lint/format·Pyright·생성 schema/capabilities/reference
동기화·sdist→wheel과 Rust HTTP/실제 브라우저 smoke를 통과했습니다.

Spec version은 0.1이며 optional `PanelSpec.filters={}`가 추가됐습니다. 기존 spec은
필터 없이 동작합니다. 생성 계약/데모를 갱신하고 남은 예전 데모 spec 22개에는
빈 filter만 추가해 의미가 같음을 assert했습니다. 원자료/스타일을 버리지 않았습니다.
Facet 이미지를 확인했고 선택한 900px의 글꼴/경계/글자 겹침 기준을 통과하지만
독립 가독성 인증이나 모바일 배치는 아닙니다.

의존성·package/editor 1.0.0·tag·배포는 바꾸지 않았습니다. 전체 최소환경·Rust unit·
MSRV·의존성 감사는 이번에 재실행하지 않았고 전체 구현/릴리스 조건은 미완료입니다.

### 이전 갤러리/에디터 연결

갤러리/에디터 연결: 빌드한 사이트에서 새로 렌더링한 읽기 배치·편집 spec·로컬
리뷰/기준 문서로 이동할 수 있습니다. Python 에디터는 같은 builder의 완성 그림
초안 4개를 제공합니다. 선택은 Open 폼만 채우며 명시적 Open 전에는 현재 그림·
PNG·action 이력을 유지합니다. 실패한 import는 입력 초안과 기존 그림을 보존하고,
htmx의 페이지 본문 이력 캐시는 사용하지 않습니다. ID는 allowlist/개수 제한으로
검사하고 초안은 HTML escape합니다. 작업창 축소가 가독성 인증을 뜻하지는 않습니다.

현재 dashboard/editor/visual/lint/schema/layout/no-deps 검사 **227 통과**, 최소
환경은 **28 통과, 1797 deselected, 경고 13개**, 실제 브라우저는 **18 통과**입니다.
초안 선택→명시적 열기→편집→SVG와 빌드 갤러리 다운로드→file picker 열기를
포함합니다. 로컬 링크·builder/spec 일치도 검사하며 렌더 실패 때 이전 편집 spec과
관계없는 파일을 유지합니다. sample 모듈 import 시 optional dependency도 lazy로
유지합니다. 이번 source-tree UI 배치에서 전체 Python/최소환경 및 Rust/TeX는
재실행하지 않았고 엔진/기본값/schema/의존성/version은 그대로입니다. B2b–B6과
릴리스 조건은 미완료입니다.

### 이전 읽기 중심 재설계

읽기 중심 재설계: [데스크톱/모바일 리뷰](VISUAL_REVIEW.html)와
[기준/reference](VISUAL_QUALITY.ko.md). 이전 4패널 프로토타입은 사용자 가독성
검토에서 거절됐습니다. 새 후보는 반응 곡선과 가로 endpoint 그림을 분리하고 직접
라벨·caption·수치 조회를 제공합니다. 기존 관측값·평균·CI 양 끝·수치 축 범위는
이전 spec과 비교합니다.

저장한 PNG의 최종 표시 pixel과 글자 경계 겹침을 검사하며 원본 point 크기만으로
판정하지 않습니다. 700px/320px 두 배치를 사용하고 실제 브라우저 viewport
900/600/360/320px에서 이미지 폭 700/320/320/280px와 선택한 웹 글꼴 14px 기준을
확인합니다. 큰 배치를 그냥 줄인 경우는 실패하는 검사도 있습니다. 수치 표 역시
같은 추정기로 계산한 값과 비교합니다.

현재 시각/lint/schema/layout 대상 검사 **82 통과**, 최소 환경은 **27 통과,
1795 deselected, 경고 13개**입니다. 기존 editor 11개와 viewport 변형 4개를
포함한 실제 브라우저 검사 **15 통과**이며 Ruff·Pyright·생성 계약·sdist→wheel도
통과했습니다. 실제 표시 폭의 브라우저 캡처를 확인했지만 독립 독자 실험이나 모델
평가 결과는 아니므로 QA 보고서에는 둘 다 `not_run`으로 남깁니다.

ONS·PLOS/Rougier·VisJudgeBench·그래프 지각 연구를 항목별 근거/한계에 연결하며
미적 종합 점수를 만들지 않습니다. 라벨은 고정된 이 데이터에 맞춘 배치이지 일반
배치 엔진이 아닙니다. Core renderer/기본 테마/schema/의존성/version은 그대로이며
이번 샘플 재설계 이후 전체 Python/최소환경 및 Rust/TeX는 재실행하지 않았습니다.
B2b–B6 기능과 릴리스 조건은 남아 있고 배포 승인은 없습니다.

### 이전 시각 프로토타입 — 사용자 검토에서 거절

아래 자동 검사 통과가 가독성을 입증한 것은 아닙니다. 성공한 디자인 기준이 아니라
과거 기록으로만 유지합니다.

시각 품질/샘플 배치: [평가 방법과 전/후 비교](VISUAL_QUALITY.ko.md).
관측값/통계/축/실제 크기를 고정한 대표 샘플의 실제 글자는 최소 8.5pt이며 native
canvas 경계 안에 있습니다. 흑백/CVD 뷰·JSON QA 결과와 갱신한 Pandas 데모를
생성하고 확인했습니다. 두 스타일 모두 자동 QA를 통과하며 임의의 미적 점수나
독립적인 독자 선호도 평가 결과는 없습니다. 렌더러/기본 테마/schema/version은
그대로이며 lint의 숨긴 범례 집계 오류만 고쳤습니다(회귀 검사 2개).

시각/lint/schema/layout 대상 테스트 **66 통과**, 최소 환경의 시각 테스트는
**11 통과, 1795 deselected, 경고 13개**입니다. PNG/PDF/SVG 재현성·JSON/actions·
작은 글꼴/overflow/빈 그림의 음성 사례와 데이터/통계 보존을 검사했습니다.
이제 향후 전체 최소 환경 검사에 새 샘플도 포함합니다. **시각 QA를 갱신한 이번 배치
이후 전체 Python/최소환경 및 Rust/브라우저/TeX를 재실행하지 않았습니다.** 아래는
이전 완전 실행의 기준 기록이지 이번 전체 실행 결과가 아닙니다. B2b–B6 기능은
남아 있으며 시각 QA가 기능 동등성 완료를 뜻하지 않습니다.

### 시각 샘플 갱신 전 전체 검증 기준(B3j 이후)

- Locked 환경은 변경 없이 동기화 상태입니다(Python 3.12.15·NumPy 2.5.2·
  Matplotlib 3.11.1). **2251 통과, Windows 조건 2 skip, 경고 1개**입니다.
  실제 Python 브라우저 11개와 논문 TeX/서지 4개 조합을 포함하며 브라우저를
  전체 개수에 다시 더하지 않습니다.
- 최소 Python 3.10·NumPy 1.23.0·Matplotlib 3.8.0 스크립트는
  **1795 통과, skip 0, 경고 3532개**입니다. 경고를 숨기거나 경고 없는 결과로
  표시하지 않습니다. Locked 경고는 극단적인 유한 ECDF count 질량의 기존
  native tick overflow입니다.
- Rust 1.99 fmt/Clippy/tests는 11 통과·1 ignored이며 Rust 실제 HTTP/브라우저,
  Python editor smoke·clean sdist→wheel 재빌드/import·생성 계약·Ruff lint/format·
  Pyright를 통과했습니다.
- 최초 전체 실행은 1541 통과 후 Ghostscript txtwrite UTF-8 출력을 Windows
  cp949로 읽는 오류 1건으로 중단됐습니다. 공통 PDF 텍스트 테스트 도우미에
  UTF-8을 명시하고 비ASCII/ligature subprocess 회귀 검사를 추가한 뒤 전체와
  최소 환경이 모두 통과했습니다. 렌더/API 동작 변경은 없습니다. 기여 가이드의
  브라우저 선택도 등록되지 않은 `browser` marker 대신 파일명으로 고쳤습니다.

Rust 1.88 MSRV·의존성 감사는 이번 배치에서 재실행하지 않았습니다. B2b–B6의
추가 범위와 전체 릴리스 조건은 미완료이며 package/editor 1.0.0·spec 0.1 유지,
tag/배포/릴리스 승인은 없습니다.

### 이전 B3j 대상 체크포인트

B3j 대상 검증은 **287 통과, Windows 조건 2 skip**입니다(histogram 186개·
순수 core/모듈 간 계약/렌더 101개). Ruff lint/format·Pyright와 생성 schema/
capabilities/reference 동기화를 통과했습니다. Python editor PNG/SVG와 Rust
HTTP/PNG smoke에서 step layer/stack을 확인했고 native path·기존 가중 통계와
PNG/PDF/SVG 재현성·RNG 보존을 검증했습니다. 막대/step 밀도/가로 dodge/누적
step CDF 비교 이미지를 확인했습니다. Step+dodge·채운 step·poly·임의 dash는
제외했습니다. **B3j 전체/최소환경/브라우저/TeX/배포물 검증은 재실행하지
않았습니다.** Package/editor 1.0.0·spec 0.1과 릴리스 상태는 그대로입니다.

### 이전 B3i 체크포인트

B3i 대상 검증은 **244 통과, Windows 조건 2 skip**입니다(histogram 143개·
순수 core 검사 1개·모듈 간 계약/렌더 100개). Ruff lint/format·Pyright와 생성
schema/capabilities/reference 동기화를 통과했습니다. Python editor PNG/SVG와
Rust HTTP/PNG smoke에서 두 모드를 확인했고 같은 환경 PNG/PDF/SVG 재현성·
global RNG 비사용도 검증했습니다. Stack/layer/가로 dodge/CDF 4패널 이미지를
다시 생성하고 확인했습니다. **B3i 전체/최소환경/브라우저/TeX/배포물 검증은
재실행하지 않았습니다.** Package/editor 1.0.0·spec 0.1 유지, 릴리스 승인 없음.

### 이전 B3h 기준 검증(B3i 이전)

B0 검증: 테스트 675개 통과, TeX/Windows 플랫폼 조건 16개 명시적 skip.
Ruff·Pyright·schema sync·wheel/sdist 검증 통과.

B1a/B1b/B2a/B2b1/B2b2/B2b3/B2b4/B2b5/B2b6/B2b7/B2b8/B3a/B3b/B3c/B3d/B3e/B3f/B3g/B3h는 Python·action/JSON·validation·registry·renderer·Python
editor에 연결했습니다. locked 환경 전체 테스트 **2159 통과, 2 skip**
(Windows 플랫폼만, 실제 TeX matrix 실행), 실제 브라우저 11개를 포함합니다. 최소 환경
Python 3.10 / NumPy 1.23 / Matplotlib 3.8은 **1703 통과, skip 0**입니다.
Ruff lint/format·Pyright·schema/capabilities/reference/gallery 동기화,
wheel/sdist 재빌드, dashboard 빌드와 Python editor smoke 검증을 통과했습니다.
gallery 36개·편집 spec 61개를 동기화하고 가중/단위 CI·가로 SEM·누적 비율
preview를 확인했습니다. 참조 수식, chunk/local RNG, 동일 환경 PNG/SVG
재현성과 양수/음수·가로·관측값 1개 막대의 오차 구간 밖 라벨도 검증했습니다.
Box/violin은 새 테스트 69개로 수치/배치, 빈/결측/단일 관측, 엄격한 옵션,
action/schema/editor PNG, global RNG를 쓰지 않는 notch와 반복 가능한
PNG/SVG·편집 spec을 검증했습니다. 중첩 box·가로 violin preview도 확인했습니다.
Swarm 테스트 53개로 원/선 두께의 실제 pixel 거리, DPI/resize/limits/layout/
양수 log 변화, 행 보존·hue 공동 배치·빈 자리, 엄격한 상한/옵션,
schema/actions/editor PNG·반복 가능한 PNG/PDF/SVG를 검증했습니다.
Swarm gallery와 combined box overlay/가로/log preview도 확인했습니다.
greedy 방식으로 최적 배치 보장은 아니며 레이어당 유효 행 2000개까지입니다.
과밀하면 gutter에 행을 보존하고 warn_thresh(기본 .05)를 넘으면 한 번 경고합니다.
최소 환경의 warning 3468개는 보고하며, 경고가 없다는 의미로 처리하지 않습니다.
Letter-value 테스트 106개로 공개 깊이 수식·독립 NumPy 분위수/area 폭,
정확한 반복값·유한 극단값, native 띠/중앙값/꼬리 배치, 빈 자리/순서/hue 색상·
해칭, 엄격한 옵션, actions/schema/editor PNG와 PNG/PDF/SVG 재현성·RNG를
검증했습니다. Full은 min/max를 포함하며 area는 full의 확장 바깥 띠까지
실제 확률 질량을 사용합니다. 높이 0인 띠의 area 폭은 0, 모두 같은 값은
exponential 폭으로 처리합니다. Gallery와 지수/가로-linear/full-area 비교도 확인했습니다.
Native/log 테스트 60개로 실제 숫자 간격·빈 자리, 가로/세로, raw/명시적 log
분위수·KDE, 모든 native 도형 역변환, swarm pixel 간격·경계·DPI·축 뒤집기,
엄격한 타입·양수·공통 축, JSON/actions/editor PNG·PNG/PDF/SVG·RNG를 검증했습니다.
숫자/log-native 3-panel 비교도 확인했습니다. stat_scale 기본 data를 유지하며 axis만
log10 통계/KDE를 선택합니다. 숫자 native ID에서 bool/날짜/문자열을 제외하고
통계 bar/point/count는 아래 확장 범위로 지원하며 추가 매핑은 아직 미지원입니다.
Violin 테스트 138개로 독립 Gaussian 수식·대역폭/grid, 정규화 기준/개수/빈 자리,
모든 inner/split/방향/native log 도형, 정확한 원자료·단일/결측 셀,
엄격한 무시 옵션/행 상한·pure core·JSON/actions/schema/editor·export를 검증했습니다.
Inner/global-count·split quartile/density·가로 관측값·log/clipped stick 4-panel도
확인했습니다. Area는 공통 fitted-coordinate KDE 밀도 척도이지 실제 잘린 도형
면적의 동일성 보장이 아닙니다. Clip은 support만 제한하며 fit 행/개수/inner 원값은
유지합니다. Split은 선택·예약 hue 정확히 두 개이며 임의 hue split은 아닙니다.
기본 중앙값/width/cut0도 유지합니다.
구성 요소 테스트 48개로 독립 artist 속성·정확한 통계/좌표 보존, 가로/세로/native
log, pure typed/dict builder·기존 기본값/one-based, hue/hatch/tint·빈 자리,
알 수 없는 nested 키/타입/역할/크기/숨김 옵션, schema/actions/editor PNG,
PNG/PDF/SVG 재현성과 global RNG 보존을 검증했습니다. 기본/스타일 box·letter tier·
가로 log-fit 4-panel도 확인했습니다. 임의 kwargs·precomputed bxp·hue/띠별 매핑·
bootstrap 추론을 추가한 것은 아닙니다.
통계 축 테스트 73개로 숫자/log 배치·빈 자리/hue, 실제 순서의 point 빈 셀/primitive
overlay, 방향/limits/실제 구간, 독립 raw/log SD/SEM/PI/CI·가중/단위 bootstrap 수식,
양수 baseline/끝점/라벨 방향·누적 전체 count 분모, 잘못된 scale/무시 옵션/비양수
계산 구간/역변환 overflow, pure builder/기존 spec·JSON/actions/schema/editor·
export/RNG를 검증했습니다. Native raw-SEM·log raw-PI·가로 log-fit CI/baseline·
log-native 누적 percent 4-panel도 확인했습니다. Axis log는 mean/median/min/max만,
count stat_scale·log 값축 stack은 미지원입니다. 새 범위는 primary만 지원하고
기존 선형 ordinal y2를 유지하며 계산 구간을 clip하지 않습니다.

Rust 1.99의 format/Clippy/tests와 실제 Python/HTTP/브라우저 bridge를
통과했습니다. TeX Live 2026과 CI-pinned Tectonic 0.15.0으로 실제 논문
엔진/서지 조합 4개를 통과했으며 Windows의 실제 bundled Ghostscript를
찾도록 테스트를 보완했습니다. 사용자 선택대로 1.99로 개발하되 1.88 MSRV는
최종 릴리스 게이트에 유지하며 통과/생략으로 처리하지 않습니다.
B2b–B6과 아래 전체 릴리스 조건은 미완료입니다.
기존 1.0.0 Python/Rust/changelog metadata 일치 검증을 통과했고
version/tag/배포 변경은 없습니다. 다음 구현은 추가 semantic/구성 요소 매핑 또는
B3 나머지 추가 histogram/KDE 표현·semantic 설정 범위입니다.
ECDF 테스트 103개로 독립 가중 indicator 수식/비율·raw 질량·반복값/최소 jump/
right-continuity·작은 꼬리를 유지하는 보완형·곡선별 분모·결측/0 가중치·hue 자리·
방향/log/limits/단일·빈 값·무시/잘못된 설정·기존/new JSON/actions/schema/editor·
Matplotlib 경로의 오른쪽 극한·PNG/PDF/SVG 재현성과 RNG를 검증했습니다.
가중치 범위가 넓은 10000-case 조사에서 tie 중간 반올림의 1-ULP 비단조를 발견해
행 가중치를 직접 float expansion으로 누적하고 영구 수식/단조 회귀 테스트를
추가했습니다. Matplotlib3.8은 alpha0도 0-width 점선의 scaled dash를 거부하므로
0-width 도형/범례 proxy는 값·스타일·metadata를 유지하며 보이지 않게 합니다.
질량1e308의 극단값 테스트가 locked suite에서 native ticker 경고 1개를 만들며 숨기거나
warning-free라고 주장하지 않습니다. 일반/가중 percent/가로 log strict 꼬리/
가중 count 4-panel도 확인했습니다. 생존/검열 추론·구간·무한 꼬리가 아니며
primary2D/선형 질량 축만 지원합니다(날짜/y2 미지원). Violin은 아직
callable KDE·임의 inner kwargs·임의 hue split·추가 size/style가 미지원입니다.

Histogram 테스트 95개로 독립 가중 불균등-bin 수식/NumPy 기준·끝 경계/범위 밖
분모·전체/곡선별 면적·누적 density 적분·결측/0/선택 행 쌍·공통 정수 경계·빈/
단일 값/hue 자리·raw log 도형·큰 가중치 뒤의 작은 bin 질량·비율/prefix 단조·
엄격한 설정/overflow/projection/shared ordinal·기존 native hist/alpha·typed
JSON/actions/schema/editor·재현 가능한 export를 검증했습니다. 공통/개별 가중
밀도·가로 log percent·binned CDF 4-panel와 갱신 gallery도 확인했습니다. NumPy는
숫자 bins/통계 effect에서만 지연 호출하며 core는 stdlib입니다. 전체/최소 환경
검증 후 엔진 동작 변경은 없습니다.

단변량 KDE 테스트 125개로 native Gaussian 공분산/밀도·독립 가중 effective-n/
분산/PDF/CDF 수식·전체/곡선별 적분/공통 범위·clip에도 fit/꼬리 정규화 유지·
단일값 질량/빈 hue/행 쌍·raw 관측 log/역방향·정확한 선/면 alpha/width/outline/
dash/hatch·큰/우세 가중치/인접 low bits/작은 그룹 CDF/scaled bandwidth product·
bounded 결정적 chunk/CDF 단조·엄격한 설정/계산 오류·기존 수식/상수 fallback·
tuple clip/typed JSON/actions/schema/editor/export/reference/RNG를 검증했습니다.
가중/대역폭/CDF 4-panel과 새 KDE gallery를 확인했고 NumPy는 지연 effect입니다.
SciPy/새 의존성 없이 기존 호출의 fit을 유지합니다. 이전 단변량 checkpoint가
전체/최소를 통과했고 이 KDE의 log-fit은 여전히 미지원입니다.
가중 violin은 별도 violin 옵션으로 지원합니다. 2변량은 아래
별도 B3d 범위입니다.

2변량 KDE의 module 129개+registry-param 1개로 독립 전체 가중 matrix 공분산/PDF·
native 2D Gaussian·Scott=Silverman·해석적 isotropic HDR/수렴/동률/trapezoid·
조건부 clip 수준·공통 질량/grid/fit 유지·행 쌍/단일값 질량·native 도형/alpha/
width/dash/hatch/범례 proxy·극단 이방 단위/가중치/인접 low bits·bounded chunk/
permutation·raw log/limits·엄격한 설정/계산/rank 오류·schema/JSON/actions/editor/
export를 검증했습니다. Gallery 35개/spec 55개와 가중/상관/pooled/clip/log 4-panel을
확인하고 전체 1825/최소 1370 통과 뒤 엔진 변경은 없습니다. SciPy/새 의존성 없이
행 10000·축당 node 256·levels 16으로 제한합니다. 유한 격자 HDR는 근사 조건부
질량이지 신뢰구간/전체 공간 보장이 아닙니다. 그 checkpoint의 Rust/TeX
미검증은 위의 현재 도구 검증으로 갱신하며 MSRV와 넓은 범위/릴리스는
여전히 미완료입니다.

가중 violin 테스트78개로 독립 공분산/effective-n/PDF·clip에도 fit/행 쌍 보존·
역 ECDF 동률/분위수/가중 평균·개수와 질량 폭/단일값 참조·큰 총량/우세 가중치/
인접 low bits/실제 bounded chunk·양 방향/split/native log/스타일·기존 defaults/
schema/actions/Python/Rust 편집기/export/RNG를 검증했습니다. Spec56개/gallery35개와
비가중/가중/count/log4-panel을 확인했습니다. 전체1923/Windows2skip/기존 ticker
경고1개, 최소1468/skip0/경고3292개를 통과했습니다. Rust1.99 format/Clippy/
11tests(ignored subprocess helper1개는 다른 테스트에서 실제 사용)와 브라우저/
HTTP/Python/가중 editor smoke도 통과했습니다. 예전28registry 검사·CI dashboard
명령·Windows 프로세스 트리 정리를 수정했습니다. 새 의존성/version/배포 없이
최종 전체/최소 검증 뒤 엔진 변경은 없습니다.

Lineplot 테스트66개+registry1개로 독립 숫자 x 추정·SD/SEM/PI/seeded 점별 CI·
x별 계층적 가중/unit bootstrap·실제 선/면/막대·정렬/관측 순서·구간 없는 셀·
data/axis-log/잘못된 끝점·정확한 alpha/zero-stroke export·엄격한 미지원 설정·
core/기존 JSON/actions/Python/Rust editor/RNG를 검증했습니다. 원자료 line은
그대로입니다. Gallery36개/spec58개와 raw/가중/log3-panel을 확인했고 전체1990/
Windows2skip/기존경고1개670.02s, 최소1534/skip0/경고3324개531.80s를 통과했습니다.
Rust1.99 format/Clippy/11tests·실제 브라우저/HTTP/bridge·TeX matrix 통과,
1.88MSRV는 최종 게이트입니다. 새 의존성/version/배포나 검증 뒤 엔진 변경은
없습니다. 점별 면은 동시 coverage/전체 궤적 resampling이 아니며 미관측 x는
표시용 보간입니다. 독립 매핑/date/y2/callable/넓은 curve 추론은 남아 있습니다.

Scatter 매핑 테스트85개로 독립 범주/숫자 hue/size·style marker·전체 auto/
명시 범위·행이 아닌 매핑 clip·지름→native면적·상수/subnormal guide1개·극단/
인접 차이·양수 면적 underflow·순서/예약/가짜 데이터 없는 범례·행 쌍/log/
정확한 native좌표/스타일/alpha·엄격한 타입/충돌/JSON·Python/Rust editor/
export/RNG·기존 호출을 검증했습니다. Guide proxy는 데이터가 아니며 limit을
늘리지 않습니다. Gallery36개/spec59개·범주/숫자/전체/순서/log4-panel을 확인했고
전체2075/Windows2skip/기존경고1개659.71s, 최소1619/skip0/경고3348개539.80s입니다.
Rust1.99 format/Clippy/11tests·실제브라우저/HTTP/JSON/semantic scatter/export 통과,
새 의존성/version/배포나 최종 검사 뒤 엔진 변경이 없습니다. Line/facet/colorbar/
outline/date/y2 매핑과 MSRV/전체 릴리스 게이트는 계획에 남습니다.

공통 scatter 척도 테스트36개로 결측 좌표에도 합집합 범위·범주/숫자 색/지름/
marker순서·독립 이름·원 table 순서/중복 없는 행·기존 palette 분리·패널당 guide1회/
개별 label·범례숨김·잘못된 이름/설정/cmap/bool순서/pooled한계/모호한라벨·상수/
subnormal·기존 JSON/core/editor/export/RNG를 검증했습니다. 전체2111/Windows2skip/
기존경고1개719.67s, 최소1655/skip0/경고3348개596.76s 통과와 Rust1.99 실제브라우저/
HTTP/JSON/shared/vector smoke 통과. Gallery36개/spec60개·local/shared4-panel 확인,
검증 실행 뒤 엔진 변경 없음(mtime/receipt 확인). 중복 launcher는 기존 job을
재실행하지 않고 거부했고 최종 receipt둘다 exit0입니다. 새 의존성/version/배포나
자동 facet/line 매핑 완료 주장은 없으며1.88MSRV와 넓은 범위는 남아 있습니다.

Line 매핑 B3h의48개 테스트로 원본tuple/predictor 셀·물리 stroke두께/marker/dash·
clip으로 곡선 합치지 않기·역할/weight/unit 행쌍·독립SD면끝점/v-h/log-fit·셀별
가중/unit CI·0native stroke·엄격한 설정/한계/타입·공통 geometry별 guide/reference와
core/JSON/editor/export/RNG를 검증하고 synthetic3-panel을 확인했습니다. 승인한
foreground 재검증: 전체2159/Windows2skip/기존경고1개699.96s, 최소1703/skip0/
경고3468개573.59s입니다. 두 exit0/실행 전후 source hash 일치를 확인하고
v11-b3h-recheck-{full,minimum}-status.json을 소비했습니다. 이전 orphaned running
receipt/일부 로그는 보존하며 통과로 소급 변경하지 않고 원인은 미확인입니다.
Source/API/core/minimum/version 변경 없이 자동facet·남은 기능/MSRV/최종 게이트는
계획에 남아 있습니다.

## 릴리스 조건

- [ ] 기능·옵션·통계 비교표를 실제 구현에 맞게 갱신.
- [ ] 배치 상태와 남은 부분 지원·보류 범위를 명시적으로 검토.
- [ ] Python/CLI/JSON/editor 경로, 기존 spec과 default/migration 검증.
- [ ] 수치·artist·브라우저·reference·같은 환경 export 재현성 테스트.
- [ ] 최소/locked 환경, Rust, 전체 TeX matrix 검증.
- [ ] Ruff·Pyright·생성 계약·clean distribution 검증.
- [ ] 영문·한글 문서, 실행 가능한 preview, Unreleased changelog 갱신.
- [ ] 이후에만 1.1.0 package/editor/release metadata 동기화.
  기존 tag/artifact를 덮어쓰거나 소유자의 릴리스 지시 없이 배포하지 않음.
