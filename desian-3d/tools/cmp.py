# 도면 크롭(출입문이 아래로 오게 회전·반전)과 렌더를 나란히
import json,sys,base64,re,fitz,doorread as DR,cols as C,gridsnap as g
K=g.K; m=json.load(open('m5_all.json'))
a={u['id']:u for u in json.load(open('/home/user/dmcsamsung/desian-3d/units-all.json'))}
PDF=g.PDF; d=fitz.open(PDF)
out=[]
for k in sys.argv[2].split(','):
    u=a[k]; ref=k if k in m else re.search(r'같은 평면 (\w+)',u['dimSrc']).group(1); v=m[ref]
    (l,r,t,b),arcs=DR.read(v)
    elen={'L':(b-t)*K,'R':(b-t)*K,'T':(r-l)*K,'B':(r-l)*K}
    dbl=[(e,c) for e,cl in arcs.items() for c in cl if c[2]>=2]
    if dbl: front=max(dbl,key=lambda x:x[1][1]-x[1][0])[0]
    else:
        cand=[e for e in 'LRTB' if arcs.get(e)]; front=max(cand,key=lambda e:len(arcs[e])) if cand else 'B'
    try: lg=json.load(open('/home/user/dmcsamsung/desian-3d/verify-log.json'))
    except Exception: lg={}
    if k in lg: front=lg[k]['front']
    p=d[v['page']]; p.set_rotation(0); pad=float(__import__('os').environ.get('PAD','3.5'))/K
    pm=p.get_pixmap(clip=fitz.Rect(l-pad,t-pad,r+pad,b+pad),matrix=fitz.Matrix(8,8))
    rot={'B':0,'T':180,'L':-90,'R':90}[front]
    out.append((k,base64.b64encode(pm.tobytes('png')).decode(),rot,bool(u.get('mirror'))))
json.dump(out,open(sys.argv[1],'w'))
