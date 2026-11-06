"""Find straight seams: a row (or column) that jumps much more than its neighbours along a long unbroken run."""
import sys,glob,os,numpy as np
def runs(mask,minlen):
    best=0;cur=0
    for v in mask:
        cur=cur+1 if v else 0
        best=max(best,cur)
    return best
def scan(g,axis,minfrac=.05):
    if axis==1: g=g.T
    d=np.abs(np.diff(g,axis=0))/(g[:-1]+.002)
    out=[]
    n=g.shape[1]
    med=np.median(d,axis=0)  # typical jump of each column
    for r in range(3,d.shape[0]-3):
        nb=np.maximum.reduce([d[r-2],d[r-1],d[r+1],d[r+2]])
        m=(d[r]>.03)&(d[r]>1.9*nb)
        if m.mean()<minfrac*.5: continue
        b=runs(m,0)
        if b>=minfrac*n: out.append((r,b))
    return out
for f in sorted(glob.glob(sys.argv[1])):
    try: g=np.load(f,mmap_mode="r")[...,1].astype(np.float32)
    except Exception as e: continue
    a,b=scan(g,0),scan(g,1)
    if a or b: print(os.path.relpath(f,"out/v2"),"rows",a[:6],"cols",b[:6],flush=True)
print("scan done")
