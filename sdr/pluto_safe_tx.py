#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Pluto CW TX with output power limit
# Author: JACON clinic team
# Description: Pluto CW transmitter (frequency + power) with RX monitor and TX/RX time + frequency plots
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iio
import sip
import threading



class pluto_safe_tx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Pluto CW TX with output power limit", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Pluto CW TX with output power limit")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pluto_safe_tx")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.p_worst_max_dbm = p_worst_max_dbm = 11.0
        self.p_limit_dbm = p_limit_dbm = -20.0
        self.p_max_dbm = p_max_dbm = 5.0
        self.att_min_db = att_min_db = max(0.0, p_worst_max_dbm - p_limit_dbm)
        self.tone_offset = tone_offset = 50e3
        self.samp_rate = samp_rate = 2.4e6
        self.rx_gain = rx_gain = 20
        self.pluto_uri = pluto_uri = 'ip:192.168.2.1'
        self.p_dbm = p_dbm = p_max_dbm - att_min_db - 10
        self.freq = freq = 1.2e9

        ##################################################
        # Blocks
        ##################################################

        self._rx_gain_range = qtgui.Range(0, 73, 1, 20, 200)
        self._rx_gain_win = qtgui.RangeWidget(self._rx_gain_range, self.set_rx_gain, "RX gain (dB, manual)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._rx_gain_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._p_dbm_range = qtgui.Range(p_max_dbm - 89.75, p_max_dbm - att_min_db, 0.25, p_max_dbm - att_min_db - 10, 200)
        self._p_dbm_win = qtgui.RangeWidget(self._p_dbm_range, self.set_p_dbm, "TX power (dBm, approx). Limited to p_limit_dbm", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._p_dbm_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._freq_range = qtgui.Range(325e6, 3.8e9, 1e6, 1.2e9, 200)
        self._freq_win = qtgui.RangeWidget(self._freq_range, self.set_freq, "TX frequency (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._freq_win, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_tx = qtgui.time_sink_c(
            256, #size
            samp_rate, #samp_rate
            "TX baseband -> Pluto (I/Q vs time)", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_tx.set_update_time(0.20)
        self.qtgui_time_sink_tx.set_y_axis(-1, 1)

        self.qtgui_time_sink_tx.set_y_label('Amplitude', "")

        self.qtgui_time_sink_tx.enable_tags(False)
        self.qtgui_time_sink_tx.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_tx.enable_autoscale(True)
        self.qtgui_time_sink_tx.enable_grid(True)
        self.qtgui_time_sink_tx.enable_axis_labels(True)
        self.qtgui_time_sink_tx.enable_control_panel(True)
        self.qtgui_time_sink_tx.enable_stem_plot(False)


        labels = ['I (real)', 'Q (imag)', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_tx.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_tx.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_tx.set_line_label(i, labels[i])
            self.qtgui_time_sink_tx.set_line_width(i, widths[i])
            self.qtgui_time_sink_tx.set_line_color(i, colors[i])
            self.qtgui_time_sink_tx.set_line_style(i, styles[i])
            self.qtgui_time_sink_tx.set_line_marker(i, markers[i])
            self.qtgui_time_sink_tx.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_tx_win = sip.wrapinstance(self.qtgui_time_sink_tx.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_tx_win, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_rx = qtgui.time_sink_c(
            256, #size
            samp_rate, #samp_rate
            "RX (I/Q vs time)", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_rx.set_update_time(0.20)
        self.qtgui_time_sink_rx.set_y_axis(-1, 1)

        self.qtgui_time_sink_rx.set_y_label('Amplitude', "")

        self.qtgui_time_sink_rx.enable_tags(False)
        self.qtgui_time_sink_rx.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_rx.enable_autoscale(True)
        self.qtgui_time_sink_rx.enable_grid(True)
        self.qtgui_time_sink_rx.enable_axis_labels(True)
        self.qtgui_time_sink_rx.enable_control_panel(True)
        self.qtgui_time_sink_rx.enable_stem_plot(False)


        labels = ['I (real)', 'Q (imag)', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_rx.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_rx.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_rx.set_line_label(i, labels[i])
            self.qtgui_time_sink_rx.set_line_width(i, widths[i])
            self.qtgui_time_sink_rx.set_line_color(i, colors[i])
            self.qtgui_time_sink_rx.set_line_style(i, styles[i])
            self.qtgui_time_sink_rx.set_line_marker(i, markers[i])
            self.qtgui_time_sink_rx.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_rx_win = sip.wrapinstance(self.qtgui_time_sink_rx.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_rx_win, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_freq_sink_tx = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            (freq - tone_offset), #fc
            samp_rate, #bw
            "TX baseband -> Pluto (spectrum, RF axis)", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_tx.set_update_time(0.20)
        self.qtgui_freq_sink_tx.set_y_axis((-140), 10)
        self.qtgui_freq_sink_tx.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_tx.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_tx.enable_autoscale(False)
        self.qtgui_freq_sink_tx.enable_grid(True)
        self.qtgui_freq_sink_tx.set_fft_average(0.2)
        self.qtgui_freq_sink_tx.enable_axis_labels(True)
        self.qtgui_freq_sink_tx.enable_control_panel(True)
        self.qtgui_freq_sink_tx.set_fft_window_normalized(False)



        labels = ["", "", "", "", "",
            "", "", "", "", ""]
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_tx.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_tx.set_line_label(i, labels[i])
            self.qtgui_freq_sink_tx.set_line_width(i, widths[i])
            self.qtgui_freq_sink_tx.set_line_color(i, colors[i])
            self.qtgui_freq_sink_tx.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_tx_win = sip.wrapinstance(self.qtgui_freq_sink_tx.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_tx_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_freq_sink_rx = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            (freq - tone_offset), #fc
            samp_rate, #bw
            "RX (spectrum, RF axis)", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_rx.set_update_time(0.20)
        self.qtgui_freq_sink_rx.set_y_axis((-140), 10)
        self.qtgui_freq_sink_rx.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_rx.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_rx.enable_autoscale(False)
        self.qtgui_freq_sink_rx.enable_grid(True)
        self.qtgui_freq_sink_rx.set_fft_average(0.2)
        self.qtgui_freq_sink_rx.enable_axis_labels(True)
        self.qtgui_freq_sink_rx.enable_control_panel(True)
        self.qtgui_freq_sink_rx.set_fft_window_normalized(False)



        labels = ["", "", "", "", "",
            "", "", "", "", ""]
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_rx.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_rx.set_line_label(i, labels[i])
            self.qtgui_freq_sink_rx.set_line_width(i, widths[i])
            self.qtgui_freq_sink_rx.set_line_color(i, colors[i])
            self.qtgui_freq_sink_rx.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_rx_win = sip.wrapinstance(self.qtgui_freq_sink_rx.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_rx_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32(pluto_uri if pluto_uri else iio.get_pluto_uri(), [True, True], 32768)
        self.iio_pluto_source_0.set_len_tag_key('')
        self.iio_pluto_source_0.set_frequency((int(freq - tone_offset)))
        self.iio_pluto_source_0.set_samplerate(int(samp_rate))
        self.iio_pluto_source_0.set_gain_mode(0, 'manual')
        self.iio_pluto_source_0.set_gain(0, rx_gain)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)
        self.iio_pluto_sink_0 = iio.fmcomms2_sink_fc32(pluto_uri if pluto_uri else iio.get_pluto_uri(), [True, True], 32768, False)
        self.iio_pluto_sink_0.set_len_tag_key('')
        self.iio_pluto_sink_0.set_bandwidth(20000000)
        self.iio_pluto_sink_0.set_frequency((int(freq - tone_offset)))
        self.iio_pluto_sink_0.set_samplerate(int(samp_rate))
        self.iio_pluto_sink_0.set_attenuation(0, min(89.75, max(att_min_db, p_max_dbm - p_dbm)))
        self.iio_pluto_sink_0.set_filter_params('Auto', '', 0, 0)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, tone_offset, 0.7, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.iio_pluto_sink_0, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.qtgui_freq_sink_tx, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.qtgui_time_sink_tx, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.qtgui_freq_sink_rx, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.qtgui_time_sink_rx, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pluto_safe_tx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_p_worst_max_dbm(self):
        return self.p_worst_max_dbm

    def set_p_worst_max_dbm(self, p_worst_max_dbm):
        self.p_worst_max_dbm = p_worst_max_dbm
        self.set_att_min_db(max(0.0, self.p_worst_max_dbm - self.p_limit_dbm))

    def get_p_limit_dbm(self):
        return self.p_limit_dbm

    def set_p_limit_dbm(self, p_limit_dbm):
        self.p_limit_dbm = p_limit_dbm
        self.set_att_min_db(max(0.0, self.p_worst_max_dbm - self.p_limit_dbm))

    def get_p_max_dbm(self):
        return self.p_max_dbm

    def set_p_max_dbm(self, p_max_dbm):
        self.p_max_dbm = p_max_dbm
        self.set_p_dbm(self.p_max_dbm - self.att_min_db - 10)
        self.iio_pluto_sink_0.set_attenuation(0,min(89.75, max(self.att_min_db, self.p_max_dbm - self.p_dbm)))

    def get_att_min_db(self):
        return self.att_min_db

    def set_att_min_db(self, att_min_db):
        self.att_min_db = att_min_db
        self.set_p_dbm(self.p_max_dbm - self.att_min_db - 10)
        self.iio_pluto_sink_0.set_attenuation(0,min(89.75, max(self.att_min_db, self.p_max_dbm - self.p_dbm)))

    def get_tone_offset(self):
        return self.tone_offset

    def set_tone_offset(self, tone_offset):
        self.tone_offset = tone_offset
        self.analog_sig_source_x_0.set_frequency(self.tone_offset)
        self.iio_pluto_sink_0.set_frequency((int(self.freq - self.tone_offset)))
        self.iio_pluto_source_0.set_frequency((int(self.freq - self.tone_offset)))
        self.qtgui_freq_sink_rx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)
        self.qtgui_freq_sink_tx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.iio_pluto_sink_0.set_samplerate(int(self.samp_rate))
        self.iio_pluto_source_0.set_samplerate(int(self.samp_rate))
        self.qtgui_freq_sink_rx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)
        self.qtgui_freq_sink_tx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)
        self.qtgui_time_sink_rx.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_tx.set_samp_rate(self.samp_rate)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.iio_pluto_source_0.set_gain(0, self.rx_gain)

    def get_pluto_uri(self):
        return self.pluto_uri

    def set_pluto_uri(self, pluto_uri):
        self.pluto_uri = pluto_uri

    def get_p_dbm(self):
        return self.p_dbm

    def set_p_dbm(self, p_dbm):
        self.p_dbm = p_dbm
        self.iio_pluto_sink_0.set_attenuation(0,min(89.75, max(self.att_min_db, self.p_max_dbm - self.p_dbm)))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.iio_pluto_sink_0.set_frequency((int(self.freq - self.tone_offset)))
        self.iio_pluto_source_0.set_frequency((int(self.freq - self.tone_offset)))
        self.qtgui_freq_sink_rx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)
        self.qtgui_freq_sink_tx.set_frequency_range((self.freq - self.tone_offset), self.samp_rate)




def main(top_block_cls=pluto_safe_tx, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
