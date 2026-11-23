# 이름 있는 패널·중첩 grid·mosaic·inset

*[English](PANEL_LAYOUTS.md)*

N13은 미공개 1.1.0 후보/schema 0.1의 opt-in 선언적 배치 기능입니다.
Native Matplotlib GridSpec/subgridspec과 실제 child inset axes를 사용합니다.
순수 builder/action/JSON/검증 core에는 외부 의존성이 없고 render 하한은
NumPy ≥1.23.5 / Matplotlib ≥3.8 / Pillow ≥13.0.0 그대로입니다.
이 기능이 G02/G03의 나머지 semantic·가중·corner·complementary-CDF 또는
전체 v2를 완료했다는 뜻은 아닙니다.

## 생성·편집·다시 열기

```python
import mudplot as mp
p = (mp.plot({"time": [1, 2, 4], "value": [3, 1, 5]})
     .line("time", "value")
     .mosaic([["main", "main", "empty"], ["main", "main", None]],
             width_ratios=[1, 1, 2])
     .nest(1, 2, width_ratios=[3, 1])
     .inset("main", [0.1, 0.2, 0.3, 0.4], panel_id="zoom")
     .line("time", "value", panel=2))
p.place("zoom", {"inset": {"parent": "main", "bounds": [0.2, 0.1, 0.4, 0.4]}})
p.rename_panel("main", "measurement")
p.reorder_panels(["zoom", "empty", "measurement"])
p.store.undo()
p.store.redo()
mp.Plot.from_json(p.to_json()).save("figure.svg")
```

Mosaic은 비어 있지 않은 직사각형 행 목록입니다. 문자열은 안정적 패널 ID,
`None`은 패널 없는 빈 자리입니다. 같은 ID가 차지하는 영역은 직사각형이어야
하며 하나의 span 패널로 정규화됩니다. 반면 비어 있는 PanelSpec은 선택·편집·
내보내기가 가능한 실제 frame입니다. 최초 opt-in에서만 익명 legacy 패널을
첫 출현 순으로 이름에 배정합니다. 이미 ID가 있으면 새 mosaic 이름이 몰래
기존 패널을 바꾸거나 소비하지 않습니다. 기존 ID 전부를 포함해야 하고 새 ID는
새 빈 패널을 만듭니다. 이름 변경·삭제는 명시적 action으로 수행합니다.

`nest(rows, cols, row=0, col=0, row_span=1, col_span=1, grid_id=None, ...)`는
현재 grid를 새 outer grid 안에 넣습니다. 패널 목록·selector·원자료 행·내부 비율·
share ID를 바꾸지 않습니다. 생략한 grid ID는 다음 사용 가능한 결정론적
`gridN`이므로 연속 nest가 충돌하지 않고 명시적 ID 충돌은 오류입니다.
`pair(...).nest(...)`와 `joint(...).nest(...)`는 수동 전처리/native 수정 없이
동작합니다. Inset은 실제 child axes이며 지원 Matplotlib 하한에서 2-D/polar/3-D
부모·자식 조합을 사용합니다. Bounds `[left, bottom, width, height]`는 부모 axes
비율로, 부모 이동에 따라갑니다. 유한·양수 크기·부모 내부 포함을 요구하며 형제끼리
접할 수는 있지만 겹칠 수 없습니다. Inset 안의 inset도 가능합니다.

## 하나의 저장 배치 규칙

`FigureSpec.panel_layout`은 flat `PanelLayoutSpec(grids=[...])`입니다.
`LayoutGridSpec`에는 grid_id·양수 rows/cols·선택적 양수 유한
width_ratios/height_ratios가 있습니다. 유일한 root는 cell=None이고 다른 grid는
부모 grid의 `GridCellSpec(grid, row, col, row_span=1, col_span=1)`에 배치합니다.
Row/col은 왼쪽 위 기준 0부터, span은 양수입니다. 각 명시적 패널은 panel_id와
placement가 있어야 하며 `PanelPlacementSpec`은 cell 또는
`InsetSpec(parent=panel_id, bounds=[...])` 중 **정확히 하나**만 가집니다.

