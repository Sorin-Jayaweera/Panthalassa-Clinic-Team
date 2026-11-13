"""Racon tab: the SeaBeacon 2 racon answering the Furuno, recorded over the air on 9 Nov 2026. Numbers are read from
radar_test/racon/data/racon_stats_summary.csv (written by radar_test/racon/racon_stats.py) when the site is built."""
import csv
import json
import shutil
from pathlib import Path

from content import item, table, ul, p, h, fig

HERE = Path(__file__).resolve().parent
RAC = HERE.parent.parent / "radar_test" / "racon"
PL, DA = RAC / "plots", RAC / "data"
REPO_PLOTS = "https://github.com/Sorin-Jayaweera/Panthalassa-Clinic-Team/blob/main/radar_test/racon/plots/"

SHOW = ["racon_fig6_iq_time", "racon_fig1_durations", "racon_fig2_edges", "racon_fig3_frequency", "racon_fig4_levels", "racon_fig5_short_block",
        "stats_20261109_215716_stack_envelope", "stats_20261109_215716_morse_timing_long", "stats_20261109_215716_morse_timing_short",
        "stats_20261109_215716_table", "stats_20261109_215716_stack_freq", "stats_20261109_215716_freq", "stats_20261109_215716_bursts",
        "stats_20261109_215716_vs_time", "stats_20261109_215716_edges", "stats_20261109_215716_stack_radar",
        "stats_seg_horn_racon_250M_stack_envelope", "stats_seg_horn_racon_250M_edges", "stats_20261109_214452_stack_envelope",
        "stats_20261109_214452_morse_timing_long", "racon_all_compare", "racon_all_hist", "racon_all_tracking", "radar_all_9nov",
        "sweeps_9to10", "sweeps_harm2", "sweeps_wide"]
ALLP = sorted(q.stem for q in PL.glob("*.png") if q.stem.startswith(("stats_", "racon_", "radar_all", "sweeps_")))
for n in sorted(set(SHOW) | set(ALLP)):
    if (PL / f"{n}.png").exists():
        shutil.copy2(PL / f"{n}.png", HERE / "img" / f"{n}.png")


def F(n, alt):
    return fig(f"{n}.png", alt) if (HERE / "img" / f"{n}.png").exists() else p(f"<i>{n}.png not made yet</i>")


def _summ():
    out = {}
    try:
        for r in csv.DictReader(open(DA / "racon_stats_summary.csv", encoding="utf-8")):
            out.setdefault(r["recording"], {})[r["quantity"]] = r
    except FileNotFoundError:
        pass
    return out


S = _summ()


def v(rec, q, k="mean", nd=3):
    try:
        return f"{float(S[rec][q][k]):.{nd}f}"
    except KeyError:
        return "?"


Q = [("delay, radar start to dot 1 start", "us"), ("dot 1", "us"), ("gap 1", "us"), ("dash", "us"), ("gap 2", "us"), ("dot 2", "us"),
     ("whole R, dot 1 start to dot 2 end", "us"), ("dot 1 start to dash start", "us"), ("dash start to dot 2 start", "us"),
     ("dot 1 freq minus radar", "MHz"), ("dash freq minus radar", "MHz"), ("dot 2 freq minus radar", "MHz"),
     ("drift dot 1 to dot 2", "MHz"), ("chirp inside dot 1", "MHz/us"), ("chirp inside the dash", "MHz/us"), ("radar pulse, half power", "us")]


def stat_table(rec):
    rows = [[q, u, v(rec, q, "n", 0), v(rec, q), v(rec, q, "sd"), v(rec, q, "p5"), v(rec, q, "median"), v(rec, q, "p95")] for q, u in Q]
    return table(["", "unit", "N", "mean", "sd", "5 %", "median", "95 %"], rows, cls="parts")


def rec_table():
    try:
        codes = json.loads((DA / "racon_stats_codes.json").read_text())
    except FileNotFoundError:
        codes = {}
    import setups_racon_view as SV
    rows = []
    for rec, label, ref, ant in SV.RECS:
        n_long = v(f"{rec} long", "dash", "n", 0)
        n_short = v(f"{rec} short", "dash", "n", 0)
        c = codes.get(rec, {})
        top = ", ".join(f"{k} {n}" for k, n in sorted(c.items(), key=lambda kv: -kv[1])[:3]) or "none"
        rows.append([rec, ant, f"{ref} dBm", label, n_long, n_short, top])
    return table(["recording", "antenna", "ref level", "conditions", "long R", "short R", "most common element patterns"], rows, cls="parts",
                 left=(0, 1, 3, 6))


