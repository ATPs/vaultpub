import { createIcons, icons } from "lucide";

/** Replace static icon placeholders after their owning UI has been attached. */
export function initIcons(): void {
  createIcons({ icons });
}
