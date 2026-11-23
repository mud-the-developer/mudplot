# 회귀 추론과 원행에 정렬된 진단

*[English](REGRESSION.md)*

기존 `regplot` layer에 opt-in `RegressionSpec`/strict dict 설정을 추가했습니다.
`regression=None`인 기존 polynomial 렌더러는 유지합니다. `residplot`은 fluent
alias이지 새 layer 종류가 아니며 원래 관측을 덮어쓰지 않습니다.

## 필요한 effect만 설치

```bash
# Unreleased source checkout 기준이며 예전 공개 v1.0.0 wheel의 기능이 아닙니다.
pip install '.[render]'      # polynomial, residual, log-x
pip install '.[regression]'  # Huber, binomial logit, LOWESS 추가
```

Advanced extra에 statsmodels>=0.14.1을 추가하며 기본 `mudplot`의 필수 의존성은
여전히 없습니다. `all`/개발 extra는 advanced 회귀를 포함합니다. Pure 구성/검증/
JSON/action 재생은 NumPy/statsmodels를 import하지 않습니다. Extra 없이 advanced
렌더를 요청하면 설치 오류를 명확히 알리고 기존 출력/editor 상태를 보존합니다.

## 모델

```python
p = mp.plot(raw).regplot("x", "y", regression={"model": "robust"})
r = mp.plot(raw).residplot("x", "y", degree=2)
l = mp.plot(binary).regplot("x", "y", regression=mp.RegressionSpec(model="logistic"))
s = mp.plot(raw).regplot("x", "y", regression={"model": "lowess", "frac": 0.4})
```

| 모델 | 의미 | 주요 제한 |
| --- | --- | --- |
| `poly` | Degree1–10 다항식 기준손실 적합 | 전체 basis·절편 하나·partial normal 근사 또는 명시적 paired-case percentile |
| `logx` | 자연로그 ln(x)에 대한 선형 response | 양수 predictor·degree1·표시 log base 및 log(y)와 별개 |
| `robust` | 기존 비가중 RLM 또는 가중 MAD0 Huber | Degree1·50회 제한·아래의 scale/미수렴 규칙 |
| `logistic` | 이진 logit 기준손실 | Numeric0/1 두 class·degree1·100회·trial/frequency 공분산 의미가 아님 |
| `lowess` | 고정 frac 국소 선형 smoother | 물리적 원행 이웃·서로 다른 x3개 이상·frac (0,1]·잔차 반복0–20 |

`frac` 기본 2/3, `iterations` 기본 3은 LOWESS 전용이며 다른 모델의 nondefault
값은 무시하지 않고 거부합니다. 이웃 행이 2개 이상이어야 합니다. Typed 회귀는
layer의 선택 행 10000개, LOWESS는 group당 5000개로 제한합니다. 선택한 좌표의
결측/비유한값·특이 design은 거부하고 기존 panel selector/hue order 뒤에 fit합니다.

Typed fit은 선형대수 전에 predictor/response를 scaling하고 원래 좌표로 되돌립니다.
비유한 예측·분리·미수렴·표현 불가 residual은 regularization/jitter/가짜 fit 없이
오류로 처리합니다. 정확한 직선은 이미 Huber 최소이므로 가짜 MAD scale이 필요
없습니다. Log 좌표축은 입력/예측이 양수여야 하며 residual y축은 linear입니다.

## 상대 기준질량과 명시적 신뢰구간

```python
p = mp.plot(raw).regplot(
    "x", "y", weights="mass", confidence=95,
    regression={"model": "poly", "bootstrap": {"n_boot": 399, "seed": 17}},
)
```

`weights`는 원자료의 상대 기준질량이며 sampling probability나 trial count가
아닙니다. Poly/log-x는 sqrt(relative mass)로 가중 제곱손실을 최소화합니다.
가중 Huber/LOWESS도 점적합과 CI에 같은 일반 가중 연산자를 사용하며, CI를 켜는
것만으로 점추정량을 바꾸지 않습니다.

