"""no-em-dash guards the house style rule that keeps getting caught by hand,
after the offending commit has already merged: no em dash (—, U+2014)
anywhere in source, comments, or documents. See the module docstring in
hooks/no_em_dash.py for why it only flags that one code point and never
rewrites automatically.
"""


def test_line_with_an_em_dash_is_flagged(tmp_path, run_hook):
    f = tmp_path / "notes.md"
    f.write_text("Two things — a plan and a person — get this done.\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert "Two things" in result.stdout
    assert "no-em-dash" in result.stdout


def test_line_number_is_reported(tmp_path, run_hook):
    f = tmp_path / "notes.md"
    f.write_text("first line is fine\nsecond line has an em dash — right here\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert f"{f}:2:" in result.stdout


def test_file_with_no_em_dash_passes(tmp_path, run_hook):
    f = tmp_path / "notes.md"
    f.write_text("Two things, a plan and a person, get this done.\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_en_dash_is_not_flagged(tmp_path, run_hook):
    """The en dash (–, U+2013) is a different character with its own
    legitimate uses (numeric ranges, minus signs). This hook is scoped to
    the em dash only and must not fire on it."""
    f = tmp_path / "notes.md"
    f.write_text("Valid range: 10–20 kg.\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_hyphen_is_not_flagged(tmp_path, run_hook):
    f = tmp_path / "notes.md"
    f.write_text("A well-formed hyphenated compound-word.\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_multiple_files_are_all_scanned(tmp_path, run_hook):
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n")
    dirty = tmp_path / "dirty.py"
    dirty.write_text("# a note — with an em dash\n")

    result = run_hook("no_em_dash", [str(clean), str(dirty)], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert str(clean) not in result.stdout
    assert f"{dirty}:1:" in result.stdout


def test_multiple_em_dashes_on_one_line_reported_once_per_line(tmp_path, run_hook):
    f = tmp_path / "notes.md"
    f.write_text("first — second — third\n")

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 1, result.stdout
    assert result.stdout.count(f"{f}:1:") == 1


def test_binary_file_is_skipped_not_crashed_on(tmp_path, run_hook):
    f = tmp_path / "image.bin"
    f.write_bytes(bytes(range(256)))

    result = run_hook("no_em_dash", [str(f)], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_no_files_given_passes_cleanly(tmp_path, run_hook):
    result = run_hook("no_em_dash", [], cwd=tmp_path)

    assert result.returncode == 0, result.stdout
