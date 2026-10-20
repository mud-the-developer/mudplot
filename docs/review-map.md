# Checklist implementation/test map — partial

Original: [2026-10-16 checklist](../mudplot_review_checklist_detailed_2026-10-16.md).
Candidate inventory/status: [review ledger](REVIEW_CHECKLIST_STATUS.md).
Execution/source fingerprints: [first five state IDs](review_evidence/review_map_state_core.json),
[determinism/indices/effect boundaries](review_evidence/review_map_state_boundaries.json),
[cross-path fixture and retained Native provenance](review_evidence/review_map_state_paths.json).

## Scope and classification

This is a **nine-ID state mapping**, not a complete150-ID map.
The remaining141 IDs have not been classified here. The candidate inventory still
contains all150 original IDs, but filenames and PASS labels are not coverage proof.
BASE-05 remains RUNNING; original counts139PASS/6RUNNING/4OPEN/1DEFERRED are unchanged.
Prior phase-specific evidence is not invalidated or re-labelled by this partial map.

For each reviewed ID, classify as **existing coverage**, **additional test needed**
or **design decision needed** after reading the implementation and assertions.
All nine below have existing coverage of the explicitly stated boundary; no new
runtime/test code or compatibility decision was needed for this mapping unit.
AST checks only resolve references, not prove their semantic adequacy.

The first five IDs were reviewed at `52acc3f30ce6afdc88a305966a3f9b323e98c76a`:
**13 passed,2 deselected,0 skipped/failed,exit0**. The two deselected HIST nodes
were not run or counted. The next three were reviewed at doc-only `701e3be` with
runtime unchanged: **35 unique passed nodes,0 skipped/failed,exit0**. Their38
ID/node relationships overlap; do not count them as38 separate tests. Across the
first two runs,48 unique nodes executed, not51. STATE-03 adds6 fresh Python
nodes(4 failure cases deselected), giving54 unique fresh nodes across three runs,
not57 summed ID relationships. Native provenance is a separate previous execution
with matching source/fixture/final hash, not a newly run native/browser test.
These are focused results, not a full-suite or release result. Source/body/log/JUnit hashes and
expanded parameterized node IDs are recorded in the separate immutable artifacts.

| ID | Classification | Selected execution | Reviewed boundary |
| --- | --- | --- | --- |
| STATE-01 | Existing coverage | 3 passed | Nested reducer input/action isolation on success and two failures |
| STATE-02 | Existing coverage | 5 passed | Public snapshots, history payloads and independent listener copies |
| STATE-03 | Existing coverage | 6 fresh Python passed; retained source-matched Native check | Ten-operation supported fixture/full-state cross-path equality, not every GUI control |
| STATE-04 | Existing coverage | 2 passed | Functional apply parse/reducer failure isolation |
| STATE-05 | Existing coverage | 2 passed | Sequential Plot/Store batch prefix commits and continued use |
| STATE-06 | Existing coverage | 1 passed | Listener exception after commit, callback order and unsubscribe recovery |
| STATE-07 | Existing coverage | 2 passed, shared nodes | Fresh process/CWD/clock/Python-RNG/hash seed and previous render/theme isolation |
| STATE-08 | Existing coverage | 33 passed | Layer/panel references, intentional panel extension and validate/render parity |
| STATE-09 | Existing coverage | 3 passed, shared nodes | Guarded core operations and validation before Figure allocation |

The last three rows refer to35 unique tests, not their38 summed relationships.

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

## STATE-03 — supported cross-path state semantics

Implementation: [api.py](../mudplot/api.py) module `apply`, `Plot.labels`/fluent
builders; [store.py](../mudplot/store.py) `Store.dispatch_all`;
[reducer.py](../mudplot/reducer.py) `reduce`;
[__main__.py](../mudplot/__main__.py) `_cmd_apply`;
[editor_server.py](../dashboard/editor_server.py) `EditorSession.dispatch_safe`,
`EditorSession._commit_store`, `_build_action`, `_Handler.do_POST`;
[Rust bridge](../mudplot-editor/src/python.rs) `PythonBridge.apply` and
[Rust server](../mudplot-editor/src/lib.rs) `Session.apply`, `app`, `action_json`.
Python references are AST-resolved; Rust impl/function source anchors were read
and hashed, not described as an AST or binary-attestation proof.

The existing [shared fixture](../tests/fixtures/review_state_paths.json) contains
one initial spec and10 supported operations. Current fresh tests:

- `tests/test_review_editor_paths.py::test_fluent_functional_and_store_paths_preserve_the_same_complete_state`
- `tests/test_review_editor_paths.py::test_cli_matches_each_expected_intermediate_state`
- `tests/test_review_editor_paths.py::test_python_session_matches_action_and_visual_form_paths` (2 routes)
- `tests/test_review_editor_paths.py::test_python_http_state_matches_each_supported_action_or_form` (2 routes)

