# Checklist implementation/test map — partial

Original: [2026-10-16 checklist](../mudplot_review_checklist_detailed_2026-10-16.md).
Candidate inventory/status: [review ledger](REVIEW_CHECKLIST_STATUS.md).
Execution/source fingerprints: [first five state IDs](review_evidence/review_map_state_core.json),
[determinism/indices/effect boundaries](review_evidence/review_map_state_boundaries.json),
[cross-path fixture and retained Native provenance](review_evidence/review_map_state_paths.json),
[history boundary/branch/failure provenance](review_evidence/review_map_history_core.json),
[open/reset/no-op policy and Python browser proof](review_evidence/review_map_document_policy.json),
[bounded replay/gesture/checkpoint evidence](review_evidence/review_map_history_design.json),
[strict JSON input and Rust codec evidence](review_evidence/review_map_json_input.json),
[JSON-09 structural evidence and remaining semantic work](review_evidence/review_map_default_semantics_gap.json),
[modeled-field cross-language codec and additive metadata evidence](review_evidence/review_map_structural_codec.json),
[render-range/canonical/drift/recovery evidence](review_evidence/review_map_json_effects.json),
[table-structure and SQL ownership evidence](review_evidence/review_map_data_boundaries.json),
[available-adapter/missing-cohort and explicit optional-skip evidence](review_evidence/review_map_adapter_missing.json),
[legacy group identity and scalar conversion evidence](review_evidence/review_map_groups_scalars.json),
[temporal precision and per-layer boundary/order evidence](review_evidence/review_map_data_policies.json),
[real optional-adapter execution in an unchanged-base uv overlay](review_evidence/review_map_optional_execution.json).

## Scope and classification

This is a **thirty-eight-ID state/history/JSON/data mapping**, not a complete150-ID map.
The remaining112 IDs have not been classified here. The candidate inventory still
contains all150 original IDs, but filenames and PASS labels are not coverage proof.
BASE-05 remains RUNNING; original counts139PASS/6RUNNING/4OPEN/1DEFERRED are unchanged.
Prior phase-specific evidence is not invalidated or re-labelled by this partial map.

For each reviewed ID, classify as **existing coverage**, **additional test needed**
or **design decision needed** after reading the implementation and assertions.
Thirty-seven below have existing coverage of their explicitly stated boundary.
JSON-09 remains **additional test needed** for its all-field meaning matrix.
DATA-01/05's earlier optional execution gaps were filled by the separate declared
uv overlay run below, not by retroactively changing skipped receipts. Existing
tests filled those gaps; no duplicate tests/UI/production policy was added.
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
(replay2/checkpoint9/real-browser3), bringing that recorded unique total to78.
The strict JSON input run adds96 distinct Python nodes(0 skip), for174 unique
Python nodes across recorded runs. Rust model11 passed is a separate count, not
185 Python cases; its broader structural tests do not close JSON-01/08/09 here.
Historical performance profile is not a new timing run. The browser cases must execute;
receipt checks reject any skip. The separate13-row cursor/hash assert probe is not
a pytest count. Native provenance is a separate previous execution
with matching source/fixture/final hash, not a newly run native/browser test.
These are focused results, not a full-suite or release result. Source/body/log/JUnit hashes and
expanded parameterized node IDs are recorded in the separate immutable artifacts.

JSON-09's separate current168 cases(139nullable+20tokens+5CLI PNG+4marker values)
bring recorded distinct Python nodes to342. The initial private receipt expected
165 by miscounting four marker parameters as one; pytest passed168, and only that
receipt assumption was corrected. Passing these cases does not close JSON-09.

JSON-01/08 add74 distinct current Python nodes, bringing the recorded unique
Python total to416. Their selected Rust2 tests are separate reruns of existing
codec/consumer nodes, not a growing unique Rust/Python combined count. Three
Rust-output→Python comparisons are an additional assert probe, not pytest cases.

JSON-05/10/11/12 add30 distinct current Python nodes, bringing the recorded unique
total to446. The real sync checker ran first and returned0 for all four generated
targets. No new full-suite, Native/Rust/browser or resource benchmark is claimed.

DATA-02/07 add59 distinct current Python nodes(49 structure/10 SQL ownership),
bringing recorded unique Python nodes to505. Real pandas cases ran without skips;
duck-protocol negative tests do not imply real PyArrow/Polars compatibility.

DATA-01/03 record19 new unique passed Python nodes and5 explicit optional skips.
Recorded passed-node total is524; skipped cases are never counted as passes.
Both IDs reuse9 passed adapter cases, so do not sum9+19 as28 new executed tests.

