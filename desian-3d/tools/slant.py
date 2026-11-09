import gridsnap as g,sys
K=g.K
pno=int(sys.argv[1]); X0,X1,Y0,Y1=map(float,sys.argv[2:6])
out=set()
for d in g.d[pno].get_drawings():
    for it in d['items']:
        if it[0]=='l':
            a,b=it[1],it[2]
            L=((a.x-b.x)**2+(a.y-b.y)**2)**.5
            if L*K>2 and abs(a.x-b.x)>0.3 and abs(a.y-b.y)>abs(a.x-b.x) and X0<min(a.x,b.x) and max(a.x,b.x)<X1 and Y0<min(a.y,b.y) and max(a.y,b.y)<Y1:
                out.add((round(a.x,2),round(a.y,2),round(b.x,2),round(b.y,2),str(d.get('color'))[:10],d.get('dashes')))
for s in sorted(out,key=lambda s:(s[1],s[0])): print(s)
