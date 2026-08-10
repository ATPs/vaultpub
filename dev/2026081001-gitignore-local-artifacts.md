# Feature: ignore local development artifacts

## Goal

Keep local credentials, runtime databases, AI tool settings, type-checker caches, and browser-test reports out of version control without excluding committed fixtures or environment templates.

## Conclusion

Extended `.gitignore` with targeted patterns for local environment files, SQLite databases, logs, local AI tool directories, additional Python type-checker caches, and Playwright report directories. The `.env.example` convention remains explicitly trackable.

## Changed Files

- `.gitignore`
- `dev/2026081001-gitignore-local-artifacts.md`

## Tests

- Verified representative paths with `git check-ignore`.

## Manual Verification

- Confirmed the existing `.claude/settings.local.json` was only covered by a user-global Git ignore rule before this change.
- Confirmed the tracked Obsidian fixture remains outside the new ignore patterns.
