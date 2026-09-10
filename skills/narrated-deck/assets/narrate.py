#!/usr/bin/env python3
"""Generate per-slide narration with Gemini TTS from narration.md.

narration.md format: a "## Slide N" heading per slide (anything after the dash is ignored),
followed by the exact words to speak. Front matter before the first heading is ignored.

Usage:
  narrate.py --dir <deck-dir> [--voice Charon] [--model pro] [--style "..."] [--only 3] [--skip-existing]
Writes: txt/slide-NN.txt, audio/slide-NN.mp3, audio/narration-full.mp3, timings.json
"""
import argparse, json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_STYLE = ("Speak clearly and warmly at a measured pace, like a product keynote narrator. "
                 "Pause briefly between sentences.")

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=".")
ap.add_argument("--voice", default="Charon")
ap.add_argument("--model", default="pro", help="pro (best) | flash | next | full model id")
ap.add_argument("--style", default=DEFAULT_STYLE)
ap.add_argument("--only", type=int, help="regenerate one slide number")
ap.add_argument("--skip-existing", action="store_true")
a = ap.parse_args()

d = pathlib.Path(a.dir).resolve()
md = (d / "narration.md").read_text()
parts = re.split(r"^## Slide (\d+)[^\n]*\n", md, flags=re.M)
# parts = [preamble, n1, text1, n2, text2, ...]
sections = {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
if not sections:
    sys.exit("no '## Slide N' sections found in narration.md")
(d / "txt").mkdir(exist_ok=True); (d / "audio").mkdir(exist_ok=True)

tts = str(HERE / "tts.py")
for n in sorted(sections):
    if a.only and n != a.only:
        continue
    txt = d / "txt" / f"slide-{n:02d}.txt"
    mp3 = d / "audio" / f"slide-{n:02d}.mp3"
    words = len(sections[n].split())
    if words < 35 or words > 90:
        print(f"note: slide {n} narration is {words} words (aim 45-70)")
    txt.write_text(sections[n] + "\n")
    if a.skip_existing and mp3.exists():
        continue
    cmd = [sys.executable, tts, "-f", str(txt), "--voice", a.voice, "--model", a.model, "--style", a.style, "-o", str(mp3)]
    print(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip())

# timings + full track
def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0

clips = [(n, d / "audio" / f"slide-{n:02d}.mp3") for n in sorted(sections)]
clips = [(n, p) for n, p in clips if p.exists()]
timings = {"voice": a.voice, "model": a.model, "slides": [
    {"slide": n, "file": f"audio/slide-{n:02d}.mp3", "duration_sec": round(dur(p), 3)} for n, p in clips]}
timings["total_sec"] = round(sum(s["duration_sec"] for s in timings["slides"]), 3)
(d / "timings.json").write_text(json.dumps(timings, indent=2))
lst = d / "audio" / "list.txt"
lst.write_text("".join(f"file '{p.name}'\n" for _, p in clips))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                str(d / "audio" / "narration-full.mp3")], check=True)
m, s = divmod(int(timings["total_sec"]), 60)
print(f"{len(clips)} clips, total {m}:{s:02d}; timings.json and audio/narration-full.mp3 written")
