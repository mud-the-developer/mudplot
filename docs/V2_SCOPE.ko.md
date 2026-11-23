# mudplot v2 범위·인수조건

*[English: authoritative feature catalogue](V2_SCOPE.md)*

**2026-10-30 기능 단위 범위 고정. 구현 완료 문서가 아닙니다.**
목표 ID: `mvv0buln-hy7f1o`. Matplotlib/Seaborn의 모든 kwargs를 무제한으로
복제하는 것이 아니라, 현재 문서의 미완료 제품 기능을 끝까지 연결합니다.
영어판의 안정적인 항목 ID·구체 범위·인수 시나리오가 기준입니다.

## 기준선과 승인된 경계

- 기존 **1.1.0 미발행 후보**, schema **0.1**, 미커밋 작업을 보존합니다.
  검증된 아티팩트 hash를 확인하고 `artifacts/v2_baseline_20261030/`에 소스
  archive·tracked patch·파일별 hash를 남겼습니다. `.pi`는 복사·삭제하지 않고
  제자리에 보존했으며 commit·원격 작업은 하지 않았습니다.
- 기존 Linux 검증은 locked Python 3.11/3.12 각각 4,547 통과, 최소 환경
  3,735 통과입니다. 이 결과를 아직 구현하지 않은 v2의 통과로 재사용하지 않습니다.
- 범위 근거: [로드맵](../ROADMAP.md), [기능 커버리지](FEATURE_COVERAGE.md),
  [기존 수치·출력 검증](review_evidence/v1_1_numeric_export_quality.json).
- 비교 기준은 문서의 Seaborn **0.13.2**, Matplotlib **3.11.2**입니다.
  실제 최소 의존성을 자동으로 올린다는 뜻이 아닙니다.
- **Linux 실행 검증 필수**, Windows/macOS는 보류·미검증으로 명시합니다.
  최종 산출물은 **2.0.0 로컬 후보**이며 commit/push/PR/merge/tag/발행은 별도 승인 사항입니다.
- Matplotlib·기존 기본 동작·이전 JSON 읽기/마이그레이션·원본 관측값/순서/알려진
  단위·dependency-free core를 유지합니다. 비호환 API/schema 변경은 먼저 확인합니다.
- smart 그림 품질 제어는 agent-facing입니다. Rust smart 토글은 필수가 아닙니다.

## 항목별 공통 완료 조건

관련 레이어가 존재하거나 테스트 수가 늘었다는 이유로 완료하지 않습니다.
각 항목은 다음을 모두 갖춰야 합니다.

1. 데이터·옵션·통계 가정·의존성/버전·잘못된 조합의 거부 계약.
2. Python builder·action/reducer·capability·schema·JSON·CLI·사용 가능한 Rust 편집 접근.
3. 기존 기본값·0.1 저장물·관측값과 행 ID 보존. 통계/이동은 명시적 요청에만 수행.
4. 수치/통계 reference, artist 배치·속성, 결측·그룹·다중 패널·경계값·지역 RNG 검증.
5. 생성→저장→재개방→편집→undo/redo→내보내기의 실제 사용 흐름과 실행 예제·문서.
6. 기능 배치별 회귀 검사 및 고정 checkpoint의 최소/locked Linux·브라우저·Rust·
   bridge·TeX·정적·보안·설치/패키징 검사.

상태는 **pending / in progress / verified(근거 필수)**입니다. 필수 항목은 모두
pending에서 시작합니다. 기존 subset만으로 나머지 범위를 완료 처리하지 않습니다.
명명한 범위를 줄이거나 뒤로 미루려면 먼저 사용자에게 확인합니다.

## 필수 기능 목록

### 공통 의미 체계·범주형·분포

| ID | v2에서 완성할 내용 |
| --- | --- |
| F01 | 적용 가능한 2-D 계열의 hue/size/style 공유, 연속 색상 colourbar·outline·공유 정규화·guide |
| F02 | 명시적 실제 시간축, 날짜 predictor/category, timezone/unit/origin, 적용 가능한 y2/facet/distribution |
| C01 | strip의 중첩/hue dodge/order/native scale/orientation/jitter |
| C02 | swarm style/date/공유 의미 체계/명명한 marker/범위가 지정된 레이어 간 충돌/live grid |
| C03 | 사전 계산 bxp, bootstrap 중앙값 CI, cap geometry, hue별 component 스타일 |
| C04 | violin 다중 hue split 정책·inner/component·KDE 설정·size/style |
| C05 | 가중 letter values, band/hue별 component와 넓은 mapping |
| C06 | 가중 count, 정규화 범위, 통계적 의미가 정의된 log-value stack/stat-scale |
| C07 | bar/point estimator·추론·semantic/date/native/log/y2 조합 |
| D01 | 전체 곡선/동시 line 추론, 시간/범주/y2 predictor, raw mapping·자동 facet |
| D02 | histogram step+dodge/filled step/fill/poly/discrete/명명한 auto-bin/너비 좌표 |
| D03 | bivariate weighted histogram·KDE 연계·date/y2 |
| D04 | KDE 2-D CDF·colourbar/절대 수준·multiple·명명한 kernel/bandwidth·date/y2/log fit |
| D05 | finite-grid 조건부 HDR과 구분되는 full-support HDR의 수치 질량/오차 계약 |
| D06 | ECDF 연속 semantic/size/style/date/y2와 명시적 이변량 누적 분포 |
| D07 | y rug, 높이/orientation/semantic |
| O01 | 명명한 stat/transform/move/scale의 재현 가능한 선언적 pipeline |

시간축은 불규칙 관측의 실제 간격을 사용하지만 기존 문자열 기본 동작을 몰래 바꾸지
않습니다. 추론은 필요한 가정과 오차를 먼저 정의하고, 잘못된 조합을 다른 통계량으로
바꿔 그리지 않습니다. `bar()`는 계속 사전 계산 값 primitive입니다.

