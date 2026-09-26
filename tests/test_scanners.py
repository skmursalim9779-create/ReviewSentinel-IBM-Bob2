import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewsentinel.scanners import complexity, injection, secrets, unsafe_eval, weak_crypto


def test_secret_is_flagged_and_redacted():
    findings = secrets.scan("f.py", 'api_key = "sk-abcdefghijklmnopqrstuvwx"\n')
    assert len(findings) == 1
    assert "REDACTED" in findings[0].snippet


def test_short_placeholder_is_ignored():
    assert secrets.scan("f.py", 'api_key = "x"\n') == []


def test_sql_and_shell_injection():
    src = 'query = "SELECT * FROM users WHERE id = " + user_id\nsubprocess.run(cmd, shell=True)\n'
    findings = injection.scan("f.py", src)
    assert {f.rule_id for f in findings} == {"RS-INJECT-001", "RS-INJECT-002"}


def test_unsafe_calls_are_flagged_but_safe_yaml_is_not():
    src = "eval(user_input)\npickle.loads(data)\nyaml.load(raw)\nyaml.load(raw, Loader=yaml.SafeLoader)\n"
    ids = {f.rule_id for f in unsafe_eval.scan("f.py", src)}
    assert {"RS-EVAL-001", "RS-EVAL-003", "RS-EVAL-004"}.issubset(ids)
    safe_lines = [f.line for f in unsafe_eval.scan("f.py", src) if f.rule_id == "RS-EVAL-004"]
    assert safe_lines == [3]


def test_weak_crypto():
    findings = weak_crypto.scan("f.py", "import hashlib\nhashlib.md5(password.encode())\n")
    assert any(f.rule_id == "RS-CRYPTO-001" for f in findings)


def test_complexity_uses_ast_end_lineno():
    body = "\n".join(f"    x{i} = {i}" for i in range(70))
    findings = complexity.scan("f.py", f"def big_function():\n{body}\n")
    assert any(f.rule_id == "RS-COMPLEX-001" for f in findings)


def test_non_python_complexity_is_skipped():
    assert complexity.scan("f.js", "function a() {}\n") == []


# ---------------------------------------------------------------------------
# False-positive regression tests (Sub-Task 1, item 6)
# ---------------------------------------------------------------------------

def test_secret_short_test_variable_not_flagged():
    """Variable named test_api_key with a short value must NOT produce a finding."""
    assert secrets.scan("f.py", 'test_api_key = "short"\n') == []


def test_secret_long_value_is_flagged():
    """Sanity: a sufficiently long secret IS still flagged."""
    findings = secrets.scan("f.py", 'api_key = "sk-abcdefghijklmnopqrstuvwx"\n')
    assert len(findings) >= 1


def test_injection_parameterized_query_not_flagged():
    """Parameterised query with ? placeholder must NOT produce a finding."""
    src = 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))\n'
    findings = injection.scan("f.py", src)
    assert not any(f.rule_id == "RS-INJECT-001" for f in findings)


def test_weak_crypto_sha256_not_flagged():
    """hashlib.sha256 is a strong hash and must NOT produce a finding."""
    findings = weak_crypto.scan("f.py", "import hashlib\nhashlib.sha256(data)\n")
    assert not any(f.rule_id == "RS-CRYPTO-001" for f in findings)


def test_unsafe_yaml_safe_loader_not_flagged():
    """yaml.load with Loader=yaml.SafeLoader is safe and must NOT be flagged as RS-EVAL-004."""
    src = "yaml.load(raw, Loader=yaml.SafeLoader)\n"
    ids = {f.rule_id for f in unsafe_eval.scan("f.py", src)}
    assert "RS-EVAL-004" not in ids


# ---------------------------------------------------------------------------
# Sub-Task 2 — new scanner tests
# ---------------------------------------------------------------------------

from reviewsentinel.scanners import path_traversal


