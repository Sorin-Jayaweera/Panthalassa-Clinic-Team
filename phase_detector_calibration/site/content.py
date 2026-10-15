"""Page content for the JACON notes, as data. build_site.py turns this into index.html."""
import html


def esc(s):
    return html.escape(s, quote=False)


def fig(name, alt):
    return f'<figure><a href="img/{name}"><img src="img/{name}" alt="{alt}"></a></figure>'


def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def ol(items):
    return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"


def math(tex):
    return f'<div class="math">\\[ {tex} \\]</div>'


def code(text, label="Code"):
    return f'<details class="code"><summary>{label}</summary><pre><code>{esc(text)}</code></pre></details>'


def table(head, rows, cls="", left=(0,)):
    def cell(tag, i, v):
        c = ' class="l"' if i in left else ""
        return f"<{tag}{c}>{v}</{tag}>"
    out = [f'<div class="tablewrap {cls}"><table><tr>' + "".join(cell("th", i, h) for i, h in enumerate(head)) + "</tr>"]
    for r in rows:
        rid = ""
        if isinstance(r, dict):
            rid, r = f' id="{r["id"]}"', r["cells"]
        out.append(f"<tr{rid}>" + "".join(cell("td", i, v) for i, v in enumerate(r)) + "</tr>")
    out.append("</table></div>")
    return "".join(out)


def item(iid, title, *body, open_=False):
    return (f'<details class="item" id="{iid}"{" open" if open_ else ""}><summary>{title}</summary>'
            f'<div class="body">{"".join(body)}</div></details>')


def h(t):
    return f"<h4>{t}</h4>"


def p(t):
    return f"<p>{t}</p>"


def link(url, text):
    return f'<a href="{url}">{text}</a>'


DS = {
    "splitter": "https://www.minicircuits.com/pdfs/ZFRSC-42+.pdf",
    "mixer": "https://www.minicircuits.com/pdfs/ZX05-30W-S+.pdf",
    "vco": "https://www.digikey.com/en/products/detail/crystek-corporation/CVCO55BE-0800-1600/1643988",
    "cgr": "https://www.saelig.com/supplier/syscomp/CGR201-Datasheet.pdf",
    "pluto": "https://wiki.analog.com/university/tools/pluto/users/transmit",
    "p162": "https://www.minicircuits.com/pdfs/ZX60-P162LN+.pdf",
    "p103": "https://www.minicircuits.com/pdfs/ZX60-P103LN+.pdf",
    "hpf": "https://www.minicircuits.com/pdfs/VHF-8400+.pdf",
    "vlm": "https://www.minicircuits.com/pdfs/VLM-33-S+.pdf",
}


def mc(model):
    return "https://www.minicircuits.com/WebStore/dashboard.html?model=" + model.replace("+", "%2B")


# ------------------------------------------------------------------ Part info
PART_HEAD = ["Part", "Band", "Max in dBm", "Max in mW", "Max in V rms", "Typical dB", "Worst dB in band", "Measured", "Other specs", "Source"]
D = "&mdash;"
PARTS = [
    {"id": "pi-vco", "cells": ["VCO", "Crystek CVCO55BE-0800-1600", "800&ndash;1600 MHz", "no RF input", D, "tuning 0.5&ndash;19 V",
                               "output +6 dBm (4.0 mW, 0.45 V rms)", "output +4 dBm (2.5 mW, 0.35 V rms)", "+4.8 to +7.4 dBm, 1.0&ndash;1.2 GHz",
                               "Vcc 11.5 V used; 30 mA max; pushing 2 MHz/V; 2nd harmonic &minus;10 dBc", "DigiKey listing", link(DS["vco"], "DigiKey")]},
    {"id": "pi-delaysplit", "cells": ["Splitter (delay line, and IF)", "Mini-Circuits ZFRSC-42-S+", "DC&ndash;4200 MHz", "28.8", "750", "6.12",
                                      "&minus;6.0 per output", "&minus;6.5 per output", "&minus;6.7 at 1.04 GHz, with connectors",
                                      "isolation 6.5 dB typ; amplitude unbalance 0.2 dB max; phase unbalance 3&deg; max; internal dissipation 0.375 W max",
                                      "datasheet", link(DS["splitter"], "PDF")]},
    {"id": "pi-phasedet", "cells": ["Mixer (phase detector), RF port", "Mini-Circuits ZX05-30W-S+", "300&ndash;4000 MHz, IF DC&ndash;950 MHz", "17.0", "50", "1.58",
                                    "&minus;6.4 conversion loss at 1.1 GHz", "&minus;9.0 conversion loss", "as phase detector: 30 to 146 mV DC out",
                                    "LO level +7 dBm (5.0 mW, 0.50 V rms); IF current 40 mA max; LO&ndash;RF isolation 35 typ / 17 min; LO&ndash;IF isolation 16 typ / 7 min; 1 dB compression +1 dBm; RF VSWR 2.8&ndash;3.5 near 1 GHz",
                                    "datasheet", link(DS["mixer"], "PDF")]},
    {"id": "pi-cable", "cells": ["SMA cables", D, D, D, D, D, D, D, "&minus;0.04, &minus;0.09, &minus;0.21 at 1.04 GHz", "extra delay cable 4.5 in = 0.55 ns", "measured 6 Oct", D]},
    {"id": "pi-pluto", "cells": ["Pluto SDR (test source)", "ADALM-PLUTO", "used at 1.0&ndash;1.2 GHz", "no RF input used", D, D, "output max +11 dBm (12.6 mW, 0.79 V rms)", D, D, D, "team notes", link(DS["pluto"], "ADI wiki")]},
    {"id": "pi-rxant", "cells": ["RX antenna", "horn", "8.2&ndash;12.4 GHz", D, D, D, "+10 to +15 dBi", D, "not tested", D, "design drawing", D]},
    {"id": "pi-limiter", "cells": ["Power limiter", "not chosen (VLM-33-S+ on hand)", D, D, D, D, D, D, "not tested", "output must stay under +15 dBm", "design drawing", link(DS["vlm"], "VLM-33-S+ PDF")]},
    {"id": "pi-lna", "cells": ["LNA", "Mini-Circuits ZX60-5123LN+", "5.5&ndash;12.5 GHz", "15.0", "31.6", "1.26", "+22.0", "+19.0 (min gain)", "not tested",
                               "supply 6 V typ (5&ndash;10 V; 12 V abs max), 80 mA (95 max); noise figure 1.4 dB; P1dB out +17 dBm; OIP3 +29.5 dBm", "datasheet", link("https://www.minicircuits.com/pdfs/ZX60-5123LN+.pdf", "PDF")]},
    {"id": "pi-rxmixer", "cells": ["RX mixer and TX mixer", "Mini-Circuits ZX05-14LH-S+", "RF/LO 3.7&ndash;10 GHz, IF DC&ndash;4 GHz", "17.0", "50", "1.58", "&minus;6.7 conversion loss (&minus;7.7 at 9.4 GHz)", "&minus;9.5 conversion loss", "not tested",
                                   "LO level +10 dBm (10 mW, 0.71 V rms); 1 dB compression +5 dBm in; LO&ndash;RF isolation 35 typ / 25 min; LO&ndash;IF 17 typ / 9 min; RF VSWR 4.0 at 9.4 GHz", "datasheet", link("https://www.minicircuits.com/pdfs/ZX05-14LH-S+.pdf", "PDF")]},
    {"id": "pi-ifamp", "cells": ["IF amp", "Mini-Circuits ZX60-P103LN+", "50&ndash;3000 MHz", "21.0", "126", "2.51", "+15.6 at 1 GHz", "+13.5 (min gain at 1 GHz)", "not tested",
                                 "supply 5.0 V (5.5 V abs max), 95 mA (120 max); noise figure 0.5 dB; P1dB out +22.4 dBm", "datasheet", link(DS["p103"], "PDF")]},
    {"id": "pi-ifamp3", "cells": ["IF amp (alternative)", "Mini-Circuits ZX60-2534MA-S+", "500&ndash;2500 MHz", "&minus;15.0", "0.032", "0.040", "+43.5 at 1 GHz", "+38 (min gain at 2 GHz)", "not tested",
                                  "supply 5.0 V (7 V abs max), 170 mA (190 max); noise figure 2.3 dB; P1dB out +19.2 dBm", "datasheet", link("https://www.minicircuits.com/pdfs/ZX60-2534MA+.pdf", "PDF")]},
    {"id": "pi-ifamp2", "cells": ["IF amp (alternative)", "Mini-Circuits ZX60-P162LN+", "700&ndash;1600 MHz", "25.0", "316", "3.98", "+22.5 at 1 GHz", "+20.9 (min gain at 1 GHz)", "not tested",
                                  "supply 4.0 V (3.8&ndash;4.2; 5.5 V abs max), 52 mA; noise figure 0.52 dB; P1dB out +19.9 dBm", "datasheet", link(DS["p162"], "PDF")]},
    {"id": "pi-limamp", "cells": ["RF limiting amp", "three gain blocks, not chosen", "1.0&ndash;1.2 GHz", D, D, D, D, D, "not tested", "output must stay under +23.5 dBm (mixer limit +17 dBm plus 6.5 dB splitter loss)", "design drawing", D]},
    {"id": "pi-env", "cells": ["Envelope detector", "Analog Devices ADL5511", D, D, D, D, D, D, "not tested", D, "design drawing", D]},
    {"id": "pi-comp", "cells": ["Comparator", "Analog Devices ADCMP600", D, D, D, D, D, D, "not tested", D, "design drawing", D]},
    {"id": "pi-dac", "cells": ["DAC", "Analog Devices nanoDAC", D, D, D, D, D, D, "not tested", "sets the comparator threshold", "design drawing", D]},
    {"id": "pi-fpga", "cells": ["FPGA", "PYNQ-Z2 or ECP5", D, D, D, D, D, D, "not tested", D, "design drawing", D]},
    {"id": "pi-sh", "cells": ["Sample and hold", "ADG1211 switch, 100 pF, ADA4622-1 op-amp", D, D, D, D, D, D, "not tested", "must output 4.8&ndash;7.8 V for the VCO", "design drawing", D]},
    {"id": "pi-pll", "cells": ["PLL local oscillator", "Analog Devices ADF5355 module", "set to 8.3 GHz", D, D, D, D, D, "not tested", D, "design drawing", D]},
    {"id": "pi-lobuf", "cells": ["LO buffer amp", "Mini-Circuits ZX60-14012L-S+", "0.3 MHz&ndash;14 GHz", "10.0", "10", "0.71", "+12 (+12.5 at 8 GHz)", "+9 (min gain)", "not tested",
                                 "supply 12 V (10.5&ndash;20 V), 62 mA (68 max); P1dB out +11 dBm (+12.2 at 8 GHz); noise figure 5.5 dB", "datasheet", link("https://www.minicircuits.com/pdfs/ZX60-14012L-S+.pdf", "PDF")]},
    {"id": "pi-losplit", "cells": ["LO splitter", "Mini-Circuits ZX10-2-1252-S+", "1.8&ndash;12.5 GHz", "32.7", "1850", "9.62", "&minus;4.1 per output at 8.3 GHz (3.0 split + 1.1)", "&minus;4.4 per output (3.0 + 1.4)", "not tested",
                                   "isolation 19.9 dB typ, 13 min; phase unbalance 8.1&deg; typ; passes DC up to 0.4 A; the 0.7 dB on the drawing is the 1.8&ndash;3.8 GHz value", "datasheet", link("https://www.minicircuits.com/pdfs/ZX10-2-1252-S+.pdf", "PDF")]},
    {"id": "pi-key", "cells": ["Keying switch", "Analog Devices ADG901", D, D, D, D, D, D, "not tested", D, "design drawing", D]},
    {"id": "pi-filter", "cells": ["Image reject filter", "Mini-Circuits VHF-8400+", "passband 9.0&ndash;13.0 GHz", "38.5", "7000", "18.7", "&minus;1.4 to &minus;1.6 at 9.3&ndash;9.5 GHz (drawing estimate)", "&minus;3.0 at 9.0&ndash;9.5 GHz", "not tested",
                                  "3 dB point 8.4 GHz; rejection 30 dB typ below 5.7 GHz, 20 dB min below 6.0 GHz; not specified at 7.1&ndash;7.3 GHz (drawing estimate 24&ndash;28 dB)", "datasheet", link(DS["hpf"], "PDF")]},
    {"id": "pi-pa", "cells": ["Power amp", "not chosen", "9.3&ndash;9.5 GHz", D, D, D, D, D, "not tested", "output about 1 W (30 dBm, 1000 mW, 7.07 V rms)", "design drawing", D]},
    {"id": "pi-txant", "cells": ["TX antenna", "horn, same as RX", "8.2&ndash;12.4 GHz", D, D, D, "+10 to +15 dBi", D, "not tested", D, "design drawing", D]},
]

