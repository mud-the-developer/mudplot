# Checklist implementation/test map — partial

Original: [2026-10-16 checklist](../mudplot_review_checklist_detailed_2026-10-16.md).
Candidate inventory/status: [review ledger](REVIEW_CHECKLIST_STATUS.md).
Execution/source fingerprints: [first five state IDs](review_evidence/review_map_state_core.json),
[determinism/indices/effect boundaries](review_evidence/review_map_state_boundaries.json),
[cross-path fixture and retained Native provenance](review_evidence/review_map_state_paths.json),
[history boundary/branch/failure provenance](review_evidence/review_map_history_core.json),
[open/reset/no-op policy and Python browser proof](review_evidence/review_map_document_policy.json),
[bounded replay/gesture/checkpoint evidence](review_evidence/review_map_history_design.json).

## Scope and classification

This is a **seventeen-ID state/history mapping**, not a complete150-ID map.
The remaining133 IDs have not been classified here. The candidate inventory still
contains all150 original IDs, but filenames and PASS labels are not coverage proof.
BASE-05 remains RUNNING; original counts139PASS/6RUNNING/4OPEN/1DEFERRED are unchanged.
Prior phase-specific evidence is not invalidated or re-labelled by this partial map.

For each reviewed ID, classify as **existing coverage**, **additional test needed**
or **design decision needed** after reading the implementation and assertions.
All seventeen below have existing coverage of the explicitly stated boundary; no new
runtime/test code or compatibility decision was needed for this mapping unit.
AST checks only resolve references, not prove their semantic adequacy.

The first five IDs were reviewed at `52acc3f30ce6afdc88a305966a3f9b323e98c76a`:
**13 passed,2 deselected,0 skipped/failed,exit0**. The two deselected HIST nodes
were not run or counted in that first run; the separate HIST run below executes
them later. The next three were reviewed at doc-only `701e3be` with
runtime unchanged: **35 unique passed nodes,0 skipped/failed,exit0**. Their38
ID/node relationships overlap; do not count them as38 separate tests. Across the
first two runs,48 unique nodes executed, not51. STATE-03 adds6 fresh Python
nodes(4 failure cases deselected), giving54 unique fresh nodes across three runs,
not57 summed ID relationships. HIST-01/02/03 add6 previously unselected nodes,
giving60 unique fresh pytest nodes across four focused runs, not63 summed ID
relationships. HIST-04/05 add4 new nodes(unit3/Python real-browser1), yielding64
unique executed pytest nodes across those runs. HIST-06/07/08 add14 distinct nodes
(replay2/checkpoint9/real-browser3), bringing the recorded unique total to78.
Historical performance profile is not a new timing run. The browser cases must execute;
receipt checks reject any skip. The separate13-row cursor/hash assert probe is not
a pytest count. Native provenance is a separate previous execution
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
| HIST-01 | Existing coverage | 1 fresh Python passed; retained Native check | Complete replay/boundaries plus separate cursor/hash probe |
| HIST-02 | Existing coverage | 1 fresh Python passed; retained Native check | Branch invalidation and saved spec/preview coherence |
| HIST-03 | Existing coverage | 4 fresh Python passed; retained Native check | Validation/import/real render failures retain spec/history/PNG/future |
| HIST-04 | Existing coverage | 1 unit + 1 actual Python browser passed; retained Native check | Distinct open/reset policies/current downloads/source files untouched; no dirty feature invented |
| HIST-05 | Existing coverage | 2 fresh Python passed; retained Native check | Equal-value events/listeners/history/redo invalidation and preview coherence |
| HIST-06 | Existing coverage | 2 seeded replay passed | Bounded768-action sequences and128 undo/redo each, exact states/hashes |
| HIST-07 | Existing coverage | 3 actual browser passed | Measured mouse-release commits/independent edits and keyboard burst semantics |
| HIST-08 | Existing coverage | 9 checkpoint passed; historical profile/design | One prior64-action state, no history truncation/public limit or new performance claim |

STATE-07/08/09 refer to35 unique tests, not their38 summed relationships.

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

## HIST-01 — undo/redo and boundaries

Implementation: [store.py](../mudplot/store.py) `Store._replay`, `Store.undo`,
`Store.redo`, `Store.history`; [Rust session](../mudplot-editor/src/lib.rs)
`Session.undo`, `Session.redo`.

- `tests/test_review_state_contracts.py::test_hist_01_undo_redo_visits_every_expected_state_and_stops_at_boundaries`

Three distinct title/size/palette actions visit every expected state and history
prefix, then repeat empty/start/end boundaries. A separate assert-based probe
using `_nested_plot` records13 event/cursor/state-hash rows in the linked history
artifact; it does not add13 pytest cases. The retained Native
`scripts/rust_editor_smoke_test.py::_review_history_contracts` checks JSON/PNG at
every step and begins before new-layer scenarios, preserving fresh-history bounds.
This is basic replay, not long-history/resource coverage.

