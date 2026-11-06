"""S8 r3: the R -> T step (fit PROSPECT-D to R alone, predict T) checked on LOTUS's same-leaf R/T of yellow leaves
(Peters & Noble 2022, FRDR doi:10.20383/103.0606; Cary 5000 integrating sphere; ref/yinxing/research4/data/spectra_new/lotus).

    python3 -I materials/yinxing/lotus_rt.py ref/yinxing/research4/data/spectra_new/lotus

Same fit as fit_spectra.py (400-780 nm, Cw/Cm held, Anth 0, a flat surface term s); T compared as 3000 K light in the
5D Mk IV's channels.
"""
import sys, json, numpy as np
R='.'; sys.path[:0]=[R+'/materials/yinxing', R+'/tools']
import fit_spectra as FS
D=sys.argv[1]
fixed={"Anth":0.0,"Cw":0.012,"Cm":0.009}
out={}
for sid in ("CCAN2","OAK01","OAK01b"):
    a=np.loadtxt(f"{D}/Cary5000_{sid}_R.txt"); b=np.loadtxt(f"{D}/Cary5000_{sid}_T.txt")
    k=(a[:,0]>=400)&(a[:,0]<=780); lam=a[k,0]; Rm=a[k,1]; Tm=np.interp(lam,b[:,0],b[:,1])
    p,rms=FS.fit_R(lam,Rm,fixed)
    _,Tp=FS.model([p[q] for q in FS.FREE],lam,fixed)
    tm,tp=FS.channels(lam,Tm),FS.channels(lam,Tp)
    out[sid]={"fit":{q:round(v,3) for q,v in p.items()},"R_rms":round(rms,4),"T_meas_ch":np.round(tm,4).tolist(),"T_pred_over_meas":np.round(tp/tm,3).tolist(),"R_ch":np.round(FS.channels(lam,Rm),4).tolist()}
print(json.dumps(out,indent=1))
