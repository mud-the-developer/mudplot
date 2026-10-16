# 읽기 중심 그래프 검토

*[English](VISUAL_QUALITY.md)*

이전 4패널 예제는 사용자 가독성 검토를 통과하지 못했습니다. 글꼴·경계·palette
휴리스틱을 통과했다고 좋은 대표 그림이 되는 것은 아니었습니다. 해당 이미지는
[거절된 프로토타입](images/visual_after.png)으로 남기며 개선본으로 홍보하지 않습니다.

## 두 질문, 두 그림

**[데스크톱/모바일 리뷰 페이지 열기](VISUAL_REVIEW.html)** — 실제 700px·320px
배치와 caption, 접어서 확인할 수 있는 endpoint 수치 표를 제공합니다.

1. **시간에 따라 평균 반응이 어떻게 다른가?** 평균/CI 선 그래프 한 장입니다.
   범례를 오가며 색상을 찾는 대신 마지막 선 구간 옆에 방법 이름을 붙였습니다.
   [데스크톱 PNG](images/visual_response.png) ·
   [모바일 PNG](images/visual_response_mobile.png) ·
   [SVG](images/visual_response.svg) · [PDF](images/visual_response.pdf) ·
   [편집 spec](images/visual_response.mplot.json)
2. **마지막 시점의 평균은 어떻게 다른가?** 가로 점/CI 그림으로 분리했습니다.
   범주 이름을 읽기 쉽게 두고 평균 점을 작게 하며 box/ECDF 패널을 반복하지
   않습니다. 모바일에서 짧은 CI의 정밀한 값은 수치 표로 보완하고, 불확실성을
   커 보이게 하려고 축을 늘리지 않습니다.
   [데스크톱 PNG](images/visual_endpoint.png) ·
   [모바일 PNG](images/visual_endpoint_mobile.png) ·
   [SVG](images/visual_endpoint.svg) · [PDF](images/visual_endpoint.pdf) ·
   [편집 spec](images/visual_endpoint.mplot.json)

관측값은 이전 프로토타입과 같은 독립 합성 데이터입니다(방법/시점마다 12개,
seed 2026). 추정량·점별 95% percentile-bootstrap CI 설정(399회, seed 17)·수치 축
범위도 유지합니다. Endpoint는 방향만 바꾸었으며 평균과 CI 양 끝을 기존 spec과
비교합니다. 여러 배치를 바꾼 재설계이지 스타일 한 요소의 통제 실험이나 디자인
선호도의 인과 효과 검증이 아닙니다.

## 참고 자료와 적용 범위

