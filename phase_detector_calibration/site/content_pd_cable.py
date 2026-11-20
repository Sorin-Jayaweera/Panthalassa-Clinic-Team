"""Phase detector tab: delay cable E and pads at the mixer, 13-14 Nov 2026."""
import json
from pathlib import Path

from content import item, table, ul, p, h, fig

PD_CABLE = item(
    "pd-cable-e", "Delay cable E (about 9 cm with its adapter) with pads at the mixer ports, 13&ndash;14 Nov: voltage vs frequency, power levels, noise, drift",
    p("Goal: one clean voltage per frequency over 200 MHz, read to &plusmn;2 MHz. The PLL can move the band anywhere, so the absolute frequency does not matter. "
      "Wiring (every plot shows it): Pluto TX &rarr; 4 &times; ZX60-P162LN+ (4.03 V, 0.23 A) &rarr; ZFRSC-42-S+ &rarr; right arm cable D to the LO port, left arm cable B + E to the RF port "
      "&rarr; ZX05-30W-S+ &rarr; IF to SDS1104X-E CH1 (1 M&Omega;) and, through pads, the SM200B. D is 16.6 cm and B 15.2 cm (Sorin, 18 Nov; earlier taken as equal), so the RF arm is longer by E + B &minus; D = 9 &minus; 1.4 = 7.6 cm. On 1 Nov it was cable C (about 12 cm), 10.6 cm."),
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

XU = json.load(open(Path(__file__).resolve().parent.parent / "pd_x_uncertainty_table.json"))
PD_RESOLUTION = item(
    "pd-resolution", "Frequency uncertainty with the power unknown, every run, by one method (Sorin, 19 Nov): need 200 MHz continuous with a total width &le;4 MHz (&plusmn;2 MHz)",
    p("Method (Sorin, 19 Nov). A level set is the Pluto levels from the highest down to a threshold. Its lookup is the median curve: at each frequency, the median of every reading of every level in the set. "
      "At each true frequency, take the voltage the detector gives with the input at the top level and at the threshold level (each the median over that level's passes), look both up on the median curve, and plot each frequency read minus the true frequency. "
      "The total width is the distance between those two frequencies (&plusmn;2 MHz = 4 MHz total). The lookup must be single valued, so the median curve is split wherever it turns (increasing or decreasing both fine); a reading past a turn has no unique frequency and is marked &times; at the bottom. "
      "Thresholds: every level (&lsquo;could be measuring anything&rsquo;), &minus;60 dBm, the lowest level where the four ZX60-P162LN+ are railed (what matters, Sorin), and &minus;50 dBm; sets with the same levels are drawn once. "
      "Railed = the chain within 1 dB of its saturated output at every frequency 950&ndash;1600 MHz in the 18 Nov power ramp (<code>amp_ramp_18nov.csv</code>): &minus;58 dBm is within 0.7 dB, &minus;60 dBm up to 1.1 dB down, &minus;63 dBm 2&ndash;3 dB, &minus;72 dBm up to 10 dB, so the railed set is &ge;&minus;58 dBm. "
      "Each run has two plots: the voltage read against frequency, one line per Pluto level and pass (every reading taken), with the median curves; then the frequency offsets. "
      "Script <code>plot_pd_x_uncertainty.py</code>; data <code>pd_dither_14nov.csv</code> (stages per run in <code>pd_runs.py</code>) and <code>p162x4_fine_1nov.csv</code> (cable C)."),
    p("This replaces the earlier figures (15&ndash;19 Nov: <code>pd_resolution_compare.png</code>, <code>pd_power_freq_error_*</code>, <code>pd_power_uncertainty_*</code>). Those used a mean or a monotonic-forced curve, a reading error &plusmn;dV added on top, the worst one-sided error, "
      "and made-up summaries (best window, % of frequencies, rms). Their numbers should not be used."),
    fig("pd_x_uncertainty_all_runs.png", "Every run with at least two power levels: total width (top level against threshold level, both looked up on the set's median curve) against frequency, one curve per level set; dotted = 4 MHz"),
    p("Is &minus;50 dBm a reasonable threshold? Link from a Furuno 1722C (2.2 kW, main beam about 24 dBi from its 5.2&deg; &times; 25&deg; beam) to the bench&rsquo;s Pluto level, taking the Pluto level as the RX mixer output: horn 10&ndash;15 dBi, limiter 0.5 dB (assumed), ZX60-5123LN+ +22.0 dB, ZX05-14LH-S+ &minus;7.72 dB, so Pluto-equivalent = antenna port + 13.8 dB. Over the sea (two-ray, radar 4 m and our antenna 2 m above the water, both assumed) the main beam is still about &minus;33 to &minus;37 dBm Pluto-equivalent at the 14 km radio horizon, 13&ndash;17 dB above &minus;50 dBm; inside about 3 km it is above 0 dBm, far above the &minus;36 dBm top level tested on the bench. Sidelobes (typically 20&ndash;25 dB down) would be near the threshold at the horizon. Script plot_pd_furuno_link_budget.py."),
    fig("pd_furuno_link_budget_19nov.png", "Furuno main beam: Pluto-equivalent level against distance, free space and two-ray over the sea, horn 10 and 15 dBi, with the -50 dBm threshold, the -58 dBm railed level, the -36 dBm top bench level and the radio horizon; with the link chain"),
    fig("pd_design_limits_19nov.png", "What limits the detector and what to change: 1 longest usable stretch against the weakest level allowed, every run; 2 pad10hf, each level minus the railed median curve; 3 gain change and curve shift of every pass against the railed median, padded runs (passes at one level agree, so the power dependence is systematic, not drift); 4 predicted usable stretch against the arm length difference, scaled from pad10hf, with every padded run measured and the cable pairs on hand. Script plot_pd_design_limits.py"),
    table(["Run", "Every level: longest stretch with total width &le;4 MHz", "Levels &ge;&minus;60 dBm", "Railed, levels &ge;&minus;58 dBm (what matters)", "Levels &ge;&minus;50 dBm"], [r[:1] + r[2:] for r in XU], left=(0, 1, 2, 3, 4)),
    ul(["pad10hf (10 dB pads, H on LO, B + F on RF, RF arm about 25 cm longer) meets 200 MHz: railed set &minus;36 to &minus;54 dBm 1084&ndash;1364 MHz (280 MHz), &minus;36 to &minus;45 dBm 1104&ndash;1420 MHz (316 MHz). One pass per level so far (8 and 4 MHz grids); the repeats are running.",
        "Only the top and the threshold level enter the width (Sorin's definition); a middle level that sits outside both is not counted. The first plot shows every level so that can be checked.",
        "With every level the padded runs reach only 8&ndash;72 MHz: &minus;63 and &minus;72 dBm fall off the saturated curve.",
        "pad10z40 and pad10z40n have one level only, so they have no power range."]),
    *[fig(png, f"{name}: voltage read against frequency, one line per Pluto level and pass, with each level set's median curve; then the frequency read for the top and the threshold level minus the true frequency, with the wiring") for name, png, *_ in XU],
)

PD_DELAY = item(
    "pd-delay", "The &lsquo;ripple&rsquo; is the interferometer itself: the arms differ by about 2.75 ns, not 0.55 ns (16 Nov)",
    p("Fit of every wide sweep with one delay: V(f) = a + b f + A cos(2&pi; f &tau; + &phi;), &tau; scanned 1.5&ndash;4 ns. The ~360 MHz pattern is not a ripple on top of a slow 0.55 ns curve; it is the main term (about 150 mV amplitude), and a 0.55 ns term is not found."),
    table(["Run", "Range (MHz)", "Best &tau; (ns)", "Full cycle (MHz)", "Amplitude (mV)"],
          [["Cable C, 1 Nov, &minus;50 dBm", "700&ndash;1600", "3.00", "333", "74"],
           ["Cable C, 1 Nov, &minus;60 dBm", "700&ndash;1600", "3.00", "333", "69"],
           ["Cable E, no pads, 13 Nov", "600&ndash;1700", "2.68", "373", "125"],
           ["Cable E, no pads, short IF cable, 15 Nov, &minus;50 dBm", "600&ndash;1600", "2.77", "361", "153"]]),
    ul(["The delay moves with the arm cable: C to E shortens it by 0.23&ndash;0.32 ns. C is about 12 cm and E about 9 cm with its adapter, so 3 cm of coax is about 0.14 ns at velocity factor 0.70. The 2.75 ns is therefore the real difference between the two arms, not an outside reflection.",
        "That also explains the usable width: half a cycle of 2.75 ns is about 180 MHz, the one-to-one width seen in every run. A 0.55 ns difference would give about 900 MHz.",
        "Ruled out: the long IF cable (same curve with a short one).",
        "Cable lengths (Sorin, 16 and 18 Nov): B 15.2 cm, D 16.6 cm (first given as 15 cm each), E about 9 cm with its adapter, C about 12 cm. So the direct arm difference with E is 7.6 cm, about 0.36 ns (velocity factor 0.70 assumed; cable type unknown); it cannot give 2.75 ns.",
        "Likely cause: the ZFRSC-42-S+ is a resistive splitter with only about 6 dB between its outputs. A reflection off one mixer port goes back up its arm, crosses the splitter 6 dB down and reaches the other mixer port. "
        "Mixed against the direct signal, that path differs by the SUM of the two arms (D + B + E = 40.8 cm, about 1.9 ns of cable, plus the splitter, adapters and the paths inside the mixer to its diodes), not their difference. "
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
    "pd-amp-chain", "Amplifier chain alone into the SM200B: is the ~360 MHz pattern already in the amplifiers? (18 Nov from 13:06): its amplitude ripple does not match, but that does not rule the amplifiers out (Sorin)",
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
    p("<b>Result (sweep 13:06&ndash;13:19, 1206 points): the amplifiers' output level does not carry the detector's ~360 MHz pattern.</b> (Sorin, 18 Nov: this does not rule the amplifiers out; it was measured into a matched pad, not into the splitter and mixer. Later the same day the SM200B arm probes traced the pattern to the mixer ports' reflections; see the 18 Nov section.) "
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
    p("<b>Gap 14:40&ndash;15:11</b> (rep 9, 750 MHz): the amplifier supply was disconnected at the bench (a status reply was read as &ldquo;the run is finished&rdquo;); "
      "the SM200B saw only its own floor, not even the amplifiers' noise (tone off &minus;38 dBm against &minus;3 dBm normally). Reconnected unchanged (4.04 V, 0.23 A); resumed 15:11:46. Run stopped at 14:53; the 1689 rows after 14:40:13 were removed (backup <code>backups\\amp_ramp_18nov_before_trim_1453.csv</code>, "
      "raw IQ moved to <code>amp_ramp\\no_signal_1440\\</code>). <code>amp_resume.sh</code> probes every 2 min with <code>amp_probe.py</code> and resumes the ramp when the output is back; "
      "the run now stops itself if the output at &minus;60 dBm or more drops below 0 dBm."),
    fig("amp_ramp_18nov.png", "Amplifier chain alone against Pluto level: compression curve per frequency, noise share, tone against frequency at fixed levels, repeatability, raw IQ power distribution, and the wiring"),
)

PD_STATUS = item(
    "pd-status", "Status, methods and open issues (read this first when coming back to the phase detector; updated 19 Nov)",
    h("Goal"),
    p("One detector voltage per frequency over about 200 MHz, read to &plusmn;1&ndash;2 MHz after op-amp scaling into an FPGA ADC, "
      "whatever the received power. The amplifiers are meant to rail, so every input level should land on the same curve. Absolute frequency does not matter (the PLL shifts it). Requirement (Sorin, 19 Nov): a continuous 200 MHz stretch read to &plusmn;2 MHz (total width &le;4 MHz) with the power unknown, measured as in the frequency uncertainty item."),
    h("Chain as built"),
    p("Pluto TX &rarr; 4 &times; ZX60-P162LN+ (4.03 V; about 22.5 dB gain and P1dB +19.9 dBm each at 1 GHz, so the chain rails near +20 dBm at every level used) &rarr; ZFRSC-42-S+ resistive splitter (about 6 dB between outputs) &rarr; "
      "every cable from the Pluto through the amplifiers to the splitter is 7 cm (Sorin, 18 Nov) &rarr; "
      "two arms (LO: cable D 16.6 cm; RF: cable B 15.2 cm + E with adapter ~9 cm; 18 Nov: very short cables, then B and D alone, then 10 dB pads at both mixer ports) &rarr; ZX05-30W-S+ LO and RF &rarr; IF &rarr; SDS1104X-E. Pads at the mixer ports: removed 15 Nov, back since 18 Nov (10 dB at LO and RF). <b>Since 19 Nov 19:24:</b> Pluto &rarr; 2 &times; ZX60-P103LN+ (5.00 V, 0.21 A) &rarr; 4 &times; ZX60-P162LN+ (4.04 V, 0.22 A) &rarr; ZFRSC-42-S+ &rarr; LO arm cable H (7 cm) and RF arm B (15.2 cm) + F (16.5 cm), RF &minus; LO 24.7 cm &rarr; 10 dB pad at each mixer port &rarr; ZX05-30W-S+ &rarr; short IF cable + 50 &Omega; &rarr; SDS1104X-E (run pad10hfp2)."),
    h("How data is taken and plotted"),
    ul(["<code>run_pd_overnight.py</code> (run from <code>signal_hound/</code>, system Python): stages written to <code>pd_dither_14nov.csv</code>, one row per reading; tone-off checks as stage <code>off</code>.",
        "High-density plan (<code>HD_NIGHT=1 HD_TAG=tag</code>): 600&ndash;1600 MHz at &minus;36/&minus;50/&minus;57 dBm, 900&ndash;1200 and 1300&ndash;1500 MHz first, coarse to fine, then repeats.",
        "Each bench configuration is one row in <code>pd_runs.py</code>. <code>make_plots.py</code> redraws every plot from the CSV, rebuilds this site and pushes (<code>--push</code>; <code>--watch</code> during a run)."]),
    h("Expected delay from the arm lengths against the fitted delay (lengths corrected 18 Nov)"),
    p("Sorin measured B 15.2 cm and D 16.6 cm on 18 Nov; every earlier figure took both as 15 cm. Expected delay = |RF arm &minus; LO arm| / (0.70 c) = 0.0477 ns/cm "
      "(velocity factor 0.70 assumed: Amazon SMA cables with a pink jacket, type unknown). Fitted delay: <code>pdlib.delay(f, v, deg=2)</code>, 600&ndash;1600 MHz, &minus;50 dBm (spread over the three levels &plusmn;0.02 ns)."),
    table(["Run", "RF &minus; LO (cm)", "Expected, old lengths (ns)", "Expected, corrected (ns)", "Fitted (ns)", "Fitted &minus; expected (ns)"],
          [["Cable C, 1 Nov (C about 12 cm, not re-measured)", "15.2 + 12 &minus; 16.6 = 10.6", "0.57", "0.51", "3.00", "2.49"],
           ["Cable E + adapter, 15 Nov (hdr, ifs)", "15.2 + 9 &minus; 16.6 = 7.6", "0.38", "0.36", "2.78&ndash;2.80", "2.43"],
           ["B and D only, 18 Nov (eq)", "15.2 &minus; 16.6 = &minus;1.4", "0", "0.07", "2.28&ndash;2.31", "2.22"],
           ["B and D + 10 dB pad at each mixer port, 18&ndash;19 Nov (pad10, first 600&ndash;1240 MHz only)", "&minus;1.4 (pads equal)", "0", "0.07", "1.63&ndash;1.65", "1.58"]]),
    ul(["The 1.4 cm between B and D is 0.07 ns: over 600&ndash;1600 MHz it turns the phase by only 24&deg;, so it cannot make the ~360 MHz pattern. The error from the expectation is 2.2&ndash;2.5 ns in every run.",
        "The fitted delay still tracks the arm difference: C &rarr; E &rarr; eq changes it by +0.22 and +0.50 ns where the lengths predict +0.14 and +0.43 ns. A straight line through the three runs gives 2.37 ns at zero difference plus 0.058 ns/cm "
        "(velocity factor 0.57, residuals &le;0.03 ns): a fixed ~2.4 ns path plus the arm difference, or a slower cable than assumed, or C longer than 12 cm.",
        "The fixed part is not in the arm cables: with the same B and D, 10 dB pads at the mixer ports move it from 2.28 to 1.65 ns. It depends on the reflections at the mixer ports.",
        "Very short arm cables (sc, 18 Nov) gave 2.76&ndash;2.79 ns, the same as cable E; their lengths were not recorded, so that run cannot be placed on the line."]),
    h("What is known"),
    ul(["The curve is dominated by a single ~2.3&ndash;2.8 ns delay (one cycle per ~360&ndash;440 MHz), not the 0.07&ndash;0.51 ns the arm differences give (table above).",
        "Not the long IF cable (15 Nov), not the Pluto's own level ripple (16 Nov), not the IF termination.",
        "SM200B probe of each arm between the splitter and the mixer (18 Nov, 29 dB pads, one mixer port driven, the other terminated): the RF arm with the mixer on it shows 1.9&ndash;2.0 dB rms ripple whose strongest delay is 2.72 ns, the detector's delay. "
        "With the mixer removed (cable D into an ANNE-50L+) the ripple drops to 0.6&ndash;0.8 dB and the 2.7 ns term is gone; with a 10 dB pad at the mixer RF port (19 dB pads to the SM200B) it is 0.56&ndash;0.76 dB with no clear delay. "
        "So the pattern is the mixer ports' reflection (datasheet VSWR up to 3.5) coming back through the resistive splitter (5.94 dB isolation) into the other arm.",
        "Unpadded, each arm carried +10 to +19 dBm (measured + 29 dB), which is what a mixer port receives; the ZX05-30W-S+ RF maximum is +17 dBm (50 mW). With 10 dB pads it is about +2 to +7 dBm.",
        "The ZX10-2-1252-S+ (the other splitter on hand) covers 1800&ndash;12500 MHz only, so it cannot replace the ZFRSC-42-S+ in this band.",
        "Amplifier chain alone into 29 dB of pads (18 Nov, SM200B): railed at +20 to +22 dBm, amplitude ripple &plusmn;0.5&ndash;0.8 dB with its strongest delay at 4.4 ns, correlation 0.08 with the detector curve; rails over the whole band only with &minus;57 dBm or more in. This does <b>not</b> rule the amplifiers out (Sorin, 18 Nov): it measured amplitude only, into a matched pad, while the 2.75 ns pattern is seen with the amplifiers railed, driving the splitter and mixer, with a 50 &Omega; IF load. The amplifiers driving the real splitter/mixer load are untested.",
        "&minus;50 and &minus;57 dBm agree within about 2 mV; &minus;36 dBm departs on the shoulders (deepest compression; supply current rises to 0.39 A).",
        "Best so far: cable E, no pads, rising edge 1340&ndash;1480 MHz, about 80 MHz with error &le;2 MHz at &plusmn;0.5 mV (&minus;50/&minus;57 dBm). Pads give a smoother but 3&times; shallower curve."]),
    h("Open"),
    ul(["Night 19&ndash;20 Nov (pad10hfp2, two P103s ahead): do the weak levels now land on the railed curve, and how far down? Where is the new railed edge? Is the +14.7 mV tone-off the chain saturating on its own noise or an oscillation (a spectrum of the chain output through pads would tell; SM200B &le;+10 dBm measured)?",
        "Questions for Sorin (19 Nov): the lookup is split wherever the median curve turns, and on the 1 MHz grid noise-level reversals cut it; should small reversals be ignored? Is &lsquo;within 1 dB of saturation&rsquo; the right railed criterion? Antenna heights (4 m and 2 m assumed)? Is the Pluto level the RX mixer output, and is the IF splitter for the envelope detector before or after the chain? What joins B to F? Which centre frequency should the linear part sit on?",
        "Cable C's length (about 12 cm) and the very short cables of the sc run were not measured; the cable velocity factor is unknown.",
        "Add a known length (e.g. 15 cm, about 0.75 ns) to one arm: if the fitted delay moves by exactly that, the 2.75 ns is a fixed offset inside the parts; if not, something else sets it.",
        "Swap the mixer's LO and RF inputs, then swap in another mixer or splitter, and see whether the delay changes sign or size.",
        "A high-isolation (Wilkinson) splitter; a low-pass filter after the amplifiers (the 2nd harmonic is only 5&ndash;9 dB down below 800 MHz)."]),
    h("Pitfalls"),
    ul(["Pluto drops off USB about hourly (Windows logs a bus removal). The scripts resume where they stopped. A drop mid-run is retried for 180 s; a Pluto missing at launch stops the run within 10 s (19 Nov 19:19). Overnight 19&ndash;20 Nov <code>pad10hfp2_relaunch_after_pluto_drop.sh</code> waits for the Pluto and relaunches (up to 6 times). Keep the laptop lid open during runs: a closed lid sends it into Modern Standby, which drops the scope and the Pluto from USB (19 Nov 21:29&ndash;21:58).",
        "The tone-off reading depends on the chain: &minus;1.7 mV with the 4 &times; P162 chain (pad10hf), +14.7 mV with two P103s ahead (pad10hfp2). Subtract each run&rsquo;s own tone-off, never another run&rsquo;s.",
        "<code>sm_api.dll</code> needs the working folder <code>signal_hound/</code>. Use system Python (radioconda has no pyvisa).",
        "Never stash, reset or check out while a run writes the CSV (18 Nov: a stash caught the live file; no data lost, but the progress log was cut)."]),
    open_=True,
)

RAW = "C:&#92;ThatFamily Dropbox&#92;Sorin Jayaweera&#92;allSaves&#92;mudd&#92;senior&#92;clinic&#92;claude&#92;phase_detector_calibration&#92;"
DAY18 = [  # (time, arrangement, instrument, data, what was seen)
    ["10:40&ndash;12:40", "Very short cables at every mixer connection, 50 &Omega; IF load", "scope", "<code>pd_dither_14nov.csv</code> stages <code>sc_*</code>", "Same ~360 MHz pattern: 2.76&ndash;2.79 ns, ~125 mV. Cables at the mixer and the IF termination ruled out."],
    ["13:06&ndash;13:19", "Amplifier chain alone &rarr; 29 dB &rarr; SM200B", "SM200B raw IQ", "<code>amp_chain_18nov.csv</code>, raw <code>amp_chain&#92;</code>", "Railed +20 to +22 dBm (measured + 29 dB); &plusmn;0.5&ndash;0.8 dB ripple, strongest delay 4.4 ns. Amplitude only, into a matched load: does not rule the amplifiers out (Sorin)."],
    ["13:30&ndash;16:40", "Amplifier chain, Pluto level stepped &minus;90 to &minus;36 dBm", "SM200B raw IQ", "<code>amp_ramp_18nov.csv</code>, raw <code>amp_ramp&#92;</code>", "Rails within 1 dB from about &minus;70 dBm in below 1000 MHz, &minus;60 to &minus;63 dBm above 1200 MHz."],
    ["17:02&ndash;19:43", "Cables B (15.2 cm, RF) and D (16.6 cm, LO) only, no E", "scope", "stages <code>eq_*</code>", "2.28&ndash;2.31 ns (peaks 945 and 1380 MHz); arm difference only &minus;1.4 cm (0.07 ns)."],
    ["19:49&ndash;19:57", "Cable E moved to the LO arm", "scope", "stages <code>elo_*</code>", "Stopped by Sorin after 8 min (not useful); 900&ndash;1350 MHz only, too short for a fit."],
    ["20:05", "SM200B in place of the mixer LO port (cable D); B drives mixer RF; LO terminated", "SM200B raw IQ", "<code>arm_probe_lo_18nov.csv</code>", "Arm tone +10 to +19 dBm (measured + 29 dB), strongest delay 1.9&ndash;2.0 ns."],
    ["20:16", "SM200B in place of the mixer RF port (cable B); D drives mixer LO; RF terminated", "SM200B raw IQ", "<code>arm_probe_rf_18nov.csv</code>", "<b>1.9&ndash;2.0 dB rms ripple, strongest delay 2.72 ns: the detector's delay is already on the arm signal.</b>"],
    ["evening", "As above, mixer removed (D &rarr; adapter &rarr; ANNE-50L+)", "SM200B raw IQ", "<code>arm_probe_rf_nomixer_18nov.csv</code>", "Ripple 0.6&ndash;0.8 dB, 2.7 ns gone: the pattern needs the mixer."],
    ["evening", "10 dB pad at the mixer RF (D) and LO (to 50 &Omega;); B &rarr; 19 dB &rarr; SM200B", "SM200B raw IQ", "<code>arm_probe_rf_padded_18nov.csv</code>", "Ripple 0.56&ndash;0.76 dB, no clear delay: pads at the mixer suppress it."],
    ["20:59 &rarr; 07:55", "B and D with a 10 dB pad at each mixer port, 50 &Omega; IF load; 600&ndash;1600 MHz every 1 MHz, 5 levels", "scope", "stages <code>pad10_*</code>", "Ramp from about 720 to 1460 MHz with the ripple about 10&times; smaller, but read at 100 mV/div (4 mV ADC steps). Stopped at 21:40 for the zoomed reading below."],
    ["21:44 &rarr; 07:55", "Same wiring; each point read in two rounds: 100 mV/div for the level, then the finest V/div (0.5&ndash;20 mV/div) centred on it; "
     "each level swept across the band in turn so only the offset moves (<code>scope_zoom.py</code>)", "scope", "stages <code>pad10z_*</code>; V/div per reading in <code>pd_zoom_readings_18nov.csv</code>",
     "<b>Two full 1 MHz sweeps (22:00&ndash;01:54, 01:55&ndash;06:04) and half a third (to 07:55).</b> 720&ndash;1600 MHz: a smooth ramp, 0.215 mV/MHz at &minus;36 to &minus;54 dBm, the three levels within 1&ndash;2 mV; about 6 mV rms left after a straight line; ripple term about 7 mV (123 mV without pads). Repeat 2 minus repeat 1 above 720 MHz: sd 0.23&ndash;0.29 mV = 1.1&ndash;1.4 MHz at &minus;63 to &minus;36 dBm; 0.48 mV = 3.8 MHz at &minus;72 dBm (shallower, not railed). Tone-off &minus;41.9 mV, steady to 0.03 mV all night. Dip at 600&ndash;720 MHz (deepest about 687 MHz) changes with level. 18 readings taken while testing (V/div switched every point, 6.5 s each) are kept as stage <code>pad10z_switching_test</code>."],
]
PD_DAY18 = item(
    "pd-day-18nov", "18 Nov, every arrangement and what it showed: the ~360 MHz pattern is the mixer ports' reflections coming back through the resistive splitter",
    p("One row per arrangement, in order. Scope rows: Pluto &rarr; 4 &times; ZX60-P162LN+ (4.03 V) &rarr; ZFRSC-42-S+ &rarr; two arms &rarr; ZX05-30W-S+ &rarr; IF &rarr; SDS1104X-E, "
      "one reading per point, written to <code>pd_dither_14nov.csv</code> by <code>run_pd_overnight.py</code>. SM200B rows: one splitter output into the SM200B through pads in place of a mixer port, "
      "16384 raw IQ samples per point (<code>run_amp_chain_iq.py</code>, <code>AMP_MODE=arm</code>, log <code>arm_probe_18nov.log</code>). SM200B levels are measured + the pads. "
      "CSVs, logs and plots are on GitHub. Raw IQ folders (78&ndash;950 MB each) stay local in <code>" + RAW + "</code> and are copied to <code>D:&#92;Panthalassa Backup</code>."),
    table(["Time", "Arrangement", "Instrument", "Data", "What was seen"], DAY18, left=(1, 3, 4)),
    fig("pd_day_18nov_delays.png", "18 Nov: strongest single delay in every arrangement and level, detector and SM200B probes"),
    fig("pd_day_18nov_detector.png", "18 Nov: detector voltage vs frequency for every scope arrangement, tone-off subtracted, stacked, with every wiring"),
    fig("pd_day_18nov_probes.png", "18 Nov: SM200B tone ripple at each probe point, stacked, with every wiring"),
    h("Each arrangement in full"),
    fig("pd_short_cables_detail_18nov.png", "Very short cables, 50 ohm IF load: 600-1600 MHz at three levels with zooms, and the wiring"),
    fig("amp_chain_18nov.png", "Amplifier chain alone into the SM200B, and the wiring"),
    fig("amp_ramp_vs_freq_18nov.png", "Amplifier chain: output tone vs frequency, one line per Pluto level, and the wiring"),
    fig("amp_ramp_waterfall_18nov.png", "Amplifier chain: each Pluto level's deviation from its own mean, and the wiring"),
    fig("pd_equal_arms_detail_18nov.png", "Cables B and D only: 600-1600 MHz at three levels with zooms, and the wiring"),
    fig("pd_cable_E_on_LO_detail_18nov.png", "Cable E on the LO arm (stopped after 8 min), and the wiring"),
    fig("arm_probe_lo_18nov.png", "SM200B at the end of the LO arm (cable D), mixer RF driven, and the wiring"),
    fig("arm_probe_rf_18nov.png", "SM200B at the end of the RF arm (cable B), mixer LO driven, and the wiring"),
    fig("arm_probe_rf_nomixer_18nov.png", "SM200B at the end of the RF arm with the mixer removed, and the wiring"),
    fig("arm_probe_rf_padded_18nov.png", "SM200B at the end of cable B with 10 dB pads at the mixer ports, and the wiring"),
    fig("pd_pads_10dB_1MHz_detail_18nov.png", "10 dB pads at both mixer ports, 100 mV/div, 20:59-21:40, five levels, and the wiring"),
    fig("pd_pads_10dB_zoomed_detail_18nov.png", "Overnight: 10 dB pads at both mixer ports, zoomed two-round readings, five levels (updates as data comes in), and the wiring"),
    fig("pd_pad10z_repeats_18_19nov.png", "Overnight zoomed run: each later repeat minus repeat 1 at every frequency and level, with the spread in mV and in MHz, and the wiring"),
    fig("pd_pads_10dB_cable_E_on_RF_detail_19nov.png", "19 Nov afternoon: 10 dB pads at both mixer ports PLUS cable E on the RF arm (RF arm 7.6 cm longer), 600-1600 MHz, six levels, zoomed readings (updates as data comes in), and the wiring. "
        "The overnight B/D runs had near-equal arms (0.07 ns), so they sat at the top of the detector's cosine and could not show frequency resolution"),
    fig("pd_theory_vs_measured.png", "Theory against measurement for every arrangement: cos(2 pi f tau) with tau from the cable length difference at an assumed velocity factor 0.70 (constants ignored), "
        "each run's strongest level scaled to -1..+1, and the best single-cosine fit; last panel all theory curves together. Script plot_pd_theory.py"),
    fig("pd_pad10d_voltage_vs_level.png", "Pads + cable E: detector voltage against Pluto level, one line per frequency (colour = frequency), raw and relative to -36 dBm, with the wiring. Script plot_pd_level_response.py"),
    fig("pd_pad10z_voltage_vs_level.png", "Pads, cables B and D only (overnight): detector voltage against Pluto level, one line per frequency, for comparison, with the wiring"),
    p("Frequency uncertainty for this and every other run: see the first item in this tab, &lsquo;Frequency uncertainty with the power unknown, every run&rsquo;."),
)

DAY19 = [  # (time, arrangement, instrument, data, what was seen)
    ["08:14&ndash;08:18", "As pad10z (B and D, 10 dB pad at each mixer port, zoomed readings), one more level: &minus;40 dBm, 600&ndash;1600 MHz", "scope", "stages <code>pad10z40_*</code>, log <code>pd_pad10z40_19nov.log</code>", "62 points; stopped when Sorin asked to focus on 900&ndash;1200 MHz."],
    ["08:19&ndash;09:00", "Same, &minus;40 dBm, 900&ndash;1200 MHz only", "scope", "stages <code>pad10z40n_*</code>", "903 points, 3 sweeps. One level, so no power range."],
    ["09:01&ndash;12:45", "Same, 900&ndash;1200 MHz, six levels &minus;36 to &minus;72 dBm cycled", "scope", "stages <code>pad10zn_*</code>",
     "4411 points. Longest stretch with total width &le;4 MHz: &minus;36 to &minus;54 dBm 1097&ndash;1199 MHz (102 MHz, cut by the band edge); &ge;&minus;50 dBm 1127&ndash;1199 MHz."],
    ["12:49&ndash;13:33", "10 dB pads as pad10z plus cable E on the RF arm (RF &minus; LO 7.6 cm), 600&ndash;1600 MHz, six levels", "scope", "stages <code>pad10d_*</code>, log <code>pd_pad10d_19nov.log</code>",
     "843 points. &minus;36 to &minus;54 dBm 1256&ndash;1384 MHz (128 MHz); &ge;&minus;50 dBm 1232&ndash;1416 MHz (184 MHz). Its median curve has noise-level reversals."],
    ["13:36&ndash;18:54", "10 dB pads, cable H (7 cm) on LO, B (15.2 cm) + F (16.5 cm) on RF: RF &minus; LO 24.7 cm plus the joint; 600&ndash;1600 MHz, six levels", "scope",
     "stages <code>pad10hf_*</code>, log <code>pd_pad10hf_19nov.log</code>, <code>pad10hf_wrapper.sh</code>",
     "<b>6170 points: 8 and 4 MHz grids, then part of a second repeat. &ge;&minus;50 dBm 1138&ndash;1391 MHz (253 MHz) meets 200 MHz; &minus;36 to &minus;54 dBm (railed) 1219&ndash;1367 MHz (148 MHz); every level 733&ndash;782 MHz (49 MHz).</b> "
     "Cosine fit to the railed median, 720&ndash;1600 MHz: A 183 mV, &tau; 1.013 ns, &phi;<sub>0</sub> &minus;2.97 rad, C 5.6 mV, 13.9 mV rms residual; rising crossing 1208 MHz. Stopped at 18:54 with the stop file so Sorin could add the P103s."],
    ["19:19", "2 &times; ZX60-P103LN+ (5.00 V on the E3630A +6 V output, 0.21 A) between the Pluto and the 4 &times; ZX60-P162LN+ (4.04 V, 0.22 A); arms and pads as pad10hf", "scope",
     "log <code>pd_pad10hfp2_19nov_first_launch_pluto_off_usb_1919.log</code>", "No data: the Pluto was off USB at launch (192.168.2.1 not answering, not listed by Windows) and the run stopped after 10 s. It answered again at 19:24."],
    ["19:24 &rarr; overnight", "Same (2 &times; P103 ahead), 600&ndash;1600 MHz, eight levels &minus;36, &minus;40, &minus;45, &minus;54, &minus;63, &minus;72, &minus;81, &minus;89 dBm, coarse to fine, repeated", "scope",
     "stages <code>pad10hfp2_*</code>, log <code>pd_pad10hfp2_19nov.log</code>, <code>pad10hfp2_wrapper.sh</code>, <code>pad10hfp2_relaunch_after_pluto_drop.sh</code>",
     "Oscillation check (Sorin): the first 43 &minus;36 dBm readings (600&ndash;936 MHz) are within 0.8 mV (median) of pad10hf's, worst 9.8 mV; noise within a reading 0.13 mV (pad10hf 0.22 mV). "
     "<b>Tone off is now +14.7 mV, steady to &plusmn;0.2 mV, rms 19.7 mV (pad10hf: &minus;1.7 mV, 6.6 mV).</b> Likely the extra gain saturating the chain on its own input noise (about &minus;82 dBm in 1 GHz &times; about 118 dB); not verified. "
     "First pass, &minus;36 to &minus;54 dBm: 1032&ndash;1448 MHz (416 MHz) &le;4 MHz total width, one pass only. &minus;89, not &minus;90 dBm: below about 1 GHz &minus;90 dBm needs more than the 89.75 dB attenuator maximum. "
     "<b>First 8 MHz pass, all levels (20:13): the weak levels flatten toward the tone-off value (about 15 mV), not toward the curve.</b> rms departure from &minus;36 dBm, new chain (pad10hf in brackets): "
     "&minus;54 dBm 1&ndash;5 mV (4&ndash;5); &minus;63 dBm 3&ndash;5 mV below 1250 MHz (3&ndash;11) but 41&ndash;45 mV above (26&ndash;27); &minus;72 dBm 16&ndash;37 mV at 750&ndash;1250 MHz, 124&ndash;149 mV above; &minus;81 and &minus;89 dBm nearly flat except 600&ndash;750 MHz. "
     "So 31 dB more gain helped below 1250 MHz and not above: above 1250 MHz the weak-level limit is not gain but something of fixed level that the chain amplifies with the tone (its own noise, an oscillation, or pickup). A spectrum of the chain output with the tone off would tell which. "
     "<b>After the 8 and 4 MHz passes (21:11): &minus;36 to &minus;54 dBm is within 4 MHz total width over 1036&ndash;1448 MHz (412 MHz; pad10hf 148 MHz), &minus;36 to &minus;45 dBm 1040&ndash;1448 MHz (408 MHz); every level to &minus;89 dBm only 4 MHz.</b> One pass so far. "
     "21:29 the laptop entered Modern Standby (Windows Kernel-Power 506; it left at 21:58 with reason &lsquo;Lid&rsquo;), and at 21:31:49 Windows removed the scope (VID F4EC) and the Pluto (VID 0456) from USB as &lsquo;draining power when idle&rsquo;: "
     "last reading 21:30:44 (2 MHz pass, 558 of 2000 points), scope VISA error, run ended 21:58:12. The relauncher restarted it at 21:58:51 from point 558; nothing was lost. The run&rsquo;s own keep-awake request does not stop a closed lid. "
     "20 Nov 01:04:57&ndash;01:26:46 the lid was closed again (Kernel-Power 506/507, reason &lsquo;Lid&rsquo;): the run paused for 22 min in the 1 MHz pass at 1135 MHz, &minus;63 dBm, then went on by itself after one Pluto retry; the reading taken across the pause (1135 MHz) fits its neighbours (&minus;58.0, &minus;56.5, &minus;54.8 mV). "
     "<b>Repeat 1 complete at 03:06 (8, 4, 2 and 1 MHz grids); tone off 14.25 mV (14.74 at the start).</b> With the 1 MHz grid in, &minus;36 to &minus;54 dBm drops to 1129&ndash;1367 MHz (238 MHz) and &minus;36 to &minus;45 dBm to 1061&ndash;1366 MHz (305 MHz). "
     "This is the lookup being cut, not the detector: the median curve on the full 1 MHz grid has about 210 monotonic pieces against 17&ndash;41 on either half, because the odd frequencies (1 MHz pass, 23:15&ndash;03:06) sit 0.1&ndash;0.3 mV (0.1&ndash;0.35 MHz) below the even ones (19:26&ndash;23:15). "
     "Repeat 1 on the 2 MHz grid alone: 410 MHz (&minus;54) and 404 MHz (&minus;45); on the odd 1 MHz frequencies alone: 420 and 334 MHz. Whether reversals this small should split the lookup is Sorin&rsquo;s open question. "
     "Repeat 2, 8 MHz grid (03:07&ndash;03:57) minus repeat 1 (19:26&ndash;20:16), per point: &minus;36 to &minus;54 dBm median within &plusmn;0.15 mV, sd 0.6&ndash;0.7 mV over 600&ndash;1600 MHz and 0.3&ndash;0.4 mV over 1040&ndash;1440 MHz; &minus;63 and &minus;72 dBm sd 0.6&ndash;1.0 mV. "
     "So the weak levels&rsquo; departure from the curve repeats from pass to pass: it is systematic, not noise. "
     "After repeat 2&rsquo;s 4 MHz pass (04:53): &minus;36 to &minus;54 dBm 1174&ndash;1367 MHz (193 MHz), &minus;36 to &minus;45 dBm 1092&ndash;1366 MHz (274 MHz). Of the 76 frequencies in 1000&ndash;1450 MHz that fail for &minus;36 to &minus;54 dBm, "
     "72 fail as &lsquo;no unique frequency&rsquo; (e.g. median &minus;34.15 mV at 1164 MHz, &minus;34.25 mV at 1165 MHz: a 0.1 mV reversal on a 0.8 mV/MHz slope) and only 4 have a total width over 4 MHz; where a width is computed it is mostly under 2.5 MHz. "
     "The lid was closed again 06:25:41&ndash;09:36:02 (Kernel-Power 506/507, reason &lsquo;Lid&rsquo;): the run paused for 3 h 10 min at 1973 of 2000 points of repeat 2&rsquo;s 2 MHz pass and went on by itself after one Pluto retry. Again 09:46:33&ndash;09:57:44 (11 min, repeat 2&rsquo;s 1 MHz pass at 953 MHz, &minus;36 dBm), resumed the same way. Again 11:36:03&ndash;12:23:32 (repeat 2&rsquo;s 1 MHz pass at 2242 of 4000 points): this time Windows removed the scope and the Pluto from USB at 12:10:32, the run ended at 12:23:36 and the relauncher restarted it at 12:24:04 from point 2242. "
     "<b>Stopped by Sorin at 12:58 (stop file, tone off; he needed the computer). Final: 14 776 readings, repeat 1 complete (8, 4, 2, 1 MHz) and repeat 2 through its 2 MHz pass plus 2760 of 4000 points of its 1 MHz pass. "
     "&minus;36 to &minus;54 dBm within 4 MHz total width over 1062&ndash;1431 MHz (369 MHz); &minus;36 to &minus;45 dBm 1038&ndash;1431 MHz (393 MHz); every level to &minus;89 dBm 7 MHz.</b> "
     "rms departure from &minus;36 dBm, 1000&ndash;1250 / 1250&ndash;1450 MHz: &minus;54 dBm 1.5 / 0.8 mV; &minus;63 dBm 3.6 / 40 mV; &minus;72 dBm 36 / 122 mV; &minus;81 and &minus;89 dBm 87&ndash;133 mV. "
     "Final copy on the D: drive: <code>D:&#92;Panthalassa Backup&#92;data&#92;phase_detector&#92;delay_line_sweeps&#92;final_copy_20nov_1258_after_2xP103_run</code> (CSV hash checked)."],
]
PD_DAY19 = item(
    "pd-day-19nov", "19 Nov, every arrangement and what it showed: a longer RF arm (24.7 cm) meets 200 MHz at &ge;&minus;50 dBm; two ZX60-P103LN+ added ahead of the chain for the night",
    p("One row per arrangement, in order. Wiring for every scope row: Pluto &rarr; amplifiers &rarr; ZFRSC-42-S+ &rarr; two arms &rarr; 10 dB pad at each mixer port &rarr; ZX05-30W-S+ &rarr; short IF cable + 50 &Omega; load &rarr; SDS1104X-E CH1, "
      "each point read in two rounds (100 mV/div, then the finest V/div centred on it, <code>scope_zoom.py</code>), each level swept across the band in turn. Data: <code>pd_dither_14nov.csv</code>, written by <code>run_pd_overnight.py</code> "
      "(<code>PD_PLAN=fine</code>, one row per configuration in <code>pd_runs.py</code>). Widths use Sorin's method (item above). Every run's own figure with its wiring is in the frequency uncertainty item."),
    table(["Time", "Arrangement", "Instrument", "Data", "What was seen"], DAY19, left=(1, 3, 4)),
    h("Analysis added on 19 Nov"),
    ul(["Frequency uncertainty, Sorin's definition: level set = top level down to a threshold; lookup = median of every reading of every level in the set; at each true frequency the top and the threshold level's readings are looked up on it; total width = the distance between the two frequencies read. Replaces every earlier resolution figure.",
        "Furuno link budget: the main beam stays above &minus;50 dBm Pluto-equivalent out to the 14 km radio horizon (two-ray over the sea; antenna heights 4 m and 2 m assumed).",
        "Design limits (<code>plot_pd_design_limits.py</code>): every pass fitted against the railed median as gain change, shift along frequency and offset. Passes at one level agree to about 0.1 MHz, so the level dependence is systematic, not drift; below about &minus;58 dBm the gain falls 10% at &minus;63 dBm and 30&ndash;60% at &minus;72 dBm.",
        "Amplifiers on hand (datasheets in <code>JACON_component_specs.xlsx</code>): ZX60-P103LN+ (50&ndash;3000 MHz, 15.6 dB at 1 GHz, P1dB +22.4 dBm, 5 V), ZX60-2534MA-S+ (43.5 dB, input damage &minus;15 dBm), ZX60-14012L-S+ (12 dB, 12 V). "
        "The P103, 2534MA and 14012L may only go before the P162s (their input limits). Two P103s add about 31 dB at 1 GHz, so the chain input is about &minus;5 to &minus;58 dBm at 1 GHz for &minus;36 to &minus;89 dBm from the Pluto.",
        "The &lsquo;railed, &ge;&minus;58 dBm&rsquo; set comes from the 18 Nov ramp of the 4 &times; P162 chain. With the two P103s ahead the railed edge should be about 31 dB lower (not yet measured), so for pad10hfp2 that column only means &ge;&minus;58 dBm."]),
    h("Choosing the arm length"),
    p("Model: V(f) = A cos(2&pi;f&tau; + &phi;<sub>0</sub>) + C, with &tau; = &Delta;L / (v<sub>f</sub> c). Measured: pad10hf's 24.7 cm gives &tau; = 1.013 ns, where v<sub>f</sub> = 0.70 would give 1.18 ns, so new lengths are scaled from the measurement, not from v<sub>f</sub>: "
      "&Delta;L<sub>new</sub> = 24.7 cm &times; &tau;<sub>new</sub> / 1.013 ns."),
    ul(["Span (what set &lsquo;22&ndash;38 cm&rsquo;): with r = &tau;<sub>new</sub>/&tau;<sub>now</sub>, every error in frequency shrinks by r and the band compresses by r, so span(r) = (1/r) &times; longest stretch of pad10hf where the total width &le; 4r MHz. "
        "Assumes the level dependence stays the same in phase and the pads keep the reflections down.",
        "Centring (where the linear part sits): the steepest, most linear point is the crossing 2&pi;f<sub>0</sub>&tau; + &phi;<sub>0</sub> = (k + &frac12;)&pi;, so &tau;<sub>k</sub> = ((k + &frac12;)&pi; &minus; &phi;<sub>0</sub>) / (2&pi;f<sub>0</sub>). "
        "pad10hf (&phi;<sub>0</sub> = &minus;2.97 rad) has its crossings at 714, 1208 and 1702 MHz. Assumes &phi;<sub>0</sub> stays when only the cable changes.",
        "Sorin (20 Nov): centre on 1.1 GHz if possible (his first estimate was about 4.5 in), but any 200 MHz span will do; the PLL then steps 9.4 GHz down to that span's centre. "
        "For a 1.1 GHz centre the formula gives &tau; = 1.112 ns (k = 1), &Delta;L = 27.1 cm: about 2.4 cm more on the RF arm. Not verified: pad10z and pad10d cover less than half a cycle, so their fits (0.435 and 0.468 ns) cannot test whether &tau; scales with &Delta;L; "
        "pad10hfp2 repeats pad10hf exactly (1.012 ns, &minus;2.96 rad). 4.5 in (11.4 cm) is &frac34; of a wavelength at 1.1 GHz for a velocity factor of about 0.56.",
        "Without changing the cable: the measured stretch (&minus;36 to &minus;54 dBm, 1062&ndash;1431 MHz) holds a 200 MHz span centred at 1250 MHz (1150&ndash;1350 MHz, 88 and 81 MHz to spare), so the PLL would sit at 9400 &minus; 1250 = 8150 MHz (low-side; the Furuno&rsquo;s 9402.6 MHz lands at 1252.6 MHz). "
        "Bands from <code>JACON_component_specs.xlsx</code>: ZX05-14LH-S+ RF and LO 3.7&ndash;10 GHz, IF DC&ndash;4 GHz (high-side LO, 10.5&ndash;10.65 GHz, is out of band); ZX60-14012L-S+ 0.3 MHz&ndash;14 GHz; ZX10-2-1252-S+ 1.8&ndash;12.5 GHz; ZX60-5123LN+ 5.5&ndash;12.5 GHz; "
        "ZX60-P162LN+ 0.7&ndash;1.6 GHz; ZX60-P103LN+ 50&ndash;3000 MHz; ZFRSC-42-S+ DC&ndash;4.2 GHz; ZX05-30W-S+ RF and LO 0.3&ndash;4 GHz. Every one covers both an 8150 MHz and an 8300 MHz LO with their IF spans. "
        "Candidates not in the workbook (VCO CVCO55BE-0800-1600, ADF5355, ADL5511, GALI-52+/ERA-33SM+, VHF-8400+, ZVE-143-S+) still need their datasheets checked."]),
)

