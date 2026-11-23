# 계층 군집 heatmap

*[English](CLUSTERMAP.md)*

Unreleased source-tree의 `clustermap`은 계층 군집 effect가 있는 matrix layer입니다.
JSON의 원래 행렬은 유지하며 변환값/leaf 순서는 렌더 시 계산하고 오래된 파생 열로
저장하지 않습니다.

![트리와 metadata를 정렬한 행별 표준화 합성 profile](images/clustered_profiles.png)

[편집 spec](images/clustered_profiles.mplot.json) ·
[SVG](images/clustered_profiles.svg) · [PDF](images/clustered_profiles.pdf) ·
[소스](../examples/clustered_profiles.py)

합성 profile을 데스크톱 700px에서 확인한 예제입니다. 색/주석은 원래 response가
아닌 **행별 sample z-score**이며 숨긴 셀도 표준화/군집에는 참여합니다. 트리/색이
유의성·인과 구조·보편 가독성 인증을 뜻하지 않습니다.

```bash
# Source checkout 기준이며 이미 공개한 v1.0.0 wheel의 기능이 아닙니다.
pip install '.[cluster]'  # render + SciPy>=1.10; 기본 필수 의존성은 그대로 비어 있음
```

```python
p = (mp.plot().matrix("m", values)
       .clustermap("m", cluster={"method": "average", "metric": "euclidean",
                    "row_cluster": True, "col_cluster": True},
                   heatmap={"xlabels": columns, "ylabels": rows},
                   clabel="Response")
       .size(7, 6))
```

Pure 구성/검증/schema/action/JSON은 NumPy/SciPy를 import하지 않습니다. Cluster/
heatmap은 strict ClusterSpec/HeatmapSpec 또는 dict이며 unknown key는 거부합니다.
All/dev extra에 군집을 포함하지만 필수 core 의존성·package/editor/spec version·
release 배포를 바꾼 것은 아닙니다.

## 순서·트리·직접 제공한 linkage

Method는 single/complete/average/weighted/centroid/median/ward, metric은
euclidean/cityblock/cosine/correlation입니다. Ward/centroid/median은 Euclidean만
허용합니다. 유한 vector라도 cosine/correlation이 정의되지 않으면 jitter/imputation
없이 실패합니다. 거리 계산 시 불필요한 큰 단위 overflow를 방지하고 필요한 단위로
복원하며 표현 불가 높이는 거부합니다.

row_cluster/col_cluster=False는 원래 순서를 유지합니다. 원소 하나인 축은 트리를
만들지 않습니다. optimal_ordering=True는 계산/제공 linkage 모두 표시 행렬 거리로
적용합니다. Lock한 SciPy 안에서 재현되지만 같은 거리 tie의 version 간 순서를
보장하지는 않습니다.

row_linkage/col_linkage는 `[left,right,distance,count]`의 `(n-1) × 4` JSON
배열입니다. 아직 소비하지 않은 서로 다른 이전 cluster를 가리켜야 하며 높이는
유한/음수 아님, count는 합친 leaf 수와 같아야 합니다. 불투명 SciPy object나
callable을 저장하지 않습니다. 직접 제공한 linkage는 데이터 갱신 뒤에도 그대로여서
의미는 사용자가 책임져야 합니다.

축별 하나의 leaf 순서로 행렬/mask/tick label/색상 표식을 함께 이동합니다. 트리
leaf는 cell centre와 맞춥니다. row_colors/col_colors는 축당 선택적 범주 색 strip
하나이며 자동 legend 범주가 아닙니다. Tree_color/tree_width와 본체 대비
비율인 dendrogram_ratio로 표시를 조절합니다.

## 표시 변환과 mask

아래 중 하나만 선택합니다.

- z_score='row'/'col': 평균을 빼고 sample SD(ddof=1)로 나눔.
- standard_scale='row'/'col': min-max [0,1].
- 둘 다 없음: 원래 값을 표시.

상수 축은 표준화할 수 없습니다. Fit-time scaling은 불필요한 overflow를 줄일 뿐
잘못된 데이터를 고치지 않습니다. 기본값은 masked 셀까지 유한 숫자를 요구합니다.
행과 열은 각각 최대 512개입니다. 아래 명시적 결측 모드에서도 NaN/Inf/bool을
`null`로 바꾸거나 보간하지 않습니다.

Mask는 표시 전용이고 군집/표준화의 행을 제외하지 않습니다. 재정렬 뒤에는
HeatmapSpec처럼 hidden 셀을 숨기며 색상 범위/주석에서 제외합니다. 주석은 변환된
표시값이므로 원래 단위로 오인하지 않도록 clabel/fmt를 지정하세요. Log 색상 norm과
z-score/min-max 변환은 함께 사용할 수 없습니다.

## 배치와 편집

