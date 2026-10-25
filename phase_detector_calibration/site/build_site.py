"""Assemble site/index.html: one page, one tab per part. Content lives in content.py."""
from pathlib import Path

import numpy as np

import content as C
import content_more as CM
import content_parts as CP
import content_pluto as CPL
import content_radar as CRA

HERE = Path(__file__).resolve().parent
P = HERE / "parts"
CAL = HERE.parent / "phase_detector_calibration_run3_cleanDC_0p02V_steps.csv"

W, H = 172, 68
REPO = "Sorin-Jayaweera/Panthalassa-Clinic-Team"
PAGES_URL = "https://sorin-jayaweera.github.io/Panthalassa-Clinic-Team/"
# key, label, part number, x, y (centre), status, link target, spec line 1, spec line 2
# status: tested = every test in its plan is done (green); partial = some tests done (yellow);
#         have = part on hand, not tested; none = not on hand or not chosen
BLOCKS = [
    ("rxant", "RX antenna", "horn", 105, 45, "have", "pi-rxant", "8.2-12.4 GHz", "gain 10-15 dBi"),
    ("limiter", "Power limiter", "not chosen", 105, 137, "none", "pi-limiter", "output must stay", "under +15 dBm"),
    ("lna", "LNA", "ZX60-5123LN+", 105, 229, "have", "tab-lna", "+22 dB, NF 1.4 dB, 6 V", "max in +15 dBm"),
    ("rxmixer", "RX mixer", "ZX05-14LH-S+", 105, 321, "have", "tab-rxmixer", "loss 7.7 dB, LO +10 dBm", "max in +17 dBm"),
    ("ifamp", "IF amp", "P103LN / 2534MA", 105, 413, "have", "tab-ifamp", "P103LN +15.6 dB, max +21", "2534MA +43.5 dB, max -15"),
    ("ifsplit", "IF splitter", "ZFRSC-42-S+", 105, 505, "have", "tab-splitter", "loss 6.0 dB (6.5 max)", "max in +28.8 dBm"),
    ("limamp", "RF limiting amp", "3 gain blocks", 105, 610, "none", "pi-limamp", "fixed output level,", "under +23.5 dBm"),
    ("delaysplit", "Delay-line splitter", "ZFRSC-42-S+", 105, 702, "partial", "tab-splitter", "loss 6.0 dB (6.5 max)", "+4.5 in cable = 0.55 ns"),
    ("phasedet", "Phase detector", "ZX05-30W-S+", 105, 800, "partial", "tab-mixer", "LO +7 dBm, max in +17", "out: DC volts vs freq."),
    ("sh", "Sample and hold", "ADG1211 + ADA4622", 105, 892, "none", "pi-sh", "holds detector voltage", "out 4.8-7.8 V to VCO"),
    ("env", "Envelope detector", "ADL5511", 325, 610, "none", "pi-env", "detects the pulse", ""),
    ("comp", "Comparator", "ADCMP600", 435, 702, "none", "pi-comp", "high during a pulse", ""),
    ("dac", "DAC", "nanoDAC", 545, 610, "none", "pi-dac", "sets comparator level", ""),
    ("fpga", "FPGA", "PYNQ-Z2 / ECP5", 655, 702, "none", "pi-fpga", "timing, Morse, hold-off", ""),
    ("losplit", "LO splitter", "ZX10-2-1252-S+", 520, 321, "have", "pi-losplit", "loss 4.1 dB at 8.3 GHz", "max in +32.7 dBm"),
    ("lobuf", "LO buffer amp", "ZX60-14012L-S+", 520, 413, "partial", "tab-lobuf", "+12.5 dB, 12 V 62 mA", "max out +12, max in +10"),
    ("pll", "PLL LO", "ADF5355", 520, 505, "none", "pi-pll", "8.3 GHz", ""),
    ("txant", "TX antenna", "horn", 935, 45, "have", "pi-txant", "8.2-12.4 GHz", "gain 10-15 dBi"),
    ("pa", "Power amp", "not chosen", 935, 137, "none", "pi-pa", "about 1 W out", ""),
    ("filter", "Image filter", "VHF-8400+", 935, 229, "have", "tab-filter", "loss < 3 dB at 9.3-9.5", "8.3 GHz LO: only 3-5 dB"),
    ("txmixer", "TX mixer", "ZX05-14LH-S+", 935, 321, "have", "tab-rxmixer", "loss 7.7 dB, LO +10 dBm", "max in +17 dBm"),
    ("key", "Keying switch", "ADG901", 935, 610, "none", "pi-key", "turns the reply on/off", ""),
    ("vco", "VCO", "CVCO55BE-0800-1600", 935, 892, "partial", "tab-vco", "+6 dBm, 11.5 V", "1.0-1.2 GHz at 4.8-7.8 V"),
]
POS = {b[0]: (b[3], b[4]) for b in BLOCKS}


