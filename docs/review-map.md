# Checklist implementation/test map — partial

Original: [2026-10-16 checklist](../mudplot_review_checklist_detailed_2026-10-16.md).
Candidate inventory/status: [review ledger](REVIEW_CHECKLIST_STATUS.md).
[Machine-readable execution and source fingerprints](review_evidence/review_map_state_core.json).

## Scope and classification

This is the first **five-ID Python core mapping**, not a complete150-ID map.
The other145 IDs have not been classified here. The candidate inventory still
contains all150 original IDs, but filenames and PASS labels are not coverage proof.
BASE-05 remains RUNNING; original counts139PASS/6RUNNING/4OPEN/1DEFERRED are unchanged.
Prior phase-specific evidence is not invalidated or re-labelled by this partial map.

For each reviewed ID, classify as **existing coverage**, **additional test needed**
or **design decision needed** after reading the implementation and assertions.
All five below have existing coverage of the explicitly stated boundary; no new
runtime/test code or compatibility decision was needed for this mapping unit.
AST checks only resolve references, not prove their semantic adequacy.

Source reviewed at `52acc3f30ce6afdc88a305966a3f9b323e98c76a` with runtime files
unchanged. Run on that source: **13 passed,2 deselected,0 skipped/failed,exit0**.
The two deselected HIST nodes were not run or counted. This is not a full-suite,
CLI, browser, native editor or release result. Source/body/log/JUnit hashes and
expanded parameterized node IDs are recorded in the linked JSON artifact.

| ID | Classification | Selected execution | Reviewed boundary |
| --- | --- | --- | --- |
| STATE-01 | Existing coverage | 3 passed | Nested reducer input/action isolation on success and two failures |
| STATE-02 | Existing coverage | 5 passed | Public snapshots, history payloads and independent listener copies |
| STATE-04 | Existing coverage | 2 passed | Functional apply parse/reducer failure isolation |
| STATE-05 | Existing coverage | 2 passed | Sequential Plot/Store batch prefix commits and continued use |
| STATE-06 | Existing coverage | 1 passed | Listener exception after commit, callback order and unsubscribe recovery |

## STATE-01 — reducer inputs

Implementation: [reducer.py](../mudplot/reducer.py) `reduce`, `_safe_replace`.
`reduce` deep-copies state; AddLayer copies its payload; replacement parameters
are copied and unknown fields raise without returning a partially mutated input.

Existing nodes in [test_review_state_contracts.py](../tests/test_review_state_contracts.py):

- `tests/test_review_state_contracts.py::test_state_01_nested_reducer_output_cannot_mutate_input_or_action`
- `tests/test_review_state_contracts.py::test_state_01_nested_reducer_failure_preserves_both_inputs`
  (two parameter cases: RemoveLayer/SetFont failure).

Fixture `_nested_plot` and mutation helper `_corrupt_snapshot` include nested
column tags, matrix cells, theme hatches and reference payloads. Assertions compare
both source state and action before/after, then mutate the successful result.
This selection is not an exhaustive test of every action variant.

## STATE-02 — snapshots and listener payloads

Implementation: [api.py](../mudplot/api.py) `Plot.spec`;
[store.py](../mudplot/store.py) `Store.state`, `Store.history`, `Store.dispatch`,
`Store._dispatch`, `Store.subscribe`.

- `tests/test_review_state_contracts.py::test_state_02_nested_public_snapshots_are_independent`
  (`plot`, `store`, `dispatch` parameter cases).
- `tests/test_review_state_contracts.py::test_state_02_nested_history_actions_are_independent_and_replay_is_unchanged`
- `tests/test_review_state_contracts.py::test_state_02_listeners_receive_separate_nested_snapshots_and_payloads`

The fixture mutation checks nested values, not only top-level identities. History
SetData/SetMatrix payload edits cannot change replay; a corrupting first listener
cannot change a later listener's state/action copy. Plot.action_log dictionary
mutation is not separately selected by this five-case surface selection.

## STATE-04 — functional apply isolation

Implementation: **module-level** [api.py](../mudplot/api.py) `apply`, not
`Plot.apply`; [reducer.py](../mudplot/reducer.py) `reduce_all`, `reduce`.

- `tests/test_review_state_contracts.py::test_state_04_functional_apply_failure_preserves_caller_inputs`
- `tests/test_review_state_contracts.py::test_state_04_functional_apply_parse_failure_does_not_leak_first_action`

Module apply parses the action sequence then folds pure reducer results. A later
invalid layer reference or unknown action leaves caller state/actions unchanged
and returns no partial result. This does not promise rollback for imperative batches.

## STATE-05 — imperative batch prefix contract

Implementation: [api.py](../mudplot/api.py) `Plot.apply`;
[store.py](../mudplot/store.py) `Store.dispatch_all`, `Store._dispatch`,
`Store.undo`, `Store.redo`.

- `tests/test_review_state_contracts.py::test_state_05_plot_apply_keeps_completed_prefix_and_can_continue`
- `tests/test_review_state_contracts.py::test_state_05_store_dispatch_all_commits_prefix_and_invalidates_old_redo`

The two APIs are checked separately: a failing middle action preserves the earlier
successful dispatch, does not execute the suffix and permits subsequent use.
Store assertions inspect state/history prefix plus undo/redo-visible cursor
semantics. No whole-batch rollback is imposed and no private cursor field is assumed.

## STATE-06 — listeners commit before notification

Implementation: [store.py](../mudplot/store.py) `Store._dispatch`, `Store.subscribe`.

- `tests/test_review_state_contracts.py::test_state_06_listener_failure_occurs_after_commit_and_is_not_rollback`

State/history commit precedes callbacks. The test asserts first/failing callback
order, propagated exception, no later callback after failure, retained committed
state/history, unsubscribe and subsequent dispatch/undo. A listener failure is not
a reducer failure and does not roll back the committed transition.

## Reproduction and next coverage boundary

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_state_contracts.py \
  -k 'test_state_01 or test_state_02 or test_state_04 or test_state_05 or test_state_06' \
  --junitxml=<private-results.xml>
```

The public artifact contains synthetic fixtures/test names and hashes, not raw
logs, secrets or user-local absolute paths. Private raw receipts are not a durable
web download. Recheck symbol/source fingerprints after implementation changes.

STATE-03's cross-path matrix and the other145 IDs still need their own reviewed
symbol/node/provenance links and classification. Do not infer missing coverage
from their omission here or infer completion from a test filename/collection/pass.
