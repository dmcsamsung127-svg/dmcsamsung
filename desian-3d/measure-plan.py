import pymupdf as fitz, numpy as np, re, json, sys
from scipy import ndimage as ndi
PDF='/root/.claude/uploads/a7808b39-5d40-548d-9bd9-112abfa52580/8ef16fdf-9___________.pdf'
MM_PER_PT = 170.4/598.08   # m per pt: 그리드 전체 치수선 170,400mm = 598.08pt 로 보정
S = 8                          # px per pt
d = fitz.open(PDF)

def walls_image(p):
    out = fitz.open(); np_ = out.new_page(width=p.mediabox.width, height=p.mediabox.height)   # 회전 전 좌표계
    sh = np_.new_shape()
    for dr in p.get_drawings():
        col = dr.get('color'); fill = dr.get('fill')
        if col and max(col) > 0.15 and not fill: continue   # 검정 외 선(그리드·중심선) 제외
        for it in dr['items']:
            if it[0]=='l': sh.draw_line(it[1], it[2])
            elif it[0]=='re': sh.draw_rect(it[1])
            elif it[0]=='qu': sh.draw_quad(it[1])
            elif it[0]=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
        sh.finish(color=(0,0,0), width=max(0.3, dr.get('width') or 0.3), fill=(0,0,0) if fill and max(fill)<0.5 else None, closePath=False)
    sh.commit()
    pm = np_.get_pixmap(matrix=fitz.Matrix(S,S), colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width) < 128

def measure(pno, want=None, close=1.4):
    p = d[pno]; ink = walls_image(p)
    ink = ndi.binary_dilation(ink, iterations=int(close*S/2))
    lab, n = ndi.label(~ink)
    res = {}
    for w in p.get_text('words'):
        rid = w[4]
        if not re.fullmatch(r'(KA|KB|FB|F|C)\d{3,4}', rid): continue
        if want and rid not in want: continue
        cx, cy = (w[0]+w[2])/2*S, (w[1]+w[3])/2*S
        # 글자 위치가 벽 위면 주변에서 가장 큰 영역 선택
        best = None
        for dx, dy in [(0,0),(0,-12),(0,12),(-12,0),(12,0),(0,-24),(0,24),(-24,0),(24,0)]:
            y, x = int(cy+dy), int(cx+dx)
            if 0<=y<lab.shape[0] and 0<=x<lab.shape[1] and lab[y,x]:
                best = lab[y,x]; break
        if not best: res[rid]=None; continue
        ys, xs = np.nonzero(lab == best)
        bw = (xs.max()-xs.min()+1)/S; bh=(ys.max()-ys.min()+1)/S
        fillr = len(xs)/((xs.max()-xs.min()+1)*(ys.max()-ys.min()+1))
        pad = close   # 팽창으로 줄어든 만큼 보정 (양쪽 벽 중심선까지)
        res[rid] = dict(w=round((bw+pad)*MM_PER_PT,2), h=round((bh+pad)*MM_PER_PT,2), fill=round(fillr,2))
    return res
if __name__=='__main__':
    print(json.dumps(measure(int(sys.argv[1]), sys.argv[2:] or None), ensure_ascii=False))

def measure2(pno, expected, close=2.5):
    """번호가 선 위에 걸친 경우까지: 번호 주변 칸 중 면적표와 가장 맞는 칸을 겹치지 않게 배정"""
    p = d[pno]; ink = walls_image(p)
    ink = ndi.binary_dilation(ink, iterations=int(close*S/2))
    lab, n = ndi.label(~ink)
    objs = ndi.find_objects(lab)
    sizes = ndi.sum(np.ones_like(lab), lab, index=range(1, n+1))
    k2 = MM_PER_PT**2
    def dims(r):
        sl = objs[r-1]; bh=(sl[0].stop-sl[0].start)/S; bw=(sl[1].stop-sl[1].start)/S
        return ((bw+close)*MM_PER_PT, (bh+close)*MM_PER_PT, sizes[r-1]/((sl[0].stop-sl[0].start)*(sl[1].stop-sl[1].start)))
    cands = []
    for w in p.get_text('words'):
        rid = w[4]
        if rid not in expected: continue
        E = expected[rid]
        seen = set()
        for fx in np.linspace(-0.5, 1.5, 9):
            for fy in np.linspace(-0.5, 1.5, 9):
                x = int((w[0] + (w[2]-w[0])*fx)*S); y = int((w[1] + (w[3]-w[1])*fy)*S)
                if 0<=y<lab.shape[0] and 0<=x<lab.shape[1] and lab[y,x] and lab[y,x] not in seen:
                    r = lab[y,x]; seen.add(r)
                    bw, bh, fr = dims(r)
                    if fr < 0.6: continue
                    score = abs(bw*bh - E)/E
                    if score < 0.2: cands.append((score, rid, r, bw, bh, fr))
    cands.sort(); used_r=set(); res={}
    for score, rid, r, bw, bh, fr in cands:
        if rid in res or r in used_r: continue
        res[rid] = dict(w=round(bw,2), h=round(bh,2), fill=round(fr,2), err=round(score,3)); used_r.add(r)
    return res

