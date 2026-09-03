import Reveal from "reveal.js";
import "reveal.js/reveal.css";
import "./styles/slides.css";
import { READING_THEME_IDS, READING_THEMES } from "./theme-data";
import { initCalloutFold } from "./stacked-pages";
import { initMath } from "./math-init";
import { initMermaid } from "./mermaid-init";
import { initIcons } from "./icons";

type RevealConfig = Record<string, boolean | number | string>;
type SplitPolicy = "auto" | "chapters" | "sections" | "detail" | "fit" | "explicit" | "single";
type Aspect = "fit" | "21:9" | "16:10" | "16:9" | "3:2" | "4:3" | "1:1" | "custom";
type Tool = "laser" | "magnify" | "pen" | null;
type Panel = "settings" | "tools" | "magnifier" | "picker" | "timer" | "help" | "grid" | null;
type MagnifierMode = "lens" | "full";
type TimerMode = "countdown" | "countup";

interface SlideSettings extends RevealConfig { theme: string; codeWrap: boolean; split: SplitPolicy; }
interface StoredPreferences { theme?: string; transition?: string; codeWrap?: boolean; textScale?: number; aspect?: Aspect; customRatio?: string; center?: boolean; progress?: boolean; slideNumber?: boolean; reducedMotion?: boolean; magnifierMode?: MagnifierMode; magnifierZoom?: number; magnifierLensSize?: number; }
interface TimerPreferences { mode: TimerMode; durationMinutes: number; warningMinutes: number; urgentMinutes: number; }
interface TimerSession { mode: TimerMode; durationMs: number; elapsedMs: number; startedAt: number | null; popupVisible: boolean; }
interface Point { x: number; y: number; }
interface Stroke { color: string; width: number; points: Point[]; }
interface SlideFragment { index: number; title: string; }
interface SlideManifestNote { id: string; title: string; sourcePath: string; fingerprint?: string; payloadUrl: string; fragments: SlideFragment[]; }
interface SlidePayload { noteId: string; sourcePath: string; fingerprint?: string; slides: Array<SlideFragment & { html: string }>; }

const SLIDE_EMBED_PROTOCOL = "vaultpub.slide";
const SLIDE_EMBED_VERSION = 1;

function embedRequestId(value: unknown): string | undefined {
  return typeof value === "string" && value.length <= 160 ? value : undefined;
}

const SETTINGS_KEY = "vaultpub.slideSettings.v2";
const LEGACY_SETTINGS_KEY = "vaultpub.slideSettings.v1";
const TIMER_SETTINGS_KEY = "vaultpub.presentationTimer.v1";
const TIMER_SESSION_PREFIX = "vaultpub.presentationTimerSession.v1:";
const SPLIT_COOKIE = "vaultpub_slide_split";
const SPLIT_OPTIONS: Array<[SplitPolicy, string]> = [["auto", "Auto"], ["chapters", "Chapters"], ["sections", "Sections"], ["detail", "Detail"], ["fit", "Fit viewport"], ["explicit", "Explicit"], ["single", "Single"]];
const SPLIT_DESCRIPTIONS: Record<SplitPolicy, string> = {
  auto: "Use dividers first, then level 2 sections, otherwise one slide.",
  chapters: "Start a slide at each level 1 heading.",
  sections: "Start a slide at each level 2 heading.",
  detail: "Start slides at level 2 and level 3 headings.",
  fit: "Paginate content to fit the current viewport.",
  explicit: "Split only at standalone --- dividers.",
  single: "Keep the note as one scrollable slide.",
};
const ASPECT_OPTIONS: Array<[Aspect, string]> = [["fit", "Fit available space"], ["21:9", "21:9"], ["16:10", "16:10"], ["16:9", "16:9"], ["3:2", "3:2"], ["4:3", "4:3"], ["1:1", "1:1"], ["custom", "Custom"]];
const TRANSITIONS = ["none", "fade", "slide", "convex", "concave", "zoom"];
const DEFAULT_TIMER: TimerPreferences = { mode: "countdown", durationMinutes: 20, warningMinutes: 5, urgentMinutes: 1 };

function readJson<T>(id: string, fallback: T): T { try { return JSON.parse(document.getElementById(id)?.textContent || "") as T; } catch { return fallback; } }
function text(value: string | null | undefined): string { return value?.trim() || "Untitled slide"; }
function ratio(value: string): number | null { const parts = value.trim().split(":"); const number = parts.length === 2 ? Number(parts[0]) / Number(parts[1]) : Number(value); return Number.isFinite(number) && number > 0.1 && number < 10 ? number : null; }
function options(values: Array<[string, string]>, selected: string): string { return values.map(([value, label]) => `<option value="${value}"${value === selected ? " selected" : ""}>${label}</option>`).join(""); }
function swatches(colors: string[]): string { return colors.map((color) => `<span style="background:${color}"></span>`).join(""); }

function readStored(): StoredPreferences {
  try {
    const raw = JSON.parse(localStorage.getItem(SETTINGS_KEY) || localStorage.getItem(LEGACY_SETTINGS_KEY) || "{}") as Record<string, unknown>;
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
    return {
      theme: typeof raw.theme === "string" && READING_THEME_IDS.has(raw.theme) ? raw.theme : undefined,
      transition: typeof raw.transition === "string" && TRANSITIONS.includes(raw.transition) ? raw.transition : undefined,
      codeWrap: typeof raw.codeWrap === "boolean" ? raw.codeWrap : undefined,
      textScale: typeof raw.textScale === "number" && raw.textScale >= 75 && raw.textScale <= 300 && raw.textScale % 5 === 0 ? raw.textScale : undefined,
      aspect: typeof raw.aspect === "string" && ASPECT_OPTIONS.some(([id]) => id === raw.aspect) ? raw.aspect as Aspect : undefined,
      customRatio: typeof raw.customRatio === "string" && ratio(raw.customRatio) ? raw.customRatio : undefined,
      center: typeof raw.center === "boolean" ? raw.center : undefined,
      progress: typeof raw.progress === "boolean" ? raw.progress : undefined,
      slideNumber: typeof raw.slideNumber === "boolean" ? raw.slideNumber : undefined,
      reducedMotion: typeof raw.reducedMotion === "boolean" ? raw.reducedMotion : undefined,
      magnifierMode: raw.magnifierMode === "lens" || raw.magnifierMode === "full" ? raw.magnifierMode : undefined,
      magnifierZoom: typeof raw.magnifierZoom === "number" && raw.magnifierZoom >= 1.25 && raw.magnifierZoom <= 4 ? raw.magnifierZoom : undefined,
      magnifierLensSize: typeof raw.magnifierLensSize === "number" && raw.magnifierLensSize >= 240 && raw.magnifierLensSize <= 560 ? raw.magnifierLensSize : undefined,
    };
  } catch { return {}; }
}
function saveStored(preferences: StoredPreferences): void { try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(preferences)); } catch { /* storage is optional */ } }
function setSplitCookie(value: SplitPolicy | null): void { document.cookie = value ? `${SPLIT_COOKIE}=${encodeURIComponent(value)}; max-age=31536000; path=/; SameSite=Lax` : `${SPLIT_COOKIE}=; max-age=0; path=/; SameSite=Lax`; }
function readTimerPreferences(): TimerPreferences {
  try {
    const raw = JSON.parse(localStorage.getItem(TIMER_SETTINGS_KEY) || "{}") as Partial<TimerPreferences>;
    return {
      mode: raw.mode === "countup" ? "countup" : "countdown",
      durationMinutes: typeof raw.durationMinutes === "number" && raw.durationMinutes >= 1 && raw.durationMinutes <= 1440 ? raw.durationMinutes : DEFAULT_TIMER.durationMinutes,
      warningMinutes: typeof raw.warningMinutes === "number" && raw.warningMinutes >= 0 && raw.warningMinutes <= 1440 ? raw.warningMinutes : DEFAULT_TIMER.warningMinutes,
      urgentMinutes: typeof raw.urgentMinutes === "number" && raw.urgentMinutes >= 0 && raw.urgentMinutes <= 1440 ? raw.urgentMinutes : DEFAULT_TIMER.urgentMinutes,
    };
  } catch { return { ...DEFAULT_TIMER }; }
}
function saveTimerPreferences(preferences: TimerPreferences): void { try { localStorage.setItem(TIMER_SETTINGS_KEY, JSON.stringify(preferences)); } catch { /* storage is optional */ } }

function readManifest(): SlideManifestNote[] {
  const manifest = readJson<unknown>("vaultpub-slide-manifest", []);
  if (!Array.isArray(manifest)) return [];
  return manifest.filter((note): note is SlideManifestNote => Boolean(
    note && typeof note === "object" && typeof (note as SlideManifestNote).id === "string"
      && typeof (note as SlideManifestNote).title === "string"
      && typeof (note as SlideManifestNote).sourcePath === "string"
      && typeof (note as SlideManifestNote).payloadUrl === "string"
      && Array.isArray((note as SlideManifestNote).fragments),
  ));
}

