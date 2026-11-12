import sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
tag=sys.argv[1]; d=np.load(f'{tag}.npz'); fs=float(d['fs'])
FMAX=3000
fig,axs=plt.subplots(4,2,figsize=(16,16))
for col,(k,c,name) in enumerate([('ch1','#d4a017','CH1'),('ch2','#1f77b4','CH2')]):
    v=d[k]-d[k].mean()
    # A: full-record high-res FFT, linear amplitude
    A=np.abs(np.fft.rfft(v*np.hanning(len(v))))*2/np.sum(np.hanning(len(v))); f=np.fft.rfftfreq(len(v),1/fs)
    m=f<FMAX; a=axs[0,col]; a.plot(f[m],A[m]*1e3,color=c,lw=.4)
    pk=f[m][np.argmax(A[m][f[m]>20])+np.sum(f[m]<=20)]
    a.set_title(f'{name}: full 3.2 s FFT, {fs/len(v):.2f} Hz bins, linear amplitude (peak {pk:.0f} Hz)'); a.set_ylabel('amplitude (mV)'); a.set_xlabel('Hz')
    # B: overlay of many short windows (20 ms), linear power
    W=int(0.02*fs); starts=np.arange(0,len(v)-W,W); w=np.hanning(W); fw=np.fft.rfftfreq(W,1/fs); mw=fw<FMAX
    S=np.array([np.abs(np.fft.rfft((v[s:s+W]-v[s:s+W].mean())*w))*2/w.sum() for s in starts])
    a=axs[1,col]
    for row in S: a.plot(fw[mw],row[mw]*1e3,color=c,alpha=.08,lw=.7)
    a.plot(fw[mw],np.median(S,0)[mw]*1e3,color='k',lw=1.5,label='median of windows'); a.legend()
    a.set_title(f'{name}: {len(starts)} overlaid 20 ms windows ({fs/W:.0f} Hz bins)'); a.set_ylabel('amplitude (mV)'); a.set_xlabel('Hz')
    # C: histogram of dominant frequency in each 20 ms window
    dom=fw[mw][np.argmax(S[:,mw][:,fw[mw]>100],1)+np.sum(fw[mw]<=100)]
    a=axs[2,col]; a.hist(dom,bins=np.arange(100,FMAX,fs/W),color=c)
    a.set_title(f'{name}: dominant frequency per 20 ms window (median {np.median(dom):.0f} Hz)'); a.set_xlabel('Hz'); a.set_ylabel('windows')
    # D: spectrogram 10 ms windows, 75% overlap
    a=axs[3,col]; a.specgram(v,NFFT=int(0.01*fs),Fs=fs,noverlap=int(0.0075*fs),cmap='magma',vmin=-90)
    a.set_ylim(0,FMAX); a.set_xlabel('time (s)'); a.set_ylabel('Hz'); a.set_title(f'{name}: spectrogram (10 ms windows)')
for a in axs.flat: a.grid(alpha=.3)
fig.suptitle(f'DSO2D15 chaotic circuit, {tag}: CH1 and CH2 are separate 3.2 s records'); fig.tight_layout(); fig.savefig(f'{tag}_fft_detail.png',dpi=110)
