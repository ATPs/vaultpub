/**
 * vaultpub client-side app (minimal inline build).
 * Provides: theme toggle, search, backlinks, graph, callout folding, mobile drawer.
 * The full TypeScript build in frontend/ replaces this with Vite.
 */
(function () {
  "use strict";

  /* ── settings ── */
  function getSettings() {
    try { return JSON.parse(localStorage.getItem("vaultpub.settings") || "{}"); } catch { return {}; }
  }
  function setSettings(p) {
    var s = getSettings();
    Object.assign(s, p);
    localStorage.setItem("vaultpub.settings", JSON.stringify(s));
  }

  /* ── theme ── */
  function applyTheme(t) {
    var h = document.documentElement;
    h.classList.remove("theme-light", "theme-dark");
    if (t === "system") {
      t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    h.classList.add(t === "dark" ? "theme-dark" : "theme-light");
  }
  function toggleTheme() {
    var s = getSettings();
    var t = s.theme || "system";
    var next = t === "light" ? "dark" : t === "dark" ? "system" : "light";
    setSettings({ theme: next });
    applyTheme(next);
  }
  applyTheme(getSettings().theme || "system");
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if ((getSettings().theme || "system") === "system") applyTheme("system");
  });
  var tb = document.getElementById("theme-toggle");
  if (tb) tb.addEventListener("click", toggleTheme);

  /* ── search ── */
  var searchDocs = [];
  fetch("/search-index.json").then(function (r) { return r.ok ? r.json() : Promise.reject(); }).then(function (d) { searchDocs = d; }).catch(function () {
    fetch("/api/search?q=").then(function (r) { return r.ok ? r.json() : []; }).then(function (d) {
      searchDocs = (d && d.results) || [];
    });
  });
  function openSearch() {
    var ov = document.getElementById("search-overlay");
    if (!ov) {
      ov = document.createElement("div");
      ov.id = "search-overlay";
      ov.className = "search-overlay";
      ov.innerHTML = '<div class="search-modal"><div class="search-input-wrapper"><input type="text" id="search-input" placeholder="Search notes..." autocomplete="off"><button id="search-close">&times;</button></div><div id="search-results" class="search-results"></div></div>';
      document.body.appendChild(ov);
      ov.querySelector("#search-close").addEventListener("click", function () { ov.classList.remove("active"); });
      ov.querySelector("#search-input").addEventListener("input", function () { doSearch(this.value); });
      ov.addEventListener("click", function (e) { if (e.target === ov) ov.classList.remove("active"); });
    }
    ov.classList.add("active");
    setTimeout(function () { var inp = document.getElementById("search-input"); if (inp) inp.focus(); }, 50);
  }
  function doSearch(q) {
    var el = document.getElementById("search-results");
    if (!el) return;
    if (!q.trim()) { el.innerHTML = ""; return; }
    var ql = q.toLowerCase();
    var results = searchDocs.filter(function (d) {
      return [d.title, d.content, (d.tags||[]).join(" "), (d.headings||[]).join(" "), (d.aliases||[]).join(" ")].join(" ").toLowerCase().indexOf(ql) !== -1;
    }).slice(0, 20);
    if (!results.length) { el.innerHTML = '<div class="search-empty">No results found</div>'; return; }
    el.innerHTML = results.map(function (d) {
      return '<a class="search-result-item" href="' + d.url + '"><div class="search-result-title">' + d.title + '</div><div class="search-result-excerpt">' + (d.excerpt || "") + '</div></a>';
    }).join("");
  }
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape") { var ov = document.getElementById("search-overlay"); if (ov) ov.classList.remove("active"); }
  });

  /* ── callout folding ── */
  document.querySelectorAll(".callout").forEach(function (c) {
    var fold = c.getAttribute("data-callout-fold");
    var content = c.querySelector(".callout-content");
    if (fold === "closed" && content) content.style.display = "none";
    var title = c.querySelector(".callout-title");
    if (title) {
      title.style.cursor = "pointer";
      title.addEventListener("click", function () {
        if (!content) return;
        var hidden = content.style.display === "none";
        content.style.display = hidden ? "" : "none";
        c.setAttribute("data-callout-fold", hidden ? "open" : "closed");
      });
    }
  });

  /* ── mobile drawer ── */
  var sidebar = document.querySelector(".sidebar-left");
  if (sidebar) {
    var menuBtn = document.getElementById("mobile-menu-btn");
    if (!menuBtn) {
      menuBtn = document.createElement("button");
      menuBtn.id = "mobile-menu-btn";
      menuBtn.className = "mobile-menu-btn";
      menuBtn.innerHTML = "&#9776;";
      var topbar = document.querySelector(".top-bar");
      if (topbar) topbar.prepend(menuBtn);
      else document.querySelector("main.content") && document.querySelector("main.content").prepend(menuBtn);
    }
    menuBtn.addEventListener("click", function () { sidebar.classList.toggle("open"); });
    document.addEventListener("click", function (e) {
      if (window.innerWidth > 768) return;
      if (!sidebar.classList.contains("open")) return;
      if (!sidebar.contains(e.target) && e.target !== menuBtn) sidebar.classList.remove("open");
    });
  }

  /* ── Mermaid ── */
  var mermaidEls = document.querySelectorAll(".mermaid");
  if (mermaidEls.length && typeof mermaid !== "undefined") {
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
    mermaidEls.forEach(function (el, i) {
      var id = "mermaid-" + i;
      try { mermaid.render(id, el.textContent || "").then(function (r) { el.innerHTML = r.svg; }); } catch (e) {}
    });
  }
})();
