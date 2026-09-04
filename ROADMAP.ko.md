# 로드맵

*[English docs: ROADMAP.md](ROADMAP.md)*

앞으로 할 구체적인 다음 단계들을 정리한 작업 목록. 이미 나온 것은
[`CHANGELOG.md`](CHANGELOG.md), 아키텍처/과거 마일스톤(M0–M12)은
[`DESIGN.md`](DESIGN.md) 참고. (신규 로드맵/문서는 기본 영어로 작성하는
관례에 따라, 이 파일은 영어판의 요약본입니다 — 자세한 내용은 항상 영어
`ROADMAP.md`를 확인하세요.)

## 1. 플롯 종류 더 추가 (matplotlib/seaborn 근접, 계속)

현재 21종 지원: line, scatter, bar, errorbar, band, hist, box, violin,
kde, heatmap, contour, contourf, pie, hline, vline, text, annotate,
scatter3d, line3d, surface, wireframe.

다음 후보 (논문에서의 유용성 순):
- **regplot**: scatter + 회귀선(선형/다항, numpy.polyfit) + 신뢰구간
- **stripplot/swarmplot**: 카테고리형 산점도 (seaborn 스타일)
- **stackplot**: 누적 영역 그래프 (다른 레이어와 달리 전체 시리즈를 한
  번에 넘겨야 해서 별도 처리 필요)
- **hist2d/hexbin**: 2변량 밀도/카운트
- **quiver**: 벡터장 화살표 (물리/공학 논문에 흔함)
- **polar**: `projection="polar"` 패널 옵션
- **step**: line 레이어의 drawstyle 옵션으로
- **rug plot**: kde/hist 옆에 관측값 표시하는 작은 눈금

각 추가는 지난 두 배치와 같은 체크리스트를 따름: LayerSpec 필드 →
capabilities.LAYER_TYPES → render.py 구현 → validate.py 검사 →
api.py 빌더 → 테스트 → 스키마/문서 재생성 → 일치성 테스트 확인.

## 2. 대시보드/에디터 완성도

- 에디터의 "Add layer" 폼이 지금 line/scatter/bar 3종만 노출 (엔진은 21종
  지원) — `mp.capabilities()` 기반으로 범용 폼 만들면 향후 신규 타입도
  UI 변경 없이 자동 반영됨
- 멀티패널 레이아웃 조작 (`.layout()`, 패널별 add/remove, projection3d
  토글)
- 파일에서 spec 불러오기 (지금은 내보내기만 있음)
- 패널별 축 라벨/스케일/범위, 범례, 보조축 설정 UI
- 이후 htmx 부분 갱신으로 전환 (진짜 Rust+htmx 에디터 전 연습)

## 3. Rust 인터랙티브 에디터 (M13)

Python 프로토타입이 action/JSON 계약을 충분히 검증할 때까지 미뤄둔
작업. 이제 액션 25종, 레이어 21종이 실전 검증됐으니 착수 가능:
1. 새 크레이트, `serde`로 `schemas/figure_spec.schema.json` 미러링
2. `axum` + `askama`로 `dashboard/editor_server.py`의 라우트 재구현
3. 1단계는 Python `render()`를 subprocess/HTTP로 호출, 2단계(선택)는
   순수 Rust 렌더러로 교체 (스키마가 고정돼 있어 교체 자유로움)
4. htmx로 부분 갱신

## 4. 품질/도구

- mypy/pyright 정적 타입 검사 (아직 안 함 — py.typed는 배포했지만 자체
  타입 정확성은 외부 검증 안 됨)
- hypothesis 기반 속성 테스트 (색상 엔진 왕복, validate/reduce 불변식)
- CONTRIBUTING.md
- DESIGN.md가 길어졌으니 ARCHITECTURE.md로 분리 검토

## 5. 패키징/릴리스

- 실제 PyPI 배포 워크플로 (태그 트리거, trusted publishing)
- 버전 정책 결정 (아직 0.0.1)
- `pyproject.toml`의 `[project.urls]`는 이제 실제 저장소를 가리킴
  (https://github.com/mud-the-developer/mudplot)
