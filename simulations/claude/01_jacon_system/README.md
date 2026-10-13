# 01 – JACON full-system LTspice model

Behavioral model of every block in `racon_draft_design01b_drawing.pdf`, from the 9.4 GHz radar echo to the Morse `. - .` reply at the same frequency.

![schematic overview](plots/JACON_schematic_overview.png)

## Using it in LTspice

1. Open **`JACON_system.asc`**. Keep the `jacon_*.asy` symbols and `jacon_blocks.inc` in the same folder.
2. In the **TEST SELECT** box, change **`.param TEST=0`** to the number of the function you want to test.
3. Press Run, then click any net label to plot it. Run time, step size and the stimuli all follow `TEST`.

Every function sits in its own dashed box, numbered like the drawing:

| box | function | blocks |
|---|---|---|
| `[0]` | test-bench stimuli | radar echo source, injected test signals |
| `[1]` | RX RF front end | power limiter → LNA → RX mixer |
| `[2]` | LO | ADF5355 PLL → LO buffer → LO splitter |
| `[3]` | IF chain | IF amp → resistive splitter |
| `[4]` | pulse detection | envelope detector, threshold DAC, comparator |
| `[5]` | limiting amp | 3 gain stages + harmonic LPF |
| `[6]` | delay-line discriminator | splitter → reference/delay coax → phase detector |
| `[7]` | sample & hold | FPGA S/H timing → ADG1211 + 100 pF → shift/scale op-amp |
| `[8]` | TX RF chain | TX mixer → image-reject HPF → PA → antenna |
| `[9]` | VCO + keying | VCO, FPGA Morse sequencer, ADG901 keying switch |

The **TEST SEL** blocks are how single blocks get isolated. When `TEST` equals their `N1`/`N2`, they replace the upstream signal with an ideal stimulus from box `[0]`; otherwise they pass the real signal through.

| TEST | exercises | nets to plot |
|---|---|---|
| 0 | **full system**: pulse → detect → sample f → hold → VCO → Morse TX | `rf_ant env det lim_out pd_out sh_hold vtune vco_f_GHz key tx_out` |
| 1 | limiter + LNA, CW power ramp −60 → +20 dBm | `rf_ant rf_lim rf_lna` |
| 2 | LO chain levels | `lo_pll lo_buf lo_rx lo_tx` |
| 3 | RX down-conversion (use View → FFT) | `rf_lna if_mix if_amp` |
| 4 | envelope detector / DAC / comparator | `if_split_in env vth det_raw` |
| 5 | limiting amp, IF power ramp | `lim_in lim_out` |
| 6 | discriminator, IF staircase 1.00–1.20 GHz (**calibration**) | `pd_rf pd_lo pd_out` |
| 7 | S&H + op-amp settling | `sh_in sh_ctrl sh_hold vtune_opa` |
| 8 | VCO tuning | `vtune vco_f_GHz if_vco` |
| 9 | TX chain + Morse keying | `key if_keyed tx_mix tx_filt tx_out` |
| 10 | RX→TX frequency transfer; add `.step param F_RADAR list 9.3e9 9.4e9 9.5e9` | `vco_f_GHz` |

Every part value is a `.param` in the PARAMETERS box, with a comment saying where it came from. Values marked *check* or *assumed* are my guesses: PLL output power, the buffer, IF-amp and PA P1dB, ADG1211 R_on, ADA4622 GBW, VCO output power, and mixer isolations. Put in the datasheet numbers.

## Python side (radioconda)

```bash
%USERPROFILE%\radioconda\python.exe run_tests.py
```
```bash
%USERPROFILE%\radioconda\python.exe run_tests.py 6 10 0
```

* `run_tests.py` does exactly what you would do by hand: it copies the `.asc`, sets `TEST`, runs LTspice in batch mode and makes the plots. With no arguments it runs every test, which takes a few minutes; `run_tests.py 6 10 0` runs just those. Output lands in `plots/` (PNGs, `test_summary.json`, `RESULTS.md` with every figure) and `results/` (logs; add `--keep-raw` for waveforms).
* `build_jacon.py` regenerates the `.asc`, `.inc`, symbols and `filters_ac.cir`. **It overwrites `JACON_system.asc`**, so edit parameter values in `PARAMS` inside the script if you plan to regenerate.
* `render_schematic.py` redraws `plots/JACON_schematic_overview.png`.