DATA-04/06 add77 distinct passed Python nodes(6 legacy group/71 scalar), giving601
recorded unique passed nodes plus the same5 optional skips, not606 passes. Separate
four synthetic group/RGBA/legend probes are not pytest cases.

DATA-05/08/09 add74 distinct passed Python nodes and7 optional timestamp skips.
Recorded unique passed total is675, with12 separate optional skipped nodes—not687
passes. This unit assigns only its layer/input/range-specific boundaries.

The subsequent uv optional overlay run executes all95 existing missing/temporal/
table-library cases with0 skips. Twelve historically skipped nodes now actually
pass in this separate run, plus13 new table-library nodes. Recorded unique passed
Python nodes are700, not675+95; previously passed repetitions are not added again.
Old12 skipped receipts remain unchanged historical facts, not retroactive passes.

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
| JSON-01 | Existing coverage | 73 fresh Python + selected Rust codec passed | All modeled-field structure/types/order and three actual Rust-output→Python probes; not renderability |
| JSON-02 | Existing coverage | 35 Python passed; retained Native app | Strict nonfinite/overflow rejection vs adapter missing normalization |
| JSON-03 | Existing coverage | 48 Python passed; fresh Rust strict codec | Recursive equal/different duplicate keys and output preservation |
| JSON-04 | Existing coverage | 1 Python passed; fresh Rust integer codec | Signed decimal boundaries/known data fields, not rendering range |
| JSON-05 | Existing coverage | 16 fresh Python passed | Exact huge JSON integers versus clear render failure/output/figure/editor preservation |
| JSON-06 | Existing coverage | 5 Python passed; fresh Rust/retained Native | Unicode pairs/lone surrogates/reserved object keys |
| JSON-07 | Existing coverage | 7 Python passed; fresh Rust default/retained Native app | Current/omitted spec version vs unsupported/malformed versions |
| JSON-08 | Existing coverage | 1 fresh Python + selected Rust consumer passed | Known base unknown-field ignore vs Any metadata and additive capabilities acceptance |
| JSON-09 | Additional test needed | 168 current structural/representative passed | Remaining role/layer/AUTO/default meaning matrix, not a product-failure finding |
| JSON-10 | Existing coverage | 1 fresh Python passed | Canonical representation invariance with list-order/type counterexamples |
| JSON-11 | Existing coverage | Sync first0 + 5 fresh Python passed | Isolated intentional drift and registry/schema/cap/reference agreement |
| JSON-12 | Existing coverage | 8 bounded-child Python passed | Damage/depth/valid-large-array handling, previous output and next-input recovery |
| DATA-01 | Existing coverage | Declared optional overlay95/95 run; all14 formats executed | Source/values/order/missing/group compatibility in stated versions; prior5skip preserved |
| DATA-02 | Existing coverage | 49 fresh Python passed | Row widths/types/column keys before pivot, missing columns and effect failure preservation |
| DATA-03 | Existing coverage | Initial19P5skip, later optional run all24 passed | Source-preserving missing/gaps/pairs/stat cohort in declared adapters, not every scalar/context |
| DATA-04 | Existing coverage | 6 fresh Python passed; separate4 group/RGBA probes | Legacy Python-equality membership/order/caption policy, not uniform semantic/stat grouping |
| DATA-05 | Existing coverage | Initial51P7skip, later optional run all58 passed | Stated precision/TZ/locale/dtype policy in recorded versions, not all date ranges/locales |
| DATA-06 | Existing coverage | 71 fresh Python passed | Supported scalar builtin normalization vs explicit unsupported-object rejection/bounded item conversion |
| DATA-07 | Existing coverage | 10 fresh Python passed | Bound params, owned vs borrowed cursor/connection/transaction lifetime and cleanup failure context |
| DATA-08 | Existing coverage | 17 fresh Python passed | Selected raw-empty/stat-empty/singleton/constant layer expectations, not all-layer uniform policy |
| DATA-09 | Existing coverage | 6 fresh Python passed | Raw duplicates/path/gaps/bar values vs explicit lineplot aggregation/sort/per-hue order |

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

## JSON-02/03/04/06/07 — strict input and structural boundaries

Implementation: [io.py](../mudplot/io.py) `_loads_json`, `_reject_json_constant`,
`_reject_duplicate_keys`, `_validate_json_value`, `to_json`, `from_json`;
[data.py](../mudplot/data.py) `_plain_value`, `to_columns`;
[spec.py](../mudplot/spec.py) `migrate_spec_dict`;
[CLI](../mudplot/__main__.py) `_cmd_apply`, `_cmd_migrate`;
[Rust codec](../mudplot-editor/src/model.rs) `from_json_strict`,
`StrictJsonVisitor.visit_map`, `reject_reserved_keys`, `FigureSpec` envelope.
Source bodies were read; fresh Python96 and Rust model11 passed without skipped
NumPy/pandas adapter cases. Only the stated boundaries are assigned to these IDs.

