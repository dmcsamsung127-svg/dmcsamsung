import json, re, collections, doorread as DR, cols as C, gridsnap as g
K=g.K
m=json.load(open('m5_all.json'))
P='/home/user/dmcsamsung/desian-3d/units-all.json'; a=json.load(open(P))
SKIP={'FB101','FB102','FB103','F228','F347'}   # 직접 확인·매물장 값
stat=collections.Counter()
def mapper(e,l,r,t,b):
    if e=='B': return (lambda X,Y:(X-l,Y-t)), 'L','R','T'
    if e=='T': return (lambda X,Y:(r-X,b-Y)), 'R','L','B'
    if e=='L': return (lambda X,Y:(Y-t,r-X)), 'T','B','R'
    return (lambda X,Y:(b-Y,X-l)), 'B','T','L'
for u in a:
    k=u['id']
    if k in SKIP or 'w' not in u: continue
    for f in ('doors','balBack','balLeft','doorX','mirror'): u.pop(f,None)
    ref=k; mm=re.search(r'\((\w+)\)',u.get('dimSrc',''))
    if k not in m and mm: ref=mm.group(1)
    v=m.get(ref)
    if not v: stat['nobox']+=1; continue
    (l,r,t,b),arcs=DR.read(v)
    elen={'L':(b-t)*K,'R':(b-t)*K,'T':(r-l)*K,'B':(r-l)*K}
    dbl=[(e,c) for e,cl in arcs.items() for c in cl if c[2]>=2]
    if dbl:
        front=max(dbl,key=lambda x:x[1][1]-x[1][0])[0]; stat['double']+=1
    else:
        side,_=C.unit_cols(v,u['w']+0.2)
        cand=[e for e in 'LRTB' if abs(elen[e]-(u['w']+0.2))<0.6]
        front=side if side in cand else (max(cand,key=lambda e:len(arcs[e])) if cand else side)
        if not arcs.get(front): stat['nodoor']+=1; continue
        stat['single']+=1
    f,leftE,rightE,backE=mapper(front,l,r,t,b)
    # 치수 방향: 문벽 길이가 w가 되도록
    if abs(elen[front]-(u['w']+0.2)) > abs(elen[front]-(u['d']+0.2)) and not u.get('_swapped'):
        u['w'],u['d']=u['d'],u['w']; stat['swap']+=1
    W,D=u['w'],u['d']
    def along(e,p,q):   # 벽 위 구간(원본 좌표) → 3D 좌표 구간
        if e in('T','B'): pts=[f(p,(t if e=='T' else b)), f(q,(t if e=='T' else b))]
        else: pts=[f((l if e=='L' else r),p), f((l if e=='L' else r),q)]
        if e==front or e==backE: vals=sorted([pts[0][0]*K,pts[1][0]*K])
        else: vals=sorted([pts[0][1]*K,pts[1][1]*K])
        return [round(max(vals[0],0),2), round(vals[1],2)]
    doors=[along(front,p,q) for p,q,n in arcs[front]]
    back=[along(backE,p,q) for p,q,n in arcs.get(backE,[])] if not u.get('noWin') else []
    sideL=[along(leftE,p,q) for p,q,n in arcs.get(leftE,[])]
    sideR=[along(rightE,p,q) for p,q,n in arcs.get(rightE,[])]
    cs=[c for c in C.columns(v['page']) if l-0.9/K<=c[0]<=r+0.9/K and t-0.9/K<=c[1]<=b+0.9/K]
    newcols=[]
    for X,Y,wm,hm in cs:
        x,y=f(X,Y); sx,sy=(wm,hm) if front in 'TB' else (hm,wm)
        newcols.append([round(x*K,2),round(y*K,2),round(sx,2),round(sy,2)])
    if newcols: u['cols']=newcols
    else: u.pop('cols',None)
    mirror=False
    if u.get('corner') and sideR and not sideL: mirror=True    # 바깥 측벽이 오른쪽 → 좌우 반전해 왼쪽에
    if mirror:
        doors=[[round(W-q,2),round(W-p,2)] for p,q in doors]; back=[[round(W-q,2),round(W-p,2)] for p,q in back]
        sideL=sideR
        if u.get('cols'): u['cols']=[[round(W-c[0],2),c[1],c[2],c[3]] for c in u['cols']]
        u['mirror']=True; stat['mirror']+=1
    u['doors']=sorted(doors)
    if back: u['balBack']=back
    if u.get('corner') and sideL: u['balLeft']=sideL
    u['updated']='2026-11-07'
json.dump(a,open(P,'w'),ensure_ascii=False,indent=0)
print(stat)
by={x['id']:x for x in a}
for k in ['KA801','KA802','KA818','KB611','KB805','F419','F532','FB204','KA911','KA604','C508','KB1901']:
    x=by[k]; print(k,x['w'],x['d'],'doors',x.get('doors'),'back',x.get('balBack'),'left',x.get('balLeft'),'mir',x.get('mirror'))
