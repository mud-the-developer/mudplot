# Changelog

All notable changes to this project are documented here.

## [Unreleased]

- Added a bilingual Fumadocs site built from the repository guides and deployed separately from Python releases. Moved the long README guides into the documentation.
- 저장소 가이드를 바탕으로 이중 언어 Fumadocs 사이트를 추가했습니다. Python 릴리스와 별도로 배포하며, README의 상세 안내를 문서로 옮겼습니다.

## [2.0.0]

Package and editor metadata align at 2.0.0. The JSON wire schema remains 0.1.
Artifacts are available from the [official GitHub release](https://github.com/mud-the-developer/mudplot/releases/tag/v2.0.0)
once the release workflow publishes them.

The combined panel legend stays above populated secondary-y marks without
moving legends away from primary data when the twin is empty.

### Added / 추가

- N14 adds finite literal patches/Path codes, native tables, mixed-coordinate
  annotation anchors, shared spans and named physical stroke/shadow effects.
- N14는 리터럴 패치·Path 코드, 네이티브 표, 혼합 좌표 주석, 공통 구간 음영과
  지정된 물리 단위 획/그림자 효과를 추가합니다.

- N02 adds supplied horizontal bars, explicit baselines/alignment and signed
  stacks, raw per-bar styles/labels and native pie wedge/text controls.
- N02는 원자료의 가로 막대, 명시 기준값·정렬·부호 누적, 막대별 스타일/라벨과
  원형 조각/텍스트 제어를 추가합니다.

- N01 adds finite native line/collection styles, data-coordinate segments,
  asymmetric error magnitudes, horizontal and vertical bands and data spans.
- N01은 네이티브 스타일, 원자료 좌표의 선분, 비대칭 오차, 가로/세로 띠와
  데이터 구간 음영을 추가합니다.

- G02/G03 add weighted original-row pair and joint views, true lower-corner
  cells, strict complementary ECDFs, native grouped binned centers and a
  real center-y2 to marginal-y link that preserves independent statistic axes.
- G02/G03은 원자료 행의 가중 pair/joint, 실제 아래 삼각 셀, 엄격한 보완 ECDF,
  네이티브 그룹 bin, 독립 통계축을 유지하는 중심 y2–주변 y 연결을 추가합니다.

- G01 adds finite relational, distribution, categorical and regression facet
  builders, pooled scatter-c calibration, and native figure legends for
  eligible grouped marks.
- G01은 관계·분포·범주·회귀 facet 빌더, 공통 원시 scatter-c 보정과 지원되는
  그룹 mark의 네이티브 figure 범례를 추가합니다.

- P01 adds render-local typography contexts, authored categorical palettes
  and native scalar maps with named shared ranges, local calibrated bars,
  and finite legend columns and handlers.
- P01은 렌더링 내부 글자 크기 context, 사용자 범주 팔레트, 공유 원시
  범위·개별 색상표, 유한 범례 열과 네이티브 handler를 추가합니다.

- F01 regression glyphs share hue, physical marker diameter and marker style
  with scatter without changing any R4 fit, sampling or diagnostic inputs.
  Typed hold-out selectors no longer inherit sibling mark/axis restrictions.
- F01 회귀점은 R4 입력·표본·진단을 바꾸지 않고 색, 물리 지름, 마커를
  매핑합니다. hold-out 선택자는 형제 레이어나 축 제약을 상속하지 않습니다.

- N10 adds native explicit nonuniform 3-D grids, signed bars, projected
  contours, voxels, and a typed display-only camera.
- N10은 비균일 3D 격자, 부호 있는 막대, 투영 등고선, 복셀 및
  화면 전용 타입 기반 카메라를 추가합니다.

- N09 adds typed native planar and 3-D quiver, raw-unit barbs, and finite
  uniform-grid streamplots without changing the legacy quiver path.
- N09은 타입 기반 평면·3D 화살표, 원시 단위 바브와 유한한 균일 격자
  유선 표시를 추가합니다. 기존 quiver 경로는 그대로입니다.

- Full-model HDR reuses a certified native geometry bound across compatible
  draws, without reusing backend-specific clipping checks or raising limits.
- 전체 모델 HDR은 호환되는 그리기에서 네이티브 기하 인증 범위를 재사용하되,
  백엔드별 클리핑 검사는 다시 수행하며 자원 한도는 그대로 유지합니다.

- A generated full-HDR unit label that is taller than its canvas can wrap
  at a word break on a single constrained-grid colourbar without changing calibration.
- 캔버스보다 높은 단일 제약 그리드의 전체 HDR 단위 라벨은 원시 보정을
  바꾸지 않고 기존 공백에서 줄을 바꿀 수 있습니다.

- N08 adds explicit masked triangle edges, face/vertex colours, contours and
  a native 3-D `trisurf` sharing the same persisted XY topology.
- N08은 명시적 연결·마스크를 사용하는 삼각형 변과 면·정점 색, 등고선,
  동일 XY 연결을 공유하는 네이티브 3D `trisurf`를 추가합니다.

- N07 adds [explicit native grid fields](docs/HEATMAP.md#explicit-native-grid-fields):
  scalar/RGB(A) images, rectilinear meshes, dense spy and editable contour levels
  and labels. Old unit-grid contours retain their existing behavior.
- N07은 [명시적 네이티브 격자](docs/HEATMAP.ko.md)를 추가합니다. 스칼라/RGB(A)
  영상, 직교 격자, 밀집 `spy`와 등고선 레벨·라벨을 지원하며 기존 등고선은
  그대로 동작합니다.

- Stacked statistic colourbars reserve a measured grid lane once while retaining
  every visible bar's native bounds in tight exports.
- 그리드에 쌓인 통계 색상 막대의 너비는 한 번만 예약하고, 여백을 자르는
  내보내기에도 모든 막대의 표시 경계를 유지합니다.

- N05/N06 add [event](docs/EVENTPLOT.md) and [interval](docs/BROKEN_BARH.md)
  group/facet lanes with explicit raw spacing, dates and log endpoints. Events
  support shared hue, physical stroke width and named dashes in source order.
- N05/N06은 [이벤트](docs/EVENTPLOT.ko.md)와 [구간](docs/BROKEN_BARH.ko.md)의
  그룹·패싯, 원시 간격, 날짜·로그 끝점을 지원합니다. 이벤트에는 원본 순서의
  공유 색·물리 선 두께·점선 매핑을 적용할 수 있습니다.

- N04 adds [native stairs](docs/STAIRS.md) with explicit mass/density rebinning,
  open and filled windows, fixed group/facet selection and positive log geometry.
- N04 [계단 플롯](docs/STAIRS.ko.md)은 질량·밀도 재구간화, 열린 경로와 채우기,
  고정 그룹·패싯 선택 및 양수 로그 좌표를 지원합니다.

- F01: typed histogram and count bodies accept shared raw hue, physical
  outline size and native dashes without changing mass denominators.
- F01: 히스토그램·도수 막대의 공유 색, 외곽선 두께와 선 스타일을 추가합니다.
  가중 질량 분모는 표시 스타일과 분리됩니다.

- N03 extends [stem plots](docs/STEM.md) with horizontal primary/twin axes,
  fixed typed groups and facets, explicit date coordinates, and shared per-mark
  hue, stroke width and marker/dash guides without changing the source rows.
- N03 [스템 플롯](docs/STEM.ko.md)은 수평 기본·보조 축, 고정 그룹과 패싯,
  명시적 날짜 좌표 및 색·선 두께·마커/점선 공유 범례를 지원합니다.

- O01 adds typed [coordinate composition](docs/COORDINATE_PIPELINE.md) before
  existing statistics and native moves, preserving raw source rows and JSON
  defaults. Live date category orders now keep every eligible spelling of a
  saved UTC instant; explicitly repeated instants still reject.
- O01 [좌표 합성](docs/COORDINATE_PIPELINE.ko.md)은 원본과 기존 JSON을
  보존하며 통계·배치 전에 적용됩니다. 날짜 패싯은 같은 시각의 다른 표기도
  함께 선택하고, 명시적 중복 시각은 계속 거부합니다.

- M01/M02 add scalar matrix norms and calibrated colourbars, explicit nullable
  clustered data and supplied condensed geometry, ordered tracks/legends, and
  editor cuts selecting original indices. See [heatmaps](docs/HEATMAP.md) and
  [clustering and matrix reservations](docs/CLUSTERMAP.md).
- M01/M02는 행렬 norm/색상표, 명시적 결측·제공 거리, 범주 트랙/범례와
  원본 인덱스 군집 절단 편집을 추가합니다. [행렬](docs/HEATMAP.ko.md) ·
  [군집 및 자원 예약](docs/CLUSTERMAP.ko.md).
- M01/M02 reject a positive computed merge height that would restore to zero
  and use the native constrained engine for advanced all-Cartesian nested matrices.
- M01/M02는 단위를 복원할 때 0이 되는 양수 병합 높이를 거부하며, 고급 행렬의
  직교좌표 중첩 배치에서 native constrained 엔진을 사용합니다.

- R01/R02 add strict appended regression bootstrap/partial/sampling/diagnostics/
  components declarations: one uniform paired physical-case percentile law with
  original criterion masses, full-basis/joint/two-stage nuisance fits, real source-
  aligned query/raw/deviance diagnostics and independently refitted full residual
  trends. All requested replicates remain; undefined required fits reject without
  retries, clipping, hidden deletion or changing point factory when CI is enabled.
  NEW-only6B invocation/figure work,19-column full design and conservative256MiB
  numerical managed/provider-reserve admission include actual target/stage/tail/
  seed/lifetime costs, not an RSS/native-artist/opaque-provider allocation promise.
  Existing omitted defaults, package1.1.0/schema0.1, providers/floors and native limits remain.
  See [regression science/API/resource workflow](docs/REGRESSION.md).
- R01/R02는 기존 네 positional 필드 뒤 strict bootstrap/partial/sampling/
  diagnostics/components를 추가합니다. 원래 기준질량의 균등 physical-case 추출,
  전체 nuisance/독립 trend 재적합, 실제 원행 query/raw/deviance와 모든 B 유지/
  정의불가 거부를 명시합니다. NEW6B/전체19열/보수적256MiB numerical admission은
  RSS/native artist/opaque provider 보장이 아니며 기존 생략 경로·버전·의존성·
  native 경계를 바꾸지 않습니다. [한국어 계약](docs/REGRESSION.ko.md).
- R01/R02 numerical admission borrows original source/spec values, projects
  consumed columns once, and preflights all known figure byte lifetimes before
  the first RNG. Paired-case curve traversal uses the first positive original
  training/query occurrence independently of display order; sparse strict errors
  retain original row indices.
- R01/R02는 원자료/spec 값을 빌려 쓰고 소비 열을 한 번만 준비하며, 알려진 전체
  figure byte 수명을 첫 RNG 전에 검사합니다. 추출 곡선 순서는 표시 순서와 무관한
  첫 양의 training/query 원행을 따르고 sparse strict 오류도 원행 위치를 유지합니다.

- Gaussian joint-CDF rectangles now use signed Plackett/fourth-derivative
  integration, outward exact-midpoint enclosures and exact current-leaf dyadic
  totals. Bounded exact field-local reuse ends before native output;
  original-law1e-6/source/pool/positive-prefix
  semantics and all guards stay unchanged, without an arbitrary relative-
  precision promise or a new numerical provider.
- Gaussian 결합 CDF는 부호 있는 Plackett 적분·미분 경계·정확한 중점 포함구간·
  현재 leaf의 정확한 합을 쓰며, 한 필드의 제한된 동일 결과 재사용은 native
  출력 전에 끝납니다.
  원래 법칙의1e-6·원천/모집단/양수 prefix와 자원 경계는 그대로이며 새 수치
  provider나 임의 상대 정밀도 보장을 추가하지 않습니다.

- D01 adds strict persisted LineSpec predictor/resampling/calibration/family
  declarations: complete original-unit percentile and exact finite-grid
  max-deviation inference, with honest undefined support and empirical-only
  nonregular extrema envelopes. Calibration is independent of bars/ribbon
  geometry. Native numeric/real-clock/categorical, v/h and actual y2 routes
  preserve per-curve missing topology without disconnecting unrelated irregular
  curves. Raw supplied lines gain independent physical hue/size/style mappings,
  never averaging or discarding source order/duplicates/barriers.
- D01 adds scale_id-owned SharedGuideSpec / SetSharedGuides whole-list requests
  and populated controls in both editors. Actual family-specific native contexts
  remain distinct unless truly equivalent; dataset legends/unrelated scales stay.
  Raw/estimated line mapping domains use the existing predictor-selected finite
  observation cohort; excluded rows cannot create guides for empty reservations.
  Complete-unit missing-response topology remains separate.
  Empty mapped line families still register declared predictor reservations on
  their actual target axes without manufacturing data or guide artists.
  Fixed live facets retain stable N13 selectors/IDs/placements through nesting,
  local edits and explicit whole-template transactions. NEW-only componentized
  2B figure work and conservative256MiB working-state admission use exact bounded
  tails, not full replicate matrices; omitted/predictor-only/cheap views retain
  old admission. See [the complete line workflow](docs/LINE_WORKFLOW.md).
  Weighted-total tail/endpoint/comparison bounds retain the real canonical weight
  denominator; mean cancellation and all numeric/RNG kernels remain unchanged.
  Percentile finalization also charges its actual per-vector sign-negation
  objects and overlapping ordered-list/sort workspace, not a full matrix.
  Shared inverse-log effects reject positive working intervals that round to a
  false zero native span, including inherited cell routes, without changing RNG.
- D01은 엄격한 저장 LineSpec으로 원본 unit 전체 percentile·유한-grid
  max-deviation을 구분합니다. Undefined support를 숨기지 않고 min/max는 두
  calibration 모두 nonregular 경험 envelope로 표시합니다. Bars/ribbon은
  calibration과 독립이며 numeric/date/categorical·v/h·실제 y2와 curve별 결측
  topology를 지원합니다. Raw line은 독립 물리 hue/size/style을 추가하되 원본
  순서·중복·장벽을 평균/제거하지 않습니다.
- scale_id가 유일한 membership인 SharedGuideSpec/SetSharedGuides 전체 list와
  두 editor의 채워진 control을 추가합니다. 실제 mark family/native 문맥을
  구분하고 진짜 같은 문맥만 합치며 dataset legend/다른 scale은 유지합니다.
  Raw/추정 line 매핑 domain은 기존 predictor 선택 finite 관측 cohort를 사용해
  제외된 행이 빈 예약 view에 guide를 만들지 않습니다. Complete-unit 결측 응답
  topology는 별도로 보존합니다.
  매핑할 관측이 없어도 실제 target 축의 선언한 predictor 예약 자리는 표시하고
  data/guide artist를 만들지 않습니다.
  Live facet의 N13 selector/ID/placement·local/whole-template 의미도 보존합니다.
  NEW 전용 component별2B figure work·보수적256MiB working state·정확한 bounded
  tail을 사용하며 omitted/predictor-only/저렴한 view의 기존 승인은 유지합니다.
  [Line workflow 한국어](docs/LINE_WORKFLOW.ko.md)를 참고하세요.
  Weighted total의 tail/endpoint/비교 byte 상한에는 실제 canonical weight 분모를
  포함하며 mean 분모 상쇄와 수치·RNG kernel은 바꾸지 않습니다.
  Percentile 마무리의 실제 vector별 부호 반전 객체와 동시에 살아 있는 정렬
  list/sort workspace도 계상하며 전체 반복 행렬로 부풀리지 않습니다.
  공유 역-log effect는 양의 working 구간이 가짜0 native 폭으로 반올림되면 기존
  cell 경로도 거부하며 RNG는 바꾸지 않습니다.

- D03–D06 add strict logical BivariateBinsSpec/Histogram2DSpec/ECDF2DSpec/HDRSpec
  declarations and source-preserving paired workflows. Six histogram statistics
  use true nonuniform raw/day areas and in-bin effective-hue/global mass; optional
  KDE shares the pre-tally cohort, never count-height scaling. Gaussian and
  variance-one Cholesky product-Epanechnikov share canonical physical covariance/
  Kish/Scott/Silverman meaning. Shared-grid 1D layer/stack/fill and cumulative
  contribution/composition remain distinct from an original-law joint CDF.
  Actual primary/y2/v-h/clocks and explicit log10-fit data/fit Jacobian units reuse
  the existing axis/row boundaries. Joint ECDF keeps every interior source knot,
  exact tied/prefix masses and strict OR complement; percent combines its unit
  before final float rounding. Statistic bars keep actual raw mappables/norms,
  including subnormal values, separate from semantic hue guides.
- Explicit full-model HDR calibrates ordered unknown cutoffs and retains all
  requested levels as disjoint earliest-band guaranteed-inside native cells.
  Support/source/numeric/transform/native/visible-clip error statements stay
  separate; visible probability is not labelled target mass or raster-pixel mass.
  NEW-only figure-wide2B composite work/256MiB owned working and retained state/
  1M live pair scalars/2M native closure-inclusive vertices retain old admission
  and separate D01/C07 ledgers. Construction caches release at real lifetimes;
  bounded depth-first tessellation and growing edge/polygon scratch are admitted
  before allocation, without recursive concatenations or reverse-slice copies.
  Physical-cohort/group construction, empirical edge/order/native-probe
  workspaces are prospectively admitted, with borrowed source leaves excluded.
  Temporal capability layers share the actual dispatch authority, including ecdf2d.
  Multiple owned statistic bars use one measured native lane; generated prose
  units wrap without shortening raw ticks/authored math, and real backend
  guide/body/twin bounds reject physically unresolved output.
  Provisional lane width uses full native axis bounds to settle label anchors;
  final visible-component checks retain a shared spine and actual owner frame.
  Unresolved requests reject wholly; no tolerance/level/data substitution.
  [Scientific/API/resource workflow](docs/DENSITY_FIELDS.md) and
  [executable example](examples/density_fields.py); final same-artifact
  installed/editor/product qualification remains separate.
- D03–D06은 명시적인 짝지은 bin/통계/KDE/결합 ECDF/전체-HDR 모델을 추가합니다.
  실제 원자료/day 면적·빈 내부 분모와 집계 전 동일 KDE 코호트를 유지하며
  원본 행·질량·식별자를 바꾸지 않습니다. Gaussian/Cholesky product-Epanechnikov,
  물리 공분산/Kish, 1D stack/구성비와 원래 법칙의 결합 CDF를 구분합니다.
  Actual primary/y2/v-h/clock·log10 fit/Jacobian 단위, 모든 경험 매듭·strict OR,
  최종 반올림 전 percent와 실제 원시 통계 mappable을 유지합니다.
  전체 HDR은 오차를 분리한 내부 보장 셀 합집합이며 보이는 질량을 목표 p나
  픽셀 질량으로 부르지 않습니다. NEW 전용2B/256MiB/1M/2M 경계와
  깊이 우선·증가 scratch의 사전 수락은 기존 경로/D01/C07을 바꾸지 않습니다.
  코호트·그룹 및 경험 경계·정렬·네이티브 검사 공간도 할당 전에 수락하고 원본
  값은 빌린 참조로 유지합니다. 시간 capability는 실제 ecdf2d 포함 dispatch와 같습니다.
  여러 통계 막대는 측정한 네이티브 영역을 함께 쓰며 생성 단위 설명만 줄바꿈합니다.
  원시 눈금·작성 수학은 유지하고 실제 장식·본체·보조축 경계가 맞지 않으면 거부합니다.
  임시 영역 너비는 실제 축 경계로 라벨 위치를 정하며, 최종 구성요소 검사는
  공통 막대 기준선과 실제 소유 축 영역을 유지합니다.
  실패를 축소된 허용오차·생략한 레벨·다른 데이터로 대신하지 않습니다.
  [한국어 계약](docs/DENSITY_FIELDS.ko.md); 최종 동일 artifact 검증은 별도입니다.
- Shared figure guide colourbars are figure-owned decorations rather than data
  axes children. Measured whole-axis decoration bands repair nested column
  spacing without moving manual titles/ticks or changing canvas/source geometry;
  final unresolved spacing still warns. Invalid implicit layout shapes/types/
  capacity reject before shared-axis expansion instead of leaking IndexError.

- C07 adds finite weighted estimator/inference combinations, exact declared-percent
  LEFT PI, full-exponent canonical source-unit reductions/moments and real
  bar-outline/point-diameter/curve-stroke role guides. Typed date/native/log/y2 and
  explicit live-template/local edits use the existing reducer/ReplaceLayer path.
  NEW-only10000selected rows/256pointwise cells/2Bactual resampling-work guard,
  compact case counts and1M active chunks preserve old admitted weighted/unit/
  dense-line routes and seeded paired schedules. Whole-effect rejection never
  returns prefix uncertainty, truncates resamples or rewrites observations.
  Guides inherit actual native zero/nonzero stroke/fill/glyph contexts; opaque
  unit IDs include empty strings, and explicit N13 sharing distinguishes weighted
  totals (value*mass) from means/raw values without changing the old unit gate.
- C07은 가중 named 통계·정확한 percent LEFT PI·canonical 원자료 산술/moment·
  실제 bar 윤곽/point 지름/curve stroke guide를 지원합니다. Date/native/log/y2·
  whole-template/로컬 편집은 기존 reducer/ReplaceLayer를 사용합니다. NEW 전용
  선택10000행/점별256cell/실제2Bwork와1M active chunk는 기존 가중치·units·
  dense-line 승인을 바꾸지 않고 seed·행 쌍을 보존합니다. 초과하면 요청 전체를
  거부하며 prefix CI/줄인 resample/원본 변경/SLA·RSS 약속을 만들지 않습니다.
  Guide는 실제 zero/nonzero stroke·fill·glyph를 상속하고 opaque unit ID의 빈
  문자열을 허용합니다. N13의 명시적 공유는 가중 total(value*mass)과 평균/원자료
  value를 구별하며 기존 단위 gate를 바꾸지 않습니다.

- C05 adds declared relative-weight LEFT letter values, exact empirical band/tail
  masses, physical-row Kish stopping, stable rank/side/raw-hue component ownership
  and BODY colour/stroke/dash plus actual observed-flier mappings through shared
  C04 selectors/domains/traits. New effect admission is32768 real band paths/
  1000000 requested flier instances per figure; advanced source rows10000/cells256
  per layer. Pure source validation does not fit; rendering prepares once before
  native construction. These are not SLA/RAM claims; legacy admission/depth32 stay.
  Declared secondary targets also compose with filtered and live facet cells.
- C05는 상대 가중 LEFT 분위수·정확한 경험 band/tail 질량·물리 행 Kish 깊이·
  안정적 rank/side/raw-hue 스타일과 실제 BODY/관측 flier 매핑을 같은 C04
  규칙으로 제공합니다. 새 한도는 layer 원본 행10000/cell256, figure 실제
  띠32768/요청 flier1000000이며 원본 검증과 한번의 effect 준비를 구분합니다.
  기존 admission/깊이32를 유지하며 SLA/RAM 보장은 아닙니다.
  선언한 보조 축을 필터·live facet cell 및 cell별 편집/기록과 함께 유지합니다.
- Generic typed ReplaceLayer edits an already existing integer-indexed layer
  without expansion/reordering or implicit live-template changes. Both real
  editors populate collapsed full action JSON, retaining normal preview-commit,
  rejection/history/reopen and existing generation/pointer ownership.
- Typed ReplaceLayer는 기존 정수 인덱스 layer를 확장/재정렬/recipe 변경 없이
  교체합니다. 양쪽 편집기의 접힌 전체 actionJSON·정상 preview commit·실패/기록/
  재열기와 기존 세대/pointer 소유권을 유지합니다.
- Correct finite unweighted type7 interpolation with one final rounding,
  including the observed subnormal even median, without special-case values,
  source mutation or a copied private selector.
- 비가중 type7 보간은 관측된 subnormal 짝수 중앙값을 포함해 한 번만
  반올림하며 특정 값 예외/원본 변경/비공개 selector 복제를 사용하지 않습니다.
- PGF reference export now balances the same hyperlink independently inside
  each native text group for explicit multiline and automatically wrapped
  labels. Citations remain once at their original final marker, outside the
  hyperlink; font/style, placement, source text and measurement stay unchanged.
- PGF 참조는 명시적 여러 줄·자동 줄바꿈의 각 native 텍스트 그룹 안에서 같은
  링크를 완결합니다. 인용은 마지막 원래 위치에서 링크 밖에 한 번만 유지하며,
  글꼴·스타일·배치·원문·측정 규칙을 바꾸지 않습니다.

- C04 adds explicit paired multi-hue half-violin lanes, H=1/odd tails/reserved
  slots, native mode-specific and typed per-hue component traits, and shared
  hue/BODY-outline-point/style mappings. Weighted tuple fits retain original
  rows and normalize by effective hue/global pools with one reference plan.
  Applicable date/native/log/v-h/y2/facet/live paths reuse the existing boundary.
  Advanced admission is10000 selected rows/256 drawn profiles, categorical64
  levels/overrides and existing1000 support points; no continuous-value64 cap.
- C04는 명시 paired 다중 hue 반쪽·H=1/홀수/예약 자리·mode별/typed hue별 native
  component·공유 hue/BODY 윤곽 point/style을 추가합니다. 원본 행/가중 fit을
  보존하고 effective hue/전체 pool 참조를 한 번 해결하며 기존 날짜/target/live
  기반을 재사용합니다. Advanced 행10000/profile256/범주형64/support1000이며
  연속 숫자값64 제한·기존 상한 확대·callable·임의 kwargs는 없습니다.
- Raw unextended violin component-only edits retain actual native inner
  flag/color/span defaults through already fitted native statistics, without
  refitting or erasing extended normalization. New Collection component proof
  on Matplotlib3.8 exposed lowercase no-line setter incompatibility; canonical
  native no-stroke representation retains segments/fill/independent glyphs.
  Logical raw-hue guides no longer repeat per category, without global label
  deduplication or dropping any plotted profile.
- 비확장 raw violin의 component-only 편집은 이미 fit한 native 통계로 기존
  inner flag/color/span을 재fit 없이 유지합니다. MPL3.8의 새 Collection
  component no-line token 문제는 native 표현으로 해결해 segment/fill/독립
  glyph를 보존하고 범주별 중복 hue guide만 logical 소유권에서 제거합니다.

- N13 adds typed stable panel identities and one declarative cell/span/inset
  convention for native nested grids and mosaics, empty positions/frames,
  ratios, safe rename/reorder/removal and complete placement updates. Named and
  hierarchical sharing use the same pure components as N12 tick inheritance;
  known statistical/spectral units are not mixed with observation axes.
  Both real editors expose populated layout actions and retain generation-safe
  visible previews. Old 0.1 omitted defaults and regular-grid rendering remain;
  isolated qualification does not close G02/G03, REL01 or the v2 catalogue.
- N13에 안정적 typed 패널 ID·단일 cell/span/inset 규칙·native 중첩 grid/mosaic·
  빈 자리/frame·비율·명시적 이름/순서/삭제/전체 배치 편집을 추가합니다.
  공유·N12 눈금 상속은 같은 순수 component를 쓰며 알려진 통계/스펙트럼 단위를
  관측값 축과 섞지 않습니다. 양쪽 편집기의 배치 폼·세대별 preview를 유지하고
  기존 버전/하한/기본 경로는 그대로입니다. 전체 v2 완료 주장이 아닙니다.
- Actual sparse legacy-open browser proof exposed missing Rust layout forms.
  Forms now consume effective renderer panel identities/counts without adding
  phantom defaults to the saved sparse document before a structural action.
- 실제 sparse legacy-open에서 빠졌던 Rust 배치 폼은 renderer의 유효 패널
  ID/수를 사용하도록 고쳤습니다. 구조 action 전 원본에 가짜 기본 필드를 넣지 않습니다.
- N13 explicit hierarchies uniformly select native tight layout before
  axes/colourbars. Full-bound thin and balanced constrained-solver stalls are
  retained as failure evidence; there is no threshold/fallback/drop-to-fit.
  Engine-specific guide rectangles and honest native decoration warnings remain.
- N13 명시 hierarchy는 axes/colorbar 생성 전 native tight layout을 일관되게
  선택합니다. 전체 한도의 constrained solver 지연 증거를 보존하고 threshold/
  fallback/표본 삭제 없이 engine별 guide 좌표와 실제 장식 경고를 유지합니다.
- Explicit tight-layout diagnostics now measure real visible axis labels and
  narrowly check eligible tick groups against automatic decorations. Tick
  union-box broadphase avoids tick-vs-tick all-pairs work. The retained R2
  publication title/tick collision warns without moving source geometry; the
  example explicitly positions its reserved-panel title inside that frame.
- 명시 tight 배치는 실제 보이는 축 label 및 기존 eligibility의 tick group과
  자동 장식 충돌을 측정합니다. Union bbox로 후보를 좁히고 tick끼리 전수 비교하지
  않습니다. R2 실제 제목/tick 충돌은 geometry를 바꾸지 않고 경고하며 예제는 공개
  title_position으로 빈 frame 안의 제목 위치를 명시합니다.
- New statistical/spectral sharing-role checks require explicit N13 geometry
  or stored panel identities. Ordinary legacy shared raw/count scenes retain
  native behavior; original category/clock/domain/sharing validation stays global.
- 새 통계/스펙트럼 공유 차원 검사는 명시 N13 geometry 또는 저장 패널 ID가 있을
  때만 적용합니다. 기존 raw/count 공유 장면과 원래 범주/시간/domain/공유 검증은
  유지하며 N13 opt-in 안의 차원 검증을 완화하지 않습니다.
- N12 adds finite typed major/minor locators/formatters, native scale
  parameters and named derived top-x/right-y unit conversions, without
  repurposing independent y2. Shared conflicts, actual primitive domains,
  every derived-view refresh and dedicated active-tick bounds reject misleading
  requests. Canonical opt-in clocks retain accepted distant-epoch microseconds;
  new logit constant views contain data. Existing schema/package/floors/default
  paths remain unchanged; isolated qualification is not integration/all-v2 closure.
- N12에 유한 typed major/minor 눈금·native scale parameter·이름 기반 보조
  x/y 단위 view를 추가하며 독립 y2를 유지합니다. 공유 충돌·실제 도형 domain·
  view 갱신·전용 active tick 상한·canonical 시간 정밀도·상수 logit 자료
  포함을 확인합니다. 기존 버전/하한은 유지하고 isolated 검증과 통합을 구분합니다.
- Canonical concise format selection adapts Matplotlib3.8 policy; full license,
  attribution and changes are bundled. Distribution expression is
  `MIT AND LicenseRef-Matplotlib`; the project's own LICENSE remains MIT.
- Actual Python browser qualification exposed stale visible preview reuse despite
  no-store responses. Preview images now use the existing view generation in
  their URL; stale generation reads reject without mixing current PNGs with old
  native handles. Bare PNG downloads remain unchanged. Disabled-data reasons
  from canonical per-panel metadata are escaped and visibly rendered.
- Python 실제 화면의 오래된 preview 재사용을 기존 view generation URL과
  stale 요청 거부로 고쳤습니다. PNG·native handle 세대를 맞추며 기존 bare
  다운로드는 유지합니다. 비활성 data drag 이유는 공통 metadata를 escape해 표시합니다.

- C03 adds typed column-reference `bxp` mode on the existing box layer, raw
  seeded median bootstrap CI, final-body-fraction caps and exact raw-key per-hue
  components. Shared box hue/body-stroke/flier-style roles support applicable
  date/log/v-h/y2/facet/live paths without rewriting source rows or units.
  New advanced work bounds are 256 drawn samplecells, 10000 selected rows and,
  independently, 10000 declared flier values; legacy no-new-request limits stay.
- C03은 기존 box layer에 typed column 참조 `bxp`·원자료 seeded 중앙값 CI·최종
  body 폭 비율 cap·정확한 raw key의 hue별 component를 추가합니다. 공유 box
  hue/body-stroke/flier-style과 적용 가능한 date/log/v-h/y2/facet/live는 원본 행/
  단위를 보존합니다. 새 advanced 상한은 samplecell256·선택행10000·별도 flier
  값10000이며 기존 무요청 경로의 상한은 그대로입니다.
- Shared selector statistics and bootstrap percentile endpoints retain tiny
  selected observations; safe midpoint/binary interpolation avoids needless
  overflow/underflow without replacing mean/sum arithmetic. Native zero-width
  dashed box components retain independent markers/fill on Matplotlib3.8.
  Raw absent controls inherit actual native rc settings; orthogonal cap edits
  do not enable unrelated bodies/means/fliers. Explicit category inference in
  live one-column distributions follows the category source, not the value x.
- 공유 선택 통계/percentile endpoint는 작은 선택 관측값을 보존하고 mean/sum
  변경 없이 불필요한 overflow/underflow를 피합니다. 3.8의 width0 dash도 실제
  marker/fill을 유지합니다. Raw 생략 제어는 실제 native rc를 따르고 cap 편집은
  무관한 body/mean/flier를 켜지 않습니다. 한 열 live 분포의 명시 범주 재추론은
  값 x가 아닌 실제 category source를 따릅니다.

- C02 adds native filled marker/style choices, independent shared hue/size/style,
  explicit date/log/v-h/y2 and compatible cross-layer packing. Original rows and
  exact legacy circles remain; one draw-pass coordinator counts duplicate drawn
  instances separately. Existing2000/layer stays; the profiled new named-scope
  operation bound is4000 physical instances, not an SLA or data downsampling.
- C02에 실제 native marker/style·공유 hue/size/style·날짜/log/v-h/y2·명시 호환
  cross-layer packing을 추가합니다. 원본 행·기존 원을 보존하고 pass마다 한 번
  중복 물리 instance도 따로 셉니다. 2000/layer 유지, 새 scope4000 연산 상한은
  SLA나 downsampling/제한 완화가 아닙니다.
- A reusable G01 increment adds opt-in SetLiveFacets/FacetTemplateSpec and explicit
  SetFacetTemplate transactions. Saved local views remain authoritative on load;
  whole-template edits deliberately supersede local overrides while preserving
  fixed selectors, same-channel slots and compatible ratios/sharing. This is the
  new C02 live-grid unit, not the old SetData/materialization subset or G01 closure.
- 재사용 G01 증분은 선택 SetLiveFacets/FacetTemplateSpec·명시 SetFacetTemplate를
  제공합니다. 로드한 로컬 view는 그대로이고 전체 편집은 로컬 override를 의도적으로
  대체하되 고정 selector·같은 채널 slot·호환 ratio/sharing을 보존합니다. 기존
  SetData/materialization이 아닌 새 C02 live 단위이며 G01 전체 종결은 아닙니다.
- N11 adds required-Hz typed spectrogram, Welch PSD/CSD/coherence and whole
  magnitude/wrapped angle/unwrapped phase. Named FFT/window/detrend/sides/
  scaling, correct padded Nyquist factors, derived units and undefined gaps
  preserve raw samples/order. Dedicated algorithm caps precede allocation.
  Native artists/pure core/JSON/actions/CLI/generic Rust share the contract.
  Isolated qualification awaits integration; no all-v2/version/floor claim.
- N11에 필수 Hz 표본율·typed spectrogram/PSD/CSD/coherence/magnitude/angle/
  phase를 추가합니다. 원본 표본·순서·미정의 gap·단위·전용 할당 상한을 유지하며
  통합 전 isolated 검증이지 전체 v2 완료나 버전/의존성 상향이 아닙니다.
- N11 source review corrected coherence's unit-dependent fourth-order numeric
  underflow/overflow with coherence-only positive channel scaling before FFT.
  Shared colour/text/reference validation now rejects malformed/unused metadata,
  and spectral legends honour existing SVG links and PGF citation/href macros.
- N11 검토에서 coherence의 단위 의존 곱 underflow/overflow를 effect 내부 양수
  채널 scaling으로 보정했습니다. 공통 metadata 검증과 SVG/PGF reference를
  재사용하며 원본/CSD 물리 단위는 유지합니다.
- The same coherence numeric boundary also normalizes each frequency's private
  segment-coefficient vector before products, preserving nonzero weak bins
  beside strong frequencies. Physical CSD remains unscaled. Zero-width dashed
  spectra use native no-line geometry with unchanged artist data on Matplotlib
  3.8 as well as current versions.
- 같은 coherence 수치 경계에서 주파수별 private segment 계수도 곱 전에
  정규화하여 강한 주파수 옆의 약한 nonzero bin을 보존합니다. 물리 CSD는
  바꾸지 않고 width 0 dash는 3.8/current 모두 데이터 보존 no-line으로 표시합니다.
- Coherence channel scaling uses only the actually consumed full-window prefix,
  never unused trailing samples; detectable nonzero loss from extreme consumed
  dynamic range raises a precision error before FFT rather than false zero bins.
- Coherence scaling은 실제 소비한 full-window prefix만 쓰며 trailing 표본은
  원본에 유지합니다. 극단 범위의 nonzero 소실은 FFT 전 정밀도 오류로 보고합니다.

- C01 opt-in categorical strips now support selected/reserved category × hue
  slots, native numeric/log/date spacing, v/h and named local uniform/none
  jitter. Keep legacy raw-x defaults/JSON and raw measurements unchanged.
  Real Rust/browser history/reopen and installed minimum API/CLI bounded
  acceptance are recorded; final frozen-product qualification remains separate.
- C01 명시 범주 strip에 빈 category×hue 슬롯 예약·native 숫자/log/날짜 간격·
  v/h·이름 있는 local uniform/none jitter를 추가합니다. 이전 raw-x 기본값·JSON과
  관측값은 보존합니다. 실제 Rust/browser history·재개방·설치 최소 환경 API/CLI의
  제한 기능 인수를 기록하며 최종 고정 제품 자격 검증은 별도입니다.
- CND01's real Python/Rust comparison triggered active-panel x/y/y2/z controls and native title/legend/text/annotation handles in Rust. Shared installed preview metadata uses actual PNG pixels, preserving clocks, source data, history, and existing generic forms. Schema 0.1 and package 1.1.0 remain unchanged.
- CND01 실제 비교에 따라 Rust 활성 패널 x/y/y2/z 제어와 native 제목·범례·text/annotate 이동을 추가합니다. 설치 가능한 공통 preview metadata는 실제 PNG 픽셀을 사용하고 시간 설정·원자료·history·기존 generic form을 유지합니다. Schema 0.1·package 1.1.0은 바꾸지 않습니다.
- M01 custom same-shaped heatmap annotation strings (up to 512 characters/cell)
  and finite x/y tick rotations now round-trip separately from scalar colour
  values. Masked cells suppress text; clustermap reorders text, masks and labels
  together by original cell identity. Wider norms/colourbar/layout remain required.
- M01에 숫자와 독립적인 같은 모양 사용자 주석(셀마다 최대 512자)·유한 x/y tick
  각도를 추가합니다. Mask는 주석을 숨기며 clustermap은 원래 cell ID에 맞춰
  text/mask/label을 함께 재배열합니다. 추가 norm/colourbar/layout은 계속 필수입니다.
- CND02 narrows redundant default-Store history replay: retain one prior
  internal transition for immediate undo and reduce only the next redo action.
  Existing deeper64-action checkpoint/custom-reducer replay and defensive public
  copies remain; no dispatch copy or resource-limit change. Retaining one extra
  old graph is an explicit memory tradeoff, not a universal speed/atomicity claim.
- CND02 기본 Store의 중복 재생을 줄여 직전 내부 상태 하나로 즉시 undo하고 다음
  redo action만 계산합니다. 깊은64-action checkpoint/custom 재생·공개 방어적 복사는
  유지하며 dispatch 복사·자원 상한 변경은 없습니다. 이전 graph 하나 추가 보관은
  명시적 메모리 tradeoff이며 보편 속도/실패 원자성 보장이 아닙니다.
- F01's scatter/lineplot increment adds explicit numeric-hue colourbars and
  scatter outlines in points. Exact raw ticks share mark normalization, including
  signed extremes and constant swatches; one logical-panel/shared guide respects
  primary/y2 and later requests without deleting dataset/size/style guides.
  Wider applicable families and complete F01 qualification remain required.
- F01 scatter/lineplot 증분에 숫자 hue colourbar·point 윤곽을 추가합니다. 정확한
  raw tick은 signed extreme·상수를 포함해 mark 정규화를 공유하며 논리 panel/
  shared guide 하나로 primary/y2·후순위 요청을 처리합니다. Dataset/size/style은
  보존하며 넓은 적용 계열·F01 전체 검증은 계속 필수입니다.
- F01 now connects independent strip/weighted-ECDF roles to the shared raw-row
  pools. Point diameters and curve strokes retain distinct physical units;
  ECDF markers show right-continuous observed knots, never boundary sentinels.
  Preserve all remaining family/inference scope as unfinished.
- Preserve legacy positional LayerSpec alpha binding by appending optional strip
  after existing fields. Actual archived-baseline/current artist opacity was
  compared; the earlier C01 frozen receipt remains historical, not overwritten.
- F01 strip/가중 ECDF를 공유 raw-row pool에 연결하며 지름/곡선 stroke의 point
  단위를 구분합니다. ECDF marker는 경계 sentinel이 아닌 실제 우연속 knot입니다.
  새 strip 필드는 뒤에 추가해 이전 positional alpha를 보존하고 실제 baseline/
  current artist를 비교했습니다. 다른 필수 계열·추론 범위는 여전히 미완료입니다.
- D07 adds vertical/horizontal/secondary-y rugs, finite axes-fraction heights,
  independent raw-row hue/stroke-point/dash mappings and shared guides. Native
  blended segments retain duplicates/order and zero height/stroke without changing
  perpendicular density/value limits or parsing height as calendar data.
  The existing width field and omitted 0.04 defaults remain; no schema/version
  change, weights, inference or point-marker reinterpretation.
- D07에 수직/수평/y2 rug·유한 axes-fraction 높이·독립 raw-row hue/point-stroke/
  dash 매핑·공유 guide를 추가합니다. 중복/순서와 높이·stroke 0을 보존하고 독립
  밀도/값축 범위를 오염시키거나 높이를 날짜로 해석하지 않습니다. 기존 width/
  생략 기본값 0.04 유지, schema/version 변경·가중치·추론·point 재해석은 없습니다.

## [1.1.0] - local candidate (not published)

### Fixed

- Correct subnormal and mixed integer/float recommendation medians and Tukey
  fences using exact interpolation, without changing inputs or scalar types.
  Include configured secondary-axis descriptions in visual QA.
- Stage PGF text and raster sidecars before publication; back up existing files
  and roll back failed publication without changing successful asset names.
  Keep temporary writes private, retain recovery backups if restoration fails,
  exclude private export files from distributions, and surface recovery notes in
  the CLI. Report the actual Matplotlib-resolved path for extensionless output.
- Include all eight linked scientific-quality PNGs in source distributions;
  the generated-image ignore rule previously omitted this subdirectory.
  Add an offline installed-wheel render/CLI smoke (`check_wheel.py --render`),
  required by CI/release, while retaining the dependency-free core smoke.
- Require finite numeric measurements and complete identifiers for paired
  recommendations; reject misaligned role columns and withhold advice without
  usable coordinate/measurement rows. Detect fractional UTC offsets discarded
  by the datetime parser without inventing repeated timestamps.
- Respect journal font minima in visual lint. Ignore transparent collection
  members, RGBA strokes/text and fully masked images; combine image opacity
  sources while retaining hatch-only patches and alternate marker faces.
- Preserve integer precision in scientific chart advice: extrema, integral
  medians, Tukey fences, numeric time ordering and native event offsets no longer
  round through float first. Add coordinate-precision warnings without changing
  measurements/units, reject implicit nonnumeric time coercion, and handle missing
  ISO time values without a crash. Decline unsupported sub-microsecond ISO string
  precision instead of falsely reporting repeats. Cover these cases in the
  minimum runner.
- Update the audit script's transitive certifi lock to2026.10.19 for
  GHSA-6q48-6c7w-9gw2. That isolated patch left application/minimum locks unchanged;
  the later Pillow/security-floor changes are recorded separately below.
- Repack native swarm artist size/linewidth arrays using pairwise radii and
  individual gutters, preserving scalar geometry, rows, transforms and crowding
  warnings. Reject invalid arrays before changing offsets; no new public size
  semantic mapping is implied.

### Security

- End Python 3.10 support for v1.1 as an owner-approved security exception;
  require Python >=3.11 and NumPy >=1.23.5, and explicitly constrain rendering to
  Pillow >=13.0.0. The previous Pillow 12.3.0 lock failed the dependency audit,
  while the patched line requires Python 3.11. Keep the Python API, FigureSpec/
  JSON, measurements and Matplotlib defaults unchanged.
- Refresh all affected locks, including auditor-only filelock/msgpack patches,
  without audit waivers. Requalify the new locks instead of reusing older passes.

### Added

- Added opt-in `smart` / `smart-print` render/save policies for measured
  legend/data collision repair, shared legends and safe direct two-method labels.
  Added deterministic `recommend()` chart advice and actual-size visual lint with
  JSON repair suggestions and CLI access. Preserve default rendering, raw data,
  FigureSpec/JSON and the existing Matplotlib renderer; no new dependency.
  Four synthetic 300-DPI before/after cases document both automatic layout and
  explicit author decisions: see `docs/SCIENTIFIC_QUALITY.md`.
- Added Swarm facet/filter selection with pooled size domains and frame-only
  reserved empty cells, including fully empty semantic grids and stable SetData
  filters. Keep plain empty layers invalid and all option/column/geometry guards;
  empty first layers no longer consume later populated size guides.
- Added Swarm-only named size domains across unfiltered layers, with pooled
  original-row numeric/categorical scales, per-panel guide deduplication and pure
  pooled limits. Keep observations/legacy colours local and reject mixed-family
  domains and facet/empty-cell combinations rather than silently renormalizing.
- Added categorical swarm size ranks with typed level keys, explicit row selection,
  reserved ordered size slots and observed-only guides. Reuse the unchanged pure
  scatter/line rank helper while preserving numeric scales and calibrated packing.
- Added opt-in numeric size-only swarm semantics with one selected row cohort,
  stable layer-local diameter mapping and matching non-data guides. Preserve
  legacy group colours, source/JSON/actions and calibrated joint packing; reject
  unsupported facet/shared/style/date mappings and ambiguous scalar overrides.
- Added bounded single-band numeric interval plots with explicit start/duration,
  raw bottom/height, overlap/source preservation and linear primary-y2 routing.
  Reject nonpositive, overflowed or float-collapsed geometry before artists, with
  executable gallery/spec and full native HTTP/browser coverage.
- Added bounded single-train numeric event plots with raw-coordinate offset/length,
  preserved duplicate events and linear primary-y2 routing, executable gallery and
  full native smoke coverage. Handle zero-width dashed legends on Matplotlib3.8
  without epsilon widths, dropped labels or changes to positive-width dashes.
- Added pre-binned vertical stairs from supplied heights and explicit N+1 edges,
  raw baseline/linear primary-y2 routing and strict unsupported-option rejection,
  with executable gallery and native JSON/PNG undo/redo coverage.
- Replaced a brittle native capability kind-count assertion with exact source
  metadata preservation checks and native HTTP stem/weighted-regression JSON,
  PNG and undo/redo integration coverage, without changing runtime behavior.
- Added bounded vertical numeric stem plots with raw baseline/order/duplicates,
  primary/y2 and positive log geometry, executable gallery/spec/vector examples
  and strict unsupported-option rejection. Include gallery Markdown in the cheap
  generated-artifact drift checker, fixing the omitted regression weights listing.
- Added opt-in relative weighted poly/log-x point fits and raw residuals through
  the existing weights column; reject weighted confidence/advanced models and
  nonrepresentable weight scaling while preserving legacy unweighted behavior.
- Added opt-in unweighted ECDF joint marginals and pair diagonals with explicit
  count/probability/percent, exact selected cohorts/tie jumps and independent
  statistic axes. Unused bins/KDE options and density are rejected.
- Added opt-in ungrouped hist2d/hexbin joint centers with paired histogram/KDE
  marginals, source-row preservation and dynamic complete cases. Colorbars and
  unsupported group/weight mappings remain explicit rejections.
- Verified exact existing v1.0.0 release checksums and OIDC certificate identity
  separately from current runtime quality, and added scoped supply-chain/audit
  failure-policy guards. The operator subsequently expanded the target to v1.1.
- Paired fixed-environment visual evidence with independent group/coordinate
  assertions and reviewed diff artifacts; no blind baseline regeneration or
  blanket cross-environment image tolerance was introduced.
- Added a bounded exhaustive state machine with an independent oracle, reviewed
  deletion-minimal replay fixtures and isolated selected mutation evidence for
  axis/group/duplicate-key/atomicity/redo contracts, without runtime/dependency changes.
- Documented measured API/Python/Rust editor costs, explicit aggregation and large
  workload limits without streaming/SLA or silent history-cut claims. Kept the
  full-suite CI contract test robust to folded YAML/JUnit command formatting.
- Made required CI browser/PGF/TeX paths fail on missing/skipped/ambiguous JUnit
  cases while preserving local optional skips. Retain matrix/source-specific
  reports and cache namespaces; bound UTF-8 JUnit input without DTD/entities.
- Aligned paired READMEs with finite pattern/resource/checkpoint scopes and
  executable caller-owned Figure cleanup. Added an interim API/evidence review
  that explicitly withholds release approval and final-review sign-off.
- Shortened default Store near-tail undo/redo using one preceding64-action state,
  retaining all history/listeners/snapshot and custom-reducer semantics. Measured
  memory tradeoff; added gesture-boundary and opt-in provenance manifest examples.
- Bound total figure layers to1024 across panels, before raw layer decode, new
  AddLayer copy or facet/joint replication, preserving accepted boundaries and
  input snapshots without trimming layers or relying on palette candidate limits.
- Bound owned render/save canvas work to40millionpixels before native allocation,
  including backend/output DPI and padded tight bounds, without rewriting source
  DPI or capped previews. Oversized effects fail explicitly and preserve old output.
- Bound figure expansion to256panels/layout cells before bulk construction or
  native geometry, retaining positive-index automatic growth inside the limit
  and explicit errors without truncating input figures.
- Bound legacy bivariate histogram bins per axis and hexbin gridsize to512 before
  native quadratic allocation, with explicit validation/capability metadata and no
  clamping of accepted values. Broader structural/export resource review remains open.
- Verified shared htmx/license ownership and native browser asset hashes, plus
  controlled compatible-label/incompatible-spec/capability startup boundaries.
  Clarified matching-checkout policy without adding a runtime version handshake.
- Added alert/current-page semantics to Python editor errors/navigation and
  verified a keyboard-only panel/form/error-recovery/handle/navigation journey.
  Existing labels, focus outlines and action/state behavior remain unchanged.
- Added public class/field context to decode errors while preserving exception
  kinds, causes, union acceptance and input values. Verified CLI/UI/native Rust
  response shapes and failure recovery without introducing a new RPC interface.
- Verified valid/broken/valid file opening, draft/history/preview preservation and
  vector-export failure recovery through real browser controls, with unchanged
  source files and a final state-matching JSON download. No new export format.
- Verified high-DPI preview dragging and keyboard/undo/redo in actual Chromium
  contexts with emulated DPR, CSS enlargement and visual-viewport scaling, while
  preserving editable DPI, panel state and original coordinate meanings.
- Verified one local editor session across two pages and a raw-action client:
  arrivals/serial commits, disjoint-field preservation and final preview match.
  Documented shared panel state and refresh behavior, not live collaboration.
- Fixed late Python editor HTML fragments replacing newer inspector state after
  out-of-order delivery. Added local UI reply generations without dropping actions
  or changing spec/JSON/history contracts; tested actual DOM and preview pixels.
- Fixed Python editor text/annotation handles using primary y coordinates for
  secondary-axis layers. Preserve actual y2 limits/scale through preview metadata
  and data dragging, retaining primary/title/legend frames and undo/redo.
- Fixed ignored annotation alpha for both text and arrows, including secondary
  axes and fully transparent output. Preserved default RGBA colour opacity and
  native z-order/clip behavior; added pixel/SVG regressions and overlay comparisons.
- Revalidated shared axis scopes and log domains, including named conflicts,
  independent secondary axes, native legacy clipping and typed LogNorm masks.
  Documented the observed Matplotlib3.8 large-constant warning separately from
  pixel correctness and warnings-as-errors output preservation.
- Revalidated role-aware listwise statistical rows across weighted summaries,
  distributions and semantic line mappings, with exact original row/weight/unit
  traces and explicit invalid-input rejection rather than silent column drops.
- Revalidated box/violin quartiles, whiskers, profiles and degenerate cells against
  manual expectations, plus fixed-seed jitter positions, matched-environment
  cross-process exports and unchanged global RNG state. No new random API.
- Revalidated Gaussian KDE bandwidth, PDF/CDF and finite-support integration
  against exact weighted moments and independent mixtures, retaining singular
  skip, clipped-tail and relative-weight contracts without a new fallback.
- Revalidated supported weighted histogram boundaries, unequal-bin density areas
  and cumulative mass against independent high-precision Decimal expectations,
  reusing existing geometry/export regressions without changing normalization.
- Fixed polynomial covariance underflow/overflow that could silently collapse or
  omit legacy confidence bands. Normalize predictor/response units in the shared
  helper and reject rank/arithmetic/nonfinite failures with causes, retaining the
  existing normal-approximation mean-fit definition and public configuration.
- Verified quiver data-space tips, asymmetric 3D/polar coordinates and continuous
  scalar guide/mask/domain behavior, preserving typed heatmap null rejection and
  numeric hue legend mapping rather than inventing new supported controls.
- Documented synthetic fixture/evidence separation and current contract-conflict
  decisions with hashed input inventory and scoped masking review, without
  presenting targeted scans as a complete secret/privacy certificate.
- Added isolated intentional-drift regressions for schema, capabilities and
  generated reference artifacts, including restored-copy success and actionable
  regeneration hints. Cross-checked registered action fields and layer vocabulary
  without tightening the structural layer-type schema contract.
- Verified Windows read-only/deny-delete output failures, synthetic ENOSPC and
  unsupported extensions without losing prior bytes, plus open-Figure ownership
  and bounded caller-close/GC/handle traces. Kept long-session/native limits explicit.
- Verified finite hatch/marker/dash and legend mapping, linear-luminance proxy
  greyscale and fixed one-column colour/grey comparisons. Removed unlimited
  colour-count/readability claims from bilingual/generated docs and gallery
  captions, retaining visible transparency/small-size limitations.
- Corrected palette quality reports to measure final8-bit HEX output and actual
  mapped-float lightness rather than nominal LCH. Added explicit CVD/model/severity/
  representation conditions, preserving generated colours and existing thresholds;
  beyond-verified-count results are measurements, not accessibility certification.
- Preserved adaptive layout margins in physical inches across DPI instead of a
  fixed pixel count, retaining default300DPI spacing. Verified complete caller-rc
  restoration and independent equivalent-environment style output; recorded the
  remaining low-DPI dense-layout residual rather than promising exact all-DPI WYSIWYG.
- Measured outside-right legend spacing beside secondary-axis decorations instead
  of a fixed axes multiplier, and coalesced repeated explicit ungrouped point/line
  guides only when source/axis/reference identity matches. Raw grouped identities
  and manual anchors remain distinct; real PNG/PDF/SVG mixed-guide bounds are checked.
- Verified installed/missing font families, Hangul/minus/math glyph coverage and
  narrow CJK/group layout with actual font-file fingerprints and diagnostics.
  Kept requested text/fonts unchanged and avoided bundled fonts, downloads or
  cross-system byte/typography guarantees.
- Added fixed-canvas diagnostics for automatic title/suptitle/outside-legend
  overflow or overlap, including unbroken text that previously clipped silently.
  Impossible legend margins no longer create negative solver rectangles. Manual
  positions, physical size and warning-as-error output rollback remain explicit.
- Verified all five TeX presets at one/two columns and two fractions against real
  PNG/PDF/SVG boxes and both previews. Clarified existing journal rc-style versus
  last size-action priority, including clearing journal style for explicit font
  fields, without changing calibration or introducing override metadata.
- Restored an explicit platform guard inside the cached Windows memory binding
  factory after Linux Pyright exposed unavailable ctypes.WinDLL attributes.
  Added a non-Windows rejection regression and checked both platform targets,
  retaining fresh samples/closed handles without ignores or dependency changes.
- Verified decode-once HTML/SVG special-character boundaries and actual raw-editor
  responses; documented explicit trusted PGF TeX escaping rather than claiming a
  universal plain-text sanitizer. Literal escaped PGF text/math compiles and unsafe
  reference macros remain rejected; no runtime coercion was added.
- Verified reference-bearing PNG/PDF/SVG deterministic metadata/IDs, four installed
  TeX/bibliography combinations with embedded fonts and actual DOI annotations,
  and PGF sidecar relocation/missing/postprocess failure limits without promising
  multi-file atomicity or cross-environment hashes.
- Reused Windows memory-observer Counter/DLL bindings so repeated samples do not
  accumulate ctypes pointer types. PID values are still queried afresh and handles
  closed; bounded editor resource traces remain separate from long-session proof.
- Serialized owned Matplotlib effects with a shared reentrant stdlib lock after
  concurrent PNG/SVG exports differed from serial output. API/preview/editor and
  gallery effects retain deterministic bytes without claiming arbitrary Figure/
  pyplot thread safety or parallel throughput; dependency-free core stays lazy.
- Added a bounded rows×history core profile with per-worker RSS/peak observations,
  explicit partial targets and null unmeasured undo/redo timings. Timeout/error/
  truncated-output tests preserve checkpoints without inventing zero-cost results.
- Preserved explicit empty marker/line-style tokens rather than treating them as
  automatic defaults. Added representative schema/CLI/Rust/raw-editor agreement
  cases while retaining omission/null/numeric-zero and layer-specific restrictions.
- Added a bounded, reproducible warm state/JSON/render cost profile with synthetic
  1k/10k/100k rows, median/p95 and separate Python allocation/cProfile evidence.
  Kept snapshot safety and avoided unmeasured zero-copy or streaming promises.
- Fixed bridge timeout/wait cleanup leaving an owned foreground descendant alive:
  target the held Windows child tree or a fresh Unix child process group, bound
  the cleanup command and keep cleanup failure in the returned diagnostic.
  Controlled foreground tests and current MSRV checks passed on Linux/Windows;
  detached workers and hard OS resource guarantees remain outside support.
- Verified default editor error logs with synthetic privacy probes and current
  Python-lock/registry-crate advisory snapshots; documented same-client draft
  responses and audit limitations without claiming security certification.
- Split the complete minimum-dependency contract into its own finite-budget CI
  job after full Pytest plus floor checks exhausted a shared hour. Retained ordered
  floor files, pinned TeX and matching system/font prerequisites; both paths report
  slow tests. Full Python/browser and Rust coverage are unchanged.
- Reserved atomic JSON/PNG/PDF/SVG staging entries exclusively before writing or
  cleanup, preventing a name collision from deleting/overwriting another file.
  Added file/directory/hardlink/symlink collision and fixed HTTP path-policy probes.
- Verified offline reference/data handling with blocked network/shell/pickle sinks
  for ordinary PNG/PDF/SVG, while documenting explicit trusted TeX/PGF boundaries.
- Documented the measured Windows venv/TMP startup boundary independently of
  mudplot and capture mode, with a same-interpreter short-TMP bridge control.
  Long absolute data paths remain distinct from unsupported launcher cwd/TMP
  configurations; no OS settings or interpreter fallback were changed.
- Verified locked-dev, allowed fresh-install and PEP517-isolated build scopes
  separately, and clarified that engine wheels exclude source-tree editors.
  Matching-checkout editor startup/assets and an isolated core consumer passed;
  observed equal wheel bytes are not a universal dependency-reproducibility promise.
- Added actionable colour/render-extra hints at missing optional effect boundaries,
  including CLI render and palette adapters, while retaining unrelated transitive
  diagnostics and causes. Installed-wheel progressive7-stage/98CLI checks cover
  core, colour, rendering, advanced extras, dev and browser-package boundaries.
- Preserved explicit marker size0 instead of replacing it with default6/4 in raw
  scatter/regression/strip/errorbar/3D paths, and forwarded marker size for3Dlines.
  Omitted/null defaults remain unchanged. Added139nullable-field structural checks
  plus CLI/native damage recovery and normal20k-row input probes.
- Kept full CI coverage but raised the finite Python matrix budget45→60minutes
  after an observed timeout; report25slowest tests instead of silently dropping tests.
- Rejected bool/noninteger layer indices consistently in RemoveLayer, SetColorbar
  and SetLayerAt instead of silently editing another layer or leaking TypeError.
  Retained valid panel auto-extension and explicit validation semantics; added
  cross-process core hashes, effect/import guards and reference-boundary regressions.
- Rejected empty native bridge render artifacts even after a successful child exit,
  preventing empty previews from committing. Added controlled empty/malformed JSON,
  exit/stderr, missing optional dependency and empty PNG/PDF/SVG probes that retain
  state/cache/redo, plus short timeout recovery coverage without claiming process-tree containment.
- Bounded failed Python-bridge stderr to64KiB raw with an explicit truncation
  marker, preserving complete successful stdout and stream separation. Added
  nonzero-output and all-operation state/cache failure regression checks.
- Verified native preview pixels immediately below/at/above2000 in both
  orientations while preserving JSON DPI/size and physical PDF/SVG exports.
  Timeout descendants and the full malformed-output matrix are not implied complete.
- Fixed raw mixed string/numeric group IDs being merged by NumPy string inference,
  with group identity changing merely when null was added. Masks now use original
  object values while preserving legacy numeric equality and ordered typed semantics.
- Added empty/singleton/row-order and structural JSON policy checks, including an
  additive-capability consumer regression; canonical serialization does not collapse
  data list order or numeric types. Broader null/default/depth-path completion remains scoped.
- Added independently sourced full34-pair CIEDE2000 references, adopted D65/IEC
  calibration checks, OLS mean-CI math, categorical/y2 artist ownership and
  asymmetric matrix-coordinate tests without changing numeric defaults.
- Verified fresh-process/time-spaced output hashes and real dimensions, installed
  engine-only wheel behavior outside the repository and disjoint minimum-version
  coverage. Recorded incomplete attempts separately; no release/version/tag or
  universal-parity approval is implied by these supported-scope P0 checks.
- Prevented overlapping Rust control swaps from using detached app targets by
  disabling the current controls during htmx requests; kept official vendor bytes,
  access rules and history policy unchanged. Added real reset/undo/redo browser checks.
- Verified open/reset/download ownership, no-op events/redo invalidation and seeded
  long replay without adding dirty-bit/save-target, coalescing or checkpoint features.
  Recorded successful Linux/Windows Rust CI jobs separately from a cancelled full
  workflow rather than claiming universal/release completion.
- Restricted missing-scalar normalization to recognized NumPy/pandas cases so
  Decimal NaNs and custom non-reflexive objects do not silently become null.
  Bounded item conversion to supported representations, preventing longdouble
  and unsupported object-chain recursion without lossy float/string coercion.
- Loaded disposable interpreter-probe provenance through an exclusive .pth/module
  pair rather than assuming sitecustomize lookup reaches a venv-local file.
  Added a foreign-customizer preservation self-check; exact Linux CI cause and
  remote rerun success remain unconfirmed rather than inferred from local passes.
- Preserved NumPy datetime64 fine-unit ISO values/NaT through scalar, column,
  structured and row paths instead of silently storing epoch integers. Preserved
  Polars nanoseconds/offsets with native formatting and a lossless round-trip check;
  retained coarse/numeric formats and explicit unsupported date-axis handling.
- Aligned Rust smoke CI with its advanced regression/clustering fixtures by
  installing the optional all extra in the test job, not making effects mandatory
  at runtime. Reproduced the published Linux render-only smoke failure and added
  a regression guard; remote rerun success is not inferred from local passes.
- Rejected unsupported Transfer-Encoding, duplicate Content-Length and truncated
  bodies before Python editor mutations. Content-Length bodies retain the16MiB
  boundary; no chunked decoder or normal-bodyless-action regression was added.
- Applied Rust's existing limited Bytes extractor before every route, including
  bodyless undo/reset, so unknown-size requests cannot mutate state before their
  byte bound is checked. Added sequential real-size form/JSON/chunked probes and
  observed server-PID lifetime RSS peaks, explicitly excluding renderer children,
  hard memory/CPU bounds, concurrency and universal-platform security claims.
- Fixed connection+query ingestion leaving internally created DB cursors open
  on success/failure. Close is honored when supported; caller-owned executed
  cursors/connections and transaction commit/rollback remain untouched. Cleanup
  errors are not silently swallowed and minimal duck cursors remain supported.
- Verified real PyArrow26/Polars2 adapters in isolated tests, including chunks/
  dictionaries/categorical groups, exact signed64 integers, Unicode/nulls,
  microsecond UTC values and strict Decimal/infinity rejection. Added targeted
  CI coverage without adding runtime dependencies or changing package versions.
- Added structural codec coverage for all24spec model types/272modeled fields,
  alternate unions/nulls/Unicode/big integers and nested types, with direct
  Python→Rust→Python value/type/order comparison. The stress fixture is not a
  renderable feature-parity claim; registered example specs are checked apart.
- Added a disposable Unicode/spaced-path interpreter probe for PATH/env/flag
  precedence, real child argv/prefix/version and invalid-flag no-fallback behavior.
  Same-version render packages are installed only in the test venv. Added Windows/
  Linux CI configuration while retaining unobserved Linux verification as pending.
  No application behavior, mandatory dependency or version change was needed.
- Fixed Rust Host/Origin rejection responses bypassing shared CSP/no-store
  headers, preserving the existing access checks. Added early rejection of
  declared Content-Length above16MiB without removing streaming body limits.
- Added shared state/UI/agent fixtures across fluent/Store/CLI/Python/Rust paths,
  actual validation/JSON/render failures preserving preview and redo, loopback
  Host/Origin matrices, IPv6 HTTP checks and real-browser CSP observations.
  Payload/chunked/RSS completion and the observed Windows transport abort are
  explicitly not claimed resolved by the header-only rejection probes.
- Fixed missing categorical/date-string x coordinates becoming a literal `None`
  category in raw plots. Shared conversion now preserves line gaps and scatter
  masks while retaining actual `"None"` labels, row alignment and source JSON.
- Added nested reducer/snapshot isolation, undo/redo boundary and branch checks,
  including real Rust HTTP spec/PNG comparisons. Documented existing Python
  fresh-history versus Rust undoable open/reset policies without changing them.
  Added adapter/cohort comparisons; absent PyArrow/polars stay explicit skips.
- Rejected malformed mixed records and positional/DB row types before table
  conversion: text/bytes/dict rows no longer become character/key columns, and
  non-mapping records/key collisions identify their record index. Sparse-record
  null filling, first-seen column order and valid sqlite3.Row inputs stay intact.
  Completed DATA-02 length/required-column/duplicate checks, including editor
  state/history/preview/redo and CLI output preservation on invalid data.
- Fixed Rust strict-JSON reserved-key reinterpretation under arbitrary-precision
  serde numbers. Original decoded key tokens are now checked without converting
  large integers to float or rejecting ordinary string values. Added failing
  numeric/escaped/nested-key regressions and real HTTP state/preview checks.
- Aligned Rust omitted spec-version behavior with Python using the embedded
  current default; null, malformed and unknown versions still fail. Shared
  boundary fixtures use explicit valid versions for unrelated negative cases
  and distinct accepted states to prevent masked failures/stale-state passes.
- Fixed silent truncation of ragged positional rows and malformed DB result
  row widths. Adapters now reject mismatches before pivoting with row index,
  actual and expected widths; valid values/order and missing-value normalization
  remain unchanged. Added pre-fix failing fixtures and minimum-version checks.
- Expanded JSON finite/missing boundary and out-of-range-render failure tests,
  including PNG/PDF/SVG output preservation and editor recovery, without claiming
  arbitrary-precision plotting or full cross-language checklist closure.
- Fixed atomic-output cleanup on Windows read-only targets: staging files no
  longer inherit the read-only flag before a replacement that must fail. Original
  bytes/read-only attributes stay unchanged; POSIX mode preservation remains.
  Added real Win32 sharing-lock/read-only tests across JSON/PNG/PDF/SVG and failed
  directory/path recovery, without administrator privileges or target chmod.
- Fixed the Rust capability regression count after clustermap registration and
  asserted its required/configuration fields. Expanded strict JSON duplicate-key,
  signed integer boundary and Unicode checks across Python/CLI/Rust/HTTP paths.
- Integrated the operator's 2026-10-16 review checklist as an ID/evidence workflow,
  preserving its original unchecked source. Added a 150-ID tracker with explicit
  open/running/pass scope, local tree/environment fingerprints and contract-run
  receipts. Added failure regressions for functional versus imperative batches,
  post-commit listener errors, and JSON/PNG/PDF/SVG partial-write/fsync/replace
  preservation on Windows Unicode paths; no production contract change or full
  review/release approval is implied.
- Added clustermap/ClusterSpec with optional SciPy row/column linkage, checked
  supplied trees/optimal leaves, matched dendrogram/matrix/label/mask/colour-strip
  orders and sample z-score/min-max display. Original finite matrices stay intact;
  undefined distances/bad topology/counts/transforms/layout fail without invented
  fits. Nested GridSpec keeps auxiliary axes/title/colorbar in bounds and freezes
  clustered layouts for exact vector replay. New cluster extra requires SciPy>=1.10;
  mandatory core deps and versions/releases remain unchanged. Added registry/
  bilingual gallery/editor/schema/minimum tests and a synthetic profile example.
- Added opt-in RegressionSpec poly/log-x/Huber/binomial-logit/LOWESS and residplot
  alias for observed-minus-fitted responses, preserving original rows and group/
  facet selection. Typed fits condition numeric units and reject unsafe model/
  option/data combinations, singular/separated/nonconverged results and residual
  joint templates. Legacy regression=None retains its polynomial path. Added an
  explicit optional regression extra(statsmodels>=0.14.1), included by all/dev;
  mandatory core dependencies remain empty and versions/releases are unchanged.
  Normal-approximation poly/log-x CI remains opt-in; weights/bootstrap/advanced CI
  and extra residual trends are not claimed. Added independent numeric/Windows/
  core/editor/export tests and five synthetic single-question examples.
- Added opt-in HeatmapSpec mask, original-value annotations/labels, explicit/log/
  centered/robust colour ranges, square cells and point-width borders. Masked
  values leave source matrices intact and do not enter colour statistics/text;
  annotation contrast accounts for image alpha. Strict options, finite matrix/
  shape checks, bounded formats and annotation cap fail before effects. Typed
  colourbar boundaries avoid native large-value/subnormal failures. Legacy
  heatmap=None behavior, versions and required dependencies remain unchanged.
- Fixed Python editor native-form fallback to use POST rather than leaking fields
  into GET URLs. Same-origin referrer policy retains valid browser Origin while
  withholding external referrers; cross-origin/null-Origin mutation guards remain
  unchanged. History forms reuse the same helper and work without JavaScript.
- Added configured KDE joint marginals (`marginal_kind="kde"`) and pair diagonals
  (`diag_kind="kde"`) with strict KDESpec/dict bandwidth, grid, cut/clip, common
  normalization/grid and fill. Existing paired/univariate cohorts, axes, singular
  skip rules and histogram defaults are retained. Actions serialize nested spec
  configuration as plain JSON. Weighted/CDF KDE grids and nondefault histogram
  bins/stat combinations fail explicitly; no dependency/version/release change.
- Added `Plot.pair()` / `SetPairGrid` numeric scatter matrices with typed histogram
  diagonals, categorical group slots and dynamic pairwise/univariate missing-row
  views over retained source data. Added named `AxisSpec.share_id` /
  `SetAxisShare` / `share_axis()` primary Cartesian linking so diagonal density
  y is never mixed with measurement units. Conflicting names/scales/limits and
  figure-sharing mixes fail validation. Existing unnamed sharing remains unchanged.
  Supports 2..8 variables; corner/semantic/weighted/CDF/nested grids stay out of
  scope. Includes editable/vector synthetic example; no dependency/version/release.
- Added terminal `Plot.joint()` / `SetJointGrid` for raw scatter/regplot with paired
  histogram marginals. Three editable panels share value axes without mixing
  density/count units; all views dynamically select complete x/y/group cases via
  optional `PanelSpec.dropna`, keeping the full source table intact. Group slots,
  source styles/references, JSON/actions/schema and existing editor paths remain.
  Supports count/density/probability/percent and integer bins; wider joint kinds,
  semantic/c/weighted/nested grids and wider pair-grid options remain open. Added a synthetic
  desktop example and retained derived-bin/log validation. No dependency/version/
  release change or full upstream parity claim.
- Extended facets to grouped raw line/scatter/bar/errorbar/band/stripplot/regplot/
  rug. Explicit raw hue_order selects/reserves typed group identities before
  coordinates, errors and fitting; facets pool those slots across cells. Missing
  groups retain colour/style/hatch/dodge positions without fictional artists.
  Duplicate/nonmonotonic raw paths, coordinate gaps, supplied bar values and paired
  uncertainty are preserved; no mean/statistical conversion. Existing unordered
  defaults remain unchanged; legacy numeric c/colorbar faceting remains unsupported.
- Added terminal `Plot.facet()` / `SetFacets` for a completed single 2-D template:
  row/col grids, column wrapping, selected/reserved empty levels, shared axes and
  independently editable panel filters over unchanged source data. Inference,
  weights and normalization are cell-local; independent scatter/line mappings
  pool deduplicated original row IDs with stable domains. Added JSON/action/
  schema/validation/editor contracts and a synthetic response-by-site example.
  This facet family still rejects legacy c, matrices/3-D/y2 and unsafe
  histogram/KDE combinations; live mapping, consolidated guides, wider pair and
  wider joint kinds remain open. No dependency/version/release or full-parity claim.
- Integrated the reading examples into the built gallery with offline review/
  criteria pages and editable downloads. Added four complete-figure drafts to
  the Python editor: selection prefills Open without changing figure/history;
  explicit Open uses the existing validated import path. Invalid imports retain
  submitted JSON, and htmx page-body history caching is disabled. Figure builders
  are shared with the reviewed examples, loaded lazily; no engine/schema/default/
  dependency/version changes. Editable sample specs are replaced only after
  successful rendering/QA, preserving earlier specs on render failure.
- Reworked the rejected four-panel showcase into separate response and endpoint
  reading tasks, with direct labels and explicit 700px/320px web layouts. Kept raw
  data, estimates, confidence bounds and numeric ranges; added a real-browser
  review page, numerical endpoint lookup and display-pixel/text-overlap checks on
  actual saved PNGs. Review criteria cite ONS, PLOS/Rougier, VisJudgeBench and
  graphical-perception research; no independent human/model quality score is
  claimed. Desktop vector/editable exports, mobile specs and grey/CVD views are
  included. Core defaults, schema, dependencies and release state are unchanged.
- The initial visual prototype and Pandas demo styling remain as historical
  examples; the four-panel image is no longer presented as a readability success.
- Added opt-in histogram `element="step"` using unfilled native stairs for
  layer/stack, both orientations and raw/log observations. Weighted/statistical
  heights and edges are unchanged; stacks outline absolute tops and previous
  baselines. Empty hues reserve theme dashes/colors, exact alpha/width include
  zero, and edge_color overrides stroke color. Old specs default to bars;
  step+dodge, filled steps/poly and custom step dashes fail validation.
  Added 43 regression cases for native paths, JSON/actions/schema/editor,
  overflow guards, PNG/PDF/SVG reproducibility and RNG isolation; refreshed
  Rust HTTP/PNG smoke and editable comparison. No dependencies/version/release.
- Added opt-in histogram `multiple="layer"|"stack"|"dodge"`, retaining legacy
  calls and defaulting old typed specs to layer. Grouped stacking follows hue
  order; dodging splits raw bin widths, including reserved empty hues. Heights,
  normalization and cumulative statistics stay unchanged; dodged density uses
  original bin widths without an area correction. Nonfinite/lost positive stack
  increments and collapsed dodge slots fail before any bars. Added 48 regression
  cases covering weighted v/h/log geometry, empty slots, pure/JSON/actions/schema,
  Python editor and repeatable PNG/PDF/SVG; updated Rust HTTP/PNG smoke and the
  editable histogram comparison. No dependency/version/release or parity change.
- Added independent lineplot SemanticSpec/column roles: distinct raw hue/size/
  style tuples partition curve/predictor cells; numeric clipping changes display
  not identity. Main stroke widths in points, filled markers/optional1..4unique
  named dashes, shared line/scatter scale domains with separate geometry guides.
  Existing weighted/per-x unit pointwise inference/sorting/raw-log/bands/bars/
  missing bounds retained, no whole-curve CI. Pure core/JSON/schema/actions/
  Python/Rust editor/exports/RNG/legacy,48newtests and editable comparison.
  Limits10000rows/256raw curves/64levels/enough markers/dashes; scalar conflicts
  fail and zero strokes retain points/intervals. No dependencies/version/release/
  raw-line/date/y2/colourbar/automatic facets/upstream parity claim.
- Added optional SemanticSpec.scale_id named figure-shared scatter domains:
  deduplicated selected table rows, matching settings/numeric hue cmap, shared
  categorical colour blocks/global bounds/sizes/marker slots and once-per-panel
  pooled guide legends without false observations. Legend-only differences and
  separate dataset labels retained; invalid names/pooled limits/conflicts fail.
  Layer-local defaults unchanged,36new tests/actual Rust browser/vector smoke
  and executable/editable local-vs-shared comparison. No dependencies/version/
  release or automatic faceting/line semantic claim; wider planned scope remains.
- Added strict opt-in SemanticSpec for independent scatter hue/size/style roles:
  categorical/numeric hue and size, categorical distinct filled markers, selected/
  reserved slots, listwise rows and global explicit/auto linear bounds. Sizes are
  point diameters, then squared to native areas; clipping changes mapping only.
  Constant/subnormal midpoint/one-guide, scaled extreme/adjacent normalization,
  positive-area underflow errors. Non-data role legend guides, label references,
  core/JSON/schema/actions/Python/Rust editor/native/export/RNG and85newtests.
  Legacy group/c/marker calls unchanged; no required dependency/version/release
  or numerical parity claim. Numeric coordinate primary2D first subset; semantic
  colorbar/outline/date/y2 and line/facet sharing remain on the wider plan.
- Added lineplot numeric-x estimates using shared named estimators/pointwise
  SD/SEM/PI/seeded CI, paired weighted mean/CI and within-x hierarchical unit
  bootstrap. NOT simultaneous bands or whole-curve resampling; raw line unchanged.
  Native bands/bars, sorting/per-hue first-seen order, horizontal/raw/log display/
  explicit axis-log fit, honest missing bounds and reserved hues/references.
  Exact band alpha/bar caps; invalid/nonmonotonic bands/derived endpoints fail.
  Pure config/JSON/schema/actions/Python/Rust editor/exports,66new tests, gallery/
  editable comparison. No new dependency/version/release or full-parity claim;
  no date/category predictors/y2/dodge/order/callable/independent semantic maps.
- Added optional violin weights: paired relative Gaussian covariance/effective n,
  inverse weighted ECDF quartile/median marks, declared-coordinate weighted mean,
  total-mass count widths and retained positive-row point/stick marks. No sample
  replication, sampling, fabricated singular KDE or clipping of fit/inner rows;
  old unweighted fits/linear quantiles remain unchanged. Stable scaled mass/mean/
  covariance and bounded kernel chunks, strict limits/derived failures, 78 new
  equation/artist/core/JSON/schema/editor/export tests and editable comparison.
  Updated Rust capability checks/real weighted HTTP/browser smoke, Windows
  Ghostscript detection and stale CI dashboard build invocation. No new required
  dependency/version/release/full-parity claim; Rust1.88 MSRV remains a final gate.
- Added kde2d/KDE2DSpec for weighted full-covariance bivariate Gaussian native
  contours/fills. Paired x/y relative weights, effective n and d=2 Scott=
  Silverman, pooled/per-hue density mass and evaluation grid, unchanged fit under
  cut/clip, raw-unit positive log display, singular/rank skip without jitter.
  Levels enclose approximate trapezoidal HDR mass CONDITIONAL on evaluated
  grid, all ties included: not confidence intervals/full-space guarantees or
  density renormalization. Scaled covariance/products and bounded 32×1024
  evaluation, clear failures for unresolvable grid/levels. Exact alpha/outline/
  hue dash/hatch/reference and native no-data legend proxies; 129 new module tests
  plus 1 registry regression, gallery 35/canonical specs 55 and editable comparison.
  No SciPy/dependencies/version/release changes; no 2D cumulative/colorbar/
  absolute levels/callable/other kernels/log fit/upstream parity.
- Added strict opt-in KDESpec for configurable weighted univariate Gaussian
  curves/fills. Relative weights define unbiased covariance/effective sample
  size, Scott/Silverman/numeric factors and bandwidth adjustment; bounded grid/
  cut/clip change evaluation, never fit rows or renormalize tails. Pooled or
  per-curve mass (including skipped singular hue mass), shared pooled support
  with conditional bandwidths, analytic full Gaussian CDF from -infinity,
  v/h/raw-unit positive observation logs and exact alpha/outline/width/hue
  dashes/hatches/reference metadata. Singleton/constant curves skip with an
  optional warning, never invent density/CDF/legend. Scaled covariance/weights,
  centered low bits, positive cross-product correction and bounded accurate
  evaluation handle extreme inputs or clearly fail invalid derived quantities.
  Old calls/JSON retain their 1.06*SD*n**(-1/5),200-point/constant fallback.
  125 new independent/native/numeric/artist/core/JSON/schema/editor/export tests,
  regenerated gallery and editable comparison. No SciPy/dependency/version/
  release change or bivariate/log-fit/weighted violin/upstream parity claim.
- Added opt-in typed HistogramSpec for shared equal-width/explicit raw bins,
  paired nonnegative weights, count/frequency/probability/proportion/percent/
  density, pooled/per-curve in-range normalization and cumulative mass
  integration (not summing density heights). Legacy hist density/group/bin/
  alpha behavior is unchanged. Supports v/h, positive observation logs/raw
  density widths, hue slots/hatches and exact alpha/outline/ref metadata.
  Scaled normalized sums/independent bins/accurate row prefixes preserve small
  mass and monotonicity; invalid derived widths/heights/raw totals fail clearly.
  95 new equation/native/artist/core/JSON/schema/editor/export tests, refreshed
  gallery and editable comparison. Bars/primary2D/linear heights only; no stack/
  dodge/step/fill/discrete/auto-bin/KDE/bivariate/date/y2/interval extension or
  new core dependency/version/release/parity claim.
- Added the ECDF first subset: raw observations/typed ECDFSpec, weighted tied
  empirical steps, per-curve proportion/percent/count and strict X>t complements.
  Accurate unrounded online prefixes preserve monotone mass; scaled normalized
  sums avoid weight overflow and right-to-left tails avoid 1-F cancellation.
  Missing/zero-weight exclusions, reserved hue color/dash slots, orientation,
  positive observation logs, exact line styles and reference metadata have
  103 equation/artist/schema/actions/editor/export tests plus native Matplotlib
  path comparisons. Zero-width dashed artists remain invisible without losing
  style/data, including Matplotlib3.8; extreme1e308 count ticker warnings reported.
  New gallery and editable four-panel preview. Primary2D/linear cumulative axes
  only; no extrapolated tails, intervals/censoring/smoothing/date/y2 or required
  dependency/version/release/parity claim. Existing layer defaults unchanged.
- Added statistical native/log first subset for barplot/pointplot/countplot:
  explicit numeric category locations/axis-coordinate spacing, log-width/dodge,
  physical-order sparse point paths, positive log values and opt-in log-fit
  mean/median/min/max with SD/SEM/PI/CI inverse endpoints. Original weighted/unit
  row pairing, count normalization and ordinal defaults remain. Nonstack bar/
  count baseline is a raw-value coordinate (linear default0, explicit positive
  on logs); bodies end at estimates, not baseline+estimate. Value-log stacked
  counts, axis-log sum/count and native/log y2 are explicitly rejected; positive
  derived/inverse geometry is never silently clipped. Pure core/JSON/actions/
  editor/native artists and repeatable PNG/PDF/SVG have 73 new tests and an
  editable four-panel preview. No required dependency, parity/version/release claim.
- Added named typed `components` styles for box body/whisker/cap/median/mean/
  flier and boxen body/median/flier. Component properties override layer styling
  with exact alpha and independent line/marker/fill controls, retaining defaults,
  hue/hatching, letter-value tiers and raw/native-log statistics/geometry.
  Unknown/unsafe/unsupported/explicitly hidden settings fail clearly. Public
  ComponentStyleSpec/DistributionComponentsSpec, strict nested JSON/schema,
  pure builders/actions/editor and repeatable PNG/PDF/SVG have 48 new tests and
  an editable four-panel comparison. No arbitrary kwargs, per-band/hue maps,
  precomputed bxp, bootstrap inference, new core dependency or version release.
- Added the violin semantics first subset: explicit box/quart/point/stick/None
  inner marks, exactly two selected/reserved hue split, width/area/count with
  per-hue/global reference scope, bandwidth adjustment and bounded cut/clip.
  Legacy median/width/observed-range defaults remain. Clip restricts KDE support,
  not fitting counts/observations; area is a common density scale rather than an
  exact clipped-polygon-area guarantee. Native/log artists and pure JSON/actions/
  editor routes are covered by 138 new tests and an editable four-panel preview.
  Callable KDE, arbitrary-hue split/inner kwargs and broader mappings remain
  unsupported; weighted violin is added in the separate extension above. No new core/SciPy dependency, version bump or publication.
- Added the native/log categorical first subset for box/violin/boxen/swarm:
  opt-in finite numeric category coordinates, reserved axis-coordinate spacing,
  positive log values, strict shared-axis declarations and preserved defaults.
  Summary `stat_scale='data'` stays raw; explicit 'axis' selects log10 statistics/
  KDE with inverse-mapped artists. Swarm keeps exact raw values and bounds.
  Added 60 regression tests and a runnable/editable comparison. Statistical
  bar/point/count native logs, date/style mappings and wider density/component
  options remain pending. No version change, release or full parity claim.
- Started the v1.1 functional-coverage target with shared, serializable `StatSpec`
  settings and dedicated raw-data `barplot`, `pointplot` and `countplot` builders
  (31 layer types). Named estimation, sample SD/mean SEM, observation PI and
  seeded percentile-bootstrap CI are independent of the existing precomputed
  `bar()` primitive. General intervals are drawn without clipping around the
  estimate; missing/singleton behavior and unsupported options are explicit.
  This subset uses 2-D linear ordinal axes; remaining coverage batches and
  release gates are still pending. No version bump or publication.
- Added paired-row weighted mean/percentile-bootstrap CI and two-stage
  unit-then-within-unit-row resampling, with explicit validation and assumptions.
  Zero-weight/missing rows are excluded; point estimates stay observation-weighted.
  Countplots now support probability/proportion/percent over all selected usable
  rows. Core builders/validation/JSON remain dependency-free.
- Added orientation, category/hue selection and reserved ordering, bar gaps,
  stacked counts and bounded numeric value labels to statistical layers, plus a
  runnable three-panel weighted/unit-CI, horizontal-SEM and stacked-percent demo.
  No invented estimates fill empty slots; unsupported scales/routes/settings and
  conflicting shared-axis orders fail explicitly.
- Extended box/violin with optional category/value columns and hue nesting,
  orientation, selected/reserved orders, width/gap/numeric dodge and shared
  colour/hatch encoding. One-column semantics/default coordinates remain.
  Missing rows drop listwise; empty cells have no fake distributions.
- Added native box IQR/percentile whiskers, deterministic Gaussian notches,
  mean/flier controls and shared stroke/flier styling; violin named/numeric
  bandwidth, bounded grid and mean/median/extrema controls. Arbitrary code,
  split/other inner styles, area/count normalization and weighted KDE are not
  silently accepted. Python/actions/JSON/schema/editor, minimum versions,
  native numeric/artist tests and repeatable PNG/SVG exports are covered.
- Added `swarmplot` (32 layer types), packing uniform circular raw observations
  in actual display space on every draw, including DPI/size/limits/layout and
  positive log-value axis changes. Orientation, order/hue/gap/numeric dodge,
  joint non-dodged hues, editable specs and editor previews are covered. Greedy
  packing is bounded to 2000 usable rows/layer; overcrowding retains all rows
  at gutters and warns rather than silently discarding observations. Arbitrary
  shapes/size mappings, native/log category scales and y2 remain unsupported.
- Added `boxenplot` (33 layer types) with deterministic linear-interpolated
  raw-data letter values, named/explicit bounded depth rules, exponential/linear/
  area widths, medians and observed tails. Includes one-column/group and nested
  category/hue orders/orientation/gap/dodge, native artists and repeatable editable
  PNG/PDF/SVG. Area uses actual interval mass, handles ties without infinities
  and extends full-depth outer bands to min/max. These bands are not CIs.
  Unsupported scale/weight/component options fail explicitly; core remains
  dependency-free and existing defaults/version metadata are unchanged.
- Bars support caller-supplied symmetric uncertainty (`yerr`, e.g. SD) and
  absolute asymmetric interval endpoints (`y_lower`/`y_upper`, e.g. 95% CI).
  Errors share actual grouped/dodged bar centers, including missing categories,
  secondary axes and polar bars. The primitive `bar()` never infers statistics.
- Added bar span/outline and independent error-line/cap styling controls, with
  thin neutral capped defaults for new bar errors and strict interval validation.
- Added an opt-in `publication` theme with soft fills, restrained typography,
  quieter spines and subtle y-grid lines behind marks. Existing themes and
  redundant encoding defaults remain unchanged.
- Added executable, seeded SD-versus-bootstrap-CI examples, editable specs and
  deterministic PNG/SVG previews, plus a refreshed bar gallery and bilingual
  usage docs. (bar의 SD·CI 표시, 논문용 스타일과 재현 가능한 비교 예제 추가.)
- Documented a bilingual Matplotlib/Seaborn feature-coverage audit and phased
  parity roadmap. Distinguish plot names from option/statistical/composition
  support and native Python customization from declarative JSON/editor support;
  planned APIs are explicitly not advertised as implemented features.

### Fixed

- Exclude disabled panel legends from lint's visible-clutter count without
  removing palette/redundant-encoding checks for their plotted data. Two regression
  cases cover entirely hidden legends and mixed visible/hidden panels.
- Decode Ghostscript's UTF-8 PDF text explicitly in TeX integration checks,
  independent of Windows cp949. Added a portable subprocess regression for
  non-ASCII text and ligatures; plot output and public APIs are unchanged.
  Corrected contributor commands to select browser tests by filename rather
  than an unregistered marker.
- Place statistical bar labels beyond their real interval endpoints, including
  negative/horizontal bars and groups that omit singleton intervals.
- Honor explicit zero cap sizes and error/outline stroke widths instead of
  substituting defaults; preserve existing standalone errorbar defaults.
- Read generated UTF-8 documentation explicitly on Windows. Separate atomic
  save/failure-cleanup tests from platform-dependent symlink and POSIX-mode
  checks so atomic replacement remains tested without elevated privileges.

- Check out the annotated release tag in the publisher job before using
  `--notes-from-tag`. The v1.0.0 tag and verified, attested artifacts remain
  unchanged; publication was completed from those exact workflow outputs.
  (발행 job의 tag checkout 누락 수정. v1.0.0 tag와 검증 산출물은 그대로 유지.)

## [1.0.0] - 2026-10-06

### Added

- Added a bilingual, executable gallery for all 28 registered plot layers.
  Every displayed source file builds the shown PNG and editable spec, and CI
  requires gallery coverage to match the live layer registry exactly.
- Declared the stable 1.x public Python/CLI/JSON compatibility and deprecation
  policy in English and Korean, with a public-surface/default-renderer guard.
  Matplotlib remains canonical; the serialized spec version stays `0.1`.

### Changed

- Narrowed the documentation's use of “pure” to the reducer's actual
  no-input-mutation/no-I/O contract and documented the mutable, defensive
  deep-copy model and its large-inline-data performance ceiling.
- Removed redundant action and return-snapshot copies from internal
  fluent/batch/editor dispatch paths while preserving public `Store` snapshot,
  history, listener, and reducer alias isolation.
- Added DB-API `params=` forwarding so `query=` values can be parameterized
  instead of interpolated into SQL.

### Fixed

- Close successful CLI render figures so repeated in-process CLI calls do not
  accumulate Matplotlib figure managers.
- Reject release reruns that would replace already-published tags/assets.
- Keep gallery source/spec checks strict about schema and values while allowing
  tiny floating-point calculation differences across NumPy/CPU versions; exact
  JSON round-trips and same-environment output reproducibility remain checked.
- Regenerated the executable publication demos so grouped KDE styling, current
  `LayerSpec` fields, and timestamp-free PDF metadata match the live engine.
  Added regressions for canonical demo specs and deterministic PDF metadata,
  and corrected the documented test total to count browser tests only once.
- Associated the Python editor's pasted-spec textarea with its visible label so
  assistive technology no longer exposes an unnamed input.
- Exposed preview drag handles as named native buttons, preserving mouse drag
  and arrow-key movement while giving assistive technology a control role and
  useful instruction.
- Replaced nested link/button export controls with single native download links
  and updated CLI help to advertise supported PGF output.
- Report numeric data, coordinates, and style values outside the renderer's
  floating-point range as clean user errors, without a CLI traceback or output
  replacement.
- Write `schema --out` and `docs --out` atomically so a failed replacement
  preserves the previous generated file and removes its temporary file.
- Capture Rust bridge stdout and stderr without OS pipes so large child output
  cannot stall until the 120-second timeout.
- Keep grouped-layer and regression-cardinality validation linear for ordinary
  hashable values while retaining equality fallback for unusual unhashable keys.
- Normalize common DataFrame/NumPy missing, temporal, and scalar values at the
  input adapter so specs remain strict-JSON serializable across CLI/Rust,
  recognize PyArrow tables before generic DataFrame duck typing, and omit
  grouped render series with no finite observations.
- Reject duplicate tabular column names, including collisions after string
  conversion, before adapters can overwrite or concatenate unrelated data.

## [0.6.1] - 2026-09-18

### Fixed

- Excluded Hypothesis runtime caches from source distributions and made the
  packaging check reject them, so sdist contents and hashes no longer depend on
  which tests ran before the build. Runtime code and APIs are unchanged.

## [0.6.0] - 2026-09-18

### Features

- Added native polar panels through `.projection_polar()` /
  `SetProjection("polar")`. Line, scatter, and bar layers work unchanged;
  unsupported layers and secondary-y axes fail validation. Polar panels can
  coexist with Cartesian and 3-D panels, remain outside Cartesian shared-axis
  links, and are exposed through the capability registry and dashboard. Radial
  labels use a vertical 90° ray to avoid Matplotlib's publication-font overlap
  at the default 22.5° position.
- Added 2-D `quiver` vector fields as the 28th layer type: numeric x/y/u/v,
  data-coordinate arrow angles, optional continuous magnitude colour/colorbar,
  y2/reference support, and explicit scale/width calibration. Validation
  rejects malformed vectors, grouping, invalid calibration, and orphaned
  colorbars before Matplotlib; 3-D quiver remains deferred.
- Added native `hist2d` and `hexbin` count maps (27 layer types total),
  sharing the existing LCH colormaps, colorbar, y2, and layout paths. Core
  validation rejects empty/non-finite data, unsupported grouping, malformed
  bins, invalid grid sizes, and invalid minimum counts before Matplotlib.
- Added long-form `stackplot` as the 25th layer type. It uses native
  Matplotlib stacked areas over existing `x`/`y`/`group` data, rejects
  per-group x-order mismatches and non-finite stack values before rendering,
  supports y2/references/styles, and cycles hatches for grayscale output.
- Added deterministic `stripplot` as the 24th layer type. It supports
  categorical/numeric x values, bounded horizontal jitter, grouping,
  references, secondary-y routing, and redundant markers; a fixed local RNG
  keeps point coordinates reproducible across repeated renders without global state.
- Added `regplot`: observations plus a numerically scaled linear/polynomial
  NumPy fit, with an explicit opt-in normal-approximation confidence band for
  the mean fit. Validation catches invalid degree/CI values, nonnumeric data,
  insufficient observations, and insufficient distinct x values before
  NumPy's linear-algebra path; no SciPy dependency was added.
- Added native Matplotlib step-line support through
  `line(..., drawstyle="steps-post")` (also `steps`, `steps-pre`, and
  `steps-mid`). This remains one `line` layer rather than introducing a
  duplicate plot type; invalid drawstyles and drawstyle on non-line layers
  fail validation.
- Added an x-axis `rug` layer using native Matplotlib tick collections, with
  grouping, labels/references, colour, alpha, width, and line-style support.
- Grouped KDE curves now cycle redundant line styles as well as colours, so
  they remain distinguishable in grayscale.

### Rust editor

- Added the co-versioned `mudplot-editor/` M13 crate: axum + Askama + tokio +
  the existing vendored htmx serve one atomic local session with cached PNG,
  undo/redo/reset, raw and visual action forms, and an agent-facing JSON route.
  Capabilities drive all-layer metadata plus theme/projection controls; saved
  specs open atomically and exact-size PDF/SVG/JSON exports are available.
  serde preserves versioned envelopes and arbitrary-precision JSON integers
  while Python remains the only reducer, validator, and renderer; bridge
  subprocesses are killed and reaped after a 120-second timeout.
- Added the pure-core `python -m mudplot apply SPEC ACTION -o OUT` bridge.
  Actions are reduced and the resulting spec validated before output; failures
  do not write output. Rust then calls the existing `render` CLI, so layer
  semantics are not duplicated across languages.
- Added declared Rust 1.88 MSRV, Cargo format/Clippy/test,
  Rust→Python→HTTP smoke coverage, and a real Chromium htmx/CSP check to CI. The unauthenticated server enforces loopback-
  only binding and HTTP Hosts (including bracketed IPv6, with userinfo and
  malformed/out-of-range ports rejected), same-origin browser mutations,
  restrictive no-store browser security headers, and request/form ceilings;
  multi-user state, specialized axis/drag
  controls, and native Rust rendering remain deferred.

### Dashboard

- Added a capabilities-driven advanced layer form covering all 28 registered
  layer types. It documents each type's required/optional fields, accepts the
  remaining `LayerSpec` fields as JSON, and rejects malformed JSON, unknown
  fields, and missing requirements before mutating editor state.
- Completed panel controls: per-panel Cartesian/polar/3-D projection; x/y
  scales and fixed/automatic limits; secondary-y-axis enable/configure/remove; and 3-D
  z-axis setup. `SetLimits(None, None)` now restores automatic limits and
  `SetSecondaryAxis(None)` removes y2, preserving the same action semantics
  for editor, agent, and Python consumers.
- Dashboard actions, undo/redo/reset, and spec imports now validate and render
  a prospective Store copy before committing it, so invalid edits or render
  failures leave state, history, and the cached preview untouched.
- Hardened the unauthenticated Python editor to match the Rust editor's local
  trust boundary: loopback-only bind/HTTP Host, same-origin mutations,
  restrictive no-store/COOP/CORP browser headers, and a 16-MiB request
  ceiling. Non-loopback startup now fails before creating editor state;
  user-controlled column names are escaped in every HTML view. Custom JS is
  same-origin external (no `script-src 'unsafe-inline'`), and htmx is
  configured for self-only requests with script-tag/eval processing disabled.

### Quality

- Release tags now fail preflight unless they are GitHub-verified signed
  annotated tags and the tag, Python package, `pyproject.toml`, Rust
  manifest/lock, changelog, and README install URLs agree. The release workflow is least-privilege, cache-disabled, uses locked
  dependency graphs, and reruns Python/Rust/browser/cross-language checks plus
  the full Tectonic/pdflatex/LuaLaTeX/BibTeX/biber matrix before publishing;
  bounded job timeouts prevent hung gates. Releases include SHA-256 checksums,
  reverify them after the cross-job artifact handoff, and carry GitHub OIDC
  build-provenance attestations. Official
  actions are commit-pinned to Node 24 releases, a retry-safe runner-native
  `gh` flow replaces the former third-party release action, and the pinned Tectonic
  binary is SHA-256 verified before execution.
- Added bilingual security-reporting guidance and enabled GitHub private
  vulnerability reporting, vulnerability alerts, and Dependabot security-fix
  pull requests for the repository.
- Added grouped weekly Dependabot updates for uv, Cargo, and GitHub Actions,
  each with a seven-day supply-chain cooldown. Current Python, minimum-
  compatibility, and Rust locks pass `pip-audit`/RustSec with no known
  vulnerabilities. A third isolated uv lock pins `pip-audit` itself; push CI,
  the nightly workflow, and release preflight audit both Python graphs plus
  the audit tool graph before project/browser/TeX setup.
- Pinned the distribution backend in the uv-locked dev environment and removed
  CI's ad-hoc/isolated installs. Packaging preflight now rebuilds the wheel
  from the sdist, imports it with site-packages disabled, enforces an
  engine-only wheel, and verifies Python typing/license, both editors'
  bilingual instructions, all dashboard sources, and the co-versioned Rust
  editor's compile-time schema/templates plus htmx inputs; the official htmx 1.9.12 artifact is
  SHA-256 pinned. Releases publish those exact verified
  outputs; the release gate independently rebuilds them and requires identical
  SHA-256 digests before publishing. Reference-only
  `src/pretext` and `src/SciencePlots` trees are explicitly excluded.
- Added a zero-error `pyright` check for `mudplot/`, the dashboard, and
  maintenance scripts to the dev environment and both CI Python jobs,
  targeting the supported Python 3.10 language level. Findings were fixed
  with explicit optional narrowing, accurate return types, checked form
  parsing, and type-safe handling of dynamic Matplotlib metadata.
- Declared the docs generator's existing pandas requirement as a dev
  dependency, so `uv sync --extra dev` now creates a complete environment for
  regenerating demos instead of relying on an undeclared local install.
- Added concise English/Korean contribution guides covering setup, checks,
  architecture boundaries, schema regeneration, and testing/documentation
  conventions; README development commands now use `uv sync` consistently.
- Standardized package metadata, module/design prose, dashboard copy, and
  palette documentation on the accurate `CVD-aware` claim. `CVD-safe` remains
  only where an explicit measured threshold and verified category ceiling
  support it. Bilingual architecture docs now describe both editors as the
  coexisting source-tree tools they are and state the dependency directions
  correctly.
- Hardened citation/href validation to reject every ASCII control character,
  including NUL and DEL, rather than only newline/tab characters. `href` now
  also permits only absolute HTTP(S) and `mailto` URIs, preventing active
  `javascript:`/`data:` links from reaching standalone SVG/PDF output.
- Added regression coverage for duplicate-label citations, disabling
  `\figcite`, math/CJK labels with references, unknown future spec fields,
  and secondary-y-axis plus colorbar layout.
- Extended Hypothesis coverage to the colour engine: sRGB/linear/Lab/LCh and
  Lab/XYZ round-trips, 8-bit hex identity, CIE76 metric properties, and
  CIEDE2000 identity/symmetry/non-negativity.
- Raised the render extra's Matplotlib lower bound from 3.6 to 3.8: an
  isolated Python 3.10/NumPy 1.23 lower-bound run exposed title overflow in
  Matplotlib 3.6/3.7, while 3.8 passes the 157 focused render/layout/reference
  checks. A separate committed PEP 723 uv lock reruns that exact Python 3.10/
  NumPy 1.23/Matplotlib 3.8 floor with Pytest 9.0.3 in CI and release preflight,
  keeping the documented native wrapping guarantee honest. The dev Pytest
  floor is now 9.0.3 because older releases are affected by PYSEC-2026-1845.
- `save_spec()`, single-file PNG/PDF/SVG export, and the apply/migrate/render
  CLI paths now share a same-directory fsync-and-replace writer, preserving
  existing permissions and symlink targets. Failed writes leave the previous
  spec/figure and no temporary debris. PGF retains Matplotlib's native
  multi-file write so raster sidecars keep the final basename, covered by a
  real-TeX regression. Saved JSON uses platform-independent LF newlines; CLI
  I/O and optional-backend failures return clean errors instead of tracebacks.
- Editor PNG previews and the explicit `mudplot render --preview` path retain
  configured DPI until either axis would exceed 2000 pixels, bounding memory
  for untrusted large-size/high-DPI specs without perturbing normal layout.
  Stored specs and final PDF/SVG exports remain exact and unchanged.
- Render and TeX-preview figures now reassert their configured inch size after
  construction, preventing interactive HiDPI backends from quantizing exact
  TeX geometry to device pixels; backend-quantization regressions are
  simulated directly in tests.
- PNG/PDF/SVG exports are now byte-reproducible for the same spec and
  environment across the Python API, CLI, and both editors. PDF creation/
  modification timestamps and SVG dates are omitted; SVG element IDs use a
  stable spec digest instead of Matplotlib's random salt, and raster artists
  stay inline despite ambient Matplotlib settings. The Python dashboard
  now also passes the target format into rendering, preserving SVG links.
- Validation now reports arbitrarily large integers as non-finite instead of
  leaking `OverflowError` from the shared `math.isfinite()` helper.
- The sRGB transfer functions now share the exact linear/power-branch
  intersection instead of the customary independently rounded cutoff pair.
  This removes its tiny discontinuity and preserves gamma/Lab/LCh round-trips
  at and around the `0.04045` boundary; Hypothesis found the failing value.
- Layer column fields are now checked against the capability contract before
  rendering: unsupported fields, non-string names, and empty optional names
  produce clear validation issues instead of ignored settings or `KeyError`.
  The audit also fixed `bar` capabilities omitting its implemented `group`.
- FigureSpec and action deserialization now enforce object/array/scalar shapes
  recursively before state mutation. Malformed untrusted JSON produces a
  boundary `TypeError` instead of implicit defaults or internal exceptions;
  categorical column values remain intentionally unconstrained JSON data.
  Excessive nesting, non-standard `NaN`/`Infinity`, floating-point overflow,
  lone Unicode surrogates, and duplicate object keys are normalized to clean
  user errors; Python and Rust both reject duplicate keys recursively;
  serialization emits strict RFC JSON, and actions require one canonical
  string `type` key. Rust envelopes preserve integers beyond 64-bit range
  rather than narrowing Python's JSON contract. Both runtimes explicitly
  reject serde's sole private arbitrary-precision marker key,
  `$serde_json::private::Number`, instead of interpreting it inconsistently. Hypothesis now checks arbitrary JSON
  is either rejected or validates without leaking an internal exception.

## [0.5.0] - 2026-09-14

A "paper workflow" release: pull citation/href metadata straight from a
`.bib` file (`ReferenceCatalog`) with an offline DOI/arXiv/URL resolver,
publication-preflight linting (`p.lint(journal=...)`) against a richer,
unified `JournalProfile` (2 journals → 4: nature/ieee/acm/revtex), and a
real multi-engine/multi-bibliography-tool TeX compile matrix -- which, by
actually running for the first time, found and fixed a real pdflatex/OT1
encoding bug in the citation-marker sentinel that every prior test run
(local or CI) had missed entirely. This closes every item in
`mudplot_v0.3_improvement_and_reference_repos.md`'s v0.5 checklist.
451 tests passing.

### Release/nightly TeX engine matrix (P1-5)

- Every push/PR already compiled a real paper with Tectonic (self-
  contained, fetches its own packages) -- but this had silently never
  actually run in CI at all, since CI never installed *any* TeX engine
  and `needs_tex` (matplotlib's own pgf-measurement prerequisite) always
  skipped the whole file first. Fixed: CI now installs `pdflatex`
  (`texlive-latex-base`/`-recommended`/`-pictures`, a comparatively small
  slice of TeX Live) and a pinned `tectonic` release, so the full
  citation/`.pgf` test suite -- not just this one test -- finally runs on
  every push.
- `tests/conftest.py`: matplotlib's pgf backend defaults to `xelatex`,
  whose Ubuntu package drags in nearly a full `texlive-latex-extra` tree
  for no benefit here. Since matplotlib accepts `pdflatex`/`lualatex` for
  this rcParam equally well, a small collection-time check now prefers
  whichever of the three is actually installed -- this only ever widens
  which environments the `needs_tex`-marked tests can run in.
- Found by actually exercising `pdflatex` for the first time (every prior
  test run, local or CI, had happened to default to `xelatex`): the PGF
  reference-marker sentinel used Unicode guillemets («/»), which don't
  exist under `pdflatex`'s default OT1 font encoding (`Command
  \guillemetleft unavailable in encoding OT1`) -- a real, previously-
  latent bug this work surfaced, not a hypothetical one. Switched to plain
  ASCII (backtick/straight-quote), present and unescaped under OT1/T1/
  Unicode alike.
- `tests/test_references.py::test_exported_pgf_compiles_into_a_real_paper`
  is now parametrised across the doc's suggested matrix: `tectonic`,
  `pdflatex`+BibTeX, `lualatex`+BibTeX, `lualatex`+biblatex/biber (a
  second paper template using `\usepackage{biblatex}`/`\printbibliography`
  for the last one). Each combination skips independently if its tools
  aren't installed, exactly like the existing `needs_tex` pattern. Also
  found on a real from-scratch Ubuntu TeX Live install (not reproduced on
  any other machine/CI setup this project has used): LuaLaTeX's real
  OpenType font shaping can render a common ligature like "fi" back out of
  the compiled PDF as one Unicode ligature glyph instead of two separate
  letters -- a font/platform detail in *how* text is encoded, not a
  citation-resolution discrepancy, so `_pdf_text()` now expands the
  standard Latin ligatures (`ff`/`fi`/`fl`/`ffi`/`ffl`) back to plain
  ASCII before any assertion runs. Also discovered (not a bug): biblatex's
  default numeric style abbreviates a given name without a following space
  (`"MFischler"`) unlike classic BibTeX's `plain.bst` (`"M Fischler"`) --
  a real typographic difference between the two bibliography conventions,
  accounted for in the assertion rather than papered over.
- New `.github/workflows/tex-matrix.yml`: installs a fuller TeX Live
  (`pdflatex`, `lualatex`, classic BibTeX, biblatex/biber) and runs just
  this parametrised test, on a nightly schedule, on a release tag push, or
  on manual request -- too slow to justify on every commit, per the doc's
  own "PR: Tectonic smoke test / nightly+release: the fuller matrix"
  split. Both new/modified workflow files pin `actions/checkout`/
  `astral-sh/setup-uv` to a commit SHA (not just a mutable tag), declare
  minimal `permissions: contents: read`, disable `astral-sh/setup-uv`'s
  cache (unneeded for a once-daily job, removes a cache-poisoning attack
  surface), and fetch `tectonic` from a pinned GitHub release tarball
  rather than piping the project's own install script into a shell.
- Verified all four matrix combinations pass locally (this machine has
  every engine installed), and separately verified the *exact* CI-post-
  change environment (only `pdflatex`+`tectonic`+`ghostscript` on `PATH`,
  `lualatex`/`xelatex`/`biber` absent) by running the full suite under a
  restricted `PATH` -- 29 passed, 2 skipped (the two `lualatex`
  combinations, correctly, since `ci.yml` doesn't install it).

### Richer journal profiles (P2-3)

- `JournalProfile` (`mp.JournalProfile`, `mp.get_journal_profile(name)`,
  `mp.JOURNAL_PROFILES`): consolidated publication constraint and style
  profile pairing style (fonts, linewidths, default figure size) with
  TeX column geometry (columnwidth, textwidth, columns) and preflight
  rules (minimum font size, recommended raster DPI, max legend entries,
  and grayscale policy) in one typed dataclass.
- Expanded `AVAILABLE_JOURNALS` from 2 to 4: `nature`, `ieee`, `acm`,
  and `revtex` now all have both full journal styling (fonts/linewidths/
  default size via `.journal()`) and matching TeX column geometry
  (via `.tex_size()`).
- `AVAILABLE_JOURNALS` and `JOURNAL_SIZES` are now derived directly from
  `JOURNAL_PROFILES` (single source of truth).
- `p.lint()` automatically uses `spec.journal` when set (no need to repeat
  `journal="ieee"` if you already called `.journal("ieee")`).
- `p.lint()`, `p.journal()`, and `p.tex_size()` all accept a
  `JournalProfile` object directly (or its string name).
- `p.lint()` gained raster submission DPI verification (`_check_dpi`):
  warns when a figure's `spec.dpi` is below the journal's recommended
  DPI (e.g. 300 for Nature/IEEE).
- Regression coverage: 6 new tests across `tests/test_journal_profiles.py`
  and `tests/test_lint.py`.

### Figure lint / publication preflight (P2-4)

- `p.lint(journal=None, *, min_font_pt=5.0, max_legend_entries=8)` /
  `mp.lint_figure(spec, ...)`: publication-quality *heuristics* distinct
  from `validate()`'s structural correctness -- does this actually work
  as a readable, greyscale/CVD-safe paper figure at its configured size,
  as a mix of `ok`/`warning`/`error` findings for an author to review
  rather than an all-or-nothing raise.
- Checks: page-width fit against a named journal's real TeX column
  geometry (`mp.capabilities()["tex_presets"]`); minimum text size across
  body/label/title/tick fonts; palette CVD-safety and true-greyscale
  safety (reusing `Palette.report()`, with the exact same palette
  construction `render()` itself uses, so a finding never disagrees with
  what's actually drawn); redundant marker/line-style/hatch encoding for
  grouped series; marker/line-style cycle-length exhaustion (more grouped
  series than distinct markers -- some become indistinguishable once
  colour is removed); legend entry count; and citation/href metadata
  validity (surfaced from `validate()`'s own reference checks).
  `report.ok` is `False` only when an `error`-level finding exists (an
  oversized figure, malformed reference metadata) -- everything else is a
  judgement call to review, not a hard failure.
- `mudplot/_lint.py` needs nothing beyond the stdlib to *import* (stays
  part of the pure engine's zero-dependency promise); only actually
  *running* the palette check needs the colour engine (numpy), imported
  lazily inside that one check -- verified in a fresh subprocess, the
  same pattern `tests/test_no_deps.py` uses for the rest of the pure core.
- Regression coverage: 22 new tests in `tests/test_lint.py`.

### DOI/URL resolver: arXiv-only `.bib` entries now resolve to a real link

- `mp.resolve_reference_href(fields)`: offline (no network access) DOI/
  arXiv-id/URL normalisation, extracted from `ReferenceCatalog` into its
  own documented, directly-usable function. Tries, in order: a `doi`
  field (bare, `doi:`-prefixed, or a full `doi.org`/`dx.doi.org` URL --
  all normalised to the same `https://doi.org/...` form); an arXiv id
  (`eprint` + `archiveprefix`/`eprinttype` == `"arxiv"`, the shape arXiv's
  own "export bibtex" feature produces) resolved to
  `https://arxiv.org/abs/...`; then a plain `url` field; `None` if none of
  those are present.
- Fixes a real gap in `ReferenceCatalog` (not just an added feature): an
  arXiv-only entry -- extremely common for ML/CS papers, `eprint` +
  `archiveprefix` and *no* `doi`/`url` field at all -- previously resolved
  to `href=None` silently, since the original doi-or-url-only fallback
  never looked at `eprint`. `ReferenceCatalog.__getitem__` now uses
  `resolve_reference_href` internally, so existing `.bib` files with
  arXiv-only entries start producing real links with no code changes.
- Regression coverage: 13 new tests in `tests/test_bib.py` (bare/prefixed/
  full-URL DOI forms all normalise identically, arXiv id resolution via
  both field-name variants, priority order when multiple are present, no
  link when none are present, and the exact arXiv-only-entry regression
  end-to-end through `ReferenceCatalog`).

### `.bib` integration: `ReferenceCatalog` (P2-1)

- `mp.ReferenceCatalog.from_bib(path)` / `.from_bib_text(text)`: a minimal,
  dependency-free reader for the common subset of BibTeX entry syntax real
  `.bib` files use (nested `{...}` field values, both quoting styles,
  unquoted numeric fields like `year = 1981`, `@comment`/`@string`/
  `@preamble` blocks correctly skipped rather than mistaken for real
  entries). Not a bibliography manager -- no cross-reference resolution,
  no `@string` macro expansion, no formatted-citation rendering (that's
  the *document*'s job, same as everywhere else reference metadata is
  used in mudplot).
- `catalog[key]` resolves straight to a ready-to-use `ReferenceSpec`:
  `citation=key`, `href` from the entry's `doi` field (as a
  `https://doi.org/...` link), falling back to its `url` field, or `None`
  if neither is present. `catalog.raw(key)` exposes every parsed field
  (title/author/year/...) for anything beyond citation/href, e.g. a
  paper-metadata preview in an editor. A missing key raises a `KeyError`
  naming the keys that *are* available.
- Plugs directly into the existing `citation=`/`href=` kwargs and the
  grouped-series `references=` dict (v0.4) -- no new layer-level API
  needed.
- Regression coverage: 12 new tests in `tests/test_bib.py` (multiple
  entries, comment/string blocks not mistaken for entries, DOI-vs-URL
  fallback, no-link entries, nested braces in a field value preserved,
  multiline values whitespace-collapsed, missing-key error, reading a
  real file by both `Path` and `str`, composing with the fluent API).

## [0.4.0] - 2026-09-07

A reference-system stabilization release: grouped-series citations/links,
a saner citation/URL validator, a documented FigureSpec version/migration
policy (+ `mudplot migrate` CLI), a citation-measurement policy for PGF
layout, a real JSON-Schema-validator compatibility test, Hypothesis-based
property tests for reducer purity, and a cross-referenced journal-profile
view. This closes every item in `mudplot_v0.3_improvement_and_reference_
repos.md`'s v0.4 checklist. 395 tests passing.

### Journal profile registry cleanup (P2-3)

- Two registries have always independently covered a "journal": `theme.
  AVAILABLE_JOURNALS`/`journal_overrides` (a style -- fonts/linewidths/
  default figure size, applied via `.journal(name)`) and `tex.TEX_PRESETS`
  (a TeX document class's column geometry, applied via `.tex_size(name,
  ...)`/`.preview(tex=name)`). They overlap only for a name that's both a
  journal *and* a well-known LaTeX class ("nature"/"ieee" are in both;
  "article"/"revtex"/"acm" are generic document classes with no house
  style, so TeX-only) -- this distinction previously existed only in the
  maintainer's head, with no cross-reference between the two modules and
  no test guarding against them silently drifting apart.
- `mp.capabilities()["journal_profiles"]`: the two merged for every name
  that has both (figure size, base/tick font, line width, column/text
  width, columns), so an agent building a coherent "IEEE-style figure"
  doesn't have to separately cross-reference the `"journals"` and
  `"tex_presets"` sections and guess whether they're meant to compose.
- `mudplot/theme.py`/`mudplot/tex.py` docstrings now cross-reference each
  other and `journal_profiles` explicitly.
- New `tests/test_journal_profiles.py`: every `AVAILABLE_JOURNALS` name
  has a matching `TEX_PRESETS` entry (so `.tex_size(name)` never fails for
  a name `.journal(name)` accepts) and a `JOURNAL_SIZES` entry;
  `journal_profiles` matches the underlying registries field-for-field;
  and an end-to-end check that `.journal(name).tex_size(name)` composes
  into one valid, renderable figure for every journal.
- Also fixed (found while cross-referencing these modules): `mudplot/
  tex.py`'s WYSIWYG mock-page preview used `plt.Rectangle`, which
  matplotlib re-exports at runtime but isn't in `pyplot`'s public type
  surface -- switched to importing `Rectangle` from `matplotlib.patches`
  directly (its actual home), no behaviour change.

### Hypothesis-based property tests

- New dev dependency: `hypothesis` (test-only). New
  `tests/test_property_based.py` widens several existing example-based
  guarantees into properties checked against a much larger randomised
  input space:
  - **reducer purity**: `reduce(state, action)` never mutates its `state`
    or `action` arguments, and its output is always still
    JSON-round-trippable -- checked over a curated slice of the action
    vocabulary (the single-field actions whose validity doesn't depend on
    other spec state) with Hypothesis-generated parameters, not just the
    handful of hand-picked actions the existing tests happen to dispatch.
  - **migration idempotency**: `migrate_spec_dict()` is a true no-op on
    any spec already at the current `SPEC_VERSION`, across many different
    resulting specs (not just the default one).
  - **citation/href character safety, as a property instead of a fixed
    example list**: any string built only from characters outside both
    unsafe sets always passes validation; any string containing at least
    one unsafe character always gets rejected -- restates P0-2's own rule
    generatively, so a future change to either unsafe-character set is
    checked against arbitrary strings, not just the four hand-picked
    examples in `test_references.py`.
  - a wider **JSON round-trip** over random figure-level settings (size,
    dpi, suptitle text including arbitrary/unicode content, theme).
  - Found one real edge case worth naming explicitly while writing this:
    a whitespace-only citation/href (e.g. `" "`) is *safe* under the
    character-safety rule but still correctly rejected by the separate
    "must be non-empty after stripping" check -- the property test filters
    for this so it verifies the character-safety rule specifically,
    without a false failure attributed to the wrong check.

### JSON Schema compatibility test

- New dev dependency: `jsonschema` (used only by tests, not the pure
  engine). `mp.json_schema()`'s existing sync guard (`test_schema_export.py`)
  only checked that the checked-in file matches a fresh regeneration
  byte-for-byte and that it superficially "looks like" a JSON Schema
  (has `$schema`, a `title`, ...) -- it never actually ran a real JSON
  Schema validator against it, so a schema that was technically malformed,
  or too permissive to catch real mistakes, could still pass every
  existing check.
- New `tests/test_json_schema_compat.py`: the schema itself is checked
  against the Draft 2020-12 meta-schema (`Draft202012Validator.check_schema`);
  a range of real specs (grouped references, multi-panel + secondary axis,
  matrix/heatmap, 3-D, the bare default) are round-tripped through
  `.to_dict()` and validated against the exported schema; and a couple of
  deliberately-wrong instances (wrong field type) are confirmed to actually
  get rejected, not silently accepted -- proving the schema is a real
  constraint an external (Rust/serde, form-generator) consumer could rely
  on, not just documentation-shaped JSON.
- Documents one real, existing gap found this way (not a bug -- a
  deliberate scope boundary made explicit): `LayerSpec`'s fields all carry
  defaults, so nothing is "required" at the *schema* level for e.g. a
  `line` layer's `x`/`y` -- that's mudplot's own semantic `validate()`'s
  job, not the JSON Schema's.

### Citation measurement policy (P0-3)

- WYSIWYG layout for a citation is only exact for compact/numeric styles
  (e.g. `"[12]"`): matplotlib lays a figure out *before* the document's own
  bibliography resolves `\figcite{key}`, so it has no way to know the real
  rendered width of e.g. an author-year citation (`"(Fischler and Bolles,
  1981)"`) ahead of time. This guarantee scope is now documented explicitly
  (`FigureSpec.reference_measure_text`, `Plot.reference_style()`).
- `.reference_style(measure_text="(Fischler and Bolles, 1981)")`: measure
  PGF legend citations against a representative example of your actual
  citation style instead of the compact default, so `_autofit()`/legend
  sizing predicts the final compiled width more accurately. The text is
  stripped back out at PGF-substitution time and never emitted to output;
  rejects characters matplotlib's PGF backend would escape (which would
  break that strip-back-out).
