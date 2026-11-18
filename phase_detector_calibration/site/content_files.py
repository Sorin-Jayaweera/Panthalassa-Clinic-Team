"""File locations tab: every Panthalassa data set, where it lives (inside and outside Dropbox, and on the USB backup), how big it is,
and the bench setup and instrument settings it was taken with. Also written as a standalone FILE_LOCATIONS.html in clinic/claude
so the USB backup carries it. One row per data set in SETS; sizes, dates and per-recording tables are computed at each build."""
import datetime as dt
import html
import os
import sys
from pathlib import Path

from content import item, p, table, ul

HERE = Path(__file__).resolve().parent
CLINIC = HERE.parents[2]
USB = r"E:\Panthalassa_backup"
sys.path[:0] = [str(CLINIC / "claude" / "radar_test" / "racon"), str(HERE.parent)]

PD_CHAIN = ("Pluto TX &rarr; 7 cm &rarr; 4 &times; ZX60-P162LN+ (7 cm between, Agilent E3630A about 4.03 V, 0.23 A) &rarr; 7 cm &rarr; ZFRSC-42-S+ splitter &rarr; "
            "right arm (LO) cable D 15 cm, left arm (RF) cable B 15 cm + C (about 12 cm) or E (about 8 cm) &rarr; ZX05-30W-S+ mixer &rarr; IF to SDS1104X-E CH1 (1 M&Omega;, DC) "
            "and, through 20 dB of pads, the SM200B.")
SM_IQ = "SM200B I/Q streaming, 50 MS/s, 41.5 MHz bandwidth, complex64 with I&sup2;+Q&sup2; = mW at the SM200B input (measured)"

