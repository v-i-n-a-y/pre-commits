import argparse
from pathlib import Path


def _fix(path: Path) -> bool:
    try:
        original = path.read_bytes()
    except OSError:
        return False
    if not original:
        return False
    fixed = original.rstrip(b"\r\n") + b"\n"
    if fixed == original:
        return False
    path.write_bytes(fixed)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ensure files end with a single newline")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    changed = [f for f in args.files if _fix(Path(f))]
    if changed:
        print("Fixed end-of-file newline:")
        for f in changed:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
