# 설치와 첫 그림

**Python 3.11 이상**이 필요합니다. 소스 checkout이나 압축을 푼 소스 아카이브에서 엔진과 Matplotlib 렌더러를 설치합니다.

```sh
python -m pip install '.[render]'
```

외부 의존성이 없는 JSON/spec·action core만 필요하면 `python -m pip install .`을 사용하세요. 산출물이 게시되면 [v2.0.0 GitHub 릴리스](https://github.com/mud-the-developer/mudplot/releases/tag/v2.0.0)에서 wheel과 소스 아카이브를 받을 수 있습니다. GitHub에만 배포하며 PyPI trusted publishing은 활성화하지 않았습니다. Wheel에는 Python 엔진만 있습니다. 대시보드, 예제 소스, Rust 편집기는 같은 버전의 소스에서 실행하세요.

| Extra | 용도 및 최소 의존성 버전 |
| --- | --- |
| `color` | 팔레트 엔진용 NumPy ≥ 1.23.5 |
| `render` | 렌더링·미리보기용 NumPy ≥ 1.23.5, Matplotlib ≥ 3.8, Pillow ≥ 13.0.0 |
| `regression` | 렌더링 의존성에 더해 robust·logistic·LOWESS용 statsmodels ≥ 0.14.1 |
| `cluster` | 렌더링 의존성에 더해 군집 heatmap용 SciPy ≥ 1.10 |
| `all`, `dev` | 회귀와 군집 선택 기능을 포함하며 `dev`에는 개발 도구도 포함 |

보안 패치가 적용된 Pillow가 Python 3.11을 요구하므로 Python 3.10 지원은 종료했습니다. 이미 공개된 v1.0.0 wheel의 내용은 바뀌지 않습니다. 지원 버전과 신고 절차는 [보안 정책](../SECURITY.ko.md)을 참고하세요.

## 그림 만들고 저장하기

[저장소 README의 독립 실행형 Python 예제](../README.ko.md)를 실행해 보세요. `save()`는 지정한 실제 크기를 유지하며, 내용에 맞춰 자를 때만 `tight=True`를 사용합니다. 반환된 Matplotlib figure는 열린 상태이므로 사용 후 `plt.close(fig)`로 닫으세요. `Plot.spec`과 `Store.state`는 격리된 스냅샷입니다. 직접 수정하지 말고 빌더 메서드나 action을 사용하세요. 이어서 [v2 워크플로](../examples/README.ko.md)와 [출판 가이드](PUBLICATION.ko.md)를 살펴보세요.

## 자원 한도

| 경계 | 지원 상한 |
| --- | --- |
| Figure 구조 | `max_panels = 256`, `max_layout_cells = 256` |
| Layer 모델 | `max_layers = 1024`, 전체 패널 합계 |
| 이변량 그리드 | hist2d `max_bins_per_axis = 512`; hexbin gridsize ≤512 |
| 소유 캔버스 작업 | `max_canvas_pixels = 40_000_000`, 출력 DPI와 tight 경계 포함 |

상한을 초과하면 조용히 값을 줄이지 않고 명시적으로 실패합니다. 크기를 제한한 편집기 미리보기는 원본 spec과 소스 DPI를 유지합니다. 이 상한은 전체 RAM·CPU·샌드박스 보장이 아닙니다. 기본 reducer는 재생에 한 개의 제한된 checkpoint를 사용할 수 있지만 사용자 reducer는 전체를 재생합니다. [성능](PERFORMANCE.ko.md), [호환성](COMPATIBILITY.ko.md), [보안](../SECURITY.ko.md) 문서에서 적용 범위를 확인하세요.

## 소스에서 개발하기

`uv sync --locked --extra dev`로 개발 환경을 설치하세요. 실제 브라우저 편집기 테스트에는 `--extra browser`를 추가합니다. [기여 가이드](../CONTRIBUTING.ko.md)에서 Python·브라우저·TeX·Rust 검사, 스키마 재생성 및 소스 배포 검사를 확인하세요.