def part_cells(c):
    """Name, part number and datasheet link share the first column."""
    name, partno, band, dbm, mw, v, typ, worst, meas, other, src, ds = c
    first = f"<strong>{name}</strong><br><span class=\"src\">{partno}</span>" + ("" if ds == D else f"<br>{ds}")
    return [first, band, dbm, mw, v, typ, worst, meas, other, src]


PARTINFO = "".join([
    "<h2>Part info</h2>",
    p("One row per part. The datasheet link is under the part name. V rms is into 50 &Omega;. &ldquo;Band&rdquo; for the worst case is 1.0&ndash;1.2 GHz for IF parts and 9.3&ndash;9.5 GHz for RF parts. Negative dB is loss, positive is gain. "
      "&ldquo;Not looked up&rdquo; means the number is in the datasheet but has not been copied here yet."),
    table(PART_HEAD, [{"id": r["id"], "cells": part_cells(r["cells"])} for r in PARTS], cls="parts", left=(0, 1, 5, 6, 7, 8, 9)),
    item("pi-bench", "Power measured on the bench",
         table(["Point", "dBm", "mW", "V rms (50 &Omega;)", "Note"],
               [["VCO output at 1.04 GHz", "+7.3", "5.4", "0.52", "measured 6 Oct"],
                ["Each splitter output", "+0.6", "1.15", "0.24", "measured 6 Oct"],
                ["Mixer RF damage limit", "+17.0", "50", "1.58", "margin 16.4 dB"],
                ["Mixer LO level wanted", "+7.0", "5.0", "0.50", "bench level was 6.4 dB lower"]], left=(0, 4)),
         p("The largest power the mixer has received is about 3 mW (Pluto at 12.6 mW, minus 6 dB in the splitter). Its limit is 50 mW.")),
    "@@RX_LEVELS@@",
    item("pi-conv", "Unit conversions used",
         math(r"P_\text{dBm} = 10\log_{10}\!\left(\frac{P_\text{mW}}{1\ \text{mW}}\right) \qquad P_\text{mW} = 10^{P_\text{dBm}/10} \qquad V_\text{rms} = \sqrt{P \times 50\ \Omega}"),
         p("Example: 50 mW = 0.050 W. V rms = &radic;(0.050 &times; 50) = 1.58 V. In dBm: 10 log<sub>10</sub>(50) = 17.0 dBm."),
         p("Worst case for the splitter: 6.0 dB split loss + 0.5 dB maximum insertion loss (100&ndash;2100 MHz) = 6.5 dB.")),
    item("pi-missing", "Numbers still missing",
         ul(["Filter rejection at 7.1&ndash;7.3 GHz. The datasheet does not give it. It has to be measured.", "PLL output power at 8.3 GHz.",
             "Crystek&rsquo;s own datasheet for the VCO. The listed VCO numbers are from the DigiKey page.",
             "All rows marked &ldquo;design drawing&rdquo; are copied from the JACON drawing and have not been checked against datasheets."])),
    item("pi-docs", "Other documents",
         ul([link("https://markimicrowave.com/technical-resources/white-papers/mixer-basics-primer/", "Marki mixer basics primer"),
             link("https://www.rfwireless-world.com/tutorials/rf-mixer-basics", "RF Wireless World mixer basics"),
             link(DS["cgr"], "Syscomp CGR-201 datasheet"),
             link("https://www.psicompany.com/man-prod-info/furuno/Gp1920C/18X4C_19X4C_GP1920C%20Installation%20Manual%20K.pdf", "Furuno radar installation manual"),
             link("https://www.instructionsmanuals.com/sites/default/files/2019-06/Furuno-1944CBB-en.pdf", "Furuno radar operator manual"),
             link("https://signalhound.com/sigdownloads/SDK/online_docs/sm_api/index.html", "Signal Hound SM API documentation")]),
         p("Racon requirements: reply within 0.7 &micro;s. Reply frequency within &plusmn;3.5 MHz of the radar for pulses shorter than 0.2 &micro;s, &plusmn;1.5 MHz for longer pulses. No reply for 100 &micro;s after the previous reply ends.")),
])

