# Test A results: ADL5511 envelope detector, CW at 1.1 GHz

Run 2026-10-26, 22:00–22:08.
- Data: `data/ed_sweep_1.10GHz_20261026_220822.csv`
- Plot: `data/ed_sweep_1.10GHz_20261026_220822.png`
- Sweep: `ed_sweep.py`; analysis: `plot_ed_sweep.py`

Setup:
- Pluto TX → SMA → ED RFIN.
- VENV → CGR-201 Input A (3 captures averaged per step).
- VRMS → DMM, typed in by hand.
- ED at 5.00 V on an E3630A.

## Before RF (Step 1)

| | Measured | Datasheet typ. | |
|---|---|---|---|
| Supply current | 17 mA (85 mW); 20 mA with RF | 21.5 mA | ✅ |
| EREF | 1.148 V cold → 1.138 V sweep start → **1.139 V sweep end** | ≈ 1.1 V | ✅ 10 mV warm-up drift, then stable (+1 mV over the sweep) |
| VENV, no RF | 1.139 V (DMM), 1.141 V (CGR-201) | ≈ EREF | ✅ The two instruments agree within 4 mV |
| VRMS, no RF | 31–32 mV | 23 mV | ✅ Higher offset than typical; it gets subtracted |

## Sweep

"Pin" is the calibrated power at RFIN. The gain columns are each output's
rise divided by the input RMS voltage.

| TX level | Pin (cal.) | VENV − baseline | VENV gain (V/V) | VRMS | Notes |
|---|---|---|---|---|---|
| −89 … −50 dB | — | −0.5 … −0.1 mV | — | 31–32 mV | No signal; flat |
| −40 | −40 dBm | 0.3 mV | 0.12 | 35 mV | Below the floor |
| −35 | −35 dBm | 1.0 mV | 0.25 | 37 mV | Below the floor |
| −30 | −30 dBm | 4.2 mV | 0.60 | 38 mV | At the floor |
| −25 | −25 dBm | 10.9 mV | 0.87 | 45 mV | |
| −20 | −20 dBm | 25.6 mV | 1.15 | 65 mV | Datasheet table: 26 mV at −20 dBm ✅ |
| −15 | −15 dBm | 53.8 mV | 1.36 | 98 mV | |
| −10 | −10 dBm | 105.3 mV | 1.49 | 165 mV | Linear region |
| −5 | −5 dBm | 189.0 mV | 1.51 | 270 mV | Linear region |
| 0 | 0 dBm | 327.9 mV | 1.47 | 446 mV | Linear region; datasheet 1.47 ✅ |

## Conclusions

1. **The ED works as specified.** In the linear region (−10 to 0 dBm),
   VENV gain is **1.47–1.51 V/V** (datasheet 1.46–1.50). At −20 dBm the
   output is **25.6 mV**, against the datasheet's own **26 mV** at that
   level.
2. **Its two outputs agree.** VENV rise ÷ (VRMS − offset) = **0.76–0.81**
   at every level with real signal (datasheet ratio 0.77). VENV on the
   CGR-201 and VRMS on the DMM give the same input power within **0.4 dB**
   from −25 to 0 dBm.
3. **Pluto calibration: Pin ≈ TX level (+0.0 dB, ±0.25 dB).** At full level
   (TX 0 dB), the Pluto delivers **0.0 dBm** at the ED, at 1.1 GHz, through
   this cable, with this flowgraph's 0.7 amplitude. Every other level is
   just the TX setting in dBm.
4. **Working range in this test: about −30 to 0 dBm.**
   - The bottom is the ED's floor, about −30 dBm, as the datasheet says.
   - The top is only the Pluto's maximum; the ED is rated to +17 dBm.
   - Below about −15 dBm, VENV falls under the straight-line 1.47 × Vin:
     about 2 dB low at −20 dBm, about 5 dB low at −30 dBm. Use the
     **measured** curve below, not the datasheet line, when setting
     thresholds.
