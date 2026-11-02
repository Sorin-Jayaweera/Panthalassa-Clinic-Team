# Test A: envelope detector (ADL5511) on its own

Wiring: `ed_test_wiring.svg`. Limits and background: `LIMITS-AND-TEST-PLAN.md`.
Results so far: `ED-TEST-RESULTS.md`. The full chain (`bench_wiring.svg`) is
saved for later.

Goal:
1. Confirm the ADL5511 board works. ✅ 26 Oct
2. Measure its transfer curve at the IF (1.0–1.2 GHz). ✅ 1.1 GHz on 26 Oct;
   1.0 and 1.2 GHz today (Step 5)
3. Use its VRMS output to calibrate the Pluto's real output power. ✅ 26 Oct
4. Check its pulse response. Today (Step 6)

## How the readings are taken (from 1 Nov)

| Signal | Read on | When |
|---|---|---|
| **VENV** | CGR-201 **Input A** | every step, by the script |
| **VRMS** | CGR-201 **Input B** | every step, by the script (no typing) |
| **EREF** | DMM, **typed into the terminal** when the script asks | before the RF and after it, every run |
| Supply current | supply display | at power-up |

Everything runs from one script, **`ed_sweep.py`**. The GRC flowgraph is only
for manual checks; don't run both at once.

