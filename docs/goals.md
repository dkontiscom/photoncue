# goals — photoncue technical success criteria

These are the testable bars the finished system must hit. They are separate from
architecture (the HOW) and from the per-version done-lines (`roadmap.md`). A
version is only "done" when its slice of these goals passes (`evaluation.md`).

1. **0-frame sync — hard, zero tolerance.** Every node on the identical timeline
   frame index at every instant; genlock holds output phase. How a violation is
   measured is a testing choice, not part of the goal.

2. **Unlimited canvas, user-defined topology.** Total wall grows by **output
   count** — sub-devices per card × cards per host × nodes — not just node count;
   no built-in cap. Each output's region is bounded only by its chosen SDI mode
   (a DeckLink 8K Pro gives up to 4 independent outputs at ≤ DCI 4K60 each). No
   hardcoded resolution, output-count, or node-count ceiling.

3. **Zero frame drops within hardware capacity.** Usable simultaneous-source
   count = whatever the node's GPU/CPU/RAM/storage sustains. A dropped frame is
   **never silent** — it is detected and **surfaced to the operator**.

4. **Frame-rate set, genlock-matched, exact rational timing:**
   23.976 / 24 / 25 / 29.97 / 30 / 48 / 50 / 59.94 / 60. NTSC-derived rates kept.
   No HFR above 60p (would need multilink SDI, uncommon on LED processors).

5. **Fail-obvious, not fail-safe.** A dead node holds its last good frame (black
   acceptable if hold is materially harder). Node-down is surfaced to the
   operator. Node failure is catastrophic and the take is redone — rescuing the
   take is out of scope.

6. **10-bit end-to-end.** Carried through the full GL path (glupload → CDL →
   compositor → appsink → DeckLink). Proven in two checkpoints: **out of the SDK
   at v0.001**, **end-to-end at v0.005**.

7. **Non-goal (explicit).** No committed live-edit (drag-to-position / CDL)
   latency. Best-effort, "responsive on LAN" is the whole bar. Do not add a
   latency test.

## Hardware-selection checks (gate the goals; not code, not architecture risk)

- The chosen sync generator + LED processor must accept the full frame-rate set
  (goal 4). Confirmed at card/sync-gen selection.
- The per-node SDI output mode sets the real per-node pixel ceiling (goal 2).
  A single 12G-SDI link tops out around 2160p60 — **confirm against the exact
  DeckLink mode table when cards are chosen** (figure is unverified until then).
