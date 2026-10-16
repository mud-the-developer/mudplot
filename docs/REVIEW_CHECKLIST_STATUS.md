# 2026-10-16 체크리스트 반영·증거 대장

원문: [상세 체크리스트](../mudplot_review_checklist_detailed_2026-10-16.md)

작업 스냅샷: [한글](WORK_SNAPSHOT.ko.md) · [English](WORK_SNAPSHOT.md).
임시 경로가 사라져도 [경로 제거 검증 요약](review_evidence/verification_receipts.json)의
실행 범위·결과·환경/소스 지문·원본 log hash를 확인할 수 있습니다. Raw log 복제나
새 전체 검증 결과를 뜻하지 않습니다.

**150개 검증 항목이며 결함 개수/제품 안정성 확률이 아닙니다.** 원문 체크박스는 보존하고 이 대장에서 실행 상태를 관리합니다.

- 기준 HEAD: `c4f40ab22660129ad4e35c63d1f66feb62e2dd99` (원문과 일치).
- 적용 범위: 기존 로컬 변경/새 파일 포함 작업 트리. clean main 재현으로 주장하지 않습니다.
- 날짜/환경: 실제 environment.json 참조; Windows 11, Python3.12.15, NumPy2.5.2, Matplotlib3.11.1.
- 1차 명령: `uv run --no-sync python -m pytest -q tests/test_review_state_contracts.py tests/test_review_output_contracts.py tests/test_reducer.py tests/test_spec_roundtrip.py tests/test_json_schema_compat.py tests/test_schema_export.py tests/test_no_deps.py tests/test_stabilization.py tests/test_cli_apply.py tests/test_cli_migrate.py --junitxml=<evidence>/contracts.xml`.
- 실제 결과: **127 passed, 2 Windows-only skips, exit 0**, 25.33s. skip: symlink privilege/POSIX mode bits.
- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-2026-10-16-88esbi7s` (임시 경로; 보관이 필요하면 별도 복사).
- 파일: environment.json(버전/원문 SHA256/변경 파일 SHA256), git-status.txt, tracked-diff.patch, contracts.log, contracts.xml, receipt.json.
- 담당: coding assistant; 관련 PR/tag/배포 없음. 기존 변경 전체를 이번 작업으로 귀속하지 않습니다.

## 5차 — 같은 corpus로 Python/Rust JSON 경계 대조

- 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-cross-json-65s92n46`.
  대상 **597 통과, Windows 조건 2 skip**; Rust all-targets **lib13+main1 통과,
  의도한 helper1 ignored**; 실제 HTTP/browser smoke, Clippy -D warnings/fmt,
  Ruff200파일/format/Pyright/schema sync/clean sdist→wheel 검사 exit0입니다.
  현재 compiler1.99이지 MSRV1.88 검증은 아닙니다. 환경/체크리스트·소스 SHA/
  명령·exit/JUnit/log와 실제 수정 전 실패 요약을 보관했습니다.
- 공유 fixture `tests/fixtures/review_json_boundaries.json`: 잘못된 spec19개,
  action11개, 정상 spec2개. API3경로/CLI4경로/Python editor/HTTP와 Rust JSON/raw
  action/open에서 거부·기존 state/history/preview/output 보존을 대조합니다.
- fixture 자체에도 검사를 넣었습니다. version 오류가 아닌 음성 입력에는 정상
  version을 명시하고, 두 정상 입력의 suptitle을 다르게 하여 stale state가 성공으로
  보이지 않게 했습니다. 이전 약한 corpus probe 결과는 완료 증거로 쓰지 않습니다.

| ID | 상태 | 실제 확인한 경계 |
|---|---|---|
| JSON-02 | PASS | NaN/±Infinity/±1e400 raw 입력과 strict 저장 거부; mapping/records/rows/NumPy/nullable pandas 각각 missing→null/±Infinity를15경우로 구분 |
| JSON-06 | PASS | root/column/array object 예약 key, escaped key, lone high/low/key surrogate, 비문자열 key 거부; 정상 한글/기호/emoji·valid pair·일반 문자열 reserved spelling 유지 |
| JSON-07 | PASS | explicit0.1과 version 생략의 동일 기본값; unknown future/unimplemented old/빈 문자열/숫자/bool/null/array 거부, CLI·editor 실패 시 기존 상태 보존 |

