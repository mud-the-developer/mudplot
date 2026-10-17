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

## 14차 — 문서 이력·no-op·long replay와 원격 Rust 확인

- 기반781f3f5 위에서 기존 정책을 검증했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-history-final-5yqwup_o`,
  [경로 제거 이력/원격 job 요약](review_evidence/history_policy_verification.json)도 보존합니다.
- Python open/reset은 새 이력, Rust open/reset은 undo 가능한 snapshot이며 reset은 시작
  기본 문서로 돌아갑니다. A의 미저장 편집/future가 있는 상태에서 B를 열고 export·undo/
  redo·reset을 확인했습니다. Python 실제 파일 picker/다운로드에서 source A/B bytes는
  불변이고 현재 B/reset spec을 다운로드했습니다. 서버에 bound filename/별도 dirty-bit 기능은
  없어 새로 구현하지 않고 정책을 명시했습니다. HIST-04는 **PASS**입니다.
- Equal-value action도 event/snapshot을 기록하고 old redo를 지우며 Store listener와
  Python/Rust 이력 의미가 유지됐습니다. HIST-05는 **PASS**입니다. Seed20261016/24301의
  각768유효 action과128undo/128redo checkpoint에서 spec/cursor/hash가 정확히 일치하여
  HIST-06을 **PASS** 처리합니다. 무한 이력/성능 상한 또는 coalescing 최적화 주장은 아닙니다.
- **FIND-017 (Rust UI):** 서버 state는 맞아도 빠른 title/theme/history 요청의 outerHTML
  swap target이 분리되어 official htmx의 null querySelector pageerror가 발생했습니다.
  Root의 hx-disabled-elt로 요청 중 현재 control들을 비활성화해 중복 swap을 방지했습니다.
  Vendor/서버 정책은 바꾸지 않고 실제 reset/undo/redo click·CSP/pageerror 없음도 확인했습니다.
- 처음 native form-selector 가정은 실제 standalone hx-post button과 달라 QA만 고쳤습니다.
  첫 묶음은 history199통과 후 browser1fail/31pass에서 멈췄습니다. 파일 선택 뒤 Open
  section 재접힘을 재확인하는 테스트로 보강하고 최종 재실행했습니다. 이전 실패를 완료로 세지 않았습니다.
- 최종 **이력 대상199통과**, 전체 Python browser **32통과**, 실제 Rust HTTP/browser의
  문서/no-op/상태/PNG 시나리오 통과. 최소 **이력-only20통과/2506deselected/경고13**이며
  더 넓은 이전354case 반복이 아닙니다. Ruff213파일/format·Pyright·계약·clean sdist→wheel을
  포함한9기록 명령이 exit0입니다. 새 전체 application regression/native-unit count는 없습니다.
- 781f3f5의 CI run39050108296에서 Linux job117447100073와 Windows job117447100196은
  MSRV1.88·native tests·bridge smoke·interpreter 경로·본문/RSS 단계 모두 성공했습니다.
  그 근거로 RUST-02를 **PASS** 처리합니다. Python3.12도 성공했지만 Python3.10이 취소되어
  workflow 전체 결론은 cancelled입니다. 전체 CI/OS/릴리스 승인으로 확대하지 않습니다.
- 원문 체크리스트/의존성/lock/버전/tag/배포는 유지합니다. 현재 UI 수정은 별도 로컬 변경이므로
  원격781의 성공을 이 후속 변경의 CI 통과로 소급하지 않습니다.

## 13차 — 미지원 scalar 거부·가려지지 않는 probe 계측

- 기반914a402 위에서 진행했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-scalars-j2l4rnhk`,
  [경로 제거 scalar/계측 요약](review_evidence/scalar_provenance_verification.json)도 보존합니다.
- **FIND-015 (DATA-06):** Decimal NaN/일부 custom 객체의 self-inequality가 null로
  바뀌고 sNaN은 InvalidOperation, longdouble/새 same-type·순환 item은 RecursionError로
  끝남을 수정 전7fail/50pass로 확보했습니다. Missing 판정은 알려진 NumPy/pandas
  floating/temporal scalar에 한정하고 item은 지원 plain/date 표현일 때만 재귀합니다.
  정상 numeric/bool/Unicode/NaN/NaT·기존 item→기본값 변환은 유지합니다.
- 새71개 검사에서 mapping/records/object dtype의 값/타입·미지원 원객체 보존·strict
  JSON ValueError·비반사 custom 객체 비교/문자열화 방지·한 번만 수행하는 item·pandas
  NA/NaT를 확인했습니다. Unsupported extended precision을 float로 강제변환하지 않으며
  arbitrary Python method sandbox는 아닙니다. DATA-06은 이 범위에서 **PASS**입니다.
