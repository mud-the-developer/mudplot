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

**리뷰59차에서실제UI의파일/export회복을검사했습니다.** 유효A→badJSON/invalidspec은
기존spec/PNG/history/layout과draft를보존하고유효B는freshhistory/오류해제로열렸습니다.
실제SVG저장경로fault는400HTML이며부분vector가아니고Figure/cache가보존됩니다.
PNG편집은계속되고fault해제후SVG200/최신title과현재state동일JSON다운로드가맞으며소스파일은불변입니다.

새실제browser1·관련229/Windows6skip·browser4통과/29deselected·floor43통과/4symlinkskip/
3059deselected/Pyparsing13경고·품질9명령이며초기helpertimeout은별도보존하고file-read후
section재확인한최종실행과구분했습니다. EDIT-06은지원범위PASS이지새export형식/CLI·agent
오류정책전체검토는아닙니다. [근거](review_evidence/editor_recovery_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS119/RUNNING5/OPEN25/DEFERRED1**입니다. Runtime없이newB9CI39178688403중확대+
회복검증을로컬보존하며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰58차

**리뷰58차에서확대/highDPIbrowserdata편집을검사했습니다.** 실제Chromium의DPR1/2·
CSS125%·CDPvisual-viewport125%를구분해3case에서spec6×3inch/600DPI와preview2000×1000을
유지했습니다. 선택panel의invertedlog/y2drag·imagefraction키이동이data기대값과맞고focus/
undo/redo/다른panel/specJSON은그대로입니다. 명시emulation이지모든nativebrowserzoom/OS/
물리hardware/75DPIdensegeometry보장은아닙니다.

새optionalbrowser3·관련178/browser8통과/28deselected/floorpure7/3099deselected/Pyparsing289경고·
품질9명령으로EDIT-02는범위내PASS이며runtime은바꾸지않았습니다. [근거](review_evidence/scaled_preview_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS118/RUNNING5/OPEN26/DEFERRED1**입니다.
기준4bcCI5job모두성공해D535응답수정+B9test를먼저게시했고newB9CI39178688403진행중이므로
새효과전체결과는남아있습니다. 확대test/doc은로컬보존하며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰57차

**리뷰57차에서로컬두page/rawaction의공유상태를확인했습니다.** 첫render의sessionlock을
보류하면다른body가도착해도state/PNG는이전commit이며release뒤A→B/raw허용순서로만
commit해독립field/history/순수apply결과가맞습니다. 최종PNG는새session의같은spec과같고
두tab이새로고침해읽었습니다. 공유panel이지tab별selection/live협업이아니며rawform응답은
HTML입니다. 새도메인revision/API를만들지않습니다.

새실제browser1·관련169/OSguard1skip·browser4통과/31deselected·floor8통과/3098deselected/
Pyparsing13경고·품질9명령으로EDIT-05는로컬범위PASS입니다. [근거](review_evidence/shared_session_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS117/RUNNING5/OPEN27/DEFERRED1**입니다.
새runtime변경없이4bcCI의Rust/min성공·양Python진행을보호해대기응답효과와로컬보존하고
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰56차

**리뷰56차에서늦은HTML이최신inspector를덮는문제를고쳤습니다.** FIND-040은A/Bcommit뒤
B를먼저전달하고A를나중에풀면DOM만A/spec·PNG는B인상태를재현했습니다. Oldhelper의도
실패를따로보존하고로컬HTMXviewgeneration으로latest-seen보다옛fragment만무시합니다.
요청/action/SpecJSON을버리거나도메인revision을만들지않으며undo/reset/open/오류도reply순서가
증가합니다. 서버재시작뒤page새로고침의한계는명시합니다.

새browser1/pureHTTP2·관련179/실제browser8통과/26deselected/floor2통과/3104deselected/
Pyparsing13경고·품질9명령·activeLSP5clean입니다. 실제DOM/spec/previewpixelSHA와focus/
scroll/nudge/panel이맞아EDIT-03/04는로컬지원범위PASS이지livecross-tab/모든zoom인증은아닙니다.
[근거](review_evidence/response_order_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS116/RUNNING5/OPEN28/DEFERRED1**입니다. 4bcCI양Rust성공/3Python진행을보호해효과unit은
로컬보존하며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰55차

**리뷰55차에서보조datahandle의잘못된yframe을복구했습니다.** FIND-039는y2log100을
primary범위로clamp하고실제drag에서199.526대신2.605를저장했습니다. 실제secondaryy
metadata를해당layer에만전달해primarydata/titleaxes/legendfigure뜻을유지했습니다.
15size/DPI/panel대조·실제artist/JSON·browser선택panel/invertedlogdrag와undo/redo가맞습니다.

Pure5/browser1을분리해관련209통과/non-Windowsguard1skip·실제browser6통과/27deselected·
floor17통과/3087deselected/Pyparsing289경고·품질10명령·activeLSP6clean입니다.
PLOT-11은지원범위PASS로PLOT01..12검토를마쳤지만보편API/nativeUI/previewparity인증은아닙니다.
[근거](review_evidence/coordinate_frame_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS114/RUNNING5/OPEN30/DEFERRED1**입니다. 기준b8CI39171315500은5job모두성공해
대기alpha+좌표효과를함께게시하고새전체CI를받으며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰54차

**리뷰54차에서annotationalpha누락과overlay를확인했습니다.** FIND-038은유효alpha가
Text/arrow둘다에빠져초기11회귀가실패했습니다. 공통branch수정으로nondefaultopacity를
primary/y2양쪽에적용하되defaultRGBAopacity/nativeclip/zorder는유지했습니다. 최종12회귀의
SVG/pixel/style이맞고alpha0변경channel은무annotationreference대비9967→0입니다.

부호/dodge/중복bar·비대칭오차·native부호stack·unsortedbandedge가수작업값과맞습니다.
관련245/floor12통과/3087deselected/Pyparsing13경고·품질9명령·activeLSP3clean으로
PLOT-09/12는지원범위PASS이지새zorder/clip/좌표API가아닙니다. [근거](review_evidence/overlay_alpha_verification.json)/
[비교](review_evidence/annotation_alpha.png)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS113/RUNNING5/OPEN31/DEFERRED1**입니다. b8CI의Rust/min성공·양Pytest진행을보호해
효과unit은로컬보존하고PLOT-11drag좌표와새alpha전체CI를별도로남깁니다. 버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰53차

**리뷰53차에서공유범위와log영역을대조했습니다.** 9축표는col/named/empty/ticks와독립
 y/y2/labels가맞고3선언충돌은거절됩니다. Legacylogclip은원값을보존하고typedinterval은
 영역오류를거절합니다. 큰양수축/독립linear색상/지원heatmapLogNorm·mask가맞으며미지원symlog는없습니다.

선택214/floor214통과/458·2873deselected·11명령으로PLOT-05/10은범위내PASS입니다.
Floor1843경고는1841Pyparsing+2MPL3.8상수1e308imageguard로별도8case에서특정했고
pixel대조는기대RGB/원자료/Werror출력보존이맞았습니다. Backend한계를기록했지숨기거나
자료를바꾸지않습니다. [근거](review_evidence/axis_domain_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS111/RUNNING5/OPEN33/DEFERRED1**입니다. 기준3bCI39166807390의5job모두성공해
수치수정runtime전체검증도확인했고분포/pairing/축문서를함께게시해새문서CI를받습니다.
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰52차

**리뷰52차에서role별원래관측을추적했습니다.** 12개명시index가x/y/hue/weight/unit/style/
size필수role과맞고미사용열의결측은함께drop하지않았습니다. Pairedweightedmean/n/unit/
질량이정확하며잘못된필수값은거절하고regplot은결측쌍을조용히빼지않습니다. B선택의실제
scatter는원래row4/5/6/8입니다. Validator/집계/drop정책변경은없습니다.

관련경계선택388통과/444deselected·floor388통과/2699deselected/분류한Pyparsing489경고·
품질9명령이며새전체suite수로소급하지않습니다. STAT-08은지원범위PASS로STAT01..08의
명시corpus검토를마쳤지만모든통계/adapter/UI인증은아닙니다. [근거](review_evidence/observation_pairs_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS109/RUNNING5/OPEN35/DEFERRED1**입니다.
3bCI양Rust성공/3Python진행을보호해분포+pairing문서는로컬보존하고새수치전체CI/버전/
의존성/lock/tag/배포는별도유지합니다.

### 이전 리뷰51차

**리뷰51차에서분포수작업값과jitter재현성을확인했습니다.** Odd/even/single/constant의
양방향8box는분위수/관측whisker/outlier가맞고표본수다른24violinprofile의독립분산/
Gaussian/정규화/분위수오차는5.55e-16입니다. 유한clip면적1을강제하거나결측표본을섞지않습니다.
기존seed0jitter위치는layer순서를바꿔도같고PYTHONHASHSEED1/777두프로세스·반복출력에서
PNG/PDF/SVGhash와전역NumPy/PythonRNG비변경을확인했습니다(같은spec/환경범위).

관련408/floor407통과/2680deselected/경고1649·품질9명령이며1649전부Pyparsing으로같은
floor실행에서분류했습니다. STAT-06/07은지원범위PASS이지모든분위수법/환경보장은아닙니다.
[근거](review_evidence/distribution_jitter_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS108/RUNNING5/OPEN36/DEFERRED1**입니다. 새runtime/API/test/framework없이3bCI
양Rust성공/3Python진행을보호해문서는로컬보존하고회귀수치수정의그정확한전체결과는남깁니다.
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰50차

**리뷰50차에서KDEmoment/유한꼬리/퇴화입력을대조했습니다.** 정확한mean5/2·분산117/22·
neff18/7와24Gaussian설정/2049point오차2.22e-16이맞고절단질량/trapezoid오차8.94e-9를
재정규화하지않습니다. Singular질량4/10은공통분모에남고4095grid의두peak는±3근처입니다.

기존1D/2D/grid285case와관련359/floor285통과/2802deselected/경고317·품질9명령을확인했고
floor285재실행으로317전부Pyparsingdeprecation으로분류했습니다. STAT-05는지원범위PASS이며
새runtime/kernel/fallback/test는없습니다. [근거](review_evidence/kde_integral_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS106/RUNNING5/OPEN38/DEFERRED1**입니다.
기준efCI39162647649는5job모두성공해대기수치/histogram/KDE를함께게시하고새효과CI를받으며
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰49차

**리뷰49차에서기존histogram회귀와독립질량을대조했습니다.** 기존186case의경계/비균일
bin·weights·원시폭·geometry·CDF·legacy/native/출력·RNG를재실행하고80자리Decimal로
19지원설정/38행을검사했습니다. In-range질량15(A9/B6)/outside198제외·common-density면적
.6/.4·개별1/1이맞고높이합/도지그림면적과통계원래폭을혼동하지않습니다. 금지frequencyCDF도유지합니다.

관련269/floor186통과/2901deselected/경고257·품질9명령이며별도floor186재통과로257전부
Pyparsingdeprecation임을확인했습니다. Normalizer/runtime/newtest를바꾸지않고STAT-04는
지원범위PASS입니다. [근거](review_evidence/histogram_normalization_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS105/RUNNING5/OPEN39/DEFERRED1**입니다.
기준efCI4성공/3.10Pytest진행을보호해대기수치/문서단위는로컬보존하고버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰48차

**리뷰48차에서퇴화다항회귀의confidence수치를고쳤습니다.** FIND-037은legacyresponse
1e-250covarianceunderflow/0폭·1e250nonfinite/소실band와rank3/11design의경고후
4.67e10예측을재현했습니다(관측최대121·수정전4/19실패). 공통predictor/response정규화와
scopedrank/산술/nonfinite오류로원단위mean-fitnormalapproximation/출력보존을유지합니다.

독립OLS공식과3scale×legacy/typed의200grid/bandpolygon·큰predictorhelper·잘못된입력을
검사했으며모든거대Matplotlib축layout보장은아닙니다. 관련201/floor19통과/3068deselected/
경고13·품질8명령으로STAT-03은corpusPASS입니다. [근거](review_evidence/regression_degenerate_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS104/RUNNING5/OPEN40/DEFERRED1**입니다.
efCI양Rust성공/3Python진행을보호해효과unit은로컬보존하고버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰47차

**리뷰47차에서projection좌표와scalar의미를확인했습니다.** 비대칭축quiverpolygon끝과
독립data변환·비단조3Dxyz·polar방위가일치하며mesh/전치대조도재실행했습니다. Heatmap명시
범위/mask/RGBA/colorbar와legacyc상수/결측이맞고typednull은기존계약대로거절됩니다.
Numerichuebounds는범위밖행도보존하며색상mappinglegend이지임의colorbar/행선택이아닙니다.

관련229/floor12통과/3056deselected/경고13·품질8명령으로PLOT-07/08은현재지원조합PASS이며
모든projection/scaleoption인증은아닙니다. [근거](review_evidence/projection_colour_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS103/RUNNING5/OPEN41/DEFERRED1**입니다.
Runtime/API/schema변경없이기준b777CI4성공/3.10sitebuild진행을보호해두unit은로컬보존하고
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰46차

**리뷰46차에서synthetic입력과계약결정을정리했습니다.** Reviewfixture5개와공유JSON42개
snapshot의hash/size/provenance/입력·결과구분을보존했고제한된profilepath/privatekey/token
검사는0hit이지만보편privacy인증은아닙니다. RawTemp로그/환경은비공유하고seed/consumer를연결했습니다.

Mutable/snapshot·batch·Figure·size·journal·HEX/pattern·PGF·tool/wheel·native범위·release
충돌표는기존선택/근거를기록할뿐새호환성권한을만들지않습니다. 기존313통과/예상경고2·품질
7명령·명시19path존재를확인해BASE-06/07은bounded준비범위PASS이며BASE-05전체150ID
symbol/test매핑은RUNNING입니다. [준비](REVIEW_PREPARATION.md)/ [근거](review_evidence/preparation_audit_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS101/RUNNING5/OPEN43/DEFERRED1**입니다.
b777CI중문서는로컬보존하고제품runtime/버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰45차

**리뷰45차에서repo를깨지않고generateddrift감지를확인했습니다.** 기존synccheck를
먼저실행하고3artifact격리사본의정상통과→의도drift실패/재생성안내→복구통과를검사했습니다.
Action36/field·layer37/생성표현도일치하고kind는구조적string/별도semantic검증을유지해
새enum제약으로schema계약을좁히지 않았습니다.

관련231/floor4통과/3052deselected/경고13·품질8명령으로JSON-11은sync/registry범위PASS이며
모든nullableUI의미/BASE매핑·privacy감사까지완료한것은아닙니다.
[근거](review_evidence/generated_drift_verification.json)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS99/RUNNING7/OPEN43/DEFERRED1**입니다. Runtime/artifact내용변경없이161CI중
unit은로컬보존하고버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰44차

**리뷰44차에서통제출력실패와Figure소유권을확인했습니다.** Windows읽기전용/deny-delete
잠금의JSON/PNG/PDF/SVG는이전bytes를보존하고ENOSPC/잘못된확장자도정리됩니다.
성공Figure는callerclose전까지열려있고GC뒤weakref가해제됐습니다. 80effect반복의
live/openFigure/tmp0·handle215→216/RSS85.5→90.8MB는bounded관찰이지모든native/
장시간누수부재증거가아니며PERF-04는별도입니다.

관련128통과/OS6skip/예상MPL경고8·floor17통과/3035deselected/경고13·품질8명령으로
OUT-04/05는이corpus에서PASS이지모든OS/ACL인증은아닙니다. [근거](review_evidence/output_lifecycle_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS98/RUNNING8/OPEN43/DEFERRED1**입니다.
Runtime변경없이161CI중unit은로컬보존하며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰43차

**리뷰43차에서유한pattern·명도·실제크기검토를분리했습니다.** 2panel의7fill/9linepoint그룹과
범례가일치하며hatch6/marker8/style4(선조합8주기)가반복됩니다. EqualLCH·독립linearY흑백proxy는
범주분리보장이아닙니다. 고정1-column컬러/흑백에서얇은선/작은marker/투명band를검토했고
6band흑백구분이약해범주축소/경계/직접label/panel을권장하며인증으로해석하지않습니다.

양언어/생성doc/docstring/gallery를유한주기·측정범위로좁히고paper5+정상/3CVD/흑백row로
설명했습니다. 관련77/site9/floor8통과/3027deselected/경고13·품질9명령으로COLOR-06/07/09/10은
이corpus/검토에서PASS입니다. [근거](review_evidence/encoding_print_verification.json)/
[comparison](review_evidence/one_column_encoding.png)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS96/RUNNING10/OPEN43/DEFERRED1**입니다. 기준16aCI39148609011은5job모두성공해
대기report/gallery단위를게시하고새CI를받으며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰42차

**리뷰42차에서최종팔레트report지표/조건을고쳤습니다.** FIND-036은nominalLCHgap3을
safe로표시하던paper7/vivid7의실제HEXgap2.79209/2.79726을재현했습니다. Float명도는
mappedRGB,report는8-bitHEX를평가하고정상/CVD유형/model/fullseverity1/표현/기준을
추가하되기존key/threshold/생성색/알고리즘은유지합니다.

저자MachadoTable1·N±1RGB/pair·결정적tie/독립process가통과했습니다. 측정범위이지
인증이아니며soft6는사전N5밖에서도측정pass할수있습니다. 관련141/floor18통과/
3009deselected/경고13·품질8명령을기록해COLOR-03/04/05/08은PASS이며나머지색상패턴/
가독성/문구gate는남습니다. [근거](review_evidence/palette_report_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS92/RUNNING10/OPEN47/DEFERRED1**입니다.
16aCI를보호해단위는로컬보존하고버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 41차

**리뷰 41차에서style소유권과DPI별pixelpadding을분리했습니다.** 번갈아그린theme/journal은
callerrc전부를복구하고같은ambient환경의독립process와PNG/PDF/SVGSHA가같아LAY-08은
범위내PASS입니다. FIND-035는pad를0.02inch로고정해기존300DPI6px를유지하면서dense
150/300오차를0.02689→0.01041inch로줄이며spec/선폭은바꾸지않습니다.

Editor600DPI/capped2000x1000preview는최대.00334inch차이·1.5pt선폭·720x360ptSVG를
유지하지만75DPIdense의.14594inch잔차가남아LAY-09는RUNNING입니다. 관련88/floor6통과/
3003deselected/경고13·품질8명령은 [근거](review_evidence/style_dpi_verification.json)에
보존했고 [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS88/RUNNING10/OPEN51/DEFERRED1**입니다.
기준5caCI39142799672는5job모두성공했으나queuedguide/pad이전이라함께게시해새CI를
받으며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 40차

**리뷰 40차에서secondary축과반복guide의실제겹침을고쳤습니다.** FIND-034의2panel/
2colorbar/share축/y2label/outsidelegend겹침과명시series범례반복을재현했습니다.
고정1.35axes배율을실측물리간격으로바꾸고같은ungroupedpoint/line의source/axis/reference만
guide를공유하며rawgroup/다른identity는유지합니다. 수동anchor/data/style/물리canvas는같습니다.

8x3.5/6x3bbox·실제PNG/PDF/SVGdraw-event가data/label침범을피하고4.5x2.8secondary는
한계를경고합니다. 새14/관련185통과·floor14통과/2989deselected/경고13·품질/packaging
8명령을기록해LAY-05는측정범위PASS입니다. [근거](review_evidence/mixed_guide_verification.json)/
[baseline](review_evidence/mixed_guides_baseline.png)/ [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS87/RUNNING9/OPEN53/DEFERRED1**입니다. 현재5caCI중effect단위는로컬보존하고
버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 39차

**리뷰 39차에서실제systemfont/glyph와한글layout진단을기록했습니다.** 없는familyfallback/
DejaVuHangul누락은원문font/text를바꾸지않고감지됩니다. MalgunGothic은한글은지원하지만
U+2212가없고선택NotoSansKR은이corpus를지원하나weight100fallbacklog가있습니다.
Filehash/glyphindex/bbox는현재Windows근거이지모든font/OS보장이아닙니다. Binary/
download/minus치환은추가하지 않았습니다.

Installed2font·좁은한글/긴그룹outsidelegendbbox와이전English/멀티라인/무공백지원·경고를
대조해LAY-04/07은이corpus에서PASS입니다. 해당systemfont부재는명시skip합니다.
관련97통과/예상glyphlayout경고14·floor5통과/2984deselected/경고26·품질/packaging
8명령은 [근거](review_evidence/font_boundary_verification.json)에보존했습니다.
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS86/RUNNING9/OPEN54/DEFERRED1**입니다.
기준66feCI39139498998은5job전부성공했지만queuedlayout이전이라소급하지않고함께게시해
새CI를받으며버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 38차

**리뷰 38차에서fixedcanvas에못드는자동text를진단했습니다.** FIND-033의unbrokentitle/
suptitle무경고clipping과oversizedoutsidelegend의음수rectsolver경로를재현해유효rect만
적용하고최종자동textbbox/겹침은행동가능한genericwarning을냅니다. 수동위치/spec/font/
물리canvas는재작성하지않고CLI진단·warning-as-error의rollback/lifecycle도확인했습니다.

관련145통과/명시impossiblefixture의MPL경고8·최소9통과/2975deselected/경고21과
품질/packaging8명령이통과했습니다. LAY-06은감지정책에서PASS,LAY-04는CJK/font등이
남아RUNNING이며 [근거](review_evidence/layout_boundary_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS84/RUNNING10/OPEN55/DEFERRED1**입니다.
805기준run은알려진type실패·floor/양native성공으로완료됐고hotfix5918/preset66fe는
게시했습니다. 현재CI39139498998은이번effect이전이므로단위는로컬보존하며버전/
의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 37차

**리뷰 37차에서 실제TeXpreset전부의filebox를확인했습니다.** 5preset×columns1/2×
fraction.75/1의20행에서vector/mockpreview·spec/render·PNG/PDF/SVG크기가맞습니다.
TeX72.27pt/in과vector72pt/in을구분하고100DPI양자화1pixel허용·preview원본보존을확인했습니다.
Registry가정이지최신publisherguide전체인증은아닙니다.

Journal4priority case는lastsizeaction·기존rcstyle우선을유지하고journalstyleclear후
명시fontfield가보이는것을확인했습니다. Font후속setter가무조건이긴다는낡은설명만
고쳐새flag/교정변경은없습니다. 관련58/floor24통과/2951deselected/경고13·양platform
검사를포함한품질/packaging8명령이통과해LAY-03은범위내PASS입니다.
[근거](review_evidence/preset_geometry_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS83/RUNNING9/OPEN57/DEFERRED1**입니다. 진행중floor를취소하지않고test/doc과
platformhotfix는로컬보존하며runtime동작/버전/의존성/lock/tag/배포도유지합니다.

### 이전 리뷰 36차

**리뷰 36차에서 Windows observer factory의 platform type경계를 복구했습니다.**
기준805CI39136943043은3.10Pyright의ctypes.WinDLL2오류로실패하고matrix형제는취소됐습니다.
Cachefactory추출때ownWindowsguard가빠져localWindows검사로는놓친문제입니다. WinDLL
전에non-Windows OSError를명시해cast/ignore없이경계를복구하고PID fresh조회/CloseHandle/
Linux reader는유지합니다.

GlobalLinux/WindowsPyright target모두통과·sampler/history4통과/로컬OS1skip·품질/
packaging7명령도통과했지만새non-Windows runtime회귀는다음LinuxCI가필요합니다.
[근거](review_evidence/platform_guard_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS82/RUNNING9/OPEN58/DEFERRED1**이며실패를소급해green으로바꾸지않습니다.
Layout작업보다이실패를먼저처리했고남은baseline job이끝날때까지hotfix는로컬보존하며
제품runtime/버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 35차

**리뷰 35차에서 literalHTML/SVG와명시trustedPGFTeX를구분했습니다.** 특수문자/
Unicode/무해script문자열이decode-once value로남고script/eventnode가추가되지않았습니다.
실제양raweditor4case도attribute/state가같고PGF의rawampersand는명확히실패하며
escapedliteral/무해TeX/math는T1·fittedpaper에서컴파일/추출문자가맞았습니다. Reference
macro탈출은계속거부하며runtime sanitizer/전형식문자변환은도입하지 않았습니다.

관련72통과/no skip·최소6통과/2945deselected/경고185와품질/packaging7명령이통과했습니다.
현재185경고는upstreamPyparsingDeprecationWarning으로기록하되suppress하거나과거전체로
extrapolate하지않습니다. OUT-09는범위내PASS이며 [근거](review_evidence/string_boundary_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS82/RUNNING9/OPEN58/DEFERRED1**입니다.
기준06dCI39131994074는5job전부성공했습니다. 대기도구/test는별도local검증과함께
게시해새CI를받고버전/의존성/lock/tag/배포는유지합니다.

### 이전 리뷰 34차

**리뷰 34차에서 실제 reference 출력/문서 결과를 확인했습니다.** 같은 reference spec의
PNG/PDF/SVG가 시간간격/새process에서도동일hash이고 DOI/라벨은 남으며 volatile
metadata는 없고 SVG ID는 결정적입니다. PGF+상대sidecar를 함께 옮기면 컴파일되고 누락하면
실패합니다. 후처리실패가 옛PGF를 덮고이미지를남길수있는비트랜잭션한계를 유지해
OUT-02/06/07은 관찰정책에서PASS입니다.

관련70case가 skip없이 통과했으며 실제tectonic·pdflatex+bibtex·lualatex+bibtex·
lualatex+biblatex의citation번호/본문과 각PDF의5embeddedfont/DOIannotation을
설치Poppler로 확인해 OUT-08은 이matrix에서PASS입니다. 모든font/OS 보장은 아닙니다.
최소6통과/2939deselected/경고13·품질/packaging6명령도 [근거](review_evidence/output_reference_verification.json)에
기록했고 [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS81/RUNNING9/OPEN59/DEFERRED1**입니다.
Runtime은 그대로며06dCI중 test/doc은로컬보존하고 버전/의존성/lock/tag/배포와별도
문자경계/권한/자원미완료범위도 유지합니다.

### 이전 리뷰 33차

**리뷰 33차에서 세션 보관량과 observer 자체 증가를 분리했습니다.** 137초/500행의
60edit/undo/redo/open cycle·실패effect10회·15자원점에서 GC후 Figure0/handle198/
temp0이었습니다. History30/교체1은 의도된 보관량이며 RSS87.9→96.4MB/peak246.6MB를
native leak 부재의 보편 증거로 해석하지 않습니다.

FIND-031은 검증 도구 문제입니다. 렌더 없이 sampler20회가 ctypes 타입20/객체662를
늘려 binding/type만 lazy reuse하고 sample값/PID handle은 fresh/close로 유지했습니다.
수정 뒤 warm대조는 새타입0/객체2증가, 회귀·관련63통과/OS2skip·품질/packaging6명령과
수정 sampler의 전체 세션 재실행도 완료했습니다. 제품renderer/state 변경은 없습니다.
PERF-04는 긴시간축/다른 native workload가 남아 RUNNING이며 [근거](review_evidence/session_resource_verification.json)/
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS77/RUNNING9/OPEN63/DEFERRED1**입니다.
06dCI를 보호해 도구/doc은 로컬 보존하고 버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 32차

**리뷰 32차에서 소유 Matplotlib effect를 직렬화했습니다.** FIND-030은 동시 PNG/SVG
save가 serial bytes와 달라진2회귀입니다. 새stdlib-only 재진입 lock이 render/save·TeX
preview·Python editor effect·site/gallery를 감싸며 optional import를 앞당기지 않습니다.
격리이지 병렬 처리량/임의 Figure·pyplot·Store thread-safe 보장이 아닙니다. 반환Figure는
caller 소유이며 병렬 drawing은 독립 spawned process를 우선합니다.

Controlled/nested/3format/2session6case·관련231·site9·최소6통과/2937deselected/
경고13과 품질/packaging8명령·LSP8경로가 통과하고 exact serial/concurrent hash도 같습니다.
PERF-06은 소유 호출 범위에서 PASS이며 [근거](review_evidence/concurrent_render_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS77/RUNNING8/OPEN64/DEFERRED1**입니다.
진행 중31eCI는 이 effect 변경 이전이므로 단위는 로컬 보존하고 state/선언적core·버전/
의존성/lock/tag/배포는 유지하며 후속 current-source CI를 받습니다.

### 이전 리뷰 31차

**리뷰 31차에서 bounded rows×history core matrix를 기록했습니다.**
`uv run --no-sync python scripts/profile_history_costs.py`는3행크기×3이력목표를
독립 core worker로 실행하며 child12초/dispatch2.5초/RSS관찰512MiB 예산입니다. OS
sandbox가 아닙니다.6목표 완료·3조합375/39/38action 중단이며 미측정 undo/redo는 null입니다.
실제 timeout/OOM은 없고3stub 회귀가 partial/error checkpoint를 보존합니다. 1천×1000의
undo/redo402.35/404.45ms·10만×10의362.61/392.95ms는 관찰값이지 SLO가 아닙니다.
Worker peak53,571,584bytes도 baseline 포함이며 renderer RSS는 아닙니다.

PERF-02는 bounded corpus에서 PASS이며 alias/replay/checkpoint를 재설계하거나 미완료
셀을 extrapolate하지 않습니다. 기존 label None/empty도 불필요하게 고치지 않았습니다.
관련62통과/OS2skip·품질/packaging6명령은 [근거](review_evidence/history_cost_verification.json)에
보존했고 [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS76/RUNNING8/OPEN65/DEFERRED1**입니다.
31eCI 동안 새script/test/doc은 로컬 보존하고 core/버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 30차

**리뷰 30차에서 명시 빈 render token을 auto/null과 구분했습니다.** FIND-029의
6artist 불일치는 schema/codec이 유지한 빈문자열을 renderer가 fallback하던 문제입니다.
이제 None만 자동값을 선택하고 지원 no-marker/no-line·기존0/default와 layer별 제한은
유지합니다. 대표 renderable20case의 schema/Python·CLI migrate·5fresh CLI render·
Rust typed→Python·rawJSON editor/HTMX state/PNG40회가 일치했습니다. 전체139nullable/
자동값/visual control 검증은 아니므로 JSON-09는 RUNNING입니다.

관련266통과/기지singleton interval 경고2·최소79통과/2858deselected/경고15·native22통과/
helper6ignored·품질/codec/packaging10명령은 [근거](review_evidence/render_token_verification.json)에
기록했습니다. [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS75/RUNNING8/OPEN66/DEFERRED1**입니다.
기준ea1CI39125371498은5job 모두 성공했지만 renderer 변경 이전이라 소급하지 않습니다.
대기 성능 단위와 함께 게시해 새 CI를 받고 버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 29차

**리뷰 29차에서 편집/JSON/렌더 비용을 실제로 분리했습니다.**
`uv run --no-sync python scripts/profile_state_costs.py`는 synthetic1천/1만/10만 행의
bounded warm workload입니다. Title dispatch median0.803/6.993/67.867ms,10만 행의
JSON encode/decode174.954/182.815ms·PNG save533.225ms를 측정했습니다. 반복 수/
median/p95와 환경·source hash도 보존합니다. 별도 profile의 deepcopy누적 비중99.923%,
render/validation호출0이며 Python 할당 peak4,828,472bytes는 native RSS가 아닙니다.
PERF-01/03은 관찰 범위에서 PASS이며 snapshot 안전성·기존 구조를 유지합니다.

정확한ea1의 Linux/Windows foreground 자손/MSRV control도20/21통과(helper5/6ignored),
Windows 도구 부재/복구까지 확인해 RUST-04는 지원 policy에서 PASS입니다. [성능](review_evidence/performance_verification.json)/
[정리 근거](review_evidence/remote_cleanup_verification.json)에 한계를 구분합니다. 관련59통과/OS2skip·
품질/packaging6명령도 통과했으며 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS75/RUNNING8/OPEN66/DEFERRED1**입니다. Full CI를 취소하지 않도록 새script/doc은
로컬에 보존하고 core runtime/버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 28차

**리뷰 28차에서 foreground 자손 timeout 정리를 고쳤습니다.** FIND-028의 직접child
종료 뒤 살아남은 grandchild를 재현했습니다. 공통 transport가 Windows 보유 tree 또는
새Unix process group만 정리하며 shell/interpreter fallback은 없습니다. 정리 도구의
별도2초 예산·직접 child kill/reap·실패 진단을 유지하고 detached/reparented worker는
정책 밖으로 명시합니다.

현재Windows lib20+main1통과/helper6ignored·정리 도구 부재/복구·정상 집중 native bridge와
fmt/lint/type/계약/packaging9명령이 통과했습니다. 새Unix/MSRV는 로컬 실행하지 않아
RUST-04는 RUNNING입니다. 기준e728CI39122032427은 이제5job 전부 성공했지만 후속
runtime 검증은 아니므로 소급하지 않습니다. 로컬 대기 단위와 함께 게시해 새 CI를 받습니다.
[근거](review_evidence/descendant_cleanup_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS72/RUNNING9/OPEN68/DEFERRED1**이며 제품한도/버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 27차

**리뷰 27차에서 실제e728 Linux floor·양native 완료 log를 확인했습니다.** Job117659400040의
ordered60파일 전체는2872통과/26skip/경고3906,943.69초입니다. Skip은 선택adapter25와
biber1이며 staging symlink skip은 없습니다. 정확한 소스·전체 성공·완전한 skip 요약으로
4symlink 통과를 판단하되 개별 verbose case log가 있다고 주장하지 않습니다. 경고 세부는
기존 flag로 suppress되어 전부 무해하다고 분류하지 않습니다.

양OS native lib18+main1통과/helper3ignored와 HTTP path/header corpus도 실제 log에서
확인해 기존 Windows 파일/경로 probe와 함께 SEC-06은 관찰 범위에서 PASS입니다. Full
Python2job은 여전히 실행 중이므로 CI-01은 RUNNING이며 후속 privacy-only 회귀도
소급하지 않습니다. [근거](review_evidence/remote_floor_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS72/RUNNING9/OPEN68/DEFERRED1**입니다.
증거 전용 단위는 CI 중 로컬에 보존하며 runtime/버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 26차

**리뷰 26차에서 기본 오류 log와 현재 advisory snapshot을 확인했습니다.** 합성 token/
연구 행만 사용한 양 editor의 validation/import/render/unknown-route 오류에서 기본
stdout/stderr marker·traceback이 없고 state/PNG를 보존했습니다. 같은 client의 오류/
draft/current-state 응답은 편집 기능이며 사용자 간 기밀성·credential 보관소가 아닙니다.
제품 runtime 변경 없이 회귀1개·관련211통과/최소1통과/2898deselected/경고13과 스타일/
타입/계약/packaging7명령이 통과했습니다.

세 committed Python lock audit의 알려진 취약점과 official OSV querybatch의 Cargo
registry69 name/version advisory는0이었습니다. cargo-audit/모든RustSec 범주·영구
보장·후속 dependency resolution 검사로 확대하지 않습니다. SEC-08은 관찰 범위에서
PASS이며 [근거](review_evidence/privacy_audit_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS71/RUNNING10/OPEN68/DEFERRED1**입니다.
기준e728의5job CI를 취소하지 않도록 이 test/doc은 로컬에 보존하며 버전/의존성/lock/
tag/배포도 유지합니다.

### 이전 리뷰 25차

**리뷰 25차에서 full/floor CI 예산을 분리했습니다.** FIND-027은 full Pytest 성공 뒤
같은 job의 floor가 남은 시간을 쓰다 취소되던 배치 문제입니다. Ordered60파일 전체
floor를 Linux/Python3.10 독립 job으로 옮기고 full3.10/3.12는 유지합니다.3Python job은
각 유한60분·Rust는 기존20분이며 PEP723 의존성/lock/not-browser filter는 그대로입니다.
고정 TeX 설치 본문/checksum은 byte 단위로 같고 locked Playwright system/font 전제도
유지합니다. Floor의 browser binary만 받지 않으며 full browser 검사는 그대로입니다.

두 경로의25slowest timing·runner 전체 argv/반환값 guard를 확인했고 CI/릴리스7통과,
실제 핵심 floor39통과/4symlink skip/2855deselected/경고13·Ruff222/타입/계약/
packaging·LSP3경로가 통과했습니다. 새로운5job 원격 완료는 아직 필요해 CI-01은 RUNNING입니다.
[근거](review_evidence/ci_floor_split_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS70/RUNNING10/OPEN69/DEFERRED1**입니다. 대기하던 소유권 수정/문서와 함께 게시하되
제품 한도·버전/의존성/lock/tag/배포는 유지하며 v1 완성은 아닙니다.

### 이전 리뷰 24차

**리뷰 24차에서 staging 소유권과 offline sink를 확인했습니다.** FIND-026은 충돌한
기존 entry를 JSON 실패 cleanup이 지우고 PNG/PDF/SVG가 덮어쓰던 문제입니다. 공통
helper가 cleanup 전에 exclusive 예약하고 text도 그 파일만 씁니다. File/directory/
hardlink는 통과, Windows 권한 symlink4skip은 남겨 SEC-06은 RUNNING입니다. 고정
Python/native HTTP route/query 대조도 파일 노출이나 state 변경 없이 통과했습니다.

일반 PNG/PDF/SVG에서 JSON/reference 문자열은 object 복원·네트워크/shell/pickle
sink를 시도하지 않았고 위험 href/citation은 거부해 SEC-07은 이 지원 경로에서 PASS입니다.
명시 TeX/PGF·사용자 export directory는 별도 신뢰 경계입니다. 관련128통과/OS6skip,
최소80통과/4skip/2814deselected/경고13·native집중HTTP·스타일/타입/계약/packaging
7명령은 [근거](review_evidence/file_sink_verification.json)에 기록했습니다.
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS70/RUNNING10/OPEN69/DEFERRED1**입니다.

기준621CI의3.10은 Pytest36분 성공 뒤 최소환경 step이 남은23분을 쓰다1h job 한도로
취소됐습니다. Annotation117639290243을 확인했으며 다른3job은 성공입니다. 다음 단위에서
검사를 줄이지 않고 별도 유한 최소환경 job 구조를 검토하되 이번 CI는 아직 바꾸지 않았습니다.
수정은 로컬에 먼저 보존하고 버전/의존성/lock/tag/배포는 유지합니다.

### 이전 리뷰 23차

**리뷰 23차에서 Windows venv/TMP 시작 경계를 분리했습니다.** Print/capabilities·
pipe/file·base/venv·site·TMP/TEMP의12대조를 각각6초로 제한했습니다. 관찰한 venv는
321문자TMP에서 print 전부터 멈추고-S도 같았으나 base Python과 긴TEMP/짧은TMP는
동작했습니다. Host/interpreter 관찰값이지 uv/CPython 보편 임계값이나 Rust capture
결함 확정은 아닙니다.5timed fixture는 성공이 아닌 종료/정리로 기록했습니다.

같은 interpreter의 짧은TMP/긴TEMP bridge 시작/open/action/PNG·한글 metadata·
336문자 source 보존도 통과했습니다. 기존 PowerShell 파일/lock 검사와 함께 지원한
구성·한계를 구분해 PKG-06은 PASS, RUST-04의 일반 자손 정리는 미완료입니다.
Runtime/OS 설정/자동 fallback 변경은 없고 관련47·스타일/타입/계약/packaging6명령이
통과했습니다. [근거](review_evidence/windows_tmp_boundary_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS69/RUNNING9/OPEN71/DEFERRED1**입니다.
621CI 실행 중에는 이 문서 단위를 게시하지 않고 버전/의존성/lock/tag/배포도 유지합니다.

### 이전 리뷰 22차

**리뷰 22차에서 locked dev·허용 범위·격리 build를 구분했습니다.** 별도 locked dev의
43package가 lock과 같고 반복 sync 버전도 같았습니다. 이전 fresh 범위 설치의16차이를
기록하되 모든 사용자가 dev lock과 같아야 한다고 설명하지 않습니다. 별도 fresh PEP517
cache에 Hatchling1.32.0과 build 전이 의존성을 설치했고 sdist→격리 wheel과 현재 환경
build의55member/관찰한 bytes가 같았습니다. 새 무의존 consumer의 외부 core도 통과해
PKG-09는 PASS이며 모든 환경의 동일 bytes를 보장하는 것은 아닙니다.

Matching621 source/artifact에서 문서 command로 두 편집기를 실제 시작해 HTML/spec/
PNG/htmx/0BSD 자산·소유 process 정리를 확인했습니다. Wheel에 없는 UI/source 경계를
명시해 PKG-08은 PASS이며 FIND-025는 'Linux CI 미관찰' 문구를 실제e14run 범위로 고쳤습니다.
이번 runtime 변경은 없고 관련12·스타일/타입/계약/최종 packaging이 통과했습니다.
[근거](review_evidence/isolation_source_editor_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS68/RUNNING10/OPEN71/DEFERRED1**입니다. 기준621CI가 실행 중일 때는 이 문서 단위를
로컬에 보존하고 버전/의존성/lock/tag/배포도 유지합니다.

### 이전 리뷰 21차

**리뷰 21차에서 설치 extras와 저장소 밖 CLI를 확인했습니다.** FIND-024의9안내 누락
surface를 고쳐 기대한 NumPy/Matplotlib/cycler 부재만 colour/render extra로 안내하고
무관한 transitive/compiled 진단은 유지합니다. Color에 Matplotlib을 강제하지 않습니다.
새 설치 wheel 환경의7점진 extra 단계·98console/module CLI가 통과했고 browser package와
별도 Chromium binary도 구분해 PKG-02/04는 PASS입니다.

관련82·최소11통과/2833deselected/경고13과 Ruff221/타입/계약/packaging·설치/source/
wheel hash를 확인했습니다. 4점 robust fixture의 정당한 수렴 오류는 QA에서 기존40점
fixture를 사용했으며 제품 한도는 바꾸지 않았습니다. PowerShell7.6.7의93/336문자 파일
경로·lock·복구는 짧은 CWD에서 통과했지만 긴 CWD console 실패와 longTEMP bridge
ready probe 미완료가 남아 PKG-06은 RUNNING입니다.

기준e14CI39111782233은 Python3.10/3.12·양OS Rust의4job 모두 성공했습니다.
후속 optional 오류 안내의 원격 검증은 아니므로 CI-01은 다음 통합 실행 전 RUNNING입니다.
[근거](review_evidence/installed_matrix_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS66/RUNNING10/OPEN73/DEFERRED1**이며 버전/의존성/lock/tag/배포·미완료 범위는 유지합니다.

### 이전 리뷰 20차

**리뷰 20차에서 marker0 의미와 손상 JSON 복구를 확인했습니다.** FIND-022의9실패는
명시0을 기본 크기로 바꾸는7경로와3D line의 크기 무시였습니다. None 검사/전달만 바꿔
생략/null 기본은 유지합니다.27artist와 nullable139 schema/Python field가 통과했지만
전 필드 CLI/Rust 의미 대조인 JSON-09는 여전히 RUNNING입니다.

API/CLI의 잘린/UTF-8오류/깊이3000에서 기존 출력/복구를 확인하고 nativeHTTP도
26/30/6042byte 손상을422로 거부해 state/PNG를 보존했습니다.188936byte 정상2만행은
무손실 처리해 JSON-12는 이 제한 corpus에서 PASS입니다.249+169대상·최소174통과/
2659deselected/경고13, native18경계·CIguard2, Ruff220/타입/계약/packaging을 기록했습니다.
총240초 중단 시도는 제외하고 완료3receipt 뒤 별도 배치의 통과를 보존했습니다.

**FIND-023은 CI 실행 예산 문제**입니다. 기준063 run39108112974의3.10이45분초과로
취소됐고 check117618247815 annotation으로 확인했습니다. 양 Rust/3.12는 성공했습니다.
전체 검사는 그대로 두고 유한60분과--durations=25로 다음 실행을 측정하며 아직 원격
재성공은 아닙니다. 기준 실행이 끝나 로컬cf95b78과 이번 수정의 게시를 재개합니다.
[증거](review_evidence/json_semantics_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS64/RUNNING10/OPEN75/DEFERRED1**이며 버전/의존성/lock/tag/배포는 유지하고 v1은 미완료입니다.

### 이전 리뷰 19차

**리뷰 19차에서 layer index 타입과 순수 core 경계를 확인했습니다.** FIND-021은
RemoveLayer/SetColorbar/SetLayerAt의 bool이 실제0/1 layer를 선택하거나 다른 noninteger가
TypeError로 새는 문제입니다. 공통 reducer 검사3줄로 거부하고 패널 자동 확장/commit 정책은 유지합니다.

신규35case로 참조/복구·validation-render 오류를 비교하고 CWD/clock/hash+RNG seed/
스타일 순서를 바꾼 새 프로세스 상태 hash가 같았습니다. Core의 데이터 파일/쓰기/네트워크/
subprocess·선택 import를 막되 Python code의 readonly import는 허용하며 sandbox는 아닙니다.
STATE-07/08/09는 PASS, 관련195통과·최소35통과/2628deselected/경고13,
Ruff220/format·Pyright·계약·packaging의7명령 통과를 [근거](review_evidence/core_boundary_verification.json)에 보존합니다.

[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS63/RUNNING11/OPEN75/DEFERRED1**입니다.
현재 작업은 로컬 커밋하고 baseline063 CI를 끊는 cancel-in-progress를 피하려고 완료 전
게시를 보류합니다. 후속 전체/browser/native/양 OS 완료는 아니며 버전/lock/tag/배포도 유지합니다.

### 이전 리뷰 18차

**리뷰 18차에서 빈 산출물 commit을 막고 실제 bridge 실패를 주입했습니다.** FIND-020은
exit0 child의 빈 PNG도 정상으로 commit하던 문제이며 공통 render transport에서
빈 bytes를 거부합니다. PDF/SVG도 같고 전체 binary decode·CPU/disk 보장은 아닙니다.

격리 Unicode 경로 venv의 private hook으로 empty/JSON/nonzero capabilities3,
성공 JSON+1MiBstderr1·실제 regression extra 부재를 포함한 action8·빈 PDF/SVG2의
**14경계**를 확인했습니다. Spec/PNG/redo hash와 정상 복구가 같아 RUST-03은 PASS입니다.
100ms controlled stub timeout 뒤 복구도 통과했지만 자손 소유권 RUST-04는 RUNNING입니다.

Native19통과/helper3ignored·Clippy·fault checker·Ruff219/format·Pyright·계약·
packaging의8기록 명령이 통과했습니다. Snapshot JSON exception은 검증 실패를
숨기지 않으려는 의도로 진단1건을 false-positive 분류했습니다.
[증거](review_evidence/bridge_fault_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS60/RUNNING11/OPEN78/DEFERRED1**입니다. 기준fe4449d CI39104961495는 양 Rust/
3.12 성공,3.10 취소로 전체 cancelled이며 후속 변경을 소급 검증하지 않습니다.
버전/의존성/lock/tag/배포는 유지하며 v1은 아직 미완료입니다.

### 이전 리뷰 17차

**리뷰 17차에서 bridge 오류 크기와 preview/cache 계약을 확인했습니다.** FIND-019는
실패 stderr1MiB가 거대한 UI 오류가 되던 문제입니다. 실패만 raw64KiB와 truncation
표시로 제한하고 성공 stdout/stream 분리는 유지합니다. UTF-8 replacement가 표시 byte를
늘릴 수 있고 disk/CPU/비밀 마스킹/자손 격리를 보장하지 않습니다. RUST-03/04는 RUNNING입니다.

실제 native HTTP6case로 두 방향의499/500/501DPI에서 PNG2000px 상한과 JSON size/DPI·
PDF/SVG 물리 크기를 확인했습니다. Apply/open/undo/redo/reset bridge 실패에서 모든
session/cache 필드도 보존되어 RUST-05/06은 PASS입니다. Native18통과/helper2ignored,
Clippy·focused preview·Ruff219파일/format·Pyright·packaging의7명령이 통과했습니다.
Full smoke foreground240초 timeout은 통과로 세지 않았습니다.

[증거](review_evidence/bridge_preview_verification.json)와 [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS59/RUNNING12/OPEN78/DEFERRED1**입니다. 버전/의존성/lock/tag/배포는 유지하며
새 전체/browser/양 OS 실행이나 v1 완성을 주장하지 않습니다.

### 이전 리뷰 16차

**리뷰 16차에서 raw 혼합 그룹 식별과 데이터/JSON 정책을 확인했습니다.** FIND-018은
NumPy dtype 추론이 문자열/숫자 ID를 합치고 null 존재로 membership이 달라지던 문제입니다.
원래 object 값으로 mask를 계산하며 기본 numeric equality의1/1.0/True 통합과 ordered
모드의 typed 의미를 유지합니다. 표시 caption 중복은 caller 정규화 정책으로 명시합니다.

Empty/singleton/행 순서·known-version unknown field·additive capability·canonical
key/Unicode를 검증했습니다. Optional marker와 제한 Python child의 손상/깊이/큰 JSON
복구는 부분 근거이므로 JSON-09/12는 RUNNING입니다. 관련 **291통과**, 최소
**61통과/2567deselected/경고201**, native **16통과/helper1ignored**이며 Ruff219파일/
format·Pyright·계약·packaging까지8명령이 통과했습니다. LSP는6중4clean/2inconclusive로
구분합니다. [근거](review_evidence/data_json_policy_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS57/RUNNING10/OPEN82/DEFERRED1**입니다.
과거 전체/P0 검사를 이번 renderer 수정의 검증으로 확대하지 않습니다. 버전/의존성/lock/
tag/배포는 유지하며 v1 완성 선언은 아닙니다.

### 이전 리뷰 15차

**리뷰 15차에서 현재 지원 범위 P0 근거를 통합했습니다.** Sharma 원본34쌍·D65/IEC
기준값·독립 OLS mean-CI·범주/그룹/y2 소속·비대칭 행렬 좌표를 보강했고 고정 환경의
fresh-process PNG/PDF/SVG 바이트와 물리 크기를 확인했습니다. 제품 수치/색 교정/default는
바꾸지 않았습니다. 알려진 N/A·선택 의존성·릴리스 보류는 별도로 유지합니다.

로컬 optional 전체 **3423통과/OS조건2skip/경고1** 뒤 QA-only contour API/최소 환경
banner를 고쳤으며 신규72개를 현재/최소 stack에서 다시 통과시켰습니다. 후속 QA까지
포함한 새 단일 전체 실행으로 확대하지 않습니다. 최소53파일을 중복 없는8배치로 실행해
**2573통과/선택25skip**을 확인했으며 단일 순서 실행과는 다릅니다. 실제 무의존 wheel을
저장소 밖 uv venv에 설치해 core/schema/validate/JSON·console/module CLI도 확인했습니다.

[통합 증거](review_evidence/completion_p0_verification.json)에 toolchain/font/lock/artifact/
log hash와 중단 시도를 구분했습니다. 92238f3 원격 CI는 네 job 모두 성공했지만 후속
QA 변경을 소급 검증하지 않습니다. [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS52/RUNNING8/OPEN89/DEFERRED1**이며 CI-01은 새 통합 CI 전 RUNNING,
CI-07 exact publish/tag는 명시적 보류입니다. 원문/버전/의존성/lock/tag/배포는 유지합니다.
남은 P1/P2와 넓은 parity roadmap을 조용히 완료 처리하거나 v1 완성을 선언하지 않습니다.

### 이전 리뷰 14차

**리뷰 14차에서 문서/no-op/long-history 정책을 검증했습니다.** Python open/reset은
새 이력, Rust는 undo 가능한 snapshot이고 reset은 시작 기본 문서로 돌아갑니다.
다운로드는 현재 상태이며 import 파일명을 묶는 dirty-bit/save-target 기능을 추가하지
않았습니다. 같은 값 action도 event로 남기고 redo를 지웁니다. 두 seed의768action과
128undo/128redo checkpoint가 정확히 재생되어 HIST-04/05/06은 이 범위에서 PASS입니다.

FIND-017은 Rust control 요청이 같은 app target을 겹쳐 swap하며 detached-target
pageerror를 내던 문제입니다. Root hx-disabled-elt로 요청 중 control을 비활성화했고
vendor/서버 이력은 바꾸지 않았습니다. 잘못된 form selector와 Open section 가정은 QA만
고쳤습니다. 최종 **이력 대상199통과**, 전체 Python browser **32통과**, 실제 Rust
HTTP/browser 통과이며 최소 history-only는 **20통과/2506deselected/경고13**입니다.
Ruff213파일/format·Pyright·LSP5경로·계약·packaging의9명령을 기록했습니다.

원격781f3f5 Rust Linux/Windows jobs는 MSRV1.88/interpreter/body 단계까지 모두
성공해 RUST-02를 PASS 처리했습니다. Python3.12도 성공했지만3.10이 취소되어
workflow39050108296 전체는 cancelled이지 green이 아닙니다. 이 결과를 후속 UI 변경의
원격 통과로 소급하지 않습니다. [14차 증거](review_evidence/history_policy_verification.json)와
[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS34/RUNNING12/OPEN104**이며 원문/버전/
lock/tag/배포는 유지하고 전체 CI/릴리스/성능 gate는 남깁니다.

### 이전 리뷰 13차

**리뷰 13차에서 미지원 scalar의 조용한 coercion/재귀를 수정했습니다.** FIND-015는
Decimal/custom NaN→null, sNaN의 InvalidOperation, longdouble/same-type/순환 item의
재귀이며 수정 전7개 실패를 확보했습니다. 알려진 NumPy/pandas scalar만 결측으로
판정하고 item은 지원 plain/date 값으로 진행할 때만 변환합니다. Scalar71개 검사가
지원 타입/원객체/strict 거부를 확인하며 손실 float/문자열/null 변환을 하지 않습니다.
DATA-06은 PASS지만 임의 Python method sandbox는 아닙니다.

914a402의 Linux CI는 advanced-effect smoke를 통과한 뒤 default provenance 부재로
실패했고 Windows는 취소됐습니다. 잘못된 interpreter나 실제 remote customizer 경로는
증명되지 않았습니다. 임시 .pth/module recorder와 외부 sitecustomize 보존 self-check로
lookup 가정을 피하고 기존 executable/prefix/version/argv assertion은 유지합니다.
로컬 Windows4case/12children은 통과했지만 Linux 재실행 전 RUST-02는 RUNNING입니다.

기록한 대상 **1116통과/27skip**, optional **244통과/skip0**, 최소 대상 **354통과/
25skip/2142deselected/경고481**, Ruff212파일/format·Pyright·LSP5경로·계약·
packaging·경로 probe의9명령은 [13차 증거](review_evidence/scalar_provenance_verification.json)에
있습니다. 새 browser/native unit count를 주장하지 않습니다. [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS30/RUNNING14/OPEN106**이며 원문/버전/lock/tag/배포는 유지합니다. 전체 suite/OS/
MSRV/보안감사/자원/릴리스 완료는 아닙니다.

### 이전 리뷰 12차

**누적 변경을359277c로 커밋/푸시한 뒤 temporal 정밀도·CI 환경을 이어서 수정했습니다.**
FIND-013은 NumPy fine-unit datetime64가 epoch 정수가 되고 Polars ns가 microsecond로
잘리는 문제이며 수정 전36개 실패를 확보했습니다. dtype/native formatter를 유지하고
parse/equality로 손실 없는 출력만 허용합니다. Coarse 형식/실제 숫자 epoch/NaT/generic
2D는 유지하고 temporal58개로 UTC/offset/DST·child TZ/C locale·여러 입력 경로와
미지원 numeric 날짜 축을 확인했습니다. Arrow upstream 안전 변환 조건도 유지하며
모든 과거 timezone/OS/날짜 축 구현을 주장하지 않습니다.

FIND-014는 CI fixture 환경 불일치입니다. 359277c의 run39045121490은 완료됐고
Python3.10/3.12는 성공, Linux Rust MSRV/lint/unit도 성공했지만 advanced 회귀 smoke가
400으로 실패하고 Windows는 취소됐습니다. Log/source와 render-only 재현으로 선택
의존성 누락을 확인해 job만 extra all로 맞추고 수정 전 실패하는 static guard를 추가했습니다.
격리 all-extra smoke는 로컬 통과했지만 수정 후 원격 CI 재통과는 아직 관찰하지 않았습니다.

기록한 대상 **1045통과/27skip**, optional overlay **173통과/skip0**, 최소 대상
**283통과/25skip/2142deselected/경고481**, Ruff211파일/format·Pyright·LSP5경로·
계약·packaging을 포함한9명령은 [12차 증거](review_evidence/temporal_ci_verification.json)에
있습니다. Browser/native unit의 새 count로 확대하지 않습니다. [대장](REVIEW_CHECKLIST_STATUS.md)은
**PASS29/RUNNING14/OPEN107**, DATA-05는 관찰한 변환 범위에서 PASS입니다.
원문/버전/core 의존성/lock/tag/배포는 유지하며 현재 전체 suite/OS/MSRV/자원/보안/릴리스
gate는 여전히 남아 있습니다.

### 이전 리뷰 11차

**리뷰 11차에서 관찰한 요청 body 경계 matrix를 마무리했습니다.** FIND-011은
Python이 미지원 Transfer-Encoding·중복 길이·짧은 body를 무시하던 문제이며 수정 전
6개 실패를 확보했습니다. Content-Length만 정확히 읽고 잘못된 framing은 action 전에
거부합니다. Python chunked는 새 decoder 없이 명시적으로 거부합니다.

FIND-012는 Rust undo가 unknown-size body 확인 전에 상태를 바꾸던 문제입니다.
계획16MiB+1 중393216bytes를 넘긴 뒤 끊겼으므로 전체 초과 body 수용으로 과장하지
않습니다. 기존 limited Bytes 추출을 모든 handler 앞에 적용하며 parts/기존 한도/
header는 유지합니다. Form/JSON/chunked·undo/reset을 포함한 로컬 순차39case 통과입니다.

Windows venv launcher가 아닌 실제 worker PID의 수명 peak는 Python252.14MiB/
Rust30.40MiB였습니다. Native 렌더 자식은 제외하며 request별 reset/전체 앱 메모리·
CPU hard bound·동시 부하 보장은 아닙니다. 소유한 process tree/listener 정리도 확인했습니다.
SEC-03은 PASS, 계산량/성능인 SEC-04/PERF는 남깁니다.

기록한 대상 **993통과/20skip**, 브라우저 **31통과**, 최소 대상 **232통과/18skip/
2142deselected/경고481**, native Rust **15통과/helper1ignored**입니다. 실제 Rust
HTTP/browser·Clippy/fmt·Ruff209파일·Pyright·LSP7경로·계약·clean sdist→wheel을
포함한13명령/39관찰은 [11차 증거](review_evidence/body_boundary_verification.json)에
있습니다. CI는 구성만 했고 Linux/MSRV 결과가 아닙니다. 의존성/lock/버전/tag/배포는
유지하며 [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS28/RUNNING14/OPEN108**입니다.
더 넓은 릴리스/자원/보안 gate가 완료된 것은 아닙니다.

### 이전 리뷰 10차

**리뷰 10차에서 실제 형식 동등성과 SQL 소유권을 마무리했습니다.** PyArrow26.0.0/
Polars2.0.0을 임시 환경에만 설치해 **114개 모두 통과/skip0**, 추가한 CI 명령도
같은114개가 로컬 통과했습니다(228개 고유 검사로 합산하지 않습니다). Arrow chunks/
dictionary·Polars categorical·borrowed SQL cursor·generic to_dict를 포함한14입력 경로와
정수/boolean/Unicode/null·UTC microseconds·empty/duplicate·Decimal/무한대 거부를
확인했습니다. 모든 optional 버전/정밀도/timezone/OS 인증은 아니며 DATA-01을 해당 범위에서 PASS 처리합니다.

FIND-010의 내부 cursor cleanup 누락은 수정 전5개 실패를 확보했습니다. Connection+
query로 만든 cursor만 지원 시 성공/실패 뒤 닫으며 borrowed cursor/connection과
transaction 제어는 호출자에게 남깁니다. Close 오류/context도 전파하고 minimal duck
cursor도 유지합니다. 소유권10개 검사 통과, DATA-07은 PASS입니다. 의존성/버전은 유지합니다.

프로젝트 대상 **980통과/20skip**(선택 전용18·Windows2), 최소 data-only 대상
**95통과/선택18skip/2266deselected/경고13**입니다. 과거의 더 넓은 최소 환경 반복이
아니며 실제 optional 검사는 별도로 skip 없이 수행했습니다. Ruff207파일/format·
Pyright·LSP6경로·계약·clean sdist→wheel을 포함한9명령과 정리 결과는
[10차 증거](review_evidence/table_sql_verification.json)에 있습니다. 전용 venv는 제거했고
프로젝트의 optional 부재/의존성·lock 비변경을 확인했습니다. 아래 browser/Rust 결과는
새 실행이 아니며 원격 optional CI도 구성만 했습니다.

[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS27/RUNNING15/OPEN108**입니다. 원문/버전/
tag/배포는 유지하며 전체 suite/최소환경/MSRV/Linux/보안/body memory/릴리스 gate는 남아 있습니다.

### 이전 리뷰 9차

**리뷰 9차에서 모델 필드 JSON과 Windows interpreter 경로를 확인했습니다.**
24모델/272필드의 nondefault·대체 union·null fixture와 nested type/JSON 기본 타입을
검사했습니다. Schema-valid지만 옵션 충돌을 의도한 직렬화 fixture이며 렌더/기능
동등성 주장은 아닙니다. 등록37예제 spec은 따로 검사합니다. 실제 Python→Rust→Python
artifact의3figure 값/타입/배열 순서를 보존하여 JSON-01을 PASS 처리했습니다.

별도 한글/공백/`&` venv에서 PATH/env/flag 우선순위와 실제12개 child의 executable/
prefix/version/argv를 검증했고 잘못된 명시 flag는 fallback하지 않았습니다. 첫 offline
준비는 캐시 부족으로 중단됐고, 준비 변경을 명시한 뒤 같은 render 버전만 임시 venv에
내려받아 정리했습니다. 프로젝트 패키지/lock은 유지하며 recorder도 해당 venv 안에만
exclusive 생성합니다. 실제 Windows는 통과했지만 Linux CI는 구성만 한 상태여서
RUST-02는 RUNNING입니다.

기록된 대상 **968통과/4skip**, 최소 환경 **207통과/2skip/2142deselected/경고481**,
Rust native **15통과/helper1ignored**입니다. Ruff205파일/format·Pyright·LSP6경로·
Clippy/fmt·계약·packaging도 통과했습니다. 기본12명령과 QA-isolation/style/package
후속5명령의 source revision을 [9차 증거](review_evidence/codec_path_verification.json)에
분리했으며 아래 브라우저31개는 과거 결과이지 새 실행이 아닙니다. 이번에 제품 결함이나
runtime 재작성이 필요했던 것은 아닙니다.

[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS25/RUNNING16/OPEN109**입니다. 원문/버전/
core 의존성/tag/배포는 그대로이며 전체 suite/최소환경/Linux/MSRV/보안감사/릴리스
gate가 완료된 것은 아닙니다.

### 이전 리뷰 8차

**리뷰 8차에서 공통 상태/실패/로컬 HTTP 경계를 확인했습니다.** FIND-008은 Rust
Host/Origin 거부 응답에 공통 no-store/CSP가 빠지는 문제를 수정했으며 접근 조건은
그대로입니다. FIND-009는 선언 Content-Length>16MiB의 업로드 전 거부를 추가하고
기존 streaming 한도를 유지합니다. 무제한 payload 우회나 content type/chunked/RSS
검증 완료를 뜻하지 않습니다.

공통10작업 fixture로 fluent/functional/Store/CLI/Python/Rust agent·지원 form의
매 상태를 비교했습니다. Log 축/layout/style/reference/typed heatmap과 실제
validation/JSON/render 실패 뒤 양 editor의 spec/PNG/redo 보존을 확인했습니다.
실제 native IPv6 listener/HTTP·Host/Origin matrix·application header·브라우저
CSP 관찰은 [8차 실행 요약](review_evidence/editor_boundary_verification.json)에 있습니다.

최종 **899통과/4skip**, Python 브라우저 **31통과**, 최소 환경 대상 **138통과/
2skip/2142deselected/경고481**입니다. 별도 경고 가시화 조사에서 이전 Matplotlib/
최신 pyparsing의 deprecation/diagnostic을 확인했으며 zero-warning 주장은 아닙니다.
Rust native **14통과/helper1ignored**, 실제 HTTP/browser·Clippy/fmt·Ruff203파일/
format·Pyright·LSP7경로·계약·clean sdist→wheel·IPv6를 포함한13명령이 최종
exit0입니다. MSRV1.88 검증은 아닙니다.

이전 묶음은 body 포함 조기 거부의 Windows10053 및 log decode 실패로 중단되어
완료로 세지 않았습니다. 거부 Origin은 업로드/해석 전403을 요구하는 header-only로
분리하고 정상 origin은 실제 payload를 사용합니다. Transport 원인이 해결됐다고
주장하지 않습니다. [대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS24/RUNNING16/OPEN110**,
SEC-03은 진행 중입니다. 원문/버전/tag/배포/core 의존성은 유지하며 전체 suite/최소환경/
Linux/MSRV/보안 감사/릴리스 gate는 남아 있습니다.

### 이전 리뷰 7차

**리뷰 7차에서 raw 범주 x 결측 표시와 중첩 상태/이력을 확인했습니다.** FIND-007은
null x가 literal None 범주가 되는 문제이며 수정 전10개 실패를 확보했습니다.
공통 `_x_values`가 결측 행 위치에 NaN을 남겨 선을 끊고 점을 mask하며 실제
`"None"` label·shared/y2 좌표를 보존합니다. 연속 날짜 축/새 통계 정책은 아닙니다.

기록한 대상 검사는 **859통과, 4skip**(실제 PyArrow/polars 부재2·Windows조건2),
최소 Python3.10/NumPy1.23 대상은 **98통과, 선택 의존성2skip, 2142deselected,
경고13**입니다. 실제 Rust HTTP/browser의 단계별 spec/PNG·이력 경계/분기·JSON
corpus도 통과했습니다. Ruff201파일/format·Pyright·LSP5경로 확인·계약·clean
sdist→wheel도 통과합니다. 이번에 native Rust unit/MSRV 전체를 새로 실행한 것은 아닙니다.

중첩 reducer 입력/action·snapshot/history/listener 격리·전체 undo/redo·분기를 확인해
STATE-01/02·HIST-01/02·DATA-03을 PASS 처리했습니다. 실제 PyArrow/polars가 없는
DATA-01, 더 넓은 reset/dirty/저장 대상을 검토해야 하는 HIST-04는 RUNNING입니다.
첫 Rust probe의 open=이력초기화 가정은 잘못되어 테스트만 고쳤습니다. 제품 이력 코드는
바꾸지 않고 Python open/reset의 fresh history와 Rust의 undoable 정책을 문서화했습니다.

[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS17/RUNNING15/OPEN118**입니다.
[7차 검증 요약](review_evidence/missing_state_verification.json)에 명령 범위·소스/log
지문·canonical 커서 해시도 남겼습니다. 전체 suite/최소환경/MSRV/Linux/보안/릴리스
gate는 남아 있고 원문 체크리스트·package/editor/spec version·tag/배포는 유지합니다.

### 이전 리뷰 6차

**리뷰 6차에서 DATA-02 입력 구조 검증을 마쳤습니다.** FIND-006은 혼합 record의
위치 없는 AttributeError와 문자열/bytes/dict 행이 문자/key 열로 바뀌는 문제이며
수정 전19개 실패를 확보했습니다. Record mapping/index 검사와 공통 row 값 검증으로
pivot 전에 거부하고 sparse-record null/열 순서·sqlite3.Row는 유지합니다. 열 길이
불일치는 원값을 유지한 채 semantic validation에서 거부하며 자동 resize/coercion은 없습니다.

커밋한 스냅샷96a8592 위의 대상 검사 **677통과, Windows조건2skip**, 최소
Python3.10/NumPy1.23 adapter **66통과, 2142deselected, 경고13**입니다.
Ruff200파일/format·Pyright·계약·clean sdist→wheel도 통과합니다. Active LSP는2경로
중1확인/1inconclusive이며 clean으로 세지 않았습니다(두 변경 경로의 명시적 Pyright는
통과). 없는 x/y/group·실제 pandas 중복 열·잘못된 protocol 열·editor import/action
실패 뒤 state/history/PNG/redo·CLI 입력/출력 bytes 보존을 검사했습니다. 실제
PyArrow/polars는 설치하지 않았고 전체 호환성으로 확대하지 않습니다.

[대장](REVIEW_CHECKLIST_STATUS.md)은 **PASS12/RUNNING13/OPEN125**입니다.
[6차 검증 요약](review_evidence/data_shape_verification.json)으로 로컬 temp log 외에도
결과/소스 지문을 보존합니다. 원문 체크리스트·version/tag/release 상태는 유지합니다.
아래 Rust/전체 브라우저 결과는 이번 Python 변경 이전이며 전체 suite/최소환경/MSRV/
Linux/보안 감사는 아직 남아 있습니다.

### 이전 리뷰 5차

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
