# Violin workflow: 짝 반쪽·native component·공유 역할

C04는 기존 `violin` layer를 확장합니다. Upstream 전체 동등성이나 넓은 F01/F02/G01/E01/Q01/REL01·v2 전체 종결은 아닙니다. Package1.1.0/schema0.1·의존성 하한·외부 의존성 없는 선언 core를 유지합니다.

```sh
python -m examples.violin_workflow artifacts/v2_violin
python -m mudplot render artifacts/v2_violin/violin_paired_profiles.mplot.json exact.png
```

예제는 원본 ID를 보존한 결정론적 **합성 관측값**으로 editable JSON과 실제 PNG/SVG/PDF를 만듭니다. 실험 자료가 아니며 행을 재작성·복제·샘플링하거나 무관한 역할을 몰래 합치지 않습니다.

## 기존 의미와 직렬화

`.violin(value, group=category)`는 한 열 의미를, `.violin(category, value, group=hue)`는 범주/관측 역할을 유지합니다. 가로 방향도 인자 역할을 바꾸지 않습니다. 새 제어를 생략하면 기존 native/default 경로와 JSON을 유지합니다. 새 `ViolinSpec` 없는 `split=True`는 선택·예약 hue가 정확히 둘인 기존 공통 중심 경로입니다.

Optional `LayerSpec.violin`은 기존 tail 뒤에 추가하고 None이면 생략합니다. `ViolinSpec`/`ViolinHueComponentsSpec`의 typed/dict 형식은 builder·action·JSON에서 동일합니다. Component는 기존 `LayerSpec.components: DistributionComponentsSpec` 자리를 재사용하며 새 optional role도 뒤에 추가하여 None을 생략합니다. Callback·Path 객체·임의 Matplotlib kwargs는 저장하지 않습니다.

```python
p = mp.plot(raw).violin(
    "season", "response", group="treatment", weights="weight",
    inner="box", split=True, density_norm="count", common_norm=True,
    violin={
        "split_policy": "paired",
        "hue_components": [
            {"level": "control", "components": {"whisker": {"color": "red"}}}
        ],
    },
    components={"body": {"alpha": 0.9}, "box": {"line_width": 1.5}},
)
```

## 명시적 다중 hue 짝 반쪽

`violin={"split_policy":"paired"}`는 `split=True`와 독립 범주형 hue를 요구합니다. 기존 두 hue 계약을 자동 변경하지 않습니다. 연속 숫자 hue의 full profile은 지원하지만 자동 짝은 거부합니다.

고정 hue 자리 수H에 P=ceil(H/2), working 범주 중심C, gap 전 전체 폭W를 둡니다. Hue i의 짝 j=floor(i/2)는 중심 `C+(j-(P-1)/2)*W/P`, 전체 짝 폭 `W/P*(1-gap)`를 사용합니다. 짝수 hue는 왼쪽/아래, 홀수는 오른쪽/위입니다. 마지막 홀수 개 hue에는 왼쪽 반쪽만 있으며 H=1도 유효합니다. H=2는 기존 반쪽 수학과 같습니다. 빈 예약 hue도 짝 순서를 유지하지만 body·inner 관측·관측 범례를 만들지 않습니다.

이 정책이 위치를 소유하므로 dodge는 자동/0만 허용하고 추가 hue dodge는 거부합니다. Width/gap은 범주 좌표이며 point 크기·확률/질량이 아닙니다. 같은 hue의 서로 다른 raw size/style tuple은 각각 실제 fit과 관측값을 보존하며 같은 hue lane을 사용합니다.

## Gaussian·가중치·정규화

기존 Gaussian evaluator를 재사용합니다. `bw_method`는 Scott/Silverman 또는 양의 유한 factor, `bw_adjust`는(0,1000], `points`는2..1000, `cut`은0..10 bandwidth입니다. SciPy·callable kernel/bandwidth·bootstrap·별도 evaluator는 추가하지 않습니다.

Clip은 증가하는 원자료 절대 measurement 경계이며 각 끝점 None을 허용합니다. Measurement clock을 선언하면 실제 target축의 규칙으로 날짜 literal을 변환합니다. Clip은 평가 support만 제한하고 fit 행·양의 질량·inner 관측/통계는 자르지 않습니다. 빈 교집합이나 표현 불가능한 support는 명확히 거부합니다.

