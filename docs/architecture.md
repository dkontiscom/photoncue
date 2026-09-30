# photoncue — Architecture

Open-source virtual production media server. Frame-accurate, synchronized video
playback across multiple nodes driving an LED wall, controlled from a web UI
(iPad-friendly). A free alternative to Pixera / disguise for the video-playback
majority of LED-volume work (not a live 3D render engine).

Fully open source. GStreamer-based.

> Status legend used below: **[decided]** locked, **[deferred]** intentionally
> post-v1, **[undecided]** still being evaluated, **[bench]** works in theory,
> must be confirmed on hardware. External facts are attributed inline.

---

## 1. Scope

### In scope (v1)
- Multi-node synchronized playback to an LED wall, frame-accurate.
- Multiple videos at once, freely placed on a global canvas.
- Timeline (Pixera/DaVinci-style) built on GStreamer Editing Services (GES).
- Live CDL color per playback (slope/offset/power/saturation + temp/tint/
  exposure/contrast).
- Live drag-to-position / scale / crop of sources on the canvas.
- ffmpeg pre-transcode of all source media to one house codec + frame rate.
- rsync + checksum file distribution to each node.
- Web-based controller (config UI + operator UI).

### Out of scope
- **[decided]** Live 3D render engine (Unreal-style) — not this project.
- **[decided]** No audio, anywhere.
- **[decided]** Delivery codecs: no H.264 / H.265 decode. No DPX / EXR.
- **[deferred]** HAP (GPU-texture codec) — no mainline GStreamer decoder; future.
- **[deferred]** OpenColorIO full color management — future; architecture must
  not preclude it (see §8).
- **[deferred]** In-clip gapless looping — operator bakes loops into a longer
  file offline; a future one-click ffmpeg helper will automate that.
- **[undecided]** Curved-wall geometric warp via glshader — wanted, not yet
  committed; may be v1 or future.

---

## 2. The synchronization model (the spine)

Three independent concerns. Two are used, one is explicitly not.

1. **Content start — PTP (software).** All nodes begin playback at the same
   moment. Each node's pipeline is told: *start at PTP time T*. Implemented with
   `GstPtpClock`.
2. **Output cadence & phase — DeckLink ref-in genlock (hardware).** Each node's
   DeckLink card locks its SDI output to a shared genlock reference, so every
   node emits its frame on the same genlock frame.
3. **Framelock / GPU swap-barrier — NOT USED.** Output is via the DeckLink SDI
   out, not the GPU DisplayPort/HDMI, so GPU-level scan-out sync is irrelevant.
   There is no NVIDIA Quadro Sync / AMD S400 in this design. Do not reintroduce
   this.

**Role split, stated precisely:**
- PTP makes the nodes *start playing the same frame at the same time*.
- Genlock (ref-in) makes the nodes *output that frame on the same physical
  frame*.

### Sync tiers — PTP + genlock is only the *cross-host* case

There are three tiers of output synchronization; climb them easiest-first, and
only reach for the next when you outgrow the current one:

1. **Same card, multiple outputs** — a multi-output DeckLink (e.g. the 8K Pro,
   up to 4 independent SDI outs) runs its outputs as a **synchronized-playback
   group** (SDK: `bmdDeckLinkConfigPlaybackGroup` +
   `bmdVideoOutputSynchronizeToPlaybackGroup`; `StartScheduledPlayback` on any
   one starts all). On the 8K Pro the sub-devices sync to each other **without a
   common reference input** (shared card clock). No PTP, no external genlock
   needed *between* one card's outputs. See §5.
2. **Multiple cards, one host** — same synchronized-playback-group mechanism, but
   the cards now need a **shared genlock reference** to phase-align.
3. **Multiple hosts** — the PTP-start + genlock-phase model below. This is the
   *only* tier that needs PTP, and it is reached only when output count or GPU
   exceeds a single host's cards.

The rest of this section describes tier 3 (cross-host), which is the hardest and
the one the sync spine must ultimately prove.

### Hard constraints
- **`GstPtpClock` is slave-only** (per GStreamer docs — it implements an
  IEEE-1588 ordinary clock in slave-only mode). GStreamer cannot be the PTP
  master. Therefore an **external PTP grandmaster is mandatory**, not optional:
  a dedicated GM device, or `ptp4l` (linuxptp) running as master on a node that
  is *not* a player. Preferably a SMPTE ST 2059-2 grandmaster that disciplines
  both the PTP domain and the genlock reference from one source.
- All nodes share **one genlock generator** at the **same frame rate**.
- The genlock frame rate **equals the media frame rate** (genlock 24 → all
  media 24). Transcode enforces this (§7).

