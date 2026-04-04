import argparse
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to test (default: run all tests)",
    )
    parser.add_argument(
        "--add-opts",
        nargs="*",
        default=[],
        help="Additional options to pass to pytest",
    )
    args = parser.parse_args(argv)

    cmd = [sys.executable, "-m", "pytest"] + list(args.files) + args.add_opts

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install it with: pip install pytest")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