Weights는 짝지은 유한 비음수 상대 질량입니다. 결측/0 행을 양수 검사 전에 제외하고 관측을 복제하지 않습니다. Gaussian은 기존 unbiased 가중 공분산/effective n을 사용합니다. 가중 분위수는 보간 NumPy 분위수가 아니라 오른쪽 연속 weighted ECDF의 역함수입니다. 단일/상수 셀은 실제 퇴화 profile이며 Gaussian이나 CI를 발명하지 않습니다.

Raw hue/size/style tuple은 fit을 나누지만 **정규화 pool은 effective hue만** 기준으로 합니다. 독립 hue가 없으면 하나의 pool, `common_norm=True`이면 전체 pool입니다. 새 경로의 peak/mass 참조는 pool별 한 번 해결합니다.

- `width`: 각 profile의 peak를1로 정규화합니다.
- `area`: fitted 좌표의 공통 density peak 기준이며 clip한 polygon 면적이 정확히 같다는 보장이 아닙니다.
- `count`: peak 정규화 후 셀 행 수 또는 양의 상대 가중 질량을 pool 최대값으로 나눈 비율을 곱합니다.

Semantic size는 weight/effective n/density/area가 아니며 공유 semantic domain도 통계 pool을 바꾸지 않습니다. Raw 비확장 `inner='legacy'`는 이미 계산한 profile/stat dict를 public native `Axes.violin`에 전달하여 기존 wrapper/명시 flag와 native inner 색상·span 묶음을 재fit 없이 유지합니다. 확장/가중/split/named inner는 선언한 정규화를 유지합니다.

## 실제 native component

| Inner | 허용 role | 의미 |
| --- | --- | --- |
| 모두 | body | 채운 profile collection·윤곽·alpha·제한된 hatch |
| legacy | mean, median, extrema | 기존 show flag가 제어하는 native 통계 segment |
| box | whisker, box, median | 관측 Tukey whisker·Q1-Q3 trunk·실제 중앙값 glyph |
| quart | quartile | 실제 가중/비가중 분위수 span3개 |
| point | point | 양의 가중 관측 각 행 한 번 |
| stick | stick | 실제 행별 local profile-width segment |
| None | body만 | inner를 만들지 않음 |

공유 `ComponentStyleSpec`의 유한 속성 vocabulary를 사용합니다. Segment role은 marker 전용 속성을 거부하고 box median/point는 실제 glyph 속성을 받습니다. Box/boxen도 새 violin 전용 role을 몰래 무시하지 않고 거부합니다. 적용 가능한 legacy 통계 component는 flag=None일 때 표시를 켤 수 있지만 명시 False와 충돌하면 거부합니다. Mean/CI/outlier 관측을 발명하지 않습니다.

비소유 속성 우선순위는 native/theme → scalar layer → global component → 정확한 hue별 component의 fieldwise merge입니다. Raw key는 `True`와 숫자1을 구분합니다. Override는 중복 없는 알려진 범주형 hue/예약 자리만 받으며 연속 숫자 hue의 값별 override는 거부합니다. Scalar/global/per-hue 소유권 충돌은 native artist 전에 검사합니다.

폭0 dashed component도 실제 segment 좌표·body fill/hatch·독립 요청 glyph를 보존합니다. Native 무선 표현을 사용하고 epsilon 폭·artist 전체 숨김·행 삭제·warning 억제를 쓰지 않습니다. 인수한 minimum 사전 검사는 기존 quart zero-dash 오류를 재현하지 않았으므로 이를 수정한 버그라고 주장하지 않습니다.

## 공유 hue·물리 SIZE·STYLE

`SemanticSpec`과 같은 strict dict를 지원합니다.

- HUE는 **BODY fill만** 소유하며 범주/숫자 매핑과 raw label은 기존 원본 행 domain pool을 공유합니다.
- SIZE는 **BODY 윤곽 stroke point만** 소유합니다. Profile 폭·확률/질량·inner stroke·marker 지름을 바꾸지 않습니다.
- STYLE은 **BODY named dash**와 point/box 모드의 **실제 관측/중앙값 glyph**만 소유합니다. 저장된 markers cycle은 기본 cycle도 항상 적용합니다. Dash-only legacy/quart/stick은 쓰지 않는 marker cycle 개수를 요구하거나 guide glyph를 발명하지 않습니다.

