"""Executable examples and generated docs for every mudplot plot layer."""

from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from mudplot._mpl_context import matplotlib_context

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
            "lineplot",
            "series",
            "Raw-data line estimates",
            "Numeric x-cell means with seeded pointwise CI, not simultaneous bands.",
            "숫자 x별 평균과 seeded 점별 CI를 표시하며 동시 신뢰대역이 아닙니다.",
        ),
        (
            "stem",
            "series",
            "Stem plot",
            "Finite synthetic vertical observations retain their supplied order "
            "and raw baseline.",
            "유한합성관측의수직stem으로원본순서와rawbaseline을보존합니다.",
        ),
        (
            "stairs",
            "series",
            "Pre-binned stairs",
            "Supplied heights and explicit edges, without rebinning observations.",
            "주어진높이와명시edge를사용하며관측을다시binning하지않습니다.",
        ),
        (
            "eventplot",
            "series",
            "Numeric event train",
            "Supplied event positions with raw-coordinate offset and mark length.",
            "주어진event위치와raw좌표offset/표식길이를사용합니다.",
        ),
        (
            "broken_barh",
            "series",
            "Numeric interval band",
            "Explicit start/duration intervals retain overlaps in one raw band.",
            "명시start/duration구간과겹침을한rawband에보존합니다.",
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
            "swarmplot",
            "series",
            "Swarm plot",
            "Circular observations repack in display space on each draw, including "
            "positive log-value axes; overcrowding retains rows with a warning.",
            "매 draw의 화면 좌표에서 원형 관측값을 다시 배치하며 "
            "양수 log 값축을 지원하고 과밀하면 행을 보존하며 경고합니다.",
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
            "Grouped means with supplied SD, light fills, and aligned capped errors; "
            "default redundant encoding remains available for hatch differences.",
            "그룹 평균과 제공된 SD를 옅은 면·정렬된 캡 오차막대로 표시합니다. "
            "기본 redundant encoding을 유지하면 해칭으로도 구분할 수 있습니다.",
        ),
        (
            "barplot",
            "series",
            "Raw-data bar plot",
            "Raw replicates aggregate to means and seeded percentile-bootstrap CI.",
            "원자료 반복 관측에서 평균과 seeded percentile-bootstrap CI를 계산합니다.",
        ),
        (
            "pointplot",
            "series",
            "Raw-data point plot",
            "Raw means and sample SE use aligned, optionally dodged point estimates.",
            "원자료 평균·표본 SE를 정렬하고 선택한 dodge로 점 추정값을 구분합니다.",
        ),
        (
            "countplot",
            "series",
            "Raw-data count plot",
            "Categorical observation counts require no y column or inferred interval.",
            "y 열이나 추정 구간 없이 범주별 원자료 관측 개수를 표시합니다.",
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
            "Nested raw boxes show seeded 90% median CI, means, 5-95% whiskers "
            "and explicit per-hue cap styles; whiskers are not CIs.",
            "중첩 원자료 box에 seeded 90% 중앙값 CI·평균·5-95% whisker와 "
            "명시 hue별 cap 스타일을 표시합니다. Whisker는 CI가 아닙니다.",
        ),
        (
            "boxenplot",
            "distributions",
            "Letter-value plot",
            "Nested raw-data quantile bands reveal tails with exponential widths; "
            "median and outside observations are not confidence intervals.",
            "원자료 분위수 띠와 지수 폭으로 꼬리를 표시합니다. "
            "중앙값·바깥 관측값은 신뢰구간이 아닙니다.",
        ),
        (
            "violin",
            "distributions",
            "Violin",
            "Horizontal nested violins use named bandwidth, median lines and "
            "consistent hue colours/hatches.",
            "가로 중첩 violin에 이름 기반 대역폭·중앙값·"
            "공통 그룹 색상과 해칭을 적용합니다.",
        ),
        (
            "kde",
            "distributions",
            "Kernel density",
            "Typed NumPy Gaussian KDE uses explicit Scott bandwidth and per-curve "
            "normalization; weights/support/CDF/fill controls are also available.",
            "Typed NumPy Gaussian KDE에 Scott 대역폭·곡선별 정규화를 명시합니다. "
            "가중치/평가 범위/CDF/채우기 설정도 지원합니다.",
        ),
        (
            "ecdf",
            "distributions",
            "Empirical cumulative distribution",
            "Weighted empirical steps aggregate ties and normalize within each curve; "
            "no bins, smoothing or inferred confidence interval.",
            "가중 원자료 계단선으로 반복값을 합산하고 각 곡선 안에서 정규화합니다. "
            "Bin·평활화·추정 신뢰구간은 사용하지 않습니다.",
        ),
        (
            "spectrum",
            "fields",
            "Signal spectrum",
            "Explicit Hz sampling, named windows and Welch density retain raw signals.",
            "Hz 표본율·이름 기반 window·Welch 밀도에서 원본 신호를 보존합니다.",
        ),
        (
            "rug",
            "distributions",
            "Rug",
            "Rug marks expose observations underneath a density estimate.",
            "밀도 추정 아래에 rug 표시로 개별 관측값을 드러냅니다.",
        ),
        (
            "kde2d",
            "fields",
            "Weighted bivariate KDE",
            "Full weighted Gaussian covariance; contour levels enclose conditional "
            "finite-grid mass, not confidence intervals or full-space coverage.",
            "가중 Gaussian 공분산을 사용하며 등고선은 유한 격자의 조건부 질량 "
            "비율입니다. 신뢰구간/전체 공간 확률 보장이 아닙니다.",
        ),
        (
            "hist2d",
            "fields",
            "2-D histogram",
            "Rectangular bins show observation counts across two variables.",
            "직사각형 bin으로 두 변수의 관측 빈도를 표시합니다.",
        ),
        (
            "ecdf2d",
            "fields",
            "Paired empirical OR complement",
            "Right-continuous paired mass uses the strict X>qx OR Y>qy complement; "
            "finite bounds do not remove denominator observations.",
            "오른쪽 연속의 짝지은 질량에서 X>qx OR Y>qy의 엄격한 보완을 표시합니다. "
            "유한 경계가 분모 관측값을 제외하지 않습니다.",
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
            "clustermap",
            "fields",
            "Clustered heatmap",
            "Hierarchical row/column ordering preserves labels and source values.",
            "계층적 행/열 순서에 label을 맞추며 원자료는 보존합니다.",
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
        (
            "hlines",
            "annotations",
            "Horizontal segments",
            "Independent levels retain finite spans.",
            "각 수준의 유한 구간을 독립적으로 표시합니다.",
        ),
        (
            "vlines",
            "annotations",
            "Vertical segments",
            "Independent ranges stay on their measured x positions.",
            "독립 범위를 지정된 x 위치에 표시합니다.",
        ),
        (
            "hspan",
            "annotations",
            "Horizontal span",
            "A shaded operating range sits behind a measured trace.",
            "측정선 뒤에 운전 범위를 음영으로 표시합니다.",
        ),
        (
            "vspan",
            "annotations",
            "Vertical span",
            "The shaded time window does not alter the observations.",
            "시간 구간을 음영으로 표시하되 관측값은 바꾸지 않습니다.",
        ),
        (
            "barh",
            "series",
            "Signed horizontal bars",
            "Signed changes extend left or right from zero.",
            "부호 있는 변화량은 0에서 왼쪽 또는 오른쪽으로 뻗습니다.",
        ),
        (
            "imshow",
            "fields",
            "Scalar image",
            "Physical extent and lower origin are explicit.",
            "물리적 범위와 아래쪽 원점을 명시합니다.",
        ),
        (
            "pcolor",
            "fields",
            "Cell polygons",
            "A missing cell is omitted from a nonuniform grid.",
            "비균일 격자에서 값이 없는 셀을 생략합니다.",
        ),
        (
            "pcolormesh",
            "fields",
            "Quadrilateral mesh",
            "Nonuniform edges keep the authored cell widths.",
            "비균일 모서리가 지정된 셀 너비를 유지합니다.",
        ),
        (
            "spy",
            "fields",
            "Dense threshold pattern",
            "Squares show finite absolute values strictly above two.",
            "절댓값이 2를 넘는 유한 값만 사각형으로 표시합니다.",
        ),
        (
            "triplot",
            "fields",
            "Explicit triangle edges",
            "Edges come from authored connectivity, not inferred triangulation.",
            "삼각분할을 추론하지 않고 지정한 연결을 표시합니다.",
        ),
        (
            "tripcolor",
            "fields",
            "Face-coloured triangles",
            "Each face takes one explicitly supplied temperature.",
            "각 삼각형에 별도로 지정한 온도를 사용합니다.",
        ),
        (
            "tricontour",
            "fields",
            "Triangular isolines",
            "Vertex measurements define three explicit contour levels.",
            "정점 측정값으로 세 개의 명시 등고선을 그립니다.",
        ),
        (
            "tricontourf",
            "fields",
            "Filled triangle contours",
            "Declared boundaries define three filled bands.",
            "지정 경계가 채워진 세 띠를 정의합니다.",
        ),
        (
            "trisurf",
            "three-dimensional",
            "Triangulated surface",
            "The surface uses the literal vertex heights and faces.",
            "지정한 정점 높이와 삼각형으로 표면을 그립니다.",
        ),
        (
            "barbs",
            "series",
            "Speed barbs",
            "Point-length staffs encode signed component vectors.",
            "포인트 길이의 바브가 부호 있는 성분 벡터를 나타냅니다.",
        ),
        (
            "streamplot",
            "fields",
            "Seeded streamlines",
            "Three seeds trace the horizontal native vector field.",
            "세 시작점에서 수평 벡터장의 유선을 그립니다.",
        ),
        (
            "quiver3d",
            "three-dimensional",
            "Spatial arrows",
            "Shafts follow the declared raw displacement.",
            "화살표 몸체가 지정한 원시 변위를 따릅니다.",
        ),
        (
            "bar3d",
            "three-dimensional",
            "Signed spatial bars",
            "One box descends from its independent base.",
            "독립 기준점에서 내려가는 상자를 포함합니다.",
        ),
        (
            "contour3d",
            "three-dimensional",
            "Spatial isolines",
            "Isolines remain at their authored height levels.",
            "등고선을 각각 지정한 높이에 표시합니다.",
        ),
        (
            "contourf3d",
            "three-dimensional",
            "Projected contour bands",
            "Height bands project onto a fixed horizontal plane.",
            "높이 띠를 고정된 수평 평면에 투영합니다.",
        ),
        (
            "voxels",
            "three-dimensional",
            "Occupied cells",
            "Only occupied cells expose faces on nonuniform edges.",
            "비균일 격자에서 점유 셀의 노출 면만 그립니다.",
        ),
        (
            "patch",
            "annotations",
            "Anchored polygon",
            "The polygon follows literal data coordinates.",
            "다각형은 지정한 데이터 좌표를 따릅니다.",
        ),
        (
            "table",
            "annotations",
            "Literal table",
            "Labels and cell values remain literal and editable.",
            "라벨과 셀 값은 그대로 편집할 수 있습니다.",
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


@matplotlib_context()
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
    lines += [
        "## Saved axis workflow / 저장 가능한 축 workflow",
        "",
        "[Executable N12 comparison](../examples/axis_controls.py) uses six native",
        "panels for symlog/asinh/logit, major/minor ticks, a declared local clock,",
        "Celsius/Fahrenheit, base-two frequency/reciprocal period and derived",
        "length units. It saves PNG/SVG/PDF and JSON with edit/history/reopen.",
        "These are axis controls, not extra registered layer types.",
        "",
        "[N12 실행 비교](../examples/axis_controls.py)는 여섯 native 패널의 눈금·",
        "scale·clock·보조 단위와 PNG/SVG/PDF·JSON 편집/history/재개방을 제공합니다.",
        "새 layer 개수를 늘리는 기능이 아니며 [유한 계약](FEATURE_COVERAGE.md)을",
        "따릅니다. Isolated qualification and parent integration remain separate.",
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
