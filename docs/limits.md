# limits — advisory design rules

**These are NOT hook-enforced.** They are design choices, not actions a hook can
see. Codex review and the human are what catch a violation. (The hook-enforced
*action* limits live in `.claude/settings.json` and are summarised in
`CLAUDE.md`.)

Treat every line below as a hard "never" for the design, even though nothing
mechanically blocks it.

## Never (design)

- **No audio.** No audio pipeline, elements, or handling, anywhere.
- **No delivery-codec decode:** no H.264/H.265, no DPX, no EXR.
- Sources are **ProRes / DNxHR / image sequences (PNG/JPEG/TIFF) only.**
- **One default house codec** (ProRes 422 HQ *or* DNxHR HQX, 10-bit 4:2:2 — the
  specific pick is a bench decision). Image sequences are a *supported input*,
  not the default (they are the most robust but the heaviest on storage/IO).
- **Transcode-normalize-verify is in-house.** The real work is the normalize
  step — VFR→CFR at house rate, colour primaries/transfer/matrix, full-vs-limited
  range, pixel format, canvas fit — not the encode. Never push the correctness
  guarantee onto the operator's DaVinci; a fine optional front-end, never the
  guarantee.
- **Output via the DeckLink SDK directly**, never GStreamer's
  `decklinkvideosink`. Pipeline ends in `appsink` → Rust/C → SDK. GES/GStreamer
  never talk to the card.
- **No GPU swap-barrier / framelock.** Output is DeckLink SDI, not GPU DP/HDMI.
  No NVIDIA Quadro Sync, no AMD S400.
- **GES in PREVIEW mode only.** Never RENDER (encode-to-file).
- **`GstPtpClock` is slave-only.** External PTP grandmaster is mandatory and is
  **never** on the controller.
- **Genlock rate == media rate.** Enforced by the offline transcode. No per-node
  rate conversion to hide a mismatch.
- **No live mid-take timeline switching.** The show is fully programmed before
  the take; only two sync events exist — the scheduled start and staying locked.
- Study **Pitivi** (Python + GES) as the reference GES app. **Not** Kdenlive
  (MLT-based; its DeckLink experience does not transfer).
- Keep the GL colour stage structured so **OpenColorIO** can slot in later
  without a rewrite — but do not build OCIO in v1.

## Deferred / undecided — do not build unless explicitly told

OpenColorIO; HAP codec; in-clip gapless looping / loop-bake helper; HFR above
60p; curved-wall `glshader` warp; DeckLink-IP / ST 2110 / PTP-only sync (v2 —
big additions, not a redo, and not in the v0.00x line).
