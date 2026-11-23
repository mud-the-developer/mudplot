# Paired density and empirical fields

These workflows use saved observations, weights, options and row identities.
They do not turn density into count height, use weights as sample replication,
or fit again after a viewport change. See [the frozen v2 catalogue](V2_SCOPE.md)
for qualification status; these local workflows do not close broader shared-axis,
semantic, layout or release rows.

## Paired histograms and a full-fit KDE overlay

```python
import mudplot as mp

d = {
    "x": [-2., -1., 0., .5, 1., 2., 3., 1.5],
    "y": [-1., 1., -.5, 1.5, .25, 2., -.5, -1.],
    "w": [1, 2, 4, 1, 3, 2, 1, 2],
    "site": ["left"] * 4 + ["right"] * 4,
}
p = mp.plot(d).hist2d(
    "x", "y", bins=mp.BivariateBinsSpec(x=[-3, 0, 1, 4], y=[-2, 0, 3]),
    stat="density", weights="w", colorbar=True,
    kde=mp.KDE2DSpec(weights="w", levels=[.5, .8], gridsize=32),
)
p.save("paired-density.svg")
```

For cell mass `C`, raw-coordinate area `A` and comparison in-bin mass `T`:

| Literal statistic | Cell value |
| --- | --- |
| `count` | `C` |
| `frequency` | `C/A` |
| `probability`, `proportion` | `C/T` |
| `percent` | `100*C/T` |
| `density` | `C/(T*A)` |

Both coordinates must be in range. Each bin is left-closed/right-open, except
that its final right edge is closed. Out-of-range rows stay in the source.
Missing required values and zero weights are excluded as paired rows before
fitting or tallying. Negative/nonfinite weights reject. An undefined normalized
histogram with no in-bin mass is not silently replaced by zero probability.

`common_norm=True` pools comparison mass; `False` uses the effective hue pool,
not an independent pool for every size/style tuple. Bin rules use the selected
observations, not weight magnitudes. `BivariateBinsSpec` requires separate logical
x/y choices; an old ambiguous flat list is not reinterpreted as paired edges.
Native cells use the true, possibly unequal edges and `H.T` orientation.

The overlay receives the **same selected paired cohort before range exclusion**.
It therefore retains rows outside the histogram bins. Its weights must inherit
or match the parent column and its `common_norm` must agree. Its own density/CDF
levels and colourbar units are not count-height rescalings. A statistic colourbar
belongs to the actual field mappable, with raw values/norm and exact raw labels
on a separate non-data calibration axis—even for subnormal positive values.
Several statistic bars share one owner-native lane, retaining separate raw norms,
ticks and citations. Only generated prose unit labels may wrap; authored labels,
mathematical tokens and exact raw tick strings are not shortened. Final backend
decoration bounds must fit the authored canvas or rendering rejects explicitly.
For stacked grid-owned bars, the measured lane reserves width once. Every
visible bar still contributes native bounds to final validation and tight export.
A generated unit on a single constrained-grid bar wraps at existing word
breaks only when its measured height exceeds the authored canvas. The unit
formula and raw calibration stay intact; the same final bounds checks apply.

## Named kernels, cumulative laws and composition

`gaussian` and `epanechnikov_product` share the same covariance-H meaning.
The compact kernel is variance-one Epanechnikov; in two dimensions it is the
product after Cholesky whitening, **not a radial/rotation-invariant kernel**.
The bandwidth matrix is `H = Σ_unbiased * (factor * bw_adjust)**2`, where
`factor` is Scott, Silverman or the finite numeric API factor; in 1D,
`h = sqrt(variance) * factor * bw_adjust`. Physical Kish size precedes ties.
Singular fields are omitted with the requested warning policy, never jittered.

```python
mp.plot(d).kde(
    "x", group="site", weights="w", kernel="epanechnikov_product",
    multiple="fill", common_grid=True, cumulative=True, fill=True,
).save("cdf-composition.pdf")

mp.plot(d).kde2d(
    "x", "y", weights="w", cumulative=True, level_kind="cdf",
    levels=[.2, .5, .8], gridsize=32, colorbar=True,
).save("true-joint-cdf.svg")
```

Univariate `layer`, `stack` and `fill` operate on a persisted common grid when
needed. Stack adds actual contributions. Fill divides them by their resolved
sum; compact-kernel true-zero regions are gaps, not uniform shares or fake zeros.
Cumulative stack/fill is a contribution/composition display, **not a population
CDF**. Two-dimensional stack/fill has no declared ordinate and rejects.

A joint KDE CDF integrates the original fitted law from minus infinity in both
coordinates. It is not rebased to finite-grid mass. The fixed absolute numerical
budget is `1e-6`; grouped `common_norm` amplitudes remain contributions rather
than hidden per-field renormalizations. Cut/clip selects queries/views only.
Gaussian rectangles use a signed Plackett integral with outward derivative and
exact-midpoint enclosures, and exact current-leaf dyadic totals. Exact-result
reuse belongs to one field and ends before native output. This is an absolute-error
contract, not arbitrary relative precision: unresolved source/numerical uncertainty
is an explicit error.

