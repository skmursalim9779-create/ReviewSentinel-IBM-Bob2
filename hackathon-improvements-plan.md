# ReviewSentinel — Hackathon Improvement Plan

## Overview

**Goal:** Maximise technical credibility and correctness for the hackathon submission by: (1) dramatically expanding test coverage, (2) hardening and extending the scanner rules, and (3) making targeted fixes to the LLM reviewer and web server.

**Scope:** Three focused sub-tasks executed in order. No structural refactors, no new frameworks, no feature additions beyond 1–2 targeted new scan rules.

**Non-goals:** Rate limiting, authentication, PDF/HTML export, historical trending, compare/diff mode, new LLM providers, UI redesign.

---

## Sub-Task 1 — Test Coverage Expansion

**Status:** `[ ] pending`

### Intent
The project currently has only 7 unit tests covering the 5 scanners. Zero tests exist for the engine, config utilities, report generation, CLI, and LLM reviewer. This is the highest-risk gap for a technical submission — reviewers will look for evidence of correctness. This sub-task brings coverage to all non-web modules.

### Expected Outcomes
- Engine functions (`scan_source`, `scan_path`, `severity_counts`, `risk_score`, `category_counts`) have direct unit tests.
- Config utilities (`mask_secret_line`, `iter_scannable_files`, `is_excluded`) have direct unit tests.
- Report module (`to_markdown`, `to_json`, `to_sarif`, `write_reports`) has unit tests verifying key fields.
- CLI argument parsing and exit codes are tested (exit 0, 1, 2 paths).
- LLM reviewer's disabled/static-explanation path is tested without any network calls.
- Each scanner gains at least one false-positive regression test (a safe variant that must NOT produce a finding).
- `pytest -q` passes with all new tests.
- CI remains green.

### Todo List
1. In `tests/test_engine.py`, write unit tests for:
   - `scan_source()` on a small synthetic source string (check finding count, rule ids, sort order).
   - `severity_counts()` — verify zero-count severities are excluded.
   - `risk_score()` — verify clamping at 0 and 100, verify known input → known score.
   - `category_counts()` — verify sort order (count desc, name asc tie-break).
   - `scan_path()` on a temp directory with two known files — verify `ScanResult.files_scanned` and `ScanResult.findings`.
2. In `tests/test_config.py`, write unit tests for:
   - `mask_secret_line()` — verify a known API key string is redacted.
   - `is_excluded()` — verify venv/ and .git/ paths are excluded.
   - `iter_scannable_files()` — verify .py files included, binary files skipped, excluded dirs skipped.
3. In `tests/test_report.py`, write unit tests for:
   - `to_markdown()` — check that severity labels, rule IDs, file paths, and score appear in output.
   - `to_json()` — parse the JSON and assert `summary.risk_score` and `findings[0].rule_id` are present.
   - `to_sarif()` — assert `version == "2.1.0"`, `runs[0].results` is non-empty, `level` maps correctly.
   - `write_reports()` — write to a temp dir, verify all three files exist and are non-empty.
4. In `tests/test_cli.py`, write unit tests for:
   - `--help` exits 0 (use `CliRunner.invoke`).
   - `scan sample_repo --no-explain` exits 0 and produces finding output (use `CliRunner.invoke`).
   - `--fail-on critical` exits 1 when scanning a temp file with a CRITICAL finding (use `CliRunner.invoke`).
   - A non-existent path exits 2 (use `CliRunner.invoke`).
   - Real subprocess call only for the CI integration smoke-test (mirrors what CI already does): `subprocess.run(["reviewsentinel", "scan", "sample_repo", "--no-explain"])` exits 0. Only add this test if it adds clear value beyond the CliRunner tests above.
5. In `tests/test_llm_reviewer.py`, write unit tests for:
   - When `enabled=False`, every finding receives a `"Static analysis finding"` explanation and no HTTP calls are made.
   - When `enabled=True` but no env vars set, falls back to static explanations gracefully.
6. Add false-positive regression tests to existing scanner test file:
   - `secrets.py`: a test helper function with `test_api_key = "short"` must NOT produce a finding.
   - `injection.py`: `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))` must NOT produce a finding.
   - `weak_crypto.py`: `hashlib.sha256(data)` must NOT produce a finding.
   - `unsafe_eval.py`: `yaml.load(raw, Loader=yaml.SafeLoader)` must NOT produce a finding (already exists — verify it still passes).

