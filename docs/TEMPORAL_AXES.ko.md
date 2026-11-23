# 명시적 시간축 (v2 진행 중)

[English](TEMPORAL_AXES.md) · [F02 범위](V2_SCOPE.ko.md)

시간축을 명시하지 않은 날짜 문자열은 기존 범주형 동작을 유지한다.

```python
import mudplot as mp

p = (
    mp.plot({"time": ["2026-01-01", "2026-01-02", "2026-01-11"],
             "signal": [2, 3, 4]})
    .line("time", "signal", marker="o")
    .date_axis("x", timezone="UTC")
    .labels(x="Observation date (UTC)", y="Declared signal")
)
p.save("temporal.svg", layout_policy="smart")
```

간격은 균등한 범주 두 칸이 아니라 1일·9일이다. 원본 값·ISO offset 표기·행 순서·
의미 열을 보존하며, 파생 좌표로 저장 데이터를 대체하지 않는다.

## 시간과 단위

- ISO calendar date/datetime과 고정 UTC offset을 지원한다. Aware 값은 실제
  instant로 비교한다. Naive 값에는 `timezone="UTC"` 또는 `"+05:30"` 같은
  고정 offset을 명시해야 한다.
- timezone을 생략하면 aware 입력만 받으며 UTC로 표시한다. 호스트 로컬 zone을
  추측하지 않는다. IANA zone·leap second·미지의 negative-zero offset·지원하지
  않는 ISO 형식은 명확히 거부한다.
- 숫자 timestamp에는 `unit`(`s/ms/us/ns/day`)과 ISO `origin`이 모두 필요하며
  값의 크기로 추측하지 않는다.

```python
import mudplot as mp

p = (
    mp.plot({"elapsed": [0, 86400, 864000], "signal": [2, 3, 4]})
    .scatter("elapsed", "signal")
    .date_axis("x", unit="s", origin="2026-01-01T00:00:00Z")
)
p.save("numeric_clock.svg")
```

- 그림·통계 좌표는 항상 1970 기준 UTC day이다. Matplotlib의 전역 epoch를
  변경하지 않으며 그 설정에 따라 통계 원점이 바뀌지 않는다.
- 밀도는 시간 관측 차원마다 day당 값이다. 숫자 축 한계와 literal geometry
  위치도 입력 timestamp 단위가 아니라 이 canonical day 좌표다.
- dependency-free `mp.temporal_coordinates(values, ...)`로 한계·기준 사건·주석
  위치의 day 값을 명시적으로 계산할 수 있다.
- microsecond까지 지원한다. 추가 소수의 0은 허용하지만 더 미세한 비영 정보,
  달력 범위 초과, float day 좌표 정밀도 손실은 조용히 자르지 않고 오류를 낸다.
  숫자 float의 microsecond 대표값은 원래 숫자 값으로 왕복해야 한다.
- 큰 정수의 low bit와 원본 offset 표기를 포함한 입력은 그대로다. 변환은
  파생 view이며 원본 덮어쓰기가 아니다.

## 연결된 경로

현재 Cartesian linear x/y/y2의 해당 raw line/scatter/strip/bar/errorbar/band/
hexbin/stackplot/rug, native stem/stairs/event/interval,
bar/point/count/line 추정, box/violin/boxen/swarm, hist/KDE/ECDF,
회귀·hist2d/KDE2D 경로에 연결했다. 수평 방향과 활성화된 y2를 구분하며 기존의
관련 없는 주축 제한은 유지한다.

날짜 범주는 실제 시간 간격으로 배치한다. 자동 감지한 패싯 슬롯에는 각 UTC 시각의
첫 적격 원문 표기를 저장한다. 저장된 순서와 명시한 순서는 시각을 기준으로 적격
행을 선택하며, 관측이 없는 시각도 예약할 수 있다. 명시한 중복 시각은 거부한다.
원본 표기와 패싯 선택자는 그대로이며, 같은 시각의 행은 원래 predictor별 통계를
계산하는 마크에서만 집계한다. 절대 날짜 응답은 mean/median/min/max를 지원하며
sum/count로 만들지 않는다.
Residual·logistic 출력은 달력 응답 축으로 표시하지 않으며 시간 predictor는 유지한다.
기본 hist/KDE 호출은 기존 설정과 관측값을 유지한다. Tick은 선언한 timezone의
local midnight를 따르지만 데이터 좌표는 UTC instant로 유지한다.

