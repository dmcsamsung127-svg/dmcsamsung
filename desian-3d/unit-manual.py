# 수동 확인용: 지정한 앞벽(front)·바깥 측벽 기준으로 치수/문/기둥을 3D 좌표로 변환
import json,sys,doorread as DR,cols as C,gridsnap as g
K=g.K; m=json.load(open('m5_all.json'))
def conv(uid,front,ref=None):
    v=m[ref or uid]; (l,r,t,b),arcs=DR.read(v)
    if front=='B': f=lambda X,Y:(X-l,Y-t); L_,R_,Bk='L','R','T'
    if front=='T': f=lambda X,Y:(r-X,b-Y); L_,R_,Bk='R','L','B'
    if front=='L': f=lambda X,Y:(Y-t,r-X); L_,R_,Bk='T','B','R'
    if front=='R': f=lambda X,Y:(b-Y,X-l); L_,R_,Bk='B','T','L'
    W=((r-l) if front in 'TB' else (b-t))*K; D=((b-t) if front in 'TB' else (r-l))*K
    def seg(e,p,q):
        if e in 'TB': Y=t if e=='T' else b; A=f(p,Y);Bp=f(q,Y)
        else: X=l if e=='L' else r; A=f(X,p);Bp=f(X,q)
        i=0 if e in (front,Bk) else 1
        return sorted([round(A[i]*K,2),round(Bp[i]*K,2)])
    out={'W':round(W,2),'D':round(D,2)}
    for name,e in (('front',front),('back',Bk),('left',L_),('right',R_)):
        out[name]=[seg(e,p,q)+[n] for p,q,n in arcs[e]]
    cs=[c for c in C.columns(v['page']) if l-0.9/K<=c[0]<=r+0.9/K and t-0.9/K<=c[1]<=b+0.9/K]
    out['cols']=[]
    for X,Y,wm,hm in cs:
        x,y=f(X,Y); sx,sy=(wm,hm) if front in 'TB' else (hm,wm)
        out['cols'].append([round(x*K,2),round(y*K,2),round(sx,2),round(sy,2)])
    return out
if __name__=='__main__':
    print(json.dumps(conv(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None)))
