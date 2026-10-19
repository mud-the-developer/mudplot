# mudplot 기여 가이드

*[English: CONTRIBUTING.md](CONTRIBUTING.md)*

변경은 작고 재현 가능하며 spec 중심이어야 합니다. `FigureSpec`과 action은
Python API, 대시보드, 저장 JSON, Rust editor가 공유하는 계약입니다.

## 개발 환경

Python 3.10+와 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
git clone https://github.com/mud-the-developer/mudplot.git
cd mudplot
uv sync --locked --extra dev
```

실제 브라우저 에디터 테스트까지 실행하려면:

```bash
uv sync --locked --extra dev --extra browser
uv run playwright install chromium
```

TeX 엔진이 없으면 TeX 의존 테스트는 건너뜁니다. 일반 CI는
Tectonic/pdflatex로 PGF 테스트를 실행하며, nightly/release 매트릭스는
LuaLaTeX, BibTeX, biber까지 검사합니다.

## 필수 CI 경로와 skip 증거

Localoptionaltest는도구가없으면skip할수있지만실행성공은아닙니다. Workflow는skip사유포함
JUnit을보관하고 `scripts/check_required_test_paths.py`로필수case의missing/skip/xfail/failure/
중복을거절합니다. 무관한test통과로필수경로를대체하지않습니다. Report는64MiB/UTF-8(BOM허용)/
NUL·DTD·entity선언금지이며pytestJUnit용이지일반XML/entity처리service가아닙니다.

| Profile | 필수 경로 |
| --- | --- |
| `ci` | 실제browserlegenddrag/nativePGF참조/Tectonic논문compile |
| `minimum` | 격리floor의PGF/Tectonic, browser요구없음 |
| `tex` | pdflatex+BibTeX/LuaLaTeX+BibTeX/LuaLaTeX+biber논문compile |
| `release` | Browser/PGF/Tectonic과전체TeXmatrix |

실제전체browser/reference검사예시이며임의의focusedsubset에적용하는명령은아닙니다.

```bash
uv run pytest -q tests/test_editor_browser.py tests/test_references.py --junitxml=paths.xml
uv run python scripts/check_required_test_paths.py ci paths.xml
```

무관한optional skip은그대로보이고허용합니다. 필수case검사/reportupload는실패뒤에도실행하지만
pytest/job실패를성공으로바꾸지않습니다. Linuxfull은Python3.10/3.12,격리floor는3.10,
RustMSRV1.88/Python3.12bridge는Windows/Linux이며모든OS/minor증명은아닙니다. UVcache접미사는
Python/minimum/Rust·OSlane을분리하고lock입력은명시합니다. Nightly/releasecache는비활성이고
결과artifact는matrix/sourceSHA이름으로release `dist`와분리합니다. JUnitidentity검사는서명된
buildprovenance/악성test방어/전체runtime정확성인증이아닙니다.

## 리뷰 체크리스트와 증거

[2026-10-16 상세 체크리스트](mudplot_review_checklist_detailed_2026-10-16.md)와
[ID/증거 대장](docs/REVIEW_CHECKLIST_STATUS.md)을 함께 사용합니다. 150개는 검증
과제이지 확인된 결함 수가 아닙니다. Batch/listener/JSON/출력 계약을 유지하고,
ID를 닫기 전에 HEAD+로컬 변경·환경·명령·종료 코드·skip·증거를 기록합니다.
부족한 검증은 OPEN으로 두며 과거 대상 통과를 전체 릴리스 gate 통과로 바꾸지 않습니다.

## Pull request 전 확인

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q --ignore=tests/test_editor_browser.py
uv run --python 3.10 --locked --script scripts/check_minimum_versions.py
uv run --locked --script scripts/audit_dependencies.py
uv run python scripts/check_schema_sync.py
uv run python scripts/check_wheel.py
```

브라우저 테스트에는 `browser` marker가 없으므로 파일명으로 선택합니다.
Chromium을 설치했다면 다음도 실행합니다.

```bash
uv run pytest -q tests/test_editor_browser.py
uv run python scripts/editor_smoke_test.py
```

`mudplot-editor/` 변경에는 Rust 1.88+가 필요합니다.

```bash
rustup toolchain install 1.88.0 --profile minimal
cargo +1.88.0 check --locked --all-targets --manifest-path mudplot-editor/Cargo.toml
cargo fmt --check --manifest-path mudplot-editor/Cargo.toml
cargo clippy --locked --all-targets --manifest-path mudplot-editor/Cargo.toml -- -D warnings
cargo test --locked --manifest-path mudplot-editor/Cargo.toml
uv run python scripts/rust_editor_smoke_test.py
# Chromium이 있으면 CSP 아래 실제 htmx swap도 확인합니다.
uv run python scripts/rust_editor_smoke_test.py --browser
```

## Codec·interpreter 집중 검사

```bash
uv run pytest -q tests/test_review_full_spec_fields.py
# 모델 필드를 바꿀 때만 structural fixture를 명시적으로 재생성합니다.
uv run python tests/test_review_full_spec_fields.py
uv run python scripts/check_python_bridge_paths.py
uv run python scripts/check_request_body_limits.py
```

