"""AST-backed detection of dynamic execution and unsafe deserialization in Python."""

import ast

from ..config import Finding


def scan(file_path: str, source: str):
    if not file_path.endswith(".py"):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        line = getattr(node, "lineno", 1)
        snippet = lines[line - 1].strip()[:220] if 0 < line <= len(lines) else ""
        name = node.func.id if isinstance(node.func, ast.Name) else None
        attr = node.func.attr if isinstance(node.func, ast.Attribute) else None

        if name == "eval":
            findings.append(Finding("RS-EVAL-001", "critical", file_path, line, "Use of eval() on dynamic input.", snippet, "execution"))
        elif name == "exec":
            findings.append(Finding("RS-EVAL-002", "critical", file_path, line, "Use of exec() on dynamic input.", snippet, "execution"))
        elif attr in {"load", "loads"} and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
            findings.append(Finding("RS-EVAL-003", "high", file_path, line, "pickle.load/loads on untrusted data can deserialize attacker-controlled objects.", snippet, "deserialization"))
        elif attr == "load" and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
            safe = any(
                kw.arg == "Loader" and isinstance(kw.value, ast.Attribute) and isinstance(kw.value.value, ast.Name) and kw.value.value.id == "yaml" and kw.value.attr == "SafeLoader"
                for kw in node.keywords
            )
            if not safe:
                findings.append(Finding("RS-EVAL-004", "medium", file_path, line, "yaml.load() without SafeLoader can instantiate arbitrary Python objects from untrusted YAML.", snippet, "deserialization"))
    return findings
