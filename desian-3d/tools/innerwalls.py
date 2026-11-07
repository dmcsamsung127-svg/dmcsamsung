# 호실 안쪽 면 사이 거리(안목치수): 칸 중심에서 좌우·상하로 가장 가까운 긴 벽선까지
import json, collections, gridsnap as g
_lines = {}
def lines(pno):
    if pno in _lines: return _lines[pno]
    V, H = [], []
    for dr in g.d[pno].get_drawings():
        col = dr.get('color')
        if col and max(col) > 0.15: continue
        for it in dr['items']:
            if it[0] != 'l': continue
            a, b = it[1], it[2]
            if abs(a.x-b.x) < 0.05: V.append((a.x, min(a.y,b.y), max(a.y,b.y)))
            elif abs(a.y-b.y) < 0.05: H.append((a.y, min(a.x,b.x), max(a.x,b.x)))
    _lines[pno] = (V, H); return V, H
def inner(v):
    L, T, R, B = v['box']; cx, cy = (L+R)/2, (T+B)/2
    V, H = lines(v['page'])
    def cover(segs, lo, hi):
        acc = collections.defaultdict(float)
        for p, a, b in segs:
            ov = min(b, hi) - max(a, lo)
            if ov > 0: acc[round(p, 2)] += ov
        return acc
    vx = cover(V, T, B); hy = cover(H, L, R)
    need_x = 0.45*(B-T); need_y = 0.45*(R-L)
    left = max([x for x, l in vx.items() if l >= need_x and x < cx - 0.5/g.K], default=None)
    right = min([x for x, l in vx.items() if l >= need_x and x > cx + 0.5/g.K], default=None)
    top = max([y for y, l in hy.items() if l >= need_y and y < cy - 0.5/g.K], default=None)
    bot = min([y for y, l in hy.items() if l >= need_y and y > cy + 0.5/g.K], default=None)
    if None in (left, right, top, bot): return None
    return (right-left)*g.K, (bot-top)*g.K
