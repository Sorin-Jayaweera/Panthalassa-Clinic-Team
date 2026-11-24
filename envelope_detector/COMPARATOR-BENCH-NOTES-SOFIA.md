# Comparator bench notes (Sofia's session)

## 18 Nov 2026: which CGR-201 drives which input

Two CGR-201 units will be on the Mac. Tell them apart by USB serial number;
the serial port name contains it.

| Role | CGR-201 USB serial | Serial port on this Mac | Seen |
|---|---|---|---|
| **J1 IN+** (signal / DC source, through 100 Ω at J1) | **C2BJ0VL** | `/dev/cu.usbserial-C2BJ0VL` | 18 Nov, only CGR-201 connected at the time (USB location 0x14210000) |
| **J3 IN−** (threshold, through the threshold adapter) | **C2BKNPC** | `/dev/cu.usbserial-C2BKNPC` | 18 Nov, the second unit plugged in (USB location 0x14220000) |

Before connecting either output to the board: run `dc` at its starting level
on that unit, check with the DMM, then connect. The CGR-201 powers up with a
large negative output.

## Setup state, 18 Nov

- Comparator VCC 3.3 V from the E3630A; grounds tied.
- No RF; IN− not connected yet. Supply display 0.02 A (display steps in
  10 mA, so about 15–25 mA). Emmy also saw about 0.02 A on this supply.

## 19 Nov 2026: CGR-201 outputs calibrated per unit (DMM at the Output BNC, nothing connected)

| Unit | Role | Readings | mV/code | 0 V code | Check |
|---|---|---|---|---|---|
| C2BKNPC | J3 IN− | code 2156 → −0.146 V; 2882 → 1.296 V | 1.986 | 2229.5 | code 2834 → **1.205 V** (target 1.200) |
| C2BJ0VL | J1 IN+ | code 2156 → −0.010 V; 2754 → 1.107 V | 1.868 | 2161.4 | code 2750 → **1.102 V** (target 1.100) |

Stored in `data/cgr_dc_cal.json`; `cgr_dc.py` uses it by serial number.
Power-up output of both units measured at −0.2 to −0.3 V (after a re-plug, before any command).
Both units moved to a different USB hub at 11:30; a re-plug resets the output, so set DC again after any re-plug.

## 19 Nov 2026, 12:21–12:40: Test B trip-point sweeps

Setup: as `comparator_test_wiring.svg` (Test B): 3.30 V, 12 mA; IN− = C2BKNPC through
1 kΩ + 100 nF (board 1.235 V by DMM); IN+ = C2BJ0VL through 100 Ω at J1; 100 Ω across
J7/J8 with short legs; ×10 probes on IN+, IN−, OUT+, OUT−. Script `cmp_sweep.py`,
plot `plot_cmp_sweep.py` → `data/cmp_testB_20261119.png`.

- Sweep 1 (`cmp_sweep_20261119_122152.csv`): **invalid**. The scope kept returning the
  first acquisition ("RUN" does not restart this scope after "STOP"). Fixed: `TRMD AUTO`.
- Sweeps 2 and 3 (`..._122720.csv`, `..._123216.csv`), IN+ in 1-code (≈1.9 mV) steps:

| | Sweep 2 up | Sweep 2 down | Sweep 3 up | Sweep 3 down |
|---|---|---|---|---|
| Toggling from (IN+ − IN−, scope) | −42.8 mV | −43.5 mV | −41.7 mV | −40.0 mV |
| Toggling to | +52.6 mV | +50.2 mV | +51.5 mV | +51.8 mV |
| Frequency | 93–94 MHz | 93–94 MHz | 93–94 MHz | 93–94 MHz |

- Band ≈ 94 mV wide, centred near +5 mV; the same going up and down (no hysteresis);
  repeatable to about 2 mV. Similar width to Emmy's clip-lead runs (±45 mV), but at
  94 MHz instead of 27 MHz. **Mounting the 100 Ω with short legs changed the frequency,
  not the band.**
- Inside the band the output spends about 45 % low, 15 % in between, 40 % high whatever
  the input: a self-sustained oscillation, not noise.
