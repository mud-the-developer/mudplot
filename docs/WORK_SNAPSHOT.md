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
- Strict JSON/data/output fixes: malformed row-width truncation, Windows
  read-only staging cleanup, Rust reserved-key reinterpretation and omitted
  spec-version consistency. See the detailed findings in the tracker.

## Verification and review state

- Latest recorded focused Python set: **597 passed, 2 Windows-specific skips**.
- Rust native tests: **14 passed, 1 intentional helper ignored**; real HTTP /
  browser smoke, Clippy and formatting passed on compiler **1.99.0**, not MSRV.
- Ruff/Pyright, generated-contract sync and clean sdist-to-wheel checks passed.
- [Portable verification receipts](review_evidence/verification_receipts.json)
  preserve path-redacted result summaries, environment/source fingerprints and
  original-log hashes. Raw logs remain local; the summary is not a fresh run.
- [150-ID review tracker](REVIEW_CHECKLIST_STATUS.md): **PASS 11 / RUNNING 14 /
  OPEN 125**. Unchecked items are not silently considered verified.

Earlier feature/minimum/browser receipts have their own scope and predate later
changes. They do not validate this entire combined worktree. A full Python /
minimum-version matrix, Rust MSRV, Linux/TeX, dependency security audit,
performance and release provenance gates remain incomplete or deferred.

See [the implementation plan](V1_1_PLAN.md), [feature coverage](FEATURE_COVERAGE.md)
and [Unreleased changelog](../CHANGELOG.md) for supported subsets and limitations.