# (tab, title, paths relative to the clinic folder or absolute, setup, instrument settings)
SETS = [
    ("Phase detector", "Delay-line phase detector sweeps 13&ndash;18 Nov (all bench configurations)",
     ["claude/phase_detector_calibration/pd_dither_14nov.csv", "claude/phase_detector_calibration/pd_overnight_13nov.csv", "claude/phase_detector_calibration/pd_cable_13nov_E_pads.csv"],
     PD_CHAIN + " Each configuration (cables, pads, IF cable, IF load) is one row of <code>pd_runs.py</code>, listed below.",
     "Pluto CW 600&ndash;1600 MHz (wide runs 300&ndash;4000 MHz) at &minus;36 to &minus;71 dBm, attenuation never under the 31 dB floor; scope CH1 mean of the IF in mV; tone-off readings as stage <code>off</code>."),
    ("Phase detector", "Amplifier chain alone 18 Nov: frequency sweep and power ramp, with raw I/Q",
     ["claude/phase_detector_calibration/amp_chain_18nov.csv", "claude/phase_detector_calibration/amp_ramp_18nov.csv",
      "claude/phase_detector_calibration/amp_chain", "claude/phase_detector_calibration/amp_ramp"],
     "Pluto TX &rarr; 7 cm &rarr; 4 &times; ZX60-P162LN+ (7 cm between, 4.03&ndash;4.04 V, 0.23 A) &rarr; 10 + 10 + 3 + 6 dB pads (29 dB) &rarr; SM200B. No splitter or mixer.",
     SM_IQ + "; auto attenuation, reference 0 dBm, tone 10 MHz above centre, 16384 samples per point (ramp reps after the first: 4096). "
     "CSV power columns are measured + 29 dB (amp output); <code>sm_in_dbm</code> is measured. Run stops at +10 dBm measured. Gap 14:40&ndash;15:11 (supply unplugged)."),
    ("Phase detector", "First delay-line setup 1 Nov (cables D and B + C, no pads), map, fine, repeats, ramp",
     ["claude/phase_detector_calibration/p162x4_map_1nov.csv", "claude/phase_detector_calibration/p162x4_fine_1nov.csv", "claude/phase_detector_calibration/p162x4_sm200b_1nov.csv",
      "claude/phase_detector_calibration/p162x4_ramp_1nov.csv", "claude/phase_detector_calibration/p162x4_tone_off_watch_1nov.csv"],
     "Same chain as above with cable C (about 12 cm) on the left arm and no pads; amplifiers first on a KUAIQU supply, then the Agilent E3630A at 3.94 V.",
     "Pluto &minus;85 to &minus;30 dBm, 700&ndash;1600 MHz in 5 MHz steps (map) and 1 MHz steps 900&ndash;1200 MHz (fine); scope CH1 mean."),
    ("Phase detector", "VCO-driven detector Oct: step response, deconvolution, noise, clean-DC noise, drift",
     ["claude/phase_detector_calibration/step_response", "claude/phase_detector_calibration/deconvolution", "claude/phase_detector_calibration/noise",
      "claude/phase_detector_calibration/noise_cleanDC", "claude/phase_detector_calibration/drift"],
     "VCO (tuning port driven by the CGR-201 generator or a DC supply) &rarr; delay-line detector &rarr; SDS1104X-E. Script docstrings in each folder give the channel use.",
     "Step: Vt 0.2&ndash;1.15 V, three shots per step. Noise: CH2 AC coupled 1 mV/div, CH3 open as the scope floor, Vt 0.1&ndash;1.1 V."),
    ("Phase detector", "Detector with the Furuno radar 1 Nov (PLL on, PLL off on purpose, and a bad PLL-off run)",
     ["claude/phase_detector_calibration/furuno_detector_1nov_pll_on", "claude/phase_detector_calibration/furuno_detector_1nov_pll_off_deliberate",
      "claude/phase_detector_calibration/BAD_furuno_detector_1nov_pll_off"],
     "Radar received over the air, receive chain to the 1.105 GHz IF, detector output on the scope triggered on the radar.",
     SM_IQ + " at the 1.105 GHz IF and at 21 MHz baseband; SSA3021X sweeps 0.1&ndash;2100 MHz and 0.1&ndash;50 MHz."),
    ("Pluto", "Pluto characterization 12&ndash;13 Oct and overnight runs (levels, spurs, traces)",
     ["claude/pluto_characterization"],
     "Pluto TX straight into the Siglent SSA3021X input; Pluto on USB. Nothing else connected.",
     "Close-in, mid and wide spans at each tone frequency and attenuation; traces saved as CSV in <code>traces/</code>."),
    ("Radar", "Furuno 1722C over the air 25 Oct: pulses, spectra, scans, raw I/Q",
     ["claude/radar_test/pulses_20261025_125851", "claude/radar_test/pulses_20261025_130030", "claude/radar_test/pulses_20261025_130207_dec8",
      "claude/radar_test/pulses_20261025_130555_dec8", "claude/radar_test/pulses_20261025_163002_dec8", "claude/radar_test/pulses_20261025_163509_dec8",
      "claude/radar_test/pulses_20261025_164250_dec8", "claude/radar_test/pulses_20261025_164400_dec8", "claude/radar_test/spectra_20261025_130335",
      "claude/radar_test/scans", "claude/radar_test/raw_20261025_130811.npz", "claude/radar_test/raw_20261025_164428.npz",
      "claude/radar_test/limiter_in_13ft_raw_20261025_164428.npz"],
     "Furuno 1722C/NT (12.1 V, 6.35 A transmitting) with AN-72 foam &rarr; air, 11.3 m &rarr; Vivaldi R120 &rarr; 14 dB of X-band pads &rarr; SM200B. "
     "The 13 ft capture goes through the limiter.",
     SM_IQ + " (the <code>_dec8</code> captures decimated by 8); internal attenuator 30 dB, reference +20 dBm for protection; sweeps 0&ndash;20 GHz."),
    ("Radar", "Receive chain screens 31 Oct and 1 Nov (Spike, scope), Spike exports",
     ["claude/radar_test/spike_screens", "data/Furino Characterization", "claude/data/Furino Characterization"],
     "Vivaldi into the limiter and LNA, load on the limiter, receive mixer IF and LO/RF feedthrough, detector output (tests 29&ndash;43, setups on the Radar tab).",
     "Spike 4.0.17 on the SM200B; Spike's export folder is <code>data\\Furino Characterization</code>."),
    ("Racon", "Racon 9 Nov: every raw I/Q sample (outside Dropbox) and its copy",
     [r"C:\racon_raw", "racon_raw_9nov"],
     "Per-recording setup below (from <code>radar_test/racon/setups_9nov.py</code>): antenna &rarr; SMA cable &rarr; Marki limiter &rarr; 20 dB pad &rarr; ZX60-5123LN+ LNA (6 V, about 23 dB) &rarr; 29 dB of pads &rarr; SM200B.",
     "<code>racon_raw.py</code>: " + SM_IQ + ", centre 9408.5 MHz, interleaved float32 I, Q in <code>iq.c64</code>, every block's sample loss and time in <code>meta.json</code>. "
     "276 GB: too large for the 64 GB USB drive, so only <code>meta.json</code> is on it."),
    ("Racon", "Racon 9 Nov: surveys, segmented captures, pulse statistics",
     ["claude/radar_test/racon/data", "claude/radar_test/racon/raw_meta"],
     "Same chain as the raw recordings; horn aimed at the radar or the racon as listed per recording below.",
     "SM200B sweeps 9&ndash;10 GHz, 18.6&ndash;19.0 GHz and 0.1&ndash;20 GHz at 100 kHz RBW; 250 MS/s segmented captures; I/Q as above."),
    ("VNA", "VNA exports 31 Oct: limiter, ZX05-30W ports, 10 dB pad, Vivaldi S11",
     ["claude/radar_test/vna"], "Each part alone on the HP 8720ES (Vivaldi on port 1, nothing on port 2).", "Markers and calibration as noted on the VNA tab per trace."),
    ("Envelope detector", "ADL5511 envelope detector 26 Oct and 1 Nov (taken on the Mac)",
     ["claude/envelope_detector/data"],
     "Pluto TX &rarr; ADL5511 &rarr; CGR-201 Input A (VENV) and Input B (VRMS). Run from the Mac's Homebrew GNU Radio Python; the copies here are the only ones known on this computer.",
     "CW sweeps at 1.0, 1.1, 1.2 GHz; 10 and 100 us pulses at 1.10 GHz; ripple captures. The 1.00 GHz INTERMITTENT-RF sweep is not to be used."),
    ("VCO", "VCO accuracy 4 Oct, rise time 10 Oct",
     ["claude/measurements/vco", "claude/vco_rise_time/data", "data"],
     "Accuracy: VCO out &rarr; spectrum analyzer. Rise time: CGR-201 square wave &rarr; VCO Vt; scope records the drive and the (aliased) RF.",
     "Rise time: low 0.5 V, high 0.75&ndash;3 V in 0.25 V steps, 50 kHz square wave, deep single-shot records."),
    ("LO buffer", "LO buffer amplifier ZX60-14012L-S+ gain 12 Oct", ["claude/lo_buffer_test"],
     "Run A: source straight to the analyzer; run B: through the amplifier.", "Attenuator stepped; level read on the analyzer."),
    ("Other", "Second oscilloscope captures 12 Nov (USB 0x049F:0x505E)", ["claude/chaos_scope"],
     "Two-channel captures read over VISA (<code>grab.py</code>); BAD_ folders are known-bad readouts.", "400 k points, 125 kS/s, 0.2 s/div, 1 V/div; settings in each <code>*_settings.json</code>."),
    ("Other", "ADF5355 synthesizer screens, simulations, documentation evidence, CAD photos",
     ["claude/adf5355", "claude/simulations", "claude/documentation", "claude/cad"], "See the matching tab.", "&mdash;"),
    ("Records", "This site, its backups, the notes, and the code",
     ["claude/docs", "claude/site_backups", "claude/phase_detector_calibration/site", "claude/JACON_notes_backup.html", "claude/radar_test/user_messages_log.md", "backups"],
     "<code>docs/index.html</code> is the published site (GitHub Pages); <code>site_backups</code> keeps dated copies; all code lives next to its data.", "&mdash;"),
]


