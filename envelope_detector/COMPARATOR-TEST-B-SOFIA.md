# Comparator Test B (board alone), 18–23 Nov 2026

ADCMP604 on the EVAL-ADCMP604BKSZ board, same board as Emmy's tests (2–9 Nov,
`COMPARATOR-TEST-RESULTS.md`). Bench work by Sofia; scripts, analysis and this write-up
made with Claude. The detailed time-stamped log is `COMPARATOR-BENCH-NOTES-SOFIA.md`;
this file is the readable version.

## Summary

- **The chip works and is not damaged.** Output levels 1.106–1.108 V (low) and
  1.493–1.505 V (high), swing about 390 mV, common mode about 1.30 V (datasheet
  1.125–1.375 V), the same as Emmy's on 2 Nov. Driven 200–280 mV away from the threshold it
  switches cleanly both ways. Supply current about 12 mA all along.
- **IN+ is not leaky now.** Emmy's leak test (1 kΩ from J1 to ground, board powered)
  gave 3.7 mV, about 3.7 µA, which is what a healthy input gives with about 1.2 V between
  the inputs. Emmy measured about 40 µA on 2 Nov.
- **The comparator oscillates (44–94 MHz) whenever IN+ is near IN−.** The output's own
  edges couple back into IN+ and IN− through the bench wiring (grabber leads, probe
  leads, cable shields, USB-grounded instruments). Every oscillating capture since 19 Nov
  looks the same: each output swings 0.7–1.1 V peak to peak (normal: 0.39 V) and the
  inputs pick up 80–250 mV.
- **The width of the oscillating zone depends on where the leads lie, not on time or on
  the chip.** It went from about 40 mV (best, 23 Nov 14:25) to about 50 mV, 140–160 mV,
  and finally "never stops" (23 Nov 20:26). Each arrangement, left untouched, repeats to
  within 3–6 mV. Only physical handling of the wiring changed it.
- **It can latch.** Once started, the oscillation can keep itself going 40–100 mV away
  from the threshold. A disturbance (connecting a cable, a meter, a pickup spike) can
  start it. In the latched state IN+ and IN− swing in opposite directions, so IN+ crosses
  IN− every cycle even though their averages are 95 mV apart.
- **The switching point** (where the average output crosses zero) stayed at +10 to +14 mV
  in every arrangement except one (+27 to +33 mV, triad 2, a lopsided oscillation).
- **What this means for the design:** this board with grabber wiring cannot show the
  chip's real threshold sharpness. Fixes are layout fixes: OUT+/OUT− as a tight
  differential pair with the termination at the receiver, IN− decoupled at the pin,
  short input traces over a ground plane, and hysteresis at the pins (or the ADCMP605's
  hysteresis pin). Requirement from the link budget: about 26–36 mV of VENV rise for the
  weakest wanted radar, so threshold margin plus transition must fit in that.
- **Hysteresis was not tested**: the planned A–B–A comparison needs a repeatable baseline,
  and the last baseline never left the oscillating state.

## Setup

### Board and instruments

| Item | Detail |
|---|---|
| Board | EVAL-ADCMP604BKSZ (ADCMP604, SC70-6). J1 IN+, J2 IN+FB (same node as J1), J3 IN−, J4 IN−FB (same node as J3), J7 OUT+, J8 OUT−. Checked 18 Nov: J1–J2 and J3–J4 about 0.1 Ω |
| Supply | 3.30 V at TP11. KUAIQU (switching, current-limited) until 23 Nov 14:10, then Agilent E3630A +6 V output (linear, no adjustable limit). About 12 mA (E3630A meter shows 0.02 A, 10 mA steps) |
| IN+ source | CGR-201 **C2BJ0VL**, DC only, through **100 Ω at J1** |
| IN− source | CGR-201 **C2BKNPC**, DC 1.20 V, through **1 kΩ in series + 100 nF to ground** (threshold network) |
| Output termination | 100 Ω between the J7 and J8 cable ends (red grabbers) |
| Scope | Siglent SDS1104X-E: SDSMMEBC3R1376 on 19 Nov, **SDSMMFCQ5R6888** on 23 Nov. ×10 probes: CH1 IN+, CH2 IN−, CH3 OUT+, CH4 OUT− |
| Scope settings | all channels ×10, DC 1 MΩ, bandwidth limit off; CH1/CH2 50 mV/div centred 1.20 V (screen 1.00–1.40 V); CH3/CH4 100 mV/div centred 1.25 V (screen 0.85–1.65 V); 1 µs/div, 500 MS/s; trigger CH3 rising 1.25 V, Auto. Snapshots at 50–200 ns/div. Script `scope_preset.py` |
| Computer | Mac; CGR-201s and scope over USB through a hub |