### Rate-drift handling — [bench]
The GES render rate and the DeckLink output rate must not fight (that shows up
as an occasional dropped/repeated frame). Preferred solution: slave the
GStreamer pipeline clock to the **DeckLink hardware reference clock**
(`IDeckLinkOutput::GetHardwareReferenceClock`, per DeckLink SDK Manual, March
2026), which is itself genlocked. Then genlock is effectively the master rate
everywhere and PTP's only job shrinks to agreeing the starting frame index
across nodes. Prototype this against the plain "PTP-clocked pipeline" approach.

### Transitions — a non-issue, by design
A show is fully programmed before the take. On "action", the operator hits play
and nothing changes on the timeline during the take. There is **no live
mid-take switching**, so there is no cross-node "switch on the same frame"
problem to solve. Only two sync events matter: **the scheduled start** and
**staying locked** while the timeline plays through. Both are handled by PTP +
genlock above. Live UI edits (position, color) happen in setup/rehearsal, where
a one-frame settling delay is irrelevant.

---

## 3. Node architecture

One node per machine, driving **one or more** sections of the wall — one SDI
slice per output, and a multi-output card (e.g. the 8K Pro) gives a single node
up to 4 slices. Add a second card (tier 2) or a second node (tier 3) only when
output count or GPU exceeds one card.

- **OS:** minimal, pinned Debian live-build ISO, booted from a USB SSD,
  coexisting with the machine's internal OS. Pinned because GStreamer is
  version-sensitive — the whole stack version is locked in the image.
- **Renderer:** one GStreamer/GES pipeline per node, rendering this node's
  region of the **global canvas**. The node knows only its own crop/region of
  the canvas (pushed as config by the controller); it does not need to know
  about the other nodes.
- **Output:** the pipeline terminates in an `appsink`. A Rust/C output layer
  takes each rendered frame and hands it to the **DeckLink SDK** for scheduled,
  genlocked SDI output. GES/GStreamer never talks to the DeckLink directly.
- **Daemon:** a Rust daemon owns pipeline lifecycle, the control link to the
  controller, PTP slaving, cue scheduling, live parameter updates, the
  appsink→DeckLink handoff, and health reporting.

### GES usage
- GES runs in **PREVIEW mode** = real-time playback to a sink. (GES has two
  pipeline modes: PREVIEW = live playback, RENDER = encode to file. RENDER is
  not used.) "Preview" and "live playout" are the same path for us.
- The reference GES-based application to study is **Pitivi** (Python + GES).
  (Kdenlive is MLT-based, not GES — its DeckLink experience does not transfer.)
- Live parameter changes during playback go through GES's commit model:
  mutate the timeline, then `ges_timeline_commit()` to push into the running
  pipeline. **[bench]** Confirm commits apply without a visible hitch for live
  tweaks (position, CDL). Expected fine for parameters; watch structural edits.
- **[bench]** Confirm an external PTP clock + scheduled base-time can be imposed
  on the `GESPipeline` (it is a `GstPipeline` underneath, so this should behave
  like any pipeline).

---

## 4. Per-node pipeline (conceptual)

```
source(s) ──► decode ──► glupload ──► CDL color ──► [warp] ──► compositor ──► appsink ──► [Rust/C] ──► DeckLink SDK (ScheduleVideoFrame)
```

- **source(s):** `filesrc` / `urisourcebin` for clips; `multifilesrc` for image
  sequences (PNG/JPEG/TIFF).
- **decode:** `gst-libav` (`avdec_prores`, `avdec_dnxhd`, etc.). Image sequences
  decode natively.
- **glupload:** move frames to GL for GPU compositing/color.
- **CDL color:** custom `GstGLFilter` applying ASC CDL + temp/tint/exposure/
  contrast; parameters live-settable (§8).
- **warp:** optional custom `glshader` for curved-wall geometry — **[undecided]**.
- **compositor:** `glvideomixer` / `compositor`. Multiple sources combined with
  per-pad `xpos`, `ypos`, `width`, `height`, `alpha`, `zorder`, `crop`, all
  runtime-settable — this is what powers live drag-to-position.
- **appsink → DeckLink:** see §5.

Each node composites the full canvas but outputs only its own SDI slice(s); the
node's crop/region config decides which part. A node driving **N outputs** (a
multi-output card) crops the canvas into N slices → **N appsinks → N DeckLink
sub-device outputs**, all in one synchronized-playback group (§2 tier 1, §5). So
the shape is "one appsink per **output**," not per node.

---

## 5. DeckLink SDK output layer (the critical C/C++ piece)

