---
name: fast-desktop
description: Fastest way to operate any Windows desktop app (click buttons, fill fields, read windows, minimize, use menus) with no thinking between steps. Use it for native-app tasks instead of screenshot-based computer use. Runs whole chains of steps through fastdesk (Windows UI Automation by element name, not pixels), reuses saved chains, and asks the model again only when one step fails.
---

# fast-desktop

Speed comes from NOT calling the model between steps. Plan the whole chain once, run it in one command, and come back only
if a step fails. Do not take screenshots. The real mouse never moves.

Runner: `fd.cmd` in the fastdesk install folder (default `%USERPROFILE%\.fastdesk`; below: `fd`; from a bash shell call it
as `~/.fastdesk/fd.cmd`). Saved chains: `<install folder>\chains\<app>-<task>.json`. Engine: in-process Windows UI
Automation (Python `uiautomation` in the tool's own virtual environment); finding and pressing an element takes
milliseconds, so a whole chain runs in about a second plus the app's own waits.

## First: does the app have a command line or API?

That beats any UI driving (zero clicks, instant). Use fastdesk only for what the app does not expose.

## The loop (aim for 2-3 tool calls in total)

1. **Saved chain?** List `chains\`. If one fits, run it: `fd run <name> --var key=value` and you are done.
2. **No chain:** look ONCE at each window you need: `fd windows`, then `fd view "<title part>"` (prints
   `role | name | value` for every element). Start the app first with a one-step chain (`{"open": "C:/path/app.exe"}`) if it
   is not open.
3. **Write the whole chain** as a JSON file in a scratch folder and run it: `fd run <file>.json`. Put `wait` steps where a
   new window opens, so you never need to look again mid-chain.
4. **A step failed?** The output shows the failing step, the error, all window titles and the current window's elements.
   Fix only that step and rerun from there (a chain file holding the remaining steps). Do not re-check steps that worked.
5. **It worked:** save the chain as `chains/<app>-<task>.json` with an `"about"` line and `{vars}` for anything that
   changes, so next time step 1 runs it with no model at all.

## Step reference

A chain is a JSON list of steps, or `{"about": "...", "steps": [...]}`. Every step may add `"window": "<title part>"`
(default: the last window used) and `"optional": true`.
- `{"open": "C:/path/app.exe"}` starts the app, or shows it from the system tray
- `{"wait": "<title part>", "timeout": 15}`; add `"new": true` to ignore windows that were already open (for example an old
  progress window with the same title); `{"wait_gone": "<title part>"}`
- `{"click": "<name>", "role": "button"}` (exact name first, then contains); unnamed: `{"click": null, "role": "button", "index": 0}`
- `{"set": "<name>|null", "role": "textfield", "index": 0, "value": "{var}"}`
- `{"toggle": "<name>", "role": "checkbox"}`, `{"menu": ["<top menu>", "<item>"]}`
- `{"read": "<regex>"}` returns the window's texts (the run's `results`)
- `{"hide": "<title part>", "button": "<name>"}` presses a title-bar button that hides the window
- `{"minimize_all_except": ["Notepad"]}`, `{"restore"|"minimize"|"close": "<title part>"}`, `{"sleep": 0.5}`
- `{var}` in any string is replaced from `--var key=value`.

Roles: button, textfield, checkbox, radio, option (list item), listitem, combobox, menuitem, menubutton, tab, tabitem,
statictext, text, link, treeitem, document, group, window.

## Rules

- Never type into, click in, minimize or close the window of your own agent app. Target windows by title.
- Window size and position do not matter. Renamed buttons (an app update, a UI language change) or an unexpected dialog
  break a chain: fix the step and save the chain again.
- Copy element names exactly from `fd view` output, including special letters in non-English interfaces.
- A classic Win32 menu opens only when its app is in front; prefer toolbar buttons or dialogs.
- Clicking a list row runs its default action (an app may open a properties dialog); close it, the row stays selected.
  Press toolbar buttons by index only when the order is known.
- Elevated (administrator) windows cannot be driven from a normal process; report them.
- Do not download files or press buttons that spend money, send messages or delete data unless the task says so.
