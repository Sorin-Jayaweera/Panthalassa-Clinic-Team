"""JACON signal chain with per-block frequency, gain/loss and power limits."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OURS = "#1f5fbf"; OTHER = "#9a9a9a"; RED = "#b03030"
fig, ax = plt.subplots(figsize=(19, 12))
ax.set_xlim(0, 100); ax.set_ylim(0, 64); ax.axis("off")

def box(x, y, w, h, title, sub, ours=True, fs=8.0):
    c = OURS if ours else OTHER
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25",
                 linewidth=1.9 if ours else 1.1, edgecolor=c,
                 facecolor="#eaf1fb" if ours else "#f2f2f2", zorder=2))
    ax.text(x+w/2, y+h-1.1, title, ha="center", va="top", fontsize=fs+1.3,
            weight="bold", color=c if ours else "#555", zorder=3)
    ax.text(x+w/2, y+h-2.9, sub, ha="center", va="top", fontsize=fs-0.8,
            color="#222", zorder=3, linespacing=1.4)
    return (x, y, w, h)

def arrow(b1, b2, label="", lab_dy=0.7):
    x1,y1,w1,h1 = b1; x2,y2,w2,h2 = b2
    p1 = (x1+w1, y1+h1/2); p2 = (x2, y2+h2/2)
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13,
                 linewidth=1.3, color="#333", zorder=1))
    if label:
        ax.text((p1[0]+p2[0])/2, (p1[1]+p2[1])/2+lab_dy, label, ha="center",
                va="bottom", fontsize=7.6, color=RED, weight="bold", zorder=4)

def stub_out(b, label, frac=0.5, down=True, length=3.0):
    """short arrow leaving a box vertically, with a text tag (no long crossing lines)"""
    x,y,w,h = b
    x0 = x + w*frac
    y0 = y if down else y+h
    y1 = y0 - length if down else y0 + length
    ax.add_patch(FancyArrowPatch((x0,y0),(x0,y1), arrowstyle="-|>", mutation_scale=11,
                 linewidth=1.2, color="#333", zorder=1))
    ax.text(x0, y1-0.5 if down else y1+0.5, label, ha="center",
            va="top" if down else "bottom", fontsize=7.3, color=RED, weight="bold")

def stub_in(b, label, frac=0.5, frm_below=False, length=3.0):
    x,y,w,h = b
    x0 = x + w*frac
    y0 = (y - length) if frm_below else (y + h + length)
    y1 = y if frm_below else y+h
    ax.add_patch(FancyArrowPatch((x0,y0),(x0,y1), arrowstyle="-|>", mutation_scale=11,
                 linewidth=1.2, color="#333", zorder=1))
    ax.text(x0, y0-0.4 if frm_below else y0+0.4, label, ha="center",
            va="top" if frm_below else "bottom", fontsize=7.3, color=RED, weight="bold")

ax.text(1, 62.4, "JACON signal chain - operating band, gain/loss and power limits per component",
        fontsize=15, weight="bold")
ax.text(1, 60.6, "Blue = the 9 parts we have (every number datasheet-verified, see evidence table).  "
        "Grey = other blocks from the drawing.  Red = expected level, LTspice model at a -30 dBm radar echo.",
        fontsize=9, color="#444")

# ---------------- RX row
Y=48.0; H=8.8
b_ant  = box(1.0,  Y,  9.0, H, "RX ANTENNA", "horn 8.2-12.4 GHz\n-50 to -10 dBm echo", ours=False)
b_lim  = box(13.0, Y, 10.5, H, "POWER LIMITER", "9.3-9.5 GHz\nclamps to ~+17 dBm\n(not one of the 9)", ours=False)
b_lna  = box(26.5, Y, 13.5, H, "ZX60-5123LN+", "LNA  9.3-9.5 GHz\ngain +22.0 dB typ\nP1dB +17.0 dBm\nmax in +15 dBm (31.6 mW)")
b_mix1 = box(43.0, Y, 14.0, H, "ZX05-14LH-S+", "RX mixer  RF 9.3-9.5 GHz\nLO 8.3 GHz -> IF 1.0-1.2 GHz\nconv. loss 6.7 dB typ\nmax RF 50 mW (+17 dBm)")
b_ifa  = box(60.0, Y, 15.0, H, "ZX60-P162LN+", "IF amp  1.0-1.2 GHz\ngain +22.5 dB typ\nP1dB +19.9 dBm\nmax in +25 dBm (316 mW)")
b_sp1  = box(78.0, Y, 15.0, H, "ZFRSC-42-S+", "IF splitter  DC-4.2 GHz\n-6.0 dB total loss\nmax in 0.75 W (+28.8 dBm)")
arrow(b_ant, b_lim, "-30 dBm"); arrow(b_lim, b_lna, "-30.5 dBm")
arrow(b_lna, b_mix1, "-8.5 dBm"); arrow(b_mix1, b_ifa, "-15.2 dBm"); arrow(b_ifa, b_sp1, "+7.3 dBm")
stub_in(b_mix1, "", frac=0.5, frm_below=True, length=3.2)
ax.text(60.0, Y-7.4, "IF amp alternates for this slot:   ZX60-P103LN+  (+15.6 dB typ, max in +21 dBm)      "
        "ZX60-2534MA-S+ (+43.5 dB typ, max in -15 dBm = 0.032 mW)",
        ha="left", va="top", fontsize=7.8, color="#8a4b00", weight="bold")
stub_out(b_sp1, "to limiting amp\n+1.3 dBm", frac=0.28, length=3.2)
stub_out(b_sp1, "to envelope det\n+1.3 dBm", frac=0.78, length=3.2)

# ---------------- LO row
Y2=34.0; H2=8.4
b_pll  = box(13.0, Y2, 12.0, H2, "PLL / LO SOURCE", "ADF5355 @ 8.3 GHz\n(not one of the 9)", ours=False)
b_buf  = box(29.0, Y2, 14.5, H2, "ZX60-14012L-S+", "LO buffer  8.3 GHz\n0.3 MHz-14 GHz, +12 dB typ\nP1dB +11 dBm\nmax in +10 dBm (10 mW)")
b_sp2  = box(47.5, Y2, 15.0, H2, "ZX10-2-1252-S+", "LO splitter  1.8-12.5 GHz\n-3.0 dB split, 0.7 dB loss\nmax in 1.85 W (+32.7 dBm)")
arrow(b_pll, b_buf, "+3 dBm"); arrow(b_buf, b_sp2, "+14 dBm")
stub_out(b_sp2, "to RX mixer LO\n+10.3 dBm", frac=0.3, down=False, length=3.2)
stub_out(b_sp2, "to TX mixer LO\n+10.3 dBm", frac=0.72, down=True, length=3.2)

# ---------------- IF / delay-line row
Y3=19.5; H3=8.8
b_lima = box(1.0,  Y3, 12.5, H3, "LIMITING AMP", "3x gain block\n1.0-1.2 GHz\n(not one of the 9)", ours=False)
b_sp3  = box(17.0, Y3, 15.0, H3, "ZFRSC-42-S+", "delay-line splitter\nDC-4.2 GHz, -6.0 dB\nmax in 0.75 W (+28.8 dBm)")
b_dly  = box(35.5, Y3, 13.0, H3, "DELAY LINES", "arm A: L_ref\narm B: +4.5 in\n1.0-1.2 GHz", ours=False)
b_pd   = box(52.0, Y3, 16.0, H3, "ZX05-30W-S+", "phase detector  RF+LO 0.3-4 GHz\nLO +7 dBm, conv. loss 6.8 dB\nRF 1 dB comp +1 dBm\nmax RF 50 mW (+17 dBm)")
b_sh   = box(71.5, Y3, 11.0, H3, "SAMPLE / HOLD", "DC output\nADG1211 + 100 pF\n(not one of the 9)", ours=False)
b_env  = box(86.0, Y3, 12.0, H3, "ENVELOPE DET", "ADL5511\n1.0-1.2 GHz\n(not one of the 9)", ours=False)
stub_in(b_lima, "from IF splitter\n+1.3 dBm", frac=0.5, frm_below=False, length=3.2)
stub_in(b_env,  "from IF splitter\n+1.3 dBm", frac=0.5, frm_below=False, length=3.2)
arrow(b_lima, b_sp3, "+14.4 dBm"); arrow(b_sp3, b_dly, "+8.4 dBm")
arrow(b_dly, b_pd, "+8.0 dBm"); arrow(b_pd, b_sh, "DC")

# ---------------- TX row
Y4=5.0; H4=8.8
b_vco  = box(1.0,  Y4, 12.0, H4, "VCO + KEYING", "CVCO55BE 1.0-1.2 GHz\nADG901 Morse key\n(not one of the 9)", ours=False)
b_mix2 = box(16.5, Y4, 15.5, H4, "ZX05-14LH-S+", "TX mixer  IF 1.0-1.2 GHz\nLO 8.3 GHz -> RF 9.3-9.5 GHz\nconv. loss 6.7 dB typ\nmax RF 50 mW (+17 dBm)")
b_filt = box(35.5, Y4, 13.0, H4, "IMAGE FILTER", "VHF-8400+ HPF\npass 9.3-9.5 GHz\n(not one of the 9)", ours=False)
b_pa   = box(52.0, Y4, 12.5, H4, "POWER AMP", "9.3-9.5 GHz\n~1 W out\n(not one of the 9)", ours=False)
b_txa  = box(68.0, Y4, 11.0, H4, "TX ANTENNA", "9.3-9.5 GHz\npulsed Morse '. - .'", ours=False)
arrow(b_vco, b_mix2, "+2 dBm"); arrow(b_mix2, b_filt, "-4.7 dBm")
arrow(b_filt, b_pa, "-6.2 dBm"); arrow(b_pa, b_txa, "+26 dBm")
stub_in(b_mix2, "", frac=0.5, frm_below=False, length=3.2)

ax.text(1, 1.0, "Levels come from the LTspice model in simulations/claude/01_jacon_system (TEST 0, -30 dBm echo). "
        "Gains, losses, bands and power limits are datasheet values; the evidence table lists the page for each.",
        fontsize=8.2, color="#444")
fig.tight_layout()
fig.savefig("JACON_component_flowchart.png", dpi=150, facecolor="white")
print("wrote JACON_component_flowchart.png")
