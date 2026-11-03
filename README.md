# agent-tools

Six tools and skills for AI coding agents (Claude Code, Codex and others). Each folder holds the source, the agent skill
(`SKILL.md`) and a README with an install prompt: paste that prompt into your own agent and it downloads, installs, sets up
and tests the tool for you.

| Folder | What it is | Written in |
|---|---|---|
| [`browser-bridge`](browser-bridge) | Lets an agent open the user's Chrome tabs, read pages, do real clicks and typing and take screenshots | Rust (relay), JavaScript (Chrome extension), Python (client) |
| [`fastdesk`](fastdesk) | Lets an agent control Windows apps. Runs a chain of clicks, typing and window reads through UI Automation and replays saved chains | Python |
| [`telegram-mcp`](telegram-mcp) | An MCP server and CLI for a personal Telegram account: read and search messages, send text, files and voice, press bot buttons | Node.js |
| [`idm-cli`](idm-cli) | A CLI that controls Internet Download Manager without opening its window, plus a skill for big downloads | C# |
| [`persian-word`](persian-word) | A skill for creating and editing Persian Word files with correct right-to-left layout | Python |
| [`persian-video`](persian-video) | A skill for making narrated explainer and promo videos with Remotion, with Persian voice-over | TypeScript and React, Node.js, Python |

## How to use

1. Open the README of the tool you want and copy its "Install prompt".
2. Paste it into your coding agent. The agent checks the requirements, downloads from this repository and its release,
   installs the tool, puts the skill into the skills folder of your agent (`.claude/skills`, `.agents/skills` or
   `.codex/skills`), registers the MCP server where there is one, and runs a smoke test.
3. Some steps stay with you on purpose: loading the Chrome extension, logging in to Telegram, creating the IDM queue.

The tools are tested on Windows 10 and 11 and most of them work only there. Binaries (`bb.exe`, `idm.exe`) are attached to the
[release](https://github.com/Sajjad-Majdi/agent-tools/releases/latest) together with their SHA-256 sums; both can be built
from the source in this repository.

## Notes

- Nothing here contains secrets. Tokens, keys and sessions are generated or entered on your own machine and are ignored by
  git (`token.txt`, `config.js`, `config.json`, `session.txt`, `daemon.key`).
- If github.com or the package registries are blocked on your network, tell your agent which mirror or proxy to use; the
  install prompts ask before using anything other than this repository.
- The skills describe mistakes that were made while using the tools, written as general advice.
