#!/usr/bin/env python3
"""
photoncue PreToolUse guard for Bash. Blocks hard-never shell actions.
Exit 2 = block (stderr is fed back to Claude as the reason). Exit 0 = allow.
Fail-safe posture: on a real match it blocks; on parse failure it ALLOWS
(so it never wedges the session) — which is why it must be TESTED, and why
scope/secret enforcement also lives in guard-edit.py.
Requires: python3.
"""
import json, re, sys

def block(reason):
    print(f"[guard-bash] BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = ((data.get("tool_input") or {}).get("command") or "")

# recursive+force rm
if re.search(r'\brm\b', cmd) and re.search(r'-\w*r', cmd) and re.search(r'-\w*f', cmd):
    block("recursive+force rm is a hard-blocked destructive op — do it yourself")

# force push
if re.search(r'\bgit\s+push\b', cmd) and (re.search(r'--force\b|--force-with-lease\b|(^|\s)-f(\s|$)', cmd) or re.search(r'\s\+\S', cmd)):
    block("force-push is hard-blocked")

# push to main/master (explicit)
if re.search(r'\bgit\s+push\b', cmd) and re.search(r'\b(main|master)\b', cmd):
    block("push to main/master is hard-blocked — you cut releases")

# writing to secret/credential files
if re.search(r'(>>?|\btee\b)\s+[^|\n]*(\.env(\b|\.)|\.pem\b|\.key\b|id_rsa|/secrets?/)', cmd):
    block("writing to a secret/credential file is hard-blocked")

# editing pinned-version files via shell (sed/tee/redirect)
if re.search(r'(>>?|\btee\b|\bsed\b\s+-i)\s+[^|\n]*(docs/pins\.md|rust-toolchain\.toml|\.tool-versions)', cmd):
    block("version-pin files are human-only")

# tampering with the guard/config via shell
if re.search(r'(>>?|\btee\b|\bsed\b\s+-i|\brm\b|\bmv\b|\bchmod\b)\s+[^|\n]*\.claude/(hooks/|settings\.json|compartment)', cmd):
    block("the guard/hook config is human-only")

sys.exit(0)
