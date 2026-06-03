/**
 * Hover preview for internal links.
 * Fetches page content via API and shows a popup on hover.
 */
import { withUrlPrefix, withoutUrlPrefix } from "./urls";

let previewTimer: ReturnType<typeof setTimeout> | null = null;
let previewBox: HTMLElement | null = null;

const cache = new Map<string, string>();

async function fetchPreview(url: string): Promise<string | null> {
  if (cache.has(url)) return cache.get(url)!;

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

function createPreviewBox(): HTMLElement {
  const box = document.createElement("div");
  box.className = "hover-preview";
  box.setAttribute("role", "tooltip");
  box.style.display = "none";
  document.body.appendChild(box);
  return box;
}

function showPreview(x: number, y: number, html: string): void {
  if (!previewBox) {
    previewBox = createPreviewBox();
  }
  previewBox.innerHTML = `<div class="hover-preview-content">${html}</div>`;
  previewBox.style.display = "block";
  previewBox.style.left = `${x}px`;
  previewBox.style.top = `${y + 5}px`;

  // Keep in viewport
  const rect = previewBox.getBoundingClientRect();
  if (rect.right > window.innerWidth) {
    previewBox.style.left = `${window.innerWidth - rect.width - 10}px`;
  }
  if (rect.bottom > window.innerHeight) {
    previewBox.style.top = `${y - rect.height - 5}px`;
  }
}

function hidePreview(): void {
  if (previewBox) {
    previewBox.style.display = "none";
  }
}

function handleLinkHover(e: Event): void {
  const target = e.target as HTMLElement;
  const link = target.closest("a.internal-link") as HTMLAnchorElement | null;
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
      showPreview(e instanceof MouseEvent ? e.clientX : 0, (e as MouseEvent).clientY || 0, html);
    }
  }, 300);
}

function handleLinkLeave(e: Event): void {
  const target = e.target as HTMLElement;
  const link = target.closest("a.internal-link");
  if (link) {
    if (previewTimer) clearTimeout(previewTimer);
    hidePreview();
  }
}

export function initPreview(): void {
  const settings = getSettings();
  if (settings.disableHoverPreview) return;

  document.addEventListener("mouseover", handleLinkHover);
  document.addEventListener("mouseout", handleLinkLeave);
  document.addEventListener("focusin", handleLinkHover);
  document.addEventListener("focusout", handleLinkLeave);
}

function getSettings(): Record<string, unknown> {
  try {
    return JSON.parse(localStorage.getItem("vaultpub.settings") || "{}");
  } catch {
    return {};
  }
}