Output is driven **directly through the DeckLink SDK**, not through GStreamer's
`decklinkvideosink`. (The GStreamer element does not expose genlock/reference
control; the SDK does, and gives frame-level scheduling.) The SDK is
cross-platform including Linux (DeckLink SDK Manual, March 2026).

Flow:
1. Enumerate device (`CreateDeckLinkIteratorInstance` on Linux), query
   `IDeckLinkOutput`.
2. Configure genlock/reference at the Desktop Video / SDK config level
   (`IDeckLinkConfiguration`); the card locks its output to ref-in.
3. `EnableVideoOutput` in the target mode (frame rate must match genlock).
   10-bit is handled in hardware, removing the Linux GL 10-bit risk.
4. Scheduled playback: `ScheduleVideoFrame(frame, displayTime, displayDuration,
   timeScale)` for each rendered frame; `StartScheduledPlayback(playbackStartTime,
   timeScale, playbackSpeed)` (playbackSpeed = 1.0 for normal) at the PTP-derived
   start. Signatures verified against the March 2026 SDK manual.
5. Verify lock: `GetReferenceStatus` / status flag
   `bmdDeckLinkStatusReferenceSignalLocked` before/while playing.
6. Optional: expose `GetHardwareReferenceClock` as a `GstClock` to clock the
   pipeline (§2 rate-drift).

Multi-output & the Synchronized Playback group (verified, March 2026 manual): a
multi-output card exposes its outputs as **sub-devices** selected via
`IDeckLinkProfileManager` profiles (`bmdProfileFourSubDevicesHalfDuplex` / two- /
one-sub-device — an 8K Pro is either 4 independent outputs ≤ DCI 4K60 **or** one
quad-linked 8K output, not both). Outputs on one host run as a **synchronized
playback group** (`bmdDeckLinkConfigPlaybackGroup` +
`bmdVideoOutputSynchronizeToPlaybackGroup`; `StartScheduledPlayback` on any one
starts all). This is a **single-host** feature — it covers multi-output-single-card
*and* multi-card-single-host, but does **not** synchronize separate machines
(that is PTP + genlock, §2 tier 3). The 8K Pro is the special case whose
sub-devices sync **without a common reference input**; multiple *cards* still
need a shared genlock.

This layer — appsink → SDK scheduling + genlock/ref verification + optional
hardware-clock slaving — is the trickiest single unit and the first to build
and bench.

---

## 6. Controller

- **Deployment:** Docker container. Disposable — runs on any laptop, even over
  wifi. The PTP master is **not** on the controller.
- **Transport:** REST + WebSocket to each node daemon.
- **Config UI:** node/screen topology, global canvas layout, per-node crop/
  region assignment, media management, file distribution.
- **Operator UI (iPad-friendly):** playback + cueing, A-B, the timeline,
  drag-to-position/scale/crop on a canvas representing the whole wall, and live
  CDL controls per source.
- Web UI framework: **[undecided]** — pick during M4.

---

## 7. Media pipeline (offline) & distribution

- **Transcode to one default house codec.** ffmpeg converts **every** source to a
  single default intra codec — **ProRes 422 HQ *or* DNxHR HQX** (both 10-bit
  4:2:2). Which of the two is the default is a **bench decision** (measure decode
  cost/determinism on real node hardware). Image sequences (PNG/JPEG/TIFF via
  `multifilesrc`) remain a **supported input, not the default** — they are the
  most *robust* (each frame independent, trivial exact seek) but the *heaviest*
  on storage and I/O, so they are the escape hatch, not the norm. One tested
  playback format eliminates per-node decode surprises.
- **The real work is the *normalize* step, not the encode.** Swapping any-codec →
  ProRes is trivial; the engineering is decoding arbitrary operator input and
  normalizing it: VFR→CFR at the house rate, colour primaries/transfer/matrix,
  full-vs-limited range, pixel format, canvas fit. Get colour/range wrong and the
  wall shifts. **Transcode-normalize-verify stays in-house** — the operator's
  DaVinci may be an optional front-end for gnarly sources, but photoncue must
  re-normalize and verify its own output; never push the correctness guarantee
  onto the operator's export.
- **Distribution:** rsync to each node with **sha256 checksums** to guarantee no
  node is silently short a frame; verify integrity before a node is marked ready.

---

## 8. Color

- **v1 — [decided]:** ASC **CDL** (slope/offset/power/saturation) + temp/tint/
  exposure/contrast, implemented as a custom `GstGLFilter`, live-controllable
  from the operator UI. High-value DoP/DiT feature.
- **Future — [deferred]:** **OpenColorIO** v2 GPU path (build a `GpuShaderDesc`,
  emit GLSL + LUT textures, wrap in a custom `GstGLFilter`) for full ACES/
  config-driven management. Not in v1, not in the grant deliverables, but the GL
  color stage must be structured so OCIO can slot in later without a rewrite.

