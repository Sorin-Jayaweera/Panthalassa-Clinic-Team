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
    if "pulse_peak" in N:
        rows.append(["Pulsed output", "Works. Level during a pulse equals the continuous-tone level. Width and spacing are correct for pulses from 100 &micro;s down to 300 ns (checked from the spectrum nulls). "
                     "Below about 100 ns the pulse comes out wider and lower than asked, because the RF bandwidth setting is 18 MHz. Between pulses only the LO leakage remains (about 60 dB under the pulse at 0 dB attenuation).",
                     "Use <code>sdr\\pluto_pulse.py</code> for pulse tests of 300 ns and longer. For 50 ns pulses the sample rate and bandwidth must be raised and rechecked. The spectrum analyzer cannot show pulse shape under 10 &micro;s; use a detector and the oscilloscope."])
    rows.append(["Warm-up", "From plugged in (chip 27 &deg;C) to settled (32 &deg;C): level fell 0.11 dB in the first 28 minutes; frequency error went from &minus;10.2 ppm to &minus;12.0 ppm in 20 minutes and &minus;12.6 ppm after 2 hours.",
                 "Let it run 30 minutes before a level-critical test and an hour before a frequency-critical one."])
    rows.append(["The RF connection", "On 13 Oct after replugging, every level read 0.3 to 0.5 dB higher than the night before, and 1 to 3.5 dB higher from 1250 to 1750 MHz. "
                 "At 11:31 the computer was moved; the level stepped down 0.45 dB and the whole table then matched the night before within 0.06 dB below 1400 MHz. The Pluto had not changed. The cable or a connector had.",
                 "Tighten the SMA connectors and do not move the cable during a test. Take the without-part reference with the same cable, in the same position, on the same day. The dip near 1450 to 1700 MHz in the frequency sweep may be the cable, not the Pluto."])
    rows.append(["Look up function", "<code>sdr\\pluto_level.py</code>: <code>pluto_dbm(freq, att, scale)</code> gives the output in dBm from the measured 1.0 to 1.2 GHz table; <code>pluto_setting(freq, want_dbm)</code> gives the attenuation setting for a wanted level.",
                 "Use it to turn settings into power when analysing a chain test. Good to about 0.5 dB across days."])
    rows.append(["Not measured", "Pulse rise time (the spectrum analyzer cannot resolve under 10 &micro;s). The line near 3 &times; LO for 1.0 to 1.2 GHz tones (3.0 to 3.6 GHz is above the analyzer's range).",
                 "Rise time: a detector on the oscilloscope, or the SM200B. 3 &times; LO: the SM200B."])
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
    if "pulse" in N:
        on = {(r[0], r[1]): r[2] for r in N["pulse"] if "during" in r[3]}
        off = [r[2] for r in N["pulse"] if "between pulses (300" in r[3]]
        out += [h("Pulsed output, 13 Oct"),
                p("Script <code>sdr\\pluto_pulse.py</code>. The Pluto is sent a repeating block of samples: a constant value for the pulse, zeros between pulses. "
                  "The RF is at the LO frequency during the pulse. Sample rate 30.72 MS/s, so the width is a whole number of 32.55 ns samples. Same wiring: Pluto TX straight into the spectrum analyzer. 1100 MHz."),
                h("Level during the pulse"),
                table(["Attenuation (dB)", "Amplitude", "Level during the pulse (dBm)", "Continuous tone at the same setting (dBm)"],
                      [[n(k[0], 0), k[1], n(v), {(0.0, 0.5): "0.10", (0.0, 1.0): "4.7 (12 Oct)", (20.0, 0.5): "&minus;18.93", (20.0, 1.0): "&minus;13.3 (12 Oct)"}.get(k, D)] for k, v in on.items()], left=()),
                ul(["500 &micro;s pulse every 2 ms, read in zero span with a 300 kHz bandwidth.",
                    "The pulse level matches the continuous tone within 0.2 dB where both were read in the same hour (amplitude 0.5). The amplitude 1.0 tone values are from the night before; that morning every level read 0.3 to 0.5 dB higher because of the RF connection (see below).",
                    f"Between pulses the reading is {n(max(off), 1)} to {n(min(off), 1)} dBm, which is the analyzer's noise in this bandwidth. The pulse is at least 55 dB above it. "
                    "The LO leakage (about &minus;60 dBm at 0 dB attenuation, from the continuous-tone tests) is still there between pulses, so the true on/off ratio at 0 dB attenuation is about 60 dB."])]
    if "pulse_width" in N:
        out += [h("Pulse shape in time"), fig("pluto_pulse_time.png", "Pulses of 100 to 1 microsecond at 1100 MHz seen in zero span"),
                table(["Asked width (&micro;s)", "Measured width between &minus;6 dB points (&micro;s)", "Time between pulses (&micro;s)", "Peak reading (dBm)", "Level between pulses (dBm)"],
                      [[r[0], n(r[1], 0), n(r[2], 0), n(r[3]), n(r[4], 1)] for r in N["pulse_width"]], left=()),
                ul(["Analyzer zero span, 1 MHz bandwidth (its widest), video trigger. Its shortest sweep is 900 &micro;s, which is one point every 1.2 &micro;s.",
                    "Pulses of 10 &micro;s and longer are shown correctly: right width, right spacing (400 &micro;s for the 20 &micro;s pulse, 200 &micro;s for the others), flat top at +0.2 to +0.3 dBm.",
                    "Pulses of 5 &micro;s and shorter read low (&minus;1.9, &minus;11.3, &minus;19.8 dBm). That is the analyzer: one point every 1.2 &micro;s and a 1 MHz filter cannot follow them. It is not the Pluto; see the spectrum below.",
                    "This analyzer cannot show the shape of the 50 ns to 1.2 &micro;s pulses the design uses. That needs a detector and the oscilloscope, or the SM200B."])]
    if "pulse_peak" in N:
        nulls = {r[0]: r for r in N.get("pulse_spectrum", [])}
        out += [h("Pulse spectrum"), fig("pluto_pulse_spectrum.png", "Spectrum of pulses from 2000 ns down to 32 ns"),
                table(["Asked width (ns)", "Samples", "Actual width (ns)", "Peak in 100 kHz bandwidth (dBm)", "Relative to a continuous tone (dB)", "Departure from 20 log10(width) (dB)", "First null, measured (MHz)", "First null, expected 1/width (MHz)"],
                      [[n(r[0], 0 if r[0] >= 100 else 1), r[1], n(r[2], 1), n(r[4]), n(r[5]), n(r[6]),
                        (n((nulls[str(int(r[0]))][2] + nulls[str(int(r[0]))][3]) / 2) if str(int(r[0])) in ("1200", "1000", "500", "300") and None not in nulls[str(int(r[0]))][2:] else D),
                        n(1e3 / r[2])] for r in N["pulse_peak"] if r[3] == 0.5], left=()),
                ol(["One pulse every 100 &micro;s, attenuation 0 dB, amplitude 0.5. Analyzer: 100 kHz bandwidth, positive-peak detector, 3 s sweep, so each point of the trace sees about 40 pulses and keeps the largest.",
                    "A first attempt with a normal fast sweep gave a ragged trace (each point either caught a pulse or missed it). Those traces are saved as <code>pulse_spectrum_*</code> and are not used.",
                    "The spectrum of a rectangular pulse of width &tau; has nulls at multiples of 1/&tau; from the centre. The null positions were found from the trace and compared with 1/&tau;.",
                    "In a bandwidth narrower than 1/&tau; the peak reading falls 20 dB for each tenfold drop in width. The departure column is the reading minus that rule, taking the 1000 ns pulse as the reference."]),
                math(r"\Delta f_\text{null} = \frac{1}{\tau} \qquad P_\text{peak}(\tau) = P_\text{peak}(\tau_0) + 20\log_{10}\!\left(\frac{\tau}{\tau_0}\right)"),
                ul(["The 5000 ns pulse is wider than the analyzer filter can treat as short, so the 20 log rule does not apply to it.", "From 2000 ns down to 300 ns the nulls are where 1/&tau; says and the peak follows the 20 log rule within 0.3 dB. The Pluto makes these pulses with the right width and full amplitude.",
                    "For 200 ns the first null (5.1 MHz expected) can be seen in the plot near 5 MHz.",
                    "Below about 130 ns the departure grows (+0.9 dB at 130 ns, +1.5 dB at 65 ns, +4.3 dB at one sample). The spectrum is cut off beyond about &plusmn;10 MHz: the Pluto's RF bandwidth setting is 18 MHz. A pulse shorter than about 100 ns comes out wider and lower than asked.",
                    "To make the 50 ns pulses the design calls for, the Pluto's sample rate and RF bandwidth would have to be raised. That has not been tried and would need its own check.",
                    "After each pulse test the normal tone generator was switched back on and read: &minus;18.82 and &minus;18.99 dBm at 20 dB, as before."])]
    out += [h("Warm-up and repeatability, 13 Oct"),
            p("The Pluto was replugged at 10:59 on 13 Oct after 11 hours unpowered. The drift log ran from 11:02 to 13:03: level and frequency at 1100 MHz, 20 dB, every 23 s, with the level table and frequency sweep repeated at 11:00, 11:04 and 12:06."),
            table(["Time", "Level at 1100 MHz, 20 dB (dBm)", "Frequency error (ppm)", "Chip temperature (&deg;C)"],
                  [["11:02", "&minus;18.89", "&minus;10.24", "27.2"], ["11:22", "&minus;19.03", "&minus;11.95", "30.7"], ["11:30", "&minus;19.00", "&minus;12.1", "31.6"],
                   ["11:31:32", "step to &minus;19.32, then &minus;19.48", "no change", "31.6"], ["11:54", "&minus;19.46", "&minus;12.38", "32.5"], ["12:27", "&minus;19.46", "&minus;12.51", "32.5"], ["13:00", "&minus;19.44", "&minus;12.57", "31.6"]], left=()),
            ul(["Warm-up, 11:02 to 11:30: level fell 0.11 dB; frequency error moved from &minus;10.2 to &minus;12.1 ppm.",
                "11:31:32: the computer was moved. The level dropped 0.45 dB between two readings 23 s apart and stayed there. The frequency did not change. The spectrum analyzer reported one USB error 23 s later and carried on.",
                "After the step, 220 readings over 90 minutes: &minus;19.49 to &minus;19.43 dBm, standard deviation 0.011 dB."]),
            h("The same table on three occasions"),
            table(["Setting", "12 Oct 23:44 (dBm)", "13 Oct 11:04, before the move (dBm)", "13 Oct 12:06, after the move (dBm)"],
                  [["1000 MHz, 0 dB", "&minus;0.01", "0.29", "0.01"], ["1100 MHz, 0 dB", "&minus;0.51", "&minus;0.01", "&minus;0.50"], ["1200 MHz, 0 dB", "&minus;0.38", "&minus;0.02", "&minus;0.40"],
                   ["1100 MHz, 20 dB", "&minus;19.47", "&minus;19.00", "&minus;19.47"], ["1100 MHz, 40 dB", "&minus;39.54", "&minus;39.05", "&minus;39.52"],
                   ["1250 MHz, 20 dB", "&minus;20.51", "&minus;19.61", "&minus;20.46"], ["1450 MHz, 20 dB", "&minus;23.51", "&minus;21.36", "&minus;22.95"], ["1600 MHz, 20 dB", "&minus;23.77", "&minus;20.30", "&minus;22.62"],
                   ["1700 MHz, 20 dB", "&minus;23.92", "&minus;22.56", "&minus;23.77"], ["2000 MHz, 20 dB", "&minus;22.79", "&minus;22.75", "&minus;22.80"]], left=(0,)),
            ul(["Before the move, 13 Oct read higher than 12 Oct at every frequency: by 0.04 to 3.5 dB, most between 1250 and 1750 MHz.",
                "After the move, 13 Oct matches 12 Oct within 0.06 dB up to 1400 MHz and within 1.1 dB from 1450 to 1650 MHz.",
                "A change that follows a mechanical disturbance, differs with frequency, and leaves the Pluto's frequency untouched is the RF path: the cable or an SMA connection between the Pluto and the analyzer.",
                "So the level tables describe the Pluto plus that cable in the state it was in on the night of 12 Oct. Inside 1000 to 1200 MHz a different state moved them by 0.3 to 0.5 dB."])]
    return "".join(out)
