"""Redraw every phase detector plot from the CSVs, put them on the site, rebuild it.
  python make_plots.py            once
  python make_plots.py --push     and commit + push the plots, data and site (explicit paths only)
  python make_plots.py --watch    repeat whenever the data file changes (with --push: publish each time)"""
import subprocess as sp
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT, SITE = HERE.parent, HERE / "site"
DATA = [HERE / "pd_dither_14nov.csv", HERE / "pd_overnight_13nov.log", HERE / "amp_chain_18nov.csv", HERE / "amp_chain_18nov.log", HERE / "amp_ramp_18nov.csv",
        *HERE.glob("arm_probe_*_18nov.csv"), *HERE.glob("arm_probe_18nov.log"), *HERE.glob("pd_*_18nov.log"), *HERE.glob("pd_*_19nov.log"), HERE / "pd_zoom_readings_18nov.csv"]
JOBS = ["plot_amp_chain.py", "plot_pd_hd_night.py", "plot_pd_ifs.py", "plot_pd_vs_pluto_level.py", "plot_pd_all_config.py", "plot_pd_key.py", "plot_day_summary.py", "plot_pd_repeats.py", "plot_pd_x_uncertainty.py", "plot_pd_design_limits.py", "plot_pd_furuno_link_budget.py", "plot_pd_level_response.py", "plot_pd_theory.py"]


def run(*a, cwd=HERE):
    return sp.run([*a], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def once(push):
    t0 = time.time()
    for j in JOBS:
        r = run(sys.executable, j)
        print(f"{j}: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr.strip().splitlines()[-1]}")
    used = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in [*SITE.glob("content*.py"), HERE / "pd_x_uncertainty_table.json"])
    new = [p for p in HERE.glob("*.png") if p.stat().st_mtime >= t0 and f'"{p.name}"' in used]
    for p in new:
        (SITE / "img" / p.name).write_bytes(p.read_bytes())
    print(run(sys.executable, "build_site.py", cwd=SITE).stdout.strip().splitlines()[-1])
    if push:
        paths = [*DATA, *new, *[SITE / "img" / p.name for p in new], *[ROOT / "docs" / "img" / p.name for p in new], ROOT / "docs" / "index.html",
                 *HERE.glob("plot_pd_*.py"), *[HERE / n for n in ("plot_amp_chain.py", "run_amp_chain_iq.py", "amp_wrapper.sh", "amp_ramp_wrapper.sh", "amp_probe.py", "amp_resume.sh", "plot_day_summary.py", "pd_plan.py", "run_pd_overnight.py",
                 "pad10_wrapper.sh", "pad10z_wrapper.sh", "pad10z40_wrapper.sh", "pad10z40n_wrapper.sh", "pad10zn_wrapper.sh", "pad10d_wrapper.sh", "pad10hf_wrapper.sh", "pad10hfp2_wrapper.sh", "pad10hfp2_relaunch_after_pluto_drop.sh", "after_minus40.sh", "scope_zoom.py", "eq_wrapper.sh", "elo_wrapper.sh", "sc_wrapper.sh")], HERE / "pdlib.py", HERE / "pd_runs.py", HERE / "pd_x_uncertainty_table.json", HERE / "make_plots.py", *SITE.glob("content*.py"), SITE / "build_site.py", *SITE.glob("parts/*")]
        rel = [str(p.relative_to(ROOT)) for p in paths if p.exists()]
        g = lambda *a: run("git", *a, cwd=ROOT)
        # never stash, reset or rebase: a running sweep appends to the CSV; commit only these paths, then merge the remote
        g("add", "--", *rel)
        g("commit", "-qm", f"Phase detector plots and data, {time.strftime('%d %b %H:%M')}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", "--", *rel)
        print("push:", g("pull", "--no-rebase", "--no-edit", "-q").returncode == 0 and g("push", "-q").returncode == 0)


if __name__ == "__main__":
    push, watch, seen = "--push" in sys.argv, "--watch" in sys.argv, 0
    while True:
        m = max(p.stat().st_mtime for p in DATA if p.exists())
        if m != seen:
            seen = m
            once(push)
        if not watch:
            break
        time.sleep(300)
