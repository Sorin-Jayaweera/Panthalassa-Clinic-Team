"""Pluto tab: second and third sets of overnight blocks. Filled from overnight_summary.json (passed in as N)."""
from content import table, ul, ol, p, h, math, fig, D


def n(v, d=2):
    if v is None or v != v:
        return D
    return f"{v:.{d}f}".replace("-", "&minus;")


def learned_rows(N):
    rows = []
    if "leak" in N:
        rows.append(["LO leakage at low levels", "The LO leakage is about &minus;60 dBm at 0 and 10 dB attenuation whatever the tone scale, &minus;68 dBm at 20 dB, &minus;78 dBm at 30 and 40 dB, then falls 1 dB per dB. "
                     "With a small tone scale it is close to the tone: at 0 dB attenuation and scale 0.02 the tone is &minus;28 dBm and the LO leakage only 31 dB under it.",
                     "To get a low level, raise the attenuation and keep the tone scale at 0.2 to 0.5. Do not use a small tone scale at low attenuation."])
    if "if_band" in N:
        b = N["if_band"]
        rows.append(["IF band table", f"1000 to 1200 MHz in 1 MHz steps, attenuation 0 to 40 dB in 2 dB steps ({b['n']} readings). At 0 dB the output is {n(b['att0'][0])} to {n(b['att0'][1])} dBm. "
                     f"It changes by at most {n(b['largest_change_per_mhz'])} dB from one MHz to the next.",
                     "Use <code>pluto_if_band_table.csv</code> to turn a setting into dBm for any IF-band test."])
    if "tune" in N:
        rows.append(["Tuning step", "A request for 5 Hz more moves the tone by about 5 to 7 Hz; 1 kHz more moves it 1001 Hz. During the test the tone was also drifting by 2 to 8 Hz per second.",
                     "Frequency can be set to a few Hz. Drift, not step size, limits how well the frequency is known."])
    if "close_in" in N:
        rows.append(["Noise close to the tone", "30 to 45 kHz from the tone the noise is about &minus;96 dBc/Hz, and 300 to 450 kHz away about &minus;107 dBc/Hz. One pair of lines 1.4 kHz either side of the 1000 MHz tone, 59 dB under it; none at 1100 or 1200 MHz.",
                     "This is near what the spectrum analyzer itself contributes, so the Pluto is at least this good. It is not a limit for the planned tests."])
    if "pulse_check" not in N:
        rows.append(["Pulsed output", "Not measured. The pulse script <code>sdr\\pluto_pulse.py</code> is written but the Pluto dropped off USB before the pulse block ran.", "Run the pulse block the next time the Pluto is on the spectrum analyzer or, better, on the SM200B."])
    rows.append(["USB, second dropout", "Dropped off USB a second time at 23:51 on 12 Oct, after 2 h 20 min of continuous use. Both times it stopped answering during a frequency change and then disappeared from Windows.",
                 "Any long run needs someone able to replug it, or a powered USB hub that can be switched from the computer."])
    return rows


