# IBM Bob workflow plan

These are **prompts to run in Bob**, not pre-created evidence. Capture the actual task history and session summary after each task you use.

## Task 01 — Plan

> Inspect the repository and the hackathon brief. Identify the smallest set of changes that makes ReviewSentinel a credible end-to-end developer code-review workflow. Do not modify files. Return architecture, acceptance criteria, testing plan, privacy boundaries, and a task breakdown.

## Task 02 — Scanner hardening

> Review the scanner implementations and tests. Improve detection quality with AST where practical, reduce false positives, preserve deterministic behavior, and add regression tests. Do not add exploit payloads. Keep scanners pure and dependency-light.

## Task 03 — Review workflow and reports

> Review the engine, CLI, Markdown/JSON/SARIF reporting, and CI gate. Make the workflow reliable for local and CI use. Ensure findings are consistently ordered and secret-like snippets are redacted before reporting.

## Task 04 — Demo surface

> Review the web demo. Make the 30-second workflow obvious: choose demo repo, scan, understand the health summary, inspect a finding, and see remediation. Keep the server dependency-light, validate GitHub URLs, enforce size/path limits, and avoid exposing secrets.

## Task 05 — Quality pass

> Run the full test suite and exercise the CLI and web health endpoint. Fix regressions. Check package installation from a clean environment and verify that a scan of the synthetic sample produces findings without requiring an LLM key.

## Task 06 — Final hackathon audit

> Audit the repository against the hackathon submission requirements: Bob IDE as a demonstrable core part of the build workflow, `bob_sessions` evidence, public-safe data sources, working prototype, README, measurable impact method, and absence of credentials. Produce a checklist of anything still missing; do not fabricate evidence.
