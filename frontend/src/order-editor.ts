import { initIcons } from "./icons";

interface OrderItem {
  token: string;
  label: string;
}

interface DirectoryChoice {
  path: string;
  label: string;
}

interface OrderPayload {
  directory: string;
  revision: string;
  directories: DirectoryChoice[];
  pinned: OrderItem[];
  folders: OrderItem[];
  files: OrderItem[];
}

interface EditorState {
  payload: OrderPayload | null;
  dirty: boolean;
  dragged: HTMLLIElement | null;
}

function readPayload(value: unknown): OrderPayload | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<OrderPayload>;
  if (typeof candidate.directory !== "string" || typeof candidate.revision !== "string") return null;
  if (!Array.isArray(candidate.directories) || !Array.isArray(candidate.pinned)
    || !Array.isArray(candidate.folders) || !Array.isArray(candidate.files)) return null;
  return candidate as OrderPayload;
}

function orderItems(list: HTMLUListElement): string[] {
  return Array.from(list.querySelectorAll<HTMLLIElement>("[data-order-token]"))
    .map((item) => item.dataset.orderToken || "")
    .filter(Boolean);
}

function createRow(item: OrderItem, movable: boolean): HTMLLIElement {
  const row = document.createElement("li");
  row.className = "order-editor-row";
  row.dataset.orderToken = item.token;
  row.draggable = movable;
  row.innerHTML = movable
    ? `<span class="order-editor-drag" title="Drag to reorder"><i data-lucide="grip-vertical" aria-hidden="true"></i></span>
       <span class="order-editor-row-label"></span>
       <button type="button" class="order-editor-icon-button" data-order-move="up" title="Move up" aria-label="Move up"><i data-lucide="chevron-up" aria-hidden="true"></i></button>
       <button type="button" class="order-editor-icon-button" data-order-move="down" title="Move down" aria-label="Move down"><i data-lucide="chevron-down" aria-hidden="true"></i></button>`
    : `<span class="order-editor-pinned-icon"><i data-lucide="pin" aria-hidden="true"></i></span><span class="order-editor-row-label"></span>`;
  row.querySelector<HTMLElement>(".order-editor-row-label")!.textContent = item.label;
  return row;
}

function setStatus(editor: HTMLElement, message = "", kind = ""): void {
  const status = editor.querySelector<HTMLElement>("[data-order-status]");
  if (!status) return;
  status.textContent = message;
  status.dataset.statusKind = kind;
}

function render(editor: HTMLElement, state: EditorState): void {
  const payload = state.payload;
  if (!payload) return;
  const input = editor.querySelector<HTMLInputElement>("[data-order-directory]")!;
  const options = editor.querySelector<HTMLDataListElement>("#order-editor-folders")!;
  const path = editor.querySelector<HTMLElement>("[data-order-editor-path]")!;
  const pinned = editor.querySelector<HTMLUListElement>("[data-order-pinned]")!;
  const folders = editor.querySelector<HTMLUListElement>("[data-order-folders]")!;
  const files = editor.querySelector<HTMLUListElement>("[data-order-files]")!;
  const pinnedSection = editor.querySelector<HTMLElement>("[data-order-pinned-section]")!;

  input.value = payload.directory;
  path.textContent = payload.directory === "." ? "/" : `${payload.directory}/`;
  options.replaceChildren(...payload.directories.map((directory) => {
    const option = document.createElement("option");
    option.value = directory.path;
    option.label = directory.label;
    return option;
  }));
  pinned.replaceChildren(...payload.pinned.map((item) => createRow(item, false)));
  folders.replaceChildren(...payload.folders.map((item) => createRow(item, true)));
  files.replaceChildren(...payload.files.map((item) => createRow(item, true)));
  pinnedSection.hidden = payload.pinned.length === 0;
  state.dirty = false;
  initIcons();
}

async function load(editor: HTMLElement, state: EditorState, directory: string): Promise<void> {
  const dataUrl = editor.dataset.orderDataUrl;
  if (!dataUrl) return;
  setStatus(editor, "Loading...");
  const url = new URL(dataUrl, window.location.href);
  url.searchParams.set("directory", directory);
  try {
    const response = await fetch(url, { credentials: "same-origin" });
    const data = readPayload(await response.json());
    if (!response.ok || !data) throw new Error("Unable to load this folder");
    state.payload = data;
    render(editor, state);
    setStatus(editor);
  } catch (error) {
    setStatus(editor, error instanceof Error ? error.message : "Unable to load this folder", "error");
  }
}

