# Plot gallery / 플롯 갤러리

_Generated from `examples/plots/`; do not edit by hand._

Every image below is real mudplot output. The displayed Python is the exact
source executed to build it, using deterministic synthetic data. Each
editable spec passes validation and a lossless JSON round-trip.

아래 이미지는 모두 결정론적 합성 데이터로 생성한 실제 mudplot 출력입니다.
표시된 Python 코드를 그대로 실행해 이미지를 만들며, 모든 spec은 검증과
무손실 JSON round-trip을 통과합니다.

Append `plot.save("figure.png")` to any example to save it.
각 예제 끝에 `plot.save("figure.png")`를 추가하면 저장할 수 있습니다.
After use, close the returned Figure with `matplotlib.pyplot.close(fig)`.
사용 후 반환된 Figure를 `matplotlib.pyplot.close(fig)`로 닫아주세요.

Required/optional names below are `LayerSpec` fields, not builder aliases
(for example, `quiver(scale=...)` sets `quiver_scale`).
필수·선택 이름은 builder 별칭이 아닌 `LayerSpec` 필드입니다.
예를 들어 `quiver(scale=...)`는 `quiver_scale` 필드를 설정합니다.

## Series and relationships / 계열 및 관계

### `line` — Line

![Line](images/plots/line.png)

Grouped trajectories use colour, marker, and dash together.

