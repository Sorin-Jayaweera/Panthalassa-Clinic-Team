# Comparator board: plug-in and power-up procedure (Test B, board alone)

Sofia's session, 19 Nov 2026. Board: EVAL-ADCMP604BKSZ (ADCMP604; this chip's
IN+ leaks about 40 µA when powered, see Emmy's `COMPARATOR-TEST-RESULTS.md`).
Wiring drawing: `comparator_test_wiring.svg`. Datasheet: ADCMP604/605 Rev. C
([DS]). Emmy's procedure: `COMPARATOR-TEST-PROCEDURE.md` on the
`comparator-tests` branch ([EM]).

## Who is connected to what

| Instrument | Serial / ID | Goes to | Through |
|---|---|---|---|
| Bench supply, current-limiting | — | VCC jack, ground | 3.30 V, **limit 30 mA** |
| CGR-201 | **C2BKNPC** | J3 (IN−), threshold | 1 kΩ in series, then 100 nF from J3 to ground (threshold adapter, right at J3) |
| CGR-201 | **C2BJ0VL** | J1 (IN+), test signal | 100 Ω in series, at J1 |
| Siglent SDS1104X-E | SDSMMEBC3R1376 | CH1 IN+, CH2 IN−, CH3 OUT+, CH4 OUT− | ×10 probes, shortest ground |
| 100 Ω | — | across J7 (OUT+) and J8 (OUT−) | short legs |
| DMM | — | J2–J4 reads IN+ − IN−; J4 to ground reads IN− | attach to read, then remove from J2 |
| Ground link | — | AGND to CGND/VEE | short wire (test points TP15–TP13) |

CGR-201 calibration per unit: `data/cgr_dc_cal.json` (19 Nov, DMM).
Set an output with `python3 cgr_dc.py <serial> <volts>`.

**Never-negative rule:** every level our scripts send goes through
`cgr_guard.py`. It only sends DC (no waveforms), only 0.10–3.00 V by that unit's
own calibration, and refuses a unit with no calibration. Allowed codes:
C2BKNPC 2280–3739, C2BJ0VL 2215–3767. Do **not** drive these units with Emmy's
`cmp_cgr.py` or the CircuitGear app: neither uses this guard or these
calibrations. Software cannot control the power-up state (about −0.2 to
−0.3 V), so a unit that was re-plugged must be set and checked before it is
connected.

## Limits

| Item | Limit | Source |
|---|---|---|
| VCC | 3.30 V (ADCMP604 2.5–5.0 V; absolute max 6.0 V) | [DS] p. 4, 6 |
| Supply current | 15 mA typical, 21 mA max. Limit set to 30 mA. **Stop above 25 mA** | [DS] p. 4 |
| IN+, IN− | Working −0.5 V to VCC + 0.2 V = 3.5 V. Absolute max −0.5 V to VCC + 0.5 V = 3.8 V, ±50 mA. Scripts allow 0–3.0 V | [DS] Table 1 p. 3, Table 3 p. 6 |
| Inputs with the board unpowered | Absolute max becomes −0.5 to +0.5 V, so **no input before power** | [DS] Table 3 |
| CGR-201 output | Can swing ±3 V. Powers up at about −0.2 to −0.3 V (measured 19 Nov). Always set DC and check it before connecting | measured |
| Outputs | 100 Ω across J7–J8; only ×10 probes on them | [DS] Table 1 (R_LOAD = 100 Ω), p. 10 |

## Power-up order

