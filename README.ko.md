# mudplot

[English](README.md) · [가이드](docs/GUIDE.ko.md) · [문서 사이트](https://mud-the-developer.github.io/mudplot/ko/)

mudplot은 Matplotlib 기반 논문용 Python 플로팅 라이브러리입니다. 출판용 출력과 함께 편집 가능한 FigureSpec **0.1**을 저장하고, 명시된 색각·흑백 조건에서 팔레트를 점검할 수 있습니다.

## 설치

**Python 3.11 이상**이 필요합니다. 소스 checkout에서 엔진과 렌더러를 설치하세요.

```sh
python -m pip install '.[render]'
```

현재 소스 버전은 **v2.0.0**입니다. [GitHub wheel](https://github.com/mud-the-developer/mudplot/releases/download/v2.0.0/mudplot-2.0.0-py3-none-any.whl)은 [GitHub 릴리스](https://github.com/mud-the-developer/mudplot/releases/tag/v2.0.0)가 게시된 뒤에 받을 수 있습니다. GitHub에만 배포하며 PyPI 게시 기능은 활성화하지 않았습니다.

## 빠른 시작

```python
import matplotlib.pyplot as plt
import mudplot as mp

data = {"voltage": [1, 2, 3], "current": [2, 4, 3], "order": ["synthetic"] * 3}
fig = (
    mp.plot(data)
    .line(x="voltage", y="current", group="order")
    .labels(x="Voltage (mV)", y="Current (μA)")
    .theme("paper").journal("nature")
    .save("fig.pdf")
)
plt.close(fig)
```

[설치 가이드](docs/INSTALL.ko.md), [실행 가능한 워크플로](examples/README.ko.md), [플롯 갤러리](docs/PLOT_GALLERY.md), [API 레퍼런스(영어)](docs/REFERENCE.md)에서 계속 살펴보세요. 문서 사이트가 배포되기 전에도 GitHub에서 원본 가이드를 볼 수 있습니다.

[기여](CONTRIBUTING.ko.md) · [보안](SECURITY.ko.md) · [MIT 라이선스](LICENSE)
