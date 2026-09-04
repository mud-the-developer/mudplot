# mudplot engine reference

_Auto-generated from `mudplot.capabilities()` / `mudplot.json_schema()` — spec version `0.1`. Do not edit by hand; regenerate with `python -m mudplot docs`._

## Layers

### `annotate`

- **required**: `text`, `at`
- **optional**: `to`, `color`, `alpha`

### `band`

- **required**: `x`, `y`, `y2`
- **optional**: `group`, `label`, `color`, `alpha`

### `bar`

- **required**: `x`, `y`
- **optional**: `label`, `color`, `alpha`

### `box`

- **required**: `x`
- **optional**: `group`, `label`, `color`, `alpha`

### `errorbar`

- **required**: `x`, `y`
- **optional**: `yerr`, `xerr`, `group`, `label`, `color`, `capsize`, `marker`, `marker_size`, `line_width`, `alpha`

### `heatmap`

- **required**: `matrix`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`

### `hist`

- **required**: `x`
- **optional**: `bins`, `density`, `group`, `label`, `color`, `alpha`

### `hline`

- **required**: `value`
- **optional**: `label`, `color`, `line_style`, `line_width`, `alpha`

### `line`

- **required**: `x`, `y`
- **optional**: `group`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`, `axis`

### `scatter`

- **required**: `x`, `y`
- **optional**: `group`, `label`, `color`, `marker`, `marker_size`, `alpha`, `c`, `cmap_kind`, `colorbar`, `clabel`, `axis`

### `text`

- **required**: `text`, `at`
- **optional**: `color`, `alpha`

### `vline`

- **required**: `value`
- **optional**: `label`, `color`, `line_style`, `line_width`, `alpha`

## Palettes

LCH-based, colourblind-safe by default. Kinds: `qualitative`, `sequential`, `diverging`.

- `qualitative`: equal(-ish) lightness, maximum hue contrast, worst-case ΔE00 across normal + CVD vision maximised. A small `lightness_jitter` (default 6) keeps greyscale/print distinguishable.
- `sequential` / `diverging`: perceptually-uniform ramps, gamut-clipped.

## Themes

Available presets: paper, paper-grid, minimal, boxed.

## Journals

- **nature**: default figure size [3.5, 2.625], base font 7pt
- **ieee**: default figure size [3.3, 2.5], base font 8pt

## TeX presets (WYSIWYG sizing)

| preset | columnwidth (pt) | textwidth (pt) | font (pt) | cols |
|---|---|---|---|---|
| `acm` | 241.0 | 506.0 | 9.0 | 2 |
| `article` | 345.0 | 345.0 | 10.0 | 1 |
| `ieee` | 252.0 | 516.0 | 10.0 | 2 |
| `nature` | 250.38425196850392 | 512.1496062992127 | 7.0 | 2 |
| `revtex` | 246.0 | 510.0 | 10.0 | 2 |

## Actions (JSON action vocabulary)

Every mutation is one of these — send as 
`{"type": "<Name>", ...}` to `mp.apply([...])`.

### `AddLayer`

| field | type | required | default |
|---|---|---|---|
| `layer` | `LayerSpec` | True | `None` |
| `panel` | `int` | False | `0` |

### `AddPanel`

| field | type | required | default |
|---|---|---|---|

### `RemoveLayer`

| field | type | required | default |
|---|---|---|---|
| `layer_index` | `int` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetAutoLabel`

| field | type | required | default |
|---|---|---|---|
| `enabled` | `bool` | False | `True` |

### `SetAxesStyle`

| field | type | required | default |
|---|---|---|---|
| `params` | `dict` | False | `{}` |

### `SetAxisLabel`

| field | type | required | default |
|---|---|---|---|
| `axis` | `str` | True | `None` |
| `text` | `str` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetColorbar`

| field | type | required | default |
|---|---|---|---|
| `layer_index` | `int` | True | `None` |
| `show` | `bool` | False | `True` |
| `label` | `str or None` | False | `None` |
| `panel` | `int` | False | `0` |

### `SetData`

| field | type | required | default |
|---|---|---|---|
| `columns` | `dict` | True | `None` |

### `SetDpi`

| field | type | required | default |
|---|---|---|---|
| `dpi` | `int` | True | `None` |

### `SetEncoding`

| field | type | required | default |
|---|---|---|---|
| `params` | `dict` | False | `{}` |

### `SetFont`

| field | type | required | default |
|---|---|---|---|
| `params` | `dict` | False | `{}` |

### `SetGridStyle`

| field | type | required | default |
|---|---|---|---|
| `params` | `dict` | False | `{}` |

### `SetJournal`

| field | type | required | default |
|---|---|---|---|
| `name` | `str or None` | True | `None` |

### `SetLayout`

| field | type | required | default |
|---|---|---|---|
| `rows` | `int` | True | `None` |
| `cols` | `int` | True | `None` |
| `width_ratios` | `list[float] or None` | False | `None` |
| `height_ratios` | `list[float] or None` | False | `None` |

### `SetLegend`

| field | type | required | default |
|---|---|---|---|
| `show` | `bool` | False | `True` |
| `title` | `str or None` | False | `None` |
| `location` | `str` | False | `'best'` |
| `frame` | `bool` | False | `False` |
| `panel` | `int` | False | `0` |

### `SetLimits`

| field | type | required | default |
|---|---|---|---|
| `axis` | `str` | True | `None` |
| `lo` | `float` | True | `None` |
| `hi` | `float` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetMatrix`

| field | type | required | default |
|---|---|---|---|
| `name` | `str` | True | `None` |
| `values` | `list` | True | `None` |

### `SetPalette`

| field | type | required | default |
|---|---|---|---|
| `kind` | `str or None` | False | `None` |
| `params` | `dict` | False | `{}` |

### `SetPanelLabel`

| field | type | required | default |
|---|---|---|---|
| `label` | `str or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetScale`

| field | type | required | default |
|---|---|---|---|
| `axis` | `str` | True | `None` |
| `scale` | `str` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetSecondaryAxis`

| field | type | required | default |
|---|---|---|---|
| `label` | `str` | False | `''` |
| `scale` | `str` | False | `'linear'` |
| `limits` | `list[float] or None` | False | `None` |
| `panel` | `int` | False | `0` |

### `SetShare`

| field | type | required | default |
|---|---|---|---|
| `x` | `str or None` | False | `None` |
| `y` | `str or None` | False | `None` |

### `SetSize`

| field | type | required | default |
|---|---|---|---|
| `width` | `float` | True | `None` |
| `height` | `float` | True | `None` |

### `SetSuptitle`

| field | type | required | default |
|---|---|---|---|
| `text` | `str` | True | `None` |

### `SetTheme`

| field | type | required | default |
|---|---|---|---|
| `name` | `str` | True | `None` |

### `SetTicksStyle`

| field | type | required | default |
|---|---|---|---|
| `params` | `dict` | False | `{}` |

### `SetTitle`

| field | type | required | default |
|---|---|---|---|
| `text` | `str` | True | `None` |
| `panel` | `int` | False | `0` |
