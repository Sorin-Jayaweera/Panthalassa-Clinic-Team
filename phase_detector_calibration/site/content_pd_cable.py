"""Phase detector tab: delay cable E and pads at the mixer, 13-14 Nov 2026."""
from content import item, table, ul, p, h, fig

PD_CABLE = item(
    "pd-cable-e", "Delay cable E (about 8 cm) with pads at the mixer ports, 13&ndash;14 Nov: voltage vs frequency, power levels, noise, drift",
    p("Goal: one clean voltage per frequency over 200 MHz, read to &plusmn;2 MHz. The PLL can move the band anywhere, so the absolute frequency does not matter. "
      "Wiring (every plot shows it): Pluto TX &rarr; 4 &times; ZX60-P162LN+ (4.03 V, 0.23 A) &rarr; ZFRSC-42-S+ &rarr; right arm cable D to the LO port, left arm cable B + E to the RF port "
      "&rarr; ZX05-30W-S+ &rarr; IF to SDS1104X-E CH1 (1 M&Omega;) and, through pads, the SM200B. D and B are the same length, so the length difference is cable E. On 1 Nov it was cable C (about 12 cm)."),
    h("Cable C against cable E, and pads at the mixer (13 Nov)"),
    p("With C and with E the output ripples about every 375 MHz, which a few-cm length difference cannot cause (it would give a period of a few GHz). "
      "The guess was reflections between the badly matched mixer ports and the splitter; the 31 Oct VNA data shows the RF port at &minus;6 dB return loss at 1.5 GHz and the LO port at &minus;13.7 dB. "
      "A 3 dB pad was put at the LO port and a 6 dB pad at the RF port (a pad improves the match by twice its value, so both ports end near &minus;18 to &minus;20 dB). "
      "The swing shrank about 3&times; and one clean rise appeared from 1228 to 1440 MHz (212 MHz)."),
    fig("pd_cable_compare.png", "Detector output vs frequency: 1 Nov cable C, 13 Nov cable E, and cable E with 3 dB at LO and 6 dB at RF, raw and with the tone-off reading subtracted, with the wiring"),
    h("Power levels in the band (1 Nov, 13 Nov evening and 14 Nov)"),
    p("1 Nov (cable C, no pads): 1 MHz sweeps at &minus;70, &minus;65, &minus;60, &minus;50, &minus;40 and &minus;36 dBm; from 960 to 1010 MHz the levels from &minus;65 to &minus;36 dBm differ by 10.8 mV on average, about 4 MHz. 13 Nov evening: 2 MHz steps at &minus;50 dBm with &minus;60 and &minus;55 dBm passes (the &minus;45 and &minus;40 dBm passes were lost when the Pluto dropped off USB). "
      "14 Nov: a power ramp from &minus;80 to &minus;36 dBm in 2 dB steps at ten frequencies from 1225 to 1450 MHz. "
      "From about &minus;58 dBm up the output does not change with level at any frequency: the detector is saturated, so at &minus;50 dBm the reading depends on frequency only. Below &minus;60 dBm it falls with level."),
    fig("p162x4_fine_1nov.png", "1 Nov, cable C, no pads: 1 MHz sweeps at six Pluto levels from -70 to -36 dBm, 900 to 1200 MHz and 950 to 1020 MHz, with the wiring (also under the Radar tab, test 52)"),
    fig("pd_dense_E_pads.png", "Cable E with pads: 2 MHz sweep at -50 dBm with the -60 and -55 dBm passes, slope, and MHz of error per 1 mV of reading error, with the wiring"),
    fig("pd_overnight_band.png", "14 Nov: band 1150-1550 MHz at 1 MHz steps against 13 Nov, slope, power ramp -80 to -36 dBm at ten frequencies, and a 20 min hold at 1340 MHz then 5 min tone off, with the wiring"),
    h("Whole range, 300&ndash;4000 MHz, with the IF port on the SM200B (14 Nov)"),
    p("10 MHz steps from 300 to 4000 MHz and 5 MHz steps from 600 to 2100 MHz. The 5 MHz sweep lies on the 13 Nov sweep within a few mV. "
      "Above 2090 MHz the output is zero because the Pluto level table stops there and the attenuation is set for the worst-case output, so the real level is far below &minus;50 dBm (the IF tone drops by about 20 dB at the same point). "
      "The IF port carries the tone at about &minus;12 dBm and 2f at about &minus;10 dBm in the band (referred to before the 20 dB of pads)."),
    fig("pd_overnight_wide.png", "14 Nov: detector output 300-4000 MHz at 10 MHz steps and 600-2100 MHz at 5 MHz steps, and the tone, 2f and 3f at the IF port on the SM200B, with the wiring"),
    h("Findings"),
    ul(["The staircase in the slope (about 9.3 MHz period) is the scope, not the detector: every flat step sits on an exact multiple of 8.0 mV, one ADC step at 0.2 V/div, and the noise (0.3 mV) is too small to smooth across steps. "
        "At 50 mV/div (2 mV steps) the steps were still there, 2.0 mV apart. From 13:01 every point is read at four scope offsets 1 mV apart and averaged (dither); the staircase is gone (see the next section). A reading front end needs an ADC step well under 8 mV.",
        "Hold at 1340 MHz for 20 min: sd 0.33 mV, no visible drift. Tone off: sd 0.26 mV.",
        "Between 13 Nov evening and 14 Nov midday the band sits 2 to 7 mV higher. That is session-to-session drift, not noise.",
        "Slope in 1240&ndash;1430 MHz from the dithered sweep: 0.17 to 1.19 mV/MHz, median 0.82 mV/MHz (the 0.54 mV/MHz read at 0.2 V/div was pulled down by the staircase)."]),
    table(["File", "What"], [
        ["<code>phase_detector_calibration/pd_cable_13nov_E_pads.csv</code>", "13 Nov evening: 2 MHz sweep and power passes"],
        ["<code>phase_detector_calibration/pd_kitty_13nov_E_pads.csv</code>", "13 Nov: 25 MHz steps with the SM200B on the IF port"],
        ["<code>phase_detector_calibration/pd_overnight_13nov.csv</code>", "14 Nov 10:51&ndash;12:51: whole range, power ramp, band, hold, tone off (0.2 V/div)"],
        ["<code>phase_detector_calibration/pd_fine_14nov.csv</code>", "14 Nov 12:52&ndash;13:00: 50 mV/div without dither (staircase still there, 2 mV steps)"],
        ["<code>phase_detector_calibration/pd_dither_14nov.csv</code>", "14 Nov 13:01&ndash;14:53: dithered 1 MHz band sweep and the band at seven levels"],
        ["<code>phase_detector_calibration/plot_pd_cable.py</code>, <code>plot_pd_dense.py</code>, <code>plot_pd_overnight.py</code>, <code>plot_pd_levels.py</code>", "The plots"]], left=(0, 1)),
)

