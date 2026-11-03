---
name: download-big-files-with-idm
description: Use for big downloads (models, weights, wheels, installers, archives, videos; roughly over 50 MB) on a Windows machine that has Internet Download Manager (IDM). Hands the file to IDM through the idm CLI instead of curl, pip, Python or huggingface_hub, proves bytes are really moving, keeps IDM's windows hidden, and resumes the follow-up work after the file lands. Includes the Hugging Face gated-model and Git Bash traps.
---

# Download Big Files With IDM

Why: on an unreliable line, long single connections drop. A 1.2 GB huggingface_hub download can stall at 872 MB and
restart from zero. IDM resumes; the others often do not. Small files (configs, tokenizers, metadata) may still use normal
tools.

The CLI is `idm.exe` (source `src/idm.cs` in the repo, build `build.ps1` there). Put it on PATH or set `IDM_CLI` to its full path.
It needs IDM installed (a commercial program the user must own) and the user logged in to a normal desktop session.

## 1. Get the final direct URL

IDM cannot send auth headers. Resolve the real link first.

- Hugging Face (gated or xet): ask the redirect with the token and take `location:`.
  ```bash
  curl -s -I -H "Authorization: Bearer $HF_TOKEN" \
    https://huggingface.co/<repo>/resolve/main/<file> | grep -i '^location:' | tr -d '\r' | cut -d' ' -f2
  ```
  The signed CDN URL expires in about one hour. Hand it to IDM at once. If IDM later reports 403, resolve a fresh URL and
  restart that item.
- Expected size: `https://huggingface.co/api/models/<repo>/tree/main` gives each file's `size`. Write it down; it is the
  finish check.
- Fetch the small sibling files normally, for example
  `snapshot_download(repo, local_dir=..., ignore_patterns=['model.safetensors', '*.onnx*'])`.
- Pip wheels: read the wheel URL from the PyPI JSON API or `pip download --no-deps -d x --dry-run`; never let pip download
  the big wheel itself.

**Queue rule:** ONE file = `idm add` (a direct download; never start the main queue, because its "when done" actions are
the user's). SEVERAL files = only the dedicated agent queue (`IDM_QUEUE`, default "Agent Queue", created once by the user in
IDM's Scheduler); never put your files in the main queue. Check the queue's "when done" actions (shutdown, hang up) before
starting a long queue.

## Fast commands: `idm.exe` (milliseconds, no IDM window stays on the desktop)

| Job | Command |
|---|---|
| Start one file | `idm add <url> <folder> <name>` (starts now, hides its progress window; about 0.4 s) |
| Several files, one after another | `idm queue <folder> <url> <url2> ... --start` (all links in one step through IDM's clipboard-list dialog, moved into the agent queue) |
| Start / stop the agent queue | `idm start`, `idm stopq` |
| Remove a row from IDM's list | `idm remove <row name>` (remove test downloads afterwards) |
| See everything | `idm status [text] [--all]`; `idm watch [text] [seconds]` prints until nothing runs |
| Stop one file | `idm stop <name or url part>` (a queue file has no progress window, so this stops the agent queue) |
| Stop everything | `idm stopall` |
| Clear the desktop | `idm hide` (every command already ends with no IDM window on the desktop) |

The queue commands (`queue`, `start`, `stopq`, `stop` on a queue file) depend on IDM internals: window texts of the
Persian interface (class `Ui` in `idm.cs`) and WM_COMMAND ids (`IDM_MOVE_CMD`, queue id `IDM_QUEUE_ID`). They were tuned on
one IDM version; if one does not work on this machine, say so and use `idm add` per file. `add`, `status`, `watch`,
`stopall`, `remove` and `hide` do not depend on them.

How it works, briefly: one file = IDM's command line (`/d ... /n`). Several files = IDM's own "add a list of links from the
clipboard" path driven off-screen. The main window is shown only fully transparent when a list row has to be selected, then
hidden again. Status comes from IDM's registry plus each item's live log (running = a progress line in the last 6 seconds
and no "Cancel by user" after it).

## 2. Start it in IDM

Run from **PowerShell**, not Git Bash:

```powershell
& "<skills dir>\download-big-files-with-idm\scripts\idm-start.ps1" -Url $url -Dir $dir -Name model.safetensors -ExpectedBytes 1211486072
```

It runs `idm.exe add <url> <dir> <name>` (about 0.4 s, prints `progress window hidden`). The exe also works from Git Bash,
because it takes no slash flags that MSYS could mangle. Raw IDM flags: `/a` adds to the queue without starting, `/s`
starts the queue.

Traps learned the hard way:

- **Git Bash rewrites the flags.** MSYS turns `/d` and `/p` into `D:/` and `P:/`, so IDM gets garbage and nothing
  downloads, with no error. Use PowerShell `Start-Process`, or in bash prefix `MSYS2_ARG_CONV_EXCL='*'`.
- **Quote every argument.** `Start-Process` joins the array with spaces; a signed URL with `&` and `=` must stay inside one
  quoted argument.
- **`/d` can fail silently** when an IDM instance is open but not handling command-line messages: the command returns fine,
  yet no item appears. Close IDM fully and retry.
- **The file does not appear until the end.** IDM writes parts to its temp folder and moves the finished file into the
  target folder only at completion. An empty target folder mid-download is normal; it is not proof of anything.

## 3. Prove it is running before saying so

**Before any sentence about IDM state, run `idm status <name>` (or `scripts/idm-status.ps1 -Match <name>`) and report only its
rows.** Each row: real file name, state (queued, running, stopped, done), percent, MB, speed, IDM's last message. Folder names
and registry ids are NOT part numbers. Empty speed means nothing is downloading.

The registry alone can be stale: IDM reuses ids and rewrites it only now and then. Live progress is the item's own log
(`%APPDATA%\IDM\DwnlData\<user>\<name>_<id>\*.log`): IDM appends `time <unix>, speed <B/s>, downl <bytes> Bytes` every
few seconds while downloading; a `time` within the last minute means it is downloading now. Do not use directory-listing
sizes or LastWriteTime of the part files: NTFS does not update them while IDM holds the files open. A temp folder that
vanished means that file finished.

```powershell
& "<skills dir>\download-big-files-with-idm\scripts\idm-status.ps1" -Match <file or url part>
& "...\idm-status.ps1" -Match <name> -Wait   # blocks until done or stopped; run it in the background
```

A launched process is not a running download. Never claim success from the command's exit code. Look twice: the byte
count must rise between two looks. If an item is stopped, say so and ask before resuming (the user may have paused it); if
resume fails with 403, the signed URL expired: resolve a fresh one.

## 4. Tidy the windows

Every download start hides the small progress window (the same effect as its "hide beside the clock" button). Never close,
Alt+F4, Stop, Pause or Cancel the progress window yourself; those can stop the transfer.

## 5. Follow up

- A plain "download this" request is done once bytes move and the windows are tidy.
- Follow-up work (load a model, pip install, extract): read IDM's ETA and check back about 10 minutes after it. Record the
  URL, file name, folder, expected bytes and the next step.
- Finished means the file exists at `<dir>\<name>` **and** its size equals the expected bytes. Check that before the next
  step. Then use the local copy and run the smallest real check.

## Safety

- Never run a downloaded executable without asking.
- Do not change IDM settings unless asked.
- Keep tokens out of IDM, out of URLs in chat and out of repositories; a signed CDN URL carries no token.
