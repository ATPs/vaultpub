const CODE_WRAP_KEY = "vaultpub.codeWrap";
const ACTIVE_HEADING_OFFSET = 96;

function trackedHeadings(): HTMLElement[] {
  const markdown = document.querySelector(".markdown-body");
  if (!markdown) return [];

  const headings = Array.from(
    markdown.querySelectorAll<HTMLElement>("h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"),
  );
  if (!headings.length) return [];

  const sectionHeadings = headings.filter((heading) => heading.tagName !== "H1");
  return sectionHeadings.length ? sectionHeadings : headings;
}

function updateCurrentHeading(link: HTMLAnchorElement, headings: HTMLElement[]): void {
  if (!headings.length) {
    link.hidden = true;
    return;
  }

  let active = headings[0];
  for (const heading of headings) {
    if (heading.getBoundingClientRect().top <= ACTIVE_HEADING_OFFSET) {
      active = heading;
      continue;
    }
    break;
  }

  const text = active.textContent?.trim() || "";
  if (!text || !active.id) {
    link.hidden = true;
    return;
  }

  link.textContent = text;
  link.href = `#${active.id}`;
  link.hidden = false;
}

function initCurrentHeading(): void {
  const link = document.querySelector<HTMLAnchorElement>("[data-current-heading]");
  if (!link) return;

  const headings = trackedHeadings();
  if (!headings.length) {
    link.hidden = true;
    return;
  }

  let ticking = false;
  const sync = (): void => {
    ticking = false;
    updateCurrentHeading(link, headings);
  };

  const requestSync = (): void => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(sync);
  };

  requestSync();
  window.addEventListener("scroll", requestSync, { passive: true });
  window.addEventListener("resize", requestSync);
}

function applyCodeWrapState(enabled: boolean, button: HTMLButtonElement): void {
  document.body.classList.toggle("code-wrap-enabled", enabled);
  button.classList.toggle("is-active", enabled);
  button.setAttribute("aria-pressed", String(enabled));
}

async function copyText(text: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to the DOM fallback below.
    }
  }

  const input = document.createElement("textarea");
  input.value = text;
  input.setAttribute("readonly", "true");
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch {
    copied = false;
  }

  input.remove();
  return copied;
}

function flashButtonLabel(button: HTMLButtonElement, label: string): void {
  const original = button.dataset.labelDefault || button.textContent || "";
  button.dataset.labelDefault = original;
  button.textContent = label;
  window.setTimeout(() => {
    button.textContent = original;
  }, 1200);
}

function initCodeTools(): void {
  const copyButton = document.querySelector<HTMLButtonElement>("[data-code-action='copy-path']");
  const wrapButton = document.querySelector<HTMLButtonElement>("[data-code-action='toggle-wrap']");

  if (wrapButton) {
    const enabled = localStorage.getItem(CODE_WRAP_KEY) === "true";
    applyCodeWrapState(enabled, wrapButton);
    wrapButton.addEventListener("click", () => {
      const nextEnabled = !document.body.classList.contains("code-wrap-enabled");
      localStorage.setItem(CODE_WRAP_KEY, String(nextEnabled));
      applyCodeWrapState(nextEnabled, wrapButton);
    });
  }

  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      const path = copyButton.dataset.codePath || "";
      if (!path) return;
      const copied = await copyText(path);
      flashButtonLabel(copyButton, copied ? "Copied" : "Failed");
    });
  }
}

export function initTopbarContext(): void {
  const context = document.querySelector<HTMLElement>(".topbar-context");
  if (!context) return;

  const kind = context.dataset.topbarContext;
  if (kind === "note") {
    initCurrentHeading();
    return;
  }
  if (kind === "code") {
    initCodeTools();
  }
}