PD_OLD = item(
    "pd-old-raw", "Three-cable setup before cable E (D | B + C, no pads), 1 Nov: every raw reading at every Pluto level",
    p("All readings from the first delay-line setup, as saved, nothing averaged or subtracted: the 700&ndash;1600 MHz map at 13 levels from &minus;85 to &minus;30 dBm (5 MHz steps), "
      "the 900&ndash;1200 MHz sweeps at six levels from &minus;70 to &minus;36 dBm (1 MHz steps), every &minus;60 dBm repeat sweep, the run read with the SM200B at four levels, the power ramp at 1054 MHz, "
      "and every held-tone and tone-off reading through the evening, including the run with the amplifiers unpowered. "
      "Data: <code>phase_detector_calibration/p162x4_map_1nov.csv</code>, <code>p162x4_fine_1nov.csv</code>, <code>p162x4_sm200b_1nov.csv</code>, <code>p162x4_ramp_1nov.csv</code>, "
      "<code>p162x4_tone_off_watch_1nov.csv</code>. Plot: <code>plot_pd_old_all.py</code>."),
    fig("pd_old_setup_all_raw.png", "1 Nov, cable D on the right and B + C on the left, no pads: every raw scope reading at every Pluto level, repeats, SM200B run, power ramp, holds and tone-off readings, with the wiring"),
)


PD_LEVELS = item(
    "pd-power-levels", "Frequency error from input power, cable E with pads, dithered reading (14 Nov): within &plusmn;2 MHz over 1248&ndash;1424 MHz for &minus;56 to &minus;40 dBm",
    p("Same wiring as above. Every point read at 50 mV/div at four scope offsets 1 mV apart, averaged, so the scope's 2 mV ADC steps average out. "
      "First a 1 MHz sweep of 1150&ndash;1550 MHz at &minus;50 dBm, then the band 1220&ndash;1452 MHz every 4 MHz at &minus;60, &minus;56, &minus;52, &minus;48, &minus;44, &minus;40 and &minus;36 dBm (the Pluto's top level; stopped after 14 of 59 points, up to 1272 MHz). "
      "Frequency error = (reading at that level &minus; median of the &minus;60 to &minus;40 dBm readings at that frequency) &divide; local slope."),
    fig("pd_levels_14nov.png", "14 Nov: dithered 1 MHz sweep against the 8 mV-step sweep, its slope, the band at seven Pluto levels, and the frequency error each level causes, with the wiring"),
    table(["Pluto levels", "Best (peak-to-peak)", "Worst (peak-to-peak)", "Median", "Range within &plusmn;2 MHz"], [
        ["&minus;60 to &minus;40 dBm", "1.3 MHz at 1256 MHz", "12.2 MHz at 1240 MHz", "3.6 MHz", "1252&ndash;1336 and 1388&ndash;1416 MHz"],
        ["&minus;56 to &minus;40 dBm", "0.5 MHz at 1332 MHz", "9.6 MHz at 1240 MHz", "2.2 MHz", "1248&ndash;1424 MHz (176 MHz)"],
        ["&minus;52 to &minus;40 dBm", "0.1 MHz at 1336 MHz", "6.6 MHz at 1240 MHz", "1.6 MHz", "1248&ndash;1424 MHz (176 MHz)"]], left=(0, 4)),
    ul(["The dithered sweep is smooth: the staircase seen at 0.2 V/div was the scope's ADC, not the detector.",
        "&minus;60 dBm is the outlier: it reads 2 to 7 MHz low across the band, because the four amplifiers are not yet fully saturated there. From &minus;56 dBm up the curves lie on top of each other.",
        "So the input must stay at or above about &minus;56 dBm at the Pluto position for &plusmn;2 MHz; then 176 MHz of the band (1248&ndash;1424 MHz) holds &plusmn;2 MHz against power, a little short of the 200 MHz goal. The worst points are at the ends of the rise, where the slope is small.",
        "Above &minus;36 dBm was not measured (the Pluto's limit). Sorin, 14 Nov: the &minus;20 dBm asked about was arbitrary; the aim is a stable curve over the input range expected.",
        "Not yet in this error budget: drift between sessions (2 to 7 mV, about 2 to 8 MHz, from 13 Nov evening to 14 Nov midday)."]),
    h("After a 25 min break: the whole curve moved up about 6 mV (14 Nov 15:29)"),
    p("The run was stopped at 14:53 and the Pluto replugged; the wiring was not changed (Sorin checked it). On restart the four amplifiers drew 0.26 A instead of 0.23 A at the same 4.03 V. "
      "A recheck at 1260, 1300, 1340, 1380 and 1420 MHz at all seven levels read 5.4 to 7.6 mV higher than before at every level from &minus;56 to &minus;36 dBm (&minus;60 dBm: &minus;0.6 to +6.0 mV). "
      "The tone-off reading moved only 0.3 mV, so the change is in the detector's response, not the scope. As frequency that is 5 to 13 MHz, far outside &plusmn;2 MHz; but the shift is nearly the same at every level, "
      "so the power dependence did not change: the whole curve moved. A shift like this can be removed by calibrating against one known tone. "
      "With the tone off the IF port showed a comb of lines on multiples of 40 MHz from 1200 to 1680 MHz, up to about &minus;35 dBm at the IF port (spectrum in <code>if_toneoff_spectrum_14nov_1530.csv</code>; source not known, 40 MHz is the Pluto's reference clock). "
      "Finer power-level passes (4, 2, then 1 MHz) are running to follow it."),
    fig("pd_recheck_14nov.png", "14 Nov: power-level curves before the 14:53 stop and after the 15:18 restart, the shift at each level in mV and as frequency, with the wiring"),
)

