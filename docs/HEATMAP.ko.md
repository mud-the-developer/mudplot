# Typed heatmap 표시 옵션

*[English](HEATMAP.md)*

`HeatmapSpec`은 원래 숫자 행렬을 바꾸지 않고 표시 옵션을 켭니다.
`heatmap=None`인 기존 imshow 기본 동작은 유지합니다.

![합성 mask/주석 heatmap](images/heatmap_controls.png)

[편집 spec](images/heatmap_controls.mplot.json) ·
[SVG](images/heatmap_controls.svg) · [PDF](images/heatmap_controls.pdf) ·
[소스](../examples/heatmap_controls.py)

합성 변화량 예제의 검토 폭은 데스크톱 700px입니다. Mask는 셀을 숨긴 것이지
원자료가 실제 결측이었다는 증거가 아니며 독립 가독성/접근성 인증도 아닙니다.

```python
p = (mp.plot().matrix("m", [[-2, 0, 3], [1, 4, 8]])
       .heatmap("m", cmap_kind="diverging", clabel="Change",
                heatmap={"annot": True, "fmt": ".1f", "center": 0,
                         "mask": [[False, True, False], [False, False, False]],
                         "xlabels": ["A", "B", "C"], "ylabels": ["N", "S"]},
                line_width=0.5, edge_color="#ffffff")
       .size(6, 4))
```

기존 layer의 `heatmap` 필드에 strict `HeatmapSpec` 또는 dict를 넣습니다.
알 수 없는 key는 거부하며 API/AddLayer action/JSON/editor가 같은 spec/reducer/
validator를 사용합니다. 새 layer 종류·필수 의존성·spec version을 추가하지 않습니다.

## Mask와 원래 값

- `mask`는 선택적인 같은 모양의 bool 행렬입니다. True는 해당 셀을 숨기고
  색상 범위/robust percentile/log 양수 조건/주석에서 제외합니다.
- 행렬은 masked 셀까지 유한 숫자여야 합니다(bool/NaN/null 불가). Mask가 잘못된
  입력을 정리하거나 원자료를 고치는 기능은 아닙니다.
- 빈/jagged 행렬, 모양이 다른 mask, 모두 숨긴 view는 일찍 거부합니다.
- `xlabels`/`ylabels`는 열/행마다 문자열 하나(최대 512자)가 필요합니다. 좌표축은
  선형 cell index이며 색상 log scale과 다릅니다.

## 색상 척도

기본 `norm="linear"`, `norm="log"`는 보이는 값과 경계가 양수여야 합니다.
`vmin`/`vmax`는 추론 범위를 덮어쓰는 유한값이며 둘 다 주면 증가해야 합니다.
범위 밖 값도 원자료/주석을 유지하므로 색상 clipping은 데이터 삭제가 아닙니다.

`robust=True`는 보이는 값의 2/98 percentile을 사용한 뒤 명시 경계를 적용합니다.
행이나 통계/관측을 다시 추정하지 않습니다.

`center`는 linear norm과 diverging palette에서만 사용합니다. 없는 경계는 중심
주변 대칭으로 추론하고 명시 경계는 유지하며 중심을 사이에 둬야 합니다.
TwoSlopeNorm이며 순차 척도의 이름만 바꾸는 것이 아닙니다. 상수 범위는 안전하게
확장하고 표현 불가능한 계산 span은 조용히 overflow하지 않고 오류로 처리합니다.
실패 시 기존 출력 파일을 바꾸지 않습니다. Typed colourbar는 명시 경계/값을 써서
아주 큰 유한값과 아주 작은 log 범위에서도 계산을 안정적으로 유지합니다.

## 주석·경계·모양

`annot=True`는 정규화/log 비율이 아닌 **원래** 보이는 숫자를 표시합니다. `fmt`는
기존 bounded 숫자 whitelist인 `g`/`.0f`/`.1f`/`.2f`/`.3f`/`.1%`/`e`/`.2e`만
지원하며 최대 4096개의 보이는 셀에 주석을 달 수 있습니다. 큰 grid는 주석을 빼거나
작은 view를 선택하세요.

글자색은 이 이미지의 colormap과 alpha가 적용된 axes 배경에서 검정/흰색 중 대비가
강한 쪽을 선택합니다. 임의 overlay·글꼴 판독·모든 접근성 조건을 평가하는 것은 아닙니다.

`square=True`는 셀의 x/y aspect를 같게 하며 전체 그림이 정사각형일 필요는 없습니다.
기존 `line_width`/`edge_color`는 point 단위 셀 경계이며 무시되지 않도록 HeatmapSpec이
있을 때만 허용합니다. `colorbar`/`clabel`·font/theme·크기와 기존 패널 설정은 유지합니다.

## 재현·편집

```bash
uv run python -m examples.heatmap_controls
uv run pytest -q tests/test_heatmap_options.py tests/test_layers.py
```

편집 예제를 에디터에서 열거나 advanced 폼으로 heatmap layer를 추가합니다. 행렬과
설정은 그대로 왕복합니다. 행렬 모양을 바꾸면 mask/label도 갱신해야 하며 잘못된
import/action은 기존 원자적 검증/렌더 경로로 현재 상태를 보존합니다.

사용자 지정 annotation 행렬·clustering·범주/date cell 좌표·추가 norm 종류는
이번 범위 밖입니다. 최종 크기와 배치를 직접 확인해야 하며 자동 글꼴/경계 검사는
미적 점수가 아닙니다.
