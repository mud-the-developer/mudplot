# 로드맵

*[English docs: ROADMAP.md](ROADMAP.md)*

앞으로 할 구체적인 다음 단계들을 정리한 작업 목록. 이미 나온 것은
[`CHANGELOG.md`](CHANGELOG.md), 아키텍처/과거 마일스톤(M0–M12)은
[`DESIGN.md`](DESIGN.md) 참고. (신규 로드맵/문서는 기본 영어로 작성하는
관례에 따라, 이 파일은 영어판의 요약본입니다 — 자세한 내용은 항상 영어
`ROADMAP.md`를 확인하세요.)

## 현재 목표: v1.1

순서별 배치·검증 체크포인트·릴리스 조건은
[v1.1 개발 진행표](docs/V1_1_PLAN.ko.md)를 따른다. 아직 Unreleased 개발이며,
기록된 검증 전에는 전체 동등성 달성·버전 발행 완료로 표시하지 않는다.

## 0. Version 1 범위

1.x에서는 Matplotlib을 mudplot의 canonical renderer로 유지한다. 현재
`FigureSpec → Matplotlib` 경계는 보존하되 실제 두 번째 renderer가 생기기
전에는 backend 추상화를 추가하지 않는다. Plotly나 Cairo는 reducer·JSON
계약을 바꾸지 않는 선택적 post-1.0 adapter로 추가할 수 있다.

- **(완료)** 등록된 28개 전체 layer의 영문·한글 실행 문서와 CI registry
  drift 검증
- **(완료)** 공개 Python/CLI/schema 표면을 감사하고
  [1.x 호환성 및 deprecation 정책](docs/COMPATIBILITY.ko.md) 문서화
- **Release gate:** 발행 전 locked Python/Rust/browser/full-TeX, clean-wheel,
  packaging, reproducibility 검증을 통과해야 함
- **Release metadata:** Python/editor `1.0.0`, serialized spec `0.1`, signed
  annotated tag 및 검증된 artifact·provenance. PyPI는 trusted publisher 설정이
  필요한 별도 결정으로 유지

## 1. Matplotlib / Seaborn 기능 동등성

현재 checkout은 Unreleased 원자료 통계/swarm/letter-value/ECDF/가중 2변량 KDE를 포함해 37종입니다:
line, lineplot, regplot, scatter, stripplot, swarmplot, bar, barplot, pointplot, countplot,
errorbar, band, stackplot, hist, hist2d, hexbin, quiver, box, boxenplot, violin,
kde, kde2d, ecdf, rug, heatmap, contour, contourf, pie, hline, vline, text, annotate,
scatter3d, line3d, surface, wireframe.
그래프 개수는 기능 동등성을 의미하지 않습니다.

목표는 registry 이름을 늘리는 것이 아니라 Matplotlib·Seaborn의 그래프·통계
사용 범위를 지원하는 것이다. [기능·옵션·통계 비교표](docs/FEATURE_COVERAGE.ko.md)에
부분 지원/미지원, 공식 비교 기준, Python 직접 사용의 한계와 완료 조건을 기록했다.
반환된 Matplotlib Figure를 직접 수정하는 경로는 JSON/editor 지원으로 세지 않는다.

v1.1 배치(기존 `.bar()`의 미리 계산된 값 의미는 유지):

- [x] 원자료 barplot/pointplot/countplot 공통 통계:
      mean/median/sum/min/max/count, SD/평균 SEM/PI/seeded bootstrap CI,
      값·가중치 쌍의 평균/CI, 2단계 단위 bootstrap, count 비율.
      문서화한 이름 기반 계산과 가정만 지원
- [x] 위 통계 레이어의 첫 범주형 범위: 가로 방향, order/hue order,
      dodge/gap, 누적 count와 값 라벨
- [x] 첫 box/violin 범위: 범주/hue 중첩, 순서/방향,
      width/gap/숫자 dodge, native box 요약·violin 대역폭/표시 옵션
- [x] 첫 swarm 범위: 매 draw 화면 좌표의 원형 packing, 실제 layout/DPI,
      양수 log 값축 변환, 과밀 시 행 보존과 명시적 경고
- [x] 첫 letter-value 범위: 셀별 분위수, 이름/정수 깊이,
      exponential/linear/area 폭·중앙값/관측 꼬리와 범주/hue 배치
- [x] 분포 native/log 첫 범위: 숫자 범주 좌표·간격, 양수 log 값,
      명시적 data/axis 통계/KDE·공통 축 검증. 기본값 유지와 새 회귀 테스트 60개.