개수·확률·밀도 축을 달력으로 바꿀 수 없다. 시간축은 linear Cartesian 축이며,
연결하지 않은 계열은 날짜를 ordinal로 그리면서 지원한다고 표시하지 않고 거부한다.

숫자 bins/clips는 canonical day 단위다. ISO histogram 경계와 일변량 KDE/violin
clip은 선언한 timezone 계약으로 변환하며 ISO·숫자 혼합은 거부한다. 이변량 bounds 등
다른 설정은 문서화된 숫자 day 좌표를 사용한다. Stairs는 ISO 경계를 받을 수 있으며
제공한 높이를 다시 추정하지 않는다. Event offset/length, stair baseline,
interval band geometry는 literal 축 좌표를 유지한다.

절대 uncertainty 끝점은 같은 clock을 사용한다. 숫자 timestamp의 오차 열과
interval 기간은 명시한 입력 단위에서 day로 변환하되 **origin을 더하지 않는다**.
ISO timestamp의 오차 크기·기간은 day다. 3600초 오차는 한 시간이지
origin+한 시간이 아니다. 원본 열은 그대로이며 부호·정밀도·누락 열 오류는 저장 전에 보고한다.

## 선택과 공유

Facet 선택·타입 구분 raw group 순서·semantic hue/size/style 순서·필수 결측·해당
0 가중치를 파싱 전에 적용한다. Facet은 기존처럼 유효한 완성 template이 필요하다.
제외 행을 무효로 만드는 축 제한은 facet 선택 후 활성화한다.

좌표 별칭은 원래 hue/size/style/group 열과 선택 행 ID를 보존한다. 같은 열이 시간
좌표와 의미 역할을 겸해도 같다. 공유 축은 시간축 여부와 실제 표시 timezone이
일치해야 하며, 다른 입력 단위·origin이 같은 canonical day 축을 나타내는 것은 가능하다.

## 보조 y축

수직 `hist()`·`kde()`·`ecdf()`는 `axis="y2"`를 받는다. 관측값은 선언한 시간축을
포함한 공유 x축을 사용하고, 숫자인 개수·확률·밀도만 y2로 옮긴다. Typed 분포의
응답 축은 기존처럼 linear여야 한다. 수평 분포는 y2로 옮기지 않으며 개수·확률·밀도
축을 시간축으로 만들 수 없다.

```python
p = (
    mp.plot({"time": ["2026-01-01", "2026-01-02", "2026-01-11"],
             "signal": [2, 3, 4]})
    .line("time", "signal", marker="o")
    .secondary_yaxis("Observation density (day⁻¹)")
    .hist("time", bins=3, stat="density", axis="y2", alpha=0.25)
    .date_axis("x", timezone="UTC")
)
```

투명도는 명시적으로 지정한다. 불투명한 y2 면은 주축의 선·범례를 가릴 수 있으며
예제는 기존 레이어 순서를 바꾸지 않는다. Semantic scatter는 지원하는 명시 clock
y2 경로를 유지한다. Raw line/lineplot은 numeric/date 또는 선언 categorical
predictor를 v/h의 실제 primary/y2에 연결한다. [Line 계약](LINE_WORKFLOW.ko.md)을
참고하라. Complete-unit 달력 추론의 deviation은 UTC day이며 log10 fit도 표시하는
좌표는 역변환한 raw 응답값이다. 표시 base와 구별한다. C02–C07 분포/추정 계약과
D01 line facet의 구체적 보조 축 경로를 허용하고 관련 없는 guard는 유지한다.
이 increment로 넓은 F01/F02/D06이 끝나는 것은 아니다.

## Joint·pair grid

`joint()`는 template에 선언한 clock을 관측값 marginal 축에만 복사한다.
`pair()`는 변수별 clock을 명시한다.

```python
import mudplot as mp

source = {"time": ["2026-01-01", "2026-01-02", "2026-01-11"], "signal": [2, 3, 4]}
joint = mp.plot(source).scatter("time", "signal").date_axis("x", timezone="UTC").joint(bins=3)
pair = mp.plot(source).pair(["time", "signal"], temporal={"time": {"timezone": "UTC"}}, bins=3)
```

