export interface ThemeInfo {
  id: string;
  name: string;
  group: "light" | "dark";
  preview: [string, string, string, string];
}

export const READING_THEMES: ThemeInfo[] = [
  { id: "light", name: "Light", group: "light", preview: ["#fafbfc", "#1a1a2e", "#2563eb", "#e5e7eb"] },
  { id: "dark", name: "Dark", group: "dark", preview: ["#1a1b1e", "#e4e4e7", "#60a5fa", "#2d2d30"] },
  { id: "nord", name: "Nord", group: "dark", preview: ["#2e3440", "#d8dee9", "#88c0d0", "#4c566a"] },
  { id: "solarized", name: "Solarized", group: "light", preview: ["#fdf6e3", "#586e75", "#268bd2", "#eee8d5"] },
  { id: "dracula", name: "Dracula", group: "dark", preview: ["#282a36", "#f8f8f2", "#bd93f9", "#44475a"] },
  { id: "forest", name: "Forest", group: "dark", preview: ["#1a2a1a", "#d4e4d4", "#6fcf6f", "#2d452d"] },
  { id: "glass-light", name: "Glass Light", group: "light", preview: ["rgba(250,251,252,.55)", "#1a1a2e", "#2563eb", "rgba(0,0,0,.08)"] },
  { id: "glass-dark", name: "Glass Dark", group: "dark", preview: ["rgba(26,27,30,.6)", "#e4e4e7", "#60a5fa", "rgba(255,255,255,.06)"] },
  { id: "obsidian", name: "Obsidian", group: "dark", preview: ["#1e1e1e", "#cccccc", "#7f6df2", "#3c3c3c"] },
  { id: "catppuccin", name: "Catppuccin", group: "light", preview: ["#eff1f5", "#4c4f69", "#1e66f5", "#ccd0da"] },
  { id: "colorful", name: "Colorful", group: "light", preview: ["#e11d48", "#7c3aed", "#2563eb", "#6366f1"] },
  { id: "colorful-dark", name: "Colorful Dark", group: "dark", preview: ["#fb7185", "#a78bfa", "#60a5fa", "#818cf8"] },
];

export const READING_THEME_IDS = new Set(READING_THEMES.map((theme) => theme.id));
