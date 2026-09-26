"""Unit tests for reviewsentinel.config utilities."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.config import is_excluded, iter_scannable_files, mask_secret_line


# ---------------------------------------------------------------------------
# mask_secret_line
# ---------------------------------------------------------------------------

def test_mask_secret_line_redacts_api_key():
    line = 'api_key = "sk-abcdefghijklmnopqrstuvwx"'
    result = mask_secret_line(line)
    assert "REDACTED" in result
    assert "sk-abcdefghijklmnopqrstuvwx" not in result


def test_mask_secret_line_redacts_password():
    line = 'password = "supersecret123"'
    result = mask_secret_line(line)
    assert "REDACTED" in result
    assert "supersecret123" not in result


def test_mask_secret_line_redacts_token_literal():
    line = "token = sk-abcdefghijklmnopqrstuvwxyz"
    result = mask_secret_line(line)
    assert "REDACTED" in result


def test_mask_secret_line_leaves_safe_line_unchanged():
    line = "x = 1 + 2"
    assert mask_secret_line(line) == "x = 1 + 2"


def test_mask_secret_line_truncates_long_lines():
    line = "x = " + "a" * 300
    result = mask_secret_line(line)
    assert len(result) <= 220


# ---------------------------------------------------------------------------
# is_excluded
# ---------------------------------------------------------------------------

def test_is_excluded_venv():
    assert is_excluded(Path("project/venv/lib/site-packages/foo.py"))


def test_is_excluded_git():
    assert is_excluded(Path("project/.git/config"))


def test_is_excluded_pycache():
    assert is_excluded(Path("project/src/__pycache__/module.cpython-311.pyc"))


def test_is_excluded_regular_file():
    assert not is_excluded(Path("project/src/main.py"))


def test_is_excluded_node_modules():
    assert is_excluded(Path("project/node_modules/lodash/index.js"))


# ---------------------------------------------------------------------------
# iter_scannable_files
# ---------------------------------------------------------------------------

def test_iter_scannable_files_includes_py():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        py_file = root / "app.py"
        py_file.write_text("x = 1\n", encoding="utf-8")
        files = list(iter_scannable_files(root))
        assert py_file in files


def test_iter_scannable_files_skips_binary_extension():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "image.png").write_bytes(b"\x89PNG\r\n")
        (root / "archive.zip").write_bytes(b"PK")
        files = list(iter_scannable_files(root))
        assert files == []


def test_iter_scannable_files_skips_excluded_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        venv_dir = root / "venv"
        venv_dir.mkdir()
        (venv_dir / "secret.py").write_text("x = 1\n", encoding="utf-8")
        files = list(iter_scannable_files(root))
        assert files == []


def test_iter_scannable_files_includes_js():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        js_file = root / "app.js"
        js_file.write_text("var x = 1;\n", encoding="utf-8")
        files = list(iter_scannable_files(root))
        assert js_file in files


def test_iter_scannable_files_multiple_types():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        py_file = root / "a.py"
        ts_file = root / "b.ts"
        txt_file = root / "c.txt"
        py_file.write_text("x = 1\n", encoding="utf-8")
        ts_file.write_text("let x = 1;\n", encoding="utf-8")
        txt_file.write_text("hello\n", encoding="utf-8")
        files = list(iter_scannable_files(root))
        assert py_file in files
        assert ts_file in files
        assert txt_file not in files
