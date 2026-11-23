"""Verify the links and assets emitted in the Pages HTML, without a server."""

import os
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Document(HTMLParser):
    def __init__(self, file):
        super().__init__()
        self.ids = set()
        self.links = []
        self.language = None
        self.feed(file.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if element_id := attrs.get("id"):
            self.ids.add(element_id)
        attr = {"a": "href", "link": "href", "img": "src", "script": "src"}.get(tag)
        if attr and (value := attrs.get(attr)):
            self.links.append((tag, value))


def main():
    out = Path(__file__).resolve().parent.parent / "out"
    base = os.environ.get("DOCS_BASE_PATH", "")
    files = {
        file.relative_to(out).as_posix(): Document(file)
        for file in out.rglob("index.html")
        if file.parent == out or file.relative_to(out).parts[0] in ("en", "ko")
    }
    problems = set()
    for required in (
        "index.html",
        "en/index.html",
        "ko/index.html",
        "en/start/install/index.html",
        "ko/start/install/index.html",
    ):
        if required not in files:
            problems.add(f"Missing page: {required}")

    routes = {f"{base}/{key.removesuffix('index.html')}": key for key in files}
    checked_assets = set()
    checked_links = 0
    for route, key in routes.items():
        doc = files[key]
        expected_lang = "ko" if route.startswith(f"{base}/ko/") else "en"
        if doc.language != expected_lang:
            problems.add(f"{route}: expected html lang={expected_lang}")
        for tag, link in doc.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            checked_links += 1
            href = urlsplit(urljoin(route, link))
            path = unquote(href.path)
            if not path.startswith(f"{base}/"):
                problems.add(f"{route}: URL outside export base path: {link}")
                continue
            normalized = path if path.endswith("/") else f"{path}/"
            if normalized in routes:
                if href.fragment and unquote(href.fragment) not in (
                    files[routes[normalized]].ids
                ):
                    problems.add(f"{route}: missing heading/anchor: {link}")
                continue
            target = out / path[len(base) + 1 :]
            if not target.is_file() or not target.resolve().is_relative_to(out):
                problems.add(f"{route}: missing rendered target: {link}")
            elif tag in ("img", "link", "script") or path.startswith(f"{base}/plots/"):
                checked_assets.add(target)
    if not any(asset.suffix == ".css" for asset in checked_assets):
        problems.add("No referenced CSS in the export")
    plots = {file for file in (out / "plots").rglob("*") if file.is_file()}
    if not plots or not plots <= checked_assets:
        problems.add("Missing or unreferenced plot assets in rendered HTML")
    if problems:
        print("\n".join(sorted(problems)), file=sys.stderr)
        return 1
    print(
        f"Verified {len(files)} HTML pages, {checked_links} local URLs and "
        f"{len(checked_assets)} distinct assets under {base or '/'}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
