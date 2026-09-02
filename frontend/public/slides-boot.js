/* Restore paint-critical Slide View preferences before Reveal initializes. */
(function bootstrapSlidePreferences() {
  "use strict";
  var themes = ["light", "dark", "nord", "solarized", "dracula", "forest", "glass-light", "glass-dark", "obsidian", "catppuccin", "colorful", "colorful-dark"];
  var preferences = {};
  try {
    var value = JSON.parse(localStorage.getItem("vaultpub.slideSettings.v2") || localStorage.getItem("vaultpub.slideSettings.v1") || "{}");
    if (value && typeof value === "object" && !Array.isArray(value)) preferences = value;
  } catch (_error) {
    // Storage is optional; server-rendered defaults remain usable.
  }
  var root = document.documentElement;
  var theme = typeof preferences.theme === "string" && themes.indexOf(preferences.theme) >= 0 ? preferences.theme : "";
  if (theme) root.className = root.className.replace(/\btheme-[\w-]+\b/g, "").trim() + " theme-" + theme;
  if (typeof preferences.textScale === "number" && preferences.textScale >= 75 && preferences.textScale <= 300) root.style.setProperty("--vaultpub-slide-scale", String(preferences.textScale / 100));
  if (preferences.codeWrap === false) root.dataset.slideCodeWrap = "false";
  if (preferences.center === true) root.dataset.slideCenter = "true";
})();
