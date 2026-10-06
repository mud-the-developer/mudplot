"""Executable examples and generated docs for every mudplot plot layer."""

from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mudplot.api import Plot

__all__ = [
    "GALLERY_CATEGORIES",
    "GALLERY_EXAMPLES",
    "GalleryExample",
    "build_example",
    "gallery_markdown",
    "render_plot_gallery",
    "write_plot_gallery_docs",
]

_EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "plots"


@dataclass(frozen=True)
class GalleryExample:
    name: str
    category: str
    title: str
    description: str
    description_ko: str

    @property
    def code(self) -> str:
        return (_EXAMPLE_DIR / f"{self.name}.py").read_text(encoding="utf-8").strip()


GALLERY_CATEGORIES = (
    ("series", "Series and relationships", "계열 및 관계"),
    ("distributions", "Distributions", "분포"),
    ("fields", "Bivariate and matrix fields", "이변량 및 행렬 필드"),
    ("annotations", "Reference marks and annotations", "기준선 및 주석"),
    ("composition", "Part-to-whole", "구성 비율"),
    ("three-dimensional", "Three-dimensional", "3차원"),
)


GALLERY_EXAMPLES = tuple(
    GalleryExample(*values)
    for values in (
        (
            "line",
            "series",
            "Line",
            "Grouped trajectories use colour, marker, and dash together.",
            "그룹별 궤적을 색상·마커·선 모양으로 함께 구분합니다.",
        ),
        (
            "regplot",
            "series",
            "Regression",
            "A polynomial mean fit with an explicit opt-in confidence band.",
            "명시적으로 선택한 신뢰구간과 다항 평균 적합선을 표시합니다.",
        ),
        (
            "scatter",
            "series",
            "Scatter",
            "Point colour shares one continuous normalization and colorbar.",
            "점 색상에 공통 연속 정규화와 colorbar를 적용합니다.",
        ),
        (
            "stripplot",
            "series",
            "Strip plot",
            "Deterministic jitter reveals individual categorical observations.",
            "결정론적 jitter로 범주별 개별 관측값을 보여줍니다.",
        ),
        (
            "stackplot",
            "series",
            "Stack plot",
            "Aligned group series form a cumulative area chart.",
            "정렬된 그룹 계열을 누적 영역으로 표현합니다.",
        ),
        (
            "quiver",
            "series",
            "Quiver",
            "Vector direction and magnitude are encoded in data coordinates.",
            "데이터 좌표계에서 벡터 방향과 크기를 표현합니다.",
        ),
        (
            "bar",
            "series",
            "Bar",
            "Grouped bars retain hatch differences in grayscale print.",
            "그룹 막대는 흑백 인쇄에서도 해칭으로 구분됩니다.",
        ),
        (
            "errorbar",
            "series",
            "Error bar",
            "Caller-supplied x/y uncertainty is rendered without inference.",
            "사용자가 제공한 x/y 불확실성을 별도 추정 없이 표시합니다.",
        ),
        (
            "band",
            "series",
            "Band",
            "A shaded lower/upper envelope accompanies the central trajectory.",
            "중심 궤적과 하한·상한 음영 영역을 함께 표시합니다.",
        ),
        (
            "hist",
            "distributions",
            "Histogram",
            "Grouped samples share bins for direct distribution comparison.",
            "그룹 표본이 같은 bin을 사용해 분포를 직접 비교합니다.",
        ),
        (
            "box",
            "distributions",
            "Box plot",
            "Compact summaries compare grouped medians and spread.",
            "그룹별 중앙값과 산포를 간결하게 비교합니다.",
        ),
        (
            "violin",
            "distributions",
            "Violin",
            "Mirrored density shapes retain categorical colour and hatch encoding.",
            "대칭 밀도 모양에 범주별 색상과 해칭을 함께 적용합니다.",
        ),
        (
            "kde",
            "distributions",
            "Kernel density",
            "A NumPy-only Gaussian KDE compares smooth grouped distributions.",
            "NumPy 기반 Gaussian KDE로 그룹별 분포를 부드럽게 비교합니다.",
        ),
        (
            "rug",
            "distributions",
            "Rug",
            "Rug marks expose observations underneath a density estimate.",
            "밀도 추정 아래에 rug 표시로 개별 관측값을 드러냅니다.",
        ),
        (
            "hist2d",
            "fields",
            "2-D histogram",
            "Rectangular bins show observation counts across two variables.",
            "직사각형 bin으로 두 변수의 관측 빈도를 표시합니다.",
        ),
        (
            "hexbin",
            "fields",
            "Hexbin",
            "Hexagonal aggregation reveals dense bivariate structure.",
            "육각형 집계로 밀집된 이변량 구조를 보여줍니다.",
        ),
        (
            "heatmap",
            "fields",
            "Heatmap",
            "A diverging LCH colormap represents a signed matrix field.",
            "발산형 LCH colormap으로 부호가 있는 행렬 필드를 표현합니다.",
        ),
        (
            "contour",
            "fields",
            "Contour",
            "Level curves trace equal values across a matrix field.",
            "등고선으로 행렬 필드의 같은 값을 연결합니다.",
        ),
        (
            "contourf",
            "fields",
            "Filled contour",
            "Filled level regions combine contour structure with continuous colour.",
            "채운 등고 영역으로 구조와 연속 색상을 함께 보여줍니다.",
        ),
        (
            "hline",
            "annotations",
            "Horizontal reference line",
            "A labelled threshold is layered over the measured series.",
            "측정 계열 위에 라벨이 있는 수평 임계선을 겹칩니다.",
        ),
        (
            "vline",
            "annotations",
            "Vertical reference line",
            "A vertical event marker identifies a transition in time.",
            "수직 이벤트 표시로 시간상의 전환점을 나타냅니다.",
        ),
        (
            "text",
            "annotations",
            "Text",
            "Free text is placed at an exact data-coordinate position.",
            "자유 텍스트를 정확한 데이터 좌표에 배치합니다.",
        ),
        (
            "annotate",
            "annotations",
            "Annotation",
            "An arrow connects explanatory text to a selected observation.",
            "화살표로 설명 텍스트와 선택한 관측값을 연결합니다.",
        ),
        (
            "pie",
            "composition",
            "Pie",
            "A small category set displays part-to-whole composition.",
            "적은 수의 범주로 전체 대비 구성 비율을 보여줍니다.",
        ),
        (
            "scatter3d",
            "three-dimensional",
            "3-D scatter",
            "Three coordinates and continuous colour describe a point cloud.",
            "세 좌표와 연속 색상으로 점 구름을 표현합니다.",
        ),
        (
            "line3d",
            "three-dimensional",
            "3-D line",
            "A parametric trajectory is drawn through three-dimensional space.",
            "매개변수 궤적을 3차원 공간에 선으로 그립니다.",
        ),
        (
            "surface",
            "three-dimensional",
            "Surface",
            "A matrix becomes a continuously coloured 3-D surface.",
            "행렬을 연속 색상의 3차원 표면으로 변환합니다.",
        ),
        (
            "wireframe",
            "three-dimensional",
            "Wireframe",
            "A matrix surface is represented by a lightweight line mesh.",
            "행렬 표면을 가벼운 선 mesh로 표현합니다.",
        ),
    )
)