Codec stress fixture는 schema-valid지만 옵션 충돌을 의도해 렌더용이 아닙니다.
등록 예제는 따로 검사합니다. Interpreter probe는 한글/공백 경로의 venv를 만들고
정리하며 같은 NumPy/Matplotlib 버전을 내려받을 수 있습니다. PATH/env/flag 선택을
검사하되 프로젝트 패키지/lock은 바꾸지 않고 recorder의 .pth/module 쌍도 그 venv 안에만
새로 만듭니다. 외부 sitecustomize를 보존하는 self-check로 lookup 우선순위 가정을 피합니다.
CI는 Windows/Linux 양쪽을 구성했지만 로컬 Windows 성공을 미실행 Linux 통과로 세지 않습니다.
Body probe는 로컬 N-1/N/N+1을 순차 실행하고 실제 서버 PID의 RSS/수명 peak만 기록하며
native 렌더 자식은 제외합니다. 부하 테스트나 hard resource 보장은 아닙니다.

Protocol skip이 아니라 실제 optional table 라이브러리를 검사하려면:

```bash
uv run --no-sync --with pyarrow==26.0.0 --with polars==2.0.0 python -m pytest -q tests/test_review_table_formats.py tests/test_review_missing_data.py tests/test_review_sql_ownership.py
```

격리된 테스트 요구사항이며 core 의존성/lock 변경은 아닙니다. 실제 optional 버전을
기록하고 기본/최소 환경의 skip과 구분하세요. CI는 pytest 전에 두 라이브러리를 직접
import하여 부재를 정상 optional 검사 성공으로 오인하지 않도록 합니다.

## 프로젝트 규칙

- 선언적 core는 의존성 0을 유지합니다. spec, action, reducer, store, IO,
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

이 명령은 `docs/PLOT_GALLERY.md`와 등록된 모든 layer의 PNG·편집 가능한
spec도 재생성합니다. Gallery coverage는 `capabilities.LAYER_TYPES`와 정확히
일치해야 합니다. 데모 데이터는 seed를 고정한 합성 데이터여야 합니다.
화면 출력이 의도적으로 바뀐 경우가 아니면 재생성된 바이너리 자산을
커밋하지 않습니다.

입력·공유/비공유evidence·기존계약결정은 [review준비](docs/REVIEW_PREPARATION.md)에
정리했습니다. Syntheticfixture입력과범위있는결과receipt를구분하고raw환경/Temp로그나
미공개연구자료를게시하지마세요. 제한된masking검사가secret-free인증은아닙니다.

## Lock과 격리 build 검사

`uv.lock`은 checkout의 dev 환경을 재현하며 wheel의 선언 의존성 범위로 설치하는 모든
사용자 환경을 제한하지 않습니다. Fresh-install 버전과 build backend/전이 의존성 버전은
근거에서 구분하세요. Backend pin만으로 모든 환경의 byte-identical build를 보장하지 않습니다.

`scripts/check_wheel.py`는 현재 build 환경의 빠른 contents/core 검사입니다. 비어 있는
출력 디렉터리에서 PEP 517 격리도 따로 확인하세요:

```bash
uv build --sdist --out-dir dist-isolated
uv build --wheel dist-isolated/mudplot-1.0.0.tar.gz --out-dir dist-isolated
```

Audit 설치는 별도 `UV_PROJECT_ENVIRONMENT`를 써서 기존 개발 환경을 덮어쓰지 마세요.
Source-tree editor는 matching checkout에서 실행하며 engine wheel 설치가 dashboard/
Rust source asset까지 설치한다는 뜻은 아닙니다.

## Release

`v*` release tag는 annotated tag이며 암호학적으로 서명되고 GitHub에서
verified로 표시되어야 합니다. release workflow는 build 전에 lightweight·
unsigned·unverified tag를 거부합니다. tag를 push하기 전에
`scripts/check_release_version.py vX.Y.Z`를 실행하세요. workflow는 publish할
정확한 artifact를 다시 build·검증합니다.

SSH 서명을 쓸 때는 **public** key만 GitHub signing key로 등록하고(private
key는 절대 upload하지 않음), 이 checkout을 설정한 뒤 push 전에 로컬에서
검증하세요.

```bash
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
git tag -s vX.Y.Z -F /tmp/mudplot-tag-message.txt
git verify-tag vX.Y.Z
git push origin vX.Y.Z
```

GPG 서명도 동일하게 허용됩니다. 로컬 signature가 유효한 것만으로는
release gate를 통과하지 않으므로 GitHub tag가 **Verified**인지도 확인하세요.

아키텍처는 [`DESIGN.md`](DESIGN.md), 우선순위 작업은
[`ROADMAP.md`](ROADMAP.md)를 참고하세요. 패치되지 않은 취약점은 public
issue가 아니라 [`SECURITY.ko.md`](SECURITY.ko.md)의 비공개 경로로 제보하세요.
