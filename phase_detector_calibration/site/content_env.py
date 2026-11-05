"""Envelope detector (ADL5511) and comparator (ADCMP604) tabs."""
from content import table, ul, ol, p, h, link, math, fig, D
from content_parts import part_tab, steps_table, NOT_RUN

ADI = "https://www.analog.com/media/en/technical-documentation/data-sheets/"

# measured 26 Oct, CW at 1100 MHz; envelope_detector/data/ed_sweep_1.10GHz_20261026_220822.csv
# attenuation, VENV rise over the no-RF baseline (mV), VRMS on the DMM (V)
SWEEP = [(89, -0.4, 0.031), (80, -0.5, 0.031), (70, -0.4, 0.032), (60, -0.1, 0.031), (50, -0.4, 0.032), (40, 0.3, 0.035), (35, 1.0, 0.037),
         (30, 4.2, 0.038), (25, 10.9, 0.045), (20, 25.6, 0.065), (15, 53.8, 0.098), (10, 105.3, 0.165), (5, 189.0, 0.270), (0, 327.9, 0.446)]


def _sweep_rows():
    rows = []
    for att, rise, vrms in SWEEP:
        pin = -att - 0.02
        vin_mv = (10 ** (pin / 10) * 1e-3 * 50) ** 0.5 * 1e3
        sig = rise > 2
        rows.append([str(att), f"{pin:.0f}".replace("-", "&minus;") if att <= 40 else "none (floor)", f"{rise:.1f}".replace("-", "&minus;"),
                     f"{rise / vin_mv:.2f}" if sig else D, f"{vrms:.3f}"])
    return rows


