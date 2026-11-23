# Box 원자료와 제공한 요약값

[English](BOX_WORKFLOW.md) · [전체 실행 예제](../examples/box_workflow.py)

C03은 기존 `box` layer를 확장합니다. `Plot.bxp`는 같은 layer의 명시 columnar-summary
모드이며 별도 renderer나 임의 kwargs 모음이 아닙니다. Package 1.1.0·schema 0.1을
유지하고 넓은 F01/F02/G01·최종 제품 검증의 완료를 뜻하지 않습니다.

## 원자료 중앙값 bootstrap CI

```python
import mudplot as mp

p = mp.plot({"method": ["A"] * 6, "response": [1, 2, 3, 4, 5, 30]})
p.box("method", "response", median_ci={"level": 90, "n_boot": 1001, "seed": 19},
      cap_fraction=0.8, showmeans=True)
p.labels(y="Measured response (mm)", title="90% bootstrap median CI")
```

`median_ci`는 재표본화한 **표본 중앙값**의 percentile CI입니다. 관측값 PI·평균 CI·
whisker 규칙이 아닙니다. `notch=None`이면 명시 CI 요청이 notch를 켜며 `notch=False`와
충돌합니다. Whisker는 독립적인 `whis`의 native IQR/분위수·실제 관측 끝점입니다.

필수 category/value/hue/의미 역할의 결측 행만 함께 제외합니다. 범주×원본 역할 tuple
samplecell 내부에서 원본 관측 행을 복원 추출합니다. Cell마다 저장한 같은 seed의
private `default_rng`를 시작하므로 같은 cohort는 facet/범주 순서와 무관한 공통 추출
index schedule을 사용합니다. 전역 NumPy RNG·원자료·ID·순서는 바꾸지 않습니다.
새 가중/unit bootstrap이나 제공한 사분위수에서 원관측값을 재구성하는 기능은 없습니다.

Level은 `(0,100)`, `n_boot`는 `1..100000`, seed는 기존 통계 정책 그대로 bool이 아닌
음이 아닌 정수이며 숨은 상한을 추가하지 않습니다. 기존 1백만 resampled-element
chunk 목표를 재사용합니다. 선택된 작은 관측값·percentile endpoint를 보존하며 짝수
중앙값 midpoint·underflow 부근 보간의 불필요한 overflow/underflow를 피합니다.
Float64이지 임의 정밀도 보장은 아니며 mean/sum 산술을 새 구현으로 바꾸지 않습니다.

관측값 한 개의 box는 실제 퇴화 분포로 남고 요청한 bootstrap notch만 경고와 함께
생략합니다. Gaussian CI를 대신 만들지 않습니다. 빈 예약 cell에는 box/CI를 만들지
않습니다. Bootstrap을 요청하지 않은 raw box의 Gaussian notch 동작은 유지합니다.

`stat_scale="data"`는 원래 관측 좌표(명시 시간은 절대 UTC-day view)에서 계산합니다.
값축이 log이고 `stat_scale="axis"`일 때만 log10에서 통계를 구한 뒤 native geometry를
한 번 역변환합니다. 저장된 원자료·단위·ID를 변환값으로 교체하지 않습니다.

## 값 복사가 아닌 기존 column 참조

```python
columns = {
    "method": ["A"], "median": [2], "q1": [1], "q3": [3],
    "lo": [0], "hi": [4], "mean": [2.1],
    "ci_low": [1.5], "ci_high": [2.5], "declared_fliers": [[5]],
    "source_id": ["original-summary-row"],
}
q = mp.plot(columns).bxp(
    "method", "median", q1="q1", q3="q3", whislo="lo", whishi="hi",
    mean="mean", cilo="ci_low", cihi="ci_high", fliers="declared_fliers",
    showmeans=True, notch=True, cap_fraction=0.8,
)
```

`bxp(category, median, ...)`는 두 열 box와 같고 `bxp(median, group=category, ...)`는
한 열 value/group 의미와 1-based 범주 위치를 유지합니다. 모든 요약 옵션은 기존
`DataSpec.columns`의 이름입니다. Layer 안에 별도 표/요약값을 복사하지 않습니다.
요약 행이 아닌 원본 행에는 nullable summary column을 둘 수 있으므로 raw/summary
view가 같은 표와 ID를 공유할 수 있습니다.

