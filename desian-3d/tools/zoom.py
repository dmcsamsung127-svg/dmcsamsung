# 고해상도 크롭 + 1m 눈금(빨강) 오버레이: python3 zoom.py out page x0 y0 x1 y1 scale
import fitz,sys,gridsnap as g
K=g.K
out,pno,x0,y0,x1,y1,s=sys.argv[1],int(sys.argv[2]),*map(float,sys.argv[3:8])
d=fitz.open(g.PDF);p=d[pno];p.set_rotation(0)
R=fitz.Rect(x0,y0,x1,y1)
pm=p.get_pixmap(clip=R,matrix=fitz.Matrix(s,s))
pm.save(out)
print('px per m',round(s/K,1),'origin pt',x0,y0)