The test-owned fluent builder, functional apply and Store compare final complete
FigureSpec. CLI(entry main/file workflow), Python session and HTTP supported
form/action routes compare intermediate specs. This is state semantics, not an
identical fluent event order or UI-only history/dirty/active-panel contract.
Four failure tests were deselected and are not evidence assigned to this ID here.

The previously executed [full native proof](review_evidence/swarm_facets_verification.json)
ran `scripts/rust_editor_smoke_test.py::_review_state_paths` for both agent and
hybrid supported-form routes. Its source hashes28/raw receipts and fixture match
current runtime; Rust lib/bridge source is unchanged since that execution base.
The helper compares every intermediate spec and printed final normalized hash
`926e9f349bcb681d626b8c9e1a2215fcd39932d5a923bf48ed3975a47fc9f6c9`, which fresh
functional apply reproduces. Hybrid form uses4 explicit control steps,2 JSON-layer
form steps and4 agent fallbacks—not10 visual GUI clicks. No new native/browser/
Linux/MSRV run or independent binary attestation is claimed by this mapping unit.

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

## STATE-07 — determinism and ambient state

Implementation: [reducer.py](../mudplot/reducer.py) `reduce`, `reduce_all`;
[theme.py](../mudplot/theme.py) `theme_preset`.

- `tests/test_review_core_boundaries.py::test_core_hash_survives_fresh_process_cwd_clock_rng_and_interleaved_styles`
- `tests/test_review_core_boundaries.py::test_previous_render_style_cannot_change_reducer_result`

The `_CORE` subprocess fixture repeats a normalized state sequence in fresh `-S`
processes with different CWD, mocked clock, hash/Python-random seeds0/97 and four
interleaved themes. Hashes agree and Python RNG state is unchanged. The separate
real previous-render/style test does not affect reducer results. This does not
claim every environment variable, custom callback or NumPy RNG scenario was tested.

## STATE-08 — references and index boundaries

Implementation: [reducer.py](../mudplot/reducer.py) `reduce`, `_ensure_panel`;
[actions.py](../mudplot/actions.py) `action_from_dict`;
[validate.py](../mudplot/validate.py) `validate`, `assert_valid`;
[_render.py](../mudplot/_render.py) `render`.

- `tests/test_review_core_boundaries.py::test_invalid_layer_indices_never_select_a_different_target` (24 cases)
- `tests/test_review_core_boundaries.py::test_missing_panels_extend_but_absent_layers_do_not_modify_existing_panels`
- `tests/test_review_core_boundaries.py::test_reduce_can_build_invalid_references_but_render_validates_before_effects` (2 cases)
- `tests/test_review_core_boundaries.py::test_invalid_panel_indices_and_unknown_wire_actions_preserve_state` (6 cases)

Negative/out-of-range/bool/float/string/null layer indices across three actions
must not select another layer. Positive missing panel2 intentionally autoextends;
missing layers still reject. Absent data/matrix references can be assembled by
pure reduce but explicit validate and render report the same issues. State/action/
history and valid recovery remain intact. Maximum panel limits and all malformed
wire-key/type classes are not exhaustively covered by this selected file.

## STATE-09 — core operation/effect boundary

Implementation: the reducer/validate/render symbols above;
[schema.py](../mudplot/schema.py) `json_schema`;
[capabilities.py](../mudplot/capabilities.py) `capabilities`.

- `tests/test_review_core_boundaries.py::test_core_hash_survives_fresh_process_cwd_clock_rng_and_interleaved_styles`
- `tests/test_review_core_boundaries.py::test_reduce_can_build_invalid_references_but_render_validates_before_effects` (2 cases)

Operation-phase audit/import guards reject data-file reads/writes, directory,
network/subprocess and optional-dependency effects during representative schema/
capabilities/validate/reduce calls. Readonly Python `.py`/`.pyc` loading is allowed;
initial core import occurs before the hook and blocked optional modules are checked
absent. This is not an interpreter or arbitrary user-Python-method sandbox.
Render may import its backend before validation, but source inspection confirms
`assert_valid` precedes Figure allocation. The two missing-reference cases verify
error parity; they do not independently audit every possible render effect.

## Reproduction and next coverage boundary

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_state_contracts.py \
  -k 'test_state_01 or test_state_02 or test_state_04 or test_state_05 or test_state_06' \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_core_boundaries.py \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_editor_paths.py \
  -k 'not test_python_failures' --junitxml=<private-results.xml>
```

The public artifacts contain synthetic fixtures/test names and hashes, not raw
logs, secrets or user-local absolute paths. Private raw receipts are not a durable
web download. Recheck symbol/source fingerprints after implementation changes.

The remaining141 IDs still need their own reviewed symbol/node/provenance links
and classification. Do not infer missing coverage
from their omission here or infer completion from a test filename/collection/pass.
