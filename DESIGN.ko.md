# mudplot — 설계 문서

*[English docs: DESIGN.md](DESIGN.md)*

논문용 그래프를 위한 파이썬 플롯 라이브러리. Matplotlib 위에 얹혀서
**지각적으로 균일하고(perceptually uniform), 색맹 안전한(colorblind-safe)**
색상 팔레트와 논문용 스타일을 제공한다.

## 0. 목표 / 차별점

- seaborn / SciencePlots 처럼 "예쁜 논문 그림"을 쉽게 그린다.
- 차별점 = **LCH(CIELAB 극좌표) 기반 색상 생성 엔진**
  - 같은 명도(L 고정) → 흑백 인쇄/명암 대비에서 공정
  - 색상각(H)을 균등 분포 → 최대 대조
  - 적녹 색맹(protanopia/deuteranopia/tritanopia) 시뮬레이션으로 검증·최적화
- SciencePlots처럼 정적 mplstyle 파일도 제공하되,
  팔레트는 **N개 요청 시 동적으로 생성**한다.

## 1. 의존성 정책

- 색 변환/색맹 시뮬레이션은 **numpy로 직접 구현** (검증 가능성 + 최소 의존성).
- 런타임 의존성: `numpy`, `matplotlib` 만.

## 2. 색상 이론 (구현 파이프라인)

```
sRGB (0..1)
  ⇄ gamma decode/encode        (convert.py)
linear sRGB
  ⇄ 3x3 matrix (D65)
CIE XYZ
  ⇄ f(t) / f^-1(t)             (D65 white point)
CIELAB (L*, a*, b*)
  ⇄ 극좌표                      C = sqrt(a^2+b^2), H = atan2(b,a)
CIELCh (L, C, H)
```

- 참조 백색점: **D65** (2° observer).
- 거리 척도: 초기엔 **CIEDE2000**(ΔE00)으로 지각 색차 계산 (distance.py).
- 색맹 시뮬레이션: **Machado, Oliveira & Fernandes (2009)** 3x3 행렬
  (severity 0~1 보간). protan/deutan/tritan 지원 (cvd.py).

## 3. 팔레트 종류

1. **Qualitative (범주형)**: 등명도 L, 등채도 C, H 균등 분포.
   - N개 요청 → 후보 hue를 많이 뽑고, ΔE00(정상시 + 색맹 시뮬레이션)
     최소값을 최대화하도록 hue 오프셋/부분집합 최적화.
   - gamut 밖이면 C를 줄여서 clip.
2. **Sequential (순차형)**: 하나의 H 근처에서 L을 단조 변화(+C 조정).
   - 지각적 균일(밝기 등간격) 보장.
3. **Diverging (발산형)**: 두 H를 양끝, 가운데 중립(저채도) 명도 피크.
4. **Cyclic (주기형)**: 위상 등 순환 데이터용(옵션, 후순위).

## 4. 핵심 아키텍처: Spec 중심 (선언적·직렬화 가능)

두 요구사항 — (a) 직관적 API, (b) 미래의 Rust(askama+tokio+htmx)
인터랙티브 편집/저장 — 은 하나의 결정으로 수렴한다:

> **그림의 모든 상태를 JSON/TOML로 직렬화 가능한 선언적 `FigureSpec`으로
> 표현하고, 이를 유일한 단일 소스(single source of truth)로 삼는다.**

```
   [ Python 빌더 API ]                    [ Rust 웹 에디터 (미래) ]
   mp.plot(df).line(...)                  askama 폼 + htmx
         │  (생성/수정)                          │ (편집)
         ▼                                        ▼
   ┌─────────────────────────────────────────────────────┐
   │   FigureSpec  (dataclass ⇆ JSON/TOML, 언어 중립)      │  ← 저장 파일 = .mplot.json
   └─────────────────────────────────────────────────────┘
         │  (렌더)                                 │ (렌더 요청)
         ▼                                        ▼
   matplotlib 백엔드                        Python 렌더러 재사용
   → PNG/PDF/SVG                            → htmx로 이미지 스왑
```

