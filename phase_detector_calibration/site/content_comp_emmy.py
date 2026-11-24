"""Emmy's ADCMP604 comparator tests (2-9 Nov 2026), shown on the Comparator tab exactly as she wrote them.

Source: branch `comparator-tests` on GitHub (8 commits by Emmy, 9 Nov 2026; last f20146f at 07:13 UTC),
merged into main on 23 Nov 2026. The text is read at every build straight from
envelope_detector/COMPARATOR-TEST-RESULTS.md and COMPARATOR-TEST-PROCEDURE.md and rendered as is
(no wording changed), and her four plots are copied from envelope_detector/plots_cmp/.
To update this section, edit those files, not this one.
"""
import html
import os
import re
import shutil
import subprocess
from pathlib import Path

from content import item, fig, p

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ED = REPO / "envelope_detector"

BRANCH = "comparator-tests"
LAST_COMMIT = "f20146f, 9 Nov 2026 07:13 UTC (8 Nov 11:13 pm Pacific)"
WORK_DATES = "2&ndash;9 Nov 2026"

# her plots: file in plots_cmp/ -> caption (her own plot titles from plot_cmp.py)
PLOTS = [
    ("1_trip_band.png", "Test 2, 5 Nov: slow input sweep past the threshold, OUT+ against IN+ &minus; IN&minus; at four IN&minus; levels"),
    ("2_rfoff_margin.png", "Test 4, 8&ndash;9 Nov: no radar signal, comparator edge rate against threshold margin"),
    ("3_osc_vs_pickup.png", "Oscilloscope on the comparator output, no radar signal (8 Nov): real oscillation (68 mV margin) against a pickup burst (335 mV)"),
    ("4_pulses_0dB.png", "Test 4, 8 Nov: 100 &micro;s pulses into the detector, Pluto at full power, 335 mV margin; zoom on one pulse"),
]


# ------------------------------------------------------------------ small Markdown renderer
# Only what her two files use: headings, tables (also ragged ones), > quotes, - / 1. / - [ ] lists
# with one level of nesting, **bold**, *italic*, `code`. Text is HTML-escaped; nothing is reworded.

def _inline(s):
    s = html.escape(s, quote=False)
    s = s.replace("****", "&#42;&#42;&#42;&#42;")                     # literal "****" in her scope notes
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<i>\1</i>", s)
    s = s.replace("\\|", "|")
    return s


def _cells(line):
    t = line.strip()
    if t.startswith("|"):
        t = t[1:]
    if t.endswith("|"):
        t = t[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", t)]


def _is_sep(line):
    return bool(re.fullmatch(r"\s*\|?[\s:\-|]+\|?\s*", line)) and "-" in line


def _table(lines):
    head = None
    rows = []
    if len(lines) > 1 and _is_sep(lines[1]):
        head, lines = _cells(lines[0]), lines[2:]
    n = len(head) if head else max(len(_cells(l)) for l in lines)
    for l in lines:
        c = _cells(l)
        while len(c) > n and c[-1] == "":                              # drop empty trailing cells of ragged rows
            c.pop()
        rows.append(c)
    out = ['<div class="tablewrap md"><table>']
    if head:
        out.append("<tr>" + "".join(f'<th class="l">{_inline(c)}</th>' for c in head) + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f'<td class="l">{_inline(c)}</td>' for c in r) + "</tr>")
    out.append("</table></div>")
    return "".join(out)


_LI = re.compile(r"^(\s*)(?:[-*]|\d+\.)\s+(.*)$")


def _list(lines):
    ordered = bool(re.match(r"^\s*\d+\.", lines[0]))
    tag = "ol" if ordered else "ul"
    out, open_sub = [f"<{tag}>"], False
    for l in lines:
        m = _LI.match(l)
        if not m:                                                       # continuation of the previous item
            out[-1] = out[-1][:-5] + " " + _inline(l.strip()) + "</li>"
            continue
        ind, text = len(m.group(1)), m.group(2)
        text = re.sub(r"^\[ \]\s*", "☐ ", text)                     # ☐ (escaped later, so no entity here)
        text = re.sub(r"^\[x\]\s*", "☑ ", text, flags=re.I)        # ☑
        if ind >= 2 and not open_sub:
            out[-1] = out[-1][:-5]
            out.append("<ul>")
            open_sub = True
        elif ind < 2 and open_sub:
            out.append("</ul></li>")
            open_sub = False
        out.append(f"<li>{_inline(text)}</li>")
    if open_sub:
        out.append("</ul></li>")
    out.append(f"</{tag}>")
    return "".join(out)


def md(text, hard_breaks=False, skip_title=False):
    """hard_breaks: every line of a paragraph keeps its own line (her results log is written one entry per line)."""
    lines = text.splitlines()
    out, i = [], 0

    def kind(l):
        s = l.strip()
        if not s:
            return "blank"
        if s.startswith("|"):
            return "table"
        if s.startswith("#"):
            return "head"
        if s.startswith(">"):
            return "quote"
        if s.startswith("```"):
            return "fence"
        if _LI.match(l):
            return "list"
        return "para"

    while i < len(lines):
        k = kind(lines[i])
        if k == "blank":
            i += 1
            continue
        if k == "head":
            m = re.match(r"^(#+)\s*(.*)$", lines[i].strip())
            lvl = len(m.group(1))
            if not (skip_title and lvl == 1):
                tag = {1: "h3", 2: "h3", 3: "h4"}.get(lvl, "h5")
                out.append(f"<{tag}>{_inline(m.group(2))}</{tag}>")
            i += 1
            continue
        if k == "fence":
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        j = i
        if k == "list":                                                 # list items plus indented continuations
            while j < len(lines) and (kind(lines[j]) == "list" or (lines[j].startswith("  ") and kind(lines[j]) == "para")):
                j += 1
        else:
            while j < len(lines) and kind(lines[j]) == k:
                j += 1
        block = lines[i:j]
        if k == "table":
            out.append(_table(block))
        elif k == "list":
            out.append(_list(block))
        elif k == "quote":
            body = "<br>".join(_inline(re.sub(r"^\s*>\s?", "", l)) for l in block)
            out.append(f'<div class="note">{body}</div>')
        else:
            out.append("<p>" + ("<br>" if hard_breaks else " ").join(_inline(l.strip()) for l in block) + "</p>")
        i = j
    return "".join(out)


