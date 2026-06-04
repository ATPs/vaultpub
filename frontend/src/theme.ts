/**
 * Theme system — multi-theme with dropdown selector.
 * Stores preference in localStorage key "vaultpub.settings".
 */

interface ThemeInfo {
  id: string;
  name: string;
  group: "light" | "dark";
  preview: [string, string, string, string];
}

const THEMES: ThemeInfo[] = [
  { id: "light",         name: "Light",         group: "light", preview: ["#fafbfc", "#1a1a2e", "#2563eb", "#e5e7eb"] },
  { id: "dark",          name: "Dark",          group: "dark",  preview: ["#1a1b1e", "#e4e4e7", "#60a5fa", "#2d2d30"] },
  { id: "nord",          name: "Nord",          group: "dark",  preview: ["#2e3440", "#d8dee9", "#88c0d0", "#4c566a"] },
  { id: "solarized",     name: "Solarized",     group: "light", preview: ["#fdf6e3", "#586e75", "#268bd2", "#eee8d5"] },
  { id: "dracula",       name: "Dracula",       group: "dark",  preview: ["#282a36", "#f8f8f2", "#bd93f9", "#44475a"] },
  { id: "forest",        name: "Forest",        group: "dark",  preview: ["#1a2a1a", "#d4e4d4", "#6fcf6f", "#2d452d"] },
  { id: "glass-light",   name: "Glass Light",   group: "light", preview: ["rgba(250,251,252,0.55)", "#1a1a2e", "#2563eb", "rgba(0,0,0,0.08)"] },
  { id: "glass-dark",    name: "Glass Dark",    group: "dark",  preview: ["rgba(26,27,30,0.6)", "#e4e4e7", "#60a5fa", "rgba(255,255,255,0.06)"] },
  { id: "obsidian",      name: "Obsidian",      group: "dark",  preview: ["#1e1e1e", "#cccccc", "#7f6df2", "#3c3c3c"] },
  { id: "catppuccin",    name: "Catppuccin",    group: "light", preview: ["#eff1f5", "#4c4f69", "#1e66f5", "#ccd0da"] },
  { id: "colorful",      name: "Colorful",      group: "light", preview: ["#e11d48", "#7c3aed", "#2563eb", "#6366f1"] },
  { id: "colorful-dark", name: "Colorful Dark", group: "dark",  preview: ["#fb7185", "#a78bfa", "#60a5fa", "#818cf8"] },
];

const THEME_CLASS_PREFIX = "theme-";
const SETTINGS_KEY = "vaultpub.settings";

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

/* ---- build selector UI ---- */
function createSwatchSpans(preview: string[]): string {
  return preview
    .map((color) => `<span style="background:${color}"></span>`)
    .join("");
}

function buildThemeSelector(): void {
  const topbar = document.querySelector(".top-bar");
  if (!topbar) return;
  const actions = topbar.querySelector(".topbar-actions") || topbar;

  // Remove any existing theme-toggle button
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

  // Build dropdown
  const dropdown = document.createElement("div");
  dropdown.className = "theme-dropdown";
  dropdown.setAttribute("role", "listbox");

  const lightThemes = THEMES.filter((t) => t.group === "light");
  const darkThemes = THEMES.filter((t) => t.group === "dark");

  dropdown.innerHTML = `
    <div class="theme-dropdown-header">Light</div>
    ${lightThemes
      .map(
        (t) => `
      <button class="theme-option${t.id === currentThemeId ? " active" : ""}"
              role="option" data-theme-id="${t.id}" aria-selected="${t.id === currentThemeId}">
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
              role="option" data-theme-id="${t.id}" aria-selected="${t.id === currentThemeId}">
        <span class="theme-option-preview">${createSwatchSpans(t.preview)}</span>
        ${t.name}
      </button>`
      )
      .join("")}
  `;

  wrapper.appendChild(btn);
  wrapper.appendChild(dropdown);

  // Events
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    wrapper.classList.toggle("open");
  });

  dropdown.addEventListener("click", (e) => {
    const option = (e.target as HTMLElement).closest<HTMLButtonElement>(".theme-option");
    if (!option) return;
    const themeId = option.dataset.themeId;
    if (!themeId) return;

    setSettings({ theme: themeId });
    applyTheme(themeId);

    // Update button label
    const theme = THEMES.find((t) => t.id === themeId);
    if (theme) {
      btn.querySelector(".theme-selector-label")!.textContent = theme.name;
      btn.querySelector(".theme-swatch")!.innerHTML = createSwatchSpans(theme.preview);
    }

    // Update active state
    dropdown.querySelectorAll(".theme-option").forEach((el) => {
      el.classList.toggle("active", (el as HTMLElement).dataset.themeId === themeId);
      el.setAttribute("aria-selected", String((el as HTMLElement).dataset.themeId === themeId));
    });

    wrapper.classList.remove("open");
  });

  // Close on outside click
  document.addEventListener("click", () => wrapper.classList.remove("open"));

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
  buildThemeSelector();

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
  const btn = document.querySelector<HTMLButtonElement>(".theme-selector-btn");
  const dropdown = document.querySelector(".theme-dropdown");
  if (!btn || !dropdown) return;

  const theme = THEMES.find((t) => t.id === themeId);
  if (!theme) return;

  const label = btn.querySelector(".theme-selector-label");
  const swatch = btn.querySelector(".theme-swatch");
  if (label) label.textContent = theme.name;
  if (swatch) swatch.innerHTML = createSwatchSpans(theme.preview);

  dropdown.querySelectorAll(".theme-option").forEach((el) => {
    const id = (el as HTMLElement).dataset.themeId;
    el.classList.toggle("active", id === themeId);
    el.setAttribute("aria-selected", String(id === themeId));
  });
}
