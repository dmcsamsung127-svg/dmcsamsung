// 사용법: node desian-3d/render-png.mjs  →  desian-3d/png/<호실>.png
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let pw;
try { pw = require("playwright"); }
catch { pw = require(join(execSync("npm root -g").toString().trim(), "playwright")); }

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "png");
mkdirSync(outDir, { recursive: true });

const browser = await pw.chromium.launch();
const page = await browser.newPage({ viewport: { width: 1110, height: 900 }, deviceScaleFactor: 1.5 });
// 외부 폰트 요청은 막고 로컬 설치된 Noto Sans KR 사용
await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
await page.goto(pathToFileURL(join(here, "index.html")).href + "?export");
await page.evaluate(() => document.fonts.ready);
const sheets = await page.$$(".sheet");
for (const s of sheets) {
  const id = (await s.getAttribute("id")).replace(/^sheet-/, "");
  await s.screenshot({ path: join(outDir, `${id}.png`) });
  console.log("saved", id);
}
await browser.close();
