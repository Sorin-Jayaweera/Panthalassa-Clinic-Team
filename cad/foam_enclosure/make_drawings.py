"""Shop drawings for the AN-72 foam enclosure: sheet 1 = cut plan, sheet 2 = assembly views.

Same frame as build_foam_enclosure.py: X = width, Y = up, Z = depth, front (+Z) and bottom open.
Run:  python make_drawings.py   ->  foam_enclosure_drawings.pdf + sheet1_cut_plan.png + sheet2_assembly.png
"""
import os
from fractions import Fraction

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ---- dimensions (inches), shared with the SolidWorks model ----
W, D, H = 48.0, 48.0, 12.0
T = 0.236
BOARD = 24.0
ROTOR_L, ROTOR_H = 41.0, 5.0
WALL_H = H - T                       # 11.764
BACK_L = (W - 2 * T) / 2             # 23.764
SCRAP = BOARD - 2 * WALL_H           # 0.472

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATE = "2026-10-15"

C_TOP, C_SIDE, C_BACK = "#9aa3ad", "#5b6670", "#c7cdd3"
C_CUT, C_SCRAP, C_ROTOR = "#d62728", "#f2d0d0", "#e07b24"
DIM_KW = dict(fontsize=8, ha="center", va="center",
              bbox=dict(fc="white", ec="none", pad=0.6))


def frac(x):
    """Nearest 1/16 as a shop fraction, e.g. 11.764 -> 11 3/4."""
    f = Fraction(round(x * 16), 16)
    whole, rem = divmod(f, 1)
    if rem == 0:
        return f"{whole}"
    return f"{whole} {rem}" if whole else f"{rem}"


def lab(x):
    return f'{x:.3f}"  (~{frac(x)}")'


def dim_h(ax, x1, x2, y, y_from, text, ext=True):
    """Horizontal dimension at height y, extension lines down/up to y_from."""
    if ext:
        for x in (x1, x2):
            ax.plot([x, x], [y_from, y + (0.6 if y > y_from else -0.6)], lw=0.5, color="k")
    ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<->", lw=0.7, shrinkA=0, shrinkB=0))
    ax.text((x1 + x2) / 2, y, text, **DIM_KW)


def dim_v(ax, y1, y2, x, x_from, text, ext=True, rot=90):
    if ext:
        for y in (y1, y2):
            ax.plot([x_from, x + (0.6 if x > x_from else -0.6)], [y, y], lw=0.5, color="k")
    ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<->", lw=0.7, shrinkA=0, shrinkB=0))
    ax.text(x, (y1 + y2) / 2, text, rotation=rot, **DIM_KW)


def rect(ax, x, y, w, h, fc, label=None, ls="-", lw=0.8, hatch=None, alpha=1.0, fs=9, ec="k"):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, ls=ls, hatch=hatch, alpha=alpha))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, weight="bold")


def title_block(fig, title, sheet):
    ax = fig.add_axes([0.70, 0.015, 0.29, 0.10])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=1.2))
    ax.plot([0, 1], [0.55, 0.55], lw=0.6, color="k")
    ax.plot([0.62, 0.62], [0, 0.55], lw=0.6, color="k")
    ax.text(0.03, 0.78, title, fontsize=11, weight="bold", va="center")
    ax.text(0.03, 0.40, "AN-72 RF foam enclosure — Panthalassa clinic", fontsize=7.5, va="center")
    ax.text(0.03, 0.15, 'Stock: Laird ECCOSORB AN-72, 24 x 24 x 0.236" (6 mm)', fontsize=7, va="center")
    ax.text(0.65, 0.40, f"Units: inches   Date: {DATE}", fontsize=7, va="center")
    ax.text(0.65, 0.15, f"Sheet {sheet} of 2   Scale: as noted", fontsize=7, va="center")


def frame(fig):
    fig.add_artist(Rectangle((0.008, 0.008), 0.984, 0.984, transform=fig.transFigure,
                             fill=False, lw=1.5))


