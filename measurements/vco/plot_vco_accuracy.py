"""
CVCO55BE-0800-1600 absolute-accuracy bench data.

    %USERPROFILE%\\radioconda\\python.exe plot_vco_accuracy.py

Blue/orange points  = measured on the bench (two takes, 10 s apart).
Red / purple lines  = datasheet, i.e. the prediction. Nothing is fitted to the data
                      except the grey line in panel A, which is labelled as such.
Error bars          = the readout quantisation: at any voltage the instrument can
                      only return one of two adjacent values, 2.670428 MHz apart.

Outputs
    VCO_tuning_and_uncertainty.png   A and D side by side (the main figure)
    VCO_absolute_accuracy.png        all four panels (A, B, C, D)
    VCO_absolute_accuracy_corrected.csv
"""
import csv
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

RAW = "VCO_absolute_accuracy_raw.csv"
GRID_MHZ = 2.670428          # readout quantisation step found in the data
GRID = GRID_MHZ / 1000       # GHz
BAND = (1.0, 1.2)            # GHz, the JACON IF window
TARGET_MHZ = 1.5             # frequency-matching goal

# datasheet numbers (CVCO55BE-0800-1600)
DS_F_LO, DS_F_HI = 0.8, 1.6          # GHz at the tuning-voltage limits
DS_V_LO, DS_V_HI = 0.5, 19.0         # V
DS_KV_TYP, DS_KV_MIN = 60.0, 15.0    # MHz/V

BLUE, ORANGE, RED, PURPLE, GREEN, GREY = (
    "#1f5fbf", "#d9822b", "#b03030", "#8e44ad", "#1d6f42", "#777777")

rows = []
with open(RAW) as fh:
    for r in csv.reader(fh):
        if len(r) > 4 and r[1].strip():
            try:
                rows.append((float(r[1]), float(r[2]), float(r[3])))
            except ValueError:
                pass
V, f1, f2 = map(np.array, zip(*rows))

pred = DS_F_LO + DS_KV_TYP / 1000 * V                       # datasheet prediction
ds_ends = DS_F_LO + (DS_F_HI - DS_F_LO) / (DS_V_HI - DS_V_LO) * (V - DS_V_LO)
ds_ends_slope = (DS_F_HI - DS_F_LO) / (DS_V_HI - DS_V_LO) * 1000
slope_fit, icept_fit = np.polyfit(V, f1, 1)
fit = icept_fit + slope_fit * V

dev_mhz = (f1 - pred) * 1000
dev_pct = dev_mhz / (f1 * 1000) * 100
kloc = np.diff(f1) / np.diff(V) * 1000
vmid = (V[1:] + V[:-1]) / 2
v_band = [float(np.interp(x, f1, V)) for x in BAND]
k_band = (BAND[1] - BAND[0]) * 1000 / (v_band[1] - v_band[0])

half_pct = (GRID_MHZ / 2) / (f1 * 1000) * 100               # +/- half a step, in %
target_pct = TARGET_MHZ / (f1 * 1000) * 100


# =====================================================================  panels
def draw_tuning(ax, legend_fs=7.6, title="A. Tuning curve: measurement vs datasheet"):
    """Measured frequency against the datasheet prediction."""
    ax.axhspan(*BAND, color="#2a9d55", alpha=.10)
    ax.errorbar(V, f1, yerr=GRID / 2, fmt="o", ms=6, color=BLUE, capsize=3, lw=1,
                label="MEASURED take 1 (bars = readout quantisation, +/-%.2f MHz)" % (GRID_MHZ / 2))
    ax.plot(V, f2, "x", ms=7, color=ORANGE, label="MEASURED take 2 (same point, 10 s later)")
    ax.plot(V, pred, "-.", lw=1.8, color=RED,
            label="DATASHEET prediction: 800 MHz + 60 MHz/V (typ sensitivity)")
    ax.plot(V, ds_ends, "--", lw=1.4, color=PURPLE,
            label="DATASHEET endpoints: 800 MHz @0.5 V to 1600 MHz @19 V (%.1f MHz/V)" % ds_ends_slope)
    ax.plot(V, fit, "-", lw=1.2, color=GREY,
            label="(fitted to the measurement, NOT a prediction: %.1f MHz/V)" % (slope_fit * 1000))
    ax.set_xlabel("tuning voltage Vt (V)")
    ax.set_ylabel("output frequency (GHz)")
    ax.set_title(title)
    ax.grid(alpha=.3)
    h, l = ax.get_legend_handles_labels()
    h.append(Patch(facecolor="#2a9d55", alpha=.10))
    l.append("GREEN SHADING = JACON IF band, 1.0-1.2 GHz")
    ax.legend(h, l, fontsize=legend_fs, loc="upper left")


