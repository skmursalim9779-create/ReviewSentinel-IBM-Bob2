"""Zero-build web demo for ReviewSentinel.

Supports the bundled synthetic repo and a pasted code snippet. Public GitHub
repo scanning is available through the API with strict host/path validation.
"""

import io
import json
import os
import re
import tempfile
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import requests

from .engine import scan_path, scan_source, category_counts, risk_score, severity_counts
from .config import SEVERITY_ORDER
from .llm_reviewer import explain
from .report import to_markdown, to_sarif

_LLM_WEB_ENABLED = os.environ.get("ENABLE_LLM_WEB", "0") == "1"  # set ENABLE_LLM_WEB=1 to enable AI explanations in web mode

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPO = ROOT / "sample_repo"
MAX_GITHUB_ZIP_BYTES = 25 * 1024 * 1024
MAX_EXTRACTED_BYTES = 100 * 1024 * 1024
GITHUB_RE = re.compile(r"^https://(?:www\.)?github\.com/([A-Za-z0-9_.-]{1,100})/([A-Za-z0-9_.-]{1,100})(?:/)?$")

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ReviewSentinel · Agentic Code Review</title>
<style>
:root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
body { margin:0; background:#0b1020; color:#eef2ff; }
.wrap { max-width:1100px; margin:auto; padding:32px 20px 60px; }
.hero { display:flex; justify-content:space-between; gap:20px; align-items:flex-end; margin-bottom:24px; }
h1 { margin:0 0 6px; font-size:38px; } p { color:#a9b4ce; }
.panel { background:#131a2e; border:1px solid #27304a; border-radius:16px; padding:18px; margin:16px 0; }
textarea,input { width:100%; box-sizing:border-box; background:#0b1020; color:#fff; border:1px solid #34405e; border-radius:10px; padding:12px; }
textarea { min-height:150px; resize:vertical; }
button { background:#4f7cff; color:white; border:0; border-radius:10px; padding:11px 15px; font-weight:700; cursor:pointer; }
button.secondary { background:#26314e; }
.controls { display:grid; gap:10px; }
.grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0; }
.card { background:#11182a; border:1px solid #27304a; padding:16px; border-radius:14px; }
.card b { display:block; font-size:28px; margin-top:5px; }
.finding { background:#0e1527; border:1px solid #28324e; border-radius:12px; padding:14px; margin:10px 0; }
.badge { display:inline-block; padding:3px 8px; border-radius:999px; font-size:12px; font-weight:700; text-transform:uppercase; background:#27304a; }
pre { white-space:pre-wrap; overflow:auto; background:#080c17; border-radius:8px; padding:10px; }
.muted { color:#91a0bd; font-size:13px; }
.row { display:flex; gap:10px; flex-wrap:wrap; }
@media (max-width:800px) { .grid {grid-template-columns:repeat(2,1fr);} .hero {align-items:flex-start; flex-direction:column;} }
</style>
</head>
<body>
<div class="wrap">
<div class="hero"><div><div class="muted">IBM Bob 2.0 hackathon prototype</div><h1>ReviewSentinel</h1><p>Scan → explain → report. Turn repetitive security review into a reproducible developer workflow.</p></div></div>
<div class="panel">
<h2>Run a review</h2>
<div class="row"><button onclick="runSample()">Scan demo repo</button><button class="secondary" onclick="document.getElementById('code').value='api_key = &quot;sk-demo-replace-me&quot;\nquery = &quot;SELECT * FROM users WHERE id = &quot; + user_id\nimport hashlib\nhashlib.md5(password.encode())'">Load code example</button></div>
<div class="controls" style="margin-top:12px"><label>Public GitHub repository URL</label><input id="github" placeholder="https://github.com/owner/repo"><button onclick="runGithub()">Scan public GitHub repo</button><label>Or paste one file for a quick review</label><textarea id="code" placeholder="Paste Python / JS / TS / Java / Go / Ruby / PHP code here"></textarea><input id="filename" value="snippet.py"><button onclick="runCode()">Review pasted code</button></div>
</div>
<div id="status" class="panel muted">Ready.</div>
<div id="summary"></div>
<div id="findings"></div>
</div>
<script>
const statusEl = document.getElementById('status');
function setStatus(t){statusEl.textContent=t;}
function esc(s){return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}
function render(d){
  const s=d.summary;
  document.getElementById('summary').innerHTML=`<div class="grid"><div class="card">Files<b>${s.files_scanned}</b></div><div class="card">Findings<b>${s.findings}</b></div><div class="card">Health<b>${s.risk_score}/100</b></div><div class="card">Scan time<b>${s.scan_seconds}s</b></div></div>`;
  document.getElementById('findings').innerHTML=`<div class="panel"><h2>Findings</h2>${d.findings.length?d.findings.map(f=>`<div class="finding"><span class="badge">${esc(f.severity)}</span> <span class="muted">${esc(f.category)} · ${esc(f.rule_id)} · ${esc(f.file)}:${esc(f.line)}</span><h3>${esc(f.message)}</h3><pre>${esc(f.snippet)}</pre><p><b>Why it matters:</b> ${esc(f.explanation||'Static rule finding; no LLM explanation configured.')}</p><p><b>Suggested fix:</b> ${esc(f.suggested_fix||'Review the secure alternative for this rule.')}</p></div>`).join(''):'<p>No findings. ✅</p>'}</div>`;
}
async function post(body){
 setStatus('Running review…');
 const r=await fetch('/api/scan',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}); const d=await r.json();
 if(!r.ok){setStatus(d.error||'Request failed');return;} setStatus('Review complete.'); render(d);
}
function runSample(){post({source:'sample'});}
function runCode(){post({source:'code',filename:document.getElementById('filename').value,content:document.getElementById('code').value});}
function runGithub(){post({source:'github',url:document.getElementById('github').value});}
</script>
</body></html>'''


def _download_github_repo(url: str) -> Path:
    m = GITHUB_RE.fullmatch(url.strip())
    if not m:
        raise ValueError("Only public github.com/owner/repo URLs are accepted")
    owner, repo = m.group(1), m.group(2)
    meta = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=12, headers={"Accept": "application/vnd.github+json", "User-Agent": "ReviewSentinel/0.2"})
    meta.raise_for_status()
    branch = meta.json().get("default_branch") or "main"
    r = requests.get(f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}", timeout=30, headers={"User-Agent": "ReviewSentinel/0.2"}, stream=True)
    r.raise_for_status()
    data = bytearray()
    for chunk in r.iter_content(chunk_size=1024 * 1024):
        data.extend(chunk)
        if len(data) > MAX_GITHUB_ZIP_BYTES:
            raise ValueError("Repository archive exceeds the 25 MB demo limit")

    tmp = Path(tempfile.mkdtemp(prefix="reviewsentinel-"))
    archive = tmp / "repo.zip"
    archive.write_bytes(data)
    extract = tmp / "repo"
    extract.mkdir()
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError("Unsafe archive path rejected")
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("Extracted repository exceeds the 100 MB demo limit")
        zf.extractall(extract)
    roots = [p for p in extract.iterdir() if p.is_dir()]
    return roots[0] if len(roots) == 1 else extract


class Handler(BaseHTTPRequestHandler):
    server_version = "ReviewSentinel/0.2"

    def _send(self, status: int, payload, content_type="application/json"):
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            return self._send(HTTPStatus.OK, HTML, "text/html; charset=utf-8")
        if path == "/api/health":
            return self._send(HTTPStatus.OK, {"status": "ok", "version": "0.2.0"})
        return self._send(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self):  # noqa: N802
        if urlparse(self.path).path != "/api/scan":
            return self._send(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 512 * 1024:
                raise ValueError("Request body too large")
            payload = json.loads(self.rfile.read(length) or b"{}")
            mode = payload.get("source")
            if mode == "sample":
                result = scan_path(SAMPLE_REPO)
            elif mode == "code":
                filename = str(payload.get("filename") or "snippet.py")
                content = str(payload.get("content") or "")
                if len(content) > 200_000:
                    raise ValueError("Pasted code exceeds the 200 KB demo limit")
                findings = scan_source(filename, content)
                from .config import ScanResult
                result = ScanResult(findings=findings, files_scanned=1, scan_seconds=0.0)
            elif mode == "github":
                root = _download_github_repo(str(payload.get("url") or ""))
                result = scan_path(root)
            else:
                raise ValueError("source must be sample, code, or github")

            explain(result.findings, enabled=_LLM_WEB_ENABLED)
            response = to_json_response(result)
            return self._send(HTTPStatus.OK, response)
        except requests.HTTPError as exc:
            return self._send(HTTPStatus.BAD_GATEWAY, {"error": f"GitHub request failed: {exc}"})
        except Exception as exc:  # noqa: BLE001
            return self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def to_json_response(result):
    findings = sorted(result.findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.file, f.line, f.rule_id))
    return {
        "summary": {
            "files_scanned": result.files_scanned,
            "scan_seconds": round(result.scan_seconds, 3),
            "findings": len(findings),
            "risk_score": risk_score(findings),
            "severity": severity_counts(findings),
            "categories": category_counts(findings),
        },
        "findings": [f.__dict__ for f in findings],
        "reports": {
            "markdown": to_markdown(findings, result.files_scanned, result.scan_seconds),
            "sarif": to_sarif(findings),
        },
    }


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"ReviewSentinel web demo listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
