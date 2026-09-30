# spec — v0.001 · decklink-out (standalone)

**Compartment:** `modules/decklink-out/` (the only editable code dir this version).
**Language:** C/C++ only. **No GStreamer, no GES, no Rust, no PTP, no colour.**

## Purpose (the single thing this proves)

The output spine: a frame handed to the DeckLink SDK comes out SDI, scheduled,
locked to an external genlock reference. Nothing about content correctness,
compositing, colour, or cross-node sync.

## Scope

- Enumerate the DeckLink device on Linux and get `IDeckLinkOutput`.
- **Select a single-output profile** via `IDeckLinkProfileManager` (the card
  needs a profile set; use a one-sub-device profile). Multi-output profiles
  (`bmdProfileFourSubDevicesHalfDuplex` etc.) and the synchronized-playback-group
  arrive at **v0.007**, not here — v0.001 drives exactly one output.
- Configure the card to genlock to its reference input (ref-in) via
  `IDeckLinkConfiguration`.
- Generate a **synthetic** 10-bit frame in software (e.g. a moving bar or a
  frame-counter burn-in — a fixed test pattern is enough).
- Enable video output in a target mode whose rate **equals the genlock rate**.
- Schedule frames and start scheduled playback.
- Read and report reference-lock status, continuously.

Out of scope: reading any file, any real codec, GStreamer, multiple frames'
worth of real content, **multiple outputs / sub-device profiles (that's v0.007)**,
more than one card, more than one machine.

## Verified DeckLink API surface (checked against the March 2026 SDK manual)

These were confirmed against the actual manual — signatures below are the real
ones, including two corrections to the architecture doc. Still, treat runtime
behaviour (does it *lock*) as unproven until the bench.

- `CreateDeckLinkIteratorInstance()` — Linux entry point to enumerate devices.
- `IDeckLinkOutput::EnableVideoOutput(...)` — target mode; rate must match genlock.
- `HRESULT ScheduleVideoFrame(IDeckLinkVideoFrame *theFrame, BMDTimeValue displayTime, BMDTimeValue displayDuration, BMDTimeScale timeScale)`
  — 3rd param is **`displayDuration`** (architecture doc wrote `duration`).
- `HRESULT StartScheduledPlayback(BMDTimeValue playbackStartTime, BMDTimeScale timeScale, double playbackSpeed)`
  — note the 3rd arg **`playbackSpeed`** (1.0 = normal); architecture doc elided it.
- `HRESULT GetReferenceStatus(BMDReferenceStatus *referenceStatus)` → one of
  `bmdReferenceUnlocked` / `bmdReferenceNotSupportedByHardware` / `bmdReferenceLocked`.
- `bmdDeckLinkStatusReferenceSignalLocked` — a **separate** lock check via
  `IDeckLinkStatus::GetFlag`. Two independent ways to confirm lock; use both.
- `HRESULT GetHardwareReferenceClock(BMDTimeScale desiredTimeScale, BMDTimeValue *hardwareTime, BMDTimeValue *timeInFrame, BMDTimeValue *ticksPerFrame)`
  — the genlocked hardware clock (needed later for rate-drift slaving; not
  required to *lock* in v0.001, but wire the read so it's ready).

If the SDK headers are provided, the skeleton should **compile against the real
headers** in this environment as part of stage-1 evaluation.

## Two-stage done-line

**Stage 1 — software (now, no card):**
- `modules/decklink-out/` builds clean with the pinned toolchain.
- Compiles against the real DeckLink SDK headers (once provided).
- The synthetic-frame generator produces a valid 10-bit `IDeckLinkVideoFrame`
  (pixel format is a genuine 10-bit format, verified by construction, not by eye).
- `/codex:adversarial-review` pointed at this spec + `goals.md` returns clean
  (focus: SDK contract adherence, enum/type correctness, error-path handling,
  resource lifetime).

**Stage 2 — hardware (when card + genlock generator + Debian node exist):**
- Device enumerates; output enables in the target mode.
- With a genlock reference connected: **both** `GetReferenceStatus` reads
  `bmdReferenceLocked` **and** the `ReferenceSignalLocked` status flag reads
  locked, and stay locked through sustained scheduled playback.
- SDI output is a stable 10-bit signal at the genlock rate (verified on a
  scope/monitor/processor that reports bit depth and lock).

## Acceptance gate

**Hard gates (binary, zero-tolerance):**
- G1: reference lock reads locked on both independent checks (stage 2).
- G2: output rate == configured genlock rate exactly (rational), no rate mismatch.
- G3: output is genuinely 10-bit end of signal chain (stage 2).
- G4: no scheduled-frame errors reported over a sustained run (use the
  scheduled-playback completion result; a late/dropped frame fails the gate).

**Graded metrics:** none yet at v0.001. Tolerances are set at the version that
first introduces the thing being graded (see `evaluation.md`).

## Toolchain inputs still needed (do not assume — see `docs/pins.md`)

C/C++ build system (CMake vs Meson), C++ standard, DeckLink SDK version, and the
repo layout under `modules/`. These are human-set in `docs/pins.md`.
