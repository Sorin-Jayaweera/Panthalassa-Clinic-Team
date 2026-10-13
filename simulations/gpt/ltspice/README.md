# LTspice Notes

## Files

- `jacon_full_system_top.cir`
  - Behavioral full chain from RX antenna to keyed TX antenna.
  - Sections are labeled to match the source drawing.
  - Probe the `.save` nodes by block:
    - RX/mixdown: `rx_ant`, `rx_limited`, `rx_lna`, `lo_drive`, `rx_mix_raw`, `if_mixer_out`
    - Triggering: `if_amp_out`, `envelope`, `threshold`, `radar_ping`
    - Frequency recovery: `if_limited`, `delayed_if`, `phase_raw`, `phase_baseband`
    - Retune/TX: `held_phase`, `vco_tune`, `vco_if`, `morse_key`, `tx_filtered`, `tx_ant`

- `if_delay_splitter_1p0_1p2GHz.cir`
  - Focused splitter/cable/multiplier/low-pass simulation.
  - Steps `fin` through 1.0, 1.05, 1.1, 1.15, and 1.2 GHz.
  - Steps `DELAY_MODE`:
    - `0`: physical 4.5 inch longer coax with VF=0.66.
    - `1`: ideal quadrature delay at 1.1 GHz.

- `jacon_common_models.lib`
  - Shared behavioral blocks: gain/limit, multiplier, sample-hold, VCO,
    first-order filters.

## Verified Batch Runs

These were run with LTspice 26.0.2 on Windows.

Focused delay simulation:

- Status: completed.
- Output files: `if_delay_splitter_1p0_1p2GHz.raw`, `if_delay_splitter_1p0_1p2GHz.log`.
- Measurement table is in the `.log`; the physical 4.5 inch case produces a
  negative recovered baseband value around 1.0-1.2 GHz, while the quadrature
  case crosses near zero at 1.1 GHz.

Full behavioral chain:

- Status: completed.
- Output files: `jacon_full_system_top.raw`, `jacon_full_system_top.log`.
- `held_phase_avg = 0.000912958`
- `tune_avg = 8.00548 V`
- `tx_peak_pp = 5.256 V`

## Command Line

```powershell
& 'C:\Users\Sorin\AppData\Local\Programs\ADI\LTspice\LTspice.exe' -b 'C:\ThatFamily Dropbox\Sorin Jayaweera\allSaves\mudd\senior\clinic\simulations\gpt\ltspice\if_delay_splitter_1p0_1p2GHz.cir'
& 'C:\Users\Sorin\AppData\Local\Programs\ADI\LTspice\LTspice.exe' -b 'C:\ThatFamily Dropbox\Sorin Jayaweera\allSaves\mudd\senior\clinic\simulations\gpt\ltspice\jacon_full_system_top.cir'
```
