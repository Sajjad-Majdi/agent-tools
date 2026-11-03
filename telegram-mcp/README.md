# Telegram MCP + CLI

An MCP server and CLI for a personal Telegram account. The agent can read and search messages, send text, files and voice,
and press bot buttons. Written in Node.js.

## What it gives an agent

15 tools, also available as `tg` commands: list chats, read history, search, unread messages, download media, mark read, send
text, send files (videos get real duration and a preview, photos, audio, voice notes, documents), forward, edit own messages,
press inline and keyboard buttons of bots, chat folders and archive. There is no delete tool on purpose.

## How it works

One background daemon holds the single Telegram connection of the computer (GramJS); the MCP server (`server.mjs`) and the
CLI (`tg.mjs`) are thin clients that talk to it on `127.0.0.1` with a local key. This avoids the main failure of personal
Telegram automation: two clients on one login from different IPs make Telegram revoke it (AUTH_KEY_DUPLICATED).

- All API calls go through one queue, at least 1.1 s apart, sends 3 s apart; FLOOD_WAIT is respected.
- Every tool call has a hard deadline; a send that times out says the message may have been sent.
- A watchdog replaces a connection that GramJS leaves half dead.
- Any client starts the daemon on demand (hidden); a second daemon sees the port taken and exits.

## Requirements

Windows (the launchers are `.cmd` and `.vbs`; the Node code itself is portable), Node.js 18+, and your own Telegram API
credentials: log in at <https://my.telegram.org>, open "API development tools" and create an app to get `api_id` and
`api_hash`. Video sending also needs `ffmpeg` and `ffprobe` on PATH. The login (phone number, code, two-step password) is
typed by the account owner in their own terminal; an agent must never ask for those in chat.

If Telegram is blocked on your network, `relay/worker.js` is an optional Cloudflare Worker that forwards the MTProto
WebSocket; put its host and secret in `config.json` (`relayHost`, `relaySecret`) and the client uses it instead of a direct
connection.

## Install prompt

```text
Install "Telegram MCP + CLI" for me. It gives AI agents my personal Telegram account through one local background daemon, an MCP server and a tg command. Project: https://github.com/Sajjad-Majdi/agent-tools (folder telegram-mcp).

Requirements: Node.js 18 or newer with npm. Optional: ffmpeg and ffprobe on PATH (needed only to send videos and voice notes). Check them first and tell me what is missing instead of guessing. I need my own Telegram api_id and api_hash from https://my.telegram.org (API development tools); I will create them myself.

Steps:
1. Download https://github.com/Sajjad-Majdi/agent-tools/archive/refs/heads/main.zip into a temp folder and extract it. Download nothing else without asking me. If github.com is blocked on my network, tell me and ask which mirror or proxy to use.
2. Copy the folder telegram-mcp (without its skill subfolder) to %USERPROFILE%\.tg-mcp and run npm install --omit=dev there (if the npm registry is slow or blocked for me, ask for a mirror and use npm's --registry option).
3. Copy config.example.json to config.json in that folder. Tell me to put my api_id and api_hash into it myself; do not ask me to paste them in the chat and do not print them. Leave relayHost and relaySecret empty unless I tell you Telegram is blocked for me.
4. Run npm run check in that folder. These checks are offline (they never contact Telegram); they must all pass.
5. Tell me to open my own terminal in %USERPROFILE%\.tg-mcp and run node login.mjs, and to type my phone number, the code Telegram sends and my two-step password there myself. Wait until I say it is done. Never ask me for these values.
6. Register the MCP server under the name tg: for Claude Code run claude mcp add --scope user tg -- node "%USERPROFILE%\.tg-mcp\server.mjs"; for Codex add [mcp_servers.tg] with command "node" and args ["%USERPROFILE%\\.tg-mcp\\server.mjs"] to %USERPROFILE%\.codex\config.toml; for another agent use its MCP configuration with the same command and arguments. Tell me the agent has to be restarted to see the new tools.
7. Install the skill: copy telegram-mcp/skill/SKILL.md to <skills folder>\telegram-cli\SKILL.md for every one of these folders that exists: %USERPROFILE%\.claude\skills, %USERPROFILE%\.agents\skills, %USERPROFILE%\.codex\skills. If none exists, create %USERPROFILE%\.claude\skills and tell me which agents will see it.
8. Ask me whether to add %USERPROFILE%\.tg-mcp to my user PATH, so that the tg command (tg.cmd) works in any shell, and whether the daemon should start at login (a shortcut to start-daemon.vbs in my Startup folder). Do each only if I say yes.
9. Smoke test: run tg status (JSON with the daemon state; loggedIn must be true after step 5), then tg dialogs --limit 3 --compact. These only read.

Safety: never send, forward, edit or press a button toward other people without my explicit approval of that exact message. Never delete anything. Never print or copy config.json, session.txt or daemon.key.
```

## Files

| Path | What |
|---|---|
| `daemon.mjs`, `src/core.mjs` | The daemon and all tools |
| `server.mjs` | Stdio MCP server (forwards to the daemon) |
| `tg.mjs`, `tg.cmd` | The CLI |
| `login.mjs`, `login.cmd` | One-time interactive login |
| `start-daemon.vbs` | Hidden launcher for the Startup folder |
| `relay/worker.js` | Optional Cloudflare Worker relay |
| `scripts/` | Offline checks (`npm run check`) and an MCP client check |
| `skill/SKILL.md` | Agent skill |

`config.json`, `session.txt` and `daemon.key` are secrets and are ignored by git.
