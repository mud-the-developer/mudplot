# mudplot v0.3.0 개선 제안 및 참고 GitHub Repository 정리

> 검토 기준: `mud-the-developer/mudplot` main branch, v0.3.0 (2026-09-06)  
> 목적: mudplot을 **LaTeX-native scientific plotting framework**로 발전시키기 위한 단기 버그픽스, API/Schema 개선, 장기 차별화 아이디어와 참고 구현 정리

---

## 1. 한눈에 보는 결론

mudplot v0.3.0의 방향은 상당히 좋다. 특히 다음 세 가지가 프로젝트의 정체성을 만들기 시작했다.

1. **FigureSpec 중심의 declarative architecture**
2. **논문 column width를 고려한 TeX-aware rendering**
3. **PGF를 통한 bibliography-aware citation / hyperlink**

이 중 세 번째는 SciencePlots나 일반적인 Matplotlib wrapper와 차별화하기 좋은 기능이다. 따라서 다음 개발의 우선순위는 plot type을 더 늘리는 것보다 **reference system을 안정화하고, FigureSpec의 장기 호환성을 정리하고, TeX/renderer contract를 명확히 하는 것**이 좋다.

가장 먼저 처리할 항목은 아래 네 가지다.

- **P0-1. grouped series별 citation/href 지원**
- **P0-2. citation/href validation 재설계**
- **P0-3. citation text measurement와 최종 LaTeX layout 불일치 해결**
- **P1-1. `ReferenceSpec`으로 citation/href metadata 구조화**

그 다음으로 schema migration, backend capability contract, TeX engine test matrix를 갖추면 pre-1.0 프로젝트로서 상당히 단단해질 수 있다.

---

# 2. 현재 v0.3.0에서 특히 좋은 부분

## 2.1 LaTeX-native reference 처리

현재 구조는 reference를 raster image에 bake하지 않고:

- PNG/PDF: plain text
- SVG: clickable `href`
- PGF: `\figcite{...}` / `\href{...}{...}`

로 backend별 처리한다.

특히 `\cite`가 아니라 `\figcite`를 출력하고, 실제 논문 preamble에서 이를 `\cite`, `\citep`, `\autocite` 등으로 정의하게 한 것은 좋은 abstraction이다.

```latex
\providecommand{\figcite}[1]{\cite{#1}}
```

이 구조는 figure와 bibliography numbering을 동일한 LaTeX document context에서 해결할 수 있게 해준다.

## 2.2 FigureSpec / reducer 중심 architecture

Figure state를 serializable한 `FigureSpec` 하나로 관리하고 rendering/editor를 side effect layer로 분리한 것은 향후 다음 기능에 특히 유리하다.

- Rust GUI
- agent editing
- undo/redo
- reproducible figures
- schema migration
- remote/editor integration
- deterministic tests

따라서 향후 기능을 추가할 때도 **Matplotlib object를 public state로 노출하기보다 FigureSpec semantics를 확장하는 방향**을 유지하는 것이 좋다.

## 2.3 실제 browser / TeX integration test를 넣기 시작한 점

Playwright 기반 editor test와 PGF compile test가 들어간 것은 매우 좋은 방향이다. plotting library는 unit test만으로는 다음 문제를 잡기 어렵다.

- legend clipping
- font metric 변화
- browser focus / drag interaction
- TeX escaping
- backend별 export 차이
- 실제 bibliography resolution

향후에도 “bug가 발견되면 renderer bug뿐 아니라 test-suite bug이기도 하다”는 원칙을 유지하는 것이 좋다.

---

# 3. P0 — 바로 개선하는 것이 좋은 항목

## P0-1. Grouped series별 reference 지원

### 현재 문제

현재 `_series_masks()`는 `group is None`인 경우에만:

```python
_decorate(layer.label, layer.citation, layer.href)
```

를 호출한다.

반면 grouped layer는:

```python
for key in _unique_stable(g):
    yield (str(key), g == key)
```

처럼 group key를 그대로 legend label로 사용한다.

따라서 아래처럼 scientific plotting에서 매우 일반적인 코드에서는:

```python
p.line(
    "snr",
    "bler",
    group="method",
)
```

`RANSAC`, `J-Linkage`, `PEARL`, `Proposed` 각각에 다른 citation을 붙일 방법이 없다.