ENV = part_tab(
    "Envelope detector", "Analog Devices ADL5511 on the ADL5511-EVALZ board. Takes one output of the IF splitter (1.0&ndash;1.2 GHz) and gives a voltage that follows the size of the IF signal. "
    "The comparator after it decides &ldquo;radar pulse present&rdquo;.", "env",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Frequency range", "DC", D, "6", "GHz"], ["Supply VPOS", "4.75", "5.0", "5.25 (5.5 absolute max)", "V"],
           ["Supply current, no RF / at +15 dBm in", D, "21.5 / 43.8", D, "mA"],
           ["Input range, &plusmn;1 dB error (100 MHz&ndash;1.9 GHz)", "&minus;29", D, "+17", "dBm"],
           ["RF input, absolute max", D, D, "+19 (79 mW, 2.0 V rms; 5.6 V pk-pk)", "dBm"],
           ["Input on the eval board", D, "&asymp; 50 &Omega; (75 &Omega; shunt R5 with the chip&rsquo;s 250 &Omega;), 100 pF AC coupling", D, ""],
           ["EREF, envelope reference", D, "1.1", D, "V"],
           ["VENV &minus; EREF gain (100 MHz / 900 MHz / 1.9 GHz)", D, "1.42 / 1.46 / 1.50", D, "V per V rms"],
           ["VENV max output; load", D, D, "3.5; load &ge; 500 &Omega; and &le; 10 pF; 15 mA drive", "V"],
           ["Envelope bandwidth / 10&ndash;90 % response / delay", D, "130 MHz / 4 ns / 2 ns", D, ""],
           ["VRMS gain (100 MHz / 900 MHz / 1.9 GHz)", D, "1.92 / 1.90 / 1.96", D, "V per V rms"],
           ["VRMS max output; load; offset with no signal", D, "offset 23 mV", "3.8; load &ge; 10 k&Omega;", "V"],
           ["ENBL high (device on)", "3.6", D, D, "V"]]) +
    p(link(ADI + "adl5511.pdf", "Datasheet") + " (Rev. E): Table 1 specifications, Table 2 absolute maximum ratings, eval board section. "
      "Eval board: VPOS and GND pins; RFIN and VENV on SMA; EREF, VRMS and GND on clip-on test points (their SMA pads are empty); SW1 toward its label = enabled.") +
    '<div class="note">VENV sits at about 1.1 V with no signal. Into 50 &Omega; that is 22 mA, more than its 15 mA drive. Never terminate VENV in 50 &Omega;: scope inputs at 1 M&Omega;, short cable.</div>',
    ul(["The output follows the RF voltage, not the power: 5 dB more input = &times;1.78 more output.",
        "At about 1.1 GHz the gains are 1.47 V/V (VENV) and 1.91 V/V (VRMS), interpolated between the 900 MHz and 1.9 GHz datasheet columns. "
        "Across 1.0&ndash;1.2 GHz they change by about 0.1 dB, so the detector is flat over the IF band.",
        "VENV follows each pulse (4 ns rise). VRMS is averaged and gives the mean power."]) +
    math(r"V_\text{ENV} - V_\text{EREF} = 1.47\,V_\text{in,rms} \qquad V_\text{RMS} = 1.91\,V_\text{in,rms} + V_\text{offset} \qquad V_\text{in,rms} = \sqrt{10^{P_\text{dBm}/10}\cdot 1\,\text{mW}\cdot 50\,\Omega}") +
    table(["Input (dBm)", "&minus;30", "&minus;20", "&minus;10", "0", "+10", "+17"],
          [["VENV &minus; EREF (mV)", "10", "33", "103", "327", "1030", "2310"], ["VENV (V), EREF = 1.1 V", "1.11", "1.13", "1.20", "1.43", "2.13", "3.41"]], left=(0,)) +
    h("Level at the detector in the JACON") +
    ul(["The drawing gives &minus;36 to +4 dBm at the IF amp input. With the ZX60-P103LN+ (+15.6 dB) and the IF splitter (6.0&ndash;6.5 dB loss) the detector sees about &minus;27 to +14 dBm.",
        "The weakest radar is then only about 3 dB above the detector&rsquo;s floor (&minus;30 dBm, measured), and the strongest is 3 dB under its +17 dBm limit.",
        "At +14 dBm VENV is about 2.7 V. The comparator (ADCMP604) needs its supply at 3.3 V or more to accept that (input max VCC + 0.5 V)."]) +
    math(r"P_\text{det} = P_\text{IF amp in} + 15.6 - (6.0\ \text{to}\ 6.5) = -36 + 15.6 - 6.5 = -26.9\ \text{dBm} \quad\text{to}\quad +4 + 15.6 - 6.0 = +13.6\ \text{dBm}"),
    p("Bench: Pluto TX (1.0&ndash;1.2 GHz tone, up to about 0 dBm) straight into RFIN. Supply 5.00 V with a 60 mA limit. VENV to Syscomp CGR-201 input A. VRMS to a multimeter (26 Oct) or CGR-201 input B (1 Nov). EREF on a multimeter. "
      "Procedure with fill-in tables: <code>envelope_detector/ED-TEST-PROCEDURE.md</code>.") +
    steps_table([
        ["1", "Power and DC levels", "supply only, nothing on the SMAs", "set 5.00 V, 60 mA limit; read current, EREF, VENV, VRMS", "nothing", "21.5 mA; EREF &asymp; 1.1 V; VENV &asymp; EREF; VRMS &asymp; 23 mV", "all close to expected"],
        ["2", "CW curve at 1.1 GHz", "Pluto TX &rarr; RFIN; VENV &rarr; CGR-201 A; meter on VRMS", "type the VRMS reading at each step", "step the Pluto 89 &rarr; 0 dB attenuation; average 3 CGR-201 captures per step; save a CSV", "VENV &minus; EREF = 1.47 &times; V<sub>in</sub>; VRMS = 1.91 &times; V<sub>in</sub> + offset", "gain within the datasheet; the two outputs agree"],
        ["3", "Band edges", "same", "nothing", "same sweep at 1.0, 1.1 and 1.2 GHz, 14 levels each", "same as 1.1 GHz within 0.5 dB", "ratio of the two outputs the same at all three"],
        ["4", "Pulse response", "Pluto pulsed &rarr; RFIN; VENV &rarr; CGR-201 A, or a 1 M&Omega; scope for edges", "set the pulse width", "capture pulses", "pulse top equals the CW value; 4 ns rise (scope only)", "pulse height within 5 % of CW"]]) +
    '<div class="note">The Pluto alone cannot hurt the detector: its highest output (about 0 to +5 dBm) is 14 dB or more under the +19 dBm limit.</div>',
    table(["Test", "Result", "Expected", "Pass?", "Date"],
          [["1. Supply current", "0.017 A (85 mW) with no RF; 0.020 A with RF", "21.5 mA typ", "pass", "26 Oct"],
           ["1. EREF", "1.148 V cold; 1.138 V after warm-up (start of sweep); 1.139 V at the end", "1.1 V nominal", "pass", "26 Oct"],
           ["1. VENV, no RF", "1.139 V on the meter; 1.141 to 1.144 V on the CGR-201", "&asymp; EREF", "pass", "26 Oct"],
           ["1. VRMS, no RF", "31&ndash;32 mV (47 mV just after power-up)", "23 mV typ", "pass; offset subtracted", "26 Oct"],
           ["2. VENV gain, &minus;10 to 0 dBm", "1.49, 1.51, 1.47 V/V", "1.47 V/V", "pass", "26 Oct"],
           ["2. VENV at &minus;20 dBm", "25.6 mV above the no-RF level", "26 mV (datasheet table at &minus;20 dBm)", "pass", "26 Oct"],
           ["2. VENV and VRMS agree", "VENV rise &divide; (VRMS &minus; offset) = 0.76&ndash;0.81 from &minus;25 to 0 dBm", "0.77", "pass", "26 Oct"],
           ["2. Floor", "outputs sink into their offsets below about &minus;30 dBm", "&minus;29 dBm (&plusmn;1 dB range)", "pass", "26 Oct"],
           ["3. Band edges", "VENV &divide; VRMS 0.773 / 0.768 / 0.766 at 1.0 / 1.1 / 1.2 GHz: +0.06 and &minus;0.02 dB against the centre. Same floor", "flat within about 0.1 dB", "pass", "1 Nov"],
           ["4. Pulse height, 100 &micro;s", "0.985&ndash;1.000 &times; CW (mean 0.992); every pulse seen", "1.00", "pass", "1 Nov"],
           ["4. Pulse height, 10 &micro;s", "0.970&ndash;0.981 &times; CW (mean 0.975); every pulse seen. The shortfall is the Pluto&rsquo;s ripple and edges (see 1 Nov checks)", "1.00", "pass", "1 Nov"],
           ["4. Rise time", "not measured: the Pluto&rsquo;s 0.65 &micro;s edges hide the detector&rsquo;s 4 ns. Needs the scope", "4 ns", "", ""]], left=(0, 1, 2, 3, 4)) +
    fig("env_cw_sweep_1100MHz.png", "Envelope detector at 1100 MHz: both outputs against Pluto level, input power from each output, and VENV against calibrated input power") +
    h("Test 2, CW at 1100 MHz, 26 Oct") +
    table(["Pluto attenuation (dB)", "Power at RFIN (dBm)", "VENV rise (mV)", "VENV gain (V/V)", "VRMS (V)"], _sweep_rows(), left=()) +
    ol(["Pluto (Soapy sink, Homebrew GNU Radio) set to a tone 100 kHz above its LO, tone scale 0.7, at 1100 MHz. The script turned it on at 89 dB attenuation and stepped down to 0 dB.",
        "At each step it waited 1 s, then averaged three CGR-201 captures (12 288 samples, 156 kHz sampling) of VENV on input A. VENV rise is the mean minus the mean before the Pluto was turned on (1.1412 V).",
        "VRMS was read on a multimeter at each step and typed in. Its offset with no signal, 31.4 mV, is the mean of the 89 to 50 dB rows.",
        "Power at RFIN: both outputs, at 10, 5 and 0 dB attenuation, with the datasheet gains, give the Pluto level. Every other row is that minus the attenuation (the AD9364 steps are exact: setting the gain and reading back the register gave &minus;89.0, &minus;79.0, 0.0 dB).",
        "VENV gain is the VENV rise divided by the input voltage at that power."]) +
    math(r"V_\text{in} = \frac{V_\text{RMS} - 31.4\ \text{mV}}{1.91} \;\text{or}\; \frac{V_\text{ENV,rise}}{1.47} \qquad P_\text{RFIN} = -A - 0.02\ \text{dBm} \quad (\text{worst disagreement } 0.24\ \text{dB})") +
    h("What it shows") +
    ul(["The detector meets its datasheet at 1.1 GHz: gain 1.47&ndash;1.51 V/V from &minus;10 to 0 dBm; 25.6 mV at &minus;20 dBm against the datasheet&rsquo;s 26 mV.",
        "Below about &minus;15 dBm VENV falls under the straight line 1.47 &times; V<sub>in</sub>: 2 dB low at &minus;20 dBm, 5 dB low at &minus;30 dBm. Use the measured curve, not the formula, to set comparator thresholds.",
        "Usable range on this bench: &minus;30 dBm (detector floor) to 0 dBm (the most this Pluto gives at tone scale 0.7).",
        "VENV scatter seen by the CGR-201: 2 mV rms with no signal, rising to 13.7 mV at 0 dBm (4 %). Checked on 1 Nov: a 400 kHz line from the Pluto, not the detector (see below). It averages out here, but the comparator sees it sample by sample.",
        "EREF and VENV fell 10 mV while the board warmed up, then held within 1&ndash;2.4 mV over the 10-minute sweep."]) +
    '<div class="note">Under question: the detector puts the Pluto at 0.0 dBm (tone scale 0.7, 0 dB, 1100 MHz). The Pluto tab measured &minus;0.36 dBm at tone scale 0.5 on the spectrum analyzer, which predicts +2.6 dBm at 0.7. '
    'The 2.6 dB difference is not explained: a different Pluto sample scaling in the Soapy driver (the Pluto tab used libiio), this detector&rsquo;s gain being low, or the cable. '
    'Next check: run the same Soapy flowgraph into the spectrum analyzer.<br><b>1 Nov:</b> the runs on 1 Nov used a <b>different Pluto</b> (serial &hellip;dfdb; 26 Oct &hellip;41f6), which reads 0.4 dB lower through the same detector, so part of the difference may be between Pluto units. Still open: every dBm on this tab rests on the detector&rsquo;s datasheet gains until the spectrum analyzer check is done.</div>' +
    h("Comparator threshold from this curve") +
    table(["Threshold above the no-RF VENV", "+10 mV", "+20 mV", "+50 mV", "+100 mV", "+200 mV"],
          [["Trips at (dBm at RFIN)", "&minus;25.5", "&minus;21.5", "&minus;15.5", "&minus;10.4", "&minus;4.5"]], left=(0,)) +
    ol(["Let the detector run about 10 minutes.", "With no RF, read VENV (CGR-201 or meter).", "Set the comparator threshold to that value plus the margin. Start at +20 mV: ten times the drift once warm."]) +
    h("1 Nov: band edges, pulse response, extra checks") +
    ul(["<b>Different Pluto</b> from 26 Oct: serial &hellip;dd1f84bfdb (26 Oct: &hellip;f3647c41f6). The same 1.1 GHz sweep read 0.44&ndash;0.49 dB lower at every level, and the ratio of the two detector outputs was unchanged, so the difference is the Pluto. The &ldquo;TX level &rarr; dBm&rdquo; calibration is per Pluto unit; <code>ed_sweep.py</code> now writes the serial into every CSV.",
        "<b>Long RF cable</b> Pluto &rarr; RFIN for the runs below, after a short cable gave intermittent RF at three steps (that run is kept as <code>&hellip;_INTERMITTENT-RF_do-not-use.csv</code>). Re-seating the SMA and repeating 0 and &minus;10 dB gave the same readings within 0.03 dB.",
        "VRMS read on CGR-201 <b>input B</b> instead of the meter; EREF read on the meter before and after each run (1.137 &rarr; 1.136 V, 0.0 mV drift within each run)."]) +
    '<div class="note"><b>Limitation, CGR-201 input B (VRMS):</b> its absolute readings are only good to several mV. Against the meter it read 1.4&ndash;1.7 % low, and its offset drifted from &minus;7.5 to &minus;2.5 mV over 75 minutes. '
    'Hook on GND repeated within 1 mV, and swapping the leads showed the error stays with input B, so it is calibration, not wiring. '
    'Every VRMS value below is a <i>rise</i> (reading minus that run&rsquo;s no-RF reading), which cancels the offset; the gain error is about 0.15 dB. Input A (VENV) read 4&ndash;8 mV above the meter&rsquo;s EREF.</div>' +
    fig("env_band_edges_20261101.png", "Envelope detector at 1.0, 1.1 and 1.2 GHz: VENV rise against Pluto level, ratio of its two outputs, and power at RFIN per frequency") +
    table(["Pluto TX level (dB)", "VENV rise 1.0 GHz (mV)", "1.1 GHz", "1.2 GHz", "VENV &divide; VRMS 1.0 GHz", "1.1 GHz", "1.2 GHz"],
          [["&minus;89 to &minus;40", "&le; 0.4", "&le; 0.4", "&le; 0.3", D, D, D], ["&minus;30", "3.3", "3.0", "2.8", D, D, D],
           ["&minus;25", "8.0", "8.0", "7.6", "0.821", "0.825", "0.805"], ["&minus;20", "18.8", "18.6", "17.8", "0.733", "0.741", "0.732"],
           ["&minus;15", "40.8", "39.3", "38.3", "0.766", "0.759", "0.757"], ["&minus;10", "81.8", "78.7", "76.2", "0.778", "0.767", "0.760"],
           ["&minus;5", "153.3", "147.1", "143.5", "0.776", "0.772", "0.777"], ["0", "267.7", "257.5", "250.1", "0.773", "0.773", "0.770"]], left=()) +
    ul(["Rises are against each sweep&rsquo;s own floor rows (TX &le; &minus;50 dB). VRMS is divided by 0.986 for input B&rsquo;s gain. No step was flagged unsteady.",
        "<b>The detector is flat across the IF band:</b> the ratio of its outputs at TX &ge; &minus;15 dB averages 0.773 / 0.768 / 0.766, which is +0.06 and &minus;0.02 dB against 1.1 GHz. One comparator threshold works for 9.3&ndash;9.5 GHz.",
        "Pluto (&hellip;dfdb) plus the long cable: power at RFIN = TX level &minus; 1.9 / &minus; 2.2 / &minus; 2.4 dB at 1.0 / 1.1 / 1.2 GHz (from the detector&rsquo;s datasheet gains; same caveat as above)."]) +
    fig("env_pulses_20261101.png", "Envelope detector pulse response at 1.1 GHz: pulse height against CW, level between pulses, and VRMS while pulsed") +
    table(["Pulse (equal gap)", "TX level (dB)", "CW rise (mV)", "Pulse height (mV)", "Height &divide; CW", "Between pulses &minus; no-RF (mV)", "Pulses seen", "VRMS rise pulsed &divide; CW"],
          [["100 &micro;s", "&minus;20", "18.4", "18.3", "1.000", "+0.1", "25", "0.658"], ["100 &micro;s", "&minus;10", "78.9", "78.0", "0.989", "+1.0", "25", "0.676"],
           ["100 &micro;s", "&minus;5", "147.7", "146.7", "0.994", "+1.0", "24", "0.664"], ["100 &micro;s", "0", "258.1", "254.3", "0.985", "+2.4", "24", "0.650"],
           ["10 &micro;s", "&minus;20", "18.2", "17.7", "0.971", "+0.3", "31", "0.651"], ["10 &micro;s", "&minus;10", "78.3", "76.8", "0.981", "+0.6", "31", "0.701"],
           ["10 &micro;s", "&minus;5", "147.0", "142.6", "0.970", "+2.0", "30", "0.688"], ["10 &micro;s", "0", "256.8", "250.9", "0.977", "+3.5", "30", "0.706"]], left=(0,)) +
    ol(["At each level the script measured CW, then switched the Pluto to pulses (2 MS/s, on and off for the same time) and the CGR-201 to 2.5 MS/s (100 &micro;s) or 20 MS/s (10 &micro;s).",
        "Pulse height: mean of the flat top minus the mean between pulses, skipping the edges (edges found on a smoothed copy with hysteresis). Checked first on synthetic captures with known heights: within 0.3 mV."]) +
    ul(["<b>Pulse height equals CW within 1&ndash;3 %</b>, so the CW threshold table holds for pulses.",
        "Between pulses VENV returns to within 0.1&ndash;3.5 mV of the no-RF level, well under a +20 mV threshold.",
        "VRMS reports the average power while pulsed (on half the time: &radic;0.5 = 0.707). Use VENV for pulses."]) +
    fig("env_ripple_pulse_shape_20261101.png", "VENV ripple with RF on and off, its spectrum with a 400 kHz line, and the average 10 microsecond pulse") +
    table(["Check", "Result"],
          [["VENV ripple source (CW, TX 0 dB)", "One line at <b>400 kHz, 13.7 mV peak</b>, and 800 kHz (1.2 mV). Not there with RF off (only lines near 70 kHz under 1 mV). 400 kHz is 4 &times; the 100 kHz tone offset: the tone beating with a Pluto TX spur at &minus;300 kHz, about &minus;25 dBc. <b>From the Pluto, not the detector.</b>"],
           ["10 &micro;s pulse shape (40 MS/s, 9 pulses averaged)", "10&ndash;90 % edges 0.65 &micro;s (the Pluto at 2 MS/s). Overshoot at both edges and ringing <i>before</i> each rising edge, which only a digital filter can do: the Pluto&rsquo;s. The top wobbles &plusmn;2&ndash;3 % with the 400 kHz ripple, which is locked to the pulses. <b>The 10 &micro;s shortfall above is this, not the detector.</b>"],
           ["Input B: calibration or fault", "Hook on GND &minus;2.0 to &minus;3.2 mV, repeatable within 1 mV; with the leads swapped the error stays with input B. Calibration."],
           ["RF connector re-seated", "0 dB: 258.2 mV (257.5&ndash;258.1 before); &minus;10 dB: 79.0 mV (78.7&ndash;78.9). Within 0.03 dB"]], left=(0, 1)) +
    '<div class="note">Unverified: <mark data-k="q">that the 400 kHz ripple comes from the Pluto&rsquo;s &minus;3 &times; f spur.</mark> Its frequency is locked to the tone offset, which points that way; changing the offset to 150 kHz should move it to 600 kHz. '
    'Until then, treat the mechanism as likely, not shown. For the comparator test: at full Pluto output VENV carries &plusmn;14 mV of ripple and the pulses overshoot about 15 % at their edges. Keep the threshold well under the pulse top.</div>' +
    ul(["Not done: the detector&rsquo;s own 4 ns rise and 50 ns&ndash;1.2 &micro;s pulses (needs the Pluto at a higher sample rate and the oscilloscope); an absolute power check of the Pluto and cable on the spectrum analyzer."]) +
    p("Files in <code>envelope_detector/</code>: <code>data/</code> (26 Oct and 1 Nov CSVs and plots; each 1 Nov CSV names its Pluto), <code>ed_sweep.py</code> (Pluto + CGR-201 sweep, CW or pulses), "
      "<code>ed_capture.py</code> (raw captures), <code>plot_ed_sweep.py</code>, <code>plot_band_and_pulses.py</code>, <code>plot_capture.py</code>, <code>ed_test_pluto_tx_soapy.grc</code>, "
      "<code>ED-TEST-RESULTS.md</code>, <code>ED-TEST-PROCEDURE.md</code>, <code>LIMITS-AND-TEST-PLAN.md</code>, wiring drawings."))

