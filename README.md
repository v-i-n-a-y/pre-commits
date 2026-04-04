# Hooks

A collection of reusable pre-commit hooks for Python projects. Currently includes a copyright header checker, pytest integration, and coverage checking. Designed to be easily extended with additional hooks in the future.

## Installation

Add the hooks repository to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/v-i-n-a-y/hooks
    rev: v0.1.0
    hooks:
      - id: copyright
        args: [--holder, "Your Company"]
```

Then install pre-commit in the target repo

```bash
pre-commit install
pre-commit run --all-files
```

## Available Hooks

### copyright

Ensures all Python files have a copyright header.

**Arguments:**

* holder (required): Default copyright holder
* --year (optional, default current year): Default copyright year
* --dry-run: Show changes without modifying files
* --update-holder: Update the holder in existing headers
* --update-year: Update the year in existing headers

Example Usage:

```bash
pre-commit run copyright-check --all-files --args "--holder 'Your Company'"
```

### ruff-check

Run 'ruff check' for extremely fast Python linting.

**Entry:** `ruff check --force-exclude`

### ruff-format

Format Python code using ruff's formatter.

**Entry:** `ruff format --force-exclude`

### pytest-run

Run pytest to execute tests.

**Entry:** `pytest-run`

**Arguments:**

* files (optional): Specific files or directories to test (default: run all tests)
* --add-opts: Additional options to pass to pytest

Example Usage:

```bash
pre-commit run pytest-run --all-files --args "tests/"
pre-commit run pytest-run --args "--add-opts=-v"
```

### coverage-check

Check test coverage meets a minimum threshold.

**Entry:** `coverage-check`

**Arguments:**

* files (optional): Specific files or directories to test (default: run all tests)
* --min-coverage (optional, default 80): Minimum required coverage percentage
* --add-opts: Additional options to pass to pytest

Example Usage:

```bash
pre-commit run coverage-check --all-files --args "--min-coverage 90"
```

## Adding New Hooks

1. Add a new module under src/hooks/
1. Add a console script entry in pyproject.toml.
1. Add a corresponding entry in .pre-commit-hooks.yaml.

### Contributing
* Fork the repo, create a branch, add your hook or improvements.
* Ensure all hooks pass linting and include meaningful tests.
* Submit a pull request with a clear description.

## License

[MIT License](LICENSE)
