# FastDesk

Lets an agent control Windows apps. It runs a chain of clicks, typing and window reads through UI Automation, and replays
saved chains. Written in Python.

## What it gives an agent

- `fd windows` lists open windows; `fd view "<title part>"` prints the elements of one window (`role | name | value`).
- `fd run <chain>` runs a whole JSON chain of steps in one command, with no model call between steps: open an app, wait for a
  window, click or press a named element, set a field, toggle a checkbox, use a menu, read texts, minimize or close windows.
- Elements are found by role and name, never by screen position, so window size and place do not matter and the real mouse
  never moves.
- When a step fails, the output lists the failing step, the error, all window titles and the current window's elements, so
  only that step needs fixing. Chains that worked are saved and replayed without any model.

## Requirements

Windows 10 or 11 and Python 3.9+. The only dependency is the `uiautomation` package (installed into a virtual environment
in the install folder). Elevated (administrator) windows cannot be driven from a normal process.

## Install prompt

```text
Install "FastDesk" for me. It lets AI agents operate Windows desktop apps (click, type, read windows) by element name through Windows UI Automation, in whole chains of steps with no model call in between. Project: https://github.com/Sajjad-Majdi/agent-tools (folder fastdesk).

Requirements: Windows 10 or 11 and Python 3.9+. Check them first and tell me what is missing instead of guessing.

Steps:
1. Download https://github.com/Sajjad-Majdi/agent-tools/archive/refs/heads/main.zip into a temp folder and extract it. Download nothing else without asking me. If github.com is blocked on my network, tell me and ask which mirror or proxy to use.
2. Copy the folder fastdesk (without its skill subfolder) to %USERPROFILE%\.fastdesk.
3. Create a virtual environment there: python -m venv %USERPROFILE%\.fastdesk\.venv, then run %USERPROFILE%\.fastdesk\.venv\Scripts\python.exe -m pip install -r %USERPROFILE%\.fastdesk\requirements.txt (if PyPI is slow or blocked for me, ask for a mirror and use pip's -i option).
4. Install the skill: copy fastdesk/skill/SKILL.md to <skills folder>\fast-desktop\SKILL.md for every one of these folders that exists: %USERPROFILE%\.claude\skills, %USERPROFILE%\.agents\skills, %USERPROFILE%\.codex\skills. If none exists, create %USERPROFILE%\.claude\skills and tell me which agents will see it. In the copied SKILL.md, the runner "fd" is %USERPROFILE%\.fastdesk\fd.cmd.
5. Ask me whether to add %USERPROFILE%\.fastdesk to my user PATH so that the command fd works in any shell. Do it only if I say yes.
6. Smoke test: run %USERPROFILE%\.fastdesk\fd.cmd windows (it must list my open windows), then fd.cmd view "<a part of one open window's title>" (it must print role | name | value rows). Do not run the demo chain calc-multiply unless I agree: it opens the Calculator.

Safety: do not press buttons that spend money, send messages or delete data unless I asked for exactly that.
```

## Files

| Path | What |
|---|---|
| `fastdesk.py` | The runner (windows, view, run) |
| `fd.cmd` | Launcher that uses the virtual environment in the same folder |
| `chains/calc-multiply.json` | Demo chain: multiplies two numbers in the Windows Calculator |
| `requirements.txt` | `uiautomation` |
| `skill/SKILL.md` | Agent skill: the loop, the step reference and the rules |

A chain is a JSON list of steps, or `{"about": "...", "steps": [...]}`. See the docstring in `fastdesk.py` for every step.
