# 그리드 기준 치수: 호실 벽(안쪽면+0.1m=벽중심)을 가장 가까운 그리드선·그리드 분할점(1/2, 1/3)에 맞춘 뒤 0.2m를 뺌
import pymupdf as fitz, json, sys
PDF='/root/.claude/uploads/a7808b39-5d40-548d-9bd9-112abfa52580/8ef16fdf-9___________.pdf'
K = 25.4/72*800/1000          # m/pt (A3, 1/800) — 그리드 10,800 간격(38.28pt)으로 확인
d = fitz.open(PDF)
_grid = {}
RAW = {}
def grids(pno):
    if pno in _grid: return _grid[pno]
    p = d[pno]; xs=set(); ys=set()
    for dr in p.get_drawings():
        col = dr.get('color')
        if not col or abs(col[0]-0.302) > 0.03 or abs(col[1]-col[0]) > 0.01: continue   # 기둥 그리드선(진회색 0.3)만
        for it in dr['items']:
            if it[0] != 'l': continue
            a, b = it[1], it[2]
            if abs(a.x-b.x) < 0.05 and abs(a.y-b.y) > 100: xs.add(round(a.x, 2))
            if abs(a.y-b.y) < 0.05 and abs(a.x-b.x) > 100: ys.add(round(a.y, 2))
    def merge(v):
        v = sorted(v); out=[]
        for x in v:
            if out and x-out[-1] < 1.0: out[-1] = (out[-1]+x)/2
            else: out.append(x)
        return out
    def pts(lines):
        c = set(lines)
        for a, b in zip(lines, lines[1:]):
            span = (b-a)*K
            if 2.0 < span < 12.5:                       # 실제 기둥 간격만
                for f in (1/2, 1/3, 2/3): c.add(a + (b-a)*f)
        return sorted(c)
    RAW[pno] = (merge(xs), merge(ys))
    _grid[pno] = (pts(merge(xs)), pts(merge(ys)))
    return _grid[pno]
TOL = 0.5/K; WALL_HALF = 0.1/K
def snap(v, cands):
    c = min(cands, key=lambda g: abs(g-v)) if cands else v
    return (c, True) if abs(c-v) <= TOL else (v, False)
def unit_dims(pno, bbox):
    x0, y0, x1, y1 = bbox
    gx, gy = grids(pno)
    L, sL = snap(x0 - WALL_HALF, gx); R, sR = snap(x1 + WALL_HALF, gx)
    T, sT = snap(y0 - WALL_HALF, gy); B, sB = snap(y1 + WALL_HALF, gy)
    cw=(R-L)*K; ch=(B-T)*K
    NOM=[2.2,2.4,2.8,3.6,4.2,5.4,6.0,8.4,10.8,12.6,13.8,16.2,19.2,21.6]
    def nom(v, both):
        if both: return round(v*10)/10                 # 양쪽 다 그리드면 공칭값(10.77→10.8)
        c=min(NOM,key=lambda n:abs(n-v)); return c if abs(c-v)<=0.15 else v
    cw=nom(cw, sL and sR); ch=nom(ch, sT and sB)
    return dict(cw=cw, ch=ch, snapped=[sL, sR, sT, sB], box=[L,T,R,B])
if __name__ == '__main__':
    m = json.load(open('measured3.json'))
    for k in sys.argv[1:]:
        v = m[k]; r = unit_dims(v['page'], v['bbox'])
        print(k, f"중심 {r['cw']:.2f} x {r['ch']:.2f} → 표기 {r['cw']-0.2:.2f} x {r['ch']-0.2:.2f}", r['snapped'])