유일한 coverage는 `Layer.confidence`입니다. 명시적 `bootstrap`은 predictor,
response, nuisance, 원래 질량과 원행 위치를 함께 나르는 **물리적 행의 균등 IID
paired bootstrap**입니다. 기본 n_boot1000·범위1–100000·seed0/비음수 정수는
이름 영역일 뿐 모든 행×반복×grid 조합을 허용하는 자원 보장이 아닙니다.
모든 B를 유지하고 필요한 replicate 하나라도 특이/분리/미수렴/비유한/정의불가이면
전체 percentile 결과를 거부합니다. 재추출·finite-only percentile·B 축소는 없습니다.
순서는 replicate-major이며, 곡선은 양의 질량을 갖는 선택 training 또는 query의
첫 원래 물리적 행 순서입니다. 그 안에서 training/query를 추출합니다.
앞선 0질량 행이나 표시 hue 순서는 이 실험의 추출 순서를 바꾸지 않습니다.

유한 binary64 예측의 공통 exact type7 경계입니다. **명목상 점별 추정량/연산자
불확실성**이지 동시/연속곡선 coverage나 새 관측의 prediction interval이 아닙니다.
독립·대표 물리적 관측과 식별 가능한 안정적 적합 등 가정이 필요합니다. LOWESS는
고정 smoother의 불확실성으로 smoothing bias를 없애지 않습니다. 실제 경험적 atom은
폭0일 수 있지만 모집단 확실성을 증명하지 않으며, 양수 구간의 native 붕괴는 오류입니다.
생략한 설정의 기존 점적합/비가중 poly/log-x 정규근사는 유지합니다.

가중 Huber는 threshold1.345 손실과
`s=Q_left,w(abs(residual),0.5)/Phi_inverse(0.75)`를 번갈아 갱신합니다.
Scale은 바뀌는 IRLS 질량이 아니라 **원래 canonical 질량**을 사용합니다.
계수와 상대 scale이50회 안에 함께 수렴해야 합니다. MAD0인데 비영 잔차가 있으면
정의불가이며, 정확한 경험적 직선만 합법적인 scale0입니다. 가짜 epsilon은 없습니다.
짝수 N의 관측 CDF-left는 낮은 중앙값이어서 비가중 평균 중앙값과 다를 수 있습니다.

가중 LOWESS 이웃은 질량 합이 아닌 원행으로 정의합니다.
`k=min(N,max(2,int(frac*N+1e-10)))`의 kth 거리 h, 경계 tie의 tricube0,
`[1,(x-t)/h]` 국소 설계와 기준×kernel×robust 질량을 사용합니다. 원래 질량의
잔차 중앙값으로 bisquare를 갱신하고, 중앙값0은 정확한 영 잔차 limit을 씁니다.
반경0·부족한 국소 rank·양수 질량 소실·비유한 예측은 fallback 없이 거부합니다.
기존 비가중 provider와 모든 퇴화/짝수 표본에서 같다고 주장하지 않습니다.

## Partial·명시적 hold-out·독립 residual trend

`regression.partial={"columns":["z"],"reference":{"z":0},"method":"joint"}`는
원래 nuisance reference의 조건부 곡선을 지정합니다. Poly/log-x는 **전체 basis**와
절편 하나를 사용합니다. FWL은 원래 x를 잔차화한 뒤 제곱하는 것이 아니라 모든
basis 열과 y를 잔차화하고 전체 model rank/잔차 DF를 사용합니다.
Huber/logit은 joint 조건부 모델이지 비선형 FWL이 아닙니다. LOWESS는 명시적
`method="two_stage"`로 predictor와 response nuisance projection을 모두 적합하고,
잔차 좌표를 smooth한 뒤 response projection을 add-back합니다. 각 replicate에서
모든 nuisance 단계를 다시 적합합니다.

기본 partial 관측은 **원래 predictor축**의 `y-m(x,z)+m(x,z_ref)`이며 잔차화한
x가 아닙니다. Logit 조정값은[0,1] 밖일 수 있어 원래 Bernoulli 관측이라 부르지
않습니다. Query 예측은 reference 대체값이 아니라 각 query의 **실제 nuisance**를 씁니다.

