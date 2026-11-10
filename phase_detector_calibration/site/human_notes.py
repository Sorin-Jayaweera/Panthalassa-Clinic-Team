"""Hand-written notes on the site, highlighted gold.

The notes live in ONE file, clinic/claude/docs/human_notes.html (in the repository, served by GitHub Pages next to index.html).
Each <section data-for="ID"> ... </section> in it is shown inside the element with that id: a tab (tab-racon) or a section
(rac-freq). data-pos="bottom" puts it at the end of that element instead of the top. Any HTML works inside a section.

The build never rewrites that file. It embeds a copy in the page (so the offline backup has the notes) and the live page
also fetches the file itself, so an edit committed on GitHub shows on the site about a minute later without a rebuild.
"""
import html
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"
FILE = DOCS / "human_notes.html"
COLOR = "#FFD700"

TEMPLATE = """<!--
  Hand-written notes for the JACON engineering notes site. Everything here is shown highlighted gold.

  One <section> per note. data-for = the id of the tab or section it belongs in:
    tabs:      tab-racon, tab-radar, tab-pluto, ...
    sections:  rac-summary, rac-freq, rac-timing, ...   (the full list is at the bottom of the Review notes tab)
  The note goes at the top of that tab or section; add data-pos="bottom" to put it at the end.
  Any HTML works inside: paragraphs, bold, lists, links, and img tags pointing at plots in the img folder.

  Two ways to edit:
    1. On GitHub: https://github.com/Sorin-Jayaweera/Panthalassa-Clinic-Team/edit/main/docs/human_notes.html
       Commit, and the site shows it about a minute later.
    2. In Dropbox: clinic\\claude\\docs\\human_notes.html, then commit and push (or ask Claude to).
  Deleting a section removes the note.

  Example (remove the comment marks around it to use it):
  <section data-for="rac-freq">
    <p><b>Sorin:</b> my note about the racon frequency.</p>
  </section>
-->
"""

CSS = f"""
.human-note {{ background: {COLOR}; color: #1a1400; border-left: 5px solid #a67c00; border-radius: 4px; padding: 8px 14px; margin: 10px 0; }}
.human-note * {{ color: inherit; }}
.human-note a {{ color: #4a3500; text-decoration: underline; }}
.human-note p {{ margin: 4px 0; }}
.human-note-tag {{ float: right; font-size: 11px; opacity: 0.7; }}
"""

JS = r"""
(function () {
  function place(src) {
    document.querySelectorAll('.human-note').forEach(function (e) { e.remove(); });
    var box = document.createElement('div');
    box.innerHTML = src;
    box.querySelectorAll('section[data-for]').forEach(function (s) {
      var host = document.getElementById(s.getAttribute('data-for'));
      if (!host) { console.warn('human note: no element with id', s.getAttribute('data-for')); return; }
      var d = document.createElement('div');
      d.className = 'human-note';
      d.innerHTML = '<span class="human-note-tag">note</span>' + s.innerHTML;
      var body = host.matches('details') ? host.querySelector(':scope > .body') : host;
      if (!body) body = host;
      if (s.getAttribute('data-pos') === 'bottom') body.appendChild(d);
      else if (host.matches('details')) body.insertBefore(d, body.firstChild);
      else { var h = body.querySelector(':scope > h2'); body.insertBefore(d, h ? h.nextSibling : body.firstChild); }
    });
  }
  var embedded = document.getElementById('human-notes-src');
  if (embedded) place(embedded.textContent);
  if (location.protocol.indexOf('http') === 0) {
    fetch('human_notes.html?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (t) { if (t !== null) place(t); })
      .catch(function () {});
  }
})();
"""


def source():
    DOCS.mkdir(parents=True, exist_ok=True)
    if not FILE.exists():
        FILE.write_text(TEMPLATE, encoding="utf-8")
    return FILE.read_text(encoding="utf-8")


def embed():
    """<script> block holding a copy of the notes file, plus the code that places the notes."""
    src = source().replace("</script", "<\\/script")
    return f'<script type="text/plain" id="human-notes-src">{src}</script>\n<script>{JS}</script>\n'


def id_list(page):
    """Every tab and section id in the page with its title, for the how-to list."""
    tabs = re.findall(r'data-panel="(tab-[a-z0-9-]+)"[^>]*>([^<]+)<', page)
    out = []
    for tid, name in tabs:
        m = re.search(rf'<div class="panel" id="{tid}"', page)
        nxt = re.search(r'<div class="panel" id="', page[m.end():]) if m else None
        chunk = page[m.end(): m.end() + nxt.start()] if nxt else page[m.end():] if m else ""
        items = re.findall(r'<details class="item" id="([^"]+)"[^>]*><summary>(.*?)</summary>', chunk)
        out.append(f"<li><code>{tid}</code> {html.escape(name)}" + (
            "<ul>" + "".join(f"<li><code>{i}</code> {re.sub('<[^>]+>', '', t)}</li>" for i, t in items) + "</ul>" if items else "") + "</li>")
    return "<ul>" + "".join(out) + "</ul>"


HOWTO = f"""<h3 id="human-notes-howto">Hand-written notes (gold)</h3>
<p>Text highlighted <span style="background:{COLOR};color:#1a1400;padding:0 4px">like this</span> was written by a person, not generated.
All of it lives in one file, <code>docs/human_notes.html</code> in the repository
(<a href="https://github.com/Sorin-Jayaweera/Panthalassa-Clinic-Team/edit/main/docs/human_notes.html">edit it on GitHub</a>).
Each <code>&lt;section data-for="ID"&gt;...&lt;/section&gt;</code> in it shows up at the top of the tab or section with that id
(<code>data-pos="bottom"</code> for the end). Any HTML works inside. Rebuilding the site never changes that file; a note stays until someone edits or deletes it.</p>
<details class="item" id="human-notes-ids"><summary>Every tab and section id</summary><div class="body">@@IDS@@</div></details>
"""