- Spec은 **plain data**만 담는다(로직 X). enum은 문자열, 색은 hex/파라미터.
- 렌더러(`render.py`)는 Spec을 받아 matplotlib Figure를 만드는 순수 함수.
- 빌더 API(`api.py`)는 Spec을 **직관적으로 조립**하는 fluent 레이어일 뿐,
  내부적으로는 항상 Spec을 갱신한다 → GUI에서 편집하든 코드로 짜든 동일.
- 저장 포맷 `.mplot.json` (+선택적 데이터 인라인/참조). Rust는 이 스키마만
  알면 되고, 초기엔 렌더링을 Python 프로세스에 위임(subprocess/HTTP).

## 4b. 상태 관리: 순수 reducer + effect 분리 (functional core / imperative shell)

Spec을 단순히 변이(mutate)하지 않고, **상태 전이를 순수 함수로**
모델링한다 (Elm/Redux 스타일). 이것이 미래 Rust 에디터와도 그대로 맞는다:
에디터는 action을 보내고, 동일한 reducer가 새 상태를 만들고, effect가
그린다.

```
   Action (순수 데이터)                State (FigureSpec)
        │                                    │
        ▼                                    ▼
   reduce(state, action) -> state'   ...  순수 함수 (입력 불변, 부수효과 없음)
        │
        ▼  (새 상태)
   ── 여기까지 functional core (순수) ─────────────────────────
   ── 이 아래부터 imperative shell (effect) ───────────────────
        │
        ▼
   Effects:  render (matplotlib) · io (파일) · preview (화면/PNG)
```

- `actions.py` — action 정의 (frozen dataclass 태그드 유니온). 예:
  `AddLayer`, `SetAxisLabel`, `SetTheme`, `SetPalette`, `SetLimits` …
- `reducer.py` — `reduce(spec, action) -> FigureSpec`. **입력 spec 불변**,
  새 spec 반환. matplotlib/파일 접근 없음.
- `store.py` — imperative shell 드라이버. 상태 보관 + `dispatch(action)` +
  구독(subscribe). 대시보드/에디터가 재사용.
- effect(`render`, `io`, `preview`)는 가장자리에만 존재.
- `api.py`의 fluent 빌더는 **action을 dispatch하는 설탕**일 뿐 —
  코드로 짜든 GUI로 편집하든 같은 reducer를 거친다.

### 대시보드 ↔ 엔진 분리 (기계 친화 vs 사람 친화)

- `mudplot/` = **순수 엔진, 기계(AI 에이전트) 친화**. 모든 것을 JSON/
  액션으로 조작하고 자기 기술(self-describing)한다. 다른 UI에 비의존.
- `dashboard/` = **별도 패키지, 사람 친화 UI**. 엔진의 store/reducer/
  action을 그대로 임포트. 추후 Rust(askama+tokio+htmx) 에디터로 대체.
- 의존 방향: dashboard → mudplot (단방향).

### 에이전트 친화 인터페이스 (기계가 쉽게 쓰도록)

AI 에이전트는 텍스트/JSON이 자연스러운 매체이므로, 엔진은 다음 4가지를
제공한다 (모두 순수·의존성 0):

1. **능력 탐색**: `mp.capabilities()` → 레이어 종류+필드, 테마/저널/
   TeX 프리셋/팔레트 종류, 액션 어휘 전체를 기계 가독 dict로 반환.
2. **스키마**: `mp.json_schema()` → `FigureSpec` 전체의 JSON Schema
   (검증/폼 생성/에이전트 플래닝용).
3. **JSON 액션으로 빌드**: `mp.apply([{"type":"AddLayer", ...}, ...])`
   → 수수한 reduce로 `FigureSpec` 생성. `action_from_dict/to_dict` 왕복.
4. **액션 이력**: `Store.history` / `Plot.action_log` → 어떻게 만들었는지
   재현·재생(replay) 가능, undo 지원.