# ------------------------------------------------------------------ VCO
C_SETVT = '''def set_vt(g, s, target, code):
    s.write(f"C1:OFST {-target:.3f}V")      # centre scope CH1 on the target
    for _ in range(4):
        g.set_offset_raw(code)              # Syscomp output code
        time.sleep(0.6)
        v, _ = scope_mean(s, 1, n=2)        # read Vt on the scope
        if abs(v - target) < 0.003:
            break
        code += (target - v) / OFFSET_V_PER_CODE   # 1.875 mV per code
    return v, code

def measure(self):                          # spectrum analyzer
    f, _ = self._peak(850e6, 500e6)         # wide span: find the peak
    f, p = self._peak(f, 2e6)               # 2 MHz span: read it
    return f, p'''
C_ALIAS = '''z = np.fft.ifft(2 * spec * w)                 # keep only the alias band, positive frequencies
p = z[lag:] * np.conj(z[:-lag])               # product of the signal with itself, lag samples earlier
# average p over all edges, then:
f_alias = band_start + np.mod(np.angle(p_avg * np.exp(-2j*np.pi*band_start*lag/fs)), 2*np.pi) * fs / (2*np.pi*lag)
f_true = 1000e6 - f_alias                     # for 750-1000 MHz sampled at 500 MSa/s'''
C_HEAT = '''F = np.array([p["vco_freq_hz"] for p in passes]) / 1e6      # 18 passes x 36 voltages
dF = (F - np.median(F, axis=0)) * 1e3                        # kHz away from the median of that voltage
ax.pcolormesh(minutes, vt, dF.T, cmap="RdBu_r", vmin=-lim, vmax=lim)'''

VCO = "".join([
    "<h2>VCO</h2>", '<p class="sub">Crystek CVCO55BE-0800-1600 on CEVAL-055 board. Vcc 11.5 V.</p>',
    table(["Quantity", "Value", "Source"],
          [["Frequency range seen", "733 MHz at 0 V to 1360 MHz at 10.1 V", "measured 4 Oct"],
           ["Tuning voltage for 1.0&ndash;1.2 GHz", "4.8 to 7.8 V", "measured 4 Oct"],
           ["Slope in 1.0&ndash;1.2 GHz", "68 MHz/V", "measured 4 Oct"],
           ["Slope, 0&ndash;1 V / 1&ndash;2 V / 2&ndash;3 V", "40 / 33 / 75 MHz/V", "measured 10 Oct"],
           ["Output power in 1.0&ndash;1.2 GHz", "+4.8 to +7.4 dBm (3.0 to 5.5 mW)", "measured 6 Oct"],
           ["Repeatability at a fixed voltage", "0.10 MHz", "measured 10 Oct"],
           ["Drift over 74 min", "59 kHz rms, no trend", "measured 10 Oct"],
           ["Shift when the load changes", "1.5 to 3.2 MHz (one tee swapped); up to 16 MHz between setups", "measured"],
           ["Delay from tuning pin to frequency", "26 ns", "measured 10 Oct"],
           ["Listed output", "6 &plusmn; 2 dBm", "DigiKey"],
           ["Listed tuning range", "0.5 to 19 V", "DigiKey"]], left=(0, 1, 2)),
    item("vco-tune10", "Frequency vs voltage, 0 to 10 V",
         fig("comp_vco_tuning.png", "VCO frequency against tuning voltage 0 to 10 V"),
         h("Result"), ul(["1.0 GHz needs 4.83 V. 1.2 GHz needs 7.75 V.", "The line 0.8 GHz + 60 MHz/V is 48 to 97 MHz higher than the measurement.",
                          "The two data sets differ by up to 16 MHz at the same voltage. The VCO was connected to different things each time."]),
         h("How it was made"), ol(["Grey squares: on 4 Oct the tuning voltage was set by hand with a bench supply. The VCO was connected straight to the spectrum analyzer. The frequency was read after waiting 10 s.",
                                    "Green line: on 10 Oct the computer set the voltage and read the analyzer, 176 points. The VCO was connected to the tee, splitter and mixer.",
                                    "The orange band marks 1.0&ndash;1.2 GHz. The voltages for the band edges were found by interpolating the grey points."])),
    item("vco-tune35", "Frequency vs voltage, 0 to 3.5 V",
         fig("vco_f_vs_v.png", "VCO output frequency against tuning voltage Vt, 0 to 3.5 V"),
         h("Result"), ul(["743.6 MHz at 0 V. 920.0 MHz at 3.50 V.", "14 points repeated on the way down agree within 0.10 MHz."]),
         h("How it was made"), ol(["The Syscomp output is set to a voltage, with its waveform switched off.",
                                    "Scope CH1 reads the voltage. The Syscomp is adjusted until CH1 is within 3 mV of the target.",
                                    "The spectrum analyzer does one sweep over 600&ndash;1100 MHz and finds the peak.",
                                    "It does a second sweep 2 MHz wide centred on that peak and reads the peak frequency and power. The marker step is 2 MHz / 751 = 2.7 kHz.",
                                    "The voltage is raised 0.02 V and the steps repeat. 176 voltages in total.",
                                    "Then 14 voltages are measured again going down, to check repeatability."]),
         math(r"c_{n+1} = c_n + \frac{V_\text{target} - V_\text{CH1}}{1.875\ \text{mV per code}}"),
         code(C_SETVT), p('Data file: <code>phase_detector_calibration_run3_cleanDC_0p02V_steps.csv</code>. Table: see the ' + link("#lut-vco", "Look up tables") + " tab.")),
    item("vco-power", "Output power vs frequency",
         fig("comp_vco_power.png", "VCO output power against frequency"),
         h("Result"), ul(["+7.4 dBm at 1.04 GHz. +4.8 dBm at 1.18 GHz. +4.5 dBm at 1.24 GHz."]),
         h("How it was made"), ol(["6 Oct. VCO connected to the spectrum analyzer through one cable.", "The tuning voltage was set by hand to ten values.", "Frequency and peak power were read from the analyzer at each."])),
    item("vco-sapower", "Analyzer power reading, 744 to 920 MHz",
         fig("power.png", "Analyzer power against frequency, one sweep"), fig("power_repeat.png", "Analyzer power, one sweep against 18 repeats"),
         h("Result"), ul(["15 of 648 readings were more than 2 dB below the median for their voltage. They occurred at random voltages and times.",
                          "During those readings the mixer output changed by 0.23 mV at most. The mixer output changes strongly with power. So the VCO power did not really drop.",
                          "From 850 to 890 MHz the reading is 4 to 7 dB low in every pass.",
                          "Correlation between the power reading and the VCO tuning slope: &minus;0.89."]),
         h("Explanation (not tested)"), p("The peak was read through a 30 kHz filter. Noise on the tuning voltage moves the VCO frequency. If it moves by more than 30 kHz during the sweep, part of the signal falls outside the filter and the peak reads low. This is worst where the tuning slope is steepest."),
         math(r"\Delta f_\text{rms} = K_v \cdot \sigma_{V_t} \qquad K_v = 33\ \text{to}\ 90\ \text{MHz/V}"),
         p("With 1 mV of noise this is 33 to 90 kHz. To check: repeat with a 1 MHz filter and averaging."),
         h("How it was made"), ol(["First plot: the peak power from the 2 MHz sweep in the calibration run. One reading per voltage.",
                                    "Second plot: the same reading taken in each of the 18 drift passes. Dots are the mean. Bars run from the lowest to the highest reading."])),
    item("vco-drift", "Drift over 74 minutes",
         fig("drift_heatmap.png", "Heat maps of frequency, mixer output and power deviation over 74 minutes"),
         h("Result"), ul(["Left panel, VCO frequency: 59 kHz rms scatter. Largest single deviation 324 kHz. No trend with time.",
                          "The scatter is larger above 2 V. The tuning slope is steeper there, so a 1 mV error in setting the voltage changes the frequency more. The voltage setting repeats to 1.7 mV."]),
         h("How it was made"), ol(["The 0 to 3.5 V sweep was run 18 times in a row, in 0.1 V steps (36 voltages). This took 74 minutes.",
                                    "For each voltage, the median of its 18 readings was calculated.",
                                    "Each cell is one reading minus the median for that voltage. Red is above the median, blue is below.",
                                    "Time runs left to right. Voltage runs bottom to top."]),
         math(r"\Delta_{ij} = x_{ij} - \operatorname{median}_i(x_{ij})"), code(C_HEAT)),
    item("vco-step", "Response to a voltage step, VCO alone",
         fig("vco_freq_vs_time.png", "VCO frequency against time for ten step sizes"), fig("vco_rise_time.png", "Rise time against step size"), fig("vco_freq_vs_voltage.png", "Settled frequency against voltage"),
         h("Result"), ul(["Frequency 10&ndash;90 % rise time: 100 to 176 ns. The drive voltage rise time is 145 ns.",
                          "The frequency follows the drive voltage with 0 to 12 ns of lag. The measurement is limited by the drive, not the VCO.",
                          "The &ldquo;static DC&rdquo; curve in the third plot is wrong by up to 1.7 MHz. See the Errors tab."]),
         h("How it was made"), ol(["The VCO output was connected to the scope. The mixer was not used.",
                                    "The scope samples at 500 MSa/s. A 765&ndash;875 MHz signal appears in the samples as a lower frequency, 235&ndash;125 MHz. This lower frequency is called the alias.",
                                    "The alias moves by 1 MHz when the real frequency moves by 1 MHz. So the real frequency is 1000 MHz minus the alias.",
                                    "The Syscomp drove a 50 kHz square wave from 0.5 V to a high level. Ten high levels from 0.75 to 3.0 V.",
                                    "The signal at the scope was tens of microvolts, smaller than the scope noise. One edge is not enough to see it.",
                                    "The VCO phase is different on every edge, so the waveforms cannot be averaged directly. Instead, each waveform is multiplied by a copy of itself a few samples earlier. The phase cancels in this product and the frequency remains.",
                                    "The product was averaged over 1112 edges per step. The angle of the average gives the alias frequency at each instant.",
                                    "Rise time is the time for the frequency to go from 10 % to 90 % of the step."]),
         math(r"f_\text{alias} = |f - k f_s| \qquad f = 2 f_s - f_\text{alias} \quad (750\text{&ndash;}1000\ \text{MHz},\ f_s = 500\ \text{MSa/s})".replace("&ndash;", "-")),
         math(r"p[n] = z[n+m]\, z^{*}[n] \qquad f_\text{alias} = \frac{f_s}{2\pi m}\arg\langle p[n] \rangle_\text{edges}"),
         code(C_ALIAS)),
    item("vco-notes", "Notes",
         h("Measured"), ul(["The tuning curve is not a straight line. Use the look up table.",
                            "The frequency depends on what the output is connected to. Calibrate in the final wiring.",
                            "The 4 Oct note that the VCO looked slow (seconds) was the bench supply and the analyzer sweep. The VCO responds in under 0.2 &micro;s.",
                            "The 4 Oct note of two discrete frequency values within 3 MHz was the analyzer marker step (2.67 MHz at a 2 GHz span)."]),
         h("Consequences"), ul(["1.0&ndash;1.2 GHz needs 4.8&ndash;7.8 V. The Syscomp reaches 3.52 V. All computer-run tests so far were at 744&ndash;920 MHz.",
                                "Racon tolerance &plusmn;1.5 to &plusmn;3.5 MHz at 68 MHz/V is &plusmn;22 to &plusmn;51 mV on the tuning pin."]),
         h("Not known"), ul(["Change with temperature and supply voltage.", "Response above 7 MHz. This needs a faster edge than the Syscomp gives."])),
])

