# mudplot

[한국어](README.ko.md) · [Guide](docs/GUIDE.md) · [Documentation site](https://mud-the-developer.github.io/mudplot/en/)

mudplot is a Python library for scientific figures built on Matplotlib. Save an editable FigureSpec **0.1** alongside publication output, and check colour palettes under documented colour-vision and greyscale conditions.

## Install

Requires **Python 3.11 or later**. From the source checkout, install the engine and renderer:

```sh
python -m pip install '.[render]'
```

The source version is **v2.0.0**. The [GitHub wheel](https://github.com/mud-the-developer/mudplot/releases/download/v2.0.0/mudplot-2.0.0-py3-none-any.whl) is available only after the [GitHub release](https://github.com/mud-the-developer/mudplot/releases/tag/v2.0.0) is published. Releases are GitHub-only; PyPI publishing is not enabled.

## Quickstart

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

Continue with the [installation guide](docs/INSTALL.md), [executable workflows](examples/README.md), [plot gallery](docs/PLOT_GALLERY.md) or [API reference](docs/REFERENCE.md). The source guides work on GitHub before the documentation site is deployed.

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)
