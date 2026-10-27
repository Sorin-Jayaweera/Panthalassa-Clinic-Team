"""Per-part tabs. Every part has the same four sections: Specs, Expected behavior, Test plan, Results."""
import content as C
from content import item, table, ul, ol, p, h, link, math, D

PDF = "https://www.minicircuits.com/pdfs/"


def part_tab(title, sub, pid, specs, expected, plan, results):
    return "".join([f"<h2>{title}</h2>", f'<p class="sub">{sub}</p>',
                    item(pid + "-specs", "Specs", specs, open_=True),
                    item(pid + "-expected", "Expected behavior", expected),
                    item(pid + "-plan", "Test plan", plan),
                    item(pid + "-results", "Results", results)])


def steps_table(rows):
    return table(["#", "Test", "Wiring", "You do", "Computer does", "Expected", "Pass if"], rows, cls="parts plan", left=(1, 2, 3, 4, 5, 6))


NOT_RUN = p("Not run yet.")

# ------------------------------------------------------------------ Limiter
LIMITER = part_tab(
    "Limiter", "Marki Microwave EVAL-HLM-20P: the HLM-20PSM limiter chip on an SMA evaluation board. Between the RX antenna and the LNA. Keeps strong radar pulses from damaging the LNA.", "lim",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Frequency range", "DC", D, "20", "GHz"], ["Insertion loss, DC&ndash;20 GHz", D, "0.5", "1.5", "dB"], ["Insertion loss at 10 GHz (features list)", D, "0.7", D, "dB"],
           ["Return loss", D, "15", D, "dB"], ["Input power at 1 dB compression", D, "+15", D, "dBm"],
           ["Flat leakage (output while clamping), at 1 GHz", D, "+17", D, "dBm"], ["Flat leakage, at 20 GHz", D, "+13", D, "dBm"],
           ["Flat leakage at 9.4 GHz (straight line between the two)", D, "&asymp; +15", D, "dBm"],
           ["Spike leakage (energy let through at a pulse&rsquo;s leading edge)", D, "0.1", D, "erg"], ["Recovery time after a pulse", D, "8", D, "ns"],
           ["RF power, average, absolute max", D, D, "5 (+37.0 dBm)", "W"], ["RF power, peak (pulsed), absolute max", D, D, "50 (+47.0 dBm)", "W"]]) +
    p("Source: " + link("https://markimicrowave.com/products/surface-mount/limiters/hlm-20psm/datasheet/", "HLM-20PSM datasheet, Rev A") + " (electrical specifications, page 4; absolute maximum ratings, page 3) and the " +
      link("https://markimicrowave.com/products/evaluation-board/limiters/eval-hlm-20p/", "EVAL-HLM-20P page") + ". No local PDF: Marki&rsquo;s site refuses scripted downloads, so open the link in a browser.") +
    '<div class="note">The board is marked with an input and an output side. The input side goes toward the antenna. Passive: no power supply.</div>',
    ul(["Below about +10 dBm in, it is a short piece of line: about 0.5&ndash;0.7 dB loss at 9.4 GHz.",
        "Around +15 dBm in, its diodes start to conduct and the output stops following the input (1 dB compression at +15 dBm in).",
        "Well above that, the output stays near the flat leakage, about +15 dBm at 9.4 GHz (+13 to +17 dBm across its band), whatever the input, up to 5 W average and 50 W peak.",
        "For each pulse the leading edge gets through before the diodes turn on (spike leakage, 0.1 erg). After the pulse it recovers in about 8 ns.",
        "What this means for the LNA (ZX60-5123LN+, absolute max input +15 dBm): the limiter alone does not keep the LNA safe. Put at least 10 dB of pad between them for testing."]) +
    math(r"P_\text{out} \approx P_\text{in} - 0.5\ \text{dB} \quad (P_\text{in} \ll +15\ \text{dBm}) \qquad P_\text{out} \approx +15\ \text{dBm} \quad (P_\text{in} \gg +15\ \text{dBm at 9.4 GHz})"),
    p("Every step starts with a leak check: the same wiring with a 50 &Omega; load in place of the antenna. A reading only counts if it is at least 20 dB above that.") +
    steps_table([
        ["1", "Leak floor", "50 &Omega; load &rarr; limiter &rarr; pads &rarr; SM200B, radar at the test distance", "transmit", "read the Max Hold peak", "below &minus;45 dBm", "20 dB under the readings in 2&ndash;4"],
        ["2", "Loss at low level", "Vivaldi &rarr; pads &rarr; SM200B, then Vivaldi &rarr; limiter &rarr; pads, radar at 11.3 m", "swap the limiter in and out without moving the cable", "difference of the two peaks", "0.5&ndash;0.7 dB", "under 1.5 dB"],
        ["3", "Clamp curve", "same as 2, radar at 11.3, 8, 6, 4, 3 m (or more pads in front of the limiter at one distance)", "move the radar or change the front pads", "limiter output (reading + pads) vs input (reading without the limiter)", "follows the input to about +10 dBm, then flattens near +15 dBm", "never above +17 dBm out"],
        ["4", "Leading edge", "as 3 at the closest distance", "transmit", "I/Q capture at 50 MS/s or faster; look at the first 50 ns of each pulse", "a short overshoot", "overshoot under the LNA&rsquo;s +15 dBm"]]) +
    '<div class="note">Keep 29 dB of pads after the limiter whenever the SM200B is on it: the limiter can pass up to +17 dBm, and the SM200B&rsquo;s limit is +20 dBm.</div>',
    table(["Test (Radar tab number)", "Setup", "Result", "Expected", "Trust", "Date"],
          [["Direction", "board markings", "input side faces the antenna", D, "yes", "25 Oct"],
           ["Radar 8: low level", "Vivaldi &rarr; limiter &rarr; 29 dB, 11.3 m, foam off", "&minus;20 dBm (Sorin) / &minus;22.9 dBm (Spike) at the SM200B &rarr; +9 / +6.1 dBm out of the limiter", "passes, under 1.5 dB loss", "fair: about 10 dB above the leak", "25 Oct"],
           ["Radar 12 vs 11: loss", "same, with and without the limiter, 11.3 m", "&minus;30.2 vs &minus;29.4 dBm: 0.8 dB", "0.5&ndash;0.7 dB", "<b>no</b>: both at the leak floor (&minus;31.2 dBm)", "25 Oct"],
           ["Radar 13: strong signal", "same, radar at 3.96 m (13 ft)", "&minus;12.9 dBm at the SM200B &rarr; <b>+16.1 dBm out of the limiter</b>; no leading-edge spike at 20 ns resolution", "+13 to +17 dBm when clamping", "partly: the input was not measured, and the leak (&minus;21 to &minus;23 dBm) is only 8&ndash;10 dB below", "25 Oct"],
           ["Radar 14: strong signal, Spike", "same as 13", "&minus;15.27 dBm (Sorin&rsquo;s Spike screenshot; reference level &minus;20 dBm, may be compressed) &rarr; +13.7 dBm out", "as 13", "low", "25 Oct"],
           ["Radar 26a: pickup", "50 &Omega; load &rarr; limiter &rarr; 10 dB &rarr; LNA (off) &rarr; 29 dB, 11.5 m", "&minus;31 dBm, same as the load alone", D, "yes", "26 Oct"],
           ["Radar 27: in the chain", "Vivaldi &rarr; limiter &rarr; 20 dB &rarr; LNA &rarr; 19 dB, 11.5 m", "chain consistent with 0.8 dB limiter loss and 22&ndash;23 dB LNA gain", D, "fair", "26 Oct"]],
          left=(0, 1, 2, 3, 4, 5)) +
    p("Not yet shown: that it clamps. That needs test 3 with a leak floor at least 20 dB below the readings. Every reading is on the Radar tab, section &ldquo;Power readings by test&rdquo;."))

