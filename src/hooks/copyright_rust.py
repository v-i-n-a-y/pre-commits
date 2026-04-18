#!/usr/bin/env python3
"""Copyright header check/fix for Rust files."""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

HEADER_SCAN_LIMIT = 20
COPYRIGHT_TEMPLATE = "//! Copyright {year} Evandor Limited\n//! All Rights Reserved\n//! Contact: info@evandor.co.uk\n"

COPYRIGHT_DEFAULT_YEAR = str(datetime.now().year)

COPYRIGHT_RE = re.compile(
    r"Copyright\s+(?P<year>\d{4})\s+Evandor\s+Limited", re.IGNORECASE
)


def has_copyright(line: str) -> bool:
    return bool(COPYRIGHT_RE.search(line))


def parse_copyright(line: str):
    m = COPYRIGHT_RE.search(line)
    if m:
        return {"year": m.group("year")}
    return None


def build_notice(year: str) -> str:
    return COPYRIGHT_TEMPLATE.format(year=year)


def preview(filepath: str, old: str, new: str):
    print(f"\n--- {filepath}")
    print(f"- {old.rstrip()}")
    print(f"+ {new.rstrip()}")


def find_copyright(lines):
    """Find copyright notice in header (first N lines)."""
    for i in range(min(len(lines), HEADER_SCAN_LIMIT)):
        if has_copyright(lines[i]):
            return i, parse_copyright(lines[i])
    return None, None


def process_rust_file(
    filepath: str,
    dry_run: bool,
    update_holder: bool,
    update_year: bool,
    default_year: str,
) -> bool:
    """Process a single Rust file. Returns True if file would change."""
    path = Path(filepath)

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
    except (UnicodeDecodeError, OSError):
        return False

    idx, info = find_copyright(lines)
    changed = False

    if idx is not None:
        if not update_holder and not update_year:
            return False

        year = update_year or info["year"]
        new_notice = build_notice(year)

        if lines[idx] != new_notice:
            changed = True
            if dry_run:
                preview(filepath, lines[idx], new_notice)
            else:
                lines[idx] = new_notice
        else:
            new_notice = build_notice(COPYRIGHT_DEFAULT_YEAR)
        changed = True
        if dry_run:
            preview(filepath, "(no copyright)", new_notice.strip())
        else:
            # Insert after module docstring if present, otherwise at top
            insert_idx = 0
            for i, line in enumerate(lines[:HEADER_SCAN_LIMIT]):
                if line.strip().startswith("//!") or line.strip().startswith('//!'):
                    insert_idx = i + 1
                    while insert_idx < len(lines) and (lines[insert_idx].strip().startswith("//!") or lines[insert_idx].strip().startswith("//!")):
                        insert_idx += 1
                    break
            lines.insert(insert_idx, new_notice)

    if changed and not dry_run:
        path.write_text("".join(lines), encoding="utf-8")

    return changed


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")

    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-year")

    parser.add_argument("--year", default=COPYRIGHT_DEFAULT_YEAR)

    args = parser.parse_args(argv)

    any_changed = False

    for filepath in args.files:
        if filepath.endswith(".rs"):
            changed = process_rust_file(
                filepath,
                args.dry_run,
                False,  # update_holder (not supported for Rust)
                args.update_year,
                args.year,
            )
            any_changed = any_changed or changed

    if args.dry_run and any_changed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
