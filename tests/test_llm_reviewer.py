"""Unit tests for reviewsentinel.llm_reviewer — no real HTTP calls."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.config import Finding
from reviewsentinel.llm_reviewer import explain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding(rule_id="RS-SECRET-001", severity="high", file="app.py", line=5,
              category="security"):
    return Finding(
        rule_id=rule_id,
        severity=severity,
        file=file,
        line=line,
        message="Hardcoded secret detected",
        snippet='api_key = "[REDACTED]"',
        category=category,
    )


# ---------------------------------------------------------------------------
# enabled=False — static explanation, no HTTP
# ---------------------------------------------------------------------------

def test_disabled_returns_findings_unchanged():
    findings = [_finding()]
    with patch("requests.post") as mock_post:
        result = explain(findings, enabled=False)
        mock_post.assert_not_called()
    # Returns the same list
    assert result is findings


def test_disabled_does_not_set_explanation():
    """When disabled, explanation is left as whatever it was (empty default)."""
    f = _finding()
    assert f.explanation == ""
    explain([f], enabled=False)
    # Still empty — disabled path does not add explanations
    assert f.explanation == ""


def test_disabled_multiple_findings_no_http():
    findings = [_finding(rule_id=f"RS-TEST-{i:03d}") for i in range(5)]
    with patch("requests.post") as mock_post:
        explain(findings, enabled=False)
        mock_post.assert_not_called()


# ---------------------------------------------------------------------------
# enabled=True but no LLM_PROVIDER set → static fallback, no HTTP
# ---------------------------------------------------------------------------

def test_no_provider_returns_static_explanation():
    env = {k: v for k, v in os.environ.items() if k not in ("LLM_PROVIDER",)}
    f = _finding()
    with patch.dict(os.environ, env, clear=True), patch("requests.post") as mock_post:
        explain([f], enabled=True)
        mock_post.assert_not_called()
    assert f.explanation != ""
    assert "Static" in f.explanation or "provider" in f.explanation.lower() or "configure" in f.explanation.lower()


def test_no_provider_sets_suggested_fix():
    env = {k: v for k, v in os.environ.items() if k not in ("LLM_PROVIDER",)}
    f = _finding()
    with patch.dict(os.environ, env, clear=True):
        explain([f], enabled=True)
    assert f.suggested_fix != ""


# ---------------------------------------------------------------------------
# enabled=True with watsonx provider — mock HTTP success
# ---------------------------------------------------------------------------

def test_watsonx_provider_calls_requests_post():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"generated_text": json.dumps({
            "explanation": "Hardcoded key exposes credentials.",
            "suggested_fix": "Use environment variables.",
        })}]
    }
    mock_response.raise_for_status = MagicMock()

    env_vars = {
        "LLM_PROVIDER": "watsonx",
        "WATSONX_URL": "https://fake.watsonx.example.com",
        "WATSONX_API_KEY": "fake-api-key",
        "WATSONX_PROJECT_ID": "fake-project-id",
    }
    f = _finding()
    with patch("requests.post", return_value=mock_response) as mock_post, \
         patch.dict(os.environ, env_vars, clear=False):
        explain([f], enabled=True)
        mock_post.assert_called_once()
    assert f.explanation == "Hardcoded key exposes credentials."
    assert f.suggested_fix == "Use environment variables."


# ---------------------------------------------------------------------------
# enabled=True with watsonx provider — mock HTTP failure (RequestException)
# ---------------------------------------------------------------------------

def test_request_exception_falls_back_to_static_explanation():
    import requests as req_lib

    env_vars = {
        "LLM_PROVIDER": "watsonx",
        "WATSONX_URL": "https://fake.watsonx.example.com",
        "WATSONX_API_KEY": "fake-api-key",
        "WATSONX_PROJECT_ID": "fake-project-id",
    }
    f = _finding()
    with patch("requests.post", side_effect=req_lib.RequestException("connection refused")), \
         patch.dict(os.environ, env_vars, clear=False):
        result = explain([f], enabled=True)

    # Must not raise; must return findings with a non-empty explanation
    assert result is not None
    assert f.explanation != ""


# ---------------------------------------------------------------------------
# enabled=True with openai_compatible provider — mock HTTP success
# ---------------------------------------------------------------------------

def test_openai_compatible_provider_calls_requests_post():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps({
            "explanation": "Open AI explanation.",
            "suggested_fix": "Use secrets module.",
        })}}]
    }
    mock_response.raise_for_status = MagicMock()

    env_vars = {
        "LLM_PROVIDER": "openai_compatible",
        "LLM_BASE_URL": "https://fake.openai.example.com",
        "LLM_API_KEY": "fake-key",
    }
    f = _finding()
    with patch("requests.post", return_value=mock_response) as mock_post, \
         patch.dict(os.environ, env_vars, clear=False):
        explain([f], enabled=True)
        mock_post.assert_called_once()
    assert f.explanation == "Open AI explanation."