# ------------------------------------------------------------------ LNA
LNA = part_tab(
    "LNA", "Mini-Circuits ZX60-5123LN+. First amplifier after the antenna and limiter. 9.3&ndash;9.5 GHz.", "lna",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Frequency range", "5.5", D, "12.5", "GHz"], ["Gain", "19.0", "22.0", D, "dB"], ["Gain flatness", D, "&plusmn;0.6", D, "dB"],
           ["Noise figure", D, "1.4", D, "dB"], ["Output power at 1 dB compression", D, "+17.0", D, "dBm"], ["Output IP3", D, "+29.5", D, "dBm"],
           ["Input return loss", D, "10.5", D, "dB"], ["Output return loss", D, "14.0", D, "dB"],
           ["Supply voltage", "+5", "+6", "+10", "V"], ["Supply current", D, "80", "95", "mA"],
           ["RF input power, absolute max", D, D, "+15 (31.6 mW, 1.26 V rms)", "dBm"], ["Supply voltage, absolute max", D, D, "+12.0", "V"],
           ["Power dissipation, absolute max", D, D, "1.2", "W"]]) +
    '<div class="note">The design drawing says &ldquo;12 V DC operating voltage&rdquo;. The datasheet operating range is 5 to 10 V, typical 6 V. 12 V is the absolute maximum. Run it at 6 V.</div>' +
    p(link(PDF + "ZX60-5123LN+.pdf", "Datasheet") + ". Connectors: SMA female in and out. Internal regulator, reverse-voltage protected."),
    ul(["Draws about 80 mA at 6 V.", "Adds 22 dB at 9.3&ndash;9.5 GHz, flat within &plusmn;0.6 dB.",
        "Weak radar: &minus;50 dBm in gives &minus;28 dBm out.", "Strong radar: &minus;10 dBm in gives +12 dBm out. This is below the +17 dBm compression point.",
        "Gain starts to drop when the output reaches +17 dBm, which is an input of about &minus;4 dBm.",
        "With the input terminated in 50 &Omega;, output noise is about &minus;150.6 dBm/Hz."]) +
    math(r"P_\text{out} = P_\text{in} + G \qquad N_\text{out} = -174\ \text{dBm/Hz} + NF + G = -174 + 1.4 + 22 = -150.6\ \text{dBm/Hz}"),
    p("Needs a 9.3&ndash;9.5 GHz source, the SM200B, fixed attenuators good to 10 GHz, and a supply set to 6.0 V with a 120 mA current limit.") +
    steps_table([
        ["1", "Supply current", "LNA powered, input and output on 50 &Omega; loads", "set 6.0 V; read the current", "nothing", "80 mA", "under 95 mA"],
        ["2", "Gain vs frequency", "source &rarr; attenuators (so input is &minus;30 dBm) &rarr; LNA &rarr; 20 dB attenuator &rarr; SM200B", "connect; then remove the LNA for the reference run", "sweep 9.3&ndash;9.5 GHz with and without the LNA; subtract", "22 dB", "19 dB or more; flat within &plusmn;1 dB"],
        ["3", "Compression", "same", "swap attenuators so the input steps from &minus;30 to &minus;2 dBm", "read output at each step; find where gain is 1 dB below its low-power value", "+17 dBm out", "+15 dBm or more"],
        ["4", "Noise figure", "50 &Omega; load &rarr; LNA &rarr; SM200B, no attenuator", "connect", "read noise density at 9.4 GHz with the LNA on and off", "1.4 dB (&minus;150.6 dBm/Hz out)", "under 2.5 dB. Only valid if the SM200B floor is well below &minus;150 dBm/Hz"],
        ["5", "Stray signals", "same as 4", "nothing", "sweep 1&ndash;20 GHz", "noise only", "no lines above the noise"]]) +
    '<div class="note">Never put more than +15 dBm into the LNA. In test 3 stop at 0 dBm input. Keep the 20 dB attenuator on the output whenever the SM200B is connected.</div>',
    table(["Test", "Result", "Expected", "Pass?", "Date"],
          [["1. Supply current", "0.08 A at 6.0 V", "80 mA, max 95 mA", "pass", "12 Oct"], ["2. Gain vs frequency", "partial: one frequency (9.4047 GHz), over the air from the radar: &asymp; 23 dB (&plusmn;2 dB)", "22 dB", "pass at 9.4 GHz", "26 Oct"],
           ["3. Compression", "not run", "+17 dBm out", "", ""], ["4. Noise figure", "not run", "1.4 dB", "", ""], ["5. Stray signals", "not run", "none", "", ""]], left=(0, 1, 2, 3, 4)) +
    p("Test 1: read from the display of an Agilent E3630A supply, 6 V output. Input and output each had a 50 &Omega; termination. The display reads to 0.01 A, so the current is between 75 and 85 mA.") +
    h("Over the air with the Furuno radar, 25 and 26 Oct (Radar tab test numbers)") +
    table(["Test", "Chain", "Distance", "SM200B (max)", "Result", "Date"],
          [["10", "open cable &rarr; LNA (6 V, 0.08 A) &rarr; 29 dB", "11.3 m", "nothing on screen", "USB dropout of the SM200B, not the LNA. Current 0.08 A matched the datasheet. No damage.", "25 Oct"],
           ["18", "Vivaldi &rarr; limiter &rarr; LNA <b>unpowered</b> &rarr; 29 dB", "3.96 m", "&minus;10 dBm (Sorin)", "Not powered: the limiter can pass +17 dBm, above the LNA&rsquo;s +15 dBm absolute max input. A 10 dB pad was added before the LNA.", "26 Oct"],
           ["26a", "50 &Omega; load &rarr; limiter &rarr; 10 dB &rarr; LNA off &rarr; 29 dB", "11.5 m", "&minus;31 dBm (Sorin)", "leak floor, same as the load alone", "26 Oct"],
           ["26b", "same, LNA on", "11.5 m", "&minus;28 dBm (Sorin)", "+3 dB: radar pickup before the LNA, amplified, about equals the leak after it. No oscillation.", "26 Oct"],
           ["26c", "50 &Omega; load &rarr; limiter &rarr; 20 dB &rarr; LNA on &rarr; 19 dB", "11.5 m", "&minus;24.06 dBm (Sorin)", "leak floor for tests 27 and 28", "26 Oct"],
           ["27", "Vivaldi &rarr; limiter &rarr; 20 dB &rarr; LNA on &rarr; 19 dB", "11.5 m", "<b>&minus;7.94 dBm</b> (Spike)", "LNA output +11.1 dBm. Input &asymp; &minus;12.1 dBm (antenna +8.7 dBm from test 7, &minus;0.8 dB limiter, &minus;20 dB pad). <b>Gain &asymp; 23 dB</b> (datasheet 22). 16 dB over the leak floor. Linear: input 7 dB under the compression point.", "26 Oct"],
           ["28", "same, LNA off", "11.5 m", "&minus;25.85 dBm (Spike)", "17.9 dB below test 27. At the leak floor, so 17.9 dB is only a lower bound on the on/off difference.", "26 Oct"]],
          left=(0, 1, 2, 3, 4, 5)) +
    '<div class="note">Rules learned: at least 10 dB of pad between the limiter and the LNA (limiter output up to +17 dBm, LNA absolute max input +15 dBm). At 11.5 m from this radar, 20 dB before the LNA keeps it linear. Always measure the leak floor (a 50 &Omega; load in place of the antenna) for the same wiring first.</div>')

