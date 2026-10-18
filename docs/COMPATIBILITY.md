# Compatibility policy — mudplot 1.x

*[한국어 문서 / Korean docs: COMPATIBILITY.ko.md](COMPATIBILITY.ko.md)*

## Stable surface

The 1.x compatibility promise covers valid use of:

- Names exported by `mudplot.__all__`, including `Plot`, `FigureSpec`, `Store`,
  actions, JSON I/O, validation, palettes, references, rendering, and TeX helpers.
- The public `Plot` builder methods, properties, and their documented arguments.
- The `mudplot` / `python -m mudplot` commands: `capabilities`, `schema`, `docs`,
  `validate`, `apply`, `render`, and `migrate`, with the existing options.
- Supported FigureSpec JSON fields and action envelopes shared by Python, Rust,
  and agents. `schemas/` and the generated [reference](REFERENCE.md) describe
  this contract; the [plot gallery](PLOT_GALLERY.md) executes every layer.

New optional arguments, exported names, layer types, and capabilities may be
added in a minor release. Consumers should discover capabilities and tolerate
additional keys instead of depending on a fixed count or JSON key order.
A removal or incompatible change requires advance deprecation in documentation
and release notes, then a new **major** package version. Runtime warnings will
also be used where practical. Security fixes and corrections that reject
invalid inputs are exceptions; their impact is recorded in the changelog.

Private underscore-prefixed implementations, editor HTML/CSS, undocumented
attributes, and upstream Matplotlib internals are not part of this promise.
The Python/Rust editors are co-versioned, loopback-only source-tree tools, not
packages in the engine wheel. Use their matching release tag. Multi-user or
remote deployment remains outside their supported scope.

## Renderer and ownership

Matplotlib is the default and canonical renderer throughout 1.x. `mp.render()`
and `Plot.render()` return an open `matplotlib.figure.Figure`; `mp.save()` and
`Plot.save()` also return an open Figure on success. The caller owns it:

```python
import matplotlib.pyplot as plt
import mudplot as mp

plot = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").size(4, 3)
figure = plot.save("figure.pdf")
try:
    assert tuple(figure.get_size_inches()) == (4, 3)
finally:
    plt.close(figure)
```

Saving preserves the configured physical size; cropping requires `tight=True`.
Equivalent specs produce byte-identical PNG/PDF/SVG output in the **same mudplot,
Matplotlib, NumPy, font, and runtime environment**. This is not a promise of
identical bytes between versions, operating systems, or font installations.
Single-file JSON/PNG/PDF/SVG writes are atomic; PGF may produce raster sidecars
and is not a transactional multi-file bundle. Renderers fail cleanly when
numeric coordinates exceed floating-point range.

Optional future Plotly/Cairo adapters must not silently change the existing
default or the reducer/JSON contract. No speculative backend interface is
required to retain the current `FigureSpec → renderer` boundary.

Read-only and deny-delete locked Windows targets are isolated failure controls:
JSON/PNG/PDF/SVG replacement errors preserve prior bytes and remove owned staging.
Synthetic ENOSPC checks do not exhaust real storage. Successful Figures remain
open until the caller closes them; bounded caller-close/GC and handle/RSS traces
are not universal native-backend or long-session leak-freedom certificates.

## Shared axes and log domains

Figure `all`/`row`/`col` sharing follows native Cartesian axis linking: the last
panel drawn with explicit bounds updates that shared group, including inverted
bounds. Independent y/y2 settings and labels are not shared. Named `share_id`
links explicit nonadjacent axes and rejects conflicting limits/scales or mixing
with figure sharing modes. Polar/3-D and grid density axes keep their documented
separate scopes.

Legacy line/scatter log axes retain raw values and delegate nonpositive clipping
to Matplotlib's native transform. Typed statistics/native categories reject
invalid selected domains or derived interval endpoints rather than substituting
positive values. Legacy `c` normalization stays linear, independent of log
measurement axes. Typed heatmap `norm="log"` supports positive unmasked cells and
bounds; explicit masks exclude nonpositive cells without replacing raw values.
Heatmap cell axes stay linear; unsupported colour norms are rejected.

Observed Matplotlib3.8 linear constant1e308 image resampling emits two overflow
guard warnings in the floor regression; sampled pixels still match norm/RGBA and
raw values remain unchanged. Warnings-as-errors aborts export, retaining previous
bytes and cleaning owned resources. This is a documented backend warning, not a
blanket suppression, colour-data rewrite or all-extreme-range rendering promise.

## Overlays and annotation opacity