각 선언은 `TemporalSpec`이나 엄격한 dict이며 `date_axis()`와 같은
timezone/unit/origin 규칙을 따른다. 미선언 변수는 숫자로 유지하며 ISO 문자열로
추측하지 않는다. 그룹 선택 후 파싱하고 pair 결측 선택은 cell별로 유지한다.
밀도 축은 숫자다. Hist/KDE/ECDF marginal·diagonal도 같은 clock을 쓰며 기존
kind별 제약을 유지한다(KDE/ECDF는 기본 `bins=20`). `SetPairGrid.temporal`로
JSON/action에 연결하며 기존 기본 action에는 필드를 덧붙이지 않는다.

`python examples/temporal_grids.py --out artifacts/temporal_grids`는 재개방 JSON과
PNG/SVG/PDF를 생성한다. Day당 밀도를 명시하고 전체 ISO tick을 위한 넓은 교육용
그림을 사용한다. 출판 크기·실물 인쇄 적합성을 검증했다는 뜻은 아니다.

## JSON·action·편집

`TemporalSpec`은 선택적 `AxisSpec.temporal`이다. 미설정 값은 생략하므로 기존
`0.1` JSON 왕복에 필드를 덧붙이지 않는다. 새 설정은 새 reader가 필요하다.
`SetTemporalAxis`로 설정·해제하며 해제하면 기존 동작으로 돌아간다.

```json
{"type":"SetTemporalAxis","axis":"x","temporal":{"timezone":"UTC","unit":null,"origin":null},"panel":0}
```

실제 Chromium/Rust에서 ISO 생성→숫자 unit/origin/timezone 편집→raw
SetTemporalAxis→undo/redo→download JSON 재개방→PNG/SVG/PDF를 검사했다.
잘못된 선언은 상태·preview를 보존한다. Checkout 밖 설치 wheel에서도 시간축
생성·JSON/action·CLI 렌더를 검사했다. [Core 근거](review_evidence/v2_temporal_core.json)를 참조한다.

F02 전체는 **미완료**다. Raw/native·ISO joint/pair와 위의 y2 부분집합은 수치
기준과 실제 편집·재개방·내보내기를 검사했다.
[Grid 근거](review_evidence/v2_temporal_grids.json)와
[y2 근거](review_evidence/v2_temporal_secondary.json)를 참조한다.
N01–N06·G02/G03·F01/D06의 더 넓은 기능은 계속 필수다. ECDF의 추가 의미 매핑과
이변량 누적 분포도 남아 있다. 제외나 임의 후속 버전 이관이 아니다.

[실행 가능한 합성 예제](../examples/temporal_axes.py):

```sh
python examples/temporal_axes.py --out artifacts/temporal_axes
```

불규칙 신호·day 밀도·이중 y축 overlay를 PNG/SVG/PDF·재개방 JSON으로 만든다. Smart 배치는 명시적
opt-in이다. 실제 원본 실험 데이터·실물 인쇄 검증은 주장하지 않는다.

### Discrete 히스토그램 단위

`hist(..., bins="discrete")` (또는 기본 bins에서 `discrete=True`)의 숫자
시간은 canonical day가 아니라 **선언한 입력 단위 하나**(`s`, `ms`, `us`,
`ns`, `day`)를 쓴다. ISO/date 관측값은 표시 clock의 자정이어야 하며
1일을 쓴다. 소수 관측값·안전하지 않은 격자·정확히 표현 불가능한 반 단위
경계(us/ns 포함)는 반올림이나 jitter 없이 거부한다. 연속 시간 관측에는
이름 규칙 또는 명시적 경계를 사용할 수 있다. 원본 값·단위·순서를 보존하며
epoch 변경이나 renderer 교체는 없다.

### N12 명시 눈금의 정밀도 경계

명시 N12 TickSpec date/auto/concise는 canonical `1970 UTC+timedelta(days)`
와 선언한 fixed clock을 공유합니다. 2100년의 허용된20/21µs를 합칠 수 있는
native num2date에 맡기지 않습니다. Fixed auto/subsecond는 날짜+6자리,
concise는 calendar/fixed 위치에서 Matplotlib3.8 유한 level/zero/offset/
trailing-zero 정책입니다. 출처·전체 license·변경 요약은 패키지의
`_matplotlib_notice.txt`에 포함합니다. Native grid float collapse는
명확한 오류이며 가짜 위치를 만들지 않습니다.

Fixed 위치·Unix seconds 변환은 source unit/origin이 아닌 UTC1970일입니다.
Global epoch·기존 no-N12 정책은 유지하며 F02 전체 완료가 아닙니다.
[N12 계약](FEATURE_COVERAGE.ko.md)·[실행 예제](../examples/axis_controls.py)를 참조하십시오.
