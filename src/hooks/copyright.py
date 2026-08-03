import argparse
import re
from datetime import datetime
from pathlib import Path

from hooks._binary import is_binary

HEADER_SCAN_LIMIT = 20
DEFAULT_YEAR = str(datetime.now().year)

COPYRIGHT_RE = re.compile(
    r"Copyright\s+(?P<year>\d{4})\s+(?P<holder>.+)", re.IGNORECASE
)

# Named comment style presets — templates use {year} and {holder}.
COMMENT_STYLES: dict[str, str] = {
    "hash":        "# Copyright {year} {holder}",
    "doubleslash": "// Copyright {year} {holder}",
    "docstring":   '"""\nCopyright {year} {holder}\n"""',
    "slashstar":   "/*\n * Copyright {year} {holder}\n */",
    "bat":         ":: Copyright {year} {holder}",
    "html":        "<!-- Copyright {year} {holder} -->",
    "sql":         "-- Copyright {year} {holder}",
}

# Maps file extension (lowercase) to a key in COMMENT_STYLES.
EXT_STYLE: dict[str, str] = {
    # Hash-comment languages
    ".py":     "hash",
    ".pyi":    "hash",
    ".sh":     "hash",
    ".bash":   "hash",
    ".zsh":    "hash",
    ".fish":   "hash",
    ".rb":     "hash",
    ".yaml":   "hash",
    ".yml":    "hash",
    ".toml":   "hash",
    ".r":      "hash",
    ".pl":     "hash",
    ".pm":     "hash",
    ".tf":     "hash",
    ".tfvars": "hash",
    # Double-slash languages
    ".rs":     "doubleslash",
    ".go":     "doubleslash",
    ".java":   "doubleslash",
    ".js":     "doubleslash",
    ".ts":     "doubleslash",
    ".jsx":    "doubleslash",
    ".tsx":    "doubleslash",
    ".c":      "doubleslash",
    ".cpp":    "doubleslash",
    ".cc":     "doubleslash",
    ".cxx":    "doubleslash",
    ".h":      "doubleslash",
    ".hpp":    "doubleslash",
    ".hxx":    "doubleslash",
    ".cs":     "doubleslash",
    ".swift":  "doubleslash",
    ".kt":     "doubleslash",
    ".kts":    "doubleslash",
    ".scala":  "doubleslash",
    ".dart":   "doubleslash",
    ".m":      "doubleslash",
    ".mm":     "doubleslash",
    ".groovy": "doubleslash",
    ".gradle": "doubleslash",
    ".proto":  "doubleslash",
    ".php":    "doubleslash",
    # Batch / Windows scripts
    ".bat":    "bat",
    ".cmd":    "bat",
    # Markup
    ".html":   "html",
    ".htm":    "html",
    ".xml":    "html",
    ".svg":    "html",
    # Double-dash languages
    ".sql":    "sql",
    ".lua":    "sql",
    ".hs":     "sql",
    ".lhs":    "sql",
    ".elm":    "sql",
}


def _resolve_template(ext: str, style: str | None, template: str | None) -> str | None:
    if template:
        return template
    style_name = style or EXT_STYLE.get(ext)
    if style_name:
        return COMMENT_STYLES.get(style_name)
    return None


def _insert_index(lines: list[str]) -> int:
    """Return the line index at which to prepend the copyright notice.

    Skips shebang lines and Python/Ruby encoding declarations so they remain first.
    """
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if i < len(lines) and re.match(r"\s*#.*coding[:=]", lines[i]):
        i += 1
    return i


def _find_copyright(lines: list[str]) -> int | None:
    for i in range(min(len(lines), HEADER_SCAN_LIMIT)):
        if COPYRIGHT_RE.search(lines[i]):
            return i
    return None


def _process_file(
    filepath: str,
    template: str,
    dry_run: bool,
    update_year: str | None,
    update_holder: str | None,
    default_year: str,
    default_holder: str,
) -> bool:
    """Return True if the file was changed (or would change under --dry-run)."""
    path = Path(filepath)
    if is_binary(path):
        print(f"copyright-check: skipping '{filepath}' (binary content detected)")
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (UnicodeDecodeError, OSError):
        return False

    idx = _find_copyright(lines)
    changed = False

    if idx is not None:
        if not update_year and not update_holder:
            return False

        def _sub(m: re.Match) -> str:
            year = update_year or m.group("year")
            holder = (update_holder or m.group("holder")).strip()
            return f"Copyright {year} {holder}"

        new_line = COPYRIGHT_RE.sub(_sub, lines[idx])
        if new_line != lines[idx]:
            changed = True
            if dry_run:
                print(f"\n--- {filepath}")
                print(f"- {lines[idx].rstrip()}")
                print(f"+ {new_line.rstrip()}")
            else:
                lines[idx] = new_line
    else:
        notice = template.format(year=default_year, holder=default_holder)
        # Ensure one blank line between the notice block and the rest of the file.
        insert_at = _insert_index(lines)
        sep = "\n" if lines[insert_at:] else ""
        notice_block = notice + "\n" + sep
        changed = True
        if dry_run:
            print(f"\n--- {filepath}")
            print(f"+ {notice}")
        else:
            lines.insert(insert_at, notice_block)

    if changed and not dry_run:
        path.write_text("".join(lines), encoding="utf-8")

    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Add or update copyright headers across many languages.",
    )
    parser.add_argument("files", nargs="*")
    parser.add_argument("--holder", required=True, help="Copyright holder name")
    parser.add_argument("--year", default=DEFAULT_YEAR, help="Year for new notices")
    parser.add_argument("--update-year", metavar="YEAR", help="Replace year in existing notices")
    parser.add_argument("--update-holder", metavar="HOLDER", help="Replace holder in existing notices")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--style",
        choices=list(COMMENT_STYLES),
        help=(
            "Comment style preset (overrides built-in extension map). "
            f"Available: {', '.join(COMMENT_STYLES)}"
        ),
    )
    parser.add_argument(
        "--template",
        metavar="TMPL",
        help=(
            'Raw comment template with {year} and {holder} placeholders, '
            'e.g. "// Copyright {year} {holder}". Overrides --style and built-in map.'
        ),
    )
    args = parser.parse_args(argv)

    any_changed = False

    for filepath in args.files:
        ext = Path(filepath).suffix.lower()
        tmpl = _resolve_template(ext, args.style, args.template)
        if tmpl is None:
            print(
                f"copyright-check: skipping '{filepath}' "
                f"(no style for extension '{ext}'; pass --style or --template)"
            )
            continue

        changed = _process_file(
            filepath,
            tmpl,
            args.dry_run,
            args.update_year,
            args.update_holder,
            args.year,
            args.holder,
        )
        any_changed = any_changed or changed

    if args.dry_run and any_changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
