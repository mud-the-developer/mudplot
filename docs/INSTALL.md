# Installation and first figure

Use **Python 3.11 or later**. From the source checkout or unpacked source archive, install the engine and its Matplotlib renderer:

```sh
python -m pip install '.[render]'
```

Use `python -m pip install .` for the dependency-free JSON/spec and action core. Once published, the [v2.0.0 GitHub release](https://github.com/mud-the-developer/mudplot/releases/tag/v2.0.0) provides the wheel and source archive. Releases are GitHub-only; PyPI trusted publishing is not enabled. The wheel contains the Python engine, not the dashboard, example sources or Rust editor. Run those tools from the matching source checkout or archive.

| Extra | Purpose and dependency floor |
| --- | --- |
| `color` | NumPy ≥ 1.23.5 for the palette engine |
| `render` | NumPy ≥ 1.23.5, Matplotlib ≥ 3.8 and Pillow ≥ 13.0.0 for rendering and previews |
| `regression` | Rendering plus statsmodels ≥ 0.14.1 for robust, logistic and LOWESS effects |
| `cluster` | Rendering plus SciPy ≥ 1.10 for clustered heatmaps |
| `all`, `dev` | Include the optional regression and clustering effects; `dev` adds development tools |

Python 3.10 support ended because the security-constrained Pillow line needs Python 3.11. This does not change the historical v1.0.0 wheel. See the [security policy](../SECURITY.md) for supported versions and reporting.

## Build and save a figure

Run the [standalone Python example in the repository README](../README.md). `save()` preserves the configured physical size; pass `tight=True` only to crop to the content. The returned Matplotlib figure stays open until you close it with `plt.close(fig)`. Edit `Plot.spec` and `Store.state` through builder methods/actions, not by mutating their isolated snapshots. Then try an [executable v2 workflow](../examples/README.md#run-and-edit-an-example) or [prepare output for publication](PUBLICATION.md).

## Resource limits

| Boundary | Supported bound |
| --- | --- |
| Figure structure | `max_panels = 256`, `max_layout_cells = 256` |
| Layer model | `max_layers = 1024` total across panels |
| Bivariate grids | hist2d `max_bins_per_axis = 512`; hexbin gridsize ≤512 |
| Owned canvas work | `max_canvas_pixels = 40_000_000`, including output DPI and tight bounds |

Above these bounds, work fails explicitly instead of being silently clamped. Capped editor previews preserve the original spec and source DPI. These limits are not total RAM, CPU or sandbox guarantees. The default reducer can use one bounded checkpoint for replay; custom reducers retain full replay. Read the [performance](PERFORMANCE.md), [compatibility](COMPATIBILITY.md) and [security](../SECURITY.md) guides for exact scope.

## Develop from source

Run `uv sync --locked --extra dev` for the development environment; add `--extra browser` for real-browser editor tests. See [contributing](../CONTRIBUTING.md) for Python, browser, TeX and Rust preflight, schema regeneration and source-distribution checks.
