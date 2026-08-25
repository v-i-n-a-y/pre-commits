import json

NOTEBOOK = {
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Title"]},
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["print('hi')"],
        },
    ],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5,
}


def _write_notebook(path, notebook=NOTEBOOK):
    path.write_text(json.dumps(notebook), encoding="utf-8")


def test_creates_paired_py_file(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)

    result = run_hook("jupytext_sync", [str(nb)], cwd=tmp_path)

    assert result.returncode == 1
    paired = tmp_path / "nb.py"
    assert paired.exists()
    text = paired.read_text(encoding="utf-8")
    assert "# %% [markdown]" in text
    assert "# # Title" in text
    assert "# %%" in text
    assert "print('hi')" in text


def test_idempotent_when_already_synced(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)
    run_hook("jupytext_sync", [str(nb)], cwd=tmp_path)

    result = run_hook("jupytext_sync", [str(nb)], cwd=tmp_path)

    assert result.returncode == 0


def test_resyncs_when_notebook_changes(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)
    run_hook("jupytext_sync", [str(nb)], cwd=tmp_path)

    notebook = json.loads(json.dumps(NOTEBOOK))
    notebook["cells"][1]["source"] = ["print('changed')"]
    _write_notebook(nb, notebook)

    result = run_hook("jupytext_sync", [str(nb)], cwd=tmp_path)

    assert result.returncode == 1
    paired = tmp_path / "nb.py"
    assert "print('changed')" in paired.read_text(encoding="utf-8")


def test_ignores_non_ipynb_files(tmp_path, run_hook):
    f = tmp_path / "notebook.txt"
    f.write_text(json.dumps(NOTEBOOK), encoding="utf-8")

    result = run_hook("jupytext_sync", [str(f)], cwd=tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / "notebook.py").exists()