def draw_uncertainty(ax, legend_fs=8.0, title=None):
    """Quantisation as a +/- frequency band (left axis) and as a percentage (right axis)."""
    # ---- left axis: the +/- frequency lines, in MHz
    ax.fill_between(V, -GRID_MHZ / 2, GRID_MHZ / 2, color=PURPLE, alpha=.18, zorder=1)
    ax.axhline(+GRID_MHZ / 2, color=PURPLE, lw=1.4)
    ax.axhline(-GRID_MHZ / 2, color=PURPLE, lw=1.4)
    ax.axhline(+TARGET_MHZ, color=GREEN, ls="--", lw=1.5)
    ax.axhline(-TARGET_MHZ, color=GREEN, ls="--", lw=1.5)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.plot(V, np.zeros_like(V), "o", ms=4.5, color=BLUE, zorder=5)
    ax.axvspan(v_band[0], v_band[1], color="#2a9d55", alpha=.12, zorder=0)
    ax.set_xlabel("tuning voltage Vt (V)")
    ax.set_ylabel("frequency uncertainty, +/- MHz   (LEFT axis)")
    ax.set_ylim(-4.0, 4.0)
    ax.grid(alpha=.3)

    # ---- right axis: the same two things expressed as a percentage of f_out.
    # Both are plotted as +/- envelopes so they sit on the same zero as the MHz lines.
    axp = ax.twinx()
    for s in (+1, -1):
        axp.plot(V, s * half_pct, "s-", ms=4.5, color=PURPLE, lw=1.3, alpha=.85)
        axp.plot(V, s * target_pct, "--", lw=1.6, color=GREEN, alpha=.85)
    axp.set_ylabel("uncertainty as +/- % of output frequency   (RIGHT axis)")
    axp.set_ylim(-0.40, 0.40)

    ax.set_title(title or
                 "D. One voltage gives one of two readings %.2f MHz apart,\n"
                 "which nearly fills the +/-%.1f MHz matching budget" % (GRID_MHZ, TARGET_MHZ),
                 fontsize=11)

    handles = [
        Patch(facecolor=PURPLE, alpha=.18,
              label="PURPLE BAND = readout quantisation, +/-%.3f MHz (left axis)" % (GRID_MHZ / 2)),
        Line2D([], [], color=PURPLE, lw=1.4,
               label="PURPLE SOLID = the +/-%.3f MHz quantisation lines (left axis)" % (GRID_MHZ / 2)),
        Line2D([], [], color=GREEN, ls="--", lw=1.5,
               label="GREEN DASHED = the +/-%.1f MHz matching target (left axis)" % TARGET_MHZ),
        Line2D([], [], color=BLUE, marker="o", ls="none", ms=4.5,
               label="BLUE DOTS = the %d measured frequencies, each plotted at its own reading" % len(V)),
        Line2D([], [], color=PURPLE, marker="s", ls="-", ms=5,
               label="PURPLE SQUARES = quantisation as %% of f_out, %.3f-%.3f %% (right axis)"
                     % (half_pct.min(), half_pct.max())),
        Line2D([], [], color=GREEN, ls="--", lw=1.6,
               label="GREEN DASHED CURVE = target as %% of f_out, %.3f-%.3f %% (right axis)"
                     % (target_pct.min(), target_pct.max())),
        Patch(facecolor="#2a9d55", alpha=.12,
              label="GREEN SHADING = Vt %.2f-%.2f V, the range that gives 1.0-1.2 GHz" % tuple(v_band)),
    ]
    ax.legend(handles=handles, fontsize=legend_fs, loc="lower center", framealpha=.95)
    return axp


IN_BAND = ("in the IF band: quantisation +/-%.3f %% to +/-%.3f %%,   target +/-%.3f %% to +/-%.3f %%"
           % (GRID_MHZ / 2 / 1000 * 100, GRID_MHZ / 2 / 1200 * 100,
              TARGET_MHZ / 1000 * 100, TARGET_MHZ / 1200 * 100))

# ============================================  main figure: A and D side by side
fig, axs = plt.subplots(1, 2, figsize=(17.5, 7.2))
draw_tuning(axs[0], legend_fs=8.0,
            title="A. Measured vs predicted (datasheet) tuning curve")