### 회귀·행렬·복합 구성

| ID | v2에서 완성할 내용 |
| --- | --- |
| R01 | 가중/bootstrap/고급 모델 CI, 부분 residualization, fit/scatter 제어 |
| R02 | 독립 residual trend, out-of-sample/deviance 진단과 요청한 추론 |
| M01 | 사용자 annotation matrix, norm, tick rotation, colourbar/layout |
| M02 | 여러 cluster colour track/legend, 명시적 결측/metric, interactive cut/layout |
| G01 | rel/dis/cat/lm builder·live facet·통합 legend·c/colourbar·추론 |
| G02 | pair corner/semantic/weighted/complementary-CDF/nested grid |
| G03 | joint semantic/c/weighted/complementary-CDF/grouped binned/nested/layout |

행렬 값과 annotation을 구분하고, clustering/재배열·cut 뒤에도 원래 행/열 ID와
metadata track이 일치해야 합니다. Joint/pair/facet 통계의 실제 사용 행과 단위가
축 공유 때문에 달라져서는 안 됩니다.

### Matplotlib native 계열·표현 제어

| ID | v2에서 완성할 내용 |
| --- | --- |
| N01 | 안전한 line/marker/collection 속성, 유한 h/v 선분, 비대칭 xy 오차, 수평 band, fill/span |
| N02 | barh/bottom/stack/align/개별 bar/label, pie wedge/text/annotation |
| N03 | 수평·그룹·facet·semantic stem |
| N04 | stairs rebin/fill/open/log/group/facet |
| N05 | eventplot group/facet/log/date/semantic |
| N06 | broken-bar date/group/facet/log |
| N07 | 명시적 grid/extent/mask/RGBA image, pcolor/pcolormesh/spy/상세 contour |
| N08 | triplot/tripcolor/tricontour/f, 삼각분할 surface와 triangle/mask |
| N09 | streamplot/barbs/quiver 제어와 3-D quiver |
| N10 | 3-D 명시 좌표 surface/wireframe/trisurf/bar/contour/voxel/camera/aspect |
| N11 | spectrogram/PSD/CSD/coherence/magnitude·phase spectrum |
| N12 | tick locator/formatter·scale 매개변수·secondary x/명명한 변환 |
| N13 | inset/nested/mosaic 배치·span/ratio·안정적 panel ID |
| P01 | palette/context/colormap·공유 범위/norm·colourbar·legend 열/명명한 handler |
| N14 | patch/path/table/span·annotation 좌표 변환·명명한 path effect |

새 렌더러를 만들지 않습니다. 새 upstream API는 최소 환경을 유지하는 guard/fallback
또는 명확한 version gate가 필요합니다. 같은 기능을 계열 두 곳에서 중복 집계하지 않습니다.

### 제품 전체 완료 항목

| ID | v2 완료 조건 |
| --- | --- |
| E01 | 모든 항목의 설치된 Python/JSON/CLI·Rust 편집·undo/redo·export 연결 |
| Q01 | 수치·시각 QA, 읽을 수 있는 출력, 실패 보호·privacy·기존 자원 경계 |
| DOC01 | 실행 예제·정확한 지원 표기·핵심 양언어 문서·이전 사용자 업그레이드 안내 |
| REL01 | 전체 Linux qualification·버전 일치·독립 재빌드·실제 설치·정확한 아티팩트·로컬 2.0.0 후보 |

## 승인된 조건부 평가

이 항목들은 **평가가 필수**이고, 무조건 refactor가 필수인 것은 아닙니다.

- **CND01:** 실제 Rust 편집 흐름을 Python의 특수 축/드래그와 비교합니다.
  필요한 조작이 없거나 사용 불가능하면 그 제어와 브라우저/history 검사를 v2에 포함합니다.
- **CND02:** 실제 대형 inline-data·긴 history의 재현 가능한 workload와 지연/할당을
  측정합니다. 근거가 있으면 structural sharing/replay checkpoint 등 최소 개선과
  aliasing/isolation 검사를 수행합니다. 근거 없이 한도를 올리거나 SLA를 만들지 않습니다.
- **CND03:** DESIGN의 TOC가 이 작업의 탐색·검토를 실제로 방해하는지 기록합니다.
  문제가 확인된 부분만 분리하고 링크를 검사합니다.

필요성이 없으면 **조건 미발동**으로 기록하며 구현 완료라고 표시하지 않습니다.
조건이 발동하면 v2 안에서 구현·검증하거나, 범위 변경을 사용자에게 확인해야 합니다.

## 명시적 제외·안전 경계

- JSON에 pickled 함수·eval/exec·임의 callback·opaque artist를 넣지 않습니다.
  안전한 named/registered 제어는 typed 계약과 명시적 의존성 경계를 가져야 합니다.
- 임의 kwargs 전면 동등성, drop-in seaborn.objects, deprecated distplot,
  온라인 dataset 다운로드·노트북 palette widget·global-state alias는 필수가 아닙니다.
- animation/GUI widget/event callback/arbitrary artist는 기존 native Python lane입니다.
  수동 native 편집을 선언적 지원으로 집계하지 않습니다.
- 원격 session/auth·native Rust renderer·Rust 전체 schema 강타입화·실제 publication은 제외합니다.
- PGF 보호는 일반 실패 복구이며 동시 독자의 다중 파일 원자성이나 강제 종료 내구성
  보장이 아닙니다. 복구 실패 시 backup과 오류 note를 보존합니다.
- 실제 원본 데이터·실물 인쇄·보류 OS를 검사하지 않았다면 검증 완료라고 주장하지 않습니다.

원본 요구를 바꿔 완료 수를 늘리지 않습니다. 항목 ID별 실행 근거를 추가하고,
영어판에 대응되지 않는 원본 gap이 발견되면 범위 blocker로 기록해 확인합니다.

## 구현 배치 근거

