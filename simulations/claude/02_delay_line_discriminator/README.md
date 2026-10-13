# 02 – Delay-line frequency discriminator, 1.0–1.2 GHz (stand-alone)

The bench version of the JACON frequency-measurement section:

```
tone 1.0–1.2 GHz ─ feed cable ─ resistive 2-way splitter ─┬─ arm A: L_REF ──────── mixer RF ┐
                                                           └─ arm B: L_REF + DL_IN ─ mixer LO ┘─ LPF ─ Vout
A·B = (ab/2)[cos(2πfΔt) + cos(2π·2f·t + …)]   →   the LPF removes the 2f sum (f0+f1); f0−f1 = 0 is DC
Vout = K·cos(2πfΔt),   Δt = DL_IN·0.0254 / (VF·c)
```

| file | what it is |
|---|---|
| `delay_line_discriminator.cir` | LTspice deck. Open it in LTspice and press Run. Every section is labelled `[1]`–`[6]`, and all knobs are `.param`s at the top |
| `plot_discriminator.py` | runs the deck in 4 variants and makes all plots (`%USERPROFILE%\radioconda\python.exe plot_discriminator.py`) |
| `plots/` | PNGs + `results_summary.json` |
| `runs/` | the generated variant decks and logs |

Parameters worth changing:

| parameter | what it sets |
|---|---|
| `DL_IN` | extra length of the delayed arm, in inches |
| `VF` | cable velocity factor |
| `P_DBM` | tone power into the splitter |
| `MIXMODE` | `0` = ideal multiplier, `1` = double-balanced mixer model |
| `CL_DB` | mixer conversion loss |
| `F_LPF` | low-pass corner after the mixer |

The frequency sweep is the `.step param FREQ` line at the bottom.

## Plots

1. `01_sweep_sim_vs_theory.png`: LTspice DC output vs frequency, overlaid on `K cos(2πfΔt)`. It agrees to within 0.1 mV (ideal multiplier) and 0.4 mV (mixer model). The bottom panel is normalised to show which lengths are centred on 1.1 GHz.
2. `02_time_domain_1p1GHz.png`: the two arms, the raw product and the filtered DC at 1.1 GHz.
3. `03_spectrum_mixer_product.png`: DC plus 2f = 2.2 GHz before the low-pass, only DC after.
4. `04_design_map_cable_length.png`: phase at 1.1 GHz vs extra length for several velocity factors, and worst-case slope across the band.
5. `05_frequency_recovery_error.png`: the frequency recovered from Vout, using an exact arccos inverse (digital) and a best straight line (the analog S&H → op-amp → VCO path).

## Results at VF = 0.70

| extra length | Δt | phase 1.0 / 1.1 / 1.2 GHz | straight-line recovery error |
|---|---|---|---|
| **4.50" (as specified)** | 545 ps | 196° / 216° / 235° | **±17 MHz** |
| 5.63" | 682 ps | 245° / **270°** / 295° | ±1.1 MHz |
| 1.88" | 227 ps | 82° / **90°** / 98° | ±0.16 MHz (but 3× less slope) |

**4.5" does not put 1.1 GHz on the quadrature (cos = 0) point unless VF ≈ 0.56.** The response is still monotonic over 1.0–1.2 GHz, but it is curved and shallow near 1.0 GHz. To centre it on 1.1 GHz, pick 5.63" (steeper) or 1.88" (more linear), or measure your cable's actual VF first (see `../03_gnuradio_pluto`). At VF ≈ 0.84 (foam dielectric), 4.5" lands almost exactly on 180°, where the slope is zero. That is the worst case.
