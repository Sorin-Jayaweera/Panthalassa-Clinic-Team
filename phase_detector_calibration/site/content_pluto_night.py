"""Pluto tab, overnight run of 12 to 13 Oct. Tables are filled from pluto_characterization/overnight_summary.json."""
import json
from pathlib import Path

from content import table, ul, ol, p, h, math, fig, D
import content_pluto_night2 as N2

SUM = Path(__file__).resolve().parent.parent.parent / "pluto_characterization" / "overnight_summary.json"
N = json.loads(SUM.read_text()) if SUM.exists() else {}


def n(v, d=2):
    if v is None or v != v:
        return D
    return f"{v:.{d}f}".replace("-", "&minus;")


def learned():
    """Short list of what the tests showed, for someone about to use this Pluto as a source."""
    if not N:
        return ""
    sc = N.get("scale", {})
    mx = ", ".join(f"{n(sc[k]['level_at_1'], 1)} dBm at {k.split()[0]} MHz" for k in ("400 att0", "1000 att0", "1100 att0", "1200 att0", "2000 att0") if k in sc)
    return "".join([
        h("What was learned"),
        table(["Subject", "Finding", "What to do"], [
            ["Highest output", f"Tone scale 1.0, attenuation 0 dB: {mx}. The team notes say +11 dBm; this unit does not reach it.", "Plan tests around +5 dBm at most. Add an amplifier if a part needs more."],
            ["Level against attenuation setting", "Follows the setting within 0.6 dB from 20 dB down to 89.75 dB (&minus;89.5 dBm at 1100 MHz). Reads 0.6 to 1.0 dB low at 0 dB.", "Use the look up table for 0 to 20 dB. From 20 dB up, output = (20 dB reading) + 20 &minus; setting."],
            ["0.25 dB steps", "Average step 0.24 dB, but single steps range from 0.09 to 0.41 dB. The same setting gives the same level from above or below (within 0.02 dB).", "Do not count steps to set a level. Read the level, or use whole-dB settings from the table."],
            ["Tone scale", "Follows 20 log10(scale) within 0.25 dB at 20 dB attenuation, from scale 0.02 to 1.0.", "Use the scale as a fine level control when the attenuation is 20 dB or more."],
            ["Distortion at high scale", "At scale 1.0 and 0 dB attenuation a line 4 MHz below the tone is only 31 dB under it. At scale 0.5 it is 46 dB under; at scale 0.3, 52 dB under.", "Keep the tone scale at 0.3 or below when a clean tone matters."],
            ["Third harmonic of the LO", "A line near three times the tone frequency, 10 to 16 dB under the tone. Measured for tones of 350 to 700 MHz. For a 1.0 to 1.2 GHz tone it is at 3.0 to 3.6 GHz, above the spectrum analyzer's range, so not measured there.",
             "Assume it is present at 1.0 to 1.2 GHz. Parts that work at 3 GHz (the amplifiers, mixers) receive it. Add a low-pass filter after the Pluto for compression or harmonic tests, and check with the SM200B."],
            ["Second and third harmonic of the tone", "50 to 60 dB under the tone at scale 0.5, 0 dB attenuation. 40 to 60 dB under at scale 1.0.", "Small enough to ignore next to the line above."],
            ["LO leakage and other sideband", "At 1100 MHz, 0 dB attenuation: LO leakage 61 to 67 dB under the tone, other sideband 67 to 72 dB under.", "No action needed."],
            ["Tone offset from the LO", "Level is flat within 0.4 dB out to 8 MHz from the LO, 1.3 dB down at 10 MHz, 7.8 dB down at 14 MHz.", "Keep the tone within 8 MHz of the LO. The scripts use 1 MHz."],
            ["Two tones", "At 0 dB attenuation with each tone at scale 0.5, the third-order products are 30 dB under the tones. At 5 dB attenuation with each tone at scale 0.25 to 0.5 they are over 50 dB under.", "For two-tone tests use 5 dB attenuation or more and each tone at scale 0.4 or less."],
            ["Frequency", "12.6 to 13.1 ppm low against the spectrum analyzer, the same at every frequency.", "Set the Pluto 12.8 ppm high (14.1 kHz at 1100 MHz) to land on a wanted frequency."],
            ["Repeatability", "Leaving 1100 MHz and returning 30 times: level spread 0.03 dB. Setting 0 dB 30 times: 0.01 dB.", "One reading is enough."],
            ["Settling", "After a retune or an attenuation change the level is at its final value within one 5.3 ms sample.", "A 0.1 s wait after each change is ample."],
            ["Flatness", "At 0 dB: +1.2 dBm at 350 MHz falling to &minus;6.3 dBm near 1600 MHz. 1.1 dB spread inside 1.0 to 1.2 GHz.", "Use the per-frequency table, not one number, when a test covers more than one frequency."],
            ["USB, first dropout", "Dropped off USB at 21:26 on 12 Oct, 5 minutes into the first run. Needed the cable replugged.", "Scripts should save each reading as it is taken and be able to resume."],
        ] + N2.learned_rows(N), cls="parts", left=(0, 1, 2))])


