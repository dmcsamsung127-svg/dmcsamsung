# 변별 문 호 위치(m, 변의 시작점 T/L 기준) 출력
import json,sys,doorread as DR,gridsnap as g,stalls as SS
K=g.K; m=json.load(open('m5_all.json'))
for k in sys.argv[1].split(','):
    v=m[k]; (l,r,t,b),o=DR.read(v)
    res={}
    for e,cl in o.items():
        base=l if e in 'TB' else t
        res[e]=[(round((p-base)*K,1),round((q-base)*K,1),n) for p,q,n in cl]
    # 주차칸이 붙은 변
    near=[]
    for x0,y0,x1,y1,cx,cy in SS.stalls(v['page']):
        if l<cx<r and t-12/K<cy<t: near.append('T')
        if l<cx<r and b<cy<b+12/K: near.append('B')
        if t<cy<b and l-12/K<cx<l: near.append('L')
        if t<cy<b and r<cx<r+12/K: near.append('R')
    print(k,'TB',round((b-t)*K,2),'LR',round((r-l)*K,2),res,'stalls',{e:near.count(e) for e in set(near)})
