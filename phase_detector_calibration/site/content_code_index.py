"""Code library tab: every Python file in clinic/claude with its docstring, functions and classes, read with ast at build time.
A lookup table of what already exists, so a task starts from existing code instead of a new copy."""
import ast
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKIP = {"site_backups", "chaos_scope", "__pycache__", ".git", "docs", "site", "node_modules"}


def _sig(f):
    a = f.args
    names = [x.arg for x in a.posonlyargs + a.args] + ([f"*{a.vararg.arg}"] if a.vararg else []) + [x.arg for x in a.kwonlyargs] + ([f"**{a.kwarg.arg}"] if a.kwarg else [])
    return f"{f.name}({', '.join(names)})"


def _first(node):
    d = ast.get_docstring(node) or ""
    return d.strip().split("\n\n")[0].replace("\n", " ")


def _entries():
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT)
        if SKIP & set(rel.parts[:-1]) or p.name.startswith("_patch"):
            continue
        try:
            t = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        defs = [(("class " if isinstance(n, ast.ClassDef) else "") + (n.name if isinstance(n, ast.ClassDef) else _sig(n)), _first(n))
                for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith("_")]
        yield rel.as_posix(), _first(t), defs, sum(1 for _ in open(p, encoding="utf-8", errors="ignore"))


def tab():
    e = html.escape
    rows = "".join(
        f'<details class="item code-entry"><summary><code>{e(path)}</code> &mdash; {e(doc[:160]) or "<i>no docstring</i>"} <span class="sub">({n} lines)</span></summary>'
        f'<div class="body"><p>{e(doc)}</p><ul>' + "".join(f"<li><code>{e(s)}</code> {e(d)}</li>" for s, d in defs) + "</ul></div></details>"
        for path, doc, defs, n in _entries())
    return ("<h2>Code library</h2>"
            "<p>Every Python file in the project folder, with what it does and the functions it offers. Generated from the code itself at every build, so it is always current. "
            "Search before writing anything new. Local folder: <code>C:\\ThatFamily Dropbox\\Sorin Jayaweera\\allSaves\\mudd\\senior\\clinic\\claude\\</code>; the same paths are on GitHub.</p>"
            '<div class="bar"><input id="code-search" type="search" placeholder="search code (e.g. tone_off, scope, wiring, csv)" aria-label="Search code" '
            'oninput="var w=this.value.toLowerCase().split(/\\s+/).filter(Boolean);document.querySelectorAll(\'.code-entry\').forEach(function(d){d.hidden=!w.every(function(x){return d.textContent.toLowerCase().indexOf(x)>=0})})"></div>'
            + rows)
