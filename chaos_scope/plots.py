import sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
tag=sys.argv[1]; mode=sys.argv[2] if len(sys.argv)>2 else 'aligned'
d=np.load(f'{tag}.npz'); t,x,y,fs=d['t'],d['ch1'],d['ch2'],float(d['fs'])
C1,C2='#d4a017','#1f77b4'   # scope colours: CH1 yellow, CH2 blue
def spec(v,n=None):
    v=v-v.mean(); w=np.hanning(len(v)); P=np.abs(np.fft.rfft(v*w))**2/(fs*np.sum(w**2))*2
    return np.fft.rfftfreq(len(v),1/fs), 10*np.log10(P+1e-20)
def welch(v,nseg=8192):
    hop=nseg//2; segs=[v[i:i+nseg] for i in range(0,len(v)-nseg+1,hop)]
    f,_=spec(segs[0]); P=np.mean([10**(spec(s)[1]/10) for s in segs],0); return f,10*np.log10(P)
FMAX=5000
lab=f'{len(t)} samples, {fs/1e3:g} kS/s, {t[-1]:.2f} s'
if mode=='unaligned':
    fig,ax=plt.subplots(1,2,figsize=(13,6))
    ax[0].plot(x,y,lw=.3,color='k',alpha=.5); ax[0].set_xlabel('CH1 (V)'); ax[0].set_ylabel('CH2 (V)')
    ax[0].set_title('XY of CH1 vs CH2 from DIFFERENT acquisitions (not time-aligned)')
    n=min(len(x),20000); ax[1].plot(x[:n],y[:n],lw=.5,color='purple'); ax[1].set_xlabel('CH1 (V)'); ax[1].set_ylabel('CH2 (V)')
    ax[1].set_title(f'first {n/fs*1e3:.0f} ms only')
    for a in ax: a.grid(alpha=.3)
    fig.suptitle(f'DSO2D15 chaotic circuit, unaligned channels — {lab}'); fig.tight_layout(); fig.savefig(f'{tag}_XY_unaligned.png',dpi=130); sys.exit()
# 1. time series + whole-record spectrum
fig,ax=plt.subplots(3,1,figsize=(14,10))
ax[0].plot(t,x,lw=.3,color=C1); ax[0].set_ylabel('CH1 (V)'); ax[0].set_title(f'CH1 vs time — {lab}')
ax[1].plot(t,y,lw=.3,color=C2); ax[1].set_ylabel('CH2 (V)'); ax[1].set_title('CH2 vs time (separate acquisition, not time-aligned with CH1)')
ax[1].set_xlabel('time (s)')
for v,c,n in [(x,C1,'CH1'),(y,C2,'CH2')]:
    f,P=welch(v); ax[2].plot(f,P,color=c,label=n,lw=1)
ax[2].set_xlim(0,FMAX); ax[2].set_xlabel('frequency (Hz)'); ax[2].set_ylabel('PSD (dB V²/Hz)'); ax[2].set_title('Spectrum of whole record (Welch, 8192-pt Hann, 50% overlap)'); ax[2].legend()
for a in ax: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f'{tag}_time_and_spectrum.png',dpi=130)
# 2. zoom so the waveform shape is visible
z=int(0.05*fs); fig,ax=plt.subplots(2,1,figsize=(14,6),sharex=True)
ax[0].plot(t[:z]*1e3,x[:z],color=C1); ax[0].set_ylabel('CH1 (V)'); ax[1].plot(t[:z]*1e3,y[:z],color=C2); ax[1].set_ylabel('CH2 (V)'); ax[1].set_xlabel('time (ms)')
ax[0].set_title('First 50 ms'); [a.grid(alpha=.3) for a in ax]; fig.tight_layout(); fig.savefig(f'{tag}_time_zoom50ms.png',dpi=130)
# 3. sliding-window animation
W=int(0.05*fs); step=int(0.01*fs); starts=range(0,len(t)-W,step)
fW,PW1=welch(x); _,PW2=welch(y)
fig=plt.figure(figsize=(14,9)); gs=fig.add_gridspec(3,1)
a0=fig.add_subplot(gs[0,:]); a0.plot(t,x,lw=.2,color=C1); a0.plot(t,y,lw=.2,color=C2); a0.set_xlabel('time (s)'); a0.set_ylabel('V'); a0.set_title('Whole record (CH1, CH2 separate acquisitions); shaded = current window')
span=a0.axvspan(0,W/fs,color='red',alpha=.25)
a1=fig.add_subplot(gs[1,0]); l1,=a1.plot([],[],color=C1,label='CH1'); l2,=a1.plot([],[],color=C2,label='CH2')
a1.set_xlim(0,W/fs*1e3); a1.set_ylim(min(x.min(),y.min())-.2,max(x.max(),y.max())+.2); a1.set_xlabel('time in window (ms)'); a1.set_ylabel('V'); a1.legend(loc='upper right'); a1.grid(alpha=.3)
a2=fig.add_subplot(gs[2,:]); a2.plot(fW,PW1,color=C1,alpha=.35,lw=1,label='CH1 whole record'); a2.plot(fW,PW2,color=C2,alpha=.35,lw=1,label='CH2 whole record')
s1,=a2.plot([],[],color=C1,lw=1.2,label='CH1 window'); s2,=a2.plot([],[],color=C2,lw=1.2,label='CH2 window')
a2.set_xlim(0,FMAX); a2.set_ylim(min(PW1[fW<FMAX].min(),PW2[fW<FMAX].min())-25,max(PW1.max(),PW2.max())+15); a2.set_xlabel('frequency (Hz)'); a2.set_ylabel('PSD (dB V²/Hz)'); a2.legend(loc='upper right',ncol=2,fontsize=8); a2.grid(alpha=.3)
a2.set_title(f'Spectrum: window ({W/fs*1e3:.0f} ms Hann, {fs/W:.0f} Hz bins) vs whole record')
fig.tight_layout(); tw=np.arange(W)/fs*1e3
def upd(i):
    s=starts[i]; xs,ys=x[s:s+W],y[s:s+W]
    l1.set_data(tw,xs); l2.set_data(tw,ys); 
    span.set_x(s/fs) if hasattr(span,'set_x') else None
    try: span.set_bounds(s/fs,0,W/fs,1)
    except Exception: pass
    f,P=spec(xs); s1.set_data(f,P); f,P=spec(ys); s2.set_data(f,P)
    a1.set_title(f'Window {s/fs:.3f}–{(s+W)/fs:.3f} s')
    return l1,l2,s1,s2
FuncAnimation(fig,upd,frames=len(starts),blit=False).save(f'{tag}_sliding_window.gif',writer=PillowWriter(fps=10),dpi=80)
print('done',len(starts),'frames')
