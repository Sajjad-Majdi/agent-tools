"""Build narration audio for a video.

Reads src/<name>/narration.txt (scenes start with "# id"; one sentence per line) and
src/<name>/glossary.json. Markup: [Term] -> shows Term, speaks glossary[Term];
[Shown|spoken] -> one-off. Captions strip Persian diacritics; speech keeps them.
Writes one m4a per scene to public/<name>/ and src/<name>/timing.json with sentence beats.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:  # only needed without --eleven
    edge_tts = None

ROOT = Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
NAME = ARGS[0] if ARGS else "video"
# --eleven: ElevenLabs (needs the key in the env var named by EL_KEY_VAR, default ELEVENLABS_API_KEY). Default: edge-tts (free).
# --check: parse the script and print the sentences, no audio, no network.
ELEVEN = "--eleven" in sys.argv
CHECK = "--check" in sys.argv
# Voice id: set EL_VOICE. The default is the premade voice "Matilda" (an example; free plans cannot use library voices via API).
EL_VOICE = os.environ.get("EL_VOICE", "XrExE9yKIg1WjnnlVkGX")
EL_MODEL = "eleven_v4_turbo" if "--turbo" in sys.argv else "eleven_v4"  # turbo: half the credits
SRC = ROOT / "src" / NAME
TIMING = SRC / "timing.json"
OUT = ROOT / "public" / NAME
CACHE = ROOT / ".tts-cache" / (NAME + ("-eleven" if ELEVEN else ""))
VOICE = "fa-IR-DilaraNeural"
RATE = "+30%"
SR = 24000
GAP = 0.22  # seconds of silence between sentences
TEMPO = 1.3 if ELEVEN else 1.0  # speed-up without pitch change (ElevenLabs voices are slow)

HARAKAT = re.compile("[ٌ-ْٰ]")  # keeps tanween-fath (تقریباً)
TERM = re.compile(r"\[([^\]|]+)(?:\|([^\]]+))?\]")


def parse():
    glossary = json.loads((SRC / "glossary.json").read_text(encoding="utf-8"))
    scenes, missing = [], set()
    for line in (SRC / "narration.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            scenes.append({"id": line[1:].strip(), "text": [], "say": []})
            continue

        def spoken(m):
            if ELEVEN and re.search("[A-Za-z]", m.group(1)):
                return m.group(1)  # ElevenLabs reads English itself; Persian letters confuse it
            if m.group(2):
                return m.group(2)
            if m.group(1) not in glossary:
                missing.add(m.group(1))
                return m.group(1)
            return glossary[m.group(1)]

        say = TERM.sub(spoken, line).replace(" ـه", "‌ه" if ELEVEN else "ه")
        text = HARAKAT.sub("", TERM.sub(lambda m: m.group(1), line))
        scenes[-1]["text"].append(text)
        scenes[-1]["say"].append(say)
    if missing:
        raise SystemExit(f"missing glossary terms: {sorted(missing)}")
    latin = [] if ELEVEN else [s for sc in scenes for s in sc["say"] if re.search("[A-Za-z]", s)]
    if latin:
        raise SystemExit("Latin letters left in speech:\n" + "\n".join(latin))
    return scenes


def eleven_key() -> str:
    var = os.environ.get("EL_KEY_VAR", "ELEVENLABS_API_KEY")
    k = os.environ.get(var)
    if not k:  # set after this shell started: read it from the Windows user environment
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
                k = winreg.QueryValueEx(h, var)[0]
        except Exception:
            pass
    if not k:
        raise SystemExit(f"set the environment variable {var} to your ElevenLabs API key")
    return k


def eleven_save(text: str, mp3: Path) -> None:
    import urllib.request
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": EL_MODEL, "language_code": "fa"}).encode(),
        headers={"xi-api-key": eleven_key(), "Content-Type": "application/json"},
    )
    mp3.write_bytes(urllib.request.urlopen(req, timeout=180).read())


async def synth(text: str, mp3: Path, sem: asyncio.Semaphore) -> None:
    txt = mp3.with_suffix(".txt")
    if mp3.exists() and txt.exists() and txt.read_text(encoding="utf-8") == text:
        return
    async with sem:
        if ELEVEN:
            for attempt in range(5):
                try:
                    await asyncio.to_thread(eleven_save, text, mp3)
                    mp3.with_suffix(".txt").write_text(text, encoding="utf-8")
                    return
                except Exception as e:
                    body = getattr(e, "read", lambda: b"")()[:300]
                    print("retry", mp3.name, e, body)
                    if b"quota" in body or b"payment" in body:
                        raise
                    await asyncio.sleep(3 + attempt * 5)
            raise RuntimeError(f"failed: {mp3}")
        for attempt in range(4):
            try:
                if edge_tts is None:
                    raise SystemExit('pip install edge-tts, or use --eleven')
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(mp3))
                mp3.with_suffix(".txt").write_text(text, encoding="utf-8")
                return
            except Exception as e:  # network hiccups
                print("retry", mp3.name, e)
                await asyncio.sleep(2 + attempt * 2)
        raise RuntimeError(f"failed: {mp3}")


def to_pcm(mp3: Path) -> bytes:
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(mp3), *(["-af", f"atempo={TEMPO}"] if TEMPO != 1 else []), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout


async def main() -> None:
    scenes = parse()
    if CHECK:
        for s in scenes:
            print(f"# {s['id']}  ({len(s['say'])} sentences)")
            for t, say in zip(s["text"], s["say"]):
                print("  screen:", t)
                print("  speech:", say)
        print(f"{sum(len(s['say']) for s in scenes)} sentences, {sum(len(x) for s in scenes for x in s['say'])} characters to speak")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(2 if ELEVEN else 6)  # free plan: 2 concurrent requests
    jobs = []
    for s in scenes:
        for i, text in enumerate(s["say"]):
            jobs.append(synth(text, CACHE / f"{s['id']}_{i:02d}.mp3", sem))
    await asyncio.gather(*jobs)

    gap = b"\x00\x00" * int(GAP * SR)
    timing = []
    for s in scenes:
        pcm = bytearray()
        beats = []
        for i, _ in enumerate(s["say"]):
            if i:
                pcm += gap
            beats.append(len(pcm) / 2 / SR)
            pcm += to_pcm(CACHE / f"{s['id']}_{i:02d}.mp3")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
             "-c:a", "aac", "-b:a", "128k", str(OUT / f"{s['id']}.m4a")],
            input=bytes(pcm), check=True,
        )
        timing.append({
            "id": s["id"],
            "audio": f"{NAME}/{s['id']}.m4a",
            "duration": round(len(pcm) / 2 / SR, 3),
            "beats": [round(b, 3) for b in beats],
            "sentences": s["text"],
        })
    TIMING.write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(t["duration"] for t in timing)
    print(f"{len(timing)} scenes, {total:.1f}s audio")


asyncio.run(main())