- 914a402의 CI run39048096708 Linux job117440805789는 MSRV/lint/unit과 advanced
  smoke를 통과했지만 경로 probe의 default.jsonl provenance가 없어 실패했고 Windows는
  취소됐습니다. 잘못된 interpreter 선택이나 실제 remote customizer 경로는 증명되지 않았습니다.
  **FIND-016 (QA 가정 보강):** venv sitecustomize lookup을 전제하지 않고 임시 전용
  module/.pth로 recorder를 로드합니다. 별도 shadow sitecustomize를 그대로 유지해도
  recorder가 실행됨을 self-check했고 원래 executable/prefix/version/argv assertion은 유지합니다.
- Optional overlay **244통과/skip0**, 프로젝트 대상 **1116통과/27skip**, 최소 대상
  **354통과/선택25skip/2142deselected/경고481**입니다. 실제 Windows 경로4case/
  12child와 foreign-customizer 보존도 통과했습니다. Ruff212파일/format·Pyright·LSP5경로·
  계약·clean sdist→wheel까지9명령이 exit0이며 새로운 browser/native-unit count나 Linux
  재통과로 세지 않습니다. RUST-02는 계속 RUNNING입니다.
- 프로젝트 의존성/lock·원문 체크리스트·버전/tag/배포는 유지합니다. 기존 실패 로그는
  ANSI 제거 후 읽어 SHA를 보존했으며 원격 CI 재실행은 후속 푸시 후 별도 관찰해야 합니다.

## 12차 — 커밋/푸시 후 timestamp 정밀도·CI 환경

- 6~11차 변경46파일을 `359277c6c7ee6862a85a158eb32ba9d4cf4dcf87`로 커밋하고
  origin/main에 푸시한 뒤 진행했습니다. 태그/버전/릴리스 상태는 바꾸지 않았습니다.
  현재 phase의 로컬 증거는 `C:\Users\mud\AppData\Local\Temp\mudplot-review-temporal-9n9cnwba`,
  [경로 제거 temporal/CI 요약](review_evidence/temporal_ci_verification.json)도 보존합니다.
- **FIND-013 (DATA-05):** NumPy datetime64 ns/ps/fs/as가 epoch 정수로 바뀌고 Polars
  ns가 microsecond로 잘리는 것을 수정 전36fail/16pass로 확보했습니다. dtype을 유지해
  scalar ISO로 변환하고, Polars native formatter/parse/equality가 lossless임을 확인합니다.
  Coarse 형식/실제 숫자 epoch/NaT와 dtype 없는 2-D array protocol은 유지합니다.
- 새 temporal58개가 scalar/0D/column/object/record/row/2D/structured·UTC/offset/DST·
  process TZ/C locale·비손실 formatter 거부·미지원 numeric date axis를 확인했습니다.
  모호한 mapping2D datetime column은 오류로 처리하고 실제 2D row 입력은 지원합니다.
  Arrow ns는 upstream safe conversion을 따르며 pandas 부재 등은 명시적으로 실패할 수
  있습니다. 모든 과거 timezone/precision/OS를 인증한 것이 아니며 DATA-05는 이 범위에서 **PASS**입니다.
- **FIND-014 (CI fixture 환경):** 359277c의 CI run39045121490은 Python3.10/3.12 jobs가
  성공했지만 Linux Rust smoke가 advanced regression action400에서 실패했고 Windows는
  취소됐습니다. Linux MSRV/lint/native unit은 성공했으나 전체 workflow는 failure입니다.
  Job117432201128 로그(ANSI 제거)·render-only 재현의 optional regression ImportError·
  설치 목록을 대조해 CI가 render만 설치한 불일치를 확인했습니다. Smoke job만 extra all로
  고치고 수정 전 실패하는 static guard를 추가했습니다. Runtime 필수 의존성은 유지합니다.
- Optional PyArrow26/Polars2를 포함해 **173개 모두 통과**, 프로젝트 대상은 **1045통과/
  27skip**, 최소 대상 **283통과/선택25skip/2142deselected/경고481**입니다. 격리된 all
  환경의 실제 Rust smoke와 Ruff211파일/format·Pyright·LSP5경로·계약·clean sdist→wheel을
  포함한9기록 명령이 exit0입니다. Browser/native unit 새 count나 수정 후 원격 CI 성공으로
  세지 않습니다. 개발 중 dtype 없는 fake-array 회귀도 별도 test로 잡아 수정 후 확인했습니다.
- 원문 체크리스트·프로젝트/lock·package/editor/spec 버전·tag/배포는 유지합니다.
  날짜는 ISO 저장이며 새로운 continuous date-axis 구현을 뜻하지 않습니다.