- **C06 — 구현 및 로컬 기능 검사 통과:** 가중 합, 사용자가 선택한 패널별
  `all/category/group` 분모와 명시한 양의 baseline에서 원본 누적합을 보존하는
  log 누적을 구현했습니다. 극단적 수치의 양의 질량·빈 선택 facet·기존 JSON·
  방향/native 축·실제 Chromium/Rust 편집/history/export·CLI·설치 wheel의
  렌더를 검사했습니다. [수치 계약](WEIGHTED_COUNTS.ko.md)과
  [완료 기능 근거](review_evidence/v2_count_scopes.json)를 참조하세요.
  [초기 부분 작업 근거](review_evidence/v2_weighted_counts.json)는 그대로 보존하며,
  그 이전 시점의 전체 완료 주장으로 해석하지 않습니다.
- 이는 필수 기능 한 개이며 통계 task나 G01/E01/Q01/DOC01/REL01·v2 후보 전체의
  완료가 아닙니다. 고정 제품의 지원 Python/Linux/TeX·보안·설치 matrix·독립 재빌드
  관문은 남아 있습니다. 개별 근거가 없는 나머지 필수 항목과 모든 조건부 평가는
  미완료입니다.
- **F02 — 진행 중, core Cartesian 경로 검증:** API/action/schema/JSON,
  raw·통계·범주·분포·회귀의 시간 view, local calendar tick, 실제 Chromium/Rust
  metadata 편집/history/export와 설치 wheel·CLI 검사를
  [core 근거](review_evidence/v2_temporal_core.json)와 [시간 계약](TEMPORAL_AXES.ko.md)에
  기록했습니다. [순수 파서 근거](review_evidence/v2_temporal_groundwork.json)는
  과거 기록으로 유지합니다. 원문·offset·단위·선택된 원본 ID를 보존합니다.
- **F02 raw/native 확장 검증:** bar/errorbar/band/stackplot/rug/hexbin 시간 좌표,
  절대 uncertainty 끝점·origin 없는 기간 변환·stem/stairs/event/start-duration을
  수치·결측·최소 환경·실제 native Chromium/Rust history/reopen/export와 설치
  wheel·CLI로 검사했습니다. [Raw/native 근거](review_evidence/v2_temporal_raw_native.json)를
  참조하세요. N01–N06/D07의 더 넓은 고유 기능 완료를 뜻하지는 않습니다.
- **F02 ISO joint/pair 확장 검증:** 변수별 명시 clock·marginal/diagonal 축·그룹 선택·
  쌍별 결측에 숫자 day geometry 기준과 실제 Chromium/Rust raw-action/편집/history/
  reopen/export·설치 wheel/CLI 근거가 있습니다.
  [Grid 근거](review_evidence/v2_temporal_grids.json)를 참조하세요.
  더 넓은 G02/G03 기능은 계속 필수이며 제외나 후속 버전 이관이 아닙니다.
  F02/E01/REL01 전체 완료를 주장하지 않습니다.
- **F02 보조 y축 부분집합 검증:** 수직 hist/KDE/ECDF는 관측값의 공유 x clock을
  유지하고 숫자 개수·밀도만 y2로 옮깁니다. 명시적 시간축 semantic scatter/line과
  기존 raw y2 경로에 숫자 day geometry·원본/JSON/action 보존과 실제 Chromium/Rust
  편집/history/reopen·3종 export 근거가 있습니다. 독립 검토에서 주 y축 범주 검증에
  y2가 섞이는 문제와 y2 품질 진단 누락을 발견해 재현·수정하고 회귀 검사를 추가했습니다.
  [보조 y축 근거](review_evidence/v2_temporal_secondary.json)를 참조하세요.
  F01/D06의 추가 의미 매핑·ECDF 이변량 누적 분포와 나머지 catalogue는 계속 필수이며
  해당 행이나 REL01 전체 완료가 아닙니다.
- **D02 step+dodge 부분집합 검증:** 빈 그룹의 예약 자리까지 기존 dodged bar와 같은
  raw hue 슬롯·가중/누적 높이를 사용합니다. 반전 log·가로 방향·날짜/y2 교차 경로의
  native-stairs 수치 기준과 실제 Chromium/Rust 인간 도형 편집/history/reopen·3종
  export·설치 API/CLI 검사를 [step+dodge 근거](review_evidence/v2_histogram_step_dodge.r2.json)에
  기록했습니다. 나머지 D02 단위는 계속 필수이며 해당 행 전체 완료가 아닙니다.
- **D02 명시 fill 부분집합 검증:** 선택 bool/null `fill`로 채운 native step과 outline
  막대를 layer/stack/dodge에서 지원하며 가중 높이·질량은 바꾸지 않습니다. 생략 시 이전
  여섯 필드 JSON·생성자를 보존하고, 이전 wheel의 기본값 7개에서 spec/action JSON과
  렌더 픽셀이 정확히 일치합니다. 채운 step의 해칭 대비, 명시 alpha/edge·0 두께·빈
  스타일 자리·log/date/y2·거부한 편집의 상태 보존을 수치·SVG·실제 Chromium/Rust
  수명주기로 검사했습니다. [Fill 근거](review_evidence/v2_histogram_fill.json)를 참조하세요.
  공개 schema·필드 fixture·설치 API/CLI·영한 안내를 동기화했습니다. 나머지 D02
  필수 단위는 아래 구성비/poly 확장과 미완료 항목에 구분합니다.
- **D02 구성비/poly 부분집합 검증:** 사용자가 선택한 계약대로 기존
  stat/common_norm/cumulative 높이를 먼저 계산한 뒤 bin별 그룹 합으로 나눕니다.
  누적 fill은 CDF가 아닌 구성비이며 감소할 수 있습니다. Poly는 원자료 bin/슬롯
  중심의 native 선/면이고 기본은 선입니다. 최소 두 표현 가능한 중심이 필요하며
  추정·jitter·빈 레이어의 축 범위 오염을 추가하지 않습니다. 수치/native 기준,
  overflow/subnormal 보호, v/h/log/반전/date/y2, collection 해칭 진단과
  API/action/JSON/CLI·실제 Chromium/Rust 편집/history/reopen·3종 export를
  [모드 근거](review_evidence/v2_histogram_modes.json)에 기록합니다. 이전 wheel
  기본값의 JSON/action/픽셀 일치도 확인했습니다. Discrete/명명 자동 bin과 전체
  width-coordinate 계약은 계속 필수이며 제외·후속 버전 이관이 아닙니다. D02와
  통계 task 전체 완료를 주장하지 않습니다.
