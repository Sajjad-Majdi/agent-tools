// tg-mcp daemon: the one process on this PC that holds the user's Telegram connection (src/core.mjs).
// Clients (server.mjs for Claude/MCP, tg.mjs CLI for every other agent and script) talk to it on 127.0.0.1:PORT with the
// key in daemon.key. Start hidden at login (start-daemon.vbs); any client also starts it on demand. Logs: logs/daemon.log.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { ROOT } from "./src/tg.mjs";
import { ensureKey, PORT } from "./src/client.mjs";

// ---------- file log (never secrets: tool names, timings, errors, GramJS warnings) ----------
const LOGS = path.join(ROOT, "logs");
const LOG = path.join(LOGS, "daemon.log");
const LOG_MAX = 2 * 1024 * 1024;
fs.mkdirSync(LOGS, { recursive: true });
const stamp = new Intl.DateTimeFormat("sv-SE", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }); // local time
function writeLog(line) {
  try {
    if (fs.existsSync(LOG) && fs.statSync(LOG).size > LOG_MAX) fs.renameSync(LOG, LOG + ".1"); // keep one old file
    fs.appendFileSync(LOG, `${stamp.format(new Date())} ${line}\n`);
  } catch {}
}
const fmtArgs = (a) => a.map((x) => (x instanceof Error ? x.stack || x.message : typeof x === "string" ? x : (() => { try { return JSON.stringify(x); } catch { return String(x); } })())).join(" ");
console.log = console.info = console.debug = (...a) => writeLog("[stdout] " + fmtArgs(a)); // GramJS prints some errors with console.*
console.error = console.warn = (...a) => writeLog("[stderr] " + fmtArgs(a));
process.on("uncaughtException", (e) => writeLog("[uncaught] " + (e?.stack || e)));
process.on("unhandledRejection", (e) => writeLog("[unhandled] " + (e?.stack || e)));

const KEY = ensureKey();
const ORIGIN = `http://127.0.0.1:${PORT}`;
const core = await import("./src/core.mjs");
core.setLogger(writeLog);

function send(res, status, obj) {
  res.writeHead(status, { "content-type": "application/json" }).end(JSON.stringify(obj));
}

let stopping = false;
async function onRequest(req, res) {
  const url = new URL(req.url, ORIGIN);
  if (req.headers["x-tg-key"] !== KEY) return send(res, 401, { ok: false, error: "bad key" });
  if (req.method === "GET" && req.url === "/health") return send(res, 200, { ok: true, role: "daemon", ...core.status() });
  if (req.method !== "POST") return send(res, 404, { ok: false, error: "not found" });
  let body = "";
  req.setEncoding("utf8");
  for await (const d of req) body += d;
  try {
    if (req.url === "/call") {
      const { tool, args } = JSON.parse(body || "{}");
      return send(res, 200, await core.runTool(tool, args || {}));
    }
    if (req.url === "/pause") {
      await core.pause();
      return send(res, 200, { ok: true, ...core.status() });
    }
    if (req.url === "/resume") {
      core.resume("resume requested");
      return send(res, 200, { ok: true, ...core.status() });
    }
    if (req.url === "/stop") {
      send(res, 200, { ok: true, stopping: true });
      return bye("stop requested");
    }
    send(res, 404, { ok: false, error: "not found" });
  } catch (e) {
    send(res, 200, { ok: false, error: String(e?.message || e), code: "ERROR" });
  }
}

const srv = http.createServer(onRequest);
srv.on("error", (e) => {
  if (e.code === "EADDRINUSE") {
    writeLog(`another daemon owns 127.0.0.1:${PORT}; this copy (pid ${process.pid}) exits`);
    process.exit(0);
  }
  writeLog("listen error: " + e.message);
  process.exit(1);
});
srv.listen(PORT, "127.0.0.1", () => {
  writeLog(`daemon ${core.VERSION} up on 127.0.0.1:${PORT} (pid ${process.pid}, node ${process.version})`);
  core.init();
});

async function bye(why) {
  if (stopping) return;
  stopping = true;
  writeLog(`stopping (${why})`);
  srv.close();
  try {
    await Promise.race([core.shutdown(), new Promise((r) => setTimeout(r, 4000))]); // Telegram socket closed before the port is freed
  } catch {}
  writeLog("stopped");
  process.exit(0);
}
process.on("SIGTERM", () => bye("SIGTERM"));
process.on("SIGINT", () => bye("SIGINT"));
process.on("SIGHUP", () => bye("SIGHUP"));