`Plot.panel_layout(layout, placements, panel_ids=None)`/SetPanelLayout은
완전한 geometry payload를 원자적으로 적용합니다. Typed dataclass 또는 JSON
객체를 받습니다. 키와 모든 incoming inset.parent/grid 참조는 **최종 ID**를
사용하며 옛 ID를 추론하지 않습니다. Panel_ids는 현재 목록 순서대로 명시적으로
ID를 배정/변경하므로 A/B swap도 가능합니다. RenamePanel은 이와 별개로 기존
저장 inset 부모 참조를 함께 바꿉니다. 중복 대상·누락된 최종 참조는 오류입니다.

ID 규칙은 `[A-Za-z][A-Za-z0-9_.-]{0,63}`입니다. 패널·grid ID는 별도 typed
namespace이며 원자료 행 ID·axis share ID·semantic scale 이름과 다릅니다.
Opt-in의 익명 패널은 목록 순서로 사용하지 않은 가장 작은 panelN을 받습니다.
배치·순서 편집·undo/redo·다시 열기에서 ID를 유지합니다. 기존 action은 계속
패널 **index**를 사용하므로 reorder 뒤 index는 의도적으로 달라집니다.

기존 최종 ID 전부를 포함해야 하며 추가 placement 키는 새 빈 실제 패널을
**ID 사전식 순서**로 뒤에 추가합니다. JSON 객체 키 순서는 패널 index를
바꾸지 않습니다. 할당 전에 패널256 상한을 확인하고 panel_ids 배열은 기존
패널만 이름 변경합니다. 같은 transaction의 새 inset이 다른 새 패널을 부모로
참조할 수도 있습니다. Pair/joint를 nest한 뒤 빈 outer cell에 새 placement를
선언하면 임시 inset/mosaic 초기화 없이 실제 형제 패널을 만들 수 있습니다.
선언하지 않은 자리는 계속 비어 있습니다.
RemovePanel은 inset이 참조하는 부모와 마지막 패널을 삭제하지 않으며 cascade나
몰래 reparent하지 않습니다.

명시적 배치와 legacy layout/width_ratios/height_ratios를 동시에 저장할 수
없습니다. Mosaic/nest/완전 배치 action이 전환하고, 일반 layout(rows,cols,...)는
명시 placement를 지우고 기존 ID를 유지한 채 regular-grid로 돌아갑니다.
명시 모드에서 AddPanel/범위 밖 index 자동 확장은 배치 없는 패널을 만들지 않고
오류로 알립니다.

## 축 공유·단위

하나의 순수 component resolver를 validator·native linking·N12 유효 눈금/scale
option 상속이 함께 사용합니다. AxisSpec.share_id와 figure의 non-none sharing
mode를 같은 축에서 섞는 기존 금지 규칙을 유지합니다.

- 명시적 row/col은 **바로 소속된 같은 grid**, 같은 정확한 row/col 구간만
  공유합니다. 다른 중첩 grid의 로컬 row0이나 일부만 겹치는 span은 연결하지
  않습니다. 이 모드에서 inset은 독립입니다.
- all은 primary Cartesian 패널 전체를 inset까지 의도적으로 연결합니다.
- 다른 grid/inset 간 공유는 figure mode none + 기존 share_axis로 선언합니다.
  Polar/3-D·독립 y2·derived axes의 기존 제한은 그대로입니다.

실제 비어 있지 않은 observation-value/clock 축과 mass/count/density/
proportion/percent/frequency 축의 차원을 구분합니다. Mean/median/point 추정값은
같은 반응 단위의 원자료 값축과 공유할 수 있으며 estimator 이름 차이만으로
거부하지 않습니다. 빈 선택 view에는 가짜 role을 만들지 않고 열 이름/label로
물리 단위를 추정하지 않습니다. 시간 선언·N12 눈금 충돌 검증을 유지하고 pair
대각 density 및 joint marginal/value 연결은 nest 뒤에도 독립성을 유지합니다.

새 공유 차원 검사는 실제 N13 opt-in(panel_layout 또는 저장 panel_id)이 있을 때만
적용합니다. 둘 다 없는 기존 파일의 raw/count 공유 동작은 유지합니다. 원래
범주·sharing mode·시간·domain·layer 유효성 검사는 계속 전역으로 적용합니다.

## 자원·편집기·업그레이드

