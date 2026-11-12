import pyvisa, numpy as np, time
RES='USB0::0x049F::0x505E::CN5603029100402::INSTR'
def open_scope():
    s=pyvisa.ResourceManager().open_resource(RES); s.timeout=20000; s.clear(); return s
def q(s):
    s.write(':WAVeform:DATA:ALL?'); return s.read_raw()
def grab(s, tries=50):
    """Returns header string and list of channel arrays (int8) for one frame."""
    hdr=None; chunks=[]
    for _ in range(tries):
        b=q(s)
        if len(b)<29: time.sleep(0.02); continue
        plen=int(b[2:11]); tot=int(b[11:20])
        if plen==128:
            hdr=b[:128].decode('latin1'); chunks=[]; need=tot-99; continue
        if hdr is None: continue
        chunks.append(np.frombuffer(b[29:plen],dtype=np.int8).copy())
        if sum(len(c) for c in chunks)>=need: return hdr,chunks
    raise RuntimeError('no full frame')