In [test_review_json_contracts.py](../tests/test_review_json_contracts.py), exact
base nodes (parameter expansions in the machine-readable artifact):

- JSON-02: `test_json_02_nonfinite_raw_spec_numbers_fail_without_output_change` (20),
  `test_json_02_adapter_missing_normalization_is_separate_from_infinity_rejection` (15).
  Strict NaN/Infinity/-Infinity/exponent overflow fail before replacing outputs.
  Adapter NaN/NA becomes None; Infinity remains a value then strict serialization
  rejects it, rather than silently treating it as missing.
- JSON-03: `test_json_03_public_loaders_reject_equal_and_different_duplicates_at_all_depths` (18),
  `test_json_03_cli_rejects_duplicate_specs_and_preserves_output` (24),
  `test_json_03_cli_action_duplicates_do_not_apply_a_partial_result` (6).
  Root/nested/array-object equal and unequal duplicates reject across selected
  loaders and CLI validate/migrate/apply/render; source/previous output survive.
- JSON-04: `test_json_04_known_data_fields_preserve_signed_integer_boundaries` (1).
  Python known data fields preserve positive/negative2^53, signed/unsigned64-bit
  boundaries and larger integers as ints, not floats. Fresh Rust
  `model::tests::strict_json_preserves_signed_integer_boundaries_and_valid_unicode`
  checks the same supported data path/decimal strings; the arbitrary-precision
  envelope test is separate. This is not JSON-05 renderer precision support.
- JSON-06: `test_json_06_normal_unicode_and_valid_surrogate_pairs_remain_structural_data` (2),
  `test_json_06_nested_reserved_keys_and_lone_surrogates_are_rejected` (3).
  Fresh Rust reserved-key, duplicate-key and signed-integer/Unicode tests preserve
  normal text/pairs and reject reserved object keys/lone surrogates. This selected
  file does not exhaust every directly constructed Python non-string map-key case.
- JSON-07: `test_json_07_unknown_or_malformed_versions_never_replace_cli_output` (7).
  `SPEC_VERSION=0.1` is distinct from package1.0.0; migration registry is empty.
  Current or omitted version works, unknown/unimplemented-old/malformed values
  fail without overwriting output. Rust's omitted-version/default-null test is a
  structural envelope test, not a second Python version-policy validator.

The retained source-matched Native `_review_json_boundaries` execution rejects
19 specs/11 actions and accepts2 Unicode/current-or-omitted cases while preserving
state/PNG. Its source28/raw8 and corpus equal the captured52 source. It supplies
application-path evidence for JSON-02/06/07, not a new Native/browser/Linux/MSRV run
or a new HTTP duplicate-key test. Raw Rust arbitrary-precision JSON may retain
large finite lexical numbers/future version strings; Python bridge validation
applies the application float/version policy. Do not force the two roles equal.

Rust model11 includes other structural/capability/token tests; passing that group
does not map all fields' default/AUTO semantics or complete JSON-01/08/09.

## JSON-01/08 — modeled structure and additive metadata

Implementation: `SpecBase.to_dict/from_dict`, `spec._from_dict`, `io.to_json/from_json`;
[Rust model](../mudplot-editor/src/model.rs) `FigureSpec`, `Capabilities` and strict
serde conversion. Fixture [review_full_spec_fields.json](../tests/fixtures/review_full_spec_fields.json)
contains24 current model types/272 fields in three filled/alternate/nullable figures.
They deliberately combine incompatible options and are not renderable plots.

Current selected nodes in `tests/test_review_full_spec_fields.py`:

- `test_structural_fixture_covers_all_dataclasses_and_nondefault_fields` (1)
- `test_checked_in_fixture_matches_current_fields_and_generator` (1)
- `test_every_structurally_supported_field_survives_python_json` (6)
- `test_each_model_default_preserves_nested_types_and_nullable_values` (24)
- `test_registered_layer_examples_round_trip_supported_values` (41)

All73 passed. Filled variants exercise every modeled nondefault field; defaults
preserve nested types, ASCII/non-ASCII JSON preserves types/values/list order, and
registered examples validate before codec comparison. Existing139 nullable cases
were deselected because their independent JSON-09 provenance is already recorded.
Rust `model::tests::full_field_fixture_preserves_types_values_and_array_order`
was freshly run with test-only `MUDPLOT_CODEC_PROBE_OUT=<owned-private>` and wrote
three actual Rust-serialized figures. Separate type-aware recursive assertions
compared keys/JSON types/list order/values to the fixture and reloaded each through
both `mp.from_json` and `Plot.from_json`. No production probe endpoint was added.