# ------------------------------------------------------------------ Splitter
SPLITTER = "".join([
    "<h2>Splitter</h2>", '<p class="sub">Mini-Circuits ZFRSC-42-S+. Resistive, 2-way. With 4.5 in extra SMA cable on one output.</p>',
    table(["Quantity", "Value", "Source"],
          [["Max input", "0.75 W = 28.8 dBm = 6.12 V rms", "datasheet"], ["Internal dissipation, max", "0.375 W", "datasheet"],
           ["Loss per output, typical", "6.0 dB", "datasheet"], ["Loss per output, worst case 1.0&ndash;1.2 GHz", "6.5 dB", "datasheet"],
           ["Loss per output, measured", "6.70 and 6.72 dB at 1.04 GHz", "measured 6 Oct"],
           ["Isolation between outputs", "6.5 dB typical (5.94 dB at 1 GHz)", "datasheet"],
           ["Amplitude unbalance, max", "0.2 dB", "datasheet"], ["Phase unbalance, max", "3&deg;", "datasheet"],
           ["VSWR at 1 GHz", "1.02 to 1.03", "datasheet"], ["Extra cable", "4.5 in = 0.55 ns", "calculated"],
           ["Phase difference at 1.1 GHz", "216&deg;", "calculated"]], left=(0, 1, 2)),
    item("sp-loss", "Loss measurement",
         h("Result"), table(["Path", "Power at analyzer (dBm)", "Loss of the added part (dB)"],
                            [["VCO &rarr; cable A &rarr; analyzer", "7.30", D], ["+ splitter, right output", "0.60", "6.70"], ["+ splitter, left output", "0.58", "6.72"],
                             ["+ cable B", "0.54", "0.04"], ["+ cable C", "0.33", "0.21"], ["+ cable D", "0.51", "0.09"]], left=(0,)),
         h("How it was made"), ol(["6 Oct. VCO at 5.38 V, 1.0388 GHz.", "The VCO was connected to the analyzer through cable A and the power was read.",
                                    "The splitter was added. The unused output had a 50 &Omega; load. The power was read again.",
                                    "Loss = power before minus power after.", "Each extra cable was added one at a time and measured the same way."])),
    item("sp-delay", "Delay calculation",
         math(r"\tau = \frac{\Delta L}{v} = \frac{0.114\ \text{m}}{0.7 \times 3\times10^{8}\ \text{m/s}} = 0.55\ \text{ns}"),
         math(r"\Delta\phi = 360^\circ \times f\tau = 360^\circ \times 1.1\times10^{9} \times 0.55\times10^{-9} = 216^\circ"),
         ul(["4.5 in = 0.114 m. Signal speed in the cable is taken as 0.7 times the speed of light.", "From 1.0 to 1.2 GHz the phase goes from 196&deg; to 236&deg;.",
             "The design drawing asks for 0.2 ns (3 to 4 cm), which gives 90&deg; at 1.1 GHz."])),
    item("sp-notes", "Notes",
         ul(["A resistive splitter loses 6 dB per output, not 3 dB. The 6.7 dB measurement is correct. The earlier 1.5 dB reading on 5 Oct was a measurement error.",
             "0.75 W is the maximum rating, not the power flowing. The note of 15 Sep (&ldquo;750 &rarr; 188 &rarr; 50 mW&rdquo;) used the rating as the signal power.",
             "Isolation between the outputs is about 6 dB. A reflection from one mixer port reaches the other mixer port 6 dB lower.",
             "Not tested: the mixer curve has more turning points than a 0.55 ns delay gives. One possible cause is reflections between the mixer ports through the splitter. A splitter with higher isolation, or attenuators on the mixer ports, would test this."])),
])

# ------------------------------------------------------------------ Mixer
C_STACK = '''dlo, dhi = levels(vd)                          # low and high level of the drive
edges = rising_edges(t, vd, dlo, dhi)          # time of each 50 % crossing

def stack_edges(t, y, edges, grid):            # grid = times relative to an edge
    acc, n = np.zeros(len(grid)), 0
    for e in edges:
        acc += np.interp(grid + e, t, y)       # this edge, shifted to time zero
        n += 1
    return acc / n                             # average of all edges'''
C_LOOKUP = '''use = cal[cal["vt_meas_v"] <= 1.2]             # the part where voltage only rises with frequency
mhz, mv = use["vco_freq_hz"] / 1e6, use["mixer_out_v"] * 1e3
order = np.argsort(mv)

def mv_to_mhz(x):
    return np.interp(x, mv[order], mhz[order])'''
