# JACON / RACON LTspice and Pluto SDR Simulations

Generated from `clinic/racon_draft_design01b_drawing.pdf`.

The design target is a RACON-style receive/respond chain:

- Receive a pulsed 9.3-9.5 GHz radar signal.
- Mix against an 8.3 GHz LO to produce a 1.0-1.2 GHz IF.
- Estimate frequency using an IF delay-line phase detector.
- Tune a 1.0-1.2 GHz VCO.
- Mix back up with the same 8.3 GHz LO.
- Filter the 7.1-7.3 GHz image.
- Key a same-frequency `. - .` Morse reply.

## LTspice

Open these files in LTspice:

- `ltspice/jacon_full_system_top.cir`
  - Full behavioral chain with labeled sections matching the drawing.
  - Change `frf`, `rx_dbm`, `td_phase`, and `tx_gain_db` near the top.
  - Probe nodes listed in `.save` to visualize each block.

- `ltspice/if_delay_splitter_1p0_1p2GHz.cir`
  - Focused 1.0-1.2 GHz wire/splitter/cable/multiplier/LPF model.
  - `DELAY_MODE=0` is the requested 4.5 inch extra coax path.
  - `DELAY_MODE=1` is the quadrature-at-1.1 GHz calibration path.

The LTspice files are intentionally behavioral. Replace individual blocks with
vendor S-parameter files as parts are selected.

## Visualizations

`visualizations/` contains generated plots and CSVs:

- `block_flow.svg` - system flow map.
- `spectrum_plan.svg` - receive/LO/IF/TX/image frequency plan.
- `delay_detector_response.svg` - `cos(2*pi*f*delta_t)` for 4.5 in vs quadrature.
- `delay_detector_response.csv` - numeric comparison table.
- `morse_keying.svg` - `. - .` keying envelope.
- `focused_delay_time_domain.svg` - sample cable-end and multiplier waveforms.

## GNU Radio / Pluto

`gnu_radio/pluto_morse_racon_test/` contains a Pluto SDR IF transmit test. Pluto
does not directly transmit 9.8 GHz; use it to drive the 1.0-1.2 GHz IF/VCO test
point or an external upconverter chain.
