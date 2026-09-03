/**
 * Initialize KaTeX math rendering.
 * Finds .math elements and renders them client-side.
 */

export function initMath(root: ParentNode = document): void {
  const mathElements = root.querySelectorAll<HTMLElement>(".math");
  if (mathElements.length === 0) return;

  import("katex").then((katex) => {
    import("katex/dist/katex.min.css");

    mathElements.forEach((el) => {
      const isBlock = el.classList.contains("block");
      const formula = el.textContent?.trim() || "";
      if (!formula) return;

      try {
        katex.default.render(formula, el, {
          throwOnError: false,
          displayMode: isBlock,
        });
      } catch {
        // Keep original text on failure
      }
    });
  });
}