C_SETTLE = '''fr = mv_to_mhz(mixer_mv)                       # mixer trace converted to frequency
f_final = np.median(fr[(t > 3000) & (t < 4500)])   # ns after the edge
inside = np.abs(fr - f_final) <= 2.0           # MHz
t_first = t[np.nonzero(inside & (t > -150))[0][0]]'''
C_DECONV = '''xn = normalise(drive)                          # drive, scaled 0 to 1
yn = normalise(mixer_to_vt(mixer_mv))          # mixer output converted back to tuning volts, scaled 0 to 1
DX = np.fft.rfft(np.gradient(xn) * win)        # differentiate, then Fourier transform
DY = np.fft.rfft(np.gradient(yn) * win)
Sxx = mean over the 20 steps of |DX|^2
Sxy = mean over the 20 steps of conj(DX) * DY
H = Sxy / Sxx                                  # output divided by input
H_reg = Sxy / (Sxx + 0.02 * Sxx[0])            # same, with a small number added so it cannot divide by zero
step = np.cumsum(np.fft.irfft(H_reg * G))      # G = low-pass at 7 MHz; cumsum integrates the impulse response'''

SETTLE_ROWS = [["0.20 &rarr; 0.40", "35.8 &rarr; 54.7", "752.9 &rarr; 763.2", "74", "122"], ["0.20 &rarr; 0.60", "36.0 &rarr; 75.2", "753.1 &rarr; 771.2", "100", "148"],
               ["0.20 &rarr; 0.80", "36.2 &rarr; 97.7", "753.4 &rarr; 777.9", "110", "158"], ["0.20 &rarr; 1.00", "36.4 &rarr; 115.3", "753.6 &rarr; 783.6", "114", "162"],
               ["0.20 &rarr; 1.15", "36.1 &rarr; 121.1", "753.2 &rarr; 787.2", "122", "170"]]
NOISE_ROWS = [["753.5", "0.85", "91", "62", "107", "71", "37"], ["763.3", "2.66", "138", "62", "52", "42", "17"], ["771.4", "2.90", "129", "62", "45", "35", "18"],
              ["778.0", "3.64", "137", "63", "38", "31", "15"], ["783.4", "2.32", "101", "65", "44", "31", "14"], ["785.9", "1.27", "84", "63", "66", "40", "21"]]

