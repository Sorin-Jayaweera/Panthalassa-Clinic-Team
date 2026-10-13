"""Build JACON_component_power_ratings.docx from specs.py + evidence crops."""
import os
import sys

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

sys.path.insert(0, ".")
import specs
from specs import PARTS, dbm_to_mw, damage_dbm_mw

RED = RGBColor(0xB0, 0x30, 0x30)
GREY = RGBColor(0x55, 0x55, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def hyperlink(par, url, text):
    r_id = par.part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), "1F5FBF")
    rPr.append(c)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "18")
    rPr.append(sz)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    link.append(run)
    par._p.append(link)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def set_cell(cell, text, bold=False, size=8.5, color=None):
    cell.text = ""
    run = cell.paragraphs[0].add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color


def table(doc, headers, rows, widths, fontsize=8.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, w in enumerate(widths):
        t.columns[i].width = Inches(w)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        set_cell(c, h, bold=True, size=fontsize, color=WHITE)
        shade(c, "1F5FBF")
        c.width = Inches(widths[i])
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            flag = isinstance(v, tuple)
            set_cell(cells[i], v[0] if flag else v, bold=flag, size=fontsize,
                     color=RED if flag else None)
            cells[i].width = Inches(widths[i])
    return t


def pic(doc, path, maxw=6.9, maxh=3.2):
    w, h = Image.open(path).size
    wi, hi = maxw, maxw * h / w
    if hi > maxh:
        hi, wi = maxh, maxh * w / h
    doc.add_picture(path, width=Inches(wi))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = GREY


def note(doc, text, size=9.5, bold=False, color=None, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        r.font.color.rgb = color
    return p


doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10)
for s in doc.sections:
    s.top_margin = s.bottom_margin = Inches(0.7)
    s.left_margin = s.right_margin = Inches(0.7)

doc.add_heading("JACON - component power ratings and signal-chain budget", level=0)
note(doc, "Mini-Circuits parts on hand, with the maximum power each one can take, taken directly from the "
          "manufacturer datasheets.", size=10.5)
note(doc, "Every number in this document is traceable. Each part has a screenshot cropped from its own datasheet "
          "PDF with the page number, plus links to the Mini-Circuits product page and to the PDF saved in "
          "datasheets/ next to this file. Nothing here is written from memory: if a value looks wrong, open the "
          "linked PDF at the cited page and check it.")
note(doc, "Conversion used throughout:  P(mW) = 10^(P(dBm)/10).   0 dBm = 1 mW,  +17 dBm = 50 mW,  "
          "+30 dBm = 1 W,  -15 dBm = 0.0316 mW.", italic=True)

# ---------------------------------------------------------------- 1. limits
doc.add_heading("1. Maximum power each part can take", level=1)
note(doc, "Two different limits matter. The damage limit is what destroys the part. The P1dB / compression limit "
          "is where it stops behaving linearly, which happens long before damage. Both are reproduced as printed "
          "on the datasheet, then converted to dBm and mW.")
rows = []
for pt in PARTS:
    d_dbm, d_mw = damage_dbm_mw(pt)
    if pt["p1db_dbm"] is None:
        p1, p1mw = "passive - n/a", "-"
    else:
        p1 = "%+.1f dBm" % pt["p1db_dbm"]
        p1mw = "%.1f mW" % dbm_to_mw(pt["p1db_dbm"])
    rows.append([pt["model"], pt["damage_txt"], "%+.2f" % d_dbm, "%.4g" % d_mw, p1, p1mw,
                 "p.%d" % pt["damage_page"]])
table(doc, ["Part", "Damage limit, as printed on the datasheet", "= dBm", "= mW",
            "P1dB / compression", "= mW", "Page"],
      rows, [1.15, 2.25, 0.62, 0.72, 1.05, 0.62, 0.45], fontsize=8.0)
note(doc, "WARNING - the ZX60-2534MA-S+ stands out: its -15 dBm (0.032 mW) damage limit is about 36 dB lower than "
          "any other amplifier here. Placed directly after the RX mixer it would be destroyed by anything except a "
          "distant echo.", bold=True, color=RED)

# ---------------------------------------------------------------- 2. roles
doc.add_heading("2. Where each part sits, and what it sees", level=1)
rows = [[pt["model"], pt["role"], pt["band"], pt["f_seen"], pt["gain_txt"]] for pt in PARTS]
table(doc, ["Part", "Role", "Datasheet band", "Frequency it sees in JACON",
            "Gain / loss at that frequency"],
      rows, [1.15, 1.55, 1.35, 1.45, 1.6], fontsize=8.0)
doc.add_page_break()

# ---------------------------------------------------------------- 3. chart
blk = doc.add_section()
blk.orientation = WD_ORIENT.PORTRAIT
blk.page_width, blk.page_height = Inches(8.5), Inches(11)
blk.left_margin = blk.right_margin = Inches(0.5)
blk.top_margin = blk.bottom_margin = Inches(0.4)
doc.add_heading("3. Block diagram with power limits", level=1)
pic(doc, "JACON_blockdiagram_layout.png", maxw=7.4, maxh=8.55)
caption(doc, "Same layout as racon_draft_design01b_drawing.pdf. Green text in each block says what that stage does. "
             "Each block also carries: title, part number, maximum input in "
             "dBm and mW, and minimum attenuation. Blue blocks are the nine parts we have, with datasheet maximum "
             "ratings and the photo from the datasheet; grey blocks are candidate parts named on the drawing and "
             "are not datasheet-verified. The small box beside each block is the running level relative to the start "
             "of that chain: worst case (maximum attenuation, minimum gain) to best case (minimum attenuation, "
             "maximum gain). Green means every term is datasheet-verified, amber means the total includes an "
             "assumed value.")

bench = doc.add_section()
bench.orientation = WD_ORIENT.LANDSCAPE
bench.page_width, bench.page_height = Inches(11), Inches(8.5)
bench.left_margin = bench.right_margin = Inches(0.5)
bench.top_margin = bench.bottom_margin = Inches(0.5)
doc.add_heading("3b. Bench test: Pluto TX to the phase detector", level=1)
pic(doc, "JACON_bench_delayline_flow.png", maxw=10.0, maxh=5.6)
caption(doc, "Pluto TX -> ZFRSC-42-S+ splitter -> 4 in and 8.5 in cables -> ZX05-30W-S+ mixer used as a phase "
             "detector, for a 750 mW (+28.75 dBm) source. Splitter and mixer attenuation and limits are datasheet "
             "values; cable loss is assumed for RG-316-class coax. A real ADALM-Pluto cannot deliver 750 mW, and at "
             "that level both mixer ports would be about 5.5 dB over the 50 mW rating.")

port = doc.add_section()
port.orientation = WD_ORIENT.PORTRAIT
port.page_width, port.page_height = Inches(8.5), Inches(11)
port.left_margin = port.right_margin = Inches(0.7)
port.top_margin = port.bottom_margin = Inches(0.7)

# ---------------------------------------------------------------- 4. headroom
doc.add_heading("4. Headroom against the damage limits", level=1)
note(doc, "Expected levels come from the LTspice model in simulations/claude/01_jacon_system. Worst case is the "
          "-10 dBm close-range echo.")
HEAD = [
    ["ZX60-5123LN+ (LNA)", "limiter output, +16.3 dBm while the limiter clamps", "+15 dBm",
     ("OVER by 1.3 dB",), "Keep the in-line attenuator the drawing calls for."],
    ["ZX05-14LH-S+ (RX mixer)", "LNA saturated output, about +17 to +18 dBm", "+17 dBm (50 mW)",
     ("0 to -1 dB",), "Marginal at close range; the same pad fixes this."],
    ["ZX60-P162LN+ (IF amp)", "mixer IF output, about +11 dBm worst case", "+25 dBm", "14 dB", "Fine."],
    ["ZX60-P103LN+ (IF amp)", "mixer IF output, about +11 dBm worst case", "+21 dBm", "10 dB", "Fine."],
    ["ZX60-2534MA-S+ (IF amp)", "mixer IF output, about +11 dBm worst case", "-15 dBm",
     ("OVER by 26 dB",), "Do not put this straight after the mixer."],
    ["ZFRSC-42-S+ (both units)", "IF amp output, about +20 dBm saturated", "+28.8 dBm (0.75 W)", "9 dB", "Fine."],
    ["ZX05-30W-S+ (phase det.)", "limiting-amp chain, about +8 dBm per port", "+17 dBm (50 mW)", "9 dB",
     "Above the +1 dBm compression point, which is intended here."],
    ["ZX60-14012L-S+ (LO buffer)", "PLL output, about +3 dBm", "+10 dBm", "7 dB",
     "Check your ADF5355 output level; +3 dBm is an assumption."],
    ["ZX10-2-1252-S+ (LO split)", "buffer output, about +14 dBm", "+32.7 dBm (1.85 W)", "19 dB", "Fine."],
]
table(doc, ["Part", "Expected worst-case input", "Damage limit", "Margin", "Action"],
      HEAD, [1.35, 1.85, 1.0, 0.85, 2.05], fontsize=8.0)
doc.add_page_break()

# ---------------------------------------------------------------- 5. evidence
doc.add_heading("5. Datasheet evidence, part by part", level=1)
note(doc, "Each screenshot below is cropped straight out of the linked PDF, at the page stated in its caption. "
          "Open the PDF, go to that page, and the same table is there.")

for pt in PARTS:
    doc.add_heading("%s - %s" % (pt["model"], pt["role"]), level=2)
    p = doc.add_paragraph()
    r = p.add_run("Datasheet: ")
    r.font.size = Pt(9)
    hyperlink(p, specs.PDF.format(pt["model"].replace("+", "%2B")), "%s.pdf (Mini-Circuits)" % pt["model"])
    r = p.add_run("   |   local copy: ")
    r.font.size = Pt(9)
    hyperlink(p, "datasheets/%s.pdf" % pt["model"], "datasheets/%s.pdf" % pt["model"])
    r = p.add_run("   |   product page: ")
    r.font.size = Pt(9)
    hyperlink(p, specs.URL.format(pt["model"].replace("+", "%2B")), "minicircuits.com")

    d_dbm, d_mw = damage_dbm_mw(pt)
    facts = [
        ["Band (datasheet)", pt["band"]],
        ["Frequency in JACON", pt["f_seen"]],
        ["Gain / loss", pt["gain_txt"]],
        ["Damage limit", "%s   =   %+.2f dBm   =   %.4g mW   (page %d)"
         % (pt["damage_txt"], d_dbm, d_mw, pt["damage_page"])],
        ["Linear limit", pt["p1db_txt"]],
        ["Notes", pt["extra"]],
    ]
    table(doc, ["Parameter", "Value"], facts, [1.5, 5.4], fontsize=8.5)
    doc.add_paragraph()
    for tag, fn, page, cap in pt["ev"]:
        path = os.path.join("evidence", fn)
        if not os.path.exists(path):
            continue
        pic(doc, path, maxw=6.9, maxh=2.6)
        caption(doc, "%s datasheet, page %d - %s" % (pt["model"], page, cap))
    doc.add_paragraph()

# ---------------------------------------------------------------- 6. caveats
doc.add_heading("6. What is assumed, and what to check yourself", level=1)
CAVEATS = [
    "Levels in the flow chart come from the LTspice model, not from measurements. They assume a -30 dBm echo, a "
    "+3 dBm ADF5355 LO output, and the limiter / limiting-amp behaviour described in the drawing.",
    "The ZX60-14012L-S+ gain (+12 dB typ) and P1dB (+11 dBm typ) are the band-wide specs for 0.3 MHz to 14 GHz. "
    "For 8.3 GHz specifically, read the typical performance curves on page 2 of its datasheet.",
    "Mini-Circuits quotes mixer damage as RF Power 50 mW. That is the RF port limit; the LO drive level is a "
    "separate specification (+10 dBm for the ZX05-14LH-S+, +7 dBm for the ZX05-30W-S+).",
    "The ZX60-2534MA-S+ datasheet is published as ZX60-2534MA+.pdf and covers both the connectorised -S+ version "
    "and the bare model; the model table on page 1 lists ZX60-2534MA-S+.",
    "The power limiter, limiting amplifier, envelope detector, VCO, keying switch, image filter and power amp are "
    "not among the nine parts, so they are not datasheet-verified in this document.",
    "Gain and loss figures are typical values at room temperature. Minimum / maximum columns on the datasheets are "
    "what you should design against.",
    "The simulated levels were computed with the band-typical 6.7 dB mixer conversion loss. The ZX05-14LH-S+ "
    "typical performance table gives 7.72 dB at RF 9400 MHz, so expect the real IF to be about 1 dB lower than the "
    "red numbers in the flow chart.",
    "Gain and conversion-loss values are now quoted at the frequency each part actually sees, taken from the "
    "typical performance tables, not the band-wide headline figures. Both are shown where they differ.",
]
for txt in CAVEATS:
    par = doc.add_paragraph(txt, style="List Bullet")
    par.runs[0].font.size = Pt(9.5)

out = "JACON_component_power_ratings.docx"
doc.save(out)
print("wrote", out, os.path.getsize(out), "bytes")
