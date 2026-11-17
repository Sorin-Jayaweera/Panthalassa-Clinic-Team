"""Data sets that had no section on the site (audit of 16 Nov 2026). For each one: what it is, how it was taken (the docstring
of the script that took it), where the files live (local path, and whether they are on GitHub), and every plot made from it.
Appended to the end of the matching tab by build_site.py. Plots are copied into site/img with the folder name as a prefix."""
import ast
import html
import re
import shutil
import subprocess
from pathlib import Path

from content import fig, item, p, table, ul

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                  # clinic/claude
IMG = HERE / "img"
DATA_EXT = (".csv", ".npz", ".npy", ".json", ".s2p", ".s1p")

try:
    TRACKED = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.splitlines())
except Exception:          # no git: say so on the page instead of failing the build
    TRACKED = set()
ON_SITE = "".join(q.read_text(encoding="utf-8", errors="ignore") for q in HERE.glob("content*.py") if q.name != "content_data_index.py")     + (HERE / "build_site.py").read_text(encoding="utf-8", errors="ignore")


def _esc(t):
    return html.escape(t, quote=False)


def _docstring(script):
    try:
        d = ast.get_docstring(ast.parse(script.read_text(encoding="utf-8", errors="ignore")))
    except SyntaxError:
        d = None
    return d.strip() if d else None


def _scripts_for(folder, names):
    """Python files under clinic/claude that mention the folder name or one of the data file stems."""
    keys = ({folder.name} if folder.name not in ("phase_detector_calibration", "radar_test", "data", "pluto_characterization", "racon") else set()) | {re.sub(r"_?\d{8}_\d{6}.*", "", Path(n).stem) for n in names}
    keys = {k for k in keys if len(k) >= 6}
    out = []
    for py in list(folder.glob("*.py")) + list(folder.parent.glob("*.py")) + list(folder.parent.parent.glob("*.py")):
        if py.name.startswith("_patch") or "site" in py.parts:
            continue
        txt = py.read_text(encoding="utf-8", errors="ignore")
        if any(k in txt for k in keys):
            out.append(py)
    seen, res = set(), []
    for s in out:
        if s.resolve() not in seen:
            seen.add(s.resolve())
            res.append(s)
    return res[:3]


def _caption(name):
    s = Path(name).stem.replace("_", " ")
    s = re.sub(r"(\d{4})(\d{2})(\d{2}) (\d{2})(\d{2})(\d{2})", r"\1-\2-\3 \4:\5:\6", s)
    return s


def dataset(iid, title, folder, what, how=None, pngs=None, files=None, extra=()):
    """One section. folder is relative to clinic/claude. pngs/files: glob patterns inside the folder (recursive)."""
    F = ROOT / folder
    files = sorted({q for pat in (files or ["**/*"]) for q in F.glob(pat) if q.is_file() and q.suffix.lower() in DATA_EXT})
    pngs = sorted({q for pat in (pngs or ["**/*.png", "**/*.jpg", "**/*.webp"]) for q in F.glob(pat) if q.is_file() and q.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and ('"' + q.name) not in ON_SITE})
    rel = lambda q: q.relative_to(ROOT).as_posix()
    n_git = sum(rel(q) in TRACKED for q in files)
    size = sum(q.stat().st_size for q in files) / 1e6
    body = [p(what)]
    if how:
        body.append(p("How it was taken: " + how))
    scripts = _scripts_for(F, [q.name for q in files])
    for s in scripts:
        d = _docstring(s)
        if d:
            body.append(p(f"Script <code>{_esc(rel(s))}</code> says:") + f"<pre>{_esc(d[:1500])}</pre>")
    loc = (f"Local folder: <code>C:\\ThatFamily Dropbox\\Sorin Jayaweera\\allSaves\\mudd\\senior\\clinic\\claude\\{folder.replace('/', chr(92))}</code>. "
           f"{len(files)} data files, {size:.1f} MB; {n_git} of them on GitHub (<code>{_esc(folder)}/</code> in the Panthalassa-Clinic-Team repository)"
           + ("." if n_git == len(files) else "; the rest are too large for GitHub and stay on the clinic computer (Dropbox)."))
    body.append(p(loc))
    if files:
        rows = [[f"<code>{_esc(q.relative_to(F).as_posix())}</code>", f"{q.stat().st_size / 1e3:.0f} kB", "yes" if rel(q) in TRACKED else "no"] for q in files[:60]]
        body.append(table(["File", "Size", "On GitHub"], rows))
        if len(files) > 60:
            body.append(p(f"&hellip; and {len(files) - 60} more files in the same folder."))
    body.extend(extra)
    IMG.mkdir(exist_ok=True)
    for q in pngs:
        tag = re.sub(r"[^A-Za-z0-9]+", "_", q.relative_to(ROOT).parent.as_posix()).strip("_")
        out = f"{tag}__{q.name}"
        dst = IMG / out
        if not dst.exists() or dst.stat().st_mtime < q.stat().st_mtime:
            shutil.copy2(q, dst)
        body.append(p(f"<b>{_esc(_caption(q.name))}</b> &mdash; <code>{_esc(rel(q))}</code>") + f'<figure><a href="img/{out}"><img loading="lazy" src="img/{out}" alt="{_esc(_caption(q.name))}"></a></figure>')
    if not pngs:
        body.append(p("No plot existed for this data yet."))
    return item(iid, title, *body)