Raw bands keep boundary row order, including duplicate or unsorted x; no automatic
sorting/aggregation is implied. Grouped bars retain each observed signed value and
uncertainty at its dodged center; stackplot uses its native zero-baseline signed
cumulative definition. Existing length/error-domain validation stays explicit.

Annotation non-default alpha applies to both text and arrow on the selected axis.
Default alpha1 retains legacy opacity embedded in RGBA colours. Native artist
z-orders/clip policies remain: line2, point/band1, text/annotation3; cross-type
priority is not a new layer-order override. An off-axis or fully transparent
artist can exist without adding visible pixels. No new public zorder/clip option
or axes/figure-coordinate annotation mode is introduced here.

## Editor coordinate frames

Text/annotation anchors are data coordinates on their selected primary or y2
axes. Python editor handles use the actual rendered axis limits/scale, including
log and inverted axes, not the primary y range for every layer. Explicit title
positions use axes fractions; explicit legend anchors use figure fractions.
Changing size/DPI or selected panel does not turn one coordinate space into
another. Drag/nudge dispatch existing actions and retains ordinary undo/redo/JSON.
Non-Cartesian layer restrictions and preview geometry limits remain separate;
this does not add axes/figure annotation modes or native-editor control parity.

## Python editor response delivery

Rendering/commit remains serialized by the local session lock. HTMX HTML replies
carry an additive `X-Mudplot-View-Generation` for UI delivery ordering; a page
ignores fragments older than the latest generation it has already displayed.
Requests/actions are not dropped or turned into a new reducer/spec revision API.
Undo/reset/open/errors retain increasing reply order, not history-cursor order.

Generation is ephemeral local view state, not authorization, persistence or live
cross-tab collaboration. Reload the page after restarting the server. Replies
without the header keep legacy handling; JSON/spec/content-type contracts remain
unchanged. Failed and delayed render cases still use the documented candidate
state/preview transaction boundary.

## Automatic layout limits

With adaptive layout enabled, automatic panel titles/suptitle and named outside
legends are checked after drawing. Remaining canvas overflow or mutual overlap
emits an actionable `UserWarning` without changing the requested canvas, spec or
font size. Unbroken tokens may need explicit line breaks; enlarge the figure or
reduce text/font size when content cannot fit. Negative working rectangles are
not sent to the layout solver.

Manual/dragged text or explicit legend anchors remain caller-owned, not forcibly
moved. The warning is a measured bbox diagnostic, not universal legibility or
all-artist collision detection. Callers may promote warnings to errors; failed
single-file exports then retain the previous output and close owned Figures.

## Style ownership and preview resolution

Owned render/save restores caller rcParams after both success and failure. Repeated
style/journal output is compared with an independent process under equivalent
ambient rc settings; a different caller environment is not a byte-identity promise.

Automatic layout padding is0.02inch at every DPI (the former6pixels at300DPI).
The original spec/DPI/line widths remain independent of capped editor pixels.
Measured150/300DPI dense geometry and600→200DPI simple preview positions are within
0.02inch here, while75DPI dense geometry still has larger backend/layout residuals.
Do not infer exact all-DPI WYSIWYG from these bounds; use adequate preview resolution.

## Mixed guides

Named outside-right legends beside a secondary y-axis use measured visible tick/
label/offset-text space with a physical offset, not a fixed axes-width multiplier.
Manual anchors remain caller-owned. Constrained layout still allocates the fixed
canvas; dense combinations may need a wider figure and impossible fits warn.

Repeated explicit ungrouped point/line guides (2-D/3-D) with the same axis, x/y/z,
label and citation/href share the first legend handle. Grouped/semantic guides keep
their existing identity handling: raw `1` and `"1"`, different data columns, axes,
references and marker sources are not merged just because visible strings match.
No spec/source/style fields are rewritten by this guide policy.

## State and action semantics

`FigureSpec` remains a mutable dataclass/list graph. `reduce()` preserves its
inputs and performs no I/O; it is not a persistent immutable data structure.
`Plot.spec`, `Store.state`, history, dispatch results, and listener arguments
are defensive snapshots of supported spec/action data. Change state through
actions, not by mutating a returned snapshot.

Panel/layer indices are nonnegative plain integers, not bool/float aliases.
Panel-creating actions retain automatic extension; edits require an existing layer.
Reduction may build missing column/matrix references without effects; explicit
validation and render validation reject them before drawing.