## 11차 — 실제 body 경계·framing·서버 PID 메모리

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-body-boundaries-3c7c1_st`,
  [경로 제거 body/메모리/실행 요약](review_evidence/body_boundary_verification.json)도 보존합니다.
- 순차 probe **39개 통과**(Python13/Rust26). 실제 form·nested JSON form·JSON
  endpoint의 N-1/N 본문을 전송했고, 알려진 N+1 선언은 업로드 전에 거부했습니다.
  Rust unknown-length chunked는 N-1/N/N+1 및 `/undo`·`/reset` 초과에서 상태/PNG
  보존을 확인했습니다. Python은 미지원 Transfer-Encoding을 읽기 전 거부합니다.
- **FIND-011 (Python framing):** Transfer-Encoding 무시·중복 Content-Length 사용·짧은
  body를 그대로 반환하는 경계에서 수정 전6fail/4pass를 확보했습니다. `_read_body`가
  지원하지 않는 framing/중복 길이를 거부하고 실제 읽은 길이가 다르면 action 전에 실패합니다.
  실제 HTTP의 reset/잘린 action prefix3사례도 상태/history/PNG를 보존했습니다.
- **FIND-012 (Rust 전역 body 경계):** 본문을 추출하지 않는 `/undo`가 unknown-size
  chunked의 한도 확인 전에 상태를 바꿨습니다. 계획16MiB+1 중393216byte를 client가
  넘긴 뒤 연결이 중단됐으므로 전체 초과 body 수용/무제한 할당으로 과장하지 않습니다.
  기존 Axum limited Bytes extractor를 모든 handler 앞에 적용하고 request parts를
  보존해 넘깁니다. 새 parser/의존성은 없고 기존 DefaultBodyLimit도 유지합니다.
- Windows venv launcher와 실제 Python server PID가 달라 최초5MiB launcher 수치는
  폐기했습니다. 현재 Python worker의 `os.getpid`를 확인해 측정했고, 소유한 process tree
  종료와 listener 폐쇄도 확인했습니다. 기록된 server PID 수명 peak는 Python252.14MiB/
  Rust30.40MiB였습니다. 시작 후 수명 peak이지 request별 reset 값/전체 앱 hard limit이
  아니며 native 렌더 자식은 제외합니다. 동시 부하/렌더 CPU/모든 OS 보장은 아닙니다.
- 본문/fault unit13개와 지원 content-type/전송 경계 및 위 메모리 관찰을 근거로 SEC-03을
  **PASS** 처리합니다. 계산량/RSS hard cap인 SEC-04/PERF와 원격 OS gate는 그대로 남습니다.
- 최종 대상 **993통과/20skip**, Python 브라우저 **31통과**, native Rust **15통과/
  helper1ignored**, 실제 Rust HTTP/browser도 통과했습니다. 최소 대상은 **232통과/
  선택18skip/2142deselected/경고481**이며 전체 matrix/zero-warning 주장은 아닙니다.
  Ruff209파일/format·Pyright·LSP7경로·Clippy/fmt·계약·clean sdist→wheel까지13기록
  명령이 exit0입니다. MSRV/Linux 실행 결과로 세지 않습니다.
- 새 순차 probe를 Windows/Linux Rust CI에 구성했지만 원격 실행은 관찰하지 않았습니다.
  원문 체크리스트·core 의존성/lock·package/editor/spec version·tag/배포는 유지합니다.

## 10차 — 실제 optional table·SQL cursor 소유권

- 실제 PyArrow26.0.0/Polars2.0.0을 별도 venv에서 실행했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-libs-_bgvxl_h`,
  [경로 제거 형식/SQL 실행 요약](review_evidence/table_sql_verification.json)도 보존합니다.
- 격리 환경의 **114개 전부 통과/skip0**, 추가한 CI 명령도 로컬 **114통과**입니다.
  두 결과는 같은 범위의 별도 실행이므로228개 고유 검사로 합산하지 않습니다.
  Mapping/records/rows/NumPy2D/structured/pandas/SQL query/cursor/generic to_dict/
  Arrow·chunks·dictionary/Polars·categorical14경로에서 값/결측/그룹/행 순서와
  원본 비변경·line/scatter/lineplot의 사용 관측을 비교했습니다. DATA-01은 **PASS**입니다.
- 실제 테이블의 signed64 범위에서2^53초과 정수·boolean·Unicode·null·UTC microsecond,
  empty named columns와 중복 Arrow 이름을 확인했습니다. Decimal/무한대는 유효 JSON으로
  coercion하지 않습니다. 모든 optional 버전/정밀도/timezone/OS를 인증한 결과는 아닙니다.
