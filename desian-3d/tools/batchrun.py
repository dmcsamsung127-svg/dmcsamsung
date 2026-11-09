# 한 프로세스에서 decide.py 를 여러 줄 실행(도면 캐시 재사용)
import sys,runpy,json,io,contextlib
lines=[]
for f in sys.argv[1:]:
    lines+= [l.split() for l in open(f) if l.strip()]
ok=0
for parts in lines:
    sys.argv=['decide.py']+parts
    buf=io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): runpy.run_path('decide.py',run_name='__main__')
        ok+=1
    except SystemExit: ok+=1
    except Exception as e: print('FAIL',parts,repr(e)[:200],flush=True)
print('BATCHDONE',ok,len(lines),flush=True)
