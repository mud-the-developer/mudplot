# 호환성 정책 — mudplot 1.x

*[English docs: COMPATIBILITY.md](COMPATIBILITY.md)*

## 안정된 공개 표면

1.x 호환성 보장은 다음의 유효한 사용에 적용됩니다.

- `mudplot.__all__`의 공개 이름: `Plot`, `FigureSpec`, `Store`, action,
  JSON I/O, validation, palette, reference, render 및 TeX helper.
- 공개 `Plot` builder method·property와 문서화된 인자.
- `mudplot` / `python -m mudplot`의 `capabilities`, `schema`, `docs`,
  `validate`, `apply`, `render`, `migrate` 명령과 기존 옵션.
- Python·Rust·agent가 공유하는 지원 FigureSpec JSON 필드와 action envelope.
  `schemas/`, 생성 [reference](REFERENCE.md), 실제 실행하는
  [전체 plot gallery](PLOT_GALLERY.md)가 이 계약을 설명합니다.

새 선택 인자·공개 이름·layer·capability는 minor release에서 추가할 수 있습니다.
소비자는 고정된 개수나 JSON key 순서에 의존하지 말고 capability를 조회하며
추가 key를 허용해야 합니다. 제거나 breaking change는 문서·release note에서
미리 deprecation을 알린 뒤 새 **major** 버전에서 수행합니다. 가능한 경우
runtime warning도 제공합니다. 보안 수정 및 잘못된 입력을 거부하는 오류 수정은
예외이며 영향을 changelog에 기록합니다.

underscore-prefixed private 구현, editor HTML/CSS, 문서화되지 않은 attribute,
upstream Matplotlib 내부 구조는 보장 범위가 아닙니다. Python/Rust editor는
함께 versioning하는 loopback-only source-tree 도구이며 engine wheel에 포함되지
않습니다. 같은 release tag에서 실행하세요. multi-user와 원격 배포는 지원 범위
밖입니다.

## Renderer와 소유권

1.x의 기본·canonical renderer는 Matplotlib입니다. `mp.render()`와
`Plot.render()`는 열린 `matplotlib.figure.Figure`를 반환하며, `mp.save()`와
`Plot.save()`도 성공 시 열린 Figure를 반환합니다. 소유권은 호출자에게 있습니다.

```python
import matplotlib.pyplot as plt
import mudplot as mp

plot = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").size(4, 3)
figure = plot.save("figure.pdf")
try:
    assert tuple(figure.get_size_inches()) == (4, 3)
finally:
    plt.close(figure)
```

기본 저장은 설정한 물리 크기를 보존하며 크롭은 `tight=True`로만 선택합니다.
동일한 spec과 **동일한 mudplot·Matplotlib·NumPy·font·runtime 환경**에서
PNG/PDF/SVG는 byte-identical입니다. 서로 다른 버전·운영체제·font 설치 간의
동일한 bytes까지 보장하지는 않습니다. 단일 JSON/PNG/PDF/SVG 파일은 atomic
write를 사용합니다. PGF는 raster sidecar가 생길 수 있으므로 전체 bundle을
transaction으로 쓰지는 않습니다. floating-point 범위를 넘는 좌표는 명확한
렌더 오류로 처리합니다.

향후 선택적 Plotly/Cairo adapter가 기존 기본 renderer나 reducer/JSON 계약을
조용히 바꿔서는 안 됩니다. 현재 `FigureSpec → renderer` 경계를 유지하기 위해
실제 필요가 없는 backend interface를 미리 만들지는 않습니다.

## 자동 layout 한계

Adaptive layout에서자동paneltitle/suptitle·namedoutsidelegend는draw뒤bbox를검사합니다.
Canvas초과/상호겹침이남으면요청canvas/spec/font크기를바꾸지않고행동가능한UserWarning을
냅니다. 공백없는긴token은명시줄바꿈이필요할수있고내용이안들어가면figure를키우거나
text/font를줄여야합니다. 음수workingrect는layoutsolver에넘기지 않습니다.

