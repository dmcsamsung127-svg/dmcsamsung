# 도면 대조 후 확정: python3 decide.py UID FRONT [key=value ...]
#  FRONT: 출입문 벽(L/R/T/B, 원본 도면 좌표). 옵션:
#   park=N  parkX0=x  ent=i(앞벽 호 중 출입문 인덱스, 기본: 가장 넓은 것) ext=L|R|none(바깥 측벽) back=0|1
#   dropcol=i,j  W=값 D=값(치수 직접 지정)  note=...
import fcntl
import builtins
if not getattr(builtins,'_decide_lock',None):   # 한 프로세스에서는 한 번만 잠금
    builtins._decide_lock=open('/tmp/claude-0/-home-user-dmcsamsung/a7808b39-5d40-548d-9bd9-112abfa52580/scratchpad/decide.lock','w'); fcntl.flock(builtins._decide_lock,fcntl.LOCK_EX)
import json,sys,re,doorread as DR,cols as C,gridsnap as g,stalls as SS
K=g.K; m=json.load(open('m5_all.json'))
P='/home/user/dmcsamsung/desian-3d/units-all.json'
LOG='/home/user/dmcsamsung/desian-3d/verify-log.json'
uid,front=sys.argv[1],sys.argv[2]; opt=dict(x.split('=',1) for x in sys.argv[3:])
a=json.load(open(P)); u=next(x for x in a if x['id']==uid)
ref=uid if uid in m else opt.get('ref')
v=m[ref]; (l,r,t,b),arcs=DR.read(v)
# 외곽 수동 지정: lr=box / tb=box (그리드·벽중심 박스에서 벽 반두께 0.1m 안쪽), 또는 l= r= t= b= (pt)
bx=v['box']; hw=0.1/K
if opt.get('lr')=='box': l,r=bx[0]+hw,bx[2]-hw
if opt.get('tb')=='box': t,b=bx[1]+hw,bx[3]-hw
for kk in ('l','r','t','b'):
    if kk in opt: exec(f"{kk}=float(opt['{kk}'])")
if any(k_ in opt for k_ in ('lr','tb','l','r','t','b')):
    import arcs as AR
    tol=0.45/K; found={'L':[],'R':[],'T':[],'B':[]}
    for a_ in AR.door_arcs(v['page']):
        x0,y0,x1,y1=a_['rect']
        if t-0.2/K<=(y0+y1)/2<=b+0.2/K:
            if abs(x1-l)<tol or abs(x0-l)<tol: found['L'].append((y0,y1))
            if abs(x0-r)<tol or abs(x1-r)<tol: found['R'].append((y0,y1))
        if l-0.2/K<=(x0+x1)/2<=r+0.2/K:
            if abs(y1-t)<tol or abs(y0-t)<tol: found['T'].append((x0,x1))
            if abs(y0-b)<tol or abs(y1-b)<tol: found['B'].append((x0,x1))
    arcs={}
    for e,lst in found.items():
        lst=sorted(set((round(p,2),round(q,2)) for p,q in lst)); cl=[]
        for p,q in lst:
            if cl and p-cl[-1][1]<0.3/K: cl[-1]=[cl[-1][0],max(q,cl[-1][1]),cl[-1][2]+1]
            else: cl.append([p,q,1])
        arcs[e]=cl
F={'B':(lambda X,Y:(X-l,Y-t),'L','R','T'),'T':(lambda X,Y:(r-X,b-Y),'R','L','B'),
   'L':(lambda X,Y:(Y-t,r-X),'T','B','R'),'R':(lambda X,Y:(b-Y,X-l),'B','T','L')}
f,LE,RE,BE=F[front]
W0=((r-l) if front in 'TB' else (b-t))*K; D0=((b-t) if front in 'TB' else (r-l))*K
g.grids(v['page']); gx,gy=g.RAW[v['page']]
def grid_span(lo,hi,G):   # 실내면 구간을 감싸는 그리드 간격
    c=[x for x in G if lo-1.2/K<x<hi+1.2/K]
    if len(c)>2: return None   # 실내에 그리드선이 지나가면 판정 안 함
    return round((max(c)-min(c))*K,2) if len(c)>=2 else None
gw=grid_span(*( (l,r,gx) if front in 'TB' else (t,b,gy) )); gd=grid_span(*( (t,b,gy) if front in 'TB' else (l,r,gx) ))
def rule(val,gsp):
    if gsp and abs(gsp-10.8)<0.1 and val>11.0: return 10.6          # 사용자 기준: 11M 넘는 호실 없음
    if gsp and gsp-0.2<=11.0 and abs(val-(gsp-0.2))<=0.35: return round(gsp-0.2,2)      # 그리드 − 벽 0.2
    return round(val,2)
