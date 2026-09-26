"""Provider-agnostic finding explanations; never sends whole files."""

import json
import os
import sys

import requests

from .config import Finding

_PROMPT_TEMPLATE = """You are a concise senior code reviewer.
A static scanner flagged {file}:{line} with rule {rule_id}.
Category: {category}
Finding: {message}

Code snippet (may be redacted):
{snippet}

Return JSON only with keys:
explanation: one concrete risk explanation in <= 45 words
suggested_fix: one concise remediation action, <= 30 words
Do not provide exploit payloads.
"""


def build_prompt(f: Finding) -> str:
    return _PROMPT_TEMPLATE.format(
        file=f.file, line=f.line, rule_id=f.rule_id, category=f.category,
        message=f.message, snippet=f.snippet
    )


def _call_watsonx(prompt: str) -> str:
    url = os.environ["WATSONX_URL"].rstrip("/") + "/ml/v1/text/generation?version=2023-05-29"
    headers = {"Authorization": f"Bearer {os.environ['WATSONX_API_KEY']}", "Content-Type": "application/json"}
    body = {
        "input": prompt,
        "project_id": os.environ["WATSONX_PROJECT_ID"],
        "model_id": os.environ.get("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2"),
        "parameters": {"max_new_tokens": 180, "temperature": 0.2},
    }
    response = requests.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    return response.json()["results"][0]["generated_text"].strip()


def _call_openai_compatible(prompt: str) -> str:
    url = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {os.environ['LLM_API_KEY']}", "Content-Type": "application/json"}
    body = {
        "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 180,
        "temperature": 0.2,
    }
    response = requests.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _parse_response(raw: str) -> tuple[str, str]:
    try:
        data = json.loads(raw)
        return str(data.get("explanation", raw)).strip(), str(data.get("suggested_fix", "Review the flagged pattern and apply the least-privilege remediation.")).strip()
    except json.JSONDecodeError:
        return raw.strip(), "Review the flagged pattern and apply the least-privilege remediation."


def explain(findings: list[Finding], enabled: bool = True) -> list[Finding]:
    if not enabled:
        return findings
    provider = os.environ.get("LLM_PROVIDER")
    if not provider:
        for finding in findings:
            finding.explanation = "Static finding; configure an LLM provider for a plain-English explanation."
            finding.suggested_fix = "Inspect the flagged line and apply the secure alternative described by the rule."
        return findings

    caller = {"watsonx": _call_watsonx, "openai_compatible": _call_openai_compatible}.get(provider)
    if caller is None:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    for finding in findings:
        try:
            finding.explanation, finding.suggested_fix = _parse_response(caller(build_prompt(finding)))
        except requests.RequestException as exc:
            print(f"WARNING [{finding.rule_id}]: network/request error — {exc}", file=sys.stderr)
            finding.explanation = "Static analysis finding; LLM explanation unavailable due to a network/request error."
            finding.suggested_fix = "Use the scanner message to remediate the flagged pattern."
        except (ValueError, KeyError) as exc:
            print(f"WARNING [{finding.rule_id}]: response parse error — {exc}", file=sys.stderr)
            finding.explanation = "Static analysis finding; LLM explanation unavailable due to a response parse error."
            finding.suggested_fix = "Use the scanner message to remediate the flagged pattern."
    return findings
