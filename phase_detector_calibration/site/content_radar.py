"""Radar tab: the Furuno radar measured over the air with the SM200B, 25 Oct 2026."""
import csv
from pathlib import Path

from content import item, table, ul, ol, p, h, math, fig, D
from content_radar_tests import POWER

_RT = Path(__file__).resolve().parent.parent.parent / "radar_test"


def _csv(name):
    rows = list(csv.reader(open(_RT / name, encoding="utf-8")))
    return table(rows[0], rows[1:], cls="parts", left=tuple(range(len(rows[0]))))


def _md(text):
    """Render radar_test/test_log.md (headings, tables, numbered and bulleted lists, **bold**, `code`)."""
    import html as _h
    import re

    def inline(t):
        t = _h.escape(t, quote=False)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", t)

    out, rows, lst = [], [], None

    def flush():
        nonlocal rows, lst
        if rows:
            out.append(table([inline(c) for c in rows[0]], [[inline(c) for c in r] for r in rows[2:]], cls="parts", left=tuple(range(len(rows[0])))))
            rows = []
        if lst:
            out.append((ol if lst[0] == "ol" else ul)([inline(i) for i in lst[1]]))
            lst = None

    for line in text.splitlines():
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        m = re.match(r"(\d+\.|-) (.*)", line)
        if m:
            kind = "ol" if m.group(1)[0].isdigit() else "ul"
            if rows or (lst and lst[0] != kind):
                flush()
            lst = lst or (kind, [])
            lst[1].append(m.group(2))
            continue
        flush()
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            out.append(h(inline(line[3:])))
        elif line.strip():
            out.append(p(inline(line)))
    flush()
    return "".join(out)

SETUP = """<pre class="diagram">
 Furuno 1722C/NT radar, NavNet, 12.1 V 6.35 A          long-range pulse (LP), 24 nm range
 AN-72 absorber foam over the radome face
          ~~~ 11.3 m (37 ft) of air, room with walls ~~~
 Vivaldi R120 antenna (5-13 GHz), facing the radar
          |  long SMA cable
 JFW 50DR-046 manual attenuator, set to 0 dB     (rated DC-2.5 GHz: not counted at 9.4 GHz)
          |
 10 dB fixed attenuator (8 GHz)  +  2 dB (8 GHz)  +  2 dB (8 GHz)   = 14 dB counted
          |
 Signal Hound SM200B, +20 dBm max input, internal attenuator 30 dB, reference level +20 dBm
</pre>"""

