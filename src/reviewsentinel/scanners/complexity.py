"""AST-based maintainability signal for oversized Python functions."""

import ast

from ..config import Finding

LONG_FUNCTION_THRESHOLD = 60


def scan(file_path: str, source: str):
    if not file_path.endswith(".py"):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    findings = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            length = end_line - node.lineno + 1
            if length >= LONG_FUNCTION_THRESHOLD:
                findings.append(
                    Finding(
                        "RS-COMPLEX-001", "low", file_path, node.lineno,
                        f"Function '{node.name}' is {length} lines long (threshold {LONG_FUNCTION_THRESHOLD}); consider splitting it for reviewability and testing.",
                        f"def {node.name}(...):", "maintainability"
                    )
                )
    return findings
