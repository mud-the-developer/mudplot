# Performance and supported workload scope

*[한국어](PERFORMANCE.ko.md)*

These are bounded synthetic observations, **not an SLA or a streaming/million-row
support promise**. Source/environment fingerprints and raw-log hashes are in the
[E2E receipt](review_evidence/e2e_performance_verification.json). The earlier
[core profile](review_evidence/performance_verification.json) and
[replay/memory comparison](review_evidence/history_improvement_verification.json)
remain separate experiments, not results silently refreshed by this document.

## Same data/action, different paths

Windows11/Python3.12.15/NumPy2.5.2/Matplotlib3.11.1, one4×3inch100DPI raw line,
three numeric/text columns, finite synthetic rows, five sequential SetTitle actions.
Each path's final supported spec and cached PNG **pixels** matched direct output;
invalid layout followed by a valid title preserved/recovered state and preview.

| Rows | Direct reduce/public PNG save+close/read | Python form HTTP+PNG fetch | Rust title-form HTTP+PNG fetch |
| --- | ---: | ---: | ---: |
| 1,000 | median530ms | 561ms | 4215ms |
| 10,000 | median553ms | 597ms | 4431ms |

Each high-cost path has5samples: nearest-rank p95 is the observed maximum, **not a
stable tail estimate**. Direct save includes atomic filesystem I/O; Python/Rust
use preview buffers/HTML. HTTP includes a new loopback connection, response body
and PNG fetch, not browser decode/paint. Do not subtract these medians as a precise
network overhead or sum overlapping component probes into a fabricated total.

Warm API/editor means imports/server and font cache are warm. Rust still starts
fresh Python children: apply then preview render per successful action. Its HTML
was~203KB/1.82MB for1k/10k rows versus Python's~25KB, another transport distinction.
The language label alone does not predict this mixed-process pipeline's latency.

Separate100-sample warm probes measured JSON encode~1.6/15.4ms, decode~3.0/18.2ms,
reduce~0.41/3.43ms and snapshot~0.41/3.38ms for1k/10k. Raw-line validation was~0.013ms;
this is **not** the cost of KDE/bootstrap/other algorithms. Three fresh-interpreter
CLI trials per size separately measure capabilities/apply/render. Apply was about
1.68–1.81s and preview render2.55–2.83s on this host, including process/import/I/O;
these probes overlap work already present in HTTP and are not additive accounting.

## Cold preparation is a separate workload

Owned initially empty font-cache directories were used, not the user's cache.
API module import~0.59s plus first save~0.54–0.56s is measured from Python script
execution, excluding interpreter launch before its first statement. Fresh Python
server default-preview readiness was~2.30s, Rust default readiness~4.28s; their
initialization work differs. First source open was~0.54–0.60s Python/~1.80–2.01s
Rust. Readiness polling adds up to50ms; default setup/open/action are not one number.
CLI child probes include actual configured venv process launch/exit. These labels
must not be replaced by a single claimed cold-start speedup.

## Small measured optimization, not a rewrite

The default pure Store reducer retains one preceding64-action-boundary internal
state. On the recorded fixtures1k-row/1000-action undo changed~405→17ms; the matched
10k-row/256-action cached/full-replay control was~219/860ms, with~280KB extra traced
Python retention. It retains all history and detached public snapshots. Custom
reducers still replay fully; earlier cursors can fall back to initial state. One
extra full Spec is a memory tradeoff, not a total-RSS bound or universal speedup.

Mouse gestures already submit once on release and keyboard bursts coalesce in the
existing UI. No core event/no-op/listener is discarded. The cheap raw validation
probe does not justify deleting trust-boundary validation; Rust child startup/JSON
and rendering are different bottlenecks. Immutable/zero-copy rewrites are not a
measured prerequisite for the present paper-oriented workload.

## Practical dataset guidance

- Start around1k rows and short10–100-action paper histories when interactive cost
  matters.10k-row raw-line cases completed here, but not with a20ms UI promise.
- A separate100k-row core matrix completed short10-action cases; larger target
  histories hit the observed dispatch budget before completion. Missing undo/redo
  timings remain **null**, not0. Do not extrapolate them to working100k×1000 sessions.
- Typed statistical/semantic paths have their own row/group/algorithm bounds
  (several are10k usable rows). Raw-line measurements do not waive those limits.
- Inline data is copied/serialized with state.16MiB request bytes,2000px/axis preview,
  256panels/cells,1024total layers,512bivariate grid axes and40Mowned-effect pixels
  are different bounds, **not interchangeable CPU/RAM protection**. See
  [compatibility](COMPATIBILITY.md) and [security](../SECURITY.md).
- Aggregate or select a domain-appropriate preview **explicitly before plotting**;
  preserve the original data/spec separately. The engine never silently removes
  observations to satisfy an editor/export limit. Rebuilding a fresh Plot/Store
  intentionally starts different history; do not pretend it preserves old undo.

For an ordered, finite numeric preview, this example makes consecutive block means
and retains group counts. It changes the represented observations; it is not a
universal downsampler or a valid replacement for original uncertainty estimates.

```python
from statistics import mean

original = [(i, float(i * i)) for i in range(25)]
block_size = 10
blocks = [original[i:i + block_size] for i in range(0, len(original), block_size)]
preview = {
    "x": [mean(x for x, _ in block) for block in blocks],
    "y": [mean(y for _, y in block) for block in blocks],
    "n": [len(block) for block in blocks],
}
assert preview["n"] == [10, 10, 5]
assert sum(preview["n"]) == len(original)
assert preview["x"] == [4.5, 14.5, 22]
```

Do not compute confidence intervals treating these means as25original samples.
Use original observations or explicit supported weighting/group semantics.

### Follow-up design boundary

A data-store/spec split is a **future design issue only if an actual workload**
shows copying/transport dominating beyond this support scope. It would require
stable data identity/lifetime, complete exports, snapshot semantics and cache
invalidation rules; no such API/storage rewrite, streaming engine or automatic
history truncation is introduced by this review.
