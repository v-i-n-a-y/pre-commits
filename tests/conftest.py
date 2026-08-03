import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def run_hook():
    """Run a hook's console entry point the same way pre-commit does: as a
    subprocess with its own argv and cwd, not an in-process function call.
    """

    def _run(module: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", f"hooks.{module}", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    return _run


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES
