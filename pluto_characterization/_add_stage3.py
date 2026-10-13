from pathlib import Path

p = Path(__file__).resolve().parent / "overnight.py"
s = p.read_text(encoding="utf-8")
assert "def b_pulse" not in s
new = r'''
# ------------------------------------------------------------------ third set: pulsed output (added 23:00 on 12 Oct)
RC_PY = r"C:\Users\Sorin\radioconda\python.exe"
PULSE = str(HERE.parent / "sdr" / "pluto_pulse.py")
STOPF = HERE / "pulse_stop.flag"


def pulse_start(f, att, width, period, amp=0.5):
    """Start sdr/pluto_pulse.py (it needs the radioconda Python) and wait until it says the pulse train is running."""
    if STOPF.exists():
        STOPF.unlink()
    pr = subprocess.Popen([RC_PY, "-u", PULSE, "--freq", str(f), "--att", str(att), "--width", str(width), "--period", str(period), "--amp", str(amp),
                           "--seconds", "90", "--stop-file", str(STOPF), "--floor", "0"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    line = ""
    for _ in range(40):
        line = pr.stdout.readline()
        if not line or "PULSING" in line:
            break
    if "PULSING" not in line:
        pr.kill()
        raise RuntimeError("pulse script did not start: " + line.strip()[:120])
    time.sleep(0.5)
    return pr, line.strip()


def pulse_stop(pr):
    STOPF.write_text("stop")
    try:
        pr.wait(20)
    except subprocess.TimeoutExpired:
        pr.kill()
    if STOPF.exists():
        STOPF.unlink()
    pl.clear()                 # the tone generator was switched off by the pulse script; everything must be sent again


def zero_span(centre, rbw, swt, rl=10, trig=None):
    """Level against time at one frequency. Returns (time axis in seconds, levels, sweep time the analyzer actually used)."""
    an_set(centre, 0, rl, rbw, False)
    A.write(f":SWE:TIME {swt}")
    if trig is None:
        A.write(":TRIG:SOUR IMM")
    else:
        A.write(":TRIG:SOUR VID")
        A.write(f":TRIG:VID:LEV {trig}")
    time.sleep(0.3)
    used = float(A.query(":SWE:TIME?"))
    A.write(":INIT:IMM")
    time.sleep(1.3 * used + 0.3)
    A.query("*OPC?")
    y = np.array([float(x) for x in A.query(":TRAC:DATA? 1").strip().strip(",").split(",")])
    return np.linspace(0, used, len(y)), y, used


def an_normal():
    A.write(":TRIG:SOUR IMM")
    A.write(":SWE:TIME:AUTO ON")
    an.clear()
    A.write(":INIT:CONT OFF")


@block("pulse")
def b_pulse():
    """Pulsed output from the Pluto (constant samples for the pulse, zeros between). What the spectrum analyzer can show of it:
    level during the pulse, level between pulses, pulse width, and the pulse spectrum."""
    f = 1.1e9
    try:
        # 1. long pulses: level during and between pulses, against attenuation and amplitude
        for att in (0, 20):
            for amp in (0.25, 0.5, 1.0):
                pr, info = pulse_start(f, att, 500e-6, 2e-3, amp)
                try:
                    t, y, used = an_do(lambda: zero_span(f, 300e3, 8e-3, trig=None))
                    save_trace(f"pulse_long_att{att}_amp{amp}", t * 1e6, y)
                    on, off = float(np.percentile(y, 97)), float(np.percentile(y, 20))
                    log("pulse", f, att, amp, 0, f, f, on, f"500 us pulse every 2 ms: level during the pulse; {info}")
                    log("pulse", f, att, amp, 0, f, f, off, "500 us pulse every 2 ms: level between pulses (300 kHz bandwidth)")
                    t, y, used = an_do(lambda: zero_span(f, 1e3, 40e-3, trig=None))
                    log("pulse", f, att, amp, 0, f, f, float(np.percentile(y, 20)), "500 us pulse every 2 ms: 1 kHz bandwidth, 20th percentile (average-like)")
                finally:
                    pulse_stop(pr)
        # 2. shorter pulses in zero span with the widest bandwidth (1 MHz) and a video trigger
        for width in (100e-6, 20e-6, 10e-6, 5e-6, 2e-6, 1e-6):
            pr, info = pulse_start(f, 0, width, max(20 * width, 200e-6), 0.5)
            try:
                for swt in (max(4 * width, 20e-6), max(20 * width, 100e-6)):
                    t, y, used = an_do(lambda: zero_span(f, 1e6, swt, trig=-25))
                    save_trace(f"pulse_w{width*1e6:.0f}us_swt{used*1e6:.0f}us", t * 1e6, y)
                    half = y.max() - 6
                    above = t[y > half]
                    w = float(above.max() - above.min() + (t[1] - t[0])) if len(above) else 0.0
                    log("pulse_width", f, 0, 0.5, 0, f, w * 1e9, float(y.max()), f"asked {width*1e6:.2f} us; freq_meas_hz column = width in ns between -6 dB points; sweep {used*1e6:.1f} us; {info}")
            finally:
                pulse_stop(pr)
        an_do(an_normal)
        # 3. pulse spectrum: the nulls are at 1/width from the centre
        for width in (1.2e-6, 0.5e-6, 0.2e-6, 0.1e-6, 65e-9, 32.5e-9):
            pr, info = pulse_start(f, 0, width, 100e-6, 0.5)
            try:
                for span, rbw in ((20e6, 100e3), (40e6, 100e3)):
                    fr, y = an_do(lambda: (an_set(f, span, 10, rbw, False), sweep(), trace())[2])
                    save_trace(f"pulse_spectrum_w{width*1e9:.0f}ns_span{span/1e6:.0f}MHz", fr, y)
                    log("pulse_spectrum", f, 0, 0.5, 0, f, fr[np.argmax(y)], float(y.max()), f"asked {width*1e9:.1f} ns every 100 us; span {span/1e6:.0f} MHz; {info}")
            finally:
                pulse_stop(pr)
    finally:
        an_do(an_normal)
        pl.clear()
    # 4. is the tone generator back?
    r = measure("pulse_check", 1.1e9, 20, span=200e3, rbw=3e3, resume=False, note="tone generator after the pulse tests")
    if r[1] < -25:
        say("TONE NOT RESTORED after pulse tests, level", r[1])
        for ch in ("altvoltage0", "altvoltage1", "altvoltage2", "altvoltage3"):
            attr("-c", DDS, ch, "raw", "1")
        pl.clear()
        r = measure("pulse_check", 1.1e9, 20, span=200e3, rbw=3e3, resume=False, note="tone generator after forcing it on")
        say("after forcing on:", r[1])

'''
s = s.replace("\ndef hourly(tag):", new + "\ndef hourly(tag):")
old = "b_leak, b_closein, b_offset2, b_tunestep, b_low2, b_ifscale, b_ifband):"
assert old in s
s = s.replace(old, "b_leak, b_closein, b_offset2, b_tunestep, b_low2, b_ifscale, b_ifband, b_pulse):")
p.write_text(s, encoding="utf-8")
print("ok")