- Mid-band waveforms (`data/cmp_waveforms_20261119.csv`, 20 ns/div): OUT+ and OUT− swing
  about 0.93 V pk-pk (more than the 0.39 V LVDS swing: ringing); **IN+ carries 226 mV
  pk-pk and IN− 100 mV pk-pk at the same frequency**, so the output is getting back into
  both inputs. 94 MHz is close to the scope's 100 MHz bandwidth, so amplitudes read low.
- The scope's IN+ − IN− values are approximate (few mV); DMM readings at the band edges
  still to take.
- Note: a /dev/cu.usbserial file's time stamp is its last write, not a re-plug. The
  "re-created at 11:34" reading earlier was a write; the units were not reset.

## 19 Nov 2026, 12:59: sweep 4, CH1 probe removed from IN+

`data/cmp_sweep_20261119_125910.csv`. IN+ − IN− taken from the code using the line fitted
to sweep 2 (CH1 attached): −98.6 mV at code 2750, 1.84 mV per code. Outside the fine
window the steps are 4 codes (about 7 mV), so the edges are known to about ±7 mV.

| | Sweeps 2–3 (CH1 on IN+) | Sweep 4 (CH1 removed) |
|---|---|---|
| Toggling band | −42 to +52 mV (≈ 94 mV) | about −73 to +85 mV (≈ 160 mV) |
| Frequency | 93–94 MHz | 67–68 MHz |
| Output variation, rms | 550–625 mV | 290–345 mV |

- **Removing the probe made the band wider, not narrower.** The ×10 probe's ~10–15 pF
  to ground on IN+ was damping the feedback into IN+, not causing it.
- 67–68 MHz matches the 69 MHz seen with both inputs floating.
- Points to a small capacitance on IN+ (to ground or to IN−) as a fix to test.
  Emmy's 0.1 µF on IN+ made things worse, but with a 1 kΩ source and a much larger value.

## 19 Nov 2026, 13:31: correction after the wiring photos (`comparator test wirings/`)

The photos show the setup differs from `comparator_test_wiring.svg`:
- **OUT± 100 Ω:** held between two red minigrabbers at the ends of BNC–grabber leads,
  in mid-air, with the CH3/CH4 probes clipped there. Not at J7/J8 with short legs. So
  sweeps 2–4 did **not** test a short termination; they used the same kind of
  clip-lead termination as Emmy. The earlier note "mounting the 100 Ω with short legs
  changed the frequency, not the band" is withdrawn.
- **Threshold adapter (1 kΩ + 100 nF):** in mid-air on grabbers, reaching J3 through an
  unshielded lead, so the 100 nF does not hold J3 itself at high frequency (fits the
  100 mV pk-pk seen on IN−).
- **Grounds:** all probe ground clips and black grabbers hooked onto one long black
  wire away from the board, so every probe has a long ground path.
- Also: J7 and J8 are about 7 cm apart on the board, so a 100 Ω "with short legs at
  J7/J8" is not possible on this board; the termination needs equal coax to a point
  where the two conductors are close together.

## 19 Nov 2026, 13:44–13:50: probe grounds moved to the board pins; sweep 5

Change: the four probe grounds moved from the long black ground wire onto the board's
ground test points. CH1 tip still off IN+. CH3/CH4 tips clip onto the 100 Ω's lead ends,
with the BNC grabbers between them and the resistor (so the scope sees the termination,
not the chip pins).

- With IN+ 100 mV below IN− (output should be steady low), the outputs now show short
  bursts: about 30 ns long, 3 % of the time, clusters about 55 ns apart, swinging past
  the screen (more than ±0.4 V). OUT+ and OUT− move **together** in the bursts
  (correlation 0.82), and OUT+ − OUT− stays low in 98 % of burst samples, so these are
  common-mode pickup in the probes' ground paths, not the comparator switching.
  IN− shows 120–230 mV pk-pk at the same times.
