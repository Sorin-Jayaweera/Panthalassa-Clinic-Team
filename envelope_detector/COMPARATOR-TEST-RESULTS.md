# Comparator results: ADCMP604 (EVAL-ADCMP604BKSZ)

Procedure: `COMPARATOR-TEST-PROCEDURE.md`. Fill in as you go. Replace "____"
with the number and its unit.

Nov 2, 6:30 pm. By Emmy

> **⚠️ Warning: this board's ADCMP604 has a faulty IN+ input.** IN+ sources ≈ 40 µA when powered (datasheet limit ±5 µA, Table 1). Results here are for scale only and are not typical ADCMP604 numbers. Don't use them to set design limits (threshold margin, offset, chatter filter). Re-measure on a replacement chip.

Setup:
- Comparator at 3.295 V (DMM at TP11) on a single-output JAIQU SPS-C3010 bench supply (not the E3630A), set 3.30 V, limit 0.039 A.
- 100 Ω across J7/J8: clips (SMA→BNC cables + BNC→grabber leads, no solder). Resistor alone 100.5 Ω; 86 Ω across J7/J8 unpowered (chip outputs in parallel, expected).
- Pot ≈ 10 kΩ (from an end-to-end reading on 6 Nov), 0.1 µF on the wiper: no (added for run 2).
- CGND/VEE tied to AGND with a grabber lead (4.8 MΩ apart before the link).
- DMM model ____. Scope probes 10×: yes / no.

## Step 0b: CGR-201 calibration

| | Measured | Expected | |
|---|---|---|---|
| Slope | 1.8525 mV/code | ≈ 1.875 (10 Oct) | 1.2 % below, OK |
| 0 V code | 2141.7 | ≈ 2047 (nominal) | 94 codes (≈ 175 mV) off nominal: this is what the calibration corrects |
| 1.200 V check (DMM) | 1.199 V | 1.200 ± 0.005 | ✅ (−1 mV) |

File: `data/cgr201_offset_cal.json` (2 Nov 2026, method: dmm).

Points: code 2261 → DMM 0.221 V (Input A 0.2107); code 3061 → DMM 1.703 V (Input A 1.6913); check → DMM 1.199 V (Input A 1.2057). Input A differs from the DMM by −10 to +7 mV, which is why Test 2 uses the DMM.

## Test 1: Supply and output levels

| Measure | LOW (IN+ = GND) | HIGH (IN+ = VCC) | Datasheet / expected | |
|---|---|---|---|---|
| Supply current | 12 mA | 12 mA | ~15.3 mA, max 21 | ✅ (supply display, 1 mA resolution) |
| VCC at jack | 3.295 V | | 3.30 | ✅ |
| IN− (J3) | 1.217 V | | 1.20 | ✅ |
| OUT+ (J7) | 1.105 V | 1.483 V | ≈ 1.00 / 1.39 (Fig. 8) | switches |
| OUT− (J8) | 1.485 V | 1.103 V | ≈ 1.39 / 1.00 | switches |
| J7 − J8 | −380 mV | +380 mV | ±245–445 (typ ≈ 390 at 3.3 V) | ✅ |
| Common mode | 1.295 V | 1.293 V | 1.125–1.375 | ✅ (change 2 mV, ≤ 50 soft check) |
| \|V_OD HIGH\| − \|V_OD LOW\| | 0 mV | | ≤ 50 | ✅ |

Result: ✅ (2 Nov 2026, evening). Notes: common mode ≈ 1.29 V, about 95 mV above the Fig. 8 typical (1.20 V at 3.3 V) but inside the guaranteed 1.125–1.375 V [DS p. 3]. Swing 380 mV matches Fig. 14 (≈ 0.39 V at 3.3 V). Supply current 12 mA is below the 15 mA typical; no minimum is specified, so this passes.

## Test 2: Trip point (offset)

### IN+ leak: summary (2–6 Nov)

