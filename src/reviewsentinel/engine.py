"""Scanning orchestration and deterministic review metrics."""

import time
from pathlib import Path

from .config import Finding, ScanResult, iter_scannable_files, SEVERITY_ORDER
from .scanners import ALL_SCANNERS


def scan_source(file_path: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for _name, scanner in ALL_SCANNERS:
        findings.extend(scanner(file_path, source))
    return findings


def scan_path(root: Path) -> ScanResult:
    result = ScanResult()
    start = time.perf_counter()
    for file_path in iter_scannable_files(root):
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        result.files_scanned += 1
        rel = str(file_path.relative_to(root)) if file_path.is_relative_to(root) else str(file_path)
        result.findings.extend(scan_source(rel, source))
    result.findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.file, f.line, f.rule_id))
    result.scan_seconds = time.perf_counter() - start
    return result


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return {k: v for k, v in counts.items() if v}


def risk_score(findings: list[Finding]) -> int:
    """Return a deterministic 0-100 review-health score. More findings => lower score."""
    penalty = sum({"critical": 18, "high": 10, "medium": 5, "low": 2, "info": 0}.get(f.severity, 0) for f in findings)
    return max(0, min(100, 100 - penalty))


def category_counts(findings: list[Finding]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        out[f.category] = out.get(f.category, 0) + 1
    return dict(sorted(out.items(), key=lambda item: (-item[1], item[0])))
