// Render video without audio in the browser, then mux the narration with ffmpeg at the exact scene offsets.
// Env: VIDEO (folder src/<VIDEO>/ with timing.json, default "video"), COMP (composition id, default "Video"),
// CHROME (path of chrome.exe), PARTS / MAXPAR / CONC (parallel chunks), PORT (bundler port, see SKILL.md).
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { execFileSync } from "child_process";
import fs from "fs";
import path from "path";

const FPS = 30, LEAD = 0.5, TAIL = 0.9, FADE = 15;
const NAME = process.env.VIDEO ?? "video";
const COMP = process.env.COMP ?? "Video";
const out = path.resolve(process.argv[2] ?? `out/${NAME}.mp4`);
const timing = JSON.parse(fs.readFileSync(`src/${NAME}/timing.json`, "utf-8"));
const browserExecutable = process.env.CHROME ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const inputProps = { noAudio: true };
// Chrome draws with ANGLE; ffmpeg may encode with NVENC (hardwareAcceleration "if-possible"). Set NOHW=1 to force software.
const chromiumOptions = { gl: "angle" };
fs.mkdirSync("out", { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), ...(process.env.PORT ? { port: Number(process.env.PORT) } : {}) });
const composition = await selectComposition({ serveUrl, id: COMP, inputProps, browserExecutable, chromiumOptions, chromeMode: "chrome-for-testing", timeoutInMilliseconds: 180000 });
const silent = path.resolve("out/_silent.mp4");
// One Chrome renders all tabs in a single renderer process, so concurrency inside one
// renderMedia call stalls at ~15% CPU. Split the frames into PARTS ranges, each with its own
// browser (real parallelism), then join the chunks without re-encoding.
const PARTS = Number(process.env.PARTS ?? 6);
const N = composition.durationInFrames;
const size = Math.ceil(N / PARTS);
const MAXPAR = Number(process.env.MAXPAR ?? 4); // browsers at once (each ~1 GB RAM; too many swaps a 16 GB machine)
const done = new Array(PARTS).fill(0);
let last = 0;
const chunks = Array.from({ length: PARTS }, (_, k) => path.resolve(`out/_part${k}.mp4`));
const queue = chunks.map((_, k) => k).filter((k) => !fs.existsSync(chunks[k] + ".ok")); // finished chunks are reused
const N0 = N - (PARTS - queue.length) * size;
const renderPart = async (k) => {
  const from = k * size, to = Math.min(N, (k + 1) * size) - 1;
  const tmp = chunks[k].replace(".mp4", ".tmp.mp4");
  await renderMedia({
    composition, serveUrl, inputProps, browserExecutable, chromiumOptions, chromeMode: "chrome-for-testing",
    codec: "h264", videoBitrate: "12M", hardwareAcceleration: process.env.NOHW ? "disable" : "if-possible", muted: true,
    outputLocation: tmp, frameRange: [from, to], timeoutInMilliseconds: 180000, concurrency: Number(process.env.CONC ?? 2),
    onProgress: ({ progress }) => {
      done[k] = progress * (to - from + 1);
      const p = Math.floor((done.reduce((a, b) => a + b, 0) / N0) * 100);
      if (p >= last + 5) { last = p; console.log(`render ${p}%`); }
    },
  });
  fs.renameSync(tmp, chunks[k]);
  fs.writeFileSync(chunks[k] + ".ok", "");
  console.log(`part ${k} done`);
};
await Promise.all(Array.from({ length: Math.min(MAXPAR, queue.length) }, async () => {
  while (queue.length) await renderPart(queue.shift());
}));
const list = path.resolve("out/_parts.txt");
fs.writeFileSync(list, chunks.map((f) => `file '${f.split(path.sep).join("/")}'`).join("\n"));
execFileSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", silent], { stdio: "inherit" });
chunks.forEach((f) => { fs.unlinkSync(f); fs.unlinkSync(f + ".ok"); });
fs.unlinkSync(list);
// audio offsets
let start = 0;
const args = ["-y", "-i", silent];
const filters = [];
timing.forEach((t, i) => {
  args.push("-i", path.resolve("public", t.audio));
  const ms = Math.round((start / FPS + LEAD) * 1000);
  filters.push(`[${i + 1}:a]adelay=${ms}|${ms}[a${i}]`);
  start += Math.ceil((LEAD + t.duration + TAIL) * FPS) - FADE;
});
filters.push(`${timing.map((_, i) => `[a${i}]`).join("")}amix=inputs=${timing.length}:normalize=0[aout]`);
// Final encode: x264 CRF 28 (flat motion graphics). The chunks are 12 Mbps (about 1.2 GB for 27 min);
// this re-encode brings it to about 65 MB with no visible loss.
args.push("-filter_complex", filters.join(";"), "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-tune", "animation", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k", "-ar", "48000", "-shortest", out);
execFileSync("ffmpeg", ["-v", "error", ...args], { stdio: "inherit" });
fs.unlinkSync(silent);
console.log("done", out);
