"""
make_flowgraph.py - writes jacon_pluto_discriminator_tx.grc (GNU Radio 3.10).

    %USERPROFILE%\\radioconda\\python.exe make_flowgraph.py

Flowgraph: complex tone at +tone_offset -> x (1 or pulse gate) -> PlutoSDR Sink
           LO = f_tx - tone_offset   =>  RF out = f_tx
GUI: TX frequency slider, attenuation slider, mode chooser
     (0 manual CW / 1 automatic stepped sweep / 2 pulsed CW), freq label,
     baseband spectrum. A Python Snippet thread does the sweep and writes a
     CSV log (tx_log_YYYYmmdd_HHMMSS.csv) next to the generated .py.
"""
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

SNIPPET = r'''import threading, time, csv, os, datetime

def _jacon_worker(tb):
    try:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        log_dir = os.getcwd()
    fname = os.path.join(log_dir, "tx_log_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")
    print("[JACON] logging TX settings to", fname, flush=True)
    with open(fname, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["unix_time_s", "mode", "tx_freq_hz", "pluto_lo_hz", "atten_db", "sweep_step_index"])
        last = None
        idx = 0
        while True:
            if tb.mode == 1:
                n = int(round((tb.sweep_stop - tb.sweep_start) / tb.sweep_step)) + 1
                k = idx % n
                f = tb.sweep_start + k * tb.sweep_step
                tb.set_f_tx(f)
                w.writerow(["%.3f" % time.time(), 1, "%.0f" % f, "%.0f" % (f - tb.tone_offset), tb.atten, k])
                fh.flush()
                print("[JACON] sweep step %d/%d  %.3f MHz  (dwell %.1f s)" % (k + 1, n, f / 1e6, tb.dwell_s), flush=True)
                idx += 1
                time.sleep(tb.dwell_s)
            else:
                idx = 0
                if tb.f_tx != tb.f_manual:
                    tb.set_f_tx(tb.f_manual)
                state = (tb.mode, tb.f_tx, tb.atten)
                if state != last:
                    w.writerow(["%.3f" % time.time(), tb.mode, "%.0f" % tb.f_tx, "%.0f" % (tb.f_tx - tb.tone_offset), tb.atten, ""])
                    fh.flush()
                    last = state
                time.sleep(0.2)

self._jacon_thread = threading.Thread(target=_jacon_worker, args=(self,), daemon=True)
self._jacon_thread.start()'''


def states(x, y, state="enabled"):
    return {"bus_sink": False, "bus_source": False, "bus_structure": None,
            "coordinate": [x, y], "rotation": 0, "state": state}


def blk(name, id_, params, x, y, stream=False):
    p = {k: str(v) for k, v in params.items()}
    if stream:
        for k in ("affinity", "alias", "comment", "maxoutbuf", "minoutbuf"):
            p.setdefault(k, "0" if k.endswith("buf") else "")
    else:
        p.setdefault("alias", "")
        p.setdefault("comment", "")
    return {"name": name, "id": id_, "parameters": p, "states": states(x, y)}


def var(name, value, x, y, comment=""):
    return blk(name, "variable", {"value": value, "comment": comment}, x, y)


def freq_sink_params():
    p = {"type": "complex", "name": '"Baseband sent to Pluto (0 Hz = Pluto LO, tone sits at +tone_offset)"',
         "fftsize": "2048", "freqhalf": "True", "wintype": "window.WIN_BLACKMAN_hARRIS", "norm_window": "False",
         "fc": "0", "bw": "samp_rate", "grid": "True", "autoscale": "False", "average": "1.0",
         "ymin": "-140", "ymax": "10", "label": "Relative Gain", "units": "dB", "nconnections": "1",
         "update_time": "0.10", "showports": "False", "gui_hint": "3,0,1,2", "tr_mode": "qtgui.TRIG_MODE_FREE",
         "tr_level": "0.0", "tr_chan": "0", "tr_tag": '""', "ctrlpanel": "False", "legend": "True",
         "axislabels": "True"}
    colors = ["blue", "red", "green", "black", "cyan", "magenta", "yellow", "dark red", "dark green", "dark blue"]
    for i in range(1, 11):
        p[f"label{i}"] = '""'
        p[f"width{i}"] = "1"
        p[f"color{i}"] = colors[i - 1]
        p[f"alpha{i}"] = "1.0"
    return p


