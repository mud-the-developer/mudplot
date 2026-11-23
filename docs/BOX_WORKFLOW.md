# Box observations and supplied summaries

[한국어](BOX_WORKFLOW.ko.md) · [Runnable complete example](../examples/box_workflow.py)

C03 extends the existing `box` layer. `Plot.bxp` is a builder for its explicit
columnar-summary mode, not a second renderer or a collection of opaque kwargs.
The package stays 1.1.0 and the JSON schema stays 0.1. These local box features
do not complete the wider F01/F02/G01 catalogue or final product qualification.

## Raw observations and median confidence intervals

```python
import mudplot as mp

p = mp.plot({"method": ["A"] * 6, "response": [1, 2, 3, 4, 5, 30]})
p.box("method", "response", median_ci={"level": 90, "n_boot": 1001, "seed": 19},
      cap_fraction=0.8, showmeans=True)
p.labels(y="Measured response (mm)", title="90% bootstrap median CI")
```

`median_ci` is a seeded percentile bootstrap of **sample medians**, not an
observation percentile interval, a mean CI, or a whisker rule. Its presence turns
notches on when `notch=None`; explicit `notch=False` conflicts. Whiskers remain
native IQR/percentile observed endpoints, controlled separately by `whis`.

Only rows missing required category/value/hue/semantic roles are excluded.
Within each logical category × raw role-tuple samplecell, resampling selects
original observation rows with replacement. Each cell starts a private
`default_rng` with the stored seed. This deliberately uses a common resampling-
index schedule: changing facet/category traversal does not change an identical
cell's result. The process-wide NumPy RNG is not touched. There is no new
weighted/unit bootstrap or inference from supplied quartiles.

The level must be in `(0,100)` and `n_boot` in `1..100000`. Seeds use the existing
statistical policy: a nonnegative integer, excluding bool, with no extra secret
upper bound. Resampling uses the existing one-million-element chunk target;
selected row counts are bounded as described below. Linear percentiles preserve
selected endpoints, including tiny selected observations. Even-median midpoint
and near-underflow interpolation avoid needless overflow/underflow; this is
float64 arithmetic, not an arbitrary-precision guarantee. Mean/sum arithmetic
has not been replaced.

A singleton remains a real degenerate box. Its requested bootstrap notch is
omitted with a warning, not replaced by a Gaussian approximation. Empty reserved
cells contain no invented box or interval.

`stat_scale="data"` computes in raw observation coordinates (explicit dates use
absolute UTC days). `stat_scale="axis"` on a log measurement axis computes in
log10 coordinates and inverse-maps the native geometry once. It does not rewrite
source values, IDs, ordering, or units. The legacy Gaussian notch remains the raw
box behavior when no bootstrap request is made.

## Supplied columns, not copied summary values

```python
columns = {
    "method": ["A"], "median": [2], "q1": [1], "q3": [3],
    "lo": [0], "hi": [4], "mean": [2.1],
    "ci_low": [1.5], "ci_high": [2.5], "declared_fliers": [[5]],
    "source_id": ["original-summary-row"],
}
q = mp.plot(columns).bxp(
    "method", "median", q1="q1", q3="q3", whislo="lo", whishi="hi",
    mean="mean", cilo="ci_low", cihi="ci_high", fliers="declared_fliers",
    showmeans=True, notch=True, cap_fraction=0.8,
)
```

`bxp(category, median, ...)` mirrors two-column `box`. The one-column spelling
`bxp(median, group=category, ...)` mirrors the old value/group form and its
one-based category positions. Summary options reference existing `DataSpec`
columns; no second table is stored in the layer. Data columns may have nullable
summary fields on non-summary rows, so raw and summary views can share the same
original table and IDs.

Every selected summary samplecell has one unique row. Duplicate summaries for
the same category/effective-hue/raw-role tuple reject; they are not averaged or
deduplicated. Required fields satisfy
`whislo <= q1 <= median <= q3 <= whishi` in absolute observation units.
Required missing fields drop listwise. Optional missing fields **never delete an
otherwise valid box**:

- A missing mean reference/value means unavailable. `showmeans=True` requires
  an available finite mean in every selected valid summary; it never substitutes
  the median. A supplied mean is not clipped to the box or whiskers.
- CI references come together. Two missing values mean unavailable; a one-sided
  missing pair is malformed. `notch=True` requires available finite ordered
  endpoints. Intervals are not clipped to quartiles or forced to contain the
  sample median. The library assigns no confidence level/method to supplied
  endpoints; label their actual provenance explicitly.
- Fliers reference a list-valued JSON column. `[]` means explicitly supplied no
  fliers; `None`/no reference means unavailable, not proof of no outliers. Every
  supplied value must be finite and strictly outside the closed whisker interval.
  Default summary rendering draws available declared fliers only. Explicit
  `showfliers=True` requires available lists; no observations are reconstructed.

Supplied summaries cannot request bootstrap or a replacement `whis` rule.
Explicit category/measurement clocks convert all relevant summary endpoints and
nested flier values on the correct primary/y2 observation axis. Log-visible
geometry must be positive. Category native/log/date spacing, orientation, shared
axes, facets, and live recipes use the existing geometry/clock boundaries.

## Caps and component precedence

