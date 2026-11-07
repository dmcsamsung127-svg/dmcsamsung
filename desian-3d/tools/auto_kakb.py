# KA/KB: 도면 판독 요약 → 제안 결정 + 이상 표시
import json,sys,doorread as DR,gridsnap as g,stalls as SS
K=g.K; m=json.load(open('m5_all.json'))
a={u['id']:u for u in json.load(open('/home/user/dmcsamsung/desian-3d/units-all.json'))}
opp={'L':'R','R':'L','T':'B','B':'T'}
LEFT={'B':'L','T':'R','L':'T','R':'B'}
for k in sys.argv[1].split(','):
    v=m[k]; (l,r,t,b),o=DR.read(v)
    dbl=[(e,c) for e,cl in o.items() for c in cl if c[2]>=2]
    fronts=sorted(set(e for e,_ in dbl))
    flag=[]
    if len(fronts)!=1: flag.append('front?'+''.join(fronts))
    f=fronts[0] if fronts else '?'
    sides=[e for e in 'LRTB' if e not in (f,opp.get(f,'')) and o.get(e)]
    ext=''
    if len(sides)==1: ext=' ext='+('L' if sides[0]==LEFT.get(f) else 'R')
    elif len(sides)>1: flag.append('sides'+''.join(sides))
    corner=a[k].get('corner') is not None
    if bool(sides)!=corner: flag.append('corner?'+str(corner))
    nb=len(o.get(opp.get(f,''),[]))
    if nb==0: flag.append('noBack')
    print(f"{k} {f}{ext}", '  #', 'TB',round((b-t)*K,2),'LR',round((r-l)*K,2),{e:[(round(p,1),round(q,1),n) for p,q,n in c] for e,c in o.items() if c}, 'FLAG '+' '.join(flag) if flag else '')
