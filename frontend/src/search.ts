/**
 * Full-text search modal using MiniSearch.
 * Loads search-index.json and provides instant search.
 */

interface SearchDoc {
  id: string;
  title: string;
  path: string;
  url: string;
  content: string;
  tags: string[];
  headings: string[];
  aliases: string[];
  excerpt: string;
}

let searchDocs: SearchDoc[] = [];
let searchIndex: import("minisearch") | null = null;

async function loadSearchIndex(): Promise<void> {
  try {
    const resp = await fetch("/search-index.json");
    if (!resp.ok) return;
    searchDocs = await resp.json();
  } catch {
    // Fallback: try API
    try {
      const resp = await fetch("/api/search?q=");
      if (resp.ok) {
        const data = await resp.json();
        searchDocs = data.results || [];
      }
    } catch {
      // Search unavailable
    }
  }
}

function createSearchUI(): HTMLElement {
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

function openSearch(): void {
  let overlay = document.getElementById("search-overlay");
  if (!overlay) {
    overlay = createSearchUI();
    document.body.appendChild(overlay);
    setupSearchListeners(overlay);
  }
  overlay.classList.add("active");
  const input = document.getElementById("search-input") as HTMLInputElement;
  input?.focus();
}

function closeSearch(): void {
  const overlay = document.getElementById("search-overlay");
  overlay?.classList.remove("active");
}

function doSearch(query: string): void {
  const resultsEl = document.getElementById("search-results");
  if (!resultsEl) return;

  if (!query.trim()) {
    resultsEl.innerHTML = "";
    return;
  }

  const q = query.toLowerCase();
  const results = searchDocs
    .filter((doc) => {
      const haystack = [
        doc.title,
        doc.content,
        ...doc.tags,
        ...doc.headings,
        ...doc.aliases,
      ].join(" ").toLowerCase();
      return haystack.includes(q);
    })
    .slice(0, 20);

  if (results.length === 0) {
    resultsEl.innerHTML = '<div class="search-empty">No results found</div>';
    return;
  }

  resultsEl.innerHTML = results
    .map(
      (doc) => `
    <a class="search-result-item" href="${doc.url}">
      <div class="search-result-title">${highlight(doc.title, q)}</div>
      <div class="search-result-excerpt">${highlight(doc.excerpt || doc.content.slice(0, 150), q)}</div>
      ${doc.tags.length ? `<div class="search-result-tags">${doc.tags.map((t) => `<span class="tag">#${t}</span>`).join(" ")}</div>` : ""}
    </a>`
    )
    .join("");
}

function highlight(text: string, query: string): string {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return escapeHtml(text);
  const before = escapeHtml(text.slice(0, idx));
  const match = escapeHtml(text.slice(idx, idx + query.length));
  const after = escapeHtml(text.slice(idx + query.length));
  return `${before}<mark>${match}</mark>${after}`;
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function setupSearchListeners(overlay: HTMLElement): void {
  const input = overlay.querySelector("#search-input") as HTMLInputElement;
  const closeBtn = overlay.querySelector("#search-close");

  input?.addEventListener("input", () => doSearch(input.value));
  closeBtn?.addEventListener("click", closeSearch);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSearch();
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      openSearch();
    }
  });
}

export function initSearch(): void {
  loadSearchIndex();

  // Hook up search trigger buttons
  document.addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    if (target.closest("[data-action='search']") || target.closest(".search-trigger")) {
      e.preventDefault();
      openSearch();
    }
  });

  // Global keyboard shortcut: Ctrl+K / Cmd+K
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      openSearch();
    }
  });
}
