const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/mermaid.core-C8lxQdUD.js","assets/_commonjsHelpers-CUmg6egw.js","assets/index-DaXJIDda.js"])))=>i.map(i=>d[i]);
const THEMES = [
  { id: "light", name: "Light", group: "light", preview: ["#fafbfc", "#1a1a2e", "#2563eb", "#e5e7eb"] },
  { id: "dark", name: "Dark", group: "dark", preview: ["#1a1b1e", "#e4e4e7", "#60a5fa", "#2d2d30"] },
  { id: "nord", name: "Nord", group: "dark", preview: ["#2e3440", "#d8dee9", "#88c0d0", "#4c566a"] },
  { id: "solarized", name: "Solarized", group: "light", preview: ["#fdf6e3", "#586e75", "#268bd2", "#eee8d5"] },
  { id: "dracula", name: "Dracula", group: "dark", preview: ["#282a36", "#f8f8f2", "#bd93f9", "#44475a"] },
  { id: "forest", name: "Forest", group: "dark", preview: ["#1a2a1a", "#d4e4d4", "#6fcf6f", "#2d452d"] },
  { id: "glass-light", name: "Glass Light", group: "light", preview: ["rgba(250,251,252,0.55)", "#1a1a2e", "#2563eb", "rgba(0,0,0,0.08)"] },
  { id: "glass-dark", name: "Glass Dark", group: "dark", preview: ["rgba(26,27,30,0.6)", "#e4e4e7", "#60a5fa", "rgba(255,255,255,0.06)"] },
  { id: "obsidian", name: "Obsidian", group: "dark", preview: ["#1e1e1e", "#cccccc", "#7f6df2", "#3c3c3c"] },
  { id: "catppuccin", name: "Catppuccin", group: "light", preview: ["#eff1f5", "#4c4f69", "#1e66f5", "#ccd0da"] },
  { id: "colorful", name: "Colorful", group: "light", preview: ["#e11d48", "#7c3aed", "#2563eb", "#6366f1"] },
  { id: "colorful-dark", name: "Colorful Dark", group: "dark", preview: ["#fb7185", "#a78bfa", "#60a5fa", "#818cf8"] }
];
const THEME_CLASS_PREFIX = "theme-";
const SETTINGS_KEY = "vaultpub.settings";
function getSettings$1() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
  } catch {
    return {};
  }
}
function setSettings(partial) {
  const current = getSettings$1();
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({ ...current, ...partial }));
}
function getStoredThemeId() {
  const settings = getSettings$1();
  const stored = settings.theme;
  if (stored && THEMES.some((t) => t.id === stored)) return stored;
  if (stored === "light") return "light";
  if (stored === "dark") return "dark";
  if (stored === "system") return resolveSystemTheme();
  return resolveSystemTheme();
}
function resolveSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
function applyTheme(themeId) {
  const html = document.documentElement;
  const existing = Array.from(html.classList).filter((c) => c.startsWith(THEME_CLASS_PREFIX));
  html.classList.remove(...existing);
  html.classList.add(THEME_CLASS_PREFIX + themeId);
}
function createSwatchSpans(preview) {
  return preview.map((color) => `<span style="background:${color}"></span>`).join("");
}
function buildThemeSelector() {
  const topbar = document.querySelector(".top-bar");
  if (!topbar) return;
  const actions = topbar.querySelector(".topbar-actions") || topbar;
  const existingBtn = document.getElementById("theme-toggle");
  if (existingBtn) existingBtn.remove();
  const wrapper = document.createElement("div");
  wrapper.className = "theme-selector";
  const currentThemeId = getStoredThemeId();
  const currentTheme = THEMES.find((t) => t.id === currentThemeId) || THEMES[0];
  const btn = document.createElement("button");
  btn.className = "theme-selector-btn";
  btn.setAttribute("aria-label", "Select theme");
  btn.setAttribute("aria-haspopup", "listbox");
  btn.innerHTML = `
    <span class="theme-swatch">${createSwatchSpans(currentTheme.preview)}</span>
    <span class="theme-selector-label">${currentTheme.name}</span>
    <span class="theme-selector-caret">&#9660;</span>
  `;
  const dropdown = document.createElement("div");
  dropdown.className = "theme-dropdown";
  dropdown.setAttribute("role", "listbox");
  const lightThemes = THEMES.filter((t) => t.group === "light");
  const darkThemes = THEMES.filter((t) => t.group === "dark");
  dropdown.innerHTML = `
    <div class="theme-dropdown-header">Light</div>
    ${lightThemes.map(
    (t) => `
      <button class="theme-option${t.id === currentThemeId ? " active" : ""}"
              role="option" data-theme-id="${t.id}" aria-selected="${t.id === currentThemeId}">
        <span class="theme-option-preview">${createSwatchSpans(t.preview)}</span>
        ${t.name}
      </button>`
  ).join("")}
    <div class="theme-dropdown-header">Dark</div>
    ${darkThemes.map(
    (t) => `
      <button class="theme-option${t.id === currentThemeId ? " active" : ""}"
              role="option" data-theme-id="${t.id}" aria-selected="${t.id === currentThemeId}">
        <span class="theme-option-preview">${createSwatchSpans(t.preview)}</span>
        ${t.name}
      </button>`
  ).join("")}
  `;
  wrapper.appendChild(btn);
  wrapper.appendChild(dropdown);
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    wrapper.classList.toggle("open");
  });
  dropdown.addEventListener("click", (e) => {
    const option = e.target.closest(".theme-option");
    if (!option) return;
    const themeId = option.dataset.themeId;
    if (!themeId) return;
    setSettings({ theme: themeId });
    applyTheme(themeId);
    const theme = THEMES.find((t) => t.id === themeId);
    if (theme) {
      btn.querySelector(".theme-selector-label").textContent = theme.name;
      btn.querySelector(".theme-swatch").innerHTML = createSwatchSpans(theme.preview);
    }
    dropdown.querySelectorAll(".theme-option").forEach((el) => {
      el.classList.toggle("active", el.dataset.themeId === themeId);
      el.setAttribute("aria-selected", String(el.dataset.themeId === themeId));
    });
    wrapper.classList.remove("open");
  });
  document.addEventListener("click", () => wrapper.classList.remove("open"));
  const searchTrigger = actions.querySelector(".search-trigger");
  if (searchTrigger) {
    actions.insertBefore(wrapper, searchTrigger);
  } else {
    actions.appendChild(wrapper);
  }
}
function initTheme() {
  const themeId = getStoredThemeId();
  applyTheme(themeId);
  buildThemeSelector();
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const stored = getSettings$1().theme;
    if (!stored || stored === "system") {
      const sysTheme = resolveSystemTheme();
      applyTheme(sysTheme);
      updateSelectorForTheme(sysTheme);
    }
  });
}
function updateSelectorForTheme(themeId) {
  const btn = document.querySelector(".theme-selector-btn");
  const dropdown = document.querySelector(".theme-dropdown");
  if (!btn || !dropdown) return;
  const theme = THEMES.find((t) => t.id === themeId);
  if (!theme) return;
  const label = btn.querySelector(".theme-selector-label");
  const swatch = btn.querySelector(".theme-swatch");
  if (label) label.textContent = theme.name;
  if (swatch) swatch.innerHTML = createSwatchSpans(theme.preview);
  dropdown.querySelectorAll(".theme-option").forEach((el) => {
    const id = el.dataset.themeId;
    el.classList.toggle("active", id === themeId);
    el.setAttribute("aria-selected", String(id === themeId));
  });
}
function urlPrefix() {
  var _a;
  let prefix = ((_a = document.body) == null ? void 0 : _a.getAttribute("data-url-prefix")) || "/";
  if (!prefix.startsWith("/")) prefix = `/${prefix}`;
  if (!prefix.endsWith("/")) prefix += "/";
  return prefix;
}
function withUrlPrefix(path) {
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  const prefix = urlPrefix();
  if (prefix === "/" || path.startsWith(prefix) || path.startsWith("/static/")) return path;
  return `${prefix.replace(/\/$/, "")}${path}`;
}
function withoutUrlPrefix(path) {
  const prefix = urlPrefix();
  if (prefix === "/" || !path.startsWith(prefix)) return path;
  return `/${path.slice(prefix.length)}`;
}
let searchDocs = [];
async function loadSearchIndex() {
  try {
    const resp = await fetch(withUrlPrefix("/search-index.json"));
    if (!resp.ok) return;
    searchDocs = await resp.json();
  } catch {
    try {
      const resp = await fetch(withUrlPrefix("/api/search?q="));
      if (resp.ok) {
        const data = await resp.json();
        searchDocs = data.results || [];
      }
    } catch {
    }
  }
}
function createSearchUI() {
  const overlay = document.createElement("div");
  overlay.id = "search-overlay";
  overlay.className = "search-overlay";
  overlay.innerHTML = `
    <div class="search-modal">
      <div class="search-input-wrapper">
        <input type="text" id="search-input" placeholder="Search notes..." autocomplete="off">
        <button id="search-close" aria-label="Close search">&times;</button>
      </div>
      <div id="search-results" class="search-results"></div>
    </div>
  `;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeSearch();
  });
  return overlay;
}
function openSearch() {
  let overlay = document.getElementById("search-overlay");
  if (!overlay) {
    overlay = createSearchUI();
    document.body.appendChild(overlay);
    setupSearchListeners(overlay);
  }
  overlay.classList.add("active");
  const input = document.getElementById("search-input");
  input == null ? void 0 : input.focus();
}
function closeSearch() {
  const overlay = document.getElementById("search-overlay");
  overlay == null ? void 0 : overlay.classList.remove("active");
}
function doSearch(query) {
  const resultsEl = document.getElementById("search-results");
  if (!resultsEl) return;
  if (!query.trim()) {
    resultsEl.innerHTML = "";
    return;
  }
  const q = query.toLowerCase();
  const results = searchDocs.filter((doc) => {
    const haystack = [
      doc.title,
      doc.content,
      ...doc.tags,
      ...doc.headings,
      ...doc.aliases
    ].join(" ").toLowerCase();
    return haystack.includes(q);
  }).slice(0, 20);
  if (results.length === 0) {
    resultsEl.innerHTML = '<div class="search-empty">No results found</div>';
    return;
  }
  resultsEl.innerHTML = results.map(
    (doc) => `
    <a class="search-result-item" href="${doc.url}">
      <div class="search-result-title">${highlight(doc.title, q)}</div>
      <div class="search-result-excerpt">${highlight(doc.excerpt || doc.content.slice(0, 150), q)}</div>
      ${doc.tags.length ? `<div class="search-result-tags">${doc.tags.map((t) => `<span class="tag">#${t}</span>`).join(" ")}</div>` : ""}
    </a>`
  ).join("");
}
function highlight(text, query) {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return escapeHtml(text);
  const before = escapeHtml(text.slice(0, idx));
  const match = escapeHtml(text.slice(idx, idx + query.length));
  const after = escapeHtml(text.slice(idx + query.length));
  return `${before}<mark>${match}</mark>${after}`;
}
function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
function setupSearchListeners(overlay) {
  const input = overlay.querySelector("#search-input");
  const closeBtn = overlay.querySelector("#search-close");
  input == null ? void 0 : input.addEventListener("input", () => doSearch(input.value));
  closeBtn == null ? void 0 : closeBtn.addEventListener("click", closeSearch);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSearch();
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      openSearch();
    }
  });
}
function initSearch() {
  loadSearchIndex();
  document.addEventListener("click", (e) => {
    const target = e.target;
    if (target.closest("[data-action='search']") || target.closest(".search-trigger")) {
      e.preventDefault();
      openSearch();
    }
  });
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      openSearch();
    }
  });
}
let previewTimer = null;
let previewBox = null;
const cache = /* @__PURE__ */ new Map();
async function fetchPreview(url) {
  if (cache.has(url)) return cache.get(url);
  try {
    const apiUrl = withUrlPrefix("/api/page" + withoutUrlPrefix(url));
    const resp = await fetch(apiUrl);
    if (!resp.ok) return null;
    const data = await resp.json();
    const html = data.html || "";
    cache.set(url, html);
    return html;
  } catch {
    return null;
  }
}
function createPreviewBox() {
  const box = document.createElement("div");
  box.className = "hover-preview";
  box.setAttribute("role", "tooltip");
  box.style.display = "none";
  document.body.appendChild(box);
  return box;
}
function showPreview(x, y, html) {
  if (!previewBox) {
    previewBox = createPreviewBox();
  }
  previewBox.innerHTML = `<div class="hover-preview-content">${html}</div>`;
  previewBox.style.display = "block";
  previewBox.style.left = `${x}px`;
  previewBox.style.top = `${y + 5}px`;
  const rect = previewBox.getBoundingClientRect();
  if (rect.right > window.innerWidth) {
    previewBox.style.left = `${window.innerWidth - rect.width - 10}px`;
  }
  if (rect.bottom > window.innerHeight) {
    previewBox.style.top = `${y - rect.height - 5}px`;
  }
}
function hidePreview() {
  if (previewBox) {
    previewBox.style.display = "none";
  }
}
function handleLinkHover(e) {
  const target = e.target;
  const link = target.closest("a.internal-link");
  if (!link) {
    hidePreview();
    return;
  }
  const href = link.getAttribute("href");
  if (!href || href.startsWith("http")) return;
  if (previewTimer) clearTimeout(previewTimer);
  previewTimer = setTimeout(async () => {
    const html = await fetchPreview(href);
    if (html) {
      showPreview(e instanceof MouseEvent ? e.clientX : 0, e.clientY || 0, html);
    }
  }, 300);
}
function handleLinkLeave(e) {
  const target = e.target;
  const link = target.closest("a.internal-link");
  if (link) {
    if (previewTimer) clearTimeout(previewTimer);
    hidePreview();
  }
}
function initPreview() {
  const settings = getSettings();
  if (settings.disableHoverPreview) return;
  document.addEventListener("mouseover", handleLinkHover);
  document.addEventListener("mouseout", handleLinkLeave);
  document.addEventListener("focusin", handleLinkHover);
  document.addEventListener("focusout", handleLinkLeave);
}
function getSettings() {
  try {
    return JSON.parse(localStorage.getItem("vaultpub.settings") || "{}");
  } catch {
    return {};
  }
}
let graphData = null;
async function loadGraphData() {
  try {
    const resp = await fetch(withUrlPrefix("/graph.json"));
    if (!resp.ok) return null;
    return await resp.json();
  } catch {
    try {
      const resp = await fetch(withUrlPrefix("/api/graph"));
      if (!resp.ok) return null;
      return await resp.json();
    } catch {
      return null;
    }
  }
}
function buildLocalGraph(graph2, noteNodeId) {
  const localEdges = graph2.edges.filter((edge) => edge.from === noteNodeId || edge.to === noteNodeId);
  const localIds = new Set(localEdges.flatMap((edge) => [edge.from, edge.to]));
  const localNodes = graph2.nodes.filter((node) => localIds.has(node.id));
  return { nodes: localNodes, edges: localEdges };
}
function createGraphCanvas(container) {
  const canvas = document.createElement("canvas");
  canvas.width = container.clientWidth || 600;
  canvas.height = container.clientHeight || 400;
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  container.appendChild(canvas);
  return canvas;
}
function simulate(nodes, edges, iterations = 50) {
  const area = nodes.length * 5e3;
  const k = Math.sqrt(area / nodes.length);
  const temp = 10;
  for (const n of nodes) {
    n.x = Math.random() * 800;
    n.y = Math.random() * 500;
  }
  for (let iter = 0; iter < iterations; iter++) {
    const t = temp * (1 - iter / iterations);
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = k * k / dist;
        const fx = dx / dist * force;
        const fy = dy / dist * force;
        nodes[i].x += fx * t * 0.01;
        nodes[i].y += fy * t * 0.01;
        nodes[j].x -= fx * t * 0.01;
        nodes[j].y -= fy * t * 0.01;
      }
    }
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    for (const edge of edges) {
      const source = nodeMap.get(edge.from);
      const target = nodeMap.get(edge.to);
      if (!source || !target) continue;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = dist * dist / k;
      const fx = dx / dist * force * 0.01;
      const fy = dy / dist * force * 0.01;
      source.x += fx;
      source.y += fy;
      target.x -= fx;
      target.y -= fy;
    }
    for (const n of nodes) {
      n.x += (400 - n.x) * 1e-3;
      n.y += (250 - n.y) * 1e-3;
    }
  }
}
function render(canvas, nodes, edges) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;
  ctx.scale(dpr, dpr);
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  ctx.strokeStyle = "var(--graph-edge-color, #999)";
  ctx.lineWidth = 0.5;
  for (const edge of edges) {
    const source = nodeMap.get(edge.from);
    const target = nodeMap.get(edge.to);
    if (!source || !target) continue;
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);
    ctx.stroke();
  }
  const colors = {
    note: "var(--graph-note-color, #4a9eff)",
    tag: "var(--graph-tag-color, #e67e22)",
    attachment: "var(--graph-attachment-color, #2ecc71)"
  };
  for (const n of nodes) {
    const r = n.group === "tag" ? 3 : 5;
    ctx.fillStyle = colors[n.group] || "#999";
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fill();
    if (n.group === "note") {
      ctx.fillStyle = "var(--graph-label-color, #333)";
      ctx.font = "9px sans-serif";
      ctx.fillText(n.label.slice(0, 15), n.x + 6, n.y + 4);
    }
  }
}
function showContainer(container) {
  container.style.display = "block";
  container.style.height = "240px";
  container.style.border = "1px solid var(--border-color)";
  container.style.borderRadius = "var(--radius, 8px)";
  container.style.overflow = "hidden";
}
async function initGraph() {
  const container = document.getElementById("graph-container");
  if (!container) return;
  const noteNodeId = container.dataset.graphNoteId;
  const fullGraph = await loadGraphData();
  graphData = noteNodeId && fullGraph ? buildLocalGraph(fullGraph, noteNodeId) : fullGraph;
  if (!graphData || graphData.nodes.length < 3) {
    container.remove();
    return;
  }
  showContainer(container);
  container.replaceChildren();
  const canvas = createGraphCanvas(container);
  const simNodes = graphData.nodes.map((n) => ({
    id: n.id,
    label: n.label,
    group: n.group,
    url: n.url,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0
  }));
  simulate(simNodes, graphData.edges, 80);
  render(canvas, simNodes, graphData.edges);
  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    new Map(simNodes.map((n) => [n.id, n]));
    for (const n of simNodes) {
      const dx = n.x - mx;
      const dy = n.y - my;
      if (Math.sqrt(dx * dx + dy * dy) < 10 && n.url) {
        window.location.href = n.url;
        return;
      }
    }
  });
  const observer = new ResizeObserver(() => {
    render(canvas, simNodes, (graphData == null ? void 0 : graphData.edges) || []);
  });
  observer.observe(container);
}
const graph = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  initGraph
}, Symbol.toStringTag, { value: "Module" }));
function initCalloutFold() {
  document.querySelectorAll(".callout").forEach((callout) => {
    const foldState = callout.getAttribute("data-callout-fold");
    if (foldState === "closed") {
      const content = callout.querySelector(".callout-content");
      if (content) content.style.display = "none";
    }
    const title = callout.querySelector(".callout-title");
    if (title) {
      title.style.cursor = "pointer";
      title.addEventListener("click", () => {
        const content = callout.querySelector(".callout-content");
        if (!content) return;
        const isHidden = content.style.display === "none";
        content.style.display = isHidden ? "" : "none";
        callout.setAttribute("data-callout-fold", isHidden ? "open" : "closed");
      });
    }
  });
}
const scriptRel = "modulepreload";
const assetsURL = function(dep) {
  return "/static/vaultpub/" + dep;
};
const seen = {};
const __vitePreload = function preload(baseModule, deps, importerUrl) {
  let promise = Promise.resolve();
  if (deps && deps.length > 0) {
    let allSettled2 = function(promises) {
      return Promise.all(
        promises.map(
          (p) => Promise.resolve(p).then(
            (value) => ({ status: "fulfilled", value }),
            (reason) => ({ status: "rejected", reason })
          )
        )
      );
    };
    document.getElementsByTagName("link");
    const cspNonceMeta = document.querySelector(
      "meta[property=csp-nonce]"
    );
    const cspNonce = (cspNonceMeta == null ? void 0 : cspNonceMeta.nonce) || (cspNonceMeta == null ? void 0 : cspNonceMeta.getAttribute("nonce"));
    promise = allSettled2(
      deps.map((dep) => {
        dep = assetsURL(dep);
        if (dep in seen) return;
        seen[dep] = true;
        const isCss = dep.endsWith(".css");
        const cssSelector = isCss ? '[rel="stylesheet"]' : "";
        if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) {
          return;
        }
        const link = document.createElement("link");
        link.rel = isCss ? "stylesheet" : scriptRel;
        if (!isCss) {
          link.as = "script";
        }
        link.crossOrigin = "";
        link.href = dep;
        if (cspNonce) {
          link.setAttribute("nonce", cspNonce);
        }
        document.head.appendChild(link);
        if (isCss) {
          return new Promise((res, rej) => {
            link.addEventListener("load", res);
            link.addEventListener(
              "error",
              () => rej(new Error(`Unable to preload CSS for ${dep}`))
            );
          });
        }
      })
    );
  }
  function handlePreloadError(err) {
    const e = new Event("vite:preloadError", {
      cancelable: true
    });
    e.payload = err;
    window.dispatchEvent(e);
    if (!e.defaultPrevented) {
      throw err;
    }
  }
  return promise.then((res) => {
    for (const item of res || []) {
      if (item.status !== "rejected") continue;
      handlePreloadError(item.reason);
    }
    return baseModule().catch(handlePreloadError);
  });
};
function initMermaid() {
  const mermaidElements = document.querySelectorAll(".mermaid");
  if (mermaidElements.length === 0) return;
  __vitePreload(() => import("./assets/mermaid.core-C8lxQdUD.js").then((n) => n.bm), true ? __vite__mapDeps([0,1]) : void 0).then((mermaid) => {
    mermaid.default.initialize({
      startOnLoad: false,
      theme: document.documentElement.classList.contains("theme-dark") ? "dark" : "default",
      securityLevel: "strict"
    });
    mermaidElements.forEach(async (el, idx) => {
      const id = `mermaid-${idx}`;
      try {
        const { svg } = await mermaid.default.render(id, el.textContent || "");
        el.innerHTML = svg;
      } catch {
        el.innerHTML = '<div class="mermaid-error">Diagram render error</div>';
      }
    });
  });
}
function initMath() {
  const mathElements = document.querySelectorAll(".math");
  if (mathElements.length === 0) return;
  __vitePreload(() => import("./assets/katex-CqNtglxf.js"), true ? [] : void 0).then((katex) => {
    __vitePreload(() => Promise.resolve({}), true ? [] : void 0);
    mathElements.forEach((el) => {
      var _a;
      const isBlock = el.classList.contains("block");
      const formula = ((_a = el.textContent) == null ? void 0 : _a.trim()) || "";
      if (!formula) return;
      try {
        katex.default.render(formula, el, {
          throwOnError: false,
          displayMode: isBlock
        });
      } catch {
      }
    });
  });
}
let currentVersion = 0;
async function checkSSE() {
  const container = document.querySelector("[data-sse-url]");
  const sseUrl = (container == null ? void 0 : container.getAttribute("data-sse-url")) || withUrlPrefix("/api/events");
  const currentUrl = withoutUrlPrefix(window.location.pathname);
  try {
    const source = new EventSource(sseUrl);
    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleEvent(data, currentUrl);
      } catch {
      }
    };
    source.onerror = () => {
      setTimeout(() => {
        if (source.readyState === EventSource.CLOSED) {
          startPolling(currentUrl);
        }
      }, 5e3);
    };
  } catch {
    startPolling(currentUrl);
  }
}
function startPolling(currentUrl) {
  let lastVersion = 0;
  setInterval(async () => {
    try {
      const resp = await fetch(withUrlPrefix("/api/events/version"));
      if (resp.ok) {
        const data = await resp.json();
        if (data.version > lastVersion) {
          lastVersion = data.version;
          refreshPage(currentUrl);
        }
      }
    } catch {
    }
  }, 5e3);
}
function handleEvent(data, currentUrl) {
  if (data.version <= currentVersion) return;
  currentVersion = data.version;
  const currentPageChanged = [...data.changed, ...data.deleted].some(
    (item) => item.url === currentUrl
  );
  currentUrl ? currentUrl.split("/").slice(1, -1).join("/") : "";
  if (currentPageChanged) {
    const deleted = data.deleted.some((item) => item.url === currentUrl);
    if (deleted) {
      showNotification("This page has been deleted.");
    } else {
      refreshContent(currentUrl);
    }
  }
  if (data.nav_changed) {
    refreshNav();
  }
  if (data.graph_changed) {
    refreshGraph();
  }
  if (data.search_changed) {
    localStorage.removeItem("vaultpub.searchCache");
  }
}
async function refreshContent(url) {
  try {
    const resp = await fetch(withUrlPrefix(`/api/page${withoutUrlPrefix(url)}`));
    if (!resp.ok) return;
    const data = await resp.json();
    const body = document.querySelector(".markdown-body");
    if (body && data.html) {
      body.innerHTML = data.html;
      showNotification("Content updated.");
    }
  } catch {
    window.location.reload();
  }
}
async function refreshNav() {
  const nav = document.querySelector(".sidebar-left");
  if (!nav) return;
  window.location.reload();
}
function refreshGraph() {
  const container = document.getElementById("graph-container");
  if (container) {
    __vitePreload(() => Promise.resolve().then(() => graph), true ? void 0 : void 0).then((mod) => mod.initGraph());
  }
}
function showNotification(message) {
  const el = document.createElement("div");
  el.className = "realtime-notification";
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3e3);
}
function refreshPage(_url) {
  window.location.reload();
}
function initRealtime() {
  const body = document.body;
  if (body.getAttribute("data-realtime") === "false") return;
  checkSSE();
}
function initMobileDrawer() {
  const sidebarLeft = document.querySelector(".sidebar-left");
  const mainContent = document.querySelector(".content");
  if (!sidebarLeft) return;
  let menuBtn = document.getElementById("mobile-menu-btn");
  if (!menuBtn) {
    menuBtn = document.createElement("button");
    menuBtn.id = "mobile-menu-btn";
    menuBtn.className = "mobile-menu-btn";
    menuBtn.setAttribute("aria-label", "Toggle navigation");
    menuBtn.innerHTML = "&#9776;";
    const topbar = document.querySelector(".top-bar");
    if (topbar) {
      topbar.prepend(menuBtn);
    } else if (mainContent) {
      mainContent.prepend(menuBtn);
    }
  }
  menuBtn.addEventListener("click", () => {
    sidebarLeft.classList.toggle("open");
  });
  document.addEventListener("click", (e) => {
    if (window.innerWidth > 768) return;
    const target = e.target;
    if (!sidebarLeft.classList.contains("open")) return;
    if (!sidebarLeft.contains(target) && target !== menuBtn) {
      sidebarLeft.classList.remove("open");
    }
  });
  const sidebarRight = document.querySelector(".sidebar-right");
  if (sidebarRight && window.innerWidth <= 768) {
    sidebarRight.classList.add("mobile-tabs");
  }
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      sidebarLeft.classList.remove("open");
      sidebarRight == null ? void 0 : sidebarRight.classList.remove("mobile-tabs");
    } else {
      sidebarRight == null ? void 0 : sidebarRight.classList.add("mobile-tabs");
    }
  });
}
const SIDEBAR_STATE_KEY = "vaultpub.sidebarState";
const NAV_TREE_STATE_KEY = "vaultpub.navTreeState";
const DEFAULT_SIDEBAR_WIDTH = 270;
const MIN_SIDEBAR_WIDTH = 220;
const MIN_CONTENT_WIDTH = 420;
function readJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "{}");
  } catch {
    return {};
  }
}
function writeJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}
function sidebarClass(side, suffix) {
  return `sidebar-${side}-${suffix}`;
}
function sidebarWidthVar(side) {
  return `--sidebar-${side}-width`;
}
function navStateKey(detail, index) {
  var _a;
  const summary = detail.querySelector("summary");
  return detail.dataset.navKey || ((_a = summary == null ? void 0 : summary.textContent) == null ? void 0 : _a.trim()) || `nav-${index}`;
}
function writeNavTreeState(state) {
  writeJson(NAV_TREE_STATE_KEY, state);
}
function isNavSortMode(value) {
  return value === "predefined" || value === "name-asc" || value === "name-desc" || value === "created-desc" || value === "created-asc" || value === "modified-desc" || value === "modified-asc";
}
function navItemValue(item, name) {
  const value = Number(item.dataset[name] || "0");
  return Number.isFinite(value) && value > 0 ? value : 0;
}
function compareNames(left, right) {
  return (left.dataset.navName || "").localeCompare(right.dataset.navName || "", void 0, { sensitivity: "base" });
}
function sortNavigationList(list, mode) {
  const items = Array.from(list.children).filter(
    (item) => item instanceof HTMLLIElement && item.hasAttribute("data-nav-sort-item")
  );
  if (items.length < 2) return;
  items.forEach((item, index) => {
    if (!item.dataset.navOriginalIndex) item.dataset.navOriginalIndex = String(index);
  });
  items.sort((left, right) => {
    const leftStarred = left.dataset.navStarred === "true";
    const rightStarred = right.dataset.navStarred === "true";
    if (leftStarred !== rightStarred) return leftStarred ? -1 : 1;
    if (leftStarred) return Number(left.dataset.navOriginalIndex) - Number(right.dataset.navOriginalIndex);
    if (mode === "predefined") return Number(left.dataset.navOriginalIndex) - Number(right.dataset.navOriginalIndex);
    const leftFolder = left.dataset.navKind === "folder";
    const rightFolder = right.dataset.navKind === "folder";
    if (leftFolder !== rightFolder) return leftFolder ? -1 : 1;
    if (mode === "name-asc") return compareNames(left, right);
    if (mode === "name-desc") return compareNames(right, left);
    const field = mode.startsWith("created") ? "navCreated" : "navModified";
    const leftDate = navItemValue(left, field);
    const rightDate = navItemValue(right, field);
    if (leftDate !== rightDate) {
      if (!leftDate) return 1;
      if (!rightDate) return -1;
      return mode.endsWith("desc") ? rightDate - leftDate : leftDate - rightDate;
    }
    return compareNames(left, right);
  });
  list.append(...items);
}
function applyNavigationSort(mode) {
  document.querySelectorAll(".file-tree ul, .directory-list, .directory-context-nav ul").forEach((list) => {
    sortNavigationList(list, mode);
  });
  document.dispatchEvent(new CustomEvent("vaultpub:navigation-sorted"));
}
function initNavigationSort() {
  const select = document.querySelector("[data-nav-sort]");
  if (!select) return;
  const state = readJson(SIDEBAR_STATE_KEY);
  const mode = isNavSortMode(state.navSort) ? state.navSort : "predefined";
  select.value = mode;
  applyNavigationSort(mode);
  select.addEventListener("change", () => {
    const next = isNavSortMode(select.value) ? select.value : "predefined";
    const nextState = readJson(SIDEBAR_STATE_KEY);
    nextState.navSort = next;
    writeJson(SIDEBAR_STATE_KEY, nextState);
    applyNavigationSort(next);
  });
}
function readStoredSidebarWidth(state, side) {
  const value = side === "left" ? state.leftWidth : state.rightWidth;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
function writeStoredSidebarWidth(state, side, width) {
  if (side === "left") state.leftWidth = width;
  else state.rightWidth = width;
}
function currentSidebarWidth(layout, side) {
  const raw = window.getComputedStyle(layout).getPropertyValue(sidebarWidthVar(side)).trim();
  const parsed = Number.parseFloat(raw);
  return Number.isFinite(parsed) ? parsed : DEFAULT_SIDEBAR_WIDTH;
}
function maxSidebarWidth(layout, side) {
  const totalWidth = layout.getBoundingClientRect().width || window.innerWidth;
  const otherSide = side === "left" ? "right" : "left";
  const otherSidebar = document.querySelector(`.sidebar-${otherSide}`);
  const otherVisible = otherSidebar && window.getComputedStyle(otherSidebar).display !== "none" && !layout.classList.contains(sidebarClass(otherSide, "collapsed"));
  const otherWidth = otherVisible ? otherSidebar.getBoundingClientRect().width || currentSidebarWidth(layout, otherSide) : 0;
  return Math.max(MIN_SIDEBAR_WIDTH, Math.floor(totalWidth - otherWidth - MIN_CONTENT_WIDTH));
}
function clampSidebarWidth(layout, side, width) {
  const nextWidth = Math.round(width);
  return Math.max(MIN_SIDEBAR_WIDTH, Math.min(nextWidth, maxSidebarWidth(layout, side)));
}
function setSidebarWidth(layout, side, width, persist) {
  const clamped = clampSidebarWidth(layout, side, width);
  layout.style.setProperty(sidebarWidthVar(side), `${clamped}px`);
  if (!persist) return;
  const state = readJson(SIDEBAR_STATE_KEY);
  writeStoredSidebarWidth(state, side, clamped);
  writeJson(SIDEBAR_STATE_KEY, state);
}
function syncSidebarWidths(layout) {
  const state = readJson(SIDEBAR_STATE_KEY);
  setSidebarWidth(layout, "left", readStoredSidebarWidth(state, "left") ?? DEFAULT_SIDEBAR_WIDTH, false);
  setSidebarWidth(layout, "right", readStoredSidebarWidth(state, "right") ?? DEFAULT_SIDEBAR_WIDTH, false);
}
function setCollapsed(layout, side, collapsed) {
  layout.classList.toggle(sidebarClass(side, "collapsed"), collapsed);
  layout.classList.remove(sidebarClass(side, "peeking"));
  const state = readJson(SIDEBAR_STATE_KEY);
  if (side === "left") state.leftCollapsed = collapsed;
  if (side === "right") state.rightCollapsed = collapsed;
  writeJson(SIDEBAR_STATE_KEY, state);
  const button = document.querySelector(`[data-sidebar-toggle="${side}"]`);
  if (button) {
    button.setAttribute("aria-expanded", String(!collapsed));
    button.setAttribute("aria-label", collapsed ? `Show ${side} sidebar` : `Hide ${side} sidebar`);
  }
}
function setPeeking(layout, side, peeking) {
  if (!layout.classList.contains(sidebarClass(side, "collapsed"))) return;
  layout.classList.toggle(sidebarClass(side, "peeking"), peeking);
}
function addPeekButton(layout, sidebar, side) {
  const existing = document.querySelector(`.sidebar-peek-${side}`);
  if (existing) return;
  const button = document.createElement("button");
  button.type = "button";
  button.className = `sidebar-peek sidebar-peek-${side}`;
  button.innerHTML = side === "left" ? "&#9654;" : "&#9664;";
  button.setAttribute("aria-label", side === "left" ? "Show navigation" : "Show page sidebar");
  let hideTimer;
  const show = () => {
    if (hideTimer !== void 0) window.clearTimeout(hideTimer);
    setPeeking(layout, side, true);
  };
  const hide = () => {
    hideTimer = window.setTimeout(() => {
      if (button.matches(":hover") || sidebar.matches(":hover")) return;
      setPeeking(layout, side, false);
    }, 80);
  };
  button.addEventListener("mouseenter", show);
  button.addEventListener("focus", show);
  button.addEventListener("mouseleave", hide);
  button.addEventListener("blur", hide);
  button.addEventListener("click", () => setCollapsed(layout, side, false));
  sidebar.addEventListener("mouseenter", show);
  sidebar.addEventListener("mouseleave", hide);
  layout.appendChild(button);
}
function addResizer(layout, sidebar, side) {
  if (sidebar.querySelector(`.sidebar-resizer-${side}`)) return;
  const handle = document.createElement("div");
  handle.className = `sidebar-resizer sidebar-resizer-${side}`;
  handle.setAttribute("aria-hidden", "true");
  handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || window.innerWidth <= 768) return;
    if (layout.classList.contains(sidebarClass(side, "collapsed"))) return;
    if (window.getComputedStyle(sidebar).display === "none") return;
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = sidebar.getBoundingClientRect().width;
    document.body.classList.add("sidebar-resize-active");
    const onMove = (moveEvent) => {
      const delta = moveEvent.clientX - startX;
      const nextWidth = side === "left" ? startWidth + delta : startWidth - delta;
      setSidebarWidth(layout, side, nextWidth, true);
    };
    const stop = () => {
      document.body.classList.remove("sidebar-resize-active");
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", stop);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", stop);
  });
  sidebar.appendChild(handle);
}
function initSidebar(layout, side) {
  const sidebar = document.querySelector(`.sidebar-${side}`);
  if (!sidebar) return;
  const state = readJson(SIDEBAR_STATE_KEY);
  const collapsed = side === "left" ? state.leftCollapsed === true : state.rightCollapsed === true;
  layout.classList.toggle(sidebarClass(side, "collapsed"), collapsed);
  const button = document.querySelector(`[data-sidebar-toggle="${side}"]`);
  if (button) {
    button.setAttribute("aria-expanded", String(!collapsed));
    button.addEventListener("click", () => {
      const nextCollapsed = !layout.classList.contains(sidebarClass(side, "collapsed"));
      setCollapsed(layout, side, nextCollapsed);
    });
  }
  addPeekButton(layout, sidebar, side);
  addResizer(layout, sidebar, side);
}
function initNavTreeState() {
  var _a, _b;
  const details = document.querySelectorAll(".file-tree details");
  if (!details.length) return;
  const state = readJson(NAV_TREE_STATE_KEY);
  details.forEach((detail, index) => {
    const key = navStateKey(detail, index);
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      detail.open = state[key];
    }
    detail.addEventListener("toggle", () => {
      state[key] = detail.open;
      writeNavTreeState(state);
    });
    const folderLink = detail.querySelector("summary .nav-folder-link");
    if (folderLink) {
      folderLink.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        detail.open = true;
        state[key] = true;
        writeNavTreeState(state);
        window.location.href = folderLink.href;
      });
    }
    const toggle = detail.querySelector("summary .nav-folder-toggle");
    if (toggle) {
      toggle.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        detail.open = !detail.open;
        state[key] = detail.open;
        writeNavTreeState(state);
      });
    }
  });
  const setAllDetails = (open) => {
    const visibleDetails = document.querySelectorAll(
      ".file-tree.folder-tabs-active .folder-tabs-selected > details > ul details, .file-tree:not(.folder-tabs-active) details"
    );
    visibleDetails.forEach((detail) => {
      const index = Array.from(details).indexOf(detail);
      detail.open = open;
      state[navStateKey(detail, index)] = open;
    });
    writeNavTreeState(state);
  };
  (_a = document.querySelector('[data-nav-tree-action="expand"]')) == null ? void 0 : _a.addEventListener("click", () => setAllDetails(true));
  (_b = document.querySelector('[data-nav-tree-action="collapse"]')) == null ? void 0 : _b.addEventListener("click", () => setAllDetails(false));
}
function currentFolderSection(sections) {
  var _a;
  const currentPath = (_a = document.querySelector("[data-current-path]")) == null ? void 0 : _a.dataset.currentPath;
  if (!currentPath) return "root";
  const matching = sections.find((section) => {
    var _a2;
    return Array.from(((_a2 = section.item) == null ? void 0 : _a2.querySelectorAll("a")) || []).some(
      (link) => link.getAttribute("href") === currentPath
    );
  });
  return (matching == null ? void 0 : matching.id) || "root";
}
function initTopFolderNavigation() {
  const fileTree = document.querySelector(".file-tree");
  const topbar = document.querySelector(".top-bar");
  const layoutButton = document.querySelector('[data-nav-folder-layout="top"]');
  const rootList = fileTree == null ? void 0 : fileTree.querySelector(":scope > ul");
  if (!fileTree || !topbar || !layoutButton || !rootList) return;
  const rootItems = Array.from(rootList.children).filter(
    (item) => item instanceof HTMLLIElement
  );
  const folderSections = rootItems.flatMap((item) => {
    var _a;
    const detail = item.querySelector(":scope > details");
    const link = detail == null ? void 0 : detail.querySelector(":scope > summary .nav-folder-link");
    if (!detail || !link) return [];
    return [{ id: detail.dataset.navKey || link.href, label: ((_a = link.textContent) == null ? void 0 : _a.trim().replace(/\/$/, "")) || "Folder", item }];
  });
  if (!folderSections.length) {
    layoutButton.disabled = true;
    layoutButton.title = "No top-level folders";
    layoutButton.setAttribute("aria-label", "No top-level folders");
    return;
  }
  const rootFiles = rootItems.filter((item) => item.querySelector(":scope > a"));
  rootFiles.forEach((item) => item.classList.add("folder-tabs-root-file"));
  const sections = [
    ...rootFiles.length ? [{ id: "root", label: "Root", item: null }] : [],
    ...folderSections
  ];
  const nav = document.createElement("nav");
  nav.className = "top-folder-nav";
  nav.setAttribute("aria-label", "Vault folders");
  const tabs = document.createElement("div");
  tabs.className = "top-folder-tabs";
  const overflow = document.createElement("div");
  overflow.className = "top-folder-overflow";
  const overflowButton = document.createElement("button");
  overflowButton.type = "button";
  overflowButton.className = "top-folder-overflow-toggle";
  overflowButton.textContent = "…";
  overflowButton.title = "More folders";
  overflowButton.setAttribute("aria-label", "More folders");
  overflowButton.setAttribute("aria-expanded", "false");
  const overflowMenu = document.createElement("div");
  overflowMenu.className = "top-folder-overflow-menu";
  overflowMenu.hidden = true;
  overflow.append(overflowButton, overflowMenu);
  nav.append(tabs, overflow);
  topbar.insertBefore(nav, topbar.querySelector(".topbar-context") || topbar.querySelector(".topbar-actions"));
  let selectedId = currentFolderSection(sections);
  let layoutFrame;
  const setButtonState = (enabled) => {
    layoutButton.innerHTML = enabled ? "&#8659;" : "&#8657;";
    const label = enabled ? "Show folders in sidebar" : "Move folders to top bar";
    layoutButton.title = label;
    layoutButton.setAttribute("aria-label", label);
    layoutButton.setAttribute("aria-pressed", String(enabled));
  };
  const closeOverflow = () => {
    overflowMenu.hidden = true;
    overflowButton.setAttribute("aria-expanded", "false");
  };
  const updateSelection = () => {
    const selected = sections.find((section) => section.id === selectedId) || sections[0];
    selectedId = selected.id;
    rootItems.forEach((item) => item.classList.remove("folder-tabs-selected"));
    fileTree.classList.toggle("folder-tabs-root-selected", selected.id === "root");
    if (selected.item) {
      selected.item.classList.add("folder-tabs-selected");
      const detail = selected.item.querySelector(":scope > details");
      if (detail) detail.open = true;
    }
  };
  const makeTab = (section) => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "top-folder-tab";
    tab.textContent = section.label;
    tab.setAttribute("aria-pressed", String(section.id === selectedId));
    tab.addEventListener("click", () => {
      selectedId = section.id;
      updateSelection();
      closeOverflow();
      scheduleOverflowLayout();
    });
    return tab;
  };
  const layoutOverflow = () => {
    if (!fileTree.classList.contains("folder-tabs-active")) return;
    let visible = [...sections];
    const hidden = [];
    const render2 = () => {
      tabs.replaceChildren(...visible.map(makeTab));
      overflowMenu.replaceChildren(...hidden.map(makeTab));
      nav.classList.toggle("has-overflow", hidden.length > 0);
    };
    render2();
    while (tabs.scrollWidth > tabs.clientWidth && visible.length > 1) {
      const lastNonSelected = [...visible].reverse().findIndex((section) => section.id !== selectedId);
      if (lastNonSelected < 0) break;
      const index = visible.length - 1 - lastNonSelected;
      hidden.unshift(visible[index]);
      visible.splice(index, 1);
      render2();
    }
  };
  const scheduleOverflowLayout = () => {
    if (layoutFrame !== void 0) window.cancelAnimationFrame(layoutFrame);
    layoutFrame = window.requestAnimationFrame(() => {
      layoutFrame = void 0;
      layoutOverflow();
    });
  };
  const setEnabled = (enabled) => {
    fileTree.classList.toggle("folder-tabs-active", enabled);
    nav.classList.toggle("is-active", enabled);
    topbar.classList.toggle("top-folder-nav-active", enabled);
    setButtonState(enabled);
    const state2 = readJson(SIDEBAR_STATE_KEY);
    state2.topFolders = enabled;
    writeJson(SIDEBAR_STATE_KEY, state2);
    if (!enabled) {
      rootItems.forEach((item) => item.classList.remove("folder-tabs-selected"));
      fileTree.classList.remove("folder-tabs-root-selected");
      closeOverflow();
      return;
    }
    updateSelection();
    scheduleOverflowLayout();
  };
  overflowButton.addEventListener("click", (event) => {
    event.stopPropagation();
    const open = overflowMenu.hidden;
    overflowMenu.hidden = !open;
    overflowButton.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (event) => {
    if (!nav.contains(event.target)) closeOverflow();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeOverflow();
  });
  layoutButton.addEventListener("click", () => {
    setEnabled(!fileTree.classList.contains("folder-tabs-active"));
  });
  new ResizeObserver(scheduleOverflowLayout).observe(nav);
  const state = readJson(SIDEBAR_STATE_KEY);
  setEnabled(state.topFolders === true);
  document.addEventListener("vaultpub:navigation-sorted", () => {
    const rootSection = sections.find((section) => section.id === "root");
    const orderedFolders = Array.from(rootList.children).flatMap((item) => {
      const detail = item.querySelector(":scope > details");
      const link = detail == null ? void 0 : detail.querySelector(":scope > summary .nav-folder-link");
      if (!detail || !link) return [];
      return [sections.find((section) => section.id === (detail.dataset.navKey || link.href))];
    }).filter((section) => Boolean(section));
    sections.splice(0, sections.length, ...rootSection ? [rootSection] : [], ...orderedFolders);
    updateSelection();
    scheduleOverflowLayout();
  });
}
function initSidebars() {
  const layout = document.querySelector(".app-layout");
  if (!layout) return;
  syncSidebarWidths(layout);
  initSidebar(layout, "left");
  initSidebar(layout, "right");
  initNavigationSort();
  initNavTreeState();
  initTopFolderNavigation();
  window.addEventListener("resize", () => syncSidebarWidths(layout));
}
let lastScrollY = 0;
const THRESHOLD = 40;
function initScroller() {
  const topbar = document.querySelector(".top-bar");
  if (!topbar) return;
  window.addEventListener(
    "scroll",
    () => {
      const y = window.scrollY;
      if (Math.abs(y - lastScrollY) < 6) return;
      if (y > lastScrollY && y > THRESHOLD) {
        topbar.classList.add("top-bar-hidden");
        document.body.classList.add("top-bar-hidden");
      } else {
        topbar.classList.remove("top-bar-hidden");
        document.body.classList.remove("top-bar-hidden");
      }
      lastScrollY = y;
    },
    { passive: true }
  );
}
function currentPathElement() {
  return document.querySelector("[data-current-path]");
}
function keepVisibleWithin(container, element) {
  if (container.scrollHeight <= container.clientHeight) return;
  const containerRect = container.getBoundingClientRect();
  const elementRect = element.getBoundingClientRect();
  if (elementRect.top < containerRect.top) {
    container.scrollTop -= containerRect.top - elementRect.top;
  } else if (elementRect.bottom > containerRect.bottom) {
    container.scrollTop += elementRect.bottom - containerRect.bottom;
  }
}
function initNavHighlight() {
  const page = currentPathElement();
  if (!page) return;
  const currentPath = page.dataset.currentPath;
  if (!currentPath) return;
  const fileTree = document.querySelector(".file-tree");
  if (!fileTree) return;
  const links = fileTree.querySelectorAll("a");
  for (const link of links) {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
      let parent = link.parentElement;
      while (parent && parent !== fileTree) {
        if (parent.tagName === "DETAILS") {
          const detail = parent;
          detail.open = true;
          detail.classList.add("has-active-descendant");
          const folderLink = detail.querySelector("summary .nav-folder-link");
          if (folderLink && folderLink !== link) {
            folderLink.classList.add("active-parent");
          }
        }
        parent = parent.parentElement;
      }
      requestAnimationFrame(() => {
        const sidebar = fileTree.closest(".sidebar-left");
        if (sidebar) keepVisibleWithin(sidebar, link);
      });
      return;
    }
  }
}
function initScrollSpy() {
  var _a;
  const article = document.querySelector(".note");
  if (!article) return;
  const toc = document.querySelector(".toc");
  if (!toc) return;
  const sidebar = toc.closest(".sidebar-right");
  const headingEls = article.querySelectorAll(
    "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"
  );
  if (headingEls.length === 0) return;
  const tocLinks = toc.querySelectorAll("a[href^='#']");
  const linkMap = /* @__PURE__ */ new Map();
  for (const link of tocLinks) {
    const id = (_a = link.getAttribute("href")) == null ? void 0 : _a.slice(1);
    if (id) linkMap.set(id, link);
  }
  let activeLink = null;
  function update() {
    const viewTop = 100;
    let currentId = null;
    for (const h of headingEls) {
      if (h.getBoundingClientRect().top <= viewTop) {
        currentId = h.id;
      } else {
        break;
      }
    }
    if (!currentId) return;
    const link = linkMap.get(currentId);
    if (!link || link === activeLink) return;
    if (activeLink) activeLink.classList.remove("active");
    link.classList.add("active");
    activeLink = link;
    requestAnimationFrame(() => {
      if (sidebar) keepVisibleWithin(sidebar, link);
    });
  }
  let ticking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          update();
          ticking = false;
        });
        ticking = true;
      }
    },
    { passive: true }
  );
  update();
}
function initNavHighlightAll() {
  initNavHighlight();
  initScrollSpy();
}
function splitHighlightedLines(codeBlock) {
  const lines = [document.createDocumentFragment()];
  const originalText = codeBlock.textContent || "";
  const currentLine = () => lines[lines.length - 1];
  const appendSegment = (text, ancestors) => {
    if (!text) return;
    let parent = currentLine();
    for (const ancestor of ancestors) {
      const clone = ancestor.cloneNode(false);
      parent.appendChild(clone);
      parent = clone;
    }
    parent.appendChild(document.createTextNode(text));
  };
  const appendText = (text, ancestors) => {
    const parts = text.split("\n");
    parts.forEach((part, index) => {
      if (index > 0) {
        lines.push(document.createDocumentFragment());
      }
      appendSegment(part, ancestors);
    });
  };
  const visitNode = (node, ancestors) => {
    if (node.nodeType === Node.TEXT_NODE) {
      appendText(node.textContent || "", ancestors);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const element = node;
    if (element.tagName === "BR") {
      lines.push(document.createDocumentFragment());
      return;
    }
    const nextAncestors = [...ancestors, element];
    Array.from(element.childNodes).forEach((child) => visitNode(child, nextAncestors));
  };
  Array.from(codeBlock.childNodes).forEach((child) => visitNode(child, []));
  if (lines.length > 1 && !lines[lines.length - 1].hasChildNodes() && originalText.endsWith("\n")) {
    lines.pop();
  }
  return lines;
}
function decorateCodeBlock(codeBlock) {
  if (codeBlock.dataset.lineNumbersReady === "true") return;
  const numberedLines = splitHighlightedLines(codeBlock).map((line, index) => {
    const lineElement = document.createElement("span");
    lineElement.className = "code-line";
    lineElement.dataset.lineNumber = String(index + 1);
    const contentElement = document.createElement("span");
    contentElement.className = "code-line-content";
    if (line.hasChildNodes()) {
      contentElement.appendChild(line);
    } else {
      contentElement.appendChild(document.createTextNode(" "));
    }
    lineElement.appendChild(contentElement);
    return lineElement;
  });
  codeBlock.replaceChildren(...numberedLines);
  codeBlock.dataset.lineNumbersReady = "true";
}
function initCodeHighlight() {
  const codeBlocks = Array.from(document.querySelectorAll("pre code"));
  if (codeBlocks.length === 0) return;
  __vitePreload(() => import("./assets/index-DaXJIDda.js"), true ? __vite__mapDeps([2,1]) : void 0).then((hljs) => {
    hljs.default.configure({
      cssSelector: "pre code",
      ignoreUnescapedHTML: true
    });
    hljs.default.highlightAll();
    for (const codeBlock of codeBlocks) {
      decorateCodeBlock(codeBlock);
    }
  });
}
const CODE_WRAP_KEY = "vaultpub.codeWrap";
const WIDE_CONTENT_KEY = "vaultpub.wideContent";
const ACTIVE_HEADING_OFFSET = 96;
function trackedHeadings() {
  const markdown = document.querySelector(".markdown-body");
  if (!markdown) return [];
  const headings = Array.from(
    markdown.querySelectorAll("h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]")
  );
  if (!headings.length) return [];
  const sectionHeadings = headings.filter((heading) => heading.tagName !== "H1");
  return sectionHeadings.length ? sectionHeadings : headings;
}
function updateCurrentHeading(link, headings) {
  var _a;
  if (!headings.length) {
    link.hidden = true;
    return;
  }
  let active = headings[0];
  for (const heading of headings) {
    if (heading.getBoundingClientRect().top <= ACTIVE_HEADING_OFFSET) {
      active = heading;
      continue;
    }
    break;
  }
  const text = ((_a = active.textContent) == null ? void 0 : _a.trim()) || "";
  if (!text || !active.id) {
    link.hidden = true;
    return;
  }
  link.textContent = text;
  link.href = `#${active.id}`;
  link.hidden = false;
}
function initCurrentHeading() {
  const link = document.querySelector("[data-current-heading]");
  if (!link) return;
  const headings = trackedHeadings();
  if (!headings.length) {
    link.hidden = true;
    return;
  }
  let ticking = false;
  const sync = () => {
    ticking = false;
    updateCurrentHeading(link, headings);
  };
  const requestSync = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(sync);
  };
  requestSync();
  window.addEventListener("scroll", requestSync, { passive: true });
  window.addEventListener("resize", requestSync);
}
function applyCodeWrapState(enabled, buttons) {
  document.body.classList.toggle("code-wrap-enabled", enabled);
  for (const button of buttons) {
    button.classList.toggle("is-active", enabled);
    button.setAttribute("aria-pressed", String(enabled));
  }
}
function applyWideContentState(enabled, button) {
  document.body.classList.toggle("wide-content-enabled", enabled);
  button.classList.toggle("is-active", enabled);
  button.setAttribute("aria-pressed", String(enabled));
}
function storedBoolean(key, defaultValue) {
  const stored = localStorage.getItem(key);
  if (stored === null) return defaultValue;
  return stored === "true";
}
async function copyText(text) {
  var _a;
  if ((_a = navigator.clipboard) == null ? void 0 : _a.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
    }
  }
  const input = document.createElement("textarea");
  input.value = text;
  input.setAttribute("readonly", "true");
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }
  input.remove();
  return copied;
}
function flashButtonLabel(button, label) {
  const original = button.dataset.labelDefault || button.textContent || "";
  button.dataset.labelDefault = original;
  button.textContent = label;
  window.setTimeout(() => {
    button.textContent = original;
  }, 1200);
}
function initCodeTools() {
  const copyButton = document.querySelector("[data-code-action='copy-path']");
  const wrapButtons = Array.from(
    document.querySelectorAll("[data-code-action='toggle-wrap']")
  );
  if (wrapButtons.length) {
    const enabled = storedBoolean(CODE_WRAP_KEY, true);
    applyCodeWrapState(enabled, wrapButtons);
    for (const wrapButton of wrapButtons) {
      wrapButton.addEventListener("click", () => {
        const nextEnabled = !document.body.classList.contains("code-wrap-enabled");
        localStorage.setItem(CODE_WRAP_KEY, String(nextEnabled));
        applyCodeWrapState(nextEnabled, wrapButtons);
      });
    }
  }
  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      const path = copyButton.dataset.codePath || "";
      if (!path) return;
      const copied = await copyText(path);
      flashButtonLabel(copyButton, copied ? "Copied" : "Failed");
    });
  }
}
function initWideContentToggle() {
  const button = document.querySelector("[data-layout-action='toggle-wide']");
  if (!button) return;
  const enabled = storedBoolean(WIDE_CONTENT_KEY, true);
  applyWideContentState(enabled, button);
  button.addEventListener("click", () => {
    const nextEnabled = !document.body.classList.contains("wide-content-enabled");
    localStorage.setItem(WIDE_CONTENT_KEY, String(nextEnabled));
    applyWideContentState(nextEnabled, button);
  });
}
function initTopbarContext() {
  initWideContentToggle();
  initCodeTools();
  const context = document.querySelector(".topbar-context");
  if (!context) return;
  const kind = context.dataset.topbarContext;
  if (kind === "note") {
    initCurrentHeading();
  }
}
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSearch();
  initPreview();
  initGraph();
  initCalloutFold();
  initMermaid();
  initMath();
  initCodeHighlight();
  initRealtime();
  initMobileDrawer();
  initSidebars();
  initScroller();
  initNavHighlightAll();
  initTopbarContext();
});
export {
  __vitePreload as _
};
