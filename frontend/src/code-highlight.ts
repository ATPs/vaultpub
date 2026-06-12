/**
 * Initialize syntax highlighting for code blocks using highlight.js.
 * Only loaded when <pre><code> elements exist on the page.
 */
import "./styles/highlight.css";

function decorateCodeBlock(codeBlock: HTMLElement): void {
  if (codeBlock.dataset.lineNumbersReady === "true") return;

  const source = codeBlock.innerHTML;
  const lines = source.split("\n");
  if (lines.length > 1 && lines[lines.length - 1] === "") {
    lines.pop();
  }

  const numberedHtml = lines
    .map((line, index) => {
      const content = line.length ? line : "&nbsp;";
      return (
        `<span class="code-line" data-line-number="${index + 1}">` +
        `<span class="code-line-content">${content}</span>` +
        `</span>`
      );
    })
    .join("");

  codeBlock.innerHTML = numberedHtml;
  codeBlock.dataset.lineNumbersReady = "true";
}

export function initCodeHighlight(): void {
  const codeBlocks = Array.from(document.querySelectorAll<HTMLElement>("pre code"));
  if (codeBlocks.length === 0) return;

  import("highlight.js").then((hljs) => {
    hljs.default.configure({
      cssSelector: "pre code",
      ignoreUnescapedHTML: true,
    });
    hljs.default.highlightAll();
    for (const codeBlock of codeBlocks) {
      decorateCodeBlock(codeBlock);
    }
  });
}
