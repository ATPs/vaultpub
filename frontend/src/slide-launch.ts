type NavSortMode =
  | "predefined"
  | "name-asc"
  | "name-desc"
  | "created-desc"
  | "created-asc"
  | "modified-desc"
  | "modified-asc";

interface SlideScope {
  label: string;
  url: string;
}

const SIDEBAR_STATE_KEY = "vaultpub.sidebarState";
const ORDER_OPTIONS: Array<[NavSortMode, string]> = [
  ["predefined", "Order"],
  ["name-asc", "Name A–Z"],
  ["name-desc", "Name Z–A"],
  ["created-desc", "Created newest"],
  ["created-asc", "Created oldest"],
  ["modified-desc", "Modified newest"],
  ["modified-asc", "Modified oldest"],
];

function isNavSortMode(value: unknown): value is NavSortMode {
  return ORDER_OPTIONS.some(([mode]) => mode === value);
}

function readScopes(): SlideScope[] {
  try {
    const element = document.getElementById("vaultpub-slide-scopes");
    const raw = JSON.parse(element?.textContent || "[]") as unknown;
    if (!Array.isArray(raw)) return [];
    return raw.filter(
      (scope): scope is SlideScope => Boolean(
        scope
        && typeof scope === "object"
        && typeof (scope as SlideScope).label === "string"
        && typeof (scope as SlideScope).url === "string",
      ),
    );
  } catch {
    return [];
  }
}

function initialOrder(): NavSortMode {
  try {
    const state = JSON.parse(localStorage.getItem(SIDEBAR_STATE_KEY) || "{}") as { navSort?: unknown };
    return isNavSortMode(state.navSort) ? state.navSort : "modified-desc";
  } catch {
    return "modified-desc";
  }
}

function closeSettingsMenu(): void {
  const menu = document.querySelector<HTMLElement>(".settings-menu");
  const button = menu?.querySelector<HTMLButtonElement>(".settings-menu-btn");
  menu?.classList.remove("open");
  button?.setAttribute("aria-expanded", "false");
}

function addOption(select: HTMLSelectElement, value: string, label: string): void {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  select.appendChild(option);
}

function createDialog(scopes: SlideScope[]): HTMLDialogElement {
  const dialog = document.createElement("dialog");
  dialog.className = "slide-launch-dialog";
  dialog.setAttribute("aria-labelledby", "slide-launch-title");
  dialog.innerHTML = `
    <form class="slide-launch-form">
      <header><h2 id="slide-launch-title">Start Slide View</h2><p>Choose the notes and their order for this deck.</p></header>
      <fieldset class="slide-launch-fieldset"><legend>Notes</legend>
        <label><input type="radio" name="slide-scope" value="vault" checked> Whole vault</label>
        <label><input type="radio" name="slide-scope" value="folder"> Subfolder</label>
        <select name="slide-folder" aria-label="Subfolder"></select>
      </fieldset>
      <label class="slide-launch-order">Order <select name="slide-order"></select></label>
      <footer><button type="button" data-action="cancel-slide-launch">Cancel</button><button type="submit">Start Slide View</button></footer>
    </form>`;

  const folder = dialog.querySelector<HTMLSelectElement>("[name=slide-folder]")!;
  const order = dialog.querySelector<HTMLSelectElement>("[name=slide-order]")!;
  const folderRadio = dialog.querySelector<HTMLInputElement>("[value=folder]")!;
  const vaultRadio = dialog.querySelector<HTMLInputElement>("[value=vault]")!;
  const folders = scopes.slice(1);
  folders.forEach((scope) => addOption(folder, scope.url, scope.label));
  ORDER_OPTIONS.forEach(([value, label]) => addOption(order, value, label));
  folderRadio.disabled = folders.length === 0;
  folder.disabled = true;

  const syncScope = (): void => {
    folder.disabled = !folderRadio.checked;
    if (folderRadio.checked) folder.focus();
  };
  folderRadio.addEventListener("change", syncScope);
  vaultRadio.addEventListener("change", syncScope);
  dialog.querySelector<HTMLElement>("[data-action=cancel-slide-launch]")?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.querySelector<HTMLFormElement>("form")!.addEventListener("submit", (event) => {
    event.preventDefault();
    const scope = folderRadio.checked ? folder.value : scopes[0]?.url;
    if (!scope) return;
    const url = new URL(scope, window.location.href);
    url.searchParams.set("sort", order.value);
    dialog.close();
    window.location.assign(url.toString());
  });
  return dialog;
}

export function initSlideLaunch(): void {
  const scopes = readScopes();
  if (!scopes.length) return;

  const dialog = createDialog(scopes);
  document.body.appendChild(dialog);
  let trigger: HTMLElement | null = null;
  dialog.addEventListener("close", () => trigger?.focus());
  document.addEventListener("click", (event) => {
    const target = (event.target as HTMLElement).closest<HTMLElement>("[data-action=launch-vault-slides]");
    if (!target) return;
    event.preventDefault();
    trigger = target;
    closeSettingsMenu();
    dialog.querySelector<HTMLSelectElement>("[name=slide-order]")!.value = initialOrder();
    dialog.showModal();
    dialog.querySelector<HTMLInputElement>("[value=vault]")?.focus();
  });
}
