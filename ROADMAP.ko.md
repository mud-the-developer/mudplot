# 로드맵

*[English docs: ROADMAP.md](ROADMAP.md)*

앞으로 할 구체적인 다음 단계들을 정리한 작업 목록. 이미 나온 것은
[`CHANGELOG.md`](CHANGELOG.md), 아키텍처/과거 마일스톤(M0–M12)은
[`DESIGN.md`](DESIGN.md) 참고. (신규 로드맵/문서는 기본 영어로 작성하는
관례에 따라, 이 파일은 영어판의 요약본입니다 — 자세한 내용은 항상 영어
`ROADMAP.md`를 확인하세요.)

## 1. 플롯 종류 더 추가 (matplotlib/seaborn 근접, 계속)

현재 25종 지원: line, regplot, scatter, stripplot, bar, errorbar, band, stackplot, hist, box, violin,
kde, rug, heatmap, contour, contourf, pie, hline, vline, text, annotate,
scatter3d, line3d, surface, wireframe.

다음 후보 (논문에서의 유용성 순):

- **(완료) regplot**: scatter + 수치 스케일링한 선형/다항 `numpy.polyfit` +
  명시적으로 요청한 평균 fit 정규근사 신뢰구간; SciPy 의존성 없음
- **(완료) stripplot**: 범위 제한·고정 seed의 재현 가능한 수평 jitter,
  grouping, 중복 marker를 지원하는 카테고리/원자료 산점도
- **swarmplot**: 충돌 회피 packing이 실제로 필요할 때 추가; 지금은 복잡하고
  취약한 근사 구현 대신 stripplot 유지
- **(완료) stackplot**: 기존 long-form `x`/`y`/`group`으로 native 누적
  영역 렌더; 모든 그룹의 ordered x 일치·유한값 검증과 흑백용 hatch 적용
- **hist2d/hexbin**: 2변량 밀도/카운트
- **quiver**: 벡터장 화살표 (물리/공학 논문에 흔함)
- **polar**: `projection="polar"` 패널 옵션
- **(완료) step**: 별도 레이어 대신 line의 native Matplotlib `drawstyle`
  (`default`/`steps`/`steps-pre`/`steps-mid`/`steps-post`) 옵션으로 구현
- **(완료) rug**: native Matplotlib 눈금으로 x축 관측값을 표시하는
  kde/hist 동반 레이어; 그룹에는 중복 선 스타일도 적용

각 추가는 지난 두 배치와 같은 체크리스트를 따름: LayerSpec 필드 →
capabilities.LAYER_TYPES → render.py 구현 → validate.py 검사 →
api.py 빌더 → 테스트 → 스키마/문서 재생성 → 일치성 테스트 확인.

## 2. 대시보드/에디터 완성도

- **(완료)** `capabilities.LAYER_TYPES` 기반 범용 advanced 폼으로 등록된
  레이어 25종 모두 노출. `LayerSpec` JSON 필드, 타입별 required/optional
  안내, 오타·필수 필드 검사를 제공하며 향후 registry 항목도 자동 반영
- **(완료)** 멀티패널 격자, 활성 패널 선택, 패널별 add/remove/edit,
  2-D/3-D projection 전환, 선택 패널 범례·제목·주석 드래그
- **(완료)** 저장된 `.mplot.json` 열기. 잘못된 spec은 기존 그림을
  유지하면서 오류 표시
- **(완료)** 패널별 title/reference, x/y 라벨·scale·고정/자동 limits,
  보조 y축 활성화·설정·제거, 3-D z축, projection, 드래그 위치 설정.
  invalid 결과는 editor history에 들어가기 전에 거부
- **(완료)** 전체 페이지 리로드 방식을 htmx 부분 갱신으로 전환
  (`dashboard/static/htmx.min.js`, 0BSD 라이선스로 vendoring, 새 Python
  의존성 없음) — 진짜 Rust+htmx 에디터 전 연습
- **(완료)** 범례·제목·`text`/`annotate` 레이어를 미리보기 위에서 마우스
  드래그 또는 화살표 키로 직접 위치 조정
- **(완료)** 같은 서버 안에서 Editor/Docs 탭 분리 (`/docs`), 정적
  사이트와 동일한 엔진 레퍼런스 렌더러 재사용

## 3. Rust 인터랙티브 에디터 (M13)

Python 프로토타입이 action/JSON 계약을 충분히 검증할 때까지 미뤄둔
작업. 이제 액션 25종, 레이어 25종이 실전 검증됐으니 착수 가능:

1. 새 크레이트, `serde`로 `schemas/figure_spec.schema.json` 미러링
2. `axum` + `askama`로 `dashboard/editor_server.py`의 라우트 재구현
3. 1단계는 Python `render()`를 subprocess/HTTP로 호출, 2단계(선택)는
   순수 Rust 렌더러로 교체 (스키마가 고정돼 있어 교체 자유로움)
4. htmx로 부분 갱신

## 4. 품질/도구

- **(완료)** pyright 정적 타입 검사 — Python 3.10 언어 수준으로
  `mudplot/`, 대시보드, 유지관리 스크립트를 CI에서 검사하며 소비자용
  `py.typed`도 계속 배포
- **(완료)** hypothesis 기반 속성 테스트 -- reduce()의 state/action 불변성,
  citation/href validator, 색상 엔진(convert.py 왕복·8-bit hex 보존,
  distance.py 지표 성질)을 `tests/test_property_based.py`에서 검증
- **(완료)** `CONTRIBUTING.md` / `CONTRIBUTING.ko.md` — 개발 환경,
  PR 전 검사, 브라우저/TeX 선택 설정, 스키마 재생성, 의존성 경계,
  테스트·문서 관례
- DESIGN.md가 길어졌으니 ARCHITECTURE.md로 분리 검토

## 5. 패키징/릴리스

- GitHub 릴리스: 완료 -- `.github/workflows/release.yml`이 태그(`v*`)마다
  sdist/wheel을 빌드해 GitHub Release에 첨부함.
- 실제 PyPI 배포: 의도적으로 보류. PyPI 프로젝트(`mudplot`)에 이 저장소를
  trusted publisher로 등록(workflow `release.yml`, environment `pypi`)하고
  GitHub에도 `pypi` environment를 만든 뒤 `release.yml`에 `publish` job을
  다시 추가할 것 -- 한 번 시도했으나 publisher 미등록으로
  `invalid-publisher` 오류로 실패함.
- 버전 정책: 현재 `0.5.0`. pre-1.0이라도 `FigureSpec`
  호환성을 깨는 변경은 minor 버전을 올림(Rust/에이전트 소비자가 스키마
  안정성에 의존).
- `pyproject.toml`의 `[project.urls]`는 이제 실제 저장소를 가리킴
  (<https://github.com/mud-the-developer/mudplot>)
