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

- Latest native19tests passed/3helpers ignored and14controlled output boundaries
  passed. Empty render artifacts no longer commit; spec/PNG/redo/recovery checks
  cover missing optional effects and fault paths. RUST-03 is PASS, but timeout
  descendant ownership remains partial in RUST-04. Prior6preview cases retain scope.

- Latest data/JSON subset **291 passed**, floor subset **61 passed/201warnings**;
  native **16 passed/1helper ignored** includes additive-capability coverage.
  Raw group masks no longer string-coerce mixed IDs. Earlier broad results below
  predate this renderer change; JSON-09/12 remain partial rather than complete.

- Latest optional full run: **3423 passed,2 OS skips,1 warning**, before a QA-only
  contour API adjustment and minimum-environment banner. Corrected72P0 cases
  separately passed on both stacks; do not treat the prior run as a later rerun.
- Minimum53files were covered exactly once in8batches: **2573 passed,25 optional
  skips**. This is not a single ordered run. A real no-dependency wheel install
  outside the repository passed core and console/module CLI checks.
- Earlier history199/browser32 and other focused receipts retain their own scope.
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
  argv from a separate Windows venv. Later Linux/Windows proof is in phase14.
- [Table/SQL receipt](review_evidence/table_sql_verification.json) records
  real optional-library versions, format/ownership scopes and cleanup of the
  isolated venv, without changing project packages/locks.
- [Body-boundary receipt](review_evidence/body_boundary_verification.json)
  preserves framing/size/status/state and corrected worker-PID observations.
- [Temporal/CI receipt](review_evidence/temporal_ci_verification.json) records
  precision and CI dependency fixes. Published359277c CI had successful Python
  jobs but failed Linux Rust smoke/cancelled Windows; remote rerun is pending.
- [Scalar/provenance receipt](review_evidence/scalar_provenance_verification.json)
  records explicit unsupported-value rejection and the non-shadowed test recorder.
  Linux914a402 failed provenance; later781f3f5 Rust jobs succeeded on both OSes.
- [History-policy receipt](review_evidence/history_policy_verification.json)
  records current document/no-op/replay/UI checks. Remote781f3f5 Linux/Windows
  Rust jobs and Python3.12 passed; Python3.10 cancelled, so the full workflow
  was cancelled. Remote success is not retroactive proof of the later UI fix.
- [P0 completion evidence](review_evidence/completion_p0_verification.json)
  connects independent numeric/geometry/export references, floor batches, installed
  artifacts and baseline92238f3 CI success. Incomplete attempts are not counted.
- [Data/JSON policy evidence](review_evidence/data_json_policy_verification.json)
  connects group identity, empty/singleton/order and structural JSON checks.
- [Bridge/preview evidence](review_evidence/bridge_preview_verification.json)
  records bounded failure output and native preview/session contracts.
- [Bridge fault evidence](review_evidence/bridge_fault_verification.json) records
  isolated failure injection and baselinefe4449d CI cancelled(3.10 cancelled;
  both Rust/3.12 passed), not proof of the later artifact guard.
- [150-ID review tracker](REVIEW_CHECKLIST_STATUS.md): **PASS60/RUNNING11/OPEN78/
  DEFERRED1**. CI-01 awaits a new integrated run; release-only CI-07 is deferred. Unchecked items are not silently considered verified.

Earlier feature/minimum/browser receipts have their own scope and predate later
changes. They do not validate this entire combined worktree. A full Python /
minimum-version matrix, Rust MSRV, Linux/TeX, dependency security audit,
performance and release provenance gates remain incomplete or deferred.

See [the implementation plan](V1_1_PLAN.md), [feature coverage](FEATURE_COVERAGE.md)
and [Unreleased changelog](../CHANGELOG.md) for supported subsets and limitations.
