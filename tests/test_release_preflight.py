from pathlib import Path

import mudplot
from scripts.check_release_version import main


def test_release_versions_currently_agree(capsys):
    assert main([f"v{mudplot.__version__}"]) == 0
    assert "release versions agree" in capsys.readouterr().out


def test_release_workflow_cannot_replace_published_assets():
    workflow = (
        Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
    ).read_text(encoding="utf-8")
    publisher = workflow.split("\n  github-release:", 1)[1]
    checkout = publisher.split("actions/checkout@", 1)[1].split("- uses:", 1)[0]
    assert "persist-credentials: false" in checkout
    assert "fetch-depth: 0" in checkout
    assert publisher.index("actions/checkout@") < publisher.index(
        "- name: Create GitHub release"
    )
    publish = publisher.split("- name: Create GitHub release", 1)[1]
    assert "--clobber" not in publish
    assert "gh release upload" not in publish
    assert "immutable" in publish and "exit 1" in publish
    assert "gh release create" in publish and "--verify-tag" in publish
    assert "--notes-from-tag" in publish


def test_release_version_rejects_wrong_tag(capsys):
    assert main(["v9.9.9"]) == 1
    assert f"expected 'v{mudplot.__version__}'" in capsys.readouterr().err
