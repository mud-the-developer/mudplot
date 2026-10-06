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

Each action copies the full spec; undo/redo replay history. Large inline data
and long histories therefore have a documented performance ceiling.
`mp.apply()` returns a new result without exposing partial results on failure.
`Plot.apply()` and `Store.dispatch_all()` are ordered individual dispatches,
**not batch transactions**. Listeners run after a committed transition; a
listener exception propagates and does not roll it back. The editors instead
validate and render prospective transitions before committing their state and
cached previews. `validate()` / `assert_valid()` remain the explicit contract
checks; rendering validates automatically.

## JSON and versions

Package/editor version **1.0.0** and serialized spec version **0.1** are
independent. A package release does not require a spec-version bump.

- Supported fields and JSON values round-trip without loss. Unknown dataclass
  fields under a recognized spec version are ignored by the Python loader and
  are **not** promised to survive a round-trip. Keep custom metadata elsewhere.
- Unknown spec versions fail explicitly. A future incompatible serialized
  shape needs a spec-version bump and migration support for previously
  supported saved files; additions with safe defaults need not change it.
- JSON is RFC-compliant: recursive duplicate keys, non-finite numbers, lone
  surrogates, non-string keys, and `$serde_json::private::Number` are rejected.
- Integers beyond 64-bit range are preserved structurally, not guaranteed to be
  renderable at arbitrary precision. Action envelopes use a string `"type"`.
- Input adapters normalize common missing values to `null`, date/time values
  to ISO strings, and NumPy scalars to Python values. Infinity, `Decimal`, and
  unsupported objects are not silently coerced. Duplicate column names fail.
- SQL values are forwarded through DB-API `params=`; mudplot does not
  interpolate them into a query.

## Dependencies and distribution

The declarative/state/JSON core has no required third-party dependencies.
Colour operations require NumPy; rendering requires NumPy and Matplotlib.
The 1.0 support floors are Python **3.10**, NumPy **1.23**, Matplotlib **3.8**,
and Rust **1.88** for the editor. These floors remain supported in 1.x;
a planned runtime-floor increase requires advance deprecation and a major
release. Critical security fixes may require tighter dependency bounds, with
an explicit changelog and installation notice.

GitHub releases contain a verified sdist and engine-only wheel, SHA-256
checksums, and OIDC build provenance. Published tags and assets are immutable;
corrections require a new release, not a moved tag or replaced asset. PyPI
publishing remains deferred until trusted publishing is configured.
