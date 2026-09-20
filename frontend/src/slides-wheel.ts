const EDGE_EPSILON = 2;
const GESTURE_IDLE_MS = 180;
const PAGE_COOLDOWN_MS = 350;
const WHEEL_TRIGGER_PX = 24;

export interface SlideWheelOptions {
  root: HTMLElement;
  currentSlide: () => HTMLElement | null;
  enabled: () => boolean;
  blocked: (target: EventTarget | null) => boolean;
  previous: () => void;
  next: () => void;
}

const wheelPixels = (event: WheelEvent, height: number): { x: number; y: number } => {
  const multiplier = event.deltaMode === WheelEvent.DOM_DELTA_LINE ? 16 : event.deltaMode === WheelEvent.DOM_DELTA_PAGE ? height : 1;
  return { x: event.deltaX * multiplier, y: event.deltaY * multiplier };
};

const scrollParent = (target: EventTarget | null, slide: HTMLElement): HTMLElement | null => {
  let node = target instanceof HTMLElement ? target : null;
  while (node && node !== slide) {
    const style = getComputedStyle(node);
    if ((style.overflowY === "auto" || style.overflowY === "scroll") && node.scrollHeight > node.clientHeight + EDGE_EPSILON) return node;
    node = node.parentElement;
  }
  return slide.scrollHeight > slide.clientHeight + EDGE_EPSILON ? slide : null;
};

export function installSlideWheelNavigation(options: SlideWheelOptions): () => void {
  let lastEventAt = 0;
  let direction = 0;
  let accumulated = 0;
  let consumedGesture = false;
  let lockedGesture = false;
  let cooldownUntil = 0;
  const resetGesture = (): void => { direction = 0; accumulated = 0; consumedGesture = false; lockedGesture = false; };
  const handler = (event: WheelEvent): void => {
    if (!options.enabled() || options.blocked(event.target) || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const slide = options.currentSlide();
    if (!slide) return;
    const delta = wheelPixels(event, slide.clientHeight || innerHeight);
    if (Math.abs(delta.y) < .5 || Math.abs(delta.x) >= Math.abs(delta.y)) return;
    const now = performance.now();
    if (now - lastEventAt > GESTURE_IDLE_MS) resetGesture();
    lastEventAt = now;
    const nextDirection = delta.y > 0 ? 1 : -1;
    if (direction && direction !== nextDirection) resetGesture();
    direction = nextDirection;
    const container = scrollParent(event.target, slide);
    if (container) {
      const maximum = Math.max(0, container.scrollHeight - container.clientHeight);
      const canScroll = nextDirection > 0 ? container.scrollTop < maximum - EDGE_EPSILON : container.scrollTop > EDGE_EPSILON;
      if (canScroll) {
        container.scrollTop = Math.max(0, Math.min(maximum, container.scrollTop + delta.y));
        consumedGesture = true;
        event.preventDefault();
        return;
      }
    }
    if (consumedGesture || lockedGesture || now < cooldownUntil) { event.preventDefault(); return; }
    accumulated += Math.abs(delta.y);
    if (accumulated < WHEEL_TRIGGER_PX) { event.preventDefault(); return; }
    lockedGesture = true;
    cooldownUntil = now + PAGE_COOLDOWN_MS;
    if (nextDirection > 0) options.next(); else options.previous();
    event.preventDefault();
  };
  options.root.addEventListener("wheel", handler, { passive: false });
  return () => options.root.removeEventListener("wheel", handler);
}