SVG의 `_link_legend_texts()` 역시 `layer.label -> layer.href` mapping을 사용하므로 같은 구조적 제약이 있다.

### 권장 API

가장 단순한 방식:

```python
p.line(
    "snr",
    "bler",
    group="method",
    references={
        "RANSAC": mp.ReferenceSpec(
            citation="fischler_1981",
            href="https://doi.org/...",
        ),
        "J-Linkage": mp.ReferenceSpec(
            citation="toldo_2008",
        ),
        "PEARL": mp.ReferenceSpec(
            citation="isack_2011",
        ),
    },
)
```

또는 group column 자체에 mapping을 거는 방식:

```python
p.references(
    "method",
    {
        "RANSAC": mp.ref(citation="fischler_1981"),
        "J-Linkage": mp.ref(citation="toldo_2008"),
    },
)
```

### 추천

첫 번째 방식을 추천한다.

이유:

- reference가 실제 legend를 생성하는 layer에 귀속된다.
- 서로 다른 layer가 같은 group column을 다른 의미로 쓸 가능성을 처리하기 쉽다.
- serialization이 명확하다.
- renderer가 layer 단위로 완결된 정보를 가진다.

### 필수 regression tests

- grouped line + 각 group별 citation
- grouped scatter + 각 group별 href
- grouped bar + citation
- citation 없는 group과 있는 group 혼합
- 동일 label이 여러 layer에 있을 때 충돌 여부
- group order 변경 후 reference mapping 유지
- JSON round-trip 후 동일 output

---

## P0-2. citation / href validation 재설계

### 현재 문제

현재 validation은 다음 문자를 모두 금지한다.

```python
_TEX_UNSAFE = set("{}\\%$#&~^_\n\r")
```

이 방식은 arbitrary TeX injection을 막으려는 의도는 좋지만 실제 scientific workflow에서는 과도하게 제한적이다.

예를 들어 다음은 정상적인 BibTeX key일 수 있다.

```text
han_v2v_2019
deepmimo_v3
smith:2025_ai
```

하지만 `_` 때문에 reject된다.

URL은 문제가 더 크다.

```text
https://example.org/paper_v2?x=1&format=pdf#section_2
```

에는 `_`, `&`, `#` 등이 들어갈 수 있다.

### 개선 방향

`citation`과 `href`를 같은 validator로 처리하지 말고 **타입별 validation/escaping**을 적용한다.

#### citation

citation은 “LaTeX source”가 아니라 “bibliography identifier”로 취급한다.

- control character 금지
- brace / backslash 등 실제 macro injection 위험 문자 금지
- underscore, colon, dash 등 일반 key에서 쓰일 수 있는 문자 허용
- 가능하면 raw LaTeX를 허용하지 않음

예시:

```python
def validate_citation_key(key: str) -> None:
    # raw TeX command나 brace injection만 차단
    ...
```

정확한 BibTeX key grammar 전체를 직접 재구현하기보다는 **mudplot이 허용하는 안전한 subset을 문서화**하는 것도 좋은 방법이다.

#### href

URL은 `urllib.parse` 등을 이용해 URI 구조를 확인한 뒤 TeX export 단계에서 별도 escaping을 수행하는 편이 낫다.

예:

```python
def tex_escape_href(url: str) -> str:
    ...
```

중요한 원칙은:

> 정상적인 URL을 validator에서 삭제/금지하는 방식보다, output backend가 올바르게 escape하도록 만든다.

### 보안 원칙

다음은 계속 유지하는 것이 좋다.

- `citation`/`href` 필드에서 arbitrary raw LaTeX 금지
- raw macro를 넣고 싶은 사용자를 위해 `unsafe_tex=` 같은 escape hatch를 쉽게 추가하지 않기
- renderer가 생성하는 macro structure는 mudplot이 소유
- 사용자 입력은 macro argument의 data로만 취급

---

## P0-3. citation placeholder와 실제 LaTeX layout 불일치

### 현재 구조

PGF export 전에 Matplotlib이 text layout을 계산할 때 실제 citation 대신 짧은 sentinel을 넣는다.

이는 긴 URL 자체를 placeholder로 넣어 axes가 collapse하는 문제를 피하기 위한 좋은 선택이다.

