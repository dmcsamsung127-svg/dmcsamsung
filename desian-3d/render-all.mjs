// 전 호실 일괄 렌더링: node desian-3d/render-all.mjs
//   units-all.json(평면안내 면적표 OCR + 층별 코너/테라스 규칙)에
//   index.html의 UNITS(매물장 옵션·연속 호실)를 덮어써서
//   desian-3d/out/<호실>/<호실>.jpg 로 저장
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let pw;
try { pw = require("playwright"); }
catch { pw = require(join(execSync("npm root -g").toString().trim(), "playwright")); }

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.argv[2] || join(here, "out");
const all = JSON.parse(readFileSync(join(here, "units-all.json"), "utf8"));

const browser = await pw.chromium.launch();
const page = await browser.newPage({ viewport: { width: 1110, height: 900 }, deviceScaleFactor: 1.5 });
await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
await page.goto(pathToFileURL(join(here, "index.html")).href + "?export");
await page.evaluate(() => document.fonts.ready);

const units = await page.evaluate(all => {
  const byId = new Map(all.map(u => [u.id, u]));
  UNITS.forEach(u => byId.set(u.id, { ...byId.get(u.id), ...u }));   // 매물장 정보 우선
  return [...byId.values()].map(u => u.id);
}, all);

let n = 0;
for (const id of units) {
  await page.evaluate(({ id, all }) => {
    const u = UNITS.find(x => x.id === id) || { ...all.find(x => x.id === id) };
    const st = { sink: !!u.sink, blind: !!u.blind, curtain: !!u.curtain, clean: true,
                 balcony: !u.id.startsWith("FB") && !u.terrace && !u.noWin };
    document.getElementById("grid").innerHTML = `<div class="sheet" id="one">${renderUnit(u, st)}</div>`;
  }, { id, all });
  mkdirSync(join(outDir, id), { recursive: true });
  await (await page.$("#one")).screenshot({ path: join(outDir, id, `${id}.jpg`), type: "jpeg", quality: 90 });
  if (++n % 100 === 0) console.log(n, "/", units.length);
}
console.log("done", n);
await browser.close();
