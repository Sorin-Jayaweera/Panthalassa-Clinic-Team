"""More per-part tabs: LO buffer amp and image reject filter."""
from content import table, ul, ol, p, h, link, math, fig, D
from content_parts import part_tab, steps_table, NOT_RUN, PDF

LOBUF = part_tab(
    "LO buffer", "Mini-Circuits ZX60-14012L-S+. Amplifies the 8.3 GHz LO from the PLL before the LO splitter.", "lob",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Frequency range", "0.0003", D, "14", "GHz"], ["Gain", "9", "12", D, "dB"], ["Gain at 8 GHz (typical data)", D, "12.55", D, "dB"],
           ["Gain flatness", D, "&plusmn;1.0", "&plusmn;2.0", "dB"], ["Output power at 1 dB compression", "9", "11", D, "dBm"],
           ["Output at 1 dB compression, 8 GHz (typical data)", D, "12.25", D, "dBm"], ["Output at 1 dB compression, 9 GHz (typical data)", D, "11.18", D, "dBm"],
           ["Noise figure", D, "5.5", "7.5", "dB"], ["Output IP3", D, "20 (17.8 at 8 GHz)", D, "dBm"],
           ["Input VSWR / output VSWR at 8 GHz", D, "1.34 / 1.65", D, ":1"],
           ["Supply voltage", "10.5", "12", "20", "V"], ["Supply current", D, "62", "68", "mA"],
           ["RF input, absolute max", D, D, "+10 (10 mW, 0.71 V rms)", "dBm"], ["Supply voltage, absolute max", D, D, "20", "V"]]) +
    p(link(PDF + "ZX60-14012L-S+.pdf", "Datasheet") + ". Internally regulated. Reverse-voltage protected."),
    ul(["Draws about 62 mA at 12 V.", "Adds about 12.5 dB at 8.3 GHz.", "The most it can put out at 8.3 GHz is about +12 dBm (1 dB compressed).",
        "The LO splitter after it loses 4.1 dB per output at 8.3 GHz (3.0 dB split + 1.1 dB typical, 1.4 dB max).",
        "So each mixer gets at most about +8 dBm. The mixers are specified for +10 dBm."]) +
    math(r"P_\text{mixer} = P_\text{amp out} - 3.0 - 1.1 = 12.2 - 4.1 = +8.1\ \text{dBm}") +
    '<div class="note">One ZX60-14012L-S+ cannot give +10 dBm to both mixers. It is about 2 dB short even when driven into compression. The drawing shows +10 dBm at each mixer. RX mixer test 3 (conversion loss vs LO power) will show how much the shortfall costs.</div>',
    p("Needs the PLL at 8.3 GHz, the SM200B, fixed attenuators, and a supply at 12.0 V with a 100 mA limit. Measure the PLL output level alone first.") +
    steps_table([
        ["1", "Supply current", "amp powered, input and output on 50 &Omega; loads", "set 12.0 V; read the current", "nothing", "62 mA", "under 68 mA"],
        ["2", "PLL level", "PLL &rarr; SM200B", "set the PLL to 8.3 GHz", "read frequency and power", "not known", "recorded; must be under +10 dBm before it goes to the amp"],
        ["3", "Gain", "PLL &rarr; attenuators (so input is &minus;15 dBm) &rarr; amp &rarr; 20 dB attenuator &rarr; SM200B", "connect; then remove the amp for the reference run", "read 8.3 GHz with and without the amp; subtract", "12.5 dB", "9 dB or more"],
        ["4", "Compression", "same", "swap input attenuators: &minus;15 to +5 dBm", "read output at each step", "+12 dBm out, at about 0 dBm in", "+9 dBm or more"],
        ["5", "Power at the mixers", "PLL &rarr; amp &rarr; LO splitter; one output &rarr; 20 dB attenuator &rarr; SM200B, other &rarr; 50 &Omega; load. Then swap.", "connect; swap outputs", "read 8.3 GHz at each output", "about +8 dBm at most", "recorded; the mixers want +10 dBm"],
        ["6", "Harmonics", "same as 5", "nothing", "read 16.6 GHz", "not specified", "recorded"]]) +
    '<div class="note">Input limit is +10 dBm. Check the PLL level (test 2) before connecting it to the amp without attenuators.</div>',
    table(["Test", "Result", "Expected", "Pass?", "Date"],
          [["1. Supply current", "0.06 A at 12.0 V", "62 mA, max 68 mA", "pass", "12 Oct"], ["2. PLL level at 8.3 GHz, through the buffer", "ADF5355 Out B &rarr; 10 dB &rarr; buffer &rarr; 20 dB &rarr; SM200B: &minus;33.57 dBm at 8.29995 GHz. With 12.5 dB buffer gain and pads at nominal, Out B &asymp; &minus;16 dBm." + fig("spike_LO_8p3GHz_no_splitter.png", "Spike: LO through buffer, -33.57 dBm"), "&minus;25.5 dBm (from Out B &minus;8 dBm at 8.000 GHz)", "8 dB low; cause not known", "31 Oct"],
           ["5. Splitter added, first look", "same chain with splitter at the end, S from buffer, output 2 on 50 &Omega;, output 1 to SM200B: &minus;59.92 dBm. 26.35 dB lower than without the splitter." + fig("spike_LO_8p3GHz_with_splitter.png", "Spike: LO through splitter, -59.92 dBm"), "4.1 dB drop", "<b>22 dB too much loss: being checked</b>", "31 Oct"],
           ["3. Gain, at 1.1 GHz", "11.5 dB (four levels: 11.8, 11.0, 11.7, 11.7)", "11 dB at 1 GHz; min 9 dB", "pass", "12 Oct"],
           ["3. Gain, 1.0 to 1.2 GHz", "10.0 to 11.4 dB (mean 10.7)", "about 11 dB; min 9 dB", "pass", "12 Oct"],
           ["3. Gain, at 8.3 GHz", "not run", "12.5 dB", "", ""], ["4. Compression, 1.0 to 1.2 GHz", "gain 1 dB down at +8.2 dBm (1000 MHz), +8.4 dBm (1100 MHz), about +9 dBm (1200 MHz)", "+11 dBm typ, +9 min (+11.5 at 1 GHz)", "0.6 to 0.8 dB under the minimum at 1000 and 1100 MHz", "12 Oct"],
           ["4. Compression, at 8.3 GHz", "not run", "+12 dBm out", "", ""],
           ["Repeatability, 1.1 GHz", "0.28 dB spread over 5 readings", "", "", "12 Oct"],
           ["Output with no input", "no lines; nothing more than 6 dB above the noise from 30 MHz to 2.1 GHz", "noise only", "pass", "12 Oct"],
           ["Second harmonic, 1.0 GHz drive at +9.1 dBm out", "&minus;13.1 dBm at 2.0 GHz (&minus;22 dBc), Pluto harmonic included", "not specified", "recorded", "12 Oct"],
           ["5. Power at the mixers", "not run", "about +8 dBm", "", ""], ["6. Harmonics", "not run", "", "", ""]], left=(0, 1, 2, 3, 4)) +
    p("Test 1: read from the display of an Agilent E3630A supply. Input and output each had a 50 &Omega; termination. The display reads to 0.01 A, so the current is between 55 and 65 mA. With a signal applied in test 3 it also read 0.06 A.") +
    fig("lobuf_gain.png", "LO buffer amp gain against frequency, and output against input at 1100 MHz") +
    h("Test 3 at 1.1 GHz, 12 Oct") +
    table(["Pluto attenuation (dB)", "Without amp (dBm)", "With amp (dBm)", "Gain (dB)"],
          [["60", "&minus;59.93", "&minus;48.17", "11.76"], ["50", "&minus;49.13", "&minus;38.16", "10.97"], ["40", "&minus;39.39", "&minus;27.74", "11.65"], ["31", "&minus;30.41", "&minus;18.74", "11.67"]]) +
    ol(["Source: the Pluto, set to a tone at 1099.99 MHz. Its attenuation was never set below 31 dB.",
        "Run A: Pluto TX connected straight to the spectrum analyzer (Siglent SSA3021X). The peak level was read at four Pluto attenuation settings.",
        "Run B: Pluto TX to the amp input, amp output to the spectrum analyzer, amp at 12 V. The same four settings were read.",
        "Gain is run B minus run A at the same setting.", "The gain is the same at all four levels, so the amp was not compressing. The 60 dB row is only a few dB above the analyzer noise."]) +
    math(r"G = P_\text{with amp} - P_\text{without amp} = -18.74 - (-30.41) = 11.67\ \text{dB}") +
    h("Test 3 from 1.0 to 1.2 GHz, 12 Oct") +
    table(["Frequency (MHz)", "Without amp (dBm)", "With amp (dBm)", "Gain (dB)"],
          [["1000", "&minus;39.00", "&minus;28.37", "10.63"], ["1050", "&minus;38.74", "&minus;28.72", "10.02"], ["1100", "&minus;39.14", "&minus;27.74", "11.40"],
           ["1150", "&minus;39.62", "&minus;28.32", "11.30"], ["1200", "&minus;39.03", "&minus;28.88", "10.15"]]) +
    ul(["Pluto attenuation 40 dB for every row.", "The with-amp readings were taken first. The amp was then removed and the without-amp readings taken.",
        "Gain varies by 1.4 dB across the band. The cables were unplugged and reconnected between the two runs, and the 1100 MHz without-amp reading changed by 0.25 dB between the first and second run, so part of the variation is the measurement.",
        "The datasheet gives 11.03 dB at 1000 MHz and a flatness of &plusmn;1 dB."]) +
    h("Test 4, compression, 12 Oct") +
    fig("lobuf_compression.png", "LO buffer amp output against input, and gain against output power, at 1000, 1100 and 1200 MHz") +
    table(["Frequency (MHz)", "Gain at low power (dB)", "Output where gain is 1 dB lower (dBm)", "Highest output reached (dBm)"],
          [["1000", "10.37", "+6.4", "+9.10"], ["1100", "11.09", "+6.3", "+9.39"], ["1200", "9.80", "+7.1", "+8.90"]]) +
    ol(["Wiring: Pluto TX to amp input, amp output to the spectrum analyzer. Amp at 12 V.",
        "The Pluto attenuation was stepped from 40 dB down to 0 dB, 16 steps, at each of three frequencies. The output power was read at each step.",
        "The input power was not measured at each step. It was calculated: the Pluto level measured at 40 dB without the amp, plus the change in the attenuation setting.",
        "Gain is output minus calculated input. The low-power gain is the average of the steps below &minus;18 dBm input.",
        "The compression point is the output power where the gain is 1 dB below the low-power gain."]) +
    ul(["The output powers are measured directly: the amp put out up to +9.4 dBm.",
        "The input power in this first calculation was not measured. The numbers in the table above are wrong for that reason. See the corrected result below."]) +
    h("Test 4 corrected with the measured Pluto level, 12 Oct") +
    fig("lobuf_compression2.png", "LO buffer amp output against measured input, and gain against output power") +
    table(["Frequency (MHz)", "Gain at low power (dB)", "Output where gain is 1 dB lower (dBm)", "Gain drop at the highest output (dB)", "Highest output (dBm)", "Input at the highest output (dBm)"],
          [["1000", "10.62", "+8.16", "1.66", "+9.10", "+0.14"], ["1100", "11.33", "+8.37", "1.57", "+9.39", "&minus;0.36"], ["1200", "10.09", "not reached; about +9", "0.96", "+8.90", "&minus;0.23"]]) +
    ol(["Later on 12 Oct the Pluto was connected straight to the spectrum analyzer and its output read at every attenuation setting from 0 to 40 dB, at the same three frequencies and the same tone scale. See the " + link("#plu-results", "Pluto tab") + ".",
        "The input power at each step is now that measured Pluto level, not the setting.",
        "Gain is the amp output minus the measured Pluto level at the same setting. The low-power gain is the average of the steps below &minus;18 dBm input.",
        "The compression point is the output power where the gain is 1 dB below the low-power gain, found by a straight line between the two nearest steps."]) +
    math(r"G(A) = P_\text{with amp}(A) - P_\text{Pluto alone}(A) \qquad P_{1\,\text{dB}} = P_\text{out}\ \text{where}\ G = G_\text{low} - 1") +
    ul(["The Pluto puts out 0.6 to 1.0 dB less than its setting says at 0 dB attenuation. That accounts for about half of the early gain drop seen in the first calculation.",
        "With the correction the gain is flat within 0.2 dB up to +3 dBm output at 1000 and 1100 MHz, then falls.",
        "1 dB compression is at +8.2 dBm (1000 MHz) and +8.4 dBm (1100 MHz). The datasheet gives +11 dBm typical and +9 dBm minimum, and +11.5 dBm in its typical data at 1000 MHz.",
        "At 1200 MHz the low-power gain itself rises by 0.4 dB between &minus;29 and &minus;5 dBm output, so the reference gain is less certain there.",
        "The amp and the Pluto-alone readings were taken with different cable connections. Repeat readings changed by up to 0.3 dB after reconnecting, so the compression points are good to about &plusmn;0.5 dB.",
        "This is at 1.0 to 1.2 GHz. The design uses the amp at 8.3 GHz, where the typical data gives +12.25 dBm. That is still to be measured."]) +
    p("Files in <code>clinic\\claude\\lo_buffer_test\\</code>: <code>runA_direct_20261012.csv</code>, <code>runA_direct_freq_20261012.csv</code>, <code>runB_amp_20261012.csv</code>, <code>compression_20261012.csv</code>, <code>compression_corrected_20261012.csv</code>, <code>amp_output_no_signal_20261012.csv</code>."))

