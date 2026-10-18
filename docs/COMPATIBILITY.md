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
