# C5·C6: 도면 실측값으로 직접 기록 (앞벽 = 계단 쪽 끝벽, 뒤 = 실내형 베란다(+6층 야외테라스), 출입문 = 긴 벽 → 오른쪽 측면)
import json,gridsnap as g,doorread as DR,arcs as AR
K=g.K; m=json.load(open('m5_all.json'))
P='/home/user/dmcsamsung/desian-3d/units-all.json'; a=json.load(open(P)); by={u['id']:u for u in a}
LOG='/home/user/dmcsamsung/desian-3d/verify-log.json'; log=json.load(open(LOG))
spir={}
exec(open('cmeasure.py').read().split("for k in")[0])
def spiral_center(p,bx,t,b):
    sx=sy=n=0
    for d in g.d[p].get_drawings():
        for it in d['items']:
            if it[0]=='l':
                a_,b_=it[1],it[2]; L=((a_.x-b_.x)**2+(a_.y-b_.y)**2)**.5*K; mx,my=(a_.x+b_.x)/2,(a_.y+b_.y)/2
                if 0.15<L<0.55 and bx[0]+0.3/K<mx<bx[2]-0.3/K and t+0.2/K<my<b-0.2/K and abs(a_.x-b_.x)>0.05 and abs(a_.y-b_.y)>0.05: sx+=mx;sy+=my;n+=1
    return sx/n,sy/n
# (l, r, balcony depth m, terrace depth m, spiral end 'R'|'L')
C={'C501':(395.28,426.48,1.22,0,'R'),'C502':(395.28,426.48,1.22,0,'R'),'C503':(395.28,426.48,1.22,0,'R'),'C504':(395.28,426.48,1.22,0,'R'),'C505':(395.28,426.48,1.22,0,'R'),
   'C506':(327.36,362.04,1.25,0,'L'),'C507':(327.36,362.04,1.25,0,'L'),'C508':(327.36,362.04,1.25,0,'L'),'C509':(327.36,362.04,1.25,0,'L'),'C510':(327.36,362.04,1.25,0,'L'),
   'C601':(402.36,426.48,1.22,1.96,'R'),'C602':(405.96,426.48,1.19,1.96,'R'),'C603':(405.96,426.48,1.19,1.96,'R'),'C604':(402.48,426.48,1.22,1.96,'R'),'C605':(405.96,426.48,1.19,1.96,'R'),
   'C606':(327.36,356.4,1.19,1.63,'L'),'C607':(327.36,352.8,1.19,1.63,'L'),'C608':(327.36,356.4,1.19,1.63,'L'),'C609':(327.36,352.8,1.19,1.63,'L'),'C610':(327.36,356.4,1.19,1.63,'L')}
for k,(l,r,bd,td,se) in C.items():
    v=m[k]; p=v['page']; bx=v['box']; _,_,t,b=DR.faces(v)
    W=round((b-t)*K,2); D=round((r-l)*K,2)
    ar=[x['rect'] for x in AR.door_arcs(p) if bx[0]-3/K<x['rect'][0]<bx[2]+3/K and bx[1]-2/K<x['rect'][1]<bx[3]+2/K]
    ent=[q for q in ar if q[3]<t+0.1/K or q[1]>b-0.1/K]           # 긴 벽 바깥 호 = 출입문
    bal=[q for q in ar if (q[0]<l+0.1/K and q[2]>l-1.6/K) if se=='R'] or [q for q in ar if q[2]>r-0.1/K and q[0]<r+1.6/K and se=='L' and t<q[1]<b]
    e=ent[0]; onT=e[3]<t+0.1/K
    # 좌표 변환: y = 계단 끝벽(앞)에서 먼 쪽(베란다)=0
    fy=(lambda X:(X-l)*K) if se=='R' else (lambda X:(r-X)*K)
    # 출입문이 오른쪽(x=W)에 오도록: 출입문 벽 쪽 Y가 x=W
    fx=(lambda Y:(b-Y)*K) if onT else (lambda Y:(Y-t)*K)
    six=sorted([fy(e[0]),fy(e[2])]); single=k.startswith('C6')
    if single: yc=(six[0]+six[1])/2; door=1.0
    else: yc=six[0]+1.0; door=1.8                             # 양개문: 호(한 짝) 시작점부터 2.1M 개구부
    sxp,syp=spiral_center(p,bx,t,b)
    u=by[k]
    for kk in ('doors','doorX','balBack','balLeft','cols','mirror','corner','sideBal','openBal','stalls','parkGap','noPark','terrace','single','door'): u.pop(kk,None)
    u.update(w=W,d=D,doorSide='R',doorAt=round(D-yc,2),door=door,balD=bd,spiral=[round(fx(syp),2),round(fy(sxp),2)])
    if single: u['single']=True
    if td: u['terrace']=True; u['terrD']=td
    if bal:
        q=bal[0]; xs=sorted([fx(q[1]),fx(q[3])]); u['balBack']=[[round(xs[0],2),round(xs[1],2)]]
    u['dimSrc']='도면 대조 확인 — 실내형 베란다'+(' + 야외테라스' if td else '')+', 출입문 긴 벽'
    u['updated']='2026-11-09'
    log[k]={'front':'manual-C','balD':bd,'terrD':td}
    print(k,W,D,'doorAt',u['doorAt'],'bal',u.get('balBack'),'spiral',u['spiral'],'terr',td)
json.dump(a,open(P,'w'),ensure_ascii=False,indent=0); json.dump(log,open(LOG,'w'),ensure_ascii=False,indent=0)