JSON-08 current node:
`tests/test_review_json_policies.py::test_known_version_ignores_unknown_dataclass_fields_but_keeps_data_metadata`.
Known-version base figure/theme/panel/layer unknown fields are ignored by Python;
Any data metadata survives, while an unknown spec version rejects. Typed closed
configs retain their own unknown-field rejection rule. This does not require
unsupported fields to survive a Python round-trip.

Fresh Rust `model::tests::capabilities_accept_additive_top_level_and_layer_metadata`
adds top-level metadata and layer metadata to the embedded capability document;
its known consumer summary remains identical. Additive consumer acceptance is
separate from Python spec unknown-field policy. This pair is fresh selected
Rust2, not a new Native HTTP/browser/Linux/MSRV run, binary attestation, every
visual-control approval or JSON-09 semantic meaning completion.

## JSON-09 — structural evidence is not the full meaning matrix

Implementation: `spec._from_dict`, `SpecBase.to_dict/from_dict`,
`schema.json_schema/_dataclass_schema`, `io.to_json/from_json`, CLI `_cmd_migrate`.
Contract: [COMPATIBILITY.md, JSON/defaults](COMPATIBILITY.md).

- `tests/test_review_full_spec_fields.py::test_every_nullable_field_distinguishes_omitted_null_and_explicit_default` (139)
- `tests/test_review_json_policies.py::test_render_token_fixture_schema_python_and_cli_migrate_agree` (20)
- `tests/test_review_json_policies.py::test_fresh_cli_empty_render_token_matches_python_png` (5)
- `tests/test_review_json_policies.py::test_optional_marker_omission_null_zero_and_explicit_value` (4)

Current inventory is24 models/272 modeled fields/139 nullable fields—cardinality,
not coverage probability. The nullable test checks schema+Python omitted→model
default, explicit null/default and typed zero/False. The representative fixture has
five layer/field combinations(line.marker,line.line_style,scatter.marker,
scatter3d.marker,line3d.line_style), four variants each. Five empty tokens also
render through actual CLI subprocess and match Python PNG. Marker size cases are
omitted/null/0/7.5. Source-matched previous Rust model11 codec tests preserve raw
fullfield/token representation; they were not rerun for this mapping unit.

**Additional work needed:** a role/layer meaning matrix for applicable fields
across schema/Python/CLI/Rust/UI, recording accept/reject/not-applicable rather
than forcing every nullable option into every control. Nontrivial defaults include
StatSpec.errorbar=`ci` versus null, LayerSpec.inner=`legacy` versus null, and
marker_size0 versus automatic sizing. Structural equality alone does not specify
the computed interval/glyph/auto value. Record prior-fixture semantic reload and
possible default-change effects without inventing unsupported old spec versions.

Reuse existing marker/stat/distribution renderer tests where they already cover
these meanings; do not add139 duplicate codec cases or infer that other137 fields
are uncovered merely because the token fixture names two fields. This row marks
reviewed evidence insufficient to close the checklist item, not a demonstrated
product failure. JSON-09 and BASE-05 remain RUNNING; formal ledger counts do not
change just because the ID now has a source/test/gap map.

## JSON-05 — structure is not arbitrary-precision plotting

Implementation: `_render._float_array`, `_x_values`, `render`; `io._atomic_destination`;
`EditorSession.load_spec`, `_commit_store`.

- `tests/test_review_render_contracts.py::test_json_05_unrepresentable_values_preserve_output_and_close_figures` (15)
- `tests/test_review_render_contracts.py::test_json_05_failed_editor_open_preserves_state_history_preview_and_recovery` (1)

10^1000 survives JSON and Plot reconstruction exactly. Selected x/y/matrix/style/
size cases across PNG/PDF/SVG instead fail clearly through CLI, preserve previous
sentinel output bytes, leave the figure set unchanged and add no temporary files.
Editor invalid open keeps spec/history/PNG and can recover with a valid document.
This does not ban large integers everywhere or claim arbitrary-precision rendering/
a fresh Native huge-coordinate test. Numeric conversion normalizes overflow errors;
render owns Figure cleanup and output replacement stays atomic.

## JSON-10 — canonical without erasing data meaning

Implementation: `io.to_json`, `io.from_json`.
`tests/test_review_json_policies.py::test_canonical_keys_whitespace_and_unicode_do_not_reorder_or_coerce_data`
compares public `sort_keys=True,indent=None` output hashes after key-order,
whitespace and Unicode-escape variants. Reversed data lists and int→float controls
must differ. This is the existing Python canonical policy, not a global list sort,
all-language canonicalization or cryptographic semantic-collision guarantee.