선택된 범주/실효 hue/원본 역할 tuple마다 요약 행 하나만 허용하고 중복 요약을 평균/
dedup하지 않습니다. 필수 값은 절대 관측 단위로
`whislo <= q1 <= median <= q3 <= whishi`여야 합니다. 필수 결측만 함께 제외하며,
**선택 mean/CI/flier의 결측 때문에 유효 box를 삭제하지 않습니다.**

- Mean 참조/값이 없으면 unavailable입니다. `showmeans=True`는 모든 선택 유효 box에
  제공한 유한 mean이 있어야 하며 median을 대입하지 않습니다. Mean을 box/whisker에
  clip하지 않습니다.
- CI 참조는 쌍입니다. 두 값 모두 결측이면 unavailable, 한쪽만 결측이면 오류입니다.
  `notch=True`는 제공한 유한 순서 있는 두 끝점을 요구합니다. 사분위수에 clip하거나
  표본 중앙값을 강제로 포함시키지 않습니다. 제공한 CI에 level/method를 추측하여
  붙이지 않으므로 실제 계산 방법·수준을 사용자가 정확히 라벨링해야 합니다.
- Fliers는 JSON list-valued column입니다. `[]`는 제공한 flier 없음,
  `None`/참조 없음은 unavailable이지 outlier가 없다는 증거가 아닙니다. 각 값은
  유한하고 닫힌 whisker 구간의 엄격한 바깥이어야 합니다. Summary 기본 표시는
  제공되어 있는 flier만 그리며 `showfliers=True`는 해당 list가 모두 있어야 합니다.

제공한 사분위수에 bootstrap이나 새 `whis`를 요청할 수 없습니다. 명시 category/값
clock은 q/whisker/mean/CI와 중첩 flier 절대값을 실제 primary/y2 대상 축에서 변환합니다.
Log로 보이는 geometry는 양수여야 하며 native/log/date·방향·facet/live는 같은 경계를
사용합니다.

## Cap과 구성 요소 우선순위

`cap_fraction`은 bool이 아닌 유한 `[0,1]`이며 **dodge와 gap 적용 후 최종 body 폭**의
비율입니다. 범주 working 좌표(ordinal/numeric/native log10/UTC days)이지 측정값
단위·pt·밀도·질량이 아닙니다. 0도 퇴화한 native cap artist를 보존합니다. 생략하면
native half-body cap을 유지합니다. 명시 cap fraction은 `components.cap`처럼 cap을
켜지만 관련 없는 숨긴 body를 켜지 않습니다.

Raw box에서 생략한 whis·notch/mean/flier·body/cap 가시성은 effect 경계의 실제
native/theme context를 따릅니다. 명시 layer/CI/매핑한 body 속성/구성 요소는 소유한
제어만 덮어씁니다. Summary의 mean/CI/flier는 ambient rc로 조작해 만들어내지 않고
위 availability 규칙을 유지합니다. Native `showbox=False`여도 실제 whisker/median/
mean/flier는 남으며 가짜 body가 없습니다. Width 0 dash는 Patch fill/hatch 및 독립
Line2D marker를 숨기지 않는 native no-line 표현을 사용합니다.

Hue별 설정은 문자열 강제 변환 kwargs가 아닌 typed list입니다.

```python
styled = mp.plot({
    "category": ["A"] * 4, "response": [1, 2, 3, 4],
    "method": [True, True, 1, 1],
}).box("category", "response", group="method", hue_components=[
    {"level": True, "components": {"cap": {"color": "red", "line_width": 2}}},
    {"level": 1, "components": {"median": {"color": "blue"}}},
])
```

공유 `category_key`에 따라 bool과 숫자는 다르고 동등한 숫자 key 중복은 거절합니다.
관측되었거나 명시 예약한 categorical hue만 허용하며 모르는/중복 key를 거절합니다.
연속 numeric hue를 임의 값별 가짜 bin으로 나누어 재정의하지 않습니다. 한 열 box의
legacy `group`은 **범주**이며 자동으로 독립 hue가 되지 않습니다. 별도 semantic hue는
그 독립 채널을 제공할 수 있습니다.

우선순위는 native/theme → layer shorthand → 소유 semantic 속성 → global components
→ 속성별 per-hue components입니다. 빠진 속성은 상속하고 빈 hatch는 명시 해제입니다.
실제로 매핑한 속성의 override는 guide와 모순되므로 오류입니다. 숨긴 mean/flier 제약은
기존 typed component 규칙을 유지합니다.

