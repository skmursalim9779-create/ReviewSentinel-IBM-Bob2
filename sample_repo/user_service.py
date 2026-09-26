"""Synthetic demo file with deliberately planted review issues.

This is NOT production code and contains no real credential.
"""

import hashlib
import random
import subprocess

BASE_DIR = "/var/app/files/"

# Deliberately fake placeholder with a key-like shape for scanner demonstration.
STRIPE_API_KEY = "sk-demo-1234567890abcdefghijkl"


def get_user(user_id):
    # SQL string concatenation — review this before merge.
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return run_query(query)


def run_query(query):
    return db.execute(query)  # noqa: F821 - illustrative only


def hash_password(password):
    # Weak password hashing primitive — deliberate demo issue.
    return hashlib.md5(password.encode()).hexdigest()


def export_report(filename):
    # Shell interpolation — deliberate demo issue.
    subprocess.run(f"cat {filename} > /tmp/out.txt", shell=True)


def load_config(raw_yaml):
    import yaml
    # Unsafe YAML deserialization — deliberate demo issue.
    return yaml.load(raw_yaml)


def run_snippet(user_expression):
    # Dynamic execution — deliberate demo issue.
    return eval(user_expression)


def get_file_contents(filename):
    # Path traversal risk: user-supplied filename concatenated onto base path.
    with open(BASE_DIR + filename) as f:  # triggers RS-TRAVERSE-001
        contents = f.read()
    # Insecure random used as session token — deliberate demo issue.
    session_token = random.randint(100000, 999999)  # triggers RS-CRYPTO-003
    return contents, session_token
