"""Safe counterpart for the synthetic ReviewSentinel demo."""

import hashlib
import secrets
import subprocess
from pathlib import Path

BASE_DIR = Path("/var/app/files/")


def get_user(user_id, db):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))


def hash_password(password, salt=b"demo-only"):
    return hashlib.sha256(salt + password.encode()).hexdigest()


def export_report(filename):
    # Prefer subprocess argument arrays and avoid a shell interpreter.
    subprocess.run(["cat", filename], check=True, stdout=open("/tmp/out.txt", "w", encoding="utf-8"))


def load_config(raw_yaml):
    import yaml
    return yaml.load(raw_yaml, Loader=yaml.SafeLoader)


def run_snippet(user_expression):
    raise ValueError("Dynamic execution is disabled")


def get_file_contents(filename: str):
    # Resolve the full path and confirm it stays within BASE_DIR.
    target = (BASE_DIR / filename).resolve()
    if not str(target).startswith(str(BASE_DIR.resolve())):
        raise ValueError("Access denied: path outside allowed directory")
    with open(target, encoding="utf-8") as f:
        contents = f.read()
    # Use the secrets module for cryptographically secure tokens.
    session_token = secrets.token_hex(16)
    return contents, session_token