### Wiring and grounding

Drawings: `comparator_test_wiring.svg` (Test B and C), `comparator_grounding.svg` (ground
groups), `comparator_hysteresis.svg` (planned hysteresis resistor). Photos of the bench
on 19 Nov: `photos_cmp_sofia/`.

- Each input and the output pair is a **group**: the board-side BNC-to-grabber cable, the
  instrument cable and the probe meet at one point; their black grabbers are clipped
  together there and nothing else goes to the board's ground pins. The board-side
  cable's shield already reaches board ground through the SMA shell.
- Board ground pins: only the supply COM (CGND/VEE jack) and the TP15–TP13 link
  (AGND–CGND/VEE).
- Note: the 100 Ω at J1 and the 1 kΩ + 100 nF for J3 sit at the far (grabber) end of the
  J1 and J3 cables, not at the board. J7 and J8 are about 7 cm apart on the board, so
  the outputs cannot be terminated "at the connectors" without cables.

### Safety and calibration

- Every CGR-201 level goes through `cgr_guard.py`: DC only (waveform off, amplitude 0),
  0.10–3.00 V by that unit's own calibration, units without calibration refused.
  `cgr_dc.py <serial> <volts>` sets a level.
- Per-unit two-point calibration, DMM at the Output BNC (`data/cgr_dc_cal.json`, 19 Nov):

| Unit | mV per code | 0 V at code | Check |
|---|---|---|---|
| C2BKNPC (IN−) | 1.986 | 2229.5 | code 2834 → 1.205 V (19 Nov), 1.214–1.220 V (23 Nov) |
| C2BJ0VL (IN+) | 1.868 | 2161.4 | code 2750 → 1.102 V (19 Nov), 1.090–1.112 V (23 Nov) |

- A CGR-201 restarts at about −0.15 to −0.3 V when its USB is (re)connected, before any
  command. That is inside the comparator's working input range (down to −0.5 V), but the
  level must be set before the BNC goes on the board. A USB hub disturbance can restart
  them too (happened 23 Nov 20:02).
- After a re-plug, the CGR-201 outputs drift upward for 10–20 minutes (7–8 mV/min at
  first on 23 Nov).

### Order of work (from `COMPARATOR-PLUGIN-PROCEDURE.md`)

1. Supply on (3.30 V at TP11, about 12 mA). 2. CGR-201s on USB, levels set with
`cgr_dc.py`, checked with the DMM at the Output BNC. 3. Connect J3, then J1. 4. **Reset
IN+ once** (0.90 V → 1.10 V) to break any oscillation the connection started. 5. Check the
scope, then sweep. To stop: J1 off, J3 off, supply off. Resistance and continuity checks
only with the board unpowered.

### What a sweep is

`cmp_sweep.py`: IN+ is stepped with DC levels (a staircase) from 1.100 V to 1.320 V and
back, 147 steps: 4 codes (about 7.5 mV) far from the threshold, 1 code (about 1.9 mV)
near it; each step held about 1.5–2 s (0.3 s settle, then one 14 µs capture of all four
channels at 500 MS/s). IN− stays at its DC level. For each step: IN+ − IN− from the
scope, OUT+ − OUT− average, output variation (rms) and the fractions of time low / in
between / high. IN+ is returned to 1.100 V at the end. The input is perfectly still at
every step: any oscillation comes from the circuit.

