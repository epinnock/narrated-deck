#!/usr/bin/env python3
"""Stitch slides/slide-NN.png + audio/slide-NN.mp3 into one MP4.

Each segment is cut to its clip's duration plus a short pause (default 0.6 s) — do not rely on
ffmpeg's -shortest, which overruns each still by a few seconds.

Usage: stitch.py --dir <deck-dir> --out deck.mp4 [--pause 0.6]
"""
import argparse, pathlib, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=".")
ap.add_argument("--out", default="deck.mp4")
ap.add_argument("--pause", type=float, default=0.6)
a = ap.parse_args()
d = pathlib.Path(a.dir).resolve()

def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)

pngs = sorted((d / "slides").glob("slide-*.png"))
if not pngs:
    raise SystemExit("no slides/slide-NN.png; run shoot.js first")
segs = []
for png in pngs:
    nn = png.stem.split("-")[1]
    mp3 = d / "audio" / f"slide-{nn}.mp3"
    seg = d / f"seg-{nn}.mp4"
    if mp3.exists():
        t = dur(mp3) + a.pause
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(png), "-i", str(mp3),
               "-t", f"{t:.3f}", "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(seg)]
    else:  # silent slide: 6 seconds, silent audio track so concat stays uniform
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(png),
               "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "6", "-c:v", "libx264", "-tune", "stillimage",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(seg)]
    subprocess.run(cmd, check=True)
    segs.append(seg)

lst = d / "seglist.txt"
lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
out = d / a.out
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "csv=p=0", str(out)],
                      capture_output=True, text=True).stdout.split()
print(f"{out}  {info}")
