#!/usr/bin/env python3
"""Generate dependency-free SVG/CSV visual checks for the JACON simulations."""

from pathlib import Path
import csv
import math


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "visualizations"
OUT.mkdir(parents=True, exist_ok=True)

C0 = 299_792_458.0
VF = 0.66
EXTRA_LEN_IN = 4.5
TD_4P5 = EXTRA_LEN_IN * 0.0254 / (VF * C0)
TD_QUAD = 1.0 / (4.0 * 1.1e9)


def polyline(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def write_svg(path, width, height, body):
    text = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    text {{ font-family: Arial, sans-serif; fill: #111; }}
    .axis {{ stroke: #222; stroke-width: 1.5; }}
    .grid {{ stroke: #ddd; stroke-width: 1; }}
    .line1 {{ fill: none; stroke: #1769aa; stroke-width: 2.5; }}
    .line2 {{ fill: none; stroke: #b35c00; stroke-width: 2.5; }}
    .band_rx {{ fill: #1769aa; }}
    .band_if {{ fill: #2e7d32; }}
    .band_tx {{ fill: #b71c1c; }}
    .band_image {{ fill: #8a6d3b; }}
    .box {{ fill: #f7f7f4; stroke: #222; stroke-width: 2; rx: 6; }}
    .rx {{ fill: #e8f2ff; }}
    .if {{ fill: #eaf6ea; }}
    .ctrl {{ fill: #fff4dd; }}
    .tx {{ fill: #ffeaea; }}
    .arrow {{ stroke: #222; stroke-width: 2.5; fill: none; marker-end: url(#arrow); }}
    .dash {{ stroke-dasharray: 7 7; }}
    .small {{ font-size: 15px; }}
    .title {{ font-size: 24px; font-weight: 700; }}
  </style>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8 z" fill="#222"/>
    </marker>
  </defs>
{body}
</svg>
"""
    path.write_text(text, encoding="utf-8")


def save_delay_response():
    freqs = [1.0e9 + i * (0.2e9 / 400) for i in range(401)]
    y_4p5 = [math.cos(2 * math.pi * f * TD_4P5) for f in freqs]
    y_quad = [math.cos(2 * math.pi * f * TD_QUAD) for f in freqs]

    with (OUT / "delay_detector_response.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "frequency_hz",
            "cos_physical_4p5in_vf0p66",
            "cos_quadrature_1p1ghz",
            "td_physical_s",
            "td_quadrature_s",
        ])
        for freq, a, b in zip(freqs, y_4p5, y_quad):
            writer.writerow([freq, a, b, TD_4P5, TD_QUAD])

    w, h = 980, 560
    left, right, top, bottom = 90, 30, 60, 80
    x0, x1 = left, w - right
    y0, y1 = h - bottom, top

    def sx(f):
        return x0 + (f - 1.0e9) / 0.2e9 * (x1 - x0)

    def sy(v):
        return y0 - (v + 1.0) / 2.0 * (y0 - y1)

    p1 = [(sx(f), sy(v)) for f, v in zip(freqs, y_4p5)]
    p2 = [(sx(f), sy(v)) for f, v in zip(freqs, y_quad)]
    grid = []
    for ghz in [1.0, 1.05, 1.1, 1.15, 1.2]:
        x = sx(ghz * 1e9)
        grid.append(f'<line class="grid" x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y0}"/>')
        grid.append(f'<text x="{x:.1f}" y="{y0+28}" text-anchor="middle">{ghz:.2f}</text>')
    for val in [-1, -0.5, 0, 0.5, 1]:
        y = sy(val)
        grid.append(f'<line class="grid" x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"/>')
        grid.append(f'<text x="{x0-15}" y="{y+5:.1f}" text-anchor="end">{val:.1f}</text>')

    body = "\n".join(grid) + f"""
  <line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>
  <line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}"/>
  <polyline class="line1" points="{polyline(p1)}"/>
  <polyline class="line2" points="{polyline(p2)}"/>
  <line x1="{sx(1.1e9):.1f}" y1="{y1}" x2="{sx(1.1e9):.1f}" y2="{y0}" stroke="#333" stroke-dasharray="6 5"/>
  <text class="title" x="{left}" y="35">Delay-line detector low-pass term</text>
  <text x="{(x0+x1)/2:.1f}" y="{h-25}" text-anchor="middle">IF frequency (GHz)</text>
  <text x="28" y="{(y0+y1)/2:.1f}" transform="rotate(-90 28 {(y0+y1)/2:.1f})" text-anchor="middle">cos(2*pi*f*dt)</text>
  <rect x="620" y="75" width="18" height="4" fill="#1769aa"/><text x="646" y="83">4.5 in coax, VF=0.66, dt={TD_4P5*1e12:.0f} ps</text>
  <rect x="620" y="105" width="18" height="4" fill="#b35c00"/><text x="646" y="113">quadrature at 1.1 GHz, dt={TD_QUAD*1e12:.0f} ps</text>
"""
    write_svg(OUT / "delay_detector_response.svg", w, h, body)


def save_time_domain():
    f = 1.1e9
    t = [i * 8e-9 / 1200 for i in range(1201)]
    a = [math.cos(2 * math.pi * f * x) for x in t]
    b = [math.cos(2 * math.pi * f * (x - TD_4P5)) for x in t]
    raw = [aa * bb for aa, bb in zip(a, b)]
    dc = 0.5 * math.cos(2 * math.pi * f * TD_4P5)

    w, h = 980, 650
    left, right, top, bottom = 80, 30, 65, 55
    plot_h = 145
    gaps = 35

    def panel(idx):
        yy1 = top + idx * (plot_h + gaps)
        yy0 = yy1 + plot_h
        return yy0, yy1

    def sx(x):
        return left + x / 8e-9 * (w - left - right)

    def sy(v, yy0, yy1):
        return yy0 - (v + 1.15) / 2.3 * (yy0 - yy1)

    parts = [f'<text class="title" x="{left}" y="35">Focused 1.1 GHz splitter/cable/multiplier behavior</text>']
    labels = [("Cable ends", a, b), ("Product", raw, None), ("Low-pass", [dc for _ in t], None)]
    for idx, (label, y_a, y_b) in enumerate(labels):
        yy0, yy1 = panel(idx)
        parts.append(f'<line class="axis" x1="{left}" y1="{yy0}" x2="{w-right}" y2="{yy0}"/>')
        parts.append(f'<line class="axis" x1="{left}" y1="{yy0}" x2="{left}" y2="{yy1}"/>')
        for ns in range(0, 9):
            x = sx(ns * 1e-9)
            parts.append(f'<line class="grid" x1="{x:.1f}" y1="{yy1}" x2="{x:.1f}" y2="{yy0}"/>')
            if idx == 2:
                parts.append(f'<text x="{x:.1f}" y="{yy0+24}" text-anchor="middle">{ns}</text>')
        parts.append(f'<text x="20" y="{(yy0+yy1)/2:.1f}">{label}</text>')
        pts = [(sx(x), sy(v, yy0, yy1)) for x, v in zip(t, y_a)]
        parts.append(f'<polyline class="line1" points="{polyline(pts)}"/>')
        if y_b is not None:
            pts_b = [(sx(x), sy(v, yy0, yy1)) for x, v in zip(t, y_b)]
            parts.append(f'<polyline class="line2" points="{polyline(pts_b)}"/>')
    parts.append(f'<text x="{(left+w-right)/2:.1f}" y="{h-15}" text-anchor="middle">Time (ns)</text>')
    write_svg(OUT / "focused_delay_time_domain.svg", w, h, "\n".join(parts))


def save_spectrum_plan():
    w, h = 1000, 360
    left, right = 95, 45

    def sx(ghz):
        return left + (ghz - 0.5) / 9.5 * (w - left - right)

    bands = [
        ("RX radar", 9.3, 9.5, "band_rx", 80),
        ("LO", 8.3, 8.3, "", 130),
        ("IF", 1.0, 1.2, "band_if", 180),
        ("TX response", 9.3, 9.5, "band_tx", 230),
        ("image", 7.1, 7.3, "band_image", 280),
    ]
    parts = ['<text class="title" x="95" y="38">JACON frequency plan</text>']
    for tick in range(1, 11):
        x = sx(tick)
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="55" x2="{x:.1f}" y2="310"/>')
        parts.append(f'<text x="{x:.1f}" y="335" text-anchor="middle">{tick}</text>')
    for label, lo, hi, klass, y in bands:
        parts.append(f'<text x="20" y="{y+5}">{label}</text>')
        if lo == hi:
            parts.append(f'<line x1="{sx(lo):.1f}" y1="{y-18}" x2="{sx(lo):.1f}" y2="{y+18}" stroke="#333" stroke-width="5"/>')
        else:
            parts.append(f'<rect class="{klass}" x="{sx(lo):.1f}" y="{y-16}" width="{sx(hi)-sx(lo):.1f}" height="32"/>')
    parts.append('<text x="500" y="352" text-anchor="middle">Frequency (GHz)</text>')
    write_svg(OUT / "spectrum_plan.svg", w, h, "\n".join(parts))


def save_morse():
    wpm = 18
    dot = 1.2 / wpm
    parts = [(1, dot, "."), (0, dot, ""), (1, 3 * dot, "-"), (0, dot, ""), (1, dot, "."), (0, 7 * dot, "")]
    cursor = 0.0
    points = []
    labels = []
    for state, dur, label in parts:
        points += [(cursor, state), (cursor + dur, state)]
        if label:
            labels.append((cursor + dur / 2, label))
        cursor += dur

    w, h = 900, 280
    left, right, top, bottom = 70, 30, 55, 60

    def sx(t):
        return left + t / cursor * (w - left - right)

    def sy(v):
        return h - bottom - v * (h - top - bottom)

    pts = [(sx(t), sy(v)) for t, v in points]
    body = f"""
  <text class="title" x="{left}" y="35">Morse keying envelope: . - .</text>
  <line class="axis" x1="{left}" y1="{h-bottom}" x2="{w-right}" y2="{h-bottom}"/>
  <line class="axis" x1="{left}" y1="{h-bottom}" x2="{left}" y2="{top}"/>
  <polyline class="line1" points="{polyline(pts)}"/>
  <text x="{(left+w-right)/2:.1f}" y="{h-18}" text-anchor="middle">Time (s)</text>
"""
    for x, label in labels:
        body += f'  <text x="{sx(x):.1f}" y="{top-12}" text-anchor="middle" font-size="24">{label}</text>\n'
    write_svg(OUT / "morse_keying.svg", w, h, body)


def save_block_svg():
    body = """
  <text class="title" x="40" y="42">JACON behavioral simulation map</text>
  <rect class="box rx" x="40" y="80" width="150" height="70"/><text x="60" y="112">RX antenna</text><text class="small" x="60" y="134">9.3-9.5 GHz</text>
  <rect class="box rx" x="230" y="80" width="150" height="70"/><text x="258" y="112">Limiter</text><text class="small" x="252" y="134">protect LNA</text>
  <rect class="box rx" x="420" y="80" width="150" height="70"/><text x="466" y="112">LNA</text><text class="small" x="456" y="134">+22 dB</text>
  <rect class="box rx" x="610" y="80" width="150" height="70"/><text x="658" y="112">Mixer</text><text class="small" x="636" y="134">RF - LO = IF</text>
  <rect class="box if" x="800" y="80" width="150" height="70"/><text x="846" y="112">IF amp</text><text class="small" x="826" y="134">1.0-1.2 GHz</text>
  <rect class="box if" x="990" y="80" width="150" height="70"/><text x="1010" y="112">IF splitter</text><text class="small" x="1012" y="134">detector branches</text>
  <path class="arrow" d="M190 115 L230 115"/><path class="arrow" d="M380 115 L420 115"/><path class="arrow" d="M570 115 L610 115"/><path class="arrow" d="M760 115 L800 115"/><path class="arrow" d="M950 115 L990 115"/>
  <rect class="box ctrl" x="610" y="210" width="150" height="70"/><text x="636" y="242">8.3 GHz LO</text><text class="small" x="632" y="264">PLL + buffer</text>
  <path class="arrow" d="M685 210 L685 150"/>
  <rect class="box if" x="990" y="210" width="150" height="76"/><text x="1015" y="240">Envelope</text><text x="1010" y="262">detector</text>
  <rect class="box ctrl" x="1180" y="210" width="150" height="76"/><text x="1206" y="240">Comparator</text><text class="small" x="1208" y="262">radar ping</text>
  <path class="arrow" d="M1065 150 L1065 210"/><path class="arrow" d="M1140 248 L1180 248"/>
  <rect class="box if" x="990" y="350" width="150" height="80"/><text x="1018" y="382">Limiter</text><text class="small" x="1006" y="404">fixed IF level</text>
  <rect class="box if" x="800" y="350" width="150" height="80"/><text x="820" y="382">Delay-line</text><text x="812" y="404">phase det.</text>
  <rect class="box ctrl" x="610" y="350" width="150" height="80"/><text x="634" y="382">Sample/</text><text x="652" y="404">hold</text>
  <rect class="box ctrl" x="420" y="350" width="150" height="80"/><text x="468" y="382">VCO</text><text class="small" x="438" y="404">1.0-1.2 GHz</text>
  <path class="arrow" d="M1065 150 L1065 350"/><path class="arrow" d="M990 390 L950 390"/><path class="arrow" d="M800 390 L760 390"/><path class="arrow" d="M610 390 L570 390"/>
  <path class="arrow dash" d="M1255 286 L1255 490 L685 490 L685 430"/>
  <rect class="box tx" x="420" y="520" width="150" height="70"/><text x="466" y="552">TX mixer</text><text class="small" x="450" y="574">+ 8.3 GHz LO</text>
  <rect class="box tx" x="610" y="520" width="150" height="70"/><text x="620" y="552">Image filter</text><text class="small" x="630" y="574">pass 9.3-9.5</text>
  <rect class="box tx" x="800" y="520" width="150" height="70"/><text x="840" y="552">Keying</text><text class="small" x="842" y="574">. - .</text>
  <rect class="box tx" x="990" y="520" width="150" height="70"/><text x="1038" y="552">PA</text><text class="small" x="1010" y="574">to TX antenna</text>
  <path class="arrow" d="M495 430 L495 520"/><path class="arrow" d="M570 555 L610 555"/><path class="arrow" d="M760 555 L800 555"/><path class="arrow" d="M950 555 L990 555"/>
  <path class="arrow" d="M685 280 L685 520 L570 520"/>
"""
    write_svg(OUT / "block_flow.svg", 1400, 640, body)


def main():
    save_delay_response()
    save_time_domain()
    save_spectrum_plan()
    save_morse()
    save_block_svg()
    print(f"Wrote SVG/CSV visualizations to {OUT}")


if __name__ == "__main__":
    main()
