"""Pluto tab. Tables are filled from pluto_characterization/summary.json, so a re-run of the analysis updates the page."""
import json
from pathlib import Path

from content import table, ul, ol, p, h, link, math, fig, D
from content_parts import part_tab, steps_table

SUM = Path(__file__).resolve().parent.parent.parent / "pluto_characterization" / "summary.json"
S = json.loads(SUM.read_text()) if SUM.exists() else {}
LOST = p("Not run yet. The Pluto dropped off USB at 21:26 on 12 Oct, during test A. The run continues from this test when the Pluto is plugged back in.")


def n(v, d=2):
    """Number with a real minus sign."""
    return (f"{v:+.{d}f}" if d else f"{v:+.0f}").replace("-", "&minus;").replace("+", "") if v is not None else D


def have(key):
    return bool(S.get(key))


def results():
    out = []
    done = {"A": have("att_table"), "B": have("freq"), "C": have("scale"), "D": have("freq_err"), "E": have("spurs"),
            "F": have("stab"), "G": have("repeat"), "H": have("tone_off")}
    att = {r[0]: r[1:] for r in S.get("att_table", [])}
    a0 = att.get(0)
    summary = [["A. Output against attenuation", (f"{n(a0[0])}, {n(a0[1])}, {n(a0[2])} dBm at 0 dB (1000, 1100, 1200 MHz). 1 dB per dB within 0.2 dB from 20 to 40 dB. "
                                                  "Reads 0.6 to 1.0 dB low at 0 dB." if a0 else "not run"), "12 Oct" if a0 else ""],
               ["A. Other frequencies", (f"{len(S['coarse'])} of 10 frequencies done: " + ", ".join(f"{r[0]:.0f}" for r in S["coarse"]) + " MHz" if have("coarse") else "not run"), "12 Oct" if have("coarse") else ""]]
    for k, name in (("B", "B. Output against frequency"), ("C", "C. Output against tone scale"), ("D", "D. Frequency error"), ("E", "E. Spectrum"),
                    ("F", "F. Stability"), ("G", "G. Analyzer check and repeat"), ("H", "H. Tone off")):
        summary.append([name, "done, see below" if done[k] else "not run: Pluto lost USB", "12 Oct" if done[k] else ""])
    out.append(table(["Test", "Result", "Date"], summary, left=(0, 1, 2)))

    # ---- A
    out.append(h("Test A: output against attenuation setting, 12 Oct"))
    if a0:
        out.append(fig("pluto_att.png", "Pluto output against attenuation setting at 1000, 1100 and 1200 MHz, and the departure from 1 dB per dB"))
        out.append(ol(["Wiring: Pluto TX to the spectrum analyzer (Siglent SSA3021X) input. Nothing else connected.",
                       "Pluto: one tone, 1 MHz above the LO, tone scale 0.5. The attenuation setting was stepped 0 to 40 dB in 1 dB steps, then 45 to 70 dB in 5 dB steps.",
                       "Analyzer: reference level +10 dBm, span 2 MHz centred on the tone, one sweep per reading, peak marker.",
                       "Repeated at 1000, 1100 and 1200 MHz. 47 settings at each, 141 readings."]))
        dev = S["att_dev"]
        out.append(table(["Attenuation setting (dB)", "1000 MHz (dB)", "1100 MHz (dB)", "1200 MHz (dB)"],
                         [[a_] + [n(dev[f][a_]) for f in ("1000", "1100", "1200")] for a_ in ("0", "1", "2", "3", "5", "10", "30", "40", "50", "60", "70")]))
        out.append(p("The table above is the measured level minus a straight line of 1 dB per dB drawn through the 20 dB reading."))
        out.append(math(r"\text{departure}(A) = P(A) - \left[P(20) + 20 - A\right]"))
        out.append(ul(["From 20 to 40 dB the output follows the setting within 0.2 dB.",
                       "Below 20 dB the output is lower than the setting says: 0.3 to 0.5 dB low at 10 dB, 0.6 to 1.0 dB low at 0 dB. There is a step of about 0.2 dB between 19 and 20 dB.",
                       "This test cannot tell whether that is the Pluto or the analyzer reading high levels slightly low. Test G (analyzer check) is needed for that.",
                       "At 55 dB and above the reading stops falling. The tone is then at the analyzer noise level for this reference level (about &minus;58 dBm). The rows at 55 to 70 dB are not valid Pluto levels.",
                       "The output at 0 dB and tone scale 0.5 is about 0 dBm (1 mW). The team notes give a maximum of +11 dBm. That was not reached; tone scale 1.0 has not been measured yet (test C)."]))
        out.append(h("Look up table: attenuation setting to output power"))
        out.append(table(["Setting (dB)", "1000 MHz (dBm)", "1100 MHz (dBm)", "1200 MHz (dBm)"], [[r[0]] + [n(v) for v in r[1:]] for r in S["att_table"] if r[0] <= 50], cls="lut", left=()))
        out.append(p("Tone scale 0.5. Files: <code>pluto_tx_calibration.csv</code> and <code>pluto_tx_calibration.json</code>."))
    if have("coarse"):
        out.append(h("Test A at other frequencies"))
        out.append(table(["Frequency (MHz)"] + [f"{a_} dB" for a_ in S["coarse_atts"]], [[f"{r[0]:.0f}"] + [n(v) for v in r[1:]] for r in S["coarse"]], cls="lut", left=()))
        out.append(p("Output in dBm at each attenuation setting. Tone scale 0.5. " + ("" if len(S["coarse"]) == 10 else "1400, 1600, 1800 and 2000 MHz are not done: the Pluto lost USB while tuning to 1400 MHz.")))

    # ---- B
    out.append(h("Test B: output against frequency"))
    if done["B"]:
        out.append(fig("pluto_freq.png", "Pluto output against frequency from 350 to 2100 MHz"))
        for att_, rows in S["freq"].items():
            lv = [r[1] for r in rows]
            band = [r[1] for r in rows if 1000 <= r[0] <= 1200]
            out.append(p(f"Attenuation {att_} dB: {n(min(lv))} to {n(max(lv))} dBm over {rows[0][0]} to {rows[-1][0]} MHz ({len(rows)} points). "
                         + (f"Inside 1000 to 1200 MHz: {n(min(band))} to {n(max(band))} dBm, a spread of {max(band)-min(band):.2f} dB." if band else "")))
        out.append(table(["Frequency (MHz)", "At 20 dB (dBm)", "At 0 dB (dBm)"],
                         [[r[0], n(r[1]), n(dict(map(tuple, S["freq"].get("0", []))).get(r[0]))] for r in S["freq"].get("20", [])], cls="lut", left=()))
    else:
        out.append(LOST)

    # ---- C
    out.append(h("Test C: output against tone scale"))
    if done["C"]:
        out.append(fig("pluto_scale.png", "Departure of the output from 20 log10 of the tone scale"))
        out.append(table(["Attenuation (dB)", "Tone scale", "Output (dBm)", "Output minus ideal (dB)"], [[r[0], r[1], n(r[2]), n(r[3])] for r in S["scale"]], left=()))
        out.append(math(r"P_\text{ideal}(s) = P(0.5) + 20\log_{10}\!\left(\frac{s}{0.5}\right)"))
    else:
        out.append(LOST)

    # ---- D, F
    out.append(h("Test D: frequency error"))
    if done["D"]:
        out.append(table(["Set (MHz)", "Error (Hz)", "Error (ppm)"], [[f"{r[0]:.0f}", n(r[1], 0), n(r[2])] for r in S["freq_err"]], left=()))
        out.append(p("Read with a 20 kHz span. The error includes the analyzer's own reference error; the two cannot be separated without a third reference."))
    else:
        out.append(LOST + p("From test A: with a 2 MHz span the tone read 5 to 13 kHz below the set frequency at 1000 to 1200 MHz. The analyzer frequency step at that span is 2.7 kHz."))
    out.append(h("Test F: stability"))
    if done["F"]:
        s = S["stab"]
        out.append(ul([f"{s['n']} readings over {s['seconds']:.0f} s at 1100 MHz, attenuation 20 dB.", f"Level: mean {n(s['level_mean'])} dBm, spread {s['level_span']:.2f} dB, standard deviation {s['level_sd']:.3f} dB.",
                       f"Frequency: mean error {n(s['freq_mean_err'], 0)} Hz, spread {s['freq_span']:.0f} Hz."]))
    else:
        out.append(LOST)

    # ---- E
    out.append(h("Test E: spectrum"))
    if done["E"]:
        out.append(fig("pluto_spectra.png", "Pluto output spectrum close to the tone and from 0 to 2.1 GHz"))
        out.append(table(["Tone (MHz)", "Attenuation (dB)", "Line", "Level relative to the tone (dB)"], [[r[0], r[1], r[2], n(r[3], 1)] for r in S["spurs"]], left=(2,)))
        if have("harm2"):
            out.append(p("Second harmonic of the 1000 MHz tone, read at 2000 MHz: " + "; ".join(f"{n(r[1])} dBm at attenuation {r[0]:.0f} dB" for r in S["harm2"]) + "."))
    else:
        out.append(LOST)

    # ---- G, H
    out.append(h("Test G: analyzer check and repeat"))
    if done["G"]:
        out.append(table(["Analyzer reference level (dBm)", "Reading of the same tone (dBm)"], [[n(r[0], 0), n(r[1])] for r in S["ref_level"]], left=()))
        out.append(table(["Attenuation (dB), in the order read", "Output (dBm)"], [[f"{r[0]:.0f}", n(r[1])] for r in S["repeat"]], left=()))
    else:
        out.append(LOST)
    out.append(h("Test H: tone off"))
    if done["H"]:
        out.append(table(["Attenuation (dB)", "Largest line, frequency (MHz)", "Level (dBm)"], [[f"{r[0]:.0f}", r[1], n(r[2])] for r in S["tone_off"]], left=()))
    else:
        out.append(LOST)

    out.append(h("Files"))
    out.append(p("Folder <code>clinic\\claude\\pluto_characterization\\</code>: <code>readings.csv</code> (every reading, with time, settings, measured frequency and level), "
                 "<code>characterize_pluto.py</code> (takes the readings), <code>analyze_pluto.py</code> (tables and plots), <code>summary.json</code>, "
                 "<code>pluto_tx_calibration.csv</code>, <code>spectrum_*.csv</code> (traces, test E), <code>run_log.txt</code>."))
    return "".join(out)