- Sweep 5 (`data/cmp_sweep_20261119_134645.csv`): the "TOGGLING" label is fooled by
  the bursts outside the band; read the high/low fractions instead. Real band (output
  high 1.8–80 % of the time): about −58 to +70 mV (≈ 128 mV), oscillation 43.5–44.6 MHz.
  Sweep 4 (grounds on the long wire): about −72 to +93 mV (≈ 165 mV), 67–68 MHz. Edge
  values ±7 mV (4-code steps outside the fine window).
- So moving the grounds narrowed the band by about a quarter and lowered the frequency,
  but added common-mode bursts. Wiring changes move both, which supports external
  coupling as the mechanism.
- **Correction (13:55):** the probe grounds were NOT moved; they are still on the long
  black ground wire. What moved onto the board's ground pins were four BNC-grabber
  ground clips (the shields of the CGR-201 and output BNC leads). The sweep 5 numbers
  stand; only the description of the change was wrong. Re-clipping CH3's ground alone
  visibly changes all channels.

## 19 Nov 2026, 14:05–14:10: all grounds on the board, long black GND wire removed

Photos `agnd_cgnd`, `board_updated`, `j3_new`. Probe grounds and BNC-grabber black
clips on the board's ground test points; one extra lead grounds the J3 100 nF; the J3
network (1 kΩ + 100 nF) still in mid-air on grabbers. CH1 tip still off IN+.

- 14:07:33: quiet. Outputs clean (±12–28 mV), IN− 116 mV pk-pk at most.
- 14:08:53 (after the J3 rearrangement in `j3_new`): IN− carries bursts at 26–27 MHz,
  up to about 0.5 V pk-pk (40 mV rms in a 2.8 µs window). The outputs move in
  **opposite** directions (correlation −0.99), so these are real output flips, while
  IN+ is 100 mV below IN−: high 2.4 % of the time in a 2.8 µs window, 0.01–0.08 % over
  70 µs–1.4 ms. Common-mode only 3–4 mV rms.
- Reading: the threshold network on IN− is now ringing at about 27 MHz (unshielded
  grabber leads + the separate ground lead for the capacitor form a resonant loop) and
  its swings exceed the 100 mV gap, so the comparator flips. 27 MHz is also what Emmy
  saw with clip leads.

## 23 Nov 2026, 13:40: instruments re-registered

