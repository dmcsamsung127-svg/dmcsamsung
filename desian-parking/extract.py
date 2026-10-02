"""고양향동 9BL 지식산업센터 평면도(A3 1/800 CAD PDF) → 주차장 3D용 데이터
   python3 extract.py 평면도.pdf out_dir

산출물
  out_dir/parking.json   층별 주차면·기둥·램프 (단위 m, 도면 화면 방향 기준: x→오른쪽, y→아래)
  out_dir/plan-<층>.webp  층별 평면도 바닥 텍스처 (건물 영역만 잘라냄)

주차면 판별: 선으로 닫힌 빈 칸 중
  일반·확장형 2.1~3.7 × 4.7~6.3m, 경형 1.7~2.3 × 3.1~4.2m, 평행 1.7~2.4 × 5.6~7.2m
  + 회색 채움 확장형(2.6×5.2m). 그리드·치수선(30m 초과)과 실명(EPS·TPS 등)이 있는 칸은 제외.
"""
import pymupdf as fitz, numpy as np, json, sys, re, os, collections
from scipy import ndimage as ndi
from PIL import Image

PDF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
K = 25.4/72*0.8          # m / pt (A3, 1/800)
S = 6                    # 판별용 래스터 px / pt
FLOORS = [(0,'B2'),(1,'B1'),(2,'1F'),(3,'2F'),(4,'3F'),(5,'4F'),(6,'5F')]
ELEV = {'B2':28.5,'B1':34.0,'1F':40.0}           # 도면 EL 표기
UPPER_FTF = 5.0                                   # 2~5층 층고(도면 미표기 → 추정)
for i, f in enumerate(['2F','3F','4F','5F']): ELEV[f] = 40.0 + UPPER_FTF*(i+1)
CROP = (160, 285, 1015, 640)                      # 화면 좌표(pt) 건물 영역
TEX_ZOOM = 4.5                                    # 텍스처 px / pt

d = fitz.open(PDF)
MB_W = d[0].mediabox.width                        # 회전(270°) 전 폭

def disp(x, y):
    """mediabox(pt) → 화면 좌표(m) — 크롭 원점 기준"""
    return (y - CROP[0]) * K, (MB_W - x - CROP[1]) * K

def disp_rect(x0, y0, x1, y1):
    (a, b), (c, e) = disp(x0, y0), disp(x1, y1)
    return dict(x=round(min(a, c), 2), y=round(min(b, e), 2), w=round(abs(c-a), 2), h=round(abs(e-b), 2))

def strokes_image(p):
    out = fitz.open(); q = out.new_page(width=p.mediabox.width, height=p.mediabox.height)
    sh = q.new_shape()
    for dr in p.get_drawings():
        if dr['type'] == 'f': continue                      # 채움(회색 주차면 등) 제외
        for it in dr['items']:
            if it[0] == 'l':
                if abs(it[1]-it[2])*K > 30: continue         # 그리드·치수선 제외
                sh.draw_line(it[1], it[2])
            elif it[0] == 're': sh.draw_rect(it[1])
            elif it[0] == 'qu': sh.draw_quad(it[1])
            elif it[0] == 'c': sh.draw_bezier(*it[1:5])
        sh.finish(color=(0,0,0), width=0.5, closePath=False)
    sh.commit()
    pm = q.get_pixmap(matrix=fitz.Matrix(S, S), colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width) < 200

def stalls(p, drawings):
    ink = strokes_image(p)
    lab, n = ndi.label(~ink)
    objs = ndi.find_objects(lab)
    area = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n+1))
    words = [w[:4] for w in p.get_text('words')]
    px = K / S
    res = []   # mediabox pt 좌표로 보관
    for i, sl in enumerate(objs):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        a, b = sorted([w*px, h*px]); fill = area[i] / (w*h)
        if fill <= 0.8: continue
        kind = None
        if 2.1 < a < 3.7 and 4.7 < b < 6.3: kind = 'N'      # 일반·확장형·장애인
        elif 1.7 < a < 2.3 and 3.1 < b < 4.2: kind = 'L'    # 경형
        elif 1.7 < a < 2.4 and 5.6 < b < 7.2: kind = 'P'    # 평행주차
        if not kind: continue
        x0, y0, x1, y1 = sl[1].start/S, sl[0].start/S, sl[1].stop/S, sl[0].stop/S
        if any(x0 < (wx0+wx1)/2 < x1 and y0 < (wy0+wy1)/2 < y1 for wx0, wy0, wx1, wy1 in words):
            continue                                          # EPS·TPS 등 실명 있는 칸 제외
        if kind == 'N' and a > 3.1: kind = 'D'                # 폭 3.3m 장애인 전용
        res.append([x0, y0, x1, y1, kind])
    # 회색 채움 확장형(2.6×5.2) — 외곽선이 없어 위에서 빠질 수 있음
    for dr in drawings:
        f = dr.get('fill')
        if dr['type'] == 'f' and f and abs(f[0]-0.8588) < 0.01:
            r = dr['rect']; a, b = sorted([r.width*K, r.height*K])
            if not (2.4 < a < 2.8 and 5.0 < b < 5.4): continue
            cx, cy = (r.x0+r.x1)/2, (r.y0+r.y1)/2
            hit = [s for s in res if s[0] < cx < s[2] and s[1] < cy < s[3]]
            if hit:
                for s in hit: s[4] = 'E'
            else:
                res.append([r.x0, r.y0, r.x1, r.y1, 'E'])
    out = []
    for x0, y0, x1, y1, kind in res:
        r = disp_rect(x0, y0, x1, y1); r['k'] = kind; out.append(r)
    return out

