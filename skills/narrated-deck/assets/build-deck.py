#!/usr/bin/env python3
"""Assemble a narrated HTML deck.

Inputs (in the deck directory):
  slides.html            the <section class="slide" id="slide-N"> fragments (see SKILL.md for classes)
  audio/slide-NN.mp3     optional narration clips (from narrate.py)
Outputs:
  index.html             full standalone document (open locally, screenshot, share as a file)
  index.artifact.html    wrapper-free fragment for the Artifact tool (no doctype/html/head/body)

Usage: build-deck.py --dir <deck-dir> --title "Deck Name" [--template path]
"""
import argparse, base64, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=".")
ap.add_argument("--title", required=True, help="short product-style name; shown in the tab and the artifact gallery")
ap.add_argument("--template", default=str(HERE / "deck-template.html"))
a = ap.parse_args()

d = pathlib.Path(a.dir).resolve()
tpl = pathlib.Path(a.template).read_text()
slides_path = d / "slides.html"
if not slides_path.exists():
    sys.exit(f"missing {slides_path}")
slides = slides_path.read_text()
ids = re.findall(r'id="slide-(\d+)"', slides)
if not ids or ids != [str(i) for i in range(1, len(ids) + 1)]:
    sys.exit(f"slides.html must contain id=\"slide-1\"..\"slide-N\" in order; found {ids}")
n = len(ids)

audio = {}
for i in range(1, n + 1):
    p = d / "audio" / f"slide-{i:02d}.mp3"
    if p.exists():
        audio[f"slide-{i:02d}"] = "data:audio/mpeg;base64," + base64.b64encode(p.read_bytes()).decode()
missing = [i for i in range(1, n + 1) if f"slide-{i:02d}" not in audio]

out = tpl.replace("<!--__SLIDES__-->", slides).replace("/*__AUDIO__*/{}", json.dumps(audio)).replace("__TITLE__", a.title)
if missing:
    # no clip for some slides: the Play button simply stops at the first missing one; say so in the report
    print(f"warning: no audio for slides {missing}")

(d / "index.html").write_text(out)

head = re.search(r"<head>(.*?)</head>", out, re.S).group(1)
body = re.search(r"<body>(.*)</body>", out, re.S).group(1)
links = "".join(re.findall(r"<link[^>]+>", head))
style = re.search(r"<style>.*?</style>", head, re.S).group(0)
frag = f"<title>{a.title}</title>\n{links}\n{style}\n{body.strip()}\n"
(d / "index.artifact.html").write_text(frag)

size = (d / "index.html").stat().st_size / 1e6
print(f"index.html {size:.2f} MB, {n} slides, {len(audio)} clips embedded; index.artifact.html written")
if size > 12:
    print("warning: over 12 MB; re-encode audio at 32 kbps or split the deck")
