import json

NOTEBOOK = {
    "cells": [
        {
            "cell_type": "code",
            "execution_count": 3,
            "metadata": {"collapsed": False, "scrolled": True},
            "outputs": [{"output_type": "stream", "text": ["hello\n"]}],
            "source": ["print('hello')"],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# Title"],
        },
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"version": "3.11.0"},
        "widgets": {"state": {}},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


def _write_notebook(path, notebook=NOTEBOOK):
    path.write_text(json.dumps(notebook), encoding="utf-8")


def test_strips_outputs_and_execution_count(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)

    result = run_hook("nbstripout", [str(nb)], cwd=tmp_path)

    assert result.returncode == 1
    stripped = json.loads(nb.read_text(encoding="utf-8"))
    code_cell = stripped["cells"][0]
    assert code_cell["outputs"] == []
    assert code_cell["execution_count"] is None


def test_strips_volatile_metadata(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)

    run_hook("nbstripout", [str(nb)], cwd=tmp_path)

    stripped = json.loads(nb.read_text(encoding="utf-8"))
    assert "collapsed" not in stripped["cells"][0]["metadata"]
    assert "scrolled" not in stripped["cells"][0]["metadata"]
    assert "widgets" not in stripped["metadata"]
    assert "language_info" not in stripped["metadata"]


def test_idempotent_on_already_clean_notebook(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)
    run_hook("nbstripout", [str(nb)], cwd=tmp_path)

    result = run_hook("nbstripout", [str(nb)], cwd=tmp_path)

    assert result.returncode == 0


def test_keep_output_flag_preserves_outputs(tmp_path, run_hook):
    nb = tmp_path / "nb.ipynb"
    _write_notebook(nb)

    run_hook("nbstripout", ["--keep-output", str(nb)], cwd=tmp_path)

    stripped = json.loads(nb.read_text(encoding="utf-8"))
    assert stripped["cells"][0]["outputs"] != []


def test_ignores_non_ipynb_files(tmp_path, run_hook):
    f = tmp_path / "notebook.txt"
    f.write_text(json.dumps(NOTEBOOK), encoding="utf-8")

    result = run_hook("nbstripout", [str(f)], cwd=tmp_path)

    assert result.returncode == 0
    assert json.loads(f.read_text(encoding="utf-8")) == NOTEBOOK
