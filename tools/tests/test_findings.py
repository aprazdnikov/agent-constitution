from pathlib import Path

from ac_tools.findings import Check, Finding


def test_render_uses_repo_relative_posix_path(tmp_path: Path) -> None:
    finding = Finding(Check.MANIFEST, tmp_path / "plugins" / "core", "boom")

    assert finding.render(tmp_path) == "[manifest] plugins/core: boom"