하지만 최종 논문에서:

```latex
\figcite{foo}
```

를 어떻게 정의하느냐에 따라 실제 폭은 크게 달라질 수 있다.

예를 들어 numeric citation:

```text
RANSAC [12]
```

은 현재 placeholder와 비슷한 폭일 수 있다.

하지만 author-year style:

```text
RANSAC (Fischler and Bolles, 1981)
```

은 훨씬 길다.

### 문제

Matplotlib은 짧은 sentinel을 기준으로 legend/title layout을 계산했는데, 최종 TeX는 긴 문자열을 렌더링한다.

결과적으로:

- legend overflow
- axes 침범
- outside legend clipping
- title wrap 변화

가 생길 수 있다.

### 단기 권장안

v0.3.x에서는 guarantee 범위를 명확하게 정의한다.

> Exact WYSIWYG layout is guaranteed for compact/numeric figure citations.  
> Author-year/custom citation macros may require a conservative measurement placeholder.

그리고 옵션 제공:

```python
p.reference_style(
    measurement="numeric",
    placeholder="[99]",
)
```

또는:

```python
p.reference_style(
    citation_measure_text="(Author et al., 2026)"
)
```

### 중장기 권장안

TeX-native two-pass measurement를 선택적으로 제공할 수 있다.

1. temporary PGF/TeX compile
2. 실제 text bbox 측정
3. layout 재계산
4. final PGF emit

다만 이 방식은 속도와 dependency cost가 커지므로 기본 동작으로 만들 필요는 없다.

---

## P0-4. SVG reference도 grouped legend semantics에 맞추기

현재 SVG link는 layer label을 기반으로 legend text와 URL을 매칭한다.

향후 `ReferenceSpec`과 grouped reference가 들어가면:

```text
Rendered legend entry
        ↓
semantic series identity
        ↓
ReferenceSpec
```

형태로 연결해야 한다.

즉 문자열 label을 key로 역추적하는 방식은 피하는 것이 좋다.

가능하면 artist 생성 시점에 reference metadata를 artist/text object에 attach한 뒤 SVG backend 처리에서 읽는 구조가 더 안전하다.

---

# 4. P1 — API / Schema 구조 개선

## P1-1. `ReferenceSpec` 도입

현재는:

```python
LayerSpec.citation
LayerSpec.href

PanelSpec.title_citation
PanelSpec.title_href
```

가 각각 존재한다.

이 구조를 계속 확장하면 이후:

```text
suptitle_citation
suptitle_href
annotation_citation
annotation_href
axis_label_citation
axis_label_href
legend_title_citation
legend_title_href
```

처럼 필드가 폭발한다.

### 제안

```python
@dataclass
class ReferenceSpec(SpecBase):
    citation: str | None = None
    href: str | None = None
```

그 뒤:

```python
@dataclass
class LayerSpec:
    ...
    reference: ReferenceSpec | None = None

@dataclass
class PanelSpec:
    ...
    title_reference: ReferenceSpec | None = None
```

향후 필요하면:

```python
ReferenceSpec(
    citation="...",
    href="...",
    # optional future fields
    doi="...",
    arxiv="...",
)
```

로 확장할 수도 있다.

다만 `doi`와 `arxiv`를 바로 넣기보다는 URL resolver가 필요해질 때 추가하는 것이 좋다.

---

## P1-2. FigureSpec schema versioning / migration contract

현재 package는 v0.3.0이지만:

```python
SPEC_VERSION = "0.1"
```

이다.

package version과 spec version이 반드시 같을 필요는 없다. 오히려 독립적인 것이 맞다.

문제는 앞으로 Rust editor, saved `.mplot.json`, agent workflow가 생기면 **spec compatibility가 public contract**가 된다는 점이다.

### 권장 구조

```python
SPEC_VERSION = "1.0"
```

같이 무조건 올릴 필요는 없지만, 최소한 다음 정책은 지금 정해야 한다.

```text
Package version: mudplot implementation release
Spec version: serialized FigureSpec compatibility contract
```

그리고 migration registry:

```python
MIGRATIONS = {
    "0.1": migrate_01_to_02,
    "0.2": migrate_02_to_03,
}
```

API:

