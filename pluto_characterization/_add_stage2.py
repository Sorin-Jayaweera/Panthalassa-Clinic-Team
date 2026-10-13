from pathlib import Path

p = Path(__file__).resolve().parent / "overnight.py"
s = p.read_text(encoding="utf-8")
assert "if_band_map" not in s
new = r'''
# ------------------------------------------------------------------ second set of blocks (added 22:30 on 12 Oct)
def an_for(level):
    """Analyzer reference level and preamp for a tone of about this level (dBm)."""
    if level > -12:
        return 10, False
    if level > -32:
        return -10, False
    return -30, True


@block("leak_vs_level")
def b_leak():
    """LO leakage and other sideband against attenuation setting and tone scale, with a 300 Hz bandwidth."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        lo = f - 1e6
        for att in (0, 10, 20, 30, 40, 50, 60):
            for s in (1.0, 0.5, 0.2, 0.1, 0.05, 0.02):
                rl, pre = an_for(6 - att + 20 * np.log10(s))
                for lab, c in (("tone", f), ("LO", lo), ("other sideband", lo - 1e6)):
                    measure("leak_vs_level", f, att, scale=s, span=50e3, rbw=300, rl=rl, preamp=pre, read_at=c * (1 - 12.8e-6), note=lab)


@block("close_in")
def b_closein():
    """Spectrum close to the tone at four spans, and the same spans with the tone off."""
    for f in (1.1e9, 1.0e9, 1.2e9):
        for att in (0, 20):
            if key("close_in", f, att, 0.5, 1e6, "span 1000") in SAVED:
                continue
            maybe_ref()
            fm, _ = tone_freq(f, att, block="close_in_find")
            for span, rbw in ((1e6, 3e3), (100e3, 300), (10e3, 30), (1e3, 10)):
                def go():
                    an_set(fm, span, 10, rbw, False)
                    sweep()
                    return trace()
                fr, y = an_do(go)
                save_trace(f"closein_{f/1e6:.0f}MHz_att{att}_span{span:.0f}", fr, y)
                log("close_in", f, att, 0.5, 1e6, fm, fr[np.argmax(y)], y.max(), f"span {span:.0f}")
    pluto(1.1e9, 89.75, scale=0.0)
    for span, rbw in ((1e6, 3e3), (100e3, 300), (10e3, 30), (1e3, 10)):
        fr, y = an_do(lambda: (an_set(1.1e9, span, 10, rbw, False), sweep(), trace())[2])
        save_trace(f"closein_tone_off_span{span:.0f}", fr, y)


@block("offset_more")
def b_offset2():
    """Tone offset test at four more LO frequencies."""
    for lo in (1.0e9, 1.2e9, 0.4e9, 2.0e9):
        for off in (0.5e6, 1e6, 2e6, 5e6, 8e6, 10e6, -1e6, -5e6):
            for lab, c in (("tone", lo + off), ("other sideband", lo - off), ("LO", lo)):
                measure("offset_more", lo + off, 0, offset=off, span=100e3, rbw=1e3, read_at=c * (1 - 12.8e-6), note=lab)
    pluto(1.1e9, 20)


@block("low_more")
def b_low2():
    """Low-level readings at every 100 MHz, fewer settings than the first low-level block."""
    for f in np.arange(500e6, 1900e6 + 1, 100e6):
        if f in (1.0e9, 1.1e9, 1.2e9):
            continue
        for att in (0, 10, 20, 30, 40):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=10, note="rl+10")
        for att in (20, 30, 40, 50, 60):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=-10, note="rl-10")
        for att in (40, 50, 60, 70, 80, 89.75):
            measure("low_more", float(f), att, span=100e3, rbw=1e3, rl=-30, preamp=True, note="rl-30 preamp")
    an_do(lambda: an_set(1.1e9, 2e6, 10, None, False))


@block("tune_step")
def b_tunestep():
    """Ask for small frequency changes and read what the tone does."""
    for base in (1.1e9, 1.0e9):
        for k in (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 0):
            pluto(base + k, 20)

            def go():
                an_set(base * (1 - 12.8e-6), 20e3, 10, None, False)
                sweep()
                f1, _ = peak()
                an_set(f1, 1e3, 10, 10, False)
                sweep()
                return peak()
            fm, lv = an_do(go)
            log("tune_step", base + k, 20, 0.5, 1e6, base, fm, lv, f"asked +{k} Hz")
            maybe_ref()


@block("if_band_map")
def b_ifband():
    """Level table for the IF band: every 1 MHz from 1000 to 1200 MHz, attenuation 0 to 40 dB in 2 dB steps."""
    for f in np.arange(1000e6, 1200e6 + 1, 1e6):
        for att in range(40, -1, -2):
            measure("if_band", float(f), att, span=200e3, rbw=3e3)


@block("if_band_scale")
def b_ifscale():
    """Tone scale 0.1 to 1.0 at every 10 MHz in the IF band, at 0, 10 and 20 dB."""
    for f in np.arange(1000e6, 1200e6 + 1, 10e6):
        for att in (20, 10, 0):
            for s in (0.1, 0.2, 0.3, 0.5, 0.7, 1.0):
                measure("if_band_scale", float(f), att, scale=s, span=200e3, rbw=3e3)

'''
s = s.replace("\ndef hourly(tag):", new + "\ndef hourly(tag):")
old = "b_wide, b_map, b_map1):"
assert old in s
s = s.replace(old, "b_wide, b_map, b_map1,\n                  b_leak, b_closein, b_offset2, b_tunestep, b_low2, b_ifscale, b_ifband):")
p.write_text(s, encoding="utf-8")
print("ok")
