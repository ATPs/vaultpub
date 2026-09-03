# Feature: Slide View embed protocol

## Goal

Make a single-note Slide View deck embeddable by an authenticated same-origin
host such as LiveClassroom. The host can handshake, receive deck/current-slide
metadata, navigate previous/next or an explicit zero-based slide index, and
track the deck fingerprint used by cue points.

## Conclusion

Added explicit `?embed=1` mode for single-note Slide View. Embedded pages hide
presenter chrome and expose version 1 of the `vaultpub.slide` protocol. The
child accepts only messages from `window.parent` with `event.origin` equal to
the child page origin, and replies only to that origin.

The protocol uses these JSON messages:

- Parent to child handshake: `{protocol: "vaultpub.slide", version: 1,
  type: "handshake", requestId?: string}`.
- Parent to child command: `{protocol: "vaultpub.slide", version: 1,
  type: "command", command: "previous" | "next" | "go_to", index?: number,
  requestId?: string}`. For compatibility, a command may also use the command
  name as `type`.
- Child to parent ready: `{protocol, version, type: "ready", requestId?,
  deck: {noteId, sourcePath, title, slideCount, fingerprint}, slide: {...}}`.
- Child to parent current slide: `{protocol, version, type: "slide-changed",
  requestId?, noteId, sourcePath, index, title, deckFingerprint}`.
- Child to parent failure: `{protocol, version, type: "error", requestId?,
  code, message}`.

The HTTP slide API and multi-note manifest now include `fingerprint`. It is a
SHA-256 digest over versioned note identity, source path, effective split
policy, split mode, and segmented source Markdown. Rendered HTML and viewer
preferences are intentionally excluded.

## Changed Files

- `frontend/src/slides.ts`
- `frontend/src/styles/slides.css`
- `src/vaultpub/core/render/slides.py`
- `src/vaultpub/core/render/templates.py`
- `src/vaultpub/django_app/templates/vaultpub/slides.html`
- `src/vaultpub/django_app/views.py`
- `src/vaultpub/web/routes.py`
- `tests/unit/test_slides.py`
- `tests/integration/test_web_app.py`
- `tests/django/test_django_app.py`
- Generated local static assets (ignored by Git)

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest -q tests/unit/test_slides.py tests/integration/test_web_app.py tests/django/test_django_app.py` passed: 83 tests.
- `/data/p/anaconda3/envs/django/bin/python -m pytest -q` passed: 231 tests.
- `npm run build` passed, including TypeScript compilation and Vite production bundling.
- `git diff --check` passed.

## Manual Verification

- HTTP contract tests verify regular pages do not opt into embed mode,
  `?embed=1` exposes metadata, and `?embed=0` remains ordinary Slide View.
- Browser-level iframe message interaction was not run because this repository
  has no browser test harness and the local environment has no checked-in
  browser automation setup.