```python
spec = mp.load("old.mplot.json", migrate=True)
```

CLI:

```bash
mudplot migrate old.mplot.json -o new.mplot.json
```

### 참고할 방향

Vega-Lite / Altair의 핵심 장점 중 하나는 declarative schema가 중심 contract라는 점이다.

mudplot은 훨씬 작은 프로젝트이므로 동일한 복잡도를 가져올 필요는 없지만:

- JSON Schema
- version field
- deterministic serialization
- migration tests
- unknown-field policy

정도는 pre-1.0에서 정리해 두는 것이 좋다.

---

## P1-3. backend capability contract 명시

현재 reference semantics는 이미 backend마다 다르다.

이를 implicit renderer logic으로만 두지 말고 capability로 노출하면 agent/editor가 훨씬 쓰기 좋아진다.

예:

```python
mp.capabilities()["backends"]["pgf"]
```

결과:

```json
{
  "citations": true,
  "hyperlinks": true,
  "vector": true,
  "latex_native": true,
  "requires_tex": true
}
```

SVG:

```json
{
  "citations": false,
  "hyperlinks": true,
  "vector": true,
  "latex_native": false
}
```

PDF:

```json
{
  "citations": false,
  "hyperlinks": false,
  "vector": true
}
```

이를 이용하면 editor에서도:

> Citation is preserved only in PGF export.

같은 warning을 정확하게 보여줄 수 있다.

---

## P1-4. docs / source-of-truth sync 강화

현재 CHANGELOG에서는 색상 관련 표현을 `colourblind-safe`에서 보다 조심스러운 표현으로 완화했다고 설명하지만 README 상단에는 여전히 강한 표현이 남아 있는 부분이 있다.

이런 drift는 프로젝트가 커질수록 자주 생긴다.

### 권장

가능한 정보는 한 곳에서 생성한다.

- supported plot types → `capabilities()`
- journal presets → registry
- backend capabilities → registry
- palette verified category counts → test-backed metadata
- spec version → `SPEC_VERSION`

그리고 CI에서 README/documentation의 generated section이 최신인지 확인한다.

이미 `docs.reference_markdown()` 방식이 있으므로 이 철학을 더 밀어붙이는 것이 좋다.

---

## P1-5. TeX engine / bibliography engine test matrix

현재 Tectonic 기반 실제 compile test가 생긴 것은 매우 좋다.

다음 단계에서는 optional CI matrix를 고려할 수 있다.

### 최소 matrix

- pdflatex
- lualatex
- xelatex
- tectonic

bibliography는:

- BibTeX
- biber/biblatex

전부 매 commit에 돌릴 필요는 없다.

예:

```text
PR:
  - Tectonic smoke test

nightly/release:
  - pdflatex + BibTeX
  - LuaLaTeX + BibTeX
  - LuaLaTeX + biblatex/biber
```

이렇게 하면 CI cost를 통제할 수 있다.

---

# 5. P2 — 장기 차별화 아이디어

## P2-1. `.bib` integration / ReferenceCatalog

현재는 사용자가 citation key와 URL을 직접 넣는다.

장기적으로는:

```python
refs = mp.ReferenceCatalog.from_bib("references.bib")

p.line(
    ...,
    reference=refs["fischler1981"],
)
```

같은 workflow가 가능하다.

이때 `.bib`에서 DOI/URL을 읽어:

- PGF citation → bibliography key
- SVG href → DOI/URL
- HTML editor → paper metadata preview

로 재활용할 수 있다.

중요한 점은 mudplot이 bibliography manager가 되는 것이 아니라 **figure에서 필요한 최소 metadata resolver**만 제공하는 것이다.

---

## P2-2. Optional PGFPlots export

현재 Matplotlib PGF backend는 렌더링된 figure를 PGF drawing command로 export한다.

장기적으로 editable TeX source가 중요해진다면 PGFPlots backend를 별도로 고려할 수 있다.

```text
FigureSpec
 ├── Matplotlib renderer
 └── PGFPlots renderer
```

장점:

- TeX source에서 line/axis/legend semantics가 더 잘 보존됨
- 논문 작업 중 TeX에서 직접 수정하기 쉬움
- raw data table과 plot command 분리 가능

단점:

- renderer를 사실상 하나 더 유지해야 함
- Matplotlib과 feature parity가 어렵다
- 3D/complex artist에서 maintenance cost가 크게 증가

따라서 **v1.0 이전 핵심 목표로 잡는 것은 추천하지 않는다.**

먼저 현재 PGF backend를 완성도 높게 만드는 것이 낫다.

---

## P2-3. Journal profile을 layout contract로 발전

SciencePlots의 장점은 단순하지만 매우 실용적인 journal style 조합이다.

mudplot은 여기서 한 단계 더 나갈 수 있다.

```python
p.journal("ieee-tcom")
p.journal("ieee-iotj")
p.journal("nature")
p.journal("acm")
```

단순 font/style뿐 아니라:

```text
column width
full width
base font
minimum tick font
line width
marker size
recommended raster DPI
allowed output formats
grayscale policy
```

를 하나의 `JournalProfile`로 관리할 수 있다.

즉 style sheet보다 **publication constraint profile**에 가깝게 만드는 것이 mudplot답다.

---

## P2-4. Figure lint / publication preflight

mudplot의 구조와 특히 잘 맞는 차별화 기능이다.

```python
report = p.lint(journal="ieee")
```

출력 예:

```text
✓ width fits IEEE single column
✓ all text >= 7 pt
✓ palette passes configured CVD threshold
✓ grouped lines have redundant encoding
⚠ legend contains 8 entries
⚠ two markers become ambiguous in grayscale
✓ PGF citations resolved
```

이는 단순 plotting library보다 **paper figure QA tool**에 가까운 기능이다.

개인적으로 장기적으로 가장 강한 차별점이 될 수 있다.

---

# 6. 참고할 GitHub repositories

아래 repo들을 “의존성으로 가져오라”는 의미가 아니라 **특정 설계 문제를 어떻게 풀었는지 참고하기 좋은 코드베이스**로 정리했다.

---

## 6.1 Matplotlib

**Repository**  
https://github.com/matplotlib/matplotlib

### 특히 볼 부분

```text
lib/matplotlib/backends/backend_pgf.py
lib/matplotlib/backends/backend_svg.py
lib/matplotlib/backends/backend_pdf.py
lib/matplotlib/backend_bases.py
```

### mudplot에서 참고할 점

- PGF text rendering / TeX engine integration
- backend capability 차이
- PDF/SVG metadata
- layout engine과 renderer measurement
- artist → backend separation

### 활용 우선순위

**최상**

mudplot은 Matplotlib 위에 있으므로 backend-specific behavior를 직접 새로 만들기 전에 upstream implementation을 먼저 확인하는 것이 좋다.

---

## 6.2 tikzplotlib

**Repository**  
https://github.com/nschloe/tikzplotlib

### 특히 볼 부분

- Matplotlib artist → PGFPlots translation
- `clean_figure`
- target resolution에 맞춘 point simplification
- TeX output regression test 구조

### mudplot에서 참고할 점

PGFPlots export를 장기적으로 고려할 경우 가장 직접적인 참고 자료다.

특히 “Matplotlib figure를 semantic TeX plot으로 변환할 때 어떤 edge case가 발생하는가”를 보는 데 좋다.

### 주의

mudplot core dependency로 바로 채택하기보다는 **design/reference implementation**으로 보는 것을 추천한다.

Matplotlib의 모든 artist를 완벽하게 PGFPlots로 변환하는 문제 자체가 매우 어렵기 때문이다.

---

## 6.3 PGFPlots

**Repository**  
https://github.com/pgf-tikz/pgfplots

### 참고할 부분

- axis / groupplots
- legend semantics
- log axis
- colormap
- 2D / 3D plots
- table-driven data
- TeX-native labeling

### mudplot에서 참고할 점

만약 향후 native PGFPlots renderer를 만든다면 실제 target language의 capability를 먼저 설계 기준으로 삼는 것이 좋다.

---

## 6.4 Vega-Lite

**Repository**  
https://github.com/vega/vega-lite

### mudplot에서 참고할 점

가장 중요한 것은 renderer가 아니라 **declarative spec 철학**이다.

특히:

- encoding이 explicit함
- spec이 serialization의 중심
- renderer와 spec이 분리됨
- schema가 tooling contract가 됨
- compositional grammar