- [x] Violin 의미 첫 범위: inner 4종/None·두 hue split·width/area/count와
      비교 기준·bw_adjust/cut/clip. 기본값 유지, 새 수치/도형/editor/export 테스트 138개.
- [x] 독립 구성 요소 첫 범위: typed box body/whisker/cap/median/mean/flier·
      boxen body/median/flier. 기본값·native/log 좌표 보존, 엄격한 설정과
      새 artist/editor/export 테스트 48개.
- [x] 통계 native/log 첫 범위: bar/point/count 숫자 간격·log 축,
      명시적 raw/log-fit 추정·양수 log bar baseline, count/기본값 보존과
      미지원 조합 검증, 새 테스트 73개.
- [x] 가중 violin 범위: 상대 공분산/effective n·역 가중 ECDF 표시·질량 폭·
      행 쌍/native log 도형, 새 테스트 78개.
- [ ] 범주형 나머지: 추가 구성 요소와 size/style/date 매핑
- [x] ECDF 첫 범위: 반복값/가중 empirical step·strict 보완형·곡선별
      proportion/percent/count·hue 순서/선·v/h/log 관측 축·typed pure/JSON/
      editor/export 계약, 새 테스트 103개, 구간 추론 없음.
- [x] Histogram 통계 첫 범위: 명시적 공통 bins/가중치·count/frequency/
      비율/percent/density·전체/곡선별 in-range 정규화·누적 질량/v-h/raw log,
      기존 동작 보존과 새 테스트 95개.
- [x] 설정 가능한 가중 단변량 KDE: typed 상대 공분산/effective n·bandwidth/
      cut/clip/grid·공통 질량/grid·해석적 CDF/채우기/v-h/raw 관측 log,
      단일값 skip과 기존 동작 보존, 새 테스트 125개.
- [x] 가중 2변량 KDE 첫 범위: 전체 공분산·raw grid/log 표시·조건부 격자
      HDR/native 등고선/채우기·자동 보정 없음, 새 테스트 129개.
- [x] 숫자 x별 집계선: named 점별 면/막대·가중/x별 unit CI·정렬/raw-log fit,
      원자료 line 유지, 새 테스트66개.
- [x] 독립 scatter 매핑: typed hue/size/style·종류/순서/전체 선형 범위·
      지름→면적/비데이터 guide, 테스트85개.
- [x] 이름 기반 공통 scatter 척도: figure 합집합 범위/색 block·설정 일치·
      중복 없는 행·패널당 pooled guide1회, 테스트36개.
- [x] 독립 lineplot 매핑: 원본tuple곡선/공통범위·main stroke두께points/
      marker-dash·기존 점별 추론 유지,48개 테스트. 승인한 foreground 재검증
      전체2159/최소1703, Rust1.99/브라우저/TeX 통과.
- [x] Histogram 그룹 배치: 명시적 layer/stack/dodge·가중 높이/정규화 유지,
      원자료 폭·빈 hue 자리 보존과 계산 도형 검사. 새 테스트 48개와
      Python/Rust editor 연동 검증.
- [x] Histogram step: layer/stack의 빈 native stairs 윤곽선·가중 높이/경계·
      hue 선 모양 자리·v/h/raw-log 배치 보존. 새 테스트 43개와 pure/JSON/
      계약·Python/Rust editor 연동 검증.
- [x] 자동 facet 첫 범위: terminal row/col·wrap/빈 셀·panel filter·공통 축/
      semantic domain·셀별 통계와 Python/action/JSON/editor 경로·실행 예제.
      [지원 범위](docs/FACETS.ko.md) 참고.
- [x] Raw group facet: line/scatter/bar/errorbar/band/stripplot/regplot/rug의
      hue/style/dodge 자리와 원래 궤적/값/오차·빈 셀을 유지합니다.
- [ ] 관계·분포: facet 조합 확장/넓은 line 추론,
      추가 histogram/KDE 표현과 semantic 설정
- [x] Joint histogram 첫 범위: raw scatter/regplot과 같은 관측 쌍의 x/y histogram,
      완전 관측 선택과 density/측정값 축 분리. [범위/예제](docs/JOINT_GRID.ko.md).
- [x] Numeric pair matrix 첫 범위: 쌍별 scatter·대각선 histogram·raw group과
      이름 기반 값축 공유로 대각선 density 단위를 분리합니다. [범위](docs/PAIR_GRID.ko.md).
- [x] 설정형 KDE grid: Joint 주변 분포/pair 대각선의 bandwidth/grid/support/
      정규화/fill을 KDESpec으로 재사용. Histogram 기본값 유지, density만 지원하며
      특이 곡선은 경고/skip합니다. 가중/CDF grid는 남아 있습니다.
