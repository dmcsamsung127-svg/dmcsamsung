# 호실 칸 주변의 실제 벽(평행한 두 선, 간격 0.1~0.45m)을 찾고, 면적표에 가장 맞는 네 벽 조합을 고름
import json, itertools, collections, gridsnap as g, innerwalls as iw
def walls_near(v, side_pad=1.6):
    L,T,R,B=v['box']; V,H=iw.lines(v['page']); pd=side_pad/g.K
    def pairs(segs, lo, hi, a0, a1):
        acc=collections.defaultdict(float)
        for p,s,e in segs:
            if a0-pd<=p<=a1+pd:
                ov=min(e,hi)-max(s,lo)
                if ov>0: acc[round(p,2)]+=ov
        ps=sorted(k for k,l in acc.items() if l>=0.3*(hi-lo))
        out=[]
        for i,p in enumerate(ps):
            for q in ps[i+1:]:
                t=(q-p)*g.K
                if 0.1<=t<=0.45: out.append(((p+q)/2, p, q))
        return out
    return pairs(V,T,B,L,R), pairs(H,L,R,T,B)
def fit(v, A, cand_pad=1.6):
    L,T,R,B=v['box']; vx,hy=walls_near(v,cand_pad); pd=cand_pad/g.K
    lefts=[w for w in vx if abs(w[0]-L)<=pd]; rights=[w for w in vx if abs(w[0]-R)<=pd]
    tops=[w for w in hy if abs(w[0]-T)<=pd]; bots=[w for w in hy if abs(w[0]-B)<=pd]
    best=None
    for l,r,t,b in itertools.product(lefts,rights,tops,bots):
        cw=(r[0]-l[0])*g.K; ch=(b[0]-t[0])*g.K
        if cw<2 or ch<2: continue
        err=abs(cw*ch-A)/A
        iw_=(r[1]-l[2])*g.K; ih=(b[1]-t[2])*g.K   # 안쪽 면 사이
        if best is None or err<best[0]: best=(err,cw,ch,iw_,ih)
    return best