def edge(a, b, sa, sb):
    def pt(k, s):
        x, y = POS[k]
        return {"t": (x, y - H / 2), "b": (x, y + H / 2), "l": (x - W / 2, y), "r": (x + W / 2, y)}[s]
    return pt(a, sa), pt(b, sb)


def arrow(p0, p1, cls="wire", via=None):
    pts = [p0] + (via or []) + [p1]
    d = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    a, w = 9, 4
    head = f"{x1:.1f},{y1:.1f} {x1-ux*a-uy*w:.1f},{y1-uy*a+ux*w:.1f} {x1-ux*a+uy*w:.1f},{y1-uy*a-ux*w:.1f}"
    return f'<path class="{cls}" d="{d}"/><polygon class="{"head" if cls == "wire" else "headc"}" points="{head}"/>'


def spark(xs, ys, x0, y0, w=150, hgt=20):
    """Small line plot of measured data, drawn inside a block."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    px = x0 + (xs - xs.min()) / (xs.max() - xs.min()) * w
    py = y0 + hgt - (ys - ys.min()) / (ys.max() - ys.min()) * hgt
    return '<polyline class="spark" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(px, py)) + '"/>'


def block_data(key, x, y):
    """What a block shows in Data mode: a small plot of what was measured, or its test status."""
    d = np.genfromtxt(CAL, delimiter=",", names=True, dtype=None, encoding="utf-8")
    up = d[d["direction"] == "up"]
    left, top = x - 75, y + 2
    if key == "vco":
        return spark(up["vt_meas_v"], up["vco_freq_hz"], left, top) + f'<text class="t2" x="{x}" y="{y+31}" text-anchor="middle">744-920 MHz for 0-3.5 V</text>'
    if key == "phasedet":
        return spark(up["vco_freq_hz"], up["mixer_out_v"], left, top) + f'<text class="t2" x="{x}" y="{y+31}" text-anchor="middle">30-146 mV, 744-920 MHz</text>'
    if key == "delaysplit":
        return (f'<text class="t2" x="{x}" y="{y+12}" text-anchor="middle">measured loss 6.70, 6.72 dB</text>'
                f'<text class="t2" x="{x}" y="{y+25}" text-anchor="middle">at 1.04 GHz (6 Oct)</text>')
    if key == "lobuf":
        return (spark([1000, 1050, 1100, 1150, 1200], [10.63, 10.02, 11.40, 11.30, 10.15], left, top)
                + f'<text class="t2" x="{x}" y="{y+31}" text-anchor="middle">gain 10-11 dB, 1 dB comp. +8.2 dBm</text>')
    if key == "ifsplit":
        return (f'<text class="t2" x="{x}" y="{y+12}" text-anchor="middle">not tested in this position</text>'
                f'<text class="t2" x="{x}" y="{y+25}" text-anchor="middle">same part as delay-line splitter</text>')
    return None


def schematic():
    out = ['<svg viewBox="0 0 1040 940" role="img" aria-label="JACON block diagram. Each block links to its part.">']
    for a, b in (("rxant", "limiter"), ("limiter", "lna"), ("lna", "rxmixer"), ("rxmixer", "ifamp"), ("ifamp", "ifsplit"),
                 ("ifsplit", "limamp"), ("limamp", "delaysplit"), ("phasedet", "sh")):
        out.append(arrow(*edge(a, b, "b", "t")))
    for a, b in (("vco", "key"), ("key", "txmixer"), ("txmixer", "filter"), ("filter", "pa"), ("pa", "txant"), ("pll", "lobuf"), ("lobuf", "losplit")):
        out.append(arrow(*edge(a, b, "t", "b")))
    x, y = POS["delaysplit"]
    yb = POS["phasedet"][1] - H / 2
    ya = y + H / 2
    out.append(arrow((x - 40, ya), (x - 40, yb)))
    out.append(arrow((x + 40, ya), (x + 40, yb), via=[(x + 40, ya + 5), (x + 58, ya + 9), (x + 22, ya + 14), (x + 58, ya + 19), (x + 40, ya + 23)]))
    out.append(f'<text class="t2" x="{x+66}" y="{ya+17}">+4.5 in cable</text>')
    for a, b, sa, sb, cls in (("ifsplit", "env", "b", "t", "wire"), ("env", "comp", "b", "t", "wire"), ("dac", "comp", "b", "t", "wire"), ("sh", "vco", "r", "l", "wire"),
                              ("losplit", "rxmixer", "l", "r", "wire"), ("losplit", "txmixer", "r", "l", "wire"), ("comp", "fpga", "r", "l", "ctl"),
                              ("fpga", "dac", "t", "b", "ctl"), ("fpga", "pll", "t", "b", "ctl"), ("fpga", "key", "r", "l", "ctl")):
        out.append(arrow(*edge(a, b, sa, sb), cls=cls))
    for lx, ly, txt in ((198, 94, "9.3-9.5 GHz, -50 to -10 dBm"), (198, 278, "-28 to +12 dBm"), (198, 370, "1.0-1.2 GHz, -36 to +4 dBm"),
                        (760, 94, "9.3-9.5 GHz, about 1 W"), (760, 780, "1.0-1.2 GHz"), (612, 296, "LO 8.3 GHz, about +8 dBm each")):
        out.append(f'<text class="lvl" x="{lx}" y="{ly}">{txt}</text>')
    for key, label, part, bx, by, st, target, s1, s2 in BLOCKS:
        cls = {"tested": "blk tested", "partial": "blk partial", "have": "blk", "none": "blk none"}[st]
        data = block_data(key, bx, by)
        if data is None:
            word = {"tested": "fully tested", "partial": "some tests done", "have": "on hand, not tested yet", "none": "not on hand"}[st]
            data = f'<text class="t2" x="{bx}" y="{by+18}" text-anchor="middle">{word}</text>'
        out.append(f'<a href="#{target}" aria-label="{label}, {part}"><g class="{cls}">'
                   f'<rect x="{bx-W/2:.0f}" y="{by-H/2:.0f}" width="{W}" height="{H}" rx="3"/>'
                   f'<text class="t1" x="{bx}" y="{by-18}" text-anchor="middle">{label}</text>'
                   f'<text class="t2" x="{bx}" y="{by-5}" text-anchor="middle">{part}</text>'
                   f'<g class="m-specs"><text class="t3" x="{bx}" y="{by+12}" text-anchor="middle">{s1}</text>'
                   f'<text class="t3" x="{bx}" y="{by+25}" text-anchor="middle">{s2}</text></g>'
                   f'<g class="m-data">{data}</g></g></a>')
    out.append("</svg>")
    return "".join(out)


VCO_4OCT = [(0.0, 732.74), (0.5, 751.43), (1.0, 778.14), (1.5, 799.50), (2.12, 834.22), (2.72, 866.26), (3.34, 906.32), (4.01, 949.37), (4.53, 981.09),
            (5.38, 1034.50), (5.98, 1071.88), (6.34, 1098.59), (6.86, 1135.98), (7.29, 1168.02), (7.53, 1184.04), (8.08, 1224.10), (8.75, 1269.50),
            (9.17, 1298.87), (9.54, 1322.91), (10.13, 1360.29)]


def lut_tab():
    d = np.genfromtxt(CAL, delimiter=",", names=True, dtype=None, encoding="utf-8")
    up = d[d["direction"] == "up"]
    vt, f, mv = up["vt_meas_v"], up["vco_freq_hz"] / 1e6, up["mixer_out_v"] * 1e3
    grid = np.round(np.arange(0.0, 3.51, 0.1), 1)
    fg = np.interp(grid, vt, f)
    sl = np.gradient(fg, grid)
    vco_rows = [[f"{v:.1f}", f"{a:.2f}", f"{s:.1f}"] for v, a, s in zip(grid, fg, sl)]
    v4 = np.array(VCO_4OCT)
    s4 = np.gradient(v4[:, 1], v4[:, 0])
    rows4 = [[f"{a:.2f}", f"{b:.2f}", f"{s:.1f}"] for (a, b), s in zip(VCO_4OCT, s4)]
    m = vt <= 1.2
    o = np.argsort(mv[m])                                       # sorted by the input of the look up: mixer voltage
    mm, fm, vm = mv[m][o], f[m][o], vt[m][o]
    mslope = np.gradient(fm, mm)                                # MHz per mV, the direction the table is used in
    mix_rows = [[f"{a:.2f}", f"{b:.2f}", f"{s:.3f}", f"{v:.3f}"] for a, b, s, v in zip(mm, fm, mslope, vm)]
    return "".join([
        "<h2>Look up tables</h2>",
        C.p("Two look ups: VCO tuning voltage Vt to VCO output frequency, and mixer output voltage to VCO frequency. Each is valid only for the wiring and power it was measured with. Pluto output levels are on the Pluto tab."),
        C.item("lut-vco", "VCO: tuning voltage Vt to output frequency, 0 to 3.5 V",
               C.fig("vco_f_vs_v.png", "VCO output frequency against tuning voltage Vt, 0 to 3.5 V"),
               C.h("Conditions"), C.ul(["Measured 10 Oct. Vcc 11.5 V.", "VCO output connected to a tee: one side to the spectrum analyzer, the other to the splitter and mixer.",
                                         "Tuning voltage read on scope CH1. Accuracy a few percent.", "Repeatability 0.10 MHz."]),
               C.h("Table"), C.table(["Tuning voltage Vt (V)", "VCO output frequency (MHz)", "Slope (MHz/V)"], vco_rows, cls="lut", left=()),
               C.p("Values every 0.1 V, interpolated from 176 measured points spaced 0.02 V. Full data: <code>phase_detector_calibration_run3_cleanDC_0p02V_steps.csv</code>."),
               C.h("How it was made"), C.p("See " + C.link("#vco-tune35", "VCO, Frequency vs voltage, 0 to 3.5 V") + ".")),
        C.item("lut-vco10", "VCO: tuning voltage Vt to output frequency, 0 to 10 V",
               C.fig("comp_vco_tuning.png", "VCO output frequency against tuning voltage Vt, 0 to 10 V"),
               C.h("Conditions"), C.ul(["Measured 4 Oct by hand. Vcc 11.48 to 11.5 V.", "VCO output connected straight to the spectrum analyzer.",
                                         "Frequency read 10 s after setting the voltage. The analyzer marker step was 2.67 MHz.", "1.0 GHz is at 4.83 V. 1.2 GHz is at 7.75 V."]),
               C.h("Table"), C.table(["Tuning voltage Vt (V)", "VCO output frequency (MHz)", "Slope (MHz/V)"], rows4, cls="lut", left=()),
               C.p("Source: <code>VCO tests.xlsx</code>, sheet &ldquo;absolute accuracy&rdquo;.")),
        C.item("lut-mixer", "Mixer (phase detector): output voltage to VCO frequency",
               C.fig("mapping.png", "Mixer output voltage against VCO frequency as measured, the same points used as a look up, and the slope"),
               C.h("Conditions"), C.ul(["Measured 10 Oct. Source: the VCO, about +0.6 dBm at each mixer port.", "Splitter ZFRSC-42-S+, 4.5 in extra cable on one side, mixer ZX05-30W-S+.",
                                         "Mixer output read on scope CH2 into 1 M&Omega;.", "Valid from 743.6 to 788.4 MHz only. Above that one voltage matches more than one frequency.",
                                         "A different input power gives a different table."]),
               C.h("Table"), C.table(["Mixer output voltage (mV)", "VCO frequency (MHz)", "Slope (MHz/mV)", "VCO tuning voltage Vt at this point (V)"], mix_rows, cls="lut", left=()),
               C.h("How to use it"), C.ol(["Read the mixer output voltage V in mV.", "Find the two rows on either side of it (the table is sorted by mixer voltage).", "Draw a straight line between them and read the VCO frequency f in MHz. The slope column is the MHz per mV between neighbouring rows."]),
               C.math(r"f(V) = f_i + (V - V_i)\,\frac{f_{i+1} - f_i}{V_{i+1} - V_i}"),
               C.code(C.C_LOOKUP), C.p("How it was made: see " + C.link("#mx-lut", "Mixer, Mixer look up table") + ".")),
    ])


TABS = [("tab-schem", "Schematic"), ("tab-parts", "Part info"), ("tab-lna", "LNA"), ("tab-rxmixer", "RX mixer"), ("tab-ifamp", "IF amp"), ("tab-lobuf", "LO buffer"), ("tab-filter", "Image filter"),
        ("tab-splitter", "Splitter"), ("tab-mixer", "Phase detector"), ("tab-vco", "VCO"), ("tab-pluto", "Pluto"), ("tab-radar", "Radar"), ("tab-gear", "Test gear"), ("tab-lut", "Look up tables"),
        ("tab-tests", "Tests to run"), ("tab-errors", "Errors"), ("tab-review", "Review notes")]

HEAD = """<title>JACON Engineering Notes</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
%s
</style>
<script>window.MathJax = { tex: { inlineMath: [["\\\\(", "\\\\)"]] }, svg: { fontCache: "global" } };</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js" async></script>
"""

BAR = """<h1>JACON engineering notes</h1>
<div class="bar" aria-label="Document tools">
  <span class="switch" role="group" aria-label="Mode">
    <button type="button" id="mode-read" aria-pressed="true">Read only</button><button type="button" id="mode-edit" aria-pressed="false" disabled>Edit</button>
  </span>
  <button type="button" id="exp-all">Expand all</button>
  <button type="button" id="col-all">Collapse all</button>
  <button type="button" id="dl-backup" hidden>Download backup (.html)</button>
  <span><mark data-k="ok">validated</mark> <mark data-k="q">under question</mark></span>
  <span id="mark-count"></span>
  <span id="doc-status">Loading</span>