그룹별 궤적을 색상·마커·선 모양으로 함께 구분합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `group`, `hue_order`, `label`, `color`, `line_width`, `line_style`, `drawstyle`, `marker`, `marker_size`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 80)
data = {
    "x": np.tile(x, 2),
    "signal": np.r_[np.sin(x), 0.65 * np.cos(x)],
    "series": ["sin"] * len(x) + ["cos"] * len(x),
}
plot = (
    mp.plot(data)
    .line("x", "signal", group="series")
    .labels(x="Phase (rad)", y="Signal", title="Grouped line")
    .legend(title="Series")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/line.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#line)

### `lineplot` — Raw-data line estimates

![Raw-data line estimates](images/plots/lineplot.png)

Numeric x-cell means with seeded pointwise CI, not simultaneous bands.

숫자 x별 평균과 seeded 점별 CI를 표시하며 동시 신뢰대역이 아닙니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `semantics`, `cmap_kind`, `group`, `stat`, `orient`, `stat_scale`, `hue_order`, `sort`, `error_style`, `error_alpha`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

# Synthetic replicates. CI is pointwise at each predictor, not simultaneous.
data = {
    "time": [1, 1, 2, 2, 4, 4, 8, 8] * 2,
    "response": [
        1,
        1.4,
        1.5,
        2,
        2.5,
        3.2,
        3.8,
        4.7,
        1.4,
        1.8,
        2,
        2.4,
        3.2,
        3.6,
        4.7,
        5.6,
    ],
    "method": ["Control"] * 8 + ["Treatment"] * 8,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .lineplot("time", "response", group="method", errorbar="ci", n_boot=251, seed=17)
    .labels(x="Time (h)", y="Response", title="Means / pointwise 95% bootstrap CI")
    .legend(title="Method", location="upper left")
    .size(5.4, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/lineplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#lineplot)

### `regplot` — Regression

![Regression](images/plots/regplot.png)

A polynomial mean fit with an explicit opt-in confidence band.

명시적으로 선택한 신뢰구간과 다항 평균 적합선을 표시합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `regression`, `degree`, `confidence`, `group`, `hue_order`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(7)
x = np.linspace(-2.5, 2.5, 48)
data = {"x": x, "y": 0.4 + 0.7 * x + 0.35 * x**2 + rng.normal(0, 0.55, len(x))}
plot = (
    mp.plot(data)
    .regplot("x", "y", degree=2, confidence=95, marker_size=4)
    .labels(x="Input", y="Response", title="Polynomial regression")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/regplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#regplot)

### `scatter` — Scatter

![Scatter](images/plots/scatter.png)

Point colour shares one continuous normalization and colorbar.

점 색상에 공통 연속 정규화와 colorbar를 적용합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `semantics`, `group`, `hue_order`, `label`, `color`, `marker`, `marker_size`, `alpha`, `c`, `cmap_kind`, `colorbar`, `clabel`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(11)
x = rng.normal(size=90)
y = 0.65 * x + rng.normal(scale=0.7, size=len(x))
data = {"x": x, "y": y, "score": np.hypot(x, y)}
plot = (
    mp.plot(data)
    .scatter(
        "x", "y", c="score", colorbar=True, clabel="Distance", marker_size=5, alpha=0.8
    )
    .labels(x="Feature 1", y="Feature 2", title="Continuous colour")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/scatter.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#scatter)

### `stripplot` — Strip plot

![Strip plot](images/plots/stripplot.png)

Deterministic jitter reveals individual categorical observations.

결정론적 jitter로 범주별 개별 관측값을 보여줍니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `jitter`, `group`, `hue_order`, `label`, `color`, `marker`, `marker_size`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(21)
conditions = ["Control", "Low", "High"]
data = {
    "condition": np.repeat(conditions, 24),
    "value": np.concatenate(
        [
            rng.normal(1.0, 0.12, 24),
            rng.normal(1.35, 0.16, 24),
            rng.normal(1.75, 0.2, 24),
        ]
    ),
}
plot = (
    mp.plot(data)
    .stripplot(
        "condition", "value", group="condition", jitter=0.18, marker_size=4, alpha=0.75
    )
    .labels(x="Condition", y="Response", title="Raw observations")
    .legend(show=False)
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/stripplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#stripplot)

### `swarmplot` — Swarm plot

![Swarm plot](images/plots/swarmplot.png)

Circular observations repack in display space on each draw, including positive log-value axes; overcrowding retains rows with a warning.

매 draw의 화면 좌표에서 원형 관측값을 다시 배치하며 양수 log 값축을 지원하고 과밀하면 행을 보존하며 경고합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `warn_thresh`, `label`, `color`, `edge_color`, `line_width`, `marker`, `marker_size`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(19)
data = {"dose": [], "response": [], "method": []}
for method, shift in (("A", 0), ("B", 0.25)):
    for dose, step in (("Low", 0), ("High", 0.6)):
        data["dose"].extend([dose] * 22)
        data["method"].extend([method] * 22)
        data["response"].extend(
            np.exp(rng.normal(shift + step, 0.16, 22)).round(2).tolist()
        )
plot = (
    mp.plot(data)
    .theme("publication")
    .swarmplot(
        "dose",
        "response",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        marker_size=4,
        edge_color="#ffffff",
        line_width=0.4,
        gap=0.1,
    )
    .yscale("log")
    .labels(x="Dose", y="Response (log scale)", title="Display-space swarm packing")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/swarmplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#swarmplot)

### `stackplot` — Stack plot

![Stack plot](images/plots/stackplot.png)

Aligned group series form a cumulative area chart.

정렬된 그룹 계열을 누적 영역으로 표현합니다.

**Required / 필수:** `x`, `y`, `group`

**Optional / 선택:** `color`, `line_width`, `line_style`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.arange(8)
data = {
    "x": np.tile(x, 3),
    "value": np.r_[2 + 0.4 * x, 1.4 + 0.3 * np.sin(x), 0.8 + 0.2 * np.cos(x)],
    "component": np.repeat(["Compute", "Storage", "Network"], len(x)),
}
plot = (
    mp.plot(data)
    .stackplot("x", "value", group="component", alpha=0.85)
    .labels(x="Week", y="Usage", title="Resource composition")
    .legend(title="Component", location="outside right")
    .size(5.2, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/stackplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#stackplot)

### `quiver` — Quiver

![Quiver](images/plots/quiver.png)

Vector direction and magnitude are encoded in data coordinates.

데이터 좌표계에서 벡터 방향과 크기를 표현합니다.

**Required / 필수:** `x`, `y`, `u`, `v`

**Optional / 선택:** `c`, `cmap_kind`, `colorbar`, `clabel`, `label`, `color`, `line_width`, `quiver_scale`, `quiver_width`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-2, 2, 9), np.linspace(-2, 2, 9))
u, v = -y, x
data = {
    "x": x.ravel(),
    "y": y.ravel(),
    "u": u.ravel(),
    "v": v.ravel(),
    "speed": np.hypot(u, v).ravel(),
}
plot = (
    mp.plot(data)
    .quiver(
        "x",
        "y",
        "u",
        "v",
        c="speed",
        colorbar=True,
        clabel="Speed",
        scale=8,
        width=0.007,
    )
    .labels(x="x", y="y", title="Rotational vector field")
    .size(4.5, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/quiver.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#quiver)

### `bar` — Bar

![Bar](images/plots/bar.png)

Grouped means with supplied SD, light fills, and aligned capped errors; default redundant encoding remains available for hatch differences.

그룹 평균과 제공된 SD를 옅은 면·정렬된 캡 오차막대로 표시합니다. 기본 redundant encoding을 유지하면 해칭으로도 구분할 수 있습니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `group`, `hue_order`, `label`, `color`, `bar_width`, `edge_color`, `line_width`, `yerr`, `y_lower`, `y_upper`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

data = {
    "dose": ["Control", "Low", "High"] * 3,
    "response": [1.0, 1.4, 1.9, 0.9, 1.6, 2.3, 1.1, 1.3, 1.7],
    "sd": [0.10, 0.13, 0.16, 0.09, 0.14, 0.18, 0.11, 0.12, 0.15],
    "cell": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .encoding(redundant_encoding=False)  # clean fills; omit for hatch encoding
    .bar(
        "dose",
        "response",
        group="cell",
        yerr="sd",
        bar_width=0.72,
        edge_color="white",
        line_width=0.5,
    )
    .labels(x="Dose", y="Response (a.u.)", title="Mean ± SD")
    .legend(title="Cell line", location="upper left")
    .ylim(0, 2.8)
    .size(5.2, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/bar.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#bar)

### `barplot` — Raw-data bar plot

![Raw-data bar plot](images/plots/barplot.png)

Raw replicates aggregate to means and seeded percentile-bootstrap CI.

원자료 반복 관측에서 평균과 seeded percentile-bootstrap CI를 계산합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `group`, `stat`, `native_scale`, `stat_scale`, `baseline`, `orient`, `order`, `hue_order`, `gap`, `value_labels`, `label_format`, `label`, `color`, `bar_width`, `edge_color`, `line_width`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

# Each condition/cell contains three raw replicates, not a supplied mean.
data = {
    "dose": (["Control"] * 3 + ["Low"] * 3 + ["High"] * 3) * 3,
    "response": [
        0.9,
        1.0,
        1.1,
        1.2,
        1.4,
        1.6,
        1.7,
        1.9,
        2.1,
        0.8,
        0.9,
        1.0,
        1.3,
        1.6,
        1.9,
        2.0,
        2.3,
        2.6,
        1.0,
        1.1,
        1.2,
        1.1,
        1.3,
        1.5,
        1.4,
        1.7,
        2.0,
    ],
    "cell": ["A"] * 9 + ["B"] * 9 + ["C"] * 9,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .encoding(redundant_encoding=False)
    .barplot(
        "dose",
        "response",
        group="cell",
        errorbar=("ci", 95),
        seed=42,
        bar_width=0.72,
        edge_color="white",
        line_width=0.5,
    )
    .labels(
        x="Dose",
        y="Response (a.u.)",
        title="Raw replicates: mean with 95% bootstrap CI",
    )
    .legend(title="Cell line", location="upper left")
    .ylim(0, 3.0)
    .size(5.2, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/barplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#barplot)

### `pointplot` — Raw-data point plot

![Raw-data point plot](images/plots/pointplot.png)

Raw means and sample SE use aligned, optionally dodged point estimates.

원자료 평균·표본 SE를 정렬하고 선택한 dodge로 점 추정값을 구분합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `group`, `stat`, `native_scale`, `stat_scale`, `orient`, `order`, `hue_order`, `dodge`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

# No manual summary table: one observation per row.
data = {
    "dose": (["Control"] * 3 + ["Low"] * 3 + ["High"] * 3) * 3,
    "response": [
        0.9,
        1.0,
        1.1,
        1.2,
        1.4,
        1.6,
        1.7,
        1.9,
        2.1,
        0.8,
        0.9,
        1.0,
        1.3,
        1.6,
        1.9,
        2.0,
        2.3,
        2.6,
        1.0,
        1.1,
        1.2,
        1.1,
        1.3,
        1.5,
        1.4,
        1.7,
        2.0,
    ],
    "cell": ["A"] * 9 + ["B"] * 9 + ["C"] * 9,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .pointplot("dose", "response", group="cell", errorbar="se", dodge=0.18)
    .labels(x="Dose", y="Response (a.u.)", title="Raw replicates: mean ± sample SE")
    .legend(title="Cell line", location="upper left")
    .ylim(0, 2.8)
    .size(5.2, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/pointplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#pointplot)

### `countplot` — Raw-data count plot

![Raw-data count plot](images/plots/countplot.png)

Categorical observation counts require no y column or inferred interval.

y 열이나 추정 구간 없이 범주별 원자료 관측 개수를 표시합니다.

**Required / 필수:** `x`

**Optional / 선택:** `group`, `stat`, `native_scale`, `baseline`, `orient`, `order`, `hue_order`, `gap`, `stack`, `value_labels`, `label_format`, `label`, `color`, `bar_width`, `edge_color`, `line_width`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

# Unequal sample sizes; countplot needs no y column and does not infer a CI.
data = {
    "dose": ["Control"] * 7 + ["Low"] * 6 + ["High"] * 5,
    "cell": ["A"] * 4 + ["B"] * 3 + ["A"] * 2 + ["B"] * 4 + ["A"] * 3 + ["B"] * 2,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .countplot("dose", group="cell", bar_width=0.72, edge_color="white", line_width=0.5)
    .labels(x="Dose", y="Observations", title="Raw observation counts")
    .legend(title="Cell line", location="upper right")
    .ylim(0, 5)
    .size(5.2, 3.5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/countplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#countplot)

### `errorbar` — Error bar

![Error bar](images/plots/errorbar.png)

Caller-supplied x/y uncertainty is rendered without inference.

사용자가 제공한 x/y 불확실성을 별도 추정 없이 표시합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `yerr`, `xerr`, `y_lower`, `y_upper`, `group`, `hue_order`, `label`, `color`, `error_color`, `error_line_width`, `capsize`, `capthick`, `marker`, `marker_size`, `line_width`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

data = {
    "time": [0, 1, 2, 3, 4],
    "mean": [1.0, 1.35, 1.72, 1.88, 2.15],
    "error": [0.08, 0.12, 0.1, 0.15, 0.13],
}
plot = (
    mp.plot(data)
    .errorbar("time", "mean", yerr="error", capsize=4, marker="o", marker_size=5)
    .labels(x="Time (h)", y="Mean ± supplied error", title="Measured uncertainty")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/errorbar.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#errorbar)

### `band` — Band

![Band](images/plots/band.png)

A shaded lower/upper envelope accompanies the central trajectory.

중심 궤적과 하한·상한 음영 영역을 함께 표시합니다.

**Required / 필수:** `x`, `y`, `y2`

**Optional / 선택:** `group`, `hue_order`, `label`, `color`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.linspace(0, 6, 70)
mean = np.sin(x) * np.exp(-x / 9)
spread = 0.12 + 0.03 * x
data = {"x": x, "mean": mean, "lower": mean - spread, "upper": mean + spread}
plot = (
    mp.plot(data)
    .band("x", "lower", "upper", label="Range", alpha=0.25)
    .line("x", "mean", label="Mean")
    .labels(x="Time", y="Signal", title="Uncertainty band")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/band.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#band)

## Distributions / 분포

### `hist` — Histogram

![Histogram](images/plots/hist.png)

Grouped samples share bins for direct distribution comparison.

그룹 표본이 같은 bin을 사용해 분포를 직접 비교합니다.

**Required / 필수:** `x`

**Optional / 선택:** `bins`, `density`, `histogram`, `group`, `hue_order`, `orient`, `label`, `color`, `edge_color`, `line_width`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(4)
data = {
    "value": np.r_[rng.normal(-0.5, 0.75, 180), rng.normal(0.8, 0.55, 180)],
    "group": ["Control"] * 180 + ["Treatment"] * 180,
}
plot = (
    mp.plot(data)
    .hist(
        "value",
        bins=np.histogram_bin_edges(data["value"], bins=18).tolist(),
        stat="density",
        common_norm=False,
        group="group",
        alpha=0.55,
    )
    .labels(x="Value", y="Density", title="Grouped histogram")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/hist.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#hist)

### `box` — Box plot

![Box plot](images/plots/box.png)

Nested category/hue boxes show medians, means and 5-95% whiskers; percentile whiskers are not confidence intervals.

범주/그룹 box로 중앙값·평균과 5-95% whisker를 표시합니다. 분위수 whisker는 신뢰구간이 아닙니다.

**Required / 필수:** `x`

**Optional / 선택:** `y`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `whis`, `components`, `notch`, `showmeans`, `showfliers`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(5)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.55)):
    for dose, effect in (("Low", 0), ("High", 1)):
        data["dose"].extend([dose] * 40)
        data["method"].extend([method] * 40)
        data["value"].extend(rng.normal(1 + shift + effect, 0.35, 40).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .box(
        "dose",
        "value",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        whis=(5, 95),
        gap=0.16,
        showmeans=True,
        edge_color="#4b5563",
        line_width=0.8,
    )
    .labels(x="Dose", y="Value", title="Nested boxes / 5-95% whiskers")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/box.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#box)

### `boxenplot` — Letter-value plot

![Letter-value plot](images/plots/boxenplot.png)

Nested raw-data quantile bands reveal tails with exponential widths; median and outside observations are not confidence intervals.

원자료 분위수 띠와 지수 폭으로 꼬리를 표시합니다. 중앙값·바깥 관측값은 신뢰구간이 아닙니다.

**Required / 필수:** `x`

**Optional / 선택:** `y`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `k_depth`, `components`, `width_method`, `outlier_prop`, `trust_alpha`, `showfliers`, `showmedians`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(83)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.4)):
    for dose, effect in (("Low", 0), ("High", 0.9)):
        data["dose"].extend([dose] * 128)
        data["method"].extend([method] * 128)
        data["value"].extend(rng.normal(1 + shift + effect, 0.4, 128).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .boxenplot(
        "dose",
        "value",
        group="method",
        order=["Low", "High"],
        hue_order=["B", "A"],
        k_depth=4,
        width_method="exponential",
        gap=0.15,
        edge_color="#4b5563",
        line_width=0.7,
        marker_size=2.5,
    )
    .labels(x="Dose", y="Response", title="Letter values / quantiles, not CI")
    .legend(title="Method", location="upper left")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/boxenplot.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#boxenplot)

### `violin` — Violin

![Violin](images/plots/violin.png)

Horizontal nested violins use named bandwidth, median lines and consistent hue colours/hatches.

가로 중첩 violin에 이름 기반 대역폭·중앙값·공통 그룹 색상과 해칭을 적용합니다.

**Required / 필수:** `x`

**Optional / 선택:** `y`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `bw_method`, `points`, `weights`, `inner`, `split`, `density_norm`, `common_norm`, `bw_adjust`, `cut`, `clip`, `marker`, `marker_size`, `showmeans`, `showmedians`, `showextrema`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(6)
data = {"dose": [], "value": [], "method": []}
for method, shift in (("A", 0), ("B", 0.45)):
    for dose, effect in (("Low", 0), ("High", 1)):
        data["dose"].extend([dose] * 50)
        data["method"].extend([method] * 50)
        data["value"].extend(rng.normal(1 + shift + effect, 0.3, 50).tolist())
plot = (
    mp.plot(data)
    .theme("publication")
    .violin(
        "dose",
        "value",
        group="method",
        orient="h",
        order=["Low", "High"],
        hue_order=["B", "A"],
        bw_method="silverman",
        points=100,
        gap=0.12,
        showextrema=False,
        edge_color="#4b5563",
        line_width=0.8,
    )
    .labels(x="Value", y="Dose", title="Horizontal nested violins")
    .legend(title="Method", location="lower right")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/violin.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#violin)

### `kde` — Kernel density

![Kernel density](images/plots/kde.png)

Typed NumPy Gaussian KDE uses explicit Scott bandwidth and per-curve normalization; weights/support/CDF/fill controls are also available.

Typed NumPy Gaussian KDE에 Scott 대역폭·곡선별 정규화를 명시합니다. 가중치/평가 범위/CDF/채우기 설정도 지원합니다.

**Required / 필수:** `x`

**Optional / 선택:** `kde`, `group`, `hue_order`, `orient`, `label`, `color`, `alpha`, `line_width`, `line_style`, `edge_color`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(8)
data = {
    "value": np.r_[rng.normal(-0.5, 0.8, 120), rng.normal(0.9, 0.6, 120)],
    "group": ["Before"] * 120 + ["After"] * 120,
}
plot = (
    mp.plot(data)
    .kde("value", group="group", bw_method="scott", common_norm=False, line_width=2)
    .labels(x="Value", y="Density", title="Gaussian KDE")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/kde.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#kde)

### `ecdf` — Empirical cumulative distribution

![Empirical cumulative distribution](images/plots/ecdf.png)

Weighted empirical steps aggregate ties and normalize within each curve; no bins, smoothing or inferred confidence interval.

가중 원자료 계단선으로 반복값을 합산하고 각 곡선 안에서 정규화합니다. Bin·평활화·추정 신뢰구간은 사용하지 않습니다.

**Required / 필수:** `x`

**Optional / 선택:** `ecdf`, `group`, `hue_order`, `orient`, `label`, `color`, `line_width`, `line_style`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(28)
data = {
    "value": np.round(
        np.r_[rng.lognormal(0, 0.45, 60), rng.lognormal(0.4, 0.5, 80)], 1
    ),
    "weight": rng.integers(1, 5, 140),
    "group": ["Control"] * 60 + ["Treatment"] * 80,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .ecdf("value", weights="weight", group="group", line_width=1.8)
    .labels(
        x="Observed value", y="Within-curve proportion", title="Weighted empirical CDF"
    )
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/ecdf.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#ecdf)

### `rug` — Rug

![Rug](images/plots/rug.png)

Rug marks expose observations underneath a density estimate.

밀도 추정 아래에 rug 표시로 개별 관측값을 드러냅니다.

**Required / 필수:** `x`

**Optional / 선택:** `group`, `hue_order`, `label`, `color`, `alpha`, `line_width`, `line_style`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(9)
values = np.r_[rng.normal(-0.6, 0.6, 45), rng.normal(0.9, 0.5, 45)]
data = {"value": values}
plot = (
    mp.plot(data)
    .kde("value", color="#777777", alpha=0.75)
    .rug("value", color="#ef6674", line_width=1.1, alpha=0.65)
    .labels(x="Value", y="Density", title="KDE with rug marks")
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/rug.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#rug)

## Bivariate and matrix fields / 이변량 및 행렬 필드

### `kde2d` — Weighted bivariate KDE

![Weighted bivariate KDE](images/plots/kde2d.png)

Full weighted Gaussian covariance; contour levels enclose conditional finite-grid mass, not confidence intervals or full-space coverage.

가중 Gaussian 공분산을 사용하며 등고선은 유한 격자의 조건부 질량 비율입니다. 신뢰구간/전체 공간 확률 보장이 아닙니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `kde2d`, `group`, `hue_order`, `label`, `color`, `alpha`, `line_width`, `line_style`, `edge_color`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(41)
cloud = rng.multivariate_normal([0, 0], [[1, 0.65], [0.65, 0.8]], size=160)
data = {"x": cloud[:, 0], "y": cloud[:, 1], "weight": rng.integers(1, 5, len(cloud))}
plot = (
    mp.plot(data)
    .kde2d(
        "x",
        "y",
        weights="weight",
        gridsize=61,
        levels=[0.5, 0.8, 0.95],
        fill=True,
        alpha=0.65,
        line_width=0.8,
        label="Weighted joint density",
    )
    .labels(x="Observed x", y="Observed y", title="Gaussian KDE / conditional grid HDR")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/kde2d.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#kde2d)

### `hist2d` — 2-D histogram

![2-D histogram](images/plots/hist2d.png)

Rectangular bins show observation counts across two variables.

직사각형 bin으로 두 변수의 관측 빈도를 표시합니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `bins`, `density`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(12)
x = rng.normal(size=600)
data = {"x": x, "y": 0.7 * x + rng.normal(scale=0.65, size=len(x))}
plot = (
    mp.plot(data)
    .hist2d("x", "y", bins=22, colorbar=True, clabel="Count")
    .labels(x="x", y="y", title="Bivariate histogram")
    .size(4.5, 3.3)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/hist2d.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#hist2d)

### `hexbin` — Hexbin

![Hexbin](images/plots/hexbin.png)

Hexagonal aggregation reveals dense bivariate structure.

육각형 집계로 밀집된 이변량 구조를 보여줍니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `gridsize`, `mincnt`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(13)
x = rng.normal(size=700)
data = {"x": x, "y": np.sin(x * 1.8) + rng.normal(scale=0.35, size=len(x))}
plot = (
    mp.plot(data)
    .hexbin("x", "y", gridsize=24, mincnt=1, colorbar=True, clabel="Count")
    .labels(x="x", y="y", title="Hexagonal binning")
    .size(4.5, 3.3)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/hexbin.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#hexbin)

### `heatmap` — Heatmap

![Heatmap](images/plots/heatmap.png)

A diverging LCH colormap represents a signed matrix field.

발산형 LCH colormap으로 부호가 있는 행렬 필드를 표현합니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `heatmap`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `line_width`, `edge_color`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 36), np.linspace(-2, 2, 24))
field = np.sin(x) * np.cos(1.5 * y)
plot = (
    mp.plot()
    .matrix("field", field)
    .heatmap("field", cmap_kind="diverging", clabel="Amplitude")
    .labels(x="Column", y="Row", title="Matrix heatmap")
    .size(4.5, 3.3)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/heatmap.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#heatmap)

### `clustermap` — Clustered heatmap

![Clustered heatmap](images/plots/clustermap.png)

Hierarchical row/column ordering preserves labels and source values.

계층적 행/열 순서에 label을 맞추며 원자료는 보존합니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `cluster`, `heatmap`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `line_width`, `edge_color`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

plot = (
    mp.plot()
    .matrix("profiles", [[1, 2, 5], [2, 1, 4], [8, 7, 2], [9, 8, 1]])
    .clustermap(
        "profiles",
        cluster={"method": "average", "row_colors": ["#00858a"] * 2 + ["#ba4056"] * 2},
        heatmap={"xlabels": ["A", "B", "C"], "ylabels": ["N1", "N2", "S1", "S2"]},
        clabel="Response",
    )
    .labels(title="Hierarchical profiles — synthetic")
    .size(6, 5)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/clustermap.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#clustermap)

### `contour` — Contour

![Contour](images/plots/contour.png)

Level curves trace equal values across a matrix field.

등고선으로 행렬 필드의 같은 값을 연결합니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `cmap_kind`, `colorbar`, `clabel`, `alpha`, `levels`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 48), np.linspace(-2, 2, 34))
field = np.exp(-(x**2 + y**2) / 3) * np.cos(2 * x)
plot = (
    mp.plot()
    .matrix("field", field)
    .contour("field", levels=9, cmap_kind="diverging", clabel="Level")
    .labels(x="Column", y="Row", title="Contour lines")
    .size(4.5, 3.3)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/contour.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#contour)

### `contourf` — Filled contour

![Filled contour](images/plots/contourf.png)

Filled level regions combine contour structure with continuous colour.

채운 등고 영역으로 구조와 연속 색상을 함께 보여줍니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `cmap_kind`, `colorbar`, `clabel`, `alpha`, `levels`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 48), np.linspace(-2, 2, 34))
field = np.sin(x) * np.exp(-0.35 * y**2)
plot = (
    mp.plot()
    .matrix("field", field)
    .contourf("field", levels=12, cmap_kind="diverging", clabel="Amplitude")
    .labels(x="Column", y="Row", title="Filled contours")
    .size(4.5, 3.3)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/contourf.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#contourf)

## Reference marks and annotations / 기준선 및 주석

### `hline` — Horizontal reference line

![Horizontal reference line](images/plots/hline.png)

A labelled threshold is layered over the measured series.

측정 계열 위에 라벨이 있는 수평 임계선을 겹칩니다.

**Required / 필수:** `value`

**Optional / 선택:** `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.arange(8)
data = {"x": x, "y": [0.7, 0.9, 1.1, 1.35, 1.2, 1.55, 1.7, 1.8]}
plot = (
    mp.plot(data)
    .line("x", "y", marker="o")
    .hline(1.5, label="Target", line_style="--", color="#555555")
    .labels(x="Run", y="Score", title="Horizontal threshold")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/hline.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#hline)

### `vline` — Vertical reference line

![Vertical reference line](images/plots/vline.png)

A vertical event marker identifies a transition in time.

수직 이벤트 표시로 시간상의 전환점을 나타냅니다.

**Required / 필수:** `value`

**Optional / 선택:** `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.linspace(0, 10, 80)
data = {"time": x, "signal": 1 / (1 + np.exp(-(x - 5)))}
plot = (
    mp.plot(data)
    .line("time", "signal")
    .vline(5, label="Intervention", line_style="--", color="#555555")
    .labels(x="Time", y="Response", title="Event marker")
    .legend()
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/vline.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#vline)

### `text` — Text

![Text](images/plots/text.png)

Free text is placed at an exact data-coordinate position.

자유 텍스트를 정확한 데이터 좌표에 배치합니다.

**Required / 필수:** `text`, `at`

**Optional / 선택:** `color`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 70)
data = {"x": x, "y": np.sin(x)}
plot = (
    mp.plot(data)
    .line("x", "y")
    .text("peak region", [1.65, 1.08], color="#333333")
    .labels(x="Phase", y="Signal", title="Placed text")
    .ylim(-1.2, 1.3)
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/text.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#text)

### `annotate` — Annotation

![Annotation](images/plots/annotate.png)

An arrow connects explanatory text to a selected observation.

화살표로 설명 텍스트와 선택한 관측값을 연결합니다.

**Required / 필수:** `text`, `at`

**Optional / 선택:** `to`, `color`, `alpha`, `axis`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x = np.linspace(0, 2 * np.pi, 70)
data = {"x": x, "y": np.sin(x)}
plot = (
    mp.plot(data)
    .line("x", "y")
    .annotate("maximum", [2.2, 1.18], to=[np.pi / 2, 1.0])
    .labels(x="Phase", y="Signal", title="Arrow annotation")
    .ylim(-1.2, 1.35)
    .size(4.5, 3.2)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/annotate.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#annotate)

## Part-to-whole / 구성 비율

### `pie` — Pie

![Pie](images/plots/pie.png)

A small category set displays part-to-whole composition.

적은 수의 범주로 전체 대비 구성 비율을 보여줍니다.

**Required / 필수:** `x`, `y`

**Optional / 선택:** `color`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp

data = {
    "component": ["Compute", "Storage", "Network", "Other"],
    "share": [46, 28, 17, 9],
}
plot = (
    mp.plot(data)
    .pie("component", "share")
    .labels(title="Resource share")
    .size(4.2, 3.4)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/pie.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#pie)

## Three-dimensional / 3차원

### `scatter3d` — 3-D scatter

![3-D scatter](images/plots/scatter3d.png)

Three coordinates and continuous colour describe a point cloud.

세 좌표와 연속 색상으로 점 구름을 표현합니다.

**Required / 필수:** `x`, `y`, `z`

**Optional / 선택:** `group`, `label`, `color`, `marker`, `marker_size`, `alpha`, `c`, `cmap_kind`, `colorbar`, `clabel`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

rng = np.random.default_rng(16)
xyz = rng.normal(size=(90, 3))
data = {
    "x": xyz[:, 0],
    "y": xyz[:, 1],
    "z": xyz[:, 2],
    "radius": np.linalg.norm(xyz, axis=1),
}
plot = (
    mp.plot(data)
    .projection3d()
    .scatter3d(
        "x",
        "y",
        "z",
        c="radius",
        colorbar=True,
        clabel="Radius",
        marker_size=4,
        alpha=0.8,
    )
    .labels(x="x", y="y", title="3-D point cloud")
    .zlabel("z")
    .size(4.8, 3.8)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/scatter3d.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#scatter3d)

### `line3d` — 3-D line

![3-D line](images/plots/line3d.png)

A parametric trajectory is drawn through three-dimensional space.

매개변수 궤적을 3차원 공간에 선으로 그립니다.

**Required / 필수:** `x`, `y`, `z`

**Optional / 선택:** `group`, `label`, `color`, `line_width`, `line_style`, `marker`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

t = np.linspace(0, 5 * np.pi, 160)
data = {"x": np.cos(t), "y": np.sin(t), "z": t / (2 * np.pi)}
plot = (
    mp.plot(data)
    .projection3d()
    .line3d("x", "y", "z", line_width=2)
    .labels(x="x", y="y", title="Helical trajectory")
    .zlabel("z")
    .size(4.8, 3.8)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/line3d.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#line3d)

### `surface` — Surface

![Surface](images/plots/surface.png)

A matrix becomes a continuously coloured 3-D surface.

행렬을 연속 색상의 3차원 표면으로 변환합니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `cmap_kind`, `colorbar`, `clabel`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 34), np.linspace(-3, 3, 34))
field = np.sinc(np.hypot(x, y))
plot = (
    mp.plot()
    .matrix("field", field)
    .projection3d()
    .surface("field", cmap_kind="diverging", clabel="Height")
    .labels(x="Column", y="Row", title="3-D surface")
    .zlabel("Height")
    .size(4.8, 3.8)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/surface.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#surface)

### `wireframe` — Wireframe

![Wireframe](images/plots/wireframe.png)

A matrix surface is represented by a lightweight line mesh.

행렬 표면을 가벼운 선 mesh로 표현합니다.

**Required / 필수:** `matrix`

**Optional / 선택:** `color`, `alpha`

<details><summary>Runnable code / 실행 코드</summary>

```python
import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-2.5, 2.5, 28), np.linspace(-2.5, 2.5, 28))
field = np.cos(x) * np.sin(y) * np.exp(-(x**2 + y**2) / 12)
plot = (
    mp.plot()
    .matrix("field", field)
    .projection3d()
    .wireframe("field", color="#336699", alpha=0.8)
    .labels(x="Column", y="Row", title="3-D wireframe")
    .zlabel("Height")
    .size(4.8, 3.8)
)
plot.save("figure.png")
```

</details>

[Editable spec / 편집 가능한 spec](images/plots/wireframe.mplot.json) · [Reference / 레퍼런스](REFERENCE.md#wireframe)
