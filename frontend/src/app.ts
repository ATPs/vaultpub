/**
 * vaultpub frontend entry point.
 * Enhances server-rendered HTML with interactive features.
 */
import "./styles/base.css";
import "./styles/obsidian-vars.css";
import "./styles/callouts.css";
import "./styles/layout.css";
import { initTheme } from "./theme";
import { initSearch } from "./search";
import { initPreview } from "./preview";
import { initGraph } from "./graph";
import { initCalloutFold } from "./stacked-pages";
import { initMermaid } from "./mermaid-init";
import { initMath } from "./math-init";
import { initRealtime } from "./realtime";
import { initMobileDrawer } from "./mobile";
import { initSidebars } from "./sidebar";

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSearch();
  initPreview();
  initGraph();
  initCalloutFold();
  initMermaid();
  initMath();
  initRealtime();
  initMobileDrawer();
  initSidebars();
});
