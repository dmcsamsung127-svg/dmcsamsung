# 원본 좌표 그대로 크롭 + 변 이름(T/B/L/R) 표시, 여러 호실을 한 장에 (HTML→PNG)
import json,sys,base64,fitz,doorread as DR,gridsnap as g
K=g.K; m=json.load(open('m5_all.json')); d=fitz.open(g.PDF)
out=[]
for k in sys.argv[2].split(','):
    v=m[k]; (l,r,t,b),_=DR.read(v); p=d[v['page']]; p.set_rotation(0); pad=float(__import__('os').environ.get('PAD','6'))/K
    R=fitz.Rect(l-pad,t-pad,r+pad,b+pad); s=float(__import__('os').environ.get('S','4.5'))
    pm=p.get_pixmap(clip=R,matrix=fitz.Matrix(s,s))
    box=[(l-R.x0)*s,(t-R.y0)*s,(r-R.x0)*s,(b-R.y0)*s]
    out.append([k,base64.b64encode(pm.tobytes('png')).decode(),pm.width,pm.height,box,round((r-l)*K,2),round((b-t)*K,2)])
html='<body style="margin:0;font:14px sans-serif;display:flex;flex-wrap:wrap">'
for k,img,w,h,(x0,y0,x1,y1),wx,hy in out:
    html+=f'''<div style="position:relative;margin:6px;width:{w}px;height:{h}px;border:1px solid #aaa"><img src="data:image/png;base64,{img}">
    <div style="position:absolute;left:{x0}px;top:{y0}px;width:{x1-x0}px;height:{y1-y0}px;outline:2px solid rgba(255,0,0,.5)"></div>
    <b style="position:absolute;left:4px;top:2px;background:#ff0;padding:1px 4px">{k} T-B {hy}m / L-R {wx}m</b>
    <b style="position:absolute;left:{(x0+x1)/2-6}px;top:{y0-18}px;color:red">T</b><b style="position:absolute;left:{(x0+x1)/2-6}px;top:{y1+2}px;color:red">B</b>
    <b style="position:absolute;left:{x0-16}px;top:{(y0+y1)/2}px;color:red">L</b><b style="position:absolute;left:{x1+4}px;top:{(y0+y1)/2}px;color:red">R</b></div>'''
open(sys.argv[1]+'.html','w').write(html+'</body>')
