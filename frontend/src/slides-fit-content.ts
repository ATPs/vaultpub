const MEDIA_SELECTOR = "img,video,iframe";

const shell = <T extends HTMLElement>(element: T): T => element.cloneNode(false) as T;

const splitParagraphAtMedia = (paragraph: HTMLElement): HTMLElement[] => {
  const parts: HTMLElement[] = [];
  let nodes: Node[] = [];
  const commit = (): void => { if (nodes.length) { const part = shell(paragraph); part.append(...nodes); parts.push(part); nodes = []; } };
  Array.from(paragraph.childNodes).forEach((node) => { nodes.push(node.cloneNode(true)); if (node instanceof HTMLElement && (node.matches(MEDIA_SELECTOR) || node.querySelector(MEDIA_SELECTOR))) commit(); });
  commit();
  return parts.length > 1 ? parts : [paragraph.cloneNode(true) as HTMLElement];
};

const splitList = (list: HTMLElement): HTMLElement[] => {
  const fragments: HTMLElement[] = [];
  let number = Number(list.getAttribute("start") || 1);
  Array.from(list.children).filter((node): node is HTMLElement => node.tagName === "LI").forEach((item) => {
    const value = Number(item.getAttribute("value") || number);
    const mediaParagraph = Array.from(item.children).find((node): node is HTMLElement => node.tagName === "P" && node.querySelectorAll(MEDIA_SELECTOR).length > 1);
    const parts = mediaParagraph ? splitParagraphAtMedia(mediaParagraph) : [item.cloneNode(true) as HTMLElement];
    parts.forEach((part, index) => {
      const listCopy = shell(list);
      if (list.tagName === "OL") listCopy.setAttribute("start", String(value));
      const itemCopy = shell(item);
      if (mediaParagraph) {
        const children = Array.from(item.children); const paragraphIndex = children.indexOf(mediaParagraph);
        if (index === 0) children.slice(0, paragraphIndex).forEach((child) => itemCopy.append(child.cloneNode(true)));
        itemCopy.append(part);
        if (index === parts.length - 1) children.slice(paragraphIndex + 1).forEach((child) => itemCopy.append(child.cloneNode(true)));
      } else itemCopy.replaceChildren(...Array.from(part.childNodes).map((node) => node.cloneNode(true)));
      if (index > 0) { listCopy.classList.add("slides-fit-list-continuation"); itemCopy.classList.add("slides-fit-list-continuation-item"); }
      listCopy.append(itemCopy); fragments.push(listCopy);
    });
    number = value + 1;
  });
  return fragments.length ? fragments : [list.cloneNode(true) as HTMLElement];
};

const splitCallout = (callout: HTMLElement): HTMLElement[] => {
  const title = callout.querySelector<HTMLElement>(":scope > .callout-title");
  const content = callout.querySelector<HTMLElement>(":scope > .callout-content");
  if (!content) return [callout.cloneNode(true) as HTMLElement];
  const parts: HTMLElement[] = [];
  Array.from(content.children).forEach((child) => {
    const children = child.tagName === "OL" || child.tagName === "UL" ? splitList(child as HTMLElement) : [child.cloneNode(true) as HTMLElement];
    children.forEach((item, index) => {
      const copy = shell(callout); if (title && (parts.length === 0 || index === 0)) copy.append(title.cloneNode(true));
      const contentCopy = shell(content); contentCopy.append(item); copy.append(contentCopy); parts.push(copy);
    });
  });
  return parts.length ? parts : [callout.cloneNode(true) as HTMLElement];
};

const splitCode = (pre: HTMLElement): HTMLElement[] => {
  const code = pre.querySelector("code"); const lines = code ? Array.from(code.querySelectorAll(":scope > .code-line")) : [];
  if (!code) return [pre.cloneNode(true) as HTMLElement];
  if (!lines.length) {
    const rawLines = (code.textContent || "").split("\n");
    const visibleLines = rawLines.filter((line, index) => line || index < rawLines.length - 1);
    return visibleLines.map((line, index) => {
    const preCopy = shell(pre); const codeCopy = shell(code); const lineCopy = document.createElement("span");
    lineCopy.className = "code-line"; lineCopy.dataset.lineNumber = String(index + 1); lineCopy.textContent = line || "\u00a0";
    codeCopy.append(lineCopy); preCopy.append(codeCopy); return preCopy;
    });
  }
  return lines.map((line) => { const preCopy = shell(pre); const codeCopy = shell(code); codeCopy.append(line.cloneNode(true)); preCopy.append(codeCopy); return preCopy; });
};

export const fitUnits = (source: HTMLElement): HTMLElement[] => {
  const content = source.querySelector<HTMLElement>(".vaultpub-slide-content");
  if (!content) return [];
  const units: HTMLElement[] = [];
  Array.from(content.children).filter((node): node is HTMLElement => node instanceof HTMLElement).forEach((node) => {
    if (node.classList.contains("callout")) units.push(...splitCallout(node));
    else if (/^H[1-6]$/u.test(node.tagName) && node.querySelectorAll(MEDIA_SELECTOR).length > 1) {
      const media = Array.from(node.querySelectorAll<HTMLElement>(MEDIA_SELECTOR));
      media.forEach((item, index) => {
        const unit = document.createElement("div"); unit.className = "slides-fit-media-only";
        if (index === 0) {
          const heading = node.cloneNode(false) as HTMLElement;
          Array.from(node.childNodes).filter((child) => !(child instanceof HTMLElement && child.matches(MEDIA_SELECTOR))).forEach((child) => heading.append(child.cloneNode(true)));
          unit.append(heading);
        }
        unit.append(item.cloneNode(true)); units.push(unit);
      });
    }
    else if (node.tagName === "OL" || node.tagName === "UL") units.push(...splitList(node));
    else if (node.tagName === "P" && node.querySelectorAll(MEDIA_SELECTOR).length > 1) units.push(...splitParagraphAtMedia(node));
    else if (node.tagName === "PRE") units.push(...splitCode(node));
    else units.push(node.cloneNode(true) as HTMLElement);
  });
  return units;
};

export const mediaSelector = MEDIA_SELECTOR;
