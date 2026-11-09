# 지정 가로선/세로선 위를 지나는 벽선 좌표(pt, m 간격) — python3 wl.py page  x0 x1 y0 y1  [scanY ...] -- [scanX ...]
import sys,innerwalls as iw,gridsnap as g
K=g.K; p=int(sys.argv[1]); x0,x1,y0,y1=map(float,sys.argv[2:6]); rest=sys.argv[6:]
i=rest.index('--'); sy=list(map(float,rest[:i])); sx=list(map(float,rest[i+1:]))
V,H=iw.lines(p); g.grids(p); gx,gy=g.RAW[p]
for y in sy:
    xs=sorted(set(round(x,2) for x,a,b in V if a<=y<=b and x0<=x<=x1))
    print(f'y={y}: x', xs)
for x in sx:
    ys=sorted(set(round(y,2) for y,a,b in H if a<=x<=b and y0<=y<=y1))
    print(f'x={x}: y', ys)
print('grid x',[round(v,2) for v in gx if x0<=v<=x1],'grid y',[round(v,2) for v in gy if y0<=v<=y1])
