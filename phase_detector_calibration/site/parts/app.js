(function () {
  // ---------------------------------------------------------------- tabs
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));
  var tabButtons = Array.prototype.slice.call(document.querySelectorAll(".tabs button"));
  var navGroups = Array.prototype.slice.call(document.querySelectorAll("nav [data-tab]"));
  function show(id) {
    panels.forEach(function (p) { p.hidden = p.id !== id; });
    tabButtons.forEach(function (b) { b.setAttribute("aria-selected", b.dataset.panel === id ? "true" : "false"); });
    navGroups.forEach(function (g) { g.hidden = g.dataset.tab !== id; });
  }
  function route(scroll) {
    var h = location.hash.slice(1);
    var el = h && document.getElementById(h);
    if (!el) { show(panels[0].id); return; }
    var p = el.classList.contains("panel") ? el : el.closest(".panel");
    if (!p) return;
    show(p.id);
    for (var d = el; d && d !== p; d = d.parentElement) if (d.tagName === "DETAILS") d.open = true;   // open whatever holds the target
    if (scroll === false) return;
    if (el !== p) el.scrollIntoView({ block: "start" });
    else if (window.scrollY > 300) document.querySelector(".tabs").scrollIntoView({ block: "start" });
  }
  tabButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      show(b.dataset.panel);                                   // switch at once; the address is a convenience
      try { history.replaceState(null, "", "#" + b.dataset.panel); } catch (e) {}
    });
  });
  window.addEventListener("hashchange", function () { route(true); });
  document.addEventListener("click", function (e) {            // in-page links work even where the address cannot change
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if (!el) return;
    e.preventDefault();
    var p = el.classList.contains("panel") ? el : el.closest(".panel");
    if (p) show(p.id);
    for (var d = el; d && d !== p; d = d.parentElement) if (d.tagName === "DETAILS") d.open = true;
    (el === p ? document.querySelector(".tabs") : el).scrollIntoView({ block: "start" });
    try { history.replaceState(null, "", a.getAttribute("href")); } catch (err) {}
  });
  function setAll(open) {
    var p = panels.filter(function (x) { return !x.hidden; })[0];
    if (p) Array.prototype.slice.call(p.querySelectorAll("details.item")).forEach(function (d) { d.open = open; });
  }
  document.getElementById("exp-all").addEventListener("click", function () { setAll(true); });
  document.getElementById("col-all").addEventListener("click", function () { setAll(false); });
  route(true);

  // schematic: show specs or measured data inside each block
  var schem = document.getElementById("schem"), bSpecs = document.getElementById("sch-specs"), bData = document.getElementById("sch-data");
  function schemMode(m) {
    schem.setAttribute("data-mode", m);
    bSpecs.setAttribute("aria-pressed", m === "specs" ? "true" : "false");
    bData.setAttribute("aria-pressed", m === "data" ? "true" : "false");
  }
  if (schem && bSpecs && bData) {
    bSpecs.addEventListener("click", function () { schemMode("specs"); });
    bData.addEventListener("click", function () { schemMode("data"); });
  }

  // ---------------------------------------------------------------- living document
  var statusEl = document.getElementById("doc-status");
  var readBtn = document.getElementById("mode-read");
  var editBtn = document.getElementById("mode-edit");
  var countEl = document.getElementById("mark-count");
  var tools = document.getElementById("seltools");
  var ALLOWED = { MARK: 1, B: 1, STRONG: 1, I: 1, EM: 1, CODE: 1, BR: 1, A: 1, SUB: 1, SUP: 1, SPAN: 1 };

  function hash(s) { var h = 5381; for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; return h.toString(36); }

  // Shared edits come from other people, so everything is rebuilt from a short allow-list.
  function sanitize(html) {
    var t = document.createElement("template");
    t.innerHTML = html;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (c) {
        if (c.nodeType === 3) return;
        if (c.nodeType !== 1 || !ALLOWED[c.tagName]) {
          if (c.nodeType === 1) { walk(c); while (c.firstChild) node.insertBefore(c.firstChild, c); }
          node.removeChild(c);
          return;
        }
        var keep = {};
        if (c.tagName === "MARK") { var k = c.getAttribute("data-k"); if (k === "ok" || k === "q") keep["data-k"] = k; }
        if (c.tagName === "A") { var href = c.getAttribute("href") || ""; if (/^(https:\/\/|#)/.test(href)) keep.href = href; }
        if (c.tagName === "SPAN") { var cl = c.getAttribute("class"); if (cl === "src" || cl === "pill" || cl === "pill tested") keep["class"] = cl; }
        Array.prototype.slice.call(c.attributes).forEach(function (a) { c.removeAttribute(a.name); });
        Object.keys(keep).forEach(function (n) { c.setAttribute(n, keep[n]); });
        if (c.tagName === "MARK" && !keep["data-k"]) { walk(c); while (c.firstChild) node.insertBefore(c.firstChild, c); node.removeChild(c); return; }
        walk(c);
      });
    })(t.content);
    return t.innerHTML;
  }

  var blocks = {};
  Array.prototype.slice.call(document.querySelectorAll("main p, main li, main td, main h3, main h4")).forEach(function (el) {
    var text = el.textContent;
    if (text.indexOf("\\(") >= 0 || text.indexOf("\\[") >= 0) return;         // math is rendered by MathJax; leave it alone
    if (el.closest(".math, pre, .tabs, .bar, .schematic, .lut") || el.querySelector("p, li, table, figure, .math")) return;
    if (!text.trim()) return;
    var id = "b" + hash(text.trim()), n = 2;
    while (blocks[id]) id = "b" + hash(text.trim()) + "_" + n++;
    el.setAttribute("data-block", id);
    blocks[id] = { el: el, orig: sanitize(el.innerHTML), saved: null, pending: Promise.resolve() };
  });

  // a downloaded backup carries the edits that were live when it was saved
  if (window.__SAVED_EDITS) Object.keys(window.__SAVED_EDITS).forEach(function (id) {
    if (blocks[id]) { blocks[id].el.innerHTML = sanitize(String(window.__SAVED_EDITS[id])); blocks[id].el.classList.add("changed"); }
  });

  function countMarks() {
    var ok = document.querySelectorAll('.panel mark[data-k="ok"]').length, q = document.querySelectorAll('.panel mark[data-k="q"]').length;
    countEl.textContent = ok + " validated, " + q + " under question";
  }
  countMarks();

  var db = null, uid = null, comments = null, canWrite = false, editing = false;
  function setStatus(s) { statusEl.textContent = s; }

  function setEditing(on) {
    editing = on && canWrite;
    document.body.classList.toggle("editing", editing);
    readBtn.setAttribute("aria-pressed", editing ? "false" : "true");
    editBtn.setAttribute("aria-pressed", editing ? "true" : "false");
    Object.keys(blocks).forEach(function (id) {
      if (editing) blocks[id].el.setAttribute("contenteditable", "true"); else blocks[id].el.removeAttribute("contenteditable");
    });
    hideTools();
    setStatus(editing ? "Editing. Changes save for everyone." : (canWrite ? "Read only. Nothing you do here changes the page." : statusEl.textContent));
  }
  readBtn.addEventListener("click", function () { setEditing(false); });
  editBtn.addEventListener("click", function () { setEditing(true); });

  function save(id) {
    var b = blocks[id];
    if (!db || !canWrite) return;
    var html = sanitize(b.el.innerHTML);
    if (html === (b.saved === null ? b.orig : b.saved)) return;
    b.saved = html;
    b.el.classList.toggle("changed", html !== b.orig);
    setStatus("Saving…");
    b.pending = b.pending.then(function () {
      var ref = db.collection("blocks").doc(id);
      return html === b.orig ? ref.delete() : ref.set({ html: html, by: uid || "", at: Date.now() });
    }).then(function () { setStatus("Saved."); }, function (e) {
      if (e && e.code === "invalid_argument") { canWrite = false; editBtn.disabled = true; setEditing(false); setStatus("You have view access, so edits are off."); }
      else setStatus("Could not save that change. Try again.");
    });
    countMarks();
  }

  var timers = {};
  document.addEventListener("input", function (e) {
    var el = e.target.closest && e.target.closest("[data-block]");
    if (!el || !editing) return;
    var id = el.getAttribute("data-block");
    clearTimeout(timers[id]);
    timers[id] = setTimeout(function () { save(id); }, 1500);
  });
  document.addEventListener("focusout", function (e) {
    var el = e.target.closest && e.target.closest("[data-block]");
    if (el && editing) { var id = el.getAttribute("data-block"); clearTimeout(timers[id]); save(id); }
  });
  document.addEventListener("keydown", function (e) {
    if (editing && e.key === "Enter" && e.target.closest && e.target.closest("[data-block]")) { e.preventDefault(); document.execCommand("insertLineBreak"); }
  });
  document.addEventListener("paste", function (e) {
    if (!editing || !(e.target.closest && e.target.closest("[data-block]"))) return;
    e.preventDefault();
    document.execCommand("insertText", false, (e.clipboardData || window.clipboardData).getData("text/plain"));
  });

  // ---- selection toolbar: validated / under question / clear / comment
  function selBlock() {
    var s = window.getSelection();
    if (!s || s.rangeCount === 0 || s.isCollapsed) return null;
    var r = s.getRangeAt(0);
    var a = r.startContainer.nodeType === 1 ? r.startContainer : r.startContainer.parentElement;
    var z = r.endContainer.nodeType === 1 ? r.endContainer : r.endContainer.parentElement;
    var ba = a && a.closest("[data-block]"), bz = z && z.closest("[data-block]");
    if (!ba || ba !== bz) return null;
    return { range: r, el: ba, id: ba.getAttribute("data-block") };
  }
  function hideTools() { tools.hidden = true; }
  function showTools() {
    var sb = selBlock();
    if (!sb || (!editing && !comments)) { hideTools(); return; }
    Array.prototype.slice.call(tools.querySelectorAll("[data-edit]")).forEach(function (b) { b.hidden = !editing; });
    tools.querySelector('[data-act="comment"]').hidden = !comments;
    tools.querySelector('[data-act="restore"]').hidden = !editing || !sb.el.classList.contains("changed");
    var rect = sb.range.getBoundingClientRect();
    tools.hidden = false;
    tools.style.top = (rect.bottom + window.scrollY + 6) + "px";
    tools.style.left = Math.max(8, Math.min(rect.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - tools.offsetWidth - 8)) + "px";
  }
  document.addEventListener("selectionchange", function () { setTimeout(showTools, 0); });
  tools.addEventListener("mousedown", function (e) { e.preventDefault(); });   // keep the selection

  function unwrap(m) { var p = m.parentNode; while (m.firstChild) p.insertBefore(m.firstChild, m); p.removeChild(m); }
  function clearMarks(sb) {
    Array.prototype.slice.call(sb.el.querySelectorAll("mark")).forEach(function (m) { if (sb.range.intersectsNode(m)) unwrap(m); });
    sb.el.normalize();
  }
  tools.addEventListener("click", function (e) {
    var btn = e.target.closest("button");
    var sb = selBlock();
    if (!btn || !sb) return;
    var act = btn.dataset.act;
    if (act === "comment") {
      if (comments) comments.openComposer({ range: sb.range }).catch(function () { comments = null; hideTools(); });
      return;
    }
    if (!editing) return;
    if (act === "restore") { sb.el.innerHTML = blocks[sb.id].orig; }
    else if (act === "clear") { clearMarks(sb); }
    else {
      var r = sb.range;
      var frag = r.extractContents();
      Array.prototype.slice.call(frag.querySelectorAll("mark")).forEach(unwrap);
      var m = document.createElement("mark");
      m.setAttribute("data-k", act);
      m.appendChild(frag);
      r.insertNode(m);
      var outer = m.parentElement && m.parentElement.closest("mark");
      if (outer) unwrap(outer);
      Array.prototype.slice.call(sb.el.querySelectorAll("mark")).forEach(function (x) { if (!x.textContent) x.remove(); });
    }
    window.getSelection().removeAllRanges();
    hideTools();
    save(sb.id);
  });

  // ---- connect to the shared store (absent when the file is opened from disk)
  function applyRemote(snap) {
    var seen = {};
    snap.docs.forEach(function (d) {
      var b = blocks[d.id], data = d.data();
      if (!b || !data || typeof data.html !== "string") return;
      seen[d.id] = 1;
      var html = sanitize(data.html);
      b.saved = html;
      if (b.el.contains(document.activeElement) || b.el === document.activeElement) return;   // don't yank text someone is typing in
      if (sanitize(b.el.innerHTML) !== html) b.el.innerHTML = html;
      b.el.classList.toggle("changed", html !== b.orig);
    });
    Object.keys(blocks).forEach(function (id) {
      var b = blocks[id];
      if (!seen[id] && b.saved !== null && b.el !== document.activeElement) { b.saved = null; b.el.innerHTML = b.orig; b.el.classList.remove("changed"); }
    });
    countMarks();
  }
  // ---- download a self-contained copy of the page (all plots inside one .html file) with the current edits
  var dlBtn = document.getElementById("dl-backup");
  function offerDownload(downloads) {
    dlBtn.hidden = false;
    dlBtn.addEventListener("click", function () {
      dlBtn.disabled = true;
      setStatus("Preparing the backup\u2026");
      fetch("JACON_notes_standalone.html").then(function (r) { if (!r.ok) throw new Error("fetch"); return r.text(); }).then(function (text) {
        var edits = {};
        Object.keys(blocks).forEach(function (id) { var h = sanitize(blocks[id].el.innerHTML); if (h !== blocks[id].orig) edits[id] = h; });
        var tag = "<scr" + "ipt>window.__SAVED_EDITS=" + JSON.stringify(edits).replace(/</g, "\\u003c") + ";</scr" + "ipt>\n";
        var at = text.indexOf("<!--APP-->");
        if (at < 0) throw new Error("marker");
        text = text.slice(0, at) + tag + text.slice(at);
        var d = new Date(), name = "JACON_notes_backup_" + d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2) + ".html";
        return downloads.save({ filename: name, data: new Blob([text]) });
      }).then(function () { setStatus("Backup saved."); }, function (e) {
        setStatus(e && e.code === "declined" ? "Backup not saved." : "Could not make the backup here. A copy is kept on the computer in clinic\\claude\\JACON_notes_backup.html.");
      }).then(function () { dlBtn.disabled = false; });
    });
  }

  var use = window.claude && window.claude.use;
  if (!use) { setStatus("Read only copy. To change this page, edit the files in phase_detector_calibration/site and run build_site.py (see README)."); return; }
  setStatus("Connecting…");
  window.claude.use("downloads").then(function (d) { if (d) offerDownload(d); });
  Promise.all([window.claude.use("db"), window.claude.use("user"), window.claude.use("comments")]).then(function (r) {
    db = r[0]; var user = r[1]; comments = r[2];
    if (!db) { setStatus("Shared edits are not available in this view."); return; }
    db.collection("blocks").onSnapshot(applyRemote, function () { setStatus("Lost the connection to shared edits. Reload to reconnect."); });
    var ask = user ? Promise.all([user.can("data.write"), user.id ? user.id() : null]) : Promise.resolve([null, null]);
    return ask.then(function (a) {
      uid = a[1];
      canWrite = a[0] !== false;
      editBtn.disabled = !canWrite;
      setStatus(canWrite ? "Read only. Nothing you do here changes the page." : "You have view access, so edits are off.");
    });
  }).catch(function () { setStatus("Shared edits are not available in this view."); });
})();
