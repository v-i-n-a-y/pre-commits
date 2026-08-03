"""coverage-check must resolve the repository being checked, not wherever
this package happens to be installed.

Under pre-commit, `language: python` hooks run from an isolated per-hook
virtualenv (typically under ~/.cache/pre-commit/...), so anchoring off
`Path(__file__)` resolves to *this package's own* install location. That
made `--cov` and the `coverage.xml` path point somewhere unrelated to the
repository under test, so the hook silently measured/reported nothing no
matter how it was invoked (github issue: coverage-check always "passes").
"""

import subprocess
from pathlib import Path

from hooks.coverage import _resolve_project_root


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def test_resolve_project_root_uses_cwd_not_install_location(tmp_path, monkeypatch):
    repo = tmp_path / "target-repo"
    repo.mkdir()
    _init_git_repo(repo)

    monkeypatch.chdir(repo)
    resolved = _resolve_project_root()

    assert resolved == repo.resolve()
    # Must never resolve to this package's own source tree, which is the bug
    # under test: previously it always did, regardless of cwd.
    this_package_root = Path(__file__).resolve().parents[1]
    assert resolved != this_package_root


def test_resolve_project_root_falls_back_to_cwd_outside_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = _resolve_project_root()
    assert resolved == tmp_path.resolve()


def test_resolve_project_root_uses_git_toplevel_from_a_subdirectory(
    tmp_path, monkeypatch
):
    repo = tmp_path / "target-repo"
    subdir = repo / "pkg" / "sub"
    subdir.mkdir(parents=True)
    _init_git_repo(repo)

    monkeypatch.chdir(subdir)
    resolved = _resolve_project_root()

    assert resolved == repo.resolve()


def test_coverage_check_writes_report_under_target_repo_and_passes(tmp_path, run_hook):
    """End-to-end: a throwaway project with 100% covered code must produce
    coverage.xml *inside that project*, not tied to this package's install
    location, and the hook must exit 0."""
    repo = tmp_path / "target-repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "pkg" / "mod.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "test_mod.py").write_text(
        "from pkg.mod import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    _init_git_repo(repo)

    result = run_hook("coverage", ["--min-coverage", "50"], cwd=repo)

    coverage_xml = repo / "coverage.xml"
    assert coverage_xml.exists(), result.stdout + result.stderr
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Coverage requirement met" in result.stdout

    # The report must describe the target repo, not this package.
    this_package_root = str(Path(__file__).resolve().parents[1])
    assert this_package_root not in coverage_xml.read_text()


def test_coverage_check_fails_loudly_below_threshold(tmp_path, run_hook):
    repo = tmp_path / "target-repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "pkg" / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n\n\ndef unused(a):\n    return a * 2\n"
    )
    (repo / "test_mod.py").write_text(
        "from pkg.mod import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    _init_git_repo(repo)

    result = run_hook("coverage", ["--min-coverage", "95"], cwd=repo)

    assert result.returncode == 1
    assert "below required" in result.stdout


def test_coverage_check_fails_loudly_when_no_source_found(tmp_path, run_hook):
    """An empty repository has nothing to cover; the hook must say so
    clearly rather than reporting a misleading 0% or, worse, exiting 0."""
    repo = tmp_path / "empty-repo"
    repo.mkdir()
    _init_git_repo(repo)

    result = run_hook("coverage", [], cwd=repo)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "coverage.xml not found" in combined or "no tests ran" in combined.lower()
