// Usage: node scripts/beats.mjs <sceneId> [videoName]  -> prints each sentence's start frame (30fps) and text
// videoName defaults to env VIDEO or "video" (the folder src/<videoName>/ that holds timing.json).
import fs from "fs";
const NAME = process.argv[3] || process.env.VIDEO || "video";
const t = JSON.parse(fs.readFileSync(`src/${NAME}/timing.json`, "utf-8")).find((s) => s.id === process.argv[2]);
const LEAD = 0.5, TAIL = 0.9;
console.log(`scene ${t.id}: ${Math.ceil((LEAD + t.duration + TAIL) * 30)} frames`);
t.beats.forEach((b, i) => console.log(`beat ${i} @ frame ${Math.round((b + LEAD) * 30)}: ${t.sentences[i]}`));
