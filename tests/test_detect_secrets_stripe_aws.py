"""Coverage for the Stripe (sk_live_/rk_live_/whsec_) and AWS secret access
key detectors added for the gaps described in issue #264 of the consuming
repository: a live Stripe key was not caught at all, and neither was a bare
AWS secret access key value.

Test keys (sk_test_/rk_test_) and the whsec_fake/whsec_placeholder style
fixtures used throughout that project's test suite are deliberately
committed and must stay allowed; only values that look like real live
secrets should fail.
"""


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


# ── Stripe secret/restricted keys ──────────────────────────────────────────


def test_stripe_live_secret_key_is_caught(tmp_path, run_hook):
    _write(
        tmp_path,
        "config.py",
        'STRIPE_SECRET_KEY = "sk_live_0000000000"\n',
    )

    result = run_hook("detect_secrets", ["config.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "Stripe live API key" in result.stdout


def test_stripe_live_restricted_key_is_caught(tmp_path, run_hook):
    _write(
        tmp_path,
        "config.py",
        'STRIPE_KEY = "rk_live_0000000000"\n',
    )

    result = run_hook("detect_secrets", ["config.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "Stripe live API key" in result.stdout


def test_stripe_test_secret_key_placeholder_is_allowed(tmp_path, run_hook):
    # Deliberately not using a "..._SECRET_KEY = " variable name here: that
    # form already trips the pre-existing, unrelated "Generic secret
    # assignment" pattern regardless of prefix, and is handled in the real
    # repo via its baseline. This isolates the new sk_live_/sk_test_ pattern.
    _write(
        tmp_path,
        "test_payment.py",
        'stripe_key = "sk_test_fake_for_unit_tests"\n',
    )

    result = run_hook("detect_secrets", ["test_payment.py"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_stripe_test_restricted_key_placeholder_is_allowed(tmp_path, run_hook):
    _write(
        tmp_path,
        "test_payment.py",
        'STRIPE_KEY = "rk_test_fake_for_unit_tests"\n',
    )

    result = run_hook("detect_secrets", ["test_payment.py"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── Stripe webhook signing secrets ─────────────────────────────────────────


def test_stripe_webhook_secret_is_caught(tmp_path, run_hook):
    _write(
        tmp_path,
        "config.py",
        'STRIPE_WEBHOOK_SECRET = "whsec_zzz11111zzz22222zzz33333zzz4"\n',
    )

    result = run_hook("detect_secrets", ["config.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "Stripe webhook signing secret" in result.stdout


def test_stripe_webhook_secret_fake_placeholder_is_allowed(tmp_path, run_hook):
    _write(
        tmp_path,
        "test_payment.py",
        'STRIPE_WEBHOOK_SECRET = "whsec_fake"\n',
    )

    result = run_hook("detect_secrets", ["test_payment.py"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_stripe_webhook_secret_placeholder_word_is_allowed(tmp_path, run_hook):
    _write(
        tmp_path,
        "core-values.yaml",
        'webhook_secret: "whsec_placeholder"\n',
    )

    result = run_hook("detect_secrets", ["core-values.yaml"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


# ── AWS secret access key ──────────────────────────────────────────────────


def test_aws_secret_access_key_assignment_is_caught(tmp_path, run_hook):
    _write(
        tmp_path,
        "settings.py",
        'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMInotarealkeyEXAMPLEKEY123"\n',
    )

    result = run_hook("detect_secrets", ["settings.py"], cwd=tmp_path)

    assert result.returncode == 1
    assert "AWS secret access key" in result.stdout


def test_aws_secret_access_key_bare_value_is_caught(tmp_path, run_hook):
    # A 40-char value in the AWS secret key alphabet, no keyword nearby (the
    # "committed separately from the AKIA id" case from issue #264).
    _write(
        tmp_path,
        "notes.txt",
        "wJalrXUtnFEMIkNotARealKeyEXAMPLEabcdefgh\n",
    )

    result = run_hook("detect_secrets", ["notes.txt"], cwd=tmp_path)

    assert result.returncode == 1
    assert "AWS secret access key" in result.stdout


def test_git_sha1_hash_is_not_flagged_as_aws_key(tmp_path, run_hook):
    # A 40-char, all-hex git commit SHA must not trip the bare AWS pattern.
    _write(
        tmp_path,
        "notes.txt",
        "5519fee1234567890abcdef1234567890abcdef\n",
    )

    result = run_hook("detect_secrets", ["notes.txt"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout


def test_url_path_is_not_flagged_as_aws_key(tmp_path, run_hook):
    # A long URL/chart path must not trip the bare AWS pattern (it contains
    # '/', which the pattern deliberately excludes from its charset).
    _write(
        tmp_path,
        "skaffold.yaml",
        "path: charts/datasphere/environments/dev/core/values-longenough\n",
    )

    result = run_hook("detect_secrets", ["skaffold.yaml"], cwd=tmp_path)

    assert result.returncode == 0, result.stdout
