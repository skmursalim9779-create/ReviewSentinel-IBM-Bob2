# ReviewSentinel

**Agentic code-review and security-audit copilot for the IBM Bob 2.0 Hackathon**

ReviewSentinel targets a repetitive developer workflow: **code review**. It combines deterministic local security checks with optional AI explanations and produces artifacts that can be consumed by both humans and developer tooling.

---

## Project Links

- **GitHub Repository:** https://github.com/skmursalim9779-create/ReviewSentinel-IBM-Bob2
- **Live Demo:** https://reviewsentinel-hfr8.onrender.com

---

## Live Demo

**https://reviewsentinel-hfr8.onrender.com**

The deployed demo supports pasted-code reviews and the bundled demonstration workflow.

---

## The Workflow

```text
Repository / pasted file / public GitHub repository
                         │
                         ▼
                  Deterministic Scan
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Secrets    Injection    Unsafe Execution
             │           │           │
             └───────────┼───────────┘
                         ▼
                  Finding + Redaction
                         │
                  Optional AI Review
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Explain    Suggested Fix   Triage
                         │
                         ▼
              Markdown + JSON + SARIF
```

The core design keeps deterministic analysis separate from the optional AI explanation layer.

---

## Why ReviewSentinel Fits the Hackathon

The hackathon brief asks builders to improve developer workflows where time, effort, or errors are high. Examples include intelligent code review, testing, maintenance, and release workflows.

ReviewSentinel focuses on code review and makes the workflow reproducible:

1. A repository or source file is scanned using deterministic rules.
2. Findings are normalized and sensitive values are redacted.
3. An optional AI layer explains selected findings and suggests remediation.
4. Results are emitted as Markdown, JSON, and SARIF.
5. The same workflow can be demonstrated through the web interface.

### IBM Bob 2.0 in the Development Workflow

IBM Bob is part of the **development workflow**, not a claim that the runtime application itself is IBM Bob.

Bob IDE is used for:

- planning the architecture and acceptance criteria;
- implementing focused changes;
- running focused Agent tasks;
- using subagents where appropriate;
- testing and verification;
- refactoring and documentation updates;
- capturing task/session evidence for the hackathon.

The repository includes `AGENTS.md` as persistent project context and `bob_sessions/` for Bob-related evidence.

---

## What Is Included

- Python package with a clean `pyproject.toml` and console entry point.
- Deterministic static scanners for:
  - credential-like strings;
  - injection-prone SQL constructions;
  - shell-command risks;
  - dynamic execution and unsafe deserialization;
  - weak hashing;
  - oversized Python functions;
  - insecure randomness;
  - path-traversal patterns.
- Secret redaction before findings reach reports or the optional LLM layer.
- Markdown, JSON, and SARIF 2.1.0 output.
- `--fail-on` support for CI quality gates.
- Zero-build web demo with three review modes:
  - bundled synthetic repository;
  - pasted source file;
  - public GitHub repository URL with archive/path safety limits.
- Automated test suite.
- GitHub Actions CI workflow.
- Docker/Render-friendly deployment configuration.

---

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install the package in editable mode:

```bash
pip install -e .
```

For development and testing dependencies:

```bash
pip install -e ".[dev]"
```

---

## Run the Deterministic Scanner

Scan the bundled synthetic repository:

```bash
reviewsentinel scan sample_repo --out reports/sample --no-explain
```

The command produces:

```text
reports/sample.md
reports/sample.json
reports/sample.sarif
```

Example CI quality gate:

```bash
reviewsentinel scan sample_repo \
  --out reports/ci \
  --no-explain \
  --fail-on high
```

---

## Run the Web Demo

Start the local web application:

```bash
reviewsentinel-web
```

Then open:

```text
http://localhost:8000
```

The web demo provides:

- **Scan demo repo**
- **Load code example**
- pasted-code review
- public GitHub repository review

The interface displays:

- number of scanned files;
- number of findings;
- calculated health score;
- scan time;
- severity and category;
- redacted code snippets;
- security rationale;
- suggested remediation.

---

## Optional AI Explanations

The deterministic scanner does **not** require an API key.

AI explanations are optional and can be configured through supported providers.

### watsonx.ai

```text
LLM_PROVIDER=watsonx

WATSONX_URL=...
WATSONX_PROJECT_ID=...
WATSONX_API_KEY=...
WATSONX_MODEL_ID=...
```

### OpenAI-Compatible Endpoint

```text
LLM_PROVIDER=openai_compatible

LLM_BASE_URL=...
LLM_API_KEY=...
LLM_MODEL=...
```

### Privacy Boundary

Only the flagged, already-redacted snippet is sent to the optional explanation layer.

ReviewSentinel does **not** send:

- full source files;
- raw credential values;
- excluded directories;
- private/client repositories through the bundled synthetic demo workflow.

The deterministic scanner remains usable even when no AI provider is configured.

---

## Security and Privacy Boundaries

ReviewSentinel is designed around a small and explicit security boundary.

- The bundled demonstration repository is synthetic.
- Never commit real secrets.
- Never commit private or client source code.
- `.gitignore` blocks `.env` files.
- `.bobignore` keeps sensitive/generated directories out of Bob context.
- GitHub demo mode accepts `https://github.com/owner/repo` style repository URLs.
- Downloaded GitHub archives are subject to size/path safety checks.
- ZIP members are checked against path traversal.
- Credential-like source lines are redacted before reporting.
- No exploit payloads or attack tooling are generated.
- Scanner implementations are deterministic and side-effect free.

