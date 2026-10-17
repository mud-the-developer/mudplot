# Unreleased work snapshot

*[한국어](WORK_SNAPSHOT.ko.md)*

This snapshot collects the current local implementation, existing worktree
changes, examples, generated contracts and review work. It is **not a release**,
not full Matplotlib/Seaborn parity, and not attribution of every change to one
coding session. Package/editor **1.0.0** and spec **0.1** remain unchanged.

## Included work

- Opt-in raw-data statistics, weights/units, categorical/distribution options,
  scatter/line semantics, and legacy-default compatibility.
- Facet, joint and numeric pair composition, histogram/KDE grid subsets.
- Typed heatmap controls, optional advanced regression/residual effects and
  hierarchical clustermap with source-data/metadata alignment.
- Python/Rust editor integration, browser import/edit paths, bilingual guides,
  regenerated schema/capabilities/reference and executable visual examples.
- Strict JSON/data/output fixes: malformed row types/row-width truncation, Windows
  read-only staging cleanup, Rust reserved-key reinterpretation and omitted
  spec-version consistency, and missing categorical x becoming a phantom label.
  Rust denial responses now retain security headers; declared oversize bodies
  are rejected before upload. Query ingestion now closes its own cursor without
  closing borrowed cursors/connections or committing the transaction. Python
  framing is explicit; Rust checks unknown-size bodies before every handler. See the
  detailed findings and limits in the tracker. Fine-unit NumPy/Polars timestamps
  now preserve ISO precision; the Rust smoke CI installs its optional effects.

## Verification and review state

- Latest project subset: **1045 passed,27 skips** (25 optional-only,2Windows).
  Real PyArrow26/Polars2 overlays: **173 passed,no skips**. Do not sum overlapping
  scopes. Minimum subset: **283 passed,25 optional skips,481warnings**, not full/
  zero-warning coverage. Last browser **31 passed** is from phase11, not a new run.
- Phase12 isolated all-extra Rust smoke passes locally. Last native-unit run
  **15 passed,1 helper ignored** and browser/HTTP are earlier phase11 receipts.
  Form/JSON/chunked body probes cover39sequential cases with server-PID lifetime
  peak observations, not native-renderer-child/whole-app CPU/memory/concurrent
  limits. Compiler **1.99.0** is not MSRV verification. The earlier Windows
  transport abort cause is not claimed fixed.
- Ruff/Pyright, generated-contract sync and clean sdist-to-wheel checks passed.
- [Portable verification receipts](review_evidence/verification_receipts.json)
  preserve path-redacted result summaries, environment/source fingerprints and
  original-log hashes. Raw logs remain local; the summary is not a fresh run.
- [Adapter receipt](review_evidence/data_shape_verification.json) and latest
  [missing/state receipt](review_evidence/missing_state_verification.json)
  record source hashes, command scopes, results and cursor samples.
- [Editor-boundary receipt](review_evidence/editor_boundary_verification.json)
  records the latest13 successful commands and shared state hashes, retaining
  limits and prior failed-run notes rather than erasing them.
- [Codec/path receipt](review_evidence/codec_path_verification.json) records
  24 models/272 fields, typed Python→Rust→Python round-trips and redacted child
  argv from a separate Windows venv. Linux CI is configured, not observed.
- [Table/SQL receipt](review_evidence/table_sql_verification.json) records
  real optional-library versions, format/ownership scopes and cleanup of the
  isolated venv, without changing project packages/locks.
- [Body-boundary receipt](review_evidence/body_boundary_verification.json)
  preserves framing/size/status/state and corrected worker-PID observations.
- [Temporal/CI receipt](review_evidence/temporal_ci_verification.json) records
  precision and CI dependency fixes. Published359277c CI had successful Python
  jobs but failed Linux Rust smoke/cancelled Windows; remote rerun is pending.
- [150-ID review tracker](REVIEW_CHECKLIST_STATUS.md): **PASS 29 / RUNNING 14 /
  OPEN 107**. Unchecked items are not silently considered verified.

Earlier feature/minimum/browser receipts have their own scope and predate later
changes. They do not validate this entire combined worktree. A full Python /
minimum-version matrix, Rust MSRV, Linux/TeX, dependency security audit,
performance and release provenance gates remain incomplete or deferred.

See [the implementation plan](V1_1_PLAN.md), [feature coverage](FEATURE_COVERAGE.md)
and [Unreleased changelog](../CHANGELOG.md) for supported subsets and limitations.
