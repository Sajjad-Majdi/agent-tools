---
name: telegram-cli
description: The user's own Telegram account through the local `tg` command (any shell) or the `tg` MCP tools. Use it for every Telegram task - reading chats, unread messages, searching, downloading media, sending text, files, photos, videos or voice notes, forwarding, editing, pressing bot buttons, archiving chats, or testing the user's Telegram bots. Prefer it over browser Telegram Web or any other Telegram route.
---

# Telegram through `tg`

`tg` is a small CLI on PATH. It talks to one background daemon that holds the only Telegram connection of this computer
(`tg-mcp`, install folder `%USERPROFILE%\.tg-mcp`). The same daemon serves the `tg` MCP tools. Output is JSON; the exit
code is 1 on any error, with `{"ok":false,"error":...}`.

## Why only this route
Telegram revokes a login (AUTH_KEY_DUPLICATED) when the same session connects twice from different IPs, and then the user
has to log in again. So:
- Use `tg` (or the `tg` MCP tools, which call the same daemon). Never write a script that opens its own Telegram client on
  `session.txt`, and never copy the session anywhere.
- If a call says the account owner must log in again, tell the user to run `node login.mjs` in the install folder. Only
  the user types their phone number, code and two-step password.

## Commands
```
tg status                                     daemon + connection state
tg dialogs [query] [--limit 30] [--unread] [--type user|bot|group|channel] [--all] [--refresh]
tg history <chat> [--limit 30] [--offset-id N] [--min-id N] [--since 2026-10-01] [--oldest-first]
tg search <text> [--chat c] [--limit 20] [--since d]
tg unread [--max-chats 20] [--per-chat 10] [--muted]
tg download <chat> <message_id> [--dir folder]
tg read <chat> [--max-id N]                   mark as read
tg send <chat> <text...> [--reply-to N]
tg send-file <chat> <path> [--caption "..."] [--as auto|photo|document|video|audio|voice] [--reply-to N]
tg forward <from_chat> <id[,id...]> <to_chat> [--copy]
tg edit <chat> <message_id> <text...>         own messages only
tg buttons <chat> <message_id>                list the buttons under a message
tg press <chat> <message_id> <button>         button text, a unique part of it, "row,col" or an index
tg archive <chat> | tg unarchive <chat>
tg folders | tg folder <name> <chat,chat,...> | tg folder-remove <name>   chat folders: 100 chats each, more = the name with a number suffix
tg log [--n 40]   tg restart                  daemon log / restart
```
Global flags: `--compact` (one-line JSON, just the data) and `--ascii` (see below).
`<chat>` = numeric id from `tg dialogs`, `@username`, a t.me link, `me` (Saved Messages) or part of a chat title.

## Rules
- Sending, forwarding, editing and pressing buttons toward other people needs the user's OK for that exact message.
  Without asking you may only target `me` (Saved Messages) and the user's own bots.
- Never delete chats or messages; archive a chat instead (`tg archive`). The user deletes things themselves in the
  Telegram app.
- Calls are throttled on purpose (about 1 call per second, sends 3 s apart) so the account behaves like a calm human
  client. Do not loop fast over many chats; `tg unread` already batches.
- A send that times out "MAY have been sent": read the chat with `tg history` before any retry, or it lands twice.

## Sending files
`tg send-file` prepares the file so it arrives right:
- Video: real duration, width/height and a preview frame; remuxed to a streamable mp4, or converted to H.264/AAC when
  Telegram could not play it (webm, vp9, av1 ...). The result lists what was done (`prepared`). Needs `ffmpeg` and
  `ffprobe` on PATH.
- `.jpg`/`.png`: sent as a photo (if Telegram refuses it, it is resent as a file). Use `--as document` to keep full quality.
- Music: sent with its duration and title. `--as voice` turns any audio into a voice note.
- Everything else (markdown, PDF, zip, code): a document with its file name.
- A caption over 1024 characters follows as a reply message. Text supports `**bold**`, `__italic__`, `` `code` ``.
- Uploads run at the computer's upload speed: a 10 MB file can take minutes on a slow line.

## Reading output in PowerShell
Use `ConvertFrom-Json`:
```powershell
$m = tg history '@somebot' --limit 5 --compact | ConvertFrom-Json
$m | ForEach-Object { "[$($_.id)] $($_.text)" }
```
Windows PowerShell 5.1 with a non-UTF-8 console code page turns non-Latin text into garbage. If text looks broken, add
`--ascii` (or set `$env:TG_ASCII = "1"`): the JSON then uses `\uXXXX` escapes and `ConvertFrom-Json` restores the text
exactly. Quote `@username` in PowerShell (`'@name'`), because a bare `@` starts a splat.

Messages carry `buttons` (rows of button texts) when they have a keyboard, and `media` with `type`, `size`, `sec`, `w`,
`h`, `preview`, `name`.

## Testing one of the user's bots
1. `tg send @thebot <link or command> --compact` and keep the returned `id`.
2. Wait a few seconds, then `tg history @thebot --min-id <id> --oldest-first --compact` for the replies.
3. `tg buttons @thebot <reply_id>`, then `tg press @thebot <reply_id> "720p"` to tap one; read the history again. A bot may
   delete or edit its menu message after the tap.

## When something fails
- `tg status`: `connected`, `dead` (login revoked: the user runs `node login.mjs`), `floodUntil` (Telegram asked us to wait;
  wait, do not retry).
- `tg log --n 40` shows every call with its time and error.
- "daemon is not running": any `tg` call starts it; `tg restart` if it seems stuck.