def full(rel):
    return Path(rel) if Path(rel).is_absolute() else CLINIC / rel


def stats(q):
    """(files, bytes, first date, last date) for a file or a folder tree."""
    fs = [q] if q.is_file() else [Path(r) / f for r, _, n in os.walk(q) for f in n] if q.exists() else []
    if not fs:
        return 0, 0, "", ""
    st = [f.stat() for f in fs]
    t = sorted(s.st_mtime for s in st)
    day = lambda x: dt.datetime.fromtimestamp(x).strftime("%d %b %Y")
    return len(fs), sum(s.st_size for s in st), day(t[0]), day(t[-1])


def size(b):
    return f"{b / 1e9:.1f} GB" if b > 1e9 else f"{b / 1e6:.1f} MB"


def loc_rows(paths):
    rows = []
    for rel in paths:
        q = full(rel)
        n, b, a, z = stats(q)
        usb = "only meta.json" if str(q).startswith(r"C:\racon_raw") else "no (copy of C:\\racon_raw)" if "racon_raw_9nov" in rel else f"{USB}\\clinic\\{rel.replace('/', chr(92))}"
        rows.append([f"<code>{html.escape(str(q))}</code>", str(n), size(b), f"{a} &ndash; {z}" if a != z else a, f"<code>{html.escape(usb)}</code>" if usb[0] == "E" else usb])
    return rows


