"""
Bench test flow: Pluto TX -> ZFRSC-42-S+ splitter -> 4 in and 8.5 in cables -> ZX05-30W-S+ (phase detector).

For every stage: attenuation (min / max), level after it in dBm and mW for a 750 mW source,
and a check against that part's datasheet maximum input.
"""
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, ".")
from specs import PARTS, damage_dbm_mw

spec = {p["model"]: p for p in PARTS}

P_SRC_MW = 750.0
P_SRC = 10 * math.log10(P_SRC_MW)          # +28.75 dBm

# ---- attenuation per stage (dB): (min, max, source-of-number, verified?)
SPLIT = (6.0, 6.5, "ZFRSC-42-S+ datasheet p.1: 5.99/6.02 dB measured at 1 GHz; spec max 6.0 + 0.5 dB", True)
CABLE_DB_PER_FT = (0.45, 0.60)             # RG-316 class coax near 1.1-1.2 GHz - ASSUMED, not a datasheet value
CONNECTORS_DB = 0.10                        # two SMA mates per cable, max case only - ASSUMED
L_A_IN, L_B_IN = 4.0, 8.5
MIXER = (6.22, 9.0, "ZX05-30W-S+ datasheet p.1: 6.22 dB measured at 944 MHz; spec max 9.0 dB", True)


def cable(length_in):
    ft = length_in / 12.0
    return (CABLE_DB_PER_FT[0] * ft, CABLE_DB_PER_FT[1] * ft + CONNECTORS_DB)


CAB_A, CAB_B = cable(L_A_IN), cable(L_B_IN)


def mw(dbm):
    return 10 ** (dbm / 10)


def fmt(dbm):
    m = mw(dbm)
    return "%+.2f dBm = %s" % (dbm, ("%.1f mW" % m) if m >= 1 else ("%.3f mW" % m))


# levels (best = min attenuation, worst = max attenuation)
split_out = (P_SRC - SPLIT[0], P_SRC - SPLIT[1])
a_out = (split_out[0] - CAB_A[0], split_out[1] - CAB_A[1])
b_out = (split_out[0] - CAB_B[0], split_out[1] - CAB_B[1])
if_out = (a_out[0] - MIXER[0], a_out[1] - MIXER[1])

split_max_dbm, split_max_mw = damage_dbm_mw(spec["ZFRSC-42-S+"])
mix_max_dbm, mix_max_mw = damage_dbm_mw(spec["ZX05-30W-S+"])

# safe drive: largest source that keeps the mixer RF port at its 50 mW limit (min-loss path)
safe_src = mix_max_dbm + SPLIT[0] + CAB_A[0]
# drive for the mixer's nominal LO level (+7 dBm, Level 7 mixer) on the longer arm, typical loss
lo_target_src = 7.0 + SPLIT[0] + CAB_B[0]

# ---------------------------------------------------------------- drawing
FW, FH = 230.0, 124.0
fig, ax = plt.subplots(figsize=(19, 19 * FH / FW))
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.invert_yaxis()
ax.axis("off")
UNIT_ASPECT = (fig.get_size_inches()[0] / FW) / (fig.get_size_inches()[1] / FH)

BLUE, GREY, RED, GREEN, AMBER = "#1f5fbf", "#8c8c8c", "#b03030", "#1d6f42", "#8a6d1f"


def box(x, y, w, h, title, lines, color, photo=None, face="#eef4fc"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6", lw=2.0, edgecolor=color,
                                facecolor=face, zorder=2))
    ax.text(x + 1.8, y + 3.4, title, fontsize=12.5, weight="bold", color=color, va="center", zorder=3)
    ty = y + 8.6
    for txt, fs, col in lines:
        ax.text(x + 1.8, ty, txt, fontsize=fs, color=col, va="center", zorder=3)
        ty += 3.6
    if photo:
        img = mpimg.imread(photo)
        ih, iw = img.shape[:2]
        pw = 11.0
        ph = pw * ih / iw * UNIT_ASPECT
        px0, py0 = x + w - pw - 1.2, y + 7.0
        ax.imshow(img, extent=(px0, px0 + pw, py0 + ph, py0), zorder=4, aspect="auto")