- **FIND-010 (DATA-07 resource):** connection+query의 내부 생성 cursor를 success/
  execute/fetch/shape/duplicate 실패 뒤 명시적으로 닫지 않음을 수정 전5fail/2pass로
  확보했습니다. `to_columns`의 해당 경로만 finally로 close(지원 시)하고 caller-owned
  executed cursor/connection은 보존합니다. Query/params를 그대로 넘기며 commit/rollback
  하지 않고 close 실패/예외 context도 전파합니다. 새 SQL 회귀10개 통과, DATA-07은 **PASS**입니다.
- 프로젝트 기본 환경은 **980통과/20skip**, 최소 data 대상은 **95통과/18skip/
  2266deselected/경고13**입니다. 기본20skip은 선택 라이브러리18·Windows조건2이며
  선택 검사 추가로 skip 수가 늘어난 것이지, 실제114-pass 검증을 생략한 것이 아닙니다.
  최소 환경에는 최신 optional 라이브러리를 설치하지 않아 그 버전 floor를 주장하지 않습니다.
- Ruff207파일/format·Pyright·LSP6경로·계약 sync·clean sdist→wheel을 포함해9기록
  명령이 exit0입니다. 새 CI step은 optional 라이브러리를 upfront import한 뒤 실행하도록
  구성했지만 원격 CI 성공으로 세지 않습니다. 이번 browser/Rust native 새 실행도 없습니다.
- 설치했던 전용 venv는 결과·버전·지문을 남긴 후 제거했습니다. 원래 프로젝트에서는
  pyarrow/polars import가 계속 불가함과 pyproject/uv.lock 비변경을 확인했습니다.
  로그/receipt만 보존하며 원문 체크리스트·버전/tag/배포는 유지합니다.

## 9차 — 모든 모델 필드 codec·Python 실행 경로

- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-codec-paths-2t3d4dl_`;
  [경로 제거 실행/child argv/codec 요약](review_evidence/codec_path_verification.json)도 보존합니다.
  기반96a8592와 기존 로컬 변경은 유지했으며 이번에는 새 제품 결함/수정이 재현되지 않았습니다.
- 전체 dataclass 탐색으로 **24모델/272필드**의 nondefault·대체 union·null/Unicode/
  big integer fixture3개를 생성했습니다. Schema-valid지만 호환되지 않는 옵션을 함께 채운
  **직렬화 전용 fixture**이며 렌더 가능성/모든 옵션 조합 동등성을 뜻하지 않습니다.
- `test_review_full_spec_fields.py` **69개**가 필드 누락/기본값으로 가려진 손실·JSON
  기본 타입·배열 순서·nested model 복원을 검사합니다. 등록37예제의 정상 spec/JSON
  왕복도 별도로 확인했습니다. Raw NumPy float64→JSON builtin float는 허용된 정규화로
  값 동등성을 확인하며, 초기5개 dtype-identity 실패를 제품 버그로 세지 않았습니다.
- 실제 Python 생성 JSON→Rust strict FigureSpec→JSON 파일→Python 모델 복원을 실행해
  fixture3개 전체를 비교했습니다. Field introspection/checked-in snapshot으로 새 필드가
  조용히 미검증 상태가 되지 않게 하며 버전은 기존0.1을 유지합니다. JSON-01은 **PASS**입니다.
- Interpreter probe는 별도 한글/공백/`&` venv·임시 경로에서 PATH default/env/flag
  세 경우 각4개의 실제 capabilities/apply/render child를 확인했습니다. `sys.executable`,
  prefix/version/원본 argv와 PNG를 검증하고, 잘못된 명시 flag는 env의 정상 Python으로
  fallback하지 않았습니다. Startup recorder는 그 임시 venv 안에만 exclusive 생성합니다.
- 첫 offline setup은 캐시 부족으로 중단되어 성공/제품 결함으로 세지 않았습니다. 명시한
  준비 변경 후 같은 NumPy/Matplotlib 버전을 임시 venv에만 내려받고 정리했습니다.
  프로젝트 패키지/의존성/lock은 바꾸지 않았습니다. 실제 Windows만 실행했으며 추가한
  Windows/Linux CI matrix는 아직 실행을 관찰하지 않아 RUST-02는 **RUNNING**입니다.
- 기록된 대상 **968통과/4skip**, native Rust **lib14+main1통과/helper1ignored**,
  최소 환경 **207통과/2skip/2142deselected/경고481**. Clippy/fmt·Ruff205파일/format·
  Pyright·LSP6경로·계약 sync·clean sdist→wheel도 통과했습니다. 이 phase의 browser
  새 실행은 없고 이전31개는 그대로 과거 결과입니다. MSRV/Linux 전체 실행도 아닙니다.
- 12개 기본 명령 뒤 QA startup-hook의 target/exclusive-create 검증을 보강하고 그
  스크립트·Ruff/format/Pyright/packaging을 별도로5명령 재실행했습니다. 변경 없는 core/
  codec 대상968개를 새 QA 변경까지 검증한 것으로 확대하지 않으며 source revision과
  17개 성공 receipt를 구분합니다. 원문 체크리스트·배포/version/tag는 유지합니다.

## 8차 — 공통 상태 경로·실패 격리·HTTP 경계

- 기반96a8592 위의 로컬 변경(6/7차 포함)을 확인했습니다. 최종 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-editor-boundary-final-hdtdgy50`,
  [경로 제거 실행/상태 해시/argv 요약](review_evidence/editor_boundary_verification.json)도 보존합니다.