## Modelling conventions

* A node voltage is the RF amplitude in a 50 Ω system: `P(dBm) = 10·log10(V²/0.1)`. RF inputs are 50 Ω terminated and RF outputs are 50 Ω Thévenin sources, so levels read directly in dBm.
* Amplifiers use a Rapp (p = 3) compression curve set from gain and P1dB. Mixers are a tanh LO switch scaled to the datasheet conversion loss, so drive level matters. Filters are real L/C ladders:
  - 3rd-order Butterworth low-passes
  - a 9th-order 0.5 dB Chebyshev high-pass standing in for the VHF-8400+
* The coax arms are ideal transmission lines plus a matched loss pad. The resistive splitters are real 16.7 Ω star networks.
* **Not modelled:** noise, phase noise, reflections other than the coax, temperature, and RX blanking while transmitting. The VCO curve is a straight line through the drawing's 6 V → 1.0 GHz and 9.5 V → 1.2 GHz points.
* **The Morse dot is 60 ns in the model** so the 9.4 GHz carrier and the Morse fit in one transient; a real racon dot is µs long. The holdoff is 1.6 µs so the ADA4622 can settle first.

## What the model says

| # | finding |
|---|---|
| 1 | The limiter passes **+16.3 dBm** to the LNA, above its **+15 dBm** max input. Keep the ~1.5 dB in-line pad the drawing mentions. |
| 2 | The LO reaches the mixers at **+10.3 dBm** against **+10 dBm** needed, so only **0.3 dB margin**. This depends on the assumed +3 dBm PLL output. |
| 3 | Mixer conversion is −6.6 dB. A −30 dBm echo gives **+7.3 dBm IF** after the IF amp. |
| 4 | With a 15 mV threshold, pulses of −21 dBm and up at the detector are caught (4–5 ns latency); −31 dBm is missed. Set `VTH_DAC` for the −50 dBm distant-radar case. |
| 5 | The limiting amp output is flat (±1 dB, +14.4 dBm) for inputs above **−35 dBm**. That covers the whole echo range after the IF split. |
| 6 | With **4.5" at VF 0.70**, the phase-detector curve is monotonic but *not centred*: the calibrated linear map (PD_V0 = −0.337 V, OPA_GAIN = 19.5) is off by up to **±17 MHz**. |
| 7 | The S&H captures the level within its 40 ns window. **An ADA4622-class op-amp (8 MHz GBW) at gain ≈ 19 takes about 760 ns to settle the tune voltage to 1 MHz**; a 100 MHz GBW op-amp takes about 90 ns. |
| 8 | VCO: 1.000 GHz at 6 V and 1.200 GHz at 9.5 V, as modelled. |
| 9 | The image-reject HPF leaves the **7.2 GHz image at −23 dBc**. **8.3 GHz LO leakage sits at −17 dBc**, because it falls inside the HPF passband and the PA amplifies it. Morse on/off ratio is 40 dB, but in the gaps the output is still LO leakage. A band-pass or notch at 8.3 GHz, or better mixer LO isolation, is needed. |
| 10 | **RX→TX frequency transfer** after one pulse through the whole analog path (limiter → delay line → PD → S&H → op-amp → VCO → up-mixer), each length calibrated with TEST 6, radar at 9.30–9.50 GHz. With **4.5"** the TX frequency is off by **+7 to +27 MHz**; with **5.63"**, **−1.7 to +5.6 MHz**; with **1.88"**, **−0.4 to +4.7 MHz**. |
| 0 | **Full chain**, −30 dBm pulse at 9.400 GHz. Detection at 23 ns. PD sampled at −0.329 V and held. The tune voltage starts pinned at the 11.5 V rail, because the hold cap starts at 0 V, and the ADA4622 slews it down to 7.94 V over ~1.5 µs. Morse `. - .` then goes out at **9.4094 GHz (+9.4 MHz error), +26.5 dBm**, with +5 dBm of 8.3 GHz LO leak between elements. |
