import sys, json, time, numpy as np
from grab import open_scope, grab
pts=int(sys.argv[1]); tb=float(sys.argv[2]); tag=sys.argv[3]
s=open_scope(); s.timeout=30000
s.write(f':ACQuire:POINts {pts}'); time.sleep(0.3); s.write(f':TIMebase:SCALe {tb}'); time.sleep(0.3)
s.write(':TRIGger:SWEep AUTO'); time.sleep(10*tb+1.0)
s.write(':TRIGger:SWEep SINGle'); time.sleep(10*tb*2+2.0)
cfg={k:s.query(k).strip() for k in [':ACQuire:POINts?',':ACQuire:SRATe?',':TIMebase:SCALe?',':CHANnel1:SCALe?',':CHANnel1:OFFSet?',':CHANnel2:SCALe?',':CHANnel2:OFFSet?',':CHANnel1:PROBe?',':CHANnel2:PROBe?']}
t0=time.time(); h1,c=grab(s,tries=5000); ch1=np.concatenate(c)[:pts]; print('ch1',len(ch1),round(time.time()-t0,1),'s')
s.write(':CHANnel1:DISPlay OFF'); time.sleep(0.5)
h2,c=grab(s,tries=5000); ch2=np.concatenate(c)[:pts]; print('ch2',len(ch2))
s.write(':CHANnel1:DISPlay ON'); time.sleep(0.5)
_,c=grab(s,tries=5000); chk=np.concatenate(c)[:pts]; same=bool(np.array_equal(chk,ch1)); print('ch1 reread identical:',same)
s.write(':TRIGger:SWEep AUTO')
o1,o2=int(h1[31:35]),int(h1[35:39])
fs=float(cfg[':ACQuire:SRATe?']); v1=float(cfg[':CHANnel1:SCALe?'])*float(cfg[':CHANnel1:PROBe?']); v2=float(cfg[':CHANnel2:SCALe?'])*float(cfg[':CHANnel2:PROBe?'])
V1=(ch1.astype(float)-o1)/25*v1; V2=(ch2.astype(float)-o2)/25*v2
t=np.arange(pts)/fs
np.savez(f'{tag}.npz',t=t,ch1=V1,ch2=V2,raw1=ch1,raw2=ch2,fs=fs)
np.savetxt(f'{tag}.csv',np.c_[t,V1,V2],delimiter=',',header='t_s,ch1_V,ch2_V',fmt='%.7g',comments='')
cfg.update(dict(o1_counts=o1,o2_counts=o2,ch1_reread_identical=same,time=time.strftime('%Y-%m-%d %H:%M:%S'),header=h1[:100]))
json.dump(cfg,open(f'{tag}_settings.json','w'),indent=1); print(cfg)
print('V1',V1.min(),V1.max(),'V2',V2.min(),V2.max())
