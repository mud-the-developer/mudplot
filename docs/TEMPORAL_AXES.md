# Explicit temporal axes (v2 work in progress)

[한국어](TEMPORAL_AXES.ko.md) · [F02 scope](V2_SCOPE.md)

Dates remain ordinary strings until you explicitly request a temporal axis:

```python
import mudplot as mp

p = (
    mp.plot({"time": ["2026-01-01", "2026-01-02", "2026-01-11"],
             "signal": [2, 3, 4]})
    .line("time", "signal", marker="o")
    .date_axis("x", timezone="UTC")
    .labels(x="Observation date (UTC)", y="Declared signal")
)
p.save("temporal.svg", layout_policy="smart")
```

The coordinate gaps are one and nine days, not two equal categorical gaps.
Data values, source ISO offsets, row order and semantic columns remain intact.
Derived coordinates never replace the saved data.

## Clock and units

- ISO calendar dates and datetimes are supported, including fixed UTC offsets.
  Aware inputs compare by instant. Naive values require an explicitly declared
  `timezone="UTC"` or a fixed offset such as `"+05:30"`.
- With no timezone declaration, only aware inputs are accepted and display uses
  UTC. The host's local zone is never inferred. IANA zones, leap seconds,
  unknown negative-zero offsets and unsupported ISO spellings reject clearly.
- Numeric timestamps require **both** `unit` (`s/ms/us/ns/day`) and an ISO
  `origin`. Neither is guessed from magnitude:

```python
import mudplot as mp

p = (
    mp.plot({"elapsed": [0, 86400, 864000], "signal": [2, 3, 4]})
    .scatter("elapsed", "signal")
    .date_axis("x", unit="s", origin="2026-01-01T00:00:00Z")
)
p.save("numeric_clock.svg")
```

- Plotting/statistical coordinates are always UTC days since 1970, independent
  of Matplotlib's configured global epoch; that epoch is not changed.
- Density is per day for each temporal observation dimension. Numeric axis
  limits and literal geometry positions use the same canonical day coordinates,
  **not** the numeric timestamp's input unit.
- Use dependency-free `mp.temporal_coordinates(values, ...)` to derive explicit
  day positions for limits, reference events and annotation anchors.
- Supported input precision is microseconds. Extra zero fraction digits are
  harmless; finer nonzero information, unsupported calendar range or loss in
  float day coordinates raises rather than silently truncating. Numeric float
  representatives must roundtrip the original numeric value.
- Source values stay unchanged, including integer low bits and original offset
  spellings. Microsecond conversion is a derived view, not input rewriting.

## Connected paths

The current implementation connects Cartesian linear x/y/y2 axes for applicable
raw line/scatter/strip/bar/errorbar/band/hexbin/stackplot/rug, native
stem/stairs/event/interval, bar/point/count/line estimators, box/violin/boxen/swarm,
hist/KDE/ECDF, regression and hist2d/KDE2D paths. Horizontal roles and enabled y2
are selected explicitly; existing unrelated primary-axis restrictions remain.

Date categories use real elapsed spacing. A facet with inferred date slots
keeps the first eligible original spelling of each UTC instant. A resolved or
explicit order selects any eligible spelling of each listed instant and can
reserve an unobserved instant. Explicit orders must not repeat an instant.
Saved selectors and source spellings are unchanged. Same-instant observations
are only aggregated where the mark already computes a statistic by predictor.

Absolute date-valued responses support mean/median/min/max, not sum/count.
Residual and logistic regression outputs cannot use a calendar response axis;
temporal predictors remain valid. Default histogram/KDE calls retain their
legacy settings and observations. Calendar ticks follow the declared local
midnights while the data coordinates remain UTC instants.
A count/probability/density axis cannot become a calendar axis. Date axes require
linear Cartesian scales; unsupported families reject instead of drawing ordinal
dates while claiming temporal support.

Numeric bins/clips use canonical day units. Explicit ISO histogram edges and
univariate KDE/violin clips are converted under the declared timezone contract;
mixed ISO/numeric bounds reject. Other configuration, including bivariate bounds,
must use its documented numeric day coordinates. Supplied stairs may use ISO
edges; their heights are not re-estimated. Event offsets/lengths, stair
baselines and interval-band geometry remain literal axis coordinates.

Absolute uncertainty endpoints share the coordinate clock. Numeric timestamp
error columns and interval durations use the declared input unit, converted to
days **without adding the origin**; ISO timestamp magnitudes/durations use days.
For example, a 3600-second error remains one hour, not origin plus one hour.
Original columns remain unchanged. Invalid signs, precision or missing columns
are reported before publication.

## Selection and sharing

Facet selection, typed raw group orders, semantic hue/size/style orders, missing
observations and applicable zero weights are respected before time parsing.
Facets still require a valid completed template, as before; select facets before
activating a restriction that makes excluded rows invalid.

Coordinate aliases retain raw hue/size/style/group columns, even if a role uses
the same column as time. Shared mappings keep original selected row identities.
Shared axes must agree on temporal presence and effective display timezone;
different declared input units/origins can still describe the same day axis.

## Secondary y

Vertical `hist()`, `kde()` and `ecdf()` accept `axis="y2"`. Their observations
still use the shared x axis, including its declared date clock; only the numeric
mass, probability or density moves to y2. Typed distributions retain their
linear response-axis contract. Horizontal distributions do not route to y2,
and a mass/probability/density axis cannot be temporal.

