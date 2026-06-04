/**
 * Desktop sidebar controls and persistent file-tree state.
 */

type SidebarSide = "left" | "right";

interface SidebarState {
  leftCollapsed?: boolean;
  rightCollapsed?: boolean;
}

const SIDEBAR_STATE_KEY = "vaultpub.sidebarState";
const NAV_TREE_STATE_KEY = "vaultpub.navTreeState";

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
  button.textContent = side === "left" ? "Nav" : "Page";
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
}

function initNavTreeState(): void {
  const details = document.querySelectorAll<HTMLDetailsElement>(".file-tree details");
  if (!details.length) return;

  const state = readJson<Record<string, boolean>>(NAV_TREE_STATE_KEY);
  details.forEach((detail, index) => {
    const summary = detail.querySelector("summary");
    const key = detail.dataset.navKey || summary?.textContent?.trim() || `nav-${index}`;
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      detail.open = state[key];
    }

    detail.addEventListener("toggle", () => {
      state[key] = detail.open;
      writeJson(NAV_TREE_STATE_KEY, state);
    });
  });
}

export function initSidebars(): void {
  const layout = document.querySelector<HTMLElement>(".app-layout");
  if (!layout) return;

  initSidebar(layout, "left");
  initSidebar(layout, "right");
  initNavTreeState();
}
