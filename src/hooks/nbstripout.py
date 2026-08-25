import argparse
import json
from pathlib import Path

# Metadata keys that vary between runs/environments without reflecting a real
# change to the notebook, and so are stripped by default (mirrors
# nbstripout's default behaviour): kernel identity, execution timings, and
# per-cell display state.
_CELL_METADATA_DROP = {"execution", "collapsed", "scrolled"}
_NOTEBOOK_METADATA_DROP = {"widgets"}
_KERNELSPEC_METADATA_DROP = {"language_info"}


def _strip_cell(cell: dict, keep_output: bool, keep_count: bool) -> None:
    if cell.get("cell_type") == "code":
        if not keep_output:
            cell["outputs"] = []
        if not keep_count:
            cell["execution_count"] = None
    metadata = cell.get("metadata")
    if isinstance(metadata, dict):
        for key in _CELL_METADATA_DROP:
            metadata.pop(key, None)


def _strip_notebook(
    notebook: dict, keep_output: bool = False, keep_count: bool = False
) -> bool:
    changed = False
    before = json.dumps(notebook, sort_keys=True)

    for cell in notebook.get("cells", []):
        _strip_cell(cell, keep_output, keep_count)

    metadata = notebook.get("metadata")
    if isinstance(metadata, dict):
        for key in _NOTEBOOK_METADATA_DROP:
            metadata.pop(key, None)
        if not keep_count:
            for key in _KERNELSPEC_METADATA_DROP:
                metadata.pop(key, None)

    after = json.dumps(notebook, sort_keys=True)
    changed = before != after
    return changed


def _process(path: Path, keep_output: bool, keep_count: bool) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
        notebook = json.loads(original)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    if _strip_notebook(notebook, keep_output, keep_count):
        text = json.dumps(notebook, indent=1, ensure_ascii=False)
        text += "\n"
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Strip Jupyter notebook outputs, execution counts, and "
        "run-specific metadata before commit"
    )
    parser.add_argument("files", nargs="*")
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep cell outputs (still strips execution counts/metadata)",
    )
    parser.add_argument(
        "--keep-count",
        action="store_true",
        help="Keep execution counts and kernel language_info",
    )
    args = parser.parse_args(argv)

    changed = [
        f
        for f in args.files
        if f.endswith(".ipynb") and _process(Path(f), args.keep_output, args.keep_count)
    ]
    if changed:
        print("Stripped notebook outputs/metadata:")
        for f in changed:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
