import argparse
import re
from pathlib import Path


def _fix(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    fixed = re.sub(r"[ \t]+([\r\n]|$)", r"\1", original)
    if fixed == original:
        return False
    path.write_text(fixed, encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fix trailing whitespace")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    changed = [f for f in args.files if _fix(Path(f))]
    if changed:
        print("Fixed trailing whitespace:")
        for f in changed:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