`cap_fraction` is a finite nonbool fraction in `[0,1]` of the **final body width
after dodge and gap**, measured in category working coordinates: ordinal,
numeric, native log10, or UTC days. It is not measurement units, points, density,
or mass. Zero retains collapsed native cap artists. Omission retains native
half-body caps. A requested cap fraction enables caps, like `components.cap`,
but does not enable an unrelated hidden body.

Raw boxes inherit absent `whis`, notch/mean/flier visibility and body/cap
visibility from the actual native/theme context at the effect boundary. Explicit
layer controls, median CI, mapped body properties and component requests override
only their respective controls. Supplied-summary optional mean/CI/flier marks
retain the availability policy above rather than being fabricated from ambient
rc defaults. Native `showbox=False` retains real whiskers/median/means/fliers and
has no fake body. Zero-width dashed patches keep fill/hatch; zero-width lines use
native no-line geometry without hiding independently requested markers.

`hue_components` is a typed list, not string-coerced arbitrary kwargs:

```python
styled = mp.plot({
    "category": ["A"] * 4, "response": [1, 2, 3, 4],
    "method": [True, True, 1, 1],
}).box("category", "response", group="method", hue_components=[
    {"level": True, "components": {"cap": {"color": "red", "line_width": 2}}},
    {"level": 1, "components": {"median": {"color": "blue"}}},
])
```

Keys follow the shared `category_key` identity: bool and number differ; equivalent
numeric keys are not duplicated. Keys must be observed or explicitly reserved
categorical hue levels. Unknown/duplicate keys reject. Numeric continuous hue
cannot be restyled by arbitrary per-value pseudo-bins. Effective hue comes from
the distribution roles: in the one-column form, legacy `group` is **category**,
not an independent hue. A semantic `hue` may provide that independent channel.

Precedence is native/theme → layer shorthand → owned semantic properties →
global components → fieldwise per-hue components. A missing component property
inherits; empty hatch explicitly disables it. Overrides of an actually mapped
property reject instead of silently contradicting guides. Hidden mean/flier
constraints retain the existing typed component rules.

## Shared hue, body stroke and real flier glyphs

The existing `SemanticSpec` shares original-row domain pools and logical-panel
colourbar intent with the accepted families. Raw hue/size/style tuples partition
samples; role values are never averaged. Domain row IDs deduplicate across
layers, but each layer retains its actual statistical/point view.

Owned properties are deliberately narrow:

- **Hue:** body face fill only. Body edges and other component colours remain
  independently editable. Numeric hue uses the same normalized nondata
  colourbar/raw labels and constant midpoint swatch as other families.
- **Size:** body outline linewidth in physical points only. It is not body width,
  mass, flier/mean marker diameter, or whisker/cap/median linewidth. Those other
  component properties remain independent.
- **Style:** body outline named dash **and actual flier glyph**, always through
  serialized `SemanticSpec.markers`, including its default cycle. There is no
  detection of which Python keyword/dictionary key was omitted. The dash uses
  supplied `dashes` or the finite default cycle; enough distinct dashes/markers
  are required. No flier observations are invented to demonstrate a mapping.

Consequently mapped body fill/linewidth/dash and mapped flier marker reject
conflicting scalar/global/per-hue overrides. Harmless whisker/cap/median styles,
body edges, and independent mean/flier diameters/edge/face properties remain
legal. Guides use actual native box/line component styles, not point proxies
masquerading as boxes. A style guide declares the flier mapping even if no data
fliers are observed.

Two-column independent legacy group/hue order or `c` cannot combine with
`SemanticSpec`; use its hue/order fields. In the one-column form the legacy group
remains category and is compatible with a separate semantic hue. Applicable
vertical/horizontal, numeric/native/log/inverted/date and primary/y2 paths are
connected for boxes; this does not relax unsupported combinations in other
families.

## Explicit live transactions and resource limits

Existing `facet(..., live=True)` / `facet_template(...)` recipes retain fixed
selectors, resolved slots, saved per-cell views and compatible ratios. Local
edits remain local; a later explicit whole-template transaction replaces all
intended cells, including reserved empty cells. Loading JSON does not silently
regenerate saved views. A changed category channel with `order=None` infers its
new levels; a supplied literal old order remains a literal selection. One-column
category identity is the group/category source, not the measurement column.

New advanced/summary work rejects before native artist/bootstrap allocation:

- At most **256 drawn box samplecells per layer**.
- At most **10000 selected source rows**, and independently **10000 total
  declared flier values**. These are two bounds, not an either/or exemption.
- Existing semantic 10000-row/64-level/256-role-tuple, facet64, figure256-panel/
  1024-layer and bootstrap100000 limits remain. No curve/depth limit is lifted.
- Legacy no-new-request box limits/JSON/default geometry remain unchanged. The
  new native operation bound is profile-backed, not an SLA or downsampling.

Run `python examples/box_workflow.py artifacts/v2_box`. Save `.mplot.json` and
reopen through `Plot.from_json`, or use
`python -m mudplot render figure.mplot.json figure.svg`. Rust's registered `box`
layer JSON form edits `box.summary`, `box.median_ci`, `box.cap_fraction` and
`box.hue_components`; RAW ACTION supports the same live transactions/history.
Invalid edits retain the accepted spec/preview/history. Rust `/fig.png` remains
its capped cached preview; PDF/SVG are actual vector exports. Use the installed
CLI/API on the same downloaded JSON for a full requested-DPI PNG.