- **D02 제한 binning 기능 근거:** 고정된 8종 명명 규칙, 할당 전 개수 상한, 가중치 크기와 독립적인 경계 선택, 정수/입력 단위 discrete bin 및 엄격한 자정·정밀도 거부를 [binning 근거](review_evidence/v2_histogram_bins.json)에 기록합니다. 기존 fill·모드·step+dodge 근거와 함께 유한 D02 기능 행을 다루되 부모의 종결 검토와 최종 RC 자격 검증이 남습니다. current/minimum core는 각각 563 통과·skip 0이며 이후 interface 41 current·2 minimum은 별도 결과로 최종 전체 트리 563 재실행이 아닙니다. 기존 기본값은 불변입니다. D02 종결 검토/최종 자격 검증이 남으며 통계 목표 전체나 v2.0 출시 완료를 주장하지 않습니다.
- **D02 제한 인수 종결:** 부모 검증과 독립 검토로 동결된 D02 기능 범위의 인수를 종결했습니다. [종결 기록](review_evidence/v2_histogram_bins_closure.json)은 불변 binning 스냅샷·이전 geometry 근거와 현재 소스 계보, 실제 브라우저·파일 검사, 시각 확인 및 기존 기본값 보존을 연결합니다. 기능 인수만 종결하며 최종 고정 소스 자격 검증·다른 catalogue 행·로컬 2.0.0 후보 완성은 아직 남아 있습니다.
- **C01 범주 strip 기능 배치 — 진행 중:** 명시한 category×hue order/dodge 빈 슬롯,
  v/h·native 숫자/log/날짜 간격·typed local uniform/none jitter를 구현하고 새 제어
  생략 시 기존 raw-x 경로·JSON을 유지합니다. 슬롯 비율·seed 계약과 targeted
  399개 검사, 실제 편집 JSON·PNG/SVG/PDF 예제 출력을
  [기능 근거](review_evidence/v2_strip_categories.json)에 기록합니다.
  실제 browser/Rust 편집·history·재개방·export와 설치 API/CLI·지원 최소 환경·
  부모 인수 전에는 C01을 종결하지 않으며 F01·v2 전체 완료도 아닙니다.

- **CND03 평가 완료 — 조건 미발동:** DESIGN/source/history/dependency를 실제 탐색한
  결과 구체적인 목차 장애가 없어서 분리·재구성을 정당화하지 못했습니다.
  기존 Store 64-action checkpoint를 정확히 기술한 영한 문구 수정은 별도 정확성
  유지이며 구조 재구성 조건의 발동이 아닙니다.
  [탐색 평가](review_evidence/v2_design_navigation.json)는 CND03의 필수 평가만
  종결합니다. CND01/CND02의 조건·구현·검증은 각각 별도 근거에서 다룹니다.

- **CND01: 조건 발동 및 Rust 특수 제어 구현.** 실제 Chromium 비교에서 Rust 두 번째 패널 축 제어와 이동 핸들이 없거나 사용할 수 없음을 확인했습니다. 활성 패널 x/y/y2/z와 지원하는 native 제목·범례·text/annotate 이동을 설치 Python 경계로 제공하고 generic layer/raw action 접근을 유지합니다. [로컬 기능 근거](review_evidence/v2_rust_specialized_controls.json)에 시도·설치/browser 수명주기 결과·native pixel 기준·소스와 산출물 hash를 보존합니다. CND01과 관련 E01의 근거이며 전체 catalogue의 E01이나 REL01 완료가 아닙니다. Package 1.1.0·schema 0.1·원자료·의존성 하한은 유지합니다.
- **M01 annotation/회전 부분집합 — 진행 중:** 같은 모양의 사용자 문자열 주석과
  tick 회전은 숫자 색상값·mask·원래 행/열 ID를 보존하고 clustermap과 함께
  재배열됩니다. 검토한 isolated patch를 통합했으며 현재 main의 수치/artist/
  editor-history 검사와 실제 생성·저장·재개방·CLI·PNG/SVG/PDF 흐름은
  [부분집합 근거](review_evidence/v2_heatmap_annotations.json)에 기록합니다.
  추가 norm/colourbar/layout·전체 Rust/browser/설치 검증·최종 Linux 관문은
  계속 필수이며 M01 전체 종결이 아닙니다.

- **C01 제한 기능 인수 종결:** 부모의 source/raster/vector 구조 검토와 실제
  Rust/browser layer 편집·history·재개방·export, 하나의 C01+M01 부분집합+CND02
  고정 snapshot 설치·최소 환경을 인수했습니다.
  [종결 근거](review_evidence/v2_strip_categories_closure.json)는 앞선 부분 근거,
  명령·source/wheel hash·harness 실패 수정 계보와 별도 current 407/minimum 369
  cohort를 보존합니다. 최종 제품 Linux/REL01과 넓은 F01 역할은 여전히 필수입니다.
- **CND02 조건 발동 평가 해결:** 승인된 기본 Store 즉시 undo/redo 개선을 통합하고
  alias/격리/custom 재생/실패 경계, 동일 100k×1000 완료 workload·설치 core 근거로
  인수했습니다. [History 근거](review_evidence/v2_history_immediate.json)는 잠정
  의견·구현 전 발동 결정·별도 isolated/integrated 측정을 보존합니다. 이전 graph
  하나 추가 보관·상한 불변·깊은 undo 실패의 기존 비원자성을 명시하며 Rust history/
  CND01·최종 REL01의 완료를 뜻하지 않습니다.