PD_FRONTEND = item(
    "pd-frontend", "Reading the detector in the 700 ns budget: op-amp scaling stage 0.5&ndash;2.0 V, op-amp choice, timing (14 Nov)",
    p("The racon has 700 ns from receiving a radar pulse to sending the reply, so the detector voltage is read once (or averaged over a few samples) and used at once. "
      "Dithering as done on the scope is a bench fix only. In the real front end a gain stage makes the ADC step small against the slope, and the stage's own noise smooths the steps."),
    h("Scaling stage"),
    p("Detector 0 to 160 mV (the 1228&ndash;1440 MHz rise) to 0.5 to 2.0 V: V<sub>out</sub> = 0.5 V + 9.375 V<sub>in</sub>. Two halves of a dual op-amp, 3.3 V single supply: "
      "A is a unity-gain buffer on the detector (so the offset resistors do not pull about 30 &micro;A into the mixer IF port); B is non-inverting, with the buffer output through R1 and 3.3 V through R2 summed at the + input, Rg from &minus; to ground, Rf from output to &minus;."),
    table(["Part", "Slow op-amp (MCP6002)", "Fast op-amp (OPA2356 etc.)", "Job"], [
        ["R1", "1.62 k&Omega;", "162 &Omega;", "buffer output to + input"], ["R2", "100 k&Omega;", "10 k&Omega;", "3.3 V to + input (sets 0.5 V)"],
        ["Rg", "1.2 k&Omega;", "120 &Omega;", "&minus; input to ground"], ["Rf", "10.2 k&Omega;", "1.02 k&Omega;", "output to &minus; input"]], left=(0, 3)),
    ul(["Gain 1 + Rf/Rg = 9.5; 0 mV gives 0.500 V, 160 mV gives 1.996 V; 8.0 mV per MHz at the ADC.",
        "On 5 V: R1 = 1.07 k&Omega; (107 &Omega;), the rest unchanged.",
        "The offset comes from the supply: 10 mV of supply noise moves the output about 1.6 mV (0.2 MHz). A reference (e.g. LM4040) is better.",
        "Out of band the detector reaches about 180 mV, i.e. 2.2 V out: clamp or check the ADC input limit.",
        "1% resistors give up to about 2% gain error (about &plusmn;2 MHz across the band); the look-up table must be measured through this exact stage, which calibrates it out."]),
    h("Op-amp choice (DigiKey, read 14 Nov; settle = slew time for 1.5 V + 6.9 time constants at gain 9.5, to 0.1% = 1.5 mV, about 0.2 MHz)"),
    table(["Part", "Package", "GBW (MHz)", "Slew (V/&micro;s)", "Settle to 0.1%", "Price (qty 1)", "Stock", "Use"], [
        ["OPA2356AIDR", "SOIC-8", "200", "360", "about 56 ns", "$3.52", "2,159", "PCB, and breadboard on a SparkFun 13655 SOIC-to-DIP adapter ($3.75 for 4)"],
        ["OPA2356AIDGKR", "MSOP-8", "200", "360", "about 56 ns", "$3.52", "2,400", "PCB with MSOP pads"],
        ["OPA2836IDR", "SOIC-8", "118", "560", "about 90 ns", "$5.56", "1,896", "low power"],
        ["ADA4891-2ARMZ-RL", "MSOP-8", "105", "210", "about 100 ns", "$2.66", "2,355", "cheapest fast one"],
        ["AD8056ANZ / AD8055ANZ", "PDIP-8", "about 300 (est.)", "1400", "about 36 ns", "$8.76 / $4.93", "157 / 387", "breadboard, needs &plusmn;5 V"],
        ["AD8032ANZ", "PDIP-8", "80", "35", "about 173 ns", "$8.12", "187", "breadboard, one 3.3 or 5 V supply"],
        ["LT1632CN8", "PDIP-8", "45", "45", "about 265 ns", "$12.52", "0", "slow, none in stock"],
        ["MCP6002-I/P", "PDIP-8", "1", "0.6", "about 13 &micro;s", "", "", "too slow for the racon"]], left=(0, 1, 7)),
    p("Spreadsheets with links: <code>phase_detector_calibration/opamp_options_14nov.xlsx</code> (PCB) and <code>opamp_breadboard_options_14nov.xlsx</code> (breadboard). First-order estimates; a breadboard adds 2&ndash;5 pF per contact and can ring, so measure a step on the scope."),
    h("Timing budget (estimate)"),
    table(["Step", "Time"], [["Detector plus 10&ndash;20 MHz RC filter (detector rise 89&ndash;140 ns, 10&ndash;90%, measured 10 Oct)", "about 150 ns"],
                             ["Op-amp settling (OPA2356)", "about 50 ns"], ["4 to 8 ADC samples at 65 MSPS", "60&ndash;120 ns"], ["ADC pipeline delay (6&ndash;7 clocks)", "about 100 ns"],
                             ["FPGA average and look-up", "about 20 ns"], ["Total", "about 380&ndash;440 ns of the 700 ns"]], left=(0,)),
    ul(["Noise: the scope saw about 0.8 mV rms per sample with the tone on (20 MHz bandwidth), about 0.9 MHz rms per sample. Averaging 4 samples gives about 0.47 MHz rms, 8 samples about 0.33 MHz rms.",
        "After the &times;9.5 stage that noise is about 8 mV rms at the ADC, about one step of an 8-bit 2 V ADC (7.8 mV), enough to smooth the steps when averaging.",
        "Drift between sessions (2&ndash;7 mV) is bigger than the &plusmn;2 MHz budget, so the system needs a calibration (for example a known tone between pulses) or a stable temperature."]),
)

PD_KEY = item(
    "pd-key", "Main result: detector voltage vs frequency, cable E with pads (14 Nov)",
    p("Raw detector output, nothing subtracted. Each plot is one run. Top: the cleanest data, the 14 Nov evening run (dithered reading, 50 mV/div), five Pluto levels from the Pluto&rsquo;s top (&minus;36 dBm) down to &minus;64 dBm, then the same data zoomed on the one-to-one region. "
      "Bottom: the widest sweep, 300&ndash;4000 MHz at &minus;50 dBm, not dithered (0.2 V/div). Each run sits a few mV higher or lower than the others (see the session-to-session section below), so different runs are not overlaid here."),
    fig("pd_key_dithered.png", "Phase detector output vs frequency, 1150-1550 MHz, five Pluto levels, 14 Nov evening, dithered; and the same data zoomed on 1215-1445 MHz; with the wiring"),
    ul(["One voltage = one frequency over about 1215&ndash;1445 MHz (about 230 MHz). Over 1240&ndash;1430 MHz the slope is 0.3&ndash;1.2 mV/MHz, median 0.84 mV/MHz (&minus;50 dBm).",
        "&minus;36 to &minus;57 dBm agree within &plusmn;2 MHz on 90% of 1240&ndash;1430 MHz. &minus;64 dBm (faded) is too weak to use.",
        "Repeat sweeps on 15 Nov agree with each other to 0.2 mV and with this run to about 1 mV (about 1 MHz)."]),
    fig("pd_key_wide.png", "Phase detector output vs frequency, 300-4000 MHz at -50 dBm, 14 Nov morning, not dithered, with the wiring"),
    ul(["Outside 1150&ndash;1550 MHz the curve keeps rippling (the ~375 MHz ripple), so the one-to-one region cannot be widened by going lower or higher.",
        "Above 2100 MHz the Pluto has no level table, so the script turned it down by 61 dB: the flat line there is not a detector reading."]),
    open_=True,
)

