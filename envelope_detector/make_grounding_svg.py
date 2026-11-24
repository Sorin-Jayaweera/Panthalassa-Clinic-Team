"""Draw comparator_grounding.svg: Test B ground connections (three local groups).

    python3 make_grounding_svg.py
"""
import os

SIG, THR, OUT, PWR, GND, SHIELD, PROBE, INK, INK2, BOX, FILL, PLANE, WARN = (
    "#2a78d6", "#eb6834", "#1f9d6b", "#d43c3c", "#111111", "#8e8e8e", "#7b4fc4",
    "#0b0b0b", "#52514e", "#8a8985", "#f4f3ef", "#dfe9df", "#b23a1e")
o = []


def T(x, y, s, size=12, c=INK2, a="start", b=False):
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" text-anchor="{a}"{" font-weight=\"bold\"" if b else ""}>{s}</text>')


def L(pts, c, w=2.4, dash=None, cap="round"):
    o.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{c}" stroke-width="{w}" '
             f'stroke-linejoin="round" stroke-linecap="{cap}"{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>')


def D(x, y, c, r=4.5):
    o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>')


def R(x, y, lab, vert=False, below=False):
    if vert:
        o.append(f'<rect x="{x-8}" y="{y-20}" width="16" height="40" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
        T(x + 13, y + 5, lab, 12, INK, "start", True)
    else:
        o.append(f'<rect x="{x-20}" y="{y-8}" width="40" height="16" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
        T(x, y + (26 if below else -13), lab, 12, INK, "middle", True)


def C(x, y, lab, c=THR, h=20, left=True):
    """Vertical capacitor hanging from (x, y); returns its bottom terminal."""
    L([(x, y), (x, y + h)], c)
    o.append(f'<line x1="{x-12}" y1="{y+h}" x2="{x+12}" y2="{y+h}" stroke="{INK}" stroke-width="2.6"/>'
             f'<line x1="{x-12}" y1="{y+h+7}" x2="{x+12}" y2="{y+h+7}" stroke="{INK}" stroke-width="2.6"/>')
    T(x + (-16 if left else 16), y + h + 8, lab, 12, INK, "end" if left else "start", True)
    return (x, y + h + 7)


def coax(pts, core):
    L(pts, SHIELD, 11, cap="butt")
    L(pts, "#ffffff", 6, cap="butt")
    L(pts, core, 2.6, cap="butt")


def grabbers(x, y, core, dx=1, sep=26):
    """Split a coax end at (x, y) into red (core) and black (shield) grabbers; returns their clip points."""
    r, b = (x + dx * 40, y - sep / 2), (x + dx * 40, y + sep / 2)
    L([(x, y), (x + dx * 14, y), (x + dx * 24, r[1]), r], core, 2.4)
    L([(x, y), (x + dx * 14, y), (x + dx * 24, b[1]), b], GND, 2.4)
    for (gx, gy), c in ((r, "#d43c3c"), (b, "#222")):
        o.append(f'<rect x="{gx-(0 if dx > 0 else 16)}" y="{gy-5}" width="16" height="10" rx="3" fill="{c}"/>')
    return (r[0] + dx * 16, r[1]), (b[0] + dx * 16, b[1])


def connector(x, y, name, label, side):
    o.append(f'<rect x="{x-14}" y="{y-14}" width="28" height="28" rx="4" fill="#d9b24a" stroke="{INK}" stroke-width="1.4"/>')
    o.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#fff" stroke="{INK}"/>')
    T(x, y + (32 if side == "below" else -22), f"{name} {label}", 12.5, INK, "middle", True)


def probe(x, y, ch, gx, gy, side=-1):
    """Probe tip at (x, y); its ground clip lands at (gx, gy)."""
    tx, ty = x, y + side * 44
    L([(x, y), (tx, ty)], PROBE, 2.2, "4 3")
    o.append(f'<rect x="{tx-30}" y="{ty-(22 if side < 0 else 0)}" width="60" height="22" rx="11" fill="{PROBE}"/>')
    T(tx, ty - (7 if side < 0 else -15), f"{ch} ×10", 11.5, "#fff", "middle", True)
    yy = ty - 11 if side < 0 else ty + 11
    L([(tx + 30, yy), (gx, yy), (gx, gy)], GND, 1.6, "2 3")
    D(x, y, PROBE, 4)
    D(gx, gy, GND, 4)


W, H = 1500, 1080
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="Helvetica, Arial, sans-serif" fill="{INK}">')
o.append(f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>')
T(30, 34, "Test B grounding: one ground return per cable, tied locally in three groups", 20, INK, "start", True)
T(30, 57, "Grey tube = coax shield (ground). Inside it, the signal wire. At the far end each BNC-to-grabber cable "
          "splits into a red (signal) and a black (shield) grabber.", 13)

# ---------------- board
bx, by, bw, bh = 560, 230, 380, 470
o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{PLANE}" stroke="{BOX}" stroke-width="1.8"/>')
T(bx + bw / 2, by + bh / 2 - 22, "EVAL-ADCMP604BKSZ", 15, INK, "middle", True)
T(bx + bw / 2, by + bh / 2 - 3, "green = the board's ground plane:", 12, INK2, "middle")
T(bx + bw / 2, by + bh / 2 + 13, "every SMA's outer shell is soldered to it", 12, INK2, "middle")
o.append(f'<rect x="{bx+bw/2-22}" y="{by+bh/2+30}" width="44" height="30" rx="3" fill="#333"/>')
T(bx + bw / 2, by + bh / 2 + 50, "chip", 11, "#fff", "middle", True)
J1, J3, J7, J8 = (bx, by + 110), (bx, by + 360), (bx + bw, by + 110), (bx + bw, by + 360)
connector(*J1, "J1", "IN+", "above")
connector(*J3, "J3", "IN−", "below")
connector(*J7, "J7", "OUT+", "above")
connector(*J8, "J8", "OUT−", "below")
J2 = (bx + 130, by)
connector(*J2, "J2", "IN+FB", "below")
T(J2[0] + 26, J2[1] + 44, "(same node as J1): nothing attached", 11, INK2)
# jacks
for x, lab in ((bx + 70, "VCC"), (bx + 150, "AGND"), (bx + 250, "CGND/VEE")):
    o.append(f'<circle cx="{x}" cy="{by+bh-40}" r="11" fill="{PWR if lab == "VCC" else "#444"}" stroke="{INK}" stroke-width="1.4"/>')
    T(x, by + bh - 58, lab, 11.5, INK, "middle", True)
L([(bx + 150, by + bh - 22), (bx + 150, by + bh - 10), (bx + 250, by + bh - 10), (bx + 250, by + bh - 22)], GND, 2.6)
T(bx + 200, by + bh - 84, "AGND–CGND/VEE joined by the TP15–TP13 link (keep)", 11, INK, "middle")

# J4 with the recommended capacitor straight into it
J4 = (bx + 330, by + bh)
connector(*J4, "J4", "IN−FB", "above")
T(J4[0] + 36, J4[1] - 18, "(same node as J3)", 11, INK2, "start")
cb = C(J4[0], J4[1] + 14, "", c=WARN, h=14, left=False)
L([cb, (cb[0], cb[1] + 10), (J4[0] + 22, cb[1] + 10), (J4[0] + 22, J4[1] + 10)], GND, 2.2)
T(J4[0] + 30, J4[1] + 32, "1–10 nF: centre socket", 11.5, WARN, "start", True)
T(J4[0] + 30, J4[1] + 47, "to J4's own shell", 11.5, WARN, "start", True)
o.append(f'<rect x="{J4[0]-30}" y="{J4[1]-52}" width="200" height="114" rx="8" fill="none" stroke="{WARN}" '
         f'stroke-width="1.6" stroke-dasharray="6 4"/>')
T(J4[0] - 26, J4[1] + 78, "NEXT CHANGE (recommended)", 11.5, WARN, "start", True)

# supply
sy = by + bh + 110
o.append(f'<rect x="{bx}" y="{sy}" width="380" height="70" rx="8" fill="{FILL}" stroke="{BOX}" stroke-width="1.6"/>')
T(bx + 190, sy + 24, "Bench supply 3.30 V, limit 30 mA", 13, INK, "middle", True)
L([(bx + 70, by + bh - 29), (bx + 70, sy)], PWR, 2.6)
T(bx + 78, sy - 12, "+", 14, PWR, "start", True)
L([(bx + 250, by + bh - 29), (bx + 250, sy)], GND, 2.6)
T(bx + 258, sy - 12, "COM", 12, GND, "start", True)
T(bx + 190, sy + 56, "On board ground pins: only COM and the TP link.", 11.5, INK2, "middle")

# ---------------- group 2: IN+ (top left)
g2 = (330, 340)
coax([(J1[0] - 14, J1[1]), (g2[0] + 70, J1[1]), (g2[0] + 70, g2[1])], SIG)
T(470, J1[1] + 28, "J1 cable", 11, INK2, "middle")
r2, k2 = grabbers(g2[0] + 70, g2[1], SIG, dx=-1)
o.append(f'<rect x="30" y="{g2[1]-150}" width="190" height="64" rx="8" fill="{FILL}" stroke="{BOX}" stroke-width="1.6"/>')
T(125, g2[1] - 122, "CGR-201 C2BJ0VL", 13, INK, "middle", True)
T(125, g2[1] - 104, "Output BNC (its shell = CGR ground)", 11, INK2, "middle")
coax([(220, g2[1] - 118), (240, g2[1] - 118), (240, g2[1] - 72), (40, g2[1] - 72), (40, g2[1]), (90, g2[1])], SIG)
r2c, k2c = grabbers(90, g2[1], SIG, dx=1)
rm = (r2c[0] + r2[0]) / 2 - 25
R(rm, r2[1], "100 Ω")
L([r2c, (rm - 20, r2[1])], SIG)
L([(rm + 20, r2[1]), r2], SIG)
L([k2c, k2], GND, 3.2)
D(r2[0] - 20, r2[1], SIG)
probe(r2[0] - 20, r2[1], "CH1", r2[0] - 20 + 50, k2[1], side=-1)
o.append(f'<rect x="60" y="{g2[1]-62}" width="330" height="102" rx="10" fill="none" stroke="{SIG}" stroke-width="1.6" stroke-dasharray="7 4"/>')
T(70, g2[1] + 60, "Group 2 (IN+): both black grabbers + CH1 ground together.", 12, SIG, "start", True)
T(70, g2[1] + 76, "CH1 tip on the J1 cable's red grabber (board side of the 100 Ω).", 12, SIG, "start", True)
T(70, g2[1] + 94, "As built, the 100 Ω is at the FAR end of the J1 cable, so the", 11, WARN)
T(70, g2[1] + 108, "cable (~100 pF/m) hangs directly on IN+. Note it in results.", 11, WARN)

# ---------------- group 1: IN− (bottom left)
g1 = (330, 600)
coax([(J3[0] - 14, J3[1]), (g1[0] + 70, J3[1]), (g1[0] + 70, g1[1])], THR)
T(470, J3[1] + 28, "J3 cable", 11, INK2, "middle")
r1, k1 = grabbers(g1[0] + 70, g1[1], THR, dx=-1, sep=64)
o.append(f'<rect x="30" y="{g1[1]+180}" width="190" height="64" rx="8" fill="{FILL}" stroke="{BOX}" stroke-width="1.6"/>')
T(125, g1[1] + 208, "CGR-201 C2BKNPC", 13, INK, "middle", True)
T(125, g1[1] + 226, "Output BNC", 11, INK2, "middle")
coax([(220, g1[1] + 212), (250, g1[1] + 212), (250, g1[1] + 162), (40, g1[1] + 162), (40, g1[1]), (90, g1[1])], THR)
r1c, k1c = grabbers(90, g1[1], THR, dx=1, sep=64)
mid = (r1c[0] + r1[0]) / 2
R(mid - 15, r1[1], "1 kΩ")
L([r1c, (mid - 35, r1[1])], THR)
L([(mid + 5, r1[1]), r1], THR)
D(mid + 40, r1[1], THR)
cg = C(mid + 40, r1[1], "100 nF")
L([cg, (cg[0], k1[1])], GND, 2.4)
L([k1c, k1], GND, 3.2)
D(cg[0], k1[1], GND, 5)
probe(mid + 40, r1[1], "CH2", cg[0] + 50, k1[1], side=-1)
o.append(f'<rect x="60" y="{g1[1]-62}" width="330" height="124" rx="10" fill="none" stroke="{THR}" stroke-width="1.6" stroke-dasharray="7 4"/>')
T(70, g1[1] + 82, "Group 1 (IN−): both black grabbers + capacitor ground", 12, THR, "start", True)
T(70, g1[1] + 98, "+ CH2 ground, all clipped together.", 12, THR, "start", True)
T(70, g1[1] + 116, "As built, the 100 nF is at the FAR end of the J3 cable. A cable", 11, WARN)
T(70, g1[1] + 130, "shorted at one end can ring (quarter-wave stub; ~27 MHz for ~1.9 m).", 11, WARN)
T(70, g1[1] + 144, "The capacitor in J4 holds IN− at the board instead.", 11, WARN)

# ---------------- group 3: outputs (right)
g3x = 1160
coax([(J7[0] + 14, J7[1]), (g3x - 60, J7[1]), (g3x - 60, 400)], OUT)
coax([(J8[0] + 14, J8[1]), (g3x - 60, J8[1]), (g3x - 60, 520)], OUT)
T(1040, J7[1] - 16, "J7 cable", 11, INK2, "middle")
T(1040, J8[1] + 28, "J8 cable", 11, INK2, "middle")
r7, k7 = grabbers(g3x - 60, 400, OUT, dx=1)
r8, k8 = grabbers(g3x - 60, 520, OUT, dx=1)
xr = g3x + 40
L([r7, (xr, r7[1]), (xr, 440)], OUT)
L([r8, (xr, r8[1]), (xr, 480)], OUT)
R(xr, 460, "100 Ω", True)
xg = g3x + 50
L([k7, (xg, k7[1])], GND, 2.4)
L([k8, (xg, k8[1])], GND, 2.4)
L([(xg, k7[1]), (xg, k8[1])], GND, 3.2)
D(xg, (k7[1] + k8[1]) / 2, GND, 5)
T(xg + 8, (k7[1] + k8[1]) / 2 + 32, "short link", 11, INK, "start")
probe(xr, r7[1], "CH3", xg + 60, k7[1], side=-1)
probe(xr, r8[1], "CH4", xg + 60, k8[1], side=1)
L([(xg, k7[1]), (xg + 60, k7[1])], GND, 2.4)
L([(xg, k8[1]), (xg + 60, k8[1])], GND, 2.4)
o.append(f'<rect x="{g3x-30}" y="320" width="300" height="290" rx="10" fill="none" stroke="{OUT}" stroke-width="1.6" stroke-dasharray="7 4"/>')
T(g3x - 20, 640, "Group 3 (outputs): J7 + J8 black grabbers joined;", 12, OUT, "start", True)
T(g3x - 20, 656, "CH3 and CH4 grounds on that link.", 12, OUT, "start", True)
T(g3x - 20, 676, "100 Ω at the FAR end is correct here: it stands", 11, INK2)
T(g3x - 20, 690, "in for the receiver at the end of the line.", 11, INK2)
T(g3x - 20, 708, "If J7 has a plain BNC cable: its shell, via a", 11, INK2)
T(g3x - 20, 722, "BNC-to-grabber adapter, to the same link.", 11, INK2)

# ---------------- explanation box
ex, ey = 980, 92
o.append(f'<rect x="{ex}" y="{ey}" width="490" height="190" rx="10" fill="#fff" stroke="{BOX}" stroke-width="1.4"/>')
T(ex + 14, ey + 24, "Why a black grabber already IS board ground", 13.5, INK, "start", True)
for i, s in enumerate(["board ground plane", "SMA connector's outer shell (soldered to it)",
                       "SMA-to-BNC adapter body (metal, screwed on)", "BNC plug shell",
                       "coax shield (the grey tube)", "black grabber at the far end"]):
    T(ex + 20, ey + 48 + i * 21, ("→ " if i else "   ") + s, 12, INK)
T(ex + 14, ey + 180, "Metal touching metal the whole way: no extra wire needed. DMM check ≈ 0 Ω.", 11.5, INK2)

# ---------------- rules
T(30, H - 62, "Don't: clip any black grabber or probe ground to a board pin too (a second path = a loop).", 12.5, PWR, "start", True)
T(30, H - 42, "Don't: add wires between the three groups (they already meet through the board).", 12.5, PWR, "start", True)
T(W - 30, H - 20, "Revised 23 Nov 2026: CH1 added; part positions as built; J4 capacitor recommended", 11, INK2, "end")
o.append("</svg>")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparator_grounding.svg")
open(out, "w").write("\n".join(o))
print("saved", out)