function wireMovableLists(editor: HTMLElement, state: EditorState): void {
  editor.querySelectorAll<HTMLUListElement>("[data-order-folders], [data-order-files]").forEach((list) => {
    list.addEventListener("click", (event) => {
      const button = (event.target as HTMLElement).closest<HTMLButtonElement>("[data-order-move]");
      if (!button) return;
      const row = button.closest<HTMLLIElement>("[data-order-token]");
      if (!row) return;
      if (button.dataset.orderMove === "up" && row.previousElementSibling) {
        list.insertBefore(row, row.previousElementSibling);
      } else if (button.dataset.orderMove === "down" && row.nextElementSibling) {
        list.insertBefore(row.nextElementSibling, row);
      } else {
        return;
      }
      state.dirty = true;
      setStatus(editor, "Unsaved changes");
      button.focus();
    });
    list.addEventListener("dragstart", (event) => {
      const row = (event.target as HTMLElement).closest<HTMLLIElement>("[data-order-token]");
      if (!row) return;
      state.dragged = row;
      row.classList.add("is-dragging");
      event.dataTransfer?.setData("text/plain", row.dataset.orderToken || "");
      if (event.dataTransfer) event.dataTransfer.effectAllowed = "move";
    });
    list.addEventListener("dragover", (event) => {
      if (!state.dragged) return;
      event.preventDefault();
      const target = (event.target as HTMLElement).closest<HTMLLIElement>("[data-order-token]");
      if (!target || target === state.dragged || target.parentElement !== list) return;
      const after = event.clientY > target.getBoundingClientRect().top + target.offsetHeight / 2;
      list.insertBefore(state.dragged, after ? target.nextElementSibling : target);
    });
    list.addEventListener("dragend", () => {
      if (!state.dragged) return;
      state.dragged.classList.remove("is-dragging");
      state.dragged = null;
      state.dirty = true;
      setStatus(editor, "Unsaved changes");
    });
  });
}

async function submit(editor: HTMLElement, state: EditorState, action: "save" | "reset"): Promise<void> {
  const payload = state.payload;
  const saveUrl = editor.dataset.orderSaveUrl;
  if (!payload || !saveUrl) return;
  if (action === "reset" && !window.confirm("Use the default order for this folder?")) return;
  const body: Record<string, unknown> = { action, directory: payload.directory, revision: payload.revision };
  if (action === "save") {
    body.folders = orderItems(editor.querySelector<HTMLUListElement>("[data-order-folders]")!);
    body.files = orderItems(editor.querySelector<HTMLUListElement>("[data-order-files]")!);
  }
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (editor.dataset.csrfToken) headers["X-CSRFToken"] = editor.dataset.csrfToken;
  setStatus(editor, action === "save" ? "Saving..." : "Resetting...");
  try {
    const response = await fetch(saveUrl, {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify(body),
    });
    const result = await response.json() as { error?: string };
    const next = readPayload(result);
    if (!response.ok || !next) throw new Error(result.error || "Unable to save the custom order");
    state.payload = next;
    render(editor, state);
    setStatus(editor, action === "save" ? "Order saved" : "Using default order", "success");
  } catch (error) {
    setStatus(editor, error instanceof Error ? error.message : "Unable to save the custom order", "error");
  }
}

export function initOrderEditor(): void {
  const editor = document.querySelector<HTMLElement>("[data-order-editor]");
  if (!editor) return;
  const state: EditorState = { payload: null, dirty: false, dragged: null };
  const input = editor.querySelector<HTMLInputElement>("[data-order-directory]")!;
  wireMovableLists(editor, state);
  input.addEventListener("change", () => {
    const requested = input.value.trim() || ".";
    if (state.dirty && !window.confirm("Discard unsaved changes?")) {
      input.value = state.payload?.directory || ".";
      return;
    }
    void load(editor, state, requested);
  });
  editor.querySelector<HTMLButtonElement>("[data-order-save]")?.addEventListener("click", () => void submit(editor, state, "save"));
  editor.querySelector<HTMLButtonElement>("[data-order-reset]")?.addEventListener("click", () => void submit(editor, state, "reset"));
  window.addEventListener("beforeunload", (event) => {
    if (!state.dirty) return;
    event.preventDefault();
    event.returnValue = "";
  });
  void load(editor, state, editor.dataset.initialDirectory || ".");
}
