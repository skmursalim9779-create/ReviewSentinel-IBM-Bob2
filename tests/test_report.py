"""Unit tests for reviewsentinel.report module."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.config import Finding
from reviewsentinel.report import to_json, to_markdown, to_sarif, write_reports


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_finding(
    rule_id="RS-SECRET-001",
    severity="critical",
    file="app.py",
    line=10,
    message="Hardcoded API key detected",
    snippet='api_key = "[REDACTED]"',
    category="security",
    explanation="This leaks credentials.",
    suggested_fix="Use environment variables.",
):
    return Finding(
        rule_id=rule_id,
        severity=severity,
        file=file,
        line=line,
        message=message,
        snippet=snippet,
        category=category,
        explanation=explanation,
        suggested_fix=suggested_fix,
    )


# ---------------------------------------------------------------------------
# to_markdown
# ---------------------------------------------------------------------------

def test_to_markdown_contains_severity_label():
    f = _make_finding(severity="critical")
    md = to_markdown([f], files_scanned=1, scan_seconds=0.1)
    assert "CRITICAL" in md


def test_to_markdown_contains_rule_id():
    f = _make_finding(rule_id="RS-SECRET-001")
    md = to_markdown([f], files_scanned=1, scan_seconds=0.1)
    assert "RS-SECRET-001" in md


def test_to_markdown_contains_file_path():
    f = _make_finding(file="src/app.py")
    md = to_markdown([f], files_scanned=1, scan_seconds=0.1)
    assert "src/app.py" in md


def test_to_markdown_contains_risk_score():
    md = to_markdown([], files_scanned=5, scan_seconds=0.5)
    assert "100" in md  # score is 100 with no findings


def test_to_markdown_no_findings():
    md = to_markdown([], files_scanned=2, scan_seconds=0.2)
    assert "No issues found" in md


def test_to_markdown_with_explanation_and_fix():
    f = _make_finding(explanation="Risk explanation here.", suggested_fix="Apply fix here.")
    md = to_markdown([f], files_scanned=1, scan_seconds=0.1)
    assert "Risk explanation here." in md
    assert "Apply fix here." in md


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------

def test_to_json_has_risk_score():
    f = _make_finding(severity="critical")
    data = to_json([f], files_scanned=3, scan_seconds=0.25)
    assert "risk_score" in data["summary"]
    assert isinstance(data["summary"]["risk_score"], int)


def test_to_json_findings_first_rule_id():
    f = _make_finding(rule_id="RS-SECRET-001")
    data = to_json([f], files_scanned=1, scan_seconds=0.1)
    assert len(data["findings"]) == 1
    assert data["findings"][0]["rule_id"] == "RS-SECRET-001"


def test_to_json_is_serialisable():
    f = _make_finding()
    data = to_json([f], files_scanned=1, scan_seconds=0.1)
    dumped = json.dumps(data)  # must not raise
    reparsed = json.loads(dumped)
    assert reparsed["summary"]["findings"] == 1


def test_to_json_empty_findings():
    data = to_json([], files_scanned=0, scan_seconds=0.0)
    assert data["summary"]["findings"] == 0
    assert data["findings"] == []


# ---------------------------------------------------------------------------
# to_sarif
# ---------------------------------------------------------------------------

def test_to_sarif_version():
    sarif = to_sarif([_make_finding()])
    assert sarif["version"] == "2.1.0"


def test_to_sarif_results_non_empty():
    sarif = to_sarif([_make_finding()])
    assert len(sarif["runs"][0]["results"]) >= 1


def test_to_sarif_level_maps_critical_to_error():
    sarif = to_sarif([_make_finding(severity="critical")])
    result = sarif["runs"][0]["results"][0]
    assert result["level"] == "error"


def test_to_sarif_level_maps_medium_to_warning():
    sarif = to_sarif([_make_finding(severity="medium")])
    result = sarif["runs"][0]["results"][0]
    assert result["level"] == "warning"


def test_to_sarif_level_maps_low_to_note():
    sarif = to_sarif([_make_finding(severity="low")])
    result = sarif["runs"][0]["results"][0]
    assert result["level"] == "note"


def test_to_sarif_empty_findings():
    sarif = to_sarif([])
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["results"] == []


# ---------------------------------------------------------------------------
# write_reports
# ---------------------------------------------------------------------------

def test_write_reports_creates_all_three_files():
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "report")
        f = _make_finding()
        md_path, json_path, sarif_path = write_reports([f], files_scanned=1, scan_seconds=0.1, out_prefix=prefix)
        assert md_path.exists()
        assert json_path.exists()
        assert sarif_path.exists()


def test_write_reports_files_are_non_empty():
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "report")
        f = _make_finding()
        md_path, json_path, sarif_path = write_reports([f], files_scanned=1, scan_seconds=0.1, out_prefix=prefix)
        assert md_path.stat().st_size > 0
        assert json_path.stat().st_size > 0
        assert sarif_path.stat().st_size > 0


def test_write_reports_json_has_correct_structure():
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "report")
        f = _make_finding(rule_id="RS-TEST-001")
        _, json_path, _ = write_reports([f], files_scanned=1, scan_seconds=0.1, out_prefix=prefix)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["summary"]["findings"] == 1
        assert data["findings"][0]["rule_id"] == "RS-TEST-001"
