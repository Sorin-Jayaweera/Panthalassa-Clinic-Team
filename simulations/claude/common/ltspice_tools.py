"""
Shared helpers for the JACON LTspice simulations.

  run_ltspice(path)        run a .cir/.asc in batch mode (no GUI popups)
  read_raw(path)           read an LTspice .raw file (binary or ascii, stepped or not)
  parse_meas(log)          pull .meas results (incl. stepped tables) out of a .log
  resample(t, y, dt)       put compressed LTspice data on a uniform time grid
  spectrum_dbm(t, y, ...)  windowed FFT in dBm (50 ohm) for RF plots

Run everything with the radioconda python (it has numpy/scipy/matplotlib):
    %USERPROFILE%\\radioconda\\python.exe <script>.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

LTSPICE_CANDIDATES = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/ADI/LTspice/LTspice.exe",
    Path("C:/Program Files/ADI/LTspice/LTspice.exe"),
    Path("C:/Program Files/LTC/LTspiceXVII/XVIIx64.exe"),
]


def find_ltspice() -> Path:
    env = os.environ.get("LTSPICE_EXE")
    if env and Path(env).exists():
        return Path(env)
    for c in LTSPICE_CANDIDATES:
        if c.exists():
            return c
    raise FileNotFoundError("LTspice.exe not found - set LTSPICE_EXE")


def run_ltspice(netlist: str | Path, extra_files: list[Path] | None = None,
                timeout: float = 3600) -> tuple[Path, Path]:
    """Run LTspice in batch mode.

    The deck (plus any extra files it needs, e.g. symbols / .lib) is copied
    to a SHORT temp folder first: LTspice pops a modal "Trouble reading file"
    dialog for very long paths, which would hang a batch run.
    Returns (raw_path, log_path) copied back next to the original deck.
    """
    netlist = Path(netlist).resolve()
    work = Path(tempfile.gettempdir()) / "jacon_lt" / netlist.stem[:20]
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(netlist, work / netlist.name)
    for f in extra_files or []:
        f = Path(f)
        dst = work / f.name
        if f.is_dir():
            shutil.copytree(f, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(f, dst)
    cmd = [str(find_ltspice()), "-b", str(work / netlist.name)]
    subprocess.run(cmd, check=False, timeout=timeout)
    raw = work / (netlist.stem + ".raw")
    log = work / (netlist.stem + ".log")
    out_raw = netlist.with_suffix(".raw")
    out_log = netlist.with_suffix(".log")
    if log.exists():
        shutil.copy2(log, out_log)
    if not raw.exists():
        txt = out_log.read_text(errors="ignore") if out_log.exists() else "(no log)"
        raise RuntimeError(f"LTspice produced no .raw for {netlist.name}\n{txt}")
    shutil.copy2(raw, out_raw)
    return out_raw, out_log


# --------------------------------------------------------------------------
class RawData:
    """Result of read_raw. Access signals case-insensitively: d['V(out)']."""

    def __init__(self, names, kinds, data, flags, plotname):
        self.names = names
        self.kinds = kinds
        self.data = data            # shape (n_vars, n_points)
        self.flags = flags
        self.plotname = plotname
        self._idx = {n.lower(): i for i, n in enumerate(names)}
        x = np.abs(np.real(data[0]))
        # LTspice concatenates .step runs; a new step starts where the x axis resets
        if "stepped" in flags and len(x) > 1:
            starts = [0] + list(np.where(np.diff(x) < 0)[0] + 1)
        else:
            starts = [0]
        ends = starts[1:] + [len(x)]
        self.steps = [slice(s, e) for s, e in zip(starts, ends)]

    def __contains__(self, name):
        return name.lower() in self._idx

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, step: int | None = None):
        key = name.lower()
        if key not in self._idx:
            raise KeyError(f"{name!r} not in raw file. Available: {self.names}")
        y = self.data[self._idx[key]]
        if self._idx[key] == 0:
            y = np.abs(np.real(y))
        return y if step is None else y[self.steps[step]]

    def time(self, step: int | None = None):
        return self.get(self.names[0], step)


def read_raw(path: str | Path) -> RawData:
    blob = Path(path).read_bytes()
    # header is UTF-16LE in LTspice XVII/24/26, ASCII in some older builds
    utf16 = blob[1:2] == b"\x00"
    enc = "utf-16-le" if utf16 else "latin-1"
    step = 2 if utf16 else 1
    for marker in ("Binary:\n", "Values:\n"):
        m = marker.encode(enc)
        pos = blob.find(m)
        if pos >= 0:
            header = blob[:pos].decode(enc)
            body = blob[pos + len(m):]
            binary = marker.startswith("Binary")
            break
    else:
        raise ValueError("not an LTspice raw file")
    _ = step

    lines = header.splitlines()
    info = {}
    names, kinds = [], []
    in_vars = False
    for ln in lines:
        if in_vars:
            parts = ln.strip().split()
            if len(parts) >= 3 and parts[0].isdigit():
                names.append(parts[1])
                kinds.append(parts[2])
                continue
            in_vars = False
        if ln.startswith("Variables:"):
            in_vars = True
            continue
        if ":" in ln:
            k, v = ln.split(":", 1)
            info[k.strip().lower()] = v.strip()
    nvars = int(info["no. variables"])
    npts = int(info["no. points"])
    flags = info.get("flags", "").lower().split()
    complex_ = "complex" in flags
    all_double = "double" in flags

    if binary:
        if complex_:
            arr = np.frombuffer(body[: npts * nvars * 16], dtype="<c16").reshape(npts, nvars).T
        elif all_double:
            arr = np.frombuffer(body[: npts * nvars * 8], dtype="<f8").reshape(npts, nvars).T
        else:
            rec = np.dtype([("t", "<f8")] + [(f"v{i}", "<f4") for i in range(1, nvars)])
            r = np.frombuffer(body[: npts * rec.itemsize], dtype=rec)
            arr = np.empty((nvars, npts))
            arr[0] = r["t"]
            for i in range(1, nvars):
                arr[i] = r[f"v{i}"]
    else:
        toks = body.decode(enc, errors="ignore").split()
        vals = []
        i = 0
        while i < len(toks) and len(vals) < npts * nvars:
            if len(vals) % nvars == 0:
                i += 1          # point index
            vals.append(complex(toks[i].replace(",", "+") + ("j" if "," in toks[i] else ""))
                        if complex_ else float(toks[i]))
            i += 1
        arr = np.array(vals).reshape(npts, nvars).T
    return RawData(names, kinds, arr, flags, info.get("plotname", ""))


# --------------------------------------------------------------------------
_num = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def parse_meas(log: str | Path) -> dict[str, list[float]]:
    """Return {meas_name_lower: [value per step]} from an LTspice .log."""
    txt = Path(log).read_text(errors="ignore")
    out: dict[str, list[float]] = {}
    # non-stepped:  "vout: AVG(v(vout))=0.0123 FROM ..."  or "name: value"
    for m in re.finditer(rf"^(\w+):\s*[^=\n]*=\s*({_num})", txt, re.M):
        out.setdefault(m.group(1).lower(), []).append(float(m.group(2)))
    # stepped table:
    #   Measurement: vout
    #     step  AVG(v(vout))  FROM  TO
    #        1  -0.0118  3e-08  4e-08
    for m in re.finditer(r"^Measurement:\s*(\w+)\s*\n[^\n]*\n((?:\s*\d+\s+[^\n]*\n)+)", txt, re.M):
        name = m.group(1).lower()
        vals = []
        for row in m.group(2).strip().splitlines():
            parts = row.split()
            if len(parts) >= 2:
                try:
                    vals.append(float(parts[1]))
                except ValueError:
                    pass
        out[name] = vals
    return out


def parse_step_params(log: str | Path) -> list[dict[str, float]]:
    """'.step freq=1e9' lines -> [{'freq':1e9}, ...]"""
    txt = Path(log).read_text(errors="ignore")
    res = []
    for m in re.finditer(r"^\.step\s+(.*)$", txt, re.M):
        d = {}
        for k, v in re.findall(rf"(\w+)=({_num})", m.group(1)):
            d[k.lower()] = float(v)
        res.append(d)
    return res


# --------------------------------------------------------------------------
def resample(t, y, dt, t0=None, t1=None):
    t = np.asarray(t)
    y = np.asarray(y)
    t0 = t[0] if t0 is None else t0
    t1 = t[-1] if t1 is None else t1
    tu = np.arange(t0, t1, dt)
    return tu, np.interp(tu, t, y)


def spectrum_dbm(t, v, t0, t1, fmax=None, r_ohm=50.0, oversample=4):
    """Hann-windowed single-sided spectrum of voltage v across r_ohm, in dBm per tone."""
    t = np.asarray(t)
    dt_native = np.median(np.diff(t[(t >= t0) & (t <= t1)]))
    dt = dt_native
    tu, vu = resample(t, v, dt, t0, t1)
    n = len(vu)
    w = np.hanning(n)
    spec = np.fft.rfft((vu - np.mean(vu) * 0) * w, n * oversample)
    f = np.fft.rfftfreq(n * oversample, dt)
    vpk = 2 * np.abs(spec) / np.sum(w)
    p = 10 * np.log10((vpk ** 2) / (2 * r_ohm) / 1e-3 + 1e-30)
    if fmax is not None:
        k = f <= fmax
        f, p = f[k], p[k]
    return f, p


def dbm_to_vpk(p_dbm, r=50.0):
    return np.sqrt(2 * r * 1e-3 * 10 ** (np.asarray(p_dbm) / 10))


def vpk_to_dbm(vpk, r=50.0):
    return 10 * np.log10(np.asarray(vpk) ** 2 / (2 * r) / 1e-3 + 1e-30)


def envelope_amplitude(t, v, f_carrier, window_cycles=4):
    """Running peak amplitude of an RF waveform (max |v| over a few carrier cycles)."""
    dt = 1 / (f_carrier * 24)
    tu, vu = resample(t, v, dt)
    n = max(3, int(window_cycles * 24))
    from scipy.ndimage import maximum_filter1d
    return tu, maximum_filter1d(np.abs(vu), n)
