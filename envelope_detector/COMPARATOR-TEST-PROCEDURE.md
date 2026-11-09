# Comparator tests: ADCMP604 (EVAL-ADCMP604BKSZ)

Started 2026-11-01. Tests 1–4 are the four tests on the website's Comparator tab
(`site/content_env.py`) and in Test B/C of `LIMITS-AND-TEST-PLAN.md`, with
additions listed at the end ("Changes from the website plan"). Fill in the
blanks here or in `COMPARATOR-TEST-RESULTS.md`.

Scripts:
- `cmp_cgr.py`: CGR-201 as a calibrated DC source, slow triangle, and the
  automatic trip-point sweep (Test 2).
- `cmp_scope.py`: edge counting on the Siglent scope (Tests 3 and 4).

Both reuse the team drivers in `../vco_rise_time/` (`cgr201.py`, `sds.py`).
Before running either script, close the CircuitGear software and any GNU Radio
flowgraph that uses the CGR-201. Only one program can hold its port.

Sources:
- **[DS]** ADCMP604/605 datasheet Rev. C
- **[CGR]** Syscomp CGR-201 datasheet
- **[ED]** `ED-TEST-RESULTS.md`
- **[LIM]** `LIMITS-AND-TEST-PLAN.md`
- **[ERR]** the website's error log

Numbers marked **(calc)** are my own arithmetic from those sources.
**(verify)** = not in any document; check it on the bench.

## What these tests give the project

1. **Proof that the board works:** supply current and the LVDS output levels.
2. **How accurately the threshold is obeyed (Test 2).** The FPGA/DAC will set
   thresholds 20–200 mV above the detector's no-RF level (about 1.14 V,
   [ED]), so an error of a few mV matters.
3. **How wide the "chatter band" is (Test 3).** This sets the smallest safe
   margin above the noise, and how long the FPGA must ignore repeat edges.
4. **Whether the detector + comparator turn each RF pulse into exactly one
   digital pulse, and at what RF level (Test 4).** This is the receiver's
   working sensitivity.

## You need

- EVAL-ADCMP604BKSZ (chip already soldered on, [LIM])
- Bench supply for 3.3 V, plus the 5 V supply for the ADL5511 in Test 4
- **100 Ω resistor** (1 %, leaded) for OUT+/OUT−
- **10 kΩ potentiometer** (multi-turn if there is one), for the IN− threshold
- 0.1 µF capacitor (optional, wiper to ground; see Step 0)
- **1 kΩ resistor** in series with the CGR-201 output
- CGR-201 + USB, DMM, Siglent SDS1104X-E with **two 10× probes**
- SMA tees, SMA→BNC cables/adapters, BNC→clip leads, a clip lead to ground IN+
- Test 4 only: ADL5511-EVALZ, Pluto + USB, short SMA cable, `ed_test_pluto_tx_soapy.grc`
- Wrist strap

## Safety limits

| Item | Limit | Why / source |
|---|---|---|
| Comparator supply | **3.30 V.** Never above 5.0 V | 2.5–5.0 V operating (VCCI/VCCO share pin 5), 6.0 V abs max [DS Table 1 p. 4, Table 3 p. 6] |
| Supply current | about 15 mA; switch off above 25 mA | 15 typ, 21 max [DS p. 4]. Use a 40 mA limit if the supply has one. The E3630A may not have an adjustable limit **(verify)**: watch its display instead. |
| IN+ / IN− | **0 to 3.0 V** in these tests | Abs max −0.5 to VCC + 0.5 = 3.8 V, ±50 mA [DS Table 3]. Working range −0.2 to 3.5 V [DS Table 1]. `cmp_cgr.py` refuses anything outside 0–3.0 V. |
| CGR-201 output | Set to DC **before** connecting; always through 1 kΩ | It swings ±3 V [CGR], and −3 V is far below −0.5 V. The 1 kΩ keeps any fault current under 4 mA (calc). |
| CGR-201 digital outputs | Never to the board | 5 V HCMOS [CGR] > 3.8 V |
| OUT+/OUT− | 100 Ω across them; 1 MΩ scope inputs only | Output specs are at R_LOAD = 100 Ω [DS Table 1] |
| VENV (Test 4) | ≥ 500 Ω load, never 50 Ω; 10× probe or 1 MΩ input | Idle at 1.1 V, drives 15 mA max [LIM] |
| ED supply (Test 4) | 5.00 V, never above 5.5 V | [LIM] |
| Order | Supplies on → then signals. Signals off → then supplies. | An input above an unpowered VCC drives current into the protection diodes [DS Table 3; LIM flag 9] |

