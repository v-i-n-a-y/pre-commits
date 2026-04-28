import argparse
import re
import sys
from pathlib import Path

DEFAULT_TYPES = [
    "feat", "fix", "docs", "style", "refactor",
    "test", "chore", "perf", "ci", "build", "revert",
]

# <type>[(<scope>)][!]: <description>
# Followed optionally by a blank line and body/footers.
_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?\s*:\s*(?P<desc>.+)"
)


def _first_line(msg: str) -> str:
    for line in msg.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate commit message against the Conventional Commits spec",
    )
    parser.add_argument("commit_msg_file", nargs="?", help="Path to the commit message file")
    parser.add_argument(
        "--types",
        nargs="+",
        metavar="TYPE",
        help="Extra allowed types (in addition to the standard set)",
    )
    args = parser.parse_args(argv)

    if not args.commit_msg_file:
        parser.print_help()
        return 1

    try:
        raw = Path(args.commit_msg_file).read_text(encoding="utf-8")
    except OSError as e:
        print(f"conventional-commit: could not read commit message file: {e}")
        return 1

    subject = _first_line(raw)
    if not subject:
        print("conventional-commit: commit message is empty.")
        return 1

    allowed_types = DEFAULT_TYPES + (args.types or [])
    m = _PATTERN.match(subject)

    if not m:
        _fail(subject, allowed_types)
        return 1

    commit_type = m.group("type")
    if commit_type not in allowed_types:
        print(f"conventional-commit: unknown type '{commit_type}'.")
        print(f"  Allowed types: {', '.join(allowed_types)}")
        _fail(subject, allowed_types)
        return 1

    return 0


def _fail(subject: str, allowed_types: list[str]) -> None:
    print(f"conventional-commit: invalid commit message: {subject!r}")
    print()
    print("  Expected format:  <type>[(<scope>)][!]: <description>")
    print(f"  Allowed types:    {', '.join(allowed_types)}")
    print()
    print("  Examples:")
    print("    feat: add login page")
    print("    fix(auth): handle token expiry")
    print("    chore!: drop Python 3.8 support")


if __name__ == "__main__":
    raise SystemExit(main())
