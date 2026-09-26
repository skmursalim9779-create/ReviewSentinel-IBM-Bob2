# Architecture

## Runtime

`engine.py` is the deterministic core. It walks supported source files, invokes pure scanners, sorts findings, and exposes simple review metrics.

`llm_reviewer.py` is deliberately optional. It receives only a short, already-redacted snippet plus the scanner context. This makes the security-sensitive scanning path usable even with no AI credits or API key.

`report.py` converts the same finding objects to three representations:

- Markdown for humans;
- JSON for application/UI integrations;
- SARIF 2.1.0 for developer-security tooling and CI ingestion.

`web.py` is a lightweight demonstration layer. It does not contain scanner logic; it calls the same engine used by the CLI. This keeps the UI and CLI behavior consistent.

## Why this architecture is useful for an agentic IDE

The boundaries are intentionally small and testable. Bob can work on scanner hardening, reporting, demo experience, or QA as separate tasks/subagents while the shared `Finding` contract stays stable. That makes the Bob workflow demonstrable without turning the runtime product into a collection of opaque agent prompts.
