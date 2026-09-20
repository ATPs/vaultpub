const TASK_STATE_KEY_PREFIX = "vaultpub.taskLists.v1:";
const TASK_SELECTOR = "input.task-list-item-checkbox";

type TaskState = Record<string, boolean>;

function storageKey(): string {
  return `${TASK_STATE_KEY_PREFIX}${location.pathname}`;
}

function readTaskState(): TaskState {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(storageKey()) || "{}");
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return Object.fromEntries(Object.entries(value).filter(([, checked]) => typeof checked === "boolean")) as TaskState;
  } catch {
    return {};
  }
}

function writeTaskState(state: TaskState): void {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(state));
  } catch {
    // Storage can be disabled; the checkbox remains usable for this page visit.
  }
}

function taskId(checkbox: HTMLInputElement, index: number): string {
  const text = checkbox.closest("li")?.textContent?.trim() || "";
  return `${index}:${text}`;
}

function taskCheckboxes(): HTMLInputElement[] {
  return Array.from(document.querySelectorAll<HTMLInputElement>(TASK_SELECTOR));
}

export function initTaskLists(): void {
  const state = readTaskState();

  const restore = (): void => {
    taskCheckboxes().forEach((checkbox, index) => {
      checkbox.disabled = false;
      const saved = state[taskId(checkbox, index)];
      if (typeof saved === "boolean") checkbox.checked = saved;
    });
  };

  restore();

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || !target.matches(TASK_SELECTOR)) return;
    const index = taskCheckboxes().indexOf(target);
    if (index < 0) return;
    state[taskId(target, index)] = target.checked;
    writeTaskState(state);
  });

  const observer = new MutationObserver((records) => {
    if (records.some((record) => Array.from(record.addedNodes).some(
      (node) => node instanceof Element && (node.matches(TASK_SELECTOR) || node.querySelector(TASK_SELECTOR)),
    ))) restore();
  });
  observer.observe(document.body, { childList: true, subtree: true });
}