Terms used below:
- **Leaves low / fully high:** the IN+ − IN− where the output stops being steadily low /
  becomes steadily high. **Width** = the distance between them.
- **50 % point:** where the average output crosses zero.
- **rms inside:** output variation (standard deviation of OUT+ − OUT− over 14 µs) inside
  the transition. About 3 mV = quiet; about 385 mV = flipping evenly between the levels;
  600–690 mV = flipping and ringing past both levels.

## 19 Nov 2026 (scope SDSMMEBC3R1376)

**Preliminary checks.** Supply 3.30 V, 12 mA (KUAIQU). CGR-201 outputs at the Output BNC
(DMM): C2BKNPC 1.205 V, C2BJ0VL 1.102 V. Connected: J4 (IN−) 1.235 V, J2–J4 −0.104 V;
0 mV across the 100 Ω and the 1 kΩ (no input current to 1 mV resolution: under 10 µA on
IN+, under 1 µA on IN−). OUT+ − OUT− −0.379 V (DMM). Scope at rest: OUT+ 1.107 V, OUT−
1.497 V, IN+ 1.131 V, IN− 1.233 V, about 2 mV rms. With both inputs open (before
connecting) the outputs oscillated at about 69 MHz.

| Sweep | Arrangement | Toggling from | Toggling to | Frequency | rms inside |
|---|---|---|---|---|---|
| 1 (12:21) | | **invalid**: scope returned the same capture every step (fixed in the script) | | | |
| 2 (12:27) | CH1 on IN+, grounds on one long wire | −43 mV | +53 mV | 93–94 MHz | 550–625 mV |
| 3 (12:32) | same | −42 mV | +52 mV | 93–94 MHz | similar |
| 4 (12:59) | **CH1 tip removed** | about −73 mV | about +85 mV | 67–68 MHz | 290–345 mV |
| 5 (13:46) | CH1 off; BNC-grabber black clips moved to board ground pins | about −58 mV | about +70 mV | 44 MHz | about 510 mV |

- Removing the CH1 probe **widened** the band: its 10–15 pF on IN+ was absorbing part of
  the feedback.
- Mid-band waveforms (sweep 2): outputs about 0.93 V pk-pk, IN+ 226–254 mV, IN− 100–108 mV
  pk-pk at 93 MHz.
- After moving ground clips to the board pins (13:44): short common-mode bursts on both
  outputs (30 ns, 3 % of the time) even at −100 mV; OUT+ and OUT− moved together, so
  pickup, not switching. Re-clipping one probe ground visibly changed all channels.
- 14:05–14:10, all grounds on the board, extra ground lead for the 100 nF: IN− rang at
  26–27 MHz up to 0.5 V pk-pk and flipped the output occasionally at −100 mV.
- Photos at 13:31 showed the 100 Ω termination and the threshold network were in mid-air
  on grabbers, not "at the board" as first drawn; the grounding scheme was redesigned
  (three local groups, `comparator_grounding.svg`).

Plots: `data/cmp_testB_20261119.png`. Data: `data/cmp_sweep_20261119_*.csv`,
`data/cmp_waveforms_20261119.csv`.

## 23 Nov 2026, afternoon (scope SDSMMFCQ5R6888)

**Preliminary checks (13:40–14:02).** CGR-201s re-registered (C2BJ0VL needed a USB re-plug
before its port opened). Scope settings re-applied (CH4 offset had drifted to −1.24 V).
CGR-201 outputs (DMM): C2BKNPC about 1.20 V, C2BJ0VL 1.090–1.092 V. Connected: IN+ 1.118 V,
IN− 1.218 V (scope), −100 mV; OUT+ 1.106 V, OUT− 1.498 V. Inputs open: about 70 MHz
oscillation; moving the board changed its amplitude by about 25 mV. 14 ms capture at
−100 mV: output never wrongly high (0 of 7 M samples); 1054 short common-mode bursts
(about every 13 µs, ~75 kHz) up to 222 mV pk-pk, also on IN+ and IN−.

