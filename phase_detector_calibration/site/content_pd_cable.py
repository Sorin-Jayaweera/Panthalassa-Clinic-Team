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
        "From 14 Nov 12:52 the runs use 50 mV/div with an offset (2 mV steps); data in <code>pd_fine_14nov.csv</code>. A reading front end needs an ADC step well under 8 mV.",
        "Hold at 1340 MHz for 20 min: sd 0.33 mV, no visible drift. Tone off: sd 0.26 mV.",
        "Between 13 Nov evening and 14 Nov midday the band sits 2 to 7 mV higher. That is session-to-session drift, not noise.",
        "Median slope in 1228&ndash;1440 MHz: 0.54 mV/MHz read at 0.2 V/div (staircase included), about 0.86 mV/MHz from end to end."]),
    table(["File", "What"], [
        ["<code>phase_detector_calibration/pd_cable_13nov_E_pads.csv</code>", "13 Nov evening: 2 MHz sweep and power passes"],
        ["<code>phase_detector_calibration/pd_kitty_13nov_E_pads.csv</code>", "13 Nov: 25 MHz steps with the SM200B on the IF port"],
        ["<code>phase_detector_calibration/pd_overnight_13nov.csv</code>", "14 Nov 10:51&ndash;12:51: whole range, power ramp, band, hold, tone off (0.2 V/div)"],
        ["<code>phase_detector_calibration/pd_fine_14nov.csv</code>", "14 Nov from 12:52: the same stages at 50 mV/div"],
        ["<code>phase_detector_calibration/plot_pd_cable.py</code>, <code>plot_pd_dense.py</code>, <code>plot_pd_overnight.py</code>", "The plots"]], left=(0, 1)),
)