## Board connections

| SMA / jack | Pin [DS Table 5] | Connect to |
|---|---|---|
| J1 | VP (IN+) | Signal: CGR-201 via 1 kΩ (Tests 2–3), or VENV (Test 4) |
| J3 | VN (IN−) | Threshold: potentiometer wiper |
| J7 | Q (OUT+) | 100 Ω to J8; scope / CGR Input B |
| J8 | Q̄ (OUT−) | 100 Ω to J7 |
| J2, J4 | IN+FB, IN−FB | **Leave open.** Purpose not traced yet [LIM] |
| VCC | VCC | +3.3 V |
| AGND, CGND/VEE | GND / VEE | Supply negative; VEE tied to AGND [LIM] |

Q (OUT+) is high when IN+ > IN− [DS Table 5].

---

## Step 0: Prepare (unpowered)

1. Put on the wrist strap.
2. **Fit the 100 Ω across OUT+/OUT−.** The board has none [LIM].
   - **Best:** solder a leaded 100 Ω between the centre pins of J7 and J8
     on the back of the board, leads as short as possible. It's easy to
     remove later.
   - **Acceptable for Tests 1–3 only:** SMA tees on J7 and J8, with the
     resistor between them on clip leads.
   - Check with the DMM, unpowered: J7 to J8 should read about 100 Ω.
3. **Wire the threshold pot** so it can never exceed VCC:
   - one end → the board's VCC jack;
   - other end → AGND;
   - wiper → J3 (SMA tee or clip on the centre pin);
   - optional: 0.1 µF from the wiper to AGND. This is my suggestion, not
     from a document: the wiper is a high-impedance node, and the capacitor
     keeps pickup off IN−.
   - Set the pot near one-third of its travel, for roughly 1.1–1.2 V.
4. Set the bench supply to **3.30 V**, output OFF (40 mA limit if it has
   one). Connect + → VCC and − → AGND. Tie CGND/VEE to AGND.

## Step 0b: Calibrate the CGR-201 output (once per session, BOARD DISCONNECTED)

**Why:** `cmp_cgr.py` sets voltages by code. This step measures how codes map
to volts (about 1.875 mV per code; `run_log_step_response.txt`, 10 Oct), so
every later level is known and kept inside 0–3.0 V.

1. CGR-201 **Output** → BNC tee → **Input A** and the **DMM** (DC V).
   Nothing else on the Output.
2. Run `python cmp_cgr.py calibrate`. Type `yes`, then the DMM reading at
   each of the two points, and at the 1.200 V check.
3. ✅ **Pass:** the check point reads 1.200 V ± 5 mV on the DMM. The script
   warns if it doesn't.

| Point | Code | Input A (V) | DMM (V) |
|---|---|---|---|
| ~0.4 V | | | |
| ~1.9 V | | | |
| 1.200 V check | | | |
| Result | ___ mV/code, 0 V at code ___ | | |

---

## Test 1: Supply current and output levels

**Why:** proves the chip is alive and the 100 Ω is right before any other
reading is trusted. Every later test reads OUT+.

**Wiring:** IN+ (J1) → clip lead to AGND (forces OUT+ low), IN− (J3) =
pot. No CGR-201 needed.