## JSON-11 — generated outputs and registry drift

Implementation: [check_schema_sync.py](../scripts/check_schema_sync.py)
`_regenerate`, `main`; `capabilities`, `json_schema`.

- `tests/test_review_generated_drift.py::test_checker_rejects_drift_then_accepts_restored_copy` (4 targets)
- `tests/test_review_generated_drift.py::test_layer_action_registry_schema_capabilities_and_reference_agree`

The real checker first returned0 for figure schema, capabilities, REFERENCE and
PLOT_GALLERY. Tests copy targets to isolated temporary storage, introduce drift,
require failure plus exact target/regeneration hint, restore original bytes and
require success. The registry case checks action dataclass fields and layer/schema/
cap/reference names agree. Originals are not manually patched or regenerated in
place to hide drift; the checker generates fresh temporary expected outputs.

## JSON-12 — bounded corrupt inputs and recovery

Implementation: `io._loads_json`, `from_json`, `_atomic_destination`, CLI `_cmd_migrate`.

- `tests/test_review_json_policies.py::test_cli_damage_does_not_replace_output_and_next_migrate_can_recover` (4)
- `tests/test_review_json_policies.py::test_bounded_child_json_checks_are_errors_or_lossless_and_can_recover` (4)

Truncated JSON, bad UTF-8,3,000 nested arrays and a valid20,000-int array run in
20-second bounded children. Invalid cases fail without Traceback/output replacement;
valid large data is lossless. Both CLI and direct-loader children then accept a
normal recovery payload. These synthetic sizes/timeouts are not a global CPU/RAM/
HTTP sandbox, unbounded resource guarantee or every encoding/depth taxonomy.

## DATA-01 — optional execution is not inferred from imports or old status

Implementation: `data.to_columns`, `_plain_value`, `_to_list`,
`_records_to_columns`, `_rows_to_columns`, `_cursor_to_columns`.

`tests/test_review_missing_data.py::test_adapter_values_and_layer_missing_cohorts_agree`
initially passed9 base-environment shapes: mapping, records, rows, NumPy object2D, structured NumPy,
nullable pandas, SQLite connection/query, borrowed SQLite cursor, generic to_dict.
The declared positional format supplies generated column names; values/order/
missing/group meaning are compared through the corresponding names, not forced
into a nonexistent common naming contract. Source objects/JSON remain unchanged;
borrowed cursor/connection reuse remains valid.

Real PyArrow, chunked Arrow, dictionary Arrow, Polars and categorical Polars
were5 explicit skips in that base run, not5 passes. The new declared uv overlay
actually executes all14 format variants plus the real table-library cases; the
source/values/typed integers/booleans/Unicode/nulls/empty/duplicate-column/unsupported
scalar checks pass. A duck-protocol negative fixture is still not a substitute.

The base environment still has no PyArrow/Polars and was not modified. Only a uv
`--with` temporary overlay supplied PyArrow26.0.0/Polars2.0.0; exact versions and
protected project/lock/base-version before/after hashes are recorded. The prior
skips and historical master PASS remain untouched; current classification now has
actual optional evidence for these versions, not a new test/driver guarantee.

## DATA-02 — rectangular input boundaries, not silent repair

Implementation: [data.py](../mudplot/data.py) `_column_names`, `_records_to_columns`,
`_row_values`, `_rows_to_columns`, `_cursor_to_columns`, `to_columns`;
[validate.py](../mudplot/validate.py) `_check_column`, `_check_data_integrity`;
CLI `_cmd_apply` and `EditorSession._commit_store` prospective commit.

All49 current parameterized nodes in [test_review_data_contracts.py](../tests/test_review_data_contracts.py)
ran. Exact expanded names are recorded in the artifact. They cover ragged
positional rows(4), DB description/width(3), bad records(8), bad rows(10), stringified
key collision(1), sparse union order/None(1), unequal columns(4), missing x/y/group
for line/scatter(6), real pandas duplicate names(2), editor failure retention(4),
CLI source/previous output retention(4), SQLiteRow support(1), valid rows/order(1).

Malformed widths/types identify row/record positions before zip/pivot. Records
must be mappings; strings/bytes/map keys are not positional rows. Stringifying
column names must not overwrite a previous column. Sparse records keep first-seen
union order and None; unequal columns remain unchanged at ingestion then validation
rejects them. No padding/truncation or sorting/duplicate-x repair is introduced.
Editor invalid open/action keeps spec/history/PNG/redo; CLI failure keeps input and
sentinel output. Duck DataFrame/Arrow/to_dict malformed fixtures test dispatch
boundaries, not real third-party compatibility. DATA-01's real optional evidence
comes separately from the declared overlay, not these malformed duck fixtures.

