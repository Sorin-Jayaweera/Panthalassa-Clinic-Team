"""ADF5355 register calculator, ported from Analog Devices' no-OS driver
(https://github.com/analogdevicesinc/no-OS/blob/main/drivers/frequency/adf5355/adf5355.c).

Gives the 13 32-bit words (R12 first, R0 last) for a frequency on RFoutA (54 MHz-6.8 GHz)
or RFoutB (6.8-13.6 GHz, the VCO doubled). It only computes; it does not talk to the box.

    python adf5355_regs.py 8300e6 --ref 100e6 --out B
"""
import argparse
from math import gcd, ceil

MIN_VCO, MAX_VCO = 3.4e9, 6.8e9
MAX_PFD = 75e6
MOD1 = 1 << 24
MAX_MOD2 = 16384


def fract_n(vco, pfd):
    vco, pfd = int(vco), int(pfd)
    integer, rem = divmod(vco, pfd)
    tmp = rem * MOD1
    fract1, fract2 = divmod(tmp, pfd)
    mod2 = pfd
    while mod2 > MAX_MOD2:
        mod2 >>= 1
        fract2 >>= 1
    g = gcd(fract2, mod2)
    return integer, fract1, fract2 // g, mod2 // g


def registers(freq, ref=100e6, out="B", outa_power=3, cp_ua=900, ref_doubler=False, ref_div2=False,
              muxout=6, mute_till_lock=True, outa_en=None, outb_en=None):
    """Return ({register: word}, info). outa_power 0..3 = -4, -1, +2, +5 dBm. muxout 6 = digital lock detect."""
    outa_en = (out == "A") if outa_en is None else outa_en
    outb_en = (out == "B") if outb_en is None else outb_en
    r = 0
    while True:
        r += 1
        pfd = ref * (2 if ref_doubler else 1) / (r * (2 if ref_div2 else 1))
        if pfd <= MAX_PFD:
            break
    if out == "B":
        if not 6.8e9 <= freq <= 13.6e9:
            raise ValueError("RFoutB covers 6.8-13.6 GHz")
        vco, div_sel = freq / 2, 0
    else:
        if not MIN_VCO / 64 <= freq <= MAX_VCO:
            raise ValueError("RFoutA covers 53.125 MHz-6.8 GHz")
        vco, div_sel = freq, 0
        while vco < MIN_VCO:
            vco *= 2
            div_sel += 1
    integer, f1, f2, m2 = fract_n(vco, pfd)
    pfd_i = int(pfd)

    R = {}
    cp = max(0, min(15, round((cp_ua - 315) / 315)))
    R[4] = (0 << 4) | (0 << 5) | (0 << 6) | (1 << 7) | (1 << 8) | (0 << 9) | (cp << 10) | (1 << 14) | \
           ((r & 0x3FF) << 15) | (int(ref_div2) << 25) | (int(ref_doubler) << 26) | ((muxout & 7) << 27) | 4
    R[5] = 0x00800025
    R[7] = (0 << 4) | (3 << 5) | (0 << 7) | (0 << 8) | (1 << 25) | 0x10000007
    R[8] = 0x102D0428
    t = max(1, min(1023, ceil(pfd_i / (20000 * 30))))
    R[9] = (t << 14) | ((ceil(pfd_i * 2 / (100000 * t)) & 0x1F) << 4) | ((ceil(pfd_i * 5 / (100000 * t)) & 0x1F) << 9) | \
           ((ceil(pfd_i / 2400000) & 0xFF) << 24) | 9
    adc = max(1, min(255, ceil((pfd_i / 100000 - 2) / 4)))
    R[10] = (1 << 4) | (1 << 5) | (adc << 6) | 0x00C0000A
    R[11] = 0x0061300B
    R[12] = (1 << 16) | 0x0000041C

    prescaler = integer >= 75
    neg_bleed = not (f1 == 0 and f2 == 0)
    bleed = max(1, min(255, ceil(400 * cp_ua / (integer * 375))))
    R[0] = ((integer & 0xFFFF) << 4) | (int(prescaler) << 20) | (1 << 21)
    R[1] = ((f1 & 0xFFFFFF) << 4) | 1
    R[2] = ((m2 & 0x3FFF) << 4) | ((f2 & 0x3FFF) << 18) | 2
    R[3] = 3
    R[6] = ((outa_power & 3) << 4) | (int(outa_en) << 6) | (int(not outb_en) << 10) | (int(mute_till_lock) << 11) | \
           ((bleed & 0xFF) << 13) | ((div_sel & 7) << 21) | (1 << 24) | (int(neg_bleed) << 29) | 0x14000006
    info = dict(ref=ref, r=r, pfd=pfd, vco=vco, int=integer, frac1=f1, frac2=f2, mod2=m2,
                actual=(pfd * (integer + (f1 + f2 / m2) / MOD1)) * (2 if out == "B" else 1) / (2 ** div_sel),
                outa_en=outa_en, outb_en=outb_en)
    return R, info


def write_order(R):
    """Start-up order from the datasheet and driver: R12 down to R0 (R0 last starts the VCO calibration)."""
    return [R[i] for i in range(12, -1, -1)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("freq", type=float)
    ap.add_argument("--ref", type=float, default=100e6)
    ap.add_argument("--out", choices="AB", default="B")
    ap.add_argument("--off", action="store_true", help="compute with both outputs disabled")
    a = ap.parse_args()
    kw = dict(outa_en=False, outb_en=False) if a.off else {}
    R, info = registers(a.freq, a.ref, a.out, **kw)
    for k, v in info.items():
        print(f"{k:8s} {v}")
    for i in range(12, -1, -1):
        print(f"R{i:<2d} 0x{R[i]:08X}")
