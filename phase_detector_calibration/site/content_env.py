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
    p("Bench: Pluto TX (1.0&ndash;1.2 GHz tone, up to about 0 dBm) straight into RFIN. Supply 5.00 V with a 60 mA limit. VENV to Syscomp CGR-201 input A. VRMS and EREF to a multimeter. "
      "Procedure with fill-in tables: <code>envelope_detector/ED-TEST-PROCEDURE.md</code>.") +
    steps_table([
        ["1", "Power and DC levels", "supply only, nothing on the SMAs", "set 5.00 V, 60 mA limit; read current, EREF, VENV, VRMS", "nothing", "21.5 mA; EREF &asymp; 1.1 V; VENV &asymp; EREF; VRMS &asymp; 23 mV", "all close to expected"],
        ["2", "CW curve at 1.1 GHz", "Pluto TX &rarr; RFIN; VENV &rarr; CGR-201 A; meter on VRMS", "type the VRMS reading at each step", "step the Pluto 89 &rarr; 0 dB attenuation; average 3 CGR-201 captures per step; save a CSV", "VENV &minus; EREF = 1.47 &times; V<sub>in</sub>; VRMS = 1.91 &times; V<sub>in</sub> + offset", "gain within the datasheet; the two outputs agree"],
        ["3", "Band edges", "same", "same", "same at 1.0 and 1.2 GHz, 3 levels", "same as 1.1 GHz within 0.5 dB", "flat across the IF band"],
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
           ["3. Band edges", "not run", "", "", ""], ["4. Pulse response", "not run", "", "", ""]], left=(0, 1, 2, 3, 4)) +
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
        "VENV scatter seen by the CGR-201: 2 mV rms with no signal, rising to 13.7 mV at 0 dBm (4 %). Probably the Pluto&rsquo;s leftover tones beating with the main tone. It averages out here, but the comparator sees it sample by sample.",
        "EREF and VENV fell 10 mV while the board warmed up, then held within 1&ndash;2.4 mV over the 10-minute sweep."]) +
    '<div class="note">Under question: the detector puts the Pluto at 0.0 dBm (tone scale 0.7, 0 dB, 1100 MHz). The Pluto tab measured &minus;0.36 dBm at tone scale 0.5 on the spectrum analyzer, which predicts +2.6 dBm at 0.7. '
    'The 2.6 dB difference is not explained: a different Pluto sample scaling in the Soapy driver (the Pluto tab used libiio), this detector&rsquo;s gain being low, or the cable. '
    'Next check: run the same Soapy flowgraph into the spectrum analyzer.</div>' +
    h("Comparator threshold from this curve") +
    table(["Threshold above the no-RF VENV", "+10 mV", "+20 mV", "+50 mV", "+100 mV", "+200 mV"],
          [["Trips at (dBm at RFIN)", "&minus;25.5", "&minus;21.5", "&minus;15.5", "&minus;10.4", "&minus;4.5"]], left=(0,)) +
    ol(["Let the detector run about 10 minutes.", "With no RF, read VENV (CGR-201 or meter).", "Set the comparator threshold to that value plus the margin. Start at +20 mV: ten times the drift once warm."]) +
    p("Files in <code>envelope_detector/</code>: <code>data/ed_sweep_1.10GHz_20261026_220822.csv</code> and <code>.png</code>, <code>ed_sweep.py</code> (Pluto + CGR-201 sweep), "
      "<code>plot_ed_sweep.py</code>, <code>ed_test_pluto_tx_soapy.grc</code>, <code>ED-TEST-RESULTS.md</code>, <code>ED-TEST-PROCEDURE.md</code>, <code>LIMITS-AND-TEST-PLAN.md</code>, wiring drawings."))

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
        ["4", "Detector to comparator", "VENV &rarr; IN+ (no termination); CGR-201 output (DC) &rarr; 1 k&Omega; &rarr; IN&minus;; OUT+ &rarr; CGR-201 B", "warm up 10 min; set IN&minus; = no-RF VENV + 20 mV", "pulse the Pluto; trigger on B; count pulses", "one output pulse per RF pulse above &minus;21.5 dBm", "no missed or extra pulses"]]) +
    '<div class="note">Set the CGR-201 output to DC before connecting it: it can swing to &minus;3 V and the comparator input limit is &minus;0.5 V. The 1 k&Omega; limits the current if it does.</div>',
    NOT_RUN)