**14:10–14:23:** supply changed to the linear E3630A (3.30 V at TP11, 0.02 A on its
meter): the 75 kHz bursts disappeared (0 in 0.28 ms where about 21 were expected).
About 14:20: OUT+ accidentally shorted to the J7 ground → OUT+ about 0 V, 65 MHz on all
channels. After removing the short: OUT+ 1.106 V, OUT− 1.502 V, common mode 1.304 V,
quiet.

**Checks before every sweep below:** both CGR-201s responding at unchanged USB addresses,
all scope settings correct, resting outputs 1.107–1.110 V / 1.503–1.505 V at about 2–3 mV
rms, IN+ − IN− about −100 mV.

| Run | Arrangement / event before it | Leaves low (up / down) | 50 % point | Fully high (up / down) | Width | rms inside |
|---|---|---|---|---|---|---|
| Sweep 6, 14:25 | E3630A, local ground groups, CH1 on IN+ | −8 / −7 mV | +11 mV | +32 / +32 mV | **40 mV** | ≈ 108 mV |
| (14:45–15:00) | 1 nF pushed into J4 (removed: unreliable, bad for the SMA), J1 100 Ω touched ground, leads re-fixed | | | | | |
| Triad 1, run 1, 15:05 | | −17 / −14 mV | +14 mV | +37 / +38 mV | 52–53 mV | ≈ 595 mV |
| Triad 1, run 2, 15:09 | | −14 / −14 mV | +14 mV | +36 / +37 mV | 50–51 mV | ≈ 595 mV |
| Triad 1, run 3, 15:18 | Mac charger plugged in | −19 / −16 mV | +12 mV | +40 / +40 mV | 56–58 mV | ≈ 560 mV |
| Baseline A, 15:31 | after a connection check | −35 / −81 mV | +27 mV | +108 / +53 mV | 134–143 mV | ≈ 677 mV |
| Triad 2, runs 1–3, 15:46–15:55 | loose leads re-laid on insulators | −44 to −47 / −85 to −87 mV | +32 to +33 mV | +111 to +114 / +71 to +75 mV | about 158 mV | ≈ 686 mV |

- Each triad repeats to about 3 mV: the bench is stable while untouched.
- In the oscillating zone the output spends about 45 % low, 15 % in between, 40 % high
  almost regardless of the input: self-oscillation, not noise.
- Triad 2 **latches**: going down it keeps oscillating to −85 mV, 40 mV past where it
  started going up.
- Waveform snapshots, 15:01 and 15:05: outputs 0.68–1.0 V pk-pk at 64–65 MHz between about
  −15 and +29 mV; IN− 200–224 mV pk-pk, IN+ 76–98 mV. At 15:01 IN+ and IN− moved **together**
  (correlation +0.8); from 15:05 on they moved in **opposite** directions (−0.9), the worst
  case for a comparator.
- AirDrop from the Mac at about 15:50 (during triad 2): no anomaly.

Plots: `data/cmp_testB_compare_20261123.png`, `cmp_testB_repeats_20261123.png`,
`cmp_testB_time_20261123.png`, `cmp_testB_overlay_20261123.png`.

## 23 Nov 2026, evening

**Preliminary checks (17:09–17:28).** All instruments had been re-plugged, so both
CGR-201s had restarted at their power-up level (inputs about −0.2 V; output correctly
high since IN+ > IN− then). Levels set at 17:09; the board saw IN− 1.177 → 1.210 V and
IN+ 1.098 → 1.118 V over 8 minutes (warm-up drift, 7–8 mV/min at first). DMM at the board
17:2x: J3 1.215 V, J1 1.105 V. Scope settings correct. Resting state 17:28: IN+ 1.127 V,
IN− 1.219 V (−92 mV), OUT+ 1.107 V, OUT− 1.503 V, 1.3–2.3 mV rms. CH1 had carried an
extra ~0.26 MHz ripple from the CGR-201 (IN+ has no filter) until a wiring change at
17:27.