# ======================================================================================
# Sheet 1: cut plan
# ======================================================================================
def board_axes(fig, rect_):
    ax = fig.add_axes(rect_)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-7, 31); ax.set_ylim(-7, 31)
    return ax


def sheet_cut_plan():
    fig = plt.figure(figsize=(17, 11))
    frame(fig)
    fig.text(0.02, 0.965, "SHEET 1 — CUT PLAN (7 boards)", fontsize=16, weight="bold", va="top")
    fig.text(0.02, 0.935, "Each board drawn to scale, viewed face-on. Red dashed = cut line. "
             "Hatched = scrap. Measure from the edge marked ◄REF.", fontsize=9.5, va="top")

    # --- board A: x4, no cut ---
    ax = board_axes(fig, [0.01, 0.36, 0.32, 0.50])
    ax.set_title("BOARDS 1–4  (qty 4)\nno cuts — top sheets T1, T2, T3, T4", fontsize=11, weight="bold")
    rect(ax, 0, 0, BOARD, BOARD, C_TOP, "T1 / T2 / T3 / T4\n24 x 24 as supplied", fs=10)
    dim_h(ax, 0, BOARD, -3, 0, '24.000"')
    dim_v(ax, 0, BOARD, -3, 0, '24.000"')

    # --- board B: x2, rip into two wall strips ---
    ax = board_axes(fig, [0.34, 0.36, 0.32, 0.50])
    ax.set_title("BOARDS 5 & 6  (qty 2)\nrip into 2 strips each — side walls L1, L2, R1, R2",
                 fontsize=11, weight="bold")
    rect(ax, 0, 0, BOARD, WALL_H, C_SIDE, "L1  (board 5)\nR1  (board 6)\n24 x 11.764", fs=10)
    rect(ax, 0, WALL_H, BOARD, WALL_H, C_SIDE, "L2  (board 5)\nR2  (board 6)\n24 x 11.764", fs=10)
    rect(ax, 0, 2 * WALL_H, BOARD, SCRAP, C_SCRAP, hatch="////")
    for y, n in ((WALL_H, "CUT 1"), (2 * WALL_H, "CUT 2")):
        ax.plot([-1, BOARD + 1], [y, y], color=C_CUT, lw=1.6, ls="--")
        ax.text(BOARD + 1.3, y, n, color=C_CUT, fontsize=8, va="center", weight="bold")
    ax.text(-0.3, -0.9, "◄REF edge", fontsize=7, ha="left")
    dim_h(ax, 0, BOARD, -3, 0, '24.000"')
    dim_v(ax, 0, WALL_H, -3, 0, lab(WALL_H))
    dim_v(ax, WALL_H, 2 * WALL_H, -3, 0, lab(WALL_H))
    ax.text(BOARD / 2, BOARD + 1.2, f'{SCRAP:.3f}" scrap strip (hatched)', fontsize=8, ha="center")

    # --- board C: x1, rip + crosscut into back strips ---
    ax = board_axes(fig, [0.67, 0.36, 0.32, 0.50])
    ax.set_title("BOARD 7  (qty 1)\nrip into 2 strips, trim each to length — back wall B1, B2",
                 fontsize=11, weight="bold")
    rect(ax, 0, 0, BACK_L, WALL_H, C_BACK, "B1\n23.764 x 11.764", fs=10)
    rect(ax, 0, WALL_H, BACK_L, WALL_H, C_BACK, "B2\n23.764 x 11.764", fs=10)
    rect(ax, BACK_L, 0, BOARD - BACK_L, 2 * WALL_H, C_SCRAP, hatch="////")
    rect(ax, 0, 2 * WALL_H, BOARD, SCRAP, C_SCRAP, hatch="////")
    for y, n in ((WALL_H, "CUT 1"), (2 * WALL_H, "CUT 2")):
        ax.plot([-1, BOARD + 1], [y, y], color=C_CUT, lw=1.6, ls="--")
        ax.text(BOARD + 1.3, y, n, color=C_CUT, fontsize=8, va="center", weight="bold")
    ax.plot([BACK_L, BACK_L], [-1, 2 * WALL_H + 0.5], color=C_CUT, lw=1.6, ls="--")
    ax.text(BACK_L, -1.6, "CUT 3", color=C_CUT, fontsize=8, ha="center", weight="bold")
    ax.text(-0.3, -0.9, "◄REF edge", fontsize=7, ha="left")
    dim_h(ax, 0, BACK_L, -4, 0, lab(BACK_L))
    dim_h(ax, BACK_L, BOARD, 27, BOARD, '0.236" scrap', ext=True)
    ax.text(BACK_L / 2, BOARD + 1.2, f'{SCRAP:.3f}" scrap strip (hatched)', fontsize=8, ha="center")
    dim_v(ax, 0, WALL_H, -3, 0, lab(WALL_H))
    dim_v(ax, WALL_H, 2 * WALL_H, -3, 0, lab(WALL_H))

    # --- piece schedule ---
    ax = fig.add_axes([0.02, 0.19, 0.66, 0.16]); ax.axis("off")
    rows = [
        ["Piece", "Qty", "Size (W x H)", "From board", "Location"],
        ["T1, T2, T3, T4", "4", '24.000 x 24.000', "1, 2, 3, 4", "Top, 2 x 2 grid"],
        ["L1, L2", "2", '24.000 x 11.764', "5", "Left wall: L1 rear, L2 front"],
        ["R1, R2", "2", '24.000 x 11.764', "6", "Right wall: R1 rear, R2 front"],
        ["B1, B2", "2", '23.764 x 11.764', "7", "Back wall: B1 left, B2 right (between side walls)"],
    ]
    tb = ax.table(cellText=rows[1:], colLabels=rows[0], loc="upper left", cellLoc="left",
                  colWidths=[0.17, 0.06, 0.18, 0.13, 0.46])
    tb.auto_set_font_size(False); tb.set_fontsize(10); tb.scale(1, 1.6)
    for (r, _), cell in tb.get_celld().items():
        if r == 0:
            cell.set_text_props(weight="bold"); cell.set_facecolor("#e8e8e8")
    fig.text(0.02, 0.165,
            "Notes\n"
            f"• Wall height 11.764\" = 12\" overall minus one 0.236\" top sheet (top sheets rest on the walls).\n"
            f"• Back strips are 0.236\" shorter so they fit between the side walls: 2 x 23.764 = 48 - 2 x 0.236.\n"
            "• Fractions are nearest 1/16\"; 11 3/4\" and 23 3/4\" are within 0.015\" — fine for foam.\n"
            "• Cut with a long straightedge and a fresh utility/foam knife; AN-72 has no meaningful kerf.\n"
            "• Total: 7 boards, 10 pieces. Buy 8 for a spare.",
            fontsize=9.5, va="top", linespacing=1.5)

    title_block(fig, "Foam enclosure — cut plan", 1)
    return fig


