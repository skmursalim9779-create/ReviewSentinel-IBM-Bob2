# ReviewSentinel report

- Files scanned: **1**
- Scan time: **0.003s**
- Findings: **6**
- Review health score: **42/100**

**By severity:** critical: 1, high: 3, medium: 2
**By category:** injection: 2, crypto: 1, deserialization: 1, execution: 1, secrets: 1

## [CRITICAL] RS-EVAL-001 — user_service.py:41
**Category:** `execution`
Use of eval() on dynamic input.

```text
return eval(user_expression)
```

## [HIGH] RS-SECRET-001 — user_service.py:10
**Category:** `secrets`
Possible hardcoded credential assigned to 'STRIPE_API_KEY'.

```text
STRIPE_API_KEY = "[REDACTED]"
```

## [HIGH] RS-INJECT-001 — user_service.py:15
**Category:** `injection`
SQL query appears to be assembled with string formatting/concatenation instead of parameterized bindings.

```text
query = "SELECT * FROM users WHERE id = " + str(user_id)
```

## [HIGH] RS-INJECT-002 — user_service.py:30
**Category:** `injection`
Shell command uses os.system or shell=True; verify inputs cannot control the command.

```text
subprocess.run(f"cat {filename} > /tmp/out.txt", shell=True)
```

## [MEDIUM] RS-CRYPTO-001 — user_service.py:25
**Category:** `crypto`
MD5 is unsuitable for security-sensitive hashing; use a modern hash or password KDF as appropriate.

```text
return hashlib.md5(password.encode()).hexdigest()
```

## [MEDIUM] RS-EVAL-004 — user_service.py:36
**Category:** `deserialization`
yaml.load() without SafeLoader can instantiate arbitrary Python objects from untrusted YAML.

```text
return yaml.load(raw_yaml)
```
