"""평면도 PDF → 층별 호실 외곽(직사각형 조각) + 건물 바닥 외곽
   python3 units.py 평면도.pdf out_dir    (align.py 결과 align.json 필요)

호실 판별: 벽선(검정)으로 닫힌 칸 중 호실 번호(F·FB·R·RB·SB·C·KA·KB) 글자가 들어 있는 칸.
점선 칸막이는 선을 1.5pt 부풀려 막는다. 칸 모양은 0.5m 격자로 잘라 직사각형 조각으로 저장.
7층 이상은 한 장에 두 층이 있어 align.json 의 세로 이동량으로 6층 시트 좌표에 맞춘다.
"""
import pymupdf as fitz, numpy as np, json, sys, re, os
from scipy import ndimage as ndi

PDF, OUT = sys.argv[1], sys.argv[2]
K = 25.4/72*0.8
S = 4
CROP = (160, 285, 1015, 640)          # extract.py 와 같은 화면 영역(pt)
CELL = 0.5                            # m
DIL = 6                               # px (= 1.5pt ≈ 0.42m, 점선 칸막이 틈 메움)
ALIGN = json.load(open(os.path.join(os.path.dirname(__file__), 'align.json')))

# (페이지, 시트 위치, 층 목록) — 16~17층은 같은 평면
SHEETS = [(0,None,['B2']),(1,None,['B1']),(2,None,['1F']),(3,None,['2F']),(4,None,['3F']),(5,None,['4F']),
          (6,None,['5F']),(7,None,['6F']),
          (8,'upper',['7F']),(8,'lower',['8F']),(9,'upper',['9F']),(9,'lower',['10F']),
          (10,'upper',['11F']),(10,'lower',['12F']),(11,'upper',['13F']),(11,'lower',['14F']),
          (12,'upper',['15F']),(12,'lower',['16F','17F']),(13,'upper',['18F']),(13,'lower',['19F']),
          (14,'upper',['20F'])]
ID = re.compile(r'(KA|KB)(N\d\d|\d{3,4})|(FB|RB|SB|F|R|C)\d{3}')

d = fitz.open(PDF)

def walls_image(p):
    out = fitz.open(); q = out.new_page(width=p.rect.width, height=p.rect.height)
    sh = q.new_shape(); M = p.rotation_matrix
    for dr in p.get_drawings():
        col = dr.get('color')
        if dr['type'] == 'f': continue
        if col and max(col) > 0.15: continue             # 회색 그리드·대지선 제외
        for it in dr['items']:
            if it[0] == 'l':
                if abs(it[1]-it[2])*K > 40: continue
                sh.draw_line(it[1]*M, it[2]*M)
            elif it[0] == 'qu': sh.draw_quad(it[1]*M)
            elif it[0] == 're': sh.draw_rect(it[1]*M)
            elif it[0] == 'c': sh.draw_bezier(*(v*M for v in it[1:5]))
        sh.finish(color=(0,0,0), width=0.5, closePath=False)
    sh.commit()
    pm = q.get_pixmap(matrix=fitz.Matrix(S, S), colorspace=fitz.csGRAY)
    ink = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width) < 200
    return ndi.binary_dilation(ink, iterations=DIL)

def to_rects(mask, x0, y0, dy):
    """mask(px, 원점 x0,y0 px) → 0.5m 격자 직사각형 조각 [x,y,w,h] (크롭 기준 m)"""
    step = CELL / K * S                                  # px per cell
    H, W = mask.shape
    gh, gw = int(np.ceil(H/step)), int(np.ceil(W/step))
    pad = np.zeros((int(gh*step)+1, int(gw*step)+1), bool); pad[:H, :W] = mask
    grid = np.array([[pad[int(r*step):int((r+1)*step), int(c*step):int((c+1)*step)].mean() > 0.5
                      for c in range(gw)] for r in range(gh)])
    rects, used = [], np.zeros_like(grid)
    for r in range(gh):                                   # 가로로 늘리고, 같은 폭으로 아래로 늘림
        c = 0
        while c < gw:
            if grid[r, c] and not used[r, c]:
                c2 = c
                while c2+1 < gw and grid[r, c2+1] and not used[r, c2+1]: c2 += 1
                r2 = r
                while r2+1 < gh and grid[r2+1, c:c2+1].all() and not used[r2+1, c:c2+1].any(): r2 += 1
                used[r:r2+1, c:c2+1] = True
                px = (x0 + c*step)/S; py = (y0 + r*step)/S + dy
                rects.append([round((px - CROP[0])*K, 2), round((py - CROP[1])*K, 2),
                              round((c2-c+1)*CELL, 2), round((r2-r+1)*CELL, 2)])
                c = c2 + 1
            else:
                c += 1
    return rects

