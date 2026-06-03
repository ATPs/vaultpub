/**
 * Theme toggle: light / dark / system.
 * Stores preference in localStorage key "vaultpub.settings".
 */

type Theme = "light" | "dark" | "system";

function getSettings(): Record<string, unknown> {
  try {
    return JSON.parse(localStorage.getItem("vaultpub.settings") || "{}");
  } catch {
    return {};
  }
}

function setSettings(partial: Record<string, unknown>): void {
  const current = getSettings();
  const merged = { ...current, ...partial };
  localStorage.setItem("vaultpub.settings", JSON.stringify(merged));
}

function getStoredTheme(): Theme {
  const settings = getSettings();
  return (settings.theme as Theme) || "system";
}

function applyTheme(theme: Theme): void {
  const html = document.documentElement;
  html.classList.remove("theme-light", "theme-dark");

  if (theme === "light") {
    html.classList.add("theme-light");
  } else if (theme === "dark") {
    html.classList.add("theme-dark");
  } else {
    // system
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    html.classList.add(prefersDark ? "theme-dark" : "theme-light");
  }
}

function toggleTheme(): void {
  const current = getStoredTheme();
  const next: Theme = current === "light" ? "dark" : current === "dark" ? "system" : "light";
  setSettings({ theme: next });
  applyTheme(next);
}

export function initTheme(): void {
  const stored = getStoredTheme();
  applyTheme(stored);

  // Listen for system changes when in system mode
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (getStoredTheme() === "system") {
      applyTheme("system");
    }
  });

  // Add toggle button if present
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", toggleTheme);
  }

  // Or create one if show_theme_toggle setting is true
  const topbar = document.querySelector(".top-bar");
  if (topbar && !btn) {
    const toggleBtn = document.createElement("button");
    toggleBtn.id = "theme-toggle";
    toggleBtn.className = "theme-toggle-btn";
    toggleBtn.setAttribute("aria-label", "Toggle theme");
    toggleBtn.textContent = "🌓";
    toggleBtn.addEventListener("click", toggleTheme);
    topbar.appendChild(toggleBtn);
  }
}