다른 inner/mean 지름·edge/face·segment 스타일은 독립입니다. 매핑한 body fill/폭/dash·실제 inner marker를 scalar/global/per-hue가 덮으면 거부하며 무해한 whisker/quartile/stick 속성은 허용합니다. Named marker는 circle 흉내가 아닌 실제 native glyph입니다.

Guide는 실제 body/glyph 속성의 violin 모양 native handler이며 scatter 면적/box proxy가 아닙니다. 관측 dataLim을 갱신하지 않습니다. 공유 domain에서 원본 행은 중복 제거하지만 다른 layer가 그리는 물리 instance는 따로 남깁니다. 기존 logical primary+y2 colorbar intent·중복 제거를 재사용합니다.

## 좌표·live·상한

적용 가능한 v/h·primary/y2·numeric-native/log category·category/measurement clock을 지원합니다. 실제 y/y2 target을 먼저 해결합니다. 시간 좌표는 canonical UTC day/선언 label clock이며 물리 stroke나 범주 비율을 날짜/밀도로 해석하지 않습니다. Log 관측/clip은 양수여야 합니다. `stat_scale='data'`는 raw, `axis`는 기존 log10 working 통계 후 한 번 역변환합니다. N12 base2/subs는 표시/눈금이며 통계 단위를 바꾸지 않습니다. Raw primitive의 symlog/asinh/logit 지원에서 violin 통계를 추정하지 않습니다.

`axis='y2'`는 먼저 `.secondary_yaxis(...)`를 선언해야 합니다.
실제 보조축 설정이 없으면 primary에 몰래 그리지 않고 거부합니다.

Live는 기존 단일 recipe와 materialized view를 재사용합니다. Selector·해결한 order·cell ID는 고정됩니다. Local edit는 local이고 이후 명시 `SetFacetTemplate` 전체 교체가 이전 override를 덮습니다. 재열기 때 저장 view가 진실이며 recipe 존재만으로 재렌더하지 않습니다. SetData는 예약 셀을 채울 수 있지만 selector를 늘리거나 excluded 행을 파싱하지 않습니다. 새 filtered/reserved-empty view는 fit하지 않되 옵션/참조/상한은 검증합니다. 기존 unfiltered all-missing 정책은 유지하며 새 mapper나 G01 전체 종결이 아닙니다.

새 advanced 상한은 layer별 **선택 source10000행 AND 그리는 profile256개**입니다. 범주형 category/hue/size/style level·override entry는64이며 연속 숫자 hue/size의 서로 다른 값은64로 제한하지 않습니다. Support2..1000·point/stick 전체 선택 행 보존을 유지합니다. 이 envelope의 Gaussian kernel term은 layer별 최대10M입니다. 실제 사전 time/tracemalloc 측정은 RSS/SLA가 아닙니다. Native Path에는 backend closure vertex가 추가되므로 support 산술을 엄격한 Path 길이 상한이라고 주장하지 않습니다. Facet64/figure256panel/1024layer·pixel 상한을 유지하고 큰 좌표/native 작업 전에 admission을 검사합니다. 상한 확대/몰래 sampling은 없습니다.

## Editor·출력·검증 계보

두 local frontend의 registered layer JSON/RAW action으로 ViolinSpec·역할·component·whole-template transaction을 편집합니다. 잘못된 요청은 인수 Spec/PNG/history를 보존하고 undo/redo·다운로드·reopen·재열기 후 edit도 같은 reducer를 사용합니다. 실제 표시 PNG revision decoded RGBA와 현재 cache의 일치를 검증합니다.

Rust PNG 다운로드는 기존 capped preview입니다. 같은 다운로드 JSON의 정확한 요청 DPI PNG는 설치 CLI/API로 생성하고 SVG/PDF는 실제 vector 출력입니다. Current/minimum driver·native reference·bridge는 같은 고정 wheel과 source-unset origin을 사용하며 Python-S는 optional dependency를 적극 차단합니다. 독립 수치/native/실제 이전 engine·양쪽 UI·실제 PGF/glyph/citation/URI 근거와 실패/교정 cohort를 분리해 기록합니다. 넓은 F01/F02/G01·제품 전체 검증은 여전히 남습니다.