draw_uncertainty(axs[1], legend_fs=7.9)
axs[1].text(0.15, 3.72, IN_BAND, fontsize=8.6, color="#333333")
fig.suptitle("CVCO55BE-0800-1600: measured tuning curve vs the datasheet prediction (left), "
             "and the uncertainty of each measured point (right)", fontsize=13, weight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig("VCO_tuning_and_uncertainty.png", dpi=140, facecolor="white")
print("wrote VCO_tuning_and_uncertainty.png")

# ============================================  full figure: A, B, C, D
fig, axs = plt.subplots(2, 2, figsize=(16, 10.5))
draw_tuning(axs[0, 0])

ax = axs[0, 1]
ax.axhline(0, color=RED, lw=1.6, ls="-.")
ax.plot(V, dev_mhz, "o-", color=BLUE, label="MEASURED minus DATASHEET prediction")
ax.text(V.max() * 0.36, -6.0, "zero line = DATASHEET prediction (800 MHz + 60 MHz/V)",
        fontsize=8.5, color=RED)
ax.text(0.2, dev_mhz.mean() + 7, "mean offset %+.0f MHz (%.1f %%)"
        % (dev_mhz.mean(), dev_pct.mean()), fontsize=9, color=BLUE)
ax.set_xlabel("tuning voltage Vt (V)")
ax.set_ylabel("measured - datasheet prediction (MHz)")
ax.set_title("B. This unit runs %.0f to %.0f MHz (%.1f to %.1f %%) below the datasheet"
             % (-dev_mhz.max(), -dev_mhz.min(), -dev_pct.max(), -dev_pct.min()))
ax.grid(alpha=.3)
ax.legend(fontsize=8.5, loc="lower right")

ax = axs[1, 0]
ax.axvspan(v_band[0], v_band[1], color="#2a9d55", alpha=.12)
ax.plot(vmid, kloc, "o-", color=BLUE, label="MEASURED local slope (between adjacent points)")
ax.axhline(DS_KV_TYP, ls="--", color=RED, label="DATASHEET typical, 60 MHz/V")
ax.axhline(DS_KV_MIN, ls=":", color=RED, label="DATASHEET minimum, 15 MHz/V")
ax.set_xlabel("tuning voltage Vt (V)")
ax.set_ylabel("local tuning sensitivity Kvco (MHz/V)")
ax.set_title("C. Sensitivity varies %.0f-%.0f MHz/V; inside the IF band it is %.0f MHz/V"
             % (kloc.min(), kloc.max(), k_band))
ax.grid(alpha=.3)
h, l = ax.get_legend_handles_labels()
h.append(Patch(facecolor="#2a9d55", alpha=.12))
l.append("GREEN SHADING = Vt %.2f-%.2f V, the range that gives 1.0-1.2 GHz" % (v_band[0], v_band[1]))
ax.legend(h, l, fontsize=8, loc="lower right")

draw_uncertainty(axs[1, 1], legend_fs=7.4)
axs[1, 1].text(0.15, 3.72, IN_BAND, fontsize=8.3, color="#333333")

fig.suptitle("CVCO55BE-0800-1600: measured tuning behaviour vs datasheet, and the measurement's own uncertainty",
             fontsize=13.5, weight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.965))
fig.savefig("VCO_absolute_accuracy.png", dpi=140, facecolor="white")
print("wrote VCO_absolute_accuracy.png")

with open("VCO_absolute_accuracy_corrected.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Voltage in V", "MEASURED take 1 (GHz)", "MEASURED take 2 (GHz)",
                "DATASHEET prediction 0.8+0.06V (GHz)", "measured - datasheet (MHz)",
                "measured - datasheet (%)", "readout uncertainty (+/- MHz)",
                "readout uncertainty (+/- %)", "local Kvco (MHz/V)"])
    for i in range(len(V)):
        kl = "" if i == 0 else "%.1f" % kloc[i - 1]
        w.writerow(["%.2f" % V[i], "%.6f" % f1[i], "%.6f" % f2[i], "%.6f" % pred[i],
                    "%.2f" % dev_mhz[i], "%.3f" % dev_pct[i], "%.3f" % (GRID_MHZ / 2),
                    "%.3f" % half_pct[i], kl])
print("wrote VCO_absolute_accuracy_corrected.csv")
print("quantisation: +/-%.3f MHz = %.3f%% at %.3f GHz, %.3f%% at %.3f GHz"
      % (GRID_MHZ / 2, half_pct.max(), f1.min(), half_pct.min(), f1.max()))
print("in-band Kvco %.1f MHz/V over Vt %.2f-%.2f V" % (k_band, v_band[0], v_band[1]))
print("measured - datasheet: %+.0f to %+.0f MHz (%.2f to %.2f %%)"
      % (dev_mhz.min(), dev_mhz.max(), dev_pct.min(), dev_pct.max()))
print("target %.1f MHz is %.3f%% at 1.0 GHz, %.3f%% at 1.2 GHz"
      % (TARGET_MHZ, TARGET_MHZ / 1000 * 100, TARGET_MHZ / 1200 * 100))
