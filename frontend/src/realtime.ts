/**
 * Realtime client via SSE (Server-Sent Events).
 * Listens for index change events and refreshes the page as needed.
 */
import { withUrlPrefix, withoutUrlPrefix } from "./urls";

interface ChangeItem {
  kind: string;
  path: string;
  url: string;
  change: "modified" | "created" | "deleted";
}

interface IndexChangedEvent {
  type: string;
  version: number;
  changed: ChangeItem[];
  deleted: ChangeItem[];
  graph_changed: boolean;
  nav_changed: boolean;
  search_changed: boolean;
}

let currentVersion = 0;

async function checkSSE(): Promise<void> {
  const container = document.querySelector("[data-sse-url]");
  const sseUrl = container?.getAttribute("data-sse-url") || withUrlPrefix("/api/events");
  const currentUrl = withoutUrlPrefix(window.location.pathname);

  try {
    const source = new EventSource(sseUrl);

    source.onmessage = (event) => {
      try {
        const data: IndexChangedEvent = JSON.parse(event.data);
        handleEvent(data, currentUrl);
      } catch {
        // Ignore parse errors (e.g., pings)
      }
    };

    source.onerror = () => {
      // Reconnect automatically via EventSource
      // Fall back to polling after a delay
      setTimeout(() => {
        if (source.readyState === EventSource.CLOSED) {
          startPolling(currentUrl);
        }
      }, 5000);
    };
  } catch {
    // SSE not available, use polling
    startPolling(currentUrl);
  }
}

function startPolling(currentUrl: string): void {
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
      // Polling failed, retry next interval
    }
  }, 5000);
}

function handleEvent(data: IndexChangedEvent, currentUrl: string): void {
  if (data.version <= currentVersion) return;
  currentVersion = data.version;

  const currentPageChanged = [...data.changed, ...data.deleted].some(
    (item) => item.url === currentUrl
  );

  const currentPageNav = currentUrl ? currentUrl.split("/").slice(1, -1).join("/") : "";

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
    // Clear search cache so next search uses fresh data
    localStorage.removeItem("vaultpub.searchCache");
  }
}

async function refreshContent(url: string): Promise<void> {
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
    // Refresh failed, reload the page
    window.location.reload();
  }
}

async function refreshNav(): Promise<void> {
  const nav = document.querySelector(".sidebar-left");
  if (!nav) return;
  // Full page reload for nav update (or could fetch nav partial)
  // For simplicity, just reload if nav changed
  window.location.reload();
}

function refreshGraph(): void {
  const container = document.getElementById("graph-container");
  if (container) {
    import("./graph").then((mod) => mod.initGraph());
  }
}

function showNotification(message: string): void {
  const el = document.createElement("div");
  el.className = "realtime-notification";
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function refreshPage(_url: string): void {
  window.location.reload();
}

export function initRealtime(): void {
  // Only initialize if realtime is enabled (check data attribute on body)
  const body = document.body;
  if (body.getAttribute("data-realtime") === "false") return;

  checkSSE();
}