```python
caps = mp.capabilities()          # "뭐를 할 수 있나?"
schema = mp.json_schema()         # "구조가 어떻게 생겼나?"
spec = mp.apply([                 # JSON만으로 전체 구성
    {"type": "SetData", "columns": {"x": [1,2,3], "y": [1,4,9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetTheme", "name": "paper"},
])
mp.save(spec, "fig.pdf")          # effect

## 4c. TeX-aware 미리보기

논문은 TeX로 쓰고 그에 맞춰 그림을 배치하므로, 미리보기는
**최종 문서에서 보이는 실제 크기·폰트**로 보여야 한다 (WYSIWYG).

- `TexContext`: 문서클래스의 `\textwidth`, `\columnwidth`(pt), 본문
  폰트크기, 단 수. 프리셋: `article`, `ieee`, `revtex`, `nature`.
- 그림을 컬럼폭×fraction의 정확한 inch 크기로 렌더하고, 그림 내
  폰트를 본문 폰트크기에 맞춘다 (pt → inch = 1/72.27).
- 미리보기는 그림을 **모의 본문 컬럼 안**에 배치하고 캡션을 붙여
  문서 맥락에서의 상대 크기감을 보여준다.

## 4c2. 안정성 감사 (2025-09 하드닝 패스)

기능 추가보다 **버그·의도 이탈 발견/수정**에 집중한 감사 패스에서 발견한
실제 버그 9건 (전부 회귀 테스트로 잠금, `tests/test_bugfixes.py`):

1. **`.journal("ieee")`가 그림 크기를 바꾸지 않음** — `render()`가 항상
   `figsize=`를 명시적으로 넘겨서 저널 프리셋의 rcParams `figure.figsize`가
   죽은 코드였음. 저널 사이즈를 `theme.JOURNAL_SIZES`로 spec에 직접 반영.
2. **패널 자동 레이블(a/b/c) 폰트가 저널 오버라이드를 무시** — 렌더 중
   활성 rcParams(`plt.rcParams["axes.titlesize"]`)를 읽도록 수정.
3. **TeX `full_width=True` 미리보기가 실제 크기의 2배 이상으로 부풀려짐**
   — `fig_w`를 잘못 재계산하던 걸 실제 렌더 크기(`sized.size[0]`)로 교체.
4. **`SetData`가 이전에 등록한 `matrices`를 조용히 삭제** — `DataSpec`을
   통째로 교체하는 대신 `columns`만 갱신하도록 수정.
5. **문자열 리스트가 글자 단위로 조각남** — `to_columns(["apple","banana"])`
   가 각 문자를 별도 "행"으로 오인(문자열도 `__len__`을 가짐). str/bytes를
   행 감지에서 명시적으로 제외.
6. **`qualitative()` 팔레트의 `min_delta_e` 계산이 순수 Python 이중 루프라
   n=1000에서 사실상 멈춤** — 완전 벡터화. 동시에 `n > n_candidates`일 때
   중복 색이 조용히 생기던 것도 명확한 에러로 변경.
7. **`Store(spec)`가 전달받은 spec을 방어적으로 복사하지 않아 외부 변이가
   내부 상태로 누수** — "순수 상태" 설계 원칙 위반. 생성 시 deepcopy.
8. **CLI가 파일없음/JSON 파싱 오류에서 원시 traceback을 그대로 출력** —
   에이전트/셸 스크립트가 파싱하기 좋은 한 줄 stderr 에러로 정리.
9. **`hline`/`vline`/`text`/`annotate`가 `axis="y2"`를 무시하고 항상 주축에
   그려짐** (다른 레이어는 이미 보조축 라우팅을 지원) — 일관되게 라우팅.
   반대로 `heatmap`/`hist`/`box`처럼 실제로 라우팅을 지원하지 않는 타입에
   `axis="y2"`를 주면 `validate()`가 명확히 거부하도록 함.
10. **grouped bar 차트가 같은 x 위치에 겹쳐 그려짐** (짧은 막대가 완전히
    가려짐 — 데이터 왜곡 위험) — 그룹 수에 따라 자동으로 나란히 배치(dodge).

### 후속 감사 ("지금 어떤 plot을 지원하는지" 질문에 답하면서 발견)

11. **`capabilities()`가 실제 기능을 과소 보고**: `bar`/`errorbar`/`band`/
    `hline`/`vline`/`text`/`annotate` 모두 `axis="y2"` 라우팅을 실제로
    지원하는데, `LAYER_TYPES`에는 `line`/`scatter`만 `axis` 필드가 있다고
    나와있었음. 자세한 내용은 영어 DESIGN.md §4c2 참고.
12. **카테고리형 x축 값이 모든 시리즈 레이어에서 크래시함**: `_col()`이
    무조건 `dtype=float`로 강제 변환해서, bar 차트에 `["control",
    "treatment"]` 같은 문자열 카테고리를 쓰면 (매우 흔한 사용 사례) 깨졌음.
    문자열 x 컬럼을 0..n-1 위치로 매핑하고 원래 문자열을 눈금 라벨로 쓰도록
    수정.
13. **`mp.render`/`mp.save` lazy 속성이 프로세스에서 첫 호출 후 깨짐**:
    PEP 562 `__getattr__`가 서브모듈을 import하는 부수효과로 자기 자신의
    슬롯을 서브모듈 객체로 덮어써서, 두 번째 호출부터 "'module' object is
    not callable" 에러가 났음. 202개 테스트가 통과했음에도 못 잡힌 이유는
    거의 모든 테스트가 내부 함수를 직접 import해서 썼기 때문. 관련된 모든
    lazy 항목을 한 번에 고정하도록 수정.

추가로 방어적 검증 강화: `validate()`에 데이터 컬럼 길이 불일치, 행렬
비정방형(jagged), 빈 패널, 잘못된 spine 문자, alpha 범위, `at`/`to` 길이
체크 추가. `SetColorbar`/`SetEncoding`/`SetFont`/`SetAxesStyle`/`SetGridStyle`/
`SetTicksStyle`/`SetPalette` 액션에 범위 밖 인덱스·미지 필드에 대한 명확한
`ValueError`를 추가(이전엔 원시 `IndexError`/`TypeError` 또는 조용한 무시).

## 4d. 자가 검증 (validate) — 렌더 전에 에이전트에게 명확한 피드백

`mudplot/validate.py`는 순수 함수 `validate(spec) -> list[str]`로, 존재하지
않는 컬럼 참조·잘못된 레이어 타입·layout 불일치 등을 미리 잡아 사람이 읽을
수 있는 문장으로 반환한다. `render()`는 그리기 전에 이를 호출해
`KeyError` 같은 불친절한 예외 대신 `ValueError`로 전체 문제 목록을 준다.
에이전트는 `mp.validate(spec)`으로 렌더 전에 스스로 점검할 수 있다.

## 4e. CLI — 셸/에이전트 자동화 진입점

`python -m mudplot {capabilities,schema,validate,render}`. `capabilities`/
`schema`/`validate`는 순수 코어만 필요, `render`만 `[render]` extra 필요.
`schemas/figure_spec.schema.json`, `schemas/capabilities.json`은 CLI로 생성한
정적 파일이며, CI에서 항상 최신 생성 결과와 diff해 드리프트를 막는다
(Rust 쪽이 신뢰할 수 있는 단일 스키마 소스).

## 4f. 확장된 플롯 지원 (3D, 분포, 2D 필드, 파이)

matplotlib/seaborn급 범위에 가까워지도록 3D(`scatter3d`/`line3d`/`surface`/
`wireframe`), 분포(`violin`/`kde`), 2D 필드(`contour`/`contourf`), `pie`를
추가했다. 3D는 패널에 `projection="3d"`를 설정하면 되고, 2D 패널과 한
그림에 섞어 쓸 수 있다. `kde`는 scipy 없이 numpy로 직접 구현한 가우시안
커널 밀도 추정이다. 자세한 아키텍처 설명은 영어 DESIGN.md §4f 참고.

## 5. 직관적 API 원칙

seaborn(`style="whitegrid"` 문자열)·matplotlib(`rcParams['axes.linewidth']`
점표기 문자열)의 비직관성을 제거한다.

- **구조화·타입화된 테마**: 문자열 키 대신 그룹화된 속성.
  ```python
  theme = mp.Theme.paper()
  theme.font.size = 10          # not rcParams['font.size']
  theme.axes.spines = "LB"      # 왼/아래만 (left, bottom)
  theme.grid.show = True
  theme.ticks.direction = "in"
  theme.palette.kind = "qualitative"   # 팔레트도 테마 일부
  ```
- **fluent 빌더**: 메서드 이름이 곧 의미. 각 호출은 Spec을 수정할 뿐.
  ```python
  (mp.plot(df)
      .line(x="voltage", y="current", group="order")
      .labels(x="Voltage (mV)", y="Current (μA)")
      .theme("paper").journal("nature")
      .save("fig.pdf"))
  ```
- **발견 가능성**: 모든 옵션은 dataclass 필드 → IDE 자동완성/문서/JSON 스키마로
  그대로 노출. Rust 폼도 같은 스키마에서 자동 생성 가능.
- **합리적 기본값**: 논문 프리셋(paper/nature/ieee)만 골라도 바로 쓸 만하게.

## 6. 모듈 구조

```
mudplot/                 # 순수 엔진 (UI 의존 없음)
  __init__.py            # 공개 API 노출
  color/                 # 색상 엔진
    convert.py distance.py cvd.py palette.py preview.py
  spec.py                # FigureSpec 등 직렬화 가능한 dataclass 모델 (state)
  actions.py             # Action 정의 (frozen dataclass 유니온)
  reducer.py             # reduce(state, action) -> state (순수)
  store.py               # imperative shell 드라이버 (dispatch/subscribe)
  theme.py               # ThemeSpec 프리셋 & rcParams 매핑
  render.py              # effect: Spec -> matplotlib Figure
  tex.py                 # TeX-aware 크기/미리보기 (effect)
  io.py                  # effect: spec <-> json (.mplot.json)
  api.py                 # fluent 빌더 (action dispatch 설탕)
