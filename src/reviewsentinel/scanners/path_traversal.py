"""AST-based detection of path traversal vulnerabilities in Python code."""

import ast

from ..config import Finding

# Common names that indicate user-controlled input
_USER_INPUT_NAMES = {
    "request", "args", "params", "data", "input",
    "filename", "path", "filepath",
}


def _contains_name(node: ast.expr) -> bool:
    """Return True if any sub-node of *node* is an ast.Name."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            return True
    return False


def _base_name(node: ast.expr) -> str | None:
    """Extract the outermost Name id from an Attribute or Subscript chain."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _base_name(node.value)
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None


def _is_user_controlled(node: ast.expr) -> bool:
    """Return True if *node* is a Name/Subscript/Attribute whose base name is
    in the user-input name list."""
    if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
        base = _base_name(node)
        return base in _USER_INPUT_NAMES
    return False


def scan(file_path: str, source: str):
    if not file_path.endswith(".py"):
        return []

    findings = []
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        # ------------------------------------------------------------------ #
        # RS-TRAVERSE-001: open() with dynamic path (BinOp or f-string)       #
        # ------------------------------------------------------------------ #
        is_open = (
            (isinstance(func, ast.Name) and func.id == "open")
            or (
                isinstance(func, ast.Attribute)
                and func.attr == "open"
            )
        )
        if is_open and node.args:
            first_arg = node.args[0]
            dynamic = False
            if isinstance(first_arg, ast.BinOp) and _contains_name(first_arg):
                dynamic = True
            elif isinstance(first_arg, ast.JoinedStr) and _contains_name(first_arg):
                dynamic = True
            if dynamic:
                line = node.lineno
                findings.append(
                    Finding(
                        "RS-TRAVERSE-001", "high", file_path, line,
                        "Path traversal risk: open() with dynamic path — validate and sanitize the path argument.",
                        lines[line - 1].strip()[:220], "path-traversal"
                    )
                )

        # ------------------------------------------------------------------ #
        # RS-TRAVERSE-002: os.path.join() with user-controlled argument       #
        # ------------------------------------------------------------------ #
        is_os_path_join = (
            isinstance(func, ast.Attribute)
            and func.attr == "join"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "path"
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "os"
        )
        if is_os_path_join:
            for arg in node.args:
                if _is_user_controlled(arg):
                    line = node.lineno
                    findings.append(
                        Finding(
                            "RS-TRAVERSE-002", "high", file_path, line,
                            "Path traversal risk: os.path.join() with user-controlled argument — use pathlib.Path.resolve() and verify the result stays within the intended base directory.",
                            lines[line - 1].strip()[:220], "path-traversal"
                        )
                    )
                    break  # one finding per call site

    return findings
