import sys, numpy as np, matplotlib, csv
matplotlib.use('Agg'); import matplotlib.pyplot as plt
tag=sys.argv[1]; d=np.load(f'{tag}.npz'); fs=float(d['fs']); t=d['t']
W=int(0.008*fs); H=int(0.002*fs); w=np.hanning(W); fw=np.fft.rfftfreq(W,1/fs)
band=(fw>600)&(fw<1000); tot=(fw>30)&(fw<5000)
fig,axs=plt.subplots(4,2,figsize=(16,15)); rows=[]
for col,(k,c,name) in enumerate([('ch1','#d4a017','CH1'),('ch2','#1f77b4','CH2')]):
    v=d[k]-d[k].mean(); st=np.arange(0,len(v)-W,H)
    P=np.array([np.abs(np.fft.rfft((v[s:s+W]-v[s:s+W].mean())*w))**2 for s in st])
    ratio=P[:,band].sum(1)/P[:,tot].sum(1)
    flag=np.zeros(len(v),bool)
    for s,r in zip(st,ratio):
        if r>0.6: flag[s:s+W]=True
    # segments
    e=np.diff(np.r_[0,flag.astype(int),0]); on=np.where(e==1)[0]; off=np.where(e==-1)[0]
    segs=[(a,b) for a,b in zip(on,off) if (b-a)/fs>=0.008]
    NF=2**18; fz=np.fft.rfftfreq(NF,1/fs); mz=(fz>300)&(fz<2500)
    ax=axs[1,col]; pks=[]
    for a,b in segs:
        x=v[a:b]-v[a:b].mean(); A=np.abs(np.fft.rfft(x*np.hanning(len(x)),NF))*2/np.hanning(len(x)).sum()
        ax.plot(fz[mz],A[mz]*1e3,color=c,alpha=.25,lw=.8)
        sel=(fz>600)&(fz<1000); pf=fz[sel][A[sel].argmax()]; pks.append(pf)
        rows.append([name,round(a/fs,5),round(b/fs,5),round((b-a)/fs*1e3,2),round(pf,1),round(np.ptp(x),3)])
    pks=np.array(pks)
    ax.set_title(f'{name}: FFT of each of {len(segs)} episodes (zero-padded), overlaid'); ax.set_xlabel('Hz'); ax.set_ylabel('amplitude (mV)')
    # concatenated episodes vs rest, Welch
    def welch(x,n=4096):
        hop=n//2; ww=np.hanning(n); S=[np.abs(np.fft.rfft((x[i:i+n]-x[i:i+n].mean())*ww))**2 for i in range(0,len(x)-n,hop)]
        return np.fft.rfftfreq(n,1/fs),10*np.log10(np.mean(S,0)/(fs*np.sum(ww**2))*2)
    ax=axs[2,col]; fA,PA=welch(v[flag]); fB,PB=welch(v[~flag])
    ax.plot(fA,PA,color=c,label=f'800 Hz episodes ({flag.mean()*100:.0f}% of time)'); ax.plot(fB,PB,color='gray',label='rest of record')
    ax.set_xlim(0,3000); ax.set_xlabel('Hz'); ax.set_ylabel('PSD (dB V²/Hz)'); ax.legend(); ax.set_title(f'{name}: spectrum of episodes vs rest (4096-pt Welch, {fs/4096:.0f} Hz bins)')
    ax=axs[3,col]; dur=np.array([(b-a)/fs*1e3 for a,b in segs])
    ax.scatter(dur,pks,color=c,s=14); ax.set_xlabel('episode length (ms)'); ax.set_ylabel('peak frequency (Hz)')
    ax.set_title(f'{name}: episode peak {np.median(pks):.0f} Hz median, {pks.mean():.0f} ± {pks.std():.0f} Hz')
    # top: example 120 ms with shading
    ax=axs[0,col]; s0=segs[len(segs)//2][0]-int(0.04*fs); s0=max(s0,0); sl=slice(s0,s0+int(0.12*fs))
    ax.plot(t[sl]*1e3,d[k][sl],color=c,lw=.8)
    for a,b in segs:
        if a<sl.stop and b>sl.start: ax.axvspan(t[a]*1e3,t[min(b,len(t)-1)]*1e3,color='green',alpha=.15)
    ax.set_xlabel('time (ms)'); ax.set_ylabel(f'{name} (V)'); ax.set_title(f'{name}: detected 600–1000 Hz episodes shaded green (>60% of power in band, ≥8 ms)')
    print(name,len(segs),'episodes',round(flag.mean()*100,1),'% of time; peak median',np.median(pks),'mean',pks.mean().round(1),'std',pks.std().round(1))
for a in axs.flat: a.grid(alpha=.3)
fig.suptitle(f'{tag}: steady ~800 Hz oscillation episodes isolated (CH1, CH2 separate records)'); fig.tight_layout(); fig.savefig(f'{tag}_800Hz_episodes.png',dpi=110)
with open(f'{tag}_800Hz_episodes.csv','w',newline='') as fh:
    wr=csv.writer(fh); wr.writerow(['channel','start_s','end_s','length_ms','peak_Hz','pk_pk_V']); wr.writerows(rows)
