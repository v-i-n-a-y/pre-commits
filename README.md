# Hooks

A collection of reusable pre-commit hooks for Python projects. Currently includes a copyright header checker. Designed to be easily extended with additional hooks in the future.

## Installation

Add the hooks repository to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/v-i-n-a-y/hooks
    rev: v0.1.2
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


Example Usage

```bash
pre-commit run copyright-check --all-files --args "--holder 'Your Company'"
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
