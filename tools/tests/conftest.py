from pathlib import Path

import pytest

from tests.builders import write_repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return write_repo(tmp_path / "repo", {"core": ["alpha"], "postgres": ["beta"]})
