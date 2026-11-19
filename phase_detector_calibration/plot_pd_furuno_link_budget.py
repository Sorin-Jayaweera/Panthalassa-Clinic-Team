"""How far away must the Furuno be for its pulses to clear the phase detector's threshold? (Sorin, 19 Nov)
Link: Furuno 1722C, 2.2 kW peak (63.4 dBm), 9402.6 MHz (measured 25 Oct), main beam 5.2 x 25 deg -> gain 10 log(41253 / (5.2 x 25)) - 1 dB
(efficiency guess) = 24 dBi. Our side, from documentation/make_blockdiagram.py and specs.py: horn 10-15 dBi, limiter 0.5 dB (assumed),
ZX60-5123LN+ LNA +22.0 dB, ZX05-14LH-S+ mixer -7.72 dB at 9.4 GHz. The bench's Pluto level is taken as the power into the IF
amplifier chain, i.e. the RX mixer output, so Pluto-equivalent level = antenna-port power + 13.8 dB (6 dB less if the IF splitter
for the envelope detector sits before the chain). Propagation over sea: free space, and flat-earth two-ray with reflection -1:
loss = FSPL - 20 log|2 sin(2 pi h1 h2 / (lambda d))|. Radio horizon 4.12 (sqrt h1 + sqrt h2) km (4/3 earth). Main beam on us only.
Heights H are assumptions to be confirmed. Saves pd_furuno_link_budget_19nov.png and prints the crossing distances."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

import wiring

HERE = Path(__file__).resolve().parent
PT, GT, F = 63.4, 10 * np.log10(41253 / (5.2 * 25)) - 1, 9402.6e6
RX = -0.5 + 22.0 - 7.72                                              # limiter, LNA, RX mixer: antenna port -> Pluto-equivalent point
GR, H = (10.0, 15.0), (4.0, 2.0)                                     # horn gain (dBi); ship radar and our antenna height above water (m), assumed
LEVELS = {-36.0: "highest level tested on the bench", -58.0: "lowest railed level", -50.0: "Sorin's threshold"}
lam = 3e8 / F
d = np.logspace(np.log10(30), np.log10(40e3), 2000)                  # m
fs = 20 * np.log10(4 * np.pi * d / lam)
two = fs - 20 * np.log10(np.abs(2 * np.sin(2 * np.pi * H[0] * H[1] / (lam * d))))
hor = 4.12e3 * sum(map(np.sqrt, H))

fig, ax = wiring.figure(1, [["Furuno 1722C\n2.2 kW, 24 dBi\n9402.6 MHz", f"sea path\nradar {H[0]:g} m, us {H[1]:g} m", "horn\n10-15 dBi", "limiter\n0.5 dB", "ZX60-5123LN+\n+22.0 dB",
                             "ZX05-14LH-S+\n-7.72 dB", "= Pluto-equivalent point\n(bench: 4 x ZX60-P162LN+ ...)"]], size=(16, 9), strip=0.3, titles=["Link from the ship's radar to the bench's Pluto level (antenna port + 13.8 dB)"])
for g, lw in zip(GR, (1.2, 2.2)):
    for loss, ls, nm in ((fs, "--", "free space"), (two, "-", "two-ray over sea (main beam, nulls included)")):
        y = PT + GT + g - loss + RX
        ax[0].plot(d / 1e3, y, ls, color="#1f78b4", lw=lw, label=f"horn {g:g} dBi, {nm}")
        for L in LEVELS:
            far = d[(y < L).argmax()] / 1e3 if (y < L).any() else np.inf     # first distance where it drops below (a null counts)
            print(f"horn {g:g} dBi, {nm:45s}: first below {L:.0f} dBm at {far:.1f} km (horizon {hor / 1e3:.1f} km)")
for L, t in LEVELS.items():
    ax[0].axhline(L, color={-36.0: "0.4", -58.0: "k", -50.0: "r"}[L], ls=":", lw=1.3, label=f"{L:.0f} dBm: {t}")
ax[0].axvline(hor / 1e3, color="#33a02c", lw=1.5, label=f"radio horizon {hor / 1e3:.1f} km (radar {H[0]:g} m, our antenna {H[1]:g} m above the sea; assumed)")
ax[0].set(xscale="log", xlim=(0.03, 40), ylim=(-90, 40), xlabel="distance to the ship (km)", ylabel="Pluto-equivalent level (dBm)\n= antenna port + 13.8 dB",
          title="Furuno main beam: level at the phase detector chain's input against distance")
ax[0].grid(alpha=0.3, which="both")
ax[0].legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.005, 1))
fig.tight_layout()
fig.savefig(HERE / "pd_furuno_link_budget_19nov.png", dpi=80)