PD_HD_NIGHT = item(
    "pd-hd-night", "Pads removed, long IF cable: 600&ndash;1600 MHz at three levels (15 Nov, 20:03&ndash;20:31)",
    p("Sorin did not trust the 25 MHz no-pads sweeps, so this run fills 600&ndash;1600 MHz densely: 900&ndash;1200 and 1300&ndash;1500 MHz first (5, 2.5, 1.25, 0.625 MHz), then the rest (10, 5, 2.5 MHz). "
      "Pluto at &minus;36, &minus;50 and &minus;57 dBm, read back to back at each frequency. One scope reading per point (no dither, as Sorin asked; 2.5 s per point), 100 mV/div because the swing without pads is about 430 mV. "
      "The trace noise (about 1.9 mV rms) is half the 4 mV ADC step, so the averaged reading is not stuck on ADC steps. "
      "Data: <code>phase_detector_calibration/pd_dither_14nov.csv</code>, stages <code>hdr_pri</code> and <code>hdr_rest</code>. Plot: <code>plot_pd_hd_night.py hdr</code>. Sorin stopped this run after pass 2 to swap in a short IF cable (next section), so it reached 5 MHz in the priority regions and 10 MHz elsewhere."),
    fig("pd_hd_night_15nov.png", "Pads removed: 600-1600 MHz at -36, -50 and -57 dBm, one reading per point, with zooms on 900-1200 and 1300-1500 MHz and the wiring"),
)

PD_IFS = item(
    "pd-ifs", "Short IF cable (15 Nov night): the ~360 MHz ripple is NOT caused by the long IF cable; densest data so far",
    p("Test of the idea that the ~360 MHz ripple (about 2.8 ns of delay, far more than the arm difference) comes from reflections on the long IF cable to the scope. "
      "Sorin replaced it with an SMA-BNC adapter and an SMA cable about 16 cm long (about twice cable E); nothing else changed (cable E, no pads). "
      "Same plan as the long-cable run: 600&ndash;1600 MHz at &minus;36, &minus;50 and &minus;57 dBm, one reading per point, 100 mV/div. "
      "Data: <code>phase_detector_calibration/pd_dither_14nov.csv</code>, stages <code>ifs_pri</code> and <code>ifs_rest</code>; tone-off readings are stage <code>off</code>, reps 91&ndash;93. Plots: <code>plot_pd_ifs.py</code>, <code>plot_pd_hd_night.py ifs</code>. "
      "The run went from 20:33 to 21:43 and then stopped when the PC shut down for a Windows update overnight: 1618 readings. 900&ndash;1200 and 1300&ndash;1500 MHz are complete at 1.25 MHz steps; the rest of 600&ndash;1600 MHz is at 5 MHz (2.5 MHz in part)."),
    fig("pd_ifs_night_15nov.png", "Short IF cable: 600-1600 MHz at -36, -50 and -57 dBm, one reading per point, with zooms on 900-1200 and 1300-1500 MHz at 1.25 MHz steps, and the wiring"),
    fig("pd_ifs_vs_long_15nov.png", "Every high-density no-pads run (long IF cable, short IF cable, very short cables with 50 ohm IF load): each at three levels, then all at -50 dBm scaled to their own swing, with the wirings"),
    ul(["Peaks at &minus;50 dBm: 760, 1162 and 1495 MHz with the long cable; 765, 1164 and 1499 MHz with the short one. The ripple period and positions are unchanged, so the IF cable is not the cause.",
        "The swing is about 10&ndash;20% larger with the short cable, and the tone-off reading moved from &minus;23.7 to about &minus;45 mV.",
        "The levels still lie on top of each other except on the 1100&ndash;1150 MHz shoulder at &minus;36 dBm and near the peaks at &minus;57 dBm.",
        "Remaining suspects for the 2.8 ns delay: standing waves between the splitter and the mixer ports, or reflections in the shared path before the splitter. The amplifier supply current rose to 0.39 A during this run (0.22 A idle earlier)."]),
)

PD_RESOLUTION = item(
    "pd-resolution", "Which setup gives 1&ndash;2 MHz with the power unknown? Cable C, cable E with pads, cable E without pads (long and short IF cable)",
    p("Question (Sorin, 15 Nov): measure one detector voltage with a small reading error dV, and do not assume the power level (only that it is inside the measured range). What frequency error results? "
      "Method: the calibration curve is the mean of the levels; for every true frequency, every level and a reading off by &plusmn;dV, invert the calibration curve and take the worst frequency error; "
      "then find the longest contiguous stretch where that worst error stays &le;1 and &le;2 MHz. Linearity is the residual from a straight line, smoothness the residual from a 15 MHz running line, both in MHz. "
      "Each setup is its own run; nothing is overlaid across runs. For the no-pads runs the steep rising edge 1340&ndash;1480 MHz is analysed (the automatic pick lands on the shallower 960&ndash;1135 MHz edge). "
      "Script: <code>plot_pd_resolution.py</code>."),
    fig("pd_resolution_compare.png", "Frequency error with the power unknown: cable C, cable E with pads, cable E without pads (long and short IF cable); each with every level, a zoom on the one-to-one region, worst error vs reading error, and linearity; with the wirings"),
    table(["Setup (region)", "Slope, median (mV/MHz)", "Spread between levels, median (mV)", "Straight line off by (MHz rms)", "Smoothness (MHz rms)",
           "Width with error &le;1 / &le;2 MHz, dV = 0.5 mV", "Same, dV = 1 mV", "Same, dV = 0.5 mV, &minus;36 dBm left out"],
          [["C, no pads (900&ndash;1027 MHz), 4 levels &minus;36 to &minus;60", "1.12", "9.5", "8.8", "0.73", "0 / 19", "0 / 12", "1 / 17"],
           ["E with pads (1236&ndash;1438 MHz), 4 levels &minus;36 to &minus;57", "0.83", "1.6", "5.7", "0.27", "0 / 55", "0 / 17", "3 / 61"],
           ["E, no pads, long IF (1340&ndash;1480 MHz), 3 levels", "2.06", "7.8", "6.5", "0.40", "15 / 25", "15 / 25", "50 / 80"],
           ["E, no pads, short IF (1340&ndash;1480 MHz), 3 levels", "1.90", "7.9", "7.3", "0.69", "21 / 30", "11 / 29", "54 / 80"]]),
    ul(["Widths are contiguous MHz. None of the setups gives 1&ndash;2 MHz over 200 MHz with the power unknown from &minus;36 to &minus;57 dBm.",
        "The limit is the spread between power levels, not the reading noise. &minus;36 dBm (the amplifiers&rsquo; hardest drive) is the level that breaks away; leaving it out triples the usable width without pads.",
        "Cable E without pads, on the rising edge, gives the most: about 80 MHz with error &le;2 MHz and about 50 MHz with &le;1 MHz at dV = 0.5 mV when &minus;50 and &minus;57 dBm are compared; slope about 2&ndash;3 mV/MHz, about 3&times; the padded setup. "
        "Sorin (16 Nov): the received power is not under our control, so a lower input is not a fix; the amplifiers are meant to saturate so every input level lands on the same curve. "
        "&minus;50 and &minus;57 dBm do land on the same curve (spread about 2 mV); the &minus;36 dBm departure has to be fixed in hardware.",
        "With pads the curve is the most linear and smoothest (spread 1.6 mV) but the slope is only 0.8 mV/MHz, so 1&ndash;2 mV of spread already costs 2 MHz.",
        "Cable C is the worst: steep at 960&ndash;1015 MHz, then a flat shelf, and 9.5 mV between levels.",
        "The short and long IF cables give the same answer, as expected from the unchanged ripple."]),
)

