# Feature: realtime shutdown latency

## Goal

Reduce `vaultpub serve` shutdown latency in realtime mode so `Ctrl+C` does not wait on the watcher's default long timeout. Verify that app shutdown signals the watcher to stop promptly and that a real `SIGINT` exits quickly.

## Conclusion

The realtime watcher now receives an explicit stop event from the ASGI lifespan and uses a short `watchfiles` rust timeout. This avoids waiting on the default multi-second watcher timeout during `Ctrl+C`. The shutdown path was verified with targeted tests and a real subprocess measurement.

## Changed Files

- `src/vaultpub/core/realtime/watcher.py`
- `src/vaultpub/web/app.py`
- `tests/unit/test_realtime_watcher.py`
- `tests/integration/test_web_app.py`

## Tests

- `/data/p/anaconda3/envs/django/bin/python -m pytest tests/unit/test_realtime_watcher.py tests/integration/test_web_app.py`
- `/data/p/anaconda3/envs/django/bin/python -m ruff check src/vaultpub/core/realtime/watcher.py src/vaultpub/web/app.py tests/unit/test_realtime_watcher.py tests/integration/test_web_app.py`

## Manual Verification

- Started a realtime app in a subprocess with a temporary vault.
- Sent `SIGINT` after startup and measured process exit time.
- Observed `shutdown_seconds=0.214` and `returncode=0`.