def floor_of(uid, floors):
    if uid.startswith(('FB', 'RB', 'SB')): return ['B' + uid[2]]
    m = re.match(r'(KA|KB)N', uid)
    if m: return floors                                   # 16~17층 공통 평면
    num = re.sub(r'^[A-Z]+', '', uid)
    return [f"{int(num[:-2])}F"]

result = {}
footprints = {}
for pno, half, floors in SHEETS:
    p = d[pno]
    ink = walls_image(p)
    lab, n = ndi.label(~ink)
    dy = ALIGN[f'{pno}-{half}'] if half else 0.0
    mid = p.rect.height / 2
    objs = ndi.find_objects(lab)
    seen, leaked = {}, []
    tom = lambda cx, cy: ((cx - CROP[0])*K, (cy + dy - CROP[1])*K)   # 화면 pt → 크롭 m
    for w in p.get_text('words'):
        t = w[4]
        if not ID.fullmatch(t): continue
        cx, cy = fitz.Point((w[0]+w[2])/2, (w[1]+w[3])/2) * p.rotation_matrix
        if half == 'upper' and cy > mid or half == 'lower' and cy < mid: continue
        best = None
        for ox, oy in [(0,0),(0,-2),(0,2),(-2,0),(2,0),(0,-4),(0,4),(-4,0),(4,0),(-3,-3),(3,3),(3,-3),(-3,3)]:
            y, x = int((cy+oy)*S), int((cx+ox)*S)
            if 0 <= y < lab.shape[0] and 0 <= x < lab.shape[1] and lab[y, x]:
                best = lab[y, x]; break
        if not best: leaked.append((t, *tom(cx, cy))); continue
        sl = objs[best-1]
        area = (sl[0].stop-sl[0].start)*(sl[1].stop-sl[1].start)/S/S*K*K
        if area > 1500: leaked.append((t, *tom(cx, cy))); continue   # 바깥·주차장으로 샌 칸
        if best in seen:
            seen[best]['labels'].append((t, *tom(cx, cy))); continue
        mask = lab[sl] == best
        mask = ndi.binary_dilation(mask, iterations=DIL)  # 부풀린 만큼 되돌림
        rects = to_rects(mask, sl[1].start, sl[0].start, dy)
        if not rects: continue
        seen[best] = dict(labels=[(t, *tom(cx, cy))], rects=rects)

    units = []
    for u in seen.values():
        L = u['labels']
        if len(L) == 1:
            units.append(dict(id=L[0][0], rects=u['rects'])); continue
        # 번호 여러 개가 한 칸에 → 긴 방향으로 번호 위치 중간에서 나눔
        bx0 = min(r[0] for r in u['rects']); bx1 = max(r[0]+r[2] for r in u['rects'])
        by0 = min(r[1] for r in u['rects']); by1 = max(r[1]+r[3] for r in u['rects'])
        ax = 0 if bx1-bx0 >= by1-by0 else 1
        L.sort(key=lambda l: l[1+ax])
        cuts = [(-1e9)] + [(L[i][1+ax]+L[i+1][1+ax])/2 for i in range(len(L)-1)] + [1e9]
        for i, l in enumerate(L):
            parts = []
            for r in u['rects']:
                a0, a1 = r[ax], r[ax]+r[2+ax]
                lo, hi = max(a0, cuts[i]), min(a1, cuts[i+1])
                if hi - lo < 0.3: continue
                q = list(r); q[ax] = round(lo, 2); q[2+ax] = round(hi-lo, 2); parts.append(q)
            if parts: units.append(dict(id=l[0], rects=parts))

    # 번호 칸이 주차장으로 샌 경우 → 같은 줄 양옆 호실 사이 빈 구간을 번호 수만큼 나눔
    def bbox(u):
        return (min(r[0] for r in u['rects']), min(r[1] for r in u['rects']),
                max(r[0]+r[2] for r in u['rects']), max(r[1]+r[3] for r in u['rects']))
    boxes = [bbox(u) for u in units]
    gaps = {}
    for t, lx, ly in leaked:
        for ax in (0, 1):
            o = 1 - ax; pos = (lx, ly)
            row = [b for b in boxes if b[o] - 0.5 < pos[o] < b[o+2] + 0.5]
            left = [b for b in row if b[ax+2] <= pos[ax] + 0.5]
            right = [b for b in row if b[ax] >= pos[ax] - 0.5]
            if not left or not right: continue
            lb = max(left, key=lambda b: b[ax+2]); rb = min(right, key=lambda b: b[ax])
            if not (0 < rb[ax] - lb[ax+2] < 120): continue
            near = lb if pos[ax] - lb[ax+2] <= rb[ax] - pos[ax] else rb
            band = (near[o], near[o+2])                         # 가까운 이웃 호실의 깊이
            gaps.setdefault((ax, round(lb[ax+2], 1), round(rb[ax], 1), band, round(near[ax+2]-near[ax], 2)), []).append((t, pos[ax]))
            break
    for (ax, a0, a1, band, nw), L in gaps.items():
        L.sort(key=lambda l: l[1]); cs = [l[1] for l in L]
        # 번호 간격(중앙값)으로 칸 경계를 잡고, 양 끝은 이웃 호실·번호 간격 반 칸까지
        sp = float(np.median(np.diff(cs))) if len(cs) > 1 else nw
        sp = min(sp, 1.6*nw)
        bounds = [max(a0, cs[0] - sp/2)] + [(cs[i]+cs[i+1])/2 for i in range(len(cs)-1)] + [min(a1, cs[-1] + sp/2)]
        for i, (t, c) in enumerate(L):
            r = [0, 0, 0, 0]
            lo, hi = bounds[i], bounds[i+1]
            r[ax] = round(lo, 2); r[2+ax] = round(hi-lo, 2)
            r[1-ax] = round(band[0], 2); r[3-ax] = round(band[1]-band[0], 2)
            units.append(dict(id=t, rects=[r], est=True))

    for u in units:
        if u['id'].startswith('C'):      # 나선계단 선에 칸이 쪼개짐 → 도면 실측 평균 3.74×8.68m 상자로
            bx0 = min(r[0] for r in u['rects']); bx1 = max(r[0]+r[2] for r in u['rects'])
            by0 = min(r[1] for r in u['rects']); by1 = max(r[1]+r[3] for r in u['rects'])
            cx, cy = (bx0+bx1)/2, (by0+by1)/2
            u['rects'] = [[round(cx-1.87, 2), round(cy-4.34, 2), 3.74, 8.68]]
        for fl in floor_of(u['id'], floors):
            v = dict(u); v['id'] = u['id'].replace('N', fl[:-1])          # KAN05 → KA1605
            result.setdefault(fl, []).append(v)
    seen = units

    # 타워층(6층 이상) 바닥 외곽: 바깥 공기와 이어진 영역을 지운 나머지
    if pno >= 7:
        y0, y1 = (int((mid if half == 'lower' else 0)*S), int((mid if half == 'upper' else p.rect.height)*S)) if half else (0, lab.shape[0])
        x0, x1 = int(CROP[0]*S), int(CROP[2]*S)
        sub = lab[y0:y1, x0:x1]
        outside = set(np.unique(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]))) - {0}
        big = [i for i in np.unique(sub) if i and i not in outside]
        inner = np.isin(sub, big) | (sub == 0)
        inner = ndi.binary_opening(inner, iterations=14)          # 선 찌꺼기 제거
        lb, nn = ndi.label(inner)
        sizes = ndi.sum(inner, lb, range(1, nn+1)) / S / S * K * K
        keep = [i+1 for i, a in enumerate(sizes) if a > 300]
        fp = to_rects(np.isin(lb, keep), x0, y0, dy)
        for fl in floors: footprints[fl] = fp
    print(pno, half, floors, len(seen), file=sys.stderr)

json.dump(dict(units=result, footprints=footprints), open(os.path.join(OUT, 'units.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in result.items()}, file=sys.stderr)