# ------------------------------------------------------------------ plots

def _commit_time(path):
    try:
        t = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(path)], cwd=REPO, capture_output=True, text=True).stdout.strip()
        return int(t) if t else None
    except OSError:
        return None


def _copy_plots():
    """Copy her plots into site/img/ (the build then copies them to docs/img/), dated by her commit, not today."""
    names = []
    for src_name, cap in PLOTS:
        src = ED / "plots_cmp" / src_name
        if not src.exists():
            continue
        dst_name = "cmp_emmy_" + src_name.replace(".png", "_20261109.png")
        dst = HERE / "img" / dst_name
        shutil.copy2(src, dst)
        t = _commit_time(src)
        if t:
            os.utime(dst, (t, t))
        names.append((dst_name, cap))
    return names


def _read(name):
    f = ED / name
    return f.read_text(encoding="utf-8") if f.exists() else None


def section():
    """Results for the Comparator tab: a dated banner, her plots, her results file in full, her procedure."""
    res = _read("COMPARATOR-TEST-RESULTS.md")
    proc = _read("COMPARATOR-TEST-PROCEDURE.md")
    banner = ('<div class="note emmy"><b>Comparator tests by Emmy, ' + WORK_DATES + '.</b> '
              "Copied unchanged from her GitHub branch <code>" + BRANCH + "</code> (last commit " + LAST_COMMIT + "), merged into main on 23 Nov 2026. "
              "Everything in this section, from here down to the end of &ldquo;Emmy&rsquo;s test procedure&rdquo;, is her own text and plots. "
              "Source files: <code>envelope_detector/COMPARATOR-TEST-RESULTS.md</code>, <code>COMPARATOR-TEST-PROCEDURE.md</code>, <code>cmp_cgr.py</code>, "
              "<code>cmp_scope.py</code>, <code>plot_cmp.py</code>, <code>plots_cmp/</code>. "
              "<b>Update 24 Nov:</b> the IN+ input she suspected was faulty was later shown not to be (see the note under her warning). "
              "Her raw data (<code>data/cmp_trip_*</code>, <code>data/cmp_scope_*</code>) stayed on the loaner Mac and is not on GitHub.</div>")
    plots = "".join(fig(n, c) for n, c in _copy_plots())
    body = banner
    if plots:
        body += "<h3>Emmy&rsquo;s plots (made by <code>plot_cmp.py</code>)</h3>" + plots
    if res:
        r = md(res, hard_breaks=True)
        i = r.find("faulty IN+ input")                                  # put the 24 Nov update right after her warning box
        j = r.find("</div>", i) if i >= 0 else -1
        body += (r[:j + 6] + UPDATE + r[j + 6:]) if j >= 0 else (UPDATE + r)
    else:
        body += p("COMPARATOR-TEST-RESULTS.md not found.")
    if proc:
        body += item("cmp-emmy-proc", "Emmy&rsquo;s test procedure (COMPARATOR-TEST-PROCEDURE.md, started 1 Nov 2026)", md(proc, skip_title=True))
    return '<div class="emmy-section">' + body + "</div>"


# Correction added 24 Nov 2026: the chip was suspected faulty on 2-9 Nov; Sofia's Test B on the same chip shows it is not.
LATER = ("Later tests on the same chip (Sofia, Test B, 23 Nov) show it is not faulty: the same leak test (1 k&Omega; from J1 to AGND, board powered) "
         "gave 3.7 mV, about 3.7 &micro;A, which is normal, and output levels, switching both ways and supply current were all normal.")
UPDATE = ('<div class="note"><b>Update, 24 Nov 2026 (not part of Emmy&rsquo;s text):</b> the warning above, and the &ldquo;faulty IN+&rdquo; '
          "conclusions further down, describe what the chip looked like on 2&ndash;9 Nov: it <i>might</i> have been faulty. " + LATER +
          " Emmy&rsquo;s log below is kept as she wrote it.</div>")

# Key findings shown at the top of the tab. Each line is her own wording from the results file;
# only the selection is ours.
TOP = ('<div class="note"><b>Emmy, 2&ndash;9 Nov 2026 (key points from her results, her wording):</b><ul>'
       "<li><b>IN+ input: possibly faulty on 2&ndash;9 Nov, but later tests show it is not.</b> Emmy measured IN+ sourcing &asymp; 40 &micro;A when powered "
       "(datasheet limit &plusmn;5 &micro;A) and treated her numbers as for scale only. " + LATER + "</li>"
       "<li>Test 1 (supply and output levels): &#9989; (2 Nov 2026, evening).</li>"
       "<li><b>So the steady 27.6 MHz appears only with IN+ near IN&minus;: it is the comparator oscillating</b>, as Test 2 suggested.</li>"
       "<li>Summary: approached from above, RF-off is reliably quiet at &asymp; 300 mV and above, and oscillates at &asymp; 120&ndash;150 mV and below.</li>"
       "<li>Next: solder the 100 &Omega; at J7/J8 (procedure Step 0 &ldquo;Best&rdquo;), then repeat the RF-off margin search; if the quiet margin drops to a few tens of mV, rerun this table at +20 mV.</li>"
       "</ul></div>")