def build():
    fg = {
        "options": {
            "parameters": {
                "author": "JACON clinic team", "catch_exceptions": "True", "category": "[GRC Hier Blocks]",
                "cmake_opt": "", "comment": "", "copyright": "",
                "description": "PlutoSDR TX source for bench-testing the JACON delay-line frequency discriminator (1.0-1.2 GHz)",
                "gen_cmake": "On", "gen_linking": "dynamic", "generate_options": "qt_gui",
                "hier_block_src_path": ".:", "id": "jacon_pluto_discriminator_tx", "max_nouts": "0",
                "output_language": "python", "placement": "(0,0)", "qt_qss_theme": "", "realtime_scheduling": "",
                "run": "True", "run_command": "{python} -u {filename}", "run_options": "prompt",
                "sizing_mode": "fixed", "thread_safe_setters": "",
                "title": "JACON - Pluto TX for the delay-line discriminator test", "window_size": "(1000,1000)",
            },
            "states": states(8, 8),
        },
        "blocks": [
            # ---------------- variables
            var("samp_rate", "2.5e6", 250, 8, "Pluto baseband rate (keep >= 2.084 MSPS)"),
            var("tone_offset", "200e3", 360, 8, "tone sits this far above the Pluto LO (keeps LO leakage off the wanted tone)"),
            var("amp", "0.9", 480, 8, "digital amplitude (<1)"),
            var("f_tx", "f_manual", 580, 8, "actual RF frequency; the sweep thread overrides it in mode 1"),
            var("sweep_start", "1.0e9", 250, 96, "mode 1 sweep start (Hz)"),
            var("sweep_stop", "1.2e9", 370, 96, "mode 1 sweep stop (Hz)"),
            var("sweep_step", "5e6", 490, 96, "mode 1 sweep step (Hz)"),
            var("dwell_s", "2.0", 610, 96, "mode 1 dwell per step (s) - long enough to read your meter/scope"),
            var("pulse_on_ms", "1.0", 730, 96, "mode 2 pulse width (ms)"),
            var("pulse_period_ms", "10.0", 850, 96, "mode 2 pulse period (ms)"),
            blk("f_manual", "variable_qtgui_range",
                {"label": "TX RF frequency (Hz)", "rangeType": "float", "value": "1.1e9", "start": "1.0e9",
                 "stop": "1.2e9", "step": "1e6", "widget": "counter_slider", "orient": "QtCore.Qt.Horizontal",
                 "min_len": "200", "gui_hint": "0,0,1,2"}, 8, 180),
            blk("atten", "variable_qtgui_range",
                {"label": "Pluto TX attenuation (dB)", "rangeType": "float", "value": "10", "start": "0",
                 "stop": "89.75", "step": "0.25", "widget": "counter_slider", "orient": "QtCore.Qt.Horizontal",
                 "min_len": "200", "gui_hint": "1,1,1,1"}, 200, 180),
            blk("mode", "variable_qtgui_chooser",
                {"label": "Mode", "type": "int", "num_opts": "3", "value": "0",
                 "option0": "0", "label0": "Manual CW", "option1": "1", "label1": "Auto stepped sweep (CSV log)",
                 "option2": "2", "label2": "Pulsed CW (radar-like gate)", "options": "[0, 1, 2]",
                 "labels": "[]", "gui_hint": "1,0,1,1"}, 400, 180),
            blk("f_label", "variable_qtgui_label",
                {"label": "Transmitting (MHz)", "type": "real", "value": "f_tx/1e6", "formatter": "None",
                 "gui_hint": "2,0,1,2"}, 600, 180),
            # ---------------- signal path
            blk("analog_sig_source_x_0", "analog_sig_source_x",
                {"type": "complex", "waveform": "analog.GR_COS_WAVE", "samp_rate": "samp_rate",
                 "freq": "tone_offset", "amp": "amp", "offset": "0", "phase": "0", "showports": "False"},
                8, 330, stream=True),
            blk("blocks_vector_source_x_0", "blocks_vector_source_x",
                {"type": "complex",
                 "vector": "[1.0+0j]*int(samp_rate*pulse_on_ms/1e3) + [0j]*int(samp_rate*(pulse_period_ms-pulse_on_ms)/1e3)",
                 "tags": "[]", "repeat": "True", "vlen": "1"}, 8, 460, stream=True),
            blk("blocks_multiply_const_vxx_0", "blocks_multiply_const_vxx",
                {"type": "complex", "const": "1.0 if mode == 2 else 0.0", "vlen": "1",
                 "comment": "gate used only in pulsed mode"}, 260, 476, stream=True),
            blk("blocks_add_const_vxx_0", "blocks_add_const_vxx",
                {"type": "complex", "const": "0.0 if mode == 2 else 1.0", "vlen": "1"}, 460, 476, stream=True),
            blk("blocks_multiply_xx_0", "blocks_multiply_xx",
                {"type": "complex", "num_inputs": "2", "vlen": "1"}, 640, 380, stream=True),
            blk("iio_pluto_sink_0", "iio_pluto_sink",
                {"type": "fc32", "uri": "", "frequency": "int(f_tx - tone_offset)", "samplerate": "int(samp_rate)",
                 "buffer_size": "32768", "cyclic": "False", "attenuation1": "atten", "len_tag_key": "",
                 "filter_source": "'Auto'", "filter": "", "fpass": "0", "fstop": "0", "bandwidth": "20000000",
                 "comment": "uri empty = first Pluto on USB; or ip:192.168.2.1"}, 840, 300, stream=True),
            blk("qtgui_freq_sink_x_0", "qtgui_freq_sink_x", freq_sink_params(), 840, 520, stream=True),
            blk("snippet_sweep", "snippet",
                {"section": "main_after_start", "priority": "0", "code": SNIPPET}, 8, 600),
        ],
        "connections": [
            ["analog_sig_source_x_0", "0", "blocks_multiply_xx_0", "0"],
            ["blocks_vector_source_x_0", "0", "blocks_multiply_const_vxx_0", "0"],
            ["blocks_multiply_const_vxx_0", "0", "blocks_add_const_vxx_0", "0"],
            ["blocks_add_const_vxx_0", "0", "blocks_multiply_xx_0", "1"],
            ["blocks_multiply_xx_0", "0", "iio_pluto_sink_0", "0"],
            ["blocks_multiply_xx_0", "0", "qtgui_freq_sink_x_0", "0"],
        ],
        "metadata": {"file_format": 1, "grc_version": "3.10.12.0"},
    }
    return fg


class _Dumper(yaml.SafeDumper):
    pass


def _str_rep(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_rep)

if __name__ == "__main__":
    out = HERE / "jacon_pluto_discriminator_tx.grc"
    out.write_text(yaml.dump(build(), Dumper=_Dumper, sort_keys=False, width=4096, allow_unicode=True))
    print("wrote", out)