def build_example(example: GalleryExample) -> Plot:
    """Run a fresh copy of one source file and return its ``plot`` object."""
    if example not in GALLERY_EXAMPLES:
        raise ValueError(f"unknown gallery example {example.name!r}")
    namespace = runpy.run_path(str(_EXAMPLE_DIR / f"{example.name}.py"))
    try:
        return namespace["plot"]
    except KeyError as error:
        raise RuntimeError(
            f"gallery example {example.name!r} did not create `plot`"
        ) from error


def render_plot_gallery(directory: str | Path, *, write_specs: bool = False) -> Path:
    """Render every example to PNG, optionally writing editable specs too."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mudplot as mp

    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    for example in GALLERY_EXAMPLES:
        plot = build_example(example)
        issues = mp.validate(plot.spec)
        if issues:
            raise ValueError(f"gallery example {example.name!r}: {'; '.join(issues)}")
        rebuilt = mp.Plot.from_json(plot.to_json())
        if rebuilt.spec.to_dict() != plot.spec.to_dict():
            raise AssertionError(f"gallery example {example.name!r} lost JSON data")
        fig = plot.save(str(destination / f"{example.name}.png"))
        plt.close(fig)
        if write_specs:
            mp.save_spec(plot.spec, destination / f"{example.name}.mplot.json")

    return destination


def gallery_markdown(image_prefix: str = "images/plots") -> str:
    """Return the bilingual, executable Markdown gallery."""
    from mudplot.capabilities import LAYER_TYPES

    lines = [
        "# Plot gallery / 플롯 갤러리",
        "",
        "_Generated from `examples/plots/`; do not edit by hand._",
        "",
        "Every image below is real mudplot output. The displayed Python is the exact",
        "source executed to build it, using deterministic synthetic data. Each",
        "editable spec passes validation and a lossless JSON round-trip.",
        "",
        "아래 이미지는 모두 결정론적 합성 데이터로 생성한 실제 mudplot 출력입니다.",
        "표시된 Python 코드를 그대로 실행해 이미지를 만들며, 모든 spec은 검증과",
        "무손실 JSON round-trip을 통과합니다.",
        "",
        'Append `plot.save("figure.png")` to any example to save it.',
        '각 예제 끝에 `plot.save("figure.png")`를 추가하면 저장할 수 있습니다.',
        "After use, close the returned Figure with `matplotlib.pyplot.close(fig)`.",
        "사용 후 반환된 Figure를 `matplotlib.pyplot.close(fig)`로 닫아주세요.",
        "",
        "Required/optional names below are `LayerSpec` fields, not builder aliases",
        "(for example, `quiver(scale=...)` sets `quiver_scale`).",
        "필수·선택 이름은 builder 별칭이 아닌 `LayerSpec` 필드입니다.",
        "예를 들어 `quiver(scale=...)`는 `quiver_scale` 필드를 설정합니다.",
        "",
    ]
    for category, title, title_ko in GALLERY_CATEGORIES:
        lines += [f"## {title} / {title_ko}", ""]
        for example in GALLERY_EXAMPLES:
            if example.category != category:
                continue
            contract = LAYER_TYPES[example.name]
            required = ", ".join(f"`{name}`" for name in contract["required"])
            optional = ", ".join(f"`{name}`" for name in contract["optional"])
            lines += [
                f"### `{example.name}` — {example.title}",
                "",
                f"![{example.title}]({image_prefix}/{example.name}.png)",
                "",
                example.description,
                "",
                example.description_ko,
                "",
                f"**Required / 필수:** {required}",
                "",
                f"**Optional / 선택:** {optional or '—'}",
                "",
                "<details><summary>Runnable code / 실행 코드</summary>",
                "",
                "```python",
                example.code,
                'plot.save("figure.png")',
                "```",
                "",
                "</details>",
                "",
                f"[Editable spec / 편집 가능한 spec]({image_prefix}/"
                f"{example.name}.mplot.json) · "
                f"[Reference / 레퍼런스](REFERENCE.md#{example.name})",
                "",
            ]
    return "\n".join(lines).rstrip() + "\n"


def write_plot_gallery_docs(docs_dir: str | Path) -> Path:
    """Regenerate committed gallery images, specs, and Markdown."""
    from mudplot.io import _atomic_write_text

    destination = Path(docs_dir)
    render_plot_gallery(destination / "images" / "plots", write_specs=True)
    markdown_path = destination / "PLOT_GALLERY.md"
    _atomic_write_text(markdown_path, gallery_markdown())
    return markdown_path
