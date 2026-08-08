"""gitignore-shadow-check guards against MVP#370: a gitignore pattern with
no anchoring slash matches a file *or directory* of that name at any depth,
not just the file it was written for. A bare "core" line meant to ignore a
stray core dump also matched a tracked "datasphere/core" directory, silently
untracking every new file created under it — no error, no warning, nothing
in "git status". Already-tracked files inside kept working normally, which
is what let it stand for hours before anyone noticed.
"""

import subprocess


def _init_git_repo(path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, check=True)


def _write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _track(root, *names):
    subprocess.run(["git", "add", *names], cwd=root, check=True)


# ── The real MVP#370 case ────────────────────────────────────────────────


def test_bare_pattern_matching_a_tracked_directory_is_flagged(tmp_path, run_hook):
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py")
    _write(tmp_path, ".gitignore", "core\ncore.[0-9]*\n*.core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert ".gitignore:1: 'core' matches tracked directory: datasphere/core" in result.stdout


def test_anchored_pattern_to_the_exact_path_is_not_flagged(tmp_path, run_hook):
    """The actual fix landed in MVP: anchoring to 'datasphere/core/core'
    instead of a bare 'core'. A pattern containing a slash is matched
    against the path from the repository root, so it cannot also hit the
    directory — this must stay silent."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py")
    _write(tmp_path, ".gitignore", "datasphere/core/core\ncore.[0-9]*\n*.core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── Trailing-slash nuance ────────────────────────────────────────────────


def test_bare_directory_only_pattern_with_trailing_slash_is_flagged(tmp_path, run_hook):
    """A trailing slash alone (no leading or embedded slash) does not anchor
    a pattern per gitignore(5) — it only restricts the match to directories.
    'core/' is exactly as unanchored, and exactly as dangerous, as 'core'."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py")
    _write(tmp_path, ".gitignore", "core/\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert "datasphere/core" in result.stdout


def test_leading_slash_pattern_is_treated_as_anchored(tmp_path, run_hook):
    _init_git_repo(tmp_path)
    _write(tmp_path, "core/settings.py", "\n")
    _track(tmp_path, "core/settings.py")
    _write(tmp_path, ".gitignore", "/core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── Skipped line kinds ───────────────────────────────────────────────────


def test_comments_and_blank_lines_are_skipped(tmp_path, run_hook):
    _init_git_repo(tmp_path)
    _write(tmp_path, "core/settings.py", "\n")
    _track(tmp_path, "core/settings.py")
    _write(tmp_path, ".gitignore", "# ignore core dumps\n\n   \n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_negation_lines_are_skipped(tmp_path, run_hook):
    _init_git_repo(tmp_path)
    _write(tmp_path, "core/settings.py", "\n")
    _track(tmp_path, "core/settings.py")
    _write(tmp_path, ".gitignore", "!core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── Wildcards: matched against real names, not blanket-skipped ─────────────


def test_wildcard_extension_pattern_with_no_matching_directory_is_allowed(tmp_path, run_hook):
    """'*.core' cannot collide with a directory named plainly 'core' (or
    anything else in this tree), so it must stay silent."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py")
    _write(tmp_path, ".gitignore", "*.core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_bare_wildcard_pattern_matching_a_tracked_directory_is_flagged(tmp_path, run_hook):
    """A bare wildcard pattern is not automatically safe: 'build*' still
    matches a tracked directory literally named 'build' the same way git
    would, and must be caught rather than waved through for containing a
    wildcard."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "app/build/output.js", "\n")
    _track(tmp_path, "app/build/output.js")
    _write(tmp_path, ".gitignore", "build*\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert "app/build" in result.stdout


# ── Directory scope ──────────────────────────────────────────────────────


def test_untracked_scratch_directory_never_trips_the_guard(tmp_path, run_hook):
    """Only directories that actually contain a tracked file count. A
    scratch directory that was never 'git add'-ed must not trigger this,
    however it happens to be named."""
    _init_git_repo(tmp_path)
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "scratch.tmp").write_text("\n")
    _write(tmp_path, ".gitignore", "core\n")
    _track(tmp_path, ".gitignore")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_nested_gitignore_only_checked_against_directories_below_it(tmp_path, run_hook):
    """An unanchored pattern in a nested .gitignore only reaches directories
    below that file, never a same-named directory living elsewhere in the
    repo outside its scope."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _write(tmp_path, "backend/other/file.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py", "backend/other/file.py")
    _write(tmp_path, "backend/.gitignore", "core\n")

    result = run_hook("gitignore_shadow", ["backend/.gitignore"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── Path quoting ─────────────────────────────────────────────────────────


def test_non_ascii_tracked_path_does_not_corrupt_directory_detection(tmp_path, run_hook):
    """git quotes and octal-escapes any tracked path containing a non-ASCII
    byte in plain 'git ls-files' output (core.quotePath defaults to true).
    Left unhandled, a quoted path corrupts the leading path component into
    something like '"datasphere', and every real finding under the true
    top-level directory gets missed or duplicated."""
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/img/Eyjafjallajökull.webp", "\n")
    _track(tmp_path, "datasphere/core/img/Eyjafjallajökull.webp")
    _write(tmp_path, ".gitignore", "core\n")

    result = run_hook("gitignore_shadow", [".gitignore"], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert ".gitignore:1: 'core' matches tracked directory: datasphere/core" in result.stdout


# ── Whole-repo default when no files are given ──────────────────────────


def test_no_files_given_discovers_every_tracked_gitignore(tmp_path, run_hook):
    # Tracked before the bad .gitignore line exists, mirroring the real
    # incident: already-tracked files are unaffected by the pattern, which
    # is exactly what made it hard to notice.
    _init_git_repo(tmp_path)
    _write(tmp_path, "datasphere/core/manage.py", "\n")
    _track(tmp_path, "datasphere/core/manage.py")
    _write(tmp_path, ".gitignore", "core\n")
    _track(tmp_path, ".gitignore")

    result = run_hook("gitignore_shadow", [], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert ".gitignore:1: 'core' matches tracked directory: datasphere/core" in result.stdout