# ------------------------------------------------------------------ RX mixer
RXMIXER = part_tab(
    "RX mixer", "Mini-Circuits ZX05-14LH-S+. Converts 9.3&ndash;9.5 GHz to 1.0&ndash;1.2 GHz with an 8.3 GHz LO. The TX mixer is the same part.", "rxm",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["LO and RF frequency", "3700", D, "10000", "MHz"], ["IF frequency", "DC", D, "4000", "MHz"], ["LO power", D, "+10 (10 mW, 0.71 V rms)", D, "dBm"],
           ["Conversion loss, 6200&ndash;10000 MHz", D, "6.7", "9.5", "dB"], ["Conversion loss at RF 9.0 GHz (typical data)", D, "6.88", D, "dB"],
           ["Conversion loss at RF 9.4 GHz (typical data)", D, "7.72", D, "dB"], ["LO&ndash;RF isolation, 6200&ndash;10000 MHz", "25", "35", D, "dB"],
           ["LO&ndash;IF isolation, 6200&ndash;10000 MHz", "9", "17", D, "dB"], ["RF input at 1 dB compression", D, "+5", D, "dBm"], ["IP3", D, "14", D, "dBm"],
           ["RF port VSWR at 9.4 GHz (typical data)", D, "4.01", D, ":1"], ["LO port VSWR at 8.2 GHz (typical data)", D, "2.18", D, ":1"],
           ["RF power, absolute max", D, D, "50 mW (+17 dBm, 1.58 V rms)", ""]]) +
    p(link(PDF + "ZX05-14LH-S+.pdf", "Datasheet") + ". Ports: LO = 2, RF = 3, IF = 1. The datasheet conversion loss is measured at a 30 MHz IF. Ours is 1.0&ndash;1.2 GHz, so expect some difference."),
    ul(["IF frequency = RF &minus; 8.3 GHz. 9.3 GHz gives 1.0 GHz. 9.5 GHz gives 1.2 GHz.", "Output is about 7 to 8 dB below the RF input.",
        "Weak radar: &minus;28 dBm in gives about &minus;36 dBm out.", "Strong radar: +12 dBm in. This is above the +5 dBm compression point, so the output will be less than +4 dBm and distorted. It is below the +17 dBm damage limit.",
        "LO leaks to the IF port 17 dB down: +10 &minus; 17 = &minus;7 dBm at 8.3 GHz. For a weak radar this is 29 dB stronger than the wanted signal.",
        "LO leaks to the RF port 35 dB down: &minus;25 dBm at 8.3 GHz going back toward the LNA.",
        "A signal at 7.1&ndash;7.3 GHz gives the same IF as 9.3&ndash;9.5 GHz. The drawing has no filter before this mixer."]) +
    math(r"f_\text{IF} = f_\text{RF} - f_\text{LO} \qquad P_\text{IF} = P_\text{RF} - L_c \qquad f_\text{image} = 2 f_\text{LO} - f_\text{RF}"),
    p("Needs the 8.3 GHz LO at +10 dBm (measure it first), a 9.3&ndash;9.5 GHz source, and the SM200B.") +
    steps_table([
        ["1", "LO level", "LO chain &rarr; SM200B", "set the PLL to 8.3 GHz", "read frequency and power", "+10 dBm at 8.300 GHz", "+7 to +13 dBm"],
        ["2", "Conversion loss vs frequency", "source at &minus;20 dBm &rarr; RF port 3; LO &rarr; port 2; IF port 1 &rarr; SM200B", "connect", "step RF 9.3&ndash;9.5 GHz; read the IF at 1.0&ndash;1.2 GHz; subtract from the RF level", "7 to 8 dB", "under 9.5 dB"],
        ["3", "Conversion loss vs LO power", "same, attenuators in the LO line", "swap LO attenuators: +4, +7, +10, +13 dBm", "repeat test 2 at 9.4 GHz", "lowest loss near +10 dBm", "loss changes less than 1 dB from +7 to +13"],
        ["4", "Compression", "same as 2", "swap RF attenuators: &minus;20 to +5 dBm", "read IF at each step", "1 dB compression at +5 dBm RF", "+3 dBm or more"],
        ["5", "LO leakage", "same as 2", "nothing", "read 8.3 GHz at the IF port; move the SM200B to the RF port and read again", "&minus;7 dBm at IF; &minus;25 dBm at RF", "IF under +1 dBm; RF under &minus;15 dBm"],
        ["6", "Image", "same as 2, source at 7.1&ndash;7.3 GHz", "retune the source", "read the IF", "same level as test 2", "recorded; decides if an RX filter is needed"]]) +
    '<div class="note">RF input limit is +17 dBm. Stay at +5 dBm or below.</div>',
    NOT_RUN)