PD_DELAY = item(
    "pd-delay", "The &lsquo;ripple&rsquo; is the interferometer itself: the arms differ by about 2.75 ns, not 0.55 ns (16 Nov)",
    p("Fit of every wide sweep with one delay: V(f) = a + b f + A cos(2&pi; f &tau; + &phi;), &tau; scanned 1.5&ndash;4 ns. The ~360 MHz pattern is not a ripple on top of a slow 0.55 ns curve; it is the main term (about 150 mV amplitude), and a 0.55 ns term is not found."),
    table(["Run", "Range (MHz)", "Best &tau; (ns)", "Full cycle (MHz)", "Amplitude (mV)"],
          [["Cable C, 1 Nov, &minus;50 dBm", "700&ndash;1600", "3.00", "333", "74"],
           ["Cable C, 1 Nov, &minus;60 dBm", "700&ndash;1600", "3.00", "333", "69"],
           ["Cable E, no pads, 13 Nov", "600&ndash;1700", "2.68", "373", "125"],
           ["Cable E, no pads, short IF cable, 15 Nov, &minus;50 dBm", "600&ndash;1600", "2.77", "361", "153"]]),
    ul(["The delay moves with the arm cable: C to E shortens it by 0.23&ndash;0.32 ns. C is about 12 cm and E about 8 cm, so 4 cm of coax is about 0.19 ns. The 2.75 ns is therefore the real difference between the two arms, not an outside reflection.",
        "That also explains the usable width: half a cycle of 2.75 ns is about 180 MHz, the one-to-one width seen in every run. A 0.55 ns difference would give about 900 MHz.",
        "Ruled out: the long IF cable (same curve with a short one).",
        "Cable lengths (Sorin, 16 Nov): B and D are both 15 cm, E about 8 cm, C about 12 cm. So the direct arm difference with E is only 8 cm, about 0.38 ns; it cannot give 2.75 ns.",
        "Likely cause: the ZFRSC-42-S+ is a resistive splitter with only about 6 dB between its outputs. A reflection off one mixer port goes back up its arm, crosses the splitter 6 dB down and reaches the other mixer port. "
        "Mixed against the direct signal, that path differs by the SUM of the two arms (D + B + E = 38 cm, about 1.8 ns of cable, plus the splitter, adapters and the paths inside the mixer to its diodes), not their difference. "
        "A sum of arms near 2.75 ns needs about 0.9 ns more than the cables alone, so this is likely but not yet proven.",
        "Test that separates the two with no new parts: lengthen arm D only. If the ~360 MHz pattern gets slower (longer cycle), it is the direct difference; if it gets faster, it is the reflection path through the splitter (sum of arms). "
        "Fix if it is the reflection path: a high-isolation (Wilkinson or hybrid) splitter in place of the resistive one, or attenuators right at the mixer ports (each dB of pad takes 2 dB off the reflected path)."]),
)

PD_NOPADS = item(
    "pd-no-pads", "Pads removed (15 Nov evening): twice the swing, and the curve moves about 110 MHz",
    p("Sorin removed the 3 dB pad at the LO port and the 6 dB pad at the RF port; nothing else changed. "
      "The same coarse sweep was run twice (1150&ndash;1550 MHz every 25 MHz, five Pluto levels, dithered, each sweep with its own 1 min tone-off reading) and compared with the two sweeps taken with the pads that morning."),
    fig("pd_nopads_15nov.png", "Phase detector without pads: two coarse sweeps at five levels; without against with the pads; and the change at each frequency and level; with both wirings"),
    ul(["The two no-pads sweeps agree within 0.5 mV (median) at every level, worst 2.0 mV.",
        "Swing: about 340 mV peak to peak without pads (&minus;88 to +254 mV, tone-off subtracted) against about 160 mV with them. On the rise the slope is about 2.7&ndash;2.8 mV/MHz (25 MHz steps, 1350&ndash;1450 MHz), about three times the 0.84 mV/MHz median with pads.",
        "The curve moved: the low point is now near 1325&ndash;1350 MHz (1225 MHz with pads) and the peak near 1500 MHz (1425&ndash;1450 MHz with pads). "
        "Rising one-to-one part about 1335&ndash;1500 MHz (about 165 MHz); a falling one-to-one part runs from below 1150 to about 1325 MHz.",
        "&minus;36 to &minus;57 dBm still lie on top of each other; &minus;64 dBm is still off.",
        "Tone-off reading: &minus;24.7 mV without pads, &minus;9.9 mV with.",
        "The highest raw reading is about 229 mV, close to the top of the scope screen (260 mV) and to the 250 mV stop rule."]),
)