## HIST-02 — branch after undo

Implementation: `Store._dispatch`; [Python session](../dashboard/editor_server.py)
`EditorSession.dispatch_safe`, `_commit_store`, `undo`, `redo`;
[IO](../mudplot/io.py) `save_spec`, `load_spec`; Rust `Session.apply`, `undo`, `redo`.

- `tests/test_review_state_contracts.py::test_hist_02_editor_branch_keeps_saved_state_history_and_preview_on_new_branch`

A→B→C, undo→B, dispatch→D cannot redo C. Python exact state/history/PNG and a
saved-load spec remain on D; retained Native history helper checks the same
JSON/PNG branch coherence. Python opens fresh history while Rust open is an
undoable snapshot. This mapping does not change that policy or cover the entire
reset/open/dirty/save-target matrix (HIST-04).

## HIST-03 — editor failure atomicity

Implementation: Python `EditorSession.dispatch_safe`, `_commit_store`, `load_spec`,
`redo`; Rust `Session.apply`, `undo`, `redo` (prospective render before commit).

- `tests/test_review_editor_paths.py::test_python_failures_preserve_spec_history_preview_and_future` (4 cases)

The four modes are invalid SetSize validation, damaged JSON, actual Matplotlib
invalid-colour action render and invalid-colour spec import render. The colour
fixture deliberately passes pure validate to exercise the effect failure. Python
compares exact state/history/PNG and redo-future bytes then recovers normally.
The retained `scripts/rust_editor_smoke_test.py::_review_failure_contracts` exercises
the same four Native HTTP failures and JSON/PNG/future/recovery assertions.

The linked retained full Native execution has matching source28/raw8 fingerprints
and successful history/failure log markers. It was not rerun for this mapping.
There is no new Native per-stage PNG hash table, Linux/MSRV/browser/binary
attestation or claim about every OS/bridge fault. Existing direct equality
assertions and the fresh Python/probe provenance are recorded separately.

## HIST-04 — existing document/open/reset policies

Contract: [COMPATIBILITY.md, state/action semantics](COMPATIBILITY.md).
Implementation: [Python session](../dashboard/editor_server.py) `EditorSession.load_spec`,
`reset`, `_commit_store`; `Store.undo`, `Store.redo`; Rust `Session.open`, `reset`.

- `tests/test_review_history_policies.py::test_python_open_and_reset_start_fresh_history_without_touching_imported_files`
- `tests/test_editor_browser.py::test_open_reset_and_download_keep_python_document_history_and_source_files_separate`

Fresh Python unit checks A/future/undo/open B starts a fresh history, selected
panel0, empty undo/redo boundaries, current JSON/SVG and unchanged source A/B bytes.
Reset starts the default empty document and fresh history. The fresh actual browser
case uses the file picker, unsaved A edit, open B, undo/redo, real JSON download B,
reset/default download, and verifies both source files unchanged. Both nodes ran;
no browser skip was counted as success.

Neither editor binds uploaded filenames to automatic overwrites or implements a
separate persistent dirty-bit/save-target feature. Do not invent one to satisfy
checklist terminology. Rust open/reset deliberately remain undoable snapshots;
reset returns startup state, not the last import. Current-source-matched retained
`_review_document_policies` Native execution checks A/future/open B/undo-redo/Bedit/
reset/undo-redo and JSON/PNG coherence. This is not a new Native/browser/Linux/MSRV
run or binary attestation. Historical canceled CI39050108296 is not used as an
ALL5-success result.

## HIST-05 — equal-valued changes remain events

Implementation: `Store._dispatch`, `Store.history`, `Store.subscribe`;
`EditorSession.dispatch_safe`; Rust `Session.apply`.

- `tests/test_review_history_policies.py::test_store_noop_is_an_event_and_clears_the_old_redo_branch`
- `tests/test_review_history_policies.py::test_python_editor_noop_keeps_an_event_and_identical_successful_preview`

SetTitle A after A/B/undo A leaves identical state but adds a history event and
listener notification, clears old redo and permits same-state undo to drop one
event. Python editor keeps the no-op action with identical successful PNG/current
saved spec and SVG. The retained Native helper tests repeated no-op snapshots and
old-redo invalidation with JSON/PNG equality. This does not optimize events away
or assert a dirty bit which the documented editor does not have. Long seeded
replay, drag coalescing and checkpoint policy are separate items, not run here.

## HIST-06 — bounded seeded replay

Implementation: `Store._dispatch`, `_replay`, `undo`, `redo`; `reduce_all`.

