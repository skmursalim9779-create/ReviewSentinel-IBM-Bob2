"""Heuristic detection of hardcoded-looking credentials, with redaction."""

import re

from ..config import Finding, mask_secret_line

_ASSIGNMENT_RE = re.compile(
    r"(?ix)\b([A-Za-z0-9_]*(?:api[_-]?key|secret|token|password|passwd|access[_-]?key))\b\s*[:=]\s*[\"']([^\"']{8,})[\"']"
)
_KNOWN_PREFIXES = re.compile(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})")
_TEST_VAR_RE = re.compile(r"(?i)^(test|fake|mock|example|sample)_")


def scan(file_path: str, source: str):
    findings = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        # Skip pure comment lines
        if stripped.startswith("#"):
            continue
        assignment = _ASSIGNMENT_RE.search(line)
        if assignment:
            var_name = assignment.group(1)
            if _TEST_VAR_RE.match(var_name):
                continue
            findings.append(
                Finding(
                    rule_id="RS-SECRET-001",
                    severity="high",
                    category="secrets",
                    file=file_path,
                    line=line_no,
                    message=f"Possible hardcoded credential assigned to '{assignment.group(1)}'.",
                    snippet=mask_secret_line(line.strip()),
                )
            )
            continue
        if _KNOWN_PREFIXES.search(line):
            findings.append(
                Finding(
                    rule_id="RS-SECRET-002",
                    severity="critical",
                    category="secrets",
                    file=file_path,
                    line=line_no,
                    message="String matches a known cloud/API key prefix pattern.",
                    snippet=mask_secret_line(line.strip()),
                )
            )
    return findings
