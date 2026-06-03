/**
 * Initialize Mermaid diagrams.
 * Selects .mermaid elements and renders them client-side.
 */

export function initMermaid(): void {
  const mermaidElements = document.querySelectorAll<HTMLElement>(".mermaid");
  if (mermaidElements.length === 0) return;

  // Dynamic import to avoid loading mermaid when not needed
  import("mermaid").then((mermaid) => {
    mermaid.default.initialize({
      startOnLoad: false,
      theme: document.documentElement.classList.contains("theme-dark") ? "dark" : "default",
      securityLevel: "strict",
    });

    mermaidElements.forEach(async (el, idx) => {
      const id = `mermaid-${idx}`;
      try {
        const { svg } = await mermaid.default.render(id, el.textContent || "");
        el.innerHTML = svg;
      } catch {
        el.innerHTML = '<div class="mermaid-error">Diagram render error</div>';
      }
    });
  });
}
