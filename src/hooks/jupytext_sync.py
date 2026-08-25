import argparse
import json
from pathlib import Path

# A self-contained, minimal reimplementation of jupytext's "percent" text
# format (https://jupytext.readthedocs.io), covering only what a diff-review
# pairing hook needs: one round-trippable ".py" sibling per ".ipynb", so
# notebook changes can be reviewed as plain text. It does not aim for byte-
# parity with the real jupytext CLI or its full markdown/light formats.

_CODE_MARKER = "# %%"
_MARKDOWN_MARKER = "# %% [markdown]"


def _paired_path(ipynb_path: Path) -> Path:
    return ipynb_path.with_suffix(".py")


def _cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)
    return source.rstrip("\n")


def _notebook_to_percent(notebook: dict) -> str:
    blocks = []
    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        source = _cell_source(cell)
        if cell_type == "markdown":
            lines = source.split("\n") if source else []
            commented = "\n".join(f"# {line}" if line else "#" for line in lines)
            blocks.append(f"{_MARKDOWN_MARKER}\n{commented}")
        elif cell_type == "code":
            blocks.append(f"{_CODE_MARKER}\n{source}")
        # Other cell types (raw, etc.) are intentionally dropped: they have
        # no natural plain-Python representation.
    return ("\n\n".join(blocks) + "\n") if blocks else ""


def _sync(ipynb_path: Path) -> bool:
    try:
        notebook = json.loads(ipynb_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    text = _notebook_to_percent(notebook)
    paired_path = _paired_path(ipynb_path)

    existing = paired_path.read_text(encoding="utf-8") if paired_path.exists() else None
    if existing == text:
        return False

    paired_path.write_text(text, encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Keep a plain-Python 'percent format' sibling file in "
        "sync with each staged .ipynb notebook, for diff-friendly review"
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    changed = [f for f in args.files if f.endswith(".ipynb") and _sync(Path(f))]
    if changed:
        print("Synced paired .py representation:")
        for f in changed:
            print(f"  {_paired_path(Path(f))}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