def extras(title):
    """Per-recording tables computed from the run tables, so they never go stale."""
    try:
        if title.startswith("Racon 9 Nov: every raw"):
            import setups_9nov as S
            return [table(["Recording (C:\\racon_raw\\...)", "Setup", "Chain after the antenna", "SM200B reference (dBm)"],
                          [[k, html.escape(v["LABEL"]), " &rarr; ".join(html.escape(c[0].replace("\n", " ")) for c in v["CHAIN"]), str(S.REF_DBM.get(k, ""))]
                           for k, v in S.SETUPS.items() if k[:4] == "2026"])]
        if title.startswith("Delay-line"):
            import pd_runs as R
            return [table(["Run tag", "Day", "Configuration"], [[r["tag"], r["day"], html.escape(r["desc"])] for r in R.RUNS])]
    except Exception as e:          # a run table that fails to import must not break the site
        return [p(f"(run table not read: {html.escape(str(e))})")]
    return []


def sections():
    return [item(f"files-{i}", f"{tab}: {title}", p("<b>Setup:</b> " + setup), p("<b>Instrument settings:</b> " + sett),
                 table(["Location on this computer", "Files", "Size", "Dates", "USB backup"], loc_rows(paths)), *extras(title))
            for i, (tab, title, paths, setup, sett) in enumerate(SETS)]


INTRO = [p("Every Panthalassa data set: where it is on the clinic computer, where its copy is on the USB backup drive, how big it is, and the bench setup and instrument settings it was taken with. "
           "Sizes and dates are read from the disk at each build of this site. Everything is inside the Dropbox clinic folder "
           "<code>C:\\ThatFamily Dropbox\\Sorin Jayaweera\\allSaves\\mudd\\senior\\clinic</code> except the raw racon recordings in <code>C:\\racon_raw</code>."),
         ul([f"USB backup: <code>{USB}</code>, made by <code>clinic\\claude\\backup_to_usb.ps1</code> (re-run any time; it adds and updates, never deletes). "
             "It holds the whole clinic folder except the 276 GB raw racon recordings, which need a drive of 512 GB or more.",
             "This list is also saved as <code>clinic\\claude\\FILE_LOCATIONS.html</code> (one file, opens in any browser) and copied to the USB drive.",
             "Power columns in the CSVs say whether they are measured at the instrument or measured plus the pads (for example measured + 29 dB)."])]


def tab():
    return "<h2>File locations</h2>" + "".join(INTRO) + "".join(sections())


def standalone():
    page = (f"<!doctype html><meta charset='utf-8'><title>Panthalassa file locations</title><style>body{{font:14px sans-serif;max-width:1200px;margin:auto;padding:16px}}"
            f"table{{border-collapse:collapse}}td,th{{border:1px solid #bbb;padding:3px 6px;text-align:left;vertical-align:top}}code{{font-size:12px}}</style>"
            f"<p>Written {dt.datetime.now():%d %b %Y %H:%M}.</p>" + tab().replace("<details", "<details open"))
    (CLINIC / "claude" / "FILE_LOCATIONS.html").write_text(page, encoding="utf-8")
