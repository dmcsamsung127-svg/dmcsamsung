# 이웃 호실과 맞닿은 벽 쌍(좌우 또는 상하) = 칸막이 → 문은 그와 직각인 벽(복도 쪽)
import json, gridsnap as g
def orient(m):
    by={}
    for k,v in m.items(): by.setdefault(v['page'],[]).append((k,v['box']))
    out={}
    tol=0.8/g.K
    for pg,rs in by.items():
        for k,(L,T,R,B) in rs:
            lr=tb=0
            for k2,(L2,T2,R2,B2) in rs:
                if k2==k: continue
                ov_y=min(B,B2)-max(T,T2); ov_x=min(R,R2)-max(L,L2)
                if ov_y>0.5*(B-T) and (abs(L-R2)<tol or abs(R-L2)<tol): lr+=1
                if ov_x>0.5*(R-L) and (abs(T-B2)<tol or abs(B-T2)<tol): tb+=1
            out[k]=('x' if lr>tb else 'y' if tb>lr else None, lr, tb)   # 'x': 문벽이 x방향(길이 cw)
    return out
