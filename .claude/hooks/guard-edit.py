#!/usr/bin/env python3
"""
photoncue PreToolUse guard for Edit/Write/MultiEdit.
Enforces: scope containment (edits stay in the current compartment), pin-file
protection, guard/config protection, secret-file protection.
Exit 2 = block. Exit 0 = allow. Requires: python3.
TEST before trusting: an untested hook can fail open.
"""
import json, os, re, sys, fnmatch

def block(reason):
    print(f"[guard-edit] BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

ti = data.get("tool_input") or {}
path = ti.get("file_path") or ti.get("path") or ""
if not path:
    sys.exit(0)

proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
rel = os.path.relpath(path, proj) if os.path.isabs(path) else path
rel = rel.replace(os.sep, "/")

# secrets
if re.search(r'(^|/)\.env(\.|$)|\.pem$|\.key$|id_rsa|(^|/)secrets?/', rel):
    block(f"{rel}: writing secrets is hard-blocked")

# guard / config tamper-protection
for pat in [".claude/hooks/", ".claude/settings.json", ".claude/compartment"]:
    if pat in rel:
        block(f"{rel}: the guard/hook config is human-only")

# pinned-version files
for pat in ["docs/pins.md", "rust-toolchain.toml", ".tool-versions"]:
    if rel.endswith(pat):
        block(f"{rel}: version-pin files are human-only")

# scope containment: only for code under modules/ or src/
if re.match(r'(modules|src)/', rel):
    allowed = []
    comp = os.path.join(proj, ".claude", "compartment")
    try:
        with open(comp) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    allowed.append(line)
    except Exception:
        allowed = []
    if allowed and not any(fnmatch.fnmatch(rel, g) for g in allowed):
        block(f"{rel} is outside the current compartment ({', '.join(allowed)}); "
              f"other modules are locked until you advance the compartment")

sys.exit(0)
