# 03 – GNU Radio / ADALM-Pluto bench test of the delay-line discriminator

Drive the physical **splitter → two cables (one 4.5" longer) → mixer → low-pass** network
with a 1.0–1.2 GHz tone from a Pluto. Log the mixer DC output, then compare it with the
LTspice model in `../02_delay_line_discriminator` to see how well the transmitted frequency
can be recovered.

| file | what it is |
|---|---|
| `jacon_pluto_discriminator_tx.grc` | GNU Radio Companion 3.10 flowgraph (QT GUI) that drives the Pluto TX |
| `make_flowgraph.py` | regenerates the `.grc`; edit this rather than the YAML |
| `pluto_sweep_cli.py` | no-GUI frequency stepper. With `--manual` it asks you for the meter reading at every step and writes `measurements/meas_*.csv` |
| `compare_sim_vs_measured.py` | fits the measured curve, overlays LTspice, plots frequency-recovery error |
| `measurements/example_SYNTHETIC_measurement*` | **fake data** made with `--make-example`, only to show the output format. Delete it once you have real data |

Run everything with radioconda's Python / GRC (it already has gr-iio):

```bash
%USERPROFILE%\radioconda\Scripts\gnuradio-companion.exe jacon_pluto_discriminator_tx.grc
```
```bash
%USERPROFILE%\radioconda\python.exe pluto_sweep_cli.py --manual --note "arm A 6in, arm B 10.5in RG316"
```
```bash
%USERPROFILE%\radioconda\python.exe compare_sim_vs_measured.py measurements\meas_YYYYMMDD_HHMMSS.csv --dl-in 4.5 --vf 0.70
```

## Flowgraph

```
Signal Source (complex, +tone_offset) ─┐
                                        ├─ Multiply ─┬─ PlutoSDR Sink  (LO = f_tx − tone_offset)
Vector Source (pulse gate) ─ ×k ─ +c ──┘             └─ QT Freq Sink
Python Snippet thread: stepped sweep + CSV log (tx_log_*.csv)
```

* **Mode 0 – Manual CW.** The slider sets the RF frequency (1.000–1.200 GHz, 1 MHz steps).
* **Mode 1 – Auto sweep.** Steps `sweep_start`→`sweep_stop` by `sweep_step`, holding each for `dwell_s` seconds, and loops. Every step is time-stamped in `tx_log_*.csv` next to the generated `.py`, so you can line up a scope/DAQ recording.
* **Mode 2 – Pulsed CW.** A 1 ms-on / 10 ms-period gate as a stand-in for radar pulses. The Pluto cannot make ns–µs radar pulses, so use this for the detector/comparator path, not for timing.
* The tone sits 200 kHz above the Pluto LO, so LO leakage and the I/Q image land 200/400 kHz away. For the discriminator this changes nothing, because all of them produce the same `cos(2πfΔt)` term to within 0.04°.
* `uri` is blank, which picks the first USB Pluto. Put `ip:192.168.2.1` in the sink block if needed.

## Bench setup

```
Pluto TX ─[pad]─ IF amp ─ ZFRSC-42-S+ ─┬─ arm A: L_REF ─────────── RF ┐
           (ZX60-P162LN+)  resistive   │                               ZX05-30W-S+ IF ─ LPF (DC–~2 MHz) ─ 50 Ω ─ DMM / scope (DC)
                           splitter    └─ arm B: L_REF + 4.5" ───── LO ┘
```

Level budget (check each part's datasheet max input before connecting):

* ZX05-30W-S+ is a **Level 7** mixer, so the LO port wants about **+7 dBm**. After the 6 dB resistive split and some cable loss, the splitter input needs about +13…+14 dBm.
* The Pluto alone only gives a few dBm at 1 GHz, so the IF amp (+22.5 dB) is needed. Use Pluto attenuation or a pad to set the level, and measure it with a power meter or spectrum analyser first.
* The RF port sees the same level; that's fine for a phase detector.
* Use a DC-coupled low-pass on the mixer IF port to kill the 2.0–2.4 GHz sum term. Any DC–few-MHz 50 Ω low-pass works, or simply a scope with a 20 MHz bandwidth limit, 50 Ω input and averaging.

⚠️ **Keep it conducted: cables, attenuators and terminations only, no antennas.** 1.0–1.2 GHz overlaps GNSS L5/E5 (1176 MHz) and aeronautical radionavigation.

## Suggested procedure

1. **Offset.** Feed the LO port only (RF port 50 Ω terminated) and read the DC output. That is the mixer offset `b`.
2. **Amplitude reference.** Make both arms the *same* length, so Δt = 0 and cos = 1. The DC output then equals the full-scale `K` for this drive level.
3. **Design sweep.** Put the 4.5" longer cable back. Run `pluto_sweep_cli.py --manual` from 1.0 to 1.2 GHz in 5 MHz steps.
4. **Wide calibration sweep.** Run `--start 0.5e9 --stop 3e9 --step 25e6` (the splitter and mixer cover this range). You'll see about 1.4 full fringes, which pins down Δt, and therefore your cable's real velocity factor, far better than a 200 MHz sweep can.
5. `compare_sim_vs_measured.py` fits `V = a·cos(2πfΔt) + b`. It reports Δt, effective VF, and residuals against the LTspice curve. It also reports recovery error for three inverses: the calibrated curve, the uncalibrated datasheet curve, and a straight line (which is what the analog S&H → op-amp → VCO path does).

## What the simulation predicts (4.5" extra, VF 0.70)

* Δt = 545 ps, so the phase runs from 196° (1.0 GHz) through 216° (1.1 GHz) to 235° (1.2 GHz).
* That puts the output at about −0.96·K … −0.58·K, not centred on zero. The steepest, most linear point (270°) falls at **1.37 GHz**, and the fringe period is 1/Δt = 1.84 GHz.
* To centre quadrature on 1.1 GHz at VF 0.70, use **5.63"** (270°, steeper) or **1.88"** (90°, more linear, less sensitive).
* The effective VF of your actual cable (connectors and adapters add delay) is exactly what step 4 measures. Feed it back into `DL_IN`/`VF` in the LTspice decks.

To make the LTspice model match your bench, edit `../02_delay_line_discriminator/delay_line_discriminator.cir`:

| parameter | set it to |
|---|---|
| `P_DBM` | power at the splitter input |
| `DL_IN`, `VF` | your extra length and the measured velocity factor |
| `MIXMODE` | `1` (real mixer) |
| `CL_DB` | the mixer's conversion loss |

Then re-run `plot_discriminator.py`.