COMP = part_tab(
    "Comparator", "Analog Devices ADCMP604 on the EVAL-ADCMP604BKSZ board (on hand). The drawing calls for the ADCMP600. Output high while the envelope detector output is above the threshold.", "cmp",
    table(["Quantity", "ADCMP604 (on hand)", "ADCMP600 (drawing)", "Unit"],
          [["Supply", "2.5&ndash;5.0 (6.0 absolute max)", "2.5&ndash;5.5 (6.0 absolute max)", "V"], ["Supply current", "15 typ, 21 max", "3&ndash;4", "mA"],
           ["Input range", "&minus;0.2 to VCC + 0.2", "&minus;0.2 to VCC + 0.2", "V"], ["Input absolute max", "&minus;0.5 to VCC + 0.5; &plusmn;50 mA", "&minus;0.5 to VCC + 0.5; &plusmn;50 mA", "V"],
           ["Offset", "&plusmn;5 max", "&plusmn;2 typ, &plusmn;5 max", "mV"], ["Hysteresis", "under 0.1, fixed (ADCMP605 has a pin to set it)", "2, fixed", "mV"],
           ["Propagation delay (50 mV overdrive)", "1.6", "3.5 at 2.5 V, 4.3 at 5.5 V", "ns"], ["Minimum pulse width", "1.3", "3 to 4.5", "ns"],
           ["Output", "LVDS: 350 mV differential into 100 &Omega;, common mode 1.125&ndash;1.375 V", "CMOS, 0 to VCC", ""],
           ["Package", "SC70-6: Q, VEE, VP, VN, VCC, Q-bar", "SOT-23-5 / SC70-5", ""]], left=(0,)) +
    p(link(ADI + "ADCMP604_605.pdf", "ADCMP604 datasheet") + ", " + link(ADI + "ADCMP600_601_602.pdf", "ADCMP600 datasheet") + ". "
      "Eval board: SMA for IN+ (J1), IN&minus; (J3), IN+FB (J2), IN&minus;FB (J4), OUT+ (J7), OUT&minus; (J8); banana jacks VCC, AGND, CGND/VEE. "
      "The back of the board has decoupling capacitors only, no resistors: the inputs are not terminated and there is no 100 &Omega; across the outputs.") +
    '<div class="note">LVDS output: it cannot drive the ADG901 control pin, a 3.3 V FPGA pin or the CGR-201 digital inputs directly. Put 100 &Omega; across OUT+ and OUT&minus;. '
    'To the FPGA: an ECP5 differential input or an LVDS receiver (SN65LVDT2 at 3.3 V has the 100 &Omega; built in).</div>',
    ul(["VP (IN+) = VENV from the detector, VN (IN&minus;) = threshold. Q high while VENV is above the threshold.",
        "Supply 3.3 V: VENV can reach about 2.7 V in the JACON (&minus;27 to +14 dBm at the detector), within VCC + 0.2 V.",
        "With almost no hysteresis, noise on VENV near the threshold makes the output toggle several times per pulse. Keep the threshold 10 mV or more above the no-RF VENV, or add positive feedback.",
        "Threshold for a given radar level: Envelope detector tab, &ldquo;Comparator threshold from this curve&rdquo;. +20 mV trips at &minus;21.5 dBm at the detector."]),
    p("Wiring drawings: <code>envelope_detector/bench_wiring.svg</code>. Supply 3.3 V, 40 mA limit, CGND/VEE tied to AGND.") +
    steps_table([
        ["1", "Supply", "board only", "set 3.3 V, 40 mA; inputs grounded", "nothing", "15 mA", "under 21 mA"],
        ["2", "Trip point", "CGR-201 output &rarr; 1 k&Omega; &rarr; IN+ (slow triangle 0.8&ndash;1.6 V, never negative); pot &rarr; IN&minus; at 1.20 V; 100 &Omega; across OUT&plusmn;; CGR-201 A on IN+, B on OUT+", "set the pot", "capture A and B", "OUT+ steps between &asymp;1.03 and 1.38 V where IN+ crosses 1.20 V", "within &plusmn;5 mV"],
        ["3", "Chatter", "same, triangle slowed to 1&ndash;10 Hz", "nothing", "count extra edges", "some", "recorded"],
        ["4", "Detector to comparator", "VENV &rarr; IN+ (no termination); CGR-201 output (DC) &rarr; 1 k&Omega; &rarr; IN&minus;; OUT+ &rarr; CGR-201 B", "warm up 10 min; set IN&minus; = no-RF VENV + 20 mV", "pulse the Pluto; trigger on B; count pulses", "one output pulse per RF pulse above &minus;21.5 dBm", "no missed or extra pulses"],
        ["5", "Ripple vs threshold", "as step 4", "Pluto CW at TX 0 dB, then TX &minus;10 dB", "step IN&minus; up from the no-RF VENV past the CW VENV in the smallest steps available; note B at each step", "B solid high, then toggling at &asymp;400 kHz, then solid low. Width of the toggling band = ripple peak to peak (&asymp;27 mV at TX 0 dB)", "band &asymp;&plusmn;5 % of the VENV rise at both levels"],
        ["6", "Edge chatter", "as step 4, B on the Siglent scope instead (CGR-201 is 5 MHz and misses ns bursts)", "pulsed, IN&minus; = no-RF + 20 mV", "zoom on each OUT+ edge", "a single edge", "count extra edges per pulse"]]) +
    '<div class="note"><b>For whoever runs the comparator tests: the Pluto puts a ripple on VENV.</b> '
    'On 1 Nov, a steady Pluto tone gave a &plusmn;13.7 mV, 400 kHz ripple on VENV at TX 0 dB (Envelope detector tab, figure &ldquo;ripple source and pulse shape&rdquo;). '
    'It comes from a Pluto spur about 25 dB below the tone, not from the detector, so a real radar pulse should not have it. '
    'The ADCMP604 has almost no hysteresis (&lt;0.1 mV) and a 1.6 ns delay, so it will follow this ripple wherever the ripple crosses the threshold.<ul>'
    '<li><b>Threshold well below the pulse top</b> (no higher than the middle of the VENV rise): the ripple never reaches it, one clean output pulse. This is the normal case.</li>'
    '<li><b>Threshold near the pulse top:</b> the output toggles at 400 kHz during the pulse. Fix: lower the threshold.</li>'
    '<li><b>Pulse only just above the threshold</b> (the weakest detectable level): ripple and noise cross the threshold whatever value is chosen, so the output chatters. '
    'The threshold cannot fix this; count it in the S-curve (step 2 of Test C) and plan for the FPGA to ignore &ldquo;on&rdquo; periods shorter than a minimum width.</li>'
    '<li><b>Slow Pluto edges (0.65 &mu;s):</b> noise during the rise can give a short burst of toggles at each edge. Ns-scale, so look with the Siglent scope (step 6).</li></ul>'
    'Step 5 measures the ripple with the comparator itself; no separate ripple test is needed first. '
    '<mark data-k="q">Unverified: that the ripple is a fixed &asymp;&plusmn;5 % of the VENV rise at every level (predicted from the &minus;25 dBc spur, measured only at TX 0 dB; '
    'below about &minus;15 dBm it is under the CGR-201&rsquo;s 5 mV steps).</mark> Step 5 at two levels checks it. '
    'Moving the Pluto tone offset from 100 kHz to 1 MHz should move the ripple to 4 MHz, which would confirm the source.</div>' +
    '<div class="note">Set the CGR-201 output to DC before connecting it: it can swing to &minus;3 V and the comparator input limit is &minus;0.5 V. The 1 k&Omega; limits the current if it does.</div>',
    NOT_RUN)
