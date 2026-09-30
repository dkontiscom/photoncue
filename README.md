# photoncue — Claude Code scaffold

Open-source, GStreamer-based virtual-production media server: frame-accurate,
synchronized video playback across multiple nodes driving an LED wall. This
folder is the **Claude Code control layer** — the guardrails, specs, and
verification setup that keep the build inside small, testable compartments.

Start by reading `CLAUDE.md`, then `docs/roadmap.md` (which version you're on) and
`docs/goals.md` (the pass/fail bars).

## Layout

```
CLAUDE.md                     lean, always-loaded rulebook + read-first map
docs/
  roadmap.md                  version ladder (v0.001 → v0.007), current focus
  goals.md                    locked success criteria
  architecture.md             the HOW (your existing doc — see ARCHITECTURE-PATCH.md)
  specs/decklink-out.md       the CURRENT compartment's spec (v0.001)
  limits.md                   advisory design rules (review/human enforce)
  evaluation.md               how each version is verified before it's "done"
  pins.md                     pinned stack versions — HUMAN-ONLY, fill before building
  ARCHITECTURE-PATCH.md       exact edits to fold into architecture.md
.claude/
  settings.json               permissions (allow/ask) + hook wiring
  compartment                 which module is editable now — HUMAN-ONLY
  hooks/guard-bash.py         PreToolUse block: rm -rf, force/main push, secrets, pins
  hooks/guard-edit.py         PreToolUse block: out-of-compartment edits, pins, config, secrets
```

Put `architecture.md` in `docs/` (apply `ARCHITECTURE-PATCH.md` to your existing
copy first).

---

## Setup (once)

**1. Prerequisites**
- `python3` (the hooks are Python; standard on Debian).
- Node.js **18.18+** (for the Codex plugin).
- Your pinned build toolchain — fill `docs/pins.md` first; **nothing builds until
  it's filled.**

**2. Do NOT run `/init`** — a `CLAUDE.md` already exists; `/init` would overwrite it.

**3. Enable the guard hooks**
The hooks are already wired in `.claude/settings.json`. After cloning:
```
chmod +x .claude/hooks/guard-bash.py .claude/hooks/guard-edit.py
```
Open Claude Code in the repo, then:
```
/hooks
```
to confirm both PreToolUse hooks are registered. **Then test that a block actually
fires** — an untested hook can fail *open* (look enforced, block nothing):
```
# ask Claude to edit a file in a module that is NOT in .claude/compartment
# it should be blocked with a [guard-edit] reason
```
If it isn't blocked, fix the matcher/path before trusting the setup.

**4. Install the Codex review plugin** (openai/codex-plugin-cc)
Requires a ChatGPT subscription (incl. Free) or an OpenAI API key; usage counts
against your Codex limits. In Claude Code:
```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```
If Codex isn't logged in yet:
```
!codex login
```
Repo/docs: https://github.com/openai/codex-plugin-cc

We use Codex **manually per version** (not the auto review-gate). The auto gate
(`/codex:setup --enable-review-gate`) installs a Stop hook that blocks "done"
until Codex is clean — powerful, but its own docs warn it can spin a long
Claude↔Codex loop and drain usage. Leave it off unless you're actively watching.

---

## The build loop (per compartment)

1. Claude Code builds **only** the current compartment (scope is hook-enforced).
2. Software checks: build, compile against real SDK headers, `gst-inspect-1.0` /
   GES introspection, unit tests.
3. Codex review on the diff:
   ```
   /codex:review
   /codex:adversarial-review   # aim it at this version's real risk (see the spec)
   ```
   Fix findings; repeat 2–3 until clean.
4. **Human bench** runs the hardware-tier gates when the DeckLink card is set up.
   No AI can verify lock/timing/10-bit — no card.
5. Both tiers pass → version done. Then (human) update `.claude/compartment` to the
   next module and write the next version's spec. Advance one rung at a time.

---

## Notes / caveats

- **Hooks are tested by sample input, not yet inside your Claude Code.** Confirm
  with `/hooks` + a real blocked action before trusting them (step 3).
- **`docs/pins.md` and `.claude/compartment` are human-only** and hook-protected —
  Claude Code cannot edit them. That's intentional.
- Claude Code memory/hook reference: https://code.claude.com/docs/en/hooks