PD_FIVE = item(
    "pd-five-levels", "Five Pluto levels across 1150&ndash;1550 MHz, coarse to fine (14 Nov evening): the rise runs 1215&ndash;1445 MHz with no flat sides; &minus;36 to &minus;57 dBm agree within &plusmn;2 MHz on 90% of it",
    p("Same wiring. Five Pluto levels: &minus;36 dBm (the Pluto's top), &minus;43, &minus;50, &minus;57 and &minus;64 dBm. At each frequency all five are read back to back (seconds apart), so slow drift moves them together. "
      "First run (15:50&ndash;17:59): 1150&ndash;1550 MHz every 2 MHz, stopped at 1412 MHz when the PC crashed. "
      "Second run (from 19:14), filled in coarse to fine by halving, as Sorin asked: both ends, the middle, the quarters, &hellip; down to 6.25 MHz (1.6% of the 400 MHz span), then 3.1 and 1.6 MHz on the rise only. "
      "Each halving step starts by re-reading 1350 MHz at the five levels as a drift check. Every point is dithered (four scope offsets 1 mV apart)."),
    fig("pd_all_config_raw.png", "Every phase detector reading of 13-15 Nov (5312 readings), raw: against time; every tone-on reading against frequency, coloured by level; the 13 Nov sweeps, the wide sweeps, the SM200B readings, every -50 dBm band sweep, the power ramp, the seven-level and five-level runs, a 20 min hold, the 15 Nov coarse repeats, and the 13 Nov sweeps before the pads were fitted, with both wirings"),
    fig("pd_bisect_14nov.png", "14 Nov evening: five Pluto levels filled in by halving down to 6.25 MHz, with the 2 MHz sweep from before the crash (thin lines), each level against -50 dBm, the frequency error, the 1350 MHz drift check, and the wiring"),
    fig("pd_sweep5_14nov.png", "14 Nov 15:50-17:59: five Pluto levels every 2 MHz from 1150 MHz up to 1412 MHz (stopped by the PC crash), slope, each level against -50 dBm, frequency error, with the wiring"),
    table(["Pluto levels", "Best (peak-to-peak)", "Worst (peak-to-peak)", "Median", "Points within &plusmn;2 MHz (1240&ndash;1430 MHz)"], [
        ["&minus;36 to &minus;64 dBm", "1.5 MHz", "36 MHz at 1425 MHz", "12.1 MHz", "23%"],
        ["&minus;36 to &minus;57 dBm", "0.4 MHz", "6.0 MHz at 1406 MHz", "1.9 MHz", "90%"],
        ["&minus;43 to &minus;57 dBm", "0.1 MHz", "5.8 MHz at 1406 MHz", "1.7 MHz", "93%"]], left=(0, 4)),
    ul(["There are no flat sides. The curve is lowest near 1215 MHz, rises to a peak near 1440&ndash;1450 MHz (about 150&ndash;160 mV) and falls again on both sides. "
        "This is the ~375 MHz ripple (see above). The one-to-one range is about 1215&ndash;1445 MHz (about 230 MHz); a frequency outside it gives a voltage that also occurs inside it.",
        "&minus;36 to &minus;57 dBm lie on top of each other over most of the rise (within &plusmn;2 MHz on 90% of the 1240&ndash;1430 MHz points). "
        "The levels part near the ends: below about 1250 MHz (small slope) and above about 1400 MHz, where &minus;36 and &minus;43 dBm flatten and dip before the peak.",
        "&minus;64 dBm is not usable: it reads up to 18 MHz high at the bottom of the rise and 50&ndash;60 mV low above 1350 MHz. The amplifiers are not saturated there. The input must stay above about &minus;57 dBm at the Pluto position.",
        "Within one session the curve is steady: the 1350 MHz check moved less than 0.5 mV (about 0.6 MHz) over 70 minutes, across a Pluto USB dropout and replug at 19:38&ndash;19:54.",
        "Between sessions it is not: after the PC restarts (18:00&ndash;18:48) the whole curve came back about 12 mV lower (about 15 MHz at 1350 MHz) than at 17:00, with the same shape. "
        "This is the third such jump on 14 Nov. A reference reading at start-up (or a known tone between pulses) would remove it.",
        "Amplifier current: 0.22 A with no tone, 0.24&ndash;0.29 A with the tone on, rising with Pluto level and changing with frequency (Sorin, 19:20&ndash;19:58). "
        "The 0.23 to 0.26 A change noted at 15:30 was the tone being on, not a fault; it is not the cause of the 15:18 offset."]),
    h("PC crashes, 14 Nov 17:20&ndash;18:48"),
    ul(["17:19&ndash;17:21 and 17:59: the PC entered Modern Standby, logged as &ldquo;Reason: Lid&rdquo;; the first run stopped at 17:21 and resumed 17:54 with no lost points.",
        "17:59: hard crash in standby; on restart Windows logged a fatal hardware error (WHEA, processor machine-check record). 18:25, 18:33, 18:37, 18:40: further freezes or forced restarts, some while no measurement was running.",
        "The measurement scripts are not the cause: the later crashes happened with no script running. The laptop also logged five &ldquo;driver power state&rdquo; crashes (0x9F) from 17 Oct to 11 Nov and Intel graphics hangs from August to October. "
        "The charger connection dropped repeatedly on 14 Nov afternoon.",
        "Since 18:48 (charger reseated, instruments replugged at 19:10) there have been no errors. The run script now also keeps the display on, since the screen turning off puts this laptop into Modern Standby."]),
    h("Repeat check, 15 Nov: the curve came back"),
    p("Same wiring, cables re-checked by hand. Windows Update restarted the PC at 02:01. Two coarse sweeps (1150&ndash;1550 MHz every 25 MHz, the same five levels), each a fresh launch of the run script with its own 1 min tone-off reading first."),
    fig("pd_coarse_15nov.png", "15 Nov 11:42-12:09: two coarse sweeps at five levels against the 14 Nov evening run (dashed), each sweep minus their average, the raw 1350 MHz / -50 dBm reading in every session, and the raw tone-off reading in every session, with the wiring"),
    ul(["The two sweeps agree to 0.13&ndash;0.23 mV (median) at &minus;36 to &minus;57 dBm, worst 0.74 mV; &minus;64 dBm is noisier (up to 5 mV near the peak).",
        "Both sit about 1 mV (about 1 MHz) above the 14 Nov evening run at every frequency and level, across a PC restart. The 12 mV jump did not recur.",
        "The session that stands out is 14 Nov afternoon (80 mV at 1350 MHz, &minus;50 dBm, against 68.5&ndash;69.5 mV in every session since). The jump came with the 14 Nov crashes and restarts, not with every new session."]),
    h("Pluto dropouts (19:38 and 21:51, 14 Nov)"),
    ul(["Both times Windows logged the Pluto as &ldquo;surprise removed, missing on the bus&rdquo;, and the program then lost its connection (Windows error 10053). Nothing was unplugged. The Pluto came back only when its USB hub was reset (19:53) or the PC restarted (02:01).",
        "The Pluto (firmware v0.39) and the scope share one USB hub (WCH 1A86:8098). Windows USB selective suspend is on for the hub and the Pluto. Both drops happened during a Pluto LO frequency change.",
        "Next: turn off USB power saving for the hub and the Pluto (fix_usb_power_admin.ps1, admin), and log the Pluto's USB state with each failure to tell a Windows-side drop from a Pluto firmware hang."]),
)

PD_PLUTO = item(
    "pd-vs-pluto", "Is the ~360 MHz pattern the Pluto&rsquo;s own level ripple? No (16 Nov)",
    p("Sorin asked whether the pattern comes from the Pluto, as with the comparator. The Pluto&rsquo;s output against frequency was measured on 12 Oct straight into the Siglent spectrum analyzer, 350&ndash;2090 MHz in 10 MHz steps "
      "(<code>pluto_characterization/pluto_map_table.csv</code>; Pluto tab, Results). It has a ripple of its own. Here it is set against the phase detector curve (cable E, no pads, short IF cable, 15 Nov). "
      "Script: <code>phase_detector_calibration/plot_pd_vs_pluto_level.py</code>."),
    fig("pd_vs_pluto_level.png", "Pluto output ripple against frequency, the phase detector curve, the detector change for a 7 dB level change, and their correlation, with both wirings"),
    ul(["Pluto ripple: 0.45&ndash;0.49 dB rms after a smooth trend, up to about 1.5 dB near 1450 MHz. Its bumps are about 150&ndash;200 MHz apart below 1150 MHz and 80&ndash;150 MHz apart above; not 360 MHz.",
        "Detector sensitivity to the Pluto level: going from &minus;57 to &minus;50 dBm (7 dB) moves the detector by a median 2.9 mV (0.4 mV per dB), at most about 28 mV near 810 MHz and 20 mV near 1500 MHz (about 4 mV per dB). "
        "So the Pluto ripple can add at most a few mV; the detector pattern swings by about 500 mV.",
        "Correlation between the two after removing smooth trends: |r| &le; 0.3 at every shift up to &plusmn;200 MHz.",
        "The pattern also changed with the arm cable (C to E), which a source effect would not do. The Pluto&rsquo;s line near 3&times; the tone (10&ndash;16 dB down) is still a possible contributor to the shape and to the &minus;36 dBm departure; a low-pass filter after the Pluto would test it."]),
)

