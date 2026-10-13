"""
render_schematic.py - draws JACON_system.asc (+ jacon_*.asy symbols) to a PNG so the
block layout can be seen without opening LTspice (approximate LTspice look).

    %USERPROFILE%\\radioconda\\python.exe render_schematic.py
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
SIZE_UNITS = {0: 9, 1: 14, 2: 20, 3: 26, 4: 32, 5: 44, 6: 60, 7: 84}   # approx text height in LTspice units


def load_symbol(name):
    p = HERE / f"{name}.asy"
    rects, texts, pins = [], [], []
    if not p.exists():
        return rects, texts, pins
    lines = p.read_text().splitlines()
    for i, ln in enumerate(lines):
        t = ln.split()
        if not t:
            continue
        if t[0] == "RECTANGLE":
            rects.append(tuple(map(int, t[2:6])))
        elif t[0] == "TEXT":
            texts.append((int(t[1]), int(t[2]), t[3], int(t[4]), " ".join(t[5:])))
        elif t[0] == "PIN":
            nm = lines[i + 1].split(maxsplit=2)[2] if i + 1 < len(lines) and "PinName" in lines[i + 1] else ""
            pins.append((int(t[1]), int(t[2]), t[3], nm))
    return rects, texts, pins


def main():
    asc = (HERE / "JACON_system.asc").read_text().splitlines()
    xs, ys = [], []
    items = []
    cur = None
    for ln in asc:
        t = ln.split()
        if not t:
            continue
        k = t[0]
        if k == "WIRE":
            items.append(("wire", *map(int, t[1:5])))
        elif k == "FLAG":
            items.append(("flag", int(t[1]), int(t[2]), t[3]))
        elif k == "SYMBOL":
            cur = ["sym", t[1], int(t[2]), int(t[3]), "", ""]
            items.append(cur)
        elif k == "SYMATTR" and cur is not None:
            if t[1] == "InstName":
                cur[4] = t[2]
            elif t[1] == "SpiceLine":
                cur[5] = " ".join(t[2:])
        elif k == "RECTANGLE":
            items.append(("rect", *map(int, t[2:6])))
        elif k == "TEXT":
            m = re.match(r"TEXT (-?\d+) (-?\d+) (\w+) (\d+) ([!;])(.*)", ln)
            if m:
                items.append(("text", int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4)),
                              m.group(5), m.group(6).replace("\\n", "\n")))
    for it in items:
        if it[0] in ("wire", "rect"):
            xs += [it[1], it[3]]
            ys += [it[2], it[4]]
        elif it[0] in ("flag", "sym", "text"):
            xs.append(it[2] if it[0] == "sym" else it[1])
            ys.append(it[3] if it[0] == "sym" else it[2])
    x0, x1, y0, y1 = min(xs) - 200, max(xs) + 2400, min(ys) - 300, max(ys) + 200
    W = 44.0
    H = W * (y1 - y0) / (x1 - x0)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.axis("off")
    ppu = 72 * W / (x1 - x0)          # points per LTspice unit

    def txt(x, y, s, just, size, color="k", weight="normal", family="sans-serif"):
        ha = {"Left": "left", "Right": "right", "Center": "center"}.get(just, "left")
        va = {"Bottom": "bottom", "Top": "top", "VCenter": "center", "Center": "center"}.get(just, "center")
        if just in ("Bottom", "Top", "VCenter"):
            ha = "center"
        ax.text(x, y, s, ha=ha, va=va, fontsize=SIZE_UNITS.get(size, 20) * ppu * 0.75, color=color,
                weight=weight, family=family)

    for it in items:
        if it[0] == "wire":
            ax.plot([it[1], it[3]], [it[2], it[4]], color="#1b4fa0", lw=1.2)
        elif it[0] == "rect":
            ax.add_patch(plt.Rectangle((min(it[1], it[3]), min(it[2], it[4])), abs(it[3] - it[1]), abs(it[4] - it[2]),
                                       fill=False, ls="--", lw=1.5, color="#555"))
        elif it[0] == "flag":
            txt(it[1], it[2] - 6, it[3], "Bottom", 1, color="#b03030")
        elif it[0] == "sym":
            _, name, sx, sy, inst, spl = it
            rects, texts, pins = load_symbol(name)
            for r in rects:
                ax.add_patch(plt.Rectangle((sx + r[0], sy + r[1]), r[2] - r[0], r[3] - r[1],
                                           facecolor="#fff7d6", edgecolor="#222", lw=1.5))
            for tx, ty, j, s, st in texts:
                txt(sx + tx, sy + ty, st, j, s, weight="bold" if s >= 2 else "normal")
            for px, py, side, nm in pins:
                j = {"LEFT": "Left", "RIGHT": "Right", "BOTTOM": "Bottom"}.get(side, "Left")
                off = {"LEFT": (8, 0), "RIGHT": (-8, 0), "BOTTOM": (0, -8)}.get(side, (0, 0))
                txt(sx + px + off[0], sy + py + off[1], nm, j, 0, color="#555")
            if rects:
                r = rects[0]
                txt(sx + (r[0] + r[2]) / 2, sy + r[1] - 8, inst, "Bottom", 1, color="#444")
                if spl:
                    txt(sx + (r[0] + r[2]) / 2, sy + r[3] + 44, spl, "Top", 1, color="#1b4fa0")
        elif it[0] == "text":
            _, x, y, j, s, kind, s_txt = it
            color = "#1b4fa0" if kind == "!" else "#2c6e2c"
            fam = "monospace" if (kind == "!" or s <= 2) and "\n" in s_txt else "sans-serif"
            txt(x, y, s_txt, "Left" if j == "Left" else j, s, color=color, family=fam)
    out = HERE / "plots" / "JACON_schematic_overview.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=60, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