W=float(opt.get('W',rule(W0,gw))); D=float(opt.get('D',rule(D0,gd)))
sx,sy=W/W0,D/D0
def seg(e,p,q):
    if e in 'TB': Y=t if e=='T' else b; A=f(p,Y); B=f(q,Y)
    else: X=l if e=='L' else r; A=f(X,p); B=f(X,q)
    i=0 if e in (front,BE) else 1; s=sx if i==0 else sy
    return sorted([round(A[i]*K*s,2),round(B[i]*K*s,2)])
ext=opt.get('ext')
mirror = ext=='R'
fr=[seg(front,p,q)+[n] for p,q,n in arcs[front]]
bk=[seg(BE,p,q) for p,q,n in arcs[BE]] if opt.get('back','1')=='1' else []
sl=[seg(LE,p,q) for p,q,n in arcs[LE]]; sr=[seg(RE,p,q) for p,q,n in arcs[RE]]
side = sr if mirror else (sl if ext=='L' else [])
mx=lambda s:[round(W-s[1],2),round(W-s[0],2)]
if mirror: fr=[mx(s)+[s[2]] for s in fr]; bk=[mx(s) for s in bk]
cols=[]
for X,Y,wm,hm in C.columns(v['page']):
    if not (l-0.9/K<=X<=r+0.9/K and t-0.9/K<=Y<=b+0.9/K): continue
    x,y=f(X,Y); x*=K*sx; y*=K*sy; cx,cy=(wm,hm) if front in 'TB' else (hm,wm)
    if mirror: x=W-x
    x0,x1,y0,y1=x-cx/2,x+cx/2,y-cy/2,y+cy/2
    if x1>0.1 and x0<W-0.1 and y1>0.1 and y0<D-0.1 and (x0<0.3 or x1>W-0.3 or y0<0.3 or y1>D-0.3):
        cols.append([round(x,2),round(y,2),round(cx,2),round(cy,2)])
for i in sorted([int(x) for x in opt.get('dropcol','').split(',') if x],reverse=True): cols.pop(i)
# 주차칸: 앞벽 바깥 12m 안, 앞벽 방향 구간이 호실과 겹치는 칸(도면 실측)
st=[]
for x0_,y0_,x1_,y1_,cx_,cy_ in SS.stalls(v['page']):
    PP=[f(x0_,y0_),f(x1_,y1_)]
    xs=sorted(p[0]*K*sx for p in PP); ys=sorted(p[1]*K*sy for p in PP)
    if mirror: xs=sorted(W-x for x in xs)
    cxm=(xs[0]+xs[1])/2
    if ys[0]>D-0.1 and ys[0]-D-0.2<=float(opt.get('maxgap','5')) and 0<=cxm<=W and (xs[1]-xs[0])<6.5:
        st.append([round(xs[0],2),round(xs[1],2),round(ys[0]-D,2),round(ys[1]-ys[0],2)])
st.sort()
mg=min([q[2] for q in st],default=0)
st=[q for q in st if q[2]-mg<1.0]   # 같은 줄(통로 같은 쪽)의 칸만
for k in ('doors','doorX','balBack','balLeft','cols','mirror','parkN','parkX0','noPark','corner','sideBal','stalls','parkGap','openBal'):
    u.pop(k,None)
u['w'],u['d']=W,D
if fr:
    ent=fr[int(opt['ent'])] if 'ent' in opt else max(fr,key=lambda s:(s[2],s[1]-s[0]))
    u['doorX']=round((ent[0]+ent[1])/2,2)
if bk: u['balBack']=sorted(s for s in bk if s[1]-s[0]>0.5)
if side: u['balLeft']=sorted(s for s in side if s[1]-s[0]>0.5)
if ext in ('L','R'): u['corner']=['','']
if opt.get('sideBal')=='1': u['sideBal']=True
if opt.get('openBal')=='1': u['openBal']=True
if cols: u['cols']=cols
if mirror: u['mirror']=True
if u.get('drive'):
    if opt.get('park')=='0' or not st: u['noPark']=True
    else:
        u['stalls']=[[a_,b_]+([dp_] if abs(dp_-5.0)>0.3 else []) for a_,b_,_,dp_ in st]; u['parkGap']=round(max(0,mg-0.2),2)
u['dimSrc']='도면 대조 확인'+(' — '+opt['note'] if 'note' in opt else '')
u['updated']='2026-11-07'
json.dump(a,open(P,'w'),ensure_ascii=False,indent=0)
try: log=json.load(open(LOG))
except Exception: log={}
log[uid]={'front':front,**opt,'w':W,'d':D}
json.dump(log,open(LOG,'w'),ensure_ascii=False,indent=0)
print(uid,json.dumps({k:u.get(k) for k in ('w','d','doorX','balBack','balLeft','cols','stalls','parkGap','noPark','mirror','corner')}),'grid',gw,gd,'front arcs',fr)