</div>
"""

TOOLS = """<div id="seltools" hidden>
  <button type="button" class="ok" data-act="ok" data-edit>Validated</button>
  <button type="button" class="q" data-act="q" data-edit>Under question</button>
  <button type="button" data-act="clear" data-edit>Clear mark</button>
  <button type="button" data-act="restore" data-edit>Restore original text</button>
  <button type="button" data-act="comment">Comment</button>
  <button type="button" data-act="suggest" hidden>Suggest a change</button>
</div>
"""


REVIEW = f"""<h2>Review notes</h2>
<p>Marks and comments made by people on the GitHub copy of this page. Each one is a GitHub issue in
<a href="https://github.com/{REPO}/issues">{REPO}</a>, written with that person's own GitHub account.</p>
<h3>How to add one</h3>
<ol><li>Open <a href="{PAGES_URL}">the GitHub copy of this page</a> and press <b>Edit</b> in the bar at the top.</li>
<li>Select some text. A small bar appears: Validated, Under question, Comment, Suggest a change.</li>
<li>Press one. GitHub opens with the quote filled in. Add a note if you want and press <b>Submit new issue</b>.</li>
<li>Reload this page. The text is highlighted and the note is listed below. The folder <code>review/</code> in the repository is updated about a minute later.</li></ol>
<p>To withdraw a mark, or when a question has been answered, close the issue on GitHub.</p>
<p id="review-status" class="sub">Loading.</p>
<div id="review-list"></div>
"""


def write_standalone(page):
    """One HTML file with every plot inside it, for backups. Written to the site folder, to clinic/claude, and to a dated copy."""
    import base64
    import datetime as dt
    import re

    def inline(m):
        data = base64.b64encode((HERE / m.group(1)).read_bytes()).decode()
        return f'src="data:image/png;base64,{data}"'
    s = re.sub(r'<a href="img/[^"]+">(<img [^>]+>)</a>', r"\1", page)       # full-size links are not needed: the image is in the file
    s = re.sub(r'src="(img/[^"]+)"', inline, s)
    s = '<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + s
    root = HERE.parent.parent                      # clinic/claude
    backups = root / "site_backups"
    backups.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d")
    for out in (HERE / "JACON_notes_standalone.html", backups / f"JACON_notes_{stamp}.html"):
        out.write_text(local_datasheets(s, PAGES_URL + "datasheets/"), encoding="utf-8")
    (root / "JACON_notes_backup.html").write_text(local_datasheets(s, "docs/datasheets/"), encoding="utf-8")     # this copy sits next to docs/
    print("standalone", len(s), "bytes ->", root / "JACON_notes_backup.html")


def local_datasheets(page, prefix):
    """Point datasheet links at the copies kept in docs/datasheets (the vendor links do not open from GitHub Pages).
    Copies clinic/claude/datasheets/*.pdf to docs/datasheets with the + signs removed from the names."""
    import re
    import shutil
    src = HERE.parent.parent / "datasheets"
    dst = HERE.parent.parent / "docs" / "datasheets"
    dst.mkdir(parents=True, exist_ok=True)
    have = {}
    for f in list(src.glob("*.pdf")) + [HERE.parent.parent / "documentation" / "datasheets" / "CVCO55BE-0800-1600.pdf"]:
        if f.exists():
            safe = f.name.replace("+", "")
            shutil.copy2(f, dst / safe)
            have[f.name] = safe

    def swap(m):
        name = m.group(1)
        alt = name.replace("-S+.pdf", "+.pdf")                      # some files are saved without the -S connector suffix
        got = have.get(name) or have.get(alt)
        return f'href="{prefix}{got}" target="_blank" rel="noopener"' if got else m.group(0)
    page = re.sub(r'href="https://www\.minicircuits\.com/pdfs/([^"]+\.pdf)"', swap, page)
    if "CGR201-Datasheet.pdf" in have:
        page = page.replace('href="https://www.saelig.com/supplier/syscomp/CGR201-Datasheet.pdf"', f'href="{prefix}CGR201-Datasheet.pdf" target="_blank" rel="noopener"')
    if "CVCO55BE-0800-1600.pdf" in have:
        page = page.replace('>DigiKey listing</a>', f'>DigiKey listing</a>, <a href="{prefix}CVCO55BE-0800-1600.pdf" target="_blank" rel="noopener">Crystek datasheet (PDF)</a>')
    return page


def write_pages(page):
    """The same page for GitHub Pages: clinic/claude/docs/index.html with its plots in docs/img/."""
    import shutil
    docs = HERE.parent.parent / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    for f in (HERE / "img").glob("*.png"):
        shutil.copy2(f, docs / "img" / f.name)
    page = local_datasheets(page, "datasheets/")
    s = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + page + "</html>\n"
    (docs / "index.html").write_text(s, encoding="utf-8")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
    print("GitHub Pages copy ->", docs / "index.html")


def main():
    schem = ("<h2>Schematic</h2>" + C.p("Click a block to open that part. Green = fully characterized (every test in its plan done). Yellow = some tests done. White = on hand, not tested yet. Dashed = not on hand or not chosen.")
             + '<div class="bar"><span>Show in each block:</span><span class="switch" role="group" aria-label="Schematic view">'
               '<button type="button" id="sch-specs" aria-pressed="true">Specs</button><button type="button" id="sch-data" aria-pressed="false">Data taken</button></span></div>'
             + f'<div class="schematic" id="schem" data-mode="specs">{schematic()}</div>')
    panels = {"tab-schem": schem, "tab-parts": C.PARTINFO.replace("@@RX_LEVELS@@", CP.RX_LEVELS), "tab-lna": CP.LNA, "tab-rxmixer": CP.RXMIXER,
              "tab-ifamp": CP.IFAMP, "tab-lobuf": CM.LOBUF, "tab-filter": CM.FILTER, "tab-vco": CP.VCO, "tab-splitter": CP.SPLITTER, "tab-mixer": CP.PHASEDET,
              "tab-pluto": CPL.PLUTO, "tab-radar": CRA.RADAR, "tab-gear": C.GEAR, "tab-lut": lut_tab(), "tab-tests": C.TESTS, "tab-errors": C.ERRORS, "tab-review": REVIEW}
    tabs = '<div class="tabs" role="tablist">' + "".join(
        f'<button type="button" role="tab" data-panel="{tid}" aria-selected="{"true" if i == 0 else "false"}">{name}</button>' for i, (tid, name) in enumerate(TABS)) + "</div>\n"
    body = "".join(f'<div class="panel" id="{tid}"{"" if i == 0 else " hidden"}>\n{panels[tid]}\n</div>\n' for i, (tid, _) in enumerate(TABS))
    page = (HEAD % (P / "style.css").read_text(encoding="utf-8")) + "<main>\n" + BAR + tabs + body + "</main>\n" + TOOLS \
        + "<!--APP-->\n<script>\n" + (P / "app.js").read_text(encoding="utf-8") + (P / "review.js").read_text(encoding="utf-8") + "</script>\n"
    (HERE / "index.html").write_text(local_datasheets(page, PAGES_URL + "datasheets/"), encoding="utf-8")
    print("index.html", len(page), "bytes")
    write_standalone(page)
    write_pages(page)


if __name__ == "__main__":
    main()
