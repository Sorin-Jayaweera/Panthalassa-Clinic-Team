"""Component data for the JACON power-budget document.

EVERY number here was pulled out of the Mini-Circuits PDF in ./datasheets by
extract, and each carries the page it came from. Nothing is from memory.
"""
URL = "https://www.minicircuits.com/WebStore/dashboard.html?model={}"
PDF = "https://www.minicircuits.com/pdfs/{}.pdf"

def dbm_to_mw(d):  return 10 ** (d / 10.0)
def mw_to_dbm(m):  return 10 * __import__("math").log10(m)

# damage_val: (value, unit as printed on datasheet, page)
PARTS = [
 dict(model="ZX60-5123LN+", role="RX LNA", jacon="[1] RX front end",
      band="5.5 - 12.5 GHz", f_seen="9.3 - 9.5 GHz",
      gain_txt="+22.0 dB typ (19.0 min), 5.5-12.5 GHz", gain_db=22.0,
      p1db_dbm=17.0, p1db_txt="+17.0 dBm typ output P1dB",
      damage_txt="RF Input Power (CW) +15 dBm", damage_dbm=15.0, damage_page=3,
      extra="Total power dissipation 1.2 W; DC +12 V", spec_page=1,
      ev=[("ratings","ZX60-5123LNplus_ratings_p3.png",3,"ABSOLUTE MAXIMUM RATINGS: RF Input Power (CW) = +15 dBm"),
          ("specs","ZX60-5123LNplus_compression_p1.png",1,"ELECTRICAL SPECIFICATIONS: gain 22.0 dB typ, P1dB +17.0 dBm typ")]),
 dict(model="ZX05-14LH-S+", role="RX down-mixer / TX up-mixer", jacon="[1] RX mixer, [8] TX mixer",
      band="RF+LO 3.7 - 10 GHz, IF DC - 4 GHz", f_seen="RF 9.3-9.5 GHz, LO 8.3 GHz, IF 1.0-1.2 GHz",
      gain_txt="conv. loss 7.72 dB typ at RF 9400 MHz (6.7 dB band typ), LO +10 dBm", gain_db=-7.72,
      p1db_dbm=5.0, p1db_txt="+5 dBm typ RF input at 1 dB compression",
      damage_txt="RF Power 50 mW", damage_dbm=None, damage_mw=50.0, damage_page=1,
      extra="Level 10 mixer: LO drive +10 dBm", spec_page=1,
      ev=[("ratings","ZX05-14LH-Splus_ratings_p1.png",1,"Maximum Ratings: RF Power = 50 mW"),
          ("specs","ZX05-14LH-Splus_compression_p1.png",1,"1 dB COMPR.: +5 dBm typ (LO +10 dBm)"),
          ("typperf","ZX05-14LH-Splus_typperf_p1.png",1,"Typical Performance Data: conversion loss 7.72 dB at RF 9400 MHz (band typ is 6.7 dB)")]),
 dict(model="ZX60-14012L-S+", role="LO buffer amplifier", jacon="[2] LO chain",
      band="0.3 MHz - 14 GHz", f_seen="8.3 GHz",
      gain_txt="12.55 dB at 8.0 GHz, 11.85 dB at 9.0 GHz -> approx 12.3 dB at 8.3 GHz", gain_db=12.3,
      p1db_dbm=11.0, p1db_txt="+11 dBm typ output P1dB (+4 dBm min at 10-14 GHz)",
      damage_txt="Input Power (no Damage) 10 dBm", damage_dbm=10.0, damage_page=1,
      extra="Band-wide spec is +12 dB typ / 9 dB min; the page 2 table gives 12.55 dB at 8 GHz. NF 5.35 dB at 8 GHz", spec_page=1,
      ev=[("ratings","ZX60-14012L-Splus_ratings_p1.png",1,"Maximum Ratings: Input Power (no Damage) = 10 dBm"),
          ("specs","ZX60-14012L-Splus_compression_p1.png",1,"Electrical Specifications: gain 12 dB typ, output P1dB +11 dBm typ"),
          ("typperf","ZX60-14012L-Splus_typperf_p2.png",2,"Typical Performance Data: 12.55 dB gain at 8000 MHz, 11.85 dB at 9000 MHz (8.3 GHz falls between)")]),
 dict(model="ZX10-2-1252-S+", role="LO 2-way splitter (DC pass)", jacon="[2] LO split to both mixers",
      band="1800 - 12500 MHz", f_seen="8.3 GHz",
      gain_txt="-3.0 dB split + 0.7 dB typ insertion loss", gain_db=-3.7,
      p1db_dbm=None, p1db_txt="passive - no compression spec",
      damage_txt="Power Input (as a splitter) 1.85 W", damage_dbm=None, damage_mw=1850.0, damage_page=2,
      extra="Internal dissipation 0.85 W max; DC current 0.4 A max", spec_page=2,
      ev=[("ratings","ZX10-2-1252-Splus_ratings_p2.png",2,"Maximum Ratings: Power Input (as a splitter) = 1.85 W")]),
 dict(model="ZX60-P162LN+", role="IF amplifier (preferred for 1.0-1.2 GHz)", jacon="[3] IF chain",
      band="0.7 - 1.6 GHz", f_seen="1.0 - 1.2 GHz",
      gain_txt="21.81 dB at 1.1 GHz (22.49 at 1.0, 21.12 at 1.2 GHz)", gain_db=21.81,
      p1db_dbm=19.9, p1db_txt="+19.9 dBm typ output P1dB at 1.0 GHz (+17.5 min)",
      damage_txt="Input RF Power (No Damage) VD=+4 V: +25 dBm", damage_dbm=25.0, damage_page=2,
      extra="Noise figure 0.52 dB typ at 1.0 GHz; power consumption 0.55 W", spec_page=2,
      ev=[("ratings","ZX60-P162LNplus_ratings_p2.png",2,"ABSOLUTE MAXIMUM RATINGS: Input RF Power (No Damage) = +25 dBm"),
          ("specs","ZX60-P162LNplus_compression_p2.png",2,"ELECTRICAL SPECIFICATIONS: gain and output P1dB vs frequency"),
          ("typperf","ZX60-P162LNplus_typperf_p4.png",4,"Typical Performance Data: 21.81 dB gain and +19.9 dBm P1dB at 1100 MHz")]),
 dict(model="ZX60-P103LN+", role="IF amplifier (wideband alternate)", jacon="[3] IF chain (alternate)",
      band="50 - 3000 MHz", f_seen="1.0 - 1.2 GHz",
      gain_txt="+15.6 dB typ at 1000 MHz (13.5 min)", gain_db=15.6,
      p1db_dbm=22.4, p1db_txt="+22.4 dBm typ output P1dB at 1000 MHz",
      damage_txt="Input RF Power (no damage): 21 dBm (50-2000 MHz), 26 dBm (2000-3000 MHz)",
      damage_dbm=21.0, damage_page=3,
      extra="Noise figure 0.5 dB typ at 1000 MHz; power consumption 0.66 W", spec_page=2,
      ev=[("ratings","ZX60-P103LNplus_ratings_p3.png",3,"ABSOLUTE MAXIMUM RATINGS: Input RF Power (no damage) = 21 dBm at 50-2000 MHz"),
          ("specs","ZX60-P103LNplus_compression_p2.png",2,"ELECTRICAL SPECIFICATIONS: gain 15.6 dB typ and P1dB +22.4 dBm typ at 1000 MHz")]),
 dict(model="ZX60-2534MA-S+", role="IF amplifier (high gain alternate)", jacon="[3] IF chain (alternate)",
      band="0.5 - 2.5 GHz", f_seen="1.0 - 1.2 GHz",
      gain_txt="+43.5 dB typ at 1.0 GHz (at VD = 5 V)", gain_db=43.5,
      p1db_dbm=19.0, p1db_txt="+19.0 dBm typ output P1dB at fL",
      damage_txt="Input Power (no damage) -15 dBm", damage_dbm=-15.0, damage_page=1,
      extra="LOWEST damage limit of any part here. Power dissipation 0.5 W; DC 5 V", spec_page=1,
      ev=[("ratings","ZX60-2534MA-Splus_ratings_p1.png",1,"Maximum Ratings: Input Power (no damage) = -15 dBm"),
          ("specs","ZX60-2534MA-Splus_compression_p1.png",1,"Electrical Specifications: gain over frequency, output P1dB")]),
 dict(model="ZFRSC-42-S+", role="Resistive 2-way splitter (IF split and delay-line split)", jacon="[3] IF split, [6] delay-line split",
      band="DC - 4200 MHz", f_seen="1.0 - 1.2 GHz",
      gain_txt="-6.0 dB total loss (5.99 / 6.02 dB at 1000 MHz)", gain_db=-6.0,
      p1db_dbm=None, p1db_txt="passive - no compression spec",
      damage_txt="Power Input (as a splitter) 0.75 W", damage_dbm=None, damage_mw=750.0, damage_page=1,
      extra="Internal dissipation 0.375 W max. Resistive: isolation equals insertion loss (~6 dB)", spec_page=1,
      ev=[("ratings","ZFRSC-42-Splus_ratings_p1.png",1,"Maximum Ratings: Power Input (as a splitter) = 0.75 W, internal dissipation 0.375 W")]),
 dict(model="ZX05-30W-S+", role="Phase detector (delay-line mixer)", jacon="[6] phase detector",
      band="RF+LO 300 - 4000 MHz, IF DC - 950 MHz", f_seen="RF+LO 1.0-1.2 GHz, IF = DC",
      gain_txt="conv. loss 6.22 dB typ at RF 944 MHz (6.8 dB band typ), LO +7 dBm", gain_db=-6.22,
      p1db_dbm=1.0, p1db_txt="+1 dBm typ RF input at 1 dB compression",
      damage_txt="RF Power 50 mW", damage_dbm=None, damage_mw=50.0, damage_page=1,
      extra="Level 7 mixer: LO drive +7 dBm. IF current 40 mA max", spec_page=1,
      ev=[("ratings","ZX05-30W-Splus_ratings_p1.png",1,"Maximum Ratings: RF Power = 50 mW, IF Current = 40 mA"),
          ("specs","ZX05-30W-Splus_compression_p1.png",1,"1 dB COMP.: +1 dBm typ; conversion loss 6.8 dB typ at LO +7 dBm"),
          ("typperf","ZX05-30W-Splus_typperf_p1.png",1,"Typical Performance Data: conversion loss 6.22 dB at RF 944 MHz, closest tabulated point to our 1.0-1.2 GHz")]),
]

def damage_dbm_mw(p):
    import math
    if p.get("damage_dbm") is not None:
        d = p["damage_dbm"]; return d, dbm_to_mw(d)
    m = p["damage_mw"]; return 10*math.log10(m), m
