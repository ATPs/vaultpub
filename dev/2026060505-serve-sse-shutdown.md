# Feature: serve SSE shutdown

## Goal

Ensure `vaultpub serve` shuts down promptly even when a browser keeps `/api/events` open, instead of waiting on Uvicorn's connection-drain path.

## Conclusion

The standalone serve path now installs a server-level shutdown signal that is set before Uvicorn starts waiting for open connections. The SSE stream checks that signal and exits quickly, which allows the HTTP connection to close during graceful shutdown. A finite graceful-shutdown timeout remains as a fallback.

## Changed Files

- `src/vaultpub/cli/main.py`
- `src/vaultpub/core/realtime/broadcaster.py`
- `src/vaultpub/web/routes.py`
- `src/vaultpub/web/sse.py`
- `tests/unit/test_sse_broadcaster.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_realtime_watcher.py tests/unit/test_sse_broadcaster.py tests/integration/test_web_app.py`
- `/data/p/anaconda3/envs/django/bin/python -m ruff check --extend-ignore B008 src/vaultpub/cli/main.py src/vaultpub/core/realtime/broadcaster.py src/vaultpub/web/app.py src/vaultpub/web/routes.py src/vaultpub/web/sse.py tests/unit/test_realtime_watcher.py tests/unit/test_sse_broadcaster.py tests/integration/test_web_app.py`

## Manual Verification

- Started `serve` in a subprocess against a temporary vault.
- Opened a live `/api/events` SSE connection with `httpx.stream`.
- Sent `SIGINT` to the server process.
- Observed `shutdown_seconds=0.715` and process `returncode=-2` (SIGINT exit).
