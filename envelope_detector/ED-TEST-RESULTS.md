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
- [x] End-of-test EREF: **1.139 V** (start 1.138 V). No-RF VENV on the CGR-201: 1.1412 V before, 1.1436 V after (+2.4 mV).
- [ ] Step 5: repeat at 1.0 and 1.2 GHz (`ed_sweep.py --freq 1.0e9 --ask-vrms`, then `--freq 1.2e9`).
- [ ] Step 6: pulse response (100 µs and 10 µs pulses, GRC flowgraph with Pulsed ticked).
- [ ] Fix the Pluto's USB power (straight into the Mac or a powered hub).
      It dropped off twice today.
