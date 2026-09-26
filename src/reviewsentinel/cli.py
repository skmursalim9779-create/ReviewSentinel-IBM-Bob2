"""ReviewSentinel command-line interface."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .engine import scan_path
from .llm_reviewer import explain
from .report import write_reports


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reviewsentinel", description="Deterministic static code review with optional AI explanations.")
    parser.add_argument("--version", action="version", version=f"ReviewSentinel {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a repository or directory")
    scan.add_argument("path")
    scan.add_argument("--out", default="reports/report", help="Output prefix for .md/.json/.sarif reports")
    scan.add_argument("--no-explain", action="store_true", help="Skip optional LLM explanation")
    scan.add_argument("--fail-on", choices=["critical", "high", "medium", "low", "info", "none"], default="none", help="Exit non-zero when this severity or worse is found")

    args = parser.parse_args(argv)
    if args.command == "scan":
        root = Path(args.path).resolve()
        if not root.exists() or not root.is_dir():
            print(f"Path not found or not a directory: {root}", file=sys.stderr)
            return 2
        result = scan_path(root)
        explain(result.findings, enabled=not args.no_explain)
        md_path, json_path, sarif_path = write_reports(result.findings, result.files_scanned, result.scan_seconds, args.out)
        print(f"Scanned {result.files_scanned} files in {result.scan_seconds:.3f}s — {len(result.findings)} finding(s).")
        print(f"Markdown report: {md_path}")
        print(f"JSON report:     {json_path}")
        print(f"SARIF report:    {sarif_path}")
        if args.fail_on != "none":
            order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            threshold = order[args.fail_on]
            if any(order.get(f.severity, 9) <= threshold for f in result.findings):
                return 1
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
