"""no-em-dash guards a house style rule: no em dash (—, U+2014) anywhere in
source, comments, or documents, because it keeps getting caught by hand after
the fact rather than before a commit lands.

This is deliberately narrow. It flags exactly one code point, U+2014 EM DASH.
It does not touch the visually similar en dash (–, U+2013), which has
legitimate, distinct uses (numeric ranges, minus signs) that this rule was
never aimed at, and it does not touch box-drawing or other unrelated Unicode
punctuation. Widening the match to "anything dash-shaped" would start
rewriting text nobody asked it to touch.

It is also read-only. It reports every match and fails; it does not choose a
replacement, because the correct fix depends on what the em dash was doing in
that sentence (full stop and a new sentence, a comma, a colon where it
introduces a definition or a list). A mechanical substitution, most often a
bare hyphen, tends to change the sentence's meaning rather than preserve it.
"""

import argparse
from pathlib import Path

EM_DASH = "—"


def _scan(path: Path) -> list[tuple[int, str]]:
    """Return (line_number, line) for each line in `path` containing an em
    dash. Files that cannot be read as UTF-8 text are silently skipped, the
    same convention every other scanning hook in this repo follows: binary
    files are not this hook's concern, and pre-commit's own `types: [text]`
    filter keeps them away in normal use."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []
    return [
        (lineno, line) for lineno, line in enumerate(lines, start=1) if EM_DASH in line
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reject em dashes (—, U+2014) in the given files"
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    found_any = False
    for filepath in args.files:
        for lineno, line in _scan(Path(filepath)):
            found_any = True
            print(f"{filepath}:{lineno}: {line.strip()}")

    if found_any:
        print(
            "\nno-em-dash: em dash (—, U+2014) found. Rewrite with real "
            "punctuation instead: a full stop and a new sentence, a comma, "
            "or a colon where it introduces a definition or a list. Do not "
            "swap in a hyphen: it changes what the sentence means rather "
            "than preserving it."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