기존 실제 패널256·전체 layer1024·render 4천만 pixel 제한을 유지합니다.
명시 배치는 grid node256·전체 선언 grid cell1024·깊이16까지이며 root 깊이는1,
패널/inset 조상도 셉니다. 기존 regular-grid cell 상한은256입니다. RAM sandbox나
지연시간 보장이 아니며 fit을 위해 표본을 버리지 않습니다. Cycle·누락/중복 참조·
여러 root·잘못된 span/ratio·grid 형제 겹침·표현할 수 없는 양수 native 범위를
거부합니다. 저장 비율은 그대로 두고 effect 내부에서만 안정적으로 정규화하여
합 overflow를 피합니다. 실제 0/붕괴 범위는 clamp/패널 누락 대신 오류입니다.

명시 배치는 모든 projection에서 axes/colorbar 생성 **전** native TightLayoutEngine을
일관되게 선택합니다. 승인된 전체 hierarchy에서 constrained solver의 과도한 제약
삽입을 피하며 시간 threshold/fallback은 없습니다. 복잡한 장식을 맞출 수 없다는
native/측정 경고는 그대로 유지하고 가독성을 보장한다고 주장하지 않습니다.
Tight rectangle은 left/bottom/right/top, 기존 constrained 경로는
left/bottom/width/height입니다. Inset은 redraw/resize/DPI에도 실제 부모 축을
따르며 저장 비율·단위·limits는 바꾸지 않습니다.
측정은 기존 보이는/비어 있지 않은/투명하지 않은 text eligibility와 off-view
tick 제외 규칙을 재사용합니다. 실제 축 label 및 tick-자동장식 충돌은 artist를
옮기지 않고 경고합니다. 축/side별 union bbox로 후보를 좁히며 모든 tick 쌍이나
caller 소유 데이터 text를 새로 추론하지 않습니다.

Python/Rust 편집기 모두 현재 값이 채워진 typed JSON 배치 폼으로 mosaic/nest,
전체 geometry·active placement·inset·rename·reorder·remove를 적용합니다.
Metadata는 실제 child axes를 순회하고 panel tag를 사용하므로 fig.axes 순서나
색상 막대/twin을 패널로 오인하지 않습니다. 선택은 reorder 시 안정적 ID를
따릅니다. Data handle은 N12의 대상별 linear/log 지원 및 명시적 비활성 이유를
유지하고 제목/범례 handle도 유지합니다. 편집기 PNG는 capped preview이며
정확한 크기 PNG는 설치 API/CLI, SVG/PDF는 설정된 물리 크기입니다.
Generation/revision URL은 실제 보이는 이미지와 handle의 세대 혼합을 막습니다.

**기존 0.1 파일에 migration은 필요 없습니다.** 새 선택적 필드는 뒤에 추가하고
None이면 저장하지 않으며 기존 regular 렌더 경로는 유지합니다. 새로운 facet/
pair/joint 구조는 패널을 명시적으로 교체합니다. 고정 typed selector마다 권위 있는
패널 하나를 유지하는 nest/mosaic/placement/inset/reorder/rename은 live 소유권을
보존합니다. Whole-template은 outer 형제를 포함한 실제 ID/placement를 유지하며
그 명시 transaction 전까지 saved local view가 권위 있는 상태입니다. Live cell을
제거하면 saved view로 남고 새 facet/pair/joint나 implicit regular grid 확장/변경은
recipe를 detach합니다. 같은 shape ratio-only 변경은 정확한 부분 셀 수를 유지하고
load는 자동 rebuild하지 않습니다. Figure guide는 scale_id만 membership으로
사용하므로 ID 변경에 중복 guide 참조를 다시 쓰지 않습니다.

[실행 예제](../examples/panel_layouts.py):

```sh
python examples/panel_layouts.py /tmp/layout-example
python -m mudplot validate /tmp/layout-example/panel_layouts.mplot.json
python -m mudplot render /tmp/layout-example/panel_layouts.mplot.json /tmp/layout.pdf
```

Linux·읽을 수 있는 raster/vector/TeX와 기능 stress 증거를 별도로 기록합니다.
Windows/macOS·물리 인쇄·원래 실험은 이 행에서 검증했다고 주장하지 않습니다.