### 실제 재현 후 수정한 Rust 차이

- **FIND-004 (JSON-06 production):** serde arbitrary_precision은 실제 사용자 object
  `{"$serde_json::private::Number":"1"}`를 숫자로 바꿀 수 있었습니다. 기존 visitor는
  내부 number-map과 실제 key를 구별하지 못했습니다. unit exit101과 정상 version의
  nested HTTP open에서 spec 변경을 먼저 재현했습니다. 공통 from_json_strict에 원본
  string token 검사를 추가했습니다. serde string deserializer로 escape를 해석하고
  뒤따르는 colon으로 실제 property key만 검사하므로 큰 정수와 일반 문자열은 유지합니다.
  새 별도 JSON parser/의존성/숫자 강제 float 변환은 넣지 않았습니다.
- **FIND-005 (JSON-07 production):** Python은 version 생략을 현재 기본값으로 읽지만
  Rust envelope는 missing field version으로 거부했습니다(unit exit101/HTTP mismatch).
  Rust의 serde default를 내장 default_spec.json의 version에 연결했습니다. 별도 version
  literal이나 null/unknown 허용은 추가하지 않았습니다. 서로 다른 정상 state를 사용해
  실제 commit을 확인했으며 기존 state와 같은 값으로 거부가 가려지지 않게 했습니다.

원문 체크리스트/공개 version/tag/deploy는 유지합니다. 이 범위의 PASS를 모든 필드/
OS/성능/지원 MSRV/릴리스 gate로 확대하지 않습니다. DATA-02와 나머지 P0는 진행 중입니다.

## 4차 — JSON 경계·어댑터 데이터 손실 방지

- 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-json-ijbqg6n6`.
  현재 로컬 작업 트리/Agg의 **404 통과, Windows 조건 2 skip**, 최소 Python3.10/
  NumPy1.23 adapter **25 통과, 2142 deselected, 경고13**입니다. Ruff199파일/format/
  Pyright/schema sync도 exit0이며 manifest/JUnit/명령/환경 override/log를 보관했습니다.
- **FIND-003 (DATA-02 P0 production):** positional ragged row의 추가 값이 조용히
  잘리거나 짧은 행이 IndexError를 냈고, DB cursor description과 row 길이 불일치도
  zip에서 조용히 잘렸습니다. 수정 전 7 fail/1 pass를 확보했습니다. data.py의
  `_rows_to_columns`/`_cursor_to_columns`에서 pivot 전에 너비를 검사하고 row index/
  실제 수/expected 수가 있는 ValueError를 반환합니다. 정상 값/순서/빈 열 입력은 유지합니다.
- 새 `test_review_data_contracts.py`8개와 기존 adapter 검사를 실행했습니다. DATA-02는
  전체 형식·필수 열/중복 열 매핑을 모두 닫기 전이므로 RUNNING입니다.
- JSON-05는 **PASS**입니다. 10^1000을 x/y/matrix/style/size에 넣어 구조 보존과
  PNG/PDF/SVG CLI 실패를 분리한15개, editor 실패 후 state/history/preview 보존과
  재사용1개를 확인했습니다. 임의 정밀도 plotting 지원으로 바꾸지 않습니다.
- JSON-02 raw NaN/±Infinity/±1e400의 CLI4경로20개와 mapping/record/row/NumPy/
  nullable pandas 결측→null5개를 보강했습니다. Infinity는 유효값으로 coercion하지
  않고 strict JSON 저장에서 거부합니다. 전체 언어/진입점 표가 남아 RUNNING입니다.
- 한 초기 회귀 실행은 MPLBACKEND 미설정으로 Tk/Tcl 환경 오류2개가 났습니다.
  이를 제품 결함이나 통과로 세지 않았고 Agg로 재실행59개 통과 후 기록한 본 검증을
  수행했습니다. Native GUI/Tk 지원을 이번에 고친 것은 아닙니다.

## 후속 JSON·출력 검증 — 2/3차

- 2차 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-json-output-mx5owq8x`.
  Python **338 통과, Windows 조건 2 skip**, Rust lib **11 통과/보조 helper 1 ignored**,
  실제 Rust HTTP/browser smoke·schema sync·Ruff·Pyright·Rust fmt exit0입니다.
