# mudplot Rust editor (M13, 1단계)

Python mudplot과 같은 `FigureSpec`·JSON action을 쓰는 로컬 axum + Askama +
htmx editor다. 생성 계약의 drift를 막기 위해 이 저장소 안에서 Python
package와 함께 versioning한다.

## 실행

저장소 root에서 `uv sync --extra render` 후:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --manifest-path mudplot-editor/Cargo.toml
```

<http://127.0.0.1:8766/>을 연다. `--bind LOOPBACK:PORT`, `--python PATH`
또는 `MUDPLOT_BIND`, `MUDPLOT_PYTHON`으로 기본값을 바꿀 수 있다.

인증이 없는 로컬 단일 사용자 도구이며 non-loopback bind 주소는 거부한다.

## 1단계 계약

- Rust는 로컬 HTTP session, undo/redo stack, compile-time template, htmx
  fragment를 담당한다.
- serde `FigureSpec`·action envelope는 모든 JSON 필드를 보존한다.
- reducer/validator의 단일 source는 `python -m mudplot apply`, renderer는
  `python -m mudplot render`로 유지한다.
- 실패한 action/render는 현재 spec과 history를 변경하지 않는다.
- htmx와 0BSD license는 `dashboard/static/`에서 재사용하며 복제하지 않는다.

Route: `GET /`, `/fig.png`, `/spec.json`, `/static/htmx.min.js`; `POST
/action`은 action JSON object를 받고 `/action/raw`, `/undo`, `/redo`,
`/reset`은 `#app` htmx fragment를 반환한다.

이번 범위에서 제외: 다중 사용자 session, 인증, Python prototype의 전체
visual form, import/vector export, native Rust renderer. bridge와 route 계약의
효용이 확인된 뒤에만 추가한다.