# --- path_traversal: RS-TRAVERSE-001 ---------------------------------------

def test_traverse_001_open_concat_flags():
    """open(base_dir + user_input, 'r') must flag RS-TRAVERSE-001."""
    src = 'open(base_dir + user_input, "r")\n'
    ids = [f.rule_id for f in path_traversal.scan("f.py", src)]
    assert "RS-TRAVERSE-001" in ids


def test_traverse_001_open_literal_not_flagged():
    """open('config.json', 'r') with a literal path must NOT flag."""
    src = 'open("config.json", "r")\n'
    assert path_traversal.scan("f.py", src) == []


def test_traverse_001_open_fstring_flags():
    """open(f'{base}/{name}') must flag RS-TRAVERSE-001."""
    src = 'open(f"{base_dir}/{filename}", "r")\n'
    ids = [f.rule_id for f in path_traversal.scan("f.py", src)]
    assert "RS-TRAVERSE-001" in ids


# --- path_traversal: RS-TRAVERSE-002 ---------------------------------------

def test_traverse_002_os_path_join_user_input_flags():
    """os.path.join('/data', filename) where filename is a Name node must flag RS-TRAVERSE-002."""
    src = 'import os\nos.path.join("/data", filename)\n'
    ids = [f.rule_id for f in path_traversal.scan("f.py", src)]
    assert "RS-TRAVERSE-002" in ids


def test_traverse_002_os_path_join_literals_not_flagged():
    """os.path.join with only literals must NOT flag."""
    src = 'import os\nos.path.join("/data", "reports", "out.csv")\n'
    assert path_traversal.scan("f.py", src) == []


# --- weak_crypto: RS-CRYPTO-003 --------------------------------------------

def test_crypto_003_random_randint_flags():
    """random.randint with import random must flag RS-CRYPTO-003."""
    src = "import random\ntoken = random.randint(0, 100)\n"
    ids = [f.rule_id for f in weak_crypto.scan("f.py", src)]
    assert "RS-CRYPTO-003" in ids


def test_crypto_003_secrets_not_flagged():
    """secrets.randbelow must NOT flag RS-CRYPTO-003."""
    src = "import secrets\nval = secrets.randbelow(100)\n"
    ids = [f.rule_id for f in weak_crypto.scan("f.py", src)]
    assert "RS-CRYPTO-003" not in ids


def test_crypto_003_only_flagged_when_random_imported():
    """random.randint without an 'import random' must NOT flag RS-CRYPTO-003."""
    src = "token = random.randint(0, 100)\n"
    ids = [f.rule_id for f in weak_crypto.scan("f.py", src)]
    assert "RS-CRYPTO-003" not in ids


# --- secrets: false-positive regressions -----------------------------------

def test_secret_test_api_key_long_not_flagged():
    """test_api_key = '...' (long value, test_ prefix) must NOT flag."""
    assert secrets.scan("f.py", 'test_api_key = "sk-abcdefghijklmnopqrstu"\n') == []


def test_secret_comment_line_not_flagged():
    """A pure comment line containing a key-like pattern must NOT flag."""
    assert secrets.scan("f.py", '# api_key = "sk-abcdefghijklmno"\n') == []


# --- injection: subprocess.Popen regressions -------------------------------

def test_injection_popen_no_shell_not_flagged():
    """subprocess.Popen with a list and no shell=True must NOT flag RS-INJECT-002."""
    src = 'subprocess.Popen(["ls", "-la"])\n'
    ids = [f.rule_id for f in injection.scan("f.py", src)]
    assert "RS-INJECT-002" not in ids


def test_injection_popen_shell_true_flags():
    """subprocess.Popen('ls -la', shell=True) must flag RS-INJECT-002."""
    src = 'subprocess.Popen("ls -la", shell=True)\n'
    ids = [f.rule_id for f in injection.scan("f.py", src)]
    assert "RS-INJECT-002" in ids