### Relevant Context
- `src/reviewsentinel/engine.py` — `scan_source`, `scan_path`, `severity_counts`, `risk_score`, `category_counts`
- `src/reviewsentinel/config.py` — `mask_secret_line`, `is_excluded`, `iter_scannable_files`, `Finding`, `ScanResult`
- `src/reviewsentinel/report.py` — `to_markdown`, `to_json`, `to_sarif`, `write_reports`
- `src/reviewsentinel/cli.py` — `main()`; uses `sys.exit`
- `src/reviewsentinel/llm_reviewer.py` — `explain(findings, enabled)`, `_static_explanation()`
- `tests/test_scanners.py` — existing tests; add false-positive cases here

---

## Sub-Task 2 — Scanner Hardening and New Rules

**Status:** `[ ] pending`

### Intent
Improve detection quality and reduce false positives in the existing 5 scanners, and add 2 new targeted rule families (path traversal and insecure random) that are easy to demonstrate and cover real vulnerability classes. New rules follow the same scanner interface contract.

### Expected Outcomes
- `secrets.py` false-positive rate reduced: variable names in comments and `test_*`/`fake_*`/`example_*` contexts are filtered.
- `injection.py` gains detection for `subprocess.Popen(..., shell=True)` (currently missed).
- `weak_crypto.py` AST + regex duplication removed; single clean detection path.
- `weak_crypto.py` gains detection for `random.randint`, `random.choice`, `random.random` used in security contexts (insecure random, `RS-CRYPTO-003`).
- New scanner `path_traversal.py` detects `os.path.join` with user-controlled input and `open()` calls where the path argument contains string concatenation or f-string with a variable (`RS-TRAVERSE-001`, HIGH).
- Scanner registry in `scanners/__init__.py` registers the new path traversal scanner.
- `sample_repo/user_service.py` gains 1–2 new vulnerable lines exercising the new rules.
- `sample_repo_fixed/user_service.py` gains the corresponding safe fixes.
- All new scanner rules have at least one positive test (finds the issue) and one negative test (does not false-positive on the safe version) in `tests/test_scanners.py`.
- `pytest -q` passes with all scanner tests.

### Todo List
1. **secrets.py improvements:**
   - Skip lines where the matched assignment variable name starts with `test_`, `fake_`, `mock_`, `example_`, or `sample_`.
   - Skip lines that are pure comments (stripped line starts with `#`).
   - Add regression test: `# api_key = "sk-abcdefghij"` (comment) must NOT flag.
   - Add regression test: `test_api_key = "sk-abcdefghijklmnopqrstu"` must NOT flag.
2. **injection.py improvements:**
   - Add detection for `subprocess.Popen` with `shell=True` under `RS-INJECT-002`.
   - Add regression test: `subprocess.Popen(["ls", "-la"])` (no shell=True) must NOT flag.
3. **weak_crypto.py cleanup + insecure random:**
   - Remove redundant regex pass for `RS-CRYPTO-001`; keep AST-only detection path.
   - Add `RS-CRYPTO-003` (MEDIUM): detect calls to `random.randint`, `random.choice`, `random.random`, `random.randrange` — the `random` module is not cryptographically secure. Use AST. Only flag if the module imported as `random` (check import aliases).
   - Add positive test: `random.randint(0, 100)` in a Python file flags `RS-CRYPTO-003`.
   - Add negative test: `secrets.randbelow(100)` does NOT flag.
4. **New scanner: path_traversal.py:**
   - Create `src/reviewsentinel/scanners/path_traversal.py`.
   - Rule `RS-TRAVERSE-001` (HIGH): Use AST to detect `open()` calls where the first argument is a `BinOp` (string concatenation) or `JoinedStr` (f-string) containing a `Name` node — indicating a variable is used directly in a file path.
   - Rule `RS-TRAVERSE-002` (HIGH): Detect `os.path.join` calls where any argument is a `Name` or `Subscript` referencing common user-input names (`request`, `args`, `params`, `data`, `input`, `filename`).
   - Python-only (skip non-.py files).
   - Graceful fallback on SyntaxError.
   - Add positive tests: `open(base_dir + user_input, "r")` flags `RS-TRAVERSE-001`; `os.path.join("/data", request.args["filename"])` flags `RS-TRAVERSE-002`.
   - Add negative test: `open("config.json", "r")` does NOT flag.
5. **Scanner registry:**
   - In `src/reviewsentinel/scanners/__init__.py`, import and register `PathTraversalScanner` alongside the existing 5.
