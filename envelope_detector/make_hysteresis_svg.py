"""Draw comparator_hysteresis.svg: where the hysteresis resistor goes in Test B.

    python3 make_hysteresis_svg.py
"""
import os

SIG, OUT, GND, SHIELD, FB, INK, INK2, BOX, FILL, PLANE, WARN = (
    "#2a78d6", "#1f9d6b", "#111111", "#8e8e8e", "#b23a1e", "#0b0b0b", "#52514e", "#8a8985", "#f4f3ef", "#dfe9df", "#b23a1e")
o = []


def T(x, y, s, size=12, c=INK2, a="start", b=False):
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" text-anchor="{a}"{" font-weight=\"bold\"" if b else ""}>{s}</text>')


def L(pts, c, w=2.4, dash=None, cap="round"):
    o.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{c}" stroke-width="{w}" '
             f'stroke-linejoin="round" stroke-linecap="{cap}"{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>')


def D(x, y, c, r=5):
    o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>')


def R(x, y, lab, c=INK, w=44, bold=True, below=False):
    o.append(f'<rect x="{x-w/2}" y="{y-9}" width="{w}" height="18" fill="#fff" stroke="{c}" stroke-width="1.8"/>')
    T(x, y + (30 if below else -15), lab, 12.5, c, "middle", bold)


def coax(pts, core):
    L(pts, SHIELD, 11, cap="butt"); L(pts, "#ffffff", 6, cap="butt"); L(pts, core, 2.6, cap="butt")


def grab(x, y, color):
    o.append(f'<rect x="{x-8}" y="{y-5}" width="16" height="10" rx="3" fill="{color}"/>')