function initialMultiNoteLocation(manifest: SlideManifestNote[]): { note: number; slide: number } {
  const match = /^#\/?(\d+)(?:\/(\d+))?$/.exec(location.hash);
  if (!match) return { note: 0, slide: 0 };
  const first = Number(match[1]);
  if (match[2] !== undefined) return { note: Math.min(first, Math.max(0, manifest.length - 1)), slide: Number(match[2]) };
  let remaining = first;
  for (let note = 0; note < manifest.length; note += 1) {
    const count = manifest[note].fragments.length + 1;
    if (remaining < count) return { note, slide: remaining };
    remaining -= count;
  }
  return { note: Math.max(0, manifest.length - 1), slide: 0 };
}

function buildInterface(defaults: SlideSettings, preferences: StoredPreferences): HTMLElement {
  const selectedTheme = preferences.theme || defaults.theme;
  const selectedTransition = preferences.transition || String(defaults.transition || "slide");
  const selectedAspect = preferences.aspect || "fit";
  const magnifierMode = preferences.magnifierMode || "lens";
  const magnifierZoom = preferences.magnifierZoom || 2;
  const magnifierLensSize = preferences.magnifierLensSize || 360;
  const timer = readTimerPreferences();
  const themeCards = READING_THEMES.map((theme) => `<button type="button" class="slides-theme-choice${theme.id === selectedTheme ? " is-selected" : ""}" data-theme="${theme.id}" aria-label="${theme.name}" aria-pressed="${theme.id === selectedTheme}"><span class="slides-theme-swatch">${swatches(theme.preview)}</span><span>${theme.name}</span></button>`).join("");
  const splitChoices = SPLIT_OPTIONS.map(([value, label]) => `<button type="button" class="slides-choice${value === defaults.split ? " is-selected" : ""}" data-split="${value}" data-tooltip="${SPLIT_DESCRIPTIONS[value as SplitPolicy]}" aria-label="${label}: ${SPLIT_DESCRIPTIONS[value as SplitPolicy]}" aria-pressed="${value === defaults.split}">${label}</button>`).join("");
  const root = document.createElement("div");
  root.className = "slides-ui";
  root.innerHTML = `
    <div class="slides-toast" role="status" aria-live="polite"></div><canvas class="slides-ink" aria-label="Drawing canvas"></canvas><div class="slides-laser" aria-hidden="true"></div><div class="slides-magnifier-lens" hidden aria-hidden="true"><div class="slides-magnifier-mirror"></div></div><div class="slides-edge-scrollbar" role="scrollbar" aria-label="Slide scroll position" aria-orientation="vertical" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0" tabindex="0" hidden><span class="slides-edge-scrollbar-thumb"></span></div>
    <nav class="slides-dock" aria-label="Presentation controls">
      <a class="slides-ui-button" data-return-control><i data-lucide="arrow-left" aria-hidden="true"></i></a>
      <button class="slides-ui-button" type="button" data-action="previous" data-tooltip="Previous slide" aria-label="Previous slide"><i data-lucide="chevron-left" aria-hidden="true"></i></button>
      <button class="slides-ui-button slides-counter" type="button" data-action="picker" data-tooltip="Jump to a slide" aria-label="Jump to a slide">0 / 0</button>
      <button class="slides-ui-button" type="button" data-action="next" data-tooltip="Next slide" aria-label="Next slide"><i data-lucide="chevron-right" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-action="overview" data-tooltip="Slide grid" aria-label="Slide grid"><i data-lucide="layout-grid" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-action="settings" data-tooltip="Slide settings" aria-label="Slide settings" aria-expanded="false"><i data-lucide="settings-2" aria-hidden="true"></i></button>
      <span class="slides-dock-divider" aria-hidden="true"></span>
      <button class="slides-ui-button" type="button" data-action="fullscreen" data-tooltip="Fullscreen" aria-label="Fullscreen"><i data-lucide="maximize" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-tool="laser" data-tooltip="Laser pointer" aria-label="Laser pointer" aria-pressed="false"><i data-lucide="circle-dot" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-tool="magnify" data-tooltip="Magnify" aria-label="Magnify" aria-pressed="false"><i data-lucide="zoom-in" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-tool="pen" data-tooltip="Draw" aria-label="Draw" aria-pressed="false"><i data-lucide="pen-line" aria-hidden="true"></i></button>
      <button class="slides-ui-button slides-timer-display" type="button" data-action="timer" data-tooltip="Presentation timer" aria-label="Presentation timer">00:00</button>
      <button class="slides-ui-button" type="button" data-action="blackout" data-tooltip="Blackout" aria-label="Blackout"><i data-lucide="monitor-off" aria-hidden="true"></i></button>
      <button class="slides-ui-button" type="button" data-action="help" data-tooltip="Keyboard shortcuts" aria-label="Keyboard shortcuts"><i data-lucide="circle-help" aria-hidden="true"></i></button>
    </nav>
    <section class="slides-panel slides-settings-panel" hidden aria-label="Slide settings" tabindex="-1"><header><strong>Slide settings</strong><button type="button" data-action="close" data-tooltip="Close settings" aria-label="Close settings"><i data-lucide="x" aria-hidden="true"></i></button></header><div class="slides-settings-grid">
      <div class="slides-settings-group slides-theme-group"><span class="slides-settings-heading">Theme</span><div class="slides-theme-cards">${themeCards}</div></div>
      <div class="slides-settings-group slides-display-group"><label>Transition<select data-setting="transition">${options(TRANSITIONS.map((item) => [item, item] as [string, string]), selectedTransition)}</select></label><label>Aspect ratio<select data-setting="aspect">${options(ASPECT_OPTIONS, selectedAspect)}</select></label><label class="slides-custom-ratio" ${selectedAspect === "custom" ? "" : "hidden"}>Custom ratio<input data-setting="customRatio" value="${preferences.customRatio || ""}" placeholder="1920:1080"></label><label>Text size<span class="slides-range"><input data-setting="textScale" type="range" min="75" max="300" step="5" value="${preferences.textScale || 100}"><output data-output="textScale">${preferences.textScale || 100}%</output></span></label></div>
      <div class="slides-settings-group slides-split-group"><span class="slides-settings-heading">Split slides</span><div class="slides-split-choices">${splitChoices}</div></div>
      <div class="slides-settings-group slides-switches"><label><input data-setting="codeWrap" type="checkbox"> Wrap code</label><label><input data-setting="center" type="checkbox"> Vertically center</label><label><input data-setting="progress" type="checkbox"> Progress bar</label><label><input data-setting="slideNumber" type="checkbox"> Slide number</label><label><input data-setting="reducedMotion" type="checkbox"> Reduce motion</label><button type="button" data-action="reset">Reset defaults</button></div>
    </div></section>
    <section class="slides-panel slides-tools-panel" hidden aria-label="Drawing tools" tabindex="-1"><header><strong>Draw</strong><button type="button" data-action="close" aria-label="Close drawing tools">×</button></header><div class="slides-ink-colors">${["#ef4444", "#facc15", "#3b82f6", "#111827"].map((color, index) => `<button type="button" data-ink-color="${color}" class="${index === 0 ? "is-selected" : ""}" style="--ink-color:${color}" aria-label="Select ink colour"></button>`).join("")}</div><label>Width <span class="slides-range"><input data-setting="inkWidth" type="range" min="2" max="16" value="4"></span></label><div class="slides-panel-row"><button data-action="eraser">Eraser</button><button data-action="undo">Undo</button><button data-action="redo">Redo</button><button data-action="clear">Clear</button></div></section>
    <section class="slides-panel slides-magnifier-panel" hidden aria-label="Magnifier controls" tabindex="-1"><header><strong>Magnify</strong><button type="button" data-action="close" aria-label="Close magnifier controls">×</button></header><div class="slides-segmented"><button type="button" data-magnifier-mode="lens" class="${magnifierMode === "lens" ? "is-selected" : ""}" aria-pressed="${magnifierMode === "lens"}">Lens</button><button type="button" data-magnifier-mode="full" class="${magnifierMode === "full" ? "is-selected" : ""}" aria-pressed="${magnifierMode === "full"}">Full slide</button></div><label>Zoom <span class="slides-range"><input data-magnifier-setting="zoom" type="range" min="1.25" max="4" step=".25" value="${magnifierZoom}"><output data-output="magnifierZoom">${magnifierZoom.toFixed(2)}×</output></span></label><label>Lens size <span class="slides-range"><input data-magnifier-setting="lensSize" type="range" min="240" max="560" step="20" value="${magnifierLensSize}"><output data-output="magnifierLensSize">${magnifierLensSize}px</output></span></label><button type="button" data-action="magnifier-reset">Reset magnifier</button></section>
    <section class="slides-panel slides-picker-panel" hidden aria-label="Slide chooser" tabindex="-1"><header><strong>Jump to slide</strong><button data-action="close" aria-label="Close slide chooser">×</button></header><input data-action="search" type="search" placeholder="Search slide titles"><div class="slides-picker-list" role="listbox"></div></section>
    <section class="slides-panel slides-timer-panel" hidden aria-label="Presentation timer" tabindex="-1"><header><strong>Timer</strong><button data-action="close" aria-label="Close timer">×</button></header><div class="slides-segmented"><button type="button" data-timer-mode="countdown" class="${timer.mode === "countdown" ? "is-selected" : ""}" aria-pressed="${timer.mode === "countdown"}">Countdown</button><button type="button" data-timer-mode="countup" class="${timer.mode === "countup" ? "is-selected" : ""}" aria-pressed="${timer.mode === "countup"}">Count up</button></div><label>Duration<select data-timer-preset>${[5, 10, 15, 20, 30, 45, 60].map((minutes) => `<option value="${minutes}"${timer.durationMinutes === minutes ? " selected" : ""}>${minutes} minutes</option>`).join("")}<option value="custom"${[5, 10, 15, 20, 30, 45, 60].includes(timer.durationMinutes) ? "" : " selected"}>Custom</option></select></label><div class="slides-timer-custom"${[5, 10, 15, 20, 30, 45, 60].includes(timer.durationMinutes) ? " hidden" : ""}><label>Hours<input data-timer-hours type="number" min="0" max="23" value="${Math.floor(timer.durationMinutes / 60)}"></label><label>Minutes<input data-timer-minutes type="number" min="0" max="59" value="${timer.durationMinutes % 60}"></label></div><div class="slides-timer-alerts"><label>Amber at <input data-timer-warning type="number" min="0" max="1440" value="${timer.warningMinutes}"> min</label><label>Red at <input data-timer-urgent type="number" min="0" max="1440" value="${timer.urgentMinutes}"> min</label></div><div class="slides-clock"></div><div class="slides-panel-row"><button data-action="timer-start">Start</button><button data-action="timer-pause">Pause</button><button data-action="timer-reset">Reset</button></div><div class="slides-panel-row"><button data-action="timer-show-popup">Show timer</button><button data-action="timer-hide-popup">Hide timer</button></div></section>
    <output class="slides-timer-popup" hidden aria-label="Presentation timer">20:00</output>
    <section class="slides-panel slides-help-panel" hidden aria-label="Keyboard shortcuts" tabindex="-1"><header><strong>Keyboard shortcuts</strong><button data-action="close" aria-label="Close keyboard shortcuts">×</button></header><p>Arrows/Space navigate. G chooser. F fullscreen. L laser. Z magnify. +/− magnify. T timer. D draw. B blackout. Esc closes a panel or tool.</p></section>
    <section class="slides-grid" hidden aria-label="Slide grid" tabindex="-1"><header><strong>Slide grid</strong><button data-action="close" aria-label="Close slide grid">×</button></header><div class="slides-grid-list"></div></section>`;
  const returnControl = root.querySelector<HTMLAnchorElement>("[data-return-control]")!;
  returnControl.href = document.body.dataset.returnUrl || "/";
  returnControl.dataset.tooltip = document.body.dataset.returnLabel || "Return";
  returnControl.setAttribute("aria-label", document.body.dataset.returnLabel || "Return");
  for (const setting of ["codeWrap", "center", "progress", "slideNumber", "reducedMotion"] as const) root.querySelector<HTMLInputElement>(`[data-setting="${setting}"]`)!.checked = preferences[setting] ?? (setting === "reducedMotion" ? matchMedia("(prefers-reduced-motion: reduce)").matches : Boolean(defaults[setting]));
  return root;
}

