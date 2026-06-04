/**
 * Initialize syntax highlighting for code blocks using highlight.js.
 * Only loaded when <pre><code> elements exist on the page.
 */
import "./styles/highlight.css";

export function initCodeHighlight(): void {
  const codeBlocks = document.querySelectorAll("pre code");
  if (codeBlocks.length === 0) return;

  import("highlight.js").then((hljs) => {
    hljs.default.configure({
      cssSelector: "pre code",
      ignoreUnescapedHTML: true,
    });
    hljs.default.highlightAll();
  });
}
