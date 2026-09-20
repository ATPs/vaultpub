/**
 * Initialize Mermaid diagrams.
 * Selects .mermaid elements and renders them client-side.
 */

export async function initMermaid(root: ParentNode = document): Promise<void> {
  const mermaidElements = root.querySelectorAll<HTMLElement>(".mermaid");
  if (mermaidElements.length === 0) return;
  const mermaid = await import("mermaid");
  mermaid.default.initialize({
    startOnLoad: false,
    theme: document.documentElement.classList.contains("theme-dark") ? "dark" : "default",
    securityLevel: "strict",
  });
  await Promise.all(Array.from(mermaidElements, async (el, idx) => {
    if (el.dataset.mermaidReady === "true") return;
    const source = el.dataset.mermaidSource || el.textContent || "";
    el.dataset.mermaidSource = source;
    el.dataset.mermaidReady = "true";
    try {
      const { svg } = await mermaid.default.render(`mermaid-${Date.now()}-${idx}`, source);
      el.innerHTML = svg;
    } catch {
      el.innerHTML = '<div class="mermaid-error">Diagram render error</div>';
      el.dataset.mermaidReady = "error";
    }
  }));
}