```python
p = (
    mp.plot({"time": ["2026-01-01", "2026-01-02", "2026-01-11"],
             "signal": [2, 3, 4]})
    .line("time", "signal", marker="o")
    .secondary_yaxis("Observation density (day⁻¹)")
    .hist("time", bins=3, stat="density", axis="y2", alpha=0.25)
    .date_axis("x", timezone="UTC")
)
```

Transparency is explicit: opaque secondary fills can obscure primary marks or
legends. The example does not change the default renderer's layering policy.
Semantic scatter retains its applicable explicit-clock y2 route. Supplied lines
and lineplot now route native numeric/date or declared categorical predictors
through actual primary/y2 axes in either orientation; see the
[line contract](LINE_WORKFLOW.md). Complete-unit calendar inference uses native
UTC-day deviations; log10 fitting still displays raw inverse-mapped response
values, independently of display base. C02–C07 distribution/estimate contracts
and D01 line facets retain their specifically admitted secondary routes; unrelated
guards remain. This does not close broader F01/F02/D06.

## Joint and pair grids

`joint()` inherits the declared template clocks, copying each only to its
observation marginal axis. `pair()` requires an explicit per-variable map:

```python
import mudplot as mp

source = {"time": ["2026-01-01", "2026-01-02", "2026-01-11"], "signal": [2, 3, 4]}
joint = mp.plot(source).scatter("time", "signal").date_axis("x", timezone="UTC").joint(bins=3)
pair = mp.plot(source).pair(["time", "signal"], temporal={"time": {"timezone": "UTC"}}, bins=3)
```

Each declaration accepts a `TemporalSpec` or its strict dictionary form, with the
same timezone/unit/origin rules as `date_axis()`. Unlisted variables remain
numeric; ISO strings do not trigger inference. Group selection precedes parsing.
Pairwise missing rows stay cell-local, and density axes stay numeric. Hist/KDE/ECDF
marginals/diagonals share the same clock; existing kind-specific option rules
remain (KDE/ECDF require the default `bins=20`). `SetPairGrid.temporal` carries the
map through JSON/actions without adding a field to old default actions.

Run `python examples/temporal_grids.py --out artifacts/temporal_grids` for
reopened joint/pair JSON and PNG/SVG/PDF. It explicitly labels per-day density
and uses a wide teaching figure for full ISO tick labels; it does not establish
publication-size or physical-print suitability.

## JSON, actions and editing

`TemporalSpec` is optional `AxisSpec.temporal` metadata. Unset metadata is omitted,
so legacy `0.1` JSON roundtrips without an added field. Explicit metadata needs
an updated reader. `SetTemporalAxis` sets or clears it; clearing restores the
legacy axis behavior.

```json
{"type":"SetTemporalAxis","axis":"x","temporal":{"timezone":"UTC","unit":null,"origin":null},"panel":0}
```

The actual Chromium/Rust workflow has verified ISO creation, numeric
unit/origin/timezone edits, raw SetTemporalAxis, undo/redo, downloaded JSON
reopening and PNG/SVG/PDF export. Invalid declarations preserve state/preview.
The installed-wheel smoke also verifies temporal creation, JSON/actions and CLI
rendering outside the checkout. See [core evidence](review_evidence/v2_temporal_core.json).

F02 is **not complete**. Raw/native, ISO joint/pair and the secondary-y subset
above have targeted numerical references and real edit/reopen/export checks.
See the [grid checkpoint](review_evidence/v2_temporal_grids.json) and
[secondary-y checkpoint](review_evidence/v2_temporal_secondary.json).
Broader N01–N06, G02/G03 and F01/D06 workflows remain separately required,
including ECDF's wider semantics and bivariate cumulative workflow. These are
remaining work, not exclusions or deferrals.

Run [the executable synthetic example](../examples/temporal_axes.py):

```sh
python examples/temporal_axes.py --out artifacts/temporal_axes
```

It generates irregular signal, day-density and dual-y overlays as PNG/SVG/PDF plus reopened JSON,
with explicit opt-in smart layout. Original experimental data and physical
print review are not claimed.

### Discrete histogram units

For `hist(..., bins="discrete")` (or `discrete=True` with default bins), numeric
timestamps use **one declared input unit** (`s`, `ms`, `us`, `ns`, or `day`),
not one canonical day. ISO/date observations must be midnight in the display
clock and use one day. Fractional observations, unsafe grids and half-unit
boundaries that cannot be represented exactly reject without rounding or jitter
(including microsecond/nanosecond half-unit boundaries). Named rules or explicit
edges remain available for continuous temporal observations. Source values,
units and order are preserved; no epoch mutation or renderer substitution occurs.

### N12 opt-in tick precision boundary

Explicit N12 major/minor TickSpec date/auto/concise formatters share canonical
`1970-01-01 UTC + timedelta(days=value)` conversion plus the declared fixed
clock. They do not delegate distant-epoch microseconds to num2date, which
can merge accepted20/21µs positions in2100. Fixed auto and subsecond include
date+6digits; concise supports fixed temporal positions and calendar providers,
following the finite Matplotlib3.8 level/zero/offset/trailing-zero policy.
Attribution/full license/change summary is bundled in `_matplotlib_notice.txt`.
Native calendar grids collapsing at float precision reject; no invented ticks.

Fixed positions and Unix-seconds secondary conversion use canonical UTC1970
days, not declared source unit/origin. Global epoch and no-N12 policies remain
unchanged; this does not close all F02. See the N12 contract in
[feature coverage](FEATURE_COVERAGE.md) and [example](../examples/axis_controls.py).