- 최종 대상 **899 통과, 4 skip**, Python 실제 브라우저 **31 통과**. 최소 환경 대상은
  **138 통과, 2 skip, 2142 deselected, 경고481**입니다. Skip은 기존 선택 의존성/
  Windows 조건이며, 경고는 별도10-case 가시화 조사에서 Matplotlib3.8/pyparsing
  deprecation/diagnostic을 확인했습니다. zero-warning 또는 전체 경고 조사를 주장하지 않습니다.
- Rust native **lib13+main1 통과/보조 helper1 ignored**, 실제 HTTP/browser의 상태·
  실패·Host/Origin·CSP·선언 크기 검사 통과. Native IPv6 `::1` listener도 실제 실행해
  HTTP/Host/header를 확인했습니다. Clippy/fmt·Ruff203파일/format·Pyright·LSP7경로·
  계약 sync·clean sdist→wheel까지13개 기록 명령이 최종 exit0입니다. MSRV1.88 결과는 아닙니다.

| ID | 판정 | 실행한 근거 |
|---|---|---|
| STATE-03 | PASS | 공통 fixture10작업의 fluent/functional/Store/CLI/Python session·HTTP/Rust agent·지원 form에서 중간/최종 FigureSpec 비교 |
| EDIT-01 | PASS | Python _build_action 및 실제 양 editor 폼/agent의 theme·size·title·layer metadata 비교; 없는 Rust UI는 agent로 수행했다고 구분 |
| RUST-01 | PASS | PythonBridge apply/render argv와 CLI source를 대조; preview만 --preview, vector는 원본 export; 실제 공통 상태 JSON 비교 |
| HIST-03 | PASS | validation/손상 JSON/실제 Matplotlib render 실패에서 양 editor spec/history/PNG/redo 보존과 후속 정상 요청 확인 |
| SEC-01 | PASS | IPv4/IPv6 bind guard와 실제 loopback listener·localhost/IPv4/IPv6 Host matrix, malformed/forwarded Host 거부 |
| SEC-02 | PASS | scheme/host/port/null/cross-site 거부·Origin 없는 CLI 및 same-origin 정상 payload 허용; 브라우저 null-Origin payload 거부 |
| SEC-05 | PASS | 정상/error/static/PNG/PDF/SVG·403/404/413 application header와 실제 htmx swap의 console/CSP event 확인 |
| SEC-03 | RUNNING | 선언16MiB+1을 업로드 전 거부하는 경계만 확인; 실제 한도 전후·content type·chunked·peak RSS matrix는 남음 |

### 재현한 보완점과 실패 실행의 처리

- **FIND-008 (application 응답 계약):** Rust의 기존 Host/Origin 거부는 차단 자체는
  성공했지만 공통 no-store/CSP header 처리를 우회했습니다. 실제 smoke의403 header
  assert 실패를 먼저 확보한 뒤 거부도 같은 header 경로로 보냈습니다. 접근 조건은 그대로입니다.
- **FIND-009 (선행 경계 보강):** 선언 Content-Length16MiB+1만 보냈을 때 body를
  기다려5초 timeout이 났습니다. middleware가 이를413으로 먼저 거부하고 기존 streaming
  DefaultBodyLimit은 유지합니다. 무제한 payload 수용이 확인된 것도, SEC-03 전체가 끝난 것도 아닙니다.
- 처음 묶음 `mudplot-review-editor-boundary-mu7xq2yn`은 Rust Origin 거부의 Windows
  WinError10053 및 로그 reader의 UTF-8 decode 오류로 중단했습니다. 뒤 검사는 실행하지
  않았고 성공으로 세지 않았습니다. 원본 실패 로그는 그대로 보존했습니다.
- 현재 거부 matrix는 body decode/upload 이전에403이어야 하는 **header-only** 요청으로
  분리하고, 정상 same-origin/agent 및 브라우저 null-Origin은 실제 payload로 확인합니다.
  Windows 연결 중단의 원인/일반 네트워크 신뢰성이 해결됐다고 주장하지 않습니다. 최종
  재실행은 명시한 UTF-8 로그 환경을 사용했으며 테스트 안의 retry/fallback은 추가하지 않았습니다.

