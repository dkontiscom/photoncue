# CLAUDE.md — photoncue

Open-source, GStreamer-based virtual-production media server. Frame-accurate,
synchronized video playback across multiple nodes driving an LED wall, operated
from a web UI. A free alternative to Pixera/disguise for the video-playback
majority of LED-volume work. **Not** a live 3D render engine.

This file is the always-loaded guardrail layer. Keep it lean. The detail lives
in `docs/`, pulled in on demand.

---

## Read-first map (open these with @ when a task touches them)

- `@docs/roadmap.md` — the version ladder. **Always know which version you are on.**
- `@docs/goals.md` — locked success criteria (the pass/fail bars).
- `@docs/architecture.md` — how the whole system is built (the HOW).
- `@docs/specs/decklink-out.md` — the **current** compartment's spec (v0.001).
- `@docs/limits.md` — advisory design rules a hook cannot catch (review + human catch these).
- `@docs/evaluation.md` — how each version is verified before it is called done.
- `@docs/pins.md` — pinned stack versions (human-only file).

---

## Current focus — v0.001

Standalone `decklink-out` (C/C++ only, **no GStreamer**): a synthetically
generated frame → scheduled, genlocked SDI out, `ReferenceSignalLocked` reading
locked, 10-bit proven out of the SDK. Full spec: `@docs/specs/decklink-out.md`.
Build only what that spec covers. The next rung is v0.002; do not build ahead.

## Build philosophy (do not deviate)

- **Hardware-in-the-loop, smallest testable unit first.** Every piece is written
  small and tested on a real DeckLink before moving on. No big-bang integration.
- **One compartment at a time.** Work stays inside the current version's module.
  Scope containment is hook-enforced — you physically cannot edit other modules.
- **Highest-risk first:** `decklink-out` (the SDK output layer) is the spine and
  is built and benched before anything else.

## Guardrails — human-readable; enforcement is in `.claude/settings.json` + hooks

Two kinds. The first kind a hook blocks. The second kind a hook cannot see (it's
a design choice, not an action) — Codex review and the human catch those.

**Enforced actions** (see `.claude/settings.json`):
- always (auto): read, build/compile, run tests, gst-inspect / GES introspection,
  lint/format, edit code inside the current compartment dir.
- ask-first: git commit, dependency / package install.
- never (hook-blocked): edit code outside the current compartment; change a pinned
  version (`docs/pins.md`, `rust-toolchain.toml`, `.tool-versions`); push to
  main/master; force-push; `rm -rf`; delete media/source; write secrets
  (`.env`, keys); edit the hooks/guard config itself.

**Advisory design rules — NEVER, but only review/human enforce** (full list in `@docs/limits.md`):
- No audio, anywhere.
- No delivery-codec decode: no H.264/H.265, no DPX, no EXR. Sources are ProRes /
  DNxHR / image sequences (PNG/JPEG/TIFF) only.
- **One default house codec** (ProRes 422 HQ *or* DNxHR HQX, 10-bit 4:2:2 — which
  one is a bench decision). Image sequences are a supported input, **not** the
  default. Transcode-normalize-verify stays in-house; never outsourced to the
  operator's DaVinci.
- Output goes through the DeckLink **SDK directly**, not GStreamer's
  `decklinkvideosink`. Pipeline terminates in `appsink` → Rust/C → SDK. GES/
  GStreamer never talks to the card.
- No GPU swap-barrier / framelock. Output is DeckLink SDI, not GPU DP/HDMI. No
  NVIDIA Quadro Sync, no AMD S400.
- GES runs in **PREVIEW mode only**. Never RENDER.
- `GstPtpClock` is slave-only; an external PTP grandmaster is mandatory and is
  **never** on the controller.
- Genlock frame rate == media frame rate. Enforced by the offline transcode; no
  per-node rate conversion to paper over a mismatch.
- No live mid-take timeline switching.
- Reference GES app to study is **Pitivi** (Python + GES). Not Kdenlive (MLT).

## Deferred / undecided — do NOT build unless told

OpenColorIO (keep the GL colour stage structured so OCIO can slot in later);
HAP codec; in-clip gapless looping / loop-bake helper; HFR above 60p; curved-wall
`glshader` warp; DeckLink-IP / ST 2110 / PTP-only sync (that is v2 — big
additions, not in v0.00x).

---

## Tech stack

| Concern | Tool |
|---|---|
| Media engine | GStreamer |
| Timeline | GStreamer Editing Services (GES), PREVIEW mode |
| Decode | gst-libav (ProRes, DNxHR), multifilesrc (image seq) |
| Colour / warp | custom GstGLFilter (CDL); glshader (warp, undecided) |
| Content-start clock | GstPtpClock (slave-only) + external PTP grandmaster |
| Output | DeckLink SDK (C/C++), SDI + ref-in genlock |
| Transcode | ffmpeg |
| Distribution | rsync + sha256 |
| Node daemon / scheduler | Rust |
| Controller | Docker container, REST + WebSocket |
| Web UI | TBD (chosen later) |
| Node OS | pinned minimal Debian live-build ISO (USB SSD) |

Exact pinned versions live in `@docs/pins.md` (human-only).
