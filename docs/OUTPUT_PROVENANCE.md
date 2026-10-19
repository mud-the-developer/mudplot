# Optional output provenance

This is an opt-in **separate manifest recipe**, not a new save option or automatic
sidecar. It never adds a timestamp, machine path, or history to PNG/PDF/SVG. Use a
fresh output directory: the example refuses to reuse one rather than overwrite
someone's files.

```python
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
from matplotlib import font_manager

out = Path("synthetic-provenance")
out.mkdir()
spec = mp.plot({"x": [1, 2, 3], "y": [2, 4, 3]}).line("x", "y").size(4, 3).spec
spec.dpi = 100
mp.save_spec(spec, out / "figure.mplot.json")
for fmt in ("png", "pdf", "svg"):
    figure = mp.save(spec, out / f"figure.{fmt}")
    plt.close(figure)


def digest(data):
    return hashlib.sha256(data).hexdigest()


canonical = mp.to_json(spec, indent=None, sort_keys=True).encode("utf-8")
data = json.dumps(spec.data.to_dict(), sort_keys=True, separators=(",", ":"))
font = font_manager.findfont(
    font_manager.FontProperties(family=[spec.theme.font.family])
)
environment = {
    "python": ".".join(map(str, sys.version_info[:3])),
    "system": platform.system(),
    "machine": platform.machine(),
    "mudplot": mp.__version__,
    "versions": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib")},
    "primary_font_sha256": digest(Path(font).read_bytes()),
}
manifest = {
    "spec_version": spec.version,
    "canonical_spec_sha256": digest(canonical),
    "data_sha256": digest(data.encode("utf-8")),
    "environment": environment,
    "environment_sha256": digest(json.dumps(environment, sort_keys=True).encode()),
    "outputs": {path.name: digest(path.read_bytes()) for path in sorted(out.iterdir())},
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

The canonical spec hash is not the pretty JSON file's byte hash; both are present.
Hashes/versions can help compare a fixed environment, but are not an environment
lock or a cross-OS/font/backend byte guarantee. The primary font hash does not
inventory all fallback/TeX fonts or ambient settings. Add those records when the
particular workload needs them; do not silently dump an environment or home path.

Review a manifest before sharing. Hashes are **not anonymization**: small or known
data/spec spaces may be guessable. Rendered files can themselves reveal data.
The example is synthetic and includes no hostname, username, argv, input path,
credentials or environment-variable dump. No optional history/checkpoint API or
mandatory provenance metadata is introduced.