Each action copies the full spec; undo/redo replay history. Large inline data
and long histories therefore have a documented performance ceiling.
`mp.apply()` returns a new result without exposing partial results on failure.
`Plot.apply()` and `Store.dispatch_all()` are ordered individual dispatches,
**not batch transactions**. Listeners run after a committed transition; a
listener exception propagates and does not roll it back. The editors instead
validate and render prospective transitions before committing their state and
cached previews. `validate()` / `assert_valid()` remain the explicit contract
checks; rendering validates automatically. The Python editor starts a fresh
history on open/reset. The Rust editor retains open/reset as undoable snapshot
transitions; new successful edits clear redo in both editors. These existing
history policies differ and are not a promise of identical UI history. Rust
reset returns the editor's startup default, not the last imported document.
Neither editor binds an imported filename for automatic overwrite or tracks a
separate persistent dirty-bit/save-target feature; downloads export current state.
An equal-value action still records an event/snapshot and clears redo. Listener
and undo semantics must not be silently removed by a no-op optimization.

Legacy raw group masks use original Python values, without NumPy string dtype
inference. Strings and numbers remain separate; default numeric equality still
merges `1`, `1.0` and `True`. Explicit ordered raw semantics retain typed bool/
numeric keys. Raw null is a legacy group, unlike statistical missing-row removal;
an empty group label may be unlabeled. Display captions remain `str(key)`, so
distinct types may have identical captions; normalize ambiguous IDs before plotting.
Raw line paths retain row order and duplicate x; lineplot aggregates per x and
applies its explicit sort policy. Empty raw line/scatter can be valid, whereas
statistical layers reject no usable observations and singletons omit undefined intervals.

## Journal and TeX sizing priority

The five `TEX_PRESETS` contain repository assumptions for typical TeX geometry,
not a fresh certification of every publisher guideline. `columns=1` uses column
width; `columns=2` uses text width, with TeX72.27pt/in converted to physical inches.
Default save preserves that canvas; SVG/PDF use72graphics points/in and raster
pixels quantize within one pixel at the requested DPI. Preview is not the only
consumer of sizing; the render and files use the same spec dimensions.

Physical size follows the last `.journal()` conventional-size / `.tex_size()` /
`.size()` action. Active journal registered rc font/linewidth keys take priority
over theme rc fields regardless of action order. `.journal(None)` clears that
style override without changing size; explicit font fields then apply. TeX sizing
sets body, label, title and tick sizes separately, so setting only body `size`
does not replace an already explicit `label_size`. No new override metadata or
render-order policy was added.

## Owned rendering concurrency

mudplot serializes its Matplotlib effects within a process with one reentrant
lock: API render/save, TeX preview, Python editor preview/placeholder/export and
site/gallery rendering. Different owned requests keep their serial state/bytes;
this is isolation, not parallel rendering throughput. Rust requests also have
session serialization and separate Python child processes.

A returned open Figure remains caller-owned after the function releases the lock.
Direct pyplot/Figure draw/save/close, Store mutations, concurrent builds targeting
the same directory and arbitrary external Matplotlib calls need caller coordination.
For parallel rendering prefer independent spawned processes; do not infer safety
for forking during threaded rendering or sharing mutable Figures.

## JSON and versions

Package/editor version **1.0.0** and serialized spec version **0.1** are
independent. A package release does not require a spec-version bump.

- Supported fields and JSON values round-trip without loss. Unknown legacy
  dataclass fields under a recognized spec version are ignored by the Python
  loader and are **not** promised to survive a round-trip. Keep custom metadata
  elsewhere. New `StatSpec` objects reject unknown options (such as arbitrary
  callable operations) so the requested calculation cannot silently change.
  Weighted/unit resampling options are supported only in their documented scope.
- Optional values are not uniformly synonyms. Omission chooses the model default;
  explicit null is retained where nullable. `StatSpec.errorbar` defaults to `"ci"`
  and `LayerSpec.inner` to `"legacy"`, unlike explicit null. Explicit marker size0
  stays0 rather than becoming the automatic point size; omitted/null defaults stay
  unchanged. Where a layer accepts marker/line-style options, explicit `""` keeps
  its no-marker/no-line meaning instead of selecting the automatic encoding; it is
  not null. Layer-specific restricted styles (for example KDE/ECDF) still validate
  their own supported choices. The structural field table is not all-field UI/CLI/
  Rust parity approval; the20-case render-token fixture covers only its stated scope.
- An omitted spec version uses the current embedded default in both Python and
  Rust; explicit null or malformed versions are not omissions.
- Unknown spec versions fail explicitly. A future incompatible serialized
  shape needs a spec-version bump and migration support for previously
  supported saved files; additions with safe defaults need not change it.
