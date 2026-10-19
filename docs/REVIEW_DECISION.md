# Current author review / 현재 작성자 검토

**Decision: NOT RELEASE APPROVED. / 릴리스 승인 아님.**

This is an interim coding-assistant source/evidence review, **not an independent
reviewer sign-off** or final handoff. DOC-04/05/06 and outstanding gates stay open.
The code base reviewed here is `d221188b709ef8c3eb99e7b9239db8a7646cfdcf`
(layer guard plus the checkpoint work); this report's commit adds
document/example corrections. Exact file fingerprints/commands are in the
[documentation receipt](review_evidence/documentation_review_verification.json).
Package/editor1.0.0 and serialized spec0.1 remain unchanged; new checkout work is
Unreleased and is not retroactively part of the published v1.0.0 wheel.

## Public surface and compatibility / 공개 API와 호환성

Comparison baseline: the original checklist SHA
`c4f40ab22660129ad4e35c63d1f66feb62e2dd99`. Source AST comparison is an inventory,
not proof that every parameter combination or all behavior is identical.

| Surface | Observed change | Classification / handling |
| --- | --- | --- |
| Root exports | 41→52, no removals | Eleven typed Spec additions; no deprecated export removal. |
| Plot methods | 70→84, no removals | Fourteen additions; existing positional parameter prefixes remain. |
| Existing parameters | Optional additions; original defaults retained | Box/violin add optional positional y; other additions are optional keywords. |
| scatter capture | Old `**style` capture becomes `**appearance`, with dedicated optional `style` role | Valid legacy marker/alpha kwargs still forward. Former unknown `style=` is a new semantic role, not removal of a valid LayerSpec field. |
| Models/actions | Model classes14→25, action classes32→36 | Optional/defaulted additions; existing annotated fields/defaults retained. |
| CLI | Seven commands/six explicit flags unchanged | Machine formats remain file/stdout/HTML/JSON according to their actual route. |
| Resource behavior | Some previously positive requests now reject | Explicit availability-hardening exception: 256panels/cells,1024total layers,512bivariate bins/axis,40Mowned-effect pixels. No truncation/implicit source DPI rewrite. |
| Diagnostics/performance | Class.field errors; one internal default Store checkpoint | Error kinds/public data/history/listener rules retained; exact error text and replay implementation are not new serialized contracts. |

See [compatibility](COMPATIBILITY.md) / [한글](COMPATIBILITY.ko.md) for limits and
[actual error/route evidence](review_evidence/machine_error_verification.json).
New resource restrictions affect large workloads: partition/reduce work explicitly.
They are not claimed to be purely additive acceptance or an OS memory/CPU sandbox.

## Evidence levels / 증거 수준

- **Reproduced production defect:** linked before/after regressions and source
  fingerprints, for example numeric covariance, ignored annotation alpha, wrong
  y2 drag frame, late HTML and resource amplification. A fixed corpus is not a
  universal correctness probability; the [ledger](REVIEW_CHECKLIST_STATUS.md)
  distinguishes non-production fixture/CI findings.
- **Reproduced documentation/example issue:** unconditional print-safe wording
  versus finite pattern cycles; examples that discarded open save Figures.
  Wording/explicit close fixes do not alter the API ownership contract.
- **Test/transport weakness:** immediate focus assertions or CDP pinch hit tests;
  failed/cancelled runs are preserved separately, not relabelled as passing.
- **Measured limitation:** long histories/inline data and remaining low-DPI dense
  geometry. Stopped workload timings remain null; small samples are not stable p95.
- **Proposal/unexecuted gate:** mandatory sidecars, remote service isolation,
  independent human AT/readability studies or final release publishing are not
  implied by a receipt. The opt-in manifest is tested but not a general redactor.

## Provisional release gate table / 잠정 gate 판단

| Gate | Current decision | Missing condition / evidence |
| --- | --- | --- |
| G0 baseline | BLOCKED | BASE-05's all150 implementation-symbol/test mapping remains in progress. |
| G1 state/JSON/bridge | BLOCKED | JSON-09 complete all-field meaning and current-source whole CI still required. |
| G2 data/statistics/geometry | PASS, documented subsets | Independent numeric/semantic receipts exist; not Matplotlib/Seaborn parity. |
| G3 publication output | BLOCKED | Remaining LAY-09 dense75DPI scope and final claim decision. Physical canvas/accepted DPI subsets have receipts. |
| G4 editor/failure recovery | BLOCKED | Focused Python/native flows pass; new layer/checkpoint source still needs exact whole CI. |
| G5 security/resources | BLOCKED | SEC-04 remaining text/algorithm/total-memory policy; trusted local tools are not a processing sandbox. |
| G6 packaging/platform | BLOCKED | PKG-07 final headless/platform evidence consolidation and current-source validation. |
| G7 CI/release | BLOCKED | Outstanding CI quality/supply-chain rows and CI-07 actual release authorization/artifacts. |
| G8 final judgment | BLOCKED | DOC-04/05/06 final assessment/independent sign-off/handoff not represented by this interim report. |

No scalar quality score or stability probability is assigned. Current source
correctness, physical publication quality, editor behavior, performance and
maintainability have different evidence scopes. Known failures/limits are retained;
there is no substitution of design-document quality for measured execution.

## Reproduction and pending work / 재현과 후속 작업

Use the matching checkout/locked environment, then the exact commands and source
hashes in the receipt. Useful entry points are `scripts/check_schema_sync.py`,
`tests/test_review_doc_contracts.py`, `tests/test_review_provenance_recipe.py` and
the ledger's named source/runtime receipts. Same input, environment and code are
needed; no result is inferred from an older suite after later implementation work.

This report performs no tag, package publish, deployment or remote server exposure.
Normal main-branch commit/push history is recorded separately in the work snapshot.
Remaining tasks belong to the existing loop/workflow, not a new approval or an
instruction embedded in archived evidence. 최종승인/배포권한을 새로 부여하지 않습니다.
