import Reveal from "reveal.js";
import "reveal.js/reveal.css";
import "./styles/slides.css";
import { initCalloutFold } from "./stacked-pages";
import { initMath } from "./math-init";
import { initMermaid } from "./mermaid-init";

type RevealConfig = Record<string, boolean | number | string>;

function readRevealConfig(): RevealConfig {
  const element = document.getElementById("vaultpub-slides-config");
  if (!element?.textContent) return {};

  try {
    return JSON.parse(element.textContent) as RevealConfig;
  } catch {
    return {};
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const revealElement = document.querySelector<HTMLElement>(".reveal");
  if (!revealElement) return;

  const deck = new Reveal(revealElement, readRevealConfig());
  void deck.initialize().then(() => {
    initCalloutFold();
    initMermaid();
    initMath();
    // Keep the slide entry's lazy highlighter isolated from the article entry.
    // Vite otherwise moves the article implementation into a shared chunk.
    void import("./code-highlight?slides").then((module) => {
      const { initCodeHighlight } = module as unknown as typeof import("./code-highlight");
      initCodeHighlight();
    });
    requestAnimationFrame(() => deck.layout());
  });
});
