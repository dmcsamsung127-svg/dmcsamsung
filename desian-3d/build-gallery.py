# units-all.json을 index.html의 ALL 자리에 넣는다: python3 desian-3d/build-gallery.py
import json, re, pathlib
here = pathlib.Path(__file__).parent
data = json.load(open(here/'units-all.json'))
keep = ('id','area','w','d','corner','terrace','noWin','drive','updated','dimSrc','door','doorH')
slim = [{k: u[k] for k in keep if k in u} for u in data]
p = here/'index.html'; s = p.read_text()
s = re.sub(r'/\*ALL_START\*/.*?/\*ALL_END\*/', lambda m: '/*ALL_START*/' + json.dumps(slim, ensure_ascii=False, separators=(',', ':')) + '/*ALL_END*/', s, flags=re.S)
# 매물 카드의 w·d도 전 호실 데이터와 맞춤
by = {u['id']: u for u in data}
def fix(m):
    u = by.get(m.group(1))
    return f'{{ id: "{m.group(1)}", w: {u["w"]}, d: {u["d"]},' if u and 'w' in u else m.group(0)
s = re.sub(r'\{ id: "((?:KA|KB|FB|F|C)\d+)", w: [\d.]+, d: [\d.]+,', fix, s)
p.write_text(s); print('ALL', len(slim), 'bytes', len(s))
