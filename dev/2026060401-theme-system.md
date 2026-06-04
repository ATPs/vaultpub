# Feature: Multi-Theme System with Design Overhaul

## Goal

Replace the simple light/dark toggle with a rich multi-theme system. Add 12 hand-crafted themes including glassmorphism (transparency) effects and colorful rainbow-heading themes. Significantly improve the default design and typography. Add scroll-aware header auto-hide. Fix sidebar peek behavior (compact icons, content-based height). Hide empty graph container.

## Conclusion

Implemented 12 themes accessible via a dropdown selector injected by JS into the top bar. The old theme toggle button is removed from server-rendered HTML and replaced dynamically. Glass themes use backdrop-filter blur with pseudo-element body backgrounds. Top bar auto-hides on scroll-down and reappears on scroll-up. Sidebar peek buttons are compact icons (▶/◀) instead of vertical text, with content-based height when peeking. Graph container is hidden by default and only shown by JS when data loads. All 86 tests pass, build succeeds.

### Themes

- **Light** — clean modern light (default fallback)
- **Dark** — deep modern dark
- **Nord** — arctic blue-gray cool tones
- **Solarized** — warm amber reading theme
- **Dracula** — bold purple/cyan/pink dark
- **Forest** — calm nature-inspired green
- **Glass Light** — frosted glass transparency, light base
- **Glass Dark** — frosted glass transparency, dark base
- **Obsidian** — true to the Obsidian app look
- **Catppuccin** — soft warm pastel light
- **Colorful** — rainbow heading colors, vibrant light
- **Colorful Dark** — rainbow heading colors, vibrant dark

## Changed Files

- `frontend/src/styles/themes.css` — NEW: all 12 theme CSS variable definitions, replaces obsidian-vars.css. Includes heading-color variables (--h1-color through --h6-color) and accent variables (--accent-1 through --accent-6)
- `frontend/src/styles/obsidian-vars.css` — REMOVED: superseded by themes.css
- `frontend/src/styles/base.css` — improved typography, heading color variables, h5/h6 sizing, spacing, table styles, selection, hr, transitions
- `frontend/src/styles/layout.css` — glass effects, theme selector dropdown with opaque/blur background, top-bar-hidden class, sidebar peek icon styling, graph container hidden by default
- `frontend/src/theme.ts` — full rewrite: 12-theme dropdown selector, localStorage persistence, system preference detection
- `frontend/src/app.ts` — import themes.css, import scroller module
- `frontend/src/sidebar.ts` — peek buttons show icons (▶/◀) instead of vertical text "Nav"/"Page"
- `frontend/src/graph.ts` — hides container when no data, shows and styles it when graph loads
- `frontend/src/scroller.ts` — NEW: auto-hide top bar on scroll down, show on scroll up
- `src/vaultpub/core/render/templates.py` — removed old theme toggle button from static HTML template
- `src/vaultpub/django_app/templates/vaultpub/base.html` — removed old theme toggle button from Django template

## Tests

- All 86 existing tests pass unchanged

## Manual Verification

- `vaultpub serve` starts successfully and serves pages
- Theme selector appears in the top bar with 12 themes in Light/Dark groups
- Theme dropdown has opaque background with backdrop-blur, content is always readable
- Switching themes applies instantly with smooth color transitions
- Colorful themes show distinct colors for h1-h6 headings
- Glass themes show frosted transparency effects against gradient body backgrounds
- Top bar hides when scrolling down and reappears when scrolling up
- Collapsed sidebar peek buttons show compact icons (▶/◀)
- Peeked sidebar height is based on content, not full viewport
- Empty graph container is hidden, only appears when populated
