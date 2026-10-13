"""
Rebuild the JACON block diagram with the EXACT layout of racon_draft_design01b_drawing.pdf.

Arrows and block positions are read straight out of that PDF, so the layout matches.
Each block shows: title (as on the drawing), part number, max input dBm, max input mW,
min attenuation - plus the component photo from its datasheet.

Beside each block sits a small box with the cumulative level relative to the start of that
chain, computed two ways: minimum attenuation through every component (best case) and
maximum attenuation (worst case). That gives the range the design has to cope with.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pymupdf
from matplotlib.patches import FancyBboxPatch, Polygon

sys.path.insert(0, ".")
from specs import PARTS, damage_dbm_mw

SRC = "../racon_draft_design01b_drawing.pdf"
OURS = "#1f5fbf"
OTHER = "#8c8c8c"
SUM_OK = "#1d6f42"      # cumulative box: every contribution datasheet-verified
SUM_ASSUME = "#8a6d1f"  # cumulative box: running total includes an assumed value

spec = {p["model"]: p for p in PARTS}


def lim(model):
    d, m = damage_dbm_mw(spec[model])
    return "%+.2f dBm" % d, "%.4g mW" % m


L = {m: lim(m) for m in spec}


def blk(key, title, x, y, part, dbm, mw, atten, photo=None, ours=True, extra=None,
        parent=None, amin=None, amax=None, assumed=False, ref=None):
    """amin/amax = attenuation in dB (positive = loss, negative = gain)."""
    return dict(key=key, title=title, x=x, y=y, part=part, dbm=dbm, mw=mw, atten=atten,
                photo=photo, ours=ours, extra=extra, parent=parent,
                amin=amin, amax=amax, assumed=assumed, ref=ref)


NS = "not specified"

BLOCKS = [
    # ---------------- RX chain (reference = power at the RX antenna port)
    blk("rxant", "RX Antenna", 260, 183, "Horn antenna, 8.2-12.4 GHz", NS, NS,
        "gain +10 to +15 dBi", None, False, parent=None, amin=0, amax=0, ref="RX ant"),
    blk("limiter", "Power Limiter", 258, 333, "Aaronia SMA Limiter 20GHz (candidate)", NS, NS,
        "approx 0.5 dB (assumed)", None, False, parent=None, amin=0, amax=0, ref="LNA in"),
    blk("lna", "LNA", 260, 541, "ZX60-5123LN+", L["ZX60-5123LN+"][0], L["ZX60-5123LN+"][1],
        "none; gain +22.0 dB", "photos/ZX60-5123LNplus.jpeg",
        parent="limiter", amin=-22.0, amax=-19.0),
    blk("mixrx", "Mixer  (RX)", 260, 742, "ZX05-14LH-S+", L["ZX05-14LH-S+"][0], L["ZX05-14LH-S+"][1],
        "6.7 dB typ / 9.5 dB max", "photos/ZX05-14LH-Splus.jpeg",
        parent="lna", amin=6.7, amax=9.5),
    blk("ifamp", "IF amp", 260, 927, "ZX60-P162LN+", L["ZX60-P162LN+"][0], L["ZX60-P162LN+"][1],
        "none; gain 21.8 dB", "photos/ZX60-P162LNplus.jpeg",
        extra="alternates: ZX60-P103LN+, ZX60-2534MA-S+",
        parent="mixrx", amin=-22.5, amax=-20.9),
    blk("ifsplit", "50 ohm Splitter  (IF)", 259, 1086, "ZFRSC-42-S+", L["ZFRSC-42-S+"][0],
        L["ZFRSC-42-S+"][1], "6.0 dB typ / 6.5 dB max", "photos/ZFRSC-42-Splus.jpeg",
        parent="ifamp", amin=6.0, amax=6.5),
    blk("limamp", "RF Limiting Amplifier", 29, 1278, "3x GALI-52+ / ERA-33SM+ (candidate)", NS, NS,
        "none; gain approx 50 dB", None, False,
        parent="ifsplit", amin=-50.0, amax=-45.0, assumed=True),
    blk("envdet", "Envelope Detector", 458, 1278, "ADL5511 (candidate)", NS, NS,
        "n/a - detector", None, False, parent="ifsplit", amin=0, amax=0, assumed=True),
    blk("dlsplit", "50 ohm Splitter  (delay line)", 28, 1493, "ZFRSC-42-S+", L["ZFRSC-42-S+"][0],
        L["ZFRSC-42-S+"][1], "6.0 dB typ / 6.5 dB max", "photos/ZFRSC-42-Splus.jpeg",
        parent="limamp", amin=6.0, amax=6.5),
    blk("phdet", "Phase detector", 28, 1704, "ZX05-30W-S+", L["ZX05-30W-S+"][0], L["ZX05-30W-S+"][1],
        "6.8 dB typ / 9.0 dB max", "photos/ZX05-30W-Splus.jpeg",
        parent="dlsplit", amin=6.8, amax=9.0),
    blk("sh", "Sample and Hold", 29, 1876, "ADG1211 + ADA4622 (candidate)", NS, NS,
        "n/a - DC", None, False, parent=None),
    blk("comp", "Comparator", 636, 1438, "ADCMP600 (candidate)", NS, NS,
        "n/a - logic out", None, False, parent=None),
    blk("dac", "DAC", 826, 1278, "AD nanoDAC series (candidate)", NS, NS,
        "n/a - DC", None, False, parent=None),
    blk("fpga", "FPGA", 1035, 1476, "PYNQ-Z2 (candidate)", NS, NS,
        "n/a - control", None, False, parent=None),
    blk("psu", "+/-5V or +/-12V", 210, 2010, "bipolar dual-rail supply", "n/a", "n/a", "n/a",
        None, False, parent=None),

    # ---------------- LO chain (reference = PLL output)
    blk("pll", "PLL Local Oscillator", 845, 1012, "ADF5355 module (candidate)", NS, NS,
        "n/a - source", None, False, parent=None, amin=0, amax=0, ref="PLL out"),
    blk("lobuf", "LO Buffer Amp", 844, 870, "ZX60-14012L-S+", L["ZX60-14012L-S+"][0],
        L["ZX60-14012L-S+"][1], "none; gain 12.6 dB typ", "photos/ZX60-14012L-Splus.jpeg",
        parent="pll", amin=-12.55, amax=-9.0),
    blk("losplit", "50 ohm Splitter", 844, 754, "ZX10-2-1252-S+", L["ZX10-2-1252-S+"][0],
        L["ZX10-2-1252-S+"][1], "4.1 dB typ / 4.4 dB max", "photos/ZX10-2-1252-Splus.jpeg",
        parent="lobuf", amin=4.1, amax=4.4),

    # ---------------- TX chain (reference = VCO output)
    blk("vco", "VCO", 1221, 1849, "Crystek CVCO55BE-0800-1600 (candidate)", NS, NS,
        "n/a - source", None, False, parent=None, amin=0, amax=0, ref="VCO out"),
    blk("key", "Keying switch", 1300, 1278, "ADG901 (candidate)", NS, NS,
        "approx 1 dB insertion loss", None, False, parent="vco", amin=1.0, amax=1.5, assumed=True),
    blk("mixtx", "Mixer  (TX)", 1302, 742, "ZX05-14LH-S+", L["ZX05-14LH-S+"][0], L["ZX05-14LH-S+"][1],
        "6.7 dB typ / 9.5 dB max", "photos/ZX05-14LH-Splus.jpeg",
        parent="key", amin=6.7, amax=9.5),
    blk("irf", "Image Reject Filter", 1303, 544, "MCL VHF-8400+ (candidate)", NS, NS,
        "1.4 dB (per drawing)", None, False, parent="mixtx", amin=1.4, amax=1.6, assumed=True),
    blk("pa", "Power Amp", 1303, 369, "ZVE-143-S+ (candidate)", NS, NS,
        "gain approx 30 dB", None, False, parent="irf", amin=-30.0, amax=-28.0, assumed=True),
    blk("txant", "TX Antenna", 1303, 186, "copy of RX antenna", NS, NS,
        "gain +10 to +15 dBi", None, False, parent="pa", amin=0, amax=0, assumed=True),
]


# ---------------------------------------------------------------- what each block does
FUNC = {
    "rxant":   "Catches the ship radar's 9.3-9.5 GHz pulse.",
    "limiter": "Clips close-range pulses so the LNA survives.",
    "lna":     "First gain stage; its low noise sets how faint a radar we can hear.",
    "mixrx":   "DOWN-CONVERSION: subtracts the 8.3 GHz LO, so 9.3-9.5 GHz becomes 1.0-1.2 GHz. Everything after this runs at IF.",
    "ifamp":   "Boosts the weak IF before it is split two ways.",
    "ifsplit": "Splits the IF: one copy to detect THAT a radar pinged, one to measure WHICH frequency.",
    "envdet":  "Rectifies the IF to a voltage that follows the pulse envelope (amplitude).",
    "dac":     "Sets the detection threshold the comparator compares against.",
    "comp":    "Goes high when the envelope beats the threshold: 'radar detected'.",
    "fpga":    "Control brain: times the sample, applies hold-off, keys the Morse reply.",
    "limamp":  "Saturates on purpose, so output amplitude is constant: throws away amplitude, keeps frequency.",
    "dlsplit": "Makes two identical copies of the limited IF for the delay line.",
    "phdet":   "Multiplies the two arms. The 2f term is filtered off, leaving DC = cos(2*pi*f*dt): frequency has become a voltage.",
    "sh":      "Samples that voltage during the pulse and holds it; the op-amp scales it for the VCO.",
    "psu":     "Bipolar rails for the op-amps and slow analog.",
    "pll":     "Fixed 8.3 GHz reference for BOTH mixers, so its own error cancels in the reply.",
    "lobuf":   "Raises the PLL output to the drive level the mixers need.",
    "losplit": "Feeds the same LO to both mixers.",
    "vco":     "Re-creates the measured frequency as a fresh 1.0-1.2 GHz tone.",
    "key":     "Chops that tone into the Morse pattern '. - .'.",
    "mixtx":   "UP-CONVERSION: adds the same 8.3 GHz LO back, returning the reply to 9.3-9.5 GHz.",
    "irf":     "Removes the unwanted 7.2 GHz image sideband from the up-mixer.",
    "pa":      "Raises the reply to about 1 W for transmission.",
    "txant":   "Radiates the Morse reply on the radar's own frequency.",
}


def wrap(text, width=46):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out


BY = {b["key"]: b for b in BLOCKS}


def cumulative(b):
    """(best_dB, worst_dB, reference_name, any_assumed) relative to the chain start."""
    if b["amin"] is None:
        return None
    chain, node = [], b
    while node is not None:
        chain.append(node)
        node = BY.get(node["parent"]) if node["parent"] else None
    chain.reverse()
    best = worst = 0.0
    assumed = False
    for n in chain:
        best -= n["amin"]
        worst -= n["amax"]
        assumed = assumed or n["assumed"]
    return best, worst, chain[0].get("ref") or "start", assumed



def fwidth(b):
    """usable characters per line: narrower when a datasheet photo sits on the right"""
    if b["key"] in ("sh", "psu"):
        return 40
    return 34 if b.get("photo") else 46


# ---------------------------------------------------------------- figure
doc = pymupdf.open(SRC)
page = doc[0]
W, H = page.rect.width, page.rect.height

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)
ax.axis("off")
ax.set_facecolor("white")

# ---- arrows exactly as drawn in the source PDF
for path in page.get_drawings():
    filled = path.get("fill") is not None
    dashed = bool(path.get("dashes") and path["dashes"] not in ("[] 0", "[]0"))
    lw = (path.get("width") or 1.0) * 0.9
    pts = []
    for it in path["items"]:
        if it[0] == "l":
            p1, p2 = it[1], it[2]
            if filled:
                pts += [(p1.x, p1.y), (p2.x, p2.y)]
            else:
                ax.plot([p1.x, p2.x], [p1.y, p2.y], color="#222", lw=lw,
                        ls=(0, (6, 4)) if dashed else "-", solid_capstyle="round", zorder=1)
        elif it[0] == "c":
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]
            ts = [i / 24 for i in range(25)]
            xs = [(1 - t) ** 3 * p0.x + 3 * (1 - t) ** 2 * t * p1.x + 3 * (1 - t) * t ** 2 * p2.x + t ** 3 * p3.x for t in ts]
            ys = [(1 - t) ** 3 * p0.y + 3 * (1 - t) ** 2 * t * p1.y + 3 * (1 - t) * t ** 2 * p2.y + t ** 3 * p3.y for t in ts]
            if filled:
                pts += list(zip(xs, ys))
            else:
                ax.plot(xs, ys, color="#222", lw=lw, ls=(0, (6, 4)) if dashed else "-", zorder=1)
    if filled and len(pts) >= 3:
        ax.add_patch(Polygon(pts, closed=True, facecolor="#222", edgecolor="#222", lw=0.4, zorder=1))

# ---- main block rectangles (computed first so the small boxes can dodge them)
BW, PHW = 352, 74
rects = {}
for b in BLOCKS:
    nf = len(wrap(FUNC.get(b["key"], ""), fwidth(b)))
    n = nf + 1 + (0 if (b["dbm"] == "n/a" and b["mw"] == "n/a") else 3) + (1 if b["extra"] else 0)
    bh = 34 + 15.5 * n
    x0 = min(b["x"] - 14, W - 12 - BW)
    rects[b["key"]] = (x0, b["y"] - 26, BW, bh)

SW, SH = 118, 42


def overlaps(r, others, pad=6):
    x, y, w, h = r
    for (ox, oy, ow, oh) in others:
        if x < ox + ow + pad and x + w + pad > ox and y < oy + oh + pad and y + h + pad > oy:
            return True
    return False


def place_sum(key, taken):
    """find a free spot for the small cumulative box next to its main block"""
    x0, y0, w, h = rects[key]
    others = [r for k, r in rects.items() if k != key] + taken
    for cand in [(x0 + w + 8, y0),
                 (x0 + w + 8, y0 + h - SH),
                 (x0 - SW - 8, y0),
                 (x0 - SW - 8, y0 + h - SH),
                 (x0 + w - SW, y0 + h + 6),
                 (x0, y0 - SH - 6)]:
        r = (cand[0], cand[1], SW, SH)
        if r[0] < 4 or r[0] + SW > W - 4 or r[1] < 4 or r[1] + SH > H - 70:
            continue
        if not overlaps(r, others):
            return r
    return (min(x0 + w + 8, W - SW - 6), y0, SW, SH)


# ---- draw blocks
taken = []
for b in BLOCKS:
    lines = [(t, 8.7) for t in wrap(FUNC.get(b["key"], ""), fwidth(b))]
    lines += [("Part: %s" % b["part"], 8.0)]
    if not (b["dbm"] == "n/a" and b["mw"] == "n/a"):
        lines += [("Max in: %s" % b["dbm"], 9.6),
                  ("Max in: %s" % b["mw"], 9.6),
                  ("Min atten: %s" % b["atten"], 9.6)]
    if b["extra"]:
        lines.append((b["extra"], 8.4))
    x0, y0, bw, bh = rects[b["key"]]
    col = OURS if b["ours"] else OTHER
    ax.add_patch(FancyBboxPatch((x0, y0), bw, bh, boxstyle="round,pad=3",
                                linewidth=2.0 if b["ours"] else 1.1, edgecolor=col,
                                facecolor="#eef4fc" if b["ours"] else "#f5f5f5", zorder=2))
    ax.text(x0 + 10, y0 + 19, b["title"], fontsize=13.5, weight="bold", color=col,
            va="center", zorder=3)
    ty = y0 + 36
    nfunc = len(wrap(FUNC.get(b["key"], ""), fwidth(b)))
    for i, (txt, fs) in enumerate(lines):
        ax.text(x0 + 10, ty, txt, fontsize=fs,
                color="#1d6f42" if i < nfunc else "#111", va="center", zorder=3)
        ty += 15.5
    if b["photo"] and os.path.exists(b["photo"]):
        img = mpimg.imread(b["photo"])
        ih, iw = img.shape[0], img.shape[1]
        pw = PHW
        ph = pw * ih / iw
        if ph > bh - 12:
            ph = bh - 12
            pw = ph * iw / ih
        px1 = x0 + bw - 8
        py0 = y0 + (bh - ph) / 2
        ax.imshow(img, extent=(px1 - pw, px1, py0 + ph, py0), zorder=4, aspect="auto")

    cum = cumulative(b)
    if cum is None:
        continue
    best, worst, ref, assumed = cum
    sx, sy, sw, sh = place_sum(b["key"], taken)
    taken.append((sx, sy, sw, sh))
    c = SUM_ASSUME if assumed else SUM_OK
    ax.add_patch(FancyBboxPatch((sx, sy), sw, sh, boxstyle="round,pad=2.5", linewidth=1.3,
                                edgecolor=c, facecolor="#fdf7e7" if assumed else "#f2faf4", zorder=5))
    ax.text(sx + sw / 2, sy + 12, ("chain start: %s" % ref) if b["parent"] is None else ("vs %s" % ref),
            fontsize=7.6 if b["parent"] is None else 8.0, color=c, ha="center",
            va="center", zorder=6)
    is_ref = b["parent"] is None
    rng = "0 dB reference" if is_ref else (
        ("%+.1f dB" % worst) if abs(worst - best) < 0.05 else ("%+.1f to %+.1f dB" % (worst, best)))
    ax.text(sx + sw / 2, sy + 29, rng, fontsize=8.6 if is_ref else 9.4, weight="bold", color="#111",
            ha="center", va="center", zorder=6)

# ---- titles and key
ax.text(715, 52, "The JACON", fontsize=30, weight="bold", color="#111")
ax.text(649, 95, "component power limits - layout follows Jason's RACON draft design",
        fontsize=13, color="#444")
ax.text(29, 2056, "Blue = the nine Mini-Circuits parts we have; max input values are datasheet absolute maximum "
        "ratings (JACON_component_power_ratings.docx has a screenshot of each, with page numbers).  "
        "Grey = candidate parts named on the drawing, not datasheet-verified.",
        fontsize=10.5, color="#444")
ax.text(29, 2072, "Small side box = running level relative to the start of that chain: worst case (maximum attenuation, "
        "minimum gain) to best case (minimum attenuation, maximum gain).  "
        "Green = every term datasheet-verified; amber = the total includes an assumed value.",
        fontsize=10.5, color="#444")
ax.text(29, 2082, "The RF limiting amplifier saturates on purpose, so levels after it are set by its saturated output "
        "rather than by this running total.", fontsize=10.5, color="#8a6d1f")

out = "JACON_blockdiagram_layout.png"
fig.savefig(out, dpi=100, facecolor="white")
print("wrote", out)
for b in BLOCKS:
    c = cumulative(b)
    if c:
        print("  %-30s %+7.1f .. %+7.1f dB vs %-8s %s" %
              (b["title"], c[1], c[0], c[2], "(assumed term)" if c[3] else ""))
