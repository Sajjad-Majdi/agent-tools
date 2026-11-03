# Persian video skill

A skill for making narrated explainer and promo videos with Remotion. The agent writes the script, makes the Persian
voice-over, syncs scenes to the voice and renders the video. Written in TypeScript and React (the scenes), with Node scripts
for rendering and Python for the voice-over.

## What it gives an agent

- The whole pipeline in order: scope, research, narration script, voice-over, scene kit, parallel scene agents, render,
  verification.
- Rules for explainer videos: explain every term, one visual moment per sentence, English terms in Latin script on screen,
  colloquial spoken Persian with diacritics where the voice needs them.
- Templates (`skill/templates/`):
  - `tts.py`: narration script to one audio file per scene plus `timing.json` with each sentence's start time. Uses
    ElevenLabs (recommended) or the free `edge-tts`; `--check` parses the script and prints what is shown and what is spoken
    without any network call.
  - `kit.tsx` and `rootHelper.tsx`: scene shell with title, progress and audio, animation helpers, blocks, arrows, chips,
    matrices, formulas.
  - `render.mjs`: renders the frames in parallel chunks with the system Chrome, joins them and mixes the narration at exact
    offsets with ffmpeg. `stills.mjs` and `beats.mjs` support scene work.
  - `BRIEF.template.txt`: the brief to give each scene agent.
- A script and glossary example in `skill/examples/demo/`.
- Technical lessons (ports, fonts, RTL, encoders, music) and the mistakes already made.

## Requirements

Node.js 20+, ffmpeg and ffprobe on PATH, Google Chrome, Python 3.9+, and a Remotion 4 project (`npx create-video@latest`).
For ElevenLabs voices, an API key in the environment variable `ELEVENLABS_API_KEY` that you set yourself. The templates are
tuned for Windows.

## Install prompt

```text
Install the "Persian video skill" for me. It teaches AI agents to make narrated Persian explainer and promo videos with Remotion (script, voice-over, scenes synced to the voice, render) and ships templates for the pipeline. Project: https://github.com/Sajjad-Majdi/agent-tools (folder persian-video).

Requirements: Node.js 20+, ffmpeg and ffprobe on PATH, Google Chrome, Python 3.9+. For ElevenLabs voice-over I need an API key in the environment variable ELEVENLABS_API_KEY, which I will set myself; never ask me to paste it in the chat. Check each requirement first and tell me what is missing instead of guessing.

Steps:
1. Download https://github.com/Sajjad-Majdi/agent-tools/archive/refs/heads/main.zip into a temp folder and extract it. Download nothing else without asking me (installers and files over 50 MB need my yes with file, source and size). If github.com is blocked on my network, tell me and ask which mirror or proxy to use.
2. Install the skill: copy the contents of persian-video/skill (SKILL.md, templates and examples) to <skills folder>\remotion-video-production\ for every one of these folders that exists: %USERPROFILE%\.claude\skills, %USERPROFILE%\.agents\skills, %USERPROFILE%\.codex\skills. If none exists, create %USERPROFILE%\.claude\skills and tell me which agents will see it.
3. Ask me whether to also install the official Remotion agent skills (npx skills add remotion-dev/skills). Do it only if I say yes.
4. Smoke test without any network or audio: make a scratch folder with scripts\ and src\demo\, copy templates\tts.py into scripts\ and the files of examples\demo into src\demo\, then run python scripts\tts.py demo --check there. It must print every sentence twice (as shown on screen and as spoken, with the glossary applied) and a character count. Delete the scratch folder afterwards.
5. Do not start a video project, install Remotion or call the voice service unless I ask for a video.

Safety: tell me the character count before any ElevenLabs run, because it costs credits. Do not open Remotion Studio or browser previews; render with the scripts in the templates.
```

## Files

| Path | What |
|---|---|
| `skill/SKILL.md` | The skill |
| `skill/templates/` | `tts.py`, `kit.tsx`, `rootHelper.tsx`, `render.mjs`, `stills.mjs`, `beats.mjs`, `BRIEF.template.txt` |
| `skill/examples/demo/` | A tiny narration script and glossary for `tts.py --check` |
