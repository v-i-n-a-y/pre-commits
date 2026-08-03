"""detect-secrets did not accept a --baseline flag at all: it is a
self-contained regex scanner with no baseline concept, so passing
`args: ['--baseline', '.secrets.baseline']` (a very common pattern) made
argparse reject the invocation outright.

These tests cover the new baseline capability end to end: generating one,
having it suppress exactly the findings it recorded, and *not* suppressing
anything new.
"""

import json


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_baseline_flag_no_longer_crashes(tmp_path, run_hook):
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')

    result = run_hook(
        "detect_secrets", ["config.py", "--baseline", "missing.baseline"], cwd=tmp_path
    )

    assert result.returncode != 2, result.stderr
    assert "unrecognized arguments" not in result.stderr


def test_scan_without_baseline_behaves_as_before(tmp_path, run_hook):
    """No --baseline at all: unchanged, pre-existing behaviour."""
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')

    result = run_hook("detect_secrets", ["config.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "Generic secret assignment" in result.stdout


def test_missing_baseline_warns_and_scans_without_suppression(tmp_path, run_hook):
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')

    result = run_hook(
        "detect_secrets",
        ["config.py", "--baseline", ".secrets.baseline"],
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "not found" in result.stdout
    assert "Generic secret assignment" in result.stdout


def test_update_baseline_records_current_findings(tmp_path, run_hook):
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')
    baseline = tmp_path / ".secrets.baseline"

    result = run_hook(
        "detect_secrets",
        ["config.py", "--update-baseline", "--baseline", str(baseline)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert baseline.exists()
    data = json.loads(baseline.read_text())
    assert "config.py" in data["results"]
    assert len(data["results"]["config.py"]) == 1
    assert data["results"]["config.py"][0]["label"] == "Generic secret assignment"


def test_baseline_suppresses_known_finding_on_rescan(tmp_path, run_hook):
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')
    baseline = tmp_path / ".secrets.baseline"
    run_hook(
        "detect_secrets",
        ["config.py", "--update-baseline", "--baseline", str(baseline)],
        cwd=tmp_path,
    )

    result = run_hook(
        "detect_secrets", ["config.py", "--baseline", str(baseline)], cwd=tmp_path
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 known finding" in result.stdout


def test_baseline_does_not_suppress_a_genuinely_new_secret(tmp_path, run_hook):
    f = _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')
    baseline = tmp_path / ".secrets.baseline"
    run_hook(
        "detect_secrets",
        ["config.py", "--update-baseline", "--baseline", str(baseline)],
        cwd=tmp_path,
    )

    # A second, different secret is added after the baseline was generated.
    f.write_text('api_key = "abcdefghijklmnopqrstuvwx"\npassword = "supersecretpw"\n')

    result = run_hook(
        "detect_secrets", ["config.py", "--baseline", str(baseline)], cwd=tmp_path
    )

    assert result.returncode == 1
    assert "Hardcoded password" in result.stdout
    # The already-baselined finding stays suppressed; only the new one fails.
    assert "Generic secret assignment" not in result.stdout


def test_update_baseline_without_explicit_files_uses_git_tracked_files(
    tmp_path, run_hook
):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    _write(tmp_path, "config.py", 'api_key = "abcdefghijklmnopqrstuvwx"\n')
    subprocess.run(["git", "add", "config.py"], cwd=tmp_path, check=True)

    baseline = tmp_path / ".secrets.baseline"
    result = run_hook(
        "detect_secrets",
        ["--update-baseline", "--baseline", str(baseline)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(baseline.read_text())
    assert "config.py" in data["results"]