공통 fixture는 `tests/fixtures/review_state_paths.json`과 `review_http_boundaries.json`에
있고 sdist 포함도 검사합니다. 최종 상태 canonical hash는 native form/agent 모두
`926e9f349bcb681d626b8c9e1a2215fcd39932d5a923bf48ed3975a47fc9f6c9`였습니다.
이 통과를 전체 UI 동등성/보안 인증/전체 suite/OS/릴리스 gate로 확대하지 않습니다.

## 7차 — 결측 좌표·중첩 상태·이력 경계

- 현재 기반96a8592 위의 로컬 변경(6차 포함)을 검사했습니다. 로컬 증거는
  `C:\Users\mud\AppData\Local\Temp\mudplot-review-missing-history-btis6dds`, 저장소 내
  [경로 제거 검증/커서 해시 표](review_evidence/missing_state_verification.json)도 보존합니다.
- 대상 **859 통과, 4 skip**: 실제 PyArrow/polars 부재2·Windows 조건2입니다. 최소
  Python3.10/NumPy1.23 대상 **98 통과, 선택 의존성2 skip, 2142 deselected, 경고13**.
  실제 Rust HTTP/browser의 단계별 spec/PNG·branch·JSON corpus가 통과했습니다.
  Ruff201파일/format·Pyright·LSP5경로 확인·계약 sync·clean sdist→wheel도 exit0입니다.
  Native Rust unit/MSRV 전체를 이번에 다시 실행한 결과로 보고하지 않습니다.
- **FIND-007 (DATA-03 production):** 범주/ISO 날짜 문자열 x의 null이 문자열 `None`
  범주가 되며 결측 관측을 정상 점처럼 표시했습니다. 수정 전10개 실패를 확보했습니다.
  `_x_values`가 non-null 범주만 등록하고 원래 행 위치에는 NaN을 남기도록 수정했습니다.
  Raw line은 단절, scatter는 mask하며 실제 문자열 `"None"`·shared/y2 정렬·JSON 원행은
  유지합니다. 새 날짜 축/통계 정규화 정책은 추가하지 않았습니다.

| ID | 판정 | 실제 확인한 경계 |
|---|---|---|
| STATE-01 | PASS | 중첩 data/matrix/theme/reference의 성공·실패 입력 비변경, 반환값과 AddLayer action 분리 |
| STATE-02 | PASS | Plot.spec/Store.state/dispatch/history·listener별 중첩 mutation 격리 및 replay 유지 |
| HIST-01 | PASS | Store와 시작 직후 Rust session의 끝까지 undo/redo·빈 경계; 단계별 spec/PNG·커서 해시 비교 |
| HIST-02 | PASS | Python/Rust A→B→C→undo→D 뒤 C redo 불가, history/저장 spec/PNG는 D branch 유지 |
| DATA-03 | PASS | None/NaN/nullable/NaT의 정규화와 raw line 단절·scatter mask·lineplot 사용 표본을 분리 검증 |
| DATA-01 | RUNNING | mapping/records/rows/NumPy2D/structured/pandas/SQL의 값·순서·그룹·원본 비변경은 확인했으나 실제 PyArrow/polars는 미실행 |
| HIST-04 | RUNNING | Python open/reset fresh와 Rust undoable snapshot 차이를 확인·문서화; 전체 dirty/저장 대상/reset 조합 검토는 남음 |

이력 코드의 제품 수정은 없었습니다. 첫 Rust probe는 open을 이력 초기화로 잘못 가정해
실패했습니다. 구현을 읽어 기존 정책을 확인한 뒤 빈 경계 검사를 서버 시작 직후로 옮기고
Rust open의 undo/redo를 따로 확인했습니다. 잘못된 probe를 제품 결함으로 세지 않았으며
재현한 결측 좌표 문제와 구분해 기록합니다. 모든 항목/OS/접근성/보안/릴리스 완료는 아닙니다.

## 6차 — DATA-02 입력 구조 검증 마무리

- 기반 commit은 `96a85922293fac14f5aa5e3dcb45b7c9ec66ff1f`이며 그 위의 로컬 변경을
  검사했습니다. 원문 기준 SHA와 현재 검토 기반을 혼동하지 않습니다. 버전/릴리스는 유지합니다.
- 로컬 증거: `C:\Users\mud\AppData\Local\Temp\mudplot-review-data-shapes-f2y9mmx2`.
  [경로 제거 검증 요약](review_evidence/data_shape_verification.json)에 명령/환경/
  소스·원문 지문/원본 log hash와 결과를 별도 보존합니다.