- Deliberately **panel-title citations don't widen** even when
  `reference_measure_text` is set: a title can wrap (`wrap=True`) across
  multiple lines, which can split the measurement filler from its sentinel
  into separate .pgf text blocks -- silently leaking the filler text into
  the final output instead of being stripped. Found by testing this
  feature against the existing two-citation demo spec (legend + title),
  not by inspection.
- Regression coverage: 6 new tests in `tests/test_references.py`
  (measured width actually widens, filler never leaks into output inc. the
  title-wrap case that broke first, `None` restores the compact default,
  PGF-unsafe characters rejected, JSON round-trip).
- Also fixed: `mudplot/docs.py`'s Markdown table dividers were an
  inconsistent mix of `|---|` and (accidentally, via editor auto-format)
  `| --- |` styles across sections, which could make a freshly generated
  `docs/REFERENCE.md` disagree with itself byte-for-byte depending on which
  tool last touched it. Standardised on `| --- |` everywhere.

### FigureSpec version/migration policy

- Package version (`mudplot.__version__`) and spec version (`SPEC_VERSION`,
  the on-disk `.mplot.json` contract) are now formally independent: not
  every release changes the serialized shape, and `SPEC_VERSION` is the one
  a Rust/agent consumer, or a saved file, actually needs to check
  compatibility against. Documented in `mudplot/spec.py`.