| Run | Leaves low (up / down) | 50 % point | Fully high (up / down) | Width | rms inside |
|---|---|---|---|---|---|
| 17:29 | −61 / −70 mV | +12 / +10 mV | +90 / +73 mV | 143–150 mV | 667 mV |
| 17:33 | −55 / −70 mV | +12 / +12 mV | +90 / +75 mV | 145 mV | 666 mV |
| 17:37 | −55 / −66 mV | +12 / +12 mV | +97 / +73 mV | 138–151 mV | 668 mV |

**Incidents and checks, 19:35–20:45:**
- **19:35, DMM continuity beeper** between J4 shell and J3 centre with the board powered:
  started the oscillation, which then latched at −98 mV (outputs about 1 V pk-pk, IN−
  430 mV, IN+ 180 mV pk-pk, 67 MHz). Reset (IN+ to 0.90 V and back to 1.10 V) cleared it.
- **19:40:** after a reset it stayed quiet for about 12 s, then restarted on its own at
  −99 mV and stayed latched (IN− about 445 mV pk-pk).
- **20:02:** C2BKNPC restarted (USB hub disturbed when the scope was re-plugged); IN− at
  about −0.15 V for about a minute (inside the working range). Re-set; DMM 1.220 V and
  1.112 V.
- **20:06:** connecting J3 and J1 started the oscillation at once; a reset cleared it; quiet
  for 70 s of watching.
- **20:11, waveform capture of three states** (`data/cmp_states_20261123_2013.png`, outputs
  at 200 mV/div so they do not clip): freshly reset (quiet, one damped ±70 mV burst on
  IN+), inside the transition (+10 mV), and back at −95 mV still oscillating. In the
  latched state IN+ swings 1.08–1.20 V and IN− 1.14–1.31 V in opposite phase at 68 MHz,
  so IN+ rises above IN− for part of every cycle; outputs 0.75–1.85 V.
- **20:15, one sweep on battery** (Mac charger out), stopped early: oscillation started at
  −55 mV going up, the same as with the charger in.
- **20:26, final baseline** (battery): oscillation started at −48 mV going up and **never
  stopped**, up to +115 mV and back down to −98 mV; no step reached a clean high.
  Hysteresis test cancelled.
- **20:35, static check:** +204 mV → HIGH (OUT+ 1.493 V, OUT− 1.116 V, 3.1 mV rms);
  −97 mV → LOW (1.108 / 1.503 V); +217 mV → HIGH; −278 mV → LOW; −98 mV → LOW.
- **20:45, leak test:** 3.7 mV across 1 kΩ from J1 to AGND (J1 off the CGR-201, IN− about
  1.23 V) → about 3.7 µA, normal.

## History of all saved oscillation waveforms

| When | IN+ − IN− | IN+ pk-pk | IN− pk-pk | IN+ and IN− move | OUT+ / OUT− pk-pk | Frequency |
|---|---|---|---|---|---|---|
| 19 Nov | +1 mV | 254 mV | 108 mV | weakly opposite (−0.26) | 948 / 948 mV | 93 MHz |
| 23 Nov 15:01 | −14 to +29 mV | 76–86 mV | 198–224 mV | together (+0.8) | 680–830 mV | 64 MHz |
| 23 Nov 15:05 | +4 to +29 mV | 90–98 mV | 194–216 mV | opposite (−0.9) | 750–1000 mV | 65 MHz |
| 23 Nov 20:11 | +22 mV | 136 mV | 192 mV | opposite (−0.9) | 1060–1140 mV | 69 MHz |
| 23 Nov 20:11, latched | −93 mV | 124 mV | 184 mV | opposite (−0.9) | 1010–1070 mV | 69 MHz |

## Things ruled out or measured

| Suspect | Result |
|---|---|
| Chip damage (two output/IN+ shorts, inputs at −0.15 to −0.3 V, continuity beeper) | none seen: levels, switching both ways, 12 mA, switching point, leakage all normal |
| Time powered / warm-up of the chip | each arrangement stable over tens of minutes |
| Switching bench supply (KUAIQU) | caused the ~75 kHz common-mode bursts; the linear E3630A removed them, not the transition width |
| Mac charger | about 5 mV wider with it in; not the main cause |
| Software or calibration change | none: every sweep used the same `cmp_sweep.py` (last changed 23 Nov 13:40, scope serial only), the same guard and calibration (19 Nov) |
| 1 nF in J4 | made the toggling harder; removed |
| IN− level | the oscillation follows IN+ ≈ IN− wherever it is (Emmy: 1.15–1.66 V) |
| CH1 probe position | unchanged between triad 1 and baseline A, so not the cause of that jump |