- **F01 기존 계열 guide 증분 — 진행 중:** scatter/lineplot의 명시 숫자 hue
  colourbar·point 윤곽을 연결합니다. 관측 축이 아닌 정규화 guide 좌표에 mark와
  같은 안정적 map/cmap·정확한 raw tick을 쓰며 상수·signed extreme·이웃/subnormal
  경계를 유지합니다. 그리기 전에 논리 panel/shared scope를 계획해 후순위 요청/
  primary/y2를 함께 처리하고 충돌한 요청 label은 거부합니다.
  [증분 근거](review_evidence/v2_semantic_colourbars.json)는 초기 실패·재현과 수정한
  current 197/minimum 30 검사·실제 예제 출력·소스 hash를 보존합니다. 모든 명명한
  적용 계열 adapter·4계열 시나리오·설치/browser·최종 관문은 계속 필수이며 F01
  전체 종결이 아닙니다.

- **F01 4계열 부분집합 검증 — 전체 종결 아님:** scatter/line/strip/ECDF의 원본
  row domain·mark별 물리 단위·가중 우연속 knot·범주 예약을 서로 다른 current/
  minimum **726 통과** cohort로 검증했습니다.
  [부분집합 근거](review_evidence/v2_semantic_families.json)는 temporal 변환 전에
  지원하지 않는 수평 semantic lineplot/y2를 거부하는 guard와 실제 예제/CLI를
  기록합니다. 이전 705 통과/1 실패는 통과 근거가 아니며 넓은 F01은 열려 있습니다.
- **C01 positional 호환 보충:** 선택 strip 필드를 기존 필드 뒤에 두어 이전
  positional alpha를 보존합니다. 실제 archived/current engine 모두 0.25로
  bind·render되며 [보충 근거](review_evidence/v2_strip_positional_compatibility.json)는
  원래 C01 종결/보관본을 덮어쓰지 않습니다.
- **D07 전체 기능 workflow — 부모 기능 인수 종결:** x/기본-y/y2 rug의
  live blended 관측/axes-fraction 변환·유한 높이·raw-row hue/point-stroke/dash는
  독립 dataLim·자동 범위를 오염시키지 않습니다. 높이/stroke 0도 segment를
  보존합니다. [Workflow 근거](review_evidence/v2_rug.json)는 독립 native/날짜/
  log/DPI/layout/group/facet/빈 셀 참조와 실제 Rust human form의 잘못된 편집
  보존·history·download·재개방·PNG/SVG/PDF 및 검토한 raster를 기록합니다.
  실제 archived engine과 고정 current source를 새로 실행해 기존 4개 사례의
  spec/action/RGBA가 정확히 같음을 확인하고 초기 불일치는 실패 계보로 유지합니다.
  Test-only 검토 정리 전 broad current/minimum은 각각 **987 통과**입니다.
  같은 고정 1.1.0 wheel 하나로 checkout 밖 API/CLI와 별도 **127 reviewed tests씩**,
  third-party effect를 실제 차단한 Python `-S` wheel-zip pure builder/validate/
  action/JSON을 실행했습니다. 기존 no-deps 시나리오도 환경별로 별도 1개씩
  통과했습니다. 합산이나 새 전체-tree 통과 수가 아니며 test-only 변경으로 같은
  engine을 재빌드하지 않았습니다. CND01은 미통합이고 넓은 F01/F02·제품 고정
  관문/REL01은 계속 필수입니다.
  부모가 전체 source/raster/proof 계보·명령·제한과 실제 설치 및 의존성 차단 pure
  경로를 검토하여 D07을 인수했습니다. F01/F02/E01/Q01/DOC01/REL01 전체나 v2의
  완료는 아니며 고정 archive/wheel·실패 근거는 그대로 보존합니다.

- **CND01 조정 통합 — 부모 기능 인수 종결:** 검토한 특수 제어 patch를
  현재 F01/D07에 통합하고 원래 layer index·공유 guide·rug·clock을 보존합니다.
  [통합 근거](review_evidence/v2_cnd01_integration.json)는 source current **413 통과**,
  설치 current **144 통과**, pinned minimum **16 통과/skip 0**, 실제 fractional
  native pixel 기준, Rust **library 20 + binary 1 통과/helper 5 ignored**,
  Rust 1.88·clippy/format·생성물 동기화·프로젝트 타입 검사를 구분합니다.
  새 고정 snapshot/wheel 하나를 두 설치 환경에서 사용하고 source fallback 없는
  driver/native 참조/bridge origin과 desktop/mobile 화면을 보존합니다.
  이전 isolated 54/16/2·Rust 근거는 역사 자료이며 통합 검증으로 바꾸지 않습니다.
  Peer의 외부 서비스 실패 후 준비된 최소 harness를 이 worker가 실행했으며 peer
  검증을 주장하지 않습니다. 기존 D07 보관본은 그대로이며 E01/F01/F02 전체나
  제품/REL01 관문의 완료는 아닙니다.
  부모가 통합 source/raster/proof 계보와 별도 current/minimum 환경을 인수했습니다.
  세 조건부 평가 모두 해결했으며 전역 E01/QA/docs/REL01이나 남은 v2 catalogue의
  완료는 아닙니다. 기존 고정 보관본/wheel·실패 근거는 그대로 보존합니다.