`sampling={"train":{"split":"train"},"query":{"split":"query"}}`는 기존 typed
동등 selector 언어(각2열 이하)의 서로 겹치지 않는 원행입니다. 묵시적 complement/
random split/임의 ID join은 없습니다. 예측 전용 query는 y가 없어도 되지만 요청한
raw/deviance 진단에는 실제 y가 필요합니다. 필요한 training/nuisance 입력은 엄격히
검사하며 결측을 묵시 삭제/대체하지 않습니다. 명시적 panel dropna는 호출자 결정입니다.
질량0 행은 원자료에 남고 적합/추출/glyph에는 참여하지 않습니다. 빈 예약에 가짜
적합/guide를 만들지 않으며, training group이 없는 양수 query는 오류입니다.

`residplot`은 기존 residual flag를 유지합니다.
`diagnostics={"kind":"raw","trend":{"model":"lowess","frac":0.8,"iterations":1}}`
처럼 독립 연속반응 trend를 지정할 수 있습니다. `"kind":"deviance"`는 binomial-logit
전용이며 y1은 `sqrt(-2*log(p))`, y0은 `-sqrt(-2*log1p(-p))`입니다.
p0/1이 관측과 일치하면0, 불일치하면 진짜 무한대입니다. 유한 native 요청은 원행
위치와 함께 거부하며 clip/삭제/가짜0을 만들지 않습니다. Zero reference는 하나입니다.

고정 관측의 진단 구간은 **평균반응 type7 구간[L,U]를 먼저** 구한 뒤
raw `[y-U,y-L]` 또는 deviance `[g_y(U),g_y(L)]`로 사상합니다.
진단 replicate를 변환한 뒤 type7한 값이나 미래 오차 분포가 아닙니다.
별도 trend는 primary+nuisance를 재적합하고 재추출 관측의 잔차로 trend도 재적합하는
**FULL pipeline** percentile입니다. OOS는 매 replicate에서 train 후 query를 독립
추출하며 query y는 primary를 학습하지 않습니다. In-sample에는 두 번째 query draw가
없고 명시적 empty query를 in-sample로 바꾸지 않습니다.

`components`의 fit/scatter는 기존 ComponentStyleSpec의 실제 stroke/marker/지름/
fill/alpha만 소유합니다. Trend style은 독립입니다. 표시/제목/guide/DPI 편집은 선언한
실험을 바꾸지 않습니다. 원자료/typed ID/중복과 native 원행 연결은 action/history/
download/reopen에 유지되며 별도 results API나 stale 계산열/store는 추가하지 않습니다.

## 적합과 독립인 점의 의미 매핑

`regplot` 또는 `residplot`의 `semantics=SemanticSpec(...)`는 실제 관측,
부분 조정 관측, hold-out 예측 및 진단점의 채우기 색·지름(pt)·마커를
매핑합니다. 숫자 hue에는 `colorbar=True`로 원시 값 눈금을 표시할 수 있고
`scatter`와 같은 `scale_id`로 눈금을 공유할 수 있습니다. 스타일은 점
마커이며 대시가 아닙니다. 테두리와 굵기는 독립입니다.

역할 값은 날짜로 변환된 좌표가 아닌 선택한 원본 행에서 읽습니다. 값이
없거나 명시 순서에서 제외되면 해당 점만 숨깁니다. 표시를 끈 점과 기준
질량이 0인 행은 눈금에 포함하지 않습니다. 의도적으로 지름을 0으로
매핑할 수 있으며 그 값은 눈금 계산에 남을 수 있지만 범례 기호는 만들지
않습니다. 양의 지름의 면적이 네이티브 표현에서 0으로 사라지면 거부합니다.

`group`, 레이어 `hue_order`, R4의 학습/질의 선택자·기준 질량·모델은
그대로 적합을 결정합니다. 매핑으로 적합, 신뢰구간, 잔차, trend 또는
기준선이 바뀌지 않습니다. 실제 점 속성을 매핑과 컴포넌트 양쪽에서
지정할 수 없고 적합 선·오차의 독립 스타일은 유지합니다. 기본 축,
설정된 Y2 및 지원되는 고정 패싯에서 동작합니다. `semantics`를 생략하면
기존 점 표시를 사용합니다. [실행 예제](../examples/regression_glyphs.py).

