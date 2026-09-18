# mudplot Rust editor (M13, v0.6)

Python mudplot과 같은 `FigureSpec`·JSON action을 쓰는 로컬 axum + Askama +
htmx editor다. 생성 계약의 drift를 막기 위해 이 저장소 안에서 Python
package와 함께 versioning한다.

## 실행

저장소 root에서 `uv sync --locked --extra render` 후:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

<http://127.0.0.1:8766/>을 연다. `--bind LOOPBACK:PORT`, `--python PATH`
또는 `MUDPLOT_BIND`, `MUDPLOT_PYTHON`으로 기본값을 바꿀 수 있다.

인증이 없는 로컬 단일 사용자 도구이며 non-loopback bind 주소/HTTP Host와
cross-origin browser mutation을 거부하며 모든 response를 `no-store`로
보내고 제한적인 CSP/browser security header를 적용한다.

## 계약과 현재 범위

- Rust는 로컬 HTTP session, undo/redo stack, compile-time template, htmx
  fragment를 담당한다.
- serde `FigureSpec`·action envelope는 64-bit 범위를 넘는 정수를 포함한
  지원 JSON 필드를 보존하며 중복 key를 재귀적으로 거부한다. arbitrary-
  precision 정수에 serde가 내부 사용하는 유일한 예약 key
  `$serde_json::private::Number`는 Python/Rust 모두 거부한다.
- reducer/validator의 단일 source는 `python -m mudplot apply`, renderer는
  `python -m mudplot render`로 유지한다.
- 실패한 action/import/render는 현재 spec과 history를 변경하지 않는다.
- capability에서 전체 layer selector/field reference와 theme/projection
  control을 생성하고 title·정확한 figure size도 같은 JSON action으로 변경한다.
- 저장 spec 열기와 정확한 크기의 PDF/SVG/JSON export를 지원한다. cached
  PNG preview는 어느 축이든 2000 pixel을 넘을 때만 DPI를 낮추며
  spec/final export는 바꾸지 않는다.
- htmx와 0BSD license는 `dashboard/static/`에서 재사용하며 복제하지 않는다.
  request body 상한은 16 MiB, Python bridge subprocess timeout은 120초다.

Route: `GET /`, `/fig.{png,pdf,svg}`, `/spec.json`,
`/static/htmx.min.js`; `POST /action`은 action JSON object를 받는다. visual
control은 `/control/*`와 `/layers`, `/open`·`/action/raw`·`/undo`·`/redo`·
`/reset`은 `#app` htmx fragment를 반환한다.

계속 의도적으로 제외: 다중 사용자 session/auth, 성숙한 Python editor의
모든 특수 axis/drag control, native Rust renderer. 로컬 실사용이 추가
상태와 코드를 정당화할 때만 도입한다.
