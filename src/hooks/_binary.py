"""Shared helper for detecting binary file content.

Hooks that rewrite files in place — trailing-whitespace, end-of-file-fixer,
mixed-line-endings, copyright-check — must never touch binary content such
as compiled PDFs, images, or archives, because treating binary bytes as text
corrupts them (a stray trailing space stripped from a PDF cross-reference
table, for instance, breaks the file's fixed-width record layout).

pre-commit itself filters files by type (`types: [text]`) before invoking a
hook, and normally keeps binaries away from these hooks. That filter is not
a hard guarantee for the hook itself, though: a caller's own
`.pre-commit-config.yaml` can override `types`/`files` for a hook, or the
installed console-script can be invoked directly outside pre-commit
altogether (for example from a Makefile or CI step). Each rewriting hook
therefore checks file content itself, rather than trusting a caller to have
excluded binaries correctly.

Classification happens in two layers, in order:

1. By filename, via the same `identify` library pre-commit itself uses to
   evaluate `types: [text]`. This is what catches formats like PDF that can
   be entirely printable ASCII (no compressed streams, no embedded fonts) —
   content-sniffing alone would call such a file "text" and still corrupt it
   by, say, stripping a trailing space that is structurally significant
   (e.g. inside a PDF's fixed-width cross-reference table).
2. Where the extension is unrecognised (or absent), by content: a file is
   treated as binary if the first kilobyte contains any byte outside a
   normal set of text characters — the same heuristic `identify` and
   libmagic use as their own content-sniffing fallback.
"""

from pathlib import Path

try:
    from identify.identify import tags_from_filename
except ImportError:  # pragma: no cover - identify is a declared dependency
    tags_from_filename = None

# Bytes considered "text": the handful of control characters that legitimately
# appear in text files (tab, newline, form-feed, escape, ...), the printable
# ASCII range, and the top half of the byte range (so UTF-8- and
# Latin-1-encoded text isn't misclassified). Everything else — most notably
# NUL and other unusual control bytes — marks a file as binary.
_TEXT_BYTES = (
    bytearray([7, 8, 9, 10, 11, 12, 13, 27])
    + bytearray(range(0x20, 0x7F))
    + bytearray(range(0x80, 0x100))
)
_SNIFF_SIZE = 1024


def _is_binary_content(path: Path) -> bool:
    """Content-sniffing fallback for files `identify` can't classify by name.

    Reads only the first kilobyte, so it's cheap to call per file. Files that
    can't be read at all are *not* reported as binary here — callers already
    handle unreadable files (missing, permissions) separately, typically by
    skipping them outright.
    """
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(_SNIFF_SIZE)
    except OSError:
        return False
    return bool(chunk.translate(None, _TEXT_BYTES))


def is_binary(path: Path) -> bool:
    """Best-effort check of whether `path` holds binary (non-text) content."""
    if tags_from_filename is not None:
        tags = tags_from_filename(path.name)
        if "binary" in tags:
            return True
        if "text" in tags:
            return False
        # Unrecognised extension (or none) — fall through to content-sniffing.

    return _is_binary_content(path)
