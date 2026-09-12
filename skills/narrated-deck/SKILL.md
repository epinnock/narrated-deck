---
name: narrated-deck
description: Build a short narrated presentation as self-contained HTML slides with Google Gemini TTS narration, a stitched MP4, and (in Claude Code) a shareable Artifact link. Use when the user asks for a presentation, deck, slides, pitch, walkthrough, or explainer "with audio", "narrated", "with voiceover", or a "video" of a plan, roadmap, or report. Not Figma Slides. The scripts are deterministic; the judgement is in the outline and the narration.
---

# Narrated deck

One pipeline, six steps. Everything lives in one deck directory; the scripts are in this
skill's `assets/` (referenced below as `$S`). A finished six-slide example is in `example/`.

```
<deck-dir>/
  slides.html         ← you write this (slide fragments; classes below)
  narration.md        ← you write this ("## Slide N" sections, 45–70 words each)
  audio/              ← narrate.py
  index.html          ← build-deck.py (standalone, audio embedded)
  index.artifact.html ← build-deck.py (wrapper-free, for the Artifact tool)
  slides/*.png        ← shoot.js
  <name>.mp4          ← stitch.py
  timings.json
```

Requirements on the machine: Python 3.9+, `ffmpeg`/`ffprobe`, Node 18+ with Playwright and
its Chromium (`npm i -D playwright && npx playwright install chromium` in the deck directory,
or point `shoot.js` at an existing install), and a Gemini API key in `GEMINI_API_KEY`.

Delegation: once the outline is agreed this is a good subagent task. Give the agent the
source documents, the slide outline, the path to this skill, and the deck directory.

## 1. Read the sources, write the outline

- Read the source material first and pin the audience and the one job of the deck.
- Default length: **10 slides, 4–5 minutes.** A "short" deck is 6–8 slides. Never more than 14.
- Outline in one pass: slide title + the ≤45 words of body that will appear + the diagram if
  any. Sequence carries meaning: open with the thesis, close with the ask. Numbered markers
  only where order is real (a process, a chain).
- Say specifics in the subject's own units and terms. No lorem, no placeholders.

## 2. Write `slides.html`

Only `<section class="slide" id="slide-N">` blocks, ids 1..N in order. Each section:

```html
<section class="slide" id="slide-4">
  <div class="body">
    <p class="eyebrow">Track one · reuse</p>
    <h2>The chain that has to hold end to end</h2>
    …content…
  </div>
  <div class="slide-foot"><span>Team · deck · Month Year</span><span class="pageno"></span></div>
</section>
```

Classes provided by `assets/deck-template.html` (1920×1080 stage scaled to the viewport;
stacks at ≤900px):

| Purpose | Classes |
|---|---|
| Title slide | `h1`, `.thesis` (accent-ruled statement), `.eyebrow` |
| Section slide | `h2`, `.lead`, `.note`, `.rule` (warning-ruled hard rule), `.big` (one large number) |
| Columns of cards | `.cols > .card` (`.card.alt` grey), `.card h3`, `.kicker.k-accent|k-success|k-warn` |
| Lists | `ul > li` (accent square), `li.ok` (success), `li.warn` |
| Chips | `.chips > .chip` (`.chip.s` success, `.chip.w` warning, `.chip.ghost` neutral) |
| Chain diagram | `.chain > .node (.n + .t) + .arrow` alternating; `.rails > .rail` underneath |
| Loop diagram | `.loop > .node + .arrow`, `.loopback` |
| Stage table | `.rows > .row (.st > .num, .crit)`, `.row.pilot` for a gated/optional row |
| Ask | `.ask` (accent panel) |

Rules: ≤45 words of body per slide; one diagram per slide at most; every slide has the
`.slide-foot`. If you need a new component, add a `<style>` block at the top of `slides.html`
that uses the tokens (`--fg --muted --accent --success --warn --line --card --bg-alt`), never
literal colours, so both themes hold.

Palette and type come from the template: white / #F5F5F7 ground, #111827 / #6B7280 text,
indigo #6366F1 accent, #0D9488 success, #D97706 warning; Geist from Google Fonts with a
system fallback; light default, dark under `prefers-color-scheme` and `[data-theme="dark"]`.
If the subject calls for a different palette, change the tokens in the template's `:root`,
the dark media block **and** the `[data-theme="dark"]` block together.