- JSON is RFC-compliant: recursive duplicate keys, non-finite numbers, lone
  surrogates, non-string keys, and `$serde_json::private::Number` are rejected.
  Rust checks original decoded property names, including Unicode escapes, so
  serde's big-number adapter cannot reinterpret literal reserved-key objects.
  The reserved spelling inside an ordinary string value remains valid text.
- Integers beyond 64-bit range are preserved structurally, not guaranteed to be
  renderable at arbitrary precision. Action envelopes use a string `"type"`.
- Input adapters normalize common missing values to `null`, date/time values
  to ISO strings, and NumPy scalars to Python values. Infinity, `Decimal`, and
  unsupported objects are not silently coerced. Duplicate column names fail.
  Positional row widths must match the first row; DB result row widths must
  match cursor description. Malformed rows fail with their index/expected width
  before pivoting, never silently truncating extra values or padding short rows.
  Every record must be a mapping; strings/bytes/mappings are not positional or
  DB row sequences. Wrong row types report their index, not character/key data.
  Sparse record keys still use first-seen column order and fill missing values
  with null. Unequal column lengths remain intact at ingestion and are rejected
  by validation before rendering or an editor commit, rather than resized.
- Only recognized floating/temporal NumPy or pandas missing scalars normalize
  to null; arbitrary object self-inequality and Decimal NaNs are not sentinels.
  A scalar `.item()` conversion follows only supported plain/date representations,
  not unsupported same-type or alternating object chains. Complex/extended-
  precision unsupported values remain objects and fail strict JSON rather than
  rounding, stringifying, becoming null or recursing indefinitely. This is not
  a sandbox for caller-provided Python methods.
- NumPy datetime64 scalars/columns/rows retain their dtype until ISO conversion,
  including ns/ps/fs/as precision and NaT→null, rather than becoming epoch integers.
  Existing coarse formats and actual numeric epoch columns remain unchanged.
  Polars datetime(ns) uses its native formatter and parse/equality verification;
  a non-lossless timezone representation fails instead of emitting rounded values.
  Ambiguous 2-D datetime columns fail; pass a 2-D array as row input instead.
  Arrow temporal conversion follows upstream safe conversion rules (nanoseconds
  may require pandas); an unsupported conversion can fail rather than truncate.
- In raw line/scatter categorical x conversion, null coordinates remain missing:
  lines break and scatter rows are masked, without a fabricated `"None"` category.
  An actual string `"None"` remains a category. ISO date strings follow the same
  categorical path here, not a newly introduced continuous date-axis contract.
  Statistical layers select their usable observations separately; source rows
  and missing values remain in the spec.
- SQL values are forwarded through DB-API `params=`; mudplot does not
  interpolate them into a query. For connection+query ingestion, the adapter
  closes the cursor it creates (when close is supported), including failures.
  A caller-provided executed cursor and its connection remain caller-owned.
  The adapter does not commit or roll back; close errors propagate rather than
  silently succeeding, with an earlier failure retained as exception context.

## Font availability and Unicode

Font discovery is an optional render effect, not dependency-free core validation.
Requested font/text values stay in the spec; the backend can log missing-family,
weight fallback or missing-glyph diagnostics. Inspect those alongside the output.
A family being installed does not mean it covers every glyph: on the measured
Windows host Malgun Gothic covered Hangul but lacked U+2212, while Noto Sans KR
covered this corpus and logged a normal-weight fallback to100. DejaVu Sans reported
missing Hangul; a deliberately absent family fell back visibly in font logs.

No font binaries/downloader or automatic minus substitution is added. Tests for
selected system CJK fonts skip explicitly where unavailable, while missing-family/
glyph cases remain separate. File hashes and glyph indices identify this measured
environment, not cross-OS/font-version byte identity or universal typography.

## String contexts

HTML editor values/drafts and SVG text/href are escaped as data; a single decode
recovers the original quotes, ampersands, backslashes and Unicode, not extra
script/event nodes. Permitted Matplotlib mathematics remains mathematics.

Explicit PGF labels follow the backend's trusted TeX grammar, not universal plain
text escaping. For example raw `A & B` fails TeX measurement, while `A \\& B`,
explicit harmless macros and math compile. Caller/document TeX encoding and page
size still matter. Citation keys and hrefs have their separate strict validation;
they do not admit arbitrary TeX macros. No implicit all-format rewriting or
untrusted-TeX sandbox is introduced.

## Palette report scope

