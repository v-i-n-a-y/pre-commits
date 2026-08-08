import argparse
import fnmatch
import subprocess
from pathlib import Path

# gitignore(5): a pattern is anchored to the directory containing the
# .gitignore file only when it has a separator "at the beginning or middle"
# of the pattern. A separator at the *end only* (a directory-only marker,
# e.g. "core/") does not anchor anything — the pattern still matches a
# directory of that name at any depth below the .gitignore. So the line that
# actually matters here is "does the pattern contain a slash once a single
# trailing slash is removed", not "does the pattern contain a slash". A bare
# "core/" is exactly as dangerous as a bare "core" and must be caught too.


def _iter_patterns(lines: list[str]):
    """Yield (line_number, pattern) for each line that is a plain pattern:
    not blank, not a comment, not a negation.

    This does not attempt full gitignore escaping (e.g. "\\#" for a literal
    leading hash) — those are rare enough in practice that treating them as
    comments/negations is an acceptable simplification for a guard hook.
    """
    for lineno, raw in enumerate(lines, start=1):
        pattern = raw.strip()
        if not pattern or pattern.startswith("#") or pattern.startswith("!"):
            continue
        yield lineno, pattern


def _unanchored_glob(pattern: str) -> str | None:
    """Return the pattern to match against a directory *name* if `pattern`
    is unanchored (no slash other than an optional trailing one), else None.
    """
    body = pattern[:-1] if pattern.endswith("/") else pattern
    if "/" in body:
        return None
    return body


def _tracked_files() -> list[str]:
    # -z: NUL-separated, unquoted paths. Without it, git quotes any path
    # containing a non-ASCII byte (core.quotePath defaults to true) as
    # e.g. '"datasphere/core/...Eyjafjallaj\303\266kull...webp"', which
    # would otherwise be split into a bogus top-level '"datasphere'
    # directory and silently corrupt every path under it.
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [entry for entry in result.stdout.split("\0") if entry]


def _discover_gitignore_files(tracked_files: list[str]) -> list[str]:
    """.gitignore files tracked anywhere in the repo, for a whole-repo run
    when no explicit files are given (typical of a manual invocation rather
    than pre-commit's changed-file selection)."""
    return [
        f for f in tracked_files if f == ".gitignore" or f.endswith("/.gitignore")
    ]


def _scope_root(gitignore_path: str) -> str:
    """POSIX directory containing `gitignore_path`, relative to the
    repository root ("" for a top-level .gitignore). Patterns in that file
    with no anchoring slash can match a directory anywhere below this root,
    never above it or outside it."""
    return gitignore_path.rsplit("/", 1)[0] if "/" in gitignore_path else ""


def _tracked_directories(tracked_files: list[str], scope_root: str) -> set[str]:
    """Directory paths (POSIX, relative to the repo root) that contain at
    least one tracked file, strictly below `scope_root`. Excludes
    `scope_root` itself: an unanchored pattern in a .gitignore only reaches
    directories *below* the file, not the directory the file lives in.
    """
    prefix = f"{scope_root}/" if scope_root else ""
    dirs: set[str] = set()
    for filepath in tracked_files:
        if prefix and not filepath.startswith(prefix):
            continue
        parts = filepath.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    return dirs


def _check_gitignore(gitignore_path: str, tracked_files: list[str]) -> list[str]:
    """Return one formatted finding line per unanchored pattern that matches
    an existing tracked directory."""
    try:
        lines = Path(gitignore_path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    scope_root = _scope_root(gitignore_path)
    candidate_dirs = _tracked_directories(tracked_files, scope_root)
    # Match against directory *names*, not full paths — an unanchored
    # pattern is checked against each path segment independently.
    by_name: dict[str, list[str]] = {}
    for d in candidate_dirs:
        by_name.setdefault(d.rsplit("/", 1)[-1], []).append(d)

    findings = []
    for lineno, pattern in _iter_patterns(lines):
        glob = _unanchored_glob(pattern)
        if glob is None:
            continue
        # Wildcards are matched, not skipped. Skipping every wildcard line
        # outright would wave through a genuinely dangerous pattern like a
        # bare "build*" that happens to collide with a tracked "build"
        # directory, while a harmless, wildcard-only pattern like "*.core"
        # simply never matches any real directory name and is silent on its
        # own merits. fnmatch reproduces gitignore's single-segment glob
        # semantics (*, ?, [seq]) closely enough for this purpose; it does
        # not replicate gitignore's backslash-escaping of literal wildcard
        # characters, which is rare enough to accept as a gap here.
        matches = sorted(
            name
            for name in by_name
            if fnmatch.fnmatchcase(name, glob)
        )
        matched_dirs = sorted(d for name in matches for d in by_name[name])
        if matched_dirs:
            plural = "y" if len(matched_dirs) == 1 else "ies"
            findings.append(
                f"{gitignore_path}:{lineno}: '{pattern}' matches tracked "
                f"director{plural}: {', '.join(matched_dirs)}"
            )
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Flag .gitignore patterns with no anchoring slash that match an "
            "existing tracked directory name, since git ignores every new "
            "file created under a directory matched this way with no error "
            "or warning."
        )
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    tracked_files = _tracked_files()
    gitignore_files = args.files or _discover_gitignore_files(tracked_files)

    all_findings: list[str] = []
    for gitignore_path in gitignore_files:
        all_findings.extend(_check_gitignore(gitignore_path, tracked_files))

    if all_findings:
        for finding in all_findings:
            print(finding)
        print(
            "\ngitignore-shadow-check: these patterns have no anchoring slash, so "
            "they match the named directory at any depth, not just the file the "
            "pattern was meant for. Every new file created under a matched "
            "directory is silently untracked: it never appears in 'git status' "
            "and 'git add .' skips it with no error.\n"
            "  Anchor the pattern to the exact path instead, e.g. "
            "'path/to/name' rather than a bare 'name'."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
