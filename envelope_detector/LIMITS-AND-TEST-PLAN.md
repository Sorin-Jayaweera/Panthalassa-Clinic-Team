# Envelope detector → comparator → keying switch: limits and bench-test plan

Started 2026-10-26, updated the same day after the photos in `parts/`.
Covers the ED → comparator → FPGA → keying-switch slice of
`design drafts/racon_draft_design01b_drawing.pdf` ("The JACON").

Sources:
- ADL5511 datasheet Rev. E
- ADCMP604/605 datasheet Rev. C
- ADCMP600/601/602 datasheet Rev. A
- ADG901/902 datasheet Rev. B
- Syscomp CGR-201 datasheet
- Icepi Zero Crowd Supply page

Anything marked **(verify)** was not in a datasheet. Check it on the board or
in its schematic.

## What is on the bench (from `parts/`)

| Photo | What it is | Notes |
|---|---|---|
| `ED.HEIC` | **ADL5511-EVALZ** (PCB A02951B) | Bottom side shown. Has the VRMS/EREF test points, JP1, GND/VPOS pins and a P2 card-edge connector, all matching the datasheet's eval board. Check the top silkscreen to tell the RFIN and VENV SMAs apart. |
| `comp_bottom.HEIC`, `comp_top.HEIC` | **ADCMP604BKSZ eval board** (SC70-6, "0214 Rev A") | **The chip is already soldered on** at the center of the DUT1 square. The 4 plated holes around it are a fixture/socket mounting footprint and are not needed. **Not the ADCMP600 from the drawing.** LVDS output, no hysteresis. SMAs: IN+, IN−, IN+FB, IN−FB, OUT+, OUT−. Banana jacks: VCC, AGND, CGND/VEE, AGND. The secondary side has only decoupling capacitors (C1–C9, C21–C29, tantalum C10/C30) and **no resistors**: the inputs are unterminated (high-Z) and there is **no 100 Ω across the outputs**. |
| `cgr_201.heic` | **Syscomp CGR-201** (unit #6) | 3 BNCs: Output (50 Ω), Input A, Input B (1 MΩ ‖ 20 pF). Label: **50 V peak max input**; instrument ground = computer ground. 2×10 header: Digital Outputs 0–7, Digital Inputs 0–7, PWM, Ext Trig, Trig Out, GND. |
| `IcePi.HEIC` | **Icepi Zero** (Lattice ECP5 FPGA, Pi-Zero size) + carrier "IcepiZero_AD9280_AD9708_2x12" + 8-bit high-speed ADC/DAC module | The SMA cable loops the DAC output back into the ADC input (self-test). **An FPGA is already here**, the ECP5 option from the drawing. |

## Component cards (same rows for every part)

### Signal-chain parts

| | **ADL5511** envelope detector | **ADCMP604** comparator (on hand) | ADCMP600 comparator (drawing / bare chip) | **ADG901** keying switch |
|---|---|---|---|---|
| **Role** | IF power → baseband envelope voltage | Envelope > threshold → digital "ping" | Same | FPGA gates the VCO → TX on/off |
| **Supply** | 4.75–5.25 V | 2.5–5.0 V (shared VCCI/VCCO pin) | 2.5–5.5 V | 1.65–2.75 V |
| **Supply abs max** | 5.5 V | 6.0 V | 6.0 V | 4.0 V |
| **Supply current** | 21.5 mA idle, 44 mA at +15 dBm | 15 mA typ, 21 mA max | 3–4 mA | < 1 µA |
| **Bench current limit** | 60 mA | 40 mA | 20 mA | 5 mA |
| **Input type** | RF, 50 Ω (75 Ω shunt + 100 pF on the eval board) | Analog differential, high-Z (≥ 100 kΩ, 1 pF) | Same | RF 50 Ω (RF1/RF2) + CMOS CTRL |
| **Input working range** | −30 to +17 dBm, DC–6 GHz | −0.2 V to VCC + 0.2 V | −0.2 V to VCC + 0.2 V | RF ≤ 7 dBm at 0 V bias; CTRL 0 / ≥ 1.7 V |
| **Input abs max** | **+19 dBm** (5.6 V p-p) | **−0.5 V to VCC + 0.5 V**, ±50 mA | **−0.5 V to VCC + 0.5 V**, ±50 mA | RF 18 dBm; **CTRL ≤ VDD + 0.3 V** |
| **Output type** | Analog, single-ended (VENV), referenced to EREF | **LVDS differential (OUT+/OUT−)** | CMOS, single-ended | RF 50 Ω |
| **Output range** | EREF (≈ 1.1 V) + 1.46 × Vrms_in; max 3.5 V | 350 mV differential, 1.125–1.375 V common mode | 0 V to VCC | Pass / block, 0.8 dB loss, ~40 dB isolation |
| **Output load needed** | **≥ 500 Ω, ≤ 10 pF** (15 mA max) | **100 Ω across OUT+/OUT−** | High-Z, ≤ 5 pF (±50 mA abs max) | 50 Ω |
| **Speed** | 130 MHz BW, 4 ns rise, 2 ns delay | 1.6 ns delay, 600 ps edges, 1.3 ns min pulse | 3.5–4.3 ns delay, 3–4.5 ns min pulse | 3.6 ns on, 5.8 ns off |
| **Hysteresis / control pins** | ENBL (SW1 on the eval board) | **< 0.1 mV, none adjustable** (the ADCMP605 adds LE/HYS) | 2 mV fixed | CTRL: 1 = through, 0 = isolated |
| **ESD** | 2 kV HBM | Standard | Standard | **1 kV** |

### Instruments and stand-ins

| | **Pluto** (Rev C, AD9364 mode) | **CGR-201** | **Icepi Zero** (ECP5) | **AD9280 / AD9708 module** |
|---|---|---|---|---|
| **Role** | Stands in for the IF signal (TX) and can receive back (RX) | Scope + threshold source (generator at DC) | The real FPGA: reads the comparator, keys the switch, talks to the computer | DAC = threshold candidate; ADC = can digitize VENV |
| **Supply** | USB, 500 mA (plug it straight into the Mac) | USB | USB-C 5 V | 5 V from the carrier |
| **Input type** | RX: RF 50 Ω, AC-coupled, 70 MHz–6 GHz | Scope: 1 MΩ ‖ 20 pF; digital in: 3/5 V HCMOS | GPIO: LVCMOS, assume 3.3 V **(verify)** | ADC SMA: analog |
| **Input range / abs max** | **RF only, ≤ 0 dBm. Never DC or logic levels** | 20 mV/div – 5 V/div; **50 V peak max** (label) | 0–3.3 V **(verify)** | Likely ±5 V full scale **(verify)**. The AD9280 itself is 0–2 V |
| **Output type** | TX: RF 50 Ω | **One** BNC output (generator): 50 Ω, ±3 V; header digital out: **5 V** HCMOS | GPIO: LVCMOS 3.3 V **(verify)** | DAC SMA: analog, op-amp buffered |
| **Output range** | ~0 to +7 dBm near 1 GHz, uncalibrated | ±3 V (8-bit) | 0 / 3.3 V | Likely ±5 V **(verify)**, 8-bit ≈ 39 mV steps |
| **Speed** | Up to 61.44 MS/s; use a cyclic TX buffer for clean pulses | **5 MHz BW, 40 MS/s** (25 ns/sample) | 50 MHz oscillator; PLL for faster sampling | ADC 32 MS/s, DAC 125 MS/s |
| **Link to computer** | USB (libiio / GNU Radio) | USB serial, documented commands | Onboard USB-UART + JTAG; open-source toolchain | Through the FPGA |

## Signal hand-offs: does each output fit the next input?

| # | From → To | Output gives | Input accepts | OK? | What to do |
|---|---|---|---|---|---|
| H1 | Pluto TX → ADL5511 RFIN | ≤ +7 dBm, 1.0–1.2 GHz | −30 to +17 dBm (abs +19) | ✅ | Direct. A 10 dB pad is optional |
| H2 | ADL5511 VENV → ADCMP604 IN+ | 1.1–1.9 V (from the Pluto), up to 3.4 V (real chain) | −0.2 V to VCC + 0.2 V; needs ≥ 500 Ω load | ✅ at VCC = 3.3 V | **No 50 Ω termination on IN+.** Keep the cable short. VCC ≥ 3.3 V for the real chain |
| H3 | Threshold (CGR-201 gen / pot) → ADCMP604 IN− | ±3 V through 50 Ω | −0.5 V to VCC + 0.5 V | ⚠️ | **Set the generator to DC first and add 1 kΩ in series.** A pot off VCC is safest |
| H3′ | AD9708 DAC → ADCMP604 IN− (later) | Likely ±5 V **(verify)** | −0.5 V to VCC + 0.5 V | ❌ as-is | Divider + clamp, or a real nanoDAC (16-bit); 39 mV steps are too coarse |
| H4 | ADCMP604 OUT+ → CGR-201 Input B | LVDS: OUT+ ≈ 1.03 V low / 1.38 V high | 1 MΩ | ⚠️ | **Put 100 Ω across OUT+/OUT−.** Only OUT+ goes to the scope (single-ended), trigger level ≈ 1.2 V. This keeps Input A free |
| H5 | ADCMP604 OUT± → Icepi Zero | LVDS | LVCMOS 3.3 V | ❌ direct | LVDS receiver (e.g. SN65LVDS2 / DS90LV012A at 3.3 V) → GPIO, or an ECP5 differential input if a P/N pair reaches the header **(verify)** |
| H6 | ADCMP604 OUT± → ADG901 CTRL | LVDS | CMOS, ≤ VDD (2.5 V) | ❌ | Only through the FPGA, or an LVDS receiver powered at 2.5 V |
| H7 | Icepi GPIO → ADG901 CTRL | 3.3 V | **≤ 2.75 V** (abs VDD + 0.3) | ❌ | Divider (e.g. 1 kΩ / 2.2 kΩ → 2.3 V) or a 2.5 V-powered buffer |
| H8 | CGR-201 digital out → ADG901 CTRL | **5 V** | ≤ 2.75 V | ❌ | Divider 1 kΩ / 1 kΩ → 2.5 V, or don't use |
| H9 | ADCMP604 OUT± → Pluto RX | LVDS / DC | RF only | ❌ | **Never** |
| H10 | ADL5511 VENV → AD9280 ADC (optional) | 1.1–3.4 V | Likely ±5 V, 8-bit ≈ 39 mV per step **(verify)** | ⚠️ | Coarse but OK for seeing pulses at 32 MS/s. Check the module's input impedance is ≥ 500 Ω |

Expected ED output at ~1.1 GHz (gain ≈ 1.46 V/V rms):

| Pin (dBm) | −30 | −20 | −10 | 0 | +7 (Pluto max) | +10 | +14 | +17 |
|---|---|---|---|---|---|---|---|---|
| VENV − EREF | 10 mV | 33 mV | 103 mV | 327 mV | 731 mV | 1.03 V | 1.64 V | 2.31 V |
| VENV | 1.11 V | 1.13 V | 1.20 V | 1.43 V | 1.83 V | 2.13 V | 2.74 V | 3.41 V |

Threshold → trip power: `P_trip[dBm] = 10·log10((ΔV/1.46)² / 50 Ω / 1 mW)`.

| ΔV above EREF | +20 mV | +50 mV | +100 mV | +300 mV |
|---|---|---|---|---|
| Trips at | −24 dBm | −16 dBm | −10 dBm | −1 dBm |

## Hookup list (computer replaces the FPGA, keying switch left out): drawn in `bench_wiring.svg`

| # | From | To | Via | Notes |
|---|---|---|---|---|
| 1 | Pluto TX | ADL5511 RFIN | SMA | 1.1 GHz CW or pulses, ≤ +7 dBm. No splitter needed while the switch is out |
| 3 | ADL5511 VENV | ADCMP604 IN+ (J1) | SMA tee, short cables | No 50 Ω anywhere on this net |
| 4 | Tee | CGR-201 Input A | SMA→BNC | VENV monitor, 1 MΩ |
| 5 | CGR-201 Output | ADCMP604 IN− (J3) | 1 kΩ series | Set to DC (1.15–2.0 V) **before** connecting |
| 6 | ADCMP604 OUT+ (J7) ↔ OUT− (J8) | each other | 100 Ω | LVDS termination |
| 7 | ADCMP604 OUT+ (J7) | CGR-201 Input B (or a bench-scope channel at 1 MΩ, never 50 Ω) | SMA→BNC | Trigger ≈ 1.2 V rising = ping |
| 8 | Bench +5 V / +3.3 V | ED VPOS / comparator VCC | banana / pins | Limits 60 / 40 mA. CGND/VEE → AGND |
| 9 | All grounds | CGR-201 BNC shell | — | One common point |
| 10 | Pluto, CGR-201 | Computer | USB | Pluto straight into the Mac |

Leave J2 (IN+FB) and J4 (IN−FB) open until their purpose is traced.

## ⚠️ Where to be careful

1. **The comparator on hand is the ADCMP604, and its output is LVDS.**
   - It is not 0 V / VCC logic: nothing that expects CMOS (the CGR-201 digital
     inputs, the ADG901 CTRL, Pico/FPGA LVCMOS pins) can read it directly.
   - It needs 100 Ω across OUT+/OUT−.
   - It is the right interface for an FPGA, which is why it may have been
     chosen.
2. **No hysteresis (< 0.1 mV).** Noise from the ED's 130 MHz bandwidth will
   make the output chatter at the threshold.
   - Add positive feedback. The IN+FB / IN−FB SMAs may be meant for this or
     may be pass-throughs; **(verify)** by tracing the board.
   - Or low-pass VENV (R19/C8 pads on the ED board), or debounce in the FPGA.
3. **Comparator inputs: −0.5 V to VCC + 0.5 V.** This applies to the CGR-201
   generator (±3 V) and the AD9708 module (likely ±5 V).
   - Configure the source before connecting.
   - Put 1 kΩ in series.
4. **VENV must not see 50 Ω.** Its 1.1 V idle level would pull 22 mA, more
   than its 15 mA drive.
   - Before connecting, check the ADCMP604 board for 49.9 Ω resistors on
     IN+/IN− **(verify)**.
   - Set scopes to 1 MΩ.
5. **Comparator VCC and the ED swing.** VENV reaches 3.4 V at +17 dBm.
   - Run the comparator at **3.3 V** (≤ 5.0 V max for the ADCMP604).
   - Tie CGND/VEE to AGND for single-supply use.
6. **ADG901 CTRL ≤ VDD (≤ 2.75 V).** 3.3 V and 5 V logic both need a divider
   or buffer (H7, H8).
7. **The real chain may overdrive the ED.**
   - Worst case is about +14 dBm or more at the ED: IF +3 dBm, +22.5 dB from
     the IF amp, −6 dB from the splitter.
   - That is close to the ED's +17 dBm spec and +19 dBm abs max.
   - Plan a pad in front of the ED.
8. **CGR-201 cannot resolve radar-length pulses** (5 MHz bandwidth).
   - Test with 10 µs–1 ms pulses.
   - For ns timing, use a lab scope or the FPGA.
9. **Supplies.** Set the current limits from the cards above.
   - Check the voltages: ED 5 V, comparator 3.3 V, **ADG901 ≤ 2.75 V**.
   - Order: supplies on before signals; signals off before supplies.
10. **Grounds.** The Pluto, CGR-201 BNC shells, Icepi and computer share USB
    ground. Tie the bench-supply negatives to that ground at one point.
11. **Pluto "off" is not zero.** LO leakage leaves a few mV of VENV between
    pulses. Set the threshold above it.
12. **ESD.** Use a wrist strap (the ADG901 is rated only 1 kV). Don't set the
    ED board's card edge on metal while powered.

## Test plan

### Test A: ADL5511 alone
Pluto TX → RFIN. VENV → CGR-201 ch A (1 MΩ, short cable). DMM on EREF and VRMS.

1. Set 5.0 V / 60 mA and SW1 = enable, with no RF. Expect about 21.5 mA,
   EREF ≈ 1.1 V, VENV ≈ EREF, VRMS ≈ 23 mV.
2. Send a CW tone at 1.1 GHz. Step the Pluto attenuation in 5 dB steps and log
   VENV − EREF and VRMS. Compare against the table above.
3. Calibrate the Pluto using VRMS: Vrms_in ≈ (VRMS − 13 mV) / 1.9. Save the
   table of attenuation setting → actual dBm.
4. Check flatness at 1.0, 1.1 and 1.2 GHz.
5. Pulsed tests with a cyclic buffer:
   - first 100 µs on / 1 ms period;
   - then 10 µs;
   - then 1.2 µs.

   The pulse height should match CW at the same level. Record the off-state
   residual.

### Test B: ADCMP604 alone
VCC = 3.3 V / 40 mA, CGND/VEE tied to AGND. Put a 100 Ω resistor across
OUT+/OUT−.

The CGR-201 has one output and two inputs, so:
- **Output (generator)** → 1 kΩ → IN+, a slow test signal;
- **Input A** = IN+, to see what the comparator is given;
- **Input B** = OUT+ only, single-ended: ≈ 1.03 V low, ≈ 1.38 V high;
- **IN−** threshold from a pot or a bench supply channel.

1. Power up with the inputs grounded. Expect about 15 mA. With the inputs
   equal, the output state is undefined; that is fine.
2. Set IN− = 1.20 V from the pot. Set the generator to a positive-only
   triangle, 0.8 → 1.6 V at 100 Hz. OUT+ should step up and down where
   Input A crosses 1.20 V (±5 mV).
3. Chatter check: slow the triangle to 1–10 Hz and count the extra edges
   (flag 2).
4. Sweep IN− from 1.1 to 2.0 V and confirm the trip point follows it.

### Test C: ED → comparator → computer (switch deferred)
0. **Warm up, then set the threshold from a fresh baseline** (learned in
   Test A, see `ED-TEST-RESULTS.md`):
   - Power the ED and let it run **about 10 minutes** before setting any
     threshold. EREF/VENV dropped 10 mV during warm-up (1.148 → 1.138 V),
     then held within 1–2.4 mV over a 10-minute sweep.
   - With no RF, measure VENV right before the test, using the CGR-201
     (`ed_sweep.py --scope-only`) or the DMM.
   - Set IN− = **that measured VENV + the margin**, not a fixed voltage.
   - Start with **+20 mV**, which trips at about −21.5 dBm. That's about 10×
     the drift once warm.
   - Margins from Test A's measured curve: +10 mV → −25.5 dBm, +50 mV →
     −15.5 dBm, +100 mV → −10.4 dBm.
1. VENV → IN+ (no termination). IN− = no-RF VENV + 20 mV (step 0). Pulse the
   Pluto well above the trip point (e.g. TX −10 dB = −10 dBm); expect one clean
   output pulse per RF pulse.
2. Lower the RF level to find where pulses are missed or start chattering
   (the S-curve).
3. **Computer as the FPGA (current plan; wiring in `bench_wiring.svg`).**
   - The CGR-201 Output is the DC threshold → 1 kΩ → IN−.
   - Input A = VENV (tee). Input B = OUT+, with its trigger on the rising edge
     = "ping detected".
   - Python counts and timestamps the pings and logs VENV for each one.
4. Deferred: the keying switch. When it comes back, the computer drives it from
   CGR-201 Digital Out 0 through a 1 kΩ/1 kΩ divider (5 V → 2.5 V) into the
   ADG901 CTRL, with VDD = 2.5 V. See H7/H8 and flag 6.
5. Later: OUT± → LVDS receiver or the ECP5's differential input → Icepi Zero,
   which takes over the timing at ns resolution.

## Getting the comparator output into the computer

**Recommended: the Icepi Zero (ECP5).** It is already on the bench and is the
FPGA from the drawing.
- Comparator OUT± goes to the FPGA through an LVDS receiver or the ECP5's
  differential input (H5).
- The FPGA timestamps edges (ns-level with a PLL-multiplied clock), handles the
  keying/Morse timing, and streams events to the computer over its onboard
  USB-UART.
- The computer only configures and logs. A USB round trip takes ≥ 1 ms, so the
  computer cannot key the switch in real time.

**For now (computer instead of the FPGA):** the CGR-201 Input B takes OUT+.
- Its trigger, set to ≈ 1.2 V on a rising edge, is the "ping detected" event.
- A script arms and reads it over the CGR-201 serial commands.
- The comparator output can't go straight to the CGR-201 digital inputs or
  Ext Trig: those expect 3/5 V logic, and LVDS swings only ~0.35 V.
- An SN65LVDT2 receiver (3.3 V, built-in 100 Ω termination) would convert it
  if a logic-level signal is wanted.

See `bench_wiring.svg` for the full hookup.

**Not the Pluto RX.** It is an RF-only input, and logic levels are out of band
and unsafe for it.

Optional loopback that shows up in GNU Radio:
- Split the Pluto TX: one branch → ED, the other branch → ADG901.
- ADG901 → ≥ 30 dB pad → Pluto RX.
- The tone appears only while the switch is keyed.
