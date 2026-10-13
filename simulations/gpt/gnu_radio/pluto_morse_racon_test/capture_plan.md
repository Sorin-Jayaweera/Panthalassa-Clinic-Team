# Bench Capture Plan

1. Run the LTspice focused delay simulation:
   `ltspice/if_delay_splitter_1p0_1p2GHz.cir`

2. Record the expected detector sign and magnitude from:
   `visualizations/delay_detector_response.csv`

3. Connect Pluto TX through attenuation to the IF input under test.

4. Set Pluto TX center frequency to the IF frequency being tested:
   1.0, 1.05, 1.1, 1.15, and 1.2 GHz are the default comparison points.

5. Capture the two cable-end signals or the post-multiplier low-pass output with
   an oscilloscope or analyzer. Log:
   - IF frequency
   - cable length difference
   - measured DC/baseband detector value
   - temperature and cable type
   - splitter part number

6. Compare real values against:
   - physical 4.5 inch coax delay
   - quadrature-at-1.1 GHz delay

7. For the full RACON path, keep the Pluto at the IF/VCO point and let the
   external 8.3 GHz LO/mixer generate the 9.3-9.5 GHz output. Verify the TX
   chain is keyed as `. - .` and that the image reject filter suppresses the
   7.1-7.3 GHz image.