Manual/draggedtext·명시legendanchor는caller소유로강제이동하지않습니다. 경고는측정bbox
진단이지보편가독성/모든artist충돌검사가아닙니다. Caller가warning을error로승격하면
single-fileexport실패시이전출력과소유Figure정리도유지합니다.

## 상태와 action 의미

`FigureSpec`은 계속 mutable dataclass/list graph입니다. `reduce()`는 입력을
변경하거나 I/O를 하지 않지만 persistent immutable 자료구조는 아닙니다.
`Plot.spec`, `Store.state`, history, dispatch 결과와 listener 인자는 지원
spec/action 데이터의 defensive snapshot입니다. 반환 snapshot을 직접 수정하지
말고 action으로 상태를 변경하세요.

Panel/layer index는 음수가 아닌 plain 정수이며 bool/float 별칭은 받지 않습니다.
패널 생성 action의 자동 확장은 유지하고 layer 편집은 기존 layer만 대상으로 합니다.
Reduce는 없는 column/matrix 참조를 일시적으로 만들 수 있지만 부수효과 없이 유지하며
명시 validation·render validation이 그리기 전에 거부합니다.

각 action은 전체 spec을 복사하며 undo/redo는 history를 replay합니다.
따라서 큰 inline data와 긴 history에는 문서화된 성능 상한이 있습니다.
`mp.apply()`는 실패한 중간 결과를 노출하지 않고 새 결과를 반환합니다.
`Plot.apply()`와 `Store.dispatch_all()`은 순서대로 개별 dispatch하는 것이며
**batch transaction이 아닙니다**. listener는 commit 이후 실행되고, listener
exception은 전파되지만 commit을 되돌리지 않습니다. editor는 반대로 후보 상태를
검증·렌더링한 뒤 state와 preview를 commit합니다. `validate()` / `assert_valid()`는
명시적 계약 검사이며 render는 자동으로 검증합니다. Python editor는 open/reset 때
새 이력을 시작하고, Rust editor는 기존처럼 open/reset도 undo 가능한 snapshot 전이로
보존합니다. 새 정상 편집은 둘 다 redo를 지웁니다. 서로 다른 기존 UI 이력 정책을
동일한 동작으로 보장하거나 이번에 변경한 것은 아닙니다. Rust reset은 마지막 import가
아닌 시작 기본 문서로 돌아갑니다. 두 editor 모두 import 파일명을 자동 덮어쓰기 대상으로
묶거나 별도 persistent dirty-bit/save-target 기능을 추적하지 않으며 다운로드는 현재 상태를
내보냅니다. 값이 같은 action도 event/snapshot을 기록하고 redo를 지웁니다. No-op 최적화로
listener/undo 의미를 조용히 제거하면 안 됩니다.

Legacy raw group mask는 NumPy 문자열 dtype 추론 없이 원래 Python 값을 사용합니다.
문자열/숫자는 분리하고 기본 numeric equality의 `1`·`1.0`·`True` 통합은 유지합니다.
명시적 ordered raw 모드는 typed bool/numeric key를 유지합니다. Raw null은 legacy group이며
통계 layer의 결측 행 제외와 다릅니다. 빈 label은 범례가 없을 수 있고 caption은 `str(key)`라
서로 다른 타입이 같은 표시명을 가질 수 있으므로 모호한 ID는 plotting 전에 정규화하세요.
Raw line은 행 순서/중복 x를 유지하고 lineplot은 x별 집계와 명시 sort 정책을 적용합니다.
빈 raw line/scatter는 유효할 수 있으나 통계 layer는 usable 관측 부재를 거부하고 singleton의
정의되지 않는 interval은 만들지 않습니다.

## Journal과TeX 크기 우선순위