### mudplot에 적용할 아이디어

현재 `group`, `c`, `axis`, `reference` 같은 정보가 증가하고 있으므로 장기적으로:

```text
data
mark
encoding
reference
layout
```

의 semantic boundary를 정리할 때 참고할 가치가 높다.

단, Vega-Lite의 복잡도를 그대로 따라가면 mudplot의 간결함을 잃을 수 있으므로 구조만 참고하는 것이 좋다.

---

## 6.5 Altair

**Repository**  
https://github.com/vega/altair

### 특히 볼 부분

- Python API ↔ JSON schema 연결
- generated schema wrappers
- validation
- deterministic schema generation
- high-level ergonomic API와 low-level spec의 공존

### mudplot에서 참고할 점

향후 Rust editor / agent / Python API가 하나의 FigureSpec을 공유할 경우 매우 좋은 reference다.

특히:

> spec schema가 truth이고 Python API는 편의 layer

라는 방향은 mudplot architecture와 잘 맞는다.

---

## 6.6 SciencePlots

**Repository**  
https://github.com/garrettj403/SciencePlots

### 참고할 부분

- IEEE / Nature 등 publication style
- composable `.mplstyle`
- font / CJK handling
- color cycle
- 실제 scientific-paper 사용자들이 요구하는 기본값

### mudplot에서 참고할 점

SciencePlots를 그대로 따라가기보다 **어떤 publication presets가 실제 사용자가 필요로 하는지** 조사하는 용도로 좋다.

mudplot은 이를 `JournalProfile` 형태로 더 구조화할 수 있다.

---

## 6.7 Colorcet

**Repository**  
https://github.com/holoviz/colorcet

### 참고할 부분

- perceptually uniform colormap collection
- categorical / continuous palette 구분
- palette naming
- gallery/documentation
- Matplotlib/Bokeh/HoloViews 등 여러 backend와의 통합

### mudplot에서 참고할 점

mudplot의 LCH engine은 이미 독자적인 강점이 있으므로 Colorcet을 dependency로 쓸 필요는 없다.

대신:

- palette taxonomy
- perceptual palette documentation
- gallery
- naming
- benchmark presentation

을 참고하기 좋다.

---

## 6.8 Colorspacious

**Repository**  
https://github.com/njsmith/colorspacious

### 참고할 부분

- CIELab / CIELCh
- CIECAM02
- CAM02-UCS
- Machado CVD simulation

### mudplot에서 참고할 점

mudplot color engine의 결과를 독립 구현과 cross-check하는 **reference oracle** 용도로 유용하다.

단, 프로젝트 자체는 오래된 편이므로 런타임 핵심 dependency보다는 test/reference 용도를 추천한다.

---

## 6.9 Hypothesis

**Repository**  
https://github.com/HypothesisWorks/hypothesis

### mudplot에서 가장 추천하는 활용

FigureSpec과 reducer는 property-based testing에 매우 잘 맞는다.

예:

```python
@given(valid_figure_specs())
def test_roundtrip(spec):
    assert FigureSpec.from_dict(spec.to_dict()) == spec
```

```python
@given(valid_actions())
def test_reducer_does_not_mutate_input(action):
    ...
```

```python
@given(urls(), citation_keys())
def test_reference_export_never_breaks_tex(...):
    ...
```

### 특히 효과가 큰 영역

- JSON round-trip
- reducer immutability
- migration
- malformed input
- URL escaping
- NaN/Inf
- empty groups
- categorical data edge cases

mudplot의 현재 test philosophy와 매우 잘 맞는다.

---

## 6.10 Playwright Python

**Repository**  
https://github.com/microsoft/playwright-python

### mudplot에서 참고할 점

v0.3에서 이미 도입한 선택이 맞다.

향후 browser editor에서 다음을 실제 browser test로 유지하는 것이 좋다.

- drag
- keyboard focus
- undo/redo
- panel selection
- file open/export
- responsive layout
- accessibility labels
- session state
- rapid repeated actions

DOM-level test만으로는 focus, scroll, actual layout 문제를 계속 놓칠 가능성이 높다.

---

## 6.11 python-jsonschema

**Repository**  
https://github.com/python-jsonschema/jsonschema

### mudplot에서 참고할 점