---

## 9. Cue / scheduling model

- **Arm / preroll:** files are distributed; each node's pipeline is prerolled
  and reports ready.
- **Start:** operator hits play → the scheduler picks a future PTP time T → every
  node calls `StartScheduledPlayback` timed to T. Because outputs are genlocked,
  T lands on the same physical frame on all nodes. Start latency after the click
  (a couple of seconds) is irrelevant — the point is that every node is fully
  ready and starts together.
- No live timeline changes during a take (§2).

---

## 10. Tech stack

| Concern | Tool |
|---|---|
| Media engine | GStreamer |
| Timeline | GStreamer Editing Services (GES), PREVIEW mode |
| Decode | gst-libav (ProRes, DNxHR), multifilesrc (image seq) |
| Color / warp | custom GstGLFilter (CDL), glshader (warp, undecided) |
| Content-start clock | GstPtpClock (slave-only) + external PTP grandmaster |
| Output | DeckLink SDK (C/C++), SDI + ref-in genlock |
| Transcode | ffmpeg |
| Distribution | rsync + sha256 |
| Node daemon / scheduler | Rust |
| Controller | Docker container, REST + WebSocket |
| Web UI | TBD |
| Node OS | pinned minimal Debian live-build ISO (USB SSD) |

---

## 11. Module breakdown (build units)

1. **decklink-out** (C/C++): SDK output, scheduled playback, genlock/ref status,
   optional hardware-clock export. *Highest-risk, build first.*
2. **node-pipeline**: GES timeline + compositor (position/crop/alpha) + CDL
   filter + appsink; parameter API for live edits.
3. **ptp-sync**: grandmaster setup + node slaving (`wait_for_sync`) + scheduled
   start at PTP time.
4. **node-daemon** (Rust): lifecycle, control link, cue scheduling,
   appsink→decklink-out handoff, health.
5. **controller** (Docker): REST/WebSocket, topology & canvas state, file mgmt.
6. **operator-ui / config-ui** (web): the two UIs.
7. **media-transcode**: ffmpeg house-format normalization.
8. **distribution**: rsync + checksum + verify.
9. **node-image**: minimal Debian live-build ISO, versions pinned.
10. **glshader-warp** (optional): curved-wall geometry.

---

## 12. Build milestones (incremental, hardware-in-the-loop)

Each piece is written small and tested on a real DeckLink immediately before
moving to the next.

- **M0 — v0.01 PoC:** single node, one clip: GES preview → appsink → DeckLink SDK
  out, genlock-locked. No PTP, no color.
- **M1 — node player core:** GES timeline, compositor position/crop/alpha, CDL
  live color, (optional) glshader; appsink→decklink-out.
- **M2 — output hardening:** decklink-out robustness, `ReferenceSignalLocked`
  verification, hardware-clock slaving vs PTP-clocked comparison.
- **M3 — multi-node PTP start:** two nodes, external grandmaster, scheduled start
  at PTP T, genlocked; confirm frame-identical output at the seam.
- **M4 — controller + web UI:** config + operator UIs; drag-to-position, live
  CDL, timeline over the network.
- **M5 — operations:** ffmpeg transcode + rsync distribution + node ISO +
  fail-state behavior (hold-last-frame vs black), monitoring, on-site validation.

---

## 13. Testing

Incremental and hardware-in-the-loop from M0. Three studios available for
testing; ~1 year for the production-trust tail (node-failure behavior, format
edge cases, on-site validation on real walls) that a demo can't cover.

First two bench tests, in order:
1. One DeckLink outputting SDI locked to ref-in on Linux, with
   `bmdDeckLinkStatusReferenceSignalLocked` reading locked.
2. Two nodes, PTP-slaved to one external master, scheduled to start at a shared
   PTP time, both genlocked — measure the frame offset at the seam.

If both hold, the spine is proven.

---

## 14. Open / bench items

- **[bench]** GES `ges_timeline_commit()` smoothness for live param tweaks.
- **[bench]** External PTP base-time on `GESPipeline`.
- **[bench]** appsink→DeckLink feed kept at the genlock rate; hardware-clock
  slaving.
- **[undecided]** Curved-wall warp via glshader (v1 or future).
- **[deferred]** OCIO, HAP, loop-bake helper.

---

## 15. Effort (rough)

~290–450h raw / ~190–290h AI-assisted. The core, demonstrable system fits inside
~3 months full-time. The "studio-trusts-it-on-a-paid-day" hardening is the
operational tail that the testing period across the three studios absorbs. The
two line items most likely to slip: the DeckLink SDK/timing layer and the
operator web UI.