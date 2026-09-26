"""Heuristic detection of common SQL and shell injection-prone constructions."""

import re

from ..config import Finding

_SQL_CONCAT_RE = re.compile(
    r'''(?ix)(["'][^"']*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b[^"']*["']\s*(\+|%|\.format\())|(f["'][^"']*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b)'''
)
_SHELL_RE = re.compile(r"(?x)(os\.system\s*\(|subprocess\.\w+\([^)]*shell\s*=\s*True)")


def scan(file_path: str, source: str):
    findings = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        if _SQL_CONCAT_RE.search(line):
            findings.append(
                Finding(
                    rule_id="RS-INJECT-001",
                    severity="high",
                    category="injection",
                    file=file_path,
                    line=line_no,
                    message="SQL query appears to be assembled with string formatting/concatenation instead of parameterized bindings.",
                    snippet=line.strip()[:220],
                )
            )
        if _SHELL_RE.search(line):
            findings.append(
                Finding(
                    rule_id="RS-INJECT-002",
                    severity="high",
                    category="injection",
                    file=file_path,
                    line=line_no,
                    message="Shell command uses os.system or shell=True; verify inputs cannot control the command.",
                    snippet=line.strip()[:220],
                )
            )
    return findings