# ------------------------------------------------------------------ IF amp
AMP_HEAD = ["Quantity", "ZX60-P103LN+", "ZX60-2534MA-S+", "ZX60-P162LN+"]
IFAMP = part_tab(
    "IF amp", "Amplifies the 1.0&ndash;1.2 GHz signal after the RX mixer. Three candidates.", "ifa",
    table(AMP_HEAD,
          [["Frequency range", "50&ndash;3000 MHz", "500&ndash;2500 MHz", "700&ndash;1600 MHz"],
           ["Gain at 1.0 GHz, typical", "15.6 dB (min 13.5)", "43.5 dB", "22.5 dB (min 20.9, max 24.5)"],
           ["Gain at 1.1&ndash;1.3 GHz", "between 15.6 (1 GHz) and 10.0 (2 GHz)", "43.7 to 43.8 dB", "20.5 dB at 1.3 GHz"],
           ["Noise figure at 1 GHz", "0.5 dB", "2.3 dB", "0.52 dB (max 0.95)"],
           ["Output at 1 dB compression, 1 GHz", "+22.4 dBm", "+19.2 dBm", "+19.9 dBm (min +17.5)"],
           ["Output IP3 at 1 GHz", "+39.4 dBm", "+16 dBm", "+29.9 dBm"],
           ["Input VSWR at 1 GHz", "1.65", "1.71", "1.19"], ["Output VSWR at 1 GHz", "1.47", "1.20", "1.38"],
           ["Supply voltage", "5.0 V", "5.0 V (or 2.8 V)", "4.0 V (3.8 to 4.2)"], ["Supply current", "95 mA (max 120)", "170 mA (max 190)", "52 mA (44 to 60)"],
           ["Supply voltage, absolute max", "5.5 V", "7 V", "5.5 V"],
           ["<strong>RF input, absolute max</strong>", "<strong>+21 dBm</strong> (126 mW, 2.51 V rms)", "<strong>&minus;15 dBm</strong> (0.032 mW, 0.040 V rms)", "<strong>+25 dBm</strong> (316 mW, 3.98 V rms)"],
           ["Power dissipation, absolute max", D, "0.5 W", D],
           ["Datasheet", link(PDF + "ZX60-P103LN+.pdf", "PDF"), link(PDF + "ZX60-2534MA+.pdf", "PDF"), link(PDF + "ZX60-P162LN+.pdf", "PDF")]], left=(0, 1, 2, 3)) +
    '<div class="note">The ZX60-2534MA-S+ is damaged by more than &minus;15 dBm at its input. The design drawing gives the IF level as &minus;37 to +3 dBm. A strong radar would destroy it. It also compresses once its input passes about &minus;24 dBm.</div>',
    table(["", "ZX60-P103LN+", "ZX60-2534MA-S+"],
          [["Weak radar, &minus;36 dBm in", "&minus;20 dBm out", "+7.5 dBm out"], ["Strong radar, +3 dBm in", "+18.6 dBm out, below compression", "input is 18 dB over the damage limit"],
           ["Input where output compresses 1 dB", "+7.8 dBm", "&minus;23.3 dBm"], ["After the IF splitter (&minus;6 dB), strong radar", "+12.6 dBm at each output", D]], left=(0, 1, 2)) +
    math(r"P_\text{in,1dB} = P_\text{out,1dB} - (G - 1) \qquad \text{P103LN: } 22.4 - 14.6 = +7.8\ \text{dBm} \qquad \text{2534MA: } 19.2 - 42.5 = -23.3\ \text{dBm}") +
    ul(["The P103LN handles the whole &minus;37 to +3 dBm range without damage or compression.", "The 2534MA can only be used where the input is always below &minus;24 dBm.",
        "The drawing lists the P103LN gain as 13 dB. The datasheet gives 15.6 dB typical at 1 GHz, 13.5 dB minimum."]),
    p("Needs the Pluto as a 1.0&ndash;1.2 GHz source, the SSA3021X or SM200B, and fixed attenuators. Measure the Pluto output level first with nothing else connected.") +
    h("ZX60-P103LN+") +
    steps_table([
        ["1", "Supply current", "amp powered, input and output on 50 &Omega; loads", "set 5.0 V, limit 150 mA; read the current", "nothing", "95 mA", "under 120 mA"],
        ["2", "Gain vs frequency", "Pluto &rarr; 30 dB attenuator &rarr; amp &rarr; 20 dB attenuator &rarr; analyzer", "connect; then remove the amp for the reference run", "step 1.0&ndash;1.2 GHz with and without the amp; subtract", "15.6 dB at 1.0 GHz, about 14.5 dB at 1.2 GHz", "13.5 dB or more at 1.0 GHz"],
        ["3", "Compression", "Pluto &rarr; attenuator &rarr; amp &rarr; 20 dB attenuator &rarr; analyzer", "swap input attenuators so the input steps from &minus;20 to +9 dBm", "read output at each step", "+22.4 dBm out, at +7.8 dBm in", "+20 dBm or more"]]) +
    h("ZX60-2534MA-S+") +
    '<div class="note">Keep at least 40 dB of attenuation between the Pluto and this amp at all times. Its input limit is &minus;15 dBm and the Pluto can put out +11 dBm.</div>' +
    steps_table([
        ["1", "Supply current", "amp powered, input and output on 50 &Omega; loads", "set 5.0 V, limit 220 mA; read the current", "nothing", "170 mA", "under 190 mA"],
        ["2", "Gain vs frequency", "Pluto &rarr; 60 dB attenuation (input &minus;50 dBm) &rarr; amp &rarr; 30 dB attenuator &rarr; analyzer", "connect; then remove the amp for the reference run", "step 1.0&ndash;1.2 GHz with and without the amp; subtract", "43.5 to 43.7 dB", "38 dB or more"],
        ["3", "Compression", "same, less input attenuation", "swap attenuators so the input steps from &minus;50 to &minus;20 dBm. Do not go above &minus;20 dBm.", "read output at each step", "+19 dBm out, at about &minus;23 dBm in", "+17 dBm or more"]]),
    NOT_RUN)

