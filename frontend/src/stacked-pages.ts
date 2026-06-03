/**
 * Callout folding and stacked-pages navigation.
 * Callouts with data-callout-fold="closed" start collapsed.
 */

export function initCalloutFold(): void {
  document.querySelectorAll<HTMLElement>(".callout").forEach((callout) => {
    const foldState = callout.getAttribute("data-callout-fold");
    if (foldState === "closed") {
      const content = callout.querySelector<HTMLElement>(".callout-content");
      if (content) content.style.display = "none";
    }

    const title = callout.querySelector<HTMLElement>(".callout-title");
    if (title) {
      title.style.cursor = "pointer";
      title.addEventListener("click", () => {
        const content = callout.querySelector<HTMLElement>(".callout-content");
        if (!content) return;
        const isHidden = content.style.display === "none";
        content.style.display = isHidden ? "" : "none";
        callout.setAttribute("data-callout-fold", isHidden ? "open" : "closed");
      });
    }
  });
}
