"""A tiny Markdown -> HTML converter for mudplot's own generated docs.

Not a general-purpose Markdown parser — it only needs to handle the small,
predictable subset that :func:`mudplot.reference_markdown` produces (headers,
bold, inline code, pipe tables, bullet lists, paragraphs). Kept dependency-free
(stdlib only) since the dashboard should stay easy to run anywhere.
"""

from __future__ import annotations

import html
import re

__all__ = ["markdown_to_html"]

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def _inline(text: str) -> str:
    text = html.escape(text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _INLINE_CODE.sub(r"<code>\1</code>", text)
    return text


def _is_table_row(line: str) -> bool:
    return line.strip().startswith("|")


def _is_table_sep(line: str) -> bool:
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", line.strip()))


def _render_table(lines: list[str]) -> str:
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    header, *body = [r for i, r in enumerate(rows) if not _is_table_sep(lines[i])]
    out = ["<table>", "<thead><tr>"]
    out += [f"<th>{_inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_list = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            i += 1
            continue

        if _is_table_row(stripped):
            j = i
            block = []
            while j < len(lines) and _is_table_row(lines[j].strip()):
                block.append(lines[j])
                j += 1
            out.append(_render_table(block))
            i = j
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(stripped[2:])}</li>")
            i += 1
            continue

        if stripped.startswith("_") and stripped.endswith("_") and len(stripped) > 1:
            out.append(f"<p><em>{_inline(stripped[1:-1])}</em></p>")
            i += 1
            continue

        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{_inline(stripped)}</p>")
        i += 1

    if in_list:
        out.append("</ul>")
    return "\n".join(out)
