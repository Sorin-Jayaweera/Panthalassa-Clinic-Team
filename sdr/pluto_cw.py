"""Drive the ADALM-Pluto as a CW source using its built-in tone generator, with a hard power limit.

The Pluto's attenuation is never set below ATT_MIN_DB, which is computed from the worst-case
full-scale output (+11 dBm) and the limit for the part under test. Change P_LIMIT_DBM on purpose
before testing a more fragile part (ZX60-2534MA-S+ needs -35).
"""
import subprocess

IIO_ATTR = r"C:\Users\Sorin\radioconda\Library\bin\iio_attr.exe"
URI = "ip:192.168.2.1"
P_WORST_MAX_DBM = 11.0   # the most the Pluto could give at 0 dB attenuation
P_LIMIT_DBM = -20.0      # the most the part under test may receive
ATT_MIN_DB = max(0.0, P_WORST_MAX_DBM - P_LIMIT_DBM)
TONE_OFFSET_HZ = 1_000_000


def _attr(*args):
    r = subprocess.run([IIO_ATTR, "-u", URI, *args], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"iio_attr {' '.join(args)} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def set_attenuation(att_db):
    if att_db < ATT_MIN_DB:
        raise ValueError(f"refusing {att_db} dB: the floor is {ATT_MIN_DB} dB (limit {P_LIMIT_DBM} dBm)")
    att_db = min(89.75, round(att_db * 4) / 4)
    _attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain", f"{-att_db}")
    return -float(_attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain").split()[0])


def tone_off():
    """Maximum attenuation and no tone."""
    _attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain", "-89.75")
    for ch in ("altvoltage0", "altvoltage1", "altvoltage2", "altvoltage3"):
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "scale", "0")


def tone_on(freq_hz, att_db, scale=0.5):
    """CW tone at freq_hz. Attenuation is set first, at maximum, then lowered to att_db."""
    if att_db < ATT_MIN_DB:
        raise ValueError(f"refusing {att_db} dB: the floor is {ATT_MIN_DB} dB (limit {P_LIMIT_DBM} dBm)")
    _attr("-c", "-o", "ad9361-phy", "voltage0", "hardwaregain", "-89.75")
    _attr("-c", "ad9361-phy", "altvoltage1", "frequency", str(int(freq_hz - TONE_OFFSET_HZ)))
    for ch, phase in (("altvoltage0", 90000), ("altvoltage2", 0)):       # I and Q of tone 1
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "frequency", str(TONE_OFFSET_HZ))
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "phase", str(phase))
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "scale", str(scale))
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "raw", "1")
    for ch in ("altvoltage1", "altvoltage3"):                             # tone 2 off
        _attr("-c", "cf-ad9361-dds-core-lpc", ch, "scale", "0")
    return set_attenuation(att_db)