5. **Threshold lookup** (comparator IN− set this far above the VENV no-RF
   baseline → trips at):

   | Threshold above baseline | Trips at |
   |---|---|
   | +5 mV | −29 dBm (inside the noise; don't use) |
   | +10 mV | −25.5 dBm |
   | **+20 mV** | **−21.5 dBm** (a sensible first setting) |
   | +50 mV | −15.5 dBm |
   | +100 mV | −10.4 dBm |
   | +200 mV | −4.5 dBm |

6. **Set thresholds relative to the measured baseline, not a fixed
   voltage.** EREF and VENV drifted about 10 mV while the board warmed up
   (1.148 → 1.138 V), which is as large as a sensitive threshold. Once warm,
   they held within 1–2.4 mV over the 10-minute sweep. **Rule for the
   comparator test:**
   - let the ED run about **10 minutes**;
   - measure the no-RF VENV;
   - set the threshold **relative to that**, starting at **+20 mV**
     (≈ −21.5 dBm, about 10× the warm drift).

   This rule is also in Test C of `LIMITS-AND-TEST-PLAN.md`.
7. **Noise and ripple to plan around.**
   - VENV scatter (as seen by the CGR-201) is about 2 mV rms with no signal.
   - It grows to **13.7 mV at 0 dBm (about 4 %)**. This is most likely the
     Pluto's leftover LO/image tones beating against the main tone. It
     averages out here, but the comparator (no hysteresis) will see it
     instantaneously.
   - So: threshold at least ~10–20 mV above the baseline, and not near a
     pulse's top level.

## What's left of Test A
- [x] End-of-test EREF, 26 Oct: **1.139 V** (start 1.138 V). No-RF VENV on the CGR-201: 1.1412 V before, 1.1436 V after (+2.4 mV).
- [x] Step 5, band edges: done 1 Nov (below).
- [x] Step 6, pulse response: done 1 Nov (below).
- [x] Pluto's USB power: straight into the Mac on 1 Nov; no dropouts.
- [ ] The ED's true 4 ns rise time: needs the Siglent scope (with the comparator delay test).

---

# Session 2: 1 Nov 2026 (band edges and pulses)

**Setup changes vs 26 Oct**
- **Different Pluto:** serial `…dd1f84bfdb` (26 Oct: `…f3647c41f6`).
- **Long RF cable** Pluto → RFIN, after a short cable gave intermittent RF.
- **VRMS read on CGR-201 Input B** instead of the DMM; the DMM is used for EREF only.
- **The script:** records the Pluto serial, flags unsteady steps, and has a pulse mode.

Data (`data/`):
- `ed_sweep_1.10GHz_20261101_210839.csv`, `ed_sweep_1.00GHz_20261101_211225.csv`, `ed_sweep_1.20GHz_20261101_211624.csv`
- `ed_pulse100us_1.10GHz_20261101_211840.csv`, `ed_pulse10us_1.10GHz_20261101_212417.csv`
- Plots: `ed_band_edges_20261101.png`, `ed_pulses_20261101.png`. Analysis: `plot_band_and_pulses.py`.

Not used:
- `…1.00GHz_20261101_204928_INTERMITTENT-RF_do-not-use.csv`: the RF dropped in and out at 3 steps.
- The two short-cable 1.1 GHz runs (20:31, 20:39) are the cross-check against 26 Oct; they are not part of this set.

## Checks before RF

| Check | Result |
|---|---|
| EREF (DMM) | 1.137 V → 1.136 V across the session; 0.0 mV drift within each run |
| Input A vs DMM | VENV − EREF = +4 to +8 mV (CGR-201 offset, as on 26 Oct) |
| Input B vs DMM | 1X probe. Reads 1.4 % low with an offset of −7.5 → −4.2 mV (it drifted 3 mV in 15 min). Absolute B values are only good to several mV; rises are fine |
| Cross-check vs 26 Oct, 1.1 GHz, short cable | every level 0.44–0.49 dB lower; ED output ratio unchanged. **Cause: a different Pluto.** Pin ≈ TX − 0.4 dB for this unit |

## Step 5: band edges (CW, 14 levels each, long cable)

Rises are measured against each sweep's floor rows (TX ≤ −50 dB). VRMS is
divided by 0.986 for Input B's gain error. **No step was flagged unsteady.**

| TX (dB) | VENV rise 1.0 GHz | 1.1 GHz | 1.2 GHz | VENV/VRMS 1.0 | 1.1 | 1.2 |
|---|---|---|---|---|---|---|
| −89 … −40 | ≤ 0.4 mV | ≤ 0.4 | ≤ 0.3 | — | — | — |
| −35 | 1.2 | 0.9 | 1.0 | — | — | — |
| −30 | 3.3 | 3.0 | 2.8 | — | — | — |
| −25 | 8.0 | 8.0 | 7.6 | 0.821 | 0.825 | 0.805 |
| −20 | 18.8 | 18.6 | 17.8 | 0.733 | 0.741 | 0.732 |
| −15 | 40.8 | 39.3 | 38.3 | 0.766 | 0.759 | 0.757 |
| −10 | 81.8 | 78.7 | 76.2 | 0.778 | 0.767 | 0.760 |
| −5 | 153.3 | 147.1 | 143.5 | 0.776 | 0.772 | 0.777 |
| 0 | 267.7 | 257.5 | 250.1 | 0.773 | 0.773 | 0.770 |

1. **The ED is flat across the IF band.** The ratio of its two outputs (TX ≥
   −15 dB) averages 0.773 / 0.768 / 0.766 at 1.0 / 1.1 / 1.2 GHz: **+0.06 dB
   and −0.02 dB** against the centre. The datasheet predicts ~0.1 dB. One
   comparator threshold works for every radar in 9.3–9.5 GHz.
2. **The floor is the same at all three frequencies:** the response begins
   around TX −35 to −30 dB.
3. **Pluto + long cable, per frequency** (Pin from both outputs, TX ≥ −10 dB):

   | Frequency | Pin |
   |---|---|
   | 1.0 GHz | TX level − 1.9 dB |
   | 1.1 GHz | TX level − 2.2 dB |
   | 1.2 GHz | TX level − 2.4 dB |

   The long cable costs about 1.8 dB at 1.1 GHz against the short cable
   (−0.4 dB). The loss rises with frequency, as coax loss does. **This is the
   calibration to use with this Pluto and this cable.**

## Step 6: pulse response at 1.1 GHz (CW and pulsed back to back at each level)

The pulse is on for the stated time and off for the same time.

| Pulse | TX (dB) | CW rise (mV) | Pulse height (mV) | Height / CW | Between pulses − no-RF (mV) | Pulses seen | VRMS rise pulsed / CW |
|---|---|---|---|---|---|---|---|
| 100 µs | −20 | 18.4 | 18.3 | 1.000 | +0.1 | 25 | 0.658 |
| 100 µs | −10 | 78.9 | 78.0 | 0.989 | +1.0 | 25 | 0.676 |
| 100 µs | −5 | 147.7 | 146.7 | 0.994 | +1.0 | 24 | 0.664 |
| 100 µs | 0 | 258.1 | 254.3 | 0.985 | +2.4 | 24 | 0.650 |
| 10 µs | −20 | 18.2 | 17.7 | 0.971 | +0.3 | 31 | 0.651 |
| 10 µs | −10 | 78.3 | 76.8 | 0.981 | +0.6 | 31 | 0.701 |
| 10 µs | −5 | 147.0 | 142.6 | 0.970 | +2.0 | 30 | 0.688 |
| 10 µs | 0 | 256.8 | 250.9 | 0.977 | +3.5 | 30 | 0.706 |

1. **Pulse height = CW within the ±5 % pass band.**
   - 100 µs: 0.985–1.000 (mean 0.992).
   - 10 µs: 0.970–0.981 (mean 0.975).

   So the CW threshold table holds for pulses. The 10 µs pulses read about
   2.5 % low. **Checked afterwards (see "Extra checks"):** it's the
   Pluto's 400 kHz ripple and edge ringing against the analysis window, not
   the ED.
2. **Every pulse was seen:** 24–25 per run at 100 µs, 30–31 at 10 µs, as
   many as fit in three captures. None were missed and none were extra.
3. **Between pulses VENV returns to within 0.1–3.5 mV of the no-RF level.**
   - The level grows with the pulse level, so it's probably the tail of each
     edge, not true leakage.
   - Even taken as leakage, 3.5 mV is at the ED's floor (≈ −30 dBm) while the
     pulse is ≈ −2 dBm: an on/off contrast of at least ~28 dB.
   - **The comparator threshold (+20 mV) sits well above it.**
4. **VRMS follows the average power, as expected:**
   - 10 µs: 0.65–0.71 of CW (expected √0.5 = 0.707).
   - 100 µs: 0.65–0.68. Its averaging filter isn't much slower than the
     200 µs period, so it ripples and its mean reads a little low.

   Use VENV for pulses; VRMS is for CW power.

**Limits of this step:** the Pluto's edges (~0.5 µs) and the CGR-201 (5 MHz,
~70 ns) are far slower than the ED (4 ns). So this confirms pulse *height*
and *count*, not the ED's rise time or 50 ns–1.2 µs radar pulses.

