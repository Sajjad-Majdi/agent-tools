# IDM CLI

A command line tool that controls Internet Download Manager without opening its window. The agent can add downloads, build
queues, watch progress and stop downloads, and there is a skill for big downloads. Written in C#.

## What it gives an agent

| Command | Job |
|---|---|
| `idm add <url> <folder> <name>` | Start one download now; its progress window is hidden at once |
| `idm queue <folder> <url> ... [--start]` | Add many links in one step into a dedicated queue |
| `idm start` / `idm stopq` | Start or stop that queue |
| `idm status [text] [--all]`, `idm watch [text] [seconds]` | Current state, read from IDM's registry and live logs |
| `idm stop <text>`, `idm stopall` | Stop one download or all of them |
| `idm remove <row name>` | Remove a row from IDM's list |
| `idm hide` | Hide every IDM window (every command already ends with no IDM window on the desktop) |

The skill (`skill/SKILL.md`) tells the agent how to get a direct URL (Hugging Face gated files, pip wheels), why big files go
through IDM (it resumes; many other tools restart from zero), how to prove a download is moving, and what to do afterwards.
Two PowerShell scripts support it: `idm-start.ps1` and `idm-status.ps1`.

## Requirements and limits

- Windows 10 or 11 with Internet Download Manager installed (commercial software; you need your own licence).
- No SDK: `build.ps1` compiles `src/idm.cs` with the C# compiler that ships with Windows (.NET Framework 4).
- Settings by environment variable: `IDM_EXE`, `IDM_QUEUE`, `IDM_QUEUE_ID`, `IDM_MOVE_CMD` (see the header of `src/idm.cs`).
- It was written against the Persian interface of IDM 6.43. The window texts it looks for are in the `Ui` class in
  `src/idm.cs`; replace them for another interface language. `add`, `status`, `watch`, `stopall`, `remove` and `hide` use only
  the command line, the registry and fixed command ids and do not depend on them. The queue commands depend on those texts
  and on menu command ids that may differ between IDM versions.

## Install prompt

```text
Install "IDM CLI" for me. It lets AI agents control Internet Download Manager from the command line (add downloads, watch progress, stop them) without opening its window, and adds a skill for big downloads. Project: https://github.com/Sajjad-Majdi/agent-tools (folder idm-cli).

Requirements: Windows 10 or 11 and Internet Download Manager already installed and licensed by me. Check that IDMan.exe exists (default C:\Program Files (x86)\Internet Download Manager\IDMan.exe) and tell me if it is somewhere else or missing.

Steps:
1. Download https://github.com/Sajjad-Majdi/agent-tools/archive/refs/heads/main.zip into a temp folder and extract it. Get idm.exe by building it (no SDK needed): powershell -NoProfile -ExecutionPolicy Bypass -File idm-cli\build.ps1 -Out %USERPROFILE%\.idm-cli\bin. Alternative: download https://github.com/Sajjad-Majdi/agent-tools/releases/download/v1.0.0/idm.exe and check its SHA-256 against SHA256SUMS.txt from the same release. Download nothing else without asking me. If github.com is blocked on my network, tell me and ask which mirror or proxy to use.
2. Ask me whether to add %USERPROFILE%\.idm-cli\bin to my user PATH. Do it only if I say yes; otherwise set the user environment variable IDM_CLI to the full path of idm.exe. If IDMan.exe is not in the default place, also set IDM_EXE.
3. Install the skill: copy the contents of idm-cli/skill (SKILL.md and the scripts folder) to <skills folder>\download-big-files-with-idm\ for every one of these folders that exists: %USERPROFILE%\.claude\skills, %USERPROFILE%\.agents\skills, %USERPROFILE%\.codex\skills. If none exists, create %USERPROFILE%\.claude\skills and tell me which agents will see it. In the copied SKILL.md, "<skills dir>" is the skills folder you chose.
4. Optional, only if I want several files in a queue: tell me to create a queue named "Agent Queue" in IDM's Scheduler once. Then read the queueID value that IDM writes for a download moved into that queue (registry HKCU\Software\DownloadManager\<id>) and set IDM_QUEUE_ID to it. The queue commands depend on IDM's Persian interface texts and menu ids (see the header of src\idm.cs); if they fail, say so and use idm add per file.
5. Smoke test: run idm status. It must print the last downloads of my list (or nothing if the list is empty) and a time in milliseconds, and it must not leave any IDM window on my screen. Do not start a download unless I ask you to.

Safety: do not change IDM settings, do not run a downloaded executable without asking me, and keep tokens out of URLs you show me.
```

## Files

| Path | What |
|---|---|
| `src/idm.cs` | The CLI source |
| `build.ps1` | Compiles it with the Windows C# compiler |
| `skill/SKILL.md` | Agent skill for big downloads |
| `skill/scripts/idm-start.ps1` | Start one file and prove it started |
| `skill/scripts/idm-status.ps1` | Read the state of the downloads without any UI |