# ======================================================================================
# Sheet 2: assembly
# ======================================================================================
def sheet_assembly():
    fig = plt.figure(figsize=(17, 11))
    frame(fig)
    fig.text(0.02, 0.965, "SHEET 2 — ASSEMBLY  (third-angle projection)", fontsize=16,
             weight="bold", va="top")
    fig.text(0.02, 0.935, "Front (+Z) and bottom are OPEN. Top, back, left, right are foam. "
             "Outer envelope 48 W x 48 D x 12 H.", fontsize=9.5, va="top")

    # one 2D axis holds front / top / right views at a common scale so they line up
    ax = fig.add_axes([0.01, 0.03, 0.62, 0.88])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-40, 100); ax.set_ylim(-14, 84)

    # ---------- FRONT VIEW (from +Z): X right, Y up ----------
    rect(ax, -24 + T, 0, BACK_L, WALL_H, C_BACK, "B1", fs=8)                   # back wall seen through opening
    rect(ax, 0, 0, BACK_L, WALL_H, C_BACK, "B2", fs=8)
    rect(ax, -24, 0, T, WALL_H, C_SIDE)                                         # wall edges
    rect(ax, 24 - T, 0, T, WALL_H, C_SIDE)
    rect(ax, -24, WALL_H, W, T, C_TOP)                                          # top edge
    rect(ax, -ROTOR_L / 2, H / 2 - ROTOR_H / 2, ROTOR_L, ROTOR_H, "none", ls="--", ec=C_ROTOR, lw=1.2)
    ax.text(0, H / 2, '41" rotor (5" tall)', color=C_ROTOR, fontsize=7.5, ha="center", va="center",
            bbox=dict(fc=C_BACK, ec="none", pad=0.5))
    ax.text(-25, 6, "L2", fontsize=8, ha="right", va="center", weight="bold")
    ax.text(25, 6, "R2", fontsize=8, ha="left", va="center", weight="bold")
    ax.text(0, -12.5, "FRONT VIEW  (looking into the open front)", fontsize=10, ha="center", weight="bold")
    dim_h(ax, -24, 24, -4, 0, '48.000" overall')
    dim_h(ax, -24 + T, 24 - T, -8, 0, '47.528" inside')
    dim_v(ax, 0, H, -35, -24, '12.000"')
    dim_v(ax, 0, WALL_H, -31, -24, '11.764"')
    ax.plot([-23.5, 23.5], [0, 0], color="k", lw=0.5)
    ax.text(0, 0.6, "open bottom / floor", fontsize=6.5, ha="center", va="bottom", style="italic")

    # ---------- TOP VIEW (above front view): X right, -Z up (front edge toward front view) ----------
    oy = 24 + 30          # centre of top view
    for name, x, z in (("T1", -12, -12), ("T2", 12, -12), ("T3", -12, 12), ("T4", 12, 12)):
        rect(ax, x - 12, oy - z - 12, 24, 24, C_TOP, name, fs=10)
    ax.add_patch(Circle((0, oy), ROTOR_L / 2, fill=False, ls="--", ec=C_ROTOR, lw=1.0))
    ax.text(0, oy - ROTOR_L / 2 + 2.2, '41" rotor sweep (hidden)', color=C_ROTOR, fontsize=7, ha="center")
    rect(ax, -24, oy - 24, T, 48, "none", ls=":", lw=0.7)               # hidden walls under the top
    rect(ax, 24 - T, oy - 24, T, 48, "none", ls=":", lw=0.7)
    rect(ax, -24 + T, oy + 24 - T, 2 * BACK_L, T, "none", ls=":", lw=0.7)
    ax.text(0, oy - 25.4, "OPEN FRONT", fontsize=8, ha="center", va="top", weight="bold")
    ax.text(0, oy + 25, "BACK", fontsize=8, ha="center", va="bottom", weight="bold")
    ax.text(-36, oy + 27, "TOP VIEW", fontsize=10, ha="left", weight="bold")
    dim_h(ax, -24, 0, oy + 28.5, oy + 24, '24.000"')
    dim_h(ax, 0, 24, oy + 28.5, oy + 24, '24.000"')
    dim_v(ax, oy - 24, oy + 24, -30, -24, '48.000" deep')
    dim_v(ax, oy - 24, oy, -27, -24, '24"')

    # ---------- RIGHT VIEW (right of front view): -Z right (front edge toward front view), Y up ----------
    ox = 24 + 14 + 24     # centre of right view in X
    rect(ax, ox - 24, 0, 24, WALL_H, C_SIDE, "R2  (front half)", fs=8.5)
    rect(ax, ox, 0, 24, WALL_H, C_SIDE, "R1  (rear half)", fs=8.5)
    rect(ax, ox - 24, WALL_H, 48, T, C_TOP)
    ax.text(ox - 25, 6, "OPEN\nFRONT", fontsize=7.5, ha="right", va="center", weight="bold")
    ax.text(ox + 25, 6, "BACK", fontsize=7.5, ha="left", va="center", weight="bold")
    ax.text(ox, -12.5, "RIGHT SIDE VIEW", fontsize=10, ha="center", weight="bold")
    dim_h(ax, ox - 24, ox + 24, -4, 0, '48.000" deep')
    dim_h(ax, ox - 24, ox, -8, 0, '24"')
    for i, (lbl, label_side) in enumerate((("left wall L1/L2 is the mirror image", 0),)):
        ax.text(ox, 14.5, lbl, fontsize=7, ha="center", style="italic")

    # ---------- DETAIL A: rear-right corner from above, 5:1 ----------
    S, ax0, ay0 = 6.0, 48.0, 40.0          # scale, anchor of detail (model point x=21, z=-24 maps here)
    def P(x, z):                           # model (x, -z-up like top view) -> sheet
        return ax0 + (x - 21) * S, ay0 + (-z - 21) * S
    x0, y0 = P(24 - T, -21);  rect(ax, x0, y0, T * S, 3 * S, C_SIDE)          # R1 edge
    x0, y0 = P(21, -24 + T);  rect(ax, x0, y0, (BACK_L - 21 + 0) * S + 0 * S, T * S, C_BACK)
    # B2 ends at x = 24 - T
    ax.text(P(24 - T / 2, -22.5)[0] + 1.6, P(0, -22.5)[1], "R1", fontsize=8, va="center", weight="bold")
    ax.text(P(22.3, 0)[0], P(0, -24 + T)[1] - 1.5, "B2", fontsize=8, ha="center", weight="bold")
    dim_h(ax, P(24 - T, 0)[0], P(24, 0)[0], ay0 - 3.0, ay0, '0.236"', ext=True)
    ax.text(ax0 + 9, ay0 + 22, "DETAIL A  (6:1)\nrear-right corner, from above\n"
            "back strips fit INSIDE side walls", fontsize=8, ha="center", va="bottom", weight="bold")

    # ---------- DETAIL B: top-to-wall joint from the front, 5:1 ----------
    bx0, by0 = 76.0, 40.0
    def Q(x, y):
        return bx0 + (x - 21) * S, by0 + (y - 9) * S
    x0, y0 = Q(24 - T, 9);  rect(ax, x0, y0, T * S, WALL_H - 9 + 0 * S, C_SIDE)
    ax.patches[-1].set_height((WALL_H - 9) * S)
    x0, y0 = Q(21, WALL_H); rect(ax, x0, y0, 3 * S, T * S, C_TOP)
    ax.text(Q(24, 10)[0] + 1.2, Q(0, 10.2)[1], "R2", fontsize=8, va="center", weight="bold")
    ax.text(Q(22, 0)[0], Q(0, H)[1] + 1.2, "T4", fontsize=8, ha="center", weight="bold")
    dim_v(ax, Q(0, WALL_H)[1], Q(0, H)[1], Q(24, 0)[0] + 3.5, Q(24, 0)[0], '0.236"', rot=0)
    ax.text(bx0 + 9, by0 + 22, "DETAIL B  (6:1)\ntop-to-wall joint, from front\n"
            "top sheets REST ON the walls", fontsize=8, ha="center", va="bottom", weight="bold")

    # ---------- exploded isometric ----------
    ax3 = fig.add_axes([0.60, 0.42, 0.40, 0.52], projection="3d", computed_zorder=False)
    ax3.set_title("EXPLODED VIEW", fontsize=11, weight="bold", y=0.98)
    gap = 10.0
    pieces = []   # (label, (x0,x1), (y0,y1), (z0,z1), colour, explode vector)
    for name, xs, zs in (("T1", (-24, 0), (-24, 0)), ("T2", (0, 24), (-24, 0)),
                         ("T3", (-24, 0), (0, 24)), ("T4", (0, 24), (0, 24))):
        pieces.append((name, xs, (WALL_H, H), zs, C_TOP, (0, 2.6 * gap, 0)))
    for name, xs, zs, e in (("L1", (-24, -24 + T), (-24, 0), (-gap, 0, 0)),
                            ("L2", (-24, -24 + T), (0, 24), (-gap, 0, 0)),
                            ("R1", (24 - T, 24), (-24, 0), (gap, 0, 0)),
                            ("R2", (24 - T, 24), (0, 24), (gap, 0, 0))):
        pieces.append((name, xs, (0, WALL_H), zs, C_SIDE, e))
    for name, xs in (("B1", (-24 + T, 0)), ("B2", (0, 24 - T))):
        pieces.append((name, xs, (0, WALL_H), (-24, -24 + T), C_BACK, (0, 0, -1.4 * gap)))

    def faces(xs, ys, zs):
        # model (x, y-up, z) -> mpl (x, -z, y) so the open front faces the camera
        c = [(x, -z, y) for x in xs for y in ys for z in zs]
        idx = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
        return [[c[i] for i in f] for f in idx]

    # painter's order for a camera at front-right: back, far (left) wall, rotor, near (right) wall, top
    order = ["B1", "B2", "L1", "L2", "R1", "R2", "T1", "T2", "T3", "T4"]
    pieces.sort(key=lambda p: order.index(p[0]))
    for name, xs, ys, zs, col, (ex, ey, ez) in pieces:
        if name == "R1":   # rotor sits between the far and near walls
            ax3.add_collection3d(Poly3DCollection(
                faces((-ROTOR_L / 2, ROTOR_L / 2), (3.5, 8.5), (-1.5, 1.5)),
                fc=C_ROTOR, ec="k", lw=0.3, alpha=0.6))
        xs2, ys2, zs2 = [v + ex for v in xs], [v + ey for v in ys], [v + ez for v in zs]
        ax3.add_collection3d(Poly3DCollection(faces(xs2, ys2, zs2), fc=col, ec="k", lw=0.4, alpha=0.95))
        cx, cy, cz = sum(xs2) / 2, sum(ys2) / 2, sum(zs2) / 2
        lift = 1.2 if name.startswith("T") else 0
        ax3.text(cx, -cz, cy + lift, name, fontsize=8, weight="bold", ha="center", zorder=10)
    ax3.text(0, -28, 0, "OPEN FRONT", fontsize=8, weight="bold", ha="center")
    ax3.set_xlim(-34, 34); ax3.set_ylim(-34, 34); ax3.set_zlim(-2, 40)
    ax3.set_box_aspect((68, 68, 42))
    ax3.view_init(elev=24, azim=-58)
    ax3.set_axis_off()

    # ---------- assembly steps ----------
    fig.text(0.635, 0.39,
             "ASSEMBLY ORDER\n"
             "1.  Stand the side walls: L2 + L1 butt end-to-end on the left (L2 at the front),\n"
             "     R2 + R1 on the right. Outside faces 48.000\" apart.\n"
             "2.  Fit the back wall B1 + B2 BETWEEN the side walls at the rear (Detail A).\n"
             "     B1 on the left, B2 on the right; their seam sits on the centreline.\n"
             "3.  Lay the top: T1 rear-left, T2 rear-right, T3 front-left, T4 front-right,\n"
             "     resting on the wall tops, flush with the outside faces (Detail B).\n"
             "4.  Leave the front and the bottom open.\n"
             "5.  Tape every butt seam from the outside so it can't open up.\n\n"
             "Check: rotor sweep (41\") has ~3.3\" clearance to each side wall,\n"
             "and 11.764\" of headroom over the 5\" rotor.",
             fontsize=9, va="top", linespacing=1.55, family="monospace")

    title_block(fig, "Foam enclosure — assembly", 2)
    return fig


def main():
    pdf_path = os.path.join(OUT_DIR, "foam_enclosure_drawings.pdf")
    figs = [(sheet_cut_plan(), "sheet1_cut_plan.png"), (sheet_assembly(), "sheet2_assembly.png")]
    with PdfPages(pdf_path) as pdf:
        for fig, png in figs:
            pdf.savefig(fig)
            fig.savefig(os.path.join(OUT_DIR, png), dpi=110)
    print("wrote", pdf_path)


if __name__ == "__main__":
    main()
