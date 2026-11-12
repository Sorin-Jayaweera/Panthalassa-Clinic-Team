import numpy as np, time, json
from grab import open_scope, grab
tag='chaos_frozen_3s2_125kSps'
s=open_scope(); s.timeout=30000
cfg={k:s.query(k).strip() for k in [':ACQuire:POINts?',':ACQuire:SRATe?',':TIMebase:SCALe?',':CHANnel1:SCALe?',':CHANnel1:OFFSet?',':CHANnel2:SCALe?',':CHANnel2:OFFSet?']}
def rd(lbl):
    t0=time.time(); h,c=grab(s,tries=5000); x=np.concatenate(c); print(lbl,len(x),f'{time.time()-t0:.0f}s',flush=True); return h,x
h1,a=rd('read1 both shown'); _,b=rd('read2 both shown')
n=len(a)//2
print('frozen (read1==read2):',np.array_equal(a,b),' halves equal:',np.array_equal(a[:n],a[n:]),flush=True)
s.write(':CHANnel1:DISPlay OFF'); time.sleep(1)
h2,c=rd('read3 CH1 hidden'); _,c2=rd('read4 CH1 hidden')
s.write(':CHANnel1:DISPlay ON'); time.sleep(0.5)
print('CH2 frozen (read3==read4):',np.array_equal(c,c2),flush=True)
ch1=a[:n] if len(a)>=2*len(c)-10 else a; ch2=c
k=min(len(ch1),len(ch2)); eq=(ch1[:k]==ch2[:k]); print('fraction CH2 codes identical to CH1:',eq.mean().round(4))
blk=eq[:k//4000*4000].reshape(-1,4000).mean(1); print(''.join('#' if v>0.99 else ('.' if v<0.05 else '?') for v in blk))
o1,o2=int(h1[31:35]),int(h1[35:39]); fs=float(cfg[':ACQuire:SRATe?'])
V1=(ch1.astype(float)-o1)/25*float(cfg[':CHANnel1:SCALe?']); V2=(ch2.astype(float)-o2)/25*float(cfg[':CHANnel2:SCALe?'])
t=np.arange(k)/fs
np.savez(f'{tag}.npz',t=t,ch1=V1[:k],ch2=V2[:k],raw1=ch1[:k],raw2=ch2[:k],fs=fs)
np.savetxt(f'{tag}.csv',np.c_[t,V1[:k],V2[:k]],delimiter=',',header='t_s,ch1_V,ch2_V',fmt='%.7g',comments='')
cfg.update(dict(o1=o1,o2=o2,frozen12=bool(np.array_equal(a,b)),frozen34=bool(np.array_equal(c,c2)),frac_identical=float(eq.mean()),hdr1=h1[:100],hdr2=h2[:100],time=time.strftime('%Y-%m-%d %H:%M:%S')))
json.dump(cfg,open(f'{tag}_settings.json','w'),indent=1); print('saved',tag)
