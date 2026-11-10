"""The bench setup for the racon recordings. EDIT THIS FILE to match what is on the bench before each run.

Everything that turns a level read at the SM200B into a level at our antenna, and then into how loud each source is (EIRP),
comes from here, and the same list draws the wiring strip on every plot. Gains are in dB: loss is negative.
"""
import math

# ---- receive chain, antenna to SM200B, in order. (label for the wiring strip, gain in dB at 9.4 GHz, where the number comes from)
CHAIN = [
    ("Vivaldi R120\nfacing the sources", 0.0, "antenna port is the reference point"),
    ("SMA cable", -1.0, "estimate, about 1 dB at 9.4 GHz; measure on the VNA"),
    ("Marki limiter", -0.8, "VNA, radar_test/vna/limiter_S_params.csv"),
    ("20 dB pad", -20.0, "nominal"),
    ("ZX60-5123LN+ LNA\n6 V", 23.0, "test 27 on 25 Oct, about 23 dB (datasheet about 22)"),
    ("29 dB of pads", -29.0, "nominal; 29 recommended on 9 Nov (39 puts the signals near the SM200B floor and under the direct leak)"),
    ("SM200B\nI/Q, 9.4 GHz", 0.0, "reads dBm at its input"),
]
CHAIN_DATE = "9 Nov 21:35, triangle: radar 40 ft, racon 23 ft, radar-racon 50 ft"

# ---- geometry, metres, measured antenna to antenna
D_RADAR_M = 12.2      # Furuno to our Vivaldi: about 40 ft (9 Nov 21:35 setup)
D_RACON_M = 7.0       # racon to our Vivaldi: about 23 ft (9 Nov 21:35 setup)
D_RADAR_RACON_M = 15.2  # Furuno to racon: about 50 ft (9 Nov 21:35 setup)

# ---- antennas and transmitters
G_RX_DBI = 8.0                    # Vivaldi at 9.4 GHz, assumed, not measured (each dB wrong moves every EIRP by 1 dB the other way)
RADAR_TX_DBM = 63.4               # Furuno 1722C/NT, 2.2 kW peak
RADAR_G_SPEC_DBI = 24.0           # from the 5.2 x 25 deg beam
RADAR_FOAM = "foam: not stated" # say what is on it
RACON_TX_DBM = 30.0               # SeaBeacon 2: 1.0 W to the antenna (datasheet)
RACON_G_SPEC_DBI = 6.0            # SeaBeacon 2 datasheet, 4.0 W ERP
RACON_SENS_DBM = -50.0            # SeaBeacon 2 system sensitivity
RADAR_ROT_S = 2.5885              # measured 25 Oct

# ---- frequencies
CENTER_HZ = 9.4026e9              # Furuno measured at 9402.6-9402.8 MHz
SM_LIMIT_DBM = 20.0
SOURCES = None    # set per recording by setups_9nov.py


def chain_gain_db():
    return sum(g for _, g, _ in CHAIN)


def fspl_db(d_m, f_hz=CENTER_HZ):
    return 20 * math.log10(4 * math.pi * d_m * f_hz / 299_792_458.0)


def stages(extra_source=True):
    """Wiring strip stages: both sources in parallel, then the chain."""
    src = SOURCES if SOURCES else [f"Furuno 1722C/NT radar\n{D_RADAR_M:g} m, {RADAR_FOAM}", f"SeaBeacon 2 racon\n{D_RACON_M:g} m from our antenna"]
    src = src[0] if len(src) == 1 else src
    return [src] + [lab + (f"\n{g:+.1f} dB" if g else "") for lab, g, _ in CHAIN]


def strip_title():
    return f"Wiring, {CHAIN_DATE}: chain gain {chain_gain_db():+.1f} dB antenna port to SM200B; radar to racon {D_RADAR_RACON_M:g} m"
