"""Small semantic checks, not a full assistive-technology certification."""

from xml.etree import ElementTree as ET

import mudplot as mp
import pytest
from dashboard.editor_view import _nav_html, render_app_body


@pytest.mark.parametrize("page,label", [("editor", "Editor"), ("docs", "Docs")])
def test_current_navigation_link_is_exposed_as_the_current_page(page, label):
    links = ET.fromstring(_nav_html(page)).findall("a")
    selected = [link for link in links if link.get("aria-current") == "page"]
    assert len(selected) == 1 and selected[0].text == label


def test_visible_error_has_alert_semantics_and_still_escapes_content():
    spec = mp.plot().spec
    body = render_app_body(spec, [], error="width <bad> must be a number")
    assert '<div class="error" role="alert">' in body
    assert "width &lt;bad&gt; must be a number" in body and "<bad>" not in body
    assert 'role="alert"' not in render_app_body(spec, [])
