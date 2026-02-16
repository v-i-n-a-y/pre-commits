import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

HEADER_SCAN_LIMIT = 15
COPYRIGHT_TEMPLATE = '"""\nCopyright {year} {holder}\n"""'

COPYRIGHT_RE = re.compile(
    r"Copyright\s+(?P<year>\d{4})\s+(?P<holder>.+)", re.IGNORECASE
)


def has_copyright(line: str) -> bool:
    return bool(COPYRIGHT_RE.search(line))


def parse_copyright(line: str):
    m = COPYRIGHT_RE.search(line)
    return m.groupdict() if m else None


def build_notice(year: str, holder: str) -> str:
    return COPYRIGHT_TEMPLATE.format(year=year, holder=holder)


def preview(filepath: str, old: str, new: str):
    print(f"\n--- {filepath}")
    print(f"- {old.rstrip()}")
    print(f"+ {new.rstrip()}")


def find_copyright(lines):
    for i in range(min(len(lines), HEADER_SCAN_LIMIT)):
        if has_copyright(lines[i]):
            return i, parse_copyright(lines[i])
    return None, None


def process_python_file(
    filepath: str,
    dry_run: bool,
    update_holder,
    update_year,
    default_year,
    default_holder,
) -> bool:
    """Process a single file. Returns True if file would change."""
    path = Path(filepath)

    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (UnicodeDecodeError, OSError):
        return False

    idx, info = find_copyright(lines)
    changed = False

    if idx is not None:
        if not update_holder and not update_year:
            return False

        year = update_year or info["year"]
        holder = update_holder or info["holder"]
        new_notice = build_notice(year, holder) + "\n"

        if lines[idx] != new_notice:
            changed = True
            if dry_run:
                preview(filepath, lines[idx], new_notice)
            else:
                lines[idx] = new_notice
    else:
        new_notice = build_notice(default_year, default_holder) + "\n\n"
        changed = True
        if dry_run:
            preview(filepath, "(no copyright)", new_notice.strip())
        else:
            lines.insert(0, new_notice)

    if changed and not dry_run:
        path.write_text("".join(lines), encoding="utf-8")

    return changed


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")

    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-holder")
    parser.add_argument("--update-year")

    parser.add_argument("--year", default=str(datetime.now().year))
    parser.add_argument("--holder", required=True)

    args = parser.parse_args(argv)

    any_changed = False

    for filepath in args.files:
        if filepath.endswith(".py"):
            changed = process_python_file(
                filepath,
                args.dry_run,
                args.update_holder,
                args.update_year,
                args.year,
                args.holder,
            )
            any_changed = any_changed or changed

    if args.dry_run and any_changed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