6. **Sample repo:**
   - Add a `get_file_contents(filename)` function to `sample_repo/user_service.py` that calls `open(base_path + filename)` (triggers `RS-TRAVERSE-001`) and uses `random.randint` for a session token (triggers `RS-CRYPTO-003`).
   - Add the safe version to `sample_repo_fixed/user_service.py` using `pathlib.Path(...).resolve()` and `secrets.token_hex()`.

### Relevant Context
- `src/reviewsentinel/scanners/secrets.py` — regex-based; add variable name filter
- `src/reviewsentinel/scanners/injection.py` — regex-based; extend Popen detection
- `src/reviewsentinel/scanners/weak_crypto.py` — AST + regex duplication; clean up + add RS-CRYPTO-003
- `src/reviewsentinel/scanners/__init__.py` — scanner registry
- `src/reviewsentinel/config.py` — `Finding`, severity constants, `SCANNABLE_EXTENSIONS`
- `sample_repo/user_service.py` — add 2 new vulnerable examples
- `sample_repo_fixed/user_service.py` — add 2 safe counterparts
- `tests/test_scanners.py` — add all new positive/negative tests here

---

## Sub-Task 3 — LLM Reviewer and Web Server Lightweight Fixes

**Status:** `[ ] pending`

### Intent
Fix two correctness bugs identified in the audit that affect demo reliability: (1) the bare `except Exception` in the LLM reviewer silently hides errors, and (2) the web server always enables LLM explanations regardless of configuration, which is misleading and could cause unexpected API calls during demos.

### Expected Outcomes
- `llm_reviewer.py`: bare `except Exception` replaced with explicit exception types (`requests.RequestException`, `ValueError`, `KeyError`); each caught separately with a descriptive fallback message logged to stderr.
- `llm_reviewer.py`: a warning is printed to stderr when the LLM call fails, so failures are observable.
- `web.py`: the `explain()` call respects a configurable flag rather than hardcoding `enabled=True`; by default LLM is disabled in web mode unless `ENABLE_LLM_WEB=1` env var is set.
- `.env.example` updated to document the new `ENABLE_LLM_WEB` variable.
- `tests/test_llm_reviewer.py` (written in Sub-Task 1) verifies the disabled path and the fallback-on-error path (mock a `requests.RequestException`).
- `pytest -q` passes with all tests.

### Todo List
1. **llm_reviewer.py — exception handling:**
   - Replace the broad `except Exception as e` block (around the provider API call) with:
     - `except requests.RequestException as e:` → print warning to stderr, return static explanation.
     - `except (ValueError, KeyError) as e:` → print warning to stderr (JSON parse failure), return static explanation.
   - Ensure the warning message includes the rule ID and a short reason.
2. **web.py — LLM enable flag:**
   - Read `os.environ.get("ENABLE_LLM_WEB", "0")` at module level.
   - Pass `enabled=(ENABLE_LLM_WEB == "1")` to the `explain()` call on the relevant line (currently hardcodes `enabled=True`).
   - Add an inline comment explaining the flag.
3. **.env.example — document the new flag:**
   - Add `ENABLE_LLM_WEB=0  # Set to 1 to enable LLM explanations in web mode` to the file.
4. **tests/test_llm_reviewer.py (extend, not replace):**
   - Add a test that patches `requests.post` to raise `requests.RequestException` and confirms the function returns a finding with a static explanation rather than raising.

### Relevant Context
- `src/reviewsentinel/llm_reviewer.py` — line ~85, bare `except Exception`; `explain()` function
- `src/reviewsentinel/web.py` — line ~172, `explain(..., enabled=True)`; also `import os` already present
- `.env.example` — add new variable documentation
- `tests/test_llm_reviewer.py` — created in Sub-Task 1, extended here

---

## Implementation Notes

- Execute sub-tasks **in order**: tests first (establishes a baseline), then scanner improvements, then web/LLM fixes.
- After each sub-task, run `pytest -q` to confirm all tests pass before proceeding.
- After Sub-Task 2, also run `reviewsentinel scan sample_repo --no-explain` to confirm the new rules fire on the new sample code.
- After Sub-Task 3, verify the web server starts cleanly and the demo works without a configured LLM provider.
- Do not change `AGENTS.md`, `README.md`, or docs during implementation — a documentation update pass is a separate task boundary per `AGENTS.md`.