1. Turn the supply on. Read the current: **expect about 15.3 mA** (15 mA
   chip [DS p. 4] + 0.33 mA through the 10 kΩ pot (calc)). Above 25 mA or
   near 0 → off, recheck the wiring.
2. DMM (black on AGND): VCC at the jack, then IN− at J3. Turn the pot to
   **1.20 V**.
3. **State LOW** (IN+ grounded, so IN+ < IN−): measure OUT+ (J7→GND),
   OUT− (J8→GND), and J7→J8 (red J7, black J8).
4. Move the IN+ clip from AGND to the **VCC jack**. Now IN+ = 3.3 V > IN−.
   3.3 V is inside the 3.5 V working range. It's above the ~2.7 V VENV
   expected at +14 dBm (website Comparator tab), though not the 3.4 V VENV
   at the ED's +17 dBm maximum [LIM H2].
5. **State HIGH:** same three readings.
6. Move the IN+ clip back to AGND (low again) before Test 2.

| Measure | Expect [DS Fig. 8, 14 at 3.3 V; graph read ±0.01 V] | LOW | HIGH |
|---|---|---|---|
| Supply current | ~15.3 mA, < 21 mA | | |
| VCC at jack | 3.30 V | | |
| IN− (J3) | 1.20 V | | |
| OUT+ (J7) | LOW ≈ 1.00 V, HIGH ≈ 1.39 V | | |
| OUT− (J8) | LOW ≈ 1.39 V, HIGH ≈ 1.00 V | | |
| J7 − J8 | LOW ≈ −0.39 V, HIGH ≈ +0.39 V | | |
| Common mode (OUT+ + OUT−)/2 | ≈ 1.20 V | | |

✅ **Pass** [DS Table 1 p. 3, "DC Output Characteristics", R_LOAD = 100 Ω]:
- current < 21 mA;
- |J7 − J8| between **245 and 445 mV** in both states;
- the two |J7 − J8| values differ by ≤ **50 mV** (ΔV_OD);
- common mode **1.125–1.375 V** in both states.

The common mode changing by ≤ 50 mV between states is my reading of the
"Peak-to-Peak Common-Mode Output, 50 mV max" row: a soft check.

If |J7 − J8| is much larger than 0.45 V, the 100 Ω is missing or open.

---

## Test 2: Trip point (offset) at four thresholds

**Why:** the design assumes "threshold = X volts" means the output flips at X
volts. The datasheet allows **±5 mV** offset [DS Table 1]. The offset can
also shift with input level: CMRR is ≥ 50 dB, so up to 3.2 mV per volt of
common mode (calc: 10^(−50/20)). So test at the levels the JACON will
actually use.

**Why the DMM and not the scope:** the CGR-201 scope reads **5.05 mV per
count** (header of `data/ed_sweep_1.10GHz_20261026_220822.csv`), the size of
the whole spec. Also, the 1 kΩ and the input's ≥ 100 kΩ common-mode
resistance [DS Table 1] drop up to about 20 mV between the CGR setting and
the pin (calc: 1.65 V / (100 kΩ ∥ 1 MΩ) × 1.05 kΩ ≈ 19 mV). A DMM between J1 and J3 reads IN+ − IN− directly at the
pins, to 0.1 mV.

**Wiring**

```
CGR Output ──(set to DC first)── 1 kΩ ──┬── J1 (IN+)
CGR Input A ────────────────────────────┘   (monitors IN+)
pot wiper ───────────────────────────────── J3 (IN−)
J7 (OUT+) ── SMA→BNC ── CGR Input B         (1 MΩ; high/low readout)
DMM: red on J1, black on J3                  (reads IN+ − IN−)
```

1. Board powered (Test 1 state). Before connecting the CGR to J1, run
   `python cmp_cgr.py dc 0.60`. Then connect it (through the 1 kΩ) and
   remove the IN+ ground clip.
