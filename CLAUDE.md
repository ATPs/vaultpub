# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

vaultpub is a Python package. Project configuration follows PEP 621 (`pyproject.toml`).

## Development Commands

```bash
# Install in editable mode
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_foo.py::test_bar

# Lint
ruff check .

# Format
ruff format .
```

## AGENTS.md
AGENTS.md is also a guide.