Rust GUI / agent / external tool이 FigureSpec JSON을 직접 다루기 시작하면 Python dataclass validation만으로는 부족해질 수 있다.

다음 용도로 유용하다.

- exported JSON Schema validation
- schema version별 validation
- external tooling interoperability
- CI contract tests

mudplot이 현재 자체 lightweight validator를 유지하더라도 **외부 contract용 JSON Schema**는 별도로 가져가는 것이 좋다.

---

# 7. Repository별 “무엇을 가져올지” 요약

| Repository | mudplot에서 참고할 핵심 | 우선순위 |
|---|---|---:|
| matplotlib/matplotlib | PGF/SVG/PDF backend와 text measurement | ★★★★★ |
| vega/vega-lite | declarative spec / schema architecture | ★★★★★ |
| vega/altair | Python API ↔ schema / validation | ★★★★★ |
| HypothesisWorks/hypothesis | FigureSpec/reducer/reference fuzz testing | ★★★★★ |
| garrettj403/SciencePlots | journal style / publication defaults | ★★★★☆ |
| nschloe/tikzplotlib | Matplotlib → semantic TeX/PGFPlots conversion | ★★★★☆ |
| pgf-tikz/pgfplots | future native TeX backend | ★★★☆☆ |
| microsoft/playwright-python | dashboard/editor E2E testing | ★★★★☆ |
| holoviz/colorcet | perceptual palette taxonomy/gallery | ★★★☆☆ |
| njsmith/colorspacious | color/CVD independent reference implementation | ★★★☆☆ |
| python-jsonschema/jsonschema | serialized spec contract validation | ★★★★☆ |

---

# 8. 추천 API 방향

최종적으로 reference API는 다음 정도가 깔끔해 보인다.

```python
import mudplot as mp

refs = {
    "RANSAC": mp.Reference(
        citation="fischler_1981",
        href="https://doi.org/10.1145/358669.358692",
    ),
    "J-Linkage": mp.Reference(
        citation="toldo_2008",
    ),
    "PEARL": mp.Reference(
        citation="isack_2011",
    ),
}

p = (
    mp.plot(df)
    .line(
        "snr",
        "bler",
        group="method",
        references=refs,
    )
    .labels(
        x="SNR (dB)",
        y="BLER",
        title="Baseline Comparison",
    )
    .title_reference(
        citation="survey_2026",
    )
    .tex_size("ieee", columns=1)
)

p.save("figure.pgf")
```

내부 spec은:

```python
ReferenceSpec(
    citation="...",
    href="...",
)
```

하나로 통일한다.

---

# 9. 권장 release roadmap

## v0.3.1 — reference hotfix

### 반드시 처리

- [ ] grouped series별 citation/href
- [ ] citation key에서 `_` 등 정상 identifier 허용
- [ ] URL escaping 재설계
- [ ] SVG grouped hyperlink support
- [ ] README의 colourblind claim / current status sync
- [ ] reference edge-case regression tests

### 테스트 예시

```text
fischler_1981
han:v2v_2019
https://example.org/paper_v2?x=1&y=2#section_3
```

---

## v0.4 — schema/reference stabilization

- [ ] `ReferenceSpec`
- [ ] FigureSpec migration policy
- [ ] backend capability registry
- [ ] citation measurement policy
- [ ] JSON Schema compatibility test
- [ ] Hypothesis-based serialization/reducer tests
- [ ] journal profile registry 정리

---

## v0.5 — paper workflow 확장

- [ ] `.bib` → `ReferenceCatalog`
- [ ] DOI/URL resolver
- [ ] figure lint / publication preflight
- [ ] richer journal profiles
- [ ] release/nightly TeX engine matrix

---

## v1.0 전에 갖추면 좋은 조건

- [ ] FigureSpec backward compatibility policy
- [ ] migration support
- [ ] backend capability가 문서화/테스트됨
- [ ] reference system이 grouped/multi-panel에서 안정적
- [ ] common TeX engines에서 release test
- [ ] deterministic example gallery
- [ ] accessibility/color claims가 test metadata와 자동 sync
- [ ] editor가 FigureSpec의 모든 핵심 필드를 수정 가능
- [ ] agent API와 human editor가 동일 action semantics 사용