- **C02 전체 기능 workflow — 부모 최종 기능 인수 종결:** 실제 명명 marker와
  원본 행 hue/지름/style, panel/실제 축 로컬의 명시 레이어 간 packing을 구현했습니다.
  기존 layer당 usable 2,000행 상한은 그대로이며 별도 profile 근거의 새 scope당
  physical instance 4,000개 상한은 SLA나 CND02에 따른 기존 상한 인상이 아닙니다.
  [전체 행 근거](review_evidence/v2_swarm_workflow.json)에 독립 native path/stroke/
  측정값, date/log/방향/y2, redraw/DPI/layout/facet, 혼잡 시 모든 instance 유지,
  실제 이전 engine의 8개 exact legacy 비교, 설치 action/JSON/CLI/무의존 경로와
  실제 Rust 사람 편집/history/reopen/PNG/SVG/PDF를 기록합니다.
  Source current/minimum의 **각 1,035 통과/host TeX skip 1**은 해당 고정 test
  snapshot입니다. 검토한 test-only oracle 수정을 포함한 최종 설치 current/minimum은
  **각 302 통과/host TeX skip 1**이며 복사한 figure 격리 fixture와 일치하는 설치
  driver/native 참조/bridge를 사용합니다. 두 cohort를 합산하지 않습니다.
  부모가 수정한 출판 예제와 별도 읽기 쉬운 Rust 화면/native vector를 인수했습니다.
  Rust PNG 다운로드는 기존 capped cached preview이며 같은 다운로드 JSON을 두
  설치 CLI에서 렌더한 요청 DPI PNG는 정확히 **3,600×2,100**입니다.
  조밀한 기능 stress 화면을 출판 가독성 QA로 주장하지 않습니다. 부모가 최종
  source/raster/proof 계보를 검토하여 C02 전체 행을 인수했으며 넓은 catalogue와
  최종 제품 검증은 계속 필수입니다.
- **G01 재사용 live-template 증분, 전체 행 종결 아님:** C02는 해결된 selector/order와
  빈 예약 cell을 고정하는 typed 직렬화 전체-template 명시 transaction을 사용합니다.
  Cell-local 편집은 로컬이며 나중의 명시 전체 교체가 이를 대체합니다. Reopen 시
  저장된 materialized view가 진실이고 자동 reactive 재생성이 아닙니다. Ratio-only
  편집은 일부만 찬 grid를 보존하고 구조 교체/실제 panel 확장은 view를 보존하며
  recipe를 해제합니다. 실제 reopen 이후 Rust 편집·cell별 native geometry·거절
  보존·history는 같은 C02 근거에 있으며 넓은 G01 계열/조합은 계속 필수입니다.
- **N11 조정 통합 — 부모 최종 기능 인수 종결:**
  [통합 spectral 근거](review_evidence/v2_signal_spectra_integration.json)는 검토 patch와
  7종 native 신호를 같은 단일 C02+N11 wheel에 연결합니다. 명시 sampling/window/
  FFT/parity/unit, 독립 수치 참조, 작은 even-bin coherence 후 양호한 odd padding,
  실제 Rust generic form과 설치 current/minimum을 검증했습니다. 별도 통합 offline
  TeX 두 환경은 같은 wheel을 새로 설치하고 각 PGF 7개/8쪽을 LuaLaTeX→BibTeX→
  Lua×2로 컴파일하여 citation/PDF link/native·추출 Σ/²를 확인했습니다.
  Host에서 skip한 PGF 회귀는 각 실제 TeX 환경에서 별도로 통과했으며 source 통과 수에
  더하지 않습니다. Isolated PGF 근거는 별도 보존합니다. Float64 계산상 zero mask는
  물리적 정확한 zero의 증명이나 극단 dynamic range FFT 상대 정확도 보장이 아닙니다.
  버전/floor/publication 변경이나 전체 F01/F02/G01/E01/Q01/DOC01/REL01/v2 완료가
  아닙니다. 부모가 통합 source·current/minimum consumer·실제 Rust·컴파일 PGF
  근거를 검토하여 지정한 N11 로컬 기능 관문 전체를 인수했습니다.

- **C03 전체 기능 workflow — 부모 최종 기능 인수 종결:** 기존 box layer에
  typed column 참조 `bxp`·원자료 seeded 중앙값 bootstrap CI·최종 body 폭 비율 cap·
  정확한 raw key의 hue별 component를 연결했습니다. [전체 근거](review_evidence/v2_box_workflow.json)는
  **engine 64개 module**을 단일 immutable wheel/source archive에 연결하고 독립
  native/cbook/seeded/Fraction geometry·primary/y2/date/log/v-h·선택 mark availability·
  역할 소유권·실제 Rust/설치 수명주기와 실제 이전 engine **12개 exact legacy
  비교**를 보존합니다. 새 advanced 상한은 **그리는 cell256·선택 source행10000
  AND 별도 declared flier값10000**이며 기존 무요청 상한/JSON은 유지합니다.
  공유 선택 통계/percentile·zero-stroke root는 실제 관측값·독립 marker/fill과
  mean/sum 산술을 보존합니다. 기존 live 경계에서 새 hue별 예약을 view 검증 전에
  해결하고 한 열 값 x가 아닌 실제 category source를 사용합니다. 옛 명시 order는
  문자 그대로이고 `order=None`이 별도 추론 요청입니다. 정정한 인과관계와 실제
  immutable 이전 engine 대비를 실패 자료와 구분해 보존합니다.
  고정 source current/minimum **각1674 통과/host PGF skip2**, 설치 current/minimum
  **각586 통과/host PGF skip2**, postfreeze test-only primary/y2 native/log
  **각16 통과**는 각각의 snapshot/cohort이며 합산하지 않습니다. Host에서 skip한
  Box/N11 두 PGF 회귀는 실제 TeX 두 환경에서 모두 통과하고 native box PGF5개를
  LuaLaTeX→BibTeX→Lua×2로 각6쪽 컴파일하여 citation/URI/μm·glyph를 확인했습니다.
  부모가 실제 예제·읽기 쉬운 설치 Rust 화면·최소 환경 compiled contact sheet를
  시각 인수했으며 IQR 밖의 실제 CI도 clip하지 않습니다. Rust PNG는 기존 capped
  cached preview이고 같은 다운로드 JSON의 설치 CLI PNG는 두 환경 모두 정확히
  **3600×2100**입니다. 부모가 최종 source/raster/proof 계보를 검토하여 지정한
  C03 로컬 기능 관문 전체를 인수했습니다. 전체 F01/F02/G01/E01/Q01/DOC01/REL01/v2·
  통합 N12 근거나 버전/floor 변경·발행을 주장하지 않습니다.

