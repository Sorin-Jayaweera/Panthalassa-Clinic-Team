"""Wiring diagram drawn inside a plot, so every saved figure shows the whole setup it was measured with.

A setup is a list of stages, left to right. A stage is one label, or a list of labels for parallel paths.
"""
import matplotlib.pyplot as plt

P162X4 = ["Pluto TX\nlevel per curve", "4 x ZX60-P162LN+\nin series, 4 V supply", "ZFRSC-42-S+\nsplitter",
          ["cable", "cable + 4.5 in\n(0.55 ns longer)"], "ZX05-30W-S+\nLO and RF in, IF out",
          ["SDS1104X-E CH1\n1 Mohm, reads the mV", "23 dB of pads\nthen SM200B"]]
MIXER_PLUTO = ["Pluto TX\nset -2 to -12.25 dBm", "splitter", ["cable", "cable + extra length"], "mixer\nLO and RF in, IF out", "multimeter\nreads the mV"]
MIXER_VCO = ["VCO\nabout +6 dBm", "tee, one side to\nspectrum analyzer", "ZFRSC-42-S+\nsplitter", ["cable", "cable + 4.5 in\n(0.55 ns longer)"],
             "ZX05-30W-S+\nabout +0.6 dBm per port", "scope CH2\n1 Mohm, reads the mV"]
P103X3 = ["Pluto TX\nlevel per plot", "3 x ZX60-P103LN+\nin series, 5 V supply", "ZFRSC-42-S+\nsplitter",
          ["cable", "cable + 4.5 in\n(0.55 ns longer)"], "ZX05-30W-S+\nLO and RF in, IF out",
          ["SDS1104X-E CH1\n1 Mohm, reads the mV", "23 dB of pads\nthen SM200B"]]
RADAR_P103 = ["Furuno radar\nover the air", "Vivaldi", "Marki limiter", "20 dB", "ZX60-5123LN+\n6 V", "16 dB",
              "ZX05-14LH-S+\nRF in, LO below", "3 x ZX60-P103LN+\n5 V", "ZFRSC-42-S+\nsplitter",
              ["cable", "cable\n+ 4.5 in"], "ZX05-30W-S+", ["SDS1104X-E\nCH1, 1 Mohm", "23 dB then\nSM200B"]]


def draw(ax, stages, title="Wiring"):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0, 1, title, fontsize=9, fontweight="bold", va="top")
    n = len(stages)
    w = 0.9 / n
    box = dict(boxstyle="round,pad=0.3", fc="white", ec="0.35", lw=0.9)
    prev = []
    for i, stage in enumerate(stages):
        labels = stage if isinstance(stage, list) else [stage]
        x = (i + 0.5) * 1 / n
        ys = [0.42] if len(labels) == 1 else [0.68, 0.14]
        here = []
        for label, y in zip(labels, ys):
            ax.text(x, y, label, ha="center", va="center", fontsize=7.5, bbox=box, zorder=3)
            here.append((x, y))
        for x0, y0 in prev:
            for x1, y1 in here:
                ax.annotate("", xy=(x1 - w * 0.42, y1), xytext=(x0 + w * 0.42, y0), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.3"), zorder=2)
        prev = here


def add_strip(fig, stages, title="Wiring", height=1.5):
    """Add a wiring strip under a figure that is already laid out. Call just before savefig."""
    w0, h0 = fig.get_size_inches()
    frac = h0 / (h0 + height)
    fig.set_size_inches(w0, h0 + height)
    for ax in fig.axes:
        p = ax.get_position()
        ax.set_position([p.x0, 1 - (1 - p.y0) * frac, p.width, p.height * frac])
    draw(fig.add_axes([0.03, 0.005, 0.94, (1 - frac) * 0.95]), stages, title)


def figure(rows, stages_list, size=(13, 8), titles=None):
    """Figure with `rows` plot axes above one wiring strip per setup. Returns fig, list of plot axes."""
    n = len(stages_list)
    fig, axes = plt.subplots(rows + n, 1, figsize=size, gridspec_kw={"height_ratios": [1] * rows + [0.27 * 2 / max(rows, 1)] * n})
    for k, stages in enumerate(stages_list):
        draw(axes[rows + k], stages, titles[k] if titles else "Wiring")
    return fig, list(axes[:rows])