| What | Result |
|---|---|
| Symptom | IN+ sits away from the source driving it; OUT+ "in between" over 35 mV (85 mV with a cap on J1); fake 17.5 / 35 mV offsets |
| Leak, powered, IN+ near 0 V | **0.04 V across 1 kΩ to AGND ≈ 40 µA out of IN+** (calc) |
| Leak, powered, IN+ ≈ 0.63 V | 30 mV across the 1 kΩ from the CGR ≈ 30 µA |
| Spec | Bias current ±5 µA; max with ≈ 1.1 V between inputs ≈ 11 µA (calc, DS Table 1: 200 kΩ min differential) |
| Board paths, unpowered | J1↔J7 / J8 12.67 MΩ; J1↔AGND 5.4 MΩ; J1↔TP11 5.5 / 12 MΩ (diodes); J1↔J2 ≈ 0 Ω |
| Ruled out | Feedback resistor, pull-up or pull-down on the board, CGR / Input A / Input B |
| Conclusion | Faulty IN+ inside the chip. Cause unknown |
| Decision (6 Nov) | Carry on for scale: Test 4 first, then Test 2 with 100 Ω in place of the 1 kΩ, Test 3 optional. Remove the J1 capacitor first. Re-check the leak (1 kΩ J1→AGND, powered) at the start of each session. Replace the chip before design numbers |

Detailed log below.

From `data/cmp_trip_summary.csv`. DMM red on J1, black on J3.

Setup check before the sweep (2 Nov, board at 3.30 V / 13 mA, IN− 1.217 V): CGR set to 0.600 V read 0.601 V at its grabber, but **J1 read 0.630 V**, i.e. IN+ sits *above* the CGR. 30 mV across the 1 kΩ (J1 side positive) = 30 µA flowing out of J1. IN− unchanged at 1.217 V. With the CGR unclipped, **J1 floats to 1.252 V**. So J1 looks like ≈ 21 kΩ to ≈ 1.25 V (calc: (1.252 − 0.630) V / 30 µA), not the ≥ 100 kΩ common-mode resistance in [DS Table 1]. Source: the chip's own IN+ (see Check 3–4). It doesn't affect the Test 2 offset (DMM reads J1 − J3 at the pins), and the low-impedance ED output in Test 4 won't notice it, but the team should check the board schematic.

| IN− (DMM at J3) | Offset up | Offset down | Offset (mean) | Input A estimate | Hysteresis | 10–90 % width | Max in-between | ≤ ±5 mV? |
|---|---|---|---|---|---|---|---|---|
| 1.157 V (≈1.16) | 20 mV (DMM) | 15 mV (DMM) | 17.5 mV | 29.0 mV | 7.41 mV | 1.48 mV | 100 % | ❌ provisional, being checked (see note) |
| 1.157 V run 2 (caps) | 33 mV (DMM) | 38 mV (DMM) | 35.5 mV | 39.2 mV | −2.73 mV | 24.09 mV | 97 % | ❌ invalid (band ≈ 85 mV) |
| 1.152 V run 3 (100 Ω, no J1 cap) | 44 mV (DMM, top edge) | 45 mV (DMM, top edge) | band centre ≈ 0 mV (calc) | 49.3 mV | −0.25 mV | 3.46 mV (top edge only) | 100 % | band ±45 mV around IN−: see note |
| 1.241 V run 4 (100 Ω) | 44 mV (DMM, top edge) | 45 mV (DMM, top edge) | band centre ≈ +2 mV (calc, ± ~6) | 50.5 mV | −0.84 mV | — | 100 % (coarse) | band ≈ −39 to +31…+55 mV, unstable: see note | | | | | | | | |
| 1.343 V run 5 (100 Ω) | 38 mV (DMM, top edge) | 36 mV (DMM, top edge) | band centre ≈ +3.5 mV (calc) | 45.1 mV | 3.89 mV (top edge) | 5.07 mV (top edge) | 100 % | band ≈ −30 to +37 mV | | | | | | | | |
| 1.663 V run 6 (100 Ω) | 36 mV (DMM, top edge) | 32 mV (DMM, top edge) | band centre ≈ −6.5 mV (calc, ± ~8) | 41.4 mV | 5.16 mV (script) | — | 98 % | band ≈ −53 to +32…+48 mV |