## 실제 좌표와 유한 자원 경계

Logical x는 predictor, y는 response입니다. v/primary=X/Y, v/y2=X/Y2,
h/primary=Y/X, h/y2=Y2/X로 실제 축을 사용합니다. Raw 적합/자연로그는 표시 log
base와 별개입니다. 날짜 predictor는 명시적 canonical UTC-day를 쓰며
ln(1970 이후 UTC일)은 origin 의존·양수 전용입니다. Timestamp 예측은 timestamp이고
날짜 response의 residual/trend duration은 날짜 formatter로 위장하지 않고 거부합니다.

기존 typed 선택 행10000/LOWESS group5000/degree/반복/native 제한은 유지합니다.
NEW 전체 design은19열 이하이고 실제 invocation/figure 합산 logical upper
work는6,000,000,000 이하입니다. 원래 점적합·전B·query/nuisance/trend·실제 gather/
이웃/중앙값/evaluation/tail 및 가변 seed변환 w*w를 RNG/native 전에 계산합니다.
Residual-only에서 쓰지 않는 primary fit grid를 만들지 않습니다.

268,435,456B는 실제 numerical plan/buffer, canonical CDF bigint, tail heap과
동시에 사는 한 vector의 ordered/sign/interpolation scratch, controls와 먼저 유지한
summary를 포함하는 **보수적 managed/provider-reserve admission estimate**입니다.
RSS/native artist/모든 opaque provider allocation의 보장이나 CPU/SLA가 아닙니다.
알려진 초과 요청은 B/grid/원행을 줄이거나 기존 생략 경로 admission을 바꾸지 않고
거부합니다. 실패 시 승인된 상태와 이전 native 출력을 보존합니다.
소비하는 열의 view는 layer마다 한 번 준비합니다. 기존 원자료/spec 값과 group
표시는 빌린 참조이므로 NEW 할당처럼 재귀 합산하지 않고, 새 view container·
날짜 좌표·행 위치 bookkeeping만 계산합니다. 뒤 layer의 초과도 포함한 알려진
전체 figure input/plan/stage 및 앞선 출력 shape 상한은 첫 RNG 전에 검사하며,
실제 유지된 수치 결과는 native 출력 전에 계속 검사합니다. Sparse panel filter
이후에도 strict 입력/미학습 group 오류는 원래 물리적 행 위치를 표시하고,
0질량은 필수 입력의 strict 검사를 면제하지 않습니다.

## 실행 가능한 그림별 질문

모두 합성 데이터이며 데스크톱 700px를 확인합니다. 독립 가독성 점수나 인과/
모델 선택 주장은 없습니다.

- [Residual](images/regression_residual.png) · [spec](images/regression_residual.mplot.json)
- [Log-x response](images/regression_logx.png) · [spec](images/regression_logx.mplot.json)
- [Outlier 유지 Huber](images/regression_robust.png) · [spec](images/regression_robust.mplot.json)
- [이진 확률](images/regression_logistic.png) · [spec](images/regression_logistic.mplot.json)
- [국소 trend](images/regression_lowess.png) · [spec](images/regression_lowess.mplot.json)

같은 basename의 PDF/SVG도 제공합니다. [소스](../examples/regression_modes.py).

```bash
uv run python -m examples.regression_modes
uv run pytest -q tests/test_regression_models.py tests/test_new_layers.py
```

## JSON/에디터

```json
{"type": "AddLayer", "layer": {"type": "regplot", "x": "x", "y": "y",
 "regression": {"model": "robust", "residual": true}}}
```

알 수 없는 설정은 거부합니다. 기존 editor의 같은 spec/검증 action 경로를 쓰며
spec/package/editor version은 유지합니다. 예전 JSON은 `regression=None`입니다.
독립 statsmodels/NumPy 비교·group/facet residual·극단 단위 scaling·잘못된 요청·
선택 의존성 누락·JSON/action/schema/editor·PNG/PDF/SVG 재현성과 global RNG
비사용을 검사합니다.