- [ ] 자동 구성 나머지: live facet mapping/통합 범례·추가 pair/joint kind
- [x] Typed heatmap 첫 범위: mask·원자료 주석/label·linear/log/중심/robust
      색상 범위·정사각 셀·경계. [범위](docs/HEATMAP.ko.md) 참고.
- [x] 설정형 회귀 첫 범위: residual/log-x/Huber/binomial-logit/LOWESS·선택 raw
      group과 optional statsmodels effect extra. [범위](docs/REGRESSION.ko.md) 참고.
- [x] 계층 clustermap: 행/열 트리·제공 linkage/optimal leaf·metadata/색 strip·
      z-score/min-max. [범위](docs/CLUSTERMAP.ko.md) 참고.
- [ ] 추가 heatmap/clustering 설정·가중/bootstrap/advanced 회귀 추론·residual 진단/설정
- [ ] 나머지 Matplotlib 유형과 축·레이아웃·색상·주석 옵션.
      앞 단계를 돕는 작은 primitive는 먼저 추가할 수 있음

체크한 항목은 Unreleased의 구현 범위이며, 미체크 항목은 계획이지 구현된
builder나 완료일 약속이 아니다. 세부 상태와 남은 릴리스 조건은
[v1.1 진행표](docs/V1_1_PLAN.ko.md)를 따른다. capabilities, JSON/action
왕복, renderer/editor 경로, 통계/artist 테스트, 실제 예제가 함께 갖춰져야 완료다.
의존성 없는 core와 기존 version 하한은 유지한다. 고급 통계 의존성이 필요하면
명시적인 optional effect 계층에 두며 필수 core 의존성으로 추가하지 않는다.

아래 완료 항목은 문서화된 기본 범위의 구현이며 **upstream 전체 옵션·통계와
동등하다는 의미가 아니다**.

- **(완료) regplot**: scatter + 수치 스케일링한 선형/다항 `numpy.polyfit` +
  명시적으로 요청한 평균 fit 정규근사 신뢰구간; SciPy 의존성 없음
- **(완료) stripplot**: 범위 제한·고정 seed의 재현 가능한 수평 jitter,
  grouping, 중복 marker를 지원하는 카테고리/원자료 산점도
- **(첫 범위 완료) swarmplot**: 매 draw의 원형 화면 좌표 packing,
  순서/hue 중첩/방향·양수 log 값축. DPI/layout/limits/크기가 바뀌면 다시 배치하고
  과밀 시 행을 보존하며 경고. 최적 배치 보장은 아니고 숫자 native/log 범주는
  지원하지만
  추가 매핑은 아직 미지원
- **(완료) stackplot**: 기존 long-form `x`/`y`/`group`으로 native 누적
  영역 렌더; 모든 그룹의 ordered x 일치·유한값 검증과 흑백용 hatch 적용
- **(완료) hist2d/hexbin**: 유한 numeric x/y의 native 직사각/육각
  카운트 맵; 기존 LCH colormap·colorbar·y2·layout 경로 재사용,
  bin/grid/count 설정 검증
- **(완료) 2-D quiver**: numeric x/y + u/v, data-coordinate 화살표,
  magnitude 색상/colorbar, y2, scale/width 보정 지원. 3-D u/v/w는 보류
- **(완료) polar**: `projection="polar"`/`.projection_polar()`에서 native
  line/scatter/bar 지원; 그 외 레이어와 y2는 명확히 거부
- **(완료) step**: 별도 레이어 대신 line의 native Matplotlib `drawstyle`
  (`default`/`steps`/`steps-pre`/`steps-mid`/`steps-post`) 옵션으로 구현
- **(완료) rug**: native Matplotlib 눈금으로 x축 관측값을 표시하는
  kde/hist 동반 레이어; 그룹에는 중복 선 스타일도 적용

각 추가는 지난 두 배치와 같은 체크리스트를 따름: LayerSpec 필드 →
capabilities.LAYER_TYPES →_render.py 구현 → validate.py 검사 →
api.py 빌더 → 테스트 → 스키마/문서 재생성 → 일치성 테스트 확인.

## 2. 대시보드/에디터 완성도

- **(완료)** 등록된 모든 layer에 실제 PNG·복사 가능한 source·편집 가능한
  JSON을 갖춘 영문·한글 실행 갤러리 항목을 추가하고,
  `capabilities.LAYER_TYPES`와 정확히 일치하는지 CI에서 검증
- **(완료)** `capabilities.LAYER_TYPES` 기반 범용 advanced 폼으로 등록된
  레이어 28종 모두 노출. `LayerSpec` JSON 필드, 타입별 required/optional
  안내, 오타·필수 필드 검사를 제공하며 향후 registry 항목도 자동 반영