# ------------------------------------------------------------------ existing tabs, regrouped into the same four sections
def split_items(html):
    i = html.index('<details class="item"')
    return html[:i], html[i:]


_, VCO_ITEMS = split_items(C.VCO)
VCO = part_tab(
    "VCO", "Crystek CVCO55BE-0800-1600 on CEVAL-055 board. Sends the reply at the frequency the phase detector measured.", "vco",
    table(["Quantity", "Value", "Source"],
          [["Frequency range", "800 to 1600 MHz", "DigiKey listing"], ["Tuning voltage", "0.5 to 19 V", "DigiKey listing"], ["Output power", "+6 &plusmn; 2 dBm (2.5 to 6.3 mW, 0.35 to 0.56 V rms)", "DigiKey listing"],
           ["Supply voltage used", "11.5 V", "design drawing"], ["Supply current", "30 mA max", "DigiKey listing"], ["Pushing", "2 MHz per volt of supply", "DigiKey listing"],
           ["Second harmonic", "&minus;10 dBc", "DigiKey listing"], ["RF input", "none", ""]], left=(0, 1, 2)) +
    p(link(C.DS["vco"], "DigiKey listing") + ". The Crystek datasheet itself has not been read."),
    ul(["Frequency rises with tuning voltage. The drawing expects 1.0&ndash;1.2 GHz for about 6 to 9.5 V.", "Output about +6 dBm, steady across the band.", "It should follow a change in tuning voltage in well under the 0.7 &micro;s reply time."]),
    ol(["Frequency vs tuning voltage, by hand, 0 to 10 V. Done 4 Oct.", "Output power vs frequency. Done 6 Oct.", "Frequency vs tuning voltage by computer, 0 to 3.5 V in 0.02 V steps. Done 10 Oct.",
        "Response to a voltage step. Done 10 Oct, limited by the 145 ns edge of the Syscomp.", "Drift over 74 minutes. Done 10 Oct.",
        "Not done: the computer-run sweep over 4.8 to 7.8 V. The Syscomp stops at 3.52 V. See " + link("#t-tx1", "Tests to run, TX1") + "."]),
    table(["Quantity", "Value", "Date"],
          [["Frequency range seen", "733 MHz at 0 V to 1360 MHz at 10.1 V", "4 Oct"], ["Tuning voltage for 1.0&ndash;1.2 GHz", "4.8 to 7.8 V (drawing expected 6 to 9.5 V)", "4 Oct"],
           ["Slope in 1.0&ndash;1.2 GHz", "68 MHz/V", "4 Oct"], ["Output power in 1.0&ndash;1.2 GHz", "+4.8 to +7.4 dBm", "6 Oct"], ["Repeatability at a fixed voltage", "0.10 MHz", "10 Oct"],
           ["Drift over 74 min", "59 kHz rms, no trend", "10 Oct"], ["Delay, tuning pin to frequency", "26 ns", "10 Oct"]], left=(0, 1, 2)) + VCO_ITEMS)

