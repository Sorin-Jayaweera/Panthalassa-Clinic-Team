"""
make_simple_flowgraph.py - writes pluto_simple_tx.grc

    Constant Source ──► PlutoSDR Sink        (TX: carrier at freq, power slider)
                    ├─► QT Freq Sink  "TX baseband"
                    └─► QT Time Sink  "TX baseband"
    PlutoSDR Source ──► QT Freq Sink  "RX"   (RX LO = freq - rx_offset so the tone
                    └─► QT Time Sink  "RX"    lands at +rx_offset, away from RX DC removal)

    %USERPROFILE%\\radioconda\\python.exe make_simple_flowgraph.py
"""
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def states(x, y):
    return {"bus_sink": False, "bus_source": False, "bus_structure": None,
            "coordinate": [x, y], "rotation": 0, "state": "enabled"}


def blk(name, id_, params, x, y, stream=True):
    p = {k: str(v) for k, v in params.items()}
    p.setdefault("alias", "")
    p.setdefault("comment", "")
    if stream:
        p.setdefault("affinity", "")
        p.setdefault("maxoutbuf", "0")
        p.setdefault("minoutbuf", "0")
    return {"name": name, "id": id_, "parameters": p, "states": states(x, y)}


def rng(name, label, value, start, stop, step, hint, x, y, comment=""):
    return blk(name, "variable_qtgui_range",
               {"label": label, "rangeType": "float", "value": value, "start": start, "stop": stop,
                "step": step, "widget": "counter_slider", "orient": "QtCore.Qt.Horizontal",
                "min_len": "200", "gui_hint": hint, "comment": comment}, x, y, stream=False)


def var(name, value, x, y, comment=""):
    return blk(name, "variable", {"value": value, "comment": comment}, x, y, stream=False)


COLORS = ["blue", "red", "green", "black", "cyan", "magenta", "yellow", "dark red", "dark green", "dark blue"]


def freq_sink(name, title, fc, hint, x, y):
    p = {"type": "complex", "name": f'"{title}"', "fftsize": "4096", "freqhalf": "True",
         "wintype": "window.WIN_BLACKMAN_hARRIS", "norm_window": "False", "fc": fc, "bw": "samp_rate",
         "grid": "True", "autoscale": "False", "average": "0.2", "ymin": "-140", "ymax": "10",
         "label": "Relative Gain", "units": "dB", "nconnections": "1", "update_time": "0.20",
         "showports": "False", "gui_hint": hint, "tr_mode": "qtgui.TRIG_MODE_FREE", "tr_level": "0.0",
         "tr_chan": "0", "tr_tag": '""', "ctrlpanel": "True", "legend": "True", "axislabels": "True"}
    for i in range(1, 11):
        p.update({f"label{i}": '""', f"width{i}": "1", f"color{i}": COLORS[i - 1], f"alpha{i}": "1.0"})
    return blk(name, "qtgui_freq_sink_x", p, x, y)


def time_sink(name, title, hint, x, y):
    p = {"type": "complex", "name": f'"{title}"', "size": "256", "srate": "samp_rate", "grid": "True",
         "autoscale": "True", "ylabel": "Amplitude", "yunit": '""', "ymin": "-1", "ymax": "1",
         "nconnections": "1", "update_time": "0.20", "entags": "False", "gui_hint": hint,
         "tr_mode": "qtgui.TRIG_MODE_FREE", "tr_slope": "qtgui.TRIG_SLOPE_POS", "tr_level": "0.0",
         "tr_delay": "0", "tr_chan": "0", "tr_tag": '""', "stemplot": "False", "ctrlpanel": "True",
         "legend": "True", "axislabels": "True"}
    labels = ["I (real)", "Q (imag)"] + ["Signal %d" % i for i in range(3, 11)]
    for i in range(1, 11):
        p.update({f"label{i}": labels[i - 1], f"width{i}": "1", f"color{i}": COLORS[i - 1], f"alpha{i}": "1.0",
                  f"style{i}": "1", f"marker{i}": "-1"})
    return blk(name, "qtgui_time_sink_x", p, x, y)


