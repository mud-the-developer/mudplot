# Contributing to mudplot

*[한국어 / Korean: CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)*

Keep changes small, reproducible, and spec-first. `FigureSpec` and actions are
the contract shared by the Python API, dashboard, saved JSON, and future
non-Python clients.

## Setup

Requirements: Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/mud-the-developer/mudplot.git
cd mudplot
uv sync --extra dev
```

For real-browser editor tests:

```bash
uv sync --extra dev --extra browser
uv run playwright install chromium
```

TeX-dependent tests skip when no TeX engine is installed. CI runs the normal
PGF suite with Tectonic/pdflatex; the scheduled/release matrix also covers
LuaLaTeX, BibTeX, and biber.

## Before opening a pull request

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q -m "not browser"
uv run python scripts/check_schema_sync.py
```

If Chromium is installed, also run:

```bash
uv run pytest -q tests/test_editor_browser.py
uv run python scripts/editor_smoke_test.py
```

## Project rules

- Keep the pure core dependency-free. `spec`, actions, reducer, store, IO,
  validation, schema generation, and TeX sizing must import without NumPy or
  Matplotlib. NumPy belongs to colour effects; Matplotlib belongs to rendering.
- Route state changes through actions and `reduce()`; do not create a second
  mutation path just for the dashboard or fluent API.
- Preserve configured physical output size by default. Cropping is explicit
  (`tight=True`).
- Prefer stdlib, native Matplotlib, and existing project patterns. Do not add a
  dependency or abstraction for one small use case.
- Keep DOI/arXiv/reference resolution deterministic and offline.
- Add one focused regression test for a bug or non-trivial branch. Add a
  cross-module consistency test when a feature has multiple registries or
  generated representations.
- Update both English and Korean user-facing docs when behavior changes.
- Record user-visible changes under `CHANGELOG.md`'s **Unreleased** section.

## Schema and generated docs

Changes to spec fields, actions, capabilities, journals, or layer metadata may
require regenerating checked-in contracts:

```bash
uv run python -m mudplot schema --out schemas/figure_spec.schema.json
uv run python -m mudplot capabilities > schemas/capabilities.json
uv run python -m mudplot docs --out docs/REFERENCE.md
uv run python scripts/check_schema_sync.py
```

Do not edit generated files by hand. The final command reproduces them in a
temporary directory and fails on drift.

## Demos and dashboard

```bash
uv run python -m scripts.render_docs_demo
uv run python -m dashboard --out /tmp/mudplot-dashboard
uv run python -m dashboard serve
```

Demo data must be deterministic and synthetic; seed random generators. Avoid
committing regenerated binary assets unless the visible output intentionally
changed.

See [`DESIGN.md`](DESIGN.md) for architecture and
[`ROADMAP.md`](ROADMAP.md) for prioritized work.