- 실제 결과: **677 통과, Windows 조건 2 skip**, 최소 Python3.10/NumPy1.23 adapter
  **66 통과, 2142 deselected, 경고13**. Ruff200파일/format·Pyright·계약 sync·clean
  sdist→wheel도 exit0입니다. 이 대상 결과를 전체 suite/MSRV/Linux로 확대하지 않습니다.
- **FIND-006 (DATA-02 production):** 혼합 입력의 record가 mapping이 아니면 위치 없는
  AttributeError가 났고 positional/DB 행의 문자열/bytes/dict는 문자/key 열로 조용히
  바뀌었습니다. 수정 전19fail/9pass를 확보했습니다. `_records_to_columns`가 record
  타입/중복 key의 index를 검사하고 `_row_values`가 두 row 경로에서 잘못된 타입을
  pivot 전에 거부합니다. 유효한 row와 sqlite3.Row·record 누락-key/null 동작은 유지합니다.

| 검증 범위 | 실제 테스트·결과 |
|---|---|
| 잘못된 record/positional/DB row·너비 | test_review_data_contracts.py의 index/expected/타입 검사, 입력 비변경 확인 |
| 열 길이 불일치 | mapping/DataFrame·Arrow·to_dict duck protocol에서 값 그대로 보존 후 validate/assert_valid가 이름별 길이로 거부 |
| 없는 x/y/group | line/scatter에서 panel/layer/column 위치 오류와 validation 입력 비변경 확인 |
| 중복 열/충돌 | 실제 pandas duplicate/string-conversion collision과 기존 mapping/record/DataFrame/Arrow/DB 중복 거부 검사 |
| 실패 격리 | 잘못된 editor import/SetData 뒤 state/history/PNG/redo 보존; CLI apply의 입력·기존 출력 보존 |
| 정상 호환 | sparse-record 첫 등장 열 순서/null, 정상 positional/DB row, sqlite3.Row·caller connection 재사용 |

