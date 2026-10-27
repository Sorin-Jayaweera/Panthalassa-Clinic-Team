# Test A: envelope detector (ADL5511) on its own

Wiring: `ed_test_wiring.svg`. Limits and background: `LIMITS-AND-TEST-PLAN.md`.
The full chain (`bench_wiring.svg`) is saved for later.

Goal:
1. Confirm the ADL5511 board works.
2. Measure its transfer curve at the IF (1.0–1.2 GHz).
3. Use its VRMS output to **calibrate the Pluto's real output power**. This
   table gets reused in every later test.
4. Check its pulse response.

## Pluto flowgraph: `ed_test_pluto_tx_soapy.grc`

This is for the Homebrew GNU Radio. If your prompt shows `(gr)` or `(base)`,
run `conda deactivate` first.

```bash
gnuradio-companion "/Users/sgfx/Desktop/HMC/Clinic/envelope detector/ed_test_pluto_tx_soapy.grc"
```

Press ▶. A small window opens with two controls:

| Control | What it does |
|---|---|
| **TX level (dB)** | −89 (start, ≈ nothing out) … 0 (full power). This is the "TX atten" column in Step 4 |
| **Pulsed** | Unchecked = steady tone (Steps 3–5). Checked = on/off pulses (Step 6) |

Two settings you edit in GRC (double-click the block, then re-run):
- `freq`: 1.1e9 by default. Change it to 1.0e9 / 1.2e9 for Step 5.
- `pulse_us`: 100 by default. Change it to 10 for the second pulse row in
  Step 6. The gap between pulses is the same length as the pulse.

The calibration in Step 4 is only valid for this flowgraph as written.

## You need

- ADL5511-EVALZ, Pluto (+ USB cable), CGR-201 (+ USB cable)
- Bench supply (one channel), DMM
- 1 short SMA–SMA cable (Pluto → RFIN)
- 1 short SMA→BNC cable or adapter (VENV → CGR-201 Input A)
- (Optional) BNC male → clip lead or scope probe, if you want EREF live on Input B. Not needed: EREF is read with the DMM instead
- DMM probes/clips for VRMS and GND
- Wrist strap

## Safety limits for this test

| Item | Limit | Why |
|---|---|---|
| ED supply | 5.00 V (4.75–5.25 V), **never above 5.5 V** | Abs max |
| Supply current limit | 60 mA | Idle is 21.5 mA; a short shows up immediately |
| RF into RFIN | Pluto ≤ +7 dBm is always safe (ED spec +17, abs max +19 dBm) | Don't add an amplifier in this test |
| VENV load | 1 MΩ scope input only, short cable. **Never 50 Ω** | VENV sits at 1.1 V and can only source 15 mA |

---

## Step 0: Prepare (unpowered)

1. Put on the wrist strap.
2. Look at the **top** of the ED board. Find out which SMA is **RFIN** and which
   is **VENV**, and note it here: RFIN = left / right, VENV = left / right.
3. Set **SW1 toward the "SW1" label** (enabled).
4. Keep the card-edge connector (P2) off anything metal.
5. Set the bench supply **before connecting it**: 5.00 V, current limit 60 mA,
   output OFF.

## Step 1: Power-only check (no RF, nothing on the SMAs)

1. Connect the supply: + → VPOS pin, COM → GND pin. Turn the output on.
2. Read the supply current. **Expect ≈ 21.5 mA.**
   - If it is above ~35 mA or about 0 mA, turn it off and recheck the wiring
     and SW1.
3. DMM (COM on the GND test point):

| Measure | Expect | Measured |
|---|---|---|
| Supply current | ≈ 21.5 mA | |
| EREF | ≈ 1.1 V | |
| VENV (at the SMA center pin) | EREF + ~2 mV | |
| VRMS | ≈ 23 mV (no-signal offset) | |

4. Optional: flip SW1 off. The current should drop to about 0 (26 µA). Then
   flip it back on.

✅ **Pass:** all four numbers are close to the expected values.

## Step 2: Hook up the readout

1. VENV SMA → **CGR-201 Input A** (short cable). Input B is unused.
2. CGR-201 settings: Input A DC coupled, 500 mV/div to start.
3. **EREF is read with the DMM, not the scope.** It's a fixed reference that
   doesn't change with RF level, only by a few mV as the board warms up.
   - Your Step 1 EREF reading is **EREF_start**.
   - Move the DMM red probe to **VRMS** and leave it there for Steps 3–6.
     The black probe stays on GND throughout.
   - At the end (before Step 7), move the red probe back to EREF once:
     **EREF_end**. If it differs from EREF_start by more than ~5 mV, use the
     average.
   - Every "VENV − EREF" in the tables below = Input A reading − EREF.
4. Input A should read about 1.1 V, the same as EREF_start within a few mV.
5. Below about −20 dBm, VENV − EREF is only 10–30 mV, too small for the
   CGR-201 to resolve on top of the 1.1 V baseline. Write "—" in those VENV
   cells; VRMS covers those rows.

## Step 3: Connect the Pluto, with TX at minimum

