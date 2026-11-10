"""The bench setup for every raw recording on 9 Nov 2026 (C:/racon_raw/<folder>), from what was said at the bench.
racon_analyze.py applies the matching entry before analysing, so each plot's wiring strip, chain gain, distances and antenna gain
are the ones that recording was made with.
"""
AFTER_ANT = [("SMA cable", -1.0, "estimate"), ("Marki limiter", -0.8, "VNA"), ("20 dB pad", -20.0, "nominal"),
             ("ZX60-5123LN+ LNA\n6 V", 23.0, "test 27, about 23 dB"), ("29 dB of pads", -29.0, "nominal"), ("SM200B\nI/Q, 50 MS/s, 9408.5 MHz", 0.0, "")]
VIV = ("Vivaldi R120", 0.0, "antenna port is the reference point")
HORN_RADAR = ("horn antenna\naimed at the radar", 0.0, "antenna port is the reference point")
HORN_RACON = ("horn antenna\naimed at the racon", 0.0, "antenna port is the reference point")
HORN_G = 15.0      # ASSUMED: gain of the horn at 9.4 GHz not given yet. Every horn EIRP moves 1 dB per dB this is off.
FAR = dict(D_RADAR_M=15.0, D_RACON_M=18.0, D_RADAR_RACON_M=10.0)
TRI = dict(D_RADAR_M=12.2, D_RACON_M=7.0, D_RADAR_RACON_M=15.2)

SETUPS = {}
for f in ("20261109_211913", "20261109_212012", "20261109_212124"):
    SETUPS[f] = dict(FAR, CHAIN=[VIV] + AFTER_ANT, G_RX_DBI=8.0, LABEL="Vivaldi, radar 15 m, racon about 18 m; racon on but not picked up",
                     SOURCES=["Furuno 1722C/NT radar\n15 m", "SeaBeacon 2 racon\nabout 18 m"], RACON_ON=True)
SETUPS["20261109_213227"] = dict(TRI, CHAIN=[VIV] + AFTER_ANT, G_RX_DBI=8.0, LABEL="Vivaldi, moved closer (triangle), ref 0 dBm: racon faint",
                                 SOURCES=["Furuno 1722C/NT radar\n40 ft (12.2 m)", "SeaBeacon 2 racon\n23 ft (7.0 m)"], RACON_ON=True)
for f in ("20261109_213542", "20261109_213625", "20261109_213716", "20261109_214452"):
    SETUPS[f] = dict(TRI, CHAIN=[VIV] + AFTER_ANT, G_RX_DBI=8.0, LABEL="Vivaldi, triangle: radar 40 ft, racon 23 ft, radar-racon 50 ft; racon on",
                     SOURCES=["Furuno 1722C/NT radar\n40 ft (12.2 m)", "SeaBeacon 2 racon\n23 ft (7.0 m)"], RACON_ON=True)
SETUPS["20261109_215120"] = dict(TRI, CHAIN=[HORN_RADAR] + AFTER_ANT, G_RX_DBI=HORN_G,
                                 LABEL="horn aimed at the radar, racon off; horn turned to the right polarisation partway through",
                                 SOURCES=["Furuno 1722C/NT radar\n40 ft (12.2 m)"], RACON_ON=False)
SETUPS["20261109_215332"] = dict(TRI, CHAIN=[HORN_RADAR] + AFTER_ANT, G_RX_DBI=HORN_G, LABEL="horn aimed at the radar (SMA to the right), racon off",
                                 SOURCES=["Furuno 1722C/NT radar\n40 ft (12.2 m)"], RACON_ON=False)
SETUPS["20261109_215716"] = dict(TRI, CHAIN=[HORN_RACON] + AFTER_ANT, G_RX_DBI=HORN_G,
                                 LABEL="horn aimed at the racon (SMA to the right), racon and radar on; radar is off the horn's axis",
                                 SOURCES=["Furuno 1722C/NT radar\n40 ft, off the horn axis", "SeaBeacon 2 racon\n23 ft (7.0 m)"], RACON_ON=True)
REF_DBM = {"20261109_211913": -10, "20261109_212012": -10, "20261109_212124": -10, "20261109_213227": 0, "20261109_213542": -25,
           "20261109_213625": -25, "20261109_213716": -25, "20261109_214452": -25, "20261109_215120": -5, "20261109_215332": -5, "20261109_215716": -25}

# ---- after the recordings: sweeps and 250 MS/s segmented captures, same horn chain, SM200B in other modes
def _sm(label):
    return AFTER_ANT[:-1] + [("SM200B\n" + label, 0.0, "")]
for f, lab in (("horn_radar_9to10", "sweep 9-10 GHz"), ("horn_radar_harm2", "sweep 18.6-19.0 GHz"), ("horn_radar_wide", "sweep 0.1-20 GHz")):
    SETUPS[f] = dict(TRI, CHAIN=[HORN_RADAR] + _sm(lab + ", 100 kHz RBW"), G_RX_DBI=HORN_G, RACON_ON=True,
                     LABEL="horn aimed at the radar (SMA to the right), racon and radar on",
                     SOURCES=["Furuno 1722C/NT radar\n40 ft (12.2 m)", "SeaBeacon 2 racon\n23 ft, off the horn axis"])
    REF_DBM[f] = -15.5
for f, lab in (("horn_racon_9to10", "sweep 9-10 GHz"), ("horn_racon_harm2", "sweep 18.6-19.0 GHz"), ("horn_racon_wide", "sweep 0.1-20 GHz")):
    SETUPS[f] = dict(TRI, CHAIN=[HORN_RACON] + _sm(lab + ", 100 kHz RBW"), G_RX_DBI=HORN_G, RACON_ON=True,
                     LABEL="horn aimed at the racon (SMA to the right), racon and radar on",
                     SOURCES=["Furuno 1722C/NT radar\n40 ft, off the horn axis", "SeaBeacon 2 racon\n23 ft (7.0 m)"])
    REF_DBM[f] = -15.5
SETUPS["horn_racon_250M"] = dict(SETUPS["20261109_215716"], CHAIN=[HORN_RACON] + _sm("segmented I/Q\n250 MS/s, 160 MHz, 9404 MHz"),
                                 LABEL="horn aimed at the racon, 250 MS/s segmented captures (finer timing)")
REF_DBM["horn_racon_250M"] = -15.5

def key_for(name):
    """Setup key for a raw folder, an npz (raw_<folder>), a sweep or seg folder (<mode>_<tag>_<stamp>)."""
    name = name[4:] if name.startswith("raw_") else name
    if name in SETUPS:
        return name
    for k in SETUPS:
        if not k[0].isdigit() and k in name:
            return k
    return None


def apply(S, raw_name):
    """Set racon_setup (S) to the setup of this recording. Returns the entry, or None if unknown."""
    raw_name = key_for(raw_name) or raw_name
    e = SETUPS.get(raw_name)
    if not e:
        return None
    for k in ("CHAIN", "D_RADAR_M", "D_RACON_M", "D_RADAR_RACON_M", "G_RX_DBI", "SOURCES"):
        setattr(S, k, e[k])
    S.CHAIN_DATE = f"9 Nov, recording {raw_name}, ref {REF_DBM[raw_name]} dBm: {e['LABEL']}"
    return e