MIXER = "".join([
    "<h2>Mixer</h2>", '<p class="sub">Mini-Circuits ZX05-30W-S+ used as the phase detector. Fed by the splitter and delay cable.</p>',
    table(["Quantity", "Value", "Source"],
          [["Max RF power", "50 mW = 17.0 dBm = 1.58 V rms", "datasheet"], ["Max IF current", "40 mA", "datasheet"],
           ["LO level wanted", "+7 dBm", "datasheet"], ["LO level on the bench", "+0.6 dBm", "measured 6 Oct"],
           ["Conversion loss at 1.1 GHz", "6.4 dB typical, 9.0 dB max", "datasheet"],
           ["Output range, VCO source", "30.3 to 145.7 mV over 744&ndash;920 MHz", "measured 10 Oct"],
           ["Range where one voltage = one frequency", "744 to 788 MHz (30 to 121 mV)", "measured 10 Oct"],
           ["Slope in that range", "2.66 mV/MHz mean, 3.73 max, 0.05 min", "measured 10 Oct"],
           ["Repeatability", "0.22 mV", "measured 10 Oct"], ["Noise, full scope bandwidth", "84 to 142 &micro;V rms", "measured 10 Oct"],
           ["Frequency resolution, single reading", "38 to 66 kHz rms in 759&ndash;786 MHz", "measured 10 Oct"],
           ["Drift at fixed frequency, 74 min", "0.37 mV max = 140 kHz", "measured 10 Oct"],
           ["Time to follow a step, 10&ndash;90 %", "89 to 140 ns (drive is 145 ns)", "measured 10 Oct"],
           ["Delay, drive to output", "26 ns", "measured 10 Oct"]], left=(0, 1, 2)),
    item("mx-vf", "Output voltage vs frequency, VCO source",
         fig("mixer_v_vs_f.png", "Mixer output voltage against frequency"),
         h("Result"), ul(["Rises from 30.3 mV at 743.6 MHz to 121.3 mV at 788.4 MHz.", "Then: minimum 111.4 mV at 802.2 MHz, maximum 145.7 mV at 834.2 MHz, minimum 136.0 mV at 868.0 MHz, maximum 142.1 mV at 886.0 MHz.",
                          "Above 788 MHz one voltage matches more than one frequency."]),
         h("How it was made"), ol(["Same sweep as the VCO frequency measurement. At each of 176 tuning voltages:", "the analyzer read the VCO frequency,",
                                    "scope CH2 read the mixer output. Three records of 14 ms each were averaged.", "The mixer voltage is plotted against the frequency from the analyzer."]),
         h("Expected shape"), math(r"V_\text{out} \approx V_0 + A\cos(2\pi f\tau)"),
         p("With &tau; = 0.55 ns this is one slow curve with turning points 900 MHz apart. The measured curve has turning points 14 to 34 MHz apart. The cause was not found.")),
    item("mx-pluto", "Output voltage vs frequency, Pluto source, four power levels",
         fig("comp_phase_detector.png", "Phase detector output against frequency, Pluto and VCO sources"),
         h("Result"), table(["Pluto setting (dBm)", "Frequency range (MHz)", "Output range (mV)", "Output at 1.08 GHz (mV)"],
                            [["&minus;2", "1000&ndash;1080", "24.3&ndash;45.7", "45.7"], ["&minus;6", "1000&ndash;1135", "15.1&ndash;46.1", "26.4"],
                             ["&minus;11", "1000&ndash;1200", "7.3&ndash;44.6", "11.9"], ["&minus;12.25", "1000&ndash;1305", "5.3&ndash;32.7", "8.3"]]),
         ul(["The output voltage depends on input power. At 1.08 GHz it changes from 45.7 mV to 8.3 mV over 10 dB.", "At &minus;12.25 dBm: minimum near 1.03 GHz, maximum at 1.20 GHz."]),
         h("How it was made"), ol(["September. Pluto SDR &rarr; splitter &rarr; two cables &rarr; mixer &rarr; multimeter.", "The Pluto frequency was stepped by hand in 5 MHz steps and the multimeter read at each.",
                                    "This was repeated at four Pluto power settings."]),
         h("Right plot, 10 October"),
         ul(["This is the computer-run sweep. The Syscomp stepped the VCO tuning pin from 0 to 3.5 V in 0.02 V steps, 176 points.",
             "At each step the spectrum analyzer read the VCO frequency (x axis). Scope CH2 read the mixer IF output into 1 M&Omega;, averaged over three 14 ms records (y axis).",
             "The Syscomp reaches 3.52 V at most, so the sweep covers 744 to 920 MHz. That is below the 1.0 to 1.2 GHz band the JACON uses.",
             "Green band, 744 to 788 MHz: the output only rises, 30 to 121 mV, so each voltage matches one frequency. Above 788 MHz it turns at 802, 834, 868 and 886 MHz, so one voltage matches several frequencies.",
             "A 0.55 ns delay alone gives turning points 900 MHz apart, not 14 to 34 MHz apart. The cause is not known.",
             "The +0.6 dBm per mixer port in the legend was measured after the splitter on 6 Oct at 1.04 GHz. It was not measured again during this sweep.",
             "The two plots are different bands, sources and powers. They are not the same curve."])),
    item("mx-vt", "Output voltage vs tuning voltage", fig("mixer_v_vs_vt.png", "Mixer output against tuning voltage"),
         h("How it was made"), p("The same data as the frequency plot, plotted against the tuning voltage instead of the frequency.")),
    item("mx-lut", "Mixer look up table",
         fig("mapping.png", "Mixer output voltage against VCO frequency as measured, the same points used as a look up, and the slope"),
         h("Result"), ul(["Valid from 743.6 to 788.4 MHz, 30.3 to 121.3 mV.", "Point-to-point roughness 0.084 mV = 40 kHz.", "Slope 0.05 to 3.73 mV/MHz. Below 755 MHz and above 785 MHz the slope is small, so a small voltage error is a large frequency error."]),
         h("How it was made"), ol(["Take the 61 calibration points with tuning voltage 0 to 1.2 V. In this range the mixer voltage only rises with frequency.",
                                    "Left panel: these points, frequency on the x axis, voltage on the y axis.", "Middle panel: the same points with the axes swapped.",
                                    "To convert a voltage, find the two points on either side of it and draw a straight line between them.", "Right panel: the slope between neighbouring points."]),
         math(r"f(V) = f_i + (V - V_i)\,\frac{f_{i+1} - f_i}{V_{i+1} - V_i} \qquad \delta f = \frac{\delta V}{dV/df}"),
         code(C_LOOKUP), p("Full table: see the " + link("#lut-mixer", "Look up tables") + " tab.")),
    item("mx-step", "Step response",
         fig("step_rise.png", "Rising steps: drive, mixer output, frequency"), fig("step_fall.png", "Falling steps: drive, mixer output, frequency"),
         h("Result"), ul(["The mixer output follows each step. 10&ndash;90 % time 89 to 140 ns rising, 93 to 128 ns falling.", "The drive voltage takes 145 ns and has a spike at the start. The mixer is responding to that shape."]),
         h("How it was made"), ol(["The Syscomp drove the VCO tuning pin with a 50 kHz square wave. Low level 0.2 V. High level 0.4, 0.6, 0.8, 1.0 or 1.15 V.",
                                    "The scope recorded the drive (CH1) and the mixer output (CH2) for 2.8 ms. That holds about 140 rising and 140 falling edges. Three recordings per step.",
                                    "The time of each edge was found from where the drive crossed half-way between its low and high levels.",
                                    "All the edges were shifted to the same time zero and stacked on top of each other, then averaged. About 420 edges per curve. Averaging reduces the noise by about 20 times.",
                                    "Top panel: average drive voltage. Middle panel: average mixer voltage. Bottom panel: the mixer voltage converted to frequency with the look up table.",
                                    "These are the recorded signals. Nothing has been divided out."]),
         math(r"\bar{y}(\tau) = \frac{1}{N}\sum_{k=1}^{N} y(t_k + \tau) \qquad N \approx 420"), code(C_STACK)),
    item("mx-settle", "Time to within 2 MHz of the final frequency",
         fig("settle_rise.png", "Rising steps with a 2 MHz band, voltage and frequency"), fig("settle_fall.png", "Falling steps with a 2 MHz band"),
         h("Result"), table(["Step on Vt (V)", "Mixer (mV)", "Frequency (MHz)", "Within 2 MHz, after drive 50 % (ns)", "Within 2 MHz, after drive starts (ns)"], SETTLE_ROWS),
         ul(["Falling steps: 82 to 164 ns after the drive 50 % point.", "After entering the band the frequency stays inside it. There is no overshoot."]),
         h("How it was made"), ol(["Start from the averaged step traces.", "Left column: the measured mixer voltage. Right column: the same trace converted to frequency with the look up table.",
                                    "The final frequency is the median of the trace from 3 to 4.5 &micro;s after the edge.", "The green band is the final frequency &plusmn;2 MHz. On the left it is converted back to mV with the look up table.",
                                    "The red dot is the first sample inside the band."]),
         math(r"t_\text{in} = \min\{\, t : |f(t) - f_\text{final}| \le 2\ \text{MHz} \,\}"), code(C_SETTLE)),
    item("mx-rise", "10&ndash;90 % time vs step size", fig("transition_time.png", "Transition times against step size"),
         h("How it was made"), ol(["For each averaged trace, take the start level and the end level.", "Find the time it reaches 10 % of the way and the time it reaches 90 % of the way. The difference is the 10&ndash;90 % time.",
                                    "This was done for the drive voltage, the mixer voltage and the converted frequency.", "The mixer and frequency times differ because the look up table is curved."]),
         math(r"s(t) = \frac{y(t) - y_0}{y_1 - y_0} \qquad t_r = t(s{=}0.9) - t(s{=}0.1)")),
    item("mx-deconv", "Deconvolution",
         fig("deconvolution.png", "Transfer function magnitude and phase, valid range, and step responses"),
         h("Result"), ul(["Gain is within 1 dB of flat up to 3 MHz.", "Delay 26 ns.", "The step response of the part alone rises in 68 ns. A perfect part measured the same way also gives 68 ns. So the part is faster than this measurement can show.",
                          "Valid only up to 7 MHz. The drive edge has almost no content near 10 MHz, so the division gives a false peak there (grey area)."]),
         h("How it was made"), ol(["The recorded mixer output is the response of the part to the Syscomp edge, which is slow and has a spike. The aim is the response to a perfect step.",
                                    "First remove the curve of the look up table: convert each mixer trace back to the tuning voltage that gives that mixer voltage. Now input and output are both in volts and the gain is 1.",
                                    "Differentiate the drive and the output. A step becomes a pulse.", "Take the Fourier transform of both.",
                                    "Divide the output transform by the drive transform. This undoes the convolution and gives the transfer function of the part. All 20 steps are combined in the division.",
                                    "Multiply by a 7 MHz low-pass filter, inverse transform, and integrate. This gives the step response of the part alone.",
                                    "Bottom right panel: grey is the recorded drive, blue is the recorded output (the raw system response), red is the step response of the part with the drive divided out, dotted is a perfect part through the same 7 MHz filter."]),
         math(r"H(f) = \frac{\sum_i X_i'^{*}(f)\, Y_i'(f)}{\sum_i |X_i'(f)|^2} \qquad s(t) = \int_{-\infty}^{t} \mathcal{F}^{-1}\!\left\{ \frac{\sum_i X_i'^{*} Y_i'}{\sum_i |X_i'|^2 + \lambda}\, G(f) \right\} dt'"),
         p("X&prime; and Y&prime; are the transforms of the differentiated drive and output. &lambda; is 2 % of the value at zero frequency. G is the 7 MHz low-pass. Delay is the slope of the phase below 5 MHz."),
         math(r"\tau = -\frac{1}{2\pi}\frac{d\phi}{df}"),
         p("Scope CH1 was connected part-way along the cable to the VCO, so the recorded drive is not exactly the voltage at the tuning pin. This may be why the gain rises above 0 dB between 3 and 7 MHz."), code(C_DECONV)),
    item("mx-noise", "Noise",
         h("Result"), table(["Frequency (MHz)", "Slope (mV/MHz)", "Mixer noise (&micro;V rms)", "Scope alone (&micro;V rms)", "Freq. noise, full bandwidth (kHz)", "1 MHz bandwidth (kHz)", "100 kHz bandwidth (kHz)"], NOISE_ROWS),
         p("The values include the scope noise, so the part itself is quieter."),
         h("How it was made"), ol(["The tuning voltage was held fixed, waveform off.", "Scope CH2 was set to AC coupling, 1 mV/div, and recorded 1.4 ms.", "The rms of the record is the voltage noise.",
                                    "CH3 with nothing connected was recorded with the same settings. That is the scope noise.", "Voltage noise divided by the look up table slope at that frequency gives frequency noise.",
                                    "For the 1 MHz and 100 kHz columns the record was low-pass filtered first."]),
         math(r"\sigma_f = \frac{\sigma_V}{dV/df} \qquad \text{example: } \frac{137\ \mu\text{V}}{3.64\ \text{mV/MHz}} = 38\ \text{kHz}")),
    item("mx-drift", "Drift over 74 minutes", fig("drift_heatmap.png", "Heat maps of frequency, mixer output and power deviation over 74 minutes"),
         h("Result"), ul(["Middle panel. At 1.0 to 1.6 V the mixer output fell steadily, by 0.4 mV per hour at most.", "At a fixed frequency in the 744&ndash;788 MHz range the output changed by at most 0.37 mV. 0.37 mV / 2.66 mV/MHz = 140 kHz."]),
         h("How it was made"), p("Same 18 sweeps and same method as the VCO drift plot. Each cell is one reading minus the median for that voltage.")),
    item("mx-notes", "Notes",
         h("Measured"), ul(["The output depends on input power as well as frequency. The look up table is valid only at the power it was measured at.",
                            "The LO port had +0.6 dBm. The datasheet level is +7 dBm.", "All scope readings were into 1 M&Omega;. A 50 &Omega; load on the IF port will give a different voltage."]),
         h("From the datasheet"), ul(["RF port VSWR 2.8 to 3.5 near 1 GHz. LO port 1.7 to 2.0.", "LO&ndash;IF isolation 7 dB minimum, so some RF appears on the output."]),
         h("Consequences"), ul(["The RF limiting amp in the design keeps the power fixed. Without it a strong and a weak radar give different voltages at the same frequency.",
                                "The limiting amp output must be under +23.5 dBm: mixer limit +17 dBm plus 6.5 dB splitter loss.", "The mixer has never received more than about 3 mW. Its limit is 50 mW."])),
])

