"""Markdown, JSON and SARIF 2.1.0 reporting."""

import json
from pathlib import Path

from .config import Finding, SEVERITY_ORDER
from .engine import category_counts, risk_score, severity_counts


def _sorted(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.file, f.line, f.rule_id))


def to_markdown(findings: list[Finding], files_scanned: int, scan_seconds: float, title: str = "ReviewSentinel report") -> str:
    findings = _sorted(findings)
    counts = severity_counts(findings)
    categories = category_counts(findings)
    lines = [f"# {title}", "", f"- Files scanned: **{files_scanned}**", f"- Scan time: **{scan_seconds:.3f}s**", f"- Findings: **{len(findings)}**", f"- Review health score: **{risk_score(findings)}/100**", ""]
    if counts:
        lines.append("**By severity:** " + ", ".join(f"{k}: {v}" for k, v in counts.items()))
        lines.append("**By category:** " + ", ".join(f"{k}: {v}" for k, v in categories.items()))
        lines.append("")
    if not findings:
        lines.append("No issues found. ✅")
        return "\n".join(lines)

    for f in findings:
        lines.extend([
            f"## [{f.severity.upper()}] {f.rule_id} — {f.file}:{f.line}",
            f"**Category:** `{f.category}`",
            f.message,
            "",
            f"```text\n{f.snippet}\n```",
        ])
        if f.explanation:
            lines.append(f"**Why it matters:** {f.explanation}")
        if f.suggested_fix:
            lines.append(f"**Suggested fix:** {f.suggested_fix}")
        lines.append("")
    return "\n".join(lines)


def to_json(findings: list[Finding], files_scanned: int, scan_seconds: float) -> dict:
    return {
        "tool": {"name": "ReviewSentinel", "version": "0.2.0"},
        "summary": {
            "files_scanned": files_scanned,
            "scan_seconds": round(scan_seconds, 3),
            "findings": len(findings),
            "risk_score": risk_score(findings),
            "severity": severity_counts(findings),
            "categories": category_counts(findings),
        },
        "findings": [f.__dict__ for f in _sorted(findings)],
    }


def to_sarif(findings: list[Finding]) -> dict:
    rules: dict[str, dict] = {}
    results = []
    for f in _sorted(findings):
        rules.setdefault(f.rule_id, {
            "id": f.rule_id,
            "name": f.rule_id,
            "shortDescription": {"text": f.message},
            "defaultConfiguration": {"level": _sarif_level(f.severity)},
        })
        results.append({
            "ruleId": f.rule_id,
            "level": _sarif_level(f.severity),
            "message": {"text": f.explanation or f.message},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": f.file}, "region": {"startLine": max(1, f.line)}}}],
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "ReviewSentinel", "version": "0.2.0", "rules": list(rules.values())}}, "results": results}],
    }


def _sarif_level(severity: str) -> str:
    return {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}.get(severity, "note")


def write_reports(findings: list[Finding], files_scanned: int, scan_seconds: float, out_prefix: str):
    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    md_path = out.with_suffix(".md")
    json_path = out.with_suffix(".json")
    sarif_path = out.with_suffix(".sarif")
    md_path.write_text(to_markdown(findings, files_scanned, scan_seconds), encoding="utf-8")
    json_path.write_text(json.dumps(to_json(findings, files_scanned, scan_seconds), indent=2), encoding="utf-8")
    sarif_path.write_text(json.dumps(to_sarif(findings), indent=2), encoding="utf-8")
    return md_path, json_path, sarif_path