def columns(drawings):
    """검정 채움 사각형 0.4~1.3m = 기둥"""
    out, seen = [], set()
    for dr in drawings:
        f = dr.get('fill')
        if dr['type'] in ('f', 'fs') and f and max(f) < 0.05:
            r = dr['rect']; w, h = r.width*K, r.height*K
            if 0.4 < w < 1.3 and 0.4 < h < 1.3 and 0.5 < w/h < 2:
                key = (round(r.x0), round(r.y0))
                if key in seen: continue
                seen.add(key); out.append(disp_rect(r.x0, r.y0, r.x1, r.y1))
    return out

def ramps(p, drawings):
    """램프 표기 주변에서 같은 길이 평행선(빗금)이 10개 이상 모인 영역"""
    segs = []
    for dr in drawings:
        if dr['type'] == 'f': continue
        for it in dr['items']:
            if it[0] != 'l': continue
            a, b = it[1], it[2]; L = abs(a-b)*K
            if 3 < L < 9 and (abs(a.x-b.x) < 0.05 or abs(a.y-b.y) < 0.05):
                v = abs(a.x-b.x) < 0.05
                start = round((min(a.y,b.y) if v else min(a.x,b.x))*K*2)/2   # 빗금 시작선 (0.5m 단위)
                segs.append((min(a.x,b.x), min(a.y,b.y), max(a.x,b.x), max(a.y,b.y), (round(L,1), start), v))
    found = {}
    for w in p.get_text('words'):
        m = re.search(r'램프#(\d)', w[4])
        if not m: continue
        cx, cy = (w[0]+w[2])/2, (w[1]+w[3])/2
        near = [s for s in segs if abs((s[0]+s[2])/2-cx)*K < 22 and abs((s[1]+s[3])/2-cy)*K < 22]
        grp = collections.Counter((s[4], s[5]) for s in near).most_common(1)
        if not grp or grp[0][1] < 10: continue
        g = [s for s in near if (s[4], s[5]) == grp[0][0]]
        # 표기에서 가장 가까운 선부터 1.2m 간격 이내로 이어지는 선만
        vert = grp[0][0][1]
        pos = lambda s: s[0] if vert else s[1]
        g.sort(key=pos)
        c0 = min(g, key=lambda s: abs(pos(s) - (cx if vert else cy)))
        i = g.index(c0); lo = hi = i
        while lo > 0 and (pos(g[lo]) - pos(g[lo-1]))*K < 1.2: lo -= 1
        while hi < len(g)-1 and (pos(g[hi+1]) - pos(g[hi]))*K < 1.2: hi += 1
        g = g[lo:hi+1]
        r = disp_rect(min(s[0] for s in g), min(s[1] for s in g), max(s[2] for s in g), max(s[3] for s in g))
        # 진행 방향: 빗금과 직각. 화면 좌표에서 mediabox 세로선(vert) → 화면 가로선 → 진행은 y
        r['dir'] = 'y' if vert else 'x'
        r['id'] = int(m.group(1))
        if r['w'] > 4 and r['h'] > 4: found[r['id']] = r
    return list(found.values())

def official_count(p):
    m = re.search(r'주차장\((\d+)대\)', p.get_text())
    return int(m.group(1)) if m else None

def texture(p, name):
    pm = p.get_pixmap(matrix=fitz.Matrix(TEX_ZOOM, TEX_ZOOM), colorspace=fitz.csGRAY)
    im = Image.frombytes('L', (pm.width, pm.height), pm.samples)
    im = im.crop(tuple(int(v*TEX_ZOOM) for v in CROP))
    im.save(os.path.join(OUT, f'plan-{name}.webp'), quality=72, method=6)
    return im.size

data = dict(crop=dict(w=round((CROP[2]-CROP[0])*K,2), h=round((CROP[3]-CROP[1])*K,2)), floors=[])
for pno, fl in FLOORS:
    p = d[pno]; drs = p.get_drawings()
    s = stalls(p, drs)
    data['floors'].append(dict(
        id=fl, el=ELEV[fl], official=official_count(p),
        stalls=s, columns=columns(drs), ramps=ramps(p, drs)))
    texture(p, fl)
    print(fl, 'stalls', len(s), '/', official_count(p), 'ramps', [r['id'] for r in data['floors'][-1]['ramps']],
          'cols', len(data['floors'][-1]['columns']), file=sys.stderr)
json.dump(data, open(os.path.join(OUT, 'parking.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