5개 `TEX_PRESETS`는보통TeXgeometry에관한repo가정이며모든publisherguide의최신인증은
아닙니다. `columns=1`은column폭,2는text폭에TeX72.27pt/in을적용해inch로변환합니다.
기본save는이canvas를유지하고SVG/PDF는72graphicspt/in,PNG는요청DPI에서1pixel내
양자화오차입니다. Sizing은preview전용이아니며render/file도같은spec크기를씁니다.

물리크기는 `.journal()` 관례크기/`.tex_size()`/`.size()` 중마지막action을따릅니다.
Activejournal의등록rcfont/linewidthkey는action순서와무관하게theme위에적용됩니다.
`.journal(None)`은크기를바꾸지않고styleoverride를지워명시fontfield를적용합니다.
TeXsize는body/label/title/tick을각각설정하므로body `size`만바꾸면명시 `label_size`는
남습니다. 새override메타데이터나render우선순위는추가하지 않았습니다.

## 소유 render의 동시성 경계

mudplot 소유 Matplotlib effect는 같은 process에서 하나의 재진입 lock으로 직렬화합니다.
API render/save·TeX preview·Python editor preview/placeholder/export·site/gallery가
대상이며 서로 다른 요청의 serial state/bytes를 유지합니다. 병렬 처리량 보장이 아닙니다.
Rust 요청에는 session 직렬화와 별도 Python child process 경계도 있습니다.

함수가 lock을 해제한 뒤 반환된 open Figure는 계속 호출자 소유입니다. 직접 pyplot/
Figure draw/save/close·Store mutation·같은 directory로의 동시 build·외부 Matplotlib
호출은 호출자가 조정해야 합니다. 병렬 작업은 독립 spawned process를 우선하고 threaded
render 도중 fork나 mutable Figure 공유의 안전성으로 확대하지 마세요.

## JSON과 버전

package/editor **1.0.0**과 serialized spec **0.1**은 독립된 버전입니다.
package release마다 spec version을 올릴 필요는 없습니다.

- 지원 필드·JSON 값은 무손실 왕복합니다. 인식하는 spec version의 기존
  dataclass에 있는 알 수 없는 필드는 Python loader가 무시하므로 **왕복 보존을
  보장하지 않습니다**. 사용자 metadata는 별도로 보관하세요. 새 `StatSpec`은
  임의 callable operation 같은 알 수 없는 옵션을 거부하여 요청한 계산을
  조용히 바꾸지 않습니다. 가중치·단위 재표본화는 문서화한 범위만 지원합니다.
- Optional 값은 모두 같은 뜻이 아닙니다. 생략은 model default를 선택하고 nullable의
  명시 null은 유지합니다. `StatSpec.errorbar` 기본 `"ci"`, `LayerSpec.inner` 기본 `"legacy"`는
  명시 null과 다릅니다. Marker size0도 자동 점 크기로 바꾸지 않고0으로 전달하며 생략/null
  기본은 유지합니다. Marker/line-style 옵션을 지원하는 layer의 명시 `""`는 자동 encoding이
  아닌 no-marker/no-line 의미를 유지하며 null과 다릅니다. KDE/ECDF 같은 개별 style 제한은
  그대로 검사합니다. 구조 필드 표만으로 전 필드 UI/CLI/Rust parity를 승인하지 않으며
 20-case render-token fixture도 명시한 범위만 검증합니다.
- spec version을 생략하면 Python/Rust 모두 내장된 현재 기본값을 사용합니다.
  명시한 null이나 잘못된 값은 생략이 아닙니다.
- 알 수 없는 spec version은 명확히 거부합니다. 향후 비호환 serialized shape는
  spec version을 올리고 이전 지원 파일의 migration을 제공해야 합니다.
  안전한 default를 가진 추가 필드는 version bump가 필요하지 않을 수 있습니다.
