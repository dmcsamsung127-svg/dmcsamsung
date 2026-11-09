# 호실별 실제 기둥 위치: 도면의 0.5~1.1m 정사각 기둥 기호를 찾아, 출입문 쪽에서 바라본 3D 좌표(x: 왼→오, y: 안쪽 벽=0 → 출입문 벽=D)로 변환
import json, re, gridsnap as g, doorside as ds
_cols = {}
def columns(pno):
    if pno in _cols: return _cols[pno]
    out = []
    for dr in g.d[pno].get_drawings():
        col = dr.get('color')
        if col and max(col) > 0.15: continue
        for it in dr['items']:
            if it[0] == 're': r = it[1]
            elif it[0] == 'qu': r = it[1].rect
            else: continue
            wm, hm = r.width*g.K, r.height*g.K
            if 0.55 <= min(wm, hm) <= 1.0 and max(wm, hm) <= 2.2:   # 기둥(정사각 0.8m, 벽기둥 0.8×1.2~2.1m)
                out.append(((r.x0+r.x1)/2, (r.y0+r.y1)/2, wm, hm))
    # 같은 기둥이 겹쳐 그려진 경우 합침
    merged = []
    for c in out:
        if not any(abs(c[0]-m[0]) < 0.4/g.K and abs(c[1]-m[1]) < 0.4/g.K for m in merged): merged.append(c)
    _cols[pno] = merged; return merged
def unit_cols(v, door_len):
    pno = v['page']; L, T, R, B = v['box']
    ex = 0.7/g.K
    cs = [c for c in columns(pno) if L-ex <= c[0] <= R+ex and T-ex <= c[1] <= B+ex]
    horiz = abs((R-L)*g.K - door_len) <= abs((B-T)*g.K - door_len)   # 문벽이 x방향(상/하 변)인가
    _, cnt = ds.door_edge(pno, (L, T, R, B))
    if horiz:  side = 'B' if cnt['B'] >= cnt['T'] else 'T'
    else:      side = 'R' if cnt['R'] >= cnt['L'] else 'L'
    res = []
    for X, Y, wm, hm in cs:
        if side == 'B': x, y = X-L, Y-T
        elif side == 'T': x, y = R-X, B-Y
        elif side == 'L': x, y = Y-T, R-X
        else: x, y = B-Y, X-L
        sx, sy = (wm, hm) if side in 'TB' else (hm, wm)
        res.append([round(x*g.K-0.1, 2), round(y*g.K-0.1, 2), round(sx, 2), round(sy, 2)])
    return side, res
if __name__ == '__main__':
    m = json.load(open('m5_all.json'))
    a = {u['id']: u for u in json.load(open('/home/user/dmcsamsung/desian-3d/units-all.json'))}
    import sys
    for k in sys.argv[1:]:
        u = a[k]; ref = k
        mm = re.search(r'\((\w+)\)', u.get('dimSrc', ''))
        if mm: ref = mm.group(1)
        print(k, u['w'], u['d'], unit_cols(m[ref], u['w']+0.2))
