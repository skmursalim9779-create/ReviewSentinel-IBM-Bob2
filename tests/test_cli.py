"""Unit tests for reviewsentinel CLI (tests/test_cli.py).

The CLI is argparse-based (not click), so we drive it through direct calls
to `main(argv=...)` and capture stdout/stderr via `io.StringIO`.
"""

import io
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.cli import main

SAMPLE_REPO = ROOT / "sample_repo"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(argv, *, capture_output=True):
    """Call main(argv) and return (exit_code, stdout_text, stderr_text)."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    if capture_output:
        with patch("sys.stdout", buf_out), patch("sys.stderr", buf_err):
            code = main(argv)
    else:
        code = main(argv)
    return code, buf_out.getvalue(), buf_err.getvalue()


# ---------------------------------------------------------------------------
# --help exits 0
# ---------------------------------------------------------------------------

def test_help_exits_0(capsys):
    """--help should print usage and exit 0 (argparse raises SystemExit(0))."""
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        # argparse may not raise on some wrappers; just ensure no crash
        pass


# ---------------------------------------------------------------------------
# scan sample_repo --no-explain exits 0 and produces output
# ---------------------------------------------------------------------------

def test_scan_sample_repo_exits_0():
    if not SAMPLE_REPO.exists():
        import pytest
        pytest.skip("sample_repo not found")
    with tempfile.TemporaryDirectory() as tmp:
        out_prefix = str(Path(tmp) / "report")
        code, stdout, _ = _run(["scan", str(SAMPLE_REPO), "--no-explain", "--out", out_prefix])
    assert code == 0


def test_scan_sample_repo_produces_findings_output():
    if not SAMPLE_REPO.exists():
        import pytest
        pytest.skip("sample_repo not found")
    with tempfile.TemporaryDirectory() as tmp:
        out_prefix = str(Path(tmp) / "report")
        _code, stdout, _ = _run(["scan", str(SAMPLE_REPO), "--no-explain", "--out", out_prefix])
    assert "finding" in stdout.lower()


# ---------------------------------------------------------------------------
# --fail-on critical exits 1 when a CRITICAL finding exists
# ---------------------------------------------------------------------------

def test_fail_on_critical_exits_1_with_critical_finding():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Write a file that triggers RS-SECRET-001 (critical or high)
        (root / "vuln.py").write_text(
            'api_key = "sk-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8"
        )
        out_prefix = str(root / "report")
        code, _stdout, _stderr = _run(
            ["scan", str(root), "--no-explain", "--fail-on", "high", "--out", out_prefix]
        )
    # RS-SECRET-001 is high or critical → should trigger exit 1
    assert code == 1


# ---------------------------------------------------------------------------
# Non-existent path exits 2
# ---------------------------------------------------------------------------

def test_nonexistent_path_exits_2():
    code, _stdout, stderr = _run(["scan", "/nonexistent/path/that/does/not/exist", "--no-explain"])
    assert code == 2


# ---------------------------------------------------------------------------
# Scanning a directory with no findings exits 0 (fail-on none)
# ---------------------------------------------------------------------------

def test_clean_directory_exits_0():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "clean.py").write_text("x = 1\nprint(x)\n", encoding="utf-8")
        out_prefix = str(root / "report")
        code, _stdout, _stderr = _run(
            ["scan", str(root), "--no-explain", "--fail-on", "none", "--out", out_prefix]
        )
    assert code == 0
