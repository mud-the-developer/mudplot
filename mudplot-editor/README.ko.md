# mudplot Rust editor (v1.0)

Python mudplot과 같은 `FigureSpec`·JSON action을 쓰는 로컬 axum + Askama +
htmx editor다. 생성 계약의 drift를 막기 위해 이 저장소 안에서 Python
package와 함께 versioning한다. 엔진 wheel에는 이 editor나 dashboard 자산이 없다.
같은 source checkout과 그 checkout의 Python 환경에서 빌드해야 한다.

## 실행

저장소 root에서 `uv sync --locked --extra render` 후:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

<http://127.0.0.1:8766/>을 연다. `--bind LOOPBACK:PORT`, `--python PATH`
또는 `MUDPLOT_BIND`, `MUDPLOT_PYTHON`으로 기본값을 바꿀 수 있다.
Interpreter 우선순위는 `--python` > `MUDPLOT_PYTHON` > PATH의 `python3`이다.
실행 파일과 인수를 shell 해석 없이 전달하며 잘못된 명시 경로는 다른 Python으로
fallback하지 않고 실패한다. Windows 실행 예:

```powershell
cargo run --locked --manifest-path mudplot-editor/Cargo.toml -- --python ".venv/Scripts/python.exe"
```

`uv run python scripts/check_python_bridge_paths.py`는 실행/임시 데이터 경로에
한글·공백·`&`가 있는 별도 venv를 검증한다. 같은 render 버전을 그 임시 venv에만
내려받을 수 있고 프로젝트 의존성은 유지한다. 로컬 Windows와 기준e14의
CI39111782233 Linux/Windows job에서 이 probe 통과를 관찰했다. 후속 변경은
별도 CI가 필요하며 모든 checkout을 검증했다는 뜻은 아니다.

인증이 없는 로컬 단일 사용자 도구이며 non-loopback bind 주소/HTTP Host와
cross-origin browser mutation을 거부하며 이 거부를 포함한 application response를
`no-store`/CSP/browser security header로 보낸다. Same-origin과 Origin 없는 로컬 agent는
지원하며 원격 사용자 인증 기능은 아니다.

## 계약과 현재 범위

- Rust는 로컬 HTTP session, undo/redo stack, compile-time template, htmx
  fragment를 담당한다.
- serde `FigureSpec`·action envelope는 64-bit 범위를 넘는 정수를 포함한
  지원 JSON 필드를 보존하며 중복 key를 재귀적으로 거부한다. arbitrary-
  precision 정수에 serde가 내부 사용하는 유일한 예약 key
  `$serde_json::private::Number`는 Python/Rust 모두 거부한다. 원래 key token을
  검사하여 serde가 literal 예약-key object를 값으로 바꾸지 못하게 하며 같은 표기의
  일반 문자열 value는 허용한다. 생략된 spec version은 Python처럼 내장 현재 기본값을
  쓰지만 명시한 null/unknown version은 실패한다. 이는 JSON 구조
  보존 계약이며 renderer 부동소수점 범위를 넘는 좌표/style 값은 명확히 실패한다.
- reducer/validator의 단일 source는 `python -m mudplot apply`, renderer는
  `python -m mudplot render`로 유지한다. 성공 stdout은 보존하고 실패 stderr는
  raw64KiB까지만 읽어 truncation 표시를 붙인다. UTF-8 대체 문자로 표시 byte는 늘 수
  있으며 디스크/CPU 제한이나 모든 자손 프로세스 격리를 보장하는 것은 아니다.
  성공 종료했어도 render 파일이 없거나 비면 preview/cache commit·export 전에
  거부한다. 이는 모든 binary format을 완전히 decode하는 검증은 아니다.
  관찰한 Windows/uv venv에서는 CWD/TMP를 짧게 두고 긴 data 절대 경로를 사용한다.
  긴TMP는 capture와 무관하게 interpreter 시작도 막았고 긴TEMP+짧은TMP는 통과했다.
  선택한 interpreter를 먼저 확인해야 하며 자동 대체나 일반 process-tree 정리 보장은 없다.
- 실패한 action/import/render는 현재 spec과 history를 변경하지 않는다. Rust의
  정상 open/reset은 undo 가능한 snapshot이며 Python open/reset은 새 이력을 시작한다.
  두 editor 모두 정상적인 새 편집 후 redo를 지운다.
- capability에서 전체 layer selector/field reference와 theme/projection
  control을 생성하고 title·정확한 figure size도 같은 JSON action으로 변경한다.
- 저장 spec 열기와 정확한 크기의 PDF/SVG/JSON export를 지원한다. cached
  PNG preview는 어느 축이든 2000 pixel을 넘을 때만 DPI를 낮추며
  spec/final export는 바꾸지 않는다.
- htmx와 0BSD license는 `dashboard/static/`에서 재사용하며 복제하지 않는다.
  request body 상한은16 MiB, Python bridge subprocess timeout은120초다. Timeout/
  wait 실패 시 Windows는 보유 child tree에 System32 taskkill을, Unix는 새 child process
  group에만 /bin/kill을 적용한다. 정리 command는 별도2초 예산이며 이후 직접 child
  kill/reap을 시도하고 정리 실패도 반환 오류에 남긴다. Foreground 소유 tree/group의
  범위이지 detached/reparented worker·CPU/disk hard limit·즉시 OS wait 보장은 아니다.
  정확한ea1의 Linux/Windows controlled 자손/MSRV step과 Windows 도구 부재/복구를
  통과했다. 후속 변경은 새로운 근거가 필요하다. 선언한
  Content-Length가16 MiB를 넘으면 body frame을 기다리기 전에 거부한다. 기존 limited
  Bytes extractor로 undo/reset을 포함한 모든 handler 전에 decoded body 한도를 적용하며
  한도 내 chunked를 지원한다. 로컬 N-1/N/N+1과 서버 PID의 수명 peak RSS를 관찰했지만
  렌더 자식/전체 앱 메모리·CPU·동시 부하 보장은 아니며 정확한 범위는 리뷰 대장에 있다.

Route: `GET /`, `/fig.{png,pdf,svg}`, `/spec.json`,
`/static/htmx.min.js`; `POST /action`은 action JSON object를 받는다. visual
control은 `/control/*`와 `/layers`, `/open`·`/action/raw`·`/undo`·`/redo`·
`/reset`은 `#app` htmx fragment를 반환한다.

계속 의도적으로 제외: 다중 사용자 session/auth, 성숙한 Python editor의
모든 특수 axis/drag control, native Rust renderer. 로컬 실사용이 추가
상태와 코드를 정당화할 때만 도입한다.
