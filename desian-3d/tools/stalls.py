import gridsnap as g
K=g.K; _c={}
def stalls(pno):
    if pno in _c: return _c[pno]
    out=[]
    for dr in g.d[pno].get_drawings():
        for it in dr['items']:
            if it[0]=='qu': R=it[1].rect
            elif it[0]=='re': R=it[1]
            else: continue
            a,b=sorted([R.width*K,R.height*K])
            if 2.3<=a<=2.75 and 4.7<=b<=5.4:
                c=((R.x0+R.x1)/2,(R.y0+R.y1)/2)
                if not any(abs(c[0]-o[4])<0.5/K and abs(c[1]-o[5])<0.5/K for o in out):
                    out.append((R.x0,R.y0,R.x1,R.y1,c[0],c[1]))
    _c[pno]=out; return out
