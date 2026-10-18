"""OUT-09: data text/XML/HTML are distinct from explicit trusted PGF TeX."""

import html
import json
import shutil
import subprocess
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from dashboard.editor_view import render_page

TEXTS = [
    "A&B <tag> \"quoted\" 'apostrophe' C:\\probe Ω",
    'safe <script data-probe="inert">window.syntheticProbe=1</script>',
]
URL = "https://example.org/paper?q=%3Ctag%3E&quote=%22#part"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.textareas = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.active = "script"
            self.scripts.append("")
        elif tag == "textarea":
            self.active = "textarea"
            self.textareas.append("")

    def handle_endtag(self, tag):
        if tag in ("script", "textarea"):
            self.active = None

    def handle_data(self, data):
        if self.active == "script":
            self.scripts[-1] += data
        elif self.active == "textarea":
            self.textareas[-1] += data


def plot(text):
    return (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y", label=text, href=URL)
        .labels(title=text)
        .size(10, 6)
    )


@pytest.mark.parametrize("text", TEXTS)
def test_html_text_is_escaped_once_and_json_editor_recovers_exact_value(text):
    spec = plot(text).spec
    body = render_page(spec, [], draft_json=mp.to_json(spec))
    assert html.escape(text) in body
    assert text not in body
    parsed, baseline = PageParser(), PageParser()
    parsed.feed(body)
    baseline.feed(render_page(mp.FigureSpec(), []))
    assert parsed.scripts == baseline.scripts
    values = [
        json.loads(t)
        for t in parsed.textareas
        if t.lstrip().startswith('{"version"')
        or t.lstrip().startswith('{\n  "version"')
    ]
    assert values and mp.from_json(json.dumps(values[0])) == spec


@pytest.mark.parametrize("text", TEXTS)
def test_svg_text_href_and_math_remain_data_not_active_nodes(text, tmp_path):
    output = tmp_path / "figure.svg"
    with plt.rc_context({"svg.fonttype": "none"}):
        plt.close(plot(text).save(str(output)))
    root = ET.fromstring(output.read_text(encoding="utf-8"))
    labels = [
        "".join(node.itertext())
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "text"
    ]
    assert text in labels
    assert all(node.tag.rsplit("}", 1)[-1] != "script" for node in root.iter())
    assert all(
        not key.lower().startswith("on") for node in root.iter() for key in node.attrib
    )
    assert URL in [
        value
        for node in root.iter()
        for key, value in node.attrib.items()
        if key.rsplit("}", 1)[-1] == "href"
    ]


@pytest.mark.skipif(
    shutil.which("pdflatex") is None, reason="explicit TeX text contract needs pdflatex"
)
def test_pgf_explicit_tex_escaping_compiles_and_raw_ampersand_fails(tmp_path):
    with plt.rc_context({"pgf.texsystem": "pdflatex"}):
        with pytest.raises(ValueError, match="alignment tab"):
            plot("A & B").save(str(tmp_path / "invalid.pgf"))
        assert not plt.get_fignums()
        escaped = (
            r"amp \& hash \# percent \% under \_ "
            r"backslash \textbackslash{} \textbf{inert} $x_1$"
        )
        plt.close(plot(escaped).save(str(tmp_path / "figure.pgf")))
    (tmp_path / "paper.tex").write_text(
        r"\documentclass{article}\usepackage[T1]{fontenc}"
        r"\usepackage[paperwidth=14in,paperheight=10in,margin=1in]{geometry}"
        r"\usepackage{pgf}\usepackage{hyperref}"
        r"\begin{document}\input{figure.pgf}\end{document}",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
        cwd=tmp_path,
        capture_output=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout.decode("utf-8", errors="replace")[
        -2000:
    ]
    assert (tmp_path / "paper.pdf").read_bytes().startswith(b"%PDF")


def test_reference_macro_escape_is_rejected_not_promoted_to_tex():
    spec = plot("plain").spec
    spec.panels[0].layers[0].citation = r"key\textbf{inert}"
    issues = mp.validate(spec)
    assert any("citation" in issue for issue in issues)
    with pytest.raises(ValueError, match="citation"):
        mp.render(spec)
