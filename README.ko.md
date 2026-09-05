# mudplot

*[English docs: README.md](README.md)*

논문용 그래프를 위한 Python 플롯 라이브러리. Matplotlib 위에서
**지각적으로 균일하고(perceptually uniform), 적녹 색맹 안전한(colorblind-safe)**
색상 팔레트와 스타일을 제공합니다.

핵심은 **LCH(CIELAB 극좌표) 기반 색상 엔진**입니다.

- **같은 명도(L\* 고정)** → 흑백 인쇄/명암에서 공정
- **최대 대조** → 색상 간 지각 색차(CIEDE2000)의 최솟값을 최대화
- **색맹 고려** → 일반 시각 + protanopia/deuteranopia 시뮬레이션의 최악 대조를
  최적화(`Palette.report()`로 직접 측정한 값이며, 인증된 접근성 기준은 아님);
  아래 [검증된 명칭 팔레트](docs/DEMO.md#4-colour-palette-presets-measured-not-assumed)
  참고
- **흑백 인쇄 안전** → 그룹화된 bar/box/violin 도 기본적으로 해칭 패턴을 함께
  사용해, 색상이 비슷해져도 막대이 구별됩니다 —
  [흑백 인쇄 데모](docs/DEMO.md#5-grouped-bar-chart-readable-after-black--white-printing)
  참고

## 아키텍처: Spec 중심 + 순수 reducer (functional core / imperative shell)

그림의 모든 상태를 **직렬화 가능한 선언적 `FigureSpec`** 으로 표현하고,
상태 전이는 **순수 reducer**로만 수행한다. effect(render/io/preview)는
가장자리로 분리.

```
 Action (순수 데이터)
     │
     ▼  reduce(state, action) -> state'      ─┐ functional core (순수)
 FigureSpec (dataclass ⇆ JSON, .mplot.json) ─┘
     │
     ▼  render / io / preview                ── imperative shell (effect)
 matplotlib → PNG/PDF/SVG
```

- fluent 빌더는 **action을 dispatch하는 설탕** — `Store`가 reducer 구동.
- `mudplot/` 엔진은 UI 의존 없음. `dashboard/`는 별도 패키지(추후).
- Python과 미래 Rust GUI가 오직 같은 action/JSON 스키마로 소통.

## 상태

초기 개발 중. 아키텍처/과거 마일스톤은 [`DESIGN.md`](DESIGN.md), 출시된 것은
[`CHANGELOG.md`](CHANGELOG.md), 구상법 다음 단계는 [`ROADMAP.md`](ROADMAP.md) 참고.

- [x] 색 변환 엔진 (sRGB ↔ linear ↔ XYZ ↔ Lab ↔ LCH), numpy 전용
- [x] 색차 (CIE76, CIEDE2000) — Sharma 2005 검증값 통과
- [x] 색맹 시뮬레이션 (Machado 2009)
- [x] 팔레트 생성기 (qualitative / sequential / diverging) + preview
- [x] 선언적 Spec 모델 + JSON 왕복 + 렌더러 + fluent 빌더
- [x] 순수 reducer + action + store (effect 분리)
- [x] TeX-aware WYSIWYG 미리보기 (article/ieee/revtex/nature/acm)
- [x] 레이어 확장: line/scatter/bar/errorbar/band/hline/vline/text/annotate + 멀티패널
- [x] 순수 코러 의존성 0 (numpy/matplotlib은 effect 전용 extras)
- [x] ruff lint 규칙 + CI 준비
- [x] 다양한 입력 형식 (dict/records/DataFrame/numpy/pyarrow/SQL)
- [x] AI 에이전트 친화 인터페이스 (capabilities/json_schema/apply/action_log)
- [x] 안정성 하드닝 패스: 실제 버그 10건 발견/수정 + 회귀 테스트 잠금
      (저널 크기 미적용, 패널레이블 폰트 불일치, TeX 미리보기 크기 2배 부풀림,
      SetData의 matrices 삭제, 문자열 리스트 글자 조각화, O(n^2) 성능/팔레트
      중복색, Store 상태 오염, CLI traceback, y2축 라우팅 불일치, 겹치는
      grouped bar) — 자세한 내용은 `DESIGN.md` §4c2, `tests/test_bugfixes.py`
- [x] 레이어 추가: histogram/boxplot/heatmap, 연속값 컬러매핑 scatter+colorbar
- [x] 논문용 마무리: suptitle, 패널 자동 레이블(a/b/c), width/height ratios
- [x] 렌더 커버리지: 보조 y축(twin), 공유축(sharex/sharey), despine(spine offset), 외부 범례
- [x] 디자인 품질: 색상+마커+선스타일 이중 인코딩, 팔레트 lightness_jitter로 그레이스케일 안전성, `Palette.report()`
- [x] 순수 spec 검증(`validate`/`assert_valid`) + 렌더링 전 자동 검증
- [x] `Store.undo()`/`redo()`
- [x] CLI (`python -m mudplot capabilities|schema|docs|validate|render`)
- [x] JSON 스키마/능력/문서 export 파일 + CI 동기화 검증 (`schemas/`, `docs/`)
- [x] 사람용 dashboard: 엔진 자기소개 기반 문서 + 디자인 갤러리 정적 사이트 (`python -m dashboard`)
- [ ] Rust 인터랙티브 에디터 (별도 크레이트, 추후)

## 설치

```bash
# 순수 엔진만 (의존성 0) — spec/actions/reducer/store/io/tex 크기 계산
pip install mudplot

# 색상 엔진 + 렌더링까지 (numpy + matplotlib)
pip install "mudplot[render]"
```

개발:

```bash
uv venv && uv pip install -e ".[dev]"
```

### 의존성 계층

| 계층 | 모듈 | 의존성 |
|---|---|---|
| 순수 엔진 | `spec` `actions` `reducer` `store` `io` `tex`(크기) | **없음** |
| 색상 엔진 | `color/*` | numpy |
| 렌더 effect | `render` `tex_preview` | numpy + matplotlib |

## 실제 렌더링 데모

![pandas 합성 데이터를 mudplot으로 렌더링한 line, scatter, violin, KDE figure](docs/images/pandas_demo.png)

`python -m scripts.render_docs_demo`로 생성한 실제 출력입니다.
고정 난수 시드의 **합성 데이터**이며 실험 결과가 아닙니다.
**[데모 갤러리](docs/DEMO.md)**에서 수정 전후 이미지, heatmap·3D,
PDF·편집 가능한 JSON과 실행·검증 방법을 확인할 수 있습니다.
데모에는 `mudplot[render]` 외에 pandas가 필요합니다.

## 사용 예

### 직관적 fluent 빌더

```python
import mudplot as mp

(mp.plot(data)                        # 아래 어느 형식이든 가능
    .line(x="voltage", y="current", group="order")
    .labels(x="Voltage (mV)", y="Current (μA)")
    .legend(title="Order")
    .theme("paper").journal("nature")
    .palette("qualitative", hue_start=30)
    .save("fig.pdf"))
```

`save()`는 지정한 figure 크기를 유지합니다. 내용에 맞게 잘라내려면
`save("fig.pdf", tight=True)`를 사용하세요. 반환된 Matplotlib figure는 열린
상태이므로 사용 후 `plt.close(fig)`로 닫습니다. `Plot.spec`과 `Store.state`는
독립적인 스냅샷입니다. 직접 변경하지 말고 빌더 메서드나 action으로 수정하세요.

### 지원하는 플롯 종류

기본(line/scatter/bar/errorbar/band), 분포(hist/box/violin/kde),
2D 필드(heatmap/contour/contourf), 3D(scatter3d/line3d/surface/wireframe),
주석(hline/vline/text/annotate), pie. 항상 최신 목록은 `mp.capabilities()`
또는 영어 README.md의 표를 참고. (신규 기능 문서는 기본 영어로 작성)

### Spec 저장/불러오기 (미래 Rust 에디터와 동일 포맷)

```python
p = mp.plot(data).line("x", "y")
json_text = p.to_json()               # .mplot.json
p2 = mp.Plot.from_json(json_text)     # 무손실 왕복
fig = p2.render()
```

### TeX WYSIWYG 미리보기

```python
# 논문 컴럼폭·폰트에 맞춘 실제 크기 미리보기 (모의 본문 컬럼 + 캐션)
fig = (mp.plot(data).line("voltage", "current", group="order")
         .labels(x="Voltage (mV)", y="Current")
         .preview(tex="ieee", caption="Figure 1. ..."))
```

### AI 에이전트용 (JSON만으로 전체 조작)

엔진은 기계 친화적으로 설계돼 있어, 에이전트가 탐색→생성→렌더를 전부
텍스트/JSON으로 할 수 있다 (사람이 보는 쪽은 `dashboard/`):

```python
import mudplot as mp

caps = mp.capabilities()   # 레이어/테마/저널/TeX프리셋/액션 어휘 (기계 가독)
schema = mp.json_schema()  # FigureSpec 전체 JSON Schema

spec = mp.apply([          # JSON 액션만으로 그림 구성 (순수 reduce)
    {"type": "SetData", "columns": {"x": [1, 2, 3], "y": [1, 4, 9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetAxisLabel", "axis": "x", "text": "X"},
    {"type": "SetTheme", "name": "paper"},
])
issues = mp.validate(spec)  # 렌더링 전 자가 검증 (순수, 에이전트 피드백용)
mp.save(spec, "fig.pdf")   # effect (내부에서 assert_valid 자동 호출)

# 빌드 이력(replay/undo)
p = mp.plot(data).line("x", "y").theme("paper")
log = p.action_log         # [{"type": "SetData", ...}, ...]
assert mp.apply(log).to_dict() == p.spec.to_dict()   # 재현 가능
```

### CLI (에이전트/셸 자동화용)

```bash
python -m mudplot capabilities                    # 엔진 능력 JSON 출력
python -m mudplot schema --out s.json              # FigureSpec JSON Schema 저장
python -m mudplot validate fig.mplot.json          # 저장된 spec 검증
python -m mudplot render fig.mplot.json out.pdf    # 렌더
```

### 순수 reducer / store 직접 사용

```python
from mudplot import Store, actions as A

store = Store()
store.subscribe(lambda spec, action: print("changed:", type(action).__name__))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
spec = store.state          # 순수하게 누적된 상태
```

### 지원하는 입력 데이터 형식

`mp.plot(data)`는 다음을 모두 자동 인식 (순수 코러라 numpy/pandas를
직접 import하지 않고 덕 타이핑으로 처리):

```python
mp.plot({"x": [1, 2], "y": [3, 4]})          # 열 딕셔너리
mp.plot([{"x": 1, "y": 3}, {"x": 2, "y": 4}]) # 레코드(list[dict])
mp.plot([[1, 3], [2, 4]])                     # 2차원 행 -> c0, c1 자동 명명
mp.plot(df)                                   # pandas / polars DataFrame
mp.plot(np_structured_array)                  # numpy 구조화 배열
mp.plot(np_2d_array)                          # numpy 2차원 -> c0, c1 ...
mp.plot(arrow_table)                          # pyarrow Table
mp.plot(cursor)                               # 실행된 DB-API 커서
mp.plot(conn, query="SELECT x, y FROM t")     # DB-API 연결 + 쿼리 (sqlite 등)
```

### 팔레트 직접 사용

```python
pal = mp.color_palette(5, "qualitative")   # 등명도·최대대조
print(pal.hex, pal.min_delta_e())
print(pal.report())      # {'cvd_safe': True, 'grayscale_safe': ..., 'note': ...}
cmap = mp.color_palette(256, "sequential").to_cmap()

# 이름 붙은 검증된 팔레트(명시된 카테고리 수까지 적색맹·녹색맹·진짜 흑백에서
# 안전함을 측정함; mp.capabilities()["palette_presets"] 참고):
pal = mp.color_palette(6, "qualitative", preset="paper")   # 또는 "vivid" / "soft"
p = mp.plot(data).line("x", "y", group="g").palette(preset="paper")

# bar/box/violin 도 기본적으로 그룹마다 해칭 패턴을 함께 사용해(ThemeSpec.hatches),
# 색상 개수와 상관없이 흑백 인쇄에서도 그룹이 구별됩니다.
p2 = mp.plot(data).bar("category", "value", group="g")  # 색상 + 해칭
p3 = p2.encoding(redundant_encoding=False)               # 색상만
```

### 대시보드 (사람이 보는 문서 + 디자인 갤러리)

엔진과 도입 `dashboard/`는 별도 패키지다 (엔진 → 대시보드 단방향 의존).
대시보드는 엔진의 `capabilities()`/`reference_markdown()`과 렌더러를 그대로
재사용해 **문서와 실제 그림이 항상 엔진과 일쉱되는** 정적 사이트만다.

```bash
python -m dashboard --out dashboard/site_build
# dashboard/site_build/index.html 열기 → 엔진 능력 마크다운 문서 + 디자인 갤러리(팔레트 안전성,
# 이중 인코딩, TeX 미리보기, 보조축, 히트랫 둥)
```

## 개발

```bash
uv run pytest        # 또는 .venv/bin/python -m pytest
```