FILTER = part_tab(
    "Image filter", "Mini-Circuits VHF-8400+ high-pass filter. Goes after the TX mixer. Passes 9.3&ndash;9.5 GHz and reduces the 7.1&ndash;7.3 GHz image.", "flt",
    table(["Quantity", "Min", "Typical", "Max", "Unit"],
          [["Passband", "9000", D, "13000", "MHz"], ["Loss, 9000&ndash;9500 MHz", D, D, "3", "dB"], ["Loss, 9500&ndash;12500 MHz", D, D, "2.5", "dB"],
           ["Frequency where loss is 3 dB", D, "8400", D, "MHz"], ["Rejection, DC&ndash;5700 MHz", D, "30", D, "dB"], ["Rejection, DC&ndash;6000 MHz", "20", D, D, "dB"],
           ["Rejection, 6000&ndash;8400 MHz", "not specified", "not specified", "not specified", "dB"], ["Return loss, 9000&ndash;13000 MHz", D, "14", D, "dB"],
           ["RF input power, max at 25 &deg;C", D, D, "7 W (+38.5 dBm, 18.7 V rms)", ""], ["Sections", D, "5", D, ""]]) +
    p(link(PDF + "VHF-8400+.pdf", "Datasheet") + ". No supply needed. DC blocked at both ports."),
    ul(["Wanted signal, 9.3&ndash;9.5 GHz: loses up to 3 dB. The drawing estimates 1.4 to 1.6 dB.",
        "Image, 7.1&ndash;7.3 GHz: the datasheet gives no number between 6.0 and 8.4 GHz. The drawing estimates 24 to 28 dB by reading the curve.",
        "LO leakage, 8.3 GHz: this is 100 MHz below the 3 dB point, so it is reduced by only about 3 to 5 dB.",
        "The TX mixer leaks LO to its RF port 35 dB down (25 dB minimum): +8 &minus; 35 = &minus;27 dBm. After the filter about &minus;31 dBm of 8.3 GHz reaches the power amp."]) +
    math(r"f_\text{image} = f_\text{LO} - f_\text{IF} = 8.3 - (1.0\ \text{to}\ 1.2) = 7.1\ \text{to}\ 7.3\ \text{GHz}") +
    '<div class="note">This filter does little to the 8.3 GHz LO. Whether that matters depends on the power amp and on emission limits. Test 3 measures it.</div>',
    p("Needs a source that can be set from 5.5 to 10 GHz (the ADF5355 PLL can, if we can retune it) and the SM200B. Each test is one run with the filter and one without; the difference is the loss.") +
    steps_table([
        ["1", "Passband loss", "source &rarr; filter &rarr; SM200B", "connect; then replace the filter with a through adaptor", "step 9.0&ndash;10.0 GHz with and without the filter; subtract", "1.4 to 1.6 dB at 9.3&ndash;9.5 GHz", "under 3 dB"],
        ["2", "Image rejection", "same", "nothing", "step 7.0&ndash;7.4 GHz", "24 to 28 dB (drawing estimate)", "recorded; 20 dB or more wanted"],
        ["3", "LO rejection", "same", "nothing", "read 8.3 GHz", "3 to 5 dB", "recorded"],
        ["4", "Stopband", "same", "nothing", "step 5.5&ndash;6.0 GHz", "30 dB", "20 dB or more"],
        ["5", "Full curve", "same", "nothing", "step 5.5&ndash;10 GHz in 50 MHz steps", "3 dB point at 8.4 GHz", "recorded as a plot"],
        ["6", "After the TX mixer", "Pluto 1.0&ndash;1.2 GHz &rarr; TX mixer IF; LO &rarr; mixer LO; mixer RF &rarr; filter &rarr; SM200B", "connect; then remove the filter", "read 9.3&ndash;9.5, 8.3 and 7.1&ndash;7.3 GHz with and without the filter", "wanted signal down under 3 dB; image down 24 to 28 dB", "recorded"]]),
    NOT_RUN)
