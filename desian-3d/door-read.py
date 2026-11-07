# 도면에서 호실별 출입문·발코니 문 위치를 읽음
import json, collections, pymupdf as fitz, gridsnap as g, innerwalls as iw, arcs as AR
K=g.K
def faces(v):
    """실내면 좌표(원본 pt): left,right(x) top,bot(y). 실패 시 box"""
    L,T,R,B=v['box']; cx,cy=(L+R)/2,(T+B)/2
    V,H=iw.lines(v['page'])
    def cover(segs, lo, hi):
        acc=collections.defaultdict(float)
        for p,a,b in segs:
            ov=min(b,hi)-max(a,lo)
            if ov>0: acc[round(p,2)]+=ov
        return acc
    vx=cover(V,T,B); hy=cover(H,L,R)
    nx=0.45*(B-T); ny=0.45*(R-L); m=0.5/K
    l=max([x for x,c in vx.items() if c>=nx and x<cx-m], default=L)
    r=min([x for x,c in vx.items() if c>=nx and x>cx+m], default=R)
    t=max([y for y,c in hy.items() if c>=ny and y<cy-m], default=T)
    b=min([y for y,c in hy.items() if c>=ny and y>cy+m], default=B)
    return l,r,t,b
def read(v):
    l,r,t,b=faces(v); pno=v['page']; tol=0.45/K
    found={'L':[],'R':[],'T':[],'B':[]}
    for a in AR.door_arcs(pno):
        x0,y0,x1,y1=a['rect']
        # 벽선에 한 변이 붙어 있고, 벽 구간 안에 있는 호
        if t-0.2/K<=(y0+y1)/2<=b+0.2/K:
            if abs(x1-l)<tol or abs(x0-l)<tol: found['L'].append((y0,y1))
            if abs(x0-r)<tol or abs(x1-r)<tol: found['R'].append((y0,y1))
        if l-0.2/K<=(x0+x1)/2<=r+0.2/K:
            if abs(y1-t)<tol or abs(y0-t)<tol: found['T'].append((x0,x1))
            if abs(y0-b)<tol or abs(y1-b)<tol: found['B'].append((x0,x1))
    out={}
    for e,lst in found.items():
        lst=sorted(set((round(p,2),round(q,2)) for p,q in lst)); cl=[]
        for p,q in lst:
            if cl and p-cl[-1][1] < 0.3/K: cl[-1]=[cl[-1][0],max(q,cl[-1][1]),cl[-1][2]+1]
            else: cl.append([p,q,1])
        out[e]=cl     # [시작, 끝, 호 개수] (원본 pt)
    return (l,r,t,b), out
if __name__=='__main__':
    import sys
    m=json.load(open('m5_all.json'))
    for k in sys.argv[1:]:
        f,o=read(m[k]); print(k,[round(x,1) for x in f],{e:[(round(p,1),round(q,1),n) for p,q,n in c] for e,c in o.items()})
