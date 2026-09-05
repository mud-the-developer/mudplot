# mudplot-dashboard (별도 패키지)

*[English docs: README.md](README.md)*

`mudplot` **엔진과 분리된** 사람 대면 도구. 엔진(순수 core)에는 UI 의존성이
전혀 없고, 대시보드는 엔진을 단방향으로 임포트한다.

```
dashboard ──▶ mudplot   (단방향 의존)
```

*(이 섹션은 참고용 스냅샷입니다. 새 문서/에디터는 기본적으로 영어로 작성하니,
최신 내용은 영어 README.md를 참고하세요.)*

## 지금 있는 것

### 1. 문서 + 디자인 갤러리 정적 사이트 생성기

```bash
python -m dashboard build --out dashboard/site_build
open dashboard/site_build/index.html
```

### 2. 로컬 인터랙티브 에디터 (프로토타입)

```bash
python -m dashboard serve   # http://127.0.0.1:8765/
```

스타일/팔레트/레이어/사이즈 등을 폼으로 조작하면 미리보기가 즉시 갱신되는
로컬 웹 에디터. 내부적으로 엔진의 Store/reducer를 그대로 재사용하므로
별도 상태가 없음. 폼 제출은 전체 페이지를 다시 불러오지 않고 htmx(0BSD,
`dashboard/static/htmx.min.js`로 vendoring, 새 Python 의존성 없음)로
그 자리에서 갱신됩니다. 상단 네비게이션에 **Editor**/**Docs** 두 탭이 있어,
`Docs`는 `mp.reference_markdown()`을 그 자리에서 렌더링해 별도
`dashboard build` 과정 없이도 엔진과 어긋나지 않습니다. 미리보기 위에서
범례(파란 ✥)·제목(보라 T)·`text`/`annotate` 레이어(초록 •) 핸들을
드래그하거나 클릭 후 화살표 키로 직접 재배치할 수 있습니다. 자세한 설명은
영어 README.md 참고.

- `site.py` — `mudplot.reference_markdown()` / `mudplot.capabilities()` 로
  엔진 레퍼런스를 만들고, 엔진의 렌더러로 디자인 원칙(팔레트 CVD/그레이스케일
  안전성, 이중 인코딩, TeX WYSIWYG, 보조축/heatmap 등)을 보여주는 갤러리
  이미지를 생성해 하나의 HTML로 묶는다.
- `markdown_lite.py` — mudplot이 생성하는 마크다운 부분집합만 처리하는
  아주 작은 변환기 (의존성 0, stdlib만).
- **문서와 그림이 항상 엔진과 일치**한다: 둘 다 라이브 엔진 호출 결과이기
  때문에 손으로 쓴 문서처럼 stale해질 수 없다.

## 재사용하는 엔진 API

인터랙티브 편집기가 생기면(다음 섹션) 자체 상태 로직을 두지 않고, 엔진의
**action / reducer / store**를 그대로 쓴다. UI 이벤트 → `Action` →
`store.dispatch` → 새 `FigureSpec` → `render`/`tex_preview` 로 화면 갱신.

```python
from mudplot import Store, actions as A, tex_preview

store = Store()
store.subscribe(lambda spec, action: rerender(spec))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
```

이 구조는 그대로 미래의 Rust(askama+tokio+htmx) 에디터로 이식된다:
UI가 같은 action(JSON)을 보내고, 동일한 reducer 의미론으로 `FigureSpec`을
갱신한 뒤 재렌더한다.

## 로드맵

1. **(완료)** 정적 문서+갤러리 사이트 (`python -m dashboard build`)
2. **(완료)** Python 프로토타입 인터랙티브 편집기 (`python -m dashboard serve`)
3. Rust(askama+tokio+htmx) 에디터 — 별도 크레이트, 동일 JSON 액션/스키마 계약
