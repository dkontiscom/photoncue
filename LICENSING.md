# Licensing

photoncue is released under the **MIT License** (see `LICENSE`). This file
explains how that choice interacts with the dependency stack, and the two
practical conditions a distributor must respect. It is guidance for building
and redistributing photoncue — not legal advice.

## Why MIT, not GPL

Nothing in photoncue's stack forces a copyleft license:

- The **DeckLink SDK** (headers/libs photoncue links against) is permissively
  licensed (Boost-style).
- **GStreamer / GES** is LGPL-2.1, which explicitly permits non-copyleft
  application licenses.
- **FFmpeg** (reached through `gst-libav`) provides the codecs photoncue needs
  — ProRes and DNxHR decode/encode — in its default **LGPL-only** build,
  without enabling any GPL switches.

A prior GPL-3.0 license was actively problematic: GPL-3.0 conflicts with the
proprietary Blackmagic DeckLink driver photoncue runs against. MIT avoids that
conflict and keeps the project maximally reusable.

## The two conditions a distributor must keep

To keep an MIT-licensed photoncue clean on top of LGPL dependencies:

1. **Build FFmpeg in its LGPL configuration.** Do **not** pass `--enable-gpl`
   or `--enable-nonfree` when building FFmpeg / `gst-libav`. ProRes (`prores`)
   and DNxHR (`dnxhd`) are available in the LGPL build, so no GPL switch is
   needed. Enabling GPL switches would pull GPL obligations onto anything that
   ships that FFmpeg build.
2. **Link GStreamer and FFmpeg dynamically.** LGPL permits use from a
   differently-licensed application when the LGPL library is dynamically
   linked (the user can substitute their own build of it). Do not statically
   link these into photoncue binaries you distribute.

## Third-party components photoncue does NOT redistribute

Two Blackmagic components are required but are **not** included in this
repository or in any photoncue distribution. Each user obtains them from
Blackmagic directly, under Blackmagic's own terms:

- **DeckLink SDK** — needed only at build time to compile the output layer.
  Permissively licensed, but kept out of the repo (see `.gitignore`); download
  it from Blackmagic.
- **Blackmagic Desktop Video driver** — the proprietary runtime driver the
  node needs to talk to the card. Its license is a single-system use license
  that does **not** grant redistribution without Blackmagic's permission, so
  photoncue does not bundle it. It is installed by the user (or fetched at
  provisioning time from Blackmagic). Bundling it into a distributed node image
  would require an OEM/redistribution agreement with Blackmagic.

## Summary

| Component | License | photoncue's handling |
|---|---|---|
| photoncue (this project) | MIT | This repo |
| GStreamer / GES | LGPL-2.1 | Dynamically linked; not redistributed |
| FFmpeg / gst-libav | LGPL (LGPL-only build) | Dynamically linked; LGPL build only |
| DeckLink SDK | Permissive (Boost-style) | Build-time only; user-supplied, not in repo |
| Desktop Video driver | Proprietary (Blackmagic EULA) | User-supplied/installed; not bundled |

If you intend to distribute a pre-built node image that includes the Desktop
Video driver, resolve the redistribution question with Blackmagic first — that
is the one open item this project does not settle on its own.