RADAR = "".join([
    "<h2>Radar</h2>",
    '<p class="sub">Furuno 1722C/NT X-band radar (NavNet VX1, 2.2 kW peak, 18 in radome) received over the air by a Vivaldi antenna and the Signal Hound SM200B, 25 Oct 2026. '
    "What the racon's limiter, LNA and mixer will be given.</p>",
    POWER,
    item("rad-pads", "Attenuator pads on the VNA: the 3, 6 and 10 dB &ldquo;8G&rdquo; pads",
         p("Agilent 8720ES, 85052D kit (3.5 mm), full 2-port cal: 50 MHz&ndash;20.05 GHz, 801 points, IF BW 1 kHz, &minus;10 dBm. Cal REG26 was made with the first cable; recalibrated with the better cable for the sweeps below. All values in dB. Copy-paste version: <code>radar_test/vna/pad_measurements.csv</code>. "
           "<b>3 dB pad, sweep 3 (marker readings, better cable, recalibrated; use these):</b>"),
         table(["Frequency", "S21 (loss)", "S12", "S11 (in match)", "S22 (out match)"], [
             ["50 MHz", "&minus;2.943 dB", "&minus;2.932 dB", "&minus;49.61 dB", "&minus;48.01 dB"],
             ["8.008 GHz", "&minus;3.505 dB", "&minus;3.707 dB", "&minus;20.20 dB", "&minus;23.12 dB"],
             ["9.400 GHz (radar band)", "<b>&minus;3.608 dB</b>", "<b>&minus;3.939 dB</b>", "&minus;19.88 dB", "&minus;15.20 dB"],
             ["10.000 GHz", "&minus;3.564 dB", "&minus;3.749 dB", "&minus;16.46 dB", "&minus;16.68 dB"],
             ["20.048 GHz", "&minus;5.369 dB", "&minus;5.085 dB", "&minus;6.86 dB", "&minus;8.84 dB"]]),
         ul(["<b>At 9.4 GHz the &ldquo;3 dB&rdquo; pad loses 3.6&ndash;3.9 dB, about 0.6&ndash;0.9 dB more than its label.</b> It is rated only to 8 GHz.",
             "S21 and S12 differ by 0.33 dB at 9.4 GHz. A passive pad is reciprocal, so that difference is measurement error, and it sets the uncertainty of these numbers.",
             "The cable mattered: the same pad read 4.18 dB at 9.5 GHz on the first cable (sweep 2) and 3.6 dB at 9.4 GHz on this one.",
             "Sweep 1 showed an S21 notch to &minus;10 dB and an S22 spike to ~0 dB near 5.7 GHz. That is more power out than in (|S21|&sup2; + |S22|&sup2; &gt; 1), so it was not the pad; it is gone in sweeps 2 and 3. Sweep 1 readings were by eye and are superseded."]),
         h("3 dB pad, sweep 3, better cable, markers"),
         fig("vna_pad3dB_sweep3_S21_markers.png", "8720ES: S21 of the 3 dB pad, better cable"),
         fig("vna_pad3dB_sweep3_S12_markers.png", "8720ES: S12 of the 3 dB pad, better cable"),
         fig("vna_pad3dB_sweep3_S11_markers.png", "8720ES: S11 of the 3 dB pad, better cable"),
         fig("vna_pad3dB_sweep3_S22_markers.png", "8720ES: S22 of the 3 dB pad, better cable"),
         h("6 dB pad (better cable, recalibrated)"),
         table(["Frequency", "S21 (loss)", "S12", "S11 (in match)", "S22 (out match)"], [
             ["50 MHz", "&minus;5.868 dB", "&minus;5.927 dB", "&minus;48.46 dB", "&minus;53.90 dB"],
             ["8.008 GHz", "&minus;6.136 dB", "&minus;6.191 dB", "&minus;29.12 dB", "&minus;18.69 dB"],
             ["9.400 GHz (radar band)", "<b>&minus;6.223 dB</b>", "<b>&minus;6.107 dB</b>", "&minus;27.02 dB", "&minus;13.48 dB"],
             ["10.000 GHz", "&minus;6.025 dB", "&minus;5.982 dB", "&minus;23.13 dB", "&minus;12.37 dB"],
             ["20.048 GHz", "&minus;5.044 dB", "&minus;4.895 dB", "&minus;11.15 dB", "&minus;14.57 dB"]]),
         fig("vna_pad6dB_S21_markers.png", "8720ES: S21 of the 6 dB pad"),
         fig("vna_pad6dB_S12_markers.png", "8720ES: S12 of the 6 dB pad"),
         fig("vna_pad6dB_S11_markers.png", "8720ES: S11 of the 6 dB pad"),
         fig("vna_pad6dB_S22_markers.png", "8720ES: S22 of the 6 dB pad"),
         h("10 dB pad: relative readings only, to be retaken"),
         p("These screens were in delta-marker mode (&Delta;REF=&Delta;), so the numbers below are relative to a fixed reference marker, not absolute dB. Differences within one column are valid. "
           "The reference value is not on the screens. Fitting the photos suggests about &minus;14.6 dB (the last 6 dB pad S22 reading), which would put S21 near &minus;10.7 and S12 near &minus;11.3 dB at 9.4 GHz, but that is an estimate. "
           "S21 and S12 then differ by a nearly constant 0.5&ndash;0.8 dB, including at 50 MHz, so do not use these as loss values."),
         table(["Marker", "Frequency", "S21 rel.", "S12 rel.", "S11 rel.", "S22 rel."], [
             ["1", "50 MHz", "+4.053", "+3.379", "&minus;32.330", "&minus;39.862"],
             ["4", "8.008 GHz", "+3.964", "+3.200", "&minus;14.947", "&minus;3.639"],
             ["2", "9.400 GHz", "+3.830", "+3.307", "&minus;12.749", "+1.643"],
             ["3", "10.000 GHz", "+3.871", "+3.290", "&minus;11.743", "+2.962"],
             ["5", "20.048 GHz", "+5.553", "+4.896", "&minus;0.074", "&minus;11.365"]]),
         fig("vna_pad10dB_delta_S21.png", "8720ES: S21 of the 10 dB pad, delta markers"),
         fig("vna_pad10dB_delta_S12.png", "8720ES: S12 of the 10 dB pad, delta markers"),
         fig("vna_pad10dB_delta_S11.png", "8720ES: S11 of the 10 dB pad, delta markers"),
         fig("vna_pad10dB_delta_S22.png", "8720ES: S22 of the 10 dB pad, delta markers"),
         h("3 dB pad, sweep 2, first cable, markers (superseded)"),
         table(["Frequency", "S21", "S12", "S11", "S22"], [
             ["50 MHz", "&minus;3.035 dB", "&minus;3.013 dB", "&minus;56.19 dB", "&minus;49.58 dB"],
             ["880 MHz", "&minus;3.116 dB", "&minus;3.065 dB", "&minus;34.95 dB", "&minus;35.91 dB"],
             ["9.502 GHz", "&minus;4.179 dB", "&minus;4.277 dB", "&minus;16.89 dB", "&minus;14.10 dB"],
             ["10.284 GHz", "&minus;4.450 dB", "&minus;4.322 dB", "&minus;14.58 dB", "&minus;18.73 dB"],
             ["20.05 GHz", "&minus;5.185 dB", "&minus;5.079 dB", "&minus;7.01 dB", "&minus;9.60 dB"]]),
         fig("vna_pad3dB_sweep2_S21_markers.png", "8720ES: S21 of the 3 dB pad with markers, first cable"),
         fig("vna_pad3dB_sweep2_S12_markers.png", "8720ES: S12 of the 3 dB pad with markers, first cable"),
         fig("vna_pad3dB_sweep2_S11_markers.png", "8720ES: S11 of the 3 dB pad with markers, first cable"),
         fig("vna_pad3dB_sweep2_S22_markers.png", "8720ES: S22 of the 3 dB pad with markers, first cable"),
         h("3 dB pad, sweep 1, glitch near 5.7 GHz (superseded)"),
         fig("vna_pad3dB_S21_10dBdiv.png", "8720ES: S21 of the 3 dB pad, 10 dB/div, sweep 1"),
         fig("vna_pad3dB_S12_10dBdiv.png", "8720ES: S12 of the 3 dB pad, 10 dB/div, sweep 1"),
         fig("vna_pad3dB_S11_10dBdiv.png", "8720ES: S11 of the 3 dB pad, 10 dB/div, sweep 1"),
         fig("vna_pad3dB_S22_10dBdiv.png", "8720ES: S22 of the 3 dB pad, 10 dB/div, sweep 1"),
         p("Original photos: <code>radar_test/vna/</code>.")),
    item("rad-vivaldi-s11", "Vivaldi antenna S11 on the VNA",
         p("Vivaldi on port 1 of the 8720ES, nothing on port 2. Delta markers off, cal not interpolated (C2 on screen). Turning the antenna around changed the earlier trace only slightly. <b>Use these numbers:</b>"),
         table(["Marker", "Frequency", "S11", "Power reflected", "Mismatch loss"], [
             ["1", "50 MHz", "+0.051 dB", "all (below the antenna&rsquo;s band)", "&ndash;"],
             ["4", "8.008 GHz", "&minus;10.557 dB", "8.8%", "0.40 dB"],
             ["2", "9.400 GHz (radar band)", "<b>&minus;14.184 dB</b>", "3.8%", "0.17 dB"],
             ["3", "10.000 GHz", "&minus;11.728 dB", "6.7%", "0.30 dB"],
             ["5", "20.046 GHz", "&minus;3.103 dB", "49%", "2.9 dB"]]),
         ul(["At 9.4 GHz the antenna is well matched: only 0.17 dB is lost to reflection. This is match only, not gain or pattern.",
             "By eye from the trace, not markers: about &minus;6 to &minus;7 dB near 6&ndash;7.5 GHz and about &minus;4 dB near 12 GHz, so the match is poorer than &minus;10 dB over parts of the rated 5&ndash;13 GHz."]),
         fig("vna_vivaldi_S11_absolute.png", "8720ES: Vivaldi S11, absolute markers"),
         h("First look, superseded (relative delta-marker readings)"),
         p("The rough estimate of about &minus;9 dB at 9.4 GHz made from these photos was wrong; the marker above reads &minus;14.2 dB."),
         p("Screens were in delta-marker mode, so the values are relative to a fixed marker, in dB; the marker's value is not on the screen."),
         table(["Marker", "Frequency", "Photo 1 (C2, cal points)", "Photo 2 (C2&Delta;, 1601 points, interpolated)"], [
             ["1", "50 MHz", "+13.436", "+13.436"],
             ["4", "8.008 GHz", "+6.268", "+5.705"],
             ["2", "9.400 GHz", "+5.243", "+8.770"],
             ["3", "10.000 GHz", "+6.920", "+5.543"],
             ["5", "20.048 GHz", "+8.732", "+8.688"]]),
         ul(["Photo 2: going to 1601 points without recalibrating turned on interpolated correction (C2&Delta;). The fuzz on the trace, and the 3.5 dB jump at 9.4 GHz, are probably from that, not the antenna. Use photo 1 until a 1601-point cal is done."]),
         fig("vna_vivaldi_S11_delta_cal_points.png", "8720ES: Vivaldi S11, cal points, delta markers"),
         fig("vna_vivaldi_S11_delta_1601pts_interpolated.png", "8720ES: Vivaldi S11, 1601 points, interpolated cal"),
         p("Originals and raw values: <code>radar_test/vna/</code>.")),
    item("rad-log", "Test log: all tests as one table (25 and 26 Oct)",
         _md(open(_RT / "test_log.md", encoding="utf-8").read()),
         h("Spike screens, 26 Oct at 11.5 m (3 MHz RBW, Min/Max, Max Hold)"),
         p("Test 25b: 50 &Omega; load &rarr; 29 dB pads, whiteboard out. The leak floor: &minus;31.2 dBm."),
         fig("spike_test25b_leak_floor_50ohm_load_29dB_11p5m.png", "Spike: leak floor with a 50 ohm load, -31.2 dBm"),
         p("Test 27: Vivaldi &rarr; limiter &rarr; 20 dB &rarr; LNA on &rarr; 19 dB. &minus;7.94 dBm, 16 dB above the &minus;24.06 dBm floor of the same chain with a load (26c)."),
         fig("spike_test27_vivaldi_limiter_20dB_LNA_on_19dB_11p5m.png", "Spike: Vivaldi, limiter, LNA on, -7.94 dBm"),
         p("Test 28: same, LNA off. &minus;25.85 dBm."),
         fig("spike_test28_vivaldi_limiter_20dB_LNA_off_19dB_11p5m.png", "Spike: Vivaldi, limiter, LNA off, -25.85 dBm"),
         p("Test 29 (31 Oct): same pads as test 27 (Vivaldi &rarr; limiter &rarr; 10+10 &rarr; LNA &rarr; 10+6+3). &minus;19.12 dBm at 9.408594 GHz, 11.2 dB below test 27 and only 4.9 dB above the 25 Oct floor of this chain, so leak may be a large part of it. Cause of the drop not known; no load control taken yet."),
         fig("spike_test29_vivaldi_limiter_20dB_LNA_19dB_31oct.png", "Spike: Vivaldi, limiter, LNA, -19.12 dBm"),
         p("Full log: <code>radar_test/test_log.md</code>. Every instruction Sorin gave during the tests: <code>radar_test/user_messages_log.md</code>.")),
    item("rad-tables", "Power and timing tables (CSV)",
         h("Power"), _csv("radar_power_table.csv"),
         ul(["Whiteboard in: the Vivaldi faced the radar but no wideband reading was taken. The value is the measured whiteboard-out peak lowered by the 3.3 dB difference between the two 100 kHz Spike readings (&minus;44.0 and &minus;40.7 dBm). The manual attenuator also moved from 50 to 0 dB between those readings.",
             "EIRP assumes 8 dBi for the Vivaldi at 9.4 GHz (not measured). Each dB the real gain differs moves the EIRP by the same dB the other way.",
             "To predict the peak at another distance d (m) with a receive antenna of gain G (dBi): P = EIRP + G &minus; 51.91 &minus; 20 log10(d)."]),
         h("Signal"), _csv("radar_signal_table.csv"),
         p("Copy-paste versions: <code>radar_test/radar_power_table.csv</code> and <code>radar_test/radar_signal_table.csv</code>."),
         p("<b>Caution:</b> the 26 Oct leak tests (log tests 16&ndash;26) show the radar reaches the SM200B directly at about &minus;20 to &minus;31 dBm. Power readings with 29 dB pads that are within 20 dB of that (tests 7&ndash;18) are partly leakage.")),
    item("rad-spike", "Spike max-hold exports, 100 kHz and 3 MHz RBW",
         fig("furuno_spike_maxhold_9370-9430MHz_rbw100kHz_vs_3MHz_11m_14dB_pads.png", "Spike max-hold spectra of the radar at 100 kHz and 3 MHz RBW, with markers"),
         ul(["Sorin's exports from Spike: <code>data/Furino Characterization/14db8G_11meters_100khzrbw.csv</code> and <code>14db8G_11meters_3mhzrbw.csv</code>. Plot made by <code>radar_test/plot_spike_exports.py</code>.",
             "Setup: Vivaldi at 11.3 m facing the radar, AN-72 foam on the radar, whiteboard out, 14 dB of 8 GHz pads, manual attenuator at 0 dB.",
             "100 kHz RBW: peak &minus;44.7 dBm at 9403.008 MHz, &minus;3 dB width 1.27 MHz. Sidelobes on the high side at +2.05, +3.47, +5.20, +6.62 MHz: &minus;10.0, &minus;14.6, &minus;17.1, &minus;19.3 dB. Their spacing (about 1.5 MHz) gives a pulse width of about 0.68 &micro;s.",
             "3 MHz RBW: peak &minus;20.5 dBm (9.0 &micro;W) at 9403.594 MHz. This filter is wide enough to hold the pulse, so this is close to the true pulse peak and agrees with the I/Q measurement (&minus;22 dBm).",
             "The 24.2 dB difference between the two peaks is the narrow filter missing most of the pulse's energy, not a change in the radar."])),
    item("rad-design", "What the front end must handle", table(["Quantity", "Measured", "Design for", "Notes"], [
        ["Carrier frequency", "9402.62 MHz median (9402.41 to 9402.80, 5th to 95th percentile of 705 pulses)", "9380 to 9440 MHz", "Furuno specifies 9410 &plusmn;30 MHz. Another unit of the same model can sit anywhere in that band."],
        ["Pulse-to-pulse frequency change", "74 kHz standard deviation within one beam pass", "&lt; 0.5 MHz", ""],
        ["Frequency change inside one pulse", "about &minus;0.15 MHz/&micro;s (about 0.1 MHz over the pulse)", "negligible", "No second tone, no oscillation inside the pulse."],
        ["Pulse width, long pulse", "680 ns median (630 to 700 ns) at half power", "0.08 to 0.8 &micro;s", "Only the long pulse (24 nm range) was measured. Shorter ranges use shorter pulses, down to about 0.08 &micro;s; not measured."],
        ["Rise time, 10 to 90 % amplitude", "40 ns median (20 to 120 ns)", "design for 20 ns", "Measured to one 20 ns sample; the true edge may be faster."],
        ["Fall time, 90 to 10 % amplitude", "80 ns median (60 to 170 ns)", "", ""],
        ["Pulse top", "flat; 1.0 to 1.7 dB ripple", "", "A clean switched carrier."],
        ["Occupied bandwidth, long pulse", "1.30 MHz at &minus;3 dB, 2.20 MHz at &minus;10 dB, 7.8 MHz at &minus;20 dB", "IF bandwidth &ge; 8 MHz for the long pulse, &ge; 25 MHz for the short pulse", "First sidelobes &minus;17 dB (low side) and &minus;11 dB (high side): lopsided, typical of a magnetron."],
        ["Time between pulses", "16 values from 1606.5 to 1706.5 &micro;s in 6.67 &micro;s steps, mean 1655 &micro;s", "do not assume a fixed interval", "Staggered on purpose. Mean rate 604 pulses/s at this range. Shorter ranges use higher rates; not measured."],
        ["Fraction of time on", "0.041 % (680 ns / 1655 &micro;s)", "", "Average power is 34 dB below peak."],
        ["Rotation", "2.5885 s (23.18 rpm)", "", "From the autocorrelation of 30 s of received power."],
        ["Main beam passing the antenna", "&minus;3 dB over 16&deg; here (about 115 ms, about 70 pulses)", "5.2&deg; (37 ms, about 22 pulses) in open space", "Broadened by room reflections at 11.3 m (the far field starts at about 13 m)."],
        ["Second harmonic, 18.805 GHz", "not detected; under &minus;41.7 dBm at the SM200B while the fundamental was &minus;22 dBm", "", "So at least 20 dB down in this measurement. The limit is the measurement, not the radar."],
        ["Peak power received here", "&minus;22 dBm at the SM200B; at least &minus;8 dBm at the Vivaldi output", "see the table below", "Through AN-72 foam, at 11.3 m. Cable and manual attenuator loss at 9.4 GHz not yet measured, so the true antenna output is somewhat higher."]],
        cls="parts", left=(0, 1, 2, 3)),
        h("Peak power at the racon antenna against distance"),
        table(["Distance to the radar", "Peak at a 12.5 dBi horn (dBm)", "Peak (mW)"],
              [["10 m", "+28", "630"], ["30 m", "+18.5", "70"], ["100 m", "+8", "6.3"], ["300 m", "&minus;1.5", "0.7"], ["1 km", "&minus;12", "0.063"], ["3 km", "&minus;21.5", "0.007"], ["10 km", "&minus;32", "0.0006"]], left=()),
        math(r"P_r = \underbrace{63.4 + 24}_{\text{EIRP, dBm}} + G_r - 20\log_{10}\!\left(\frac{4\pi d}{\lambda}\right), \qquad \lambda = 3.19\ \text{cm}"),
        ul(["63.4 dBm = 2.2 kW peak. 24 dBi = the radar antenna gain implied by its 5.2&deg; &times; 25&deg; beam. G<sub>r</sub> = 12.5 dBi for the racon horn.",
            "Main beam, line of sight, no foam. These are design values; the measurement here was through foam and is about 30 dB lower than this formula gives for 11.3 m and a 10 dBi antenna.",
            "Average power at any distance is 34 dB below the peak in the table.",
            "The limiter must take the closest-approach peak (+28 dBm at 10 m) and keep the LNA input under its +15 dBm limit; the limiter's spike leakage on a 20 ns edge is what to check."])),
    item("rad-plots-pulse", "One pulse: shape, I and Q, frequency inside the pulse",
         fig("radar_one_pulse.png", "The strongest pulse: power, amplitude, I and Q, and instantaneous frequency"),
         ul(["Top left: power, one sample every 20 ns. Half-power width 660 ns.", "Top right: amplitude. Rise and fall 80 ns between 10 % and 90 % here.",
             "Bottom left: I and Q after removing the carrier. Both are smooth through the pulse: the carrier is clean; the slow change in Q is a small frequency offset and drift.",
             "Bottom right: the instantaneous frequency across the flat top, within about 1 MHz of the carrier."]),
         fig("radar_pulse_spectrogram.png", "Spectrogram inside one pulse"),
         p("A 0.32 &micro;s sliding FFT through the pulse. One frequency throughout; energy spreads only at the switching edges.")),
    item("rad-plots-fft", "FFT of a pulse, with bandwidth markers",
         fig("radar_fft_pulse.png", "FFT of single pulses with -3, -10 and -20 dB bandwidth markers and the ideal rectangular-pulse spectrum"),
         ul(["Each FFT covers 2 &micro;s around one pulse. Orange: power average of the 23 pulses within 3 dB of the strongest. Dotted: an ideal 660 ns rectangular pulse.",
             "Bandwidth 1.30 MHz at &minus;3 dB, 2.20 MHz at &minus;10 dB, 7.8 MHz at &minus;20 dB.",
             "The nulls are where the ideal pulse puts them (multiples of 1/660 ns = 1.52 MHz); the sidelobes are uneven, which a small frequency drift inside the pulse causes."])),
    item("rad-plots-train", "Pulse train and waterfall",
         fig("radar_train_spectrogram.png", "60 ms of one beam pass with the time between each pair of pulses, and a waterfall of each pulse's spectrum"),
         ul(["Top: 60 ms of the strongest beam pass. Purple numbers are the time between pulses in &micro;s.",
             "Bottom: one row per pulse, each row that pulse's spectrum. Every pulse is at the same frequency (red dots: mean &minus;0.103 MHz from 9402.6 MHz, 74 kHz standard deviation).",
             "The dip in strength in the middle of the pass is the beam's shape plus room reflections."])),
    item("rad-plots-pri", "Time between pulses",
         fig("radar_pri.png", "Histogram of the time between pulses and the first 150 intervals in order"),
         p("Over 9,900 intervals: 16 values from 1606.5 to 1706.5 &micro;s, 6.67 &micro;s apart, used about equally and mixed in a repeating order. A racon cannot predict the next pulse from the last interval.")),
    item("rad-plots-rot", "Rotation and the beam as seen from the Vivaldi",
         fig("radar_timeline.png", "Pulse peaks over 30 s and the autocorrelation that gives the rotation period"),
         fig("radar_beam.png", "Received pulse peak against radar antenna angle, all rotations folded"),
         ul(["Rotation 2.5885 s (23.18 rpm), from 30 s of every pulse with no samples lost.",
             "Main beam &minus;22.2 dBm. Half a turn away (&minus;166&deg;) there is a second response 10.6 dB lower: the back of the antenna or a reflection off the room behind the Vivaldi. Other bumps at &plusmn;50&deg; and +120&deg; are reflections.",
             "The &minus;3 dB width here (16&deg;) is wider than the 5.2&deg; specification because of reflections and the short distance."])),
    item("rad-plots-stats", "Pulse statistics", fig("radar_pulse_stats.png", "Histograms of pulse width, rise time, fall time and carrier frequency"),
         p("From 30 s at 50 MS/s: the 152 pulses within 3 dB of the strongest for the edge figures; 705 pulses above &minus;30 dBm for frequency.")),
    item("rad-plots-swept", "Swept spectra, 0 to 20 GHz", fig("radar_spectra_swept.png", "Max-hold swept spectra at several spans and resolution bandwidths"),
         ul(["Swept max hold at several spans, 12 to 30 s each. Nothing found from 5 to 9 GHz, 10.8 to 13 GHz, or near 18.8 GHz above the sweep noise (about &minus;48 to &minus;54 dBm with a 3 MHz RBW).",
             "A swept analyzer only catches a pulse when the sweep and the beam line up, so peak levels on these plots read low and differ from scan to scan. Use the I/Q measurements above for power."])),
    item("rad-setup", "Setup and safety",
         SETUP,
         ul(["SM200B damage limit +20 dBm. Worst case before the test, with only the 14 dB of fixed pads counted, the radar's main beam on a 10 dBi antenna at 11.3 m: +10.4 dBm at the SM200B, 9.6 dB under the limit.",
             "The manual attenuator was not counted: JFW rates it DC to 2.5 GHz. Setting it from 50 dB to 0 dB changed the reading by only about 3 dB, confirming it does little at 9.4 GHz.",
             "Changes were made one at a time with a reading between: Vivaldi pointed away (&minus;38.8 dBm in 10 MHz RBW), turned to face the radar, whiteboard removed and manual attenuator to 0 dB (&minus;21.5 dBm in Spike, 3 MHz RBW). Highest pulse peak at the SM200B in all captures: &minus;21.6 dBm, 41.6 dB under the limit.",
             "Radar supply: 12.1 V, 6.35 A (77 W) transmitting; 4.64 A in standby. Antenna does not turn in standby.",
             "SM200B internal temperature 24 &deg;C at switch-on, 49 &deg;C after an hour; Spike showed 47 to 48 &deg;C."])),
    item("rad-files", "Files and how the numbers were made",
         ul(["Folder <code>radar_test/</code> in the repository.",
             "<code>sm200b_scan.py</code>, <code>sm200b_monitor.py</code>: swept scans and the safety monitor used during setup.",
             "<code>radar_pulses.py</code>: I/Q streaming. 50 MS/s (one sample every 20 ns, 41.5 MHz bandwidth) for pulse shape; 6.25 MS/s for 30 s timing captures that keep up with no lost samples. Finds every pulse 15 dB above the noise and records time, peak, width, rise, fall, carrier frequency and chirp. Output folders <code>pulses_*</code>.",
             "<code>capture_raw.py</code>: 60 ms of raw I/Q around the strongest beam pass, <code>raw_*.npz</code>.",
             "<code>plot_raw.py</code>, <code>plot_stats.py</code>: the plots on this tab, written to <code>radar_test/plots/</code>. <code>radar_spectra.py</code>: the swept spectra.",
             "Rotation: autocorrelation of the received power, 1 ms bins, refined over four turns. Beam plot: time folded modulo the rotation period. Carrier frequency: mean phase step between samples on the flat top of each pulse.",
             "Power is |I + jQ|&sup2; of the SM200B's corrected 32-bit I/Q, which is in mW at its input."])),
])
