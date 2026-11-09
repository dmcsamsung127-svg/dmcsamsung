import { createRequire } from "node:module"; import { execSync } from "node:child_process";
import { readFileSync } from "node:fs"; import { join } from "node:path"; import { pathToFileURL } from "node:url";
const require = createRequire(import.meta.url);
const pw = require(join(execSync("npm root -g").toString().trim(), "playwright"));
const here="/home/user/dmcsamsung/desian-3d"; const all=JSON.parse(readFileSync(join(here,"units-all.json"),"utf8"));
const crops=JSON.parse(readFileSync(process.argv[3],"utf8"));
const b=await pw.chromium.launch(); const p=await b.newPage({viewport:{width:1300,height:800}});
await p.route(/fonts\.(googleapis|gstatic)\.com/, r=>r.abort());
await p.goto(pathToFileURL(join(here,"index.html")).href+"?export");
await p.evaluate(({crops,all})=>{ document.body.innerHTML=crops.map(([id,img,rot,mir])=>{
  const u={...all.find(x=>x.id===id),...UNITS.find(x=>x.id===id)};
  const st={sink:false,blind:false,curtain:false,clean:true,balcony:!u.id.startsWith("FB")&&!u.noWin&&!/^C\d/.test(u.id)};
  return `<div style="display:flex;align-items:center;gap:10px;border-bottom:1px solid #ccc;font:16px sans-serif"><b style="width:70px">${id}</b>
  <div style="width:580px;height:580px;display:flex;align-items:center;justify-content:center"><img src="data:image/png;base64,${img}" style="max-width:560px;max-height:560px;transform:${mir?'scaleX(-1) ':''}rotate(${rot}deg)"></div>
  <div style="width:600px"><pre style="font:11px monospace;white-space:pre-wrap">${JSON.stringify({w:u.w,d:u.d,doorX:u.doorX,balBack:u.balBack,balLeft:u.balLeft,cols:u.cols,park:u.drive&&!u.noPark?(u.parkN||"auto"):0,mirror:u.mirror})}</pre>${renderUnit(u,st)}</div></div>`}).join("");
  document.querySelectorAll("svg").forEach(s=>{s.style.width="580px";s.style.height="auto"});},{crops,all});
await p.screenshot({path:process.argv[2],fullPage:true}); await b.close();
