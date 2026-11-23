# v1.1.0 local candidate checklist

*[한국어](V1_1_RELEASE_CHECKLIST.ko.md)*

**Status: numeric/export-hardened 1.1.0 candidate fully qualified locally.**
This is not a published release or permission to publish. The work remains local
and uncommitted. No push, PR, merge, tag or publication was performed.

## Frozen scope

- Ship the implemented, documented subsets plus agent-facing scientific quality.
  Unimplemented B2b/B3/B4/B5/B6 expansions remain post-v1.1 backlog, not completed.
- Preserve Matplotlib, existing Python/CLI defaults, FigureSpec/JSON schema 0.1,
  old-spec migration and original measurements. No new chart types in this work.
- `smart` / `smart-print`, `recommend()` and visual lint are Python/CLI features.
  A Rust smart toggle is not needed. Existing editor compatibility is checked.
- Owner-approved security exception: Python >=3.11, colour/render NumPy >=1.23.5,
  Matplotlib >=3.8, render Pillow >=13.0.0. Python 3.10 support ends explicitly.
- Remote CI is not a current development requirement. Windows is deferred, not
  claimed as verified or permanently unsupported. Publication remains separate.

## Qualification gates

| ID | Status | Evidence / boundary |
| --- | --- | --- |
| R01 | PASS | Owner-approved scoped implementation and security support exception |
| R02 | PASS | Fresh locked full suites: Python 3.11/3.12, each 4547 passed / 45 skipped / 0 failed |
| R03 | PASS | Fresh pinned minimum full suite: 3735 passed / 36 skipped / 0 failed |
| R04 | PASS | Required real-browser cases and post-hardening Rust HTTP/browser/bridge/body-boundary smoke passed |
| R05 | DEFERRED | Local Rust fmt/clippy/tests and Rust 1.88 all-targets passed; Windows deferred by owner |
| R06 | PASS | Required PGF/reference and pdflatex/lualatex/tectonic/biblatex paper identities passed |
| R07 | PASS | Four synthetic 300-DPI before/after cases: unchanged data/size, >=8 pt, no after composition errors |
| R08 | PASS | All eight scientific PNGs required in sdist; installed default/smart/CLI smoke passes; final hashes/rebuild proof are external; dependency/static checks pass |
| R09 | PENDING | Owner review of figures, known limitations and any publication decision; no external approval claimed |
| R10 | NOT REQUIRED | No remote CI gate for current local development; no remote actions performed |
| R11 | PASS | Python/Rust/Cargo.lock/uv.lock/README/changelog agree on local candidate 1.1.0; preflight and 40 metadata/policy guards pass |
| R12 | OWNER APPROVAL | No signed tag or publication authorized/performed |

`PASS` is bounded to its recorded source/environment. Skips are retained, not
converted into passes. The detailed audit ledger is not bulk-marked PASS.

## Fresh frozen implementation checkpoint

| Environment | Executed | Passed | Skipped | Failed/errors |
| --- | ---: | ---: | ---: | ---: |
| Locked Python 3.11 | 4592 | 4547 | 45 | 0 |
| Locked Python 3.12 | 4592 | 4547 | 45 | 0 |
| Pinned minimum Python 3.11 | 3771 | 3735 | 36 | 0 |

The pinned Ubuntu environment includes tzdata, Chromium and its dependencies,
full TeX prerequisites and checksum-verified Tectonic 0.15.0. All required report
profiles pass, including their no-unrelated-failure checks. This checkpoint
actually tests package version 1.1.0, not the earlier held 1.0.0 labels.

The first run of this batch failed only the old PGF characterization test in
all three environments: it expected post-processing failure to overwrite the
previous user output. The owner explicitly approved replacing that limitation
with staging/backup/rollback. That test was updated to require preservation of
the old PGF and PNG; no runtime bytes changed between attempts. Both real-TeX
preflights and then all three complete suites passed. Original failed XML/logs
remain unchanged, not relabelled as successes.

The checkpoint now includes exact floating-point profile interpolation,
secondary-axis QA and PGF failure protection. Actual raster PGFs and logical
symlink destinations compile into a real paper; repeated exports are byte-identical.
Runtime/tests/config/locks match the complete frozen snapshot. Subsequent changes
are limited to this bilingual checklist, the generated report's two advisory
suggestion strings, and the new receipt. The eight PNGs and their measurements
remain byte-identical.

Current evidence: [numeric/export-quality receipt](review_evidence/v1_1_numeric_export_quality.json).
Previous [distribution](review_evidence/v1_1_distribution_quality.json) and
[runtime](review_evidence/v1_1_quality_hardening.json) receipts retain their own
snapshot scope. Raw reports/logs and final hashes remain in the ignored directory
named in the current receipt; `.pi`, `artifacts`, and private export stages/writes/
backups are excluded from distributions. Windows and remote CI are not claimed.

## Implemented scientific safeguards

- Measure legend/data collisions, prefer safe direct labels, deduplicate shared
  encodings, reposition outside and validate after drawing again.
- Direct-label colour uses the composited fill and existing linear-sRGB engine.
- Recommendations retain integer profiles, integral medians, IQR fences, time
  ordering and event offsets. Float coordinate limits are explicit warnings.
- Unsupported sub-microsecond ISO time/offsets warn instead of inventing repeats;
  missing time values do not crash and nonnumeric time is not silently coerced.
- Paired advice requires finite measurements and complete identifiers; misaligned
  roles are rejected and unusable coordinate/measurement rows cannot drive advice.
- Visual checks respect journal font minima and effective opacity, retaining
  hatch-only patches and alternate marker faces. Forty-one regressions cover the
  hardening boundaries, including fractional UTC offsets discarded by the parser.
- Fifty-four additional regressions cover subnormal/mixed numeric medians and
  fences, secondary descriptions, private temporary writes, PGF rollback/recovery
  and actual extensionless CLI paths. Original observations and scalar types remain intact.
- PGF sidecars keep their successful names; ordinary failures restore old files,
  and failed restoration retains a recovery backup with CLI-visible notes. There
  is no promise of concurrent all-files atomic visibility or process-kill durability.
- No automatic measurement changes, unit inference, outlier removal, significance
  claims or geometry replacement. Policies remain render-time, not spec fields.

## Historical evidence and remaining limits

Earlier failed/skipped runs remain unchanged:
[initial dependency blocker](review_evidence/v1_1_dependency_blocker.json),
[security resolution](review_evidence/v1_1_security_resolution.json),
[earlier local checkpoint](review_evidence/v1_1_local_validation.json),
[previous local candidate](review_evidence/v1_1_local_candidate.json),
[integer advice](review_evidence/v1_1_agent_precision.json),
[ISO precision](review_evidence/v1_1_agent_precision_iso.json).
The new clean reports do not rewrite those older snapshots as green.

QA is a deterministic composition proxy, not an accessibility/statistical
certificate or a substitute for real-paper/domain review. The failure cases are
synthetic; the original failure dataset was not supplied. Existing documented
CPU/RAM/history/inline-data limits still apply; no streaming or sandbox SLA.

See [scientific quality](SCIENTIFIC_QUALITY.md), [compatibility](COMPATIBILITY.md),
[coverage](FEATURE_COVERAGE.md), [development history](V1_1_PLAN.md),
[the audit ledger](REVIEW_CHECKLIST_STATUS.md) and [contributor commands](../CONTRIBUTING.md).