| Reference | 적용한 내용 |
| --- | --- |
| [ONS typography](https://service-manual.ons.gov.uk/data-visualisation/build-specifications/typography), [chart elements](https://service-manual.ons.gov.uk/data-visualisation/build-specifications/chart-elements) | 실제 표시 pixel과 웹 글자 14px 기준, 가능한 경우 직접 라벨. 큰 그림을 계속 축소하지 않고 배치를 전환합니다. |
| [Rougier 외, Ten Simple Rules for Better Figures](https://doi.org/10.1371/journal.pcbi.1003833) | 전달할 질문을 먼저 정하고 매체에 맞추며 caption에서 불확실성을 설명합니다. |
| [Rougier, Scientific Visualization: Python + Matplotlib](https://github.com/rougier/scientific-visualization-book) | 색상 프리셋/기본값만 고르는 대신 typography와 layout을 설계합니다. |
| [VisJudgeBench](https://github.com/HKUSTDial/VisJudgeBench) | 충실성·가독성·구성을 나누어 검토합니다. 이 저장소에서 모델/데이터셋을 실행한 것은 아닙니다. |
| [Heer & Bostock, CHI 2010](https://idl.uw.edu/papers/crowdsourcing-graphical-perception) | 단순 렌더링 성공이 아니라 독자의 판독 과제로 평가하는 접근입니다. |

[Nature artwork guide](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)는
논문 제출용 별도 참고 자료입니다. 웹 pixel 기준을 모든 논문의 point 규격으로
혼용하지 않습니다. 제공한 PDF는 웹 배치의 벡터 복사본이지 학술지 규격 인증이 아닙니다.

## 실제 측정 항목

[visual_quality.json](images/visual_quality.json)은 별도의 미리보기가 아니라
**실제로 저장한 PNG**를 기준으로 다음을 기록합니다.

- 원본 pixel 크기와 목표 표시 크기.
- 원본 point 크기만이 아닌, 표시 pixel로 환산한 글자 em 크기.
- 보이는 글자와 축이 캔버스를 벗어나는지.
- 글자 bounding box끼리 겹치는지(목표 크기에서 1px 허용).
- 기존 `Plot.lint()`의 palette/encoding 결과.

실제 브라우저 viewport 900·600·360·320px에서 이미지 폭은 각각 700·320·320·280px
이며 글자는 여전히 14px 이상인지 검사합니다. 데스크톱 그림을 그냥 320px로
축소한 경우는 글꼴 검사에서 실패하며 모바일 배치로 인정하지 않습니다. 임의의
Markdown 호스트는 이미지를 다르게 줄일 수 있으므로 크기 검토는 전용 페이지에서 합니다.

화면 밖 tick은 제외하지만 Matplotlib 자동 layout에서 빠진 직접 라벨은 검사합니다.
모든 글자/데이터 충돌·문구·전경/배경 대비율을 평가하거나 접근성을 인증하지는
않습니다. 라벨 위치는 이 세 곡선에 맞춰 직접 배치했으므로 데이터가 달라지면
새 layout/검토가 필요합니다. Core renderer·기본 테마·spec schema·필수 의존성은
바꾸지 않았습니다.

[반응 곡선 흑백](images/visual_response_gray.png) ·
[Protan 뷰](images/visual_response_protan.png) ·
[Deutan 뷰](images/visual_response_deutan.png). Linear sRGB 휘도와 기존 Machado
모델을 사용하는 검토 보조 자료이지 인증이 아닙니다.

## VisJudgeBench의 6개 항목을 분리

| 항목 | 근거 / 남은 판단 |
| --- | --- |
| Data fidelity | 원자료·수치 축·평균·CI 양 끝·global RNG 보존을 회귀 검사합니다. |
| Semantic readability | 글꼴/경계/글자 겹침과 판독 과제. 독립적인 독자 평가는 미실시입니다. |
| Insight discovery | 질문마다 그림을 분리했지만 독자가 실제 비교를 빨리 찾는지는 아직 측정하지 않았습니다. |
| Design style | 익숙하고 절제된 표현을 사용하며 독창성 자체에 보너스를 주지 않습니다. |
| Visual composition | 브라우저 배치와 글자 경계 검사를 하되 위계/여백은 사람의 판단이 남습니다. |
| Color harmony | 그룹의 색상 일관성·흑백/CVD 뷰를 제공하며 독립 미적 평가는 없습니다. |

자동 pass/fail을 이 여섯 항목의 점수로 바꾸지 않습니다. 보고서의
`independent_human_review`와 `model_judge`는 모두 `not_run`입니다.
[ChartJudgeBench](https://arxiv.org/abs/2609.24210) 같은 연구도 LMM 평가자의 승인을
그대로 최종 판단으로 사용하는 것에 주의를 줍니다.

## 아직 실시하지 않은 독자 판독 검사

전/후라는 칭찬 없이 목표 크기로 보여주고 다음을 묻습니다.

1. 12시간 후 평균이 가장 높은 방법은 무엇인가?
2. Reference의 마지막 평균은 대략 얼마인가?
3. 음영은 관측값 산포인가, 평균의 불확실성인가?

정답률·판독 시간을 기록합니다. 대략 읽기 과제에서는 수치 표를 닫아 두고 정밀
조회 때 열어 봅니다. 버전 비교 순서를 바꾸어 순서 효과를 줄입니다. 소규모 pilot은
사용성 피드백이지 보편적으로 더 좋은 디자인이라는 증명이 아닙니다. 독자 결과는 아직 없습니다.

## 실제 갤러리/에디터에서 사용

`python -m dashboard build --out dashboard/site_build`는 기존 layer 갤러리와 함께
`reading/` 아래에 읽기 배치·내보내기·로컬 리뷰/기준 페이지를 다시 생성합니다.
미리보기 PNG를 복사하는 대신 소스에서 렌더링하고 링크와 편집 spec을 검사합니다.

`python -m dashboard serve`의 **Start from a sample → Complete figure drafts**에서
예제를 선택합니다. 선택은 읽기 전용 초안 요청이며 그림 편집이 아닙니다.
**Open figure**를 눌러야 현재 그림을 교체하고 undo 이력을 새로 시작하므로
기존 작업은 먼저 export하세요. 실패한 import는 현재 그림과 입력 JSON을 유지합니다.
에디터는 htmx의 localStorage 페이지 본문 이력 캐시를 쓰지 않습니다. 작업창에
맞춘 미리보기를 실제 크기의 가독성 평가로 간주하지 않습니다.

## 재생성

render/dev extras를 설치한 source checkout에서 실행합니다.

```bash
uv run python examples/publication_showcase.py
uv run pytest -q tests/test_visual_quality.py tests/test_lint.py tests/test_schema_export.py
uv run pytest -q tests/test_editor_browser.py -k test_visual_review
```

데스크톱 PNG/PDF/SVG/spec·모바일 PNG/spec·반응 곡선의 색각 뷰·JSON QA를 생성합니다.
`python -m scripts.render_docs_demo`에도 포함됩니다. 이전 4패널 자료는 역사적
fixture로 남기며 재생성하거나 가독성 검증에 성공한 기준으로 부르지 않습니다.
