#!/usr/bin/env python3
"""Text-to-speech via the Gemini API (high-quality hosted voices).

Usage:
  tts.py "Hello there"                       # -> hello-there.wav in cwd
  tts.py -f script.txt -o intro.mp3          # read text from a file, write mp3 (needs ffmpeg)
  tts.py "..." --voice Puck --model pro      # pick a voice / model
  tts.py "..." --style "Read slowly, like a documentary narrator:"
  tts.py --list-voices

Key: GEMINI_API_KEY in the environment, else the key already configured for the
image MCP in ~/.claude.json (mcpServers.mcp-image.env.GEMINI_API_KEY).

Models (alias -> id): flash -> gemini-2.5-flash-preview-tts (default),
pro -> gemini-2.5-pro-preview-tts, next -> gemini-3.1-flash-tts-preview.
Output is 24 kHz 16-bit mono PCM wrapped as WAV; .mp3/.ogg/.m4a go through ffmpeg.
"""
import argparse, base64, json, os, re, socket, subprocess, sys, urllib.request, urllib.error, wave

# This box has broken IPv6 egress: force IPv4 for every lookup.
_orig_gai = socket.getaddrinfo
def _ipv4_only(*a, **k):
    return [r for r in _orig_gai(*a, **k) if r[0] == socket.AF_INET] or _orig_gai(*a, **k)
socket.getaddrinfo = _ipv4_only

MODELS = {
    "flash": "gemini-2.5-flash-preview-tts",
    "pro": "gemini-2.5-pro-preview-tts",
    "next": "gemini-3.1-flash-tts-preview",
}
# Prebuilt voices published for Gemini TTS (name: character).
VOICES = {
    "Zephyr": "bright", "Puck": "upbeat", "Charon": "informative", "Kore": "firm",
    "Fenrir": "excitable", "Leda": "youthful", "Orus": "firm", "Aoede": "breezy",
    "Callirrhoe": "easy-going", "Autonoe": "bright", "Enceladus": "breathy", "Iapetus": "clear",
    "Umbriel": "easy-going", "Algieba": "smooth", "Despina": "smooth", "Erinome": "clear",
    "Algenib": "gravelly", "Rasalgethi": "informative", "Laomedeia": "upbeat", "Achernar": "soft",
    "Alnilam": "firm", "Schedar": "even", "Gacrux": "mature", "Pulcherrima": "forward",
    "Achird": "friendly", "Zubenelgenubi": "casual", "Vindemiatrix": "gentle", "Sadachbia": "lively",
    "Sadaltager": "knowledgeable", "Sulafat": "warm",
}


def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    try:
        cfg = json.load(open(os.path.expanduser("~/.claude.json")))
        return cfg["mcpServers"]["mcp-image"]["env"]["GEMINI_API_KEY"]
    except Exception:
        sys.exit("No GEMINI_API_KEY in the environment or ~/.claude.json")


def synth(text, voice, model, key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Gemini API error {e.code}: {e.read().decode()[:500]}")
    try:
        part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    except (KeyError, IndexError):
        sys.exit("No audio in response: " + json.dumps(data)[:500])
    mime = part.get("mimeType", "")
    rate = int(re.search(r"rate=(\d+)", mime).group(1)) if "rate=" in mime else 24000
    return base64.b64decode(part["data"]), rate


def write_wav(path, pcm, rate):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", help="text to speak (or use -f)")
    ap.add_argument("-f", "--file", help="read text from a file")
    ap.add_argument("-o", "--out", help="output path (.wav default; .mp3/.ogg/.m4a via ffmpeg)")
    ap.add_argument("--voice", default="Kore", help="prebuilt voice name (see --list-voices)")
    ap.add_argument("--model", default="flash", help="flash | pro | next | full model id")
    ap.add_argument("--style", default="", help="natural-language delivery instruction prepended to the text")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    if a.list_voices:
        for n, c in VOICES.items():
            print(f"{n:<14} {c}")
        return
    text = open(a.file).read() if a.file else a.text
    if not text:
        ap.error("give text or -f FILE")
    if a.voice not in VOICES:
        print(f"warning: {a.voice} is not in the known voice list; trying anyway", file=sys.stderr)
    model = MODELS.get(a.model, a.model)
    prompt = f"{a.style.strip()}\n\n{text}" if a.style else text

    pcm, rate = synth(prompt, a.voice, model, api_key())

    out = a.out or (re.sub(r"[^a-z0-9]+", "-", text.lower())[:40].strip("-") or "speech") + ".wav"
    ext = os.path.splitext(out)[1].lower()
    if ext in ("", ".wav"):
        write_wav(out if ext else out + ".wav", pcm, rate)
        final = out if ext else out + ".wav"
    else:
        tmp = out + ".tmp.wav"
        write_wav(tmp, pcm, rate)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, out], check=True)
        os.remove(tmp)
        final = out
    secs = len(pcm) / (2 * rate)
    print(f"{final}  ({secs:.1f}s, {model}, voice {a.voice})")


if __name__ == "__main__":
    main()
