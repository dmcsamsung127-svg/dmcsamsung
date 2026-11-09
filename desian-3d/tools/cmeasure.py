import json,gridsnap as g,doorread as DR,innerwalls as iw,arcs as AR
K=g.K; m=json.load(open('m5_all.json'))
for k in [f'C5{i:02d}' for i in range(1,11)]+[f'C6{i:02d}' for i in range(1,11)]:
    v=m[k]; p=v['page']; bx=v['box']; l,r,t,b=DR.faces(v)
    V,H=iw.lines(p); cy=(t+b)/2
    xs=sorted(set(round(x,2) for x,a,bb in V if a<cy-0.5/K and bb>cy+0.5/K and bx[0]-4/K<x<bx[2]+4/K))
    # 짧은 선(나선계단) 무게중심
    sx=sy=n=0
    for d in g.d[p].get_drawings():
        for it in d['items']:
            if it[0]=='l':
                a_,b_=it[1],it[2]; L=((a_.x-b_.x)**2+(a_.y-b_.y)**2)**.5*K
                mx,my=(a_.x+b_.x)/2,(a_.y+b_.y)/2
                if 0.15<L<0.55 and bx[0]+0.3/K<mx<bx[2]-0.3/K and t+0.2/K<my<b-0.2/K and abs(a_.x-b_.x)>0.05 and abs(a_.y-b_.y)>0.05:
                    sx+=mx;sy+=my;n+=1
    arcs=[(round(x0,1),round(y0,1),round(x1,1),round(y1,1)) for x0,y0,x1,y1 in [a['rect'] for a in AR.door_arcs(p)] if bx[0]-3/K<x0<bx[2]+3/K and bx[1]-2/K<y0<bx[3]+2/K]
    print(k,'p',p,'t,b',round(t,2),round(b,2),'xs',xs,'spiral',(round(sx/n,1),round(sy/n,1),n) if n else None,'arcs',arcs)
