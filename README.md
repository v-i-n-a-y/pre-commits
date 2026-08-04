# pre-commits

A collection of reusable [pre-commit](https://pre-commit.com) hooks covering copyright headers, linting, formatting, testing, and coverage — for Python, Rust, and many other languages.

## Quick start

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/v-i-n-a-y/pre-commits
    rev: v0.6.0
    hooks:
      - id: copyright-check
        args: [--holder, "Your Company"]
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-endings
      - id: no-commit-to-branch
      - id: detect-secrets
      - id: conventional-commit
        stages: [commit-msg]
      - id: ruff-check
      - id: ruff-format
      - id: pytest-run
      - id: coverage-check
        args: [--min-coverage, "90"]
```

Then run:

```bash
pre-commit install
pre-commit run --all-files
```

---

## Available hooks

### `copyright-check`

Inserts or updates a copyright header in source files. Supports **50+ file extensions** across all popular languages, with automatic comment style detection per extension.

| Style | Extensions |
|-------|-----------|
| `# ...` | `.py` `.sh` `.bash` `.zsh` `.rb` `.yaml` `.toml` `.tf` and more |
| `// ...` | `.rs` `.go` `.java` `.js` `.ts` `.cpp` `.c` `.h` `.cs` `.swift` `.kt` `.php` and more |
| `/* ... */` | available via `--style slashstar` |
| `:: ...` | `.bat` `.cmd` |
| `<!-- ... -->` | `.html` `.xml` `.svg` |
| `-- ...` | `.sql` `.lua` `.hs` |
| `"""..."""` | available via `--style docstring` |

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--holder` | yes | Copyright holder name |
| `--year` | no (default: current year) | Year used in new notices |
| `--update-year YEAR` | no | Replace the year in existing notices |
| `--update-holder HOLDER` | no | Replace the holder in existing notices |
| `--style NAME` | no | Force a named style for all files (`hash`, `doubleslash`, `slashstar`, `docstring`, `bat`, `html`, `sql`) |
| `--template "..."` | no | Raw format string, e.g. `"// Copyright {year} {holder}"` — overrides everything |
| `--dry-run` | no | Show what would change without modifying files (exits 1 if changes needed) |

Files with an unrecognised extension are skipped with a warning unless `--style` or `--template` is provided.

**Examples:**

```yaml
# Standard usage
- id: copyright-check
  args: [--holder, "Acme Corp"]

# Force a custom comment style for all matched files
- id: copyright-check
  args: [--holder, "Acme Corp", --style, slashstar]

# Fully custom template (e.g. for a non-standard language)
- id: copyright-check
  args: [--holder, "Acme Corp", --template, "/* Copyright {year} {holder} */"]

# Bulk-update the year across the whole repo
- id: copyright-check
  args: [--holder, "Acme Corp", --update-year, "2026"]
```

> **Note:** Shebang lines (`#!/...`) and Python encoding declarations are automatically preserved above the inserted notice.

---

### `ruff-check`

Runs [`ruff check --force-exclude`](https://docs.astral.sh/ruff/) for fast Python linting.

Applies to: `.py`, `.pyi`, `.ipynb`

```yaml
- id: ruff-check
```

---

### `ruff-format`

Runs [`ruff format --force-exclude`](https://docs.astral.sh/ruff/) to format Python code.

Applies to: `.py`, `.pyi`, `.ipynb`

```yaml
- id: ruff-format
```

---

### `pytest-run`

Runs your test suite via `pytest`. Fails the commit if any tests fail.

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--add-opts` | Extra options passed directly to pytest |

**Examples:**

```yaml
- id: pytest-run

# With extra pytest options
- id: pytest-run
  args: [--add-opts, "-v --tb=short"]
```

---

### `coverage-check`

Runs pytest with coverage collection and fails if the line coverage falls below the threshold.

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--min-coverage` | `80` | Minimum required line coverage percentage |
| `--add-opts` | — | Extra options passed to pytest |

**Examples:**

```yaml
- id: coverage-check
  args: [--min-coverage, "90"]
```

---

### `trailing-whitespace`

Strips trailing spaces and tabs from every line. Auto-fixes and returns exit code 1 to trigger re-staging.

```yaml
- id: trailing-whitespace
```

---

### `end-of-file-fixer`

Ensures every file ends with exactly one newline. Auto-fixes and returns exit code 1 to trigger re-staging.

```yaml
- id: end-of-file-fixer
```

---

### `mixed-line-endings`

Detects and normalises mixed CR/LF line endings. Defaults to LF; pass `--eol crlf` for Windows-style endings. Auto-fixes.

```yaml
- id: mixed-line-endings

# Force CRLF instead
- id: mixed-line-endings
  args: [--eol, crlf]
```

---

### `no-commit-to-branch`

Blocks direct commits to protected branches. Defaults to `main` and `master`; use `--branch` to customise.

```yaml
- id: no-commit-to-branch

# Custom protected branches
- id: no-commit-to-branch
  args: [--branch, main, --branch, develop]
```

---

### `detect-secrets`

Scans staged files for hardcoded secrets and credentials without requiring any external tools. Does not auto-fix — secrets must be removed manually.

**Detected patterns:**

| Pattern | Label |
|---------|-------|
| `AKIA[0-9A-Z]{16}` | AWS Access Key ID |
| `-----BEGIN ... PRIVATE KEY-----` | Private key |
| `gh[pousr]_...` | GitHub token |
| `xox[baprs]-...` | Slack token |
| `AIza...` | Google API key |
| `eyJ...` | JWT |
| `sk_live_...`, `rk_live_...` | Stripe live API key |
| `whsec_...` (long, no placeholder wording) | Stripe webhook signing secret |
| `aws_secret_access_key = "..."` / bare 40-char value | AWS secret access key |
| `api_key = "..."`, `secret = "..."` etc. | Generic secret assignment |
| `password = "..."` | Hardcoded password |

Two of these are deliberately narrower than they could be, to avoid failing on test fixtures or unrelated repo content:

- **Stripe:** `sk_test_...` and `rk_test_...` keys are never matched — only `_live_` keys are. Stripe's webhook secret prefix (`whsec_...`) does not encode test vs. live mode, so it cannot be told apart by prefix; instead this only flags values long enough to be a real generated secret that do not contain an obvious placeholder word (`fake`, `placeholder`, `dummy`, `test`, etc.), so that fixtures like `whsec_fake` stay allowed.
- **AWS secret access key:** the bare (unlabelled) match only fires on values in the key's base64 alphabet that are not all-hex (which rules out git/SHA1 hashes) and excludes `/` from the charset (which rules out URL and Helm chart paths). It will not catch a real key sitting in a lockfile or vendored bundle, since nothing distinguishes that from an npm integrity hash at this length — exclude those paths at the `.pre-commit-config.yaml` level instead.

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--baseline PATH` | Suppress findings already recorded in this baseline file |
| `--update-baseline` | Instead of scanning, (re)write `--baseline` from the current findings in the given files (or, with no files given, every git-tracked file) |

A baseline entry only ever matches by content. Each recorded finding is a SHA-256 hash of the exact secret text, keyed to the file it was found in. Editing a baselined file, or a secret changing even slightly, produces a new, unsuppressed finding. A baseline can silence a specific reviewed string, never a whole file or pattern.

```yaml
- id: detect-secrets
  args: [--baseline, .secrets.baseline]
```

Generate or refresh the baseline (review the diff before committing it, since everything it contains is treated as known-safe from then on):

```bash
detect-secrets --update-baseline --baseline .secrets.baseline
```

> **Note:** this is a self-contained baseline format specific to this hook, not the one produced by the separate `detect-secrets` PyPI package. If you already have a `.secrets.baseline` generated by that tool, this hook will not understand it and will say so; regenerate it with the command above.

---

### `conventional-commit`

Validates commit messages against the [Conventional Commits](https://www.conventionalcommits.org) spec. Runs at the `commit-msg` stage.

**Format:** `<type>[(<scope>)][!]: <description>`

**Built-in types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--types` | Extra allowed types in addition to the standard set |

```yaml
- id: conventional-commit
  stages: [commit-msg]

# With custom extra types
- id: conventional-commit
  stages: [commit-msg]
  args: [--types, wip, spike]
```

---

### `rust-fmt`

Formats Rust code via `cargo fmt`. Requires Rust to be installed on the host.

```yaml
- id: rust-fmt
```

---

### `rust-clippy`

Lints Rust code via `cargo clippy`. Requires Rust to be installed on the host.

```yaml
- id: rust-clippy
```

---

## Requirements

- Python ≥ 3.9
- [pre-commit](https://pre-commit.com) installed in the target repo
- Rust toolchain (`cargo`) for `rust-fmt` and `rust-clippy`

## License

[MIT](LICENSE)
