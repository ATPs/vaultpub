# Feature: Normal View Font Size

## Goal

Let each visitor adjust normal-view text size from Settings without changing Slide View typography.

## Conclusion

Settings now stores a 12-28 px `fontSize` override in `vaultpub.settings`. Normal pages begin from the publisher `font_size` value, reset to that value, and apply a valid stored override before styles load. Slide View keeps its own text-scale preference.

## Changed Files

- Normal-view configuration, templates, and Django settings bridge
- Settings UI, first-paint bootstrap, and layout styles
- ASGI, Django, static-build, and configuration regression tests

## Tests

- Focused configuration, ASGI, Django, and static-builder tests
- Full pytest suite, Ruff, compileall, and frontend bundle build

## Manual Verification

- Not run; verify normal-view persistence and Slide View isolation in a browser after deployment.
