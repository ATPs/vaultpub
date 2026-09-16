/** Theme system — multi-theme with dropdown selector. */
import { READING_THEMES as THEMES } from "./theme-data";

const THEME_CLASS_PREFIX = "theme-";
const SETTINGS_KEY = "vaultpub.settings";
const DEFAULT_FONT_SIZE = 16;
const MIN_FONT_SIZE = 12;
const MAX_FONT_SIZE = 28;

/* ---- settings helpers ---- */
function getSettings(): Record<string, unknown> {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
  } catch {
    return {};
  }
}

function setSettings(partial: Record<string, unknown>): void {
  const current = getSettings();
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({ ...current, ...partial }));
}

function deleteSetting(key: string): void {
  const current = getSettings();
  delete current[key];
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(current));
}

function validFontSize(value: unknown): number | null {
  const size = typeof value === "number" ? value : Number(value);
  return Number.isInteger(size) && size >= MIN_FONT_SIZE && size <= MAX_FONT_SIZE ? size : null;
}

function defaultFontSize(): number {
  return validFontSize(document.body.dataset.fontSizeDefault) ?? DEFAULT_FONT_SIZE;
}

function storedFontSize(fallback: number): number {
  return validFontSize(getSettings().fontSize) ?? fallback;
}

function applyFontSize(fontSize: number): void {
  document.documentElement.style.setProperty("--font-size", `${fontSize}px`);
}

/* ---- resolve stored theme ---- */
function getStoredThemeId(): string {
  const settings = getSettings();
  const stored = settings.theme as string | undefined;
  if (stored && THEMES.some((t) => t.id === stored)) return stored;

  // Legacy: map old light/dark/system to theme ids
  if (stored === "light") return "light";
  if (stored === "dark") return "dark";
  if (stored === "system") return resolveSystemTheme();

  return resolveSystemTheme();
}

