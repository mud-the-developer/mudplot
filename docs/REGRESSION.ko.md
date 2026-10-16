# 설정형 회귀와 원자료 residual

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
| `poly` | NumPy polynomial response fit, degree 1..10 | 요청 시 기존 정규근사 평균 fit band만 지원 |
| `logx` | 자연로그 log(x)에 대한 선형 response fit | 양수 x·degree 1; log(y)/logistic이 아님 |
| `robust` | statsmodels RLM의 HuberT loss | Degree 1·최대 50회; outlier를 자동 삭제하지 않음 |
| `logistic` | logit link의 statsmodels GLM Binomial | Numeric y 0/1 두 class 필요·degree 1·최대 100회 |
| `lowess` | statsmodels 국소 선형 smoother | 서로 다른 x 3개 이상·frac (0,1]·iterations 정수 0..20 |

`frac` 기본 2/3, `iterations` 기본 3은 LOWESS 전용이며 다른 모델의 nondefault
값은 무시하지 않고 거부합니다. 이웃 행이 2개 이상이어야 합니다. Typed 회귀는
layer의 선택 행 10000개, LOWESS는 group당 5000개로 제한합니다. 선택한 좌표의
결측/비유한값·특이 design은 거부하고 기존 panel selector/hue order 뒤에 fit합니다.

Typed fit은 선형대수 전에 predictor/response를 scaling하고 원래 좌표로 되돌립니다.
비유한 예측·분리·미수렴·표현 불가 residual은 regularization/jitter/가짜 fit 없이
오류로 처리합니다. 정확한 직선은 이미 Huber 최소이므로 가짜 MAD scale이 필요
없습니다. Log 좌표축은 입력/예측이 양수여야 하며 residual y축은 linear입니다.

## Residual은 deviance나 추론이 아님

`residplot`은 복사한 설정의 `residual=True`를 강제합니다. 원래 행 순서/x에서
**관측 y - in-sample fitted response**와 layer당 zero guide 하나를 표시합니다.
선택한 raw group/facet마다 독립 fit합니다. Out-of-sample 오차·deviance residual·
weights·상관계수·인과 추론·residual 위 추가 LOWESS trend를 뜻하지 않습니다.
Model='lowess'이면 원래 response의 LOWESS fit에서 residual을 구합니다.

Joint 주변 분포는 raw y를 뜻하므로 residual 템플릿은 거부합니다. 일반 설정형
regplot은 기존 데이터/축 제한 안에서 joint/facet 경로를 사용할 수 있습니다.

`confidence=95`는 poly/logx의 명시적 정규근사 평균 fit CI이며 bootstrap이나
전체 곡선 동시 coverage가 아닙니다. Residual/robust/logistic/LOWESS band는
명시적으로 미지원입니다. 추가 fit/scatter control·가중 회귀·bootstrap은 남았습니다.

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