# ------------------------------------------------------------------ Test gear
GEAR = "".join([
    "<h2>Test gear</h2>",
    item("g-cgr", "Syscomp CGR-201",
         table(["Quantity", "Value"], [["Output range", "&minus;4.0 to +3.52 V"], ["Offset step", "1.875 mV per code"], ["Amplitude step", "1.33 to 1.40 mV pk-pk per code"],
                                       ["Edge 10&ndash;90 %", "145 ns, with a spike at the start about half the step height"], ["Connection", "USB serial, COM12, 115200 baud"]], left=(0, 1)),
         ul(["With a waveform selected and amplitude 0 it still outputs about 100 mV pk-pk of that waveform. For DC the waveform must be switched off.",
             "It returns to default settings when its USB is unplugged.", "It can output negative voltages. The scripts refuse to set less than &minus;0.1 V."]), p(link(DS["cgr"], "Datasheet"))),
    item("g-scope", "Siglent SDS1104X-E oscilloscope",
         table(["Quantity", "Value"], [["Bandwidth", "100 MHz"], ["Sample rate", "1 GSa/s; 500 MSa/s when CH1 and CH2 are both on"], ["Resolution", "8 bit"], ["Input", "1 M&Omega; only"], ["Noise at 1 mV/div", "60 to 65 &micro;V rms"]], left=(0, 1)),
         ul(["CH1 with CH3 gives 1 GSa/s on both.", "It does not trigger on a channel that is switched off.", "A steady DC level with no noise reads in steps of one bit. Some noise is needed to read between steps.",
             "Stopping a script during a data transfer blocks its USB link until the cable is unplugged and plugged back.", "The tuning voltages in these notes are scope readings, accurate to a few percent. They were not checked with a multimeter."])),
    item("g-sa", "Siglent SSA3021X spectrum analyzer",
         table(["Quantity", "Value"], [["Range", "9 kHz to 2.1 GHz"], ["Marker step at 2 MHz span", "2.7 kHz"], ["Repeat readings", "within 0.03 MHz and 0.1 dB"]], left=(0, 1)),
         ul(["The marker must be read after a complete sweep. Reading earlier gave power errors of 15 dB.", "At a wide span the marker step is large: 2.67 MHz at a 2 GHz span."])),
    item("g-sm", "Signal Hound SM200B spectrum analyzer",
         table(["Quantity", "Value"], [["Range", "100 kHz to 20 GHz"], ["Capture bandwidth", "160 MHz"], ["Software", "Spike 4.0.17 installed; SM API 2.3.10 loads from Python"], ["Status", "not yet connected to the computer"]], left=(0, 1)),
         ul(["Read the maximum input power on its label before connecting an amplifier to it.", "Python files are in <code>clinic\\claude\\signal_hound\\</code>."])),
    item("g-pluto", "ADALM-Pluto SDR", ul(["Used as a 1.0&ndash;1.2 GHz source in September.", "Maximum output +11 dBm = 12.6 mW (team notes).", "Measured 12 Oct: about 0 dBm at attenuation 0 dB and tone scale 0.5. See the Pluto tab.", "GNU Radio flowgraphs: <code>pluto_simple_tx.grc</code>, <code>soapy_simple_tx.grc</code>."]), p(link(DS["pluto"], "ADI wiki"))),
])

# ------------------------------------------------------------------ Errors
ERRORS = "".join([
    "<h2>Errors found</h2>",
    item("e-leak", "Syscomp output not steady at amplitude 0",
         table(["Syscomp setting", "Vt ripple", "Analyzer shows"], [["Square selected, amplitude 0", "48 mV rms, 116 mV pk-pk", "two peaks, 769.7 and 773.1 MHz"], ["Waveform off", "2 mV rms (scope noise)", "one peak, 771.4 MHz"]], left=(0, 1, 2)),
         ul(["Affected: calibration runs 1 and 2, the first noise test, the partial sweep with the open tee, and the static curve of 10 Oct morning.", "Their frequencies are wrong by &minus;1.75 to +0.40 MHz.", "Fixed by switching the waveform off. Run 3 and everything after it is correct.", "Step tests were not affected. They use a real square wave with levels read on the scope."])),
    item("e-early", "Analyzer marker read before the sweep finished",
         ul(["Power readings jumped by 15 dB between neighbouring points.", "Fixed by doing one complete sweep before each reading.", "After the fix, six readings in a row agreed within 0.1 dB and 0.03 MHz.", "The open tee port was wrongly blamed for this at first."])),
    item("e-tee", "Open tee port",
         fig("comparison.png", "Open tee and closed tee compared, 0 to 0.7 V"), fig("bad.png", "Partial sweep with the open tee port"),
         ul(["The first wiring had a second tee with one port left open. It was replaced with a male-male adaptor.", "15 points were recorded with the open port before the change.",
             "With the port closed the VCO ran 1.5 to 3.2 MHz lower at the same voltage.", "Both plots were taken before the Syscomp fix. Frequencies are wrong by up to 1.7 MHz. The power panel in the second plot is the early-reading error and is not valid."])),
])

# ------------------------------------------------------------------ Tests to run
def test(tid, name, part, wire, you, me, result, extra=""):
    return item(tid, f"{tid.upper().replace('T-', '')}. {name}",
                table(["", ""], [["Part", part], ["Wiring", wire], ["You do", you], ["Computer does", me], ["Result", result]], left=(0, 1)), extra)


