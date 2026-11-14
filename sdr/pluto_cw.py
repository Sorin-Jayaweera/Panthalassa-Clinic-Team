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


IIO_PY = r"C:\Users\Sorin\radioconda\Lib\site-packages\iio.py"
IIO_DLL_DIR = r"C:\Users\Sorin\radioconda\Library\bin"
_iio = None        # libiio Python binding, loaded once
_ctx = None        # one network context kept open (each iio_attr call opened a new one, ~15 per tone change)
_persistent = True


def _load_iio():
    global _iio
    if _iio is None:
        import importlib.util
        import os
        os.environ["PATH"] = IIO_DLL_DIR + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(IIO_DLL_DIR)
        spec = importlib.util.spec_from_file_location("iio", IIO_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _iio = mod
    return _iio


def drop_context():
    global _ctx
    _ctx = None


def _attr_ctx(args):
    """Same arguments as iio_attr: [-c] [-o] device channel attribute [value]. All channels used here are outputs."""
    global _ctx
    a = [x for x in args if x not in ("-c", "-o")]
    dev_name, ch_name, attr = a[0], a[1], a[2]
    val = a[3] if len(a) > 3 else None
    if _ctx is None:
        _ctx = _load_iio().Context(URI)
    try:
        dev = _ctx.find_device(dev_name)
        ch = dev.find_channel(ch_name, True)
        at = ch.attrs[attr]
        if val is not None:
            at.value = val
        return at.value.strip()
    except OSError as e:
        _ctx = None                  # connection lost: reopen next call
        raise RuntimeError(f"libiio {' '.join(a)} failed: {e}")


def _attr(*args):
    global _persistent
    if _persistent:
        try:
            return _attr_ctx(args)
        except RuntimeError:
            raise
        except OSError as e:
            drop_context()
            raise RuntimeError(f"libiio context {URI} failed: {e}")
        except (ImportError, AttributeError, KeyError, TypeError):
            _persistent = False      # binding not usable: fall back to iio_attr for the rest of the run
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