def build():
    return {
        "options": {
            "parameters": {
                "author": "JACON clinic team", "catch_exceptions": "True", "category": "[GRC Hier Blocks]",
                "cmake_opt": "", "comment": "", "copyright": "",
                "description": "Pluto CW transmitter (frequency + power) with RX monitor and TX/RX time + frequency plots",
                "gen_cmake": "On", "gen_linking": "dynamic", "generate_options": "qt_gui",
                "hier_block_src_path": ".:", "id": "pluto_simple_tx", "max_nouts": "0",
                "output_language": "python", "placement": "(0,0)", "qt_qss_theme": "", "realtime_scheduling": "",
                "run": "True", "run_command": "{python} -u {filename}", "run_options": "prompt",
                "sizing_mode": "fixed", "thread_safe_setters": "", "title": "Pluto simple CW TX + RX monitor",
                "window_size": "(1400,1000)"},
            "states": states(8, 8),
        },
        "blocks": [
            # ---- controls
            rng("freq", "TX frequency (Hz)", "1.2e9", "325e6", "3.8e9", "1e6", "0,0,1,2", 224, 8),
            rng("p_dbm", "TX power (dBm, approx - calibrate p_max_dbm)", "p_max_dbm - 10", "p_max_dbm - 89.75",
                "p_max_dbm", "0.25", "1,0,1,1", 424, 8, "requested output power; only as accurate as p_max_dbm"),
            rng("rx_gain", "RX gain (dB, manual)", "20", "0", "73", "1", "1,1,1,1", 624, 8),
            var("p_max_dbm", "5.0", 824, 8,
                "CALIBRATE: power measured at 0 dB attenuation at your frequency (Pluto ~0..+7 dBm, frequency dependent)"),
            var("pluto_uri", "'ip:192.168.2.1'", 624, 88,
                "network address over the Pluto's USB-Ethernet gadget; lets TX and RX blocks share one Pluto"),
            var("samp_rate", "600e3", 824, 88,
                "BASEBAND rate: plots cover freq +/- samp_rate/2. The Pluto does the GHz mixing, so this is NOT 2x the RF"),
            var("tone_offset", "50e3", 960, 88,
                "baseband sine frequency (keep << samp_rate/2); Pluto LO = freq - tone_offset so the RF tone lands exactly on freq. Do NOT put the RF frequency here"),
            # ---- TX
            blk("analog_sig_source_x_0", "analog_sig_source_x",
                {"type": "complex", "waveform": "analog.GR_COS_WAVE", "samp_rate": "samp_rate",
                 "freq": "tone_offset", "amp": "0.7", "offset": "0", "phase": "0", "showports": "False",
                 "comment": "complex sine at +tone_offset -> single RF tone at freq"}, 16, 240),
            blk("iio_pluto_sink_0", "iio_pluto_sink",
                {"type": "fc32", "uri": "pluto_uri","frequency": "int(freq - tone_offset)", "samplerate": "int(samp_rate)",
                 "buffer_size": "32768", "cyclic": "False",
                 "attenuation1": "min(89.75, max(0.0, p_max_dbm - p_dbm))", "len_tag_key": "",
                 "filter_source": "'Auto'", "filter": "", "fpass": "0", "fstop": "0", "bandwidth": "20000000",
                 "comment": "attenuation = p_max_dbm - p_dbm"}, 320, 200),
            freq_sink("qtgui_freq_sink_tx", "TX baseband -> Pluto (spectrum, RF axis)", "freq - tone_offset", "2,0,1,1", 320, 330),
            time_sink("qtgui_time_sink_tx", "TX baseband -> Pluto (I/Q vs time)", "2,1,1,1", 320, 440),
            # ---- RX
            blk("iio_pluto_source_0", "iio_pluto_source",
                {"type": "fc32", "uri": "pluto_uri","frequency": "int(freq - tone_offset)", "samplerate": "int(samp_rate)",
                 "buffer_size": "32768", "quadrature": "True", "rfdc": "True", "bbdc": "True",
                 "gain1": "'manual'", "manual_gain1": "rx_gain", "len_tag_key": "", "filter_source": "'Auto'",
                 "filter": "", "fpass": "0", "fstop": "0", "bandwidth": "20000000",
                 "comment": "loop TX -> attenuator (>=30 dB) -> RX to see the real output"}, 16, 580),
            freq_sink("qtgui_freq_sink_rx", "RX (spectrum, RF axis)", "freq - tone_offset", "3,0,1,1", 320, 580),
            time_sink("qtgui_time_sink_rx", "RX (I/Q vs time)", "3,1,1,1", 320, 690),
        ],
        "connections": [
            ["analog_sig_source_x_0", "0", "iio_pluto_sink_0", "0"],
            ["analog_sig_source_x_0", "0", "qtgui_freq_sink_tx", "0"],
            ["analog_sig_source_x_0", "0", "qtgui_time_sink_tx", "0"],
            ["iio_pluto_source_0", "0", "qtgui_freq_sink_rx", "0"],
            ["iio_pluto_source_0", "0", "qtgui_time_sink_rx", "0"],
        ],
        "metadata": {"file_format": 1, "grc_version": "3.10.12.0"},
    }


if __name__ == "__main__":
    out = HERE / "pluto_simple_tx.grc"
    out.write_text(yaml.safe_dump(build(), sort_keys=False, width=4096))
    print("wrote", out)
