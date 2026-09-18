import mudplot
from scripts.check_release_version import main


def test_release_versions_currently_agree(capsys):
    assert main([f"v{mudplot.__version__}"]) == 0
    assert "release versions agree" in capsys.readouterr().out


def test_release_version_rejects_wrong_tag(capsys):
    assert main(["v9.9.9"]) == 1
    assert f"expected 'v{mudplot.__version__}'" in capsys.readouterr().err