- `FigureSpec.from_dict()` (and therefore `from_json`/`load_spec`/
  `Plot.from_json`, every deserialisation path) now checks the saved
  `version` field: an older *known* version gets upgraded through a new
  `MIGRATIONS` registry (empty for now -- nothing predates `"0.1"` yet);
  an unrecognised version (older with no migration, or newer than this
  mudplot understands) now raises a clear `ValueError` instead of silently
  loading with whatever fields happen to match. `validate()` catches the
  same problem for a `FigureSpec` built directly (bypassing `from_dict`)
  with a mismatched `version`.
- New CLI subcommand: `mudplot migrate old.mplot.json -o new.mplot.json`
  (upgrades and rewrites a saved spec; a no-op write if it's already
  current).
- Regression coverage: 4 new tests in `tests/test_spec_roundtrip.py`, a new
  `tests/test_cli_migrate.py` (4 tests).

### Reference metadata: grouped series, saner citation/URL validation

- `ReferenceSpec` (`mp.Reference`/`mp.ReferenceSpec`): the citation/href pair
  used to live only on `LayerSpec`/title fields; now also the type of
  `LayerSpec.references`, a `{group_value: ReferenceSpec}` dict for
  attaching a *different* citation/href to each series of a `group=`-ed
  layer (previously impossible -- every series in a group shared one
  `label`/`citation`/`href` at most, so e.g. `group="method"` with RANSAC/
  J-Linkage/PEARL series couldn't cite a different paper per method). Wired
  through PGF `\figcite`/`\href` decoration and SVG per-legend-entry links,
  the same as the existing ungrouped case; a group value absent from
  `references` gets no decoration (no silent fallback to a shared citation).
- Citation/href validation split into separate rules instead of one shared
  TeX-unsafe-character blocklist: a citation is only ever used as a
  `\figcite{KEY}` lookup argument (never typeset), so ordinary BibTeX-key
  punctuation (`_`, `:`, `-`) is now allowed -- previously `fischler_1981`
  or `han:v2v_2019` were rejected outright. `href` becomes a
  `\href{URL}{...}` argument, which hyperref itself reads with special
  URL-safe catcodes (like `\url`), so query strings/fragments (`_`, `&`,
  `#`, `%`, `~`) are now allowed there too. Brace/backslash/control
  characters (the actual macro-injection risk) are still rejected in both.
- `mp.capabilities()["backends"]`: which of `citations`/`hyperlinks`/
  `vector`/`requires_tex` each output format (`png`/`pdf`/`svg`/`pgf`)
  actually preserves, so an agent/editor can show e.g. "citations are only
  kept in PGF export" instead of that being implicit renderer behaviour.
- Regression coverage: 14 new tests in `tests/test_references.py`.

## [0.3.0] - 2026-09-06

LaTeX-native citations/links in figure text, a genuinely usable editor
(multi-panel, drag-to-position, open/export), and the first real-browser
test coverage -- which found three bugs the HTML-level tests could not see.
345 tests passing.

### LaTeX-native citations and links inside a figure

- `LayerSpec.citation`/`href` (legend entries) and `PanelSpec.title_citation`/
  `title_href` (via `.title_reference(...)`): attach a BibTeX key and/or URL
  to figure text. Nothing is baked into the image -- the document resolves
  it, so a figure's `[1]` is the same `[1]` as in its References list.
- `.pgf` export (`save("fig.pgf")`): emits `\figcite{key}` and
  `\href{url}{...}`. Deliberately `\figcite`, not `\cite`, so the paper
  decides what a figure citation means (`\cite`/`\citep`/`\autocite`/
  nothing) -- `mudplot.PREAMBLE` provides the default mapping.
- Backend-dependent by design: PGF gets real macros, SVG turns the text into
  a clickable link, raster output stays plain.
- Metadata is substituted into LaTeX source verbatim, so `validate()`
  rejects braces/backslashes/newlines in these fields (a trust boundary:
  the user's document compiles the result).
- Verified end to end against a real TeX installation: a generated .pgf
  compiles with pdflatex+bibtex, and the citation numbers in the figure
  match the paper's bibliography (`tests/test_references.py` covers the
  export contract; the compile check was manual).
- The markers used to survive pgf's text escaping are kept short on purpose:
  they sit in the text matplotlib measures during layout, and an embedded
  full URL collapsed the axes to zero size. Locked in with a test that
  fails on the layout warning.

### Editor

- Canvas-first layout: the figure is a large sticky workspace, controls sit
  in an independently scrolling inspector, secondary sections collapse.
  Single column below 800px.
- **Multi-panel editing**: set the grid, then pick which panel every control
  edits. Titles/axes, layer list, position toggles and all three drag
  handles follow the selection; panel-scoped actions default to it
  server-side. The selection is session state, never written to the spec.
- Direct editing of panel title and x/y axis labels, plus legend-label,
  citation and link fields -- no more raw JSON for ordinary edits.
- **Open** a saved `.mplot.json` (validated first, so a bad file reports the
  problem instead of wedging the editor) and **export** PDF/SVG at the exact
  configured size, not just the preview PNG.
- Fixed: the htmx fragment carried its own `#app-body` wrapper while every
  swap targeted `#app-body` with `innerHTML`, so each edit nested another
  copy.
- Fixed (found by the new browser tests): arrow-key nudging never worked --
  clicking a handle to focus it counted as an edit, which swapped in a new
  overlay and stole that focus; scroll restore ran before layout and was
  clamped away; form labels were never bound to their inputs, so every field
  was unlabelled for screen readers.
- Nudges are coalesced, so holding an arrow key produces one action instead
  of one per keypress.

### Renderer

- Each Axes records `ax._mudplot_panel`. `fig.axes` also collects twin (y2)
  and colorbar axes, so its order stops matching panel order after the first
  panel -- anything mapping a rendered Axes back to its spec needs this.

### Testing

- `tests/test_editor_browser.py`: real Chrome via Playwright (optional
  `browser` extra; skipped when absent) covering drag, keyboard nudge,
  multi-panel targeting, open-from-file, and swap behaviour.
- `tests/test_references.py`: the exported `.pgf` is compiled by tectonic
  and the resulting PDF read back, so "the citation resolves against the
  paper's bibliography" is checked rather than asserted.

## [0.2.0] - 2026-09-05

TeX-ready figure sizing/layout, position-anywhere legends/titles/
annotations, and a substantially more usable interactive editor (htmx
partial updates, drag-to-position, visual redesign). 322 tests passing.

### TeX column sizing, overlap-free layout, draggable legends, docs/editor tabs

- `Plot.tex_size(preset, columns=1|2)`: size the *actual* figure (not just
  `.preview()`) to a TeX document's single-column width or full text width
  (for a double-column-spanning figure), matching the same column/font
  metrics `.preview(tex=...)` already used.
- `render()`/`save()` now precompute layout so text never overlaps or gets
  silently clipped, while still preserving the exact configured physical
  size (needed for TeX placement): titles/suptitle wrap natively at the
  figure width instead of overflowing it, and canvas space is reserved for
  any named `"outside ..."` legend location so it's never cut off. Uses
  matplotlib's own constrained-layout engine and text-measurement renderer
  throughout -- no custom layout system, and a no-op when nothing would
  otherwise be clipped. 3-D panels keep the previous `tight_layout()`
  fallback (matplotlib's constrained layout doesn't support 3-D Axes well).
- `LegendSpec.bbox_to_anchor` / `.legend(bbox_to_anchor=[x, y])`: pin a
  legend to an exact figure-fraction position, overriding `location`.
  Trusted as-is (not auto-adjusted) since an explicit position may
  deliberately overlap the plot.
- Dashboard editor: a ✥ handle to drag the legend directly on the preview
  (mouse drag, or click + arrow keys), dispatching the same
  `SetLegend(bbox_to_anchor=...)` action as the fluent API. Also split into
  **Editor**/**Docs** tabs within the one running server (`/docs` serves
  the live engine reference), instead of needing the separate static
  `dashboard build` for documentation.
- Regression coverage: `tests/test_layout.py`, additions to
  `tests/test_dashboard_editor.py`.

### Dashboard editor: htmx partial updates, title/annotation dragging, redesign

- Converted the editor's full-page-reload-per-action UX to htmx partial
  swaps: every form/drag now updates the preview, layer list, and action
  log in place. Vendored `htmx.min.js` (0BSD licensed, `dashboard/static/`)
  -- no new Python dependency, plain form-post fallback still works for
  non-JS clients (`HX-Request` header detection).
- `PanelSpec.title_position` / `.title_position([x, y])`: pin a panel
  title to an exact axes-fraction spot (bypasses matplotlib's title-
  specific y-offset transform, which otherwise silently discards a
  repositioned y under constrained_layout -- draws a plain axes-fraction
  text artist instead once a position is set).
- `SetLayerAt` action / `.set_layer_at(layer_index, at)`: reposition a
  `text`/`annotate` layer's anchor (data coordinates) -- also usable by an
  agent, not just the editor.
- Dashboard editor: draggable handles for the legend (blue), panel title
  (purple), and any `text`/`annotate` layer (green, one per layer,
  automatic) directly on the preview -- mouse drag or click + arrow keys.
  A dedicated "Add text / annotation" form. New `EditorSession.refresh()`
  caches one render's PNG + layout info (panel bbox/limits/scale) so
  `/fig.png` and the drag handles' placement can't disagree.
- Visual redesign: consistent spacing/typography/colour system, card
  shadows, a checkerboard preview background (so a white figure is visibly
  bounded), clearer button/error/log styling.
- `text`/`annotate` layers are now excluded from constrained_layout's
  space-reservation solve (`Artist.set_in_layout(False)`) -- their data-
  coordinate position isn't known until axes limits are, which previously
  produced spurious "constrained_layout not applied" warnings.
- Regression coverage: additions to `tests/test_layout.py` and
  `tests/test_dashboard_editor.py` (23 new tests).

## [0.1.0] - 2026-09-05

First tagged release: the pure spec/reducer/store engine, the LCH colour
engine, the Matplotlib renderer (21 layer types), TeX-aware preview, the
fluent + agent-facing APIs, the CLI, and the human-facing dashboard, plus
three stability-hardening passes and named colour-palette presets. See
`docs/DEMO.md` for a reproducible, pandas-driven demo of the actual output.

### Colour: named palette presets + black & white print safety

- Added three named, pre-verified `qualitative` palette presets
  (`mudplot.capabilities()["palette_presets"]`): `paper` (default, safe up to
  6 categories), `vivid` (higher chroma, safe up to 6), `soft` (lower chroma
  for large-area fills, safe up to 5). "Safe" = measured via
  `Palette.report()` (worst-case ΔE00 ≥ 8 across normal + protanopia/
  deuteranopia simulation, min CIE L* gap ≥ 3 in true relative-luminance
  greyscale), not an assumed or certified guarantee — see
  `tests/test_palette_presets.py`. Use via `.palette(preset="paper")` or
  `mp.color_palette(n, preset="paper")`.
- `ThemeSpec.hatches`: bar/box/violin fills now also cycle a hatch pattern
  per group by default (alongside the existing marker/line-style cycle for
  line/scatter), so grouped fills stay distinguishable in black & white
  print/photocopy regardless of how similar the underlying greys are.
  Disable via `.encoding(redundant_encoding=False)`.
- `docs/DEMO.md` §4/§5: palette presets previewed under normal/CVD/true
  greyscale vision, plus a grouped bar chart converted pixel-by-pixel to
  true relative-luminance greyscale to demonstrate hatches remain readable
  after printing (not a mockup).
- Softened the top-level README colour claims from "colourblind-safe" to
  "colourblind-aware" / measured, to match what is actually verified.

### Stabilization: data fidelity and editing

- Categorical x positions now use Matplotlib's shared category registry across
  layers, secondary axes and shared panels instead of independent mappings.
- Grouped 2-D/3-D continuous scatter uses a single normalization and colorbar.
- 3-D panels honor axis scales/limits, legend placement and panel labels;
  mixed-projection figures retain sharing between their 2-D panels.
- Palette size accounts for all independent series and pie slices per panel.
- Store state/history/return values/listener notifications are isolated
  snapshots, and reducer results no longer alias mutable action payloads.
  Change store state through actions rather than mutating `plot.spec`.
- `save()` now preserves the configured physical size by default, including
  with ambient Matplotlib tight-crop settings. Use `save(path, tight=True)`
  (or `mp.save(spec, path, tight=True)`) for the previous cropped output.
- TeX preview avoids cropping/rescaling the embedded figure; context-free
  preview returns the actual vector figure rather than a rasterized copy.
- Failed render/save operations close their figures; successful calls still
  return an open figure owned by the caller.
- Validate figure geometry, ratios, all axis scales/limits and empty encoding
  cycles; reject negative/non-integer panel indices and invalid layout actions.
- Regression coverage: `tests/test_stabilization.py`.

### Added

- **Colour engine**: sRGB ↔ linear ↔ XYZ ↔ Lab ↔ LCH conversions (numpy-only);
  CIE76/CIEDE2000 colour difference (validated against Sharma et al. 2005);
  Machado et al. (2009) colour-vision-deficiency simulation
  (protan/deutan/tritan); qualitative/sequential/diverging palette
  generators optimised for maximum contrast and CVD safety.
- **Declarative spec model**: `FigureSpec` and friends — a fully
  serialisable dataclass tree with lossless JSON round-tripping.
- **Pure reducer architecture**: `actions` + `reducer` + `store`
  (functional core / imperative shell); `Store.undo()`/`redo()`.
- **Renderer**: line/scatter/bar/errorbar/band/hline/vline/text/annotate/
  hist/box/heatmap layers; multi-panel layouts with width/height ratios;
  secondary y-axis; shared axes; despine; outside legends; continuous
  colour-mapped scatter + colorbar (using the same LCH colormaps).
- **Design-quality features**: redundant marker/line-style encoding for
  greyscale/CVD safety; palette `lightness_jitter`;
  `Palette.report()`/`grayscale_srgb()`.
- **TeX-aware WYSIWYG preview**: renders a figure at its true final size
  and font inside a mock document column (article/ieee/revtex/nature/acm
  presets).
- **Fluent builder API** (`mp.plot(...)`) accepting dict/records/rows/
  pandas/polars/numpy/pyarrow/DB-API cursor or connection+query inputs.
- **Agent-facing interface**: `capabilities()`, `json_schema()`, `apply()`,
  action history/replay (`action_log`), pure `validate()`/`assert_valid()`.
- **CLI**: `python -m mudplot {capabilities,schema,docs,validate,render}`.
- **Docs generation**: `mudplot.docs.reference_markdown()` — the same
  introspection that powers `capabilities()`, turned into a Markdown
  reference (`docs/REFERENCE.md`), kept in sync with CI.
- **Dashboard** (separate package, human-facing):
  - a static docs + design-gallery site generator
    (`python -m dashboard build`)
  - a local interactive editor prototype (`python -m dashboard serve`),
    driving the exact same Store/actions/reducer as the fluent API
- Packaging: `py.typed` marker, MIT `LICENSE`, English-first docs with
  Korean translations kept alongside (`*.ko.md`).

### Fixed (stability hardening pass)

- `.journal(...)` didn't actually change the figure size (a dead rcParams
  entry was shadowed by an explicit `figsize=`); now applied directly to
  the spec.
- Auto panel labels (a/b/c) used the theme's font size directly instead of
  the effective (possibly journal-overridden) rcParams value.
- The TeX `full_width=True` preview inflated the embedded figure to
  roughly 2x its true rendered size.
- `SetData` silently discarded previously-registered `data.matrices`.
- A flat list of strings passed as plotting data was shredded
  character-by-character instead of being rejected/treated as one column.
- `qualitative()`'s own `min_delta_e` reporting used an O(n²) pure-Python
  loop (impractically slow beyond a few hundred colours); requesting more
  colours than `n_candidates` silently produced duplicates.
- `Store(spec)` didn't defensively copy its initial state, so external
  mutations could leak into "pure" store state.
- The CLI printed raw Python tracebacks for ordinary errors (missing file,
  malformed JSON) instead of a clean one-line message.
- `hline`/`vline`/`text`/`annotate` ignored `axis="y2"` and always drew on
  the primary axis.
- Grouped bar charts drew every group at the same x position, hiding
  shorter bars behind taller ones; bars are now dodged automatically.
- `capabilities()` under-reported that `bar`/`errorbar`/`band`/`hline`/
  `vline`/`text`/`annotate` all support `axis="y2"` routing (only
  `line`/`scatter` listed it), even though it worked correctly at render
  time. Added a cross-module consistency test to prevent this class of
  drift from recurring.
- Categorical x-axis values (e.g. bar-chart category labels like
  `"control"`/`"treatment"`) crashed every series layer with "could not
  convert string to float". Non-numeric x columns are now mapped to
  positions with the original strings applied as tick labels.
- The lazy top-level API (`mp.render`, `mp.save`) broke after the *first*
  call in a process: resolving one lazy attribute had the side effect of
  shadowing another (or itself, on the next access) with the raw
  submodule instead of the intended function, due to how Python binds
  submodules onto their parent package. This slipped past 202 passing
  tests because they mostly import the real functions directly rather
  than exercising the lazy `mp.*` attributes repeatedly -- exactly the
  pattern real multi-figure scripts (and the README's own examples) use.

See `DESIGN.md` §4c2 and `tests/test_bugfixes.py` for full details on each
of the above.

### Expanded plot coverage + 2 more bugs

### Added

- **3-D plots**: `scatter3d`, `line3d`, `surface`, `wireframe`. A panel
  opts in via `.projection3d()`; 2-D and 3-D panels can coexist in the same
  multi-panel figure. `render()` was restructured to build axes with
  `fig.add_subplot()` per panel (instead of `plt.subplots()`) so each panel
  can have its own projection, with `sharex`/`sharey` re-implemented
  manually via `Axes.sharex`/`sharey` for the (2-D-only) "all"/"row"/"col"
  modes.
- **Distribution plots**: `violin`, `kde` (a small numpy-only Gaussian KDE
  -- no scipy dependency).
- **2-D field plots**: `contour`, `contourf` (share the same
  `data.matrices` + LCH-colormap infrastructure as `heatmap`).
- **`pie`** charts.
- Categorical x-axis values (already fixed for 2-D series layers) and the
  redundant-encoding/colour-mapping machinery all extend to the new types
  where it makes sense.

### Fixed

- **Pie charts silently drew a duplicate, overlapping legend.**
  `ax.pie(..., labels=...)` also registers each wedge as a legend handle
  (so `ax.legend()` can be called separately), which collided with
  mudplot's generic "draw a legend if there are labelled handles" logic --
  every pie chart got its on-wedge labels *and* a redundant legend on top.
  Fixed by clearing each wedge's legend label after drawing.
- **The deepest root cause of the lazy `mp.render`/`mp.save` bug (from the
  previous pass) was still only partially fixed.** The original fix patched
  up the colliding `_LAZY` entries inside `__getattr__`, but *any* ordinary
  import elsewhere in the codebase -- e.g. `Plot.save()`'s own
  `from .render import save` -- triggers the exact same submodule/parent-
  binding side effect *without* ever calling `__getattr__`, so it could
  still silently squat on the "render" slot before a single `mp.render`
  access happened. The real, permanent fix was renaming the implementation
  module from `mudplot/render.py` to `mudplot/_render.py` so the collision
  is structurally impossible rather than something to keep patching around.

## Supported plot types (current)

`line`, `scatter` (continuous colour mapping + colorbar), `bar`
(auto-dodges when grouped; categorical or numeric x), `errorbar`, `band`,
`hist`, `box`, `violin`, `kde`, `heatmap`, `contour`, `contourf`, `pie`,
`hline`/`vline`, `text`/`annotate`, and 3-D `scatter3d`/`line3d`/`surface`/
`wireframe`. Most support secondary y-axis routing (`heatmap`/`hist`/`box`/
`violin`/`kde`/`pie`/`contour`/`contourf`/3-D types don't, since it isn't
meaningful for them). See `docs/REFERENCE.md` (or `mp.capabilities()`) for
the authoritative, always-up-to-date list.
