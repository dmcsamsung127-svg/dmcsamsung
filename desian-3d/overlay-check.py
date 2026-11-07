import sys, json; sys.path.insert(0, '.')
import pymupdf as fitz, measure
def overlay(pno, res, out, clip=None, dpi=110):
    src = measure.d; doc = fitz.open(); doc.insert_pdf(src, from_page=pno, to_page=pno); p = doc[0]
    for rid, v in res.items():
        if v['page'] != pno: continue
        r = fitz.Rect(v['bbox'])
        p.draw_rect(r * p.derotation_matrix if False else r, color=(1,0,0), width=0.6)
    pm = p.get_pixmap(dpi=dpi, clip=(fitz.Rect(clip) * p.rotation_matrix) if clip else None)
    pm.save(out)
