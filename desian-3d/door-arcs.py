# 문 열림 호 = 짧은 사선 조각이 4개 이상 이어진 하나의 경로. 경로별 bbox와 경첩(호 양 끝 중 벽 쪽)을 돌려줌
import pymupdf as fitz, gridsnap as g
_c={}
def door_arcs(pno):
    if pno in _c: return _c[pno]
    out=[]
    for dr in g.d[pno].get_drawings():
        col=dr.get('color')
        if col and max(col)>0.15: continue
        segs=[(it[1],it[2]) for it in dr['items'] if it[0]=='l']
        diag=[(a,b) for a,b in segs if abs(a.x-b.x)>0.03 and abs(a.y-b.y)>0.03 and abs(a-b)<1.5]
        if len(diag)<4: continue
        # 이어진 조각 사슬로 나눔
        chains=[]
        for a,b in diag:
            for ch in chains:
                if abs(ch[-1]-a)<0.05: ch.append(b); break
            else: chains.append([a,b])
        for ch in chains:
            if len(ch)<5: continue
            r=fitz.Rect(ch[0],ch[0])
            for p in ch: r|=p
            rad=max(r.width,r.height)*g.K
            if 0.5<=rad<=1.4 and r.width>0.3/g.K and r.height>0.3/g.K:
                out.append(dict(rect=(r.x0,r.y0,r.x1,r.y1), a=(ch[0].x,ch[0].y), b=(ch[-1].x,ch[-1].y), rad=round(rad,2)))
    _c[pno]=out; return out