function resolveSystemTheme(): string {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/* ---- apply ---- */
function applyTheme(themeId: string): void {
  const html = document.documentElement;
  const existing = Array.from(html.classList).filter((c) => c.startsWith(THEME_CLASS_PREFIX));
  html.classList.remove(...existing);
  html.classList.add(THEME_CLASS_PREFIX + themeId);
}

/* ---- build Settings UI ---- */
function createSwatchSpans(preview: string[]): string {
  return preview
    .map((color) => `<span style="background:${color}"></span>`)
    .join("");
}

function buildSettingsMenu(): void {
  const topbar = document.querySelector(".top-bar");
  if (!topbar) return;
  const actions = topbar.querySelector(".topbar-actions") || topbar;

  // Remove any existing theme-toggle button
  const existingBtn = document.getElementById("theme-toggle");
  if (existingBtn) existingBtn.remove();

  const wrapper = document.createElement("div");
  wrapper.className = "settings-menu";

  const currentThemeId = getStoredThemeId();
  const currentTheme = THEMES.find((t) => t.id === currentThemeId) || THEMES[0];
  const publisherFontSize = defaultFontSize();
  const currentFontSize = storedFontSize(publisherFontSize);

  const btn = document.createElement("button");
  btn.className = "settings-menu-btn";
  btn.setAttribute("aria-label", "Settings");
  btn.setAttribute("aria-haspopup", "menu");
  btn.setAttribute("aria-expanded", "false");
  btn.innerHTML = `
    <span class="theme-swatch">${createSwatchSpans(currentTheme.preview)}</span>
    <span class="settings-menu-label">Settings</span>
    <span class="settings-menu-caret">&#9660;</span>
  `;

  // Build dropdown
  const dropdown = document.createElement("div");
  dropdown.className = "settings-dropdown";
  dropdown.setAttribute("role", "menu");

  const lightThemes = THEMES.filter((t) => t.group === "light");
  const darkThemes = THEMES.filter((t) => t.group === "dark");

  dropdown.innerHTML = `
    <div class="settings-section settings-layout-controls">
      <button class="settings-option" type="button" role="menuitem" data-layout-action="toggle-wide" aria-pressed="false">Wide content</button>
    </div>
  `;

  const orderEditorUrl = document.body.dataset.orderEditorUrl;
  if (orderEditorUrl) {
    const orderSection = document.createElement("div");
    orderSection.className = "settings-section settings-order-action";
    orderSection.innerHTML = `<a class="settings-option" role="menuitem" href="${orderEditorUrl}">Custom order</a>`;
    dropdown.appendChild(orderSection);
  }

  const appearanceSection = document.createElement("div");
  appearanceSection.className = "settings-section settings-appearance";
  appearanceSection.innerHTML = `
    <div class="settings-dropdown-header">Appearance</div>
    <div class="settings-font-size">
      <label for="settings-font-size">Text size <output data-font-size-output>${currentFontSize}px</output></label>
      <input id="settings-font-size" data-setting="font-size" type="range" min="${MIN_FONT_SIZE}" max="${MAX_FONT_SIZE}" step="1" value="${currentFontSize}">
      <button class="settings-font-size-reset" type="button" data-action="reset-font-size">Reset</button>
    </div>
    <div class="theme-dropdown-header">Light</div>
    ${lightThemes
      .map(
        (t) => `
      <button class="theme-option${t.id === currentThemeId ? " active" : ""}"
              role="menuitemradio" data-theme-id="${t.id}" aria-checked="${t.id === currentThemeId}">
        <span class="theme-option-preview">${createSwatchSpans(t.preview)}</span>
        ${t.name}
      </button>`
      )
      .join("")}
    <div class="theme-dropdown-header">Dark</div>
    ${darkThemes
      .map(
        (t) => `
      <button class="theme-option${t.id === currentThemeId ? " active" : ""}"
              role="menuitemradio" data-theme-id="${t.id}" aria-checked="${t.id === currentThemeId}">
        <span class="theme-option-preview">${createSwatchSpans(t.preview)}</span>
        ${t.name}
      </button>`
      )
      .join("")}

  `;

  const context = document.querySelector<HTMLElement>(".topbar-context");
  const noteSlidesUrl = context?.dataset.slideNoteUrl;
  const vaultSlidesUrl = document.body.dataset.vaultSlidesUrl;
  const hasVaultLaunch = Boolean(vaultSlidesUrl && document.getElementById("vaultpub-slide-scopes"));
  if (noteSlidesUrl || hasVaultLaunch) {
    const slideSection = document.createElement("div");
    slideSection.className = "settings-section settings-slide-actions";
    slideSection.innerHTML = [
      noteSlidesUrl
        ? `<a class="settings-option settings-slide-action" role="menuitem" href="${noteSlidesUrl}" title="View this Markdown note in Slide Mode">Note in Slide View</a>`
        : "",
      hasVaultLaunch
        ? '<button class="settings-option settings-slide-action" type="button" role="menuitem" data-action="launch-vault-slides" title="Choose a scope and order for Slide View">Vault in Slide View</button>'
        : "",
    ].join("");
    dropdown.appendChild(slideSection);
  }
  dropdown.appendChild(appearanceSection);

  wrapper.appendChild(btn);
  wrapper.appendChild(dropdown);

  // Events
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = !wrapper.classList.contains("open");
    wrapper.classList.toggle("open", open);
    btn.setAttribute("aria-expanded", String(open));
  });

  dropdown.addEventListener("click", (e) => {
    const action = (e.target as HTMLElement).closest<HTMLElement>("[data-action]")?.dataset.action;
    if (action === "reset-font-size") {
      deleteSetting("fontSize");
      document.documentElement.style.removeProperty("--font-size");
      const input = dropdown.querySelector<HTMLInputElement>("[data-setting=font-size]");
      const output = dropdown.querySelector<HTMLOutputElement>("[data-font-size-output]");
      if (input) input.value = String(publisherFontSize);
      if (output) output.value = `${publisherFontSize}px`;
      return;
    }

    const option = (e.target as HTMLElement).closest<HTMLButtonElement>(".theme-option");
    if (!option) return;
    const themeId = option.dataset.themeId;
    if (!themeId) return;

    setSettings({ theme: themeId });
    applyTheme(themeId);

    const theme = THEMES.find((t) => t.id === themeId);
    if (theme) {
      btn.querySelector(".theme-swatch")!.innerHTML = createSwatchSpans(theme.preview);
    }

    // Update active state
    dropdown.querySelectorAll(".theme-option").forEach((el) => {
      el.classList.toggle("active", (el as HTMLElement).dataset.themeId === themeId);
      el.setAttribute("aria-checked", String((el as HTMLElement).dataset.themeId === themeId));
    });

    wrapper.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
  });

  dropdown.addEventListener("input", (e) => {
    const input = (e.target as HTMLElement).closest<HTMLInputElement>("[data-setting=font-size]");
    if (!input) return;
    const fontSize = validFontSize(input.value);
    if (fontSize === null) return;
    applyFontSize(fontSize);
    setSettings({ fontSize });
    const output = dropdown.querySelector<HTMLOutputElement>("[data-font-size-output]");
    if (output) output.value = `${fontSize}px`;
  });

  // Close on outside click
  document.addEventListener("click", (event) => {
    if (!wrapper.contains(event.target as Node)) {
      wrapper.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && wrapper.classList.contains("open")) {
      wrapper.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
      btn.focus();
    }
  });

  // Insert before search trigger (or at end)
  const searchTrigger = actions.querySelector(".search-trigger");
  if (searchTrigger) {
    actions.insertBefore(wrapper, searchTrigger);
  } else {
    actions.appendChild(wrapper);
  }
}

/* ---- public ---- */
export function initTheme(): void {
  const themeId = getStoredThemeId();
  applyTheme(themeId);
  buildSettingsMenu();

  // Listen for system preference changes
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const stored = getSettings().theme as string | undefined;
    // Only auto-switch if user chose "system" or hasn't made an explicit theme choice yet
    if (!stored || stored === "system") {
      const sysTheme = resolveSystemTheme();
      applyTheme(sysTheme);
      // Update selector UI without saving
      updateSelectorForTheme(sysTheme);
    }
  });
}

function updateSelectorForTheme(themeId: string): void {
  const btn = document.querySelector<HTMLButtonElement>(".settings-menu-btn");
  const dropdown = document.querySelector(".settings-dropdown");
  if (!btn || !dropdown) return;

  const theme = THEMES.find((t) => t.id === themeId);
  if (!theme) return;

  const swatch = btn.querySelector(".theme-swatch");
  if (swatch) swatch.innerHTML = createSwatchSpans(theme.preview);

  dropdown.querySelectorAll(".theme-option").forEach((el) => {
    const id = (el as HTMLElement).dataset.themeId;
    el.classList.toggle("active", id === themeId);
    el.setAttribute("aria-checked", String(id === themeId));
  });
}
