import argparse
from pathlib import Path


def _fix(path: Path, eol: bytes) -> bool:
    try:
        original = path.read_bytes()
    except OSError:
        return False
    if b"\r" not in original:
        return False
    # Normalise all CRLF → LF first, then apply desired eol
    normalised = original.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    fixed = normalised.replace(b"\n", eol) if eol != b"\n" else normalised
    if fixed == original:
        return False
    path.write_bytes(fixed)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Normalise mixed line endings")
    parser.add_argument("files", nargs="*")
    parser.add_argument(
        "--eol",
        choices=["lf", "crlf"],
        default="lf",
        help="Target line ending (default: lf)",
    )
    args = parser.parse_args(argv)

    eol = b"\r\n" if args.eol == "crlf" else b"\n"
    changed = [f for f in args.files if _fix(Path(f), eol)]
    if changed:
        print(f"Normalised line endings to {args.eol.upper()}:")
        for f in changed:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