2. For each level below:
   - DMM black on AGND, red on J3: turn the pot to the level and **write
     down the exact reading**;
   - move the DMM to **red J1 / black J3**;
   - run `python cmp_cgr.py sweep --vn <that reading>`.
3. The script:
   - checks OUT+ low/high (it stops with a hint if Input B is on J8 or
     nothing switches);
   - scans IN+ up in ~7.5 mV steps, then in single codes (~1.9 mV) up and
     down through the trip;
   - parks at the 50 % point twice and asks for the DMM reading (mV).
   - About 2 minutes per level.
4. It prints the offset and appends a row to `data/cmp_trip_summary.csv`.
   The per-step data goes to `data/cmp_trip_vn<level>_<time>.csv`.

| IN− target | Why this level | IN− at J3 (DMM) | Offset up (mV) | Offset down (mV) | Hysteresis (mV) | 10–90 % width (mV) | Max "in-between" | Pass? |
|---|---|---|---|---|---|---|---|---|
| 1.16 V | ED no-RF ~1.14 V + 20 mV, the first threshold [ED] | | | | | | | |
| 1.24 V | +100 mV (trips ≈ −10.4 dBm [ED]) | | | | | | | |
| 1.34 V | +200 mV (≈ −4.5 dBm [ED]) | | | | | | | |
| 1.65 V | VCC/2: the input stage hands over here, so the offset may step [DS p. 12, "Crossover Bias Points"] | | | | | | | |

**Expect**
- Offset within ±5 mV.
- Hysteresis about 0 (< 0.1 mV [DS Table 1]); up to ±1 mV is just the 1.9 mV
  code step.
- 10–90 % width of a few mV. It's mostly the CGR's ~2 mV rms DC noise [ERR],
  smeared by the comparator's own noise.
- "In-between" is the share of Input B samples between the two levels. A
  large value near the trip means the output oscillates faster than the
  CGR can follow (5 MHz [CGR]). That's the oscillation the datasheet
  describes for slow inputs [DS p. 12]. Note it; it isn't a failure.

✅ **Pass:** |offset| ≤ 5 mV at all four levels [DS Table 1].

When done: `python cmp_cgr.py off`.

---

## Test 3: Chatter with a slow input

**Why:** the ADCMP604 has no hysteresis [DS Table 1]. When a slow or noisy
input crawls through the threshold, the output can flip many times, and the
FPGA would count each flip as a radar ping. This test measures how wide the
noisy band is, in mV, and how long a burst of flips lasts. The CGR-201 is too
slow to see individual flips, so this uses the Siglent.

**Wiring:** as Test 2, plus:
- scope **CH1** = 10× probe on J1 (IN+);
- scope **CH2** = 10× probe on J7 (OUT+), with a short ground lead.

The DMM can stay or go. Set IN− ≈ 1.24 V with the pot and note the DMM
reading.

**Scope settings** (set by hand):

| Setting | Value |
|---|---|
| CH1 | DC, probe 10X, 20 mV/div, offset = −(IN− reading) |
| CH2 | DC, probe 10X, 100 mV/div, offset −1.20 V |
| Bandwidth limit | Off on both |
| Trigger | CH2, rising edge, **1.20 V**, mode Normal. Move the trigger point to about 2 div from the left |
| Memory depth | The largest it allows with two channels |

For each row:
1. `python cmp_cgr.py triangle --center <IN− reading> --pkpk 0.10 --freq <f>`
2. Set the timebase.
3. `python cmp_scope.py --label tri_<f>Hz --shots 10`

| Triangle | Input slope (calc: 2 × pk-pk × f) | Timebase | Bursts | Max rising edges per burst | Longest burst (µs) | Noise band = burst × slope (mV) |
|---|---|---|---|---|---|---|
| 1 Hz | 0.2 V/s | 5 ms/div | | | | |
| 10 Hz | 2 V/s | 500 µs/div | | | | |
| 100 Hz | 20 V/s | 50 µs/div | | | | |

