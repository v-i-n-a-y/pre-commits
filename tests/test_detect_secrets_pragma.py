"""The hook ignored `# pragma: allowlist secret`, the inline marker Yelp's
detect-secrets honours, so every such annotation in a consuming repo was
inert and the only suppression route was the baseline file.
"""


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_pragma_suppresses_the_finding_on_its_line(tmp_path, run_hook):
    _write(tmp_path, "conf.py", 'password = "LoadTest!2026x"  # pragma: allowlist secret\n')

    result = run_hook("detect_secrets", ["conf.py"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout
    assert "Hardcoded password" not in result.stdout


def test_pragma_is_case_insensitive_and_tolerates_spacing(tmp_path, run_hook):
    _write(tmp_path, "conf.py", 'api_key = "abcdefghijklmnopqrstuvwx"  # PRAGMA : Allowlist  Secret\n')

    result = run_hook("detect_secrets", ["conf.py"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_pragma_does_not_suppress_other_lines(tmp_path, run_hook):
    _write(
        tmp_path,
        "conf.py",
        'password = "LoadTest!2026x"  # pragma: allowlist secret\n'
        'api_key = "abcdefghijklmnopqrstuvwx"\n',
    )

    result = run_hook("detect_secrets", ["conf.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "Generic secret assignment" in result.stdout
    assert "Hardcoded password" not in result.stdout


def test_pragma_line_is_not_written_into_a_baseline(tmp_path, run_hook):
    _write(tmp_path, "conf.py", 'password = "LoadTest!2026x"  # pragma: allowlist secret\n')

    result = run_hook(
        "detect_secrets",
        ["conf.py", "--baseline", "b.json", "--update-baseline"],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout
    assert "conf.py" not in (tmp_path / "b.json").read_text()
