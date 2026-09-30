# roadmap — photoncue version ladder

One version = one small, testable compartment with its own done-line (= its own
acceptance gate in `evaluation.md`). Claude Code builds **only the current
version**. A full spec exists for the current and next version; later rungs stay
one-liners until bench results reshape them.

Every version has a **two-stage done-line**:
- **stage 1 — software (no card needed):** builds clean, compiles against the
  real SDK headers where relevant, gst-inspect / GES introspection pass, Codex
  adversarial-review clean.
- **stage 2 — hardware (needs the DeckLink card + genlock + node):** the lock /
  timing / 10-bit bench.

"vX done in a week" honestly means **stage 1** in a week; stage 2 waits on hardware.

| Version | Done-line |
|---|---|
| **v0.001** | `decklink-out` standalone (C/C++, no GStreamer): a synthetic frame → scheduled, genlocked SDI out; `ReferenceSignalLocked` reads locked; **10-bit proven out of the SDK** (10-bit test pattern). |
| **v0.002** | GStreamer in: GES preview → `appsink` → `decklink-out`, one real clip out SDI, genlocked. **Drop-detection built and surfaced to operator** here (first version where real frames flow). |
| **v0.003** | Canvas, single source: `compositor`/`glvideomixer` `xpos`/`ypos`/`crop`/`alpha`, reposition one source live. |
| **v0.004** | Canvas, multi-source: composite several sources on one node. |
| **v0.005** | CDL colour: custom `GstGLFilter`, live-settable; **10-bit proven end-to-end** through the GL path (glupload → CDL → compositor → appsink → DeckLink). |
| **v0.006** | Output hardening: continuous lock check, hardware-clock-slave vs PTP-clocked comparison, drop-detection refined. |
| **v0.007** | Multi-output, one card: put the 8K Pro into a multi-sub-device profile (`IDeckLinkProfileManager` → `bmdProfileFourSubDevicesHalfDuplex` etc.), drive 2–4 SDI outputs via the **synchronized-playback-group** (`bmdDeckLinkConfigPlaybackGroup` + `bmdVideoOutputSynchronizeToPlaybackGroup`, `StartScheduledPlayback` on one starts all); confirm frame-identical across the card's outputs. No PTP, no external ref needed *between* the card's own outputs. |
| **v0.008** | Multi-node: 2 nodes, external PTP grandmaster, scheduled start at a shared PTP time T, both genlocked, **seam frame-offset measured = 0** → full multi-host spine proven. |
| later | controller + web UI (config + operator, iPad); then operations: ffmpeg transcode-normalize, rsync+sha256 distribution, Debian node ISO, fail-state behaviour. |

**Three sync tiers, easiest first** (this ladder climbs them in order): (1) same card,
multi-output — synchronized-playback-group, no PTP, no ref between outputs (v0.007);
(2) multi-card, one host — synchronized-playback-group but needs a shared genlock;
(3) multi-host — PTP-start + genlock-phase (v0.008), only needed past one host's cards.

**Design note for v0.002+ (pipeline):** a node driving N outputs crops the canvas into
N slices → N appsinks → N sub-device outputs. This changes "one appsink per node" to
"one appsink per output." v0.001 stays single-output; write the v0.002 spec with the
N-output shape in mind so it isn't a rewrite at v0.007.

Per-card ceiling to confirm at purchase: a DeckLink 8K Pro drives up to **4
independent outputs at ≤ DCI 4K60 each**, *or* one quad-linked 8K output — not both.
Add a card (tier 2) or a node (tier 3) only when output count or GPU exceeds one card.

Detailed specs currently written: **v0.001** (`specs/decklink-out.md`).
Write the v0.002 spec when v0.001 stage 1 is clean.