- **N12 조정 통합 — 부모 최종 기능 인수 종결:**
  유한한 tick locator/formatter·native scale parameter·derived axis 계약을
  최신 C03/C02/live 코드를 보존하여 통합했습니다.
  [통합 근거](review_evidence/v2_axis_controls_integrated.json)는 **engine66개 module**을
  새 단일 wheel/source archive·current/minimum 설치 prefix·독립 native 참조에
  연결합니다. 기존 isolated N12와 인수한 C03 archive 근거는 별도로 보존합니다.
  고정 source 두 환경은 **각2019 통과/host PGF skip2**입니다. 원래 설치 cohort는
  **각1156 통과/설치 전용 child-import harness 실패1/skip2**로 그대로 보존하며,
  해당 private `-S` import root만 고친 뒤 영향받은 사례를 환경별 **별도1 통과**로
  기록합니다. Child의 실제 설치 origin·66개 hash를 확인했고 결과를 합산하거나
  원래 cohort를 전체 통과로 바꾸지 않습니다.
  두 환경의 실제 Rust/Python 화면에서 human form·primary/y2 handle 경계·native
  frame 기반 base-two pointer·거절 원자성·history·4종 다운로드·재열기를 실행했고,
  매 revision의 실제 표시 image decoded RGBA가 현재 cached PNG와 일치합니다.
  부모가 기능 stress 화면과 별도의 읽기 쉬운 **5100×3000** 6패널 예제를 인수했습니다.
  같은 wheel의 새 offline 설치에서 환경별 **native PGF8개**를 LuaLaTeX→BibTeX→
  Lua×2로 **문서10쪽** 컴파일했습니다. 07쪽은 wrapper pagination 빈 쪽,
  10쪽은 bibliography이므로 plot10개가 아닙니다. Wrapper header만 고쳐 재컴파일한
  계보와 변하지 않은 PGF hash를 보존합니다. 실제 μm/Σ/²·2100년20/21µs·citation·
  PDF URI와 missing-character 없음이 확인되었고 부모가 compiled 페이지를 인수했습니다.
  별도 TeX 회귀는 환경별 **3 통과/187 deselected/skip0**입니다. 실제 immutable
  C03 engine과 새 engine의 **10개 사례/환경**에서 JSON/actions/RGBA/limits/label이
  정확히 같습니다. Rust PNG 다운로드는 기존 **2000×533** capped preview이고,
  같은 다운로드 JSON의 두 설치 CLI PNG는 정확히 **4500×1200**입니다.
  전체 notice와 `MIT AND LicenseRef-Matplotlib` metadata를 확인했으며 own MIT·
  dependency floor·package1.1.0/schema0.1은 바뀌지 않았습니다. 부모가 최종
  source/raster/proof/ledger 전체를 검토하여 승인한 N12 workflow 전체를 기능
  인수했습니다. 전체 F01/F02/G01/E01/Q01/DOC01/REL01/v2나 N13 완료를 주장하지 않습니다.

- **C04 전체 workflow — 부모 최종 기능 인수 종결:**
  [근거](review_evidence/v2_violin.json)는 하나·홀수·예약 hue의 paired-half,
  가중 정규화, 실제 inner/component, BODY 윤곽 stroke pt SIZE와 실제 STYLE
  glyph, date/native/log/y2·고정 live-template 편집을 **69개 모듈/94de3f91…
  단일 wheel**에 연결합니다. Native raw 상속과 최소 버전의 no-line 처리는
  독립 fill/glyph를 보존합니다. 원래 current SOURCE 결과 **2662 통과/
  obsolete-contract 실패1/skip6**과 수정된 소비자 사례 **별도1 통과**를
  합치지 않습니다. 명시적 test overlay의 minimum SOURCE는 **2663 통과/skip6**,
  설치 current/minimum은 **각1718 통과/host PGF skip3**입니다. 필수 browser·
  같은 native/bridge interpreter·source fallback 없음·매 test figure 종료를
  적용했습니다. SOURCE skip6은 host PGF3+없는 CJK font3이며 font 통과가 아닙니다.
  실제 offline TeX는 별도 **환경별4 통과/279 deselected**입니다.
  두 환경의 실제 Rust/Python form·live/role/inner 편집·거절/history·download·
  reopen에서 표시 PNG의 decoded RGBA가 현재 revision과 일치합니다. 부모가
  읽기 쉬운 실제 편집 화면과 수정한 publication/compiled 예제를 인수했습니다.
  Hue guide는 다섯 treatment별 한 번이고 shared guide가 tail을 덮지 않습니다.
  실제 native 상한 **profile256/선택10000행/support1000/closure 포함512768정점**,
  별도 **stick segment10000개와 관측 diamond SVG glyph10000개**를 보존합니다.
  다운로드 PNG는 **2000×1166** capped preview이며 같은 JSON의 API/CLI는
  정확한 **3600×2100** 동일 RGBA입니다. 잘못된 입력은 이전 완성 출력을 보존합니다.
  실제 인수한 N12 engine과 새 engine의 **환경별24개 비교 가능 사례**에서
  JSON/actions/RGBA/limits/label이 같습니다. 원래 실패·archive는 보존하고,
  test만 고친 최종 SOURCE/SDIST binding을 별도로 기록하며 runtime wheel을
  다시 만들지 않습니다. Package1.1.0/schema0.1·own MIT/전체 notice·floor는 같습니다.