## Extra checks, 1 Nov (after the band and pulse runs)

Data:
- `ed_sweep_1.10GHz_20261101_215000.csv`
- `ed_capture_ripple_1.10GHz_20261101_215044.csv`
- `ed_capture_pulse100us_…_215128.csv`
- `ed_capture_pulse10us_…_215212.csv`

Plot: `ed_ripple_and_pulse_shape_20261101.png` (`ed_capture.py`, `plot_capture.py`).

| Check | Result |
|---|---|
| **Input B: calibration or fault?** | Hook on GND: −2.0 to −3.2 mV, repeating within 1 mV; the offset had drifted −7.5 → −4.2 → −2.5 mV over ~75 min. Leads swapped: B read VENV 1.7 % low (1.1230 vs 1.1422 V on A), so the error **follows Input B**. **Calibration, not a fault.** Both inputs have a few mV of offset and ~1–2 % gain error; rises cancel the offset |
| **RF connector repeatability** (SMA re-seated, 1.1 GHz) | TX 0 dB: 258.2 mV (before: 257.5–258.1); TX −10 dB: 79.0 mV (78.7–78.9). **Within 0.03 dB** |
| **VENV ripple source** (CW, TX 0 dB) | One line at **400 kHz, 13.7 mV peak**, plus its harmonic at 800 kHz (1.2 mV). RF off: only ~70 kHz lines under 1 mV (bench environment). 400 kHz is **4 × the 100 kHz tone offset**: the tone at +100 kHz beating with a Pluto TX spur at −300 kHz (the IQ modulator's "−3 × f" product at full output), about −25 dBc. **Source: the Pluto, not the ED.** Not the 100/200 kHz LO/image beat first guessed |
| **10 µs pulse shape** (40 MS/s, 9 pulses averaged) | 10–90 % edge **0.65 µs** (the Pluto at 2 MS/s; the ED's 4 ns and the CGR-201's 70 ns are hidden). Overshoot at both edges, and ripple **before** each rising edge: pre-ringing comes from a digital filter, so it's the Pluto's interpolation filters. The flat top wobbles ±2–3 % with the 400 kHz ripple, which is locked to the pulses (20 µs = 8 ripple cycles). **So the 10 µs "2.5 % low" result is the Pluto's ripple and edges against the analysis window, not the ED.** Over the whole top, 0.98–0.99 × CW |

Both explanations that were flagged as unverified are now checked:
- **Ripple:** from the Pluto; its frequency is locked to the tone offset.
- **10 µs shortfall:** the Pluto's ripple and ringing.

The ripple source could be confirmed one step further by changing the tone
offset: 150 kHz would move the ripple to 600 kHz.

**For the comparator test:** with this Pluto at full output, VENV carries
±14 mV of 400 kHz ripple, and pulses overshoot ~15 % at their edges. Keep
the threshold well away from the pulse top. Lowering the tone scale or the
level reduces both effects. A real radar pulse doesn't have them.

## What it means for the comparator test
- **One threshold works across 1.0–1.2 GHz** (flat within 0.1 dB).
- **Pulse heights equal the CW values** within 1–3 %, so +20 mV above the
  no-RF VENV trips at about −21.5 dBm for pulses too. Measured on 26 Oct with
  CW; re-check at the band edges if needed.
- **Between pulses VENV sits within 3.5 mV of baseline**, well under a +20 mV
  threshold.
- **Today's Pluto + long cable:** Pin ≈ TX − 1.9 / 2.2 / 2.4 dB at 1.0 / 1.1 /
  1.2 GHz.
