// Review on the GitHub copy of the page. There is no shared store here, so marks and comments are GitHub issues:
// pressing a button opens a new issue with the quote filled in, written with the reader's own GitHub account.
// The page reads the open issues back and highlights the quoted text. Appended to app.js by build_site.py.
(function () {
  if (window.claude && window.claude.use) {                       // the Claude-hosted page has its own shared edits
    var rs = document.getElementById("review-status");
    if (rs) rs.textContent = "The notes are listed on the GitHub copy of this page. This copy has its own highlights and comments (press Edit).";
    return;
  }
  var REPO = "Sorin-Jayaweera/Panthalassa-Clinic-Team";
  var SITE = "https://sorin-jayaweera.github.io/Panthalassa-Clinic-Team/";
  var KINDS = { validated: "ok", question: "q", comment: "c", change: "c" };
  var NAMES = { validated: "Validated", question: "Under question", comment: "Comment", change: "Suggested change" };
  var statusEl = document.getElementById("doc-status"), readBtn = document.getElementById("mode-read"), editBtn = document.getElementById("mode-edit");
  var tools = document.getElementById("seltools"), countEl = document.getElementById("mark-count");
  var listEl = document.getElementById("review-list"), listStatus = document.getElementById("review-status");
  if (!editBtn || !tools) return;
  var reviewing = false;

  function setMode(on) {
    reviewing = on;
    document.body.classList.toggle("reviewing", on);
    readBtn.setAttribute("aria-pressed", on ? "false" : "true");
    editBtn.setAttribute("aria-pressed", on ? "true" : "false");
    tools.hidden = true;
    statusEl.textContent = on ? "Select text, then choose Validated, Under question, Comment or Suggest a change. It opens a GitHub issue to submit."
                              : "Read only. Press Edit to mark or comment on text (uses your GitHub account).";
  }
  editBtn.disabled = false;
  editBtn.title = "Mark text as validated or under question, comment, or suggest a change. Uses GitHub issues.";
  readBtn.addEventListener("click", function () { setMode(false); });
  editBtn.addEventListener("click", function () { setMode(true); });
  setMode(false);

  function sel() {
    var s = window.getSelection();
    if (!s || s.rangeCount === 0 || s.isCollapsed) return null;
    var r = s.getRangeAt(0);
    var a = r.startContainer.nodeType === 1 ? r.startContainer : r.startContainer.parentElement;
    var z = r.endContainer.nodeType === 1 ? r.endContainer : r.endContainer.parentElement;
    var ba = a && a.closest("[data-block]"), bz = z && z.closest("[data-block]");
    if (!ba || ba !== bz) return null;
    return { range: r, el: ba, text: s.toString().replace(/\s+/g, " ").trim() };
  }
  function place() {
    var sb = sel();
    if (!sb || !reviewing || !sb.text) { tools.hidden = true; return; }
    Array.prototype.slice.call(tools.querySelectorAll("button")).forEach(function (b) {
      b.hidden = !({ ok: 1, q: 1, comment: 1, suggest: 1 })[b.dataset.act];
    });
    var rect = sb.range.getBoundingClientRect();
    tools.hidden = false;
    tools.style.top = (rect.bottom + window.scrollY + 6) + "px";
    tools.style.left = Math.max(8, Math.min(rect.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - tools.offsetWidth - 8)) + "px";
  }
  document.addEventListener("selectionchange", function () { setTimeout(place, 0); });

  function where(el) {
    var panel = el.closest(".panel"), item = el.closest("details.item");
    var tabBtn = panel && document.querySelector('.tabs button[data-panel="' + panel.id + '"]');
    var sum = item && item.querySelector("summary");
    return { tab: tabBtn ? tabBtn.textContent.trim() : "", section: sum ? sum.textContent.trim() : "", anchor: (item && item.id) || (panel && panel.id) || "" };
  }
  tools.addEventListener("click", function (e) {
    var btn = e.target.closest("button"), sb = sel();
    if (!btn || !sb || !reviewing) return;
    var kind = { ok: "validated", q: "question", comment: "comment", suggest: "change" }[btn.dataset.act];
    if (!kind) return;
    e.stopImmediatePropagation();
    var w = where(sb.el), quote = sb.text.slice(0, 400);
    var title = "[" + kind + "] " + w.tab + ": " + quote.slice(0, 70) + (quote.length > 70 ? "..." : "");
    var body = "<!-- jacon-review -->\n**Kind:** " + kind + "\n**Tab:** " + w.tab + "\n**Section:** " + w.section + "\n**Block:** " + sb.el.getAttribute("data-block") +
      "\n**Quote:** " + quote + "\n**Link:** " + SITE + "#" + w.anchor + "\n\n**Note:**\n\n" +
      (kind === "change" ? "Change it to:\n\n" : kind === "validated" ? "(optional: how you checked it)\n" : "(write your " + (kind === "question" ? "question or doubt" : "comment") + " here)\n");
    window.open("https://github.com/" + REPO + "/issues/new?title=" + encodeURIComponent(title) + "&body=" + encodeURIComponent(body), "_blank", "noopener");
    window.getSelection().removeAllRanges();
    tools.hidden = true;
  }, true);

  // ---- read the notes back
  function parse(issue) {
    var body = issue.body || "", t = /^\[(validated|question|comment|change)\]/i.exec(issue.title || "");
    if (!t || body.indexOf("jacon-review") < 0) return null;
    function field(n) { var m = new RegExp("\\*\\*" + n + ":\\*\\*[ \\t]*(.*)").exec(body); return m ? m[1].trim() : ""; }
    var note = body.split(/\*\*Note:\*\*/)[1] || "";
    note = note.replace(/\(optional: how you checked it\)|\(write your [a-z ]+ here\)/g, "").trim();
    return { kind: t[1].toLowerCase(), tab: field("Tab"), section: field("Section"), block: field("Block"), quote: field("Quote"), link: field("Link"), note: note,
             by: (issue.user && issue.user.login) || issue.by || "", at: (issue.created_at || issue.at || "").slice(0, 10), url: issue.html_url || issue.url || "", number: issue.number, replies: issue.comments || issue.replies || 0 };
  }
  function wrap(el, quote, k, tip, url) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), n;
    while ((n = walker.nextNode())) {
      var flat = n.nodeValue.replace(/\s+/g, " ");
      var i = flat.indexOf(quote);
      if (i < 0 || flat.length !== n.nodeValue.length) continue;
      var r = document.createRange();
      r.setStart(n, i); r.setEnd(n, i + quote.length);
      var m = document.createElement("mark");
      m.setAttribute("data-k", k); m.setAttribute("data-issue", url); m.title = tip;
      r.surroundContents(m);
      m.addEventListener("click", function () { window.open(url, "_blank", "noopener"); });
      return true;
    }
    return false;
  }
  function render(items, source) {
    Array.prototype.slice.call(document.querySelectorAll("mark[data-issue]")).forEach(function (m) { var p = m.parentNode; while (m.firstChild) p.insertBefore(m.firstChild, m); p.removeChild(m); p.normalize(); });
    var counts = { validated: 0, question: 0, comment: 0, change: 0 }, rows = [];
    items.forEach(function (it) {
      counts[it.kind]++;
      var el = it.block && document.querySelector('[data-block="' + it.block.replace(/[^a-z0-9_]/gi, "") + '"]');
      var tip = NAMES[it.kind] + " by " + it.by + ", " + it.at + (it.note ? ": " + it.note.slice(0, 300) : "") + " (click to open)";
      var found = el ? (wrap(el, it.quote, KINDS[it.kind], tip, it.url) || (el.classList.add("noted"), el.title = tip, true)) : false;
      rows.push([it, found, el]);
    });
    if (countEl) countEl.textContent = counts.validated + " validated, " + counts.question + " under question, " + (counts.comment + counts.change) + " comments";
    if (!listEl) return;
    listEl.textContent = "";
    listStatus.textContent = items.length ? items.length + " open notes (" + source + ")." : "No notes yet (" + source + ").";
    if (!items.length) return;
    var table = document.createElement("table"), head = document.createElement("tr");
    ["Kind", "Where", "Quoted text", "Note", "By", "Date", ""].forEach(function (h) { var th = document.createElement("th"); th.textContent = h; head.appendChild(th); });
    table.appendChild(head);
    rows.forEach(function (row) {
      var it = row[0], tr = document.createElement("tr");
      function td(text, cls) { var c = document.createElement("td"); c.textContent = text; if (cls) c.className = cls; tr.appendChild(c); return c; }
      td(NAMES[it.kind]);
      var w = td("");
      var a = document.createElement("a");
      a.textContent = it.tab + (it.section ? ", " + it.section : "");
      a.href = "#" + ((row[2] && (row[2].closest("details.item") || row[2].closest(".panel")) || {}).id || "");
      w.appendChild(a);
      if (!row[1]) w.appendChild(document.createTextNode(" (the text has changed since)"));
      td(it.quote, "quote"); td(it.note + (it.replies ? " [" + it.replies + " replies]" : "")); td(it.by); td(it.at);
      var l = td(""), g = document.createElement("a");
      g.textContent = "#" + it.number; g.href = it.url; g.target = "_blank"; g.rel = "noopener";
      l.appendChild(g);
      table.appendChild(tr);
    });
    listEl.appendChild(table);
  }
  function ok(u) { return typeof u === "string" && u.indexOf("https://github.com/" + REPO + "/issues/") === 0; }
  function load() {
    fetch("https://api.github.com/repos/" + REPO + "/issues?state=open&per_page=100", { headers: { Accept: "application/vnd.github+json" } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (list) { render(list.filter(function (i) { return !i.pull_request; }).map(parse).filter(function (x) { return x && ok(x.url); }), "live from GitHub"); })
      .catch(function () {
        fetch("review.json").then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (d) { render((d.open || []).filter(function (x) { return x && KINDS[x.kind] && ok(x.url); }), "saved copy from " + (d.updated || "earlier")); })
          .catch(function () { if (listStatus) listStatus.textContent = "Could not load the notes. See the issues on GitHub."; });
      });
  }
  load();
  document.addEventListener("visibilitychange", function () { if (!document.hidden) load(); });   // coming back from submitting an issue
})();
