"""``.bib`` -> :class:`ReferenceSpec` resolution (P2-1).

mudplot is not a bibliography manager -- ``ReferenceCatalog`` is a minimal,
dependency-free reader for the common subset of BibTeX entry syntax real
``.bib`` files use, whose only job is turning ``@article{key, doi = {...},
...}`` into the citation/href metadata a figure actually needs
(``ReferenceSpec``). It does not resolve cross-references, string macros
(``@string``), or render formatted citations -- that's the *document's*
job, same as everywhere else reference metadata is used in mudplot (see
``mudplot.tex.PREAMBLE``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .spec import ReferenceSpec

__all__ = ["ReferenceCatalog"]


def _skip_braced_block(text: str, start: int) -> int:
    """Index just past the balanced ``{...}`` block opening at ``start``."""
    depth, i, n = 0, start, len(text)
    while i < n:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    i, n = 0, len(body)
    while i < n:
        while i < n and (body[i].isspace() or body[i] == ","):
            i += 1
        j = i
        while j < n and (body[j].isalnum() or body[j] in "_-:."):
            j += 1
        name = body[i:j].strip().lower()
        if not name:
            break
        i = j
        while i < n and body[i].isspace():
            i += 1
        if i >= n or body[i] != "=":
            break  # malformed field -- stop rather than misparse the rest
        i += 1
        while i < n and body[i].isspace():
            i += 1
        if i >= n:
            break
        if body[i] == "{":
            end = _skip_braced_block(body, i)
            value = body[i + 1 : end - 1]
            i = end
        elif body[i] == '"':
            end = body.find('"', i + 1)
            end = n if end == -1 else end
            value = body[i + 1 : end]
            i = end + 1
        else:
            end = i
            while end < n and body[end] not in ",\n":
                end += 1
            value = body[i:end].strip()
            i = end
        fields[name] = " ".join(value.split())
    return fields


def _parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    i, n = 0, len(text)
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        j = at + 1
        while j < n and (text[j].isalnum() or text[j] == "_"):
            j += 1
        entry_type = text[at + 1 : j].strip().lower()
        k = j
        while k < n and text[k].isspace():
            k += 1
        if k >= n or text[k] != "{":
            i = j
            continue
        if entry_type in ("comment", "string", "preamble"):
            # Not an actual reference (a macro definition, a free-text
            # comment, ...) -- skip its whole block so its contents can't
            # be mistaken for a real entry's fields.
            i = _skip_braced_block(text, k)
            continue
        end = _skip_braced_block(text, k)
        body = text[k + 1 : end - 1]
        i = end
        comma = body.find(",")
        if comma == -1:
            continue  # entry with no key/fields at all -- nothing to index
        key = body[:comma].strip()
        if key:
            entries[key] = _parse_fields(body[comma + 1 :])
    return entries


@dataclass
class ReferenceCatalog:
    """A parsed ``.bib`` file: ``catalog[key]`` -> a ready-to-use
    ``ReferenceSpec`` (``citation=key``, ``href`` resolved from the entry's
    ``doi`` field as a ``https://doi.org/...`` link, falling back to its
    ``url`` field, or ``None`` if neither is present).
    """

    entries: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_bib_text(cls, text: str) -> ReferenceCatalog:
        """Parse already-loaded ``.bib`` source text."""
        return cls(entries=_parse_bib(text))

    @classmethod
    def from_bib(cls, path: str | Path) -> ReferenceCatalog:
        """Parse a ``.bib`` file on disk."""
        return cls.from_bib_text(Path(path).read_text(encoding="utf-8"))

    def __len__(self) -> int:
        return len(self.entries)

    def __contains__(self, key: str) -> bool:
        return key in self.entries

    def __iter__(self):
        return iter(self.entries)

    def raw(self, key: str) -> dict[str, str]:
        """The entry's raw BibTeX fields (title/author/year/doi/url/...),
        for anything beyond citation/href -- e.g. a paper-metadata preview
        in an editor.
        """
        if key not in self.entries:
            raise KeyError(f"no BibTeX entry {key!r} (have: {sorted(self.entries)})")
        return dict(self.entries[key])

    def __getitem__(self, key: str) -> ReferenceSpec:
        entry = self.raw(key)
        href = None
        if entry.get("doi"):
            href = f"https://doi.org/{entry['doi']}"
        elif entry.get("url"):
            href = entry["url"]
        return ReferenceSpec(citation=key, href=href)
