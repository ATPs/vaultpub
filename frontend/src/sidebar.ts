/**
 * Desktop sidebar controls and persistent file-tree state.
 */

type SidebarSide = "left" | "right";

interface SidebarState {
  leftCollapsed?: boolean;
  rightCollapsed?: boolean;
  leftWidth?: number;
  rightWidth?: number;
}

const SIDEBAR_STATE_KEY = "vaultpub.sidebarState";
const NAV_TREE_STATE_KEY = "vaultpub.navTreeState";
const DEFAULT_SIDEBAR_WIDTH = 270;
const MIN_SIDEBAR_WIDTH = 220;
const MIN_CONTENT_WIDTH = 420;

function readJson<T extends object>(key: string): T {
  try {
    return JSON.parse(localStorage.getItem(key) || "{}") as T;
  } catch {
    return {} as T;
  }
}

function writeJson(key: string, value: object): void {
  localStorage.setItem(key, JSON.stringify(value));
}

function sidebarClass(side: SidebarSide, suffix: string): string {
  return `sidebar-${side}-${suffix}`;
}

function sidebarWidthVar(side: SidebarSide): string {
  return `--sidebar-${side}-width`;
}

function navStateKey(detail: HTMLDetailsElement, index: number): string {
  const summary = detail.querySelector("summary");
  return detail.dataset.navKey || summary?.textContent?.trim() || `nav-${index}`;
}

function writeNavTreeState(state: Record<string, boolean>): void {
  writeJson(NAV_TREE_STATE_KEY, state);
}

