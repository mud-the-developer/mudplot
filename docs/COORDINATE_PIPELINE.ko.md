# 좌표 변환과 이름 있는 통계 조합

[English](COORDINATE_PIPELINE.md) · [실행 가능한 합성 예제](../examples/coordinate_pipeline.py)

`LayerSpec.transforms`는 이미 그려진 도형이 아니라 논리 입력 좌표에 적용됩니다. 각 뷰는 원본 행을 선택하고, 요청한 좌표를 변환하고, 기존 통계를 계산한 뒤 기존 배치와 패널 표시 축척을 적용합니다. 원본 열, 가중치, 단위 ID, 범주, 의미 매핑은 그대로 유지됩니다.

```python
import mudplot as mp

p = mp.plot({"dose": [1, 1, 10, 10], "response": [1, 10, 10, 100],
             "mass": [1, 3, 1, 3]})
p.pointplot("dose", "response", weights="mass", errorbar=None, native_scale=True,
            transforms=[mp.TransformSpec("y", "log")])
p.axis_scale("x", "log", options={"base": 2}).labels(y="log10 response")
```

첫 추정값은 `log10(7.75)`가 아닌 `(1×0 + 3×1)/4 = 0.75`입니다. 밑 2인 표시 축척은 다른 축에 적용됩니다. 기존 `stat_scale="axis"`는 통계를 계산한 뒤 좌표를 원래 단위로 되돌립니다. 이와 달리 `log` 변환은 밑 10 로그 좌표에 그대로 남으며, 원래 단위에 대한 야코비안을 적용하지 않습니다.

- 단계는 총 1–4개입니다. 한 역할에는 `identity`, `log`, `standardize`, `log` 다음 `standardize` 중 하나를 사용합니다. 각 단계에 `role`과 `name`만 적습니다. 순서를 유지하며 서로 다른 역할의 단계를 섞을 수 있습니다. `None` 또는 생략은 이전 동작과 JSON을 유지합니다. 빈 배열은 오류, 명시적 `identity`는 결과를 바꾸지 않는 의도 표시입니다.
- `log`에는 유한한 양수만 사용합니다. `standardize`는 선택된 뷰에서 앞선 변환을 적용한 값의 모집단 평균·표준편차를 사용합니다. 가중치는 적격 행 판정과 이후 통계에 쓰이고, 보정에서는 각 적격 원행이 한 번씩 기여합니다. 재표집 중 보정값은 고정됩니다. 빈 셀에는 추정값을 만들지 않고, 적격 행의 분산이 0이거나 서로 다른 값의 좌표가 겹치면 거부합니다.
- `barplot`·`pointplot`·`lineplot`에는 숫자 네이티브 예측자 및 측정값에 적용할 수 있습니다. count는 측정값 변환이 없으며 `countplot`은 네이티브 범주 좌표만 변환합니다. `.line()`은 원행의 순서와 간격을 유지하고 추정하지 않습니다. `stripplot`은 `StripSpec` 등 기존 범주형 경로를 사용하고, 네이티브 숫자 범주 또는 숫자 측정값을 변환합니다.
- `hist`·`kde`·`ecdf`의 논리 관측값은 가로 배치에서도 `x`입니다. `hist2d`·`kde2d`·`ecdf2d`에는 `x`, `y`가 있습니다. 비항등 단계에는 이름 있는 histogram/KDE 설정이 필요합니다. 기존 estimators, 커널·대역폭, HDR, 누적/보완 및 스택/dodge/fill의 허용 범위는 그대로입니다.
- 같은 역할에 비항등 단계와 날짜, 로그 표시축, 통계용 축 맞춤을 동시에 쓸 수 없습니다. 다른 역할의 호환되는 날짜나 로그축은 그대로 사용합니다. 호환되지 않는 원래/파생 단위는 동일하거나 공유된 데이터 축에서 혼합할 수 없습니다.
- `bins`, `clip`, ECDF 경계·질의, 축 한계, 기준선과 눈금 위치는 표시 축척 적용 전의 실제 좌표 단위로 적습니다. 범주 `order`, hue, 가중치와 단위 ID는 원본 기준입니다. 밀도는 파생 폭·면적 기준이며 후속 dodge가 높이를 재계산하지 않습니다. strip jitter는 기존 seed와 배치 슬롯을 사용합니다. 새 전역 자원 한도는 추가하지 않습니다.

두 편집기의 등록 레이어 추가 폼에서 **Coordinate pipeline** 도움말을 확인할 수 있습니다. 추가 또는 **Replace layer**의 레이어 JSON에 `"transforms":[{"role":"y","name":"log"}]`를 입력하거나, `null`로 초기화합니다. **Replace layer**는 선택 셀만, **Whole live facet template**은 고정된 전체 셀을 명시적으로 갱신합니다. JSON 다시 열기, 실행 취소/다시 실행에서 선언을 유지합니다.

```sh
python examples/coordinate_pipeline.py /path/to/output
python -m mudplot validate /path/to/output/coordinate-pipeline.mplot.json
```

합성 예제는 편집 가능한 JSON과 PNG·SVG·PDF를 저장합니다. 범위는 O01의 유한한 조합이며 `seaborn.objects` 호환 API나 버전·의존성 변경을 뜻하지 않습니다.
