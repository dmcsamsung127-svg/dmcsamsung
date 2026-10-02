"""2개 평면이 한 장에 있는 시트(7층 이상)를 6층 시트 좌표로 옮길 세로 이동량(pt, 화면 기준) 계산"""
import pymupdf as fitz, numpy as np, sys, json
PDF = sys.argv[1]
d = fitz.open(PDF)
Z = 2  # px/pt

def walls(p):
    pm = None
    out = fitz.open(); q = out.new_page(width=p.rect.width, height=p.rect.height)
    sh = q.new_shape(); M = p.rotation_matrix
    for dr in p.get_drawings():
        col = dr.get('color')
        if dr['type'] == 'f' or (col and max(col) > 0.15): continue
        if (dr.get('width') or 0) < 0.4: continue        # 두꺼운 벽선만
        for it in dr['items']:
            if it[0] == 'l': sh.draw_line(it[1]*M, it[2]*M)
        sh.finish(color=(0,0,0), width=1)
    sh.commit()
    pm = q.get_pixmap(matrix=fitz.Matrix(Z, Z), colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width) < 128

ref = walls(d[7]).astype(np.float32)
H = ref.shape[0]; mid = int(421*Z)
res = {}
for pno in range(8, 15):
    im = walls(d[pno]).astype(np.float32)
    for half, est, (a, b) in (('upper', 203.7, (0, mid)), ('lower', -192.9, (mid, H))):
        sub = np.zeros_like(im); sub[a:b] = im[a:b]
        best = None
        for dy in np.arange(est-15, est+15, 0.5):
            s = int(round(dy*Z))
            sh = np.roll(sub, s, axis=0)
            score = (sh*ref).sum()
            if not best or score > best[1]: best = (float(dy), score)
        res[f'{pno}-{half}'] = best[0]
        print(pno, half, best, file=sys.stderr)
json.dump(res, open('align.json', 'w'))