_, SPL_ITEMS = split_items(C.SPLITTER)
SPLITTER = part_tab(
    "Splitter", "Mini-Circuits ZFRSC-42-S+. Resistive 2-way. Used twice: after the IF amp, and as the delay-line split before the phase detector.", "spl",
    table(["Quantity", "Typical", "Max", "Unit"],
          [["Frequency range", "DC to 4200", D, "MHz"], ["Loss per output (6 dB split + insertion loss)", "6.0", "6.5 (100&ndash;2100 MHz)", "dB"], ["Loss per output at 1000 MHz (typical data)", "5.99 and 6.02", D, "dB"],
           ["Isolation between outputs", "6.5 (5.94 at 1000 MHz)", D, "dB"], ["Amplitude unbalance", "0.02", "0.2", "dB"], ["Phase unbalance", "0.63 at 1000 MHz", "3", "degrees"],
           ["VSWR at 1000 MHz", "1.02 to 1.03", D, ":1"], ["Input power, absolute max", D, "0.75 W (+28.8 dBm, 6.12 V rms)", ""], ["Internal dissipation, absolute max", D, "0.375 W", ""]], left=(0,)) +
    p(link(C.DS["splitter"], "Datasheet") + ". No supply needed. Ports: sum = 3, outputs = 1 and 2."),
    ul(["Each output is 6.0 dB below the input, the same at 1.0 and 1.2 GHz.", "The two outputs match within 0.2 dB.", "A signal put into one output appears at the other output 6 dB lower.",
        "After the IF amp with a strong radar: +18.6 dBm in gives +12.6 dBm at each output. This is far below the 0.75 W limit."]),
    p("Needs the Pluto, an analyzer and one 50 &Omega; load.") +
    steps_table([
        ["1", "Loss at one frequency", "source &rarr; splitter port 3; port 1 &rarr; analyzer; port 2 &rarr; 50 &Omega; load. Then swap ports 1 and 2.", "connect; swap", "read power with and without the splitter", "6.0 dB", "under 6.5 dB. Done 6 Oct at 1.04 GHz"],
        ["2", "Loss vs frequency", "same", "swap outputs", "step 1.0&ndash;1.2 GHz; read both outputs", "6.0 dB, flat", "under 6.5 dB; outputs within 0.2 dB"],
        ["3", "Isolation", "source &rarr; port 1; port 2 &rarr; analyzer; port 3 &rarr; 50 &Omega; load", "connect", "step 1.0&ndash;1.2 GHz", "6 dB", "recorded"]]),
    table(["Test", "Result", "Expected", "Date"], [["1. Loss, right output, 1.0388 GHz", "6.70 dB", "6.0 typical, 6.5 max", "6 Oct"], ["1. Loss, left output, 1.0388 GHz", "6.72 dB", "6.0 typical, 6.5 max", "6 Oct"],
                                                   ["2. Loss vs frequency", "not run", "", ""], ["3. Isolation", "not run", "", ""]], left=(0, 1, 2, 3)) +
    p("The measured loss is 0.2 dB over the datasheet maximum. The measurement includes the connectors and was made with the VCO as the source.") + SPL_ITEMS)