def night2(N):
    out = []
    if "if_band" in N:
        b = N["if_band"]
        out += [h("IF band table: 1000 to 1200 MHz in 1 MHz steps"), fig("pluto_if_band.png", "Pluto output across 1000 to 1200 MHz in 1 MHz steps, and departure from 1 dB per dB"),
                ul([f"{b['freqs']} frequencies &times; {b['atts']} attenuation settings (0 to 40 dB in 2 dB steps) = {b['n']} readings. Tone scale 0.5, bandwidth 3 kHz.",
                    f"At 0 dB: {n(b['att0'][0])} dBm (lowest, at {n(b['att0_min_at'], 0)} MHz) to {n(b['att0'][1])} dBm (highest, at {n(b['att0_max_at'], 0)} MHz).",
                    f"At 20 dB: {n(b['att20'][0])} to {n(b['att20'][1])} dBm.",
                    f"Departure from 1 dB per dB (relative to the 20 dB reading): {n(b['dep0'][0])} to {n(b['dep0'][1])} dB at 0 dB; {n(b['dep40'][0])} to {n(b['dep40'][1])} dB at 40 dB.",
                    f"Largest change between neighbouring 1 MHz points: {n(b['largest_change_per_mhz'])} dB. A straight line between table points is good to under 0.1 dB.",
                    "Full table: <code>pluto_characterization\\pluto_if_band_table.csv</code>."]),
                table(["Frequency (MHz)", "0 dB", "4 dB", "10 dB", "20 dB", "30 dB", "40 dB"], [[n(r[0], 0)] + [n(x) for x in r[1:]] for r in b["rows"]], cls="lut", left=()),
                p("Output in dBm. Every tenth frequency shown.")]
    if "if_scale" in N:
        out += [h("IF band: tone scale 1.0"),
                table(["Frequency (MHz)", "Scale 1.0 at 0 dB (dBm)", "Short of +6.02 dB (dB)", "Scale 1.0 at 10 dB (dBm)", "Short of +6.02 dB (dB)", "Scale 1.0 at 20 dB (dBm)", "Short of +6.02 dB (dB)"],
                      [[n(r[0], 0)] + [n(x) for x in r[1:]] for r in N["if_scale"]], cls="lut", left=()),
                p("&ldquo;Short of +6.02 dB&rdquo; is the scale 1.0 reading minus the scale 0.5 reading minus 6.02 dB. Zero means the output doubled in voltage as it should. "
                  "At 0 dB attenuation the output is 0.35 to 1.0 dB short: the highest output in the IF band is +4.25 to +5.8 dBm. At 10 and 20 dB it is within 0.12 dB.")]
    if "map_s1" in N:
        pass
    if "leak" in N:
        lk = [r for r in N["leak"] if r[0] == 1100]
        out += [h("LO leakage and other sideband against level"), fig("pluto_leak.png", "LO leakage against attenuation setting, and other sideband relative to the tone, at four tone scales"),
                table(["Attenuation (dB)", "Tone scale", "Tone (dBm)", "LO leakage (dBm)", "LO leakage (dB rel. tone)", "Other sideband (dBm)", "Other sideband (dB rel. tone)"],
                      [[n(r[1], 0), r[2]] + [n(x, 1) for x in r[3:]] for r in lk], cls="lut", left=()),
                ol(["Tone at 1100 MHz, LO at 1099 MHz, other sideband at 1098 MHz. Each read with a 300 Hz bandwidth, 50 kHz span.",
                    "The analyzer reference level was chosen from the expected tone level: +10 dBm, &minus;10 dBm, or &minus;30 dBm with the preamp.",
                    "Analyzer noise with the preamp is about &minus;118 dBm, so sideband readings near that value are limits."]),
                ul(["The LO leakage does not depend on the tone scale. It is set by the attenuation setting only.",
                    "From 0 to 10 dB attenuation it stays near &minus;60 dBm. From 40 dB up it falls 1 dB per dB.",
                    "The other sideband follows the tone: 64 to 72 dB under it at scale 0.5 to 1.0.",
                    "Same pattern at 1000 and 1200 MHz (in <code>overnight_summary.json</code>)."])]
    if "offset_more" in N:
        out += [h("Tone offset at other LO frequencies"),
                table(["LO (MHz)", "Offset (MHz)", "Tone (dBm)", "LO leakage (dB rel. tone)", "Other sideband (dB rel. tone)"], [[n(r[0], 0), n(r[1], 1), n(r[2]), n(r[3], 1), n(r[4], 1)] for r in N["offset_more"]], cls="lut", left=()),
                p("Attenuation 0 dB, tone scale 0.5, bandwidth 1 kHz. The other sideband is 57 to 76 dB under the tone at every LO tried; it is worst at 2000 MHz (57 to 61 dB under).")]
    if "low_more" in N:
        out += [h("Low level at every 100 MHz"),
                table(["Frequency (MHz)", "0 dB", "10", "20", "30", "40", "50", "60", "70", "80", "89.75 dB", "Largest departure, 20 to 89.75 dB (dB)"],
                      [[n(r[0], 0)] + [n(x) for x in r[1:]] for r in N["low_more"]], cls="lut", left=()),
                p("Output in dBm. Three analyzer settings tied together as in the low level test above. 1000, 1100 and 1200 MHz are in that test.")]
    if "tune" in N:
        out += [h("Tuning step"),
                table(["Base (MHz)", "Asked for (Hz above base)", "Tone moved (Hz)", "Tone moved, drift removed (Hz)"], [[n(r[0], 0), n(r[1], 0), n(r[2], 0), n(r[3], 0)] for r in N["tune"]], cls="lut", left=()),
                ol(["The tone was asked to move by 1 Hz to 5 kHz and read in a 1 kHz span with a 10 Hz bandwidth.",
                    "The first and last rows of each set both ask for +0 Hz. The tone had moved between them: " + "; ".join(f"{n(d[1], 0)} Hz in {n(d[2], 0)} s at {n(d[0], 0)} MHz" for d in N["tune_drift"]) + ".",
                    "That drift is taken as a straight line in time and subtracted in the last column."]),
                p("With the drift removed the tone follows requests of 50 Hz and more within about 10 Hz at 1000 MHz. The 1100 MHz set drifted faster and is less clear. The LO setting has a resolution of a few Hz; drift is the larger effect.")]
    if "close_in" in N:
        out += [h("Spectrum close to the tone"), fig("pluto_close_in.png", "Spectrum within 500 kHz, 50 kHz, 5 kHz and 500 Hz of the tone, with the analyzer's own noise"),
                table(["Tone (MHz)", "Span (kHz)", "Bandwidth (Hz)", "Noise at 30 to 45% of the span from the tone (dB rel. tone)", "Same, per Hz (dBc/Hz)", "Largest point beyond 10% of the span (dB rel. tone)"],
                      [[r[0], n(r[1] / 1e3, 0), n(r[2], 0), n(r[3], 1), n(r[4], 1), n(r[5], 1)] for r in N["close_in"]], left=()),
                math(r"L(\Delta f) = P_\text{noise} - P_\text{tone} - 10\log_{10}(B)"),
                p("\\(B\\) = analyzer bandwidth in Hz. The black trace is the analyzer with the tone off: its noise floor, but not its phase noise, which only appears when a signal is present. "
                  "The Siglent's own phase noise is specified near &minus;98 dBc/Hz at 10 kHz, so these numbers are an upper limit on the Pluto, not its true value.")]
    if "pulse" in N or "pulse_width" in N:
        out += [h("Pulsed output")]
        if "pulse" in N:
            out += [table(["Attenuation (dB)", "Amplitude", "Level (dBm)", "What"], [[n(r[0], 0), r[1], n(r[2]), r[3]] for r in N["pulse"]], left=(3,))]
        if "pulse_width" in N:
            out += [fig("pluto_pulse_time.png", "Pulses of 100 to 1 microsecond seen in zero span"),
                    table(["Asked", "Width between &minus;6 dB points (ns)", "Peak (dBm)", "Sweep"], N["pulse_width"], left=(0, 3))]
        if "pulse_spectrum" in N:
            out += [fig("pluto_pulse_spectrum.png", "Spectrum of pulses from 1200 ns down to 33 ns"),
                    table(["Asked width (ns)", "Peak (dBm)", "First null above (MHz)", "First null below (MHz)"], [[r[0], n(r[1]), n(r[2]), n(r[3])] for r in N["pulse_spectrum"]], left=()),
                    math(r"\tau = \frac{1}{\Delta f_\text{null}}")]
    return "".join(out)