1. Before connecting: the flowgraph is not running.
2. Connect Pluto TX → RFIN.
3. Start the flowgraph. It opens at **TX level = −89** with **Pulsed
   unchecked**.
4. Record the "Pluto on, ~nothing out" readings. They are your noise floor:

| Measure | Value |
|---|---|
| VRMS | |
| VENV − EREF | |

## Step 4: CW transfer curve at 1.1 GHz (the main measurement)

**Automated option: `ed_sweep.py`.**
- **What it does:** steps the Pluto through the TX levels below, reads VENV
  on CGR-201 Input A (averaging 3 captures per step), turns the RF off
  again, and saves `data/ed_sweep_<freq>_<time>.csv`.
- **Before running:** close the CircuitGear software and the GRC flowgraph.
  Each of them locks its device.
- **Your part:** record EREF with the DMM before and after. VRMS is still
  read by hand if you want it.
- **What's in the CSV:**
  - `venv_rise_v`: VENV minus the no-RF baseline, which cancels the scope's
    offset;
  - `venv_v`: absolute VENV, which you can compare with EREF.

```bash
/usr/local/Cellar/gnuradio/3.10.12.0_12/libexec/venv/bin/python ed_sweep.py
```

Use `--scope-only` to just read Input A with no RF, and `--freq 1.0e9` for
Step 5.

Step the **TX level** slider and log one row per step. Wait about 1 s after
each change, then read.

Compute the actual power from VRMS:
- Vin = (VRMS − 0.013) / 1.90
- Pin [dBm] = 10·log10(Vin² / 50 / 0.001)

| TX atten (dB) | VRMS (V) | VENV − EREF (V) | → Pin (dBm, from VRMS) | VENV−EREF ÷ Vin (expect ≈ 1.46) |
|---|---|---|---|---|
| −80 | | | | |
| −70 | | | | |
| −60 | | | | |
| −50 | | | | |
| −40 | | | | |
| −35 | | | | |
| −30 | | | | |
| −25 | | | | |
| −20 | | | | |
| −15 | | | | |
| −10 | | | | |
| −5 | | | | |
| 0 | | | | |

What you should see (datasheet values at ~1 GHz):

| Pin (dBm) | −30 | −20 | −10 | −5 | 0 | +5 | +7 |
|---|---|---|---|---|---|---|---|
| VRMS | 0.026 V | 0.055 V | 0.147 V | 0.252 V | 0.438 V | 0.769 V | 0.964 V |
| VENV − EREF | 10 mV | 33 mV | 103 mV | 184 mV | 326 mV | 581 mV | 731 mV |

✅ **Pass:**
- From about −25 dBm up, each 5 dB attenuation step changes Pin by about 5 dB.
- The ratio in the last column stays around 1.4–1.5.
- Below about −30 dBm, the readings flatten into the floor. That is expected.

📌 **Keep this table.** "TX atten → actual dBm" is the Pluto calibration for
every later test.

## Step 5: Frequency flatness

Repeat three rows (−30, −15, 0 dB) at **1.0 GHz** and **1.2 GHz**, the edges
of the IF band. Stop the flowgraph, change `freq`, and run it again.

| TX atten | Pin @ 1.0 GHz | Pin @ 1.1 GHz | Pin @ 1.2 GHz | VENV−EREF @ 1.0 / 1.1 / 1.2 |
|---|---|---|---|---|
| −30 | | | | |
| −15 | | | | |
| 0 | | | | |

✅ **Pass:** VENV−EREF for the same Pin agrees within about ±0.5 dB across the
band. Most of the Pin difference is the Pluto itself, not the ED.

## Step 6: Pulse response

Set TX level to about −10 dB and tick **Pulsed**. Trigger the CGR-201 on
Input A, rising edge, at EREF + 100 mV.

| `pulse_us` | What to look for on Input A | Pulse top − baseline | Matches CW at same level? |
|---|---|---|---|
| 100 | Clean, flat-topped pulse sitting on ~1.1 V | | |
| 10 | Still flat-topped | | |

Shorter pulses aren't worth trying here, because the CGR-201 can't show them
cleanly.

1. Also record the baseline **between** pulses, compared with Step 3's floor.
   This is the Pluto's "off" leakage, and the comparator threshold must sit
   above it.
2. Optional, for true ED speed (4 ns rise): put the bench scope on VENV with a
   1 MΩ input and a ×10 probe, never 50 Ω.

✅ **Pass:** the 100 µs and 10 µs pulse heights match the CW VENV−EREF at the
same attenuation, within about 5 %.

## Step 7: Power down

1. Stop the Pluto flowgraph (■ in GRC, or close its window).
2. Turn off the bench supply.
3. Disconnect cables.

---

## What this test gives you for the next step (comparator)

- The Pluto calibration table (TX attenuation → dBm).
- The ED's real gain (V/V rms) at 1.1 GHz, so you can set the threshold:
  - ΔV above EREF ↔ trip power, from your own measurements instead of the
    datasheet;
  - the minimum threshold, which has to clear the Step 3 / Step 6 floor.
- Confirmation that the pulse shape is clean at ≥ 10 µs, the pulse length to
  use with the CGR-201.
