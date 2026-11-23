# 실행 가능한 v2 워크플로와 업그레이드 안내

[English](README.md) · [플롯 갤러리](../docs/PLOT_GALLERY.md) · [기능 지원 범위](../docs/FEATURE_COVERAGE.ko.md)

현재 소스는 FigureSpec 스키마 **0.1**을 유지하는 미발행 로컬 **2.0.0** 후보입니다. 범위가 정해진 v2 워크플로를 제공하며 Seaborn·Matplotlib 전체와 동등하지 않습니다. 같은 산출물의 TeX 컴파일을 포함한 최종 검증은 끝나지 않았습니다.

## 예제 실행 및 편집

Python 3.11 이상을 사용하세요. 코어에 필수 외부 패키지는 없습니다. 같은 버전의 소스나 풀어놓은 sdist에서 `.[render]`를 로컬 환경에 설치합니다(NumPy ≥1.23.5, Matplotlib ≥3.8, Pillow ≥13). 선택적 모델에는 `.[regression]` 또는 `.[cluster]`가 필요하며 `all`은 둘을 포함합니다. 대시보드·예제 소스·Rust 편집기는 엔진 wheel에 들어 있지 않습니다.

```sh
mkdir -p /tmp/mudplot-example
python examples/scalar_display.py /tmp/mudplot-example
python -m mudplot validate /tmp/mudplot-example/scalar-display.mplot.json
python -m mudplot render /tmp/mudplot-example/scalar-display.mplot.json /tmp/mudplot-example/reopened.svg
```

이 예제는 명시적인 스칼라 색 범위와 원시 단위 가이드를 사용하며 JSON, PNG, SVG, PDF를 저장합니다. 같은 Python 환경으로 [로컬 Rust 편집기](../mudplot-editor/README.ko.md)를 시작하고 루프백 페이지에서 JSON을 여세요. 레이어 양식 또는 지원되는 raw action으로 가이드를 변경한 뒤 실행취소·다시 실행하고, 복사본을 내려받아 다시 엽니다. 인증 없는 로컬 도구이며 원격 협업 서버가 아닙니다. 옵션에 따라 전용 위젯 대신 공용 양식이나 raw action을 사용합니다.

각 스크립트에 출력 경로를 지정하세요. 일부 기본 경로는 문서 디렉터리입니다. 예제 입력은 합성 데이터 또는 리터럴이며, 모든 옵션 조합의 지원을 입증하지는 않습니다.

## 워크플로 고르기

| 작업 | 실행 가능한 소스 |
| --- | --- |
| 통계 구간 선택 | [가중·단위 추정](statistical_categories.py), [제공한 SD와 CI](bar_uncertainty.py), [완전한 단위 궤적](line_workflow.py), [회귀 모델](regression_modes.py) |
| 분포 탐색 | [히스토그램 구간](histogram_binning.py), [히스토그램 도형](histogram_modes.py), [가중 KDE](kde_semantics.py), [경험적 CDF](ecdf_semantics.py), [짝지은 밀도 필드](density_fields.py) |
| 범주 비교 | [Box 요약값](box_workflow.py), [가중 바이올린](weighted_violin.py), [Letter value](weighted_letter_values.py), [가중 도수](weighted_counts.py), [네이티브 범주 축](native_categorical_scales.py) |
| 패널 비교·축 맞추기 | [패싯 빌더](facet_builders.py), [가중 pair·joint 그리드](weighted_grids.py), [명시적 시간축](temporal_axes.py), [축 제어](axis_controls.py), [이름 있는 패널](panel_layouts.py) |
| 네이티브 도형·필드 그리기 | [Heatmap 옵션](heatmap_controls.py), [군집 행렬](matrix_workflow.py), [네이티브 주석](native_annotations.py), [벡터](vector_workflow.py), [명시적 3D 도형](spatial_workflow.py) |
| 출판용 그림 준비 | [읽기 중심 그래프](publication_showcase.py), [선택형 과학 그림 QA](scientific_quality.py) |

## 이전 0.1 파일 다시 열기

원본을 보관하고 먼저 열거나 검증하세요. 생략한 옵션은 호환 기본값을 유지합니다. 기존 열을 자동으로 재해석하지 않으며 달력·이름 있는 척도·토폴로지·복합 배치는 명시적으로 선택합니다. `python -m mudplot migrate old.mplot.json --out reopened.mplot.json`으로 검증된 별도 복사본을 저장합니다. 명시적 null이나 지원하지 않는 버전은 거부합니다. 미등록 필드에 메타데이터를 보관하지 마세요. 새 옵션을 0.1로 저장해도 이전 프로그램에서 읽을 수 있다고 보장하지 않습니다. [호환성 계약](../docs/COMPATIBILITY.ko.md)을 참고하세요.
