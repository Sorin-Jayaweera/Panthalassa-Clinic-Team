"""Plots for data sets that had none (audit of 16 Nov 2026). Each plot is saved next to its data so the site's data index
(site/content_data_index.py) picks it up. Each figure carries a text line with the setup, as far as it is recorded."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent       # clinic/claude
PD = ROOT / "phase_detector_calibration"


def setup_note(fig, text):
    fig.text(0.01, 0.005, "Setup: " + text, fontsize=8, ha="left", va="bottom", wrap=True)


def noise():
    a = list(csv.DictReader(open(PD / "noise" / "noise_summary.csv")))
    b = list(csv.DictReader(open(PD / "noise_cleanDC" / "noise_summary.csv")))
    fig, ax = plt.subplots(3, 1, figsize=(11, 11))
    for rows, vt, lab, c in ((a, "vt_meas_v", "first run", "#d95f02"), (b, "vt_meas_v", "clean DC supply", "#1b9e77")):
        x = np.array([float(r[vt]) for r in rows])
        for bw, ls in (("full", "-"), ("1MHz", "--"), ("100kHz", ":")):
            ax[0].plot(x, [float(r[f"mixer_rms_uv_{bw}"]) / 1e3 for r in rows], ls, marker="o", color=c, label=f"{lab}, {bw}")
            ax[2].plot(x, [float(r[f"freq_noise_khz_{bw}"]) for r in rows], ls, marker="o", color=c, label=f"{lab}, {bw}")
        ax[0].plot(x, [float(r["scope_floor_rms_uv_full"]) / 1e3 for r in rows], "-", color="#999999", lw=0.8, label=f"{lab}: scope floor (open channel), full")
        ax[1].plot(x, [float(r["slope_mv_per_mhz"]) for r in rows], "-o", color=c, label=lab)
    ax[0].set(ylabel="detector rms (mV)", yscale="log", title="Phase detector output noise at fixed VCO tuning voltages (rms in each bandwidth)")
    ax[1].set(ylabel="slope (mV/MHz)", title="Detector slope at each tuning voltage (from the calibration)")
    ax[2].set(xlabel="VCO tuning voltage (V)", ylabel="frequency noise (kHz rms)", yscale="log", title="Noise turned into frequency: rms / slope")
    for x in ax:
        x.grid(alpha=0.3, which="both")
        x.legend(fontsize=7, ncol=2)
    setup_note(fig, "VCO (tuning voltage from the bench supply; second run from a clean DC source) -> splitter -> delay arm -> ZX05-30W-S+ phase detector -> SDS1104X-E, "
                    "700k samples at 500 MS/s per voltage; an open scope channel recorded at the same time gives the scope floor. Data: phase_detector_calibration/noise*/noise_summary.csv.")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for d in ("noise", "noise_cleanDC"):
        fig.savefig(PD / d / "noise_summary.png", dpi=90)
    plt.close(fig)


def furuno_iq():
    fig, ax = plt.subplots(2, 1, figsize=(11, 8))
    for k, name in enumerate(("iq_if_1p105GHz.npz", "iq_baseband_21MHz.npz")):
        for d, lab, c in (("furuno_detector_1nov_pll_on", "PLL on", "#1b9e77"), ("furuno_detector_1nov_pll_off_deliberate", "PLL off (deliberate)", "#d95f02")):
            z = np.load(PD / d / name)
            iq, fs = z["iq"].astype(np.complex64), float(z["fs"])
            n = 4096
            seg = iq[: (len(iq) // n) * n].reshape(-1, n)
            P = np.mean(np.abs(np.fft.fftshift(np.fft.fft(seg * np.hanning(n), axis=1), axes=1)) ** 2, axis=0)
            f = np.fft.fftshift(np.fft.fftfreq(n, 1 / fs)) / 1e6
            ax[k].plot(f, 10 * np.log10(P + 1e-30), lw=0.8, color=c, label=f"{lab} ({len(iq) / fs * 1e3:.0f} ms at {fs / 1e6:.0f} MS/s)")
        ax[k].set(xlabel="offset from centre (MHz)", ylabel="power (dB, relative)", title=f"SM200B I/Q, {name.replace('.npz', '')}: averaged spectrum, PLL on against off")
        ax[k].grid(alpha=0.3)
        ax[k].legend(fontsize=8)
    setup_note(fig, "Furuno radar over the air -> JACON receive chain -> IF -> phase detector; SM200B recording I/Q at the 1.105 GHz IF and at 21 MHz baseband, 1 Nov. "
                    "Data: phase_detector_calibration/furuno_detector_1nov_pll_on and _pll_off_deliberate.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(PD / "furuno_detector_1nov_pll_off_deliberate" / "iq_spectrum_pll_on_vs_off.png", dpi=90)
    plt.close(fig)


def pd_first():
    rows = list(csv.reader(open(ROOT / "data" / "Phase Detector Test  9_16_26.csv")))
    powers = [c for c in rows[1] if c.startswith("TX")]
    cols = [i for i, c in enumerate(rows[3]) if c.startswith("Input Frequency")]
    fig, ax = plt.subplots(figsize=(11, 5))
    for pw, ci in zip(powers, cols):
        pts = []
        for r in rows[5:]:
            try:
                pts.append((float(r[ci]), float(r[ci + 1])))
            except (ValueError, IndexError):
                pass
        pts = [q for q in pts if q[0] < 1.5]
        a = np.array(sorted(pts))
        ax.plot(a[:, 0] * 1e3, a[:, 1], "-o", ms=3, label=pw.replace("TX Power dBm = ", "Pluto TX ") + " dBm")
    ax.set(xlabel="Pluto frequency (MHz)", ylabel="multimeter reading (mV, as typed: column says 'Output Voltage mW')",
           title="First phase detector test by hand, 16 Sept: multimeter reading against frequency at four Pluto levels")
    ax.grid(alpha=0.3)
    ax.legend()
    setup_note(fig, "as written in the file: Pluto SDR -> splitter -> mixer -> BNC -> split cables -> multimeter. Data: data/Phase Detector Test  9_16_26.csv.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(ROOT / "data" / "Phase_Detector_Test_9_16_26.png", dpi=90)
    plt.close(fig)


def vco_hand():
    rows = [r for r in csv.reader(open(ROOT / "data" / "VCO tests - absolute accuracy 10_4_2026.csv")) if len(r) > 5 and r[1].replace(".", "").isdigit()]
    v = np.array([float(r[1]) for r in rows])
    f0, f10, pr = (np.array([float(r[k]) for r in rows]) for k in (2, 3, 4))
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    ax[0].plot(v, f0 * 1e3, "-o", label="read at once")
    ax[0].plot(v, f10 * 1e3, "--s", label="read after 10 s")
    ax[0].plot(v, pr * 1e3, ":", color="k", label="predicted (datasheet line)")
    ax[0].set(ylabel="frequency (MHz)", title="VCO frequency against tuning voltage, typed in by hand, 4 Oct")
    ax[1].plot(v, (f0 - pr) * 1e3, "-o", label="read at once minus predicted")
    ax[1].plot(v, (f10 - f0) * 1e3, "-s", label="after 10 s minus at once")
    ax[1].set(xlabel="tuning voltage (V)", ylabel="MHz", title="Error against the prediction, and the change after 10 s (about one spectrum-analyzer step)")
    for a in ax:
        a.grid(alpha=0.3)
        a.legend()
    setup_note(fig, "bench supply -> VCO tuning pin; VCO output -> spectrum analyzer, read by hand. Data: data/VCO tests - absolute accuracy 10_4_2026.csv.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ROOT / "data" / "VCO_tests_absolute_accuracy_10_4_2026.png", dpi=90)
    plt.close(fig)


def vna_markers():
    V = ROOT / "radar_test" / "vna"
    sets = [("mixer_ZX05-30W_LO_RF.csv", "ZX05-30W-S+ LO (port 1) to RF (port 2), IF open"),
            ("mixer_ZX05-30W_LO_IF.csv", "ZX05-30W-S+ LO (port 1) to IF (port 2), RF open"),
            ("mixer_ZX05-30W_IF_RF.csv", "ZX05-30W-S+ IF (port 1) to RF (port 2), LO open"),
            ("limiter_S_params.csv", "HLM-20PSM limiter")]
    fig, ax = plt.subplots(len(sets), 1, figsize=(11, 3.2 * len(sets)))
    for a, (fn, t) in zip(ax, sets):
        rows = [r for r in csv.reader(open(V / fn)) if r and not r[0].startswith("#")]
        head, data = rows[0], np.array([[float(x) for x in r] for r in rows[1:]])
        data = data[np.argsort(data[:, 1])]
        for k in range(2, data.shape[1]):
            a.plot(data[:, 1], data[:, k], "-o", label=head[k])
        a.set(xscale="log", xlabel="frequency (GHz)", ylabel="dB", title=f"{t}: VNA marker values" + (" (unpowered, no LO drive)" if "ZX05" in t else " (unpowered)"))
        a.grid(alpha=0.3, which="both")
        a.legend(fontsize=8, ncol=4)
    setup_note(fig, "VNA, 2-port calibration, part unpowered; the unused mixer port left open as in the setup photos. Marker values only (5 frequencies). "
                    "Data: radar_test/vna/*.csv; the full traces are the screenshots shown below.")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(V / "vna_marker_values.png", dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    for fn in (noise, furuno_iq, pd_first, vco_hand, vna_markers):
        try:
            fn()
            print("ok", fn.__name__)
        except Exception as e:      # one bad file should not stop the others
            print("FAILED", fn.__name__, repr(e))