PD_SC = item(
    "pd-short-cables", "Very short cables at every mixer connection, 50 ohm load on the IF (18 Nov 10:39-12:40): pattern unchanged",
    p("<b>Result (first full pass, 11:02):</b> the pattern did not change. Peaks at &minus;50 dBm at 770, 1160 and 1510 MHz (15 Nov: 760&ndash;765, 1162&ndash;1164, 1495&ndash;1499); "
      "best single delay 2.74 ns (15 Nov: 2.77 ns); swing about 450 mV. Tone-off was &minus;8 mV at 10:39 and &minus;25 mV from 11:02 onward, steady after that; the tone-on curve did not move (later passes match pass 1 within about 1 mV median), so only the zero reading changed. "
      "So the cables at the mixer and the IF termination are not the source, and nor is any reflection path whose delay is the sum of the arms. "
      "New suspect: the amplifier chain itself. Its saturated output power can ripple with frequency (reflections between the four stages), the curve would then be the same at every input level and independent of the arm and IF cables, as seen. "
      "Test: amplifier chain output into the SM200B through pads, swept 600&ndash;1600 MHz; or drive the splitter straight from the Pluto with the amplifiers bypassed."),
    p("Test of whether the ~360 MHz pattern (best single delay about 2.75 ns) comes from reflections on the cables at the mixer. "
      "Sorin replaced every connection at the mixer with very short cables and put a 50 ohm load on the IF line into the scope (SDS1104X-E). "
      "Same plan as the 15 Nov runs: 600&ndash;1600 MHz at &minus;36, &minus;50 and &minus;57 dBm, one reading per point, 100 mV/div; 900&ndash;1200 and 1300&ndash;1500 MHz filled first, then repeat sweeps every 5 MHz. "
      "Data: <code>phase_detector_calibration/pd_dither_14nov.csv</code>, stages <code>sc_pri</code>, <code>sc_rest</code>, <code>sc_rep</code>; tone-off is stage <code>off</code>, reps 141 and up. "
      "Plots are redrawn by <code>make_plots.py</code> from the run table <code>pd_runs.py</code>; the comparison with the earlier runs is in the section below."),
    fig("pd_short_cables_detail_18nov.png", "Phase detector with very short cables at the mixer and a 50 ohm IF load: 600-1600 MHz at three levels with zooms, and the wiring"),
)

PD_AMP = item(
    "pd-amp-chain", "Amplifier chain alone into the SM200B: is the ~360 MHz pattern already in the amplifiers? (18 Nov from 13:06): no, the pattern comes after them",
    p("Pluto TX &rarr; 4 &times; ZX60-P162LN+ (4.03 V; every cable 7 cm) &rarr; 10 + 10 + 3 + 6 = 29 dB of pads &rarr; SM200B. No splitter, arms or mixer. "
      "Expected: the chain rails near +20 dBm (datasheet P1dB +19.9 dBm per stage at 1 GHz), so about &minus;9 dBm at the SM200B, nearly the same at every input level. "
      "If the amplifiers cause the detector pattern, the output level should ripple with a ~2.75 ns delay (peaks near 770, 1160, 1510 MHz)."),
    p("Plan: 600&ndash;1600 MHz every 25 MHz, then every 5 MHz; Pluto &minus;36, &minus;43, &minus;50, &minus;57, &minus;64, &minus;71 dBm at each frequency. "
      "At each point 16384 raw IQ samples (50 MS/s, 328 &micro;s, tone 10 MHz above the centre) are saved, and the instantaneous power |I+jQ|&sup2; of every sample is used, not only an average; "
      "the 2nd and 3rd harmonics are read too (the Pluto has a line near 3&times; the tone, 10&ndash;16 dB down, and a railed amplifier makes harmonics). "
      "Script <code>run_amp_chain_iq.py</code> (wrapper <code>amp_wrapper.sh</code>, waits for the SM200B, resumes after USB drops); data <code>amp_chain_18nov.csv</code>; raw IQ in "
      "<code>C:\\ThatFamily Dropbox\\Sorin Jayaweera\\allSaves\\mudd\\senior\\clinic\\claude\\phase_detector_calibration\\amp_chain\\</code> (local only, about 150 MB); plot <code>plot_amp_chain.py</code>."),
    p("The Pluto alone, from the Pluto tab (12&ndash;13 Oct, into the spectrum analyzer): level repeatable to 0.03 dB on returning to a frequency, settled within 5 ms, "
      "and across 600&ndash;1600 MHz its ripple after a smooth trend is 0.5 dB rms with only 0.11 dB at a 2.75 ns delay (its strongest component is 1.4 ns, 0.22 dB). "
      "With the amplifiers railed that is attenuated further, so the Pluto itself is not the source."),
    fig("amp_chain_18nov.png", "Amplifier chain alone: output tone, instantaneous power, harmonics and ripple against frequency at six Pluto levels, raw IQ example, and the wiring"),
    p("<b>Result (sweep 13:06&ndash;13:19, 1206 points): the amplifiers do not cause the detector's ~360 MHz pattern.</b> "
      "With &minus;57 dBm or more into the chain the output is railed at +20 to +22 dBm across 650&ndash;1600 MHz, with about &plusmn;0.5&ndash;0.8 dB of ripple whose strongest single delay is 4.4 ns (about 225 MHz period), "
      "not the detector's 2.75 ns; the ripple's correlation with the detector curve (18 Nov short-cable run, 800&ndash;1600 MHz, trends removed) is 0.08. "
      "Anything before the splitter is common to both arms, so the amplifiers' phase cancels in the detector; only their level could matter, and it does not match. "
      "The pattern therefore comes from the splitter, the mixer or the ports between them. It stayed at 2.74&ndash;2.77 ns with cable E and with very short arm cables, so it looks fixed inside those parts "
      "(for example a different delay from the mixer's LO and RF ports to its core) rather than set by the arm lengths."),
    p("Not railed at low input: with &minus;64 dBm in, the output falls to about +18 dBm above 1300 MHz; with &minus;71 dBm it falls from +20 dBm below 1000 MHz to +12 dBm at 1600 MHz. "
      "So the chain holds a constant output only down to about &minus;60 dBm at the top of the band; the ramp below maps exactly where."),
    p("First readings: the chain puts out +17 to +21 dBm (railed). With no tone it still puts out about &minus;3 dBm in the SM200B's 41.5 MHz window: 90 dB of gain amplifies its own thermal noise, "
      "so over the amplifiers' ~1 GHz bandwidth the noise alone is near +6 dBm, close to saturation. Below about 800 MHz the 2nd harmonic lands inside the amplifiers' band and comes out only 5&ndash;9 dB under the tone. "
      "Where 30.75 dB of Pluto attenuation would be needed (&minus;36 dBm near 1525 MHz) the Pluto script's 31 dB safety floor is used instead, 0.25 dB lower; the CSV keeps the setting used."),
    h("Output against Pluto level"),
    p("After the frequency sweep: Pluto &minus;90 to &minus;36 dBm in 1 dB steps at 700&ndash;1600 MHz every 50 MHz plus 770, 960, 1160, 1340 and 1510 MHz (detector peaks and troughs), repeated up to 30 times "
      "(rep 1 keeps 16384 IQ samples per point, later reps 4096). Shows where the chain starts to rail, how much of the output is noise rather than tone at each level, and how repeatable it is. "
      "Data <code>amp_ramp_18nov.csv</code>, raw IQ <code>amp_ramp\\</code> (local only), wrapper <code>amp_ramp_wrapper.sh</code> (<code>AMP_MODE=ramp</code>)."),
    p("Pass 1 (all 24 frequencies): the chain rails at +19.5 to +22 dBm everywhere; it is within 1 dB of that from about &minus;70 dBm in below 1000 MHz, but needs &minus;60 to &minus;63 dBm above 1200 MHz. "
      "At &minus;90 dBm in the output falls from +11 dBm at 700 MHz to &minus;7 dBm at 1500 MHz."),
    p("<b>Signal lost at 14:40:13</b> (rep 9, 750 MHz), mid-step: the SM200B saw only its own floor, not even the amplifiers' noise (tone off &minus;38 dBm against &minus;3 dBm normally), "
      "so the amplifiers lost power or the path to the SM200B opened. Run stopped at 14:53; the 1689 rows after 14:40:13 were removed (backup <code>backups\\amp_ramp_18nov_before_trim_1453.csv</code>, "
      "raw IQ moved to <code>amp_ramp\\no_signal_1440\\</code>). <code>amp_resume.sh</code> probes every 2 min with <code>amp_probe.py</code> and resumes the ramp when the output is back; "
      "the run now stops itself if the output at &minus;60 dBm or more drops below 0 dBm."),
    fig("amp_ramp_18nov.png", "Amplifier chain alone against Pluto level: compression curve per frequency, noise share, tone against frequency at fixed levels, repeatability, raw IQ power distribution, and the wiring"),
)

