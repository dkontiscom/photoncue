# evaluation — how a version is verified before it is called done

## Structure (applies to every version)

Two tiers, reused from the "Technical evaluation criteria" work:

- **Hard gates** — binary, zero-tolerance. Any fail = version not done.
- **Graded metrics** — tolerance-based. The tolerance number is set **at the
  version that first introduces the thing being graded**, next to the code that
  must hit it — not all up front.

Each version's gates live in its own spec (`specs/<module>.md`). The version's
done-line *is* its gate.

## The two verification tiers (what can check what)

Because the hardware truth is unreachable without a card, every check is one of:

- **Software tier (no card):** builds/compiles, compiles against the real SDK
  headers, `gst-inspect-1.0` / GES introspection (API exists, spelled right,
  property present), unit tests, and **Codex review** of the diff. This tier can
  run now, in CI, and in this environment.
- **Hardware tier (needs card + genlock + node):** lock, timing, seam frame
  offset, 10-bit on the wall, drop behaviour under load, fail-state. **Only the
  human bench proves these.** No AI — Codex or otherwise — can verify them; they
  have no card either.

A clean software tier never implies the hardware tier passes.

## Per-version gate + regression

- Each version carries its own acceptance gate (its done-line).
- Every later version **re-runs all prior software checks as regression** (cheap,
  automated).
- Prior **hardware checks re-run only at bench sessions** (when the card is set
  up), not every commit.

## Codex as the second AI — manual per version (chosen mode)

Verification uses the OpenAI **codex-plugin-cc** plugin, run **manually at each
version's end** (not as an always-on gate). Its docs warn the automatic review
gate can spin a long Claude↔Codex loop and drain usage; promote to a hard Stop-
hook gate later only if wanted.

Per version, run:

- `/codex:adversarial-review` pointed at the version's `spec` + `goals.md` —
  steerable, so aim it at the version's real risk (v0.001: SDK contract
  adherence, enum/type correctness, error paths, resource lifetime; later
  versions: race conditions, rate/clock handling, drop accounting).
- `/codex:review` for a straight read-only pass on the diff.

Codex clean = software tier's design/correctness check passed. It is **not** the
hardware gate.

## The loop (per compartment)

1. Claude Code builds only the current compartment (scope hook-enforced).
2. Software tier runs: build, headers-compile, introspection, unit tests.
3. `/codex:adversarial-review` + `/codex:review` on the diff; fix findings; repeat
   2–3 until clean.
4. Human bench runs the hardware-tier gates when the card is available.
5. Only when both tiers pass is the version done; advance the compartment
   (`.claude/compartment`, human-only) and write the next version's spec.

Steps 1–3 are automatable now. Step 4 is the human gate and cannot be skipped or
simulated.