_, MIX_ITEMS = split_items(C.MIXER)
PHASEDET = part_tab(
    "Phase detector", "Mini-Circuits ZX05-30W-S+ mixer, fed by the delay-line splitter. Turns frequency into a DC voltage.", "pd",
    table(["Quantity", "Typical", "Min / Max", "Unit"],
          [["LO and RF frequency", "300 to 4000", D, "MHz"], ["IF frequency", "DC to 950", D, "MHz"], ["LO power", "+7 (5.0 mW, 0.50 V rms)", D, "dBm"],
           ["Conversion loss, 600&ndash;2000 MHz", "6.8", "max 9.0", "dB"], ["Conversion loss at 1106 MHz (typical data)", "6.36", D, "dB"],
           ["LO&ndash;RF isolation", "35", "min 17", "dB"], ["LO&ndash;IF isolation", "16", "min 7", "dB"], ["RF input at 1 dB compression", "+1", D, "dBm"],
           ["RF port VSWR at 944 / 1106 MHz", "3.48 / 2.77", D, ":1"], ["LO port VSWR at 914 / 1076 MHz", "1.97 / 1.70", D, ":1"],
           ["RF power, absolute max", D, "50 mW (+17 dBm, 1.58 V rms)", ""], ["IF current, absolute max", D, "40", "mA"]], left=(0,)) +
    p(link(C.DS["mixer"], "Datasheet") + ". Ports: LO = 1, RF = 2, IF = 3. No supply needed. The datasheet does not specify DC output when used as a phase detector."),
    ul(["Both inputs are the same frequency, so the IF output is a DC voltage.", "The voltage follows a cosine of the phase difference between the two inputs.",
        "With a 0.55 ns cable difference the phase is 196&deg; at 1.0 GHz and 236&deg; at 1.2 GHz. The voltage should change smoothly in one direction across the band.",
        "The voltage also scales with input power. It is only a frequency reading if the power is held fixed."]) +
    math(r"V_\text{out} \approx V_0 + A(P)\cos(2\pi f\tau) \qquad \tau = 0.55\ \text{ns}"),
    ol(["Output vs frequency with the Pluto at four power levels, by hand. Done in September.", "Output vs frequency with the VCO as source, by computer, 744 to 920 MHz. Done 10 Oct.",
        "Step response, noise and drift. Done 10 Oct.", "Not done: the same in 1.0&ndash;1.2 GHz, with fixed power, and with different delay cables. See " + link("#t-pd1", "Tests to run, PD1 to PD5") + "."]),
    table(["Quantity", "Value", "Date"],
          [["Output range, VCO source", "30.3 to 145.7 mV over 744&ndash;920 MHz", "10 Oct"], ["Range where one voltage = one frequency", "744 to 788 MHz", "10 Oct"],
           ["Slope in that range", "2.66 mV/MHz mean", "10 Oct"], ["Power at each input", "+0.6 dBm (wanted: +7 on LO)", "6 Oct"], ["Noise", "84 to 142 &micro;V rms = 38 to 66 kHz", "10 Oct"],
           ["10&ndash;90 % time after a step", "89 to 140 ns (input edge is 145 ns)", "10 Oct"], ["Delay, input to output", "26 ns", "10 Oct"]], left=(0, 1, 2)) +
    p("The measured curve does not match the expected smooth cosine. It has turning points 14 to 34 MHz apart. The cause is not known.") + MIX_ITEMS)

