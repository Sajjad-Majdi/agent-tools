---
name: remotion-video-production
description: How to make a narrated video, animated explainer, promo or educational course with Remotion, end to end - script, Persian text-to-speech narration, scenes synced to the voice, parallel scene agents, rendering. Use for every request for an explainer or course video, especially in Persian. Holds the fastest working pipeline, ready templates and the mistakes already made. Load the official remotion-* skills too for API details.
---

# Remotion video production (Persian narration)

Remotion (React) renders the frames, a text-to-speech service makes the voice, ffmpeg joins them. This skill holds the
pipeline that worked, the rules that kept the videos good, and the traps. Templates for the whole pipeline are in
`templates/` next to this file; `examples/demo/` is a tiny narration script and glossary to try `tts.py --check` on.

## 1. Rules for explainer videos

1. **Explain, never assume.** Treat the viewer as knowing nothing. Introduce every term before using it, with a plain
   definition, an everyday analogy and a concrete number example. Build each idea on the one before. A 20-30 minute video
   is fine; depth beats brevity.
2. **Show, do not tell.** Every sentence of narration has its own visual moment: the thing being said appears, moves or
   changes while it is said. Use concrete numbers, real transformations, cause then effect, one focal point at a time. No
   text walls.
3. **Technical terms on screen stay English, in Latin script** (`Attention`, `KV Cache`). Never write them in Persian
   letters on screen.
4. **Narration is colloquial spoken Persian** («می‌خوایم»), not bookish («می‌خواهیم»).
5. **Diacritics in the spoken text** on transliterated terms and Persian homographs (بُردار، کَش، مِه) so the voice
   pronounces them right. Captions strip them; speech keeps them.
6. **No captions or subtitles** unless the user asks. The narration audio is enough; the bottom of the frame stays free for
   visuals.
7. Before any download over 50 MB or any installer, tell the user the file, source and size and wait for a yes. Test
   installer flags with the command's help text first, so no dialog opens on the user's screen.
8. Before claiming a fact about recent models or research, look it up. Tell the user which on-screen numbers are
   illustrative and which come from a source.