## 공유 hue·BODY stroke·실제 flier glyph

기존 `SemanticSpec`/원본 행 domain pool/논리 panel colourbar intent를 재사용합니다.
원본 hue/size/style tuple로 sample을 분할하며 역할 값을 평균하지 않습니다. Domain은
원본 row ID를 dedup하지만 layer마다 실제 통계/point view는 유지합니다.

- **Hue:** BODY face fill만 소유합니다. Body edge·다른 component 색상은 독립입니다.
  Numeric hue는 같은 정규화 nondata colourbar/정확한 raw label/상수 midpoint swatch입니다.
- **Size:** BODY outline linewidth의 물리 pt만 소유합니다. Body 폭/질량/mean·flier 지름/
  whisker·cap·median 선폭은 아닙니다. 다른 속성은 독립적으로 편집합니다.
- **Style:** BODY outline named dash와 실제 FLIER glyph를 항상 매핑합니다.
  직렬화된 `SemanticSpec.markers`의 기본 cycle도 포함하며 Python keyword/dict key의
  생략 여부를 탐지하지 않습니다. 공급한 `dashes` 또는 유한 기본 cycle과 충분한
  서로 다른 dash/marker를 요구하고 flier 관측값을 만들어내지 않습니다.

따라서 매핑한 body fill/linewidth/dash·flier marker의 충돌 override는 거절하지만
무관한 whisker/cap/median 스타일·body edge·독립 mean/flier 지름/edge/face는 허용합니다.
Guide는 실제 native box/line 속성을 사용하며 box를 점 proxy로 위장하지 않습니다.
관측 flier가 없어도 style guide는 해당 flier **매핑**을 명시할 뿐 데이터를 생성하지 않습니다.

두 열 독립 legacy group/hue order나 `c`와 `SemanticSpec`은 함께 쓰지 않고 config의
hue/order를 사용합니다. 한 열 group은 category로 남아 별도 semantic hue와 호환됩니다.
Box의 v/h·numeric/native/log/inversion/date·primary/y2를 연결하며 다른 계열의 미지원
조합을 일괄 허용하지 않습니다.

## 명시 live 편집과 연산 상한

기존 `facet(..., live=True)` / `facet_template(...)` recipe는 고정 selector·slot·저장한
cell view·호환 ratio를 보존합니다. Local 편집은 local이며 나중의 명시 whole-template
교체가 빈 예약 cell을 포함한 대상 전체를 갱신합니다. JSON load는 자동 재생성이 아닙니다.
새 범주 채널에 `order=None`을 보내면 새 수준을 추론하지만 제공한 옛 목록은 문자 그대로
선택 목록입니다. 한 열 범주 identity는 값 x가 아닌 group/category source입니다.

Native artist/bootstrap 할당 전에 새 advanced/summary 요청을 제한합니다.

- Layer당 그려지는 samplecell 최대 **256개**.
- 선택된 source **10000행** 및 별도로 선언한 flier **총 10000값**. 둘 중 하나만
  만족하면 되는 조건이 아니라 독립된 두 상한입니다.
- 기존 semantic10000행/64level/256role-tuple·facet64·figure256panel/1024layer·
  bootstrap100000을 유지하고 curve/depth 상한을 올리지 않습니다.
- 새 제어를 생략한 legacy box의 상한/JSON/기본 geometry는 유지합니다. 새 native
  연산 상한은 profile 근거이지 SLA나 downsampling이 아닙니다.

`python examples/box_workflow.py artifacts/v2_box`로 실행합니다. `.mplot.json`을
`Plot.from_json`으로 다시 열거나 `python -m mudplot render figure.mplot.json figure.svg`를
사용합니다. Rust의 등록된 `box` layer JSON form은 `box.summary`/`box.median_ci`/
`box.cap_fraction`/`box.hue_components`를 편집하고 RAW ACTION은 같은 live/history를
사용합니다. 거절된 편집은 인수한 spec/preview/history를 보존합니다. Rust `/fig.png`는
기존 capped cached preview이고 PDF/SVG는 실제 vector입니다. 같은 다운로드 JSON을
설치 CLI/API로 렌더하면 요청한 원래 DPI의 PNG를 얻습니다.
