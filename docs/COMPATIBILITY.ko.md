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

## 상태와 action 의미

`FigureSpec`은 계속 mutable dataclass/list graph입니다. `reduce()`는 입력을
변경하거나 I/O를 하지 않지만 persistent immutable 자료구조는 아닙니다.
`Plot.spec`, `Store.state`, history, dispatch 결과와 listener 인자는 지원
spec/action 데이터의 defensive snapshot입니다. 반환 snapshot을 직접 수정하지
말고 action으로 상태를 변경하세요.

각 action은 전체 spec을 복사하며 undo/redo는 history를 replay합니다.
따라서 큰 inline data와 긴 history에는 문서화된 성능 상한이 있습니다.
`mp.apply()`는 실패한 중간 결과를 노출하지 않고 새 결과를 반환합니다.
`Plot.apply()`와 `Store.dispatch_all()`은 순서대로 개별 dispatch하는 것이며
**batch transaction이 아닙니다**. listener는 commit 이후 실행되고, listener
exception은 전파되지만 commit을 되돌리지 않습니다. editor는 반대로 후보 상태를
검증·렌더링한 뒤 state와 preview를 commit합니다. `validate()` / `assert_valid()`는
명시적 계약 검사이며 render는 자동으로 검증합니다.

## JSON과 버전

package/editor **1.0.0**과 serialized spec **0.1**은 독립된 버전입니다.
package release마다 spec version을 올릴 필요는 없습니다.

- 지원 필드·JSON 값은 무손실 왕복합니다. 인식하는 spec version의 알 수 없는
  dataclass 필드는 Python loader가 무시하므로 **왕복 보존을 보장하지 않습니다**.
  사용자 정의 metadata는 별도로 보관하세요.
- 알 수 없는 spec version은 명확히 거부합니다. 향후 비호환 serialized shape는
  spec version을 올리고 이전 지원 파일의 migration을 제공해야 합니다.
  안전한 default를 가진 추가 필드는 version bump가 필요하지 않을 수 있습니다.
- JSON은 RFC 규약을 따릅니다. 재귀적 duplicate key, non-finite number,
  lone surrogate, 문자열이 아닌 key와 `$serde_json::private::Number`를 거부합니다.
- 64-bit를 넘는 정수는 구조적으로 보존하지만 arbitrary-precision plotting까지
  보장하지 않습니다. action envelope는 문자열 `"type"`을 사용합니다.
- input adapter는 일반적인 missing value를 `null`, 날짜·시간을 ISO 문자열,
  NumPy scalar를 Python 값으로 정규화합니다. Infinity·`Decimal`·미지원 객체를
  조용히 변환하지 않으며 중복 열 이름은 거부합니다.
- SQL 값은 DB-API `params=`로 전달하며 mudplot이 query에 보간하지 않습니다.

## 의존성과 배포

선언적/state/JSON core의 필수 third-party 의존성은 없습니다. 색상 계산에는
NumPy, 렌더링에는 NumPy와 Matplotlib이 필요합니다. 1.0 지원 하한은 Python
**3.10**, NumPy **1.23**, Matplotlib **3.8**, Rust editor **1.88**입니다.
이 하한은 1.x에서 계속 지원합니다. 계획된 runtime 하한 상향은 사전 deprecation과
major release가 필요합니다. 중대한 보안 수정은 의존성 조건을 강화할 수 있으며
changelog와 설치 안내에서 명시합니다.

GitHub release에는 검증된 sdist·engine-only wheel, SHA-256 checksum 및 OIDC
build provenance를 포함합니다. 공개 tag와 자산은 불변이며 수정은 tag 이동이나
자산 덮어쓰기가 아니라 새 release로 배포합니다. PyPI는 trusted publishing이
설정될 때까지 계속 보류합니다.