## DATA-03 — normalized missing values are not invented observations

Implementation: `data._plain_value`, `_to_list`, `_render._x_values`,
`_series_masks`, `_stat.usable_rows`.

- `tests/test_review_missing_data.py::test_missing_categorical_x_never_creates_a_none_category` (8)
- `tests/test_review_missing_data.py::test_literal_none_label_is_distinct_from_missing_x_across_shared_axes_and_twins`
- `tests/test_review_missing_data.py::test_adapter_values_and_layer_missing_cohorts_agree` (9 passed,5 optional skipped)
- `tests/test_review_missing_data.py::test_pandas_nat_x_is_missing_instead_of_a_literal_tick`

For six-row A/B data, source y=None stays in the spec; raw lines retain NaN gaps,
scatter masks corresponding pairs, and grouped lineplot(errorbar=None) estimates
use complete rows without shifting identities. Explicit line/scatter x tests keep
missing x as a gap/masked row, never a fabricated `"None"` tick; a literal string
`"None"` stays a category across shared axes/twins. Pandas NaT becomes None and
ISO dates remain categorical labels, not a new continuous date-axis contract.

The initial19 passed/5 skipped receipt proves only its installed paths. The
later optional overlay actually passes all24 cases, including the five formerly
skipped formats. Neither is every missing scalar/context, and source nonmutation
does not imply sandboxing user-provided Python methods.

## DATA-04 — preserve declared group identity, not caption inference

Implementation: `_render._unique_stable`, `_series_masks` with object dtype;
contract [COMPATIBILITY.md](COMPATIBILITY.md).

- `tests/test_review_group_identity.py::test_default_raw_group_identity_does_not_depend_on_array_string_inference` (4)
- `tests/test_review_group_identity.py::test_raw_mixed_string_and_number_groups_keep_their_original_observations` (line/scatter2)

Default raw groups use original Python equality and first-seen order. String
`"1"` differs from numeric1; numeric1/1.0/True merge. Null is a legacy raw group;
empty labels may be unlabeled. Captions remain `str(key)`, so distinct string and
numeric IDs may both display `"1"` without merging their observations. Caller
normalization can disambiguate labels; this unit does not rewrite group values.

Four separate synthetic scatter probes record exact row IDs/group values/caption/
RGBA and emitted legend labels, assert distinct series colours and unchanged
source, and close all figures. They add no pytest cases. Explicit ordered raw
bool/numeric keys and typed semantic/statistical group rules differ by context;
this selection proves legacy raw paths, not every grouping rule in all families.

## DATA-06 — supported values, not silent unsupported coercion

Implementation: `data._plain_value`, `_to_list`, `to_columns`;
`io._validate_json_value`, `to_json`.

Current nodes in [test_review_scalar_boundaries.py](../tests/test_review_scalar_boundaries.py):

- `test_supported_numpy_scalars_cross_json_with_correct_builtin_values` (45)
- `test_unsupported_scalars_remain_objects_until_explicit_json_rejection` (21)
- `test_nonreflexive_custom_object_is_not_treated_as_missing_or_stringified`
- `test_fresh_same_type_item_result_does_not_recurse_forever`
- `test_item_conversion_cycle_is_not_followed_through_unsupported_classes`
- `test_item_protocol_returning_a_plain_supported_value_stays_supported`
- `test_pandas_known_missing_scalars_remain_null`

All71 ran. Mapping/record/object-array inputs preserve exact supported int/float/
bool/Unicode values or recognized NumPy/Pandas missing→None. Finite unsupported
Decimal/longdouble/complex objects retain identity until strict JSON rejects them
with a type-specific error; Decimal NaN is not a generic missing sentinel.
Unknown self-inequality/stringification is not invoked to guess missing values;
unsupported same-type/cyclic item conversion is not followed recursively. A
supported plain huge-int item result remains valid. `item()` may still execute
caller code; these conversion bounds are not a Python-method security sandbox.
Builtin Infinity/strict JSON behavior is separately mapped under JSON-02, not a
new implicit null conversion. This is not every dtype/dependency object taxonomy.

## DATA-07 — parameters and caller-owned resources

Implementation: `data.to_columns` query/finally and borrowed cursor paths,
`_cursor_to_columns`, `_column_names`, `_row_values`.

All10 nodes in [test_review_sql_ownership.py](../tests/test_review_sql_ownership.py)
ran (expanded parameter names in the artifact):

