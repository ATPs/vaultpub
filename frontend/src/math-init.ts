/**
 * Initialize KaTeX math rendering.
 * Finds .math elements and renders them client-side.
 */

export async function initMath(root: ParentNode = document): Promise<void> {
  const mathElements = root.querySelectorAll<HTMLElement>(".math");
  if (mathElements.length === 0) return;
  const [katex] = await Promise.all([import("katex"), import("katex/dist/katex.min.css")]);
  mathElements.forEach((el) => {
    if (el.dataset.mathReady === "true") return;
    const formula = el.dataset.mathSource || el.textContent?.trim() || "";
    el.dataset.mathSource = formula;
    el.dataset.mathReady = "true";
    if (!formula) return;
    try {
      katex.default.render(formula, el, { throwOnError: false, displayMode: el.classList.contains("block") });
    } catch { el.dataset.mathReady = "error"; }
  });
}