---

# 10. 추가로 꼭 넣고 싶은 테스트 케이스

## Reference

- [ ] citation key에 underscore
- [ ] citation key에 colon / dash
- [ ] URL query string
- [ ] URL fragment
- [ ] URL percent encoding
- [ ] 한 layer에 citation + href 동시 사용
- [ ] citation만 존재
- [ ] href만 존재
- [ ] grouped series별 다른 citation
- [ ] duplicate visible labels
- [ ] citation macro disabled (`\figcite` → empty)
- [ ] numeric cite
- [ ] author-year cite

## Layout

- [ ] long author-year citation + outside legend
- [ ] IEEE single-column
- [ ] 2-column full width
- [ ] multi-panel
- [ ] y2 axis + colorbar
- [ ] long title citation
- [ ] CJK title/legend + citation
- [ ] math text + citation

## Serialization

- [ ] ReferenceSpec JSON round-trip
- [ ] old spec migration
- [ ] unknown future fields
- [ ] invalid version
- [ ] action replay 후 동일 output

## Security

- [ ] brace injection
- [ ] backslash macro injection
- [ ] newline injection
- [ ] malformed URL
- [ ] encoded special-character URL
- [ ] malicious `.mplot.json`

---

# 11. 하지 않는 것이 좋은 것

## 11.1 raw LaTeX를 public FigureSpec에 바로 허용

예:

```python
citation=r"\whatever{...}"
```

이런 escape hatch는 초기에는 편해 보여도:

- renderer portability
- JSON safety
- Rust GUI
- agent generation
- schema validation
- security

를 모두 어렵게 만든다.

semantic metadata를 유지하는 것이 좋다.

---

## 11.2 plot type을 너무 빠르게 늘리기

현재 이미 20개 이상의 layer type이 있다.

v0.3 이후에는 plot 종류보다:

- reference
- schema
- layout
- export
- tests
- journal workflow

를 안정화하는 쪽이 프로젝트의 차별화에 더 중요하다.

---

## 11.3 PGFPlots renderer를 너무 일찍 core 목표로 잡기

PGFPlots export는 매력적이지만 사실상 두 번째 renderer를 만드는 일이다.

현재 Matplotlib PGF 기반 citation-aware workflow가 충분히 독특하므로 먼저 이를 production-quality에 가깝게 만드는 것이 좋다.

---

# 12. 최종 추천 우선순위

내가 maintainer라면 다음 순서로 진행한다.

```text
1. grouped reference
2. citation / URL validator + escaping
3. ReferenceSpec
4. citation measurement contract
5. FigureSpec migration/version policy
6. backend capability registry
7. Hypothesis property tests
8. TeX release-test matrix
9. ReferenceCatalog (.bib)
10. publication figure lint
11. optional PGFPlots backend
```

핵심은 mudplot을:

> “Matplotlib보다 예쁜 그림을 그리는 라이브러리”

로 만들기보다는,

> **“논문에 들어가는 figure를 declarative하게 정의하고, accessibility·layout·citation·TeX integration까지 검증하는 scientific figure framework”**

로 가져가는 것이다.

이 방향이 SciencePlots, seaborn, 일반 Matplotlib wrapper와 가장 명확하게 차별화될 수 있다.

---

# 13. 검토에 사용한 주요 링크

- mudplot: https://github.com/mud-the-developer/mudplot
- mudplot changelog: https://raw.githubusercontent.com/mud-the-developer/mudplot/main/CHANGELOG.md
- Matplotlib: https://github.com/matplotlib/matplotlib
- Matplotlib PGF backend: https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/backends/backend_pgf.py
- SciencePlots: https://github.com/garrettj403/SciencePlots
- tikzplotlib: https://github.com/nschloe/tikzplotlib
- PGFPlots: https://github.com/pgf-tikz/pgfplots
- Vega-Lite: https://github.com/vega/vega-lite
- Altair: https://github.com/vega/altair
- Colorcet: https://github.com/holoviz/colorcet
- Colorspacious: https://github.com/njsmith/colorspacious
- Hypothesis: https://github.com/HypothesisWorks/hypothesis
- Playwright Python: https://github.com/microsoft/playwright-python
- jsonschema: https://github.com/python-jsonschema/jsonschema
