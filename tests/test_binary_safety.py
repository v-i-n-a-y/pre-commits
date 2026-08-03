"""The text-hygiene hooks (trailing-whitespace, end-of-file-fixer,
mixed-line-endings) and copyright-check all rewrite files in place. Run
directly against a committed PDF, they corrupted it: mixed-line-endings
mangled bytes inside compressed streams that happened to match \\r, and
trailing-whitespace/end-of-file-fixer stripped bytes that are structurally
significant in a PDF (e.g. the fixed-width cross-reference table).

pre-commit's own `types: [text]` filtering keeps binaries away from these
hooks by default, but that is a caller-side safety net, not a guarantee for
the hook itself: it can be overridden in a caller's config, and the
installed console-scripts can be (and evidently were) invoked directly. Each
hook must refuse to touch binary content on its own.
"""

import shutil


def _copy_fixture(fixtures_dir, tmp_path, name):
    dest = tmp_path / name
    shutil.copy(fixtures_dir / "sample.pdf", dest)
    return dest


def test_trailing_whitespace_leaves_pdf_untouched(tmp_path, fixtures_dir, run_hook):
    pdf = _copy_fixture(fixtures_dir, tmp_path, "doc.pdf")
    before = pdf.read_bytes()

    result = run_hook("trailing_whitespace", [str(pdf)], cwd=tmp_path)

    assert result.returncode == 0
    assert pdf.read_bytes() == before


def test_end_of_file_fixer_leaves_pdf_untouched(tmp_path, fixtures_dir, run_hook):
    pdf = _copy_fixture(fixtures_dir, tmp_path, "doc.pdf")
    before = pdf.read_bytes()

    result = run_hook("end_of_file", [str(pdf)], cwd=tmp_path)

    assert result.returncode == 0
    assert pdf.read_bytes() == before


def test_mixed_line_endings_leaves_pdf_untouched(tmp_path, fixtures_dir, run_hook):
    pdf = _copy_fixture(fixtures_dir, tmp_path, "doc.pdf")
    before = pdf.read_bytes()

    result = run_hook("line_endings", [str(pdf)], cwd=tmp_path)

    assert result.returncode == 0
    assert pdf.read_bytes() == before


def test_copyright_check_leaves_pdf_untouched_even_with_forced_style(
    tmp_path, fixtures_dir, run_hook
):
    """--style forces a comment style regardless of extension, bypassing the
    extension allow-list that normally keeps copyright-check off unknown
    file types — the binary guard must still catch it."""
    pdf = _copy_fixture(fixtures_dir, tmp_path, "doc.pdf")
    before = pdf.read_bytes()

    result = run_hook(
        "copyright",
        ["--holder", "Acme", "--style", "hash", str(pdf)],
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert pdf.read_bytes() == before
    assert "binary content detected" in result.stdout


def test_pdf_still_opens_after_all_hygiene_hooks_run(tmp_path, fixtures_dir, run_hook):
    """End-to-end sanity check using a real PDF parser, not just a byte
    comparison, to prove the file is still a valid, openable PDF."""
    pdf = _copy_fixture(fixtures_dir, tmp_path, "doc.pdf")

    for module in ("trailing_whitespace", "end_of_file", "line_endings"):
        run_hook(module, [str(pdf)], cwd=tmp_path)

    import pytest

    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(pdf))
    assert len(reader.pages) == 1
    assert "Hello" in reader.pages[0].extract_text()


def test_hooks_still_fix_genuine_text_files(tmp_path, run_hook):
    """Guard against over-broad binary detection: real text files with
    trailing whitespace, missing final newlines, and CRLF endings must still
    be fixed exactly as before."""
    f = tmp_path / "file.txt"
    f.write_bytes(b"hello   \r\nworld\t\r\nno newline at end")

    run_hook("trailing_whitespace", [str(f)], cwd=tmp_path)
    run_hook("line_endings", [str(f)], cwd=tmp_path)
    run_hook("end_of_file", [str(f)], cwd=tmp_path)

    assert f.read_bytes() == b"hello\nworld\nno newline at end\n"


def test_hooks_still_fix_extensionless_text_files(tmp_path, run_hook):
    """Binary detection falls back to content-sniffing for files `identify`
    can't classify by extension; plain text with no extension must still be
    treated as text."""
    f = tmp_path / "PLAINFILE"
    f.write_bytes(b"hello   \r\nworld\r\n")

    run_hook("line_endings", [str(f)], cwd=tmp_path)

    assert f.read_bytes() == b"hello   \nworld\n"


def test_content_sniffing_skips_extensionless_binary_files(tmp_path, run_hook):
    """A binary file with an extension `identify` doesn't recognise must
    still be caught by the content-sniffing fallback."""
    f = tmp_path / "blob.unknownbinaryext"
    payload = bytes([0x25, 0x00, 0x01, 0x02]) + bytes(range(256)) * 3 + b"\r\n\r"
    f.write_bytes(payload)
    before = f.read_bytes()

    run_hook("line_endings", [str(f)], cwd=tmp_path)
    run_hook("end_of_file", [str(f)], cwd=tmp_path)
    run_hook("trailing_whitespace", [str(f)], cwd=tmp_path)

    assert f.read_bytes() == before