DATA-02를 **PASS**로 닫습니다. 직접 실행한 새/기존 DATA-02 회귀 파일은49개이고
최소 환경에서도 전부 실행했습니다. 실제 PyArrow/polars는 설치하지 않았으며 그 라이브러리
전체 호환성이나 DATA-01의 형식 간 동등성을 완료한 것으로 세지 않습니다. Arrow 등은
이 항목의 malformed-input duck protocol만 확인했습니다. 새 성능/결측/정렬 정책은 없습니다.

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
| STATE-01 | P0 | PASS | reducer의 입력 비변경 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-02 | P0 | PASS | 공개 스냅샷의 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-03 | P0 | PASS | 상태 변경 경로의 일관성 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-04 | P0 | PASS | mp.apply의 실패 격리 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-05 | P0 | PASS | 비트랜잭션 배치 API의 계약 보존 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-06 | P0 | PASS | listener 예외의 commit 시점 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-07 | P1 | OPEN | 결정성과 암묵적 전역 상태 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-08 | P1 | OPEN | 잘못된 참조와 경계 인덱스 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| STATE-09 | P1 | OPEN | 검증과 부수효과 경계 | mudplot/spec.py; reducer.py; store.py; api.py | test_reducer.py; test_stabilization.py; test_review_state_contracts.py |
| HIST-01 | P0 | PASS | 기본 undo/redo와 경계 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-02 | P0 | PASS | undo 이후 분기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-03 | P0 | PASS | 편집기 action/import/render 실패 원자성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-04 | P1 | PASS | reset과 open의 이력 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-05 | P1 | PASS | no-op action의 정책 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-06 | P1 | PASS | 긴 이력의 재생 정확성 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-07 | P2 | OPEN | 연속 드래그 action 합치기 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| HIST-08 | P2 | OPEN | 체크포인트와 이력 제한 | mudplot/store.py; dashboard/editor_server.py; mudplot-editor/src/model.rs | test_reducer.py; test_dashboard_editor.py; test_editor_browser.py |
| JSON-01 | P0 | PASS | 공식 지원 필드의 손실 없는 왕복 | io.py/spec.py; model.rs::full_field_fixture_preserves_types_values_and_array_order | test_review_full_spec_fields.py(69); Python→Rust→Python 9차 artifact |
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
| DATA-01 | P0 | PASS | 입력 형식 간 동일 데이터의 동등성 | data.py::to_columns/_to_list/_mapping_to_columns | test_review_missing_data.py(14formats); test_review_table_formats.py(13); 실제 optional114-pass 실행 |
| DATA-02 | P0 | PASS | 열 길이·필수 열·중복 열 | data.py::_records_to_columns/_row_values; validate.py::_check_data_integrity/_check_column | test_review_data_contracts.py(49); test_data.py; test_validate_hardening.py; 6차 증거 |
| DATA-03 | P0 | PASS | 결측값의 정규화와 렌더링 분리 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-04 | P1 | OPEN | 혼합 그룹 식별자 | mudplot/data.py; validate.py | test_data.py; test_stabilization.py |
| DATA-05 | P1 | PASS | 날짜·시간·timezone | data.py::_plain_value/_to_list/2D datetime path | test_review_temporal_precision.py(58); 실제 optional/일반/minimum 12차 기록 |
| DATA-06 | P1 | PASS | NumPy scalar와 지원하지 않는 객체 | data.py::_plain_value missing/item guards | test_review_scalar_boundaries.py(71); optional/project/minimum 13차 기록 |
| DATA-07 | P1 | PASS | SQL 파라미터와 연결 소유권 | data.py::to_columns query finally | test_review_sql_ownership.py(10); named/tuple params·transaction·borrowed cursor·cleanup failures |
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
| EDIT-01 | P0 | PASS | UI 입력과 공통 action | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-02 | P1 | OPEN | 드래그·키보드 위치 편집 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-03 | P1 | OPEN | htmx 교체 이후 상태·이벤트 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-04 | P1 | OPEN | 지연 응답과 최신 preview | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-05 | P1 | OPEN | 두 탭·동시 agent 요청 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-06 | P1 | OPEN | open·export·실패 후 회복 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-07 | P1 | OPEN | 입력 오류의 위치·설명 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-08 | P1 | OPEN | 키보드 접근과 상태 피드백 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| EDIT-09 | P1 | OPEN | agent 응답의 기계 판독성 | dashboard/editor_server.py; editor_view.py | test_dashboard_editor.py; test_editor_browser.py |
| RUST-01 | P0 | PASS | Python CLI 위임의 계약 일치 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-02 | P0 | PASS | Python 실행 파일 선택과 quoting | main.rs::parse_args; python.rs::PythonBridge | check_python_bridge_paths.py Windows/Linux CI jobs success for781f3f5; 14차 remote snapshot |
| RUST-03 | P1 | OPEN | 실패한 subprocess와 출력 경계 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-04 | P1 | OPEN | 120초 timeout과 자식 정리 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-05 | P1 | OPEN | preview 2000px 제한과 원본 보존 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-06 | P1 | OPEN | Rust history와 캐시의 commit 순서 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| RUST-07 | P1 | OPEN | 공유 static 자산·버전 정합성 | mudplot-editor/src/; scripts/rust_editor_smoke_test.py | Rust unit tests; rust_editor_smoke_test.py --browser |
| SEC-01 | P0 | PASS | loopback bind와 Host 검증 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-02 | P0 | PASS | Origin과 mutation 경계 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-03 | P0 | PASS | 16 MiB 요청 한도 | _Handler._read_body; protect_local_boundary limited Bytes | test_review_body_framing.py(13); check_request_body_limits.py(39); 실제 PID RSS/peak·상태 보존 11차 기록 |
| SEC-04 | P1 | OPEN | 작은 요청의 과도한 계산 방어 | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
| SEC-05 | P1 | PASS | CSP·no-store·브라우저 header | dashboard/editor_server.py; mudplot-editor/src/; SECURITY.md | test_dashboard_editor.py; test_editor_browser.py; Rust guards |
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

- 현재 상태: PASS 34, RUNNING 12, OPEN 104, FAIL 0, BLOCKED 0, N/A 0, DEFERRED 0. 이는 완료율/안정성 확률이 아닙니다.
- 확인된 production 결함: FIND-002/003/004/005/006/007/008/010/011/012/013/015/017을 재현 후 수정했습니다. FIND-014는 별도의 CI fixture 설치 환경 불일치입니다. FIND-001은 연결 검사 결함, FIND-009는 요청 선행 거부 보강이며 실제 전체 body 한도 우회를 확인한 것은 아닙니다. 미검증 영역의 결함 부재를 뜻하지 않습니다.
- 다음: JSON/출력 ID의 기존 fixture 범위를 대조하고, editor/보안/Rust/패키징의 P0 경계를 증거 파일과 연결합니다. 기준을 완전히 충족한 ID만 닫습니다.
- 원문 G0~G8 gate는 전체 PASS가 아닙니다. 전체 suite·전체 최소 환경·Rust MSRV·headless Linux·TeX/성능·dependency 보안 감사·release provenance는 이번 1차 검토에서 미실행입니다.
- 비교 SHA의 clean main 실행은 별도 작업 트리/환경이 필요합니다. 현재 dirty tree를 reset/clean/revert하지 않습니다.
- 공개 계약 변경, snapshot/zero-copy 구조 변경, 원격 인증, PGF 다중 파일 원자성, 새 성능 임계값/전면 benchmark framework는 도입하지 않았습니다.
