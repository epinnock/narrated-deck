# narrated-deck

A Claude Code skill that turns a plan, roadmap, or report into a short narrated
presentation: self-contained HTML slides with embedded Google Gemini TTS narration, a
1920×1080 MP4, and (inside Claude Code) a shareable Artifact link.

- **Slides**: one HTML file, keyboard and click navigation, deep links, light and dark
  themes, phone-width layout, a Play button that narrates and auto-advances.
- **Narration**: Gemini 2.5 Pro TTS (or Flash / 3.1 Flash preview), 30 voices, steerable with
  a plain-English style prompt.
- **Video**: Playwright screenshots stitched with ffmpeg, one segment per slide, cut to the
  narration length.

## Install

In Claude Code:

```
/plugin marketplace add epinnock/narrated-deck
/plugin install narrated-deck@narrated-deck
```

Then ask for a deck: "make a five-minute narrated deck of this roadmap", or invoke
`/narrated-deck` directly.

Without Claude Code, copy `skills/narrated-deck/` anywhere and run the scripts in
`assets/` by hand (see the skill's step 4).

## Requirements

- Python 3.9+, `ffmpeg` and `ffprobe`
- Node 18+ with Playwright and Chromium: `npm i -D playwright && npx playwright install chromium`
  in the deck directory, or set `PLAYWRIGHT_MODULE` to an existing install
- A Gemini API key in `GEMINI_API_KEY` (Google AI Studio)

## How it works

```
slides.html + narration.md
   → narrate.py     audio/slide-NN.mp3, narration-full.mp3, timings.json
   → build-deck.py  index.html (audio embedded), index.artifact.html
   → shoot.js       slides/slide-NN.png
   → stitch.py      deck.mp4
```

`skills/narrated-deck/SKILL.md` holds the writing rules (slide density, narration length
and tone, palette and type) and the gotchas. `skills/narrated-deck/example/` is a
six-slide onboarding deck you can build end to end to check the setup.

## Try the example

```bash
mkdir demo && cd demo
cp ../skills/narrated-deck/example/slides.example.html slides.html
cp ../skills/narrated-deck/example/narration.example.md narration.md
S=../skills/narrated-deck/assets
python3 $S/narrate.py --dir . --voice Charon --model pro
python3 $S/build-deck.py --dir . --title "First Week Onboarding"
node $S/shoot.js .
python3 $S/stitch.py --dir . --out onboarding.mp4
```

## License

MIT
