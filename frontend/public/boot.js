/**
 * Restore paint-critical VaultPub preferences before the main stylesheet renders.
 */
(function bootstrapVaultpubPreferences() {
  "use strict";

  var root = document.documentElement;
  var themeIds = [
    "light",
    "dark",
    "nord",
    "solarized",
    "dracula",
    "forest",
    "glass-light",
    "glass-dark",
    "obsidian",
    "catppuccin",
    "colorful",
    "colorful-dark",
  ];

  /** Return a stored JSON object, or an empty object when storage is unavailable or invalid. */
  function readStoredObject(key) {
    try {
      var value = JSON.parse(localStorage.getItem(key) || "{}");
      if (value && typeof value === "object" && !Array.isArray(value)) return value;
      localStorage.removeItem(key);
      return {};
    } catch (_error) {
      try {
        localStorage.removeItem(key);
      } catch (_storageError) {
        // Storage may be disabled; the in-memory fallback is still safe.
      }
      return {};
    }
  }

  /** Resolve the browser color-scheme preference without assuming matchMedia is available. */
  function systemTheme() {
    try {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    } catch (_error) {
      return "light";
    }
  }

  var settings = readStoredObject("vaultpub.settings");
  var storedTheme = typeof settings.theme === "string" ? settings.theme : "";
  var themeId = themeIds.indexOf(storedTheme) >= 0 ? storedTheme : systemTheme();
  Array.prototype.slice.call(root.classList).forEach(function removePreviousTheme(className) {
    if (className.indexOf("theme-") === 0) root.classList.remove(className);
  });
  root.classList.add("theme-" + themeId);

  var sidebarState = readStoredObject("vaultpub.sidebarState");
  if (sidebarState.topFolders !== true) return;

  var bootStyle = document.createElement("style");
  bootStyle.textContent = [
    "html.vaultpub-top-folders-booting .file-tree,",
    "html.vaultpub-top-folders-booting .topbar-context,",
    "html.vaultpub-top-folders-booting [data-nav-folder-layout=\"top\"] {",
    "  visibility: hidden;",
    "}",
  ].join("\n");
  document.head.appendChild(bootStyle);
  root.classList.add("vaultpub-top-folders-booting");

  var observer = null;

  /** Reveal navigation only after the main frontend has selected its final folder layout. */
  function finishFolderBootstrap() {
    if (!root.classList.contains("vaultpub-top-folders-booting")) return;
    root.classList.remove("vaultpub-top-folders-booting");
    if (observer) observer.disconnect();
  }

  /** Detect either a ready top-folder layout or the no-folder fallback. */
  function folderLayoutReady() {
    var fileTree = document.querySelector(".file-tree");
    var topNavigation = document.querySelector(".top-folder-nav.is-active");
    var layoutButton = document.querySelector('[data-nav-folder-layout="top"]');
    return Boolean(
      (fileTree && fileTree.classList.contains("folder-tabs-active") && topNavigation)
      || (layoutButton && layoutButton.disabled)
    );
  }

  if (typeof MutationObserver !== "undefined") {
    observer = new MutationObserver(function handleFolderLayoutMutation() {
      if (folderLayoutReady()) finishFolderBootstrap();
    });
    observer.observe(root, {
      attributes: true,
      attributeFilter: ["class", "disabled"],
      childList: true,
      subtree: true,
    });
  }

  document.addEventListener("DOMContentLoaded", function revealAfterFrontendInitialization() {
    window.requestAnimationFrame(function waitForFrontendFrame() {
      window.requestAnimationFrame(finishFolderBootstrap);
    });
  }, { once: true });
})();
