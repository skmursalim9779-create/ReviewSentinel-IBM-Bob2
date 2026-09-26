# ReviewSentinel — IBM Bob working context

## Purpose
ReviewSentinel is a developer-facing code-review and security-audit copilot. Its core workflow is:

1. scan a repository or file;
2. surface deterministic, explainable findings;
3. optionally ask an LLM to explain risk and suggest a minimal fix;
4. emit human-readable Markdown plus machine-readable JSON/SARIF;
5. expose the same workflow through a small web demo.

The project is designed to showcase IBM Bob IDE as the development partner for the hackathon: planning, implementation, focused subagents, testing, refactoring, and documentation updates should be performed in Bob IDE and captured in `bob_sessions/`.

## Architecture
- `src/reviewsentinel/engine.py`: orchestration and deterministic metrics.
- `src/reviewsentinel/scanners/`: pure, dependency-light scanners. Each scanner exposes `scan(file_path, source) -> list[Finding]` and must have no network side effects.
- `src/reviewsentinel/llm_reviewer.py`: provider-neutral explanation layer. It must receive only short, already-redacted flagged snippets; never send full source files or secrets.
- `src/reviewsentinel/report.py`: Markdown, JSON and SARIF 2.1.0 output.
- `src/reviewsentinel/cli.py`: local and CI-friendly command line interface.
- `src/reviewsentinel/web.py`: zero-build demo UI/API for sample code, pasted code, and public GitHub repositories.
- `sample_repo/`: synthetic vulnerable code for safe demos. Never add real credentials or client data.
- `tests/`: automated regression tests.

## Coding rules
- Python 3.11+.
- Prefer standard library; keep external dependencies limited to `requests` and `pyyaml` unless a strong reason is documented.
- Scanners must be deterministic and side-effect free.
- Avoid broad regexes when an AST approach is practical for Python.
- Security findings must redact credential-like values in report snippets.
- Do not generate exploit payloads or attack tooling. Findings should explain risk and remediation only.
- Keep the web endpoint bounded: validate GitHub URLs, enforce archive/request size limits, and reject unsafe ZIP paths.
- Never commit `.env`, API keys, tokens, or private datasets.

## Suggested Bob task boundaries
1. **Plan** — inspect architecture, hackathon requirements, acceptance criteria, and propose the smallest high-impact changes. No code changes.
2. **Scanner hardening** — improve detection quality and regression tests.
3. **Workflow/API** — improve CLI output, CI gating, JSON/SARIF reporting.
4. **Demo surface** — implement or refine the web experience without changing scanner semantics.
5. **Quality pass** — run tests, review failures, fix regressions, and check security/privacy boundaries.
6. **Final documentation** — update README, demo script, architecture, impact measurement, and submission checklist.

Keep these tasks isolated when possible so each Bob session has a clear purpose and can be captured as required evidence.

## Required Bob evidence
For every Bob task used for the submission, capture the task session-consumption summary and export the task history as instructed by the hackathon guide. Store evidence in `bob_sessions/`. Do not fabricate evidence files.
