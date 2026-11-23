# 네이티브 평면 도형

[English](NATIVE_GEOMETRY.md) · [실행 예제](../examples/native_planar_geometry.py)

아래 호출은 공급된 값을 그리며 값을 추정하지 않습니다. 새 선언을 생략하면
기존 호출 의미를 유지합니다. 저장 레이어나 `AddLayer`/`ReplaceLayer`로 편집하고
임의 Matplotlib 인자나 콜백은 저장하지 않습니다.

## 선, 오차, 띠와 구간

- `line`과 `scatter`의 `native_style=ComponentStyleSpec(...)`은 실제 마커와 획,
  색, 불투명도를 설정합니다. 마커 지름과 획 너비의 단위는 pt이며 산점도는
  지름의 제곱을 네이티브 면적으로 사용합니다. 컬렉션 획 `none`은 채움을
  유지한 채 획을 없앱니다. 기존 의미 역할이나 스칼라 매핑과 중복 지정하지 않습니다.
- `hlines(SegmentSpec(at,start,end))`는 y와 실제 x 양 끝점, `vlines`는 x와
  실제 y 양 끝점을 받습니다. 기존 `hline`/`vline` 참조선의 축 비율이 아닙니다.
  열린 x/y/y2 축 및 선언된 날짜 단위를 사용합니다.
- `errorbar(..., magnitudes=ErrorMagnitudesSpec(x=["left","right"],
  y=["below","above"]))`의 크기는 원자료 열에서 읽습니다. 중심에서 아래 크기를
  빼고 위 크기를 더합니다. 숫자 시간의 크기에는 입력 단위만 적용하고 원점은
  더하지 않습니다. ISO 시간은 일 단위입니다. 필수 값 결측은 해당 행만 제외하고
  표시할 실제 끝점은 달력·log·logit의 표현 범위에 맞아야 합니다.
- `band(along,lower,upper,orient="v"|"h",fill=FillSpec(...))`는 실제 수직/수평
  채움입니다. `where`는 불리언 열이며 양쪽 관측이 허용하는 구간만 채웁니다.
  결측에는 다리를 만들지 않습니다. `step`은 `pre`/`post`/`mid`,
  `interpolate=True`는 마스크 경계의 실제 교차점을 사용합니다.
- `hspan`/`vspan`은 `SpanSpec(start,end,fractions)`를 공유합니다. 실제 y/x
  구간을 음영 처리하며 직교 방향은 `[0,1]` 안의 축 비율입니다.

확장 옵션은 데카르트 패널, 원자료 행 10,000개와 그룹 64개 이내에서 기존 네이티브
메모리·경로 상한을 적용합니다. 저장 형식에 그림 계산 결과를 복제하지 않습니다.


## 제공된 막대와 원형 조각

[실행 예제](../examples/native_bars_and_pie.py). `bar`의 `BarGeometrySpec` 또는
`barh`로 실제 표시 위치를 설정합니다. 가로 막대의 `bottom`은 왼쪽 끝이며,
숫자 상수나 원자료 열입니다. `align="edge"`는 공급한 위치를 첫 모서리로
사용합니다. `multiple="stack"`은 같은 원 범주/좌표를 맞추고 범주별 한 기준점에서
양수·음수 높이를 따로 누적합니다. `True`와 숫자 `1`은 다른 범주입니다.
막대별 `styles` 배열은 원자료 행 기준입니다. `labels`는 원 텍스트 열,
`value_format`은 공급한 부호 있는 높이의 표시 형식이며 누적 끝값이 아닙니다.
기존 오차 옵션을 새 막대 형상에 섞지 않고 독립 `errorbar`를 사용합니다.

`PieGeometrySpec`은 최대 64개 행의 네이티브 조각, 각도/방향, 반지름, 시작점,
폭, explode, 조각 몸체 스타일, 라벨 위치/회전/글자색/크기를 제어합니다.
`value="raw"`는 실제 공급값, `value="percent"`는 질량 백분율입니다.
`normalize=False`는 총합이 1 이하인 부분 원을 그립니다. 원자료 행에 대응하는
`annotations`는 실제 조각 가장자리에 연결된 주석이며 떨어진 거리는 pt입니다.
콜백이나 임의 서식 표현식은 저장하지 않습니다.

## 리터럴 패치·표·주석 좌표

[실행 예제](../examples/native_annotations.py). `PatchSpec`의 사각형·타원은
증가하는 두 모서리, 다각형은 세 점 이상이 필요합니다. 경로에는 꼭짓점별
`MOVETO`, `LINETO`, `CURVE3`, `CURVE4`, `CLOSEPOLY`를 지정하고 각 2차/3차
곡선의 2/3개 코드와 꼭짓점을 모두 제공합니다. `data`, `axes`, `figure` 중
좌표계를 고르며 축·그림 좌표는 `[0,1]` 비율입니다. 보이지 않는 축을 추가하지
않습니다. 구간 음영은 앞에서 설명한 `SpanSpec`을 공유합니다.

`LiteralTableSpec`은 축 비율 `[left,bottom,width,height]` 안에 실제 문자열과
행/열 헤더를 그립니다. 표 내용은 계산식, HTML, 원자료 열이 아닙니다. 정렬,
글자 크기, 테두리와 색을 실제 셀에 적용합니다.

`AnnotationSpec`으로 텍스트와 화살표 끝의 좌표계, 정렬·회전과 지정된 화살표를
설정합니다. 데이터 좌표는 실제 네이티브 축 값(날짜 축은 UTC day)입니다.
에디터는 지원하는 데카르트 축의 데이터 앵커에만 끌기 핸들을 제공합니다.
축/그림 비율은 저장값이나 `SetLayerAt`으로 편집하고 화살표 끝은 함께 이동하지
않습니다. `PathEffectSpec("stroke"|"shadow", ...)`의 폭과 오프셋은 pt이며
실제 네이티브 효과만 사용합니다.