TESTS = "".join([
    "<h2>Tests to run</h2>",
    item("t-safety", "Rules before any test", ul(["Read the maximum input power on the Signal Hound SM200B label. Do not exceed it.", "Put a fixed attenuator before the SM200B whenever an amplifier is in the path.",
                                                 "Use a DC block if the part under test can put DC on its output.", "Do not connect the Furuno radar to anything by cable. It is 2.2 kW peak. Radar tests are over the air only."]), open_=True),
    item("t-gear", "What the computer can control",
         table(["Gear", "Connection", "Computer can", "Status"],
               [["Signal Hound SM200B", "USB 3.0", "sweep to 20 GHz, read peak and channel power, capture pulses", "software installed; device not connected yet"],
                ["Siglent SSA3021X", "USB", "sweep to 2.1 GHz, read peak frequency and power", "working"], ["Siglent SDS1104X-E", "USB", "read DC levels and waveforms to 100 MHz", "working"],
                ["Syscomp CGR-201", "USB", "DC to 3.52 V, square waves", "working"], ["ADALM-Pluto", "USB", "tone at 325 MHz&ndash;3.8 GHz", "working; see the Pluto tab"],
                ["ADF5355 PLL", "depends on the board", "set the LO frequency", "board not known"], ["Bench supplies", "by hand", "nothing", "manual"]], left=(0, 1, 2, 3)),
         p("Not decided: the source for 9.3&ndash;9.5 GHz test signals. Options: (1) a second ADF5355 at 9.4 GHz, (2) Pluto at 1.0&ndash;1.2 GHz into the TX mixer with the 8.3 GHz LO, (3) the radar over the air. Option 2 can be swept by the computer.")),
    "<h3>RX chain (input RF)</h3>",
    test("t-rx0", "Source and cables", "9.4 GHz source, every cable", "source &rarr; cable &rarr; SM200B. Swap each cable in turn.", "connect; say which cable is in", "sweep 9.3&ndash;9.5 GHz, read level and frequency", "source power and frequency across the band; loss of each cable at 9.4 GHz"),
    test("t-rx1", "Horn antennas", "two horns, 8.2&ndash;12.4 GHz", "source &rarr; horn A, facing horn B &rarr; SM200B. Gap at least 1 m, measured.", "set the gap; rotate one horn 90&deg; when asked", "sweep and read received power", "gain in dBi across the band (drawing: 10&ndash;15); loss with crossed polarization",
         math(r"G_\text{dBi} = \tfrac{1}{2}\left( P_r - P_t + 20\log_{10}\frac{4\pi d f}{c} \right)")),
    test("t-rx2", "Power limiter", "the chosen limiter", "source &rarr; limiter &rarr; SM200B", "change attenuators to step the input power", "read output at each step", "loss at low power; level where it starts limiting; pass if output stays under +15 dBm"),
    test("t-rx3", "LNA", "ZX60-5123LN+, 6 V (not 12 V)", "source &rarr; 30 dB attenuator &rarr; LNA &rarr; 20 dB attenuator &rarr; SM200B. Then with a 50 &Omega; load on the LNA input.", "power the LNA; read the supply current; swap attenuators", "sweep frequency; step input power; read noise floor with input terminated", "gain across the band (expect +22 dB); output level at 1 dB compression (expect +17 dBm); noise figure (expect 1.4 dB)",
         math(r"NF \approx N_\text{out}\,[\text{dBm/Hz}] + 174 - G")),
    test("t-rx4", "LO chain", "ADF5355 &rarr; ZX60-14012L-S+ &rarr; ZX10-2-1252-S+", "PLL &rarr; SM200B. Add the buffer amp. Add the splitter and read each output with the other terminated.", "set the PLL to 8.3 GHz; add one part at a time", "read frequency, power and spurs at each stage", "LO frequency error; power at each mixer LO port (need +10 dBm)"),
    test("t-rx5", "RX mixer", "ZX05-14LH-S+", "source at &minus;20 dBm &rarr; RF port; LO chain &rarr; LO port; IF port &rarr; SM200B", "connect", "step RF 9.3&ndash;9.5 GHz; read IF at 1.0&ndash;1.2 GHz; read 8.3 GHz at the IF port", "conversion loss across the band (expect 6.7 dB); LO leakage at the IF port"),
    test("t-rx6", "IF amp", "ZX60-P103LN+ or ZX60-2534MA-S+", "Pluto &rarr; 30 dB attenuator &rarr; amp &rarr; 20 dB attenuator &rarr; analyzer. For the 2534MA use 60 dB before the amp: its input limit is &minus;15 dBm.", "power the amp at 5.0 V; swap attenuators", "step Pluto frequency and level; read output", "gain across 1.0&ndash;1.2 GHz (expect 15.6 dB for P103LN, 43.5 dB for 2534MA); maximum output power. Full steps: IF amp tab."),
    test("t-rx7", "IF splitter", "ZFRSC-42-S+", "Pluto &rarr; splitter; one output &rarr; analyzer, other &rarr; 50 &Omega; load. Then swap.", "swap outputs", "step 1.0&ndash;1.2 GHz; read both", "loss per output (expect 6.0&ndash;6.5 dB); difference between outputs"),
    test("t-rx8", "Whole RX chain by cable", "limiter &rarr; LNA &rarr; mixer &rarr; IF amp &rarr; splitter", "source &rarr; attenuators &rarr; chain &rarr; SM200B. Add one part per run.", "add the next part; set attenuators as asked", "sweep frequency; step input from &minus;50 to &minus;10 dBm", "total gain compared with the sum of the parts; input level where the chain compresses; IF level at the splitter outputs"),
    test("t-rx9", "Over the air, then the radar", "horn, limiter, then the full chain", "horn &rarr; limiter &rarr; attenuator &rarr; SM200B, no LNA. Then the full chain.", "place the horn; run the radar; keep people out of the beam", "capture pulses", "radar frequency, pulse width, repetition rate, received power at that distance; the same pulse at the IF"),
    "<h3>Phase detector</h3>",
    test("t-pd1", "Calibration in 1.0&ndash;1.2 GHz", "splitter, delay cable, mixer", "Pluto &rarr; splitter &rarr; two cables &rarr; mixer &rarr; scope CH2. Tee to an analyzer.", "connect", "step 1.0&ndash;1.2 GHz in 1 MHz steps; read voltage and frequency", "mV against MHz in the design band; whether one voltage matches one frequency over all 200 MHz"),
    test("t-pd2", "Power sensitivity", "same", "same as PD1", "nothing", "repeat the sweep at five power levels", "MHz of error per dB of power change"),
    test("t-pd3", "Delay length", "same, different extra cable", "same; extra cable none, 1.5 in, 4.5 in, longer", "swap the cable", "repeat the sweep", "which length gives one voltage per frequency over 1.0&ndash;1.2 GHz with the largest slope"),
    test("t-pd4", "With the limiting amp", "limiting amp, splitter, mixer", "Pluto &rarr; attenuators &rarr; limiting amp &rarr; splitter &rarr; mixer", "check the amp output is under +23.5 dBm first", "repeat the sweep for inputs &minus;37 to +3 dBm", "whether the curve stays the same over the input power range"),
    test("t-pd5", "Response to a pulse", "full phase detector", "Pluto pulsed, 50 ns to 1.2 &micro;s &rarr; chain &rarr; scope", "connect", "capture and stack pulses", "time from pulse start until the voltage is within tolerance. Total allowed reply delay is 0.7 &micro;s."),
    "<h3>Envelope detector</h3>",
    test("t-env1", "Detector curve", "ADL5511", "Pluto &rarr; attenuators &rarr; detector &rarr; scope", "swap attenuators", "step the level; read output voltage", "volts out against dBm in at 1.0&ndash;1.2 GHz"),
    test("t-env2", "Pulse response", "ADL5511", "Pluto pulsed &rarr; detector &rarr; scope", "connect", "capture and stack pulses", "rise and fall time. Shortest radar pulse is 50 ns."),
    test("t-env3", "Comparator and DAC", "ADCMP600, nanoDAC", "detector &rarr; comparator; DAC sets threshold; scope on both", "set the DAC", "capture both signals", "delay from pulse edge to comparator edge; weakest pulse detected at each DAC setting"),
    "<h3>TX chain (output RF)</h3>",
    test("t-tx1", "VCO in 1.0&ndash;1.2 GHz", "VCO", "source reaching 8 V &rarr; VCO &rarr; attenuator &rarr; analyzer", "build an op-amp stage, or set a supply by hand", "read frequency at each voltage", "look up table from 4.8 to 7.8 V in the final wiring"),
    test("t-tx2", "Sample and hold", "ADG1211, 100 pF, ADA4622-1", "Syscomp step &rarr; sample and hold &rarr; scope", "connect", "capture", "acquisition time; droop while holding. VCO needs &plusmn;22 mV."),
    test("t-tx3", "Keying switch", "ADG901", "Pluto tone &rarr; switch &rarr; SM200B; Syscomp square wave on the control pin", "connect", "read on and off levels; capture switching", "loss when on; leakage when off; switching time"),
    test("t-tx4", "TX mixer", "ZX05-14LH-S+", "Pluto 1.0&ndash;1.2 GHz &rarr; IF port; LO 8.3 GHz &rarr; LO port; RF port &rarr; SM200B", "connect", "step Pluto; read 9.3&ndash;9.5, 7.1&ndash;7.3 and 8.3 GHz", "output power at 9.3&ndash;9.5 GHz; image at 7.1&ndash;7.3 GHz; LO leakage"),
    test("t-tx5", "Image filter", "VHF-8400+", "TX mixer output &rarr; filter &rarr; SM200B", "connect", "read the same three bands", "loss at 9.3&ndash;9.5 GHz (expect 1.4&ndash;1.6 dB); rejection at 7.1&ndash;7.3 GHz (expect 24&ndash;28 dB)"),
    test("t-tx6", "Power amp", "not chosen", "filter &rarr; amp &rarr; 30 dB attenuator rated for the power &rarr; SM200B", "power the amp", "step input; read output", "gain; maximum output"),
    "<h3>Oscillators, keying and control</h3>",
    test("t-ctl1", "PLL", "ADF5355", "PLL &rarr; SM200B", "set 8.3 GHz", "read frequency, power, spurs; capture a frequency change", "frequency error; output power; lock time"),
    test("t-ctl2", "Reply frequency", "whole system by cable, through attenuators", "source 9.3&ndash;9.5 GHz in; SM200B on the output", "connect", "step frequency and level; read reply frequency", "reply minus input frequency. Pass: &plusmn;1.5 MHz (long pulses), &plusmn;3.5 MHz (short pulses)."),
    test("t-ctl3", "Reply delay", "FPGA, comparator, keying switch", "scope on the comparator output and the keying line", "connect", "capture", "time from radar pulse to start of reply. Pass: 0.7 &micro;s or less."),
    test("t-ctl4", "Morse keying and blocking", "FPGA, keying switch", "SM200B on the output; repeated input pulses", "connect", "capture the reply", "dash = 3 dots; no reply for 100 &micro;s after the previous reply ends"),
])
