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

- Latest805CI exposed2Linux Pyright errors in the extracted Windows factory, not
  a renderer/test failure. Explicit platform guarding restores that boundary;
  both Linux/Windows global checks pass locally, with4runtime tests/1OSskip.
  A fresh Linux guard execution/CI is still needed. Layout work was postponed;
  hold this tooling fix while the remaining prior jobs settle.

- Latest HTML/SVG literal/draft decode-once and actual raw-editor4payload checks
  preserve data without added active nodes. Explicit trusted PGF escaping/math
  compiles; OUT-09 is PASS, not an untrusted-TeX sandbox or all-font guarantee.
  Connected72passes/floor6passes and185classified upstream deprecations retain scope.
- Baseline06dCI39131994074 is ALL5SUCCESS. The queued tooling/tests have their own
  local results and can now publish; later CI still needs its exact current result.

- Latest reference-bearing deterministic exports retain labels/links without volatile
  dates/IDs. PGF relocation/missing/failure semantics and4real TeX/bibliography
  combinations pass; compiled PDFs retain resolved numbers,5embedded fonts each
  and actual DOI annotations. OUT-02/06/07/08 are PASS in this installed scope.
  Related70passes/no skips and floor6passes retain PGF non-transactional/OS/font
  limits; runtime is unchanged and the earlier local hold protected06dCI to completion.

- Latest137second session trace reclaims owned Figures and keeps handles/temp
  counts flat while history/cache changes are explicit. RSS/native lifetime still
  needs longer observation; PERF-04 is RUNNING, not leak-free certification.
- The sampler itself recreated ctypes types;20no-render calls reproduced662object
  growth. Lazy Windows bindings now reuse types without caching PID measurements;
  corrected session rerun/63related checks/2OSskips and6quality/package receipts pass.
  No product render/state change; the earlier tooling hold protected06dCI to completion.

- Latest owned Matplotlib effects use shared reentrant serialization after2serial/
  concurrent export mismatches. Three-format exact hashes, independent session
  previews/layout and nested calls pass:231connected/9site/floor6checks. PERF-06
  is PASS within owned calls; external Figures/pyplot remain caller-coordinated.
  This effect unit stays local during current31eCI, with no throughput promise.

- Latest independent-worker rows×history matrix completed6targets and explicitly
  stopped3at dispatch budgets; unknown undo/redo remains null, not zero. Core-PID
  RSS/peak is observed, not whole-app/native-renderer or hard-limit proof. PERF-02
  is PASS in scope;62related tests/2OSskips and6quality/package checks pass.
  No replay/alias optimization. Hold the new script/test/docs unit during31eCI.

- Latest renderer keeps supported empty marker/style values rather than automatic
  fallback.20representative cases agree across schema/Python/CLI/typedRust and
  both rawJSON editors40times; JSON-09 remains partial for other nullable meanings.
  Related266passes/floor79passes/native22passes are scoped; numeric0/defaults stay.
- Baselineea1CI39125371498 is ALL5SUCCESS before this token fix. Publish the queued
  performance/fixture changes, but don't call that baseline current-source proof.

- Latest bounded warm1k/10k/100k-row cost profile separates core editing, JSON and
  render/save. Title dispatch medians0.803/6.993/67.867ms; measured copying dominates
  a separate instrumented profile, not a guarantee on all hardware. PERF-01/03 PASS.
  No core optimization/alias-safety reduction; only the reproducible script is new.
- Exactea1Linux/Windows foreground descendant and currentMSRV checks passed20/21
  tests (5/6helpers ignored), so RUST-04 is PASS in its documented non-detached scope.
  The earlier publication hold protected its full CI until that run completed.

- Latest foreground descendant timeout now uses a held Windows tree/fresh Unix
  process group, bounded cleanup command and explicit cleanup-error diagnostics.
  Windows21tests/6helpers ignored and normal native bridge pass; later remote
  Unix/MSRV controls above now confirm that scope. Detached workers remain unsupported.