**Expect:** nobody has measured this yet.
- The datasheet says that with a good layout a slow input gives "broadband
  noise" at the crossing rather than violent chatter, and that extra load
  capacitance (probes count) can turn it into oscillation [DS p. 12].
- **Rough guess (calc):** a noise band of about ±2 × 2 mV rms ≈ 8 mV. That
  gives bursts of about 40 ms, 4 ms and 0.4 ms at 1, 10 and 100 Hz.
- **Sanity check:** the "noise band" column should come out roughly the same
  at all three speeds. If it does, the band is a property of the input
  noise, which is the number the threshold margin has to beat.
- Fast chatter above the scope's sample rate or 100 MHz bandwidth gets
  undercounted, but the burst length stays right.

✅ **Recorded** (no pass/fail): the noise band in mV and the longest burst.

When done: `python cmp_cgr.py off`.

---

## Test 4: Envelope detector → comparator with Pluto pulses

**Why:** this is the real job. For each RF pulse at the detector there should
be **exactly one** OUT+ pulse, none with RF off, and the RF level where
pulses start being caught is the receiver's sensitivity. [ED] predicts a
+20 mV threshold trips at about **−21.5 dBm**.

**Wiring:** as `bench_wiring.svg`, with two changes:
- the threshold comes from the **pot** (cannot exceed VCC; none of the
  CGR's ~2 mV DC ripple [ERR]);
- OUT+ goes to the **Siglent** instead of CGR Input B.

```
Pluto TX ──SMA── ED RFIN
ED VENV ── SMA tee ──┬── J1 (IN+)          NO 50 Ω anywhere on this net
                     └── CH1 (10× probe, or SMA→BNC into 1 MΩ)
pot wiper ────────────── J3 (IN−)
J7 (OUT+) ── CH2 (10× probe)
DMM: red on J3, black on J1                 (reads threshold − VENV = the margin)
```

1. ED: 5.00 V on. SW1 enabled. **Let it run 10 minutes** (VENV drifts about
   10 mV while warming [ED]). Comparator 3.3 V on.
2. Pluto straight into the computer's USB (it dropped out on a hub [ED]).
   Run `ed_test_pluto_tx_soapy.grc` with **TX level −89**, Pulsed off. The
   Pluto is "running but silent", so its leakage is included in the
   baseline [LIM flag 11].
3. DMM black on AGND, red on J1: **VENV baseline** = ____ V.
4. DMM red J3, black J1: turn the pot until it reads **+20.0 mV** (the
   margin). Record it.
5. **False-ping check (RF off):** scope trigger CH2 rising 1.20 V, Normal.
   Run `python cmp_scope.py --label rf_off --shots 3 --timeout 60 --ref-ch 0`.
   ✅ Expect "no trigger" all three times, i.e. no false pings in 3 minutes.
6. **Pulsed:** tick Pulsed (`pulse_us` = 100 → 100 µs on, 100 µs off).
   Scope:
   - CH1 DC, 50 mV/div, offset −1.20 V;
   - CH2 as Test 3;
   - trigger **CH1** rising at **baseline + 10 mV**;
   - timebase **2 ms/div** (about 140 pulses per shot).
7. For each TX level: set it, then
   `python cmp_scope.py --label ed_tx<level>_100us --shots 10 --match --period-us 200`.
8. Repeat the −10 and −20 rows with `pulse_us` = 10 (edit in GRC, re-run),
   timebase 200 µs/div, `--period-us 20`.

| TX level | ≈ dBm at ED [ED: Pin ≈ TX level] | VENV rise [ED] | Expect | Ref pulses | Hit | Missed | Extra | VENV pulse height on CH1 |
|---|---|---|---|---|---|---|---|---|
| −10 dB | −10 | 105 mV | every pulse, no extras | | | | | |
| −15 dB | −15 | 54 mV | every pulse, no extras | | | | | |
| −20 dB | −20 | 26 mV | mostly caught; only 6 mV above the margin, so some chatter possible | | | | | |
| −22 dB | −22 | ~18 mV (interpolated, calc) | mostly missed | | | | | |
| −25 dB | −25 | 11 mV | none | | | | | |
| −10 dB, 10 µs | −10 | 105 mV | every pulse | | | | | |
| −20 dB, 10 µs | −20 | 26 mV | as at 100 µs | | | | | |

How to read the counts:
- **Missed** = an RF pulse with no OUT+ edge within ±2 µs of its start.
- **Extra** = additional OUT+ rising edges, either at the pulse start
  (chatter as VENV rises) or anywhere else (noise on the pulse top, false
  pings).
- If CH1 can't see the pulses (−25 dB), the script falls back to counting
  against the period.

✅ **Pass:**
- RF off: no triggers.
- At −10 and −15 dB (≥ 6 dB above the expected trip), for both pulse
  lengths: **0 missed and 0 extra** over all 10 shots.
- Near the trip (−20 to −25 dB): recorded. These rows set the threshold
  margin and the FPGA's repeat-edge filter.

Also note: the 100 µs and 10 µs VENV pulse heights should match the CW
"VENV rise" column within about 5 %. That completes Test A Step 6 of the ED
procedure at the same time.

---

## Later: Tests 5 and 6 (need parts or code that aren't ready)

- **5. Radar-length pulses and delay.**
  - Real radar pulses are 50 ns–1.2 µs (drawing). The current GRC flowgraph
    runs at 2 MS/s, so it can't make them.
  - Possible sources: an Icepi Zero pin → 470 Ω / 47 Ω divider into IN+
    (0.3 V pulses, ~43 Ω source, calc) with IN− ≈ 0.15 V; or a Pluto cyclic
    buffer at a high sample rate (untested).
  - Expected delay 1.6 ns at 50 mV overdrive, 3.0 ns at 10 mV [DS p. 4].
    The 100 MHz scope can't resolve that, so pass/fail is "under 10 ns and
    the output width within ±5 ns of the input" (my criterion).
- **6. Into the FPGA.**
  - The Icepi Zero pins are 3.3 V CMOS. LVDS needs an SN65LVDT2-type
    receiver (100 Ω built in) or an ECP5 differential input pair, if one
    reaches the header **(verify)** [LIM H5].
  - Then compare the FPGA's count against the Test 4 counts.

## Power down

1. `python cmp_cgr.py off`; stop the GRC flowgraph.
2. Disconnect the CGR-201 / VENV from J1.
3. Comparator supply off, then the ED supply.
4. Disconnect the rest.

---

## Changes from the website plan (for the team)

| Website / LIMITS plan | Here | Why |
|---|---|---|
| Test 1: supply current only | Also OUT+/OUT− levels in both states, and IN+ at 3.3 V | Checks the 100 Ω and gives the readout levels every later test relies on [DS Table 1] |
| Test 2: triangle on IN+, trip read on the CGR-201 scope, IN− = 1.20 V | Stepped DC with a DMM across IN+/IN− at the pins, at four levels | CGR scope = 5.05 mV/count, as big as the ±5 mV spec. The 1 kΩ + input loading move IN+ by up to ~20 mV (calc). Offset can change with level (CMRR) and at VCC/2 [DS p. 12] |
| Test 3: count extra edges on the CGR-201 | Siglent, three triangle speeds, burst length → noise band | CGR bandwidth 5 MHz [CGR] can't show the edges |
| Test 4: threshold from CGR via 1 kΩ, count on CGR Input B | Pot threshold, DMM reads the margin directly, Siglent counts with pulse matching | No CGR ripple on IN−; the margin is measured, not computed; misses and extras are counted separately |
| — | RF-off false-ping check, S-curve over TX level, 10 µs pulses | Sensitivity and false-alarm numbers for the FPGA design |
