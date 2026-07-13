/**
 * Desktop sidebar controls and persistent file-tree state.
 */

type SidebarSide = "left" | "right";
type NavSortMode = "predefined" | "name-asc" | "name-desc" | "created-desc" | "created-asc" | "modified-desc" | "modified-asc";

interface SidebarState {
  leftCollapsed?: boolean;
  rightCollapsed?: boolean;
  leftWidth?: number;
  rightWidth?: number;
  topFolders?: boolean;
  navSort?: NavSortMode;
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

function isNavSortMode(value: string | undefined): value is NavSortMode {
  return value === "predefined"
    || value === "name-asc"
    || value === "name-desc"
    || value === "created-desc"
    || value === "created-asc"
    || value === "modified-desc"
    || value === "modified-asc";
}

function navItemValue(item: HTMLLIElement, name: "navCreated" | "navModified"): number {
  const value = Number(item.dataset[name] || "0");
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function compareNames(left: HTMLLIElement, right: HTMLLIElement): number {
  return (left.dataset.navName || "").localeCompare(right.dataset.navName || "", undefined, { sensitivity: "base" });
}

function sortNavigationList(list: HTMLUListElement, mode: NavSortMode): void {
  const items = Array.from(list.children).filter(
    (item): item is HTMLLIElement => item instanceof HTMLLIElement && item.hasAttribute("data-nav-sort-item"),
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

function applyNavigationSort(mode: NavSortMode): void {
  document.querySelectorAll<HTMLUListElement>(".file-tree ul, .directory-list, .directory-context-nav ul").forEach((list) => {
    sortNavigationList(list, mode);
  });
  document.dispatchEvent(new CustomEvent("vaultpub:navigation-sorted"));
}

function initNavigationSort(): void {
  const select = document.querySelector<HTMLSelectElement>("[data-nav-sort]");
  if (!select) return;
  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  const mode = isNavSortMode(state.navSort) ? state.navSort : "predefined";
  select.value = mode;
  applyNavigationSort(mode);
  select.addEventListener("change", () => {
    const next = isNavSortMode(select.value) ? select.value : "predefined";
    const nextState = readJson<SidebarState>(SIDEBAR_STATE_KEY);
    nextState.navSort = next;
    writeJson(SIDEBAR_STATE_KEY, nextState);
    applyNavigationSort(next);
  });
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
    const visibleDetails = document.querySelectorAll<HTMLDetailsElement>(
      ".file-tree.folder-tabs-active .folder-tabs-selected details, .file-tree:not(.folder-tabs-active) details",
    );
    visibleDetails.forEach((detail) => {
      const index = Array.from(details).indexOf(detail);
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

interface FolderSection {
  id: string;
  label: string;
  item: HTMLLIElement | null;
}

function currentFolderSection(sections: FolderSection[]): string {
  const currentPath = document.querySelector<HTMLElement>("[data-current-path]")?.dataset.currentPath;
  if (!currentPath) return "root";

  const matching = sections.find((section) => (
    Array.from(section.item?.querySelectorAll<HTMLAnchorElement>("a") || []).some(
      (link) => link.getAttribute("href") === currentPath,
    )
  ));
  return matching?.id || "root";
}

function initTopFolderNavigation(): void {
  const fileTree = document.querySelector<HTMLElement>(".file-tree");
  const topbar = document.querySelector<HTMLElement>(".top-bar");
  const layoutButton = document.querySelector<HTMLButtonElement>("[data-nav-folder-layout=\"top\"]");
  const rootList = fileTree?.querySelector<HTMLUListElement>(":scope > ul");
  if (!fileTree || !topbar || !layoutButton || !rootList) return;

  const rootItems = Array.from(rootList.children).filter(
    (item): item is HTMLLIElement => item instanceof HTMLLIElement,
  );
  const folderSections = rootItems.flatMap((item) => {
    const detail = item.querySelector<HTMLDetailsElement>(":scope > details");
    const link = detail?.querySelector<HTMLAnchorElement>(":scope > summary .nav-folder-link");
    if (!detail || !link) return [];
    return [{ id: detail.dataset.navKey || link.href, label: link.textContent?.trim().replace(/\/$/, "") || "Folder", item }];
  });
  if (!folderSections.length) {
    layoutButton.disabled = true;
    layoutButton.title = "No top-level folders";
    layoutButton.setAttribute("aria-label", "No top-level folders");
    return;
  }

  const rootFiles = rootItems.filter((item) => item.querySelector(":scope > a"));
  rootFiles.forEach((item) => item.classList.add("folder-tabs-root-file"));

  const sections: FolderSection[] = [
    ...(rootFiles.length ? [{ id: "root", label: "Root", item: null }] : []),
    ...folderSections,
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
  let layoutFrame: number | undefined;

  const setButtonState = (enabled: boolean): void => {
    layoutButton.innerHTML = enabled ? "&#8659;" : "&#8657;";
    const label = enabled ? "Show folders in sidebar" : "Move folders to top bar";
    layoutButton.title = label;
    layoutButton.setAttribute("aria-label", label);
    layoutButton.setAttribute("aria-pressed", String(enabled));
  };

  const closeOverflow = (): void => {
    overflowMenu.hidden = true;
    overflowButton.setAttribute("aria-expanded", "false");
  };

  const updateSelection = (): void => {
    const selected = sections.find((section) => section.id === selectedId) || sections[0];
    selectedId = selected.id;
    rootItems.forEach((item) => item.classList.remove("folder-tabs-selected"));
    fileTree.classList.toggle("folder-tabs-root-selected", selected.id === "root");
    if (selected.item) {
      selected.item.classList.add("folder-tabs-selected");
      const detail = selected.item.querySelector<HTMLDetailsElement>(":scope > details");
      if (detail) detail.open = true;
    }
  };

  const makeTab = (section: FolderSection): HTMLButtonElement => {
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

  const layoutOverflow = (): void => {
    if (!fileTree.classList.contains("folder-tabs-active")) return;
    let visible = [...sections];
    const hidden: FolderSection[] = [];

    const render = (): void => {
      tabs.replaceChildren(...visible.map(makeTab));
      overflowMenu.replaceChildren(...hidden.map(makeTab));
      nav.classList.toggle("has-overflow", hidden.length > 0);
    };

    render();
    while (tabs.scrollWidth > tabs.clientWidth && visible.length > 1) {
      const lastNonSelected = [...visible].reverse().findIndex((section) => section.id !== selectedId);
      if (lastNonSelected < 0) break;
      const index = visible.length - 1 - lastNonSelected;
      hidden.unshift(visible[index]);
      visible.splice(index, 1);
      render();
    }
  };

  const scheduleOverflowLayout = (): void => {
    if (layoutFrame !== undefined) window.cancelAnimationFrame(layoutFrame);
    layoutFrame = window.requestAnimationFrame(() => {
      layoutFrame = undefined;
      layoutOverflow();
    });
  };

  const setEnabled = (enabled: boolean): void => {
    fileTree.classList.toggle("folder-tabs-active", enabled);
    nav.classList.toggle("is-active", enabled);
    topbar.classList.toggle("top-folder-nav-active", enabled);
    setButtonState(enabled);
    const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
    state.topFolders = enabled;
    writeJson(SIDEBAR_STATE_KEY, state);
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
    if (!nav.contains(event.target as Node)) closeOverflow();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeOverflow();
  });
  layoutButton.addEventListener("click", () => {
    setEnabled(!fileTree.classList.contains("folder-tabs-active"));
  });
  new ResizeObserver(scheduleOverflowLayout).observe(nav);

  const state = readJson<SidebarState>(SIDEBAR_STATE_KEY);
  setEnabled(state.topFolders === true);

  document.addEventListener("vaultpub:navigation-sorted", () => {
    const rootSection = sections.find((section) => section.id === "root");
    const orderedFolders = Array.from(rootList.children).flatMap((item) => {
      const detail = item.querySelector<HTMLDetailsElement>(":scope > details");
      const link = detail?.querySelector<HTMLAnchorElement>(":scope > summary .nav-folder-link");
      if (!detail || !link) return [];
      return [sections.find((section) => section.id === (detail.dataset.navKey || link.href))];
    }).filter((section): section is FolderSection => Boolean(section));
    sections.splice(0, sections.length, ...(rootSection ? [rootSection] : []), ...orderedFolders);
    updateSelection();
    scheduleOverflowLayout();
  });
}

export function initSidebars(): void {
  const layout = document.querySelector<HTMLElement>(".app-layout");
  if (!layout) return;

  syncSidebarWidths(layout);
  initSidebar(layout, "left");
  initSidebar(layout, "right");
  initNavigationSort();
  initNavTreeState();
  initTopFolderNavigation();
  window.addEventListener("resize", () => syncSidebarWidths(layout));
}
