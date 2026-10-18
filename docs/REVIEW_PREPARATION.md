# Review inputs and contract decisions

This is preparation evidence for BASE-06/07, not a release gate or a complete
privacy classifier. The unchanged 150-item checklist is a verification backlog,
not a list of confirmed bugs. BASE-05's complete per-ID coverage mapping remains
separate; no automatic candidate-test ranking is presented as executed coverage.

## Input inventory

| Shared synthetic fixture | Purpose and generation | Consumer |
| --- | --- | --- |
| `tests/fixtures/review_state_paths.json` | Fixed small columns/matrix/actions; no RNG. Cross-path forms are explicit data. | `tests/test_review_editor_paths.py`; editor path checks |
| `tests/fixtures/review_json_boundaries.json` | Literal valid/invalid JSON, numbers, surrogates, versions and reserved names; no RNG. Invalid cases are not valid/renderable examples. | `tests/test_review_json_policies.py`; Rust model tests |
| `tests/fixtures/review_http_boundaries.json` | Fixed local loopback/attacker examples and placeholders `{base}`, `{port}`, `{other_port}`; no real service/account. | `tests/test_review_http_boundaries.py`; Rust HTTP smoke |
| `tests/fixtures/review_full_spec_fields.json` | Deterministic model-field generator, schema-valid codec stress with incompatible options; not a renderability claim. | `tests/test_review_full_spec_fields.py`; typed Rust model |
| `tests/fixtures/review_render_tokens.json` | Fixed representative empty/omitted/automatic marker/style semantics; not all 139 nullable meanings or all visual controls. | `tests/test_review_json_policies.py`; raw editor probes |

Source hashes, sizes, parsed root keys and the exact shared JSON snapshot are in
[the preparation audit](review_evidence/preparation_audit_verification.json).
Earlier randomized history verification uses local `random.Random` seeds
20261016 and24301 in `tests/test_review_history_policies.py`. Performance scripts
state their own fixed row/history workloads; they do not silently substitute real
research data or turn an uncompleted target into a zero measurement.

## Shared and private evidence

- `tests/fixtures/` contains minimal synthetic **inputs**, including intentional
  malformed inputs. They are not logs or successful-render certificates.
- `docs/review_evidence/` contains bounded **results**: source/environment
  fingerprints, commands/exit codes, metrics, scoped limitations and raw-log
  hashes. Historical source hashes are historical, not current-suite proof.
- Owned local Temp directories retain raw stdout/stderr, runtime files, images
  and full diagnostic paths. Do not copy a raw environment dump, credentials,
  unpublished research rows or private home paths into shared JSON.
- Publish module-relative source paths and local artifact placeholders rather
  than profile paths. Keep actual input-specific values only when synthetic and
  necessary to reproduce the boundary; do not echo submitted data in warnings.
  Same-client JSON drafts remain intentional editing data, not public logs.
- The static JSON audit parses files and checks profile-path/private-key/token
  patterns without printing candidate values. No findings is **not** proof that
  arbitrary text cannot contain a secret. Inspect new inputs and findings before
  publication; do not auto-redact and call altered raw logs original evidence.
- Evidence lineage uses hashes, not invented approval. Binary font files and
  private datasets are excluded. Purposefully tracked synthetic PNG comparison
  sheets have their source settings/hashes and are not cross-environment goldens.

## Contract difference decisions

| Claim or proposal in tension | Actual contract / retained decision | Evidence and rationale |
| --- | --- | --- |
| Mutable `FigureSpec` interpreted as a requirement for persistent immutable nodes | Mutable dataclasses remain; public snapshots and reducer inputs are isolated. No new persistent data structure. | `docs/COMPATIBILITY.md`, `tests/test_review_state_contracts.py`; preserve alias safety without unasked architecture. |
| One atomic rule for every batch API | Functional apply returns no partial result; Store batches can retain committed prefixes; editor candidate effects are transactional. | Compatibility state section and state-contract tests; checklist proposals do not override distinct existing boundaries. |
| Success saving a file means the returned Figure is closed | API render/save return open caller-owned Figures; CLI/editor close their owned effects. | Output ownership docs, `tests/test_review_output_lifecycle.py`; no silent caller resource-ownership change. |
| `tight` cropping silently changes publication size | Default keeps configured canvas; explicit `tight=True` opts into cropping. | `tests/test_review_export_determinism.py`; TeX/graphics point units and raster rounding remain explicit. |
| Later font setters always beat an active journal style | Physical size follows the last size action; registered journal rc keys retain priority; clear journal style for explicit theme font fields. | `tests/test_review_preset_sizes.py`; correct the overbroad API doc instead of changing calibration or adding override metadata. |
| Palette report nominal LCH equals exported colour quality | Float methods measure mapped float RGB; report measures final 8-bit HEX with explicit normal/CVD/model/severity conditions. | `tests/test_review_palette_reports.py`; correct observed false safe flags without changing generated colours or thresholds. |
| Hatch/marker encoding guarantees arbitrary category counts or print readability | Cycles are finite and physical output needs inspection; transparent bands can blend. | `tests/test_review_redundant_encoding.py`, colour/grey plate and generated reference; bounded measurement, not certification. |
| PGF is a universal plain-text sanitizer or atomic single file | Explicit PGF uses trusted TeX grammar and may create non-transactional sidecars; references have separate strict validation. | String/PGF bundle tests; no untrusted-TeX sandbox or new multi-file transaction promise. |
| Source-tree tools must appear in the engine wheel | Dashboard and Rust editor are separate matching-source tools; core wheel excludes UI packages intentionally. | Dashboard/editor READMEs and `scripts/check_wheel.py`; preserve one-way dependency and distribution boundary. |
| Every Python UI capability needs native Rust controls | Typed JSON preservation and documented raw-action subset are checked independently from visual-control parity. | Compatibility/editor docs; JSON-09's remaining nullable/native meanings are not declared complete here. |
| Current verification counts mean release approval/version change | Keep versions, dependency floors and locks; release/tag/distribution approval remains separate. | Review tracker and release checks; no inferred authority from test or machine evidence. |

No new runtime compatibility change or approval is introduced by this table.
Known source/doc differences are recorded with the selected preserved or corrected
contract; future behavioral compatibility changes need separate explicit review.