- Baselinee728CI39122032427 is ALL5SUCCESS. It predates the cleanup change; queued
  local units can publish, but CI-01 is not retroactive proof of this new runtime.

- Actuale728Linux floor completed2872passes/26optional+TeXskips/3906warnings;
  exact source and complete skip summary support4staging symlink passes. Both OS
  native jobs passed19tests/3helpers ignored plus HTTP path checks. SEC-06 is now
  PASS for measured policies, not a sandbox/all-OS guarantee. The later privacy/
  cleanup changes retain their own evidence; the earlier full jobs have now succeeded.

- Latest default-log probes preserve state/PNG and do not record synthetic input
  markers or tracebacks in Python/Rust stdout/stderr. Same-client draft/diagnostic
  output remains intentional.211related/floor1checks pass; runtime code is unchanged.
- Current3Python-lock audits and69Cargo-registry OSV queries report no known
  advisory within their scoped snapshots, not security certification. SEC-08 is
  PASS. The local test/docs publication hold protectede728CI until it completed.

- Latest CI full/floor separation retains the ordered60-file floor and complete
  full/browser/Rust checks under3finite60minute Python jobs and2Rust20minute jobs.
  Same TeX/system-font prerequisites and both timing reports are preserved.
  CI/release7passes and critical floor39passes/4skips are local, not5job remote proof.
  The ownership/docs queue can publish with this change; CI-01 still needs that run.

- Latest staging ownership and fixed HTTP path/query guards pass; normal PNG/PDF/
  SVG references stay offline data. Related128passes/6OSskips and floor80passes/
  4symlink skips were local; the later Linux result above covers those cases.
  SEC-07 is PASS. The exclusive reservation prevents collision deletion.
- Baseline621CI ended cancelled at1hour during floor checks after3.10Pytest passed;
  other3jobs succeeded. The floor now has separate finite execution without
  dropping coverage; this prior cancelled run is not all-green.

- Latest Windows TMP controls12cases distinguish observed venv startup limits from
  core/capture. ShortTMP/longTEMP on the same interpreter passes native open/action/
  PNG and long source preservation; related47checks pass. PKG-06 is PASS only for
  this supported host configuration and documented limits, not general descendant
  cleanup or all long paths. That earlier diagnostic did not change product runtime.

- Latest locked43-package snapshot/repeat sync, separate isolated PEP517 backend,
  equal55-member observed wheel builds and an independent core consumer pass.
  Both matching-checkout source editors start with expected shared assets; PKG-08/
  09 are PASS. Runtime code is unchanged; this is not release or universal-byte approval.
  The earlier documentation publication hold protected621CI until it settled.

- Latest82optional-related and floor11passes/13warnings plus installed-wheel7
  progressive extras stages/98CLI calls pass outside checkout. Missing effects
  now explain the right extra without masking other imports. Browser binary
  absence is distinct from package installation; PKG-02/04 are PASS.
- Baselinee14CI39111782233 succeeded in all4Python/Rust OS jobs; these later guards
  still need their own integrated run. Windows93/336character file/lock paths pass
  from short cwd; the later TMP control above now explains that observed startup limit.

- Latest249field/marker+169connected passes, floor174passes/13warnings and native
  JSON recovery18boundary cases retain explicit marker0 without changing automatic
  defaults.139nullable schema/Python field states pass; JSON-09 broader parity is
  pending. JSON-12 bounded corrupt/large API/CLI/HTTP recovery is PASS.
- Baseline063CI completed cancelled:3.10 exceeded45minutes per annotation; both
  Rust and3.12 passed. Full tests remain; finite60minutes and25slowest timings are
  configured for the next run. Two local units can now publish, not release/tag.

- Latest core subset195passed; new35cases pass on current/floor stacks. Bool/
  noninteger layer indices no longer choose targets or leak TypeError. Core hashes
  agree across process environments and guarded core effects remain dependency-free.
  The publication hold protected baseline063CI until it completed.

- Latest native19tests passed/3helpers ignored and14controlled output boundaries
  passed. Empty render artifacts no longer commit; spec/PNG/redo/recovery checks
  cover missing optional effects and fault paths. RUST-03 is PASS, but timeout
  descendant ownership remains partial in RUST-04. Prior6preview cases retain scope.

