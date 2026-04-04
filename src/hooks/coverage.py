import argparse
import subprocess
import sys
from pathlib import Path


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

    # Determine the project root directory
    script_dir = Path(__file__).resolve()
    project_root = script_dir.parents[2]  # hooks/.. = project root

    # Build the command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=" + str(project_root),
        "--cov-report=term",
        "--cov-report=xml:" + str(project_root / "coverage.xml"),
    ] + list(args.files) + args.add_opts

    try:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            return result.returncode

        # Parse coverage from XML report
        coverage_file = project_root / "coverage.xml"
        if not coverage_file.exists():
            print("Error: coverage.xml not found. Coverage may have failed.")
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