- `test_connection_query_closes_only_its_own_cursor_even_on_failure` (5)
- `test_minimal_connection_cursor_without_close_keeps_duck_protocol_support`
- `test_owned_cursor_close_failure_is_not_silently_swallowed` (2)
- `test_borrowed_cursor_is_not_closed_and_remains_reusable`
- `test_sqlite_named_values_are_bound_without_commit_or_connection_close`

Connection+query creates one owned cursor, forwards query/params identity and
closes it once on success/execute/fetch/shape/duplicate failure. A minimal supported
cursor without close stays valid. Close failure propagates with the earlier execute
exception as context, not silently swallowed. Borrowed executed SQLite cursor
remains reusable; caller connection and transaction remain open with no commit or
rollback. Named quote/injection-looking strings and nulls are bound through DB-API
params, not interpolated. Synthetic lifecycle probes plus in-memory SQLite are not
external DB-driver/network coverage. No ownership policy was changed by mapping.

## DATA-05 — supported precision, not implicit date-axis conversion

Implementation: `data._plain_value`, `_to_list`, `to_columns` dtype-preserving
scalar/column/2D row paths. Initial tests in
[test_review_temporal_precision.py](../tests/test_review_temporal_precision.py)
record51 passed and7 real optional skips; the later declared overlay passes all58. NumPy ns/ps/fs/as in8 shapes preserve
exact ISO text/NaT→None and source arrays; coarse D/s/ms/us formats stay stable.
Plain2D protocol stays valid while ambiguous2D datetime columns reject rather
than collapse cells. Numeric int epoch remains numeric without a datetime dtype.
Two child processes vary TZ(UTC/Honolulu) with LC_ALL=C; pandas ns offsets in four
zones remain exact. ISO date strings do not silently become numeric lineplot x.

A Polars-shaped lossy formatter mock proves rejection-before-values but is not
actual library compatibility. The new overlay actually executes real Polars ns in
three zones plus DST transition and Arrow ns in three zones: all7 pass separately
from their earlier skipped receipts. The stated1970 near-epoch high-resolution/
2026 offsets and two-TZ/C locale checks are still not all datetime64 ranges,
historical tzdata/locales, all library versions or continuous native-date axes.

## DATA-08 — empty/singular means different things per layer

Implementation: `validate._check_statistical_layer`, `_estimate.summarize`,
`_lineplot.draw_lineplot`, `data.to_columns`.

Current nodes in [test_review_data_edges.py](../tests/test_review_data_edges.py):

- `test_named_empty_raw_data_is_a_valid_empty_figure` (line/scatter2)
- `test_statistical_layers_reject_no_usable_observations` (four kinds×empty/all-missing8)
- `test_singleton_estimate_stays_visible_without_a_fabricated_interval` (bar/point2)

Additional current nodes:
`tests/test_lineplot.py::test_singletons_break_bands_but_do_not_invent_or_remove_point_estimates`;
`tests/test_box_violin.py::test_constant_and_singleton_cells_are_real_degenerate_distributions` (4).
Raw named empty figures have no artists and survive JSON. Undefined empty/all-null
statistics reject without rewriting source. Singleton estimates3 remain while
intervals omit with warnings; lineplot keeps the middle estimate and breaks its
SD bands. Box/violin singleton/constant vertices are finite and exactly y4.
These17 pass assertions do not impose one empty/singular policy on all density,
Swarm/log/weighted/facet/projection combinations.

## DATA-09 — preserve raw paths, aggregate only when declared

Implementation: `_lineplot.draw_lineplot`, `_stat.usable_rows`,
`_estimate.summarize`, `_render._series_masks`.

- `tests/test_review_data_edges.py::test_raw_paths_keep_duplicates_but_lineplot_explicitly_aggregates` (sort False/True2)
- `tests/test_lineplot.py::test_first_observed_x_order_is_per_hue_and_bands_reject_self_crossing`
- `tests/test_raw_group_order.py::test_raw_line_keeps_duplicate_x_original_path_order_and_same_styles_in_each_cell`
- `tests/test_raw_group_order.py::test_ordered_raw_line_preserves_coordinate_gaps_instead_of_joining_across_them`
- `tests/test_raw_group_order.py::test_raw_bar_preserves_supplied_values_errors_and_sparse_dodge_hatch_slots`

Raw x[2,1,2,0]/y[4,1,5,0] remains that path. Statistical duplicate x2 explicitly
becomes mean4.5, sort=False preserves first-observed[2,1,0], sort=True yields
[0,1,2]. Per-hue first order remains separate; nonmonotonic SD bands reject while
bars remain valid. Ordered facets keep raw duplicate paths/style slots/NaN gaps;
raw bars retain supplied heights/errors/dodge/hatches. Six current nodes check
these contexts, not universal sorting/aggregation or all cross-family guides.