W, H = 1400, 860
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif" fill="{INK}">')
o.append(f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>')
T(30, 34, "Test B with hysteresis: ONE extra resistor, between two red grabbers that already exist", 20, INK, "start", True)
T(30, 57, "Nothing goes on the board, nothing into J2, no new ground wires. Everything else stays exactly as in comparator_grounding.svg.", 13)

# board
bx, by, bw, bh = 520, 140, 360, 360
o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{PLANE}" stroke="{BOX}" stroke-width="1.8"/>')
T(bx + bw / 2, by + bh / 2 - 10, "EVAL-ADCMP604BKSZ", 15, INK, "middle", True)
T(bx + bw / 2, by + bh / 2 + 10, "(J3, J8, supply, J2, J4: unchanged)", 11.5, INK2, "middle")
J1, J7 = (bx, by + 90), (bx + bw, by + 90)
for (x, y), lab in ((J1, "J1 IN+"), (J7, "J7 OUT+")):
    o.append(f'<rect x="{x-14}" y="{y-14}" width="28" height="28" rx="4" fill="#d9b24a" stroke="{INK}" stroke-width="1.4"/>')
    T(x, y - 22, lab, 12.5, INK, "middle", True)

# group 2 (IN+) on the left
gy = 330
coax([(J1[0] - 14, J1[1]), (440, J1[1]), (440, gy)], SIG)
T(470, J1[1] + 26, "J1 cable", 11, INK2, "middle")
L([(440, gy), (430, gy), (420, gy - 14), (405, gy - 14)], SIG); grab(397, gy - 14, "#d43c3c")
L([(440, gy), (430, gy), (420, gy + 14), (405, gy + 14)], GND); grab(397, gy + 14, "#222")
coax([(60, gy), (160, gy)], SIG)
T(110, gy - 20, "from CGR-201 C2BJ0VL", 11, INK2, "middle")
L([(160, gy), (170, gy), (180, gy - 14), (195, gy - 14)], SIG); grab(203, gy - 14, "#d43c3c")
L([(160, gy), (170, gy), (180, gy + 14), (195, gy + 14)], GND); grab(203, gy + 14, "#222")
R(300, gy - 14, "100 Ω (existing)")
L([(211, gy - 14), (278, gy - 14)], SIG); L([(322, gy - 14), (389, gy - 14)], SIG)
L([(211, gy + 14), (389, gy + 14)], GND, 3)
D(389, gy - 14, FB, 6)
T(389, gy + 46, "IN+ point", 12, FB, "middle", True)
T(389, gy + 62, "(J1 cable's red grabber)", 11, FB, "middle")
o.append(f'<rect x="40" y="{gy-60}" width="430" height="140" rx="10" fill="none" stroke="{SIG}" stroke-width="1.6" stroke-dasharray="7 4"/>')
T(50, gy + 100, "Group 2 (IN+), as now", 12, SIG, "start", True)

# group 3 (outputs) on the right
coax([(J7[0] + 14, J7[1]), (960, J7[1]), (960, gy)], OUT)
T(930, J7[1] + 26, "J7 cable", 11, INK2, "middle")
L([(960, gy), (970, gy), (980, gy - 14), (995, gy - 14)], OUT); grab(1003, gy - 14, "#d43c3c")
L([(960, gy), (970, gy), (980, gy + 14), (995, gy + 14)], GND); grab(1003, gy + 14, "#222")
L([(1011, gy - 14), (1110, gy - 14), (1110, gy + 30)], OUT)
o.append(f'<rect x="1102" y="{gy+30}" width="16" height="40" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
T(1126, gy + 55, "100 Ω to the J8 red grabber (existing)", 11.5, INK, "start", True)
L([(1011, gy + 14), (1060, gy + 14)], GND, 3)
T(1066, gy + 18, "to J8 black + CH3/CH4 grounds", 11, INK2)
D(1011, gy - 14, FB, 6)
T(1080, gy - 40, "OUT+ point", 12, FB, "start", True)
T(1080, gy - 24, "(J7 cable's red grabber)", 11, FB, "start")
o.append(f'<rect x="930" y="{gy-80}" width="440" height="170" rx="10" fill="none" stroke="{OUT}" stroke-width="1.6" stroke-dasharray="7 4"/>')
T(940, gy + 110, "Group 3 (outputs), as now", 12, OUT, "start", True)

# the new resistor
fy = 600
L([(389, gy - 14), (389, fy), (660, fy)], FB, 2.8)
L([(740, fy), (1011, fy), (1011, gy - 14)], FB, 2.8)
R(700, fy, "Rf ≈ 3.9–4.7 kΩ  (NEW)", c=FB, w=80)
T(700, fy + 34, "one resistor, two clips: one leg on each red grabber above", 12, FB, "middle", True)
T(700, fy + 52, "keep its leads as short as the bench allows; no other wire, no ground", 12, FB, "middle")

# explanation
ex, ey = 40, 690
o.append(f'<rect x="{ex}" y="{ey}" width="1320" height="150" rx="10" fill="#fff" stroke="{BOX}" stroke-width="1.4"/>')
T(ex + 16, ey + 26, "How it works", 13.5, INK, "start", True)
lines = [
    "When OUT+ goes high (+0.39 V relative to low), a small current flows through Rf into the IN+ point and lifts IN+ a little: the output holds itself high.",
    "To switch back, IN+ must fall below the threshold by that extra lift. Hysteresis ≈ 0.39 V × Rs / (Rs + Rf), with Rs = 100 Ω + the CGR-201's own 50 Ω = 150 Ω.",
    "Rf 5.6 kΩ → about 10 mV;  4.7 kΩ → about 12 mV;  3.9 kΩ → about 14 mV;  2 kΩ → about 27 mV.  Rs sets how far IN+ can be lifted.",
    "Why not J2: J2 is the same node as J1, but reaching it needs another cable, which adds a long loop. The J1 red grabber is the same node and already exposed.",
]
for i, s in enumerate(lines):
    T(ex + 16, ey + 52 + i * 22, s, 12, INK)
T(W - 30, H - 8, "Draft, 23 Nov 2026", 11, INK2, "end")
o.append("</svg>")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparator_hysteresis.svg")
open(out, "w").write("\n".join(o))
print("saved", out)