Run 1 (2 Nov 21:55, `data/cmp_trip_vn1.157_20261102_215527.csv`): Input B read OUT+ 1.260 / 1.652 V (392 mV swing; Input B's level is ~155 mV above the Test 1 DMM values, uncalibrated channel). Parked "up" at code 2779 OUT+ was already high 100 % of the time; "down" at 2776, 18 %. Hysteresis 7.4 mV and 100 % "in-between" don't fit a no-hysteresis part with a clean output: suspect oscillation and/or the J1 loading (≈ 21 kΩ to 1.25 V) found in the setup check. Offset not accepted until checked.

Step-file analysis (Input B = OUT+, low 1.258 V, high 1.650 V): OUT+ has **three** states, not two.
- Low up to code 2753 (set 1.132 V, Input A 1.146 V).
- From code 2757 (set 1.140 V, Input A 1.151 V) to 2779 (set 1.181 V): every sample "in between", mean rising smoothly 1.437 → 1.534 V, i.e. 46 % → 70 % of the way from low to high (calc). Reads as fast oscillation averaged by the CGR's 5 MHz input [CGR], starting near 50 % duty, so the real trip point is near code 2755 (≈ 10–15 mV *below* IN−, from Input A, calc).
- Snaps fully high at 2780 going up, back to "in between" at 2775 going down: the 7.4 mV "hysteresis" is this snap, and the script's 17.5 mV "offset" is the top of the oscillating band, not the trip point.
- So the band where OUT+ isn't cleanly low or high is ≈ 40 mV wide (codes 2755–2780, calc). DMM check at ref_low: −67 mV measured vs −72 predicted.
Cause: the faulty IN+ (Checks 3–4); oscillation from slow input + high-impedance input nodes (J1 ≈ 1 kΩ, pot wiper with no capacitor) + extra load on OUT+ (Input B cable on J7 only). Next: 0.1 µF from J3 and J1 to AGND and re-run.
Run 2 (2 Nov 22:13, 0.1 µF wiper→AGND and 0.1 µF J1→AGND added, `--span 0.08`, `data/cmp_trip_vn1.157_20261102_221348.csv`): worse. OUT+ (Input B mean) now rises smoothly from 1.26 V at Input A ≈ 1.115 V to 1.64 V at Input A ≈ 1.202 V: a ≈ 85 mV band behaving like an amplifier with gain ≈ 4 (calc), not a comparator. Script output: offset 35.5 mV (DMM 33 / 38), hysteresis −2.7 mV, 10–90 % width 24 mV. Not a valid offset.
Re-reading the setup check: J1 "floating at 1.252 V" was taken with IN− at 1.217 V, i.e. IN+ ≈ 35 mV above IN−, about where runs 1–2 put the "trip". *(Superseded: ruled out by Check 2.)* That pattern fits **negative feedback from the outputs into IN+** (an IN+ that, left alone, parks itself at the threshold). With OUT− at 1.485 V and J1 at 0.630 V drawing 30 µA, a path of ≈ 28 kΩ from OUT− to J1 would explain it (calc, hypothesis). Next: unpowered resistance J1↔J7, J1↔J8, J1↔J2, J3↔J7/J8.
Check 2 (unpowered, CGR and Inputs A/B unplugged, 100 Ω and both caps in place): J1↔J7 12.67 MΩ, J1↔J8 12.67 MΩ, J1↔AGND 5.4 MΩ, **J1↔J2 ≈ 0 Ω (J2 "IN+FB" is the same node as IN+)**, J3↔J7 2.3 kΩ, J7↔AGND 166 Ω. No resistor from the outputs to IN+: the feedback-resistor idea is ruled out. J3↔J7 ≈ pot wiper (≈ 2.3 kΩ, calc) + the output path to AGND, so not a feedback path either.
Datasheet check [DS Table 1, p. 3]: bias current IP, IN −5.0 to +5.0 µA (±2 typ); common-mode resistance 100 kΩ min (370 typ); differential-mode resistance 200 kΩ min (750 typ); active gain 62 dB. Measured ≈ 30 µA out of J1 at 0.63 V (IN− 1.217 V) is about 6× the bias-current limit; bias plus differential-resistance current at that point is at most ≈ 8 µA (calc: 5 µA + 0.587 V / 200 kΩ). Unpowered, J1 looks normal (5.4 MΩ). **Suspect: the IN+ input leaks when powered (possible damage).** Next: leakage test with 1 kΩ from J1 to AGND, board powered, CGR disconnected.
Check 3 (powered 3.30 V, CGR and Inputs A/B unplugged, 1 kΩ from J1 to AGND): **J1 = 0.04 V → ≈ 40 µA out of IN+** (calc: 40 mV / 1 kΩ) with IN+ near 0 V. That is ≈ 8× the ±5 µA bias-current limit [DS Table 1]. Confirms the leak without the CGR. Cause unknown (faulty/damaged IN+, or a part on the board that only matters when powered): one more check, J1↔TP11 (VCC) unpowered.
Check 4 (unpowered, 1 kΩ unclipped from AGND): J1↔TP11 5.5 MΩ one way, 12 MΩ the other. (A first reading of 10 kΩ both ways went J1 → 1 kΩ → AGND → pot → TP11 through our own wiring; it puts the pot at ≈ 10 kΩ.) **Nothing on the board pulls IN+ up or down.** With power on, IN+ sources ≈ 40 µA; the most a healthy part could draw here is ≈ 11 µA (calc: 5 µA bias + ≈ 1.1 V / 200 kΩ differential). **Conclusion: this chip's IN+ input is faulty.** Test 2–4 numbers from this board won't represent a good ADCMP604; replace the chip or board before measuring for real.
Run 3 (5 Nov 21:24, recalibrated 1.8550 mV/code, 0 V at code 2155.9; 100 Ω in place of the 1 kΩ; J1 capacitor removed; wiper capacitor kept; `data/cmp_trip_vn1.152_20261105_212405.csv`). J1 tracked the CGR to within a few mV (0.61 V both). IN− 1.152 V.
- OUT+ (Input B) is low up to code 2746, then "in between" from code 2750 to 2798, sitting at 1.34–1.52 V (mostly a flat 1.42–1.45 V, ≈ 43–50 % of the way up, calc), then snaps cleanly high at 2799–2800. Same going down; hysteresis −0.25 mV.
- Converting codes to IN+ − IN− using the DMM reading at code 2798 (+44 mV, so J1 ≈ CGR setting + 4.9 mV, calc): the band runs from **≈ −45 mV to ≈ +45 mV**, centred at **≈ 0 mV** (calc, ± about 2 mV).
- So the stiffer source did **not** shrink the band (≈ 90 mV wide now; 35 mV in run 1 was only its upper part, measured differently). The leak doesn't explain it; something makes the output toggle whenever IN+ is within ≈ 45 mV of IN−. Likely fast oscillation through wiring parasitics [DS p. 12: capacitive loading or poor bypassing → oscillation]: clip-lead 100 Ω termination, Input B cable on J7 only, long leads.
- The script's 44.6 mV "offset" is the top edge of the band, not the trip point.
- Next: look at OUT+, J1 and J3 on the Siglent with IN+ parked mid-band.
Run 4 (5 Nov 21:29, IN− 1.241 V, 100 Ω, `data/cmp_trip_vn1.241_20261105_212912.csv`).
- Low edge clean: OUT+ leaves low between codes 2798 and 2802 (50 % at ≈ 2800, set 1.195 V). J1 ≈ setting + 6–8 mV from the two DMM readings (calc), so the low edge is at **≈ −39 mV**.
- **The oscillation changes character over time.** In the coarse scan the in-between samples sit mid-level (fast toggling, averaged by the CGR, as in run 3). In the fine scans a few seconds later the samples are split ≈ 45 % low / 45 % high / 9 % mid: toggling slow enough for the CGR to see both levels. Going down, some codes read fully high (98 %) between codes that toggle. So the top edge moves between ≈ code 2838 and 2850 (**≈ +31 to +55 mV**, calc).
- Band centre ≈ +2 mV (calc, uncertain by about ±6 mV because the top edge wanders).
- The 44.3 mV "offset" is again the top edge. 10–90 % width not computed (curve not monotonic).
Run 5 (5 Nov 21:31, IN− 1.343 V, 100 Ω, `data/cmp_trip_vn1.343_20261105_213101.csv`). J1 ≈ setting + 8 mV from the DMM readings (calc).
- Low edge: 50 % at code ≈ 2859 → **≈ −30 mV**. Top edge: 50 % high at ≈ 2896.5 going up, ≈ 2894.5 going down → **≈ +39 / +35 mV** (calc).
- In between: steady mid-level (fast mode) the whole run, no slow toggling this time. Band ≈ 67 mV wide, centre **≈ +3.5 mV** (calc).
Run 6 (5 Nov 21:33, IN− 1.663 V, just above VCC/2, 100 Ω, `data/cmp_trip_vn1.663_20261105_213314.csv`). J1 ≈ setting + 7 mV from the DMM readings (calc).
- Band starts at code ≈ 3020 → **≈ −53 mV**. Top edge ≈ +48 mV going up (code ≈ 3074.5) and ≈ +32 mV going down (≈ 3065.7): about 16 mV apart (calc).
- Mixed modes: slow toggling (≈ 43 % low / 42 % high) at codes 3022–3042 and 3062–3074, fast mid-level at 3046–3058.
- Centre ≈ −6.5 mV (calc, uncertain by about ±8 mV). Possibly the input-stage crossover near VCC/2 [DS p. 12], but within the uncertainty.
Scope check (9 Nov, Siglent SDS1104X-E, 10× probe on J7 with short ground to AGND; IN− 1.674 V; CGR `dc 1.667`, DMM J1 − J3 ≈ 0 mV):
- ⚠️ Setup note: the CGR powers up at a large negative output. Once it was clipped on before `dc` was run, and J1 read −0.2 V (protection diode) until it was unclipped. **Always run `dc` before the CGR touches the board.** Leak to be re-checked.
- **OUT+ oscillates: ≈ 27.7 MHz**, mean 1.26 V (between the DMM's 1.105 V low and 1.483 V high, so ≈ 40 % high, calc), Pk-Pk ≈ 700 mV at 100 mV/div (larger than the 380 mV swing: ringing / probe-ground pickup). *Not yet confirmed as comparator oscillation:* with IN+ ≈ 100 mV below IN− (`dc 1.56`) the 27 MHz was still there (mean 1.24 V, Pk-Pk ≈ 500 mV), and the photo at 20 ns/div shows the trace clipped off the top of the screen (Mean/Pk-Pk shown with ">") with the trigger untriggered (Auto). Could be pickup on the probe ground or supply noise. Checks (CH2 100 mV/div, 2 µs/div, Auto trigger; laptop charger plugged in nearby):
  - Probe tip on its own ground: Freq **** (no 28 MHz) → the 28 MHz is not probe pickup.
  - IN+ far below (`dc 0.50`): OUT+ steady low, mean 1.09 V (DMM low 1.105 V), short spikes ≈ 300–500 mV Pk-Pk, Freq wandering ≈ 1–4 MHz (no steady tone).
  - IN+ far above (`dc 2.50`): OUT+ steady high, mean > 1.46 V (trace at the top edge, clipped), spikes ≈ 200–340 mV Pk-Pk, Freq ≈ 0.25–0.6 MHz wandering.
  - **So the steady 27.6 MHz appears only with IN+ near IN−: it is the comparator oscillating**, as Test 2 suggested. The spikes seen at every level are background pickup (suspect the laptop charger / long ground lead), not the comparator.
  - Input B cable unplugged from J7 and laptop charger unplugged, IN+ at the threshold (`dc 1.667`): mean 1.28 V, Pk-Pk ≈ 800 mV, Freq switching between 27 MHz and ****. Still oscillating, now on and off. **The Input B cable is not the main cause.** Remaining suspects: the clip-lead 100 Ω termination and long leads [DS p. 12], or the chip. Next fix to try: solder the 100 Ω at J7/J8 (procedure Step 0 "Best").
  - Earlier reading at `dc 1.56` (≈ −107 mV) also showed 27 MHz, wider than Test 2's band edge (≈ −53 mV) at this level: the 10× probe's capacitance on J7 may widen the band [DS p. 12]. Not re-checked.
- Moments earlier, with IN+ a little lower, OUT+ sat steadily low (mean 1.11 V).
62 dB gain means the chip alone would go from low to high over ≈ 0.3 mV of input (calc: 390 mV / 1260), so the 35–85 mV band is not the chip's own gain.
DMM shows 1 mV resolution on auto range (0.020 V); use the 200 mV manual range for 0.1 mV.

Conclusions (with numbers):
(Runs 3–6, 100 Ω source, faulty-IN+ board: for scale only. "Offset" = centre of the in-between band, hand-calculated; the script's offsets are the band's top edge.)
1. Offset range across levels: ≈ −6.5 to +3.5 mV (0, +2, +3.5, −6.5 mV at 1.152 / 1.241 / 1.343 / 1.663 V). Within ±5 mV [DS Table 1]: roughly, at the three ED levels; the 1.663 V value is uncertain by ±8 mV.
2. Change from 1.15 to 1.66 V: ≈ −6.5 mV, larger than the ≈ 1.5 mV CMRR allows (calc) but within the uncertainty; may be the VCC/2 crossover.
3. Transition width: OUT+ isn't cleanly low or high over **≈ 70–100 mV** (≈ −30…−53 mV to +31…+55 mV). Far wider than the CGR's ~2 mV rms noise [ERR] or the chip's own gain (≈ 0.3 mV, calc).
4. Oscillation near the trip: **yes**, at every level, switching between a fast mode (averaged by the CGR) and a slower one (both levels visible). Not explained by the IN+ leak (the 100 Ω didn't shrink it). Suspect the clip-lead wiring [DS p. 12]. If real in the final circuit, a 20 mV threshold margin would sit inside the band.
Next: Siglent on OUT+ and J1 with IN+ parked mid-band; then try the soldered 100 Ω at J7/J8 (procedure Step 0 "Best") and without the Input B cable.

## Test 3: Chatter

From `data/cmp_scope_summary.csv`, labels `tri_*`. IN− = ____ V.

| Triangle | Slope | Bursts | Max rising per burst | Longest burst (µs) | Noise band (mV) |
|---|---|---|---|---|---|
| 1 Hz | 0.2 V/s | | | | |
| 10 Hz | 2 V/s | | | | |
| 100 Hz | 20 V/s | | | | |

Conclusions:
1. Noise band ≈ ____ mV, consistent across speeds: yes / no.
2. Smallest threshold margin that clears it: ____ mV (≥ the band).
3. Longest burst ____ µs → this is the repeat-edge filter the FPGA would need for slow edges.

## Test 4: Detector → comparator

9 Nov setup: comparator on HP E3630A +6 V output (3.310 V on DMM, ≈ 0.02 A); detector on JAIQU 5.00 V / 0.060 A limit (display 4.96 V, 0.017 A), SW1 enabled. VENV → SMA-to-BNC → BNC tee → J1, tee → BNC-grabber lead → CH1 10× probe; CH2 10× probe on J7; common ground detector GND → AGND. No 50 Ω on VENV. Pluto serial **104473b04a060** (not the 26 Oct or 1 Nov unit, so its TX level → dBm may differ by ~0.5 dB [ED]); straight into the Mac; GRC `ed_test_pluto_tx_soapy.grc` running at TX −89, CW. During warm-up the JAIQU leads touched (supply went to C.C, 0 V / 0.060 A); output off, leads separated, detector back to 0.017 A and VENV 1.14 V: no damage, warm-up restarted. `cmp_scope.py` patched locally for pyvisa-py (drain tolerates USB timeout); OUT+ thresholds `--out-lo 1.20 --out-hi 1.40` (this board: low 1.105 V, high 1.483 V).

Warm-up 10 min. VENV baseline 1.14 V. Margin (DMM J3 − J1) 18.4 mV (target 20.0).

RF-off check (3 × 60 s) at margin 18.4 → 17.2 mV (VENV drifted up ≈ 1 mV), trigger CH2 rising 1.40 V, Normal, 1 ms/div, `data/cmp_scope_rf_off_20261108_205227`: **triggered all 3 times; 366k–563k rising edges in each 14 ms record, all one continuous burst** (≈ 26–40 million edges per second, calc). ❌ With RF off and a ≈ 17 mV margin the comparator oscillates continuously: the margin sits inside the oscillation band found in Test 2 (≈ ±40–50 mV) and on the scope (27.6 MHz). Margin search, RF off (quick single shots, 10 s timeout):
| Margin (DMM J3 − J1) | Record | Result |
|---|---|---|
| 54.8 mV | 14 ms | 717k rising edges, one continuous burst; OUT+ p2/p98 1.044 / 1.58 V (full swing: real toggling) |
| ≈ 100 mV | 14 ms | triggered (run interrupted during download) |
| 110.6 mV | 1.4 ms (100 µs/div) | 74k rising edges, continuous (≈ 53 million edges per second, calc) |
| ≈ 110 mV, CH1 on VENV via the J1 tee's grabber lead (CH1 probe menu wrongly at 1X) | 1.4 ms | 63k edges; OUT+ 1.052 / 1.604 V; VENV p98 ≈ 1.27 V and spread roughly 1.07–1.27 V (×10 corrected, calc) |
| ≈ 110 mV, grabber lead and CH1 probe removed from the J1 tee (first try) | — | 74k edges, **discarded**: the scope may not have been re-armed, so this was likely a stale capture |
| ≈ 110 mV, grabber lead and CH1 probe removed from the J1 tee (repeat, `..._211555`) | 1.4 ms | **1 rising edge** (burst 0.008 µs) in the one trigger within 10 s: essentially quiet. Removing the unshielded lead on IN+ made the difference |
| ≈ 110 mV, coax-only IN+, full check 3 × 60 s (`..._211735`) | 1.4 ms | each shot: 1 rising edge, 0.008 µs burst; OUT+ otherwise low (p2/p98 1.108 / 1.136 V on the earlier single shot). Triggered within 60 s every time. Zoomed on screen (200 ns/div and 20 ns/div): each event is a **≈ 1 µs burst of ≈ 24–25 MHz ringing, swinging both above and below the 1.12 V low level** (≈ 0.87 to 1.41 V), sinusoidal, growing then dying away. A comparator flip would step up to ≈ 1.48 V and back and could not go far below its low level, so these are **interference picked up on the output wiring/probe, not pings**. ✅ RF-off counted as **pass at ≈ 110 mV** with the coax-only IN+ path. (Not checked: whether an LVDS receiver, which reads OUT+ − OUT−, would see these bursts.) The ringing frequency (≈ 25 MHz) is close to the 27–28 MHz oscillation, which suggests the clip-lead output wiring has a resonance there that the comparator locks onto when it oscillates (calc/inference). |
| ≈ 68 mV, coax-only IN+ (`..._212552`) | 1.4 ms | 64,860 rising edges, one continuous burst: **oscillating** |
| ≈ 93 mV, coax-only IN+ (`..._212803`) | 1.4 ms | 74,418 rising edges, continuous: **oscillating** |
| ≈ 106 mV (`..._213657`) | 1.4 ms | 74,034 edges: oscillating (≈ 110 was quiet earlier) |
| ≈ 145 mV (`..._213902`) | 1.4 ms | 73,206 edges, OUT+ 0.996 / 1.536 V (full swing): oscillating |
| ≈ 560 mV (`rf_off_m560`) | — | **no trigger in 10 s: quiet** |
(Margins from here on = DMM at J3 − 1.14 V. VENV read on CH1 via a BNC cable at ≈ 1.11 V; the scope's DC accuracy is a few %, so the DMM's 1.14 V is used.)
→ Not a fixed boundary: quiet at ≈ 110 mV after the grabber lead was removed, then oscillating at 106 and 145 mV after stepping down to 68/93 and back up. Looks like the oscillation **latches**: once started it continues to larger margins. Stepping down from 560 mV next.
Round A (CH1 BNC cable on the J1 tee; stepping down from quiet 560 mV): 300 mV quiet; ≈ 154 mV (`rf_off_A154`) → 73,678 edges, **oscillating**. Restart between 154 and 300 mV.
(Laptop died and was restarted here; Pluto now shares a USB-C adapter with the scope, CGR unplugged.)
Round B (CH1 cable removed: the tee only joins the detector and J1; stepping down): 560 mV → triggered, 0 edges counted (quiet; a spike just reached the 1.40 V trigger); 335 mV → same, twice (quiet); **122 mV → 37,917 edges, oscillating**; 65 mV → 37,841 edges, oscillating. Restart between 122 and 335 mV.
- Edge rate without the CH1 cable ≈ 27 million per second vs ≈ 53 million with it (calc): the cable changes the oscillation's speed, but not clearly where it starts.
- Summary: approached from above, RF-off is reliably quiet at ≈ 300 mV and above, and oscillates at ≈ 120–150 mV and below. The single quiet run at ≈ 110 mV earlier wasn't repeated.
With the grabber lead on J1's tee, it oscillated even at 110 mV; with the IN+ path all coax, 110 mV is almost quiet. Next: check the single edge, run the full 3 × 60 s RF-off check, then try smaller margins with the coax-only IN+ path.

| TX level | Pulse | Ref pulses | Hit | Missed | Extra | VENV pulse height | CW VENV rise [ED] |
|---|---|---|---|---|---|---|---|
**Pulse test at margin ≈ 335 mV** (quiet RF-off: 1 interference event; CH2 trigger 1.40 V, 1 ms/div = 14 ms ≈ 70 pulse periods; no CH1 reference, so counted against the period; Pluto through a shared USB-C adapter, no dropouts reported):
| TX level | Pulse | Expected pulses / shot | Output bursts (3 shots) | Rising edges per burst (max) | Longest burst | Reading |
|---|---|---|---|---|---|---|
| 0 dB | 100 µs | ≈ 70 | 27, 33, 23 | 2,678 / 2,714 / 2,580 | 94.7–99.5 µs | ≈ 1/3–1/2 of pulses seen, and each one is a ≈ 27 MHz chatter burst lasting the whole pulse (calc: 2,700 edges / 100 µs) |
| −3 dB | 100 µs | ≈ 70 | 0, 1, 1 (single 8–10 ns interference events) | — | — | no pulses caught |
| RF off after the pulses | — | — | 0 | — | — | quiet: the pulses did not leave it oscillating |
Why: at 0 dB VENV rises ≈ 330 mV (calc from [ED]: 105 mV at −10 dB × 1.78²), about equal to the 335 mV margin, so the pulse tops sit right at the threshold, inside the oscillation band: the comparator chatters for the whole pulse and misses the pulses whose tops fall just short. At −3 dB the rise (≈ 235 mV, calc) never reaches it. This is the teammate's concern (VENV hovering at the threshold → 0101… instead of a steady 1), seen directly.
Original table (planned for a +20 mV margin; not run, because RF-off oscillated below ≈ 150–300 mV with this wiring):

| −10 dB | 100 µs | | | | | | 105 mV |
| −15 dB | 100 µs | | | | | | 54 mV |
| −20 dB | 100 µs | | | | | | 26 mV |
| −22 dB | 100 µs | | | | | | ~18 mV (interp.) |
| −25 dB | 100 µs | | | | | | 11 mV |
| −10 dB | 10 µs | | | | | | 105 mV |
| −20 dB | 10 µs | | | | | | 26 mV |

Conclusions:
(Faulty-IN+ board, clip-lead output wiring: for scale only.)
1. Every pulse caught with no extras: **no**. The planned +20 mV margin couldn't be used: with RF off the comparator oscillated (≈ 27–53 MHz) at margins below ≈ 150–300 mV.
2. RF level where pulses start being caught: at a 335 mV margin, only 0 dB (Pluto full power, ≈ 0 dBm [ED], ±0.5 dB for this Pluto) reaches the threshold, and only ≈ 1/3–1/2 of pulses register. Predicted −21.5 dBm at +20 mV [ED] could not be tested.
3. Chatter near the trip: ≈ 2,600–2,700 rising edges per pulse (the whole 100 µs pulse), when the pulse top sits at the threshold.
4. Pulse heights vs CW: not measured (CH1 removed from the IN+ path to stop it feeding the oscillation).
5. RF-off after pulses: quiet. No sign the pulses start a lasting oscillation at this margin.
Next: solder the 100 Ω at J7/J8 (procedure Step 0 "Best"), then repeat the RF-off margin search; if the quiet margin drops to a few tens of mV, rerun this table at +20 mV.

## What's left
- [ ] Update the website Comparator tab (`site/content_env.py`) with these results
- [ ] Test 5: radar-length pulses and delay (needs a short-pulse source)
- [ ] Test 6: comparator → Icepi Zero (needs an LVDS receiver or ECP5 pair, verify)