## Optional execution update — environment, not a production change

Existing `tests/test_review_missing_data.py`, `tests/test_review_temporal_precision.py`
and `tests/test_review_table_formats.py` ran together in an ephemeral uv overlay:
**95 passed,0 skipped/failed**. Actual versions: PyArrow26.0.0, Polars2.0.0,
NumPy2.5.2, pandas3.0.5, Matplotlib3.11.1, pytest9.1.1. The executed `--with` inputs
were unpinned; the reproduction command below pins the recorded optional versions.
Project pyproject/uv.lock/.venv config hashes, base numeric-library versions and
base optional-package absence matched before/after. No source/test/core-dependency/
lock/base-venv/global-Python change or new package install into the main environment.

The new receipt preserves old snapshots and identifies all12 formerly skipped
node IDs as actually executed now. DATA-01/05 move from additional-execution-needed
to existing coverage only for this declared version/fixture scope. This does not
close JSON-09 semantics, certify past/future timezone or library compatibility,
or count95 repeated nodes as95 new cases. No fresh Native/Rust/browser/sandbox/
performance run is implied by these Python table-library tests.

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

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_json_contracts.py \
  --junitxml=<private-results.xml>
cargo test --locked --manifest-path mudplot-editor/Cargo.toml model::tests::
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_full_spec_fields.py::test_every_nullable_field_distinguishes_omitted_null_and_explicit_default \
  tests/test_review_json_policies.py::test_render_token_fixture_schema_python_and_cli_migrate_agree \
  tests/test_review_json_policies.py::test_fresh_cli_empty_render_token_matches_python_png \
  tests/test_review_json_policies.py::test_optional_marker_omission_null_zero_and_explicit_value \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_full_spec_fields.py \
  tests/test_review_json_policies.py::test_known_version_ignores_unknown_dataclass_fields_but_keeps_data_metadata \
  -k 'not every_nullable_field' --junitxml=<private-results.xml>
MUDPLOT_CODEC_PROBE_OUT=<owned-private> cargo test --locked --manifest-path mudplot-editor/Cargo.toml \
  model::tests::full_field_fixture_preserves_types_values_and_array_order -- --exact
cargo test --locked --manifest-path mudplot-editor/Cargo.toml \
  model::tests::capabilities_accept_additive_top_level_and_layer_metadata -- --exact
```

```sh
uv run --no-sync python scripts/check_schema_sync.py
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_render_contracts.py tests/test_review_generated_drift.py \
  tests/test_review_json_policies.py::test_canonical_keys_whitespace_and_unicode_do_not_reorder_or_coerce_data \
  tests/test_review_json_policies.py::test_cli_damage_does_not_replace_output_and_next_migrate_can_recover \
  tests/test_review_json_policies.py::test_bounded_child_json_checks_are_errors_or_lossless_and_can_recover \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_data_contracts.py tests/test_review_sql_ownership.py \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short tests/test_review_missing_data.py \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_group_identity.py tests/test_review_scalar_boundaries.py \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync python -m pytest -q --tb=short \
  tests/test_review_temporal_precision.py tests/test_review_data_edges.py \
  tests/test_lineplot.py::test_first_observed_x_order_is_per_hue_and_bands_reject_self_crossing \
  tests/test_lineplot.py::test_singletons_break_bands_but_do_not_invent_or_remove_point_estimates \
  tests/test_raw_group_order.py::test_raw_line_keeps_duplicate_x_original_path_order_and_same_styles_in_each_cell \
  tests/test_raw_group_order.py::test_ordered_raw_line_preserves_coordinate_gaps_instead_of_joining_across_them \
  tests/test_raw_group_order.py::test_raw_bar_preserves_supplied_values_errors_and_sparse_dodge_hatch_slots \
  tests/test_box_violin.py::test_constant_and_singleton_cells_are_real_degenerate_distributions \
  --junitxml=<private-results.xml>
```

```sh
uv run --no-sync --with pyarrow==26.0.0 --with polars==2.0.0 python -m pytest -q --tb=short \
  tests/test_review_missing_data.py tests/test_review_temporal_precision.py \
  tests/test_review_table_formats.py --junitxml=<private-results.xml>
```

The public artifacts contain synthetic fixtures/test names and hashes, not raw
logs, secrets or user-local absolute paths. Private raw receipts are not a durable
web download. Recheck symbol/source fingerprints after implementation changes.

The remaining112 IDs still need their own reviewed symbol/node/provenance links
and classification. Do not infer missing coverage
from their omission here or infer completion from a test filename/collection/pass.