dashboard/               # 별도 패키지: 인터랙티브 UI (추후)
tests/
  test_convert.py test_distance_cvd.py test_palette.py
  test_spec_roundtrip.py test_render.py test_reducer.py test_tex.py
```

## 7. Rust 인터랙티브 에디터 로드맵 (미래)

- 저장 포맷 `.mplot.json`을 Rust `serde`로 역직렬화 (동일 스키마).
- askama 템플릿으로 Spec 필드 → HTML 폼 렌더. htmx로 필드 변경 시
  부분 POST → 서버가 Spec 갱신 → 재렌더 이미지 조각만 교체.
- 렌더링: 1단계는 Python 렌더러를 tokio에서 subprocess/HTTP로 호출.
  2단계(선택)는 순수 Rust 렌더러(plotters 등)로 대체 가능하나, 스키마가
  고정돼 있으므로 백엔드 교체가 자유롭다.
- **핵심**: Python과 Rust가 오직 `FigureSpec` JSON 스키마로만 소통.

## 8. 개발 순서 (마일스톤)

- [x] M0: 환경/스캐폴드
- [x] M1: 색 변환 + 테스트
- [x] M2: 색차 + 색맹 시뮬레이션
- [x] M3: qualitative 팔레트
- [x] M4: sequential / diverging + cmap
- [x] M5: Spec 모델 + JSON 왕복 + 렌더러 + fluent 빌더
- [x] M6: 순수 reducer + action + store (functional core / imperative shell)
- [x] M6b: Theme 프리셋 + TeX-aware WYSIWYG 미리보기
- [x] M7: 레이어 확장(line/scatter/bar/errorbar/band/hline/vline/text/
      annotate) + 멀티패널 레이아웃
- [x] M7b: 순수 코러 의존성 0 분리 + ruff lint
- [x] M8: JSON 스키마/능력 export (`schemas/`) + CI 동기화 검증 (Rust 대비)
- [x] M8b: 순수 spec 검증(`validate`/`assert_valid`), 렌더 전 자동 호출
- [x] M8c: CLI (`python -m mudplot capabilities|schema|validate|render`)
- [x] M8d: 레이어 확장(hist/box), suptitle, 패널 자동 레이블, width/height ratios
- [x] M8e: `Store.undo()`/`redo()`
- [x] M9: 렌더 커버리지 확대 — heatmap, 연속값 컬러매핑 scatter+colorbar,
      보조 y축(twin), 공유축(sharex/sharey), despine(spine offset), 외부 범례
- [x] M9b: 디자인 품질 — 색상+마커+선스타일 이중 인코딩(`theme.redundant_encoding`),
      팔레트 `lightness_jitter`로 그레이스케일 안전성 확보, `Palette.report()`
- [x] M10: 문서 자동 생성 — `mudplot.docs` (capabilities/schema 재사용,
      `docs/REFERENCE.md`, CI 동기화 검증) + `python -m mudplot docs`
- [x] M11: 사람용 dashboard (별도 패키지) — 엔진 자기소개 기반 문서+디자인
      갤러리 정적 사이트 생성기 (`python -m dashboard`)
- [x] M11b: 안정성 하드닝 #1 — 실제 버그 10건 발견/수정, 크로스모듈
      일관성 테스트 추가
- [x] M11c: 로컬 인터랙티브 에디터 프로토타입 (`python -m dashboard
      serve`), fluent API와 동일한 Store/action/reducer 사용
- [x] M11d: 안정성 하드닝 #2 — 버그 3건 추가 발견/수정
- [x] M12: 매트플롯립/seaborn 수준 레이어 확장 — 3D
      (`scatter3d`/`line3d`/`surface`/`wireframe`), `violin`, `kde`,
      `contour`/`contourf`, `pie` (총 21개 레이어 타입); 버그 2건 추가
      발견/수정
- [x] M12b: 안정성 하드닝 #3 — 범주형 좌표가 레이어·보조축·공유패널
      간에 서로 달랐던 문제, 그룹화된 연속값 scatter가 독립적인 색상
      정규화를 사용하던 문제, 3D 패널이 축 스케일·범위·범례·레이블을
      무시하던 문제, `Store`가 반환값/이력/리스너를 통해 가변 상태를
      유출하던 문제, `save()`가 지정 크기를 무시하고 자동 크롭하던 등
      실제 버그 7건 발견/수정; 축/기하 검증 강화;
      `tests/test_stabilization.py`에 회귀 테스트 추가
- [x] M12c: 이름 붙은 검증된 qualitative 팔레트 프리셋 3종
      (`paper`/`vivid`/`soft`) — 각각 명시된 카테고리 수까지 CVD·진짜 흑백
      안전을 직접 측정; bar/box/violin도 기본적으로 그룹마다 해칭 패턴을
      함께 사용해 흑백 인쇄에서도 구별됨. `docs/DEMO.md` §4/§5에 실제
      픽셀 변환 기반 흑백 인쇄 증거 이미지 수록
- [x] **v0.1.0 릴리스** (첫 태그 릴리스)
- [x] M12d: TeX 1단/2단 컬럼 크기 지정(`Plot.tex_size()`); matplotlib
      자체 constrained-layout 엔진과 텍스트 측정 렌더러를 이용한 겹침
      방지 레이아웃 패스(`_autofit`) -- 넘치는 제목/suptitle 자동
      줄바꿈, 이름 붙은 "outside ..." 범례를 위한 캔버스 여백 확보,
      직접 만든 레이아웃 시스템 없음, 잘릴 우려가 없으면 아무 변화도
      없음. 범례/제목/주석을 정확한 위치에 고정하는
      `LegendSpec.bbox_to_anchor`/`PanelSpec.title_position`/
      `SetLayerAt`. 대시보드 에디터에는 htmx 부분 갱신(vendoring,
      0BSD, 새 Python 의존성 없음), 미리보기 위에서 마우스/화살표 키로
      범례·제목·주석을 직접 드래그하는 핸들, 시각적 리디자인, 한
      서버 안의 Editor/Docs 탭을 추가. `tests/test_layout.py`,
      `tests/test_dashboard_editor.py` 참고.
- [ ] M13: Rust askama+tokio+htmx 에디터 (별도 크레이트)

## 9. 검증 기준

- 변환: 왕복 오차 < 1e-6, 문헌값 일치.
- 팔레트: 정상시 + protan/deutan ΔE00 최소값 리포트.
- **Spec: build → to_json → from_json → 동일 Spec (왕복 무손실)**.
- **Spec → render 결정성: 같은 Spec은 같은 그림.**
- 시각 회귀: 갤러리 이미지.