- **N13 조정 통합 — 부모 최종 기능 인수 종결:**
  [통합 근거](review_evidence/v2_panel_layout_integrated.json)는 isolated r4와
  구별합니다. 같은 wheel에서 단일 flat 유한 graph·안정 ID·span/ratio·실제
  child inset·sharing·부분 live grid selector·명시적 native Tight와 opt-in 단위
  검사를 실행하며 기존 no-opt-in 공유는 바꾸지 않습니다. 두 설치 환경에서
  thin과 balanced **grid256/panel256/cell1024/layer1024**를 모두 그렸고,
  depth16·depth17/cycle 거절·이전 출력 보존·**실제 tick label16384개**를
  sampling 없이 확인했습니다. 기능/진단 비용 stress이지 가독성·RSS·SLA 증명이
  아닙니다. 네 실제 frontend/profile flow의 현재 PNG decoded checkpoint15개와
  실제 source-unset·69 hash·driver/bridge/frontend envelope가 같은 wheel에
  연결됩니다. 1400/540px 전체 화면에서 채워진 control8개가 가로 overflow 없이
  도달 가능합니다. Offline 환경별 **native PGF13개→문서14쪽**은 plot13개와
  bibliography이며 citation/URI·실제 μm/Σ/²/clock glyph를 확인했습니다.
  Desktop/TeX current NumPy는 별도 기록하고 isolated count를 통합 결과로
  바꾸지 않습니다. 두 행은 전체 F01/F02/G01/E01/Q01/DOC01/REL01/v2 완료가 아닙니다.

- **C05 Main 전체 workflow — 부모 최종 기능 인수 종결:**
  [근거](review_evidence/v2_boxen_workflow.json)는 corrected R4의 전체 isolated
  근거와 새 **de3fe109… wheel/71모듈 aa6243b8… runtime**을 구별합니다. 두 새
  설치 환경에서 독립 가중 LEFT band/tail·True/1 역할·실제 BODY pt/flier glyph·
  원본 ID·date/log/y2의 선택/empty live 셀·로컬/전체 template 교체·undo/redo/
  reopen·실제 CLI PNG/SVG/PDF·완성 출력 보존을 실행했습니다. Python-S는
  NumPy/Matplotlib/SciPy를 능동 거절하면서 배포한 순수 C05/C07 builder/action/
  JSON workflow를 실행합니다. 부모가 전체 isolated named ledger와 별도 통합
  근거를 모두 검토하고 C05 전체 행을 기능 인수했습니다. 더 넓은 catalogue
  gate는 열린 상태입니다.

- **C07 전체 workflow — 부모 최종 기능 인수 종결:**
  [같은 artifact 근거](review_evidence/v2_statistical_workflow.json)는
  **de3fe109… wheel/71모듈 aa6243b8… runtime**·불변 SDK906파일·최종
  SOURCE/SDIST 전용 consumer/docs 수정 lineage를 연결합니다. 두 frozen source는
  각각 **3010통과/명시적 TeX·CJK skip22**이며 합산하지 않습니다. 원래 설치
  **2183통과/skip11/setup-error20** cohort는 실패로 남기고 짧은 OWN TMP의
  browser **32통과/공개 전제 test실패1** 및 각각 별도 **1통과** continuation을
  전체 통과로 바꾸지 않습니다. 실제 두 frontend·두 설치 환경의 workflow와
  가독성 flow별 현재 PNG decoded checkpoint10개·다운로드/재열기·같은 JSON의
  정확한 API/CLI **3600×2100** PNG를 실행했습니다. 독립 native geometry는
  72/300DPI·v/h·primary/y2·실제 반전 inset을 확인합니다. 실제 선택10000행/
  cell256 및 전체 요청100000 resample의 **unit+case work2B/random원소1B**를
  독립 CI·RNG state와 비교했으며 SLA/RSS 보장이 아닙니다. Offline 환경별
  **native PGF7개→문서8쪽**에 Lua/BibTeX·실제 glyph/URI/reference를 확인합니다.
  실제 archived control16개는 환경별 spec/action/RGBA/label이 같고, 다섯 native
  view endpoint의 최대2ULP 차이는 명시적으로 exact-limit 동등성이 아닙니다.
  부모가 전체 근거 matrix와 정확한 일곱 nonruntime 경로 SOURCE/SDIST 수정을
  검토하여 지정한 C07 로컬 gate 전체를 기능 인수했습니다. 원래 실패 cohort와
  모든 불변 identity를 보존하며 더 넓은 F01/F02/G01/E01/Q01/DOC01/REL01/v2
  완료는 주장하지 않습니다.

- **C06 전체 workflow·최종 source lineage — 부모 인수 종결:**
  [보충 근거](review_evidence/v2_count_scopes_final_source.json)는 기존 owner
  결정·cohort·visual/editor 근거를 보존하고 현재 71모듈 aa6243b8…/de3fe109…
  wheel/수정 SDK908파일에 연결합니다. 두 맞는 설치 환경의 새 public native
  consumer는 all/category/group 분모·raw log-stack top·선택된 panel-local/
  empty view·로컬/전체 template 기록·실제 CLI·완성 출력 거절 보존을 손계산과
  비교하며 Python-S는 optional library를 능동 거절합니다. 기존 cohort를 확인용
  재실행하거나 현재 결과로 바꾸지 않았고 새 count 기능을 추가하지 않았습니다.

- **D02 bounded 전체 workflow·최종 source lineage — 부모 인수 종결:**
  [보충 근거](review_evidence/v2_histogram_final_source.json)는 기존 전체 bounded
  D02 인수·여덟 규칙/native/visual/editor 근거를 보존합니다. 두 최종 wheel
  설치 smoke는 가중 비균일 filled step+dodge·outline·fill/poly·auto/discrete/
  time-unit·date/y2 geometry와 CLI/action/reopen을 실제 실행하며 Python-S는
  모든 고정 bin 규칙을 확인합니다. Histogram/bin 수학과 native histogram
  renderer 경계는 기존 승인 source와 같습니다. Hash만이나 옛 전체 cohort
  재실행이 아닌 누락된 최신 source 연결이며 REL01·더 넓은 행은 열린 상태입니다.
