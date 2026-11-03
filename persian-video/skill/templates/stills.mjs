// Usage: node scripts/stills.mjs <outDir> <entry.tsx> <compId:frame> [...]
// Renders PNG stills (half size) with system Chrome. Audio is off.
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import fs from "fs";
import path from "path";
const [out, entry, ...list] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
// Remotion's own Chrome download can be unreachable on some networks; point CHROME at an installed Chrome instead.
const browserExecutable = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const inputProps = { noAudio: true };
const serveUrl = await bundle({ entryPoint: path.resolve(entry) });
for (const item of list) {
  const [id, frame] = item.split(":");
  const composition = await selectComposition({ serveUrl, id, inputProps, browserExecutable, chromeMode: "chrome-for-testing" });
  const file = path.join(out, `${id}-${frame}.png`);
  await renderStill({ composition, serveUrl, output: file, frame: Number(frame), scale: 0.5, inputProps, browserExecutable, chromeMode: "chrome-for-testing" });
  console.log("ok", file);
}
