# ReviewSentinel report

- Files scanned: **1**
- Scan time: **0.002s**
- Findings: **8**
- Review health score: **27/100**

**By severity:** critical: 1, high: 4, medium: 3
**By category:** crypto: 2, injection: 2, deserialization: 1, execution: 1, path-traversal: 1, secrets: 1

## [CRITICAL] RS-EVAL-001 — user_service.py:44
**Category:** `execution`
Use of eval() on dynamic input.

```text
return eval(user_expression)
```

## [HIGH] RS-SECRET-001 — user_service.py:13
**Category:** `secrets`
Possible hardcoded credential assigned to 'STRIPE_API_KEY'.

```text
STRIPE_API_KEY = "[REDACTED]"
```

## [HIGH] RS-INJECT-001 — user_service.py:18
**Category:** `injection`
SQL query appears to be assembled with string formatting/concatenation instead of parameterized bindings.

```text
query = "SELECT * FROM users WHERE id = " + str(user_id)
```

## [HIGH] RS-INJECT-002 — user_service.py:33
**Category:** `injection`
Shell command uses os.system or shell=True; verify inputs cannot control the command.

```text
subprocess.run(f"cat {filename} > /tmp/out.txt", shell=True)
```

## [HIGH] RS-TRAVERSE-001 — user_service.py:49
**Category:** `path-traversal`
Path traversal risk: open() with dynamic path — validate and sanitize the path argument.

```text
with open(BASE_DIR + filename) as f:  # triggers RS-TRAVERSE-001
```

## [MEDIUM] RS-CRYPTO-001 — user_service.py:28
**Category:** `crypto`
MD5 is unsuitable for security-sensitive hashing; use a modern hash or password KDF as appropriate.

```text
return hashlib.md5(password.encode()).hexdigest()
```

## [MEDIUM] RS-EVAL-004 — user_service.py:39
**Category:** `deserialization`
yaml.load() without SafeLoader can instantiate arbitrary Python objects from untrusted YAML.

```text
return yaml.load(raw_yaml)
```

## [MEDIUM] RS-CRYPTO-003 — user_service.py:52
**Category:** `crypto`
Use of insecure random module — use secrets or os.urandom for cryptographic purposes.

```text
session_token = random.randint(100000, 999999)  # triggers RS-CRYPTO-003
```