`Palette.report()` evaluates the exported8-bit HEX sRGB colours, including final
quantization, and exposes `evaluation` for representation, normal vision, selected
CVD types, Machado2009 full severity1 and the existing ΔE00≥8/L*gap≥3 thresholds.
Float `min_delta_e()`/`min_lightness_gap()` evaluate mapped float sRGB; nominal
LCH design coordinates are not output quality. Float colormaps can differ slightly
from the HEX report. Existing result keys remain, with additive conditions.

These measured flags are not universal printing/accessibility certification or a
new preset guarantee outside the documented category count. An N+1palette can pass
or fail its actual metrics. Deterministic farthest-point sampling uses `hue_start`
and first remaining candidate on exact ties; no RNG seed parameter is added.

## Greyscale and redundant patterns

Greyscale is a linear-sRGB relative-luminance display proxy using Y weights
0.2126/0.7152/0.0722, then sRGB re-encoding, not every printer/viewer prediction.
Equal nominal L* does not give categorical greyscale separation. Default hatch6,
marker8 and line-style4 cycles are finite; paired marker/dash sequences repeat
after8groups, not32. Artist and legend cues are tested together across panels.

At fixed one-column width,0.6pt strokes/2pt markers and hatches can complement
colour;6alpha.18bands still blend strongly in greyscale. Inspect the real size,
use fewer bands/categories, boundary strokes/direct labels or separate panels.
The committed comparison is an agent visual review of synthetic renderings,
not printer/observer testing or accessibility certification.

## Polynomial numerical limits

Legacy and typed polynomial fits normalize predictor and response units before
covariance calculation, then restore original units. This prevents a small/large
response from silently collapsing or losing its confidence band. The interval is
still the documented normal-approximation **mean-fit** band, not a prediction
interval. Rank warnings, arithmetic faults and nonfinite predictions are fit
errors with causes, not a pseudoinverse fallback or a fabricated valid band.
Finite computation at extreme units does not guarantee Matplotlib can lay out
ticks or display those axis ranges. Missing/constant/insufficient inputs keep
existing explicit validation; no new model assumptions or schema fields.

## Dependencies and distribution

The declarative/state/JSON core has no required third-party dependencies.
Colour operations require NumPy; rendering requires NumPy and Matplotlib.
Missing dependencies at public colour/render/save/preview, CLI render and palette
Matplotlib-adapter boundaries raise an install hint for `mudplot[color]` or
`mudplot[render]`. Only the expected missing module is relabelled; unrelated
transitive/compiled-import errors keep their original diagnosis and exception cause.
The colour extra does not force Matplotlib. The browser extra installs Playwright,
not its browser binary; `playwright install chromium` remains a separate step.

On the observed Windows host(PowerShell7.6.7,LongPathsEnabled1), short cwd plus
336-character absolute file paths passed API/console/module/lock/render checks.
Console startup from a>260-character cwd failed; use a short cwd with absolute
paths. Separate controls found that the observed uv-created venv could not start
its print program with a321-character `TMP`, even with `-S`, while base Python
worked and long `TEMP` with short `TMP` worked. Pipe/file capture made no difference.
The same selected venv then passed bridge startup/open/action/PNG with short `TMP`
and long `TEMP`; no interpreter fallback is performed. Keep cwd/`TMP` short and
test the selected interpreter under the intended environment before starting the
editor. These are measured host/interpreter limits, not universal thresholds or
process-tree cleanup guarantees. No system long-path setting is changed by mudplot.
Unreleased advanced robust/logistic/LOWESS effects use the optional `regression`
extra with statsmodels>=0.14.1 (also included by all/dev), loaded only at fit time.
Ordinary polynomial/residual/log-x rendering needs no statsmodels. This extra
is tested on Python 3.10/NumPy1.23/Matplotlib3.8 with statsmodels0.14.1; it does
not change the mandatory dependency contract or already-published assets.
Unreleased clustermap uses a separate cluster extra(SciPy>=1.10, all/dev included),
verified with SciPy1.10/Python3.10/NumPy1.23/Matplotlib3.8. Pure clustering configs
and checked linkage JSON remain standard-library-only.
The 1.0 support floors are Python **3.10**, NumPy **1.23**, Matplotlib **3.8**,
and Rust **1.88** for the editor. These floors remain supported in 1.x;
a planned runtime-floor increase requires advance deprecation and a major
release. Critical security fixes may require tighter dependency bounds, with
an explicit changelog and installation notice.

GitHub releases contain a verified sdist and engine-only wheel, SHA-256
checksums, and OIDC build provenance. Published tags and assets are immutable;
corrections require a new release, not a moved tag or replaced asset. PyPI
publishing remains deferred until trusted publishing is configured.