def freq_table():
    try:
        rows = list(csv.DictReader(open(DA / "racon_freq_offset.csv", encoding="utf-8")))
    except FileNotFoundError:
        return p("<i>racon_freq_offset.csv not made yet</i>")
    f = lambda x, sg=True: f"{float(x):+.2f}" if sg else f"{float(x):.2f}"  # noqa: E731
    return table(["element", "replies", "N", "peak (MHz)", "median (MHz)", "mean (MHz)", "sd (MHz)", "5 % (MHz)", "95 % (MHz)"],
                 [[r["element"] + (" minus Furuno" if r["element"] in ("dash", "dot 1", "dot 2") else ""), r["group"], r["n"], f(r["peak"]), f(r["median"]),
                   f(r["mean"]), f(r["sd"], False), f(r["p5"]), f(r["p95"])] for r in rows], cls="parts", left=(0, 1))


try:
    FO = next({k: f"{float(v):+.2f}" for k, v in r.items() if k in ("peak",)} for r in csv.DictReader(open(DA / "racon_freq_offset.csv", encoding="utf-8"))
              if r["element"] == "dash" and r["group"] == "all")
except (FileNotFoundError, StopIteration):
    FO = {}


KIND = [("stack_envelope", "Envelope of every reply, stacked"), ("stack_freq", "Instantaneous frequency and spectrum of every reply, stacked"),
        ("freq", "Element frequency, drift and chirp"), ("bursts", "Busiest bursts, reply by reply"),
        ("morse_timing_long", "Long R timing histograms"), ("morse_timing_short", "Short R timing histograms"),
        ("vs_time", "Delay, lengths and frequency through the recording"), ("edges", "Averaged edges"), ("table", "Statistics table"),
        ("stack_radar", "Furuno pulses, stacked")]


def other_names():
    """Plots not already shown in another section of this tab."""
    import re
    shown = set(re.findall(r'F\("([^"]+)"', Path(__file__).read_text(encoding="utf-8")))
    return [n for n in ALLP if n not in shown]


def other_plots():
    import setups_racon_view as SV
    left = set(other_names())
    out = [p("Every plot not already shown above, one group per recording, frequency plots first. "
             "Recordings where the racon was off or not picked up only have the Furuno pulse plot.")]
    for rec, label, ref, ant in SV.RECS:
        names = [(f"stats_{rec}_{k}", t) for k, t in KIND if f"stats_{rec}_{k}" in left]
        if names:
            out.append(h(f"{rec}: {ant}, {label}"))
            out += [F(n, f"{t}, {rec}") for n, t in names]
            left -= {n for n, _ in names}
    if left:
        out.append(h("Other"))
        out += [F(n, n) for n in sorted(left)]
    return "".join(out)