- 3차 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-windows-output-gdp35khy`.
  JSON/출력/에디터 대상 **354 통과, Windows 조건 2 skip**, Ruff/format/Pyright/
  schema sync/clean sdist→wheel 검사 exit0입니다. 명령/로그/JUnit/환경과 source
  hash는 각 `environment.json`, `receipts.json`, `contracts.xml`에 있습니다.
- 범위: 현재 로컬 작업 트리, Windows/Python3.12.15. Rust는 설치 compiler1.99.0이며
  MSRV1.88 실행으로 간주하지 않습니다. 원문 SHA256은 각 manifest와 일치합니다.

| ID | 판정/기대 결과 | 실제 증거 |
|---|---|---|
| JSON-03 | PASS: root/nested/array object의 같은/다른 duplicate key 거부, 기존 state/preview/output 유지 | test_review_json_contracts.py의 API/CLI 42+6 cases; Python HTTP open/raw-action; Rust strict unit+JSON/raw/open HTTP smoke |
| JSON-04 | PASS: 2^53/signed·unsigned64/큰 양·음 integer 구조 보존; 정밀 렌더 보장은 아님 | Python known data field boundary; model.rs signed-boundary unit; 실제 bridge open/spec/action 왕복 unused_integer_boundaries |
| OUT-03 | PASS: JSON/PNG/PDF/SVG partial-write/flush-close/fsync/replace 실패 시 기존 bytes와 staging/Figure 정리 | test_review_output_contracts.py::test_out_03_atomic_failure_retains_previous_bytes_and_cleans_staging 16 cases, 공개 save API에서 fault injection |

OUT-04는 RUNNING입니다. 실제 Win32 delete-sharing lock, 읽기 전용 대상, 없는 상위
경로·디렉터리 대상까지 확인했으나 디스크 공간·전체 권한·다른 OS를 완료 처리하지
않습니다. JSON-06/07도 추가 Python/Rust 사례는 통과했지만 전체 필드/진입점 표를
완료하지 않아 RUNNING을 유지합니다. 전체 gate 승인이나 미측정 성능 주장은 없습니다.

### 재현한 문제와 최소 수정

- **FIND-001 (연결 검사):** Rust generated capability 테스트가 registry를36으로 고정해
  실제37에서 exit101. model.rs 기대 수를37로 갱신하고 clustermap의 matrix 필수 필드와
  cluster/heatmap/colorbar 지원을 별도 assert했습니다. 실패 요약과 수정 후 lib 로그는
  2차 증거에 있습니다. 제품 전체 JSON 손상으로 과장하지 않습니다.
- **FIND-002 (OUT-04 production):** Windows 읽기 전용 대상의 mode를 staging에 복사하여
  replace 실패 뒤 read-only .tmp 삭제가 실패함을 네 형식에서 재현했습니다(pytest-508,
  수정 전 4 fail). io.py::_atomic_destination에서 POSIX mode 복사만 non-Windows로
  제한했습니다. 원본 읽기 전용 속성/bytes를 바꾸거나 임의 파일을 chmod하지 않습니다.
  실제 잠금4·읽기전용4·잘못된 경로8과 원자성16 검사 통과. POSIX mode/symlink 두 사례는
  Windows에서 skip이므로 다른 OS 검증 완료로 보고하지 않습니다.

## 1차 확인된 계약과 새 회귀 검사

| ID | 판정/기대 결과 | 구현 심볼 | 실제 증거 |
|---|---|---|---|
| BASE-01 | PASS: HEAD/tag/dirty 범위와 파일 지문 확보 | git working tree | environment.json / git-status.txt / tracked-diff.patch |
| STATE-04 | PASS: mp.apply 실패는 입력 state/actions 보존, 부분 반환 없음 | mudplot/api.py::apply; reducer.py::reduce_all | test_review_state_contracts.py::test_state_04_* (2개) / contracts.xml |
| STATE-05 | PASS: Plot.apply/Store.dispatch_all은 완료 prefix 유지, 후속 사용/redo 의미 유지 | Plot.apply; Store.dispatch_all | test_review_state_contracts.py::test_state_05_* (2개) / contracts.xml |
| STATE-06 | PASS: listener 예외 전파하되 이미 commit된 state/history 유지 | Store._dispatch; subscribe | test_review_state_contracts.py::test_state_06_listener_failure_occurs_after_commit_and_is_not_rollback / contracts.xml |

1차 당시 OUT-03/04는 RUNNING이었습니다. 당시12개 검사는 partial-write/fsync/replace만 다뤘으며 위 후속 증거로 확대했습니다. 과거 결과를 나중 범위의 통과로 소급하지 않습니다.

새 코드: tests/test_review_state_contracts.py(5), tests/test_review_output_contracts.py(12). 기존 테스트가 다루지 않던 실패 단계/형식만 추가했고 production semantics는 변경하지 않았습니다.

## 전체 ID 추적

**아래 구현/테스트는 검토 후보입니다. 해당 파일 존재/수집/이전 통과만으로 PASS가 아닙니다.** 후보가 넓은 항목은 ID별 심볼/fixture/실행 결과를 좁혀야 합니다.

| ID | 우선순위 | 상태 | 확인 항목 | 구현 후보 | 테스트/증거 후보 |
|---|---|---|---|---|---|
| BASE-01 | P0 | PASS | 커밋·태그·작업 트리의 기준선 기록 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-02 | P0 | RUNNING | 지원 범위와 비목표 확인 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-03 | P0 | RUNNING | 검증 환경 명세 수집 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-04 | P0 | RUNNING | 변경 전 테스트 기준선 확보 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-05 | P1 | RUNNING | 기존 테스트와 체크리스트 매핑 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-06 | P1 | RUNNING | fixture와 증거 데이터 분리 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| BASE-07 | P1 | RUNNING | 문서 계약 충돌 처리 | docs/COMPATIBILITY.md; CONTRIBUTING.md; SECURITY.md | environment.json; git-status.txt; tracked-diff.patch |
| STATE-01 | P0 | OPEN | reducer의 입력 비변경 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-02 | P0 | OPEN | 공개 스냅샷의 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-03 | P0 | OPEN | 상태 변경 경로의 일관성 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-04 | P0 | PASS | mp.apply의 실패 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-05 | P0 | PASS | 비트랜잭션 배치 API의 계약 보존 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-06 | P0 | PASS | listener 예외의 commit 시점 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-07 | P1 | OPEN | 결정성과 암묵적 전역 상태 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-08 | P1 | OPEN | 잘못된 참조와 경계 인덱스 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-09 | P1 | OPEN | 검증과 부수효과 경계 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| HIST-01 | P0 | OPEN | 기본 undo/redo와 경계 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-02 | P0 | OPEN | undo 이후 분기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-03 | P0 | OPEN | 편집기 action/import/render 실패 원자성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-04 | P1 | OPEN | reset과 open의 이력 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-05 | P1 | OPEN | no-op action의 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-06 | P1 | OPEN | 긴 이력의 재생 정확성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-07 | P2 | OPEN | 연속 드래그 action 합치기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-08 | P2 | OPEN | 체크포인트와 이력 제한 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| JSON-01 | P0 | RUNNING | 공식 지원 필드의 손실 없는 왕복 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-02 | P0 | PASS | 비유한 숫자의 경계 분리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-03 | P0 | PASS | 재귀 중복 키 거부 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-04 | P0 | PASS | 큰 정수의 구조적 보존 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-05 | P0 | PASS | float 범위 밖 좌표의 실패 처리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-06 | P0 | PASS | 예약 키·문자열 키·Unicode 유효성 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-07 | P0 | PASS | 알 수 없는 spec 버전 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-08 | P1 | OPEN | 알 수 없는 필드의 명시된 처리 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-09 | P1 | OPEN | 생략·null·자동값·기본값 구분 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-10 | P1 | OPEN | canonical serialization과 해시 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-11 | P1 | RUNNING | 스키마·capabilities·문서 동기화 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| JSON-12 | P1 | OPEN | JSON 크기·깊이·손상 입력 복구 | mudplot/io.py; spec.py; schema.py; mudplot-editor/src/model.rs | test_spec_roundtrip.py; test_json_schema_compat.py; test_schema_export.py |
| DATA-01 | P0 | OPEN | 입력 형식 간 동일 데이터의 동등성 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-02 | P0 | RUNNING | 열 길이·필수 열·중복 열 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-03 | P0 | OPEN | 결측값의 정규화와 렌더링 분리 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-04 | P1 | OPEN | 혼합 그룹 식별자 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-05 | P1 | OPEN | 날짜·시간·timezone | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-06 | P1 | OPEN | NumPy scalar와 지원하지 않는 객체 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-07 | P1 | OPEN | SQL 파라미터와 연결 소유권 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-08 | P1 | OPEN | 빈 데이터·상수·단일 관측값 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-09 | P1 | OPEN | 행 순서·정렬·중복 x의 정책 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| PLOT-01 | P0 | OPEN | 전체 등록 레이어의 실행·계약 커버리지 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-02 | P0 | OPEN | 범주형 x의 레이어 간 정렬 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-03 | P0 | OPEN | 그룹·패널 간 스타일 일관성 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-04 | P0 | OPEN | 보조 y축 소속과 스케일 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-05 | P1 | OPEN | shared axes와 독립 설정 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-06 | P0 | OPEN | heatmap·surface 행렬 방향 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-07 | P1 | OPEN | quiver·3D·polar의 좌표 의미 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-08 | P1 | OPEN | 연속 색상과 colorbar 의미 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-09 | P1 | OPEN | bar·stack·band·errorbar 정렬 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-10 | P1 | OPEN | log scale과 유효 영역 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-11 | P1 | OPEN | annotation·legend의 좌표계 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| PLOT-12 | P1 | OPEN | 겹침·z-order·alpha와 클리핑 | mudplot/_render.py; capabilities.py; validate.py | test_new_layers.py; test_layout.py; test_capabilities_consistency.py |
| STAT-01 | P0 | OPEN | regplot의 적합값 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-02 | P0 | OPEN | confidence band의 의미 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-03 | P1 | OPEN | 회귀의 퇴화 입력 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-04 | P1 | OPEN | histogram bin·density·weights | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-05 | P1 | OPEN | KDE bandwidth·적분·퇴화 입력 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-06 | P1 | OPEN | box·violin의 집계 정의 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-07 | P1 | OPEN | jitter와 난수 재현성 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| STAT-08 | P1 | OPEN | 통계 전처리의 관측 대응 | mudplot/_estimate.py; _stat.py; _histogram.py; _kde.py | test_statistics.py; test_weighted_statistics.py; test_histogram_statistics.py; test_kde_options.py |
| COLOR-01 | P0 | OPEN | 색 공간 변환의 기준값 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-02 | P0 | OPEN | CIEDE2000의 독립 reference | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-03 | P1 | OPEN | gamut 처리 이후 품질 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-04 | P1 | OPEN | CVD 시뮬레이션 조건 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-05 | P1 | OPEN | preset 범주 수의 경계 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-06 | P1 | OPEN | 균일 명도와 흑백 구분의 분리 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-07 | P1 | OPEN | 중복 표현의 일관성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-08 | P1 | OPEN | 팔레트 결정성·seed·tie-break | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-09 | P1 | OPEN | 실제 그림 크기의 가독성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| COLOR-10 | P2 | OPEN | 품질 report와 대외 문구 정합성 | mudplot/color/; theme.py | test_convert.py; test_distance_cvd.py; test_palette_presets.py |
| LAY-01 | P0 | OPEN | 최종 파일의 물리 크기 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-02 | P0 | OPEN | tight 옵션의 명시적 차이 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-03 | P1 | OPEN | TeX preset·columns 적용 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-04 | P1 | OPEN | 긴 제목·suptitle·범례 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-05 | P1 | OPEN | 외부 범례·colorbar·멀티패널 조합 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-06 | P1 | OPEN | 배치 불가능 상태의 처리 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-07 | P1 | OPEN | 폰트 부재·fallback·한글 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-08 | P1 | OPEN | 반복 렌더링의 스타일 격리 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| LAY-09 | P1 | OPEN | DPI·벡터 출력과 UI 위치의 일치 | mudplot/_render.py; tex.py; theme.py | test_layout.py; test_journal_profiles.py; test_stabilization.py |
| OUT-01 | P0 | RUNNING | 동일 환경의 반복 출력 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-02 | P1 | OPEN | volatile metadata·ID | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-03 | P0 | PASS | 단일 파일 저장의 원자성 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-04 | P1 | RUNNING | 출력 실패·잠금·권한 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-05 | P1 | RUNNING | Figure 소유권과 누수 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-06 | P1 | OPEN | PGF bundle 한계 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-07 | P1 | OPEN | 참조의 형식별 의미 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-08 | P1 | OPEN | TeX 컴파일로 참조 확인 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-09 | P1 | OPEN | SVG·TeX·HTML 문자열 경계 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| OUT-10 | P2 | OPEN | 출력 provenance 기록 | mudplot/io.py; _render.py; tex.py | test_spec_roundtrip.py; test_stabilization.py; test_references.py; test_review_output_contracts.py |
| EDIT-01 | P0 | OPEN | UI 입력과 공통 action | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-02 | P1 | OPEN | 드래그·키보드 위치 편집 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-03 | P1 | OPEN | htmx 교체 이후 상태·이벤트 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-04 | P1 | OPEN | 지연 응답과 최신 preview | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-05 | P1 | OPEN | 두 탭·동시 agent 요청 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-06 | P1 | OPEN | open·export·실패 후 회복 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-07 | P1 | OPEN | 입력 오류의 위치·설명 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-08 | P1 | OPEN | 키보드 접근과 상태 피드백 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-09 | P1 | OPEN | agent 응답의 기계 판독성 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| RUST-01 | P0 | OPEN | Python CLI 위임의 계약 일치 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-02 | P0 | OPEN | Python 실행 파일 선택과 quoting | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-03 | P1 | OPEN | 실패한 subprocess와 출력 경계 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-04 | P1 | OPEN | 120초 timeout과 자식 정리 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-05 | P1 | OPEN | preview 2000px 제한과 원본 보존 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-06 | P1 | OPEN | Rust history와 캐시의 commit 순서 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-07 | P1 | OPEN | 공유 static 자산·버전 정합성 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| SEC-01 | P0 | OPEN | loopback bind와 Host 검증 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-02 | P0 | OPEN | Origin과 mutation 경계 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-03 | P0 | OPEN | 16 MiB 요청 한도 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-04 | P1 | OPEN | 작은 요청의 과도한 계산 방어 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-05 | P1 | OPEN | CSP·no-store·브라우저 header | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-06 | P1 | OPEN | 파일 경로·임시 파일 경계 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-07 | P1 | OPEN | 외부 참조·입력의 실행 금지 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-08 | P1 | OPEN | 오류 로그·비밀값·의존성 위험 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| PERF-01 | P1 | OPEN | 상태 변경과 렌더링 비용 분리 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-02 | P1 | OPEN | 데이터 크기×이력 길이 matrix | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-03 | P1 | OPEN | deep copy의 실제 프로파일 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-04 | P1 | OPEN | 장시간 세션의 자원 증가 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-05 | P1 | OPEN | Python/Rust end-to-end 비교 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-06 | P1 | OPEN | 동시 render의 격리 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-07 | P2 | OPEN | 작은 최적화부터 평가 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PERF-08 | P2 | OPEN | 대형 데이터 지원 범위의 명문화 | mudplot/store.py; reducer.py; _render.py | workload measurements not run |
| PKG-01 | P0 | OPEN | 깨끗한 wheel의 코어 독립성 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-02 | P1 | OPEN | optional extras의 기능 경계 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-03 | P0 | OPEN | sdist와 wheel 내용·메타데이터 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-04 | P1 | OPEN | 저장소 밖 CLI 실행 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-05 | P0 | OPEN | 최소 지원 버전 검사 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-06 | P1 | RUNNING | Windows 한글·공백·긴 경로 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-07 | P1 | OPEN | GUI 없는 Linux와 OS 차이 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-08 | P1 | OPEN | source-tree 편집기의 실행 안내 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| PKG-09 | P1 | OPEN | lock·빌드 격리·설치 재현 | pyproject.toml; scripts/check_wheel.py; scripts/check_minimum_versions.py | test_no_deps.py; packaging/minimum scripts |
| CI-01 | P0 | RUNNING | 표준 검사 실제 실행 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-02 | P1 | OPEN | 브라우저·TeX skip 가시성 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-03 | P1 | OPEN | 속성 기반 상태 테스트 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-04 | P1 | OPEN | golden image의 역할과 오차 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-05 | P1 | OPEN | 핵심 실패를 잡는 테스트인지 검증 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-06 | P1 | OPEN | CI 지원 환경과 병렬 실행 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-07 | P0 | OPEN | 릴리스 버전·태그·산출물 동일성 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-08 | P1 | OPEN | 체크섬·OIDC provenance 검증 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| CI-09 | P1 | OPEN | 공급망 권한·실패 정책 | .github/workflows/; CONTRIBUTING.md; scripts/check_release_version.py | test_release_preflight.py; workflow/artifact evidence not collected |
| DOC-01 | P1 | OPEN | 한글·영문·생성 문서 정합성 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-02 | P1 | OPEN | public API와 오류 계약 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-03 | P1 | OPEN | 발견 사항의 증거 수준 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-04 | P1 | OPEN | 릴리스 허용 조건 판정 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-05 | P2 | OPEN | 근거 기반 재평가 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |
| DOC-06 | P1 | OPEN | 개발자·Codex 인계 결과 | README.md; docs/COMPATIBILITY.md; docs/V1_1_PLAN.md | test_schema_export.py; scripts/check_schema_sync.py; manual claim review |

## 판정 범위와 다음 순서

- 현재 상태: PASS 11, RUNNING 14, OPEN 125, FAIL 0, BLOCKED 0, N/A 0, DEFERRED 0. 이는 완료율/안정성 확률이 아닙니다.
- 확인된 production 결함: FIND-002/003/004/005를 재현 후 수정했습니다. FIND-001은 별도 연결 검사 결함입니다. 미검증 영역의 결함 부재를 뜻하지 않습니다.
- 다음: JSON/출력 ID의 기존 fixture 범위를 대조하고, editor/보안/Rust/패키징의 P0 경계를 증거 파일과 연결합니다. 기준을 완전히 충족한 ID만 닫습니다.
- 원문 G0~G8 gate는 전체 PASS가 아닙니다. 전체 suite·전체 최소 환경·Rust MSRV·headless Linux·TeX/성능·dependency 보안 감사·release provenance는 이번 1차 검토에서 미실행입니다.
- 비교 SHA의 clean main 실행은 별도 작업 트리/환경이 필요합니다. 현재 dirty tree를 reset/clean/revert하지 않습니다.
- 공개 계약 변경, snapshot/zero-copy 구조 변경, 원격 인증, PGF 다중 파일 원자성, 새 성능 임계값/전면 benchmark framework는 도입하지 않았습니다.