> **Limitation: VRMS on the CGR-201 is less accurate than on the DMM.**
> - Input B resolves 5 mV per count and relies on the CGR-201's stored
>   calibration, so its *absolute* reading can be off by a few mV. The
>   26 Oct values were read on a DMM.
> - Subtracting the no-RF VRMS (the script's `vrms_rise_v`) cancels the
>   offset part of that error, but not a gain error.
> - Weak-signal rows are the least certain: VRMS within about 10 mV of its
>   no-RF value, i.e. below about −25 dBm.
> - Results that use Input B VRMS must say so wherever they're reported,
>   including the GitHub tracker. For a cross-check, read VRMS on the DMM at
>   one or two strong levels: `--ask-vrms` prompts for it.

```bash
PY=/usr/local/Cellar/gnuradio/3.10.12.0_12/libexec/venv/bin/python
cd "/Users/sgfx/Desktop/HMC/Clinic/envelope detector"
$PY ed_sweep.py --scope-only                       # read A and B once, no RF
$PY ed_sweep.py --freq 1.0e9 --levels=-30,-15,0    # Step 5, low edge
$PY ed_sweep.py --freq 1.2e9 --levels=-30,-15,0    # Step 5, high edge
$PY ed_sweep.py --pulse-us 100                     # Step 6, 100 us pulses
$PY ed_sweep.py --pulse-us 10                      # Step 6, 10 us pulses
```

Each run:
1. reads the no-RF baseline of both inputs;
2. asks for **EREF**: put the DMM's red probe on EREF, type the reading
   (e.g. `1.139`) and press Enter. It prints VENV − EREF as a check (expect
   within about 10 mV);
3. asks **Enter** before any RF;
4. runs the steps, then turns the RF off (also on an error or Ctrl-C);
5. asks for **EREF again** and prints the drift over the run;
6. saves a CSV in `data/`, with both EREF readings in its header.

Enter alone skips an EREF prompt. `--no-eref` turns both prompts off.
Keep the DMM's black probe on GND and the red probe on EREF for the whole
session; VRMS no longer needs the DMM.

Close the CircuitGear software and the GRC flowgraph first; each locks its
device.

## You need

- ADL5511-EVALZ, Pluto, CGR-201: Pluto **straight into the Mac** (the shared
  hub caused both dropouts on 26 Oct).
- Bench supply with an adjustable current limit, and a DMM.
- 1 short SMA–SMA cable (Pluto → RFIN): **the same cable as 26 Oct**, so
  that day's Pluto calibration still holds.
- 1 short SMA→BNC cable (VENV → CGR-201 Input A).
- 1 BNC lead to clips, or a scope probe (VRMS → CGR-201 Input B).
- Wrist strap.

## Safety limits for this test

| Item | Limit | Why |
|---|---|---|
| ED supply | 5.00 V (4.75–5.25 V), **never above 5.5 V** | Abs max |
| Supply current limit | 60 mA | Idle is ≈ 17–21 mA; a short shows up immediately |
| RF into RFIN | Pluto ≤ 0 dBm here (measured 26 Oct); ED abs max +19 dBm | Don't add an amplifier |
| VENV load | 1 MΩ input only, short cable. **Never 50 Ω** | VENV sits at 1.1 V and can only source 15 mA |
| Input B clip | Hook on **VRMS**, ground clip on **GND1/GND2**. Never on VPOS | VPOS is +5 V; ground there shorts the supply |

---

## Step 0: Prepare (unpowered)

1. Wrist strap on. SW1 toward its label (enabled). Card edge (P2) off metal.
2. Bench supply set **before connecting**: 5.00 V, 60 mA limit, output off.

## Step 1: Power-only check (no RF, nothing on the SMAs)

1. Supply: + → VPOS, COM → GND. Output on. **Expect ≈ 17–21 mA** (26 Oct: 17 mA).
2. DMM, black on a GND test point:

| Measure | Expect (26 Oct value) | Today |
|---|---|---|
| Supply current | ≈ 17 mA | |
| EREF | ≈ 1.14 V (1.138 V warm) | |
| VRMS | ≈ 31 mV | |

3. Let the board **warm up about 10 minutes** before Step 5. EREF dropped 10 mV
   during warm-up last time, then held within 1–2 mV.
4. Leave the DMM on EREF (black on GND). From here on, the script asks for
   its reading before and after every run.

## Step 2: Hook up the readout

1. VENV SMA → **CGR-201 Input A**.
2. VRMS → **CGR-201 Input B**:
   - hook / red clip on the **VRMS** test point;
   - ground clip on **GND1 or GND2**;
   - a scope probe goes on **1X**.
3. Run `$PY ed_sweep.py --scope-only` (no RF). Expect:

| Input | Expect |
|---|---|
| VENV (A) | ≈ EREF, within ~10 mV (26 Oct: 1.141 V on A vs 1.139 V on the DMM) |
| VRMS (B) | ≈ the DMM's VRMS, about 31 mV |

4. **If B reads ~0–10 mV instead of ~31 mV:**
   - Move the hook from VRMS to **EREF** for a moment and re-run `--scope-only`:

     | B reads | Meaning |
     |---|---|
     | ≈ 1.14 V | the lead works; it was a contact problem on VRMS |
     | ≈ 0.11 V | the probe is on **10X**: switch it to 1X |
     | ≈ 0 V | the lead isn't connected (check the clips and the BNC) |

   - Put the hook back on VRMS afterwards.

   **1 Nov result:** probe on 1X, lead OK. Input B against the DMM:
   - VRMS 15.5 mV vs 23 mV;
   - EREF 1.1138 V vs 1.137 V.

   So B reads **1.4 % low with a −7 mV offset** (its stored calibration).
   Input A read VENV within +3 mV of the DMM. The offset cancels in the VRMS
   rises; the gain error is 0.12 dB.

### About the CGR-201's input errors (read this once)

Each input has a small **zero offset** and a small **gain (scale) error** left
over after its stored calibration. On this unit's low range:

| Input | Zero offset | Gain | Measured |
|---|---|---|---|
| A | ≈ +3 mV | small, not measured separately | VENV vs DMM, 26 Oct and 1 Nov |
| B | ≈ −7.2 mV | × 0.986 (1.4 % low) | two points vs DMM, 1 Nov: VRMS 23 mV, EREF 1.137 V |

These errors are only "fixed" in a loose sense:
- **Repeatable** for a given input range and offset setting. That's why
  `ed_sweep.py` always sets the same ones: DC coupling, low range (±2.6 V),
  0 V centred.
- **Drifts a little with temperature**, so it isn't a constant forever.
  Re-check against the DMM at the start of a session. Seen on 1 Nov: with
  VRMS steady at 0.023 V on the DMM, Input B read 0.0155 V at about 20:20
  and 0.0188 V at 20:34. Its offset moved 3 mV in about 15 min, probably
  the CGR-201 warming up. Within one run it stayed within ±0.3 mV (the no-RF
  rows of the 20:34 sweep).
- **Different Plutos give different levels.** The 1 Nov runs used a
  different Pluto (serial `…dd1f84bfdb`) from 26 Oct (`…f3647c41f6`). The
  1.1 GHz sweep came out 0.44–0.49 dB lower at every level, so the "TX level
  → dBm" calibration is per unit. `ed_sweep.py` now writes the Pluto serial
  into each CSV.
- **Different on each range.** These numbers are for the low range only.
- **Not the cables.** A 50 Ω coax is 50 Ω only for RF (characteristic
  impedance); at DC it is a few milliohms in series with the 1 MΩ input. A
  50 Ω *terminator* would matter, but EREF would then collapse toward 0 V,
  and it read 1.114 V.

**What it means for results:**
- **Rises** (the reading minus the no-RF reading) cancel the offset. The 1.4 %
  gain error is 0.12 dB.
- **Absolute** CGR-201 voltages are only good to a few mV (A) and ~7 mV + 1.4 %
  (B). If one is needed: B_true ≈ (B_read + 7.2 mV) / 0.986.

**Check that it is calibration, not a fault (2 minutes, no RF):**
1. B hook on a **GND** test point. B should read ≈ **−7 mV**: that's the
   offset by itself. Repeat it: it should come back within about 1 mV.
2. **Swap the leads**: VENV into B, VRMS into A. If the error follows the
   **input** (B still reads low on whatever it gets), it's that input's
   calibration. If it follows the **signal**, it's the wiring.
3. Three points (GND, VRMS, EREF) on one straight line means a plain
   offset-and-gain calibration error. A fault would show up as jumps,
   readings that don't repeat, or points off the line.

## Step 3: Connect the Pluto (RF still off)

The GRC flowgraph is not running. Connect Pluto TX → RFIN. The script
records the no-RF readings itself; nothing to write down.

## Step 4: CW transfer curve at 1.1 GHz ✅ done 26 Oct

Results and plot: `ED-TEST-RESULTS.md`. In short:
- VENV gain 1.47–1.51 V/V;
- Pluto: power at RFIN ≈ TX level (0.0 dBm at 0 dB);
- floor ≈ −30 dBm.

Re-run only if something changed (cable, board, Pluto):
`$PY ed_sweep.py`. VRMS is now recorded automatically.

## Step 5: Band edges, 1.0 and 1.2 GHz (CW)

```bash
$PY ed_sweep.py --freq 1.0e9 --levels=-30,-15,0
$PY ed_sweep.py --freq 1.2e9 --levels=-30,-15,0
```

About a minute each; nothing to type except Enter. Results go in
`data/ed_sweep_1.00GHz_*.csv` and `data/ed_sweep_1.20GHz_*.csv`.

| TX level | VENV rise @ 1.0 / 1.1 / 1.2 GHz (mV) | VRMS rise @ 1.0 / 1.1 / 1.2 GHz (mV) |
|---|---|---|
| −30 | … / 4.2 / … | … / 7 / … |
| −15 | … / 53.8 / … | … / 67 / … |
| 0 | … / 327.9 / … | … / 415 / … |

(1.1 GHz values from 26 Oct. VRMS rise = VRMS minus its no-RF value.)

✅ **Pass:** the ratio VENV rise ÷ VRMS rise is about **0.77–0.8** at all three
frequencies (that checks the ED itself). The rises themselves may differ by a
dB or so; that is mostly the Pluto's output changing with frequency.

## Step 6: Pulse response (100 µs and 10 µs)

```bash
$PY ed_sweep.py --pulse-us 100
$PY ed_sweep.py --pulse-us 10
```

At each level (−20, −10, −5, 0 dB) the script:
1. measures **CW** (the same as Step 4);
2. switches the Pluto to **pulses** (on for the pulse length, off for the same
   time);
3. switches the CGR-201 to a faster sampling rate: 2.5 MS/s for 100 µs,
   20 MS/s for 10 µs. That's about 200 samples per pulse and at least 8
   pulses per capture;
4. finds the **pulse top** and the level **between pulses**, skipping the
   edges.

It prints, for each level:
```
VENV 1.2465 V (rise 105.3 mV) ...                      ← CW
pulse top 1.2460 V, between 1.1412 V, height 104.8 mV = 0.995 x CW rise | 25 pulses
```

| Quantity | Expect | Pass if |
|---|---|---|
| Pulse height ÷ CW rise (`pulse_vs_cw`) | 1.00 | 0.95–1.05 at 100 µs and 10 µs |
| Between pulses (`pulse_base_v`) | the no-RF baseline (≈ 1.14 V) | within ~2 mV: the Pluto is really off between pulses |
| Pulses seen | about 3 captures × 8+ periods | no missing or extra pulses |
| VRMS while pulsed | (VRMS_CW − 31 mV) × 0.71 + 31 mV | the pulses are on half the time: half the power |

This step can't show the ED's real 4 ns rise: the CGR-201 (5 MHz) and the
Pluto's edges (~0.5 µs) are much slower. That needs the bench scope later,
together with the comparator delay test.

## Step 7: Power down

1. Make sure no script or flowgraph is running (RF off). The last run's
   end-of-run EREF prompt is your final EREF reading.
2. Turn off the bench supply.
3. Disconnect the cables.

---

## What this gives the comparator test

- The ED is flat across 1.0–1.2 GHz, so one threshold works across the band.
- Pulse heights equal the CW values, so the CW threshold table
  (+20 mV → −21.5 dBm) holds for pulses.
- The level between pulses: the comparator threshold must sit above it.