def night():
    if not N:
        return ""
    out = [h("Overnight run, 12 to 13 Oct"),
           p(f"Started 21:44 on 12 Oct. Same wiring: Pluto TX straight into the spectrum analyzer. {N['readings']} readings and {N['traces']} saved traces so far (last reading {N['last'].replace('T', ' ')}). "
             "Script <code>overnight.py</code>, readings <code>overnight_readings.csv</code>, traces in <code>traces\\</code>, analysis <code>analyze_overnight.py</code>, numbers <code>overnight_summary.json</code>.")]

    if "low" in N:
        out += [h("Low level: output down to the 89.75 dB setting"), fig("pluto_low_level.png", "Pluto output against attenuation setting from 0 to 89.75 dB at five frequencies"),
                ol(["One analyzer setting cannot cover 0 to &minus;90 dBm. Four were used: reference level +10 dBm; &minus;10 dBm; &minus;30 dBm with the preamp, 1 kHz bandwidth; the same with 100 Hz bandwidth.",
                    "Each setting was read at five attenuation settings shared with the one before. The average difference over those five is the correction that ties it to the one before.",
                    "The +10 dBm setting is used for 0 to 40 dB, the &minus;10 dBm setting to 60 dB, the preamp settings above that."]),
                math(r"c_2 = \overline{P_1(A) - P_2(A)}\ \text{over the shared}\ A \qquad P(A) = P_2(A) + c_2"),
                table(["Frequency (MHz)", "Corrections between settings (dB)", "Largest departure from 1 dB per dB, 20 to 89.75 dB (dB)", "Output at 89.75 dB (dBm)"],
                      [[k, ", ".join(n(x) for x in v["offsets"]), n(v["dep_max_20_to_89"]), n(v["lowest"])] for k, v in N["low"].items()], left=()),
                p("Analyzer noise at the lowest setting (preamp, 100 Hz bandwidth): about &minus;119 dBm, 29 dB under the lowest Pluto level.")]
        k = "1100"
        if k in N["low"]:
            rows = N["low"][k]["table"]
            out += [table(["Setting (dB)", "Output at 1100 MHz (dBm)"], [[n(a, 2 if a % 1 else 0), n(b)] for a, b in rows if a >= 40], cls="lut", left=())]

    if "fine" in N:
        f = N["fine"]
        out += [h("Fine steps: 0.25 dB attenuation steps, 0 to 12 dB"), fig("pluto_fine_steps.png", "Size of each 0.25 dB attenuation step and difference between going up and going down"),
                table(["Frequency (MHz)", "Mean step (dB)", "Smallest (dB)", "Largest (dB)", "Standard deviation (dB)", "Up minus down, largest (dB)"],
                      [[k, n(f[f"{k} down"]["mean"], 3), n(f[f"{k} down"]["min"], 3), n(f[f"{k} down"]["max"], 3), n(f[f"{k} down"]["sd"], 3), n(f[f"{k} updown"]["maxabs"], 3)]
                       for k in ("1000", "1100", "1200") if f"{k} down" in f and f"{k} updown" in f], left=()),
                ul(["Each setting was read going down from 12 to 0 dB, then going up. Analyzer bandwidth 3 kHz, span 200 kHz.",
                    "The steps are uneven: the same pattern appears at all three frequencies and in both directions, so it is the Pluto, not noise.",
                    "Going up and going down agree within 0.02 dB. There is no memory of the direction."])]

    if "scale" in N:
        sc = N["scale"]
        out += [h("Tone scale at five frequencies"), fig("pluto_scale_all.png", "Departure of the output from 20 log10 of the tone scale at five frequencies"),
                table(["Frequency (MHz)", "Attenuation (dB)", "Output at scale 1.0 (dBm)", "Departure at scale 1.0 (dB)", "Departure at scale 0.1 (dB)", "Departure at scale 0.02 (dB)"],
                      [[k.split()[0], k.split()[1][3:], n(v["level_at_1"]), n(v["dep_at_1"]), n(v["dep_at_0p1"]), n(v["dep_at_0p02"])] for k, v in sc.items()], left=()),
                p("Departure = measured level minus the level predicted from the scale 0.5 reading.")]
    if "scale_lines" in N:
        out += [fig("pluto_scale_spectra.png", "Spectrum near the 1100 MHz tone at tone scales 0.1, 0.5, 0.8 and 1.0"),
                table(["Attenuation (dB)", "Tone scale", "Tone (dBm)", "1 MHz below (LO)", "2 MHz below (other sideband)", "4 MHz below", "1 MHz above", "2 MHz above", "Median of trace (noise)"],
                      [[r[0], r[1], n(r[2])] + [n(x, 1) for x in r[3:]] for r in N["scale_lines"] if r[0] == 0], left=()),
                ul(["Levels in dB relative to the tone. Attenuation 0 dB, tone at 1100 MHz, bandwidth 30 kHz.",
                    "The line 4 MHz below the tone grows as the scale goes up: 46 dB under at scale 0.5, 31 dB under at scale 1.0. It is three times the 1 MHz offset on the other side of the LO, which is what the third harmonic of the tone generator's 1 MHz signal produces.",
                    "The other columns stay near the noise of this measurement. The tone offset test below measures the LO leakage and the other sideband with a narrower bandwidth."])]

    if "offset" in N:
        out += [h("Tone offset from the LO"), fig("pluto_offset.png", "Tone level against offset from the LO, and LO leakage and other sideband relative to the tone"),
                table(["Attenuation (dB)", "Offset (MHz)", "Tone (dBm)", "Relative to 1 MHz offset (dB)", "LO leakage (dB rel. tone)", "Other sideband (dB rel. tone)"],
                      [[n(r[0], 0), n(r[1], 1), n(r[2]), n(r[3]), n(r[4], 1), n(r[5], 1)] for r in N["offset"] if r[0] == 0], left=()),
                ul(["LO fixed at 1100 MHz. The tone was moved from 0.1 to 14 MHz above it, and 0.5 to 9 MHz below it. Bandwidth 3 kHz.",
                    "Sample rate 30.72 MS/s, RF bandwidth setting 18 MHz (9 MHz either side). The fall above 8 MHz is that filter.",
                    "LO leakage and other sideband readings at 20 dB attenuation are at the analyzer noise and are not listed."])]

    if "two_tone" in N:
        out += [h("Two tones"), fig("pluto_two_tone.png", "Third-order products of two tones 1 MHz apart against attenuation setting"),
                table(["Frequency (MHz)", "Scale of each tone", "Attenuation (dB)", "Each tone (dBm)", "Larger third-order product (dB rel. one tone)", "LO leakage (dB rel. one tone)"],
                      [[n(r[0], 0), r[1], n(r[2], 0), n(r[3]), n(r[4], 1), n(r[6], 1)] for r in N["two_tone"] if r[0] == 1100], left=()),
                ol(["Tone 1 is 2 MHz above the LO, tone 2 is 3 MHz above. Both the same scale.", "The third-order products fall at 2&times;2 &minus; 3 = 1 MHz and 2&times;3 &minus; 2 = 4 MHz above the LO. Each was read with a 1 kHz bandwidth.",
                    "Products under about &minus;72 dBm are analyzer noise, so the rows at 20 dB attenuation are limits, not levels."]),
                math(r"f_\text{IM3} = 2f_1 - f_2 \quad\text{and}\quad 2f_2 - f_1"),
                p("At 0 dB attenuation the products grow fast with scale (60 dB under at scale 0.1, 30 dB under at scale 0.5). At 5 dB attenuation and scale 0.5 they are 53 dB under. The output stage is the cause.")]

    if "close" in N:
        c = N["close"]
        out += [h("Lines close to the tone, 350 to 2050 MHz"), fig("pluto_close_lines.png", "Lines within 4 MHz of the tone against tone frequency"),
                table(["Line", "Median (dB rel. tone)", "Largest (dB rel. tone)", "At (MHz)"],
                      [[k[5:], n(v["median"], 1), n(v["max"], 1), n(v["at"], 0)] for k, v in c.items() if k.startswith("att0 ")], left=(0,)),
                p("Attenuation 0 dB, tone scale 0.5, bandwidth 30 kHz. All lines except &ldquo;4 MHz below&rdquo; are at the analyzer noise for this bandwidth, so they are limits. The 2100 MHz point is left out: it is at the edge of the analyzer's range.")]

    if "harm" in N:
        hm = N["harm"]
        out += [h("Harmonics"), fig("pluto_harmonics.png", "Harmonics of the tone relative to the tone, against tone frequency"),
                table(["Tone (MHz)", "Tone (dBm)", "Line near 3 &times; LO (dBm)", "Relative to the tone (dB)"],
                      [[n(r[0], 0), n(r[4]), n(r[5]), n(r[6], 1)] for r in hm if r[3] == "near 3 LO" and r[2] == 0 and r[1] == 0.5], left=()),
                ul(["Attenuation 0 dB, tone scale 0.5. The line is at 3 &times; LO &minus; 1 MHz (for a 400 MHz tone: 3 &times; 399 &minus; 1 = 1196 MHz).",
                    "It is 10 to 16 dB under the tone and does not change with the attenuation setting or the tone scale. The Pluto's mixer is driven by a square-wave LO, which has a third harmonic; the same is expected at every LO frequency.",
                    "It can only be seen here for tones up to 700 MHz, because the analyzer stops at 2.1 GHz. For 1.0 to 1.2 GHz tones it falls at 3.0 to 3.6 GHz."]),
                math(r"f_\text{line} = 3 f_\text{LO} - f_\text{offset} = 3\,(f_\text{tone} - 1\ \text{MHz}) - 1\ \text{MHz}"),
                table(["Tone (MHz)", "Tone scale", "2 &times; tone (dB rel. tone)", "3 &times; tone (dB rel. tone)"],
                      [[n(f, 0), s, n(next((r[6] for r in hm if r[0] == f and r[1] == s and r[2] == 0 and r[3] == "2f"), None), 1),
                        n(next((r[6] for r in hm if r[0] == f and r[1] == s and r[2] == 0 and r[3] == "3f"), None), 1)]
                       for s in (0.5, 1.0) for f in sorted({r[0] for r in hm if r[2] == 0 and r[3] == "2f"})], left=()),
                p("Attenuation 0 dB. A dash means the harmonic is above 2.1 GHz or under the analyzer noise.")]
        out += ['<div class="note">Any earlier or later test that measures total power after the Pluto (a power meter, a detector, or an amplifier driven near compression) includes the line near 3 &times; LO. '
                'The LO buffer amp compression test of 12 Oct read the output at the tone frequency only, so its output powers are not affected, but the amp was also amplifying a 3.0 to 3.6 GHz signal about 10 to 16 dB smaller.</div>']

    if "wide" in N:
        out += [h("Wide search, 0 to 2.1 GHz"), fig("pluto_wide.png", "Spectrum from 0 to 2.1 GHz with the tone at five frequencies and with the tone off"),
                table(["Tone (MHz)", "Tone (dBm)", "Largest other line at (MHz)", "Level (dBm)", "Relative to the tone (dB)"],
                      [[n(r[1], 0), n(r[2]), n(r[3], 0), n(r[4], 1), n(r[5], 1)] for r in N["wide"] if r[0] == 0], left=()),
                p("Attenuation 0 dB, bandwidth 100 kHz. For tones of 400 to 700 MHz the largest other line is the one near 3 &times; LO. For tones of 800 MHz and above nothing is above the analyzer noise (about &minus;50 dBm at this bandwidth) below 2.1 GHz; the frequencies listed for those rows are noise peaks.")]

    if "retune" in N:
        r = N["retune"]
        out += [h("Retune and attenuation repeatability"),
                table(["What was repeated", "Readings", "Mean (dBm)", "Spread (dB)", "Standard deviation (dB)"],
                      [["Tune to another frequency (400 to 1900 MHz, random), return to 1100 MHz, 20 dB", r["back"]["n"], n(r["back"]["mean"], 3), n(r["back"]["span"], 3), n(r["back"]["sd"], 3)],
                       ["Set 0 dB (after 20 dB)", r["att0"]["n"], n(r["att0"]["mean"], 3), n(r["att0"]["span"], 3), n(r["att0"]["sd"], 3)],
                       ["Set 40 dB (after 0 dB)", r["att40"]["n"], n(r["att40"]["mean"], 3), n(r["att40"]["span"], 3), n(r["att40"]["sd"], 3)],
                       ["Set 20 dB (after 40 dB)", r["att20"]["n"], n(r["att20"]["mean"], 3), n(r["att20"]["span"], 3), n(r["att20"]["sd"], 3)]], left=(0,)),
                p("The larger spread at 40 dB is analyzer noise: the tone is 31 dB above the noise with this bandwidth (3 kHz) instead of 51 dB or more.")]

    if "settle" in N:
        out += [h("Settling"), fig("pluto_settling.png", "Level at 1100 MHz against time while the Pluto is retuned and while its attenuation is changed"),
                ul([f"Analyzer at 1100 MHz with zero span: it records level against time, one point every {n(N.get('settle_step_ms', 5.3), 1)} ms, bandwidth 300 kHz.",
                    "Left: the Pluto was moved from 900 to 1100 MHz. Right: attenuation changed from 40 to 20 dB. Six repeats each.",
                    "In every repeat the level is within 0.5 dB of its final value at the first point after the change. Settling takes less than one point.",
                    "The delay between sending the command over USB and the change appearing was not measured."])]

    for key, img, sc in (("map", "pluto_map.png", "0.5"), ("map_s1", "pluto_map_scale1.png", "1.0")):
        if key in N:
            m = N[key]
            out += [h(f"Full map, tone scale {sc}"), fig(img, f"Pluto output against frequency at each attenuation setting, tone scale {sc}"),
                    ul([f"{m['n']} readings at {m['freqs']} frequencies" + (" (still running)." if (key == "map" and m["freqs"] < 176) or (key == "map_s1" and m["freqs"] < 71) else "."),
                        f"At 0 dB attenuation: highest {n(m['att0_max'])} dBm at {n(m['att0_max_at'], 0)} MHz, lowest {n(m['att0_min'])} dBm at {n(m['att0_min_at'], 0)} MHz.",
                        f"Inside 1000 to 1200 MHz at 0 dB: {n(m['band_1000_1200'][0])} to {n(m['band_1000_1200'][1])} dBm.",
                        f"Full table: <code>{img[:-4]}_table.csv</code>."])]

    out += [N2.night2(N)]
    out += [h("Readings that are not used"),
            ul(["The spectrum analyzer's range ends at 2.1 GHz. When a sweep was centred at 2100 MHz the analyzer shortened its span without reporting it, and the script kept using the short span for the readings that followed.",
                "Affected: every 2100 MHz point, and the whole first tone-scale-1.0 map (213 readings, block name <code>map_scale1</code> in the readings file). They read &minus;85 to &minus;117 dBm, which is noise.",
                "They are still in <code>overnight_readings.csv</code> but are left out of every table and plot. The script now keeps each sweep inside the analyzer's range and the map is retaken as block <code>map_s1</code>.",
                "Found at 22:45 on 12 Oct by checking the map for values that could not be right."])]
    if "ref" in N:
        rf = N["ref"]
        out += [h("Drift through the night"), fig("pluto_drift.png", "Reference readings, tone frequency error and Pluto temperature against time"),
                table(["Reading", "Number", "First (dBm)", "Mean (dBm)", "Spread (dB)", "Last minus first (dB)"],
                      [[k.replace(" att", " MHz, ") + " dB", v["n"], n(v["first"]), n(v["mean"]), n(v["span"], 3), n(v["last_minus_first"], 3)] for k, v in rf.items() if " att" in k], left=(0,)),
                ul([f"The same six readings were repeated every 10 minutes for {n(rf['hours'], 1)} hours.",
                    f"Tone frequency error at 1100 MHz: {n(rf['freq_ppm']['min'], 2)} to {n(rf['freq_ppm']['max'], 2)} ppm.",
                    f"Pluto chip temperature: {n(rf['temp_c']['min'], 1)} to {n(rf['temp_c']['max'], 1)} &deg;C."])]
        if "drift" in N:
            d = N["drift"]
            out += [p(f"Level at 1100 MHz, 20 dB, read every 30 s: {d['n']} readings, mean {n(d['mean'], 3)} dBm, spread {n(d['span'], 3)} dB, standard deviation {n(d['sd'], 4)} dB.")]
        if "hourly" in N:
            hh = N["hourly"]
            out += [p(f"Hourly repeats ({len(hh['tags'])} so far): the level table (0 to 40 dB at 1000, 1100, 1200 MHz) changed by at most {n(hh['att_table_worst_span_db'], 3)} dB at any setting; "
                      f"the frequency sweep (350 to 2100 MHz at 20 dB) by at most {n(hh['freq_sweep_worst_span_db'], 3)} dB at any frequency.")]
    return "".join(out)
