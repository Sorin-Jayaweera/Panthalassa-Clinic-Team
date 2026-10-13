"""What the Pluto is putting out, from the measured tables.

    from pluto_level import pluto_dbm, pluto_setting
    pluto_dbm(1100e6, att_db=31)              # -> output in dBm at the Pluto's TX connector
    pluto_setting(1100e6, want_dbm=-40)       # -> attenuation setting that gives that level

Source: pluto_characterization/pluto_if_band_table.csv, measured 12 Oct 2026 with the Pluto TX straight into the
Siglent SSA3021X. 1000 to 1200 MHz in 1 MHz steps, attenuation 0 to 40 dB in 2 dB steps, tone scale 0.5, Pluto warm.

How good the number is:
  - same day, same cable: about 0.1 dB
  - after unplugging the Pluto or moving the cable: about 0.5 dB inside 1000-1200 MHz
  - Pluto just plugged in (first 30 minutes): reads about 0.1 to 0.4 dB higher than the table
  - the table does not include the cable from the Pluto to the part under test
For anything that needs better than 0.5 dB, read the Pluto directly on the analyzer on the day, with the same cable.
"""
import csv
from pathlib import Path

import numpy as np

_TABLE = Path(__file__).resolve().parent.parent / "pluto_characterization" / "pluto_if_band_table.csv"
_rows = list(csv.reader(open(_TABLE)))
_ATT = np.array([float(h.replace("level_dbm_att", "")) for h in _rows[0][1:]])
_F = np.array([float(r[0]) for r in _rows[1:]]) * 1e6
_L = np.array([[float(x) for x in r[1:]] for r in _rows[1:]])          # [frequency, attenuation]


def pluto_dbm(freq_hz, att_db, scale=0.5):
    """Output in dBm for a tone at freq_hz with this attenuation setting and tone scale."""
    if not _F[0] <= freq_hz <= _F[-1]:
        raise ValueError(f"table covers {_F[0]/1e6:.0f} to {_F[-1]/1e6:.0f} MHz; for other frequencies see pluto_map_table.csv")
    if not 0 <= att_db <= 89.75:
        raise ValueError("attenuation setting is 0 to 89.75 dB")
    if not 0 < scale <= 1:
        raise ValueError("tone scale is above 0, up to 1")
    col = np.array([np.interp(freq_hz, _F, _L[:, j]) for j in range(len(_ATT))])
    if att_db <= _ATT[-1]:
        level = float(np.interp(att_db, _ATT, col))
    else:
        level = float(col[-1] - (att_db - _ATT[-1]))                    # measured: 1 dB per dB within 0.6 dB from 40 to 89.75 dB
    level += 20 * np.log10(scale / 0.5)
    if scale > 0.5 and att_db < 10:
        # the output stage compresses at high level: 0.35 to 1.0 dB short at scale 1.0 and 0 dB attenuation
        level -= 0.7 * (scale - 0.5) / 0.5 * (10 - att_db) / 10
    return level


def pluto_setting(freq_hz, want_dbm, scale=0.5):
    """Attenuation setting (a multiple of 0.25 dB) that gives the level closest to want_dbm."""
    atts = np.arange(0, 89.76, 0.25)
    levels = np.array([pluto_dbm(freq_hz, a, scale) for a in atts])
    return float(atts[int(np.argmin(np.abs(levels - want_dbm)))])


if __name__ == "__main__":
    for f in (1000e6, 1100e6, 1150e6, 1200e6):
        print(f"{f/1e6:.0f} MHz: 0 dB {pluto_dbm(f, 0):+.2f} dBm, 31 dB {pluto_dbm(f, 31):+.2f} dBm, 60 dB {pluto_dbm(f, 60):+.2f} dBm; for -40 dBm set {pluto_setting(f, -40)} dB")