def arrow(p1, p2, top, bot, lx=None, ly=None):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=18, lw=1.8, color="#222", zorder=1))
    mx = lx if lx is not None else (p1[0] + p2[0]) / 2
    my = ly if ly is not None else (p1[1] + p2[1]) / 2
    ax.text(mx, my - 2.2, top, fontsize=8.6, ha="center", va="center", weight="bold", color="#111",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#dddddd", lw=0.6), zorder=5)
    ax.text(mx, my + 2.2, bot, fontsize=8.2, ha="center", va="center", color="#555",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#dddddd", lw=0.6), zorder=5)


def status(level_dbm, limit_dbm):
    margin = limit_dbm - level_dbm
    if margin < 0:
        return ("OVER limit by %.1f dB" % -margin, RED)
    if margin < 3:
        return ("at limit (%.1f dB margin)" % margin, AMBER)
    return ("OK (%.1f dB margin)" % margin, GREEN)


def short(dbm):
    m = mw(dbm)
    return "%+.2f dBm = %s" % (dbm, ("%.1f mW" % m) if m >= 1 else ("%.3f mW" % m))


ax.text(2, 4, "Bench test: Pluto TX -> splitter -> 4 in / 8.5 in cables -> frequency mixer (phase detector)",
        fontsize=16, weight="bold")
ax.text(2, 8.8, "Source set to 750 mW (+28.75 dBm).  On each arrow: level entering the next block with minimum "
        "attenuation (bold) and maximum attenuation (grey).", fontsize=10.5, color="#444")

# ---- blocks
s_txt, s_col = status(P_SRC, split_max_dbm)
box(2, 42, 36, 30, "Pluto TX (source)",
    [("ADALM-Pluto, 1.0-1.2 GHz tone", 9.2, "#111"),
     ("Set to 750 mW (+28.75 dBm)", 9.2, "#111"),
     ("Real Pluto max: a few dBm", 9.0, RED),
     ("(about 5 mW). 750 mW needs", 9.0, RED),
     ("an external power amplifier.", 9.0, RED)],
    GREY, face="#f5f5f5")

box(62, 42, 42, 30, "50 ohm Splitter",
    [("Part: ZFRSC-42-S+", 9.2, "#111"),
     ("Atten: 6.0 min / 6.5 max dB", 9.2, "#111"),
     ("Max in: +28.75 dBm (750 mW)", 9.2, "#111"),
     ("Input: " + s_txt, 9.2, s_col)],
    BLUE, photo="photos/ZFRSC-42-Splus.jpeg")

box(126, 12, 34, 22, "Cable A  (4 in)",
    [("Coax, RG-316 class (assumed)", 9.0, "#111"),
     ("Atten: %.2f min / %.2f max dB" % CAB_A, 9.0, "#111"),
     ("0.45-0.60 dB/ft + 0.1 dB SMA", 8.4, AMBER)],
    GREY, face="#fdf7e7")
box(126, 80, 34, 22, "Cable B  (8.5 in)",
    [("Coax, RG-316 class (assumed)", 9.0, "#111"),
     ("Atten: %.2f min / %.2f max dB" % CAB_B, 9.0, "#111"),
     ("4.5 in longer than cable A", 8.4, "#444")],
    GREY, face="#fdf7e7")

ra_txt, ra_col = status(a_out[0], mix_max_dbm)
rb_txt, rb_col = status(b_out[0], mix_max_dbm)
box(184, 38, 44, 38, "Frequency mixer",
    [("(phase detector)", 9.2, "#444"),
     ("Part: ZX05-30W-S+", 9.2, "#111"),
     ("Conv loss: 6.22 min / 9.0 max dB", 9.0, "#111"),
     ("Max RF in: +16.99 dBm (50 mW)", 9.0, "#111"),
     ("RF (cable A): " + ra_txt, 9.0, ra_col),
     ("LO (cable B): " + rb_txt, 9.0, rb_col),
     ("Level 7: LO wants +7 dBm", 8.6, "#444")],
    BLUE, photo="photos/ZX05-30W-Splus.jpeg")

# ---- arrows with labels in the gaps
arrow((38.8, 57), (61.2, 57), short(P_SRC), "direct, no loss", lx=50, ly=50)
arrow((104.8, 50), (125.2, 23), short(split_out[0]), short(split_out[1]), lx=115, ly=36)
arrow((104.8, 64), (125.2, 91), short(split_out[0]), short(split_out[1]), lx=115, ly=78)
arrow((160.8, 23), (185, 42), short(a_out[0]), short(a_out[1]), lx=172, ly=26)
arrow((160.8, 91), (185, 72), short(b_out[0]), short(b_out[1]), lx=172, ly=90)
ax.text(180.5, 36.5, "RF", fontsize=10, weight="bold", color=BLUE)
ax.text(180.5, 78.5, "LO", fontsize=10, weight="bold", color=BLUE)

# ---- IF / DC out
ax.add_patch(FancyArrowPatch((206, 76.8), (206, 93), arrowstyle="-|>", mutation_scale=18, lw=1.8, color="#222"))
ax.text(206, 96.5, "IF out = DC, scales with cos(2 pi f dt)", fontsize=9.4, ha="center", weight="bold")
ax.text(206, 100.3, "peak: " + short(if_out[0]) + " (min)", fontsize=9.0, ha="center")
ax.text(206, 103.8, short(if_out[1]) + " (max atten)", fontsize=9.0, ha="center", color="#555")

# ---- summary
ax.text(2, 106, "What this means at 750 mW", fontsize=11.5, weight="bold", color="#111")
ax.text(2, 110.5, "Splitter input is exactly on its 0.75 W", fontsize=9.6, color=RED)
ax.text(2, 114.0, "damage rating (no margin).", fontsize=9.6, color=RED)
ax.text(2, 118.5, "Both mixer ports get ~+22 dBm (~175 mW),", fontsize=9.6, color=RED, weight="bold")
ax.text(2, 122.0, "3.5x its 50 mW max: it would be damaged.", fontsize=9.6, color=RED, weight="bold")
ax.text(70, 106, "Safe source levels", fontsize=11.5, weight="bold", color="#111")
ax.text(70, 110.5, "Max without damaging the mixer: %s" % short(safe_src), fontsize=9.6, color=GREEN, weight="bold")
ax.text(70, 114.0, "For the mixer's nominal +7 dBm LO: %s" % short(lo_target_src), fontsize=9.6, color=GREEN, weight="bold")
ax.text(70, 118.5, "Splitter and mixer values: datasheets (see the power-ratings doc).", fontsize=9.0, color="#444")
ax.text(70, 122.0, "Cable loss is ASSUMED - swap in your cable's datasheet values.", fontsize=9.0, color=AMBER)

out = "JACON_bench_delayline_flow.png"
fig.savefig(out, dpi=140, facecolor="white", bbox_inches="tight")
print("wrote", out)
print("source      %s" % fmt(P_SRC))
print("split out   %s .. %s" % (fmt(split_out[0]), fmt(split_out[1])))
print("cable A out %s .. %s" % (fmt(a_out[0]), fmt(a_out[1])))
print("cable B out %s .. %s" % (fmt(b_out[0]), fmt(b_out[1])))
print("IF peak     %s .. %s" % (fmt(if_out[0]), fmt(if_out[1])))
print("safe source %s ; LO-target source %s" % (fmt(safe_src), fmt(lo_target_src)))
