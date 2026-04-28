import argparse
import subprocess


DEFAULT_BRANCHES = ["main", "master"]


def _current_branch() -> str | None:
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Block direct commits to protected branches")
    parser.add_argument(
        "--branch",
        action="append",
        dest="branches",
        metavar="BRANCH",
        help="Protected branch name (repeatable; default: main, master)",
    )
    args = parser.parse_args(argv)

    protected = args.branches or DEFAULT_BRANCHES
    branch = _current_branch()

    if branch in protected:
        print(f"no-commit-to-branch: direct commits to '{branch}' are not allowed.")
        print(f"  Protected branches: {', '.join(protected)}")
        print("  Create a feature branch and open a pull request instead.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
