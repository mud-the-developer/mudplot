# mudplot 기여 가이드

*[English: CONTRIBUTING.md](CONTRIBUTING.md)*

변경은 작고 재현 가능하며 spec 중심이어야 합니다. `FigureSpec`과 action은
Python API, 대시보드, 저장 JSON, 미래의 비-Python 클라이언트가 공유하는
계약입니다.

## 개발 환경

Python 3.10+와 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
git clone https://github.com/mud-the-developer/mudplot.git
cd mudplot
uv sync --extra dev
```

실제 브라우저 에디터 테스트까지 실행하려면:

```bash
uv sync --extra dev --extra browser
uv run playwright install chromium
```

TeX 엔진이 없으면 TeX 의존 테스트는 건너뜁니다. 일반 CI는
Tectonic/pdflatex로 PGF 테스트를 실행하며, nightly/release 매트릭스는
LuaLaTeX, BibTeX, biber까지 검사합니다.

## Pull request 전 확인

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q -m "not browser"
uv run python scripts/check_schema_sync.py
```

Chromium을 설치했다면 다음도 실행합니다.

```bash
uv run pytest -q tests/test_editor_browser.py
uv run python scripts/editor_smoke_test.py
```

## 프로젝트 규칙

- 순수 코어는 의존성 0을 유지합니다. spec, action, reducer, store, IO,
  validation, schema 생성, TeX 크기 계산은 NumPy/Matplotlib 없이 import되어야
  합니다. NumPy는 색상 effect, Matplotlib은 렌더 effect에만 둡니다.
- 상태 변경은 action과 `reduce()`를 거칩니다. 대시보드나 fluent API만을 위한
  별도 mutation 경로를 만들지 않습니다.
- 설정된 실제 출력 크기를 기본적으로 보존합니다. 크롭은 `tight=True`로만
  명시합니다.
- 표준 라이브러리, Matplotlib 기본 기능, 기존 프로젝트 패턴을 우선합니다.
  작은 용도 하나를 위해 의존성이나 추상화를 추가하지 않습니다.
- DOI/arXiv/reference 해석은 결정적이고 오프라인이어야 합니다.
- 버그나 비단순 분기에는 집중된 회귀 테스트 하나를 추가합니다. 레지스트리나
  생성 표현이 여러 개면 모듈 간 일치성 테스트를 추가합니다.
- 사용자 동작이 바뀌면 영문·한글 문서를 함께 갱신합니다.
- 사용자에게 보이는 변경은 `CHANGELOG.md`의 **Unreleased**에 기록합니다.

## 스키마와 생성 문서

Spec 필드, action, capability, 저널, 레이어 메타데이터를 바꾸면 체크인된
계약을 다시 생성해야 할 수 있습니다.

```bash
uv run python -m mudplot schema --out schemas/figure_spec.schema.json
uv run python -m mudplot capabilities > schemas/capabilities.json
uv run python -m mudplot docs --out docs/REFERENCE.md
uv run python scripts/check_schema_sync.py
```

생성 파일을 손으로 고치지 않습니다. 마지막 명령은 임시 디렉터리에서 모두
재생성하고 드리프트가 있으면 실패합니다.

## 데모와 대시보드

```bash
uv run python -m scripts.render_docs_demo
uv run python -m dashboard --out /tmp/mudplot-dashboard
uv run python -m dashboard serve
```

데모 데이터는 seed를 고정한 합성 데이터여야 합니다. 화면 출력이 의도적으로
바뀐 경우가 아니면 재생성된 바이너리 자산을 커밋하지 않습니다.

아키텍처는 [`DESIGN.md`](DESIGN.md), 우선순위 작업은
[`ROADMAP.md`](ROADMAP.md)를 참고하세요.