function readStoredSidebarWidth(state: SidebarState, side: SidebarSide): number | null {
  const value = side === "left" ? state.leftWidth : state.rightWidth;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function writeStoredSidebarWidth(state: SidebarState, side: SidebarSide, width: number): void {
  if (side === "left") state.leftWidth = width;
  else state.rightWidth = width;
}

function currentSidebarWidth(layout: HTMLElement, side: SidebarSide): number {
  const raw = window.getComputedStyle(layout).getPropertyValue(sidebarWidthVar(side)).trim();
  const parsed = Number.parseFloat(raw);
  return Number.isFinite(parsed) ? parsed : DEFAULT_SIDEBAR_WIDTH;
}

function maxSidebarWidth(layout: HTMLElement, side: SidebarSide): number {
  const totalWidth = layout.getBoundingClientRect().width || window.innerWidth;
  const otherSide: SidebarSide = side === "left" ? "right" : "left";
  const otherSidebar = document.querySelector<HTMLElement>(`.sidebar-${otherSide}`);
  const otherVisible = (
    otherSidebar
    && window.getComputedStyle(otherSidebar).display !== "none"
    && !layout.classList.contains(sidebarClass(otherSide, "collapsed"))
  );
  const otherWidth = otherVisible
    ? (otherSidebar.getBoundingClientRect().width || currentSidebarWidth(layout, otherSide))
    : 0;
  return Math.max(MIN_SIDEBAR_WIDTH, Math.floor(totalWidth - otherWidth - MIN_CONTENT_WIDTH));
}

function clampSidebarWidth(layout: HTMLElement, side: SidebarSide, width: number): number {
  const nextWidth = Math.round(width);
  return Math.max(MIN_SIDEBAR_WIDTH, Math.min(nextWidth, maxSidebarWidth(layout, side)));
}

function setSidebarWidth(layout: HTMLElement, side: SidebarSide, width: number, persist: boolean): void {
  const clamped = clampSidebarWidth(layout, side, width);
  layout.style.setProperty(sidebarWidthVar(side), `${clamped}px`);
  if (!persist) return;

  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  writeStoredSidebarWidth(state, side, clamped);
  writeJson(SIDEBAR_STATE_KEY, state);
}

function syncSidebarWidths(layout: HTMLElement): void {
  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  setSidebarWidth(layout, "left", readStoredSidebarWidth(state, "left") ?? DEFAULT_SIDEBAR_WIDTH, false);
  setSidebarWidth(layout, "right", readStoredSidebarWidth(state, "right") ?? DEFAULT_SIDEBAR_WIDTH, false);
}

function setCollapsed(layout: HTMLElement, side: SidebarSide, collapsed: boolean): void {
  layout.classList.toggle(sidebarClass(side, "collapsed"), collapsed);
  layout.classList.remove(sidebarClass(side, "peeking"));

  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  if (side === "left") state.leftCollapsed = collapsed;
  if (side === "right") state.rightCollapsed = collapsed;
  writeJson(SIDEBAR_STATE_KEY, state);

  const button = document.querySelector<HTMLButtonElement>(`[data-sidebar-toggle="${side}"]`);
  if (button) {
    button.setAttribute("aria-expanded", String(!collapsed));
    button.setAttribute("aria-label", collapsed ? `Show ${side} sidebar` : `Hide ${side} sidebar`);
  }
}

function setPeeking(layout: HTMLElement, side: SidebarSide, peeking: boolean): void {
  if (!layout.classList.contains(sidebarClass(side, "collapsed"))) return;
  layout.classList.toggle(sidebarClass(side, "peeking"), peeking);
}

function addPeekButton(layout: HTMLElement, sidebar: HTMLElement, side: SidebarSide): void {
  const existing = document.querySelector(`.sidebar-peek-${side}`);
  if (existing) return;

  const button = document.createElement("button");
  button.type = "button";
  button.className = `sidebar-peek sidebar-peek-${side}`;
  button.innerHTML = side === "left" ? "&#9654;" : "&#9664;";
  button.setAttribute("aria-label", side === "left" ? "Show navigation" : "Show page sidebar");

  let hideTimer: number | undefined;
  const show = () => {
    if (hideTimer !== undefined) window.clearTimeout(hideTimer);
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

function addResizer(layout: HTMLElement, sidebar: HTMLElement, side: SidebarSide): void {
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

    const onMove = (moveEvent: PointerEvent): void => {
      const delta = moveEvent.clientX - startX;
      const nextWidth = side === "left" ? startWidth + delta : startWidth - delta;
      setSidebarWidth(layout, side, nextWidth, true);
    };

    const stop = (): void => {
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

function initSidebar(layout: HTMLElement, side: SidebarSide): void {
  const sidebar = document.querySelector<HTMLElement>(`.sidebar-${side}`);
  if (!sidebar) return;

  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  const collapsed = side === "left" ? state.leftCollapsed === true : state.rightCollapsed === true;
  layout.classList.toggle(sidebarClass(side, "collapsed"), collapsed);

  const button = document.querySelector<HTMLButtonElement>(`[data-sidebar-toggle="${side}"]`);
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

function initNavTreeState(): void {
  const details = document.querySelectorAll<HTMLDetailsElement>(".file-tree details");
  if (!details.length) return;

  const state = readJson<Record<string, boolean>>(NAV_TREE_STATE_KEY);
  details.forEach((detail, index) => {
    const key = navStateKey(detail, index);
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      detail.open = state[key];
    }

    detail.addEventListener("toggle", () => {
      state[key] = detail.open;
      writeNavTreeState(state);
    });

    const folderLink = detail.querySelector<HTMLAnchorElement>("summary .nav-folder-link");
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

    const toggle = detail.querySelector<HTMLButtonElement>("summary .nav-folder-toggle");
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

  const setAllDetails = (open: boolean): void => {
    details.forEach((detail, index) => {
      detail.open = open;
      state[navStateKey(detail, index)] = open;
    });
    writeNavTreeState(state);
  };

  document
    .querySelector<HTMLButtonElement>('[data-nav-tree-action="expand"]')
    ?.addEventListener("click", () => setAllDetails(true));
  document
    .querySelector<HTMLButtonElement>('[data-nav-tree-action="collapse"]')
    ?.addEventListener("click", () => setAllDetails(false));
}

export function initSidebars(): void {
  const layout = document.querySelector<HTMLElement>(".app-layout");
  if (!layout) return;

  syncSidebarWidths(layout);
  initSidebar(layout, "left");
  initSidebar(layout, "right");
  initNavTreeState();
  window.addEventListener("resize", () => syncSidebarWidths(layout));
}
