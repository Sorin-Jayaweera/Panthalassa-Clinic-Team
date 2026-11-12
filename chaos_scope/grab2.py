import numpy as np, time
from grab import open_scope, q
def grab_pos(s, tries=5000):
    """Place each data packet at its reported offset (field 3 minus 99)."""
    hdr=None; buf=None; filled=None; ups=[]
    for _ in range(tries):
        b=q(s)
        if len(b)<29: time.sleep(0.02); continue
        plen=int(b[2:11]); tot=int(b[11:20]); up=int(b[20:29])
        if plen==128:
            hdr=b[:128].decode('latin1'); n=tot-99; buf=np.zeros(n,np.int8); filled=np.zeros(n,bool); ups=[]; continue
        if hdr is None: continue
        d=np.frombuffer(b[29:plen],dtype=np.int8); o=up-99; ups.append(up)
        buf[o:o+len(d)]=d; filled[o:o+len(d)]=True
        if filled.all(): return hdr,buf,ups
    raise RuntimeError(f'incomplete: {filled.mean() if filled is not None else 0}')
