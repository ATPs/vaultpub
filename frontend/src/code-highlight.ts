/**
 * Initialize syntax highlighting for code blocks using highlight.js.
 * Only loaded when <pre><code> elements exist on the page.
 */
/**
 * Split a highlighted code block into line fragments without corrupting spans.
 *
 * Explanation:
 *   Input: a highlighted `<code>` element whose inline highlight spans may
 *   cross newline characters.
 *   Output: one document fragment per visual code line.
 *   Where: Used by `decorateCodeBlock` before adding line-number wrappers.
 *   What: Walks the highlighted DOM and clones inline ancestors per line so
 *   multi-line strings keep valid span markup instead of splitting raw HTML.
 */
function splitHighlightedLines(codeBlock: HTMLElement): DocumentFragment[] {
  const lines: DocumentFragment[] = [document.createDocumentFragment()];
  const originalText = codeBlock.textContent || "";

  const currentLine = (): DocumentFragment => lines[lines.length - 1];

  const appendSegment = (text: string, ancestors: HTMLElement[]): void => {
    if (!text) return;

    let parent: Node = currentLine();
    for (const ancestor of ancestors) {
      const clone = ancestor.cloneNode(false) as HTMLElement;
      parent.appendChild(clone);
      parent = clone;
    }
    parent.appendChild(document.createTextNode(text));
  };

  const appendText = (text: string, ancestors: HTMLElement[]): void => {
    const parts = text.split("\n");
    parts.forEach((part, index) => {
      if (index > 0) {
        lines.push(document.createDocumentFragment());
      }
      appendSegment(part, ancestors);
    });
  };

  const visitNode = (node: Node, ancestors: HTMLElement[]): void => {
    if (node.nodeType === Node.TEXT_NODE) {
      appendText(node.textContent || "", ancestors);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;

    const element = node as HTMLElement;
    if (element.tagName === "BR") {
      lines.push(document.createDocumentFragment());
      return;
    }

    const nextAncestors = [...ancestors, element];
    Array.from(element.childNodes).forEach((child) => visitNode(child, nextAncestors));
  };

  Array.from(codeBlock.childNodes).forEach((child) => visitNode(child, []));

  if (lines.length > 1 && !lines[lines.length - 1].hasChildNodes() && originalText.endsWith("\n")) {
    lines.pop();
  }

  return lines;
}

function decorateCodeBlock(codeBlock: HTMLElement): void {
  if (codeBlock.dataset.lineNumbersReady === "true") return;

  const numberedLines = splitHighlightedLines(codeBlock).map((line, index) => {
    const lineElement = document.createElement("span");
    lineElement.className = "code-line";
    lineElement.dataset.lineNumber = String(index + 1);

    const contentElement = document.createElement("span");
    contentElement.className = "code-line-content";
    if (line.hasChildNodes()) {
      contentElement.appendChild(line);
    } else {
      contentElement.appendChild(document.createTextNode("\u00a0"));
    }

    lineElement.appendChild(contentElement);
    return lineElement;
  });

  codeBlock.replaceChildren(...numberedLines);
  codeBlock.dataset.lineNumbersReady = "true";
}

export function initCodeHighlight(root: ParentNode = document): void {
  const codeBlocks = Array.from(root.querySelectorAll<HTMLElement>("pre code"));
  if (codeBlocks.length === 0) return;

  import("highlight.js").then((hljs) => {
    hljs.default.configure({ ignoreUnescapedHTML: true });
    for (const codeBlock of codeBlocks) {
      if (!codeBlock.dataset.highlighted) hljs.default.highlightElement(codeBlock);
      decorateCodeBlock(codeBlock);
    }
  });
}
