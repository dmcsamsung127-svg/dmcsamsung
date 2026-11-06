import json, sys, pymupdf as fitz, gridsnap as g, measure
a=json.load(open('/home/user/dmcsamsung/desian-3d/units-all.json')); ids={u['id'] for u in a}
def run(pno, cols=3, rows=2, dpi=260):
    r=measure.measure5(pno, ids)
    doc=fitz.open(); doc.insert_pdf(g.d,from_page=pno,to_page=pno); p=doc[0]; M=p.rotation_matrix
    res={}; vb=[]
    for k,v in r.items():
        q=g.unit_dims(pno,v['bbox']); res[k]=dict(v, **q)
        L,T,R,B=q['box']; rr=fitz.Rect(L,T,R,B)
        p.draw_rect(rr, color=(1,0,0), width=0.35)
        vr=rr*M; vb.append(vr)
        w=min(q['cw'],q['ch'])-0.2; h=max(q['cw'],q['ch'])-0.2
        # 글씨는 화면 기준으로 가로쓰기
        p.insert_text(fitz.Point(vr.x0+1.2, vr.y1-1.5)*~M, f"{w:.1f}x{h:.1f}", fontsize=3.4, color=(0,0,0.9), rotate=p.rotation)
    if not vb: return res
    X0=min(r.x0 for r in vb)-8; X1=max(r.x1 for r in vb)+8; Y0=min(r.y0 for r in vb)-8; Y1=max(r.y1 for r in vb)+8
    tw=(X1-X0)/cols; th=(Y1-Y0)/rows; n=0
    for j in range(rows):
        for i in range(cols):
            clip=fitz.Rect(X0+i*tw, Y0+j*th, X0+(i+1)*tw, Y0+(j+1)*th)
            if not any(clip.intersects(v) for v in vb): continue
            n+=1; p.get_pixmap(dpi=dpi, clip=clip).save(f't_{pno+1:02d}_{n}.png')
    return res
if __name__=='__main__':
    pno=int(sys.argv[1]); res=run(pno, int(sys.argv[2]) if len(sys.argv)>2 else 3, int(sys.argv[3]) if len(sys.argv)>3 else 2)
    json.dump(res, open(f'm5_p{pno+1:02d}.json','w')); print(len(res))
