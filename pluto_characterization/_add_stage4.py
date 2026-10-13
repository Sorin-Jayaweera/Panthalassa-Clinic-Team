from pathlib import Path

p = Path(__file__).resolve().parent / "overnight.py"
s = p.read_text(encoding="utf-8")
assert "def b_pulse2" not in s
new = r'''
@block("pulse_spectrum_peak")
def b_pulse2():
    """Pulse spectrum again, with the positive-peak detector and a 3 s sweep so every trace point sees at least 40 pulses.
    (The first attempt used a fast sweep; each point then caught a pulse or missed it, and the trace was too ragged to find the nulls.)"""
    f = 1.1e9
    try:
        for width in (5e-6, 2e-6, 1.2e-6, 1e-6, 0.5e-6, 0.3e-6, 0.2e-6, 0.13e-6, 0.1e-6, 65e-9, 32.5e-9):
            for amp in ((0.5, 1.0) if width in (1.2e-6, 0.1e-6) else (0.5,)):
                pr, info = pulse_start(f, 0, width, 100e-6, amp)
                try:
                    for span in (10e6, 40e6):
                        def go():
                            an_set(f, span, 10, 100e3, False)
                            A.write(":DET:TRAC1 POS")
                            A.write(":SWE:TIME 3")
                            time.sleep(0.3)
                            sweep()
                            return trace()
                        fr, y = an_do(go)
                        save_trace(f"pulsepk_w{width*1e9:.0f}ns_amp{amp}_span{span/1e6:.0f}MHz", fr, y)
                        log("pulse_spectrum_peak", f, 0, amp, 0, f, fr[np.argmax(y)], float(y.max()), f"asked {width*1e9:.1f} ns every 100 us; span {span/1e6:.0f} MHz; peak detector, 3 s sweep; {info}")
                finally:
                    pulse_stop(pr)
        # the same spans with a continuous tone from the buffer-free tone generator, for the level reference
        pluto(1.1e9, 0)
        fr, y = an_do(lambda: (an_set(f, 10e6, 10, 100e3, False), sweep(), trace())[2])
        save_trace("pulsepk_cw_reference_span10MHz", fr, y)
        log("pulse_spectrum_peak", f, 0, 0.5, 1e6, f, fr[np.argmax(y)], float(y.max()), "continuous tone, same analyzer settings")
    finally:
        def back():
            A.write(":DET:TRAC1 NORM")
            an_normal()
        an_do(back)
        pl.clear()
    measure("pulse_check", 1.1e9, 20, span=200e3, rbw=3e3, resume=False, note="tone generator after the second pulse test")

'''
s = s.replace("\ndef hourly(tag):", new + "\ndef hourly(tag):")
old = "b_ifscale, b_ifband, b_pulse):"
assert old in s
s = s.replace(old, "b_ifscale, b_ifband, b_pulse, b_pulse2):")
p.write_text(s, encoding="utf-8")
print("ok")