## 3. Write `narration.md`

```
## Slide 1 — Title
Welcome to … (45–70 words)

## Slide 2 — Where we stand
…
```

- 45–70 words per slide → 20–30 s at the pro voice's ~125 words per minute. Ten slides ≈ 4–5
  minutes.
- Conversational, present tense, one idea per sentence. Say what the slide shows without
  reading it aloud. Identifiers at most once per slide; no file paths, URLs, or acronyms the
  listener cannot hear.
- The narration is the exact text sent to TTS; punctuation drives pacing. Full stops, not
  dashes.

## 4. Run the pipeline

```bash
S=${CLAUDE_SKILL_DIR}/assets   # the skill's own assets directory
D=/path/to/deck-dir
python3 $S/narrate.py --dir $D --voice Charon --model pro     # Gemini 2.5 Pro TTS, one call per slide
python3 $S/build-deck.py --dir $D --title "Deck Name"         # index.html + index.artifact.html
node    $S/shoot.js $D                                         # slides/slide-NN.png at 1920×1080
python3 $S/stitch.py --dir $D --out deck.mp4                   # per-slide segments + concat
```

- TTS: `assets/tts.py` reads `GEMINI_API_KEY` (or, in Claude Code, the key configured for the
  image MCP in `~/.claude.json`). Models: `pro` (best, default here), `flash`, `next`
  (`gemini-3.1-flash-tts-preview`). Voices: Charon (informative), Sulafat (warm), Kore (firm),
  Puck (upbeat); `tts.py --list-voices` for all 30. Regenerate one slide with `--only N`;
  reuse existing clips with `--skip-existing`.
- The default style prompt (keynote narrator, measured pace, pause between sentences) is in
  `narrate.py`; override with `--style`.
- `shoot.js` opens `index.html?clean` so the control bar is not captured and waits for
  `document.fonts.ready`. Pass a Playwright module path as the second argument or set
  `PLAYWRIGHT_MODULE` when it is installed elsewhere.
- `stitch.py` cuts each segment to clip length + 0.6 s. Do not use ffmpeg `-shortest` for
  stills; it overruns every segment by seconds.

## 5. Look once, then publish

- Look at one or two PNGs in `slides/` (the diagram slide and the densest slide). Fix
  clipping or overlap in `slides.html`, rebuild, reshoot. One pass, not a loop.
- In Claude Code, publish `index.artifact.html` with the Artifact tool (the title is inside
  the file; pass a one-sentence description, a favicon, and a label like "v1"). The fragment
  has no doctype/html/head/body; the Google Fonts link is the only external resource. Keep the
  file under 12 MB (ten clips ≈ 1.2 MB).
- If a subagent wrote the files, read `slides.html` and `narration.md` in full before
  publishing. `index.html` is template + slides + base64 audio of that narration, so the
  megabytes of base64 do not need reading.
- Deliver the MP4 alongside the link (caption: slide count, duration, voice). The link is the
  interactive version; the MP4 is for people who will not click.

## 6. Report

Link, MP4 path and duration, slide count, voice and model, anything shortened or not built.
Do not paste the narration.

## Gotchas already paid for

- Artifact pages must not contain `<!doctype>`, `<html>`, `<head>` or `<body>`; the tool wraps
  the fragment. `build-deck.py` produces that fragment.
- Body background is set from a token in the template; keep it, or the host theme bleeds
  through.
- Deep links are `#slide-N`; `?clean` hides the chrome. Space toggles play, arrows navigate,
  `◐` toggles theme, and the speed slider (0.5–4×, `[` / `]` to step) sets narration
  playback rate — remembered per viewer in `localStorage`, pitch-corrected where the
  browser supports it. It affects only the HTML player; the MP4 is always 1×.
- Play auto-advances on `ended`; a slide with no clip stops playback there. Narrate every
  slide or accept the stop.
- `tts.py` forces IPv4 lookups because some hosts have broken IPv6 egress; harmless elsewhere.
- Keep prose off chart-like slides; a stage table with a ≤12-word criterion per row reads
  better than paragraphs.
