"""Sofia's comparator Test B (board alone), 18-23 Nov 2026, on the Comparator tab.

The text is read at every build from envelope_detector/COMPARATOR-TEST-B-SOFIA.md and rendered
with the same small Markdown renderer as Emmy's section. Plots come from envelope_detector/data/.
To update this section, edit that file, not this one.
"""
import shutil
from pathlib import Path

import content_comp_emmy as EMMY
from content import item, fig, p

HERE = Path(__file__).resolve().parent
ED = HERE.parent.parent / "envelope_detector"

PLOTS = [
    ("cmp_testB_overlay_20261123.png", "All Test B sweeps on 23 Nov: average output and toggling strength against IN+ &minus; IN&minus; "
     "(blue: triad 1, orange: triad 2, green: evening). Each group repeats; the arrangement of the leads moves the whole curve."),
    ("cmp_states_20261123_2013.png", "23 Nov 20:11: all four channels quiet after a reset, inside the transition, and latched back at "
     "&minus;95 mV. In the latched state IN+ and IN&minus; swing in opposite phase and cross every cycle."),
    ("cmp_testB_repeats_20261123.png", "23 Nov 15:05&ndash;15:18: three repeats against sweep 6 (14:25), a time view of one sweep, and "
     "output snapshots at six input levels."),
    ("cmp_testB_20261119.png", "19 Nov: sweeps 2 and 3 (toggling between &minus;42 and +52 mV at 94 MHz) and mid-band waveforms."),
]

TOP = ('<div class="note"><b>Sofia, 18&ndash;23 Nov 2026 (Test B, board alone; details below):</b><ul>'
       "<li>The chip works and is not damaged: clean switching both ways, output levels 1.107 / 1.503 V, 12 mA; "
       "IN+ leakage now about 3.7 &micro;A (normal), not the 40 &micro;A Emmy measured on 2 Nov.</li>"
       "<li>Near the threshold the output oscillates at 44&ndash;94 MHz (0.7&ndash;1.1 V pk-pk) because its own edges couple back into "
       "IN+ and IN&minus; through the bench wiring. The zone was 40 mV wide at best and 140&ndash;160 mV or worse later the same day, "
       "depending only on where the leads lay; each arrangement repeats to 3&ndash;6 mV.</li>"
       "<li>The oscillation can latch 40&ndash;100 mV away from the threshold after a disturbance. Hysteresis was not tested "
       "(no repeatable baseline at the end).</li>"
       "<li>Next: parts soldered at the board (hysteresis resistor J7&ndash;J2, small capacitor J4 to ground) or a PCB with a tight "
       "output pair and IN&minus; decoupled at the pin.</li></ul></div>")


def _copy_plots():
    names = []
    for name, cap in PLOTS:
        src = ED / "data" / name
        if not src.exists():
            continue
        dst_name = "cmp_sofia_" + name
        shutil.copy2(src, HERE / "img" / dst_name)
        names.append((dst_name, cap))
    return names


def section():
    f = ED / "COMPARATOR-TEST-B-SOFIA.md"
    if not f.exists():
        return p("COMPARATOR-TEST-B-SOFIA.md not found.")
    banner = ('<div class="note"><b>Comparator Test B by Sofia, 18&ndash;23 Nov 2026</b> (board alone, DC staircase on IN+, '
              "threshold on IN&minus;; bench work by Sofia, scripts and write-up with Claude). Source: "
              "<code>envelope_detector/COMPARATOR-TEST-B-SOFIA.md</code>; time-stamped log "
              "<code>COMPARATOR-BENCH-NOTES-SOFIA.md</code>; data <code>envelope_detector/data/cmp_*</code>; "
              "photos <code>envelope_detector/photos_cmp_sofia/</code>.</div>")
    plots = "".join(fig(n, c) for n, c in _copy_plots())
    body = banner + "<h3>Plots</h3>" + plots + EMMY.md(f.read_text(encoding="utf-8"), skip_title=True)
    return item("cmp-sofia", "Sofia&rsquo;s Test B, 18&ndash;23 Nov 2026: setup, checks, every sweep, incidents", body)