# ------------------------------------------------------------------ expected levels through the RX chain
RX_LEVELS = item("pi-levels", "Expected power through the RX chain",
                 table(["After", "Gain or loss (dB)", "Weak radar (dBm)", "Strong radar (dBm)", "Limit at this point"],
                       [["Antenna", D, "&minus;50", "&minus;10", ""], ["LNA ZX60-5123LN+", "+22", "&minus;28", "+12", "LNA input max +15 dBm; output compresses at +17 dBm"],
                        ["RX mixer ZX05-14LH-S+", "&minus;7.7", "&minus;35.7", "+4.3 or less", "mixer input max +17 dBm; compresses above +5 dBm in. +12 dBm in is compressed"],
                        ["IF amp ZX60-P103LN+", "+15.6", "&minus;20.1", "+19.9 or less", "amp input max +21 dBm; output compresses at +22.4 dBm"],
                        ["IF splitter ZFRSC-42-S+", "&minus;6.0", "&minus;26.1", "+13.9 or less", "splitter input max +28.8 dBm"]], left=(0, 4)) +
                 p("Antenna levels are from the design drawing. Limiter loss is not included because no limiter is chosen. Gains are datasheet typical values at 9.4 GHz and 1 GHz.") +
                 p("With the ZX60-2534MA-S+ in place of the P103LN the strong-radar input of +4 dBm is 19 dB over its &minus;15 dBm damage limit."))
