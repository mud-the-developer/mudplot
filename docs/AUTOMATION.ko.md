# FigureSpec, CLI와 로컬 편집기

`FigureSpec` **0.1**은 공통 저장 포맷입니다. 오래된 파일을 편집하기 전에 원본을 보관하세요. [호환성 정책](COMPATIBILITY.ko.md), [JSON 스키마](../schemas/figure_spec.schema.json), [엔진 레퍼런스(영어)](REFERENCE.md)를 참고하세요.

## Spec 저장/불러오기 (Rust editor와 동일한 포맷)

```python
p = mp.plot(data).line("x", "y")
json_text = p.to_json()               # .mplot.json
p2 = mp.Plot.from_json(json_text)     # 무손실 왕복
fig = p2.render()
```

## JSON 기능 조회와 action

엔진은 기계 친화적으로 설계돼 있어, 에이전트가 탐색→생성→렌더를 전부
텍스트/JSON으로 할 수 있다 (사람이 보는 쪽은 `dashboard/`):

```python
import mudplot as mp

caps = mp.capabilities()   # 레이어/테마/저널/TeX프리셋/액션 어휘 (기계 가독)
schema = mp.json_schema()  # FigureSpec 전체 JSON Schema

spec = mp.apply([          # render/I/O effect 없이 JSON action으로 구성
    {"type": "SetData", "columns": {"x": [1, 2, 3], "y": [1, 4, 9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetAxisLabel", "axis": "x", "text": "X"},
    {"type": "SetTheme", "name": "paper"},
])
issues = mp.validate(spec)  # 부수효과 없는 렌더 전 에이전트 피드백
mp.save(spec, "fig.pdf")   # effect (내부에서 assert_valid 자동 호출)

# 빌드 이력(replay/undo)
p = mp.plot(data).line("x", "y").theme("paper")
log = p.action_log         # [{"type": "SetData", ...}, ...]
assert mp.apply(log).to_dict() == p.spec.to_dict()   # 재현 가능
```

## CLI (에이전트/셸 자동화용)

```bash
python -m mudplot capabilities                    # 엔진 능력 JSON 출력
python -m mudplot schema --out s.json              # FigureSpec JSON Schema 저장
python -m mudplot validate fig.mplot.json          # 저장된 spec 검증
python -m mudplot render fig.mplot.json out.pdf    # suffix에 따라 PNG/PDF/SVG/PGF 렌더
python -m mudplot apply fig.mplot.json action.json -o next.mplot.json
```

## Reducer / store 직접 사용

```python
from mudplot import Store, actions as A

store = Store()
store.subscribe(lambda spec, action: print("changed:", type(action).__name__))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
spec = store.state          # 방어적 snapshot; 변경은 action으로
```

## 지원하는 입력 데이터 형식

`mp.plot(data)`는 다음을 모두 자동 인식 (의존성 없는 core는 numpy/pandas를
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
mp.plot(conn, query="SELECT x, y FROM t WHERE run = ?", params=(run_id,))
                                              # 매개변수화 DB-API 쿼리(sqlite)
```

입력 adapter는 일반적인 결측 sentinel(`NaN`, `pd.NA`, `NaT`)을 JSON
`null`로, date/time 값을 ISO 8601 문자열로, NumPy scalar를 일반 Python
값으로 정규화합니다. 무한대와 지원하지 않는 객체는 조용히 바꾸지 않고
엄격한 JSON 검증에서 계속 거부합니다. 열 이름은 문자열 변환 후에도
고유해야 하며, 충돌은 덮어쓰지 않고 거부합니다.

## 대시보드 (사람이 보는 문서 + 디자인 갤러리)

엔진과는 별도인 `dashboard/` 패키지다 (`dashboard → engine` 단방향 의존).
대시보드는 엔진의 `capabilities()`/`reference_markdown()`과 렌더러를 그대로
재사용해 **문서와 실제 그림이 항상 엔진과 일치하는** 정적 사이트를 만든다.

```bash
python -m dashboard --out dashboard/site_build
# dashboard/site_build/index.html 열기 → 엔진 능력 마크다운 문서 + 디자인 갤러리
```

## Rust editor

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

Python action/reducer 의미를 복제하지 않고 같은 계약을 호출한다. 인증 없는
서버는 non-loopback bind/HTTP Host와 cross-origin browser mutation을
거부한다.
범위와 route는
[`mudplot-editor/README.ko.md`](../mudplot-editor/README.ko.md) 참고.


대시보드는 같은 버전의 checkout에서 실행하세요. `python -m dashboard serve`로 루프백 편집기를 시작한 뒤 **Editor → Start from a sample → Complete figure drafts**를 선택하면 자동 적용 없이 Open 양식만 채웁니다. 열기·내보내기, 키보드 핸들, 보안 범위는 [대시보드 안내](../dashboard/README.ko.md)를 참고하세요.
