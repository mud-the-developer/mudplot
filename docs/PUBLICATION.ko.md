# 출판용 그림

실제 출판 크기에 맞춰 그림과 인용을 설정하고 결과물을 점검합니다. 기본값을 바꾸지 않는 구성 옵션은 [과학 그림 구성과 QA](SCIENTIFIC_QUALITY.md)를 참고하세요.

## TeX WYSIWYG 미리보기

```python
# 논문 컬럼폭·폰트에 맞춘 실제 크기 미리보기 (모의 본문 컬럼 + 캐션)
fig = (mp.plot(data).line("voltage", "current", group="order")
         .labels(x="Voltage (mV)", y="Current")
         .preview(tex="ieee", caption="Figure 1. ..."))
```

## 실제 figure를 1단/2단 컬럼 폭에 맞추기

`.tex_size(...)`는 `.preview()`와 같은 컬럼폭·폰트 크기 계산을, 미리보기가
아니라 실제로 `.render()`/`.save()`하는 figure에 적용합니다. 긴 제목이나
바깥쪽 범례도 이 크기에서 겹치거나 잘리지 않도록 자동으로 배치됩니다
(아래 "레이아웃" 참고).

```python
p.tex_size("ieee", columns=1)    # 한 컬럼 폭
p.tex_size("nature", columns=2)  # 전체 텍스트 폭 (2단 논문의 figure*)
```

## 레이아웃: 지정한 크기 그대로, 텍스트가 잘리거나 겹치지 않게

`render()`/`save()`는 내용에 맞춰 figure를 자르거나 다시 늘리지 않습니다 —
`.size()`나 `.tex_size()`로 지정한 물리적 크기가 그대로 유지되며, 이는 TeX
배치에서 중요합니다. 대신 figure를 반환하기 전에 다음을 수행합니다.

- figure 폭을 넘는 제목/suptitle을 자동 줄바꿈(matplotlib의 실제 렌더러로
  측정한 네이티브 텍스트 줄바꿈이며, 직접 계산한 추정치가 아님)
- 이름이 붙은 `"outside ..."` 범례 위치를 위한 캔버스 여백을 정확히
  확보해, 플롯 영역과 겹치거나 가장자리에서 잘리지 않게 함

명시적으로 지정한 `bbox_to_anchor=[x, y]`(아래 참고)는 그대로 신뢰하며
자동 조정하지 않습니다 — 플롯 위에 겹치는 배치를 의도했을 수도 있기
때문입니다. 이 과정은 모두 matplotlib 자체의 레이아웃 엔진과 텍스트 측정
렌더러를 사용하며(직접 만든 레이아웃 시스템 없음), 이미 잘 맞는
figure에는 아무 변화도 주지 않습니다 — 잘릴 우려가 없다면 폰트 크기는
지정한 그대로입니다. matplotlib의 constrained layout이 3D Axes를 잘
지원하지 않아 3D 패널은 당분간 `tight_layout()`으로 대체됩니다.

## 그림 안에 citation과 링크 넣기 (LaTeX 연동)

범례 항목이나 패널 제목에 BibTeX 키와 URL을 붙일 수 있습니다. 이미지에 번호를
굽지 않고 **논문이 컴파일 시점에 해석**하므로, 그림 안의 `[1]`이 References의
`[1]`과 정확히 같은 번호가 됩니다.

```python
(mp.plot(data)
    .line("x", "y", label="RANSAC",
          citation="fischler1981",             # BibTeX 키
          href="https://doi.org/10.1145/358669.358692")
    .labels(title="Robust fitting")
    .title_reference(citation="hartley2003")
    .tex_size("ieee", columns=1)
    .save("fig.pgf"))                          # .pgf -> LaTeX 네이티브 내보내기
```

```latex
\input{preamble.tex}   % 또는 mudplot.PREAMBLE 내용을 한 번 붙여넣기
\begin{figure}\centering
  \input{fig.pgf}
  \caption{Errors of two estimators.}
\end{figure}
```

내보낸 파일은 `\cite{...}`가 아니라 `\figcite{fischler1981}`를 남깁니다.
그림 인용을 무엇으로 처리할지 **문서가 결정**하게 하기 위해서입니다:

```latex
\providecommand{\figcite}[1]{\cite{#1}}   % mudplot.PREAMBLE; \citep, \autocite 등으로 교체 가능
```