def measure3(pno, expected, close=2.5):
    """measure2와 같되, 칸의 도면 좌표(bbox, pt)까지 돌려줌 — 검수용 오버레이에 사용"""
    p = d[pno]; ink = walls_image(p)
    ink = ndi.binary_dilation(ink, iterations=int(close*S/2))
    lab, n = ndi.label(~ink)
    objs = ndi.find_objects(lab)
    sizes = ndi.sum(np.ones_like(lab), lab, index=range(1, n+1))
    cands = []
    for w in p.get_text('words'):
        rid = w[4]
        if rid not in expected: continue
        E = expected[rid]; seen = set()
        for fx in np.linspace(-0.5, 1.5, 9):
            for fy in np.linspace(-0.5, 1.5, 9):
                x = int((w[0] + (w[2]-w[0])*fx)*S); y = int((w[1] + (w[3]-w[1])*fy)*S)
                if not (0<=y<lab.shape[0] and 0<=x<lab.shape[1]) or not lab[y,x] or lab[y,x] in seen: continue
                r = lab[y,x]; seen.add(r); sl = objs[r-1]
                hp = sl[0].stop-sl[0].start; wp = sl[1].stop-sl[1].start
                fr = sizes[r-1]/(hp*wp)
                if fr < 0.6: continue
                mk = (lab[sl] == r)
                # 대표 폭: 행·열마다 칸 길이를 재고 상위 중앙값 사용(문 홈·창문선 밖 누수 무시)
                rows = mk.sum(1); cols = mk.sum(0)
                rows = rows[rows > 0.5*rows.max()]; cols = cols[cols > 0.5*cols.max()]
                wp2 = float(np.median(rows)); hp2 = float(np.median(cols))
                bw = (wp2/S+close)*MM_PER_PT; bh = (hp2/S+close)*MM_PER_PT
                score = abs(bw*bh - E)/E
                if score < 0.2:
                    bbox = ((sl[1].start/S)-close/2, (sl[0].start/S)-close/2, (sl[1].stop/S)+close/2, (sl[0].stop/S)+close/2)
                    cands.append((score, rid, r, bw, bh, fr, bbox, (w[0],w[1],w[2],w[3])))
    cands.sort(key=lambda c: c[0]); used=set(); res={}
    for score, rid, r, bw, bh, fr, bbox, lb in cands:
        if rid in res or r in used: continue
        res[rid] = dict(w=round(bw,2), h=round(bh,2), fill=round(float(fr),2), err=round(float(score),3), page=pno, bbox=[round(v,2) for v in bbox], label=[round(v,2) for v in lb]); used.add(r)
    return res