| Device | Serial | Port / VISA resource | Role |
|---|---|---|---|
| CGR-201 | C2BJ0VL | `/dev/cu.usbserial-C2BJ0VL` (identifies as "Syscomp CircuitGear MKII V1.1 FPGA 0x02") | J1 IN+ |
| CGR-201 | C2BKNPC | not connected yet | J3 IN− |
| Siglent SDS1104X-E | **SDSMMFCQ5R6888** (a different scope from 19 Nov's SDSMMEBC3R1376) | `USB0::62700::60984::SDSMMFCQ5R6888::0::INSTR` | CH1 IN+, CH2 IN−, CH3 OUT+, CH4 OUT− |

`scope_read.py`, `scope_preset.py` and `cmp_sweep.py` now point at SDSMMFCQ5R6888.
C2BJ0VL needed a USB re-plug before its port opened (13:31 and 13:32 refused).
Its output has not been set since the re-plug (power-up level, about −0.2 to −0.3 V).
- 13:42: C2BKNPC connected and identifies (same firmware string). It is the J3 IN− unit
  from 19 Nov, so its calibration in `data/cgr_dc_cal.json` applies. Both units
  responding; neither output set yet.

## 23 Nov 2026, 13:55–14:02: both inputs connected, IN+ 100 mV below IN−

Scope SDSMMFCQ5R6888 with 19 Nov settings (CH4 offset had drifted to −1.24 V; reset).
CGR-201 outputs at codes 2834 (C2BKNPC, DMM about 1.20 V) and 2750 (C2BJ0VL, DMM
1.090–1.092 V: about 11 mV lower than on 19 Nov). Grounds: output group tied locally
(CH3/CH4 grounds on the J7/J8 black grabbers). CH1 tip on IN+.

- With inputs open: comparator oscillates at about 70 MHz (as on 19 Nov). Moving the
  board changes the amplitude by about 25 mV.
- Connected: IN+ 1.118 V, IN− 1.218 V (scope), difference −100 mV. OUT+ 1.106 V,
  OUT− 1.498 V, 2 mV rms over 0.7 µs.
- 14 ms capture (7 M samples): **output never wrongly high** (0 of 7 M samples).
  1054 short disturbances in 14 ms (about one every 13 µs, about 75 kHz), 0.23 % of
  samples, common-mode up to 222 mV pk-pk, also on IN+ (130 mV) and IN− (112 mV).
  The rate is close to the 69 kHz pickup Emmy attributed to a laptop charger.
- The 27 MHz "quarter-wave stub" idea for IN− is withdrawn: the J3 path is only about
  30 cm (a quarter-wave stub would be about 165 MHz).

## 23 Nov 2026, 14:10–14:23: supply swap, accidental output short

- Supply changed from the KUAIQU (switching) to the Agilent E3630A +6 V output (linear),
  3.30 V at TP11, no current limit; meter reads 0.02 A (10 mA steps). Board otherwise
  unchanged.
- An interrupted scope capture left the scope's USB stuck ("access denied"); fixed by
  re-plugging its USB into another hub port. Scope settings survived; CGR-201s were not
  reset (same USB positions, outputs still as set at 13:55).
- About 14:20: **OUT+ (J7 side of the 100 Ω) accidentally shorted to the J7 ground** in
  the output group. Seen as OUT+ ≈ 0 V, OUT− swinging −0.14 to +0.94 V, and 65 MHz
  oscillation on all channels with IN+ 100 mV below IN−. The chip felt warm to the touch
  (normal operation alone is about 50 mW → roughly 45 °C by the datasheet's 426 °C/W).
- 14:23, short removed: OUT+ 1.106 V, OUT− 1.502 V, swing 396 mV, common mode 1.304 V
  (19 Nov: 1.106 / 1.498 V). No disturbances at all in 0.28 ms. Output levels look
  undamaged; the sweep will check the trip point and band.
- With the linear supply, the ~75 kHz bursts seen at 13:59 on the KUAIQU (about 21
  expected in 0.28 ms) are absent: points to the KUAIQU as their source (one window;
  confirm with a longer capture).

## 23 Nov 2026, 14:25–14:30: sweep 6 (E3630A, local grounding, CH1 on IN+)

Pre-checks passed (both CGR-201s respond, guard limits, scope settings, outputs
1.109/1.504 V). `data/cmp_sweep_20261123_142549.csv`, plot
`data/cmp_testB_compare_20261123.png` (with 19 Nov sweep 2).

| | 19 Nov sweep 2 | 23 Nov sweep 6 |
|---|---|---|
| Output leaves LOW (IN+ − IN−, scope) | −43 mV | −8 mV |
| Average output crosses zero | about +5 mV | +11 mV (up and down within 0.4 mV) |
| Output fully HIGH | +53 mV | +32 mV |
| Transition width | ≈ 95 mV | ≈ 41 mV |
| Output variation inside it | 550–625 mV rms | 90–160 mV rms |
| Average output across it | almost flat (self-oscillation) | rises smoothly with input |

- No hysteresis: going up and down agree within about 1.5 mV at every point.
- Outside the transition the output is clean; the variation grows slowly (10–45 mV
  rms) from about 40 mV before it.
- The strongest spectral line inside the transition sits at 125 MHz = a quarter of the
  500 MS/s sample rate, which is also present when quiet: likely the scope's own
  interleaving spur, so the oscillation frequency is not resolved here (above the
  scope's 100 MHz bandwidth or below its noise).
- Several things changed between the runs (supply, grounding, scope unit, J1 CGR drift
  of about 10 mV, the accidental output short), so the improvement can't be pinned on
  one of them.
- The chip behaves normally after the output short: switching point, output levels and
  symmetry all reasonable.

## 23 Nov 2026, 14:45–15:23: J4 capacitor tried and removed; second short; three repeats

- 1 nF pushed into J4's centre socket (14:45–14:47): inside the transition the output
  toggled harder (195–240 mV rms first seating, 130–155 re-seated, vs 100–115 without),
  switching point unchanged. Contact unreliable and bad practice for an SMA jack
  (leads can spread the centre contact). **Removed.** Proper method: solder an
  0402/0603 cap at the connector or design it in near IN− on the PCB.
- About 15:00: **the J1 100 Ω touched ground** (accidental). 15:01 snapshots showed
  strong 65 MHz oscillation already at −14 mV. Leads re-fixed; nothing touching.
- 15:04 checks: CGR-201s respond (same USB positions), scope settings OK, outputs
  1.110 / 1.505 V. Snapshots 15:05: `data/cmp_snapshots_20261123_1505.csv`.
- Repeats (`cmp_sweep_20261123_150456.csv`, `..._150934.csv`, `..._151822.csv`; the
  third with the Mac charger plugged in; an earlier third attempt was stopped at step 12
  and not saved):

| Run | Low until | 50 % point | High from | Width | rms inside |
|---|---|---|---|---|---|
| Sweep 6, 14:25 (earlier wiring) | −8 mV | +11 mV | +32 mV | 40 mV | ≈ 108 mV |
| Repeat 1, 15:05 | −17 / −14 mV | +14 mV | +37 / +38 mV | 52–53 mV | ≈ 595 mV |
| Repeat 2, 15:09 | −14 / −14 mV | +14 mV | +36 / +37 mV | 50–51 mV | ≈ 595 mV |
| Repeat 3, 15:18, charger in | −19 / −16 mV | +12 mV | +40 / +40 mV | 56–58 mV | ≈ 560 mV |

  (up / down where they differ.) Repeats 1–2 agree to about 3 mV; the charger widened the
  transition by about 5 mV. The 50 % point is stable at +12 to +14 mV in all runs.
- Plot: `data/cmp_testB_repeats_20261123.png` (`plot_cmp_repeats.py`).
- Conclusion: today's arrangement is repeatable, but sweep 6's gentler behaviour (40 mV,
  ~100 mV rms) came from an earlier lead arrangement that was not recorded. The physical
  arrangement of the leads changes the result more than repeat-to-repeat scatter does.

## 23 Nov 2026, 15:31: baseline A after the wiring check (charger in)

`data/cmp_sweep_20261123_153128.csv`. After re-checking every connection against
`comparator_grounding.svg` (CH1 tip moved onto the J1 red grabber's metal):
low until −35 / −81 mV, 50 % at +27 mV, high from +108 / +53 mV (up / down):
**transition 134–143 mV, ~680 mV rms inside**, the widest today; 50 % point moved from
+12–14 to +27 mV. Clean at rest (2–3 mV rms). Another arrangement change, not time
(the 15:05–15:18 repeats were stable). Kept as baseline A for the hysteresis
comparison (A, hysteresis, A again).

Hysteresis wiring: `comparator_hysteresis.svg`. Rs = 100 Ω + CGR-201's 50 Ω = 150 Ω, so
Rf 5.6 kΩ ≈ 10 mV, 4.7 kΩ ≈ 12 mV, 3.9 kΩ ≈ 14 mV, 2 kΩ ≈ 27 mV (earlier figures ignored
the 50 Ω and were too low).
- 15:50 (during the triad-2 repeats): AirDrop from the Mac to a phone for 3–4 s. Check the steps around this time for anomalies.

## 23 Nov 2026, 15:46–16:00: triad 2 (wiring re-checked, loose leads on plastic, charger in)

`cmp_sweep_20261123_154607.csv`, `..._155121.csv`, `..._155549.csv`;
overlay of all today's sweeps: `data/cmp_testB_overlay_20261123.png`.

| Run | Starts toggling (up / down) | Stops toggling (up / down) | 50 % point | rms inside |
|---|---|---|---|---|
| r1 15:46 | −44 / −85 mV | +114 / +75 mV | +33 mV | 686 mV |
| r2 15:51 | −47 / −87 mV | +111 / +74 mV | +33 mV | 686 mV |
| r3 15:55 | −47 / −87 mV | +111 / +71 mV | +32 mV | 686 mV |

- The three agree within about 3 mV at every edge: the arrangement is stable.
- The toggling zone is about 158 mV wide (−45 to +112 going up) and **latches**: going
  down it keeps oscillating until −85 mV, 40 mV past where it started going up; at the
  top it starts again at +72 going down vs stopping at +112 going up. Once oscillating,
  it sustains itself (as Emmy saw on 9 Nov).
- The 50 % point moved +13 → +27 → +33 mV across the three arrangements of the day. In a
  self-oscillating zone the 50 % point reflects the oscillation's duty cycle, not only
  the comparator's true threshold.
- AirDrop at about 15:50 (triad 2 r1, down-going steps): no anomaly in those steps.
- This is the widest state of the day, but repeatable: used as the baseline for the
  hysteresis test.

## 23 Nov 2026, about 16:05: paused until the evening

Board to be powered down: J1 then J3 disconnected, then the E3630A output off. On return:
photograph the bench, power up (3.30 V at TP11, ~0.02 A), re-set both CGR-201s with
`cgr_dc.py` and check them with the DMM, connect J3 then J1, re-check the scope
settings, run a baseline triad, then the hysteresis resistor (2–2.2 kΩ first,
4.7 kΩ second), then a baseline after removing it.
- 17:2x: restart lesson: plug in the CGR-201 USB first and let them run 15–20 min before sweeping. After a re-plug at 17:08 they drifted up 7–8 mV/min at first (IN− 1.177 → 1.210 V by 17:17). DMM at the board then: J3 1.215 V, J1 1.105 V.

## 23 Nov 2026, 17:29–17:42: evening triad (after re-plug, warm-up and a wiring change)

`cmp_sweep_20261123_172916.csv`, `..._173336.csv`, `..._173752.csv` (charger in).

| Run | Leaves low (up / down) | 50 % point | Fully high (up / down) | Width | rms inside |
|---|---|---|---|---|---|
| 17:29 | −61 / −70 mV | +12 / +10 mV | +90 / +73 mV | 143–150 mV | 667 mV |
| 17:33 | −55 / −70 mV | +12 / +12 mV | +90 / +75 mV | 145 mV | 666 mV |
| 17:37 | −55 / −66 mV | +12 / +12 mV | +97 / +73 mV | 138–151 mV | 668 mV |

- Repeatable to about 6 mV at the edges, 2 mV at the 50 % point; inputs steady within a sweep.
- Width about 145 mV, like triad 2 (158 mV); 50 % point back at +12 mV like triad 1.
- Latching smaller than triad 2: about 10–15 mV at the bottom, 15–24 mV at the top.
- Overlay: `data/cmp_testB_overlay_20261123.png`.

## 23 Nov 2026, about 19:35: continuity beeper on the powered board → latched oscillation

DMM continuity mode between J4 shell (ground) and J3 centre (IN−) with the board
powered: it beeped (the 100 nF looks like a short at first) and kicked the comparator
into oscillation. At 19:36, with IN+ still 98 mV below IN−, all four channels showed
67 MHz: outputs about 1 V pk-pk, IN− 430 mV pk-pk, IN+ 180 mV pk-pk. The oscillation
had **latched**: it sustained itself 98 mV away from the threshold.
Recovered by moving IN+ to 0.90 V (well below) and back to 1.10 V: clean low again
(OUT+ 1.107 V, OUT− 1.504 V, 2–3 mV rms). No damage seen. Lesson: resistance and
continuity checks only with the board unpowered.
- 19:38–19:41: the oscillation restarts on its own. After a reset (IN+ 0.90 → 1.10 V) it
  was quiet for about 12 s (out rms 3.4 mV, IN− 18 mV pk-pk), then at 19:40:02 jumped to
  67 MHz (out rms 676 mV, IN− about 445 mV pk-pk) with IN+ − IN− still −99 mV, and stayed
  there for the rest of the 90 s watch. New since the continuity check; DMM leads were
  not attached. IN− carries the largest swing: suspect the IN− network (1 kΩ, 100 nF,
  their grabbers and ground) or J4.
- 20:02: C2BKNPC reset by a hub disturbance (scope re-plugged on the same hub); re-set
  20:03 (DMM 1.220 V; C2BJ0VL 1.112 V). 20:06–20:08: after connecting J3 then J1 the
  comparator was oscillating at once (out rms 658 mV, IN− ~200 mV pk-pk) at −95 mV, the
  connection itself kicked it. Reset (IN+ 0.90 → 1.10 V) at 20:08: quiet for 70 s of
  watching (out rms 3.3–3.6 mV, IN− 20–28 mV pk-pk). Procedure from now on: after
  connecting J1, always reset IN+ (0.90 → 1.10 V) once before measuring.

## 23 Nov 2026, 20:11: all four channels in three states (`data/cmp_states_20261123_2013.png`)

Outputs at 200 mV/div (unclipped), 50 ns/div. States: (1) freshly reset at −95 mV,
(2) +10 mV inside the transition, (3) back at −95 mV, still oscillating (latched).
- Latched state: IN+ swings 1.08–1.20 V and IN− 1.14–1.31 V at about 68 MHz, **in
  opposite phase**. Although their averages are 95 mV apart, IN+ rises above IN− for
  part of every cycle, so the comparator keeps flipping: the oscillation feeds itself.
- The outputs reach about 0.75–1.85 V (normal levels 1.10–1.50 V).
- Freshly reset: a single damped burst on IN+ (about ±70 mV) and IN− at about 170–260 ns,
  i.e. pickup events still happen and can restart the latch.
- Reading: the outputs couple into IN+ and IN− with opposite signs (differential
  feedback), most likely through lead proximity between the input and output groups.

## 23 Nov 2026, 20:15–20:17: one sweep on battery (charger unplugged), stopped early

`data/cmp_sweep_battery_20261123.log` (partial, stopped by the user at step ~40; no CSV).
Mac on battery. Started quiet (3.4 mV rms at −97 mV); oscillation began going up at
**−55 mV** (69 MHz, ~680 mV rms), the same as the evening triad (−55 to −61 mV).
So the Mac charger is not what widens the transition. Reset afterwards (IN+ 0.90 → 1.10 V).

## 23 Nov 2026, 20:26–20:31: final baseline sweep (battery), worst of the day

`data/cmp_sweep_20261123_202640.csv`. Started quiet at −97 mV; oscillation started going up
at −48 mV and **never stopped**: through +115 mV and all the way back down to −98 mV the
output toggled (~620–680 mV rms, 69 MHz). Not one step reached a clean HIGH. Decision:
no hysteresis test on this arrangement; the grabber setup is no longer controllable.
Reset afterwards (IN+ 0.90 → 1.10 V).
- 20:35 static check after the final sweep (each level set, then one 14 µs capture):
  IN+ − IN− = +204 mV → HIGH (OUT+ 1.493, OUT− 1.116 V, 3.1 mV rms); −97 mV → LOW
  (1.108 / 1.503 V); +217 mV → HIGH; −278 mV → LOW; −98 mV → LOW. Switches correctly
  both ways with clean, symmetric levels (Emmy, 2 Nov: 1.105 / 1.483 V). No sign of
  damage in the DC function; input leakage not re-checked.
- ~20:45 Emmy's leak test repeated: board powered, J1 disconnected from the CGR-201, 1 kΩ
  from J1 (via the J1 cable's centre) to AGND, IN− at about 1.23 V. **3.7 mV across the
  1 kΩ → about 3.7 µA** out of IN+. Datasheet: bias ±5 µA, plus up to about 1.2 V / 200 kΩ
  = 6 µA through the differential input resistance (typical 750 kΩ → 1.6 µA), so
  about 2–4 µA is what a healthy input gives here. Emmy measured 40 µA in the same test
  on 2 Nov. **No sign of a faulty IN+ now**; today's incidents did not add leakage.