| # | Do | Check |
|---|---|---|
| 0 | Wrist strap on. Supply output off. Both CGR-201 BNCs **not** connected to the board. | — |
| 1 | Supply: 3.30 V, current limit 30 mA, output off. Connect + to VCC, − to ground. Ground link in place. | DMM, power off: AGND to CGND/VEE near 0 Ω |
| 2 | Supply output **on**. | Current 15–25 mA. Not in current-limit (CC) mode. DMM VCC (TP11) to ground: 3.30 V |
| 3 | Probes on (CH1–CH4) and 100 Ω in place. | Scope: OUT+ and OUT− each near 1.1 V or 1.5 V, or jittering (inputs still open) |
| 4 | Set both CGR-201s to DC: C2BKNPC 1.20 V, C2BJ0VL 1.10 V. | DMM at each **Output BNC**, nothing connected: 1.195–1.205 V and 1.095–1.105 V |
| 5 | Connect **C2BKNPC → threshold adapter → J3**. | DMM J4 to ground: about 1.20 V |
| 6 | Connect **C2BJ0VL → 100 Ω → J1**. | DMM J2 to J4 (IN+ − IN−): about −100 mV (the 40 µA leak shifts IN+ up by about 4 mV through 100 Ω). Remove the DMM lead from J2 afterwards |
| 7 | Look at the scope. | OUT+ steady low, OUT− steady high, no 27 MHz. Supply current unchanged |
| 8 | Start the measurement. | — |

## Shutdown

1. Set C2BJ0VL to 1.10 V (output low, IN+ well below the threshold).
2. Disconnect J1, then J3.
3. Supply output off.
4. Only now unplug CGR-201 USB cables, if at all. A re-plug resets the
   output to about −0.2 to −0.3 V.

## If something looks wrong

- **Supply shows CC (current limit), or current above 25 mA:** supply off,
  disconnect J1 and J3, check the wiring.
- **A CGR-201 USB was unplugged or the Mac slept:** disconnect that BNC from
  the board, set DC again, check with the DMM, reconnect.
- **The DMM reads IN+ or IN− below 0 V or above 3.3 V:** disconnect that
  input first, then investigate.

## Compared with Emmy's procedure [EM]

| Item | Emmy | Here | Why |
|---|---|---|---|
| Order | "Supplies on → then signals. Signals off → then supplies." | Same | Inputs above an unpowered VCC drive the protection diodes |
| Threshold source | 10 kΩ pot from the board's VCC, 0.1 µF on the wiper from run 2 | CGR-201 C2BKNPC through 1 kΩ + 100 nF | Set from the Mac, repeatable, logged. Emmy chose the pot partly for the CGR's ~2 mV DC ripple; the 1 kΩ + 100 nF filter (corner about 1.6 kHz) removes that. The pot's advantage (it can't exceed VCC) is replaced by the script limit plus DMM checks |
| IN+ series resistor | 1 kΩ (runs 1–2), then 100 Ω (runs 3–6) | 100 Ω | Same as her runs 3–6, so the results compare directly. With the 40 µA leak, IN+ sits about 4 mV above the CGR setting (40 mV with 1 kΩ). Lower source resistance also holds IN+ more firmly against coupling from the outputs |
| CGR-201 calibration | One calibration per session, two points + 1.20 V check, DMM | Per unit, two points + check, DMM, by serial number | Two units in use. The units differ: 1.986 vs 1.868 mV/code, zero codes 2229.5 vs 2161.4 |
| Before connecting the CGR | `dc 0.60` | Set DC and check with the DMM at the Output BNC | Same idea; the DMM check catches a wrong calibration or a reset unit |
| 100 Ω termination | Clip leads at the end of SMA–BNC cables ("Best": solder at J7/J8) | Short legs at J7/J8 | Emmy's clip-lead version oscillated at about 27 MHz; this tests her suggested next step |
| Output readout | CGR-201 Input B on J7; later a ×10 probe on J7 | ×10 probes on both J7 and J8 (CH3, CH4) | Sees 27 MHz (the CGR-201 can't); OUT+ − OUT− is what an FPGA would see |
| IN+ monitor | CGR-201 Input A on the J1 tee; later CH1 probe | CH1 ×10 probe on IN+ | Emmy found a lead on IN+ fed the oscillation. **Repeat with the CH1 probe removed** to check this |
| Supply | 3.30 V; limit 39–40 mA (JAIQU), none on the E3630A | 3.30 V, limit 30 mA | 30 mA is above the 21 mA datasheet maximum, so it never limits a healthy chip, and lower than 40 mA for a fault |
| DMM | Red J1 / black J3 for IN+ − IN− | Red J2 / black J4 | Same nodes (J1 = J2, J3 = J4, checked 18 Nov); J2 and J4 keep the DMM off the cables carrying the signals |