def build():
    L, Sh = "ALL long", "ALL short"
    return "".join([
        "<h2>Racon</h2>",
        '<p class="sub">SeaBeacon 2 racon answering the Furuno 1722C/NT, received over the air with the SM200B on 9 Nov 2026. '
        "This is the reply the JACON has to copy: Morse R, its timing, its frequency and its edges. Every plot shows the wiring it was taken with.</p>",
        item("rac-summary", "Summary",
             '<p style="font-size:15px"><b><a href="https://sorin-jayaweera.github.io/Panthalassa-Clinic-Team/racon_iq/">Interactive raw I/Q viewer: the whole 250 MS/s horn recording</a></b> (every sample of all 2671 snippets; zoom on a selection, pan, step reply by reply, jump to the Furuno pulse).</p>',
             ul([f"<b>Frequency relative to the Furuno: dash minus Furuno peak {FO.get('peak', '?')}, median {v('ALL', 'dash freq minus radar', 'median', 2)}, mean {v('ALL', 'dash freq minus radar', 'mean', 2)}, sd {v('ALL', 'dash freq minus radar', 'sd', 2)} MHz;</b> "
                 f"5-95 % {v('ALL', 'dash freq minus radar', 'p5', 1)} to {v('ALL', 'dash freq minus radar', 'p95', 1)} MHz. The racon picks a new frequency for each reply and does not follow "
                 "the radar from pulse to pulse.",
                 f"<b>Inside a reply it climbs steadily:</b> dot 2 is {v('ALL', 'drift dot 1 to dot 2', 'median', 2)} MHz above dot 1 "
                 f"(sd {v('ALL', 'drift dot 1 to dot 2', 'sd', 2)}), a chirp of about {v('ALL', 'chirp inside the dash', 'median', 3)} MHz/us in the dash and faster in dot 1.",
                 f"<b>Morse R (dot dash dot) after every radar pulse it hears.</b> {v(L, 'dash', 'n', 0)} long and {v(Sh, 'dash', 'n', 0)} short complete replies measured.",
                 f"<b>Two versions.</b> Long R: dot {v(L, 'dot 1', 'median', 2)} us, gap {v(L, 'gap 1', 'median', 2)} us, dash {v(L, 'dash', 'median', 2)} us, "
                 f"whole reply {v(L, 'whole R, dot 1 start to dot 2 end', 'median', 2)} us. Short R: everything about 0.75 times as long "
                 f"(dot {v(Sh, 'dot 1', 'median', 2)}, gap {v(Sh, 'gap 1', 'median', 2)}, dash {v(Sh, 'dash', 'median', 2)}, whole {v(Sh, 'whole R, dot 1 start to dot 2 end', 'median', 2)} us). "
                 "About one reply in five is short; the short ones come in one block per pass of the radar beam (see below).",
                 f"<b>Timing is crystal-steady.</b> Long R gaps and dash vary by about {v(L, 'gap 2', 'sd', 3)} and {v(L, 'dash', 'sd', 3)} us (1 sd), "
                 "a few nanoseconds once the rare faded replies are left out (see the histograms).",
                 f"<b>Delay jitters.</b> Dot 1 starts {v(L, 'delay, radar start to dot 1 start', 'median', 2)} us after the radar pulse starts (long R; "
                 f"5-95 % {v(L, 'delay, radar start to dot 1 start', 'p5', 2)} to {v(L, 'delay, radar start to dot 1 start', 'p95', 2)} us). "
                 f"Short R start earlier and steadier ({v(Sh, 'delay, radar start to dot 1 start', 'median', 2)} us).",
                 "<b>Edges are fast:</b> about 30 ns 10-90 % at 250 MS/s (160 MHz bandwidth), close to what the SM200B itself can show. "
                 "The radar pulse edges read about 55 ns.",
                 "<b>Level:</b> about &minus;52 dBm at the SM200B with the horn 7 m from the racon (chain gain &minus;27.8 dB, so about &minus;24 dBm at the horn port). "
                 "The horn gain is not known yet, so no racon EIRP is given."]), open_=True),
        item("rac-freq", "Frequency: racon reply minus the Furuno pulse",
             F("racon_fig0_freq_offset", "Racon minus Furuno frequency: dash, dots, drift, long and short R, per recording, with peak, median, mean and sd"),
             freq_table(),
             p("Each element's frequency is the phase slope over its middle 80 %; the Furuno pulse's frequency is measured the same way in the same snippet, "
               "so the offset does not depend on the SM200B's tuning. Peak = mode of a 0.1 MHz histogram smoothed over 0.5 MHz. "
               "Table: <code>radar_test/racon/data/racon_freq_offset.csv</code>."),
             F("racon_fig3_frequency", "Offset, drift and chirp histograms; racon against Furuno frequency"),
             F("racon_fig6_iq_time", "I and Q against time, one long R and one short R (250 MS/s): whole reply as recorded, whole reply referenced to the Furuno frequency, the whole Furuno pulse as recorded and referenced to its own frequency, and 1 us of the dash"),
             '<p style="font-size:15px"><b><a href="https://sorin-jayaweera.github.io/Panthalassa-Clinic-Team/racon_iq/">Interactive raw I/Q viewer: the whole 250 MS/s horn recording</a></b> (every sample of all 2671 snippets; zoom on a selection, pan, step reply by reply, jump to the Furuno pulse).</p>',
             p("In the Furuno-referenced row the I/Q rotation rate is the racon-minus-Furuno offset: the long R dash makes about 25 turns in 25.7 us (+0.95 MHz). "
               "Script <code>radar_test/racon/racon_iq.py</code>; plotted samples in <code>radar_test/racon/data/racon_iq_examples.csv</code>."),
             F("stats_20261109_215716_stack_freq", "Instantaneous frequency and spectrum of every reply, stacked"),
             F("stats_20261109_215716_freq", "Horn recording: element frequency, drift and chirp"),
             F("stats_20261109_215716_bursts", "Three bursts reply by reply: Furuno and racon frequency, offset, delay"),
             F("racon_all_tracking", "Racon frequency against Furuno frequency, all recordings")),
        item("rac-timing", "Timing: Morse element lengths, gaps and delay",
             F("racon_fig1_durations", "Every Morse duration, long and short R, all recordings"),
             F("stats_20261109_215716_stack_envelope", "Every full R reply stacked, lined up on the radar and on dot 1, plus normalised overlays"),
             F("stats_20261109_214452_stack_envelope", "Same for the long Vivaldi recording"),
             F("stats_seg_horn_racon_250M_stack_envelope", "Same at 250 MS/s"),
             F("stats_20261109_215716_morse_timing_long", "Long R timing histograms, horn recording"),
             F("stats_20261109_215716_morse_timing_short", "Short R timing histograms, horn recording"),
             F("stats_20261109_214452_morse_timing_long", "Long R timing, Vivaldi recording"),
             F("stats_20261109_215716_vs_time", "Delay, element lengths and frequencies through the 3 minute recording"),
             F("stats_20261109_215716_table", "Table of statistics, horn recording")),
        item("rac-short", "Short R: 0.75x timing, sent as one 18-reply block per Furuno beam pass",
             F("racon_fig5_short_block", "Long and short R timing, every burst with its short block, and how the short block differs"),
             ul(["The gap that cuts into the dash in the stacked plots is the <b>short R</b>. It is the same Morse R played 0.75 times as long, "
                 "so it is over by 45 us while the long R is still in its dash.",
                 "It is not random. It comes as <b>one solid block of about 18 replies in a row (about 28 ms)</b> once per burst, at a different place in each burst, "
                 "and then a few stray short replies 5 to 15 replies later. Every block is in <code>radar_test/racon/data/racon_short_blocks.csv</code>.",
                 "28 ms is about 3.9 degrees of the radar's 2.59 s turn, roughly the width of the radar's main beam. Inside the block the racon answers sooner "
                 "(1.34 us, very steady, against 1.72 us with a wide spread) and the radar reads about 7 dB stronger at the SM200B. "
                 "Both point the same way: <b>the short R is the answer to the radar's main beam, and the long R is the answer to its sidelobes</b>. "
                 "The racon is only 15 m from the radar, so the sidelobes are strong enough to trigger it all round the turn.",
                 "Not proven: the radar level is measured at the SM200B, not at the racon, and the radar's beamwidth has not been measured. "
                 "The stray short replies after the block may be a near sidelobe. The SeaBeacon manual may say whether it shortens its code on strong interrogations."])),
        item("rac-edges", "Edges: 10-90 % rise and fall times",
             F("racon_fig2_edges", "Averaged edges of the Furuno pulse and every racon element; 10-90 % per recording"),
             F("stats_seg_horn_racon_250M_edges", "Averaged edges at 250 MS/s"),
             F("stats_20261109_215716_edges", "Averaged edges at 50 MS/s"),
             p("Single replies are too noisy at 250 MS/s to time an edge, so every reply is lined up on its own half-power crossing and averaged. "
               "The short spike right at each racon edge in the average may be a real turn-on/turn-off transient or a side effect of lining up on a noisy crossing; not yet decided.")),
        item("rac-levels", "Levels at the SM200B",
             F("racon_fig4_levels", "Racon level per recording, dots against the dash, Furuno level")),
        item("rac-stats", "Statistics tables, all recordings pooled",
             h("Long R"), stat_table(L), h("Short R"), stat_table(Sh),
             p("N = complete replies (exactly dot, dash, dot with dot 4-15 us and dash 18-35 us). Edges at half of each element's own power, interpolated between samples. "
               "Frequencies from the phase slope over the middle 80 % of each element; chirp from a quadratic phase fit. "
               "The full table, per recording and per version: <code>radar_test/racon/data/racon_stats_summary.csv</code>; every reply: <code>data/stats_&lt;recording&gt;_replies.csv</code>.")),
        item("rac-all", "Recording-to-recording comparison",
             F("racon_all_compare", "Mean and spread of every quantity per recording"),
             F("racon_all_hist", "Pooled histograms, stacked by recording"),
             F("racon_all_tracking", "Racon frequency against radar frequency, all recordings"),
             rec_table()),
        item("rac-radar", "Furuno pulses in these recordings",
             F("stats_20261109_215716_stack_radar", "Every radar pulse stacked, its spectrum, and an overlay"),
             F("radar_all_9nov", "Radar pulse length, frequency and level in every recording")),
        item("rac-sweeps", "Sweeps 0.1-20 GHz; Furuno 2nd harmonic",
             F("sweeps_9to10", "9-10 GHz sweeps, horn at the radar and at the racon"),
             F("sweeps_harm2", "18.6-19.0 GHz sweeps: the radar's 2nd harmonic"),
             F("sweeps_wide", "0.1-20 GHz sweeps"),
             ul(["Horn at the radar, both on: strongest line 9403.7 MHz, &minus;38.6 dBm at the SM200B (swept, so it reads lower than the I/Q peak).",
                 "<b>2nd harmonic seen: 18806.8 MHz, &minus;63.0 dBm at the SM200B</b> with the horn on the radar, exactly twice the radar frequency. "
                 "Not seen (below &minus;87 dBm) with the horn on the racon. The chain's loss at 18.8 GHz is not known (LNA, limiter, horn), so this is not yet a level at the antenna.",
                 "0.1-20 GHz: besides the radar only 1855 MHz and 2.4-2.56 GHz lines (phones, Wi-Fi). The wide sweep is slow and misses most short pulses, "
                 "which is why the harmonic is not in it.",
                 "The 3rd harmonic (28.2 GHz) is above the SM200B's 20 GHz."])),
        item("rac-where", "Data locations (full paths)",
             table(["what", "where"], [
                 ["Raw I/Q, every sample, 9 Nov (complex64, 50 MS/s, 41.5 MHz wide, centre 9408.5 MHz), one folder per recording with iq.c64 + meta.json; NOTES.txt = conditions log",
                  "<code>C:&#92;racon_raw&#92;</code> (275.9 GB, recording computer)"],
                 ["Backup of the raw I/Q in Dropbox (complete copy, checked: 24 files, 0 failed)",
                  "<code>C:&#92;ThatFamily Dropbox&#92;Sorin Jayaweera&#92;allSaves&#92;mudd&#92;senior&#92;clinic&#92;racon_raw_9nov&#92;</code>"],
                 ["Cut-out pulses and replies (raw_&lt;recording&gt;.npz), per-reply CSVs (stats_&lt;recording&gt;_replies.csv), radar CSVs, summary tables, short-block list, edge times",
                  "<code>C:&#92;ThatFamily Dropbox&#92;Sorin Jayaweera&#92;allSaves&#92;mudd&#92;senior&#92;clinic&#92;claude&#92;radar_test&#92;racon&#92;data&#92;</code>"],
                 ["250 MS/s segmented captures (c00-c10.npz)",
                  "<code>...&#92;claude&#92;radar_test&#92;racon&#92;data&#92;seg_horn_racon_250M_20261109_222441&#92;</code>"],
                 ["Sweeps 9-10 GHz, 18.6-19.0 GHz, 0.1-20 GHz",
                  "<code>...&#92;claude&#92;radar_test&#92;racon&#92;data&#92;survey_horn_radar_*</code> and <code>survey_horn_racon_*</code>"],
                 ["Every plot", "<code>C:&#92;ThatFamily Dropbox&#92;Sorin Jayaweera&#92;allSaves&#92;mudd&#92;senior&#92;clinic&#92;claude&#92;radar_test&#92;racon&#92;plots&#92;</code>"],
                 ["Recording settings copied from each meta.json", "<code>...&#92;claude&#92;radar_test&#92;racon&#92;raw_meta&#92;</code>"],
                 ["Scripts: racon_stats.py (statistics and per-recording plots), racon_figs.py (one-figure-per-idea plots), setups_9nov.py (wiring per recording)",
                  "<code>...&#92;claude&#92;radar_test&#92;racon&#92;</code>"],
             ], cls="parts", left=(0, 1)),
             p("Everything under <code>claude&#92;</code> except the raw I/Q is also in the GitHub repository at the same relative path."), open_=False),
        item("rac-other", f"Other plots, by recording ({len(other_names())})", other_plots()),
        item("rac-files", "Scripts and recording files",
             ul(["Raw I/Q, every sample: <code>C:\\racon_raw\\&lt;time&gt;\\iq.c64</code> (complex64, 50 MS/s, 41.5 MHz wide, centre 9408.5 MHz) with <code>meta.json</code>; "
                 "about 282 GB, backed up to Dropbox. Conditions log: <code>NOTES.txt</code> there.",
                 "<code>radar_test/racon/</code> in the repository: <code>racon_raw.py</code> (recorder), <code>raw_to_snips.py</code> (cuts each pulse and reply out), "
                 "<code>racon_analyze.py</code> (first pass), <code>racon_stats.py</code> (these statistics and plots), <code>setups_9nov.py</code> (wiring and distances of each recording), "
                 "<code>racon_capture.py</code> (sweeps and 250 MS/s segmented captures).",
                 f"Every plot for every recording: <a href=\"{REPO_PLOTS}\">radar_test/racon/plots</a>.",
                 "Assumed, not measured: horn gain (15 dBi used where needed), Vivaldi gain (8 dBi), SMA cable loss (1 dB), LNA gain (23 dB)."])),
    ])


RACON = build()