PLUTO = part_tab(
    "Pluto", "Analog Devices ADALM-Pluto SDR. Test source for 1.0&ndash;1.2 GHz. Not part of the JACON design.", "plu",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Tuning range (stock)", "325", D, "3800", "MHz"], ["TX output power", D, D, "+7", "dBm"], ["TX attenuation setting", "0", D, "89.75", "dB"],
           ["TX attenuation step", D, "0.25", D, "dB"], ["Bandwidth", "0.2", D, "20", "MHz"], ["Converter resolution", D, "12", D, "bits"],
           ["Frequency accuracy", D, D, "&plusmn;25", "ppm"], ["Connectors", D, "SMA, 50 &Omega;", D, ""], ["Supply", D, "USB, 5 V", D, ""]]) +
    p(link("https://wiki.analog.com/university/tools/pluto", "ADI wiki") + ". The team notes give a maximum output of +11 dBm. The measured output at attenuation 0 dB and tone scale 0.5 is about 0 dBm.") +
    h("How the computer controls it") +
    ul(["Address <code>ip:192.168.2.1</code> over USB. Program <code>iio_attr.exe</code>. Script <code>clinic\\claude\\sdr\\pluto_cw.py</code>.",
        "The tone is made inside the Pluto, 1 MHz above the LO. The LO is set to the wanted frequency minus 1 MHz.",
        "Level is set two ways: the attenuation setting (0 to 89.75 dB) and the tone scale (0 to 1, a digital amplitude).",
        "<code>pluto_cw.py</code> refuses any attenuation below 31 dB unless the limit is changed in the file. 31 dB keeps the output under &minus;20 dBm. "
        "For this test the limit was set to 0 dB, because only the spectrum analyzer (safe to +30 dBm) was connected. It was set back to 31 dB afterwards."]),
    ul(["Output falls 1 dB for each 1 dB of attenuation setting.", "Output changes by 20 log10 of the tone scale.", "Output is flat within a few dB from 325 MHz to 2.1 GHz.",
        "Frequency is within 25 ppm: 27.5 kHz at 1.1 GHz.", "Besides the tone there is a line at the LO (1 MHz below) and one at the other sideband (2 MHz below). Their levels are not specified.",
        "A harmonic at twice the tone frequency. Level not specified."]) +
    math(r"P_\text{out} = P_0(f) - A + 20\log_{10}\!\left(\frac{s}{0.5}\right)") +
    p("\\(P_0(f)\\) = output at attenuation 0 dB and tone scale 0.5. \\(A\\) = attenuation setting in dB. \\(s\\) = tone scale."),
    p("One wiring for every test: Pluto TX to the spectrum analyzer input. Pluto on USB. No wiring changes.") +
    steps_table([
        ["A", "Output against attenuation", "Pluto TX &rarr; spectrum analyzer", "nothing", "step attenuation 0&ndash;40 dB in 1 dB steps, then to 70 dB, at 1000, 1100, 1200 MHz; ten settings at ten other frequencies, 400&ndash;2000 MHz", "1 dB per dB", "recorded as a table"],
        ["B", "Output against frequency", "same", "nothing", "step 350&ndash;2100 MHz in 25 MHz steps (10 MHz inside 1.0&ndash;1.2 GHz) at 20 dB and 0 dB", "flat within a few dB", "recorded"],
        ["C", "Output against tone scale", "same", "nothing", "step tone scale 0.05&ndash;1.0 at 1100 MHz, at 20 dB and 0 dB", "20 log10(scale)", "recorded"],
        ["D", "Frequency error", "same", "nothing", "read the tone in a 20 kHz span at eight frequencies, 400&ndash;2000 MHz", "within 25 ppm", "recorded"],
        ["E", "Spectrum", "same", "nothing", "save traces at 10 MHz span, 200 MHz span and 0&ndash;2.1 GHz, at 1000, 1100, 1200 MHz, at 20 dB and 0 dB; read 2000 MHz with the tone at 1000 MHz", "lines at the LO and the other sideband; a second harmonic", "recorded"],
        ["F", "Stability", "same", "nothing", "read level and frequency 40 times over about 3 minutes", "not specified", "recorded"],
        ["G", "Analyzer check and repeat", "same", "nothing", "read one tone at reference levels &minus;10, 0, +10, +20 dBm; then repeat attenuation 40, 20, 0, 20, 40 dB", "same reading each time", "recorded"],
        ["H", "Tone off", "same", "nothing", "set tone scale 0; read the largest line near the LO at 0, 10, 31 dB", "not specified", "recorded"]]),
    results())