- **(완료)** 멀티패널 격자, 활성 패널 선택, 패널별 add/remove/edit,
  Cartesian/polar/3-D projection 전환, 선택 패널 범례·제목·주석 드래그
- **(완료)** 저장된 `.mplot.json` 열기. 잘못된 spec은 기존 그림을
  유지하면서 오류 표시
- **(완료)** 패널별 title/reference, x/y 라벨·scale·고정/자동 limits,
  보조 y축 활성화·설정·제거, 3-D z축, projection, 드래그 위치 설정.
  prospective 결과는 검증·렌더에 성공해야 editor history에 commit
- **(완료)** 전체 페이지 리로드 방식을 htmx 부분 갱신으로 전환
  (`dashboard/static/htmx.min.js`, 0BSD 라이선스로 vendoring, 새 Python
  의존성 없음) — 진짜 Rust+htmx 에디터 전 연습
- **(완료)** 범례·제목·`text`/`annotate` 레이어를 미리보기 위에서 마우스
  드래그 또는 화살표 키로 직접 위치 조정
- **(완료)** 같은 서버 안에서 Editor/Docs 탭 분리 (`/docs`), 정적
  사이트와 동일한 엔진 레퍼런스 렌더러 재사용

## 3. Rust 인터랙티브 에디터 (M13)

**Version 1 로컬 editor 필수 기능 완료** — Python과 함께 versioning하는
`mudplot-editor/` crate:

- serde가 versioned `FigureSpec`·action envelope를 보존하고 생성
  schema/reference를 계약으로 사용
- axum + Askama로 PNG/PDF/SVG/JSON output, 공용 vendored htmx, JSON
  `/action`, visual control, 전체 layer capability metadata, spec open,
  undo/redo/reset 제공
- 새 dependency-free-core `mudplot apply`와 기존 `mudplot render` subprocess를 호출해
  28개 layer의 reducer/validator/renderer 의미를 Rust에 복제하지 않음
- 인증 없는 로컬 단일 session이며 non-loopback bind/HTTP Host와
  cross-origin browser mutation을 거부

로컬 실사용이 정당화한 뒤에만 Python editor의 특수 axis/drag control,
원격 사용용 cookie session/auth를 추가. native Rust renderer와 전체 schema
강타입화는 Rust가 reduction/rendering을 맡을 때만 검토.

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
- **(완료)** capability 기반 column 계약 — 잘못됐거나 지원하지 않는
  column 필드를 렌더 전에 거부하고 groupable/routable 집합을 계약 테스트로 고정
- **Deep-copy 성능 경계**: 문서화하고 측정함. 내부 fluent/batch dispatch는
  쓰이지 않는 반환 snapshot을 더 만들지 않지만, reducer action마다 mutable
  spec 전체를 복사하고 undo/redo는 history를 재생함. 실제 대형 inline-data
  workload profiling에서 필요성이 확인될 때만 structural sharing 또는 replay
  checkpoint를 추가할 것.
- **(보류)** DESIGN.md 분리 — 현재 목차로 충분하며 탐색/리뷰 비용이 실제로
  커질 때 audit 이력을 CHANGELOG.md로 이동. 파일 분리 자체는 사용자 가치가 없음

## 5. 패키징/릴리스

- GitHub 릴리스: 완료 -- `.github/workflows/release.yml`이 tag/Python/
  pyproject/Rust manifest+lock/changelog/README version 일치를 확인하고 locked
  dependency로 Python+Rust+전체 TeX-engine preflight 후 sdist/wheel,
  SHA-256 checksum, OIDC build-provenance attestation을 태그(`v*`)마다
  GitHub Release에 첨부함.
- 실제 PyPI 배포: 의도적으로 보류. PyPI 프로젝트(`mudplot`)에 이 저장소를
  trusted publisher로 등록(workflow `release.yml`, environment `pypi`)하고
  GitHub에도 `pypi` environment를 만든 뒤 `release.yml`에 `publish` job을
  다시 추가할 것 -- 한 번 시도했으나 publisher 미등록으로
  `invalid-publisher` 오류로 실패함.
- 버전 정책: package/editor `1.0.0`, 독립된 spec `0.1`.
  additive feature는 minor release, 공개 Python/CLI/JSON breaking change는
  사전 deprecation과 major release가 필요함.
  [호환성 정책](docs/COMPATIBILITY.ko.md) 참고.
- `pyproject.toml`의 `[project.urls]`는 이제 실제 저장소를 가리킴
  (<https://github.com/mud-the-developer/mudplot>)
