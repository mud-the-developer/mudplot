# mudplot-dashboard (source-tree 도구)

*[English docs: README.md](README.md)*

`mudplot` **엔진과 분리된** 사람 대면 도구. 엔진의 의존성 없는 선언적
core에는 UI 의존성이 없고, 대시보드는 엔진을 단방향으로 임포트한다.

```
dashboard ──▶ mudplot   (단방향 의존)
```

*(이 섹션은 참고용 스냅샷입니다. 새 문서/에디터는 기본적으로 영어로 작성하니,
최신 내용은 영어 README.md를 참고하세요.)*

## 지금 있는 것

### 1. 문서 + 디자인 갤러리 정적 사이트 생성기

```bash
python -m dashboard build --out dashboard/site_build
# dashboard/site_build/index.html을 브라우저에서 엽니다.
```

빌드 결과의 `reading/VISUAL_REVIEW.html`에는 700px/320px 배치·caption·수치 조회,
SVG/PDF/편집 spec과 로컬 기준 문서가 포함됩니다. 에디터 초안과 같은 소스로
예제를 렌더링하며 원자료·canonical spec·로컬 링크를 검사합니다. 자동 생성이
곧 좋은 디자인이나 가독성 인증이라는 뜻은 아닙니다.

### 2. 로컬 인터랙티브 에디터

```bash
python -m dashboard serve   # http://127.0.0.1:8765/
```

**Start from a sample → Complete figure drafts**에서 Response/Endpoint의
700px/320px 배치를 선택할 수 있습니다. 선택은 **Open** 폼만 채우며 현재 그림·
PNG·action 이력은 바꾸지 않습니다. 기존 작업은 먼저 export한 뒤 **Open figure**를
눌러 적용하세요. 정상 import는 기존 파일 열기처럼 undo 이력을 새로 시작하고,
실패하면 현재 그림과 입력한 JSON 초안을 보존합니다. htmx의 localStorage 페이지
본문 이력 캐시는 사용하지 않습니다. 작업창 미리보기는 축소될 수 있으므로 최종
크기는 실제 크기 리뷰/내보내기에서 확인합니다.

스타일/팔레트/사이즈, 멀티패널 격자·활성 패널·Cartesian/polar/3-D projection,
x/y/z scale·고정/자동 limits·보조 y축, 라벨/reference 등을 폼으로
조작하면 미리보기가 즉시 갱신되는 로컬 웹
에디터. 서버는 loopback bind/HTTP Host만 허용하고 cross-origin mutation을
거부하며 request/form body를 제한하고 모든 response에 CSP와
`Cache-Control: no-store`를 적용합니다. Native 폼에도 명시적 POST action이 있어
JS가 없거나 아직 연결되지 않았을 때 입력을 GET URL에 넣지 않습니다. Referrer는
same-origin 정책(외부 전송 없음)을 사용하며 Origin/cross-site 차단을 완화하지 않습니다.
요청 body는 최대16MiB의 Content-Length framing을 지원하고 Transfer-Encoding/chunked·
중복 길이·불완전 body는 action 전에 거부합니다. 새 chunked decoder를 추가한 것은
아니며 정상적인 bodyless 로컬 action은 그대로 지원합니다.
빠른 폼 외에도 `capabilities.LAYER_TYPES` 기반 checked-JSON 폼으로
등록된 모든 레이어를 추가하고, 저장된 `.mplot.json`을 열거나
JSON/PNG/PDF/SVG로 내보낼 수 있습니다. 화면 preview는 어느 축이든
2000 pixel을 넘을 때만 DPI를 낮추며 spec과 최종 PDF/SVG export의
size/DPI는 그대로 유지합니다. 내부적으로 엔진의 Store/reducer를
그대로 재사용하므로 별도 상태가 없고, invalid action/import와 render
failure는 state/history를 바꾸기 전에 거부됩니다. 폼 제출은 전체 페이지를 다시 불러오지 않고
htmx 1.9.12(0BSD, `dashboard/static/htmx.min.js`로 vendoring, 새 Python
의존성 없음)로 그 자리에서 갱신됩니다. 공식 배포 파일의 SHA-256은
`scripts/check_wheel.py`에서 고정·검증합니다. 상단 **Editor**/**Docs** 탭의 `Docs`는
`mp.reference_markdown()`을 라이브 렌더링합니다. 미리보기 위에서 범례(파란
✥)·제목(보라 T)·`text`/`annotate` 레이어(초록 •) 핸들을 드래그하거나
클릭 후 화살표 키로 직접 재배치할 수 있습니다. 자세한 설명은 영어
README.md 참고.

- `site.py` — `mudplot.reference_markdown()` / `mudplot.capabilities()` 로
  엔진 레퍼런스를 만들고, 등록된 전체 layer 실행 예제와 디자인 원칙(팔레트
  CVD/그레이스케일 안전성, 이중 인코딩, TeX WYSIWYG, 보조축/heatmap 등)을
  실제 renderer로 생성해 index와 별도의 읽기 리뷰 페이지로 묶습니다.
- `plot_gallery.py` + `../examples/plots/` — 등록된 layer마다 실행 가능한
  source 파일 하나를 둔다. CI가 registry와 정확한 coverage를 비교하고,
  모든 spec의 검증·JSON round-trip·실제 렌더링을 수행한다.
- `markdown_lite.py` — mudplot이 생성하는 마크다운 부분집합만 처리하는
  아주 작은 변환기 (의존성 0, stdlib만).
- **엔진의 생성 계약과 렌더링 예제를 검사**합니다. 사람이 쓰는 설명과
  디자인 판단은 별도 검토가 필요하며, 자동 생성만으로 stale/가독성 문제가
  모두 사라지는 것은 아닙니다.

## 재사용하는 엔진 API

Python 인터랙티브 편집기는 자체 상태 로직을 두지 않고 엔진의
**action / reducer / store**를 그대로 쓴다. UI 이벤트 → `Action` →
`store.dispatch` → 새 `FigureSpec` → `render`/`tex_preview` 로 화면 갱신.

```python
from mudplot import Store, actions as A, tex_preview

store = Store()
store.subscribe(lambda spec, action: rerender(spec))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
```

Rust(Askama+tokio+htmx) editor도 같은 구조를 사용한다. capability 기반
control과 agent JSON 모두 `mudplot apply`를 호출해 Python reducer 의미론을
유지하고 `mudplot render`로 figure를 갱신하거나 export한다.

## 로드맵

1. **(완료)** 정적 문서+갤러리 사이트 (`python -m dashboard build`)
2. **(완료)** Python 로컬 인터랙티브 편집기 (`python -m dashboard serve`)
3. **(v1 필수 기능 완료)** 함께 versioning하는
   `mudplot-editor/` Rust crate — Python CLI를 통해 동일 JSON 계약을
   공유하고 visual control/open/vector export 지원
