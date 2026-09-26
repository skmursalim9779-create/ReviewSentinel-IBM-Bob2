"""Detect weak cryptographic primitives in Python code."""

import ast
import re

from ..config import Finding

_STATIC_SALT_RE = re.compile(r"(?i)\bsalt\s*=\s*[\"'][^\"']+[\"']")

_INSECURE_RANDOM_FUNCS = {"randint", "choice", "random", "randrange", "uniform"}


def scan(file_path: str, source: str):
    if not file_path.endswith(".py"):
        return []
    findings = []
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    if tree is not None:
        # Collect names that are imported as 'random' at module level
        random_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "random":
                        # import random  -> accessed as 'random'
                        # import random as r -> accessed as 'r'
                        random_names.add(alias.asname if alias.asname else alias.name)
            elif isinstance(node, ast.ImportFrom):
                # from random import ... — we deliberately do NOT flag this
                # because individual function imports may have legitimate uses
                # and the common-name check is too broad.
                pass

        for node in ast.walk(tree):
            # RS-CRYPTO-001: weak hash (AST only — no duplicate regex pass)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "hashlib"
                and node.func.attr in {"md5", "sha1"}
            ):
                line = node.lineno
                findings.append(
                    Finding(
                        "RS-CRYPTO-001", "medium", file_path, line,
                        f"{node.func.attr.upper()} is unsuitable for security-sensitive hashing; use a modern hash or password KDF as appropriate.",
                        lines[line - 1].strip()[:220], "crypto"
                    )
                )

            # RS-CRYPTO-003: insecure random module
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in random_names
                and node.func.attr in _INSECURE_RANDOM_FUNCS
            ):
                line = node.lineno
                findings.append(
                    Finding(
                        "RS-CRYPTO-003", "medium", file_path, line,
                        "Use of insecure random module — use secrets or os.urandom for cryptographic purposes.",
                        lines[line - 1].strip()[:220], "crypto"
                    )
                )

    for line_no, line in enumerate(lines, start=1):
        if _STATIC_SALT_RE.search(line):
            findings.append(Finding("RS-CRYPTO-002", "low", file_path, line_no, "Hardcoded/static salt value; salts should be random per record.", line.strip()[:220], "crypto"))
    return findings
