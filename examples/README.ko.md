# 실행 가능한 v2 워크플로와 업그레이드 안내

[English](README.md) · [행별 예제와 검증 근거](../docs/V2_EXAMPLE_EVIDENCE.md) · [레이어 예제 66종](../docs/PLOT_GALLERY.md)

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

[달력](temporal_axes.py), [라이브 패싯](facet_builders.py), [가중 pair·joint 격자](weighted_grids.py), [네이티브 주석](native_annotations.py), [명시적 3D 도형](spatial_workflow.py) 예제도 있습니다. 각 스크립트에 출력 경로를 지정하세요. 일부 기본 경로는 문서 디렉터리입니다. 과학적 의미와 지원 한계는 [행별 목록](../docs/V2_EXAMPLE_EVIDENCE.md#workflow-index)을 참고하세요.

## 이전 0.1 파일 다시 열기

원본을 보관하고 먼저 열거나 검증하세요. 생략한 옵션은 호환 기본값을 유지합니다. 기존 열을 자동으로 재해석하지 않으며 달력·이름 있는 척도·토폴로지·복합 배치는 명시적으로 선택합니다. `python -m mudplot migrate old.mplot.json --out reopened.mplot.json`으로 검증된 별도 복사본을 저장합니다. 명시적 null이나 지원하지 않는 버전은 거부합니다. 미등록 필드에 메타데이터를 보관하지 마세요. 새 옵션을 0.1로 저장해도 이전 프로그램에서 읽을 수 있다고 보장하지 않습니다. [호환성 계약](../docs/COMPATIBILITY.ko.md)을 참고하세요.
