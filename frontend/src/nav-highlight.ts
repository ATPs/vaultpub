/**
 * Left nav: highlight the current page link and expand parent folders.
 * Right nav (TOC): scroll-spy to highlight the current section heading.
 */

function initNavHighlight(): void {
  const article = document.querySelector<HTMLElement>(".note");
  if (!article) return;
  const currentPath = article.dataset.notePath;
  if (!currentPath) return;

  const fileTree = document.querySelector<HTMLElement>(".file-tree");
  if (!fileTree) return;

  const links = fileTree.querySelectorAll<HTMLAnchorElement>("a");
  for (const link of links) {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");

      // Expand all ancestor <details> so the active link is visible
      let parent = link.parentElement;
      while (parent && parent !== fileTree) {
        if (parent.tagName === "DETAILS") {
          (parent as HTMLDetailsElement).open = true;
        }
        parent = parent.parentElement;
      }

      requestAnimationFrame(() => {
        link.scrollIntoView({ block: "nearest" });
      });
      return;
    }
  }
}

function initScrollSpy(): void {
  const article = document.querySelector<HTMLElement>(".note");
  if (!article) return;
  const toc = document.querySelector<HTMLElement>(".toc");
  if (!toc) return;

  const headingEls = article.querySelectorAll<HTMLHeadingElement>(
    "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]",
  );
  if (headingEls.length === 0) return;

  const tocLinks = toc.querySelectorAll<HTMLAnchorElement>("a[href^='#']");
  const linkMap = new Map<string, HTMLAnchorElement>();
  for (const link of tocLinks) {
    const id = link.getAttribute("href")?.slice(1);
    if (id) linkMap.set(id, link);
  }

  let activeLink: HTMLAnchorElement | null = null;

  function update(): void {
    const viewTop = 100;
    let currentId: string | null = null;

    for (const h of headingEls) {
      if (h.getBoundingClientRect().top <= viewTop) {
        currentId = h.id;
      } else {
        break;
      }
    }

    if (!currentId) return;

    const link = linkMap.get(currentId);
    if (!link || link === activeLink) return;

    if (activeLink) activeLink.classList.remove("active");
    link.classList.add("active");
    activeLink = link;

    // Keep the active TOC link visible
    requestAnimationFrame(() => {
      link.scrollIntoView({ block: "nearest" });
    });
  }

  let ticking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          update();
          ticking = false;
        });
        ticking = true;
      }
    },
    { passive: true },
  );

  // Initial run
  update();
}

export function initNavHighlightAll(): void {
  initNavHighlight();
  initScrollSpy();
}
