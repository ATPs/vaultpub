/**
 * Auto-hide top bar on scroll down, show on scroll up.
 * Gives more vertical reading space.
 */

let lastScrollY = 0;
const THRESHOLD = 40;

export function initScroller(): void {
  const topbar = document.querySelector<HTMLElement>(".top-bar");
  if (!topbar) return;

  window.addEventListener(
    "scroll",
    () => {
      const y = window.scrollY;
      if (Math.abs(y - lastScrollY) < 6) return;

      if (y > lastScrollY && y > THRESHOLD) {
        topbar.classList.add("top-bar-hidden");
      } else {
        topbar.classList.remove("top-bar-hidden");
      }
      lastScrollY = y;
    },
    { passive: true },
  );
}