- `tests/test_review_history_policies.py::test_seeded_long_history_replay_matches_exact_states_without_numeric_drift` (seeds20261016/24301)

Each seed generates768 valid title/size/font/limit actions, compares each dispatch
state, then128 undo/128 redo/history cursors and full apply/canonical state hash.
This is exact bounded replay, not unlimited history performance or leak proof.

## HIST-07 — measure existing gestures before coalescing

Implementation: [editor_view.py](../dashboard/editor_view.py) `_DRAG_JS` mouse
move/release and180ms keyboard post queue; `EditorSession.dispatch_safe`.

- `tests/test_review_gesture_browser.py::test_mouse_gestures_commit_once_and_keep_independent_edits_and_undo`
- `tests/test_editor_browser.py::test_arrow_keys_nudge_the_title`
- `tests/test_editor_browser.py::test_a_burst_of_nudges_is_not_dropped`

Fresh real-browser trace records two gestures of100 moves each: zero requests
while moving, one on release. Focus-only click emits zero edits. Independent title
change between gestures remains a separate event; undo reverses one gesture while
preserving the title. Keyboard tests retain nudge/burst effects. Existing behavior
already gives these boundaries, so the retained design deliberately adds no new
core coalescer, Esc cancel or gesture API. Measured round-trip samples are local
observations, not a latency service guarantee.

## HIST-08 — one internal checkpoint, no truncation

Implementation: `Store.__init__`, `_dispatch`, `_replay`, `state`, `history`;
[profiler](../scripts/profile_history_costs.py) `collect_case` preserves partial/null
measurements instead of treating missing timing as zero.

All nine existing nodes in [test_review_history_checkpoint.py](../tests/test_review_history_checkpoint.py) were executed:

- `test_near_tail_checkpoint_is_single_prior_state_and_replay_stays_exact`
- `test_branch_below_checkpoint_invalidates_only_cache_not_history_semantics`
- `test_branch_at_checkpoint_reuses_valid_prefix_and_clears_redo`
- `test_public_snapshot_mutation_cannot_change_internal_checkpoint`
- `test_custom_reducer_keeps_full_replay_and_gets_no_default_cache`
- `test_failed_dispatch_does_not_replace_valid_checkpoint`
- `test_listener_failure_after_checkpoint_commit_does_not_roll_back`
- `test_noop_at_cache_boundary_is_still_an_event`
- `test_setdata_checkpoint_and_action_payloads_remain_detached`

The default pure reducer retains one previous64-action boundary state, deep-copies
before replay, falls back before the cached prefix, and invalidates it on an older
branch. Custom reducers keep full replay/call counts. All history/redo/no-op/
listener/snapshot semantics remain; no public memory limit or history truncation.

The [historical profile/design record](review_evidence/history_improvement_verification.json)
includes fixed9-case before/after and two memory comparisons. Six relevant store/
reducer/gesture/checkpoint/profiler hashes still match, but the old timing is not
rerun or promoted to current performance. Three large targets remain stopped/
incomplete (10,000rows×1,000actions;100,000×100;100,000×1,000). Unknown timings
remain unknown, not zero or completed. One extra full supported Spec is not a hard
OS RSS bound or a long-lived GUI leak guarantee. Other fields in that artifact
are historical, not refreshed by this mapping.

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

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_state_contracts.py::test_hist_01_undo_redo_visits_every_expected_state_and_stops_at_boundaries \
  tests/test_review_state_contracts.py::test_hist_02_editor_branch_keeps_saved_state_history_and_preview_on_new_branch \
  tests/test_review_editor_paths.py::test_python_failures_preserve_spec_history_preview_and_future \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_history_policies.py::test_python_open_and_reset_start_fresh_history_without_touching_imported_files \
  tests/test_review_history_policies.py::test_store_noop_is_an_event_and_clears_the_old_redo_branch \
  tests/test_review_history_policies.py::test_python_editor_noop_keeps_an_event_and_identical_successful_preview \
  tests/test_editor_browser.py::test_open_reset_and_download_keep_python_document_history_and_source_files_separate \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_history_policies.py::test_seeded_long_history_replay_matches_exact_states_without_numeric_drift \
  tests/test_review_history_checkpoint.py tests/test_review_gesture_browser.py \
  tests/test_editor_browser.py::test_arrow_keys_nudge_the_title \
  tests/test_editor_browser.py::test_a_burst_of_nudges_is_not_dropped \
  --junitxml=<private-results.xml>
```

The public artifacts contain synthetic fixtures/test names and hashes, not raw
logs, secrets or user-local absolute paths. Private raw receipts are not a durable
web download. Recheck symbol/source fingerprints after implementation changes.

The remaining133 IDs still need their own reviewed symbol/node/provenance links
and classification. Do not infer missing coverage
from their omission here or infer completion from a test filename/collection/pass.