Logical `fit_scales=["data", "axis"]` chooses each coordinate's fit. An actual
log axis uses log10 regardless of display base; `density_space="data"` includes
the raw-density Jacobian and `"fit"` reports working-coordinate density. CDFs
never receive that Jacobian. No symlog/asinh/logit or absolute-calendar log fit is
inferred from raw primitive support. Native/log/date coordinates must remain
representable; unresolved support/precision is an error, not an epsilon shift.

## Explicit full-model HDR, not conditional grid coverage

```python
mp.plot(d).kde2d(
    "x", "y", weights="w", levels=[.8, .95], gridsize=17,
    hdr=mp.HDRSpec(scope="full", tolerance=.01),
    fill=True, line_width=0, colorbar=True,
).save("full-model-hdr.pdf")
```

Without `HDRSpec`, the old conditional finite-grid contour definition remains.
Full mode calibrates unknown, strictly ordered density cutoffs against the
original fitted law. Its native set is a documented union of guaranteed-inside
adaptive cells, not a falsely smooth grid contour. Nested requests retain
separate levels/disjoint earliest bands. Raw-density HDR after log fitting uses
the Jacobian for membership but still integrates probability in the original
fitted law.

The requested absolute conditional tolerance is positive and at most `.05`.
Support omission, integration/classification, source/transform, native geometry
and visible clipping are tracked separately under the stated IEEE/computed-model
assumptions. Both target-mass and HDR-region symmetric-difference bounds must
resolve. Visible clipped probability is reported as such, **not called p**.
Physical outlines are decorations, not additional probability mass. Unresolved
order, tolerance, coordinates or resources rejects the complete effect; no
level dropping, tolerance substitution or conditional fallback is used.

Within one live figure, layout and export draws reuse the fitted-geometry proof
only for the same native paths and axis policy, and only if the actual backend's
measured affine/serialization error fits the certified bound. Each draw checks
its own clipping and visible probability. Changed paths, axes or error bounds
require a new proof; unsupported topology or unresolved bounds reject the draw.
Reuse does not reset or increase the resource ledger.

## Explicit paired empirical CDF

```python
mp.plot(d).ecdf2d(
    "x", "y", bounds=[[-3, 4], [-2, 3]], weights="w",
    stat="percent", complementary=True, query_x=[0, 1], query_y=[0, 1],
    colorbar=True,
).save("joint-empirical.svg")
```

The lower orthant is `X <= qx AND Y <= qy`. Its strict complement is
`X > qx OR Y > qy`, **not joint survival**. Literal statistics remain
`proportion`, `percent`, `count`; no `probability` alias is added to ECDF.
Bounds/queries do not remove denominator observations. All interior source
knots, ties and queries are retained; cells are right-continuous, not smoothed.
Canonical source/mass is retained before ties and final float rounding; percent
is combined before rounding so a representable small jump is not erased.

## Coordinates, roles, live views and limits

- `orient="h"` swaps display roles only. Actual primary/y2 targets and declared
  per-coordinate clocks control conversion; probability/density is never a date.
- Temporal bin/clip/bounds/query coordinates follow the existing rule: ISO
  strings or canonical UTC days since 1970, **not** the numeric observation's
  `s/ms/us/ns/day` input unit. Numeric observations still require that explicit
  unit and origin. Density areas use canonical day widths in each clock dimension.
- SIZE is physical main stroke or cell/contour outline points—not area, mass,
  bin width or a weight. STYLE uses real dashes; only univariate ECDF has real
  observed-knot glyphs. HUE identifies raw field tint separately from statistic
  mappables. Scalar owned-role conflicts reject before candidate acceptance.
- Local `ReplaceLayer` edits remain local. `SetFacetTemplate` explicitly replaces
  fixed live cells and supersedes local overrides. Loading preserves saved views;
  rendering/editor previews recompute from saved observations/options, not by
  silently applying a whole-template replacement. N13 IDs/selectors stay stable.
- NEW paired/field requests retain at most 10,000 selected positive complete
  physical rows/layer, 256 raw-tuple fields and 64 categorical levels. Numeric
  raw values are not arbitrarily limited to 64 distinct values. Histogram has
  512 bins/axis; joint ECDF 512 edges/axis; KDE2D 256 nodes/axis and 16 levels.
- One NEW-figure ledger admits at most 2 billion composite units, 256 MiB total
  working/retained geometry/native-plan/artist storage, 1 million simultaneously
  live numerical pair scalars and 2 million native path vertices including
  closures. Full HDR has at most 65,536 active cells/current level and 48 cutoff
  updates plus the initial trial. No counter resets per field/level.
  Cohort/group construction, empirical edge/order plans and native probes are
  admitted before allocation; temporary construction storage ends before native
  output. Source labels and observation leaves remain borrowed, not copied.
- These are finite admission bounds, **not FLOPs, RSS or an SLA**. Actual backend
  RGBA buffers remain outside that allowance under the existing 40M-pixel rule.
  Old admitted plain/weighted/cumulative univariate routes and geometry-only
  identity Gaussian completions do not acquire gratuitous NEW guards. D01/C07
  ledgers remain separate. CLI/editor failures retain accepted complete output,
  source state and history rather than publishing a prefix result.