각 clustermap은 별도 unfiltered primary Cartesian 패널을 쓰며 추가 layer/y2/
공유 축/crop 좌표 limits는 허용하지 않습니다. 독립 멀티패널 구성은 가능합니다.
Label이 없으면 원래 숫자 index를 표시하고 제목은 맨 위 보조 axes 위에 둡니다.

Nested GridSpec과 정렬된 보조 axes로 트리/색 strip/colourbar를 지정한 그림 안에
둡니다. Vector clip ID 재현성을 위해 계산 뒤 배치를 고정하므로 크기/DPI는 spec에서
바꿔 다시 렌더하고 직접 Figure resize가 군집 배치를 재생성한다고 기대하지 마세요.

기존 editor에서도 같은 AddLayer 설정을 사용합니다. 선택 effect 누락/잘못된
linkage/metric/새 spec은 기존 editor 상태·출력을 보존합니다. 행렬 모양을 바꾸면
mask/label도 갱신해야 합니다.

```bash
uv run python -m examples.clustered_profiles
uv run pytest -q tests/test_clustermap.py tests/test_heatmap_options.py
```

## 결측, 제공 거리, 편집 가능한 절단

`missing="complete_features"`인 군집 행렬만 실제 `None`/JSON `null`을 소비합니다.
`SetMatrix`로 먼저 저장할 수는 있지만 이 정책 없는 군집/heatmap/contour/surface
레이어에 쓰면 검증에 실패합니다. 표준화는 표시 마스크가 숨긴 숫자까지 관측값으로
포함합니다. 축마다 **원본 항목 전체에 관측된 공통 특성**만 골라 named metric을
계산합니다. 행/열 ID를 삭제하거나 pairwise 거리/대체값을 만들지 않습니다.
공통 특성 또는 유효 거리가 없으면 실패합니다. 보이는 결측은 슬래시와 범례로
표시하고 수치 색상과 주석에는 쓰지 않습니다.

`row_distances`/`col_distances`의 `CondensedDistanceSpec(label, values)`는 원본
순서의 SciPy condensed `d01,d02,…,d12,…`에 맞춘 유한·비음수 값 `n(n−1)/2`개와
거리/단위 이름입니다. single/complete/average/weighted로 이 거리에서 트리를
만듭니다. Ward/median/centroid는 Euclidean 입력이 필요합니다. 제공 트리의
순서 비용으로 쓰려면 `optimal_ordering=True`를 지정합니다. 같은 형태로 `SetMatrix`
갱신해도 제공 거리/트리는 불변입니다. 원본 위치의 항목이나 거리 의미가 바뀌면
호출자가 다시 선언해야 하며, 길이/유효 조건이 맞지 않으면 거부됩니다.
명시적 결측·제공 거리·절단으로 새로 계산한 병합의 양수 높이가 단위 복원 뒤
표현 불가능하면 거부합니다. 실제 0과 제공 트리의 높이는 그대로 유지합니다.

`row_cut`/`col_cut`의 `ClusterCutSpec(height, anchor=None)`은 **하위 병합 중 최대
높이**가 `height` 이하인 최대 서브트리로 나눕니다. 동률은 포함하고 역전된 트리의
실제 높이는 바꾸지 않습니다. 선택값은 원본 0부터 시작하는 인덱스입니다. 양쪽
에디터에서 높이·인덱스를 바꾸면 실제 선택 인덱스가 표시되고, `ReplaceLayer`로
기록되어 실행 취소와 다시 실행이 가능합니다. 행/열을 필터링하지 않습니다.

## 여러 트랙과 배치

`row_tracks`/`col_tracks`: 축마다 고유한 `id`, `title`, 원본 순서의 `values`,
순서가 지정된 `{key,label,color}` `levels`, 선택적 `ratio`와 `legend`.
기존 색 strip은 본체에 가장 가깝고 범례가 없습니다. 연속 트랙/자동 구간은
추론하지 않습니다. `row_dendrogram_ratio`/`col_dendrogram_ratio`로 축마다 나무
비율을, `track_legend_side`로 `right`/`bottom`을 지정합니다. 색상표는 heatmap
옵션을 재사용합니다. `python -m examples.matrix_workflow /path/to/output`으로
예제를 실행합니다.
고급 행렬 옵션을 쓰는 중첩 배치가 모두 직교좌표 패널이면 native constrained
배치가 회전 글자와 가이드를 위한 자리를 확보합니다. 기존·극좌표·3D 경로는 그대로입니다.

새 행렬 옵션에 대해 그림당 작업 크레딧 838,860,800, 관리 예약 96 MiB,
단일 직렬 SciPy 호출 예약 최대 16 MiB를 검사합니다. 실행 시간, 프로세스 RSS,
외부 라이브러리의 모든 할당을 보장하지 않습니다. 기존 캔버스·크기·주석·에디터
한도를 유지합니다. 장식이 들어가지 않으면 출력 크기/위치를 변경하세요.