같은 spec이라도 백엔드별로 처리가 다릅니다:

| 형식 | citation | href |
| --- | --- | --- |
| `.pgf` | `\figcite{key}` — 논문 bibliography가 번호 부여 | hyperref로 `\href{url}{...}` |
| `.svg` | 생략 (해석할 대상이 없음) | 텍스트가 클릭 가능한 링크 |
| `.png`/`.pdf` | 생략 | 생략 |

이 값들은 LaTeX 소스에 그대로 치환되므로 `validate()`가 중괄호·백슬래시를
거부합니다. 링크는 절대 `http`/`https`/`mailto` URI만 허용하며 active/file/
data/custom scheme, 상대 링크, control 문자, 공백은 SVG/PGF export 전에
거부합니다. `_`/`:`/`-`/`&`/`#`/`%` 같은 일반 URL 문자는 계속 허용합니다.

`group=`으로 묶인 레이어는 `references=`(`{group값: mp.Reference(...)}` 딕셔너리)로
시리즈별로 다른 논문을 인용할 수 있습니다. 딕셔너리에 없는 group 값은 인용/링크가
붙지 않습니다:

```python
(mp.plot(data).line("snr", "bler", group="method", references={
    "RANSAC": mp.Reference(citation="fischler1981", href="https://doi.org/..."),
    "J-Linkage": mp.Reference(citation="toldo2008"),
}))
```

citation key/URL을 직접 입력하는 대신 기존 `.bib` 파일에서 바로 가져올 수도
있습니다. `mp.ReferenceCatalog`는 실제 `.bib` 파일이 쓰는 흔한 BibTeX 문법을
읽는 최소한의(의존성 없는) 리더입니다 — 완전한 참고문헌 관리자는 아닙니다:

```python
refs = mp.ReferenceCatalog.from_bib("references.bib")
ref = refs["fischler1981"]   # -> ReferenceSpec(citation=..., href=...)
# href는 (네트워크 접근 없이) mp.resolve_reference_href로 해결됩니다:
# doi 필드(맨, "doi:" 접두사, 또는 전체 doi.org URL 모두 동일하게 정규화)
# -> https://doi.org/...; 없으면 arXiv id(eprint + archiveprefix/eprinttype
# == "arxiv", arXiv 자체 "export bibtex" 형태) -> https://arxiv.org/abs/...;
# 그런 url 필드; 다 없으면 None
p.line("x", "y", label="RANSAC", citation=ref.citation, href=ref.href)
```

PGF 레이아웃은 기본적으로 간결한 숫자 인용 스타일(`"[12]"`)을 기준으로
측정됩니다. 저자-연도 등 더 긴 스타일을 쓴다면
`.reference_style(measure_text="(Author, Year)")`를 지정해 범례 크기가
실제 컴파일 결과 폭에 더 가깝게 예측되도록 하세요.

## 범례·제목·주석을 정확한 위치에 놓기

```python
p.legend(bbox_to_anchor=[0.8, 0.5])    # figure 비율 [x, y], location을 덮어씀
p.legend(location="upper left")        # bbox_to_anchor=None으로 이름 위치 복원
p.title_position([0.1, 0.85])          # axes 비율 [x, y]; None이면 기본값 복원
p.set_layer_at(layer_index, [3, 0.5])  # text/annotate 레이어 위치 이동(데이터 좌표)
```

인터랙티브 에디터의 드래그 가능한 핸들(마우스 또는 화살표 키, 미리보기 위에서
직접)도 이 기능을 사용합니다 ([대시보드 문서](../dashboard/README.ko.md) 참고).

## Figure lint / 출판 preflight

`validate()`는 구조적 올바름만 검사합니다("이 레이어에 `axis='y2'`가 허용되는가").
`.lint()`는 대신 실제 출판용 품질 휴리스틱을 검사합니다 — 지정된 크기에서 실제로
흑백·색맹 안전하고 읽기 쉬운 논문용 그림이 맞는지. 강제 실패가 아니라 검토할 항목을
알려주는 방식입니다:

```python
report = p.lint(journal="ieee")
print(report)
# ✓ width fits ieee single column (3.49in <= 3.49in)
# ✓ dpi (300) meets ieee recommendation (300 DPI)
# ✓ all text >= 6pt
# ⚠ palette does not pass the measured CVD-safety threshold for 9 series -- see Palette.report()
# ⚠ palette colours become ambiguous in true greyscale
# ✓ grouped series have redundant marker/line-style/hatch encoding
# ⚠ 9 series in one group exceeds the marker/line-style cycle length (4) -- ...
# ⚠ legend contains 9 entries (> 8) -- consider splitting into panels or using direct labelling
# ✓ citation/href metadata is well-formed

report.ok   # error 레벨 항목이 있을 때만 False (예: 페이지에 안 맞는 크기)
```

검사 항목: 지정한 journal 프로필에 대한 페이지 폭·래스터 DPI, 최소 글자 크기,
팔레트 CVD/흑백 안전성(`Palette.report()` 재사용), 그룹화된 시리즈의 이중
인코딩, 마커/선스타일 사이클 소진, 범례 크기, 참고문헌 메타데이터 유효성.
기준값은 해당 journal 프로필(아래 참고)을 기본으로 사용하고 호출당 덮어쓸 수
있습니다(`min_font_pt=`, `max_legend_entries=`). `journal=`을 생략하면 이미
`.journal(...)`로 지정한 것을 자동으로 사용합니다. `mp.lint_figure(spec, ...)`는
부수효과 없는 에이전트용 동일 함수입니다 — 실제로 렌더링하지 않으므로 matplotlib 없이 `color`
extra(numpy)만 있으면 됩니다.

## Journal 프로필 (스타일 시트가 아닌 출판 제약 모음)

지원하는 각 저널은 하나의 `JournalProfile`로, **스타일**(폰트, 선 굵기, 관례적
그림 크기) + **TeX 기하학**(컬럼/텍스트 폭, 단 수) + **preflight 제약**(최소 글자
크기, 권장 래스터 DPI, 범례 수 상한, 흑백 정책)을 함께 보유합니다. 따라서
`.journal()`, `.tex_size()`, `.lint()`이 서로 따로 찾는 게 아니라 하나의 정의를
공유합니다:

```python
mp.AVAILABLE_JOURNALS          # ('nature', 'ieee', 'acm', 'revtex')
prof = mp.get_journal_profile("acm")
prof.columnwidth_pt            # 241.0
prof.min_font_pt               # 6.0
prof.recommended_dpi           # 300

# 저널 이름을 넣는 자리엔 프로필 객체도 그대로 들어감
p.journal(prof).tex_size(prof, columns=1).lint(journal=prof)
```

`mp.capabilities()["journal_profiles"]`에서 에이전트용 JSON으로 전부 노출됩니다.

## 팔레트 직접 사용

```python
pal = mp.color_palette(5, "qualitative")   # 명도 jitter·색상 대조
print(pal.hex, pal.min_delta_e())
print(pal.report())      # 최종 HEX 지표와 명시한 evaluation 조건을 포함
cmap = mp.color_palette(256, "sequential").to_cmap()

# 이름 붙은 검증된 팔레트(명시된 카테고리 수까지 적색맹·녹색맹·진짜 흑백에서
# 안전함을 측정함; mp.capabilities()["palette_presets"] 참고):
pal = mp.color_palette(6, "qualitative", preset="paper")   # 또는 "vivid" / "soft"
p = mp.plot(data).line("x", "y", group="g").palette(preset="paper")

# bar/box/violin 도 기본적으로 그룹마다 해칭 패턴을 함께 사용해(ThemeSpec.hatches),
# 유한한 패턴은 반복되므로 실제 인쇄 크기의 가독성을 따로 확인해야 합니다.
p2 = mp.plot(data).bar("category", "value", group="g")  # 색상 + 해칭
p3 = p2.encoding(redundant_encoding=False)               # 색상만
```

`Palette.report()`는양자화를포함한최종 **8-bit HEX sRGB**를측정합니다. `evaluation`에는
정상시각·선택CVD유형·Machado2009 fullseverity와기존ΔE00≥8/L*gap≥3기준이들어갑니다.
Float `srgb` metric과작은차이가날수있으며측정flag이지접근성/인쇄인증이아닙니다.
Preset사전검증범주수를넘으면새report를확인하세요. 결정적sampling의시작점은
`hue_start`이며별도randomseed옵션은없습니다.