- Latest data/JSON subset **291 passed**, floor subset **61 passed/201warnings**;
  native **16 passed/1helper ignored** includes additive-capability coverage.
  Raw group masks no longer string-coerce mixed IDs. Earlier broad results below
  predate later renderer changes; the current JSON-09/12 status is recorded above.

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
- [Core boundary evidence](review_evidence/core_boundary_verification.json)
  records reference/type failures, cross-process hashes and current/floor checks.
- [JSON semantics evidence](review_evidence/json_semantics_verification.json)
  records139field meanings, marker forwarding, bounded input recovery and CI timeout.
- [Installed matrix evidence](review_evidence/installed_matrix_verification.json)
  connects actual extras, wheel/source hashes, outside CLI and bounded Windows paths.
- [Isolation/source editor evidence](review_evidence/isolation_source_editor_verification.json)
  separates lock, fresh-range drift, isolated backend and actual matching-source startup.
- [Windows TMP boundary evidence](review_evidence/windows_tmp_boundary_verification.json)
  records interpreter/capture/environment controls and the same-interpreter bridge result.
- [File/sink evidence](review_evidence/file_sink_verification.json) records owned
  staging, route policies, offline sink controls and separate CI budget exhaustion.
- [CI floor-split evidence](review_evidence/ci_floor_split_verification.json)
  records unchanged scope/prerequisites and local runner/critical-subset checks.
- [Privacy/advisory evidence](review_evidence/privacy_audit_verification.json)
  records default synthetic log probes, exact lock snapshots and audit limitations.
- [Remote floor/native evidence](review_evidence/remote_floor_verification.json)
  retains completed-job log hashes, skip scopes and source-based symlink inference.
- [Descendant cleanup evidence](review_evidence/descendant_cleanup_verification.json)
  records controlled Windows timeout/failure/recovery plus limits and pre-change CI.
- [Performance evidence](review_evidence/performance_verification.json) retains
  stage median/p95, repeat counts and separate Python allocation/profile caveats.
- [Current remote cleanup](review_evidence/remote_cleanup_verification.json) checks
  exact source/MSRV/controlled cases on both OSes without all-job completion claims.
- [Render-token evidence](review_evidence/render_token_verification.json) retains
  explicit normalization, CLI/codec/rawUI scopes and the remaining all-field gap.
- [History-cost evidence](review_evidence/history_cost_verification.json) retains
  completed/stopped targets, exact budgets/RSS scopes and checkpoint-error tests.
- [Owned-concurrency evidence](review_evidence/concurrent_render_verification.json)
  records exact serial/concurrent bytes, current/floor checks and ownership limits.
- [Session-resource evidence](review_evidence/session_resource_verification.json)
  separates current RSS/handle/Figure/cache observations from observer self-growth.
- [Output/reference evidence](review_evidence/output_reference_verification.json)
  retains hashes, compiler/JUnit/sidecar cases and actual PDF font/URI inspection.
- [String-context evidence](review_evidence/string_boundary_verification.json)
  records exact HTML/SVG values, compiled trusted TeX and current warning categories.
- [Platform-guard evidence](review_evidence/platform_guard_verification.json)
  records the exact failed CI step and separate current platform checks.
- [150-ID review tracker](REVIEW_CHECKLIST_STATUS.md): **PASS82/RUNNING9/OPEN58/
  DEFERRED1**. CI-01 awaits a new integrated run; release-only CI-07 is deferred. Unchecked items are not silently considered verified.

Earlier feature/minimum/browser receipts have their own scope and predate later
changes. They do not validate this entire combined worktree. A full Python /
minimum-version matrix, Rust MSRV, Linux/TeX, dependency security audit,
performance and release provenance gates remain incomplete or deferred.

See [the implementation plan](V1_1_PLAN.md), [feature coverage](FEATURE_COVERAGE.md)
and [Unreleased changelog](../CHANGELOG.md) for supported subsets and limitations.