- JSON은 RFC 규약을 따릅니다. 재귀적 duplicate key, non-finite number,
  lone surrogate, 문자열이 아닌 key와 `$serde_json::private::Number`를 거부합니다.
  Rust는 Unicode escape를 포함한 원본 property 이름을 검사하여 serde big-number
  adapter가 예약 key object를 값으로 바꾸지 못하게 합니다. 일반 문자열 value 안의
  예약어 표기는 정상 텍스트로 유지합니다.
- 64-bit를 넘는 정수는 구조적으로 보존하지만 arbitrary-precision plotting까지
  보장하지 않습니다. action envelope는 문자열 `"type"`을 사용합니다.
- input adapter는 일반적인 missing value를 `null`, 날짜·시간을 ISO 문자열,
  NumPy scalar를 Python 값으로 정규화합니다. Infinity·`Decimal`·미지원 객체를
  조용히 변환하지 않으며 중복 열 이름은 거부합니다. Positional row 너비는 첫 행,
  DB result row는 cursor description과 같아야 하며 불일치 시 pivot 전에 행 index/
  기대 너비를 포함한 오류를 냅니다. 추가 값을 잘라내거나 짧은 행을 채우지 않습니다.
  각 record는 mapping이어야 하며 positional/DB 행에 문자열·bytes·mapping을 넣으면
  문자·key 데이터로 바꾸지 않고 해당 행 index를 포함한 오류를 냅니다. Record의
  누락 key는 기존처럼 첫 등장 열 순서와 null 채우기를 유지합니다. 열 길이 불일치는
  입력 단계에서 원값을 보존하고 렌더/editor commit 전 validation에서 거부합니다.
- 알려진 NumPy floating/temporal 및 pandas missing scalar만 null로 정규화하며
  임의 객체의 self-inequality와 Decimal NaN은 결측 sentinel로 보지 않습니다.
  `.item()`은 지원 plain/date 표현으로 변환될 때만 이어가고 미지원 same-type/순환
  객체 chain을 따라가지 않습니다. Complex/extended precision 등 미지원 값은
  반올림/문자열/null/무한 재귀 대신 strict JSON에서 명시적으로 거부합니다.
  호출자가 제공한 Python method를 sandbox하는 기능은 아닙니다.
- NumPy datetime64 scalar/column/row는 ISO 변환 전 dtype을 유지해 ns/ps/fs/as와
  NaT→null을 보존하고 epoch 정수로 바꾸지 않습니다. 기존 coarse 형식과 실제 숫자
  epoch 열은 유지합니다. Polars datetime(ns)는 native formatter와 parse/equality로
  검증하며 손실 있는 timezone 표현은 반올림 값 대신 오류를 냅니다. 모호한 2-D datetime
  column은 거부하므로 2-D 배열을 row 입력으로 넘기세요. Arrow는 upstream의 안전한
  temporal 변환을 따르며 ns에 pandas가 필요할 수 있습니다. 미지원 변환은 잘라내지 않고 실패합니다.
- Raw line/scatter의 범주 x 변환에서 null은 결측으로 유지해 선을 끊고 점을 mask하며
  가짜 `"None"` 범주를 만들지 않습니다. 실제 문자열 `"None"`은 범주로 유지합니다.
  ISO 날짜 문자열도 여기서는 같은 범주 경로이며 연속 날짜 축 계약을 추가한 것은 아닙니다.
  통계 layer는 사용 가능한 관측을 별도로 선택하며 원자료 행/결측은 spec에 남깁니다.
- SQL 값은 DB-API `params=`로 전달하며 mudplot이 query에 보간하지 않습니다.
  Connection+query로 내부 생성한 cursor만 close를 지원하면 성공/실패 뒤 정리합니다.
  호출자가 넘긴 executed cursor와 connection의 소유권은 호출자에게 있고 commit/
  rollback도 하지 않습니다. Close 오류는 숨기지 않고 전파하며 이전 실패는 예외 context에 남습니다.

## 문자열 문맥