def measure4(pno, expected, close=2.5):
    """벽 중심선 기준 치수: 호실 안 여러 줄에서 양쪽 벽(잉크 띠)의 한가운데까지 거리를 재고 중앙값 사용"""
    p = d[pno]; ink = walls_image(p)
    ink = ndi.binary_dilation(ink, iterations=int(close*S/2))
    lab, n = ndi.label(~ink)
    objs = ndi.find_objects(lab)
    sizes = ndi.sum(np.ones_like(lab), lab, index=range(1, n+1))
    H, W = lab.shape; CAP = int(1.6/MM_PER_PT*S)   # 벽 띠 최대 1.6m
    def span(line, i0, r):
        # line: 1D 라벨 배열, i0: 칸 내부 위치 → 양쪽 벽 띠 중심까지의 길이(px)
        a = i0
        while a > 0 and line[a-1] == r: a -= 1
        b = i0
        while b < len(line)-1 and line[b+1] == r: b += 1
        def band(start, step):
            k = 0; j = start
            while 0 <= j < len(line) and line[j] == 0 and k < CAP: j += step; k += 1
            return k
        L = band(a-1, -1); R = band(b+1, +1)
        return (b - a + 1) + L/2 + R/2
    def center_dims(r):
        sl = objs[r-1]; y0, y1 = sl[0].start, sl[0].stop; x0, x1 = sl[1].start, sl[1].stop
        ws, hs = [], []
        for f in (0.2, 0.35, 0.5, 0.65, 0.8):
            y = int(y0 + (y1-y0)*f); row = lab[y]
            xs = np.nonzero(row[x0:x1] == r)[0]
            if len(xs): ws.append(span(row, x0 + int(np.median(xs)), r))
            x = int(x0 + (x1-x0)*f); col = lab[:, x]
            ys = np.nonzero(col[y0:y1] == r)[0]
            if len(ys): hs.append(span(col, y0 + int(np.median(ys)), r))
        if not ws or not hs: return None
        return (float(np.median(ws))/S*MM_PER_PT, float(np.median(hs))/S*MM_PER_PT)
    cands = []
    for w in p.get_text('words'):
        rid = w[4]
        if rid not in expected: continue
        E = expected[rid]; seen = set()
        for fx in np.linspace(-0.5, 1.5, 9):
            for fy in np.linspace(-0.5, 1.5, 9):
                x = int((w[0] + (w[2]-w[0])*fx)*S); y = int((w[1] + (w[3]-w[1])*fy)*S)
                if not (0<=y<H and 0<=x<W) or not lab[y,x] or lab[y,x] in seen: continue
                r = lab[y,x]; seen.add(r); sl = objs[r-1]
                hp = sl[0].stop-sl[0].start; wp = sl[1].stop-sl[1].start
                if sizes[r-1]/(hp*wp) < 0.6: continue
                cd = center_dims(r)
                if not cd: continue
                score = abs(cd[0]*cd[1] - E)/E
                if score < 0.2:
                    bbox = (sl[1].start/S, sl[0].start/S, sl[1].stop/S, sl[0].stop/S)
                    cands.append((score, rid, r, cd[0], cd[1], bbox))
    cands.sort(key=lambda c: c[0]); used=set(); res={}
    for score, rid, r, cw, ch, bbox in cands:
        if rid in res or r in used: continue
        res[rid] = dict(w=round(cw,3), h=round(ch,3), err=round(float(score),3), page=pno, bbox=[round(v,2) for v in bbox]); used.add(r)
    return res

def measure5(pno, ids, close=2.5):
    """호실 번호 글자 영역과 가장 많이 겹치는 칸 = 그 호실(면적으로 추측하지 않음). 칸의 안쪽면 bbox(pt) 반환"""
    p = d[pno]; ink = walls_image(p)
    ink = ndi.binary_dilation(ink, iterations=int(close*S/2))
    lab, n = ndi.label(~ink); objs = ndi.find_objects(lab)
    H, W = lab.shape; res = {}
    for w in p.get_text('words'):
        rid = w[4]
        if rid not in ids: continue
        x0, y0, x1, y1 = [int(v*S) for v in w[:4]]
        pad = 2*S
        win = lab[max(0,y0-pad):min(H,y1+pad), max(0,x0-pad):min(W,x1+pad)]
        core = lab[max(0,y0):min(H,y1), max(0,x0):min(W,x1)]
        vals, cnts = np.unique(core[core>0], return_counts=True)
        if not len(vals):
            vals, cnts = np.unique(win[win>0], return_counts=True)
            if not len(vals): continue
        r = int(vals[np.argmax(cnts)]); sl = objs[r-1]
        bbox = (sl[1].start/S - close/2, sl[0].start/S - close/2, sl[1].stop/S + close/2, sl[0].stop/S + close/2)
        res[rid] = dict(page=pno, bbox=[round(v,2) for v in bbox], share=round(float(cnts.max()/cnts.sum()),2))
    return res