See:

```text
docs/dataset-sources.md
```

for the data-source record.

---

## Bob IDE Development Protocol

`AGENTS.md` defines the persistent working context and development constraints.

A practical IBM Bob workflow for this repository is:

1. **Plan mode**  
   Analyze the repository, define scope, acceptance criteria, and implementation order.

2. **Focused Agent task**  
   Implement one clearly bounded change.

3. **Subagents / parallel work where appropriate**  
   Use focused subagent work for independent areas such as tests, scanner improvements, documentation, or verification.

4. **Testing task**  
   Run the relevant test suite and verify regressions.

5. **Quality task**  
   Run final scanner, CLI, web, and reporting checks.

6. **Documentation task**  
   Update README, demo instructions, and hackathon artifacts.

7. **Evidence capture**  
   Capture the required Bob task/session evidence after each Bob task that was actually used.

Bob session evidence is stored under:

```text
bob_sessions/
```

See:

```text
docs/bob-workflow.md
```

for the repository's documented Bob workflow.

---

## Testing

Run the complete test suite with:

```bash
python -m pytest -q
```

The current implementation includes tests covering:

- scanner behavior;
- false-positive regressions;
- engine/config utilities;
- report generation;
- CLI behavior;
- LLM reviewer behavior;
- CI-related execution paths.

A final implementation state should only be described using test results that were actually executed.

---

## Reporting

ReviewSentinel produces three report formats.

### Markdown

Human-readable security findings and remediation context.

### JSON

Machine-readable structured findings suitable for automation and downstream processing.

### SARIF 2.1.0

A standard security-analysis interchange format suitable for integration with developer and CI tooling.

Typical outputs:

```text
reports/sample.md
reports/sample.json
reports/sample.sarif
```

---

## Measuring Impact

Do not invent benchmark numbers.

Measure the same repository before and after changes using a reproducible manual-review baseline.

Record:

- scan wall-clock time;
- number of findings;
- finding categories;
- consistency across repeated scans;
- time required to understand and triage the generated report.

The application exposes scan time and finding counts so real measurements can be used in the hackathon presentation and demo.

---

## Project Layout

```text
reviewsentinel/
├── AGENTS.md
├── README.md
├── START_HERE.md
├── pyproject.toml
├── requirements.txt
├── .bobignore
├── .gitignore
├── .env.example
│
├── bob_sessions/
│
├── docs/
│   ├── architecture.md
│   ├── bob-workflow.md
│   ├── dataset-sources.md
│   ├── demo-script.md
│   ├── hackathon-compliance.md
│   └── submission-checklist.md
│
├── examples/
│
├── reports/
│
├── sample_repo/
│
├── sample_repo_fixed/
│
├── src/
│   └── reviewsentinel/
│       ├── cli.py
│       ├── config.py
│       ├── engine.py
│       ├── llm_reviewer.py
│       ├── report.py
│       ├── web.py
│       └── scanners/
│
└── tests/
```

---

## Demo Story for the Hackathon

### Problem

Developers repeatedly rediscover common risky coding patterns and rewrite similar explanations during code review.

### Solution

ReviewSentinel turns this repetitive process into a reproducible workflow:

```text
Scan
  ↓
Detect
  ↓
Redact
  ↓
Explain
  ↓
Suggest remediation
  ↓
Report
```

### Demo Flow

A recommended demonstration sequence is:

1. Open the ReviewSentinel web demo.
2. Load the bundled code example or demo repository.
3. Run the review.
4. Show the finding count, health score, and scan time.
5. Open a security finding.
6. Show the redacted snippet.
7. Show the explanation and suggested remediation when AI is enabled.
8. Demonstrate structured Markdown, JSON, or SARIF output.
9. Show the equivalent development workflow inside IBM Bob.

### Bob Evidence

During the project build, demonstrate:

- Bob **Plan** mode;
- focused **Agent** tasks;
- subagent work where appropriate;
- test execution;
- implementation/refactoring work;
- documentation updates;
- real Bob task/session evidence stored in:

```text
bob_sessions/
```

---

## Hackathon Submission Evidence

The repository contains supporting documentation and evidence for the IBM Bob 2.0 Hackathon, including:

```text
docs/bob-workflow.md
docs/hackathon-compliance.md
docs/submission-checklist.md
bob_sessions/
```

Bob evidence should correspond to real Bob tasks actually performed during development.

Do not create or alter evidence to represent work that was not performed.

---

## Deployment

The application is deployable as a Docker/Render web service.

### Live Deployment

**https://reviewsentinel-hfr8.onrender.com**

The deployed service is configured from the repository's:

```text
render.yaml
```

---

## Current Demonstration Capabilities

The live demo currently demonstrates:

- pasted-code security review;
- deterministic finding detection;
- secret redaction;
- severity classification;
- health scoring;
- scan-time reporting;
- security findings for multiple vulnerability categories;
- optional AI explanation support;
- Render deployment.

Example findings demonstrated by the bundled workflow include:

- hardcoded credential detection;
- SQL injection-prone query construction;
- weak hashing such as MD5;
- shell execution risks;
- path traversal risks;
- unsafe deserialization;
- insecure random-number generation.

---

## Validation

The project was locally validated with:

```text
87 tests passing
```

The bundled synthetic vulnerable repository produced:

```text
8 findings
```

The fixed counterpart repository produced:

```text
0 findings
```

The pasted-code workflow produced:

```text
3 findings
```

These values are based on the current validated build.

---

## License

MIT