document.addEventListener("DOMContentLoaded", () => {
  const revealElement = document.querySelector<HTMLElement>(".reveal");
  if (!revealElement) return;
  const defaults = readJson<SlideSettings>("vaultpub-slide-settings", { theme: "light", codeWrap: true, split: "auto" });
  const manifest = readManifest();
  const multiNote = document.body.dataset.vaultpubMultiNote === "true" && manifest.length > 0;
  const singlePage = document.body.dataset.slideLayout === "single" && !multiNote;
  const embedMode = document.body.dataset.vaultpubEmbed === "true" && window.parent !== window;
  if (multiNote && new URLSearchParams(location.search).has("print-pdf")) {
    document.body.classList.add("slides-print-disabled");
    return;
  }
  const deck = new Reveal(revealElement, {
    ...readJson<RevealConfig>("vaultpub-slides-config", {}),
    controls: false,
    ...(multiNote ? { navigationMode: "linear" } : {}),
    ...(singlePage ? { margin: 0, width: innerWidth, height: innerHeight, slideNumber: false } : {}),
  }) as any;
  let embedReady = false;
  let handshakeReceived = false;
  let handshakeRequestId: string | undefined;
  let pendingCommandRequestId: string | undefined;
  const currentEmbedSlide = (): { noteId: string; sourcePath: string; index: number; title: string; deckFingerprint: string } => {
    const current = deck.getCurrentSlide() as HTMLElement | null;
    return {
      noteId: current?.dataset.sourceNote || document.body.dataset.vaultpubNoteId || "",
      sourcePath: current?.dataset.sourcePath || document.body.dataset.vaultpubSourcePath || "",
      index: Number(deck.getIndices().h || 0),
      title: text(current?.querySelector("h1,h2,h3")?.textContent),
      deckFingerprint: document.body.dataset.vaultpubDeckFingerprint || "",
    };
  };
  const postEmbed = (message: Record<string, unknown>): void => {
    if (!embedMode) return;
    try { window.parent.postMessage({ protocol: SLIDE_EMBED_PROTOCOL, version: SLIDE_EMBED_VERSION, ...message }, location.origin); } catch { /* parent may have gone away */ }
  };
  const sendEmbedReady = (requestId?: string): void => {
    const slide = currentEmbedSlide();
    postEmbed({
      type: "ready",
      ...(requestId ? { requestId } : {}),
      deck: {
        noteId: slide.noteId,
        sourcePath: slide.sourcePath,
        title: document.body.dataset.vaultpubDeckTitle || document.title,
        slideCount: deck.getSlides().length,
        fingerprint: slide.deckFingerprint,
      },
      slide,
    });
  };
  const sendEmbedError = (code: string, message: string, requestId?: string): void => {
    postEmbed({ type: "error", code, message, ...(requestId ? { requestId } : {}) });
  };
  const sendEmbedSlideChanged = (requestId?: string): void => {
    postEmbed({ type: "slide-changed", ...currentEmbedSlide(), ...(requestId ? { requestId } : {}) });
  };
  const onEmbedMessage = (event: MessageEvent<unknown>): void => {
    if (!embedMode || event.origin !== location.origin || event.source !== window.parent) return;
    if (!event.data || typeof event.data !== "object" || Array.isArray(event.data)) return;
    const message = event.data as Record<string, unknown>;
    if (message.protocol !== SLIDE_EMBED_PROTOCOL || message.version !== SLIDE_EMBED_VERSION) return;
    const requestId = embedRequestId(message.requestId);
    if (message.type === "handshake") {
      handshakeReceived = true;
      handshakeRequestId = requestId;
      if (embedReady) sendEmbedReady(requestId);
      return;
    }
    const command = message.type === "command" ? message.command : message.type;
    if (command !== "previous" && command !== "next" && command !== "go_to") return;
    if (!embedReady) { sendEmbedError("not_ready", "Slide View is still loading", requestId); return; }
    const before = Number(deck.getIndices().h || 0);
    if (command === "go_to") {
      const index = message.index;
      if (typeof index !== "number" || !Number.isInteger(index) || index < 0 || index >= deck.getSlides().length) {
        sendEmbedError("invalid_index", "Slide index is outside this deck", requestId);
        return;
      }
      pendingCommandRequestId = requestId;
      deck.slide(index);
    } else {
      pendingCommandRequestId = requestId;
      if (command === "previous") deck.prev(); else deck.next();
    }
    if (Number(deck.getIndices().h || 0) === before) {
      pendingCommandRequestId = undefined;
      sendEmbedSlideChanged(requestId);
    }
  };
  if (embedMode) window.addEventListener("message", onEmbedMessage);
  void deck.initialize().then(() => {
    const noteSlots = Array.from(revealElement.querySelectorAll<HTMLElement>(".vaultpub-note-slot"));
    const payloads = new Map<number, SlidePayload>();
    const loading = new Map<number, Promise<SlidePayload>>();
    const originalSlidesByNote = new Map<number, HTMLElement[]>();
    let windowCenter = 0;
    const noteIndex = (): number => Math.max(0, Number(deck.getIndices().h || 0));
    const noteSlot = (index: number): HTMLElement | null => noteSlots[index] || null;
    const activeSlot = (): HTMLElement | null => multiNote ? noteSlot(noteIndex()) : null;
    const enrich = (root: ParentNode): void => {
      initCalloutFold(root); initMermaid(root); initMath(root);
      void import("./code-highlight?slides").then((module) => (module as unknown as typeof import("./code-highlight")).initCodeHighlight(root));
    };
    const createSlide = (note: SlideManifestNote, slide: SlidePayload["slides"][number]): HTMLElement => {
      const section = document.createElement("section");
      section.className = "vaultpub-slide";
      section.dataset.sourceNote = note.id;
      section.dataset.sourcePath = note.sourcePath;
      section.dataset.slideIndex = String(slide.index);
      section.innerHTML = `<div class="markdown-body vaultpub-slide-content">${slide.html}</div>`;
      return section;
    };
    const loadNote = (index: number): Promise<SlidePayload> => {
      const cached = payloads.get(index);
      if (cached) return Promise.resolve(cached);
      const pending = loading.get(index);
      if (pending) return pending;
      const note = manifest[index];
      if (!note) return Promise.reject(new Error("Slide note is unavailable"));
      const url = new URL(note.payloadUrl, location.href);
      const split = new URL(location.href).searchParams.get("split");
      if (split) url.searchParams.set("split", split);
      const request = fetch(url, { credentials: "same-origin" }).then(async (response) => {
        if (!response.ok) throw new Error("Slide note could not be loaded");
        const payload = await response.json() as SlidePayload;
        if (payload.noteId !== note.id || payload.sourcePath !== note.sourcePath || (note.fingerprint && payload.fingerprint !== note.fingerprint) || !Array.isArray(payload.slides)) throw new Error("Slide note response did not match the deck");
        payloads.set(index, payload);
        return payload;
      }).finally(() => loading.delete(index));
      loading.set(index, request);
      return request;
    };
    const hydrateNote = async (index: number): Promise<void> => {
      if (!multiNote) return;
      const slot = noteSlot(index);
      const note = manifest[index];
      if (!slot || !note || slot.dataset.vaultpubHydrated === "true") return;
      const payload = await loadNote(index);
      if (!slot.isConnected) return;
      slot.replaceChildren(slot.firstElementChild!);
      payload.slides.forEach((slide) => slot.appendChild(createSlide(note, slide)));
      slot.dataset.vaultpubHydrated = "true";
      originalSlidesByNote.set(index, Array.from(slot.children).map((slide) => slide.cloneNode(true) as HTMLElement));
      deck.sync();
    };
    const deactivateMedia = (slot: HTMLElement): void => {
      slot.querySelectorAll<HTMLElement>("img[src],audio[src],video[src],iframe[src]").forEach((media) => {
        if (media instanceof HTMLMediaElement) { media.pause(); media.removeAttribute("src"); media.load(); }
        else media.removeAttribute("src");
      });
    };
    const activateMedia = (index: number): void => noteSlots.forEach((slot, slotIndex) => {
      if (slotIndex !== index) { deactivateMedia(slot); return; }
      slot.querySelectorAll<HTMLElement>("[data-vaultpub-src]").forEach((media) => media.setAttribute("src", media.dataset.vaultpubSrc || ""));
    });
    const dehydrateNote = (index: number): void => {
      const slot = noteSlot(index);
      if (!slot || slot.dataset.vaultpubHydrated !== "true") return;
      deactivateMedia(slot);
      slot.replaceChildren(slot.firstElementChild!);
      slot.removeAttribute("data-vaultpub-hydrated");
      originalSlidesByNote.delete(index);
      payloads.delete(index);
    };
    const hydrateWindow = async (index: number): Promise<void> => {
      if (!multiNote) return;
      windowCenter = index;
      const wanted = new Set([index - 1, index, index + 1].filter((value) => value >= 0 && value < manifest.length));
      noteSlots.forEach((_slot, slotIndex) => { if (!wanted.has(slotIndex)) dehydrateNote(slotIndex); });
      await Promise.all(Array.from(wanted, (value) => hydrateNote(value)));
      const active = windowCenter;
      const activeWindow = new Set([active - 1, active, active + 1].filter((value) => value >= 0 && value < manifest.length));
      noteSlots.forEach((_slot, slotIndex) => { if (!activeWindow.has(slotIndex)) dehydrateNote(slotIndex); });
      activateMedia(active);
      const slot = noteSlot(active); if (slot) enrich(slot);
    };
    if (!multiNote) enrich(revealElement);
    const ui = buildInterface(defaults, readStored()); document.body.appendChild(ui); initIcons();
    const dock = ui.querySelector<HTMLElement>(".slides-dock")!;
    const panels = new Map<Exclude<Panel, null>, HTMLElement>([["settings", ui.querySelector(".slides-settings-panel")!], ["tools", ui.querySelector(".slides-tools-panel")!], ["magnifier", ui.querySelector(".slides-magnifier-panel")!], ["picker", ui.querySelector(".slides-picker-panel")!], ["timer", ui.querySelector(".slides-timer-panel")!], ["help", ui.querySelector(".slides-help-panel")!], ["grid", ui.querySelector(".slides-grid")!]]);
    const canvas = ui.querySelector<HTMLCanvasElement>(".slides-ink")!; const context = canvas.getContext("2d")!; const laser = ui.querySelector<HTMLElement>(".slides-laser")!; const lens = ui.querySelector<HTMLElement>(".slides-magnifier-lens")!; const lensMirror = ui.querySelector<HTMLElement>(".slides-magnifier-mirror")!; const toast = ui.querySelector<HTMLElement>(".slides-toast")!; const counter = ui.querySelector<HTMLElement>(".slides-counter")!; const picker = ui.querySelector<HTMLElement>(".slides-picker-list")!; const gridList = ui.querySelector<HTMLElement>(".slides-grid-list")!; const edgeScrollbar = ui.querySelector<HTMLElement>(".slides-edge-scrollbar")!; const edgeScrollbarThumb = ui.querySelector<HTMLElement>(".slides-edge-scrollbar-thumb")!; const timerPopup = ui.querySelector<HTMLOutputElement>(".slides-timer-popup")!;
    const timerPreferences = readTimerPreferences(); const timerKey = `${TIMER_SESSION_PREFIX}${location.pathname}${new URLSearchParams(location.search).get("sort") || ""}`;
    let activePanel: Panel = null; let trigger: HTMLElement | null = null; let tool: Tool = null; let magnified = false; let magnifierMode: MagnifierMode = readStored().magnifierMode || "lens"; let magnifierZoom = readStored().magnifierZoom || 2; let magnifierLensSize = readStored().magnifierLensSize || 360; let lensPinned = false; let lensPoint = { x: innerWidth / 2, y: innerHeight / 2 }; let lensSlide: HTMLElement | null = null; let inkColor = "#ef4444"; let inkWidth = 4; let drawing = false; let stroke: Stroke | null = null; let idle = 0; let resizeTimer = 0; let applyingSplit = false; let lastTimerWarning = "";
    let timerSession: TimerSession = { mode: timerPreferences.mode, durationMs: timerPreferences.durationMinutes * 60000, elapsedMs: 0, startedAt: null, popupVisible: false };
    const ink = new Map<string, Stroke[]>(); const redo = new Map<string, Stroke[]>();
    const singleOriginalSlides = multiNote ? [] : Array.from(revealElement.querySelectorAll<HTMLElement>(".slides > section.vaultpub-slide")).map((slide) => slide.cloneNode(true) as HTMLElement);
    const key = (): string => { const index = deck.getIndices(); return `${index.h || 0}-${index.v || 0}`; };
    const strokes = (): Stroke[] => ink.get(key()) || [];
    const say = (message: string): void => { toast.textContent = message; toast.classList.add("is-visible"); window.setTimeout(() => toast.classList.remove("is-visible"), 1600); };
    const wake = (): void => { document.body.classList.remove("slides-ui-idle"); clearTimeout(idle); if (!activePanel && !dock.matches(":hover")) idle = window.setTimeout(() => document.body.classList.add("slides-ui-idle"), 2500); };
    const draw = (): void => { context.clearRect(0, 0, innerWidth, innerHeight); strokes().forEach((item) => { context.beginPath(); context.strokeStyle = item.color; context.lineWidth = item.width; context.lineCap = "round"; item.points.forEach((point, index) => index ? context.lineTo(point.x * innerWidth, point.y * innerHeight) : context.moveTo(point.x * innerWidth, point.y * innerHeight)); context.stroke(); }); };
    const sizeCanvas = (): void => { const pixel = devicePixelRatio || 1; canvas.width = innerWidth * pixel; canvas.height = innerHeight * pixel; canvas.style.width = `${innerWidth}px`; canvas.style.height = `${innerHeight}px`; context.setTransform(pixel, 0, 0, pixel, 0, 0); draw(); };
    const activeScrollableSlide = (): HTMLElement | null => {
      if (singlePage) return null;
      const current = deck.getCurrentSlide() as HTMLElement | null;
      return current?.matches(".vaultpub-slide") ? current : null;
    };
    const updateSlideNumberPosition = (): void => {
      if (singlePage) return;
      const revealBounds = revealElement.getBoundingClientRect(); const slideBounds = deck.getSlidesElement().getBoundingClientRect(); const dockBounds = dock.getBoundingClientRect();
      const right = Math.max(0, revealBounds.right - slideBounds.right) + 12;
      const dockCoversCorner = dockBounds.left < slideBounds.right && dockBounds.right > slideBounds.right - 72 && dockBounds.top < slideBounds.bottom;
      const bottom = Math.max(0, revealBounds.bottom - slideBounds.bottom, dockCoversCorner ? revealBounds.bottom - dockBounds.top + 8 : 0) + 12;
      revealElement.style.setProperty("--slides-number-right", `${right}px`);
      revealElement.style.setProperty("--slides-number-bottom", `${bottom}px`);
    };
    const updateEdgeScrollbar = (): void => {
      const slide = activeScrollableSlide();
      if (!slide) { edgeScrollbar.hidden = true; return; }
      const maximum = Math.max(0, slide.scrollHeight - slide.clientHeight);
      if (maximum < 1) { edgeScrollbar.hidden = true; return; }
      const track = edgeScrollbar.getBoundingClientRect().height;
      if (!track) return;
      const thumbHeight = Math.min(track, Math.max(28, track * (slide.clientHeight / slide.scrollHeight)));
      const travel = track - thumbHeight; const progress = maximum ? slide.scrollTop / maximum : 0;
      edgeScrollbarThumb.style.height = `${thumbHeight}px`;
      edgeScrollbarThumb.style.transform = `translateY(${travel * progress}px)`;
      edgeScrollbar.hidden = false;
      edgeScrollbar.setAttribute("aria-valuemax", String(Math.round(maximum)));
      edgeScrollbar.setAttribute("aria-valuenow", String(Math.round(slide.scrollTop)));
      edgeScrollbar.setAttribute("aria-valuetext", `${Math.round(progress * 100)}% through slide`);
    };
    const updateSlideChrome = (): void => { updateSlideNumberPosition(); updateEdgeScrollbar(); };
    const scheduleSlideChrome = (): void => { requestAnimationFrame(updateSlideChrome); };
    const scrollSlideFromEdge = (clientY: number): void => {
      const slide = activeScrollableSlide(); if (!slide) return;
      const track = edgeScrollbar.getBoundingClientRect(); const thumbHeight = edgeScrollbarThumb.getBoundingClientRect().height;
      const maximum = Math.max(0, slide.scrollHeight - slide.clientHeight); const travel = Math.max(1, track.height - thumbHeight);
      slide.scrollTop = Math.max(0, Math.min(maximum, ((clientY - track.top - thumbHeight / 2) / travel) * maximum));
      updateEdgeScrollbar();
    };
    edgeScrollbar.addEventListener("pointerdown", (event) => { edgeScrollbar.setPointerCapture(event.pointerId); scrollSlideFromEdge(event.clientY); event.preventDefault(); });
    edgeScrollbar.addEventListener("pointermove", (event) => { if (edgeScrollbar.hasPointerCapture(event.pointerId)) scrollSlideFromEdge(event.clientY); });
    edgeScrollbar.addEventListener("pointerup", (event) => { if (edgeScrollbar.hasPointerCapture(event.pointerId)) edgeScrollbar.releasePointerCapture(event.pointerId); });
    edgeScrollbar.addEventListener("keydown", (event) => {
      const slide = activeScrollableSlide(); if (!slide) return;
      const page = Math.max(48, slide.clientHeight * .8); let next: number | null = null;
      if (event.key === "ArrowDown") next = slide.scrollTop + 48;
      else if (event.key === "ArrowUp") next = slide.scrollTop - 48;
      else if (event.key === "PageDown") next = slide.scrollTop + page;
      else if (event.key === "PageUp") next = slide.scrollTop - page;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = slide.scrollHeight;
      if (next === null) return;
      slide.scrollTop = next; updateEdgeScrollbar(); event.preventDefault(); event.stopPropagation();
    });
    revealElement.addEventListener("scroll", (event) => { if (event.target === activeScrollableSlide()) updateEdgeScrollbar(); }, true);
    const saved = (): StoredPreferences => readStored();
    const dimensions = (): { width: number; height: number } => { if (singlePage) return { width: innerWidth, height: innerHeight }; const preference = saved(); const chosen = preference.aspect || "fit"; if (chosen === "fit") return { width: innerWidth, height: innerHeight }; const value = chosen === "custom" ? ratio(preference.customRatio || "") : ratio(chosen); const safe = value || 16 / 9; return { width: 1600, height: Math.round(1600 / safe) }; };
    const isFit = (): boolean => defaults.split === "fit";
    const saveTimerSession = (): void => { try { sessionStorage.setItem(timerKey, JSON.stringify(timerSession)); } catch { /* session recovery is optional */ } };
    const restoreTimerSession = (): void => {
      try {
        const raw = JSON.parse(sessionStorage.getItem(timerKey) || "{}") as Partial<TimerSession>;
        if ((raw.mode === "countdown" || raw.mode === "countup") && typeof raw.durationMs === "number" && typeof raw.elapsedMs === "number" && (raw.startedAt === null || typeof raw.startedAt === "number")) {
          timerSession = { mode: raw.mode, durationMs: Math.max(60000, raw.durationMs), elapsedMs: Math.max(0, raw.elapsedMs), startedAt: raw.startedAt, popupVisible: Boolean(raw.popupVisible) };
        }
      } catch { /* fall back to the last timer preference */ }
    };
    const timerElapsed = (): number => timerSession.elapsedMs + (timerSession.startedAt === null ? 0 : Math.max(0, Date.now() - timerSession.startedAt));
    const formatTimer = (milliseconds: number, overtime = false): string => {
      const seconds = Math.floor(Math.abs(milliseconds) / 1000); const hours = Math.floor(seconds / 3600); const minutes = Math.floor((seconds % 3600) / 60); const remainingSeconds = seconds % 60;
      return `${overtime ? "+" : ""}${hours ? `${hours}:${String(minutes).padStart(2, "0")}:` : `${String(Math.floor(seconds / 60)).padStart(2, "0")}:`}${String(remainingSeconds).padStart(2, "0")}`;
    };
    const timerValue = (): { label: string; warning: string } => {
      const elapsed = timerElapsed();
      if (timerSession.mode === "countup") return { label: formatTimer(elapsed), warning: "neutral" };
      const remaining = timerSession.durationMs - elapsed;
      if (remaining < 0) return { label: formatTimer(remaining, true), warning: "overtime" };
      if (timerPreferences.urgentMinutes > 0 && remaining <= timerPreferences.urgentMinutes * 60000) return { label: formatTimer(remaining), warning: "urgent" };
      if (timerPreferences.warningMinutes > 0 && remaining <= timerPreferences.warningMinutes * 60000) return { label: formatTimer(remaining), warning: "warning" };
      return { label: formatTimer(remaining), warning: "neutral" };
    };
    const setTimerPopupVisible = (visible: boolean): void => { timerPopup.hidden = !visible; timerSession.popupVisible = visible; saveTimerSession(); };
    const renderTimer = (): void => {
      const value = timerValue(); const running = timerSession.startedAt !== null;
      ui.querySelector<HTMLElement>(".slides-timer-display")!.textContent = value.label;
      ui.querySelector<HTMLElement>(".slides-clock")!.textContent = `${value.label}${timerSession.mode === "countdown" ? " remaining" : " elapsed"}`;
      timerPopup.value = value.label; timerPopup.dataset.warning = value.warning;
      if (value.warning !== "neutral" && value.warning !== lastTimerWarning) say(value.warning === "warning" ? "Timer warning" : value.warning === "urgent" ? "Timer urgent" : "Timer overtime");
      lastTimerWarning = value.warning;
    };
    const pauseTimer = (): void => { if (timerSession.startedAt !== null) { timerSession.elapsedMs = timerElapsed(); timerSession.startedAt = null; saveTimerSession(); } renderTimer(); };
    const startTimer = (): void => { if (timerSession.mode === "countdown" && timerElapsed() >= timerSession.durationMs) timerSession.elapsedMs = 0; if (timerSession.startedAt === null) timerSession.startedAt = Date.now(); setTimerPopupVisible(true); panelClose(); renderTimer(); };
    const resetTimer = (): void => { timerSession.elapsedMs = 0; timerSession.startedAt = null; lastTimerWarning = ""; saveTimerSession(); renderTimer(); };
    const updateTimerDuration = (): void => { const hours = Number(ui.querySelector<HTMLInputElement>("[data-timer-hours]")!.value || 0); const minutes = Number(ui.querySelector<HTMLInputElement>("[data-timer-minutes]")!.value || 0); const duration = Math.max(1, Math.min(1440, hours * 60 + minutes)); timerPreferences.durationMinutes = duration; timerSession.durationMs = duration * 60000; saveTimerPreferences(timerPreferences); saveTimerSession(); renderTimer(); };
    const clearMagnification = (): void => { if (magnified) document.body.classList.remove("slides-magnified"); magnified = false; lens.hidden = true; lensPinned = false; };
    const refreshLensMirror = (): void => {
      if (tool !== "magnify" || magnifierMode !== "lens") return;
      const slide = deck.getCurrentSlide() as HTMLElement | null; const content = slide?.querySelector<HTMLElement>(".vaultpub-slide-content");
      if (!slide || !content) { lens.hidden = true; return; }
      const clone = slide.cloneNode(true) as HTMLElement; clone.removeAttribute("style"); clone.querySelectorAll("[id]").forEach((item) => item.removeAttribute("id")); clone.querySelectorAll("a,button,input,select,textarea").forEach((item) => item.setAttribute("tabindex", "-1")); clone.querySelectorAll("video,audio,iframe").forEach((item) => { const placeholder = document.createElement("div"); placeholder.className = "slides-magnifier-media"; placeholder.textContent = "Media: use Full slide magnification"; item.replaceWith(placeholder); });
      clone.setAttribute("aria-hidden", "true"); clone.inert = true; lensMirror.replaceChildren(clone); lensSlide = slide;
    };
    const positionLens = (show = false): void => {
      if (tool !== "magnify" || magnifierMode !== "lens") return;
      if (lens.hidden && !show) return;
      if (!lensSlide || !lensMirror.firstElementChild) refreshLensMirror(); if (!lensSlide || !lensMirror.firstElementChild) return;
      const rect = lensSlide.getBoundingClientRect(); const computed = deck.getComputedSlideSize(); const baseScale = rect.width / Math.max(1, computed.width); const width = Math.min(magnifierLensSize, Math.max(160, innerWidth - 24)); const height = Math.min(Math.round(width / 1.5), Math.max(106, innerHeight - 24)); const left = Math.max(12, Math.min(innerWidth - width - 12, lensPoint.x - width / 2)); const top = Math.max(12, Math.min(innerHeight - height - 12, lensPoint.y - height / 2)); const mirror = lensMirror.firstElementChild as HTMLElement; const scale = baseScale * magnifierZoom; const originX = (lensPoint.x - rect.left) / baseScale; const originY = (lensPoint.y - rect.top) / baseScale;
      lens.style.width = `${width}px`; lens.style.height = `${height}px`; lens.style.left = `${left}px`; lens.style.top = `${top}px`; mirror.style.width = `${computed.width}px`; mirror.style.height = `${computed.height}px`; mirror.style.left = `${lensPoint.x - left - originX * scale}px`; mirror.style.top = `${lensPoint.y - top - originY * scale}px`; mirror.style.transform = `scale(${scale})`; lens.hidden = false;
    };
    const panelClose = (): void => { if (!activePanel) return; panels.get(activePanel)!.hidden = true; activePanel = null; document.body.classList.remove("slides-panel-open"); dock.querySelectorAll<HTMLElement>("[aria-expanded]").forEach((button) => button.setAttribute("aria-expanded", "false")); const previous = trigger; trigger = null; previous?.focus(); wake(); };
    const panelOpen = (next: Exclude<Panel, null>, source: HTMLElement): void => { if (activePanel === next) { panelClose(); return; } panels.forEach((panel) => panel.hidden = true); activePanel = next; trigger = source; panels.get(next)!.hidden = false; document.body.classList.add("slides-panel-open"); dock.querySelectorAll<HTMLElement>("[aria-expanded]").forEach((button) => button.setAttribute("aria-expanded", String(button.dataset.action === next))); wake(); panels.get(next)!.focus(); };
    const setTool = (next: Tool): void => { clearMagnification(); tool = tool === next ? null : next; canvas.style.pointerEvents = tool === "pen" ? "auto" : "none"; canvas.classList.toggle("is-active", tool === "pen"); laser.classList.toggle("is-active", tool === "laser"); dock.querySelectorAll<HTMLElement>("[data-tool]").forEach((button) => { const selected = button.dataset.tool === tool; button.classList.toggle("is-active", selected); button.setAttribute("aria-pressed", String(selected)); }); if (tool === "pen") panelOpen("tools", dock.querySelector<HTMLElement>("[data-tool=pen]")!); else if (tool === "magnify") { panelOpen("magnifier", dock.querySelector<HTMLElement>("[data-tool=magnify]")!); refreshLensMirror(); positionLens(true); } else if (activePanel === "tools" || activePanel === "magnifier") panelClose(); if (tool) say(tool === "magnify" ? "Magnifier armed" : `${tool} active`); wake(); };
    const slideIndex = (): number => Math.max(0, (deck.getSlides() as HTMLElement[]).indexOf(deck.getCurrentSlide()));
    const updateNavigation = (): void => {
      if (multiNote) {
        const indices = deck.getIndices(); const currentNote = Number(indices.h || 0); const currentSlide = Number(indices.v || 0);
        const localCount = noteSlot(currentNote)?.children.length || 1;
        counter.textContent = `File ${currentNote + 1}/${manifest.length} · Slide ${currentSlide + 1}/${localCount}`;
        ui.querySelectorAll<HTMLElement>("[data-note-index]").forEach((item) => item.classList.toggle("is-current", Number(item.dataset.noteIndex) === currentNote && Number(item.dataset.localIndex || 0) === currentSlide));
      } else {
        const slides = deck.getSlides() as HTMLElement[]; const current = slideIndex(); counter.textContent = `${current + 1} / ${slides.length}`;
        ui.querySelectorAll<HTMLElement>("[data-slide-index]").forEach((item) => item.classList.toggle("is-current", Number(item.dataset.slideIndex) === current));
      }
      draw();
    };
    const addNavigationItem = (parent: HTMLElement, note: number, local: number, heading: string, path: string, withThumbnail: boolean): void => {
      const item = document.createElement("button"); item.type = "button"; item.dataset.noteIndex = String(note); item.dataset.localIndex = String(local); item.dataset.search = `${heading} ${path}`;
      const title = document.createElement("strong"); title.textContent = `${heading}`; item.appendChild(title);
      if (path) { const detail = document.createElement("small"); detail.textContent = path; item.appendChild(detail); }
      if (withThumbnail) {
        const content = noteSlot(note)?.children[local]?.querySelector<HTMLElement>(".vaultpub-slide-content");
        if (content) { const thumb = document.createElement("span"); thumb.className = "slides-grid-thumb"; thumb.appendChild(content.cloneNode(true)); thumb.querySelectorAll("[src]").forEach((media) => media.removeAttribute("src")); item.prepend(thumb); }
      }
      parent.appendChild(item);
    };
    const buildNavigation = (): void => {
      picker.replaceChildren(); gridList.replaceChildren();
      if (multiNote) {
        manifest.forEach((note, index) => {
          addNavigationItem(picker, index, 0, `File: ${note.title}`, note.sourcePath, false);
          addNavigationItem(gridList, index, 0, `File: ${note.title}`, note.sourcePath, true);
          note.fragments.forEach((fragment) => {
            addNavigationItem(picker, index, fragment.index + 1, fragment.title, note.sourcePath, false);
            addNavigationItem(gridList, index, fragment.index + 1, fragment.title, note.sourcePath, true);
          });
        });
      } else {
        const slides = deck.getSlides() as HTMLElement[];
        slides.forEach((slide, index) => {
          const heading = slide.dataset.slideKind === "note-divider" ? `File: ${text(slide.querySelector("h1,h2,h3")?.textContent)}` : text(slide.querySelector("h1,h2,h3")?.textContent);
          const path = slide.dataset.sourcePath || ""; const item = document.createElement("button"); item.type = "button"; item.dataset.slideIndex = String(index); item.dataset.search = `${heading} ${path}`; item.textContent = heading; picker.appendChild(item);
          const gridItem = item.cloneNode(true) as HTMLButtonElement; const thumb = document.createElement("span"); thumb.className = "slides-grid-thumb"; const content = slide.querySelector<HTMLElement>(".vaultpub-slide-content"); if (content) thumb.appendChild(content.cloneNode(true)); gridItem.prepend(thumb); gridList.appendChild(gridItem);
        });
      }
      updateNavigation();
    };
    const goToMultiNoteSlide = async (note: number, local: number): Promise<void> => {
      await hydrateWindow(note); deck.sync(); deck.slide(note, Math.min(local, Math.max(0, (noteSlot(note)?.children.length || 1) - 1))); buildNavigation(); updateNavigation();
    };
    const pageWith = (page: HTMLElement, candidate: HTMLElement): HTMLElement => { const trial = page.cloneNode(true) as HTMLElement; trial.querySelector<HTMLElement>(".vaultpub-slide-content")!.appendChild(candidate.cloneNode(true)); return trial; };
    const paginateFit = (): void => {
      if (!isFit()) return;
      const current = deck.getCurrentSlide() as HTMLElement | null; const currentPath = current?.dataset.sourcePath || ""; const currentNote = noteIndex(); const currentVertical = Number(deck.getIndices().v || 0); const sourceSlides = multiNote ? originalSlidesByNote.get(currentNote) || [] : singleOriginalSlides; const slideSize = deck.getComputedSlideSize(); const safeHeight = Math.max(260, slideSize.height - 36);
      if (!sourceSlides.length) return;
      const measure = document.createElement("div"); measure.className = "slides-fit-measure"; measure.style.width = `${Math.max(320, slideSize.width)}px`; measure.style.height = `${safeHeight}px`; document.body.appendChild(measure);
      const fits = (page: HTMLElement, scale = 1): boolean => { const trial = page.cloneNode(true) as HTMLElement; trial.querySelector<HTMLElement>(".vaultpub-slide-content")!.style.setProperty("--vaultpub-fit-scale", String(scale)); measure.replaceChildren(trial); return measure.querySelector<HTMLElement>(".vaultpub-slide-content")!.scrollHeight <= safeHeight + 1; };
      const makePage = (source: HTMLElement): HTMLElement => { const page = source.cloneNode(false) as HTMLElement; page.appendChild(source.querySelector<HTMLElement>(".vaultpub-slide-content")!.cloneNode(false)); return page; };
      const pages: HTMLElement[] = [];
      sourceSlides.forEach((source) => { let page = makePage(source); let content = page.querySelector<HTMLElement>(".vaultpub-slide-content")!; const commit = (): void => { if (content.childElementCount) pages.push(page); page = makePage(source); content = page.querySelector<HTMLElement>(".vaultpub-slide-content")!; };
        for (const node of Array.from(source.querySelector<HTMLElement>(".vaultpub-slide-content")!.children)) { const candidate = node.cloneNode(true) as HTMLElement; if (fits(pageWith(page, candidate))) { content.appendChild(candidate); continue; } if (content.childElementCount) { commit(); if (fits(pageWith(page, candidate))) { content.appendChild(candidate); continue; } } if (candidate.tagName === "P" && !candidate.children.length) { const words = (candidate.textContent || "").match(/\S+\s*/g) || []; let start = 0; while (start < words.length) { let low = start + 1; let high = words.length; let best = start; while (low <= high) { const middle = Math.floor((low + high) / 2); const fragment = candidate.cloneNode(false) as HTMLElement; fragment.textContent = words.slice(start, middle).join(""); if (fits(pageWith(page, fragment))) { best = middle; low = middle + 1; } else high = middle - 1; } if (best === start) { candidate.classList.add("slides-fit-overflow"); content.appendChild(candidate); break; } const fragment = candidate.cloneNode(false) as HTMLElement; fragment.textContent = words.slice(start, best).join(""); content.appendChild(fragment); start = best; if (start < words.length) commit(); } } else { candidate.classList.add("slides-fit-overflow"); content.appendChild(candidate); commit(); } }
        commit();
      });
      pages.forEach((page) => { if (!fits(page)) return; let low = 1; let high = 1.6; for (let index = 0; index < 5; index += 1) { const middle = (low + high) / 2; if (fits(page, middle)) low = middle; else high = middle; } page.querySelector<HTMLElement>(".vaultpub-slide-content")!.style.setProperty("--vaultpub-fit-scale", low.toFixed(3)); });
      measure.remove();
      if (multiNote) {
        const slot = noteSlot(currentNote); if (!slot) return;
        slot.replaceChildren(...pages); deck.sync(); deck.slide(currentNote, Math.min(currentVertical, Math.max(0, pages.length - 1))); enrich(slot); buildNavigation();
      } else {
        revealElement.querySelector<HTMLElement>(".slides")!.replaceChildren(...pages); deck.sync(); const slides = deck.getSlides() as HTMLElement[]; deck.slide(Math.max(0, slides.findIndex((slide) => slide.dataset.sourcePath === currentPath))); enrich(revealElement); buildNavigation();
      }
    };
    const apply = (): void => { const preference = saved(); const html = document.documentElement; html.classList.remove(...Array.from(html.classList).filter((name) => name.startsWith("theme-"))); html.classList.add(`theme-${preference.theme || defaults.theme}`); html.style.setProperty("--vaultpub-slide-scale", String((preference.textScale || 100) / 100)); document.body.classList.toggle("slides-code-wrap", preference.codeWrap ?? defaults.codeWrap); document.body.classList.toggle("slides-center-content", preference.center ?? Boolean(defaults.center)); const reduced = preference.reducedMotion ?? matchMedia("(prefers-reduced-motion: reduce)").matches; document.body.classList.toggle("slides-reduced-motion", reduced); const size = dimensions(); deck.configure({ controls: false, transition: reduced ? "none" : (preference.transition || defaults.transition), progress: preference.progress ?? defaults.progress, ...(singlePage ? { margin: 0, slideNumber: false } : { slideNumber: preference.slideNumber ?? defaults.slideNumber }), center: preference.center ?? defaults.center, width: size.width, height: size.height }); requestAnimationFrame(() => { deck.layout(); sizeCanvas(); requestAnimationFrame(() => { paginateFit(); scheduleSlideChrome(); refreshLensMirror(); positionLens(); }); }); };
    const start = async (): Promise<void> => {
      try {
        if (multiNote) {
          const initial = initialMultiNoteLocation(manifest);
          await hydrateWindow(initial.note); deck.slide(initial.note, initial.slide);
        }
      }
      catch { say("This file could not be loaded. Select it again to retry."); }
      restoreTimerSession(); apply(); buildNavigation(); sizeCanvas(); renderTimer(); if (timerSession.popupVisible) setTimerPopupVisible(true); setInterval(renderTimer, 1000); wake();
    };
    void start();
    dock.addEventListener("pointerenter", () => { clearTimeout(idle); document.body.classList.remove("slides-ui-idle"); }); dock.addEventListener("pointerleave", wake);
    dock.addEventListener("click", (event) => { const target = (event.target as HTMLElement).closest<HTMLElement>("[data-action],[data-tool]"); if (!target) return; const action = target.dataset.action; if (target.dataset.tool) { setTool(target.dataset.tool as Exclude<Tool, null>); return; } if (action === "previous") deck.prev(); else if (action === "next") deck.next(); else if (action === "picker") panelOpen("picker", target); else if (action === "overview") panelOpen("grid", target); else if (action === "settings") panelOpen("settings", target); else if (action === "timer") panelOpen("timer", target); else if (action === "help") panelOpen("help", target); else if (action === "blackout") { deck.togglePause(); target.classList.toggle("is-active"); } else if (action === "fullscreen") { if (document.fullscreenElement) void document.exitFullscreen(); else void document.documentElement.requestFullscreen?.().catch(() => say("Fullscreen is unavailable")); } wake(); });
    ui.addEventListener("click", (event) => {
      const target = (event.target as HTMLElement).closest<HTMLElement>("[data-action],[data-theme],[data-split],[data-ink-color],[data-slide-index],[data-note-index],[data-magnifier-mode],[data-timer-mode]");
      if (!target || dock.contains(target)) return;
      const action = target.dataset.action;
      if (action === "close") { panelClose(); return; }
      if (target.dataset.noteIndex !== undefined) { void goToMultiNoteSlide(Number(target.dataset.noteIndex), Number(target.dataset.localIndex || 0)); panelClose(); return; }
      if (target.dataset.slideIndex !== undefined) { deck.slide(Number(target.dataset.slideIndex)); panelClose(); return; }
      if (action === "reset") { localStorage.removeItem(SETTINGS_KEY); setSplitCookie(null); const url = new URL(location.href); url.searchParams.delete("split"); location.assign(url.toString()); return; }
      if (action === "magnifier-reset") {
        magnifierMode = "lens"; magnifierZoom = 2; magnifierLensSize = 360;
        const preference = saved(); preference.magnifierMode = magnifierMode; preference.magnifierZoom = magnifierZoom; preference.magnifierLensSize = magnifierLensSize; saveStored(preference);
        ui.querySelector<HTMLInputElement>("[data-magnifier-setting=zoom]")!.value = "2"; ui.querySelector<HTMLInputElement>("[data-magnifier-setting=lensSize]")!.value = "360"; ui.querySelector<HTMLOutputElement>("[data-output=magnifierZoom]")!.textContent = "2.00×"; ui.querySelector<HTMLOutputElement>("[data-output=magnifierLensSize]")!.textContent = "360px";
      } else if (action === "timer-start") startTimer();
      else if (action === "timer-pause") { if (timerSession.startedAt === null) startTimer(); else pauseTimer(); }
      else if (action === "timer-reset") resetTimer();
      else if (action === "timer-show-popup") setTimerPopupVisible(true);
      else if (action === "timer-hide-popup") setTimerPopupVisible(false);
      else if (action === "eraser" || action === "undo") { const current = strokes(); if (current.length) { const removed = current[current.length - 1]; ink.set(key(), current.slice(0, -1)); redo.set(key(), [...(redo.get(key()) || []), removed]); draw(); } }
      else if (action === "redo") { const undone = redo.get(key()) || []; const restored = undone.pop(); if (restored) { redo.set(key(), undone); ink.set(key(), [...strokes(), restored]); draw(); } }
      else if (action === "clear") { ink.set(key(), []); draw(); }
      else if (target.dataset.inkColor) { inkColor = target.dataset.inkColor; ui.querySelectorAll<HTMLElement>("[data-ink-color]").forEach((item) => item.classList.toggle("is-selected", item.dataset.inkColor === inkColor)); }
      else if (target.dataset.magnifierMode) {
        magnifierMode = target.dataset.magnifierMode as MagnifierMode; const preference = saved(); preference.magnifierMode = magnifierMode; saveStored(preference); ui.querySelectorAll<HTMLElement>("[data-magnifier-mode]").forEach((item) => { const selected = item.dataset.magnifierMode === magnifierMode; item.classList.toggle("is-selected", selected); item.setAttribute("aria-pressed", String(selected)); }); clearMagnification(); refreshLensMirror(); positionLens(true);
      } else if (target.dataset.timerMode) {
        timerPreferences.mode = target.dataset.timerMode as TimerMode; timerSession.mode = timerPreferences.mode; resetTimer(); saveTimerPreferences(timerPreferences); ui.querySelectorAll<HTMLElement>("[data-timer-mode]").forEach((item) => { const selected = item.dataset.timerMode === timerPreferences.mode; item.classList.toggle("is-selected", selected); item.setAttribute("aria-pressed", String(selected)); });
      } else if (target.dataset.theme) { const preference = saved(); preference.theme = target.dataset.theme; saveStored(preference); ui.querySelectorAll<HTMLElement>("[data-theme]").forEach((item) => { const selected = item.dataset.theme === preference.theme; item.classList.toggle("is-selected", selected); item.setAttribute("aria-pressed", String(selected)); }); apply(); }
      else if (target.dataset.split && !applyingSplit) { applyingSplit = true; target.setAttribute("aria-pressed", "true"); target.classList.add("is-applying"); setSplitCookie(target.dataset.split as SplitPolicy); const url = new URL(location.href); url.searchParams.set("split", target.dataset.split); location.assign(url.toString()); }
      if (action === "magnifier-reset") { ui.querySelectorAll<HTMLElement>("[data-magnifier-mode]").forEach((item) => { const selected = item.dataset.magnifierMode === magnifierMode; item.classList.toggle("is-selected", selected); item.setAttribute("aria-pressed", String(selected)); }); clearMagnification(); refreshLensMirror(); positionLens(true); }
      wake();
    });
    ui.querySelectorAll<HTMLInputElement | HTMLSelectElement>("[data-setting]").forEach((input) => {
      const updateSetting = (): void => { const setting = input.dataset.setting!; if (setting === "inkWidth") { inkWidth = Number(input.value); return; } const preference = saved(); const value: string | number | boolean = input instanceof HTMLInputElement && input.type === "checkbox" ? input.checked : setting === "textScale" ? Number(input.value) : input.value; if (setting === "customRatio" && value && !ratio(String(value))) { input.setCustomValidity("Use width:height or a decimal ratio"); return; } input.setCustomValidity(""); (preference as Record<string, string | number | boolean>)[setting] = value; saveStored(preference); if (setting === "textScale") ui.querySelector<HTMLOutputElement>("[data-output=textScale]")!.textContent = `${value}%`; if (setting === "aspect") ui.querySelector<HTMLElement>(".slides-custom-ratio")!.hidden = value !== "custom"; apply(); };
      input.addEventListener(input instanceof HTMLSelectElement ? "change" : "input", updateSetting);
    });
    ui.querySelectorAll<HTMLInputElement>("[data-magnifier-setting]").forEach((input) => input.addEventListener("input", () => {
      const preference = saved();
      if (input.dataset.magnifierSetting === "zoom") { magnifierZoom = Number(input.value); preference.magnifierZoom = magnifierZoom; ui.querySelector<HTMLOutputElement>("[data-output=magnifierZoom]")!.textContent = `${magnifierZoom.toFixed(2)}×`; }
      else { magnifierLensSize = Number(input.value); preference.magnifierLensSize = magnifierLensSize; ui.querySelector<HTMLOutputElement>("[data-output=magnifierLensSize]")!.textContent = `${magnifierLensSize}px`; }
      saveStored(preference); if (magnifierMode === "full" && magnified) document.documentElement.style.setProperty("--slides-magnification", String(magnifierZoom)); else positionLens();
    }));
    const timerPreset = ui.querySelector<HTMLSelectElement>("[data-timer-preset]")!;
    timerPreset.value = ["5", "10", "15", "20", "30", "45", "60"].includes(String(timerPreferences.durationMinutes)) ? String(timerPreferences.durationMinutes) : "custom";
    timerPreset.addEventListener("change", () => { const custom = timerPreset.value === "custom"; ui.querySelector<HTMLElement>(".slides-timer-custom")!.hidden = !custom; if (!custom) { const duration = Number(timerPreset.value); ui.querySelector<HTMLInputElement>("[data-timer-hours]")!.value = String(Math.floor(duration / 60)); ui.querySelector<HTMLInputElement>("[data-timer-minutes]")!.value = String(duration % 60); updateTimerDuration(); } });
    ui.querySelectorAll<HTMLInputElement>("[data-timer-hours],[data-timer-minutes]").forEach((input) => input.addEventListener("input", updateTimerDuration));
    ui.querySelector<HTMLInputElement>("[data-timer-warning]")!.addEventListener("input", (event) => { timerPreferences.warningMinutes = Math.max(0, Number((event.target as HTMLInputElement).value || 0)); if (timerPreferences.urgentMinutes > timerPreferences.warningMinutes) timerPreferences.urgentMinutes = timerPreferences.warningMinutes; ui.querySelector<HTMLInputElement>("[data-timer-urgent]")!.value = String(timerPreferences.urgentMinutes); saveTimerPreferences(timerPreferences); renderTimer(); });
    ui.querySelector<HTMLInputElement>("[data-timer-urgent]")!.addEventListener("input", (event) => { timerPreferences.urgentMinutes = Math.min(timerPreferences.warningMinutes, Math.max(0, Number((event.target as HTMLInputElement).value || 0))); (event.target as HTMLInputElement).value = String(timerPreferences.urgentMinutes); saveTimerPreferences(timerPreferences); renderTimer(); });
    ui.querySelector<HTMLInputElement>("[data-action=search]")?.addEventListener("input", (event) => { const query = (event.target as HTMLInputElement).value.toLowerCase(); picker.querySelectorAll<HTMLElement>("[data-search]").forEach((item) => item.hidden = !item.dataset.search!.toLowerCase().includes(query)); });
    canvas.addEventListener("pointerdown", (event) => { if (tool !== "pen") return; drawing = true; canvas.setPointerCapture(event.pointerId); stroke = { color: inkColor, width: inkWidth, points: [{ x: event.clientX / innerWidth, y: event.clientY / innerHeight }] }; ink.set(key(), [...strokes(), stroke]); redo.delete(key()); draw(); event.preventDefault(); }); canvas.addEventListener("pointermove", (event) => { if (!drawing || !stroke) return; stroke.points.push({ x: event.clientX / innerWidth, y: event.clientY / innerHeight }); draw(); }); canvas.addEventListener("pointerup", () => { drawing = false; stroke = null; });
    revealElement.addEventListener("pointermove", (event) => { wake(); if (tool === "laser") { laser.style.left = `${event.clientX}px`; laser.style.top = `${event.clientY}px`; laser.classList.add("is-visible"); } if (tool === "magnify" && magnifierMode === "full" && magnified) { document.documentElement.style.setProperty("--slides-zoom-x", `${event.clientX}px`); document.documentElement.style.setProperty("--slides-zoom-y", `${event.clientY}px`); } if (tool === "magnify" && magnifierMode === "lens" && (!lensPinned || event.pointerType === "touch")) { lensPoint = { x: event.clientX, y: event.clientY }; positionLens(true); } });
    revealElement.addEventListener("pointerdown", (event) => { if (!ui.contains(event.target as Node) && activePanel) panelClose(); if (tool !== "magnify") return; if (magnifierMode === "full") { if (magnified) { clearMagnification(); return; } magnified = true; document.documentElement.style.setProperty("--slides-zoom-x", `${event.clientX}px`); document.documentElement.style.setProperty("--slides-zoom-y", `${event.clientY}px`); document.documentElement.style.setProperty("--slides-magnification", String(magnifierZoom)); document.body.classList.add("slides-magnified"); event.preventDefault(); return; } lensPoint = { x: event.clientX, y: event.clientY }; lensPinned = !lensPinned; positionLens(true); event.preventDefault(); });
    const scheduleApply = (): void => { clearTimeout(resizeTimer); resizeTimer = window.setTimeout(apply, 180); };
    deck.on("slidechanged", () => { clearMagnification(); updateNavigation(); scheduleSlideChrome(); const commandRequestId = pendingCommandRequestId; pendingCommandRequestId = undefined; if (embedReady) sendEmbedSlideChanged(commandRequestId); if (multiNote) void hydrateWindow(noteIndex()).then(() => { buildNavigation(); updateNavigation(); scheduleApply(); }).catch(() => say("This file could not be loaded. Select it again to retry.")); else { refreshLensMirror(); positionLens(); } }); window.addEventListener("resize", scheduleApply); revealElement.querySelectorAll("img,video,iframe").forEach((media) => media.addEventListener("load", scheduleApply)); window.setTimeout(scheduleApply, 500); document.addEventListener("pointermove", wake, { passive: true }); document.addEventListener("keydown", (event) => { const updateMagnifierZoom = (change: number): void => { if (tool !== "magnify") return; magnifierZoom = Math.max(1.25, Math.min(4, magnifierZoom + change)); ui.querySelector<HTMLInputElement>("[data-magnifier-setting=zoom]")!.value = String(magnifierZoom); ui.querySelector<HTMLOutputElement>("[data-output=magnifierZoom]")!.textContent = `${magnifierZoom.toFixed(2)}×`; const preference = saved(); preference.magnifierZoom = magnifierZoom; saveStored(preference); if (magnifierMode === "full" && magnified) document.documentElement.style.setProperty("--slides-magnification", String(magnifierZoom)); else positionLens(); }; if (event.key === "Escape") { if (activePanel) panelClose(); else if (tool) setTool(null); return; } if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement) return; if (event.key === "?") panelOpen("help", dock.querySelector("[data-action=help]")!); else if (event.key.toLowerCase() === "g") panelOpen("picker", dock.querySelector("[data-action=picker]")!); else if (event.key.toLowerCase() === "t") panelOpen("timer", dock.querySelector("[data-action=timer]")!); else if (event.key === "+" || event.key === "=") updateMagnifierZoom(.25); else if (event.key === "-") updateMagnifierZoom(-.25); else if (event.key.toLowerCase() === "f") { if (document.fullscreenElement) void document.exitFullscreen(); else void document.documentElement.requestFullscreen?.().catch(() => say("Fullscreen is unavailable")); } else if (event.key.toLowerCase() === "l") setTool("laser"); else if (event.key.toLowerCase() === "z") setTool("magnify"); else if (event.key.toLowerCase() === "d") setTool("pen"); else if (event.key.toLowerCase() === "b") deck.togglePause(); });
    if (embedMode) { embedReady = true; if (handshakeReceived) sendEmbedReady(handshakeRequestId); }
  }).catch(() => { if (embedMode) sendEmbedError("initialization_failed", "Slide View could not be initialized"); });
});
