"""Unit tests for reviewsentinel.engine."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.engine import (
    category_counts,
    risk_score,
    scan_path,
    scan_source,
    severity_counts,
)
from reviewsentinel.config import Finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding(rule_id="RS-TEST-001", severity="high", file="f.py", line=1,
              category="security"):
    return Finding(
        rule_id=rule_id,
        severity=severity,
        file=file,
        line=line,
        message="test finding",
        snippet="code here",
        category=category,
    )


# ---------------------------------------------------------------------------
# scan_source
# ---------------------------------------------------------------------------

def test_scan_source_returns_findings_for_secret():
    findings = scan_source("f.py", 'api_key = "sk-abcdefghijklmnopqrstuvwx"\n')
    assert len(findings) >= 1
    rule_ids = {f.rule_id for f in findings}
    assert "RS-SECRET-001" in rule_ids


def test_scan_source_findings_sorted_by_severity_then_line():
    # scan_source does NOT sort; scan_path does.
    # Verify via scan_path that the final findings list is sorted.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "vuln.py").write_text(
            'api_key = "sk-abcdefghijklmnopqrstuvwx"\neval(user_input)\n',
            encoding="utf-8",
        )
        result = scan_path(root)
    assert len(result.findings) >= 2
    from reviewsentinel.config import SEVERITY_ORDER
    orders = [SEVERITY_ORDER.get(f.severity, 9) for f in result.findings]
    assert orders == sorted(orders)


def test_scan_source_clean_code_returns_empty():
    findings = scan_source("clean.py", "x = 1\nprint(x)\n")
    assert findings == []


# ---------------------------------------------------------------------------
# severity_counts
# ---------------------------------------------------------------------------

def test_severity_counts_excludes_zero_counts():
    findings = [_finding(severity="critical"), _finding(severity="critical")]
    counts = severity_counts(findings)
    assert counts == {"critical": 2}
    assert "high" not in counts
    assert "medium" not in counts


def test_severity_counts_empty():
    assert severity_counts([]) == {}


def test_severity_counts_mixed():
    findings = [
        _finding(severity="critical"),
        _finding(severity="high"),
        _finding(severity="high"),
        _finding(severity="medium"),
    ]
    counts = severity_counts(findings)
    assert counts["critical"] == 1
    assert counts["high"] == 2
    assert counts["medium"] == 1
    assert "low" not in counts


# ---------------------------------------------------------------------------
# risk_score
# ---------------------------------------------------------------------------

def test_risk_score_no_findings_is_100():
    assert risk_score([]) == 100


def test_risk_score_clamps_at_zero():
    # 6 critical findings → penalty = 6*18 = 108 → clamped to 0
    findings = [_finding(severity="critical") for _ in range(6)]
    assert risk_score(findings) == 0


def test_risk_score_known_input():
    # 1 critical (18) + 1 high (10) → penalty 28 → score 72
    findings = [_finding(severity="critical"), _finding(severity="high")]
    assert risk_score(findings) == 72


def test_risk_score_never_exceeds_100():
    assert risk_score([]) <= 100


# ---------------------------------------------------------------------------
# category_counts
# ---------------------------------------------------------------------------

def test_category_counts_sorted_desc_count():
    findings = [
        _finding(category="security"),
        _finding(category="security"),
        _finding(category="quality"),
    ]
    counts = category_counts(findings)
    items = list(counts.items())
    assert items[0] == ("security", 2)
    assert items[1] == ("quality", 1)


def test_category_counts_tie_break_by_name():
    findings = [
        _finding(category="z_cat"),
        _finding(category="a_cat"),
    ]
    counts = category_counts(findings)
    keys = list(counts.keys())
    assert keys == ["a_cat", "z_cat"]


def test_category_counts_empty():
    assert category_counts([]) == {}


# ---------------------------------------------------------------------------
# scan_path
# ---------------------------------------------------------------------------

def test_scan_path_counts_files_and_findings():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # One file with a known secret
        (root / "secrets_file.py").write_text(
            'api_key = "sk-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8"
        )
        # One clean file
        (root / "clean.py").write_text("x = 1\n", encoding="utf-8")

        result = scan_path(root)
        assert result.files_scanned == 2
        rule_ids = {f.rule_id for f in result.findings}
        assert "RS-SECRET-001" in rule_ids
        assert result.scan_seconds >= 0


def test_scan_path_excludes_venv():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        venv_dir = root / "venv"
        venv_dir.mkdir()
        (venv_dir / "secret.py").write_text(
            'api_key = "sk-abcdefghijklmnopqrstuvwx"\n', encoding="utf-8"
        )
        result = scan_path(root)
        assert result.files_scanned == 0
        assert result.findings == []