PD_STATUS = item(
    "pd-status", "Status, methods and open issues (read this first when coming back to the phase detector; updated 18 Nov)",
    h("Goal"),
    p("One detector voltage per frequency over about 200 MHz, read to &plusmn;1&ndash;2 MHz after op-amp scaling into an FPGA ADC, "
      "whatever the received power. The amplifiers are meant to rail, so every input level should land on the same curve. Absolute frequency does not matter (the PLL shifts it)."),
    h("Chain as built"),
    p("Pluto TX &rarr; 4 &times; ZX60-P162LN+ (4.03 V; about 22.5 dB gain and P1dB +19.9 dBm each at 1 GHz, so the chain rails near +20 dBm at every level used) &rarr; ZFRSC-42-S+ resistive splitter (about 6 dB between outputs) &rarr; "
      "every cable from the Pluto through the amplifiers to the splitter is 7 cm (Sorin, 18 Nov) &rarr; "
      "two arms (LO: cable D 15 cm; RF: cable B 15 cm + E 8 cm; on 18 Nov replaced by very short cables) &rarr; ZX05-30W-S+ LO and RF &rarr; IF &rarr; SDS1104X-E. Pads at the mixer ports: removed since 15 Nov."),
    h("How data is taken and plotted"),
    ul(["<code>run_pd_overnight.py</code> (run from <code>signal_hound/</code>, system Python): stages written to <code>pd_dither_14nov.csv</code>, one row per reading; tone-off checks as stage <code>off</code>.",
        "High-density plan (<code>HD_NIGHT=1 HD_TAG=tag</code>): 600&ndash;1600 MHz at &minus;36/&minus;50/&minus;57 dBm, 900&ndash;1200 and 1300&ndash;1500 MHz first, coarse to fine, then repeats.",
        "Each bench configuration is one row in <code>pd_runs.py</code>. <code>make_plots.py</code> redraws every plot from the CSV, rebuilds this site and pushes (<code>--push</code>; <code>--watch</code> during a run)."]),
    h("What is known"),
    ul(["The curve is dominated by a single ~2.75 ns delay (one cycle per ~360 MHz), not the 0.38 ns the arm lengths give. It shifted only slightly with the arm cable (C 3.00 ns, E 2.77 ns) and not at all with very short cables (2.74 ns, 18 Nov).",
        "Not the long IF cable (15 Nov), not the Pluto's own level ripple (16 Nov), not the cables at the mixer or the IF termination, and not reflections through the arms (18 Nov).",
        "Not the amplifier chain (18 Nov, SM200B on the chain alone): railed at +20 to +22 dBm, ripple &plusmn;0.5&ndash;0.8 dB with its strongest delay at 4.4 ns, correlation 0.08 with the detector curve. The chain rails over the whole band only with &minus;57 dBm or more in.",
        "Main suspect now: a fixed delay inside the splitter or mixer (for example different LO and RF port delays to the mixer core), since the 2.75 ns stays with any arm cable.",
        "&minus;50 and &minus;57 dBm agree within about 2 mV; &minus;36 dBm departs on the shoulders (deepest compression; supply current rises to 0.39 A).",
        "Best so far: cable E, no pads, rising edge 1340&ndash;1480 MHz, about 80 MHz with error &le;2 MHz at &plusmn;0.5 mV (&minus;50/&minus;57 dBm). Pads give a smoother but 3&times; shallower curve."]),
    h("Open"),
    ul(["Add a known length (e.g. 15 cm, about 0.75 ns) to one arm: if the fitted delay moves by exactly that, the 2.75 ns is a fixed offset inside the parts; if not, something else sets it.",
        "Swap the mixer's LO and RF inputs, then swap in another mixer or splitter, and see whether the delay changes sign or size.",
        "A high-isolation (Wilkinson) splitter; a low-pass filter after the amplifiers (the 2nd harmonic is only 5&ndash;9 dB down below 800 MHz).",
        "Power-cycle the SDS1104X-E: it is stuck on a VISA protocol error since 12:50 and must be reset by hand before the next detector run."]),
    h("Pitfalls"),
    ul(["Pluto drops off USB about hourly (Windows logs a bus removal). The scripts resume where they stopped; the wrapper relaunches.",
        "<code>sm_api.dll</code> needs the working folder <code>signal_hound/</code>. Use system Python (radioconda has no pyvisa).",
        "Never stash, reset or check out while a run writes the CSV (18 Nov: a stash caught the live file; no data lost, but the progress log was cut)."]),
    open_=True,
)
