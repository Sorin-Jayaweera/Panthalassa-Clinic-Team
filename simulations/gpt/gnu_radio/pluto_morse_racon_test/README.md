# Pluto SDR RACON IF Test

This folder is for driving the physical IF/VCO/upconverter test chain with an
ADALM-Pluto SDR and comparing real measurements against the LTspice IF delay
detector model.

Important hardware note: Pluto cannot directly transmit 9.8 GHz. Use it at the
1.0-1.2 GHz IF/VCO test point, or feed an external upconverter/mixer chain. The
JACON draft mixes a 1.0-1.2 GHz VCO/IF signal with an 8.3 GHz LO to produce the
9.3-9.5 GHz radar-response band.

Files:

- `pluto_morse_racon_test.py` - runnable GNU Radio Python flowgraph.
- `pluto_morse_racon_test.grc` - GNU Radio Companion starting-point metadata
  mirroring the Python flowgraph variables and block intent.
- `capture_plan.md` - bench-test checklist for comparing measured data with
  the LTspice visualizations.

Default signal:

- Center frequency: 1.1 GHz
- Sample rate: 2 MS/s
- Tone offset: 100 kHz
- Morse key: `. - .`
- Pluto URI: `ip:192.168.2.1`

Start with a high attenuation setting and an external attenuator. Increase power
only after the spectrum analyzer confirms the expected level and frequency.
