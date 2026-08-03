import argparse
import subprocess
import sys
from pathlib import Path


def _resolve_project_root() -> Path:
    """Resolve the root of the repository being checked.

    Under pre-commit, this script runs from an isolated, per-hook virtualenv
    (typically under ~/.cache/pre-commit/...), so `Path(__file__)` points at
    *this package's own* install location, never at the repository the user
    is committing to. pre-commit always invokes hooks with the working
    directory set to the top level of the repository under test, so
    `Path.cwd()` is the correct anchor, not this file's location.

    We cross-check against `git rev-parse --show-toplevel` where git is
    available, since that's the authoritative answer and lets us warn if the
    two ever disagree instead of quietly measuring/writing to the wrong
    place.
    """
    cwd = Path.cwd().resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
        )
    except FileNotFoundError:
        return cwd

    if result.returncode != 0:
        # Not inside a git working tree (or git unavailable). cwd is the
        # only signal we have, which is what pre-commit gives us anyway.
        return cwd

    git_root = Path(result.stdout.strip()).resolve()
    if git_root != cwd:
        print(
            f"Warning: current directory ({cwd}) is not the git repository "
            f"root ({git_root}); using the git root for coverage."
        )
    return git_root


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to test (default: run all tests)",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum required coverage percentage (default: 80)",
    )
    parser.add_argument(
        "--add-opts",
        nargs="*",
        default=[],
        help="Additional options to pass to pytest",
    )
    args = parser.parse_args(argv)

    # Determine the project root directory: the repository being checked,
    # not the location this script happens to be installed at.
    project_root = _resolve_project_root()

    # Build the command
    cmd = (
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=" + str(project_root),
            "--cov-report=term",
            "--cov-report=xml:" + str(project_root / "coverage.xml"),
        ]
        + list(args.files)
        + args.add_opts
    )

    try:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            return result.returncode

        # Parse coverage from XML report
        coverage_file = project_root / "coverage.xml"
        if not coverage_file.exists():
            print(
                f"Error: coverage.xml not found at {coverage_file}. "
                "Coverage collection may have failed, or no tests were "
                f"collected under project root {project_root}."
            )
            return 1

        import xml.etree.ElementTree as ET

        tree = ET.parse(coverage_file)
        root = tree.getroot()
        line_rate = float(root.get("line-rate", 0))
        coverage = line_rate * 100

        print(f"\nCoverage: {coverage:.1f}%")
        print(f"Required: {args.min_coverage:.1f}%")

        if coverage < args.min_coverage:
            print(
                f"Error: Coverage {coverage:.1f}% is below required {args.min_coverage:.1f}%"
            )
            return 1

        print("Coverage requirement met!")
        return 0

    except FileNotFoundError:
        print(
            "Error: pytest or coverage not found. Please install with: pip install pytest pytest-cov"
        )
        return 1
    except ET.ParseError as e:
        print(f"Error: Could not parse coverage XML: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
