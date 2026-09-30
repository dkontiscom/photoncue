# pins — locked stack versions (HUMAN-ONLY)

Editing this file is hook-blocked for Claude Code. Change a pin only deliberately;
the whole stack is version-sensitive and a silent bump breaks reproducibility.

Fill each `<!-- NEEDS INPUT -->` before the first build.

- Repo name / host, greenfield or existing: `<!-- NEEDS INPUT -->`
- Code layout root for modules (e.g. `modules/`): `<!-- NEEDS INPUT -->`
- C/C++ build system (CMake vs Meson): `<!-- NEEDS INPUT -->`
- C++ standard (e.g. C++17 / C++20): `<!-- NEEDS INPUT -->`
- GStreamer version pin (whole stack locked to it): `<!-- NEEDS INPUT -->`
- gst-libav / gst-plugins-* version pin: `<!-- NEEDS INPUT -->`
- DeckLink SDK version (architecture cites the March 2026 manual — confirm exact
  SDK version): `<!-- NEEDS INPUT -->`
- Debian base version for the node ISO: `<!-- NEEDS INPUT -->`
- Rust toolchain / edition pin (Cargo): `<!-- NEEDS INPUT -->`
- Default house codec (ProRes 422 HQ vs DNxHR HQX) — **bench decision, leave open
  until measured on node hardware:** `<!-- NEEDS INPUT (bench) -->`