9. Keep the finished video's size sane: flat motion graphics encode to about 2-3 MB per minute with x264 CRF 28 (`-tune
   animation`). Check the output size before delivery.

## 2. Voice (text to speech)

`templates/tts.py` supports ElevenLabs (`--eleven`, recommended; `--turbo` uses `eleven_v4_turbo` and costs half) and the free
`edge-tts` (default without `--eleven`; lower quality, needs `pip install edge-tts`).

- ElevenLabs key: the environment variable `ELEVENLABS_API_KEY` (or the name in `EL_KEY_VAR`). Voice id: `EL_VOICE`
  (the default is the premade voice "Matilda", only an example; free plans can use premade voices through the API, not
  library voices). Cost is about 1 credit per character: count the characters first (`tts.py <name> --check` prints the
  total) and tell the user if the quota cannot cover it. Do not paste keys into chat or files.
- With `--eleven`, `[Term]` is sent in English (Latin). ElevenLabs reads English well; Persian transliterations of English
  terms confuse it. Test two or three term-heavy sentences before the full run.
- Known misreads to fix in the spoken text: «مدل» may come out as «مَدل» (write «مُدِل»); a bare «تو» meaning "in" may be
  read as "you" (write «توی»); abbreviations such as `ReLU` need a spelled form («رِلو»). Keep an ElevenLabs-only respelling
  map in `tts.py`, separate from the edge-tts glossary.
- ElevenLabs acts out punctuation: «!» makes the end of a sentence sound shocked. End narration sentences with «.» unless
  real surprise is meant.
- v4 models accept audio tags such as `[excited]` or `[whispers]`. The script format uses `[...]` for terms, so write tags
  as `{excited}` in the narration and have `tts.py` turn them into `[excited]` in the spoken text only. Test on Persian first.
- Check the voice without listening: transcribe the audio with a speech-to-text model and compare it with the script. Accept
  a cached transcript only if it is real text, not a cached error.
- After synthesis, add an ffmpeg `loudnorm` pass on the muxed audio if the mean level is quiet.

## 3. Fastest pipeline (do it in this order)

Doing a short version first and then rewriting costs hours. Agree on scope first, then build once.

1. **Scope** (one question at most): audience level, target length, topics. Default: zero to hero, as long as needed.
2. **Research** current facts (web search, model cards). Note sources.
3. **Script** `src/<name>/narration.txt` + `glossary.json` (format below). One idea per line. Scenes of 5-14 sentences.
   Write the whole script before any visuals.
4. **Audio:** `python scripts/tts.py <name> [--eleven --turbo]` gives one m4a per scene in `public/<name>/` and
   `src/<name>/timing.json` with each sentence's start time (beats). It is cached per sentence, so re-running after edits only
   re-synthesizes changed lines.
5. **Kit + registry:** copy `templates/kit.tsx` into `src/<name>/` (SceneShell with title, progress and audio; `useAt(beat)`,
   `useSince`, Block, Arrow, Chip, FaText, Tokens, Matrix, Formula ...) and `templates/rootHelper.tsx`. Create placeholder
   scene files so everything compiles. Remove from SceneShell anything the video does not want (for example captions).
6. **Parallel scene agents** (section 5). Each agent owns one scenes file and one entry file.
7. **Type-check** `npx tsc --noEmit`, then **render** with `VIDEO=<name> COMP=<compositionId> node scripts/render.mjs out/<file>.mp4`.
   It renders muted with the system Chrome, then muxes the scene audio with ffmpeg at exact offsets. One `renderMedia` call
   keeps every tab in one Chrome renderer process, so CPU stays low whatever the concurrency; `render.mjs` therefore splits
   the frames into `PARTS` chunks, renders `MAXPAR` chunks at once (each in its own browser) and joins them with ffmpeg
   concat. Good starting values: `PARTS=12 MAXPAR=4 CONC=2` (each browser uses about 1 GB of RAM; too many swaps a 16 GB
   machine). Finished chunks get a `.ok` marker and are reused after a crash. The GPU can encode (NVENC) but cannot speed up
   the drawing: Chrome draws DOM and SVG on the CPU.
8. **Verify:** duration, audio level (`ffmpeg -af volumedetect`), file size, a few frames, and a single-frame brightness
   spike check for corrupt frames. Report honestly what was and was not checked by eye.

## 4. Script format (`templates/tts.py` reads it)

```
# sceneId
یه جمله‌ی محاوره‌ای با [Token] و [KV Cache] و [2017|دو هزار و هِفده].
```
- `[Term]`: the screen shows `Term`; speech uses `glossary.json[Term]` (with diacritics). One spoken form per term keeps the
  pronunciation consistent across the video.
- `[Shown|spoken]`: a one-off override (numbers, years, model names).
- `[Term] ـه`: the screen shows «Term ـه», speech joins it as «...ه».
- The plural of an English term in a Persian sentence is the singular term + «ها»: `[Token]ها` gives «Tokenها». Never use
  the English plural (`[Tokens]`).
- The script refuses to run if a term is missing from the glossary or Latin letters remain in speech (edge-tts).
- `python scripts/tts.py <name> --check` prints every sentence as shown on screen and as spoken, with the character count,
  and writes nothing.

## 5. Parallel scene agents (what worked)

- Write `docs/BRIEF.txt` first (template in `templates/BRIEF.template.txt`): viewer level, hard rules, layout safe area, the kit API,
  "every beat gets a visual", tools and the quality bar. Give each agent a scene list with a concrete visual idea per scene.
- One scenes file + one `src/entries/<X>.tsx` per agent (it registers only its scenes through `makeRoot`). Stills then bundle
  in isolation, so one agent's half-written file never breaks another.
- Agents must not edit the kit or shared files. Keep helpers inside their own file.
- 3 agents with 5-8 scenes each is a good size, within the user's agent limits. Agents stall on long runs or network drops.
  Resume with a short message ("continue from your partial work in <file>"). If an agent stalls again right away, check its
  file: the work is often already done. List and stop a whole agent tree before handing over, or a second set will write the
  same file.
- Check stills: `node scripts/beats.mjs <sceneId> [videoName]` gives each beat's frame. Render stills with
  `node scripts/stills.mjs <outDir> src/entries/<X>.tsx T-<sceneId>:<frame> ...` and look at them.

## 6. Technical lessons (Windows)

- Remotion's Chrome Headless Shell download can fail on restricted networks. Use the system Chrome:
  `browserExecutable: "C:/Program Files/Google/Chrome/Application/chrome.exe"` (env `CHROME` in the templates) and
  `chromeMode: "chrome-for-testing"`.
- **Do not open Remotion Studio or any browser preview** on a machine where a download manager watches the browser: it grabs
  media from localhost and opens dialogs. Render with `inputProps {noAudio: true}` and mux the audio with ffmpeg.
- WAV crashes `@remotion/media` (a mediabunny assertion). Use m4a/AAC.
- Google Fonts can load slowly. Set `timeoutInMilliseconds: 180000` in `selectComposition`, `renderMedia` and still renders,
  and retry once if a render fails on a font timeout.
- RTL: always `dir="rtl"` on Persian text. A comma or arrow between two Latin words inside a Persian line flips their order,
  so use «و» or rephrase. Vazirmatn lacks «←» and «−».
- Animations only through `useCurrentFrame` and `interpolate`. No CSS transitions. Use a deterministic `rand(i)`.
- Scene length = LEAD 0.5 s + narration + TAIL 0.9 s, with a 15-frame fade between scenes (subtract it from the total).
- If bundling, stills or rendering fail with "No available ports found", Windows may have reserved the port range (check
  `netsh interface ipv4 show excludedportrange protocol=tcp`). Pass a free `port` (env `PORT` in `render.mjs`).
- The `@remotion/transitions` shader presentations (crosswarp, ripple, zoom-blur ...) need an experimental Chrome API. Use the
  CSS ones or write your own.
- Promo and ad work needs real creativity, not the course template: a vertical 1080x1920 frame, a fresh kit (a phone mockup
  with the app UI recreated in React, a finger with taps and holds, kinetic headlines, how-to pills, aurora and grain).
  Recreate the app UI in React (crisp) instead of upscaling low-resolution screenshots.
- Music: instrumental, matched to the video's mood, no words. Calm under the opening, rising at the product reveal, peaking on
  the closing logo. Never cut into a track at its drop; enter in its build with a short crossfade and matched levels (measure
  RMS above 150 Hz, since laptop speakers drop the lows). Code-synthesized music sounds cheap. Gemini-generated tracks run at
  an exact tempo, so a beat grid fitted with numpy lets you cut only on downbeats where the chord loop matches. Check any
  track for producer tags or voices before using it. Sound effects can come from ElevenLabs' sound-generation endpoint
  (a few credits each).
- Hardware encoders can hang silently on one chunk (no error, no progress). Set `NOHW=1` for software encoding and keep the
  finished chunks. CPU-only rendering with `gl: "swiftshader"` at concurrency 4 dropped tiles in a few frames (visible
  flicker); concurrency 1 fixed it. For a small text fix re-render only that scene's frame range and splice it, then check
  every frame for brightness spikes.

## 7. Mistakes already made (do not repeat)

- Transliterated English terms on screen. See rule 3.
- Used terms without explaining them, which assumed the viewer already knew them. See rule 1.
- Spoken text without diacritics, so the voice misread words. See rule 5.
- Opened a browser preview while a download manager was running, which popped download dialogs.
- Started a big download without telling the user, and passed wrong installer flags, which opened a help dialog.
- Built a short version first and then rewrote everything. See section 3, step 1.
- Delivered a 1.2 GB file for 27 minutes (hardware encode at 12 Mbps). Expect about 2-3 MB per minute; `render.mjs` does the
  final encode with x264 CRF 28.
- Wrote English plurals (`Tokens`) inside Persian sentences. See section 4.
- Did not test the voice on homographs («مدل», «تو») and abbreviations before the full run.
- Cached a Python traceback as if it were a transcript. Accept a cached result only if it looks like a result.
- A stopped parent agent's scene agents kept running and a second set wrote the same scenes file. Stop the whole tree first.
- A narration with a mean level of -25 dB sounded quiet. Add a `loudnorm` pass before delivery.
- Long status reports. Keep replies short.

## 8. Templates

`templates/` holds the files from a 24-minute explainer. They assume the video folder `src/<name>/` (`VIDEO` env, default
`video`) and a root composition id (`COMP` env, default `Video`). The kit's palette names (`attn`, `ffn`, `norm` ...) come
from that course; rename them for your topic. Needed tools: Node 20+, ffmpeg and ffprobe on PATH, Google Chrome, Python 3.9+
(`tts.py`), a Remotion 4 project (`npx create-video@latest`) with `@remotion/media`, `@remotion/google-fonts`,
`@remotion/bundler` and `@remotion/renderer`.