HTML editor value/draft와 SVG text/href는 data로 escape하며 한 번 decode하면 원래
따옴표·ampersand·backslash·Unicode를 회복하고 script/event node가 추가되지 않습니다.
허용한 Matplotlib 수식은 그대로 수식입니다.

명시 PGF label은 보편 plain-text escaping이 아닌 backend의 신뢰하는 TeX 문법입니다.
Raw `A & B`는 TeX 측정에서 실패하지만 `A \\& B`·명시한 무해 macro/수식은 컴파일됩니다.
호출자/document의 TeX encoding·page 크기도 중요합니다. Citation key/href의 엄격한
별도 검증이 임의 TeX macro를 허용하지 않으며 자동 전형식 rewriting이나 untrusted-TeX
sandbox를 도입하지 않습니다.

## 의존성과 배포

선언적/state/JSON core의 필수 third-party 의존성은 없습니다. 색상 계산에는
NumPy, 렌더링에는 NumPy와 Matplotlib이 필요합니다. 공개 colour/render/save/preview·
CLI render·palette의 Matplotlib adapter에서 기대한 의존성이 없으면 `mudplot[color]` 또는
`mudplot[render]` 설치를 안내합니다. 무관한 transitive/compiled import 오류는 진단과
exception cause를 유지합니다. Color extra가 Matplotlib을 강제하지 않고 browser extra도
Playwright 패키지만 설치하므로 `playwright install chromium`은 별도 단계입니다.

관찰한 PowerShell7.6.7/LongPathsEnabled1 Windows에서 짧은 CWD+336문자 절대 파일
경로의 API/console/module/lock/render는 통과했지만260문자 초과 CWD의 console 시작은
실패했습니다. 짧은 CWD와 절대 경로를 사용하세요. 별도 대조에서 관찰한 uv venv는
321문자 `TMP`일 때 print program도 시작하지 못했고 `-S`/pipe/file capture도 같았습니다.
Base Python은 동작했고 긴 `TEMP`+짧은 `TMP`에서는 같은 venv도 동작했습니다. 이 구성의
bridge 시작/open/action/PNG도 통과했으며 interpreter를 자동 대체하지 않습니다. CWD/
`TMP`를 짧게 두고 의도한 환경에서 선택한 interpreter를 먼저 검사하세요. 관찰한 host/
interpreter 한계이지 모든 경로 임계값·process-tree 정리 보장이나 OS 설정 변경은 아닙니다.
Unreleased robust/logistic/
LOWESS effect는 optional `regression` extra(statsmodels>=0.14.1; all/dev 포함)를
fit 때만 불러옵니다. 일반 polynomial/residual/log-x는 statsmodels가 필요 없습니다.
이 extra는 Python3.10/NumPy1.23/Matplotlib3.8/statsmodels0.14.1에서 확인했으며
필수 의존성이나 기존 공개 자산을 바꾸지 않습니다. Unreleased clustermap은 별도
cluster extra(SciPy>=1.10, all/dev 포함)이며 SciPy1.10/Python3.10/NumPy1.23/
Matplotlib3.8에서 확인했습니다. Pure 설정/linkage JSON 검사는 stdlib만 사용합니다.
1.0 지원 하한은 Python
**3.10**, NumPy **1.23**, Matplotlib **3.8**, Rust editor **1.88**입니다.
이 하한은 1.x에서 계속 지원합니다. 계획된 runtime 하한 상향은 사전 deprecation과
major release가 필요합니다. 중대한 보안 수정은 의존성 조건을 강화할 수 있으며
changelog와 설치 안내에서 명시합니다.

GitHub release에는 검증된 sdist·engine-only wheel, SHA-256 checksum 및 OIDC
build provenance를 포함합니다. 공개 tag와 자산은 불변이며 수정은 tag 이동이나
자산 덮어쓰기가 아니라 새 release로 배포합니다. PyPI는 trusted publishing이
설정될 때까지 계속 보류합니다.
