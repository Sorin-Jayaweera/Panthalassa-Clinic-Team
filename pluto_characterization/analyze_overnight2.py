"""Second and third sets of overnight blocks. Imported at the end of analyze_overnight.py; uses its data and helpers."""
import csv

import matplotlib.pyplot as plt
import numpy as np


def run(B, S, TR, HERE, save, r2):
    # ---------------------------------------------------------------- LO leakage and other sideband against level
    if B["leak_vs_level"]:
        S["leak"] = []
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
        for f in (1.0e9, 1.1e9, 1.2e9):
            atts = sorted({r["att_db"] for r in B["leak_vs_level"] if r["freq_set_hz"] == f})
            for s_ in sorted({r["scale"] for r in B["leak_vs_level"]}, reverse=True):
                ok, lo_, sb_ = [], [], []
                for att in atts:
                    g = {r["note"]: r["level_dbm"] for r in B["leak_vs_level"] if r["freq_set_hz"] == f and r["att_db"] == att and r["scale"] == s_}
                    if len(g) == 3:
                        ok.append(att)
                        lo_.append(g["LO"])
                        sb_.append(g["other sideband"] - g["tone"])
                        S["leak"].append([f / 1e6, att, s_, r2(g["tone"], 1), r2(g["LO"], 1), r2(g["LO"] - g["tone"], 1), r2(g["other sideband"], 1), r2(g["other sideband"] - g["tone"], 1)])
                if f == 1.1e9 and s_ in (1.0, 0.5, 0.1, 0.02):
                    ax[0].plot(ok, lo_, "o-", ms=3, label=f"tone scale {s_}")
                    ax[1].plot(ok, sb_, "o-", ms=3, label=f"tone scale {s_}")
        ax[0].plot([0, 60], [-60, -120], color="gray", ls=":", label="1 dB per dB")
        ax[0].set(xlabel="Attenuation setting (dB)", ylabel="LO leakage (dBm)", title="LO leakage at 1099 MHz against attenuation setting")
        ax[1].set(xlabel="Attenuation setting (dB)", ylabel="Other sideband relative to the tone (dB)", title="Other sideband (1098 MHz) relative to the tone")
        for x in ax:
            x.grid(alpha=0.3)
            x.legend(fontsize=8)
        save(fig, "pluto_leak")

    # ---------------------------------------------------------------- tone offset at other LO frequencies
    if B["offset_more"]:
        S["offset_more"] = []
        for r in B["offset_more"]:
            if r["note"] != "tone":
                continue
            g = {x["note"]: x["level_dbm"] for x in B["offset_more"] if x["freq_set_hz"] == r["freq_set_hz"] and x["offset_hz"] == r["offset_hz"]}
            S["offset_more"].append([r2((r["freq_set_hz"] - r["offset_hz"]) / 1e6, 0), r2(r["offset_hz"] / 1e6, 1), r2(g["tone"]), r2(g["LO"] - g["tone"], 1), r2(g["other sideband"] - g["tone"], 1)])

    # ---------------------------------------------------------------- tuning step
    if B["tune_step"]:
        S["tune"] = []
        S["tune_drift"] = []
        for base in sorted({round(r["freq_set_hz"], -4) for r in B["tune_step"]}):
            g = [r for r in B["tune_step"] if abs(r["freq_set_hz"] - base) < 1e4]
            f0, f1 = g[0]["freq_meas_hz"], g[-1]["freq_meas_hz"]          # first and last are both "+0 Hz": the difference is drift
            for i, r in enumerate(g):
                asked = r["freq_set_hz"] - base
                drift = (f1 - f0) * i / (len(g) - 1)
                S["tune"].append([base / 1e6, r2(asked, 0), r2(r["freq_meas_hz"] - f0, 0), r2(r["freq_meas_hz"] - f0 - drift, 0)])
            S["tune_drift"].append([base / 1e6, r2(f1 - f0, 0), (g[-1]["t"] - g[0]["t"]).total_seconds()])

    # ---------------------------------------------------------------- close-in spectra
    if B["close_in"]:
        fig, ax = plt.subplots(2, 2, figsize=(13, 8))
        S["close_in"] = []
        for k, (span, rbw) in enumerate(((1e6, 3e3), (100e3, 300), (10e3, 30), (1e3, 10))):
            a_ = ax[k // 2, k % 2]
            for f in (1000, 1100, 1200):
                p_ = TR / f"closein_{f}MHz_att0_span{span:.0f}.csv"
                if not p_.exists():
                    continue
                d = np.genfromtxt(p_, delimiter=",", skip_header=1)
                pk = d[:, 1].max()
                fc = d[np.argmax(d[:, 1]), 0]
                a_.plot((d[:, 0] - fc) / 1e3, d[:, 1] - pk, lw=0.8, label=f"{f} MHz")
                off = np.abs(d[:, 0] - fc)
                m = (off > 0.3 * span) & (off < 0.45 * span)
                S["close_in"].append([f, span, rbw, r2(np.median(d[m, 1]) - pk, 1), r2(np.median(d[m, 1]) - pk - 10 * np.log10(rbw), 1), r2(d[off > 0.1 * span, 1].max() - pk, 1)])
            p_ = TR / f"closein_tone_off_span{span:.0f}.csv"
            if p_.exists():
                d = np.genfromtxt(p_, delimiter=",", skip_header=1)
                a_.plot((d[:, 0] - d[:, 0].mean()) / 1e3, d[:, 1] + 0.45, lw=0.8, color="k", label="tone off (analyzer noise)")
            a_.set(xlabel="Offset from the tone (kHz)", ylabel="Level relative to the tone (dB)", title=f"Span {span/1e3:.0f} kHz, bandwidth {rbw:.0f} Hz")
            a_.grid(alpha=0.3)
            a_.legend(fontsize=8)
        fig.suptitle("Spectrum close to the tone, attenuation 0 dB, tone scale 0.5", fontweight="bold")
        save(fig, "pluto_close_in")

    # ---------------------------------------------------------------- low level at more frequencies
    if B["low_more"]:
        S["low_more"] = []
        for f in sorted({r["freq_set_hz"] for r in B["low_more"]}):
            sets = {nn: {r["att_db"]: r["level_dbm"] for r in B["low_more"] if r["freq_set_hz"] == f and r["note"] == nn} for nn in ("rl+10", "rl-10", "rl-30 preamp")}
            if not all(len(v) >= 5 for v in sets.values()):
                continue
            o1 = np.mean([sets["rl+10"][a] - sets["rl-10"][a] for a in (20, 30, 40)])
            o2 = np.mean([sets["rl-10"][a] + o1 - sets["rl-30 preamp"][a] for a in (40, 50, 60)])
            tab = {a: sets["rl+10"][a] for a in (0, 10, 20, 30, 40)}
            tab.update({a: sets["rl-10"][a] + o1 for a in (50, 60)})
            tab.update({a: sets["rl-30 preamp"][a] + o2 for a in (70, 80, 89.75)})
            S["low_more"].append([f / 1e6] + [r2(tab[a]) for a in (0, 10, 20, 30, 40, 50, 60, 70, 80, 89.75)] + [r2(max(abs(tab[a] - (tab[20] + 20 - a)) for a in tab if a >= 20))])

    # ---------------------------------------------------------------- IF band table, 1 MHz steps
    if len(B["if_band"]) > 100:
        g = B["if_band"]
        atts = sorted({r["att_db"] for r in g})
        fs = sorted({r["freq_set_hz"] for r in g})
        T = np.full((len(fs), len(atts)), np.nan)
        for r in g:
            T[fs.index(r["freq_set_hz"]), atts.index(r["att_db"])] = r["level_dbm"]
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
        for a in (0, 10, 20, 30, 40):
            ax[0].plot(np.array(fs) / 1e6, T[:, atts.index(a)] + a, lw=1, label=f"{a} dB (plotted + {a} dB)")
        j20 = atts.index(20.0)
        dep = T - (T[:, [j20]] + 20 - np.array(atts)[None, :])
        im = ax[1].imshow(dep.T, aspect="auto", origin="lower", extent=[fs[0] / 1e6, fs[-1] / 1e6, atts[0] - 1, atts[-1] + 1], cmap="RdBu_r", vmin=-1.2, vmax=1.2)
        fig.colorbar(im, ax=ax[1], label="Measured minus (20 dB reading + 20 - setting) (dB)")
        ax[0].set(xlabel="Tone frequency (MHz)", ylabel="Output referred to 0 dB attenuation (dBm)", title="Output across the IF band, 1 MHz steps")
        ax[1].set(xlabel="Tone frequency (MHz)", ylabel="Attenuation setting (dB)", title="Departure from 1 dB per dB")
        ax[0].grid(alpha=0.3)
        ax[0].legend(fontsize=8)
        save(fig, "pluto_if_band")
        with open(HERE / "pluto_if_band_table.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["freq_mhz"] + [f"level_dbm_att{a:g}" for a in atts])
            for i, f in enumerate(fs):
                w.writerow([f"{f/1e6:.0f}"] + [f"{x:.2f}" for x in T[i]])
        j0 = atts.index(0.0)
        S["if_band"] = dict(n=len(g), freqs=len(fs), atts=len(atts), att0=[r2(np.nanmin(T[:, j0])), r2(np.nanmax(T[:, j0]))],
                            att0_min_at=fs[int(np.nanargmin(T[:, j0]))] / 1e6, att0_max_at=fs[int(np.nanargmax(T[:, j0]))] / 1e6,
                            att20=[r2(np.nanmin(T[:, j20])), r2(np.nanmax(T[:, j20]))], dep0=[r2(np.nanmin(dep[:, j0])), r2(np.nanmax(dep[:, j0]))],
                            dep40=[r2(np.nanmin(dep[:, -1])), r2(np.nanmax(dep[:, -1]))], largest_change_per_mhz=r2(np.nanmax(np.abs(np.diff(T[:, j20])))),
                            rows=[[fs[i] / 1e6] + [r2(T[i, atts.index(a)]) for a in (0, 4, 10, 20, 30, 40)] for i in range(0, len(fs), 10)])
    if B["if_band_scale"]:
        S["if_scale"] = []
        for f in sorted({r["freq_set_hz"] for r in B["if_band_scale"]}):
            row = [f / 1e6]
            for att in (0.0, 10.0, 20.0):
                g = {r["scale"]: r["level_dbm"] for r in B["if_band_scale"] if r["freq_set_hz"] == f and r["att_db"] == att}
                row += [r2(g[1.0]), r2(g[1.0] - g[0.5] - 6.02)]
            S["if_scale"].append(row)

    # ---------------------------------------------------------------- pulses
    if B["pulse"]:
        S["pulse"] = [[r["att_db"], r["scale"], r2(r["level_dbm"]), r["note"].split(";")[0]] for r in B["pulse"]]
    S["pulse_width"] = []
    for wd in (100, 20, 10, 5, 2, 1):
        c = sorted(TR.glob(f"pulse_w{wd}us_swt*us.csv"), key=lambda q: float(q.stem.split("swt")[1][:-2]))
        if not c:
            continue
        d = np.genfromtxt(c[0], delimiter=",", skip_header=1)
        t, y = d[:, 0], d[:, 1]
        k = int(np.argmax(y[20:200])) + 20 if wd < 100 else int(np.argmax(y[:200]))      # the second pulse in the trace (the first is cut by the trigger)
        if wd == 100:
            k = 20
        hi = y[k]
        a = k
        while a > 0 and y[a - 1] > hi - 6:
            a -= 1
        b_ = k
        while b_ < len(y) - 1 and y[b_ + 1] > hi - 6:
            b_ += 1
        pk = np.where(y > y.max() - 6)[0]
        gaps = np.diff(t[pk][np.r_[True, np.diff(pk) > 5]])
        S["pulse_width"].append([wd, r2(t[b_] - t[a] + (t[1] - t[0]), 1), r2(float(np.median(gaps)), 1) if len(gaps) else None, r2(y.max()), r2(np.median(y[y < y.max() - 30]), 1), r2(t[1] - t[0], 2)])
    if not S["pulse_width"]:
        del S["pulse_width"]
    if B["pulse_spectrum_peak"]:
        cw = [r["level_dbm"] for r in B["pulse_spectrum_peak"] if r["note"].startswith("continuous")]
        S["pulse_peak"] = []
        for r in B["pulse_spectrum_peak"]:
            if "span 40 MHz" not in r["note"]:
                continue
            w = float(r["note"].split("asked ")[1].split(" ns")[0])
            samples = int(r["note"].split("width_samples=")[1].split()[0])
            S["pulse_peak"].append([w, samples, r2(samples / 30.72e6 * 1e9, 1), r["scale"], r2(r["level_dbm"]), r2(r["level_dbm"] - (cw[0] if cw else 0)), None])
        ref = next((x for x in S["pulse_peak"] if x[0] == 1000.0 and x[3] == 0.5), None)
        for x in S["pulse_peak"]:
            if ref and x[3] == 0.5:
                x[6] = r2(x[4] - ref[4] - 20 * np.log10(x[2] / ref[2]))
        S["pulse_cw_ref"] = r2(cw[0]) if cw else None
    sp = sorted(TR.glob("pulsepk_w*_amp0.5_span40MHz.csv"), key=lambda q: -float(q.stem.split("_w")[1].split("ns")[0]))
    if sp:
        S["pulse_spectrum"] = []
        fig, ax = plt.subplots(figsize=(12, 5))
        for p_ in sp:
            d = np.genfromtxt(p_, delimiter=",", skip_header=1)
            k0 = int(np.argmax(d[:, 1]))

            def first_null(idx):
                y = d[idx, 1]
                ys = np.convolve(y, np.ones(5) / 5, mode="same")            # light smoothing; the peak-detector trace is already steady
                for i in range(6, len(ys) - 6):
                    if ys[i] < ys[0] - 10 and ys[i] == ys[i - 6:i + 7].min() and ys[i + 6] > ys[i] + 2:
                        return abs(d[idx[i], 0] - d[k0, 0])
                return None
            up = first_null(np.arange(k0, len(d)))
            dn = first_null(np.arange(k0, -1, -1))
            w = p_.stem.split("_w")[1].split("ns")[0]
            S["pulse_spectrum"].append([w, r2(d[k0, 1]), None if up is None else r2(up / 1e6, 2), None if dn is None else r2(dn / 1e6, 2)])
            if w in ("2000", "1200", "500", "200", "100", "32"):
                ax.plot((d[:, 0] - 1.1e9) / 1e6, d[:, 1], lw=0.9, label=f"asked {w} ns")
        ax.set(xlabel="Offset from 1100 MHz (MHz)", ylabel="Level in 100 kHz bandwidth (dBm)", title="Pulse spectrum, one pulse every 100 us, attenuation 0 dB, amplitude 0.5 (peak detector, 3 s sweep)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        save(fig, "pluto_pulse_spectrum")
    zs = sorted(TR.glob("pulse_w*us_swt*us.csv"))
    if zs:
        fig, ax = plt.subplots(2, 3, figsize=(15, 8))
        for k, wd in enumerate((100, 20, 10, 5, 2, 1)):
            c = sorted(TR.glob(f"pulse_w{wd}us_swt*us.csv"), key=lambda q: float(q.stem.split("swt")[1][:-2]))
            if not c:
                continue
            d = np.genfromtxt(c[0], delimiter=",", skip_header=1)
            ax[k // 3, k % 3].plot(d[:, 0], d[:, 1], lw=0.9)
            ax[k // 3, k % 3].set(xlabel="Time (us)", ylabel="Level (dBm)", title=f"Asked {wd} us")
            ax[k // 3, k % 3].grid(alpha=0.3)
        fig.suptitle("Pulses seen by the spectrum analyzer at 1100 MHz (zero span, bandwidth 1 MHz)", fontweight="bold")
        save(fig, "pluto_pulse_time")
    if B["pulse_check"]:
        S["pulse_check"] = [[r2(r["level_dbm"]), r["note"]] for r in B["pulse_check"]]
