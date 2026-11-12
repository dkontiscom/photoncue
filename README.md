# photoncue

**A free, open-source media server for LED-volume virtual production.**
Frame-accurate, genlocked, multi-node video playback onto an LED wall —
controlled from a browser or an iPad. A vendor-neutral alternative to
Pixera and disguise for the *video-playback* majority of LED-volume work.

> **Not** a live 3D render engine (it is not trying to be Unreal/Aximmetry).
> It does one thing: put the right frame on the wall, on every node, on the
> same frame, with correct colour — reliably enough to trust on a paid shoot.

Licensed **MIT**. GStreamer-based. Built in the open.

---

## Why this exists

On an LED volume, a huge share of the actual shooting day is not live 3D
render — it is **playback**: plates, loops, content, reference, all placed on
the wall and run back in sync. The tools that do this well (Pixera, disguise)
are proprietary, expensive, and locked to their own hardware ecosystems.

There is no credible open-source option for the frame-accurate, genlocked,
multi-output playback that this work needs. photoncue is an attempt to build
one — on commodity Linux nodes and Blackmagic DeckLink output, with the sync
and colour discipline that a professional wall actually demands.

The goal is not a tech demo. The goal is something a studio will put on the
wall on a paid day and trust.

---

## What it does (target capability)

- **Multi-node synchronized playback**, frame-accurate across every node
  driving the wall.
- **Unlimited, user-defined canvas** — the wall grows by *output count*
  (sub-devices per card × cards per host × nodes), with no hardcoded
  resolution, output-count, or node-count ceiling.
- **Live compositing** — multiple sources freely placed, scaled, cropped on a
  global canvas.
- **Live colour** — ASC CDL (slope/offset/power/saturation) plus
  temp/tint/exposure/contrast, per source, from the operator UI.
- **10-bit end-to-end**, carried through the full GPU colour path to the SDI
  output.
- **Fail-obvious, not fail-silent** — a dropped frame or a dead node is
  *detected and surfaced to the operator*, never hidden.
- **In-house transcode-normalize-verify** — every source is normalized to one
  house codec and frame rate (VFR→CFR, colour primaries/transfer/matrix,
  range, pixel format, canvas fit) and verified, so the wall doesn't shift
  because of a bad export.
- **Browser / iPad control** — config and operator UIs over the network.

See [`docs/goals.md`](docs/goals.md) for the exact, testable success bars.

---

## How it works (the short version)

```
source(s) → decode → glupload → CDL colour → [warp] → compositor → appsink → [Rust/C] → DeckLink SDK → SDI out
```

Each node renders its slice of a shared global canvas and outputs it over
SDI. Synchronization is two independent, deliberately-separated concerns:

- **Content start — PTP (software):** every node is told to begin playback at
  the same PTP time *T*.
- **Output cadence & phase — genlock (hardware):** every node's DeckLink card
  locks its SDI output to a shared genlock reference, so the frame lands on
  the same physical frame everywhere.

Output goes through the **DeckLink SDK directly**, not GStreamer's
`decklinkvideosink` — because the SDK exposes the genlock/reference control and
frame-level scheduling that a wall needs and the GStreamer element does not.

The full design — sync tiers, node architecture, the DeckLink output layer,
the offline media pipeline, colour, and the open bench questions — is in
[`docs/architecture.md`](docs/architecture.md).

---

## Status — honest

**This repository currently holds the complete engineering specification and
the build plan. Product code is being written against it, compartment by
compartment.** This is a spec-first, hardware-in-the-loop project, not a
dump of a finished tool.

What that means for you right now:

- If you want to **understand the design**, everything is here and current
  ([`docs/`](docs/)).
- If you want to **run it**, it is not runnable yet — follow the roadmap.
- If you want to **contribute**, the current build compartment and its
  acceptance gate are defined (see below); the highest-risk piece is first.

The roadmap is public and specific precisely so this claim is checkable rather
than aspirational.

---

## Roadmap

Built as a ladder of small, individually-testable versions, each with its own
pass/fail gate. Full ladder: [`docs/roadmap.md`](docs/roadmap.md).

| Version | What it proves |
|---|---|
| **v0.001** | `decklink-out` standalone: a synthetic 10-bit frame → scheduled, genlocked SDI out, reference-lock confirmed. The output spine. **← current** |
| **v0.002** | GStreamer in: one real clip → SDI, genlocked; drop-detection surfaced to the operator. |
| **v0.003–4** | Canvas compositing: reposition/crop one, then several sources live. |
| **v0.005** | Live CDL colour; 10-bit proven end-to-end through the GPU path. |
| **v0.006** | Output hardening: continuous lock check, clock-slaving comparison. |
| **v0.007** | Multi-output from one card (synchronized playback group). |
| **v0.008** | Multi-node: two hosts, external PTP, scheduled start, seam frame-offset measured = 0. |
| later | Controller + web UI; then operations (transcode, distribution, node ISO, fail-state). |

Every version has a **two-stage done-line**: *software* (builds, compiles
against the real SDK headers, introspection, review — checkable anywhere) and
*hardware* (lock / timing / 10-bit on a real DeckLink + genlock + wall — only
the bench proves these). A clean software stage never implies the hardware
stage passes. See [`docs/evaluation.md`](docs/evaluation.md).

---

## How it's being built

This is a solo-led project using a disciplined, AI-assisted,
hardware-in-the-loop process. That discipline is encoded in the repo, not just
described:

- **One compartment at a time.** Work is scoped to the current version's
  module; scope containment is machine-enforced so the build can't sprawl
  ahead of what's been tested.
- **Pinned, reproducible stack.** Toolchain and dependency versions are locked
  ([`docs/pins.md`](docs/pins.md)); the whole stack is version-sensitive.
- **Two-tier verification.** Software checks run continuously; a second AI
  reviewer passes over each version's diff; the human bench proves the
  hardware-truth gates that no software check can.

The automation lives in [`.claude/`](.claude/) and
[`CLAUDE.md`](CLAUDE.md). You don't need it to read, use, or contribute to
photoncue — it's how the maintainer keeps a hard, hardware-bound build honest
and small.

---

## Licensing

MIT (see [`LICENSE`](LICENSE)). photoncue sits cleanly on top of LGPL
dependencies (GStreamer, FFmpeg) and the permissively-licensed DeckLink SDK.
Two conditions keep a redistribution clean — build FFmpeg LGPL-only, link the
LGPL libraries dynamically. The Blackmagic SDK and Desktop Video driver are
**not** redistributed here; you obtain them from Blackmagic. Full detail and
the rationale: [`LICENSING.md`](LICENSING.md).

---

## Contributing

The design is settled enough to build against and open enough that the bench
questions are marked as bench questions. If you run an LED volume and can offer
hardware-in-the-loop testing — a wall, DeckLink output, genlock — that is the
single most valuable contribution, because the hardware-truth gates cannot be
proven any other way.

*(Contribution guide and the current open compartment: see
[`docs/roadmap.md`](docs/roadmap.md) and [`CLAUDE.md`](CLAUDE.md).)*
