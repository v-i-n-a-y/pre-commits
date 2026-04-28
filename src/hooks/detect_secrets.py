import argparse
import re
from pathlib import Path

# (pattern, label) — ordered from most to least specific
SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN\s+(?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key"),
    (r"gh[pousr]_[A-Za-z0-9_]{36,255}", "GitHub token"),
    (r"xox[baprs]-[0-9A-Za-z\-]{10,}", "Slack token"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API key"),
    (r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "JWT token"),
    (
        r"(?i)(?:api[_\-]?key|api[_\-]?secret|auth[_\-]?token|access[_\-]?token"
        r"|secret[_\-]?key|client[_\-]?secret|private[_\-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9+/\-_]{20,}",
        "Generic secret assignment",
    ),
    (
        r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "Hardcoded password",
    ),
]

_COMPILED = [(re.compile(pat), label) for pat, label in SECRET_PATTERNS]


def _scan(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, matched_text, label) for each hit."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []

    hits = []
    for lineno, line in enumerate(lines, start=1):
        for regex, label in _COMPILED:
            m = regex.search(line)
            if m:
                hits.append((lineno, m.group(0)[:60], label))
                break  # one label per line
    return hits


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scan files for secrets and credentials")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    found_any = False
    for filepath in args.files:
        hits = _scan(Path(filepath))
        if hits:
            found_any = True
            for lineno, snippet, label in hits:
                print(f"{filepath}:{lineno}: [{label}] {snippet!r}")

    if found_any:
        print("\ndetect-secrets: potential secrets found — remove them before committing.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
