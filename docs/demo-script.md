# 3-minute demo script

## 0:00–0:25 — Problem

“Security code review repeatedly checks the same risky patterns. ReviewSentinel turns that repetitive work into a deterministic scan plus a concise explanation and machine-readable output.”

## 0:25–1:15 — Scan

Open the web demo and choose **Scan demo repo**. Point out the file count, finding count, scan time, health score, severity and categories. Open the hardcoded credential finding and show that the displayed value is redacted.

## 1:15–2:05 — Explain and act

Show one finding with its risk explanation and remediation. With an LLM provider configured, explain that the model receives only the flagged snippet, not the whole file. Then show the SARIF/JSON output for CI/tooling handoff.

## 2:05–2:35 — Bob evidence

Show the Bob IDE task list and one task session summary. Explain that the project was built and iterated through focused Bob Plan/Agent tasks and that the evidence is stored in `bob_sessions/`.

## 2:35–3:00 — Impact

Run the same repository twice and show the deterministic result. Report measured scan time and the separately measured human triage/review baseline. Do not use invented performance numbers.
