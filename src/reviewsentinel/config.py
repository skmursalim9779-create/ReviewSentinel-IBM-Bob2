"""Shared configuration, finding types, and safe scanning boundaries."""

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_EXCLUDES = (
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "bob_sessions",
    "reports",
    ".env",
    ".pytest_cache",
)

SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php"
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

SEVERITY_WEIGHT = {"critical": 10, "high": 6, "medium": 3, "low": 1, "info": 0}


@dataclass
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    message: str
    snippet: str
    category: str = "quality"
    explanation: str = ""
    suggested_fix: str = ""


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    scan_seconds: float = 0.0


def is_excluded(path: Path) -> bool:
    return any(part in set(path.parts) for part in DEFAULT_EXCLUDES)


def iter_scannable_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not is_excluded(path) and path.suffix.lower() in SCANNABLE_EXTENSIONS:
            yield path


def mask_secret_line(line: str) -> str:
    """Redact obvious secret assignment values before report/LLM handling."""
    import re

    pattern = re.compile(
        r"(?i)(\b[A-Za-z0-9_]*(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\b\s*[:=]\s*[\"'])([^\"']+)([\"'])"
    )
    line = pattern.sub(r"\1[REDACTED]\3", line)
    line = re.sub(r"\b(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9][A-Za-z0-9._-]{12,}|ghp_[A-Za-z0-9]{30,})\b", "[REDACTED_TOKEN]", line)
    return line[:220]