## Why careful rewiring changed the result so much

The comparator amplifies about 1260 times and decides within about 0.3 mV. Its output
edges (0.6 ns, 0.4–1 V) push a little current into every nearby conductor (C × dV/dt:
0.5 pF gives a few hundred µA during an edge), and the shared grounds through the probes,
cable shields and USB add more paths. Whether the circuit oscillates depends on whether
the amount that gets back to IN+ − IN− is above or below a critical level, like a
microphone near a speaker. This bench sits near that tipping point, so moving a lead by
a centimetre, or changing which output couples into which input, switches it between
quiet, narrow and wide or latched. Nothing has to be "wrong" with any single connection
for that to happen. Loose resistor tails resting on insulators are harmless; what
matters is how close input-side and output-side conductors are and how the loops are
shaped.

## Lessons for the bench

- Photograph the bench before every run (lead positions decide the result).
- Plug the CGR-201s in first and let them run 15–20 minutes before sweeping.
- Don't touch the USB hub while the CGR-201s are connected to the board.
- After connecting J1, reset IN+ once (0.90 → 1.10 V).
- No resistance or continuity checks on a powered board.
- Don't push component legs into SMA sockets.
- A grabber-lead setup can't reach a controlled state; further tests need parts soldered
  at the board (hysteresis resistor J7–J2, a small capacitor J4 to ground) or a PCB.

## Open questions for the professor

1. Is there a recommended way to terminate and probe the LVDS outputs on this eval board
   (J7 and J8 are 7 cm apart), e.g. split termination (2 × 50 Ω with a capacitor to
   ground) or a small adapter board?
2. Is soldering the hysteresis resistor between J7 and J2 (the "IN+FB" connector) the
   intended use of J2/J4?
3. Would USB isolators on the CGR-201s (breaking the USB ground loops) be worth it, or
   should the threshold come from a battery-powered reference instead?
4. ADCMP604 vs ADCMP605 (built-in hysteresis pin) vs ADCMP600 for the PCB.
5. What transition width / threshold margin should the design target (link budget says
   margin + transition ≤ about 26–36 mV of VENV rise)?

## Files

| What | Where (envelope_detector/) |
|---|---|
| Detailed time-stamped log | `COMPARATOR-BENCH-NOTES-SOFIA.md` |
| Plug-in procedure, limits | `COMPARATOR-PLUGIN-PROCEDURE.md` |
| Drawings | `comparator_test_wiring.svg`, `comparator_grounding.svg`, `comparator_hysteresis.svg`, `comparator_output_hookup.svg` |
| Photos (19 Nov) | `photos_cmp_sofia/` |
| Level control and guard | `cgr_guard.py`, `cgr_dc.py`, `data/cgr_dc_cal.json` |
| Sweep, checks, snapshots | `cmp_sweep.py`, `cmp_points.py`, `cmp_snapshot.py`, `scope_read.py`, `scope_preset.py` |
| Plots | `plot_cmp_sweep.py`, `plot_cmp_compare.py`, `plot_cmp_time.py`, `plot_cmp_repeats.py`, `plot_cmp_overlay.py`, `plot_cmp_states.py` → `data/cmp_*.png` |
| Data | `data/cmp_sweep_2026111*_*.csv`, `data/cmp_sweep_20261123_*.csv`, `data/cmp_sweep_*.log`, `data/cmp_waveforms_20261119.csv`, `data/cmp_snapshots_20261123*.csv`, `data/cmp_states_20261123_*.csv`, `data/cmp_points_20261123.csv` |
| Drawing generators | `make_grounding_svg.py`, `make_hysteresis_svg.py` |