def _tab(*items):
    return ("<h3>More data sets (added 16 Nov after an audit of the clinic folder)</h3>"
            + p("Every data set found in the clinic folder that did not yet have a section on this tab. Each lists how it was taken, where the files are, and every plot made from it.")
            + "".join(items))


def tabs():
    T = {}
    T["tab-mixer"] = _tab(
        dataset("dx-pd-step", "Phase detector step response (10 Oct): VCO tuning stepped between two voltages, detector output against time",
                "phase_detector_calibration/step_response",
                "The VCO tuning voltage was stepped between a low and a high value (0.2 to 1.15 V) and the phase detector output was captured on the scope, three shots per step. "
                "The plots show the mean trace per step, rise and fall, the time to settle within 2 MHz, and the transition time against voltage."),
        dataset("dx-pd-deconv", "Phase detector step response, deconvolved (10 Oct)", "phase_detector_calibration/deconvolution",
                "Transfer function and deconvolved step response worked out from the step-response captures above."),
        dataset("dx-pd-noise", "Phase detector output noise at each VCO tuning voltage (Oct)", "phase_detector_calibration/noise",
                "Scope captures of the detector output with the VCO held at fixed tuning voltages 0.1 to 1.1 V, plus two diagnostic captures at 0.6 V. noise_summary.csv has the rms at each voltage."),
        dataset("dx-pd-noise-clean", "Phase detector output noise, clean DC supply (Oct)", "phase_detector_calibration/noise_cleanDC",
                "Same noise measurement repeated with a clean DC supply for the tuning voltage."),
        dataset("dx-pd-drift", "Phase detector drift passes (Oct)", "phase_detector_calibration/drift",
                "Repeated passes over the same tuning voltages to see how the detector reading drifts with time."),
        dataset("dx-pd-furuno-on", "Phase detector with the Furuno radar, PLL on (1 Nov)", "phase_detector_calibration/furuno_detector_1nov_pll_on",
                "Detector output shots triggered on the radar, I/Q at the 1.105 GHz IF and at 21 MHz baseband (SM200B), and spectrum analyzer sweeps 0.1&ndash;2100 MHz and 0.1&ndash;50 MHz."),
        dataset("dx-pd-furuno-off", "Phase detector with the Furuno radar, PLL off on purpose (1 Nov)", "phase_detector_calibration/furuno_detector_1nov_pll_off_deliberate",
                "The same I/Q captures with the PLL switched off deliberately, for comparison."),
        dataset("dx-pd-early", "Early phase detector calibration files (Sept&ndash;Oct and 1 Nov)", "phase_detector_calibration",
                "Older calibration and exploration files in the phase detector folder that had no section: the first calibration (0.05 V and 0.02 V tuning steps), the Pluto calibration at &minus;36 dBm, the 1 Nov Pluto exploration, the 13 Nov baseline and cable-E coarse sweeps, the SM200B reading on 13 Nov, and the partial open-tee stub test.",
                pngs=["phase_detector_calibration*.png", "pluto_explore*.png", "pluto_calibration_1nov*.png", "partial_open_tee*.png", "pd_cable_13nov*.png", "pd_kitty*.png"],
                files=["phase_detector_calibration*.csv", "pluto_calibration_1nov*.csv", "pluto_explore_1nov.csv", "pd_cable_13nov*", "pd_kitty_13nov*", "partial_open_tee*", "BAD_amps_off*"]),
        dataset("dx-pd-first", "First phase detector test by hand (16 Sept)", "data",
                "The first phase detector readings, typed in by hand.", pngs=["Phase*.png"], files=["Phase Detector Test*"]),
    )
    T["tab-env"] = _tab(dataset("dx-env", "Envelope detector bench data (26 Oct and 1 Nov): sweeps, band edges, ripple and pulses", "envelope_detector/data",
                                "ADL5511 envelope detector on the bench: level sweeps at 1.0, 1.1 and 1.2 GHz, 10 us and 100 us pulses at 1.10 GHz, ripple captures, and band edges. "
                                "The 1.00 GHz sweep marked INTERMITTENT-RF is not to be used. Procedure and results: <code>envelope_detector/ED-TEST-PROCEDURE.md</code>, <code>ED-TEST-RESULTS.md</code>."))
    T["tab-vco"] = _tab(
        dataset("dx-vco-acc", "VCO absolute accuracy (4 Oct)", "measurements/vco",
                "Frequency of the VCO at each tuning voltage against the value expected, raw and corrected for the spectrum analyzer reading."),
        dataset("dx-vco-hand", "VCO tests typed in by hand (4 Oct)", "data", "Hand-entered VCO absolute accuracy readings (source of the table above).", pngs=["VCO*.png"], files=["VCO tests*"]),
        dataset("dx-vco-rise", "VCO rise time captures and static tuning (10 Oct)", "vco_rise_time/data",
                "Tuning-voltage steps from 0.75&ndash;3 V with the VCO output through a frequency discriminator on the scope, several shots per step; the static tuning curve; and two exploratory steps.",
                pngs=["**/*.png"]),
    )
    T["tab-radar"] = _tab(
        dataset("dx-radar-scans", "Radar test 25 Oct: spectrum scans (baseline and with the radar on)", "radar_test/scans",
                "Wide (0&ndash;20 GHz) and X-band spectrum scans with the radar off (baseline) and on (look), and the last monitor reading."),
        dataset("dx-radar-spectra", "Radar test 25 Oct: spectra around the radar pulse", "radar_test/spectra_20261025_130335",
                "Spectra from 0&ndash;20 GHz, 5&ndash;9 GHz, 9&ndash;10.8 GHz, 10.8&ndash;13 GHz, the pulse at 9.37&ndash;9.44 GHz at three RBWs, and the second harmonic at 18.7&ndash;18.9 GHz."),
        dataset("dx-radar-pulses", "Radar test 25 Oct: captured pulses (eight captures)", "radar_test",
                "Each capture folder holds the pulse list, a 10 us envelope and short I/Q snippets around each pulse; one has the beam profile. Also the monitor logs and the 13 ft raw capture through the limiter.",
                pngs=["pulses_2026*/*.png"], files=["pulses_2026*/*", "monitor_2026*.csv", "raw_2026*.npz", "limiter_in_13ft*"]),
        dataset("dx-radar-screens", "Scope and spectrum analyzer screens, 31 Oct and 1 Nov (receive chain tests 29&ndash;43)", "radar_test/spike_screens",
                "Screenshots and exported traces from the receive-chain bench tests: Vivaldi into the limiter and LNA, load on the limiter, the receive mixer IF and LO/RF feedthrough, and the detector output."),
    )
    T["tab-racon"] = _tab(
        dataset("dx-racon-plots", "Racon 9 Nov: every analysis plot (per capture, per segment, the sweeps and the summary figures)", "radar_test/racon",
                "All plots made from the 9 Nov racon session that were not yet on this tab: per-capture chain, loudness, replies, stats and timeline; the stacked statistics; the band sweeps (9&ndash;10 GHz, second harmonic, wide); "
                "the summary figures (frequency offset, durations, edges, levels, short block, I/Q against time); and the synthetic-data checks. The raw recordings (.npz, several GB) stay on the clinic computer; the interactive I/Q viewer is at racon_iq/.",
                pngs=["plots/*.png"], files=["data/*.json", "data/*.csv", "raw_meta/*.json"]),
    )
    T["tab-vna"] = _tab(
        dataset("dx-vna", "VNA exports (31 Oct): limiter S-parameters, ZX05-30W mixer port isolation, 10 dB pad, Vivaldi S11", "radar_test/vna",
                "Traces exported from the VNA: limiter S-parameters and the raw change, the ZX05-30W-S+ mixer LO&ndash;RF, LO&ndash;IF and IF&ndash;RF isolation, the 10 dB pad, the Vivaldi S11, and the SSA3021X IF direct reading."),
    )
    T["tab-pluto"] = _tab(
        dataset("dx-pluto-traces", "Pluto: every saved spectrum trace and the remaining plots (12&ndash;13 Oct)", "pluto_characterization",
                "Spectrum analyzer traces saved during the Pluto characterization (close-in, mid and wide spans at each tone frequency and attenuation), the scale-1.0 map table, and the plots not yet shown on this tab. "
                "Wiring: Pluto TX straight into the Siglent spectrum analyzer, Pluto on USB.",
                pngs=["pluto_level_vs_attenuation.png", "pluto_level_vs_frequency.png", "pluto_tone_scale.png"],
                files=["traces/*.csv", "spectrum_*.csv", "pluto_map_scale1_table.csv"]),
    )
    return T
