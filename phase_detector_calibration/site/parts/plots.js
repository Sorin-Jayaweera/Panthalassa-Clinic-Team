
// ---------------------------------------------------------------- all plots + stars (added 16 Nov)
// Every <figure> on the page is collected into the "All plots" grid, newest first (dates from the image files at build time).
// Stars: shared stars come from site/stars.json (built into the page, so everyone sees them); your own stars and un-stars are kept in
// this browser only. "Copy my stars" puts your list on the clipboard so it can be added to stars.json for the whole team.
(function () {
  var DATES = window.PLOT_DATES || {};
  var SHARED = window.PLOT_STARS_SHARED || [];
  var KEY = "jacon-plot-stars-v1";
  var local = { add: [], remove: [] };
  try { var s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.add) local = s; } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(local)); } catch (e) {} }
  function starred(k) { return (SHARED.indexOf(k) >= 0 && local.remove.indexOf(k) < 0) || local.add.indexOf(k) >= 0; }
  function toggle(k) {
    var on = !starred(k);
    local.add = local.add.filter(function (x) { return x !== k; });
    local.remove = local.remove.filter(function (x) { return x !== k; });
    if (on && SHARED.indexOf(k) < 0) local.add.push(k);
    if (!on && SHARED.indexOf(k) >= 0) local.remove.push(k);
    save(); refresh();
  }
  function keyOf(img) { var s = img.getAttribute("src") || ""; return s.split("/").pop(); }

  // collect plots
  var plots = [], seen = {};
  Array.prototype.slice.call(document.querySelectorAll(".panel figure")).forEach(function (f, i) {
    var img = f.querySelector("img"); if (!img) return;
    var panel = f.closest(".panel"); if (!panel || panel.id === "tab-plots") return;
    var k = keyOf(img);
    if (!f.id) f.id = "fig-" + i;
    var det = f.closest("details.item");
    var sec = det ? (det.querySelector("summary") || {}).textContent || "" : "";
    var tabBtn = document.querySelector('.tabs button[data-panel="' + panel.id + '"]');
    var p = { key: k, src: img.getAttribute("src"), alt: img.getAttribute("alt") || "", fig: f, panel: panel.id,
              tab: tabBtn ? tabBtn.textContent : panel.id, section: sec.trim(), date: DATES[k] || "" };
    // star button on the figure in place
    var b = document.createElement("button");
    b.type = "button"; b.className = "star"; b.dataset.key = k; b.title = "Star this plot";
    b.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); toggle(k); });
    f.classList.add("starrable"); f.appendChild(b);
    if (seen[k]) return; seen[k] = 1;
    plots.push(p);
  });
  plots.sort(function (a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; });

  function tile(p) {
    var d = document.createElement("div"); d.className = "ptile"; d.dataset.key = p.key;
    d.innerHTML = '<a class="pthumb" href="#' + p.fig.id + '" title="Go to this plot in its section"><img loading="lazy" alt=""></a>'
      + '<div class="pcap"><span class="ptab"></span> <span class="pdate"></span><br><span class="psec"></span></div>';
    d.querySelector("img").src = p.src; d.querySelector("img").alt = p.alt;
    d.querySelector(".ptab").textContent = p.tab;
    d.querySelector(".pdate").textContent = p.date ? p.date.slice(0, 10) : "";
    d.querySelector(".psec").textContent = p.section || p.alt;
    var b = document.createElement("button"); b.type = "button"; b.className = "star"; b.dataset.key = p.key; b.title = "Star this plot";
    b.addEventListener("click", function () { toggle(p.key); });
    d.appendChild(b);
    return d;
  }

  // the All plots tab
  var grid = document.getElementById("plotgrid");
  var q = document.getElementById("plot-search"), only = document.getElementById("plot-starred-only"), cnt = document.getElementById("plot-count");
  var tiles = plots.map(function (p) { var t = tile(p); if (grid) grid.appendChild(t); return { p: p, el: t }; });
  function filter() {
    var words = (q && q.value || "").toLowerCase().split(/\s+/).filter(Boolean), n = 0;
    tiles.forEach(function (t) {
      var hay = (t.p.alt + " " + t.p.key + " " + t.p.section + " " + t.p.tab + " " + t.p.date).toLowerCase();
      var ok = words.every(function (w) { return hay.indexOf(w) >= 0; }) && (!only || only.getAttribute("aria-pressed") !== "true" || starred(t.p.key));
      t.el.hidden = !ok; if (ok) n++;
    });
    if (cnt) cnt.textContent = n + " of " + tiles.length + " plots";
  }
  if (q) q.addEventListener("input", filter);
  if (only) only.addEventListener("click", function () { only.setAttribute("aria-pressed", only.getAttribute("aria-pressed") === "true" ? "false" : "true"); filter(); });
  var cols = document.getElementById("plot-cols");
  if (cols && grid) cols.addEventListener("input", function () { grid.style.setProperty("--pcols", cols.value); });
  var copy = document.getElementById("plot-copy-stars");
  if (copy) copy.addEventListener("click", function () {
    var all = plots.filter(function (p) { return starred(p.key); }).map(function (p) { return p.key; });
    var txt = JSON.stringify(all, null, 1);
    try { navigator.clipboard.writeText(txt); copy.textContent = "Copied " + all.length + " stars"; } catch (e) { window.prompt("Your starred plots:", txt); }
  });

  // a "Starred plots" section at the top of every tab, and an "All starred plots" block in the All plots tab
  var subs = {};
  Array.prototype.slice.call(document.querySelectorAll(".panel")).forEach(function (panel) {
    if (panel.id === "tab-plots") return;
    if (!plots.some(function (p) { return p.panel === panel.id; })) return;
    var d = document.createElement("details"); d.className = "item starred-sub"; d.id = panel.id + "-starred";
    d.innerHTML = '<summary>Starred plots in this tab (<span class="n">0</span>)</summary><div class="body"><p class="sub">Star any plot with the &#9734; in its corner. Stars on the shared list (stars.json) show for everyone; your own stars are kept in this browser.</p><div class="pgrid small"></div></div>';
    var h2 = panel.querySelector(":scope > h2");
    if (h2 && h2.nextSibling) panel.insertBefore(d, h2.nextSibling); else panel.insertBefore(d, panel.firstChild);
    subs[panel.id] = d;
  });
  var allStar = document.getElementById("plot-starred-all");

  function refresh() {
    Array.prototype.slice.call(document.querySelectorAll("button.star")).forEach(function (b) {
      var on = starred(b.dataset.key); b.textContent = on ? "★" : "☆"; b.setAttribute("aria-pressed", on ? "true" : "false");
      b.classList.toggle("on", on);
    });
    Object.keys(subs).forEach(function (pid) {
      var g = subs[pid].querySelector(".pgrid"); g.innerHTML = "";
      var list = plots.filter(function (p) { return p.panel === pid && starred(p.key); });
      list.forEach(function (p) { g.appendChild(tile(p)); });
      subs[pid].querySelector(".n").textContent = list.length;
    });
    if (allStar) {
      allStar.innerHTML = "";
      plots.filter(function (p) { return starred(p.key); }).forEach(function (p) { allStar.appendChild(tile(p)); });
      var n = document.getElementById("plot-starred-n"); if (n) n.textContent = allStar.children.length;
    }
    Array.prototype.slice.call(document.querySelectorAll(".pgrid button.star")).forEach(function (b) {
      var on = starred(b.dataset.key); b.textContent = on ? "★" : "☆"; b.classList.toggle("on", on);
    });
    filter();
  }
  refresh();
})();
