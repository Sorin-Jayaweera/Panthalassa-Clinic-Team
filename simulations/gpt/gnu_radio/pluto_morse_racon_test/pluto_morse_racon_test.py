#!/usr/bin/env python3
"""GNU Radio Pluto TX flowgraph for JACON IF/VCO testing.

This transmits a keyed complex tone at the ADALM-Pluto RF center frequency. Use
it to drive the 1.0-1.2 GHz IF/VCO/upconverter test point, not direct 9.8 GHz TX.
"""

import math
import time

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr

try:
    from gnuradio import iio
except ImportError as exc:
    raise SystemExit(
        "GNU Radio gr-iio is required for Pluto. Install gnuradio-iio / libiio."
    ) from exc


class PlutoMorseRaconTx(gr.top_block):
    def __init__(
        self,
        uri="ip:192.168.2.1",
        center_freq=1.1e9,
        samp_rate=2e6,
        tone_offset=100e3,
        tx_atten_db=40,
        amplitude=0.25,
        wpm=18,
    ):
        gr.top_block.__init__(self, "Pluto Morse RACON IF Test")

        dot = 1.2 / float(wpm)
        dash = 3 * dot
        gap = dot
        sequence = [
            (1, dot), (0, gap),
            (1, dash), (0, gap),
            (1, dot), (0, 7 * dot),
        ]

        samples = []
        for state, seconds in sequence:
            samples.extend([amplitude * state] * max(1, int(seconds * samp_rate)))

        self.key = blocks.vector_source_f(samples, True)
        self.tone = analog.sig_source_c(
            samp_rate, analog.GR_COS_WAVE, tone_offset, 1.0, 0.0
        )
        self.key_complex = blocks.float_to_complex(1)
        self.multiply = blocks.multiply_cc()

        self.sink = iio.fmcomms2_sink_fc32(uri, [True, True], 32768, False)
        self.sink.set_len_tag_key("")
        self.sink.set_frequency(int(center_freq))
        self.sink.set_samplerate(int(samp_rate))
        self.sink.set_bandwidth(int(samp_rate))
        self.sink.set_attenuation(0, float(tx_atten_db))
        self.sink.set_filter_params("Auto", "", 0, 0)

        zero = analog.sig_source_f(samp_rate, analog.GR_CONST_WAVE, 0, 0, 0)

        self.connect(self.key, (self.key_complex, 0))
        self.connect(zero, (self.key_complex, 1))
        self.connect(self.tone, (self.multiply, 0))
        self.connect(self.key_complex, (self.multiply, 1))
        self.connect(self.multiply, self.sink)


def main():
    tb = PlutoMorseRaconTx()
    tb.start()
    print("Transmitting keyed '. - .' IF test tone. Press Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    tb.stop()
    tb.wait()


if __name__ == "__main__":
    main